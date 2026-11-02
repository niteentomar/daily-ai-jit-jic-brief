#!/usr/bin/env python3
"""
Fetch per-day token totals from LangSmith and write logs/langsmith_tokens_by_date.json.

Uses POST /runs/stats with data_source_type=root_lite (retained aggregates on shortlived
projects), falling back to lite. Missing ledger dates are estimated from pipeline log
LLM call counts (last resort).
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from statistics import median

import requests
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
_CACHE_PATH = _ROOT / "logs" / "langsmith_tokens_by_date.json"
_LOG_PATHS = (
    _ROOT / "logs" / "launchd_stderr.log",
    _ROOT / "logs" / "launchd_stdout.log",
)
_PROJECT_ID = os.getenv("LANGCHAIN_PROJECT_ID", "")  # set in .env (account-specific, not committed)
_DEFAULT_START = date(2026, 6, 18)
_DEFAULT_END = date(2026, 7, 16)
_STATS_URL = "https://api.smith.langchain.com/runs/stats"
_REQUEST_DELAY_S = 2.0
_MAX_RETRIES = 5

_RE_LEDGER_DATE = re.compile(r"Ledger updated .* date=(\d{4}-\d{2}-\d{2})")
_RE_HTTP = re.compile(
    r"HTTP Request: POST .*?/models/([a-z0-9.-]+)(?::stream|:generateContent)?"
)


def _headers() -> dict[str, str]:
    api_key = os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        raise SystemExit("LANGCHAIN_API_KEY is not set")
    return {"x-api-key": api_key, "Content-Type": "application/json"}


def _post_stats(body: dict) -> requests.Response:
    resp = requests.post(_STATS_URL, headers=_headers(), json=body, timeout=60)
    for attempt in range(_MAX_RETRIES):
        if resp.status_code != 429:
            return resp
        time.sleep(min(30, 2 ** attempt * 2))
        resp = requests.post(_STATS_URL, headers=_headers(), json=body, timeout=60)
    return resp


def _stats_for_day(
    session_id: str,
    day: date,
    *,
    data_source_type: str,
    is_root: bool,
) -> tuple[int | None, int]:
    """Return (total_tokens, run_count) for one UTC calendar day."""
    start = f"{day.isoformat()}T00:00:00Z"
    end = f"{(day + timedelta(days=1)).isoformat()}T00:00:00Z"
    body: dict = {
        "session": [session_id],
        "start_time": start,
        "end_time": end,
        "data_source_type": data_source_type,
    }
    if is_root:
        body["is_root"] = True

    resp = _post_stats(body)
    if not resp.ok:
        return None, 0
    payload = resp.json()
    tokens = payload.get("total_tokens")
    run_count = int(payload.get("run_count") or 0)
    if tokens is None or run_count == 0:
        return None, run_count
    return int(tokens), run_count


def _ledger_dates(conn_path: Path) -> list[str]:
    import sqlite3

    if not conn_path.exists():
        return []
    conn = sqlite3.connect(conn_path)
    try:
        rows = conn.execute(
            "SELECT DISTINCT covered_date FROM historical_ledger ORDER BY covered_date"
        ).fetchall()
    finally:
        conn.close()
    return [row[0] for row in rows if row[0]]


def _load_token_usage_json() -> dict[str, int]:
    path = _ROOT / "logs" / "token_usage.json"
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}

    by_date: dict[str, int] = {}
    for model, payload in raw.items():
        if not isinstance(payload, dict):
            continue
        run_date = payload.get("date")
        if run_date:
            by_date[run_date] = by_date.get(run_date, 0) + int(
                payload.get("tokens_used", 0) or 0
            )
        for historical in payload.get("history") or []:
            if not isinstance(historical, dict):
                continue
            hist_date = historical.get("date")
            if hist_date:
                by_date[hist_date] = by_date.get(hist_date, 0) + int(
                    historical.get("tokens_used", 0) or 0
                )
    return by_date


def _api_calls_by_date() -> dict[str, int]:
    """Count Vertex/Gemini POST calls per covered_date from pipeline logs."""
    by_date: dict[str, int] = {}
    for path in _LOG_PATHS:
        if not path.exists():
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        for block in re.split(r"(?=INFO:__main__:Pipeline start)", text):
            if "Pipeline start" not in block:
                continue
            ledger_dates = _RE_LEDGER_DATE.findall(block)
            if not ledger_dates:
                continue
            run_date = ledger_dates[-1]
            by_date[run_date] = by_date.get(run_date, 0) + len(_RE_HTTP.findall(block))
    return by_date


def _estimate_missing(
    merged: dict[str, int],
    langsmith_dates: set[str],
    ledger_dates: list[str],
) -> tuple[dict[str, int], list[str]]:
    """
    Estimate tokens for ledger dates still missing using median tokens/call.

    Returns (estimates, estimated_date_keys).
    """
    calls = _api_calls_by_date()
    ratios: list[float] = []
    for run_date, tokens in merged.items():
        if run_date not in langsmith_dates:
            continue
        call_count = calls.get(run_date, 0)
        if call_count > 0:
            ratios.append(tokens / call_count)
    if not ratios:
        return {}, []

    tokens_per_call = median(ratios)
    estimates: dict[str, int] = {}
    estimated_keys: list[str] = []
    for run_date in ledger_dates:
        if run_date in merged:
            continue
        call_count = calls.get(run_date, 0)
        if call_count <= 0:
            continue
        estimates[run_date] = int(call_count * tokens_per_call)
        estimated_keys.append(run_date)
    return estimates, estimated_keys


def fetch_tokens_by_date(
    dates: list[str],
    *,
    session_id: str | None = None,
) -> dict[str, int]:
    """Query LangSmith stats for ledger dates; prefer root_lite, then lite."""
    session_id = session_id or _PROJECT_ID
    by_date: dict[str, int] = {}

    for day_key in dates:
        day = date.fromisoformat(day_key)
        tokens, _ = _stats_for_day(
            session_id, day, data_source_type="root_lite", is_root=True
        )
        if tokens is None:
            tokens, _ = _stats_for_day(
                session_id, day, data_source_type="lite", is_root=False
            )
        if tokens is not None:
            by_date[day_key] = tokens
        time.sleep(_REQUEST_DELAY_S)

    return by_date


def _write_cache(
    merged: dict[str, int],
    *,
    langsmith_dates: set[str],
    estimated_dates: list[str],
    start: date,
    end: date,
) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "_meta": {
            "source": "langsmith_runs_stats",
            "project_id": _PROJECT_ID,
            "fetched_at": date.today().isoformat(),
            "date_range": [start.isoformat(), end.isoformat()],
            "dates_from_langsmith": len(langsmith_dates),
            "dates_estimated_from_logs": len(estimated_dates),
            "estimated_dates": sorted(estimated_dates),
        },
        "tokens_by_date": dict(sorted(merged.items())),
    }
    _CACHE_PATH.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> int:
    load_dotenv(_ROOT / ".env")
    ledger_dates = _ledger_dates(_ROOT / "database" / "ledger.db")
    start = date.fromisoformat(ledger_dates[0]) if ledger_dates else _DEFAULT_START
    end = date.fromisoformat(ledger_dates[-1]) if ledger_dates else _DEFAULT_END

    fetched = fetch_tokens_by_date(ledger_dates)
    langsmith_dates = set(fetched.keys())

    token_log = _load_token_usage_json()
    merged = dict(token_log)
    merged.update(fetched)

    estimates, estimated_keys = _estimate_missing(merged, langsmith_dates, ledger_dates)
    merged.update(estimates)

    _write_cache(
        merged,
        langsmith_dates=langsmith_dates,
        estimated_dates=estimated_keys,
        start=start,
        end=end,
    )

    print(f"Wrote {_CACHE_PATH}")
    print(f"LangSmith dates: {len(langsmith_dates)}")
    print(f"Estimated dates: {len(estimated_keys)}")
    print(f"Total dates in cache: {len(merged)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
