"""
MODULE: app.py
PURPOSE: Streamlit dashboard — run metrics, cooldown checker, lesson queue,
         audit log, SQL console, email template preview
INPUTS: database/ledger.db (SQLite), config/topic_pool.json, config/email_template.html
OUTPUTS: Interactive Streamlit single-page UI; topic_pool.json writes (Panel 3)
DEPENDENCIES: streamlit, sqlite3, tools.topic_manager, tools.memory, core.delivery
RULE REFERENCES: ZT-002 (SELECT-only SQL console), R-004 (ledger read-only from dashboard)
CHANGE LOG: 1.0.0 | 2026-06-17 | TC-008 initial implementation | Claude Code
            1.1.0 | 2026-06-21 | CL-025 bugfix: _panel_sql()'s bare ternary
            expression statement (`st.error(err) if err else st.dataframe(...)`)
            triggered Streamlit's magic-write feature, which wrapped the whole
            line in st.write(...) and probed st.dataframe()'s DeltaGenerator
            return value for _repr_html_(), crashing with StreamlitAPIException.
            Replaced with a proper if/else block | Claude Code
            1.2.0 | 2026-06-22 | CL-028 bugfix: Panel 1's st.line_chart() call
            crashed — altair==5.5.0 itself fails to import under Python 3.14
            (TypeError: _TypedDictMeta.__new__() got an unexpected keyword
            argument 'closed'). Verified st.bar_chart() and a plain
            pd.DataFrame input fail identically, so converting the chart's
            input format would not have fixed it. Removed the chart call —
            the dataframe above already shows the same data | Claude Code
            1.3.0 | 2026-06-25 | CL-054 bugfix: _get_recent_runs() lesson_topic
            CASE expression used run_type = 'LESSON' only, so JIC runs (which
            also carry a lesson topic) showed NULL in Panel 1. Widened to
            IN ('JIC', 'LESSON') | Claude Code
            1.4.0 | 2026-07-28 | CL-060: Run Metrics no longer shows misleading
            jit_count=0/jic_count=1 from ledger row counts; enriches model/tokens
            from gateway_telemetry_logs and logs/token_usage.json; collapses
            consecutive retry rows for the same lesson topic | Claude Code
            1.5.0 | 2026-07-28 | CL-060b: backfill JIT/JIC item counts from pipeline
            logs (gap-fill / validation patterns); token_usage.json for all dated
            rows; shortened Panel 1 caption | Claude Code
            1.6.0 | 2026-07-28 | CL-060c: unknown JIT/JIC counts display as 5+
            (CL-056 minimum); token backfill merges token_usage.json history
            entries and pipeline-log model hints | Claude Code
            1.7.0 | 2026-07-28 | CL-061: token backfill reads
            logs/langsmith_tokens_by_date.json (LangSmith stats cache) before
            token_usage.json and pipeline-log hints | Claude Code
            2.0.0 | 2026-11-01 | CL-066: Panel 1 reads run_log (status, quality,
            quiet flags, model, fallback, tokens, cost today / month to date);
            legacy view kept when run_log is empty. New "Run Explorer" panel
            (prompts, searches, raw vs final output, de-dup decisions, quality,
            rendered newsletter). New pre-built SQL queries for run_log,
            llm_calls, news_ledger, run_errors. Test Send needs explicit
            confirmation | Claude Code
"""
import json
import logging
import os
import re
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent
_DB_PATH = Path(os.getenv("NEWSLETTER_DB_PATH") or (_ROOT / "database" / "ledger.db"))  # env override for tests
_POOL_PATH = _ROOT / "config" / "topic_pool.json"
_TEMPLATE_PATH = _ROOT / "config" / "email_template.html"
_TOKEN_LOG_PATH = _ROOT / "logs" / "token_usage.json"
_LANGSMITH_TOKENS_PATH = _ROOT / "logs" / "langsmith_tokens_by_date.json"
_PIPELINE_LOG_PATHS = (
    _ROOT / "logs" / "launchd_stderr.log",
    _ROOT / "logs" / "launchd_stdout.log",
)
_TOPIC_MAX_LEN = 55
_FALLBACK_ITEM_COUNT = 5
_UNKNOWN_ITEM_LABEL = "5+"

_RE_LEDGER_DATE = re.compile(r"Ledger updated .* date=(\d{4}-\d{2}-\d{2})")
_RE_LOG_MODEL = re.compile(r"models/([a-z0-9.-]+)(?::|:stream|:generateContent)")
_RE_TOKEN_BUDGET = re.compile(
    r"Token budget exceeded for ([^:]+):\s*(\d+)/\d+ tokens", re.IGNORECASE
)
_RE_GAP_REACHED = re.compile(
    r"(JIT|JIC) gap-fill reached minimum[^\d]*(\d+) items", re.IGNORECASE
)
_RE_AGENT_ITEM_COUNT = re.compile(r"(JIT|JIC) output has (\d+) items", re.IGNORECASE)
_RE_GAP_TOTAL = re.compile(
    r"(JIT|JIC) gap-fill query .*\(total (\d+)/", re.IGNORECASE
)

load_dotenv(dotenv_path=_ROOT / ".env")


# ---------------------------------------------------------------------------
# Pure data helpers — testable without Streamlit
# ---------------------------------------------------------------------------

def _accumulate_token_entry(
    by_date: dict[str, dict],
    run_date: str,
    model: str,
    tokens: int,
) -> None:
    """Add one model's token count into the per-date aggregate."""
    if not run_date or tokens <= 0:
        return
    entry = by_date.setdefault(run_date, {"tokens_used": 0, "_models": []})
    entry["tokens_used"] += tokens
    entry["_models"].append((model, tokens))


def _finalize_token_by_date(by_date: dict[str, dict]) -> dict[str, dict]:
    """Pick dominant model per date and drop internal bookkeeping keys."""
    finalized: dict[str, dict] = {}
    for run_date, entry in by_date.items():
        models = entry.pop("_models", [])
        finalized[run_date] = {
            "tokens_used": entry.get("tokens_used", 0),
            "model_used": max(models, key=lambda item: item[1])[0] if models else None,
        }
    return finalized


def _load_langsmith_tokens_from_cache(by_date: dict[str, dict]) -> None:
    """
    Ingest logs/langsmith_tokens_by_date.json (LangSmith stats cache).

    Accepts either {date: tokens} or {"tokens_by_date": {date: tokens}}.
    """
    if not _LANGSMITH_TOKENS_PATH.exists():
        return
    try:
        raw = json.loads(_LANGSMITH_TOKENS_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return

    token_map = raw.get("tokens_by_date") if isinstance(raw, dict) else None
    if not isinstance(token_map, dict):
        token_map = raw if isinstance(raw, dict) else {}

    for run_date, tokens in token_map.items():
        if run_date.startswith("_"):
            continue
        try:
            total = int(tokens)
        except (TypeError, ValueError):
            continue
        if total > 0:
            entry = by_date.setdefault(
                run_date, {"tokens_used": 0, "_models": []}
            )
            entry["tokens_used"] = total


def _load_token_usage_from_json(
    by_date: dict[str, dict],
    *,
    skip_dates: set[str] | None = None,
) -> None:
    """
    Ingest logs/token_usage.json into by_date (mutates in place).

    Reads every model entry (skips metadata keys like smoke_test), sums tokens
    per date across models, and includes optional per-model history arrays.
    Dates in skip_dates are not overwritten (LangSmith cache takes precedence).
    """
    if not _TOKEN_LOG_PATH.exists():
        return
    skip = skip_dates or set()
    try:
        raw = json.loads(_TOKEN_LOG_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return

    for model, payload in raw.items():
        if not isinstance(payload, dict):
            continue
        run_date = payload.get("date")
        if run_date and run_date not in skip:
            _accumulate_token_entry(
                by_date,
                run_date,
                model,
                int(payload.get("tokens_used", 0) or 0),
            )
        for historical in payload.get("history") or []:
            if not isinstance(historical, dict):
                continue
            hist_date = historical.get("date")
            if hist_date and hist_date not in skip:
                _accumulate_token_entry(
                    by_date,
                    hist_date,
                    model,
                    int(historical.get("tokens_used", 0) or 0),
                )


def _ingest_token_hints_from_log_text(by_date: dict[str, dict], text: str) -> None:
    """Merge token-budget warning hints from one pipeline log into by_date."""
    if not text.strip():
        return

    current_date: str | None = None
    for block in re.split(r"(?=INFO:__main__:Pipeline start)", text):
        if "Pipeline start" not in block:
            continue
        ledger_dates = _RE_LEDGER_DATE.findall(block)
        if ledger_dates:
            current_date = ledger_dates[-1]
        if not current_date:
            continue
        for model, tokens in _RE_TOKEN_BUDGET.findall(block):
            _accumulate_token_entry(by_date, current_date, model.strip(), int(tokens))


def _parse_models_from_log_text(text: str) -> dict[str, str]:
    """Dominant httpx model slug per covered_date from pipeline log blocks."""
    if not text.strip():
        return {}

    by_date: dict[str, str] = {}
    for block in re.split(r"(?=INFO:__main__:Pipeline start)", text):
        if "Pipeline start" not in block:
            continue
        ledger_dates = _RE_LEDGER_DATE.findall(block)
        if not ledger_dates:
            continue
        run_date = ledger_dates[-1]
        models = _RE_LOG_MODEL.findall(block)
        if models:
            by_date[run_date] = max(set(models), key=models.count)
    return by_date


def _load_models_by_date() -> dict[str, str]:
    """Merge dominant model hints from all configured pipeline log files."""
    merged: dict[str, str] = {}
    for path in _PIPELINE_LOG_PATHS:
        if not path.exists():
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        merged.update(_parse_models_from_log_text(text))
    return merged


def _load_token_usage_by_date() -> dict[str, dict]:
    """
    Merge token totals from LangSmith cache, token_usage.json, and log hints.

    Priority: langsmith_tokens_by_date.json, then token_usage.json, then
    token-budget warnings in pipeline logs.

    Returns {date: {"tokens_used": int, "model_used": str}} where model_used is
    the model with the highest token count that day (langsmith entries have no
    per-model split).
    """
    by_date: dict[str, dict] = {}
    _load_langsmith_tokens_from_cache(by_date)
    langsmith_dates = set(by_date.keys())
    _load_token_usage_from_json(by_date, skip_dates=langsmith_dates)
    for path in _PIPELINE_LOG_PATHS:
        if not path.exists():
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        _ingest_token_hints_from_log_text(by_date, text)
    return _finalize_token_by_date(by_date)


def _short_model_name(model: str | None) -> str | None:
    """Strip provider prefix for compact dashboard display."""
    if not model:
        return None
    return model.split("/", 1)[-1] if "/" in model else model


def _truncate_topic(topic: str | None) -> str | None:
    if not topic:
        return topic
    if len(topic) <= _TOPIC_MAX_LEN:
        return topic
    return topic[: _TOPIC_MAX_LEN - 1].rstrip() + "…"


def _section_count_from_run_block(block: str, section: str) -> int | None:
    """
    Best-effort JIT/JIC final item count from one pipeline run log block.

    Prefers gap-fill success totals, then fallback substitution (5 items),
    then partial totals when gap-fill could not reach minimum.
    """
    section = section.upper()
    key = section.lower()

    reached = [int(n) for s, n in _RE_GAP_REACHED.findall(block) if s.upper() == section]
    if reached:
        return reached[-1]

    if f"{section} validation failed" in block and "substituting fallback" in block:
        return _FALLBACK_ITEM_COUNT

    agent_counts = [
        int(n) for s, n in _RE_AGENT_ITEM_COUNT.findall(block) if s.upper() == section
    ]
    gap_totals = [int(n) for s, n in _RE_GAP_TOTAL.findall(block) if s.upper() == section]

    if f"{section} still below minimum after gap-fill" in block:
        candidates = agent_counts + gap_totals
        return max(candidates) if candidates else None

    if (
        f"{section} validation failed" in block
        or f"{section} below minimum" in block
    ) and gap_totals:
        return max(gap_totals)

    return None


def _parse_item_counts_from_log_text(text: str) -> dict[str, dict[str, int | None]]:
    """
    Parse pipeline logs into per-covered_date JIT/JIC item counts.

    Each completed run is anchored by ``Ledger updated … date=YYYY-MM-DD``.
    Later runs for the same date overwrite earlier ones (retries).
    """
    if not text.strip():
        return {}

    by_date: dict[str, dict[str, int | None]] = {}
    for block in re.split(r"(?=INFO:__main__:Pipeline start)", text):
        if "Pipeline start" not in block:
            continue
        ledger_dates = _RE_LEDGER_DATE.findall(block)
        if not ledger_dates:
            continue
        run_date = ledger_dates[-1]
        by_date[run_date] = {
            "jit_count": _section_count_from_run_block(block, "JIT"),
            "jic_count": _section_count_from_run_block(block, "JIC"),
        }
    return by_date


def _load_item_counts_by_date() -> dict[str, dict[str, int | None]]:
    """Load and merge JIT/JIC counts from all configured pipeline log files."""
    merged: dict[str, dict[str, int | None]] = {}
    for path in _PIPELINE_LOG_PATHS:
        if not path.exists():
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        for run_date, counts in _parse_item_counts_from_log_text(text).items():
            merged[run_date] = counts
    return merged


def _format_item_count(count: int | None) -> str | int:
    """Display JIT/JIC count; unknown counts show pipeline minimum (CL-056)."""
    if count is None:
        return _UNKNOWN_ITEM_LABEL
    return count


def _format_item_count_display(count: int | None) -> str:
    """Arrow-safe display value for st.dataframe (CL-060c)."""
    value = _format_item_count(count)
    return value if isinstance(value, str) else str(value)


def _enrich_run_metrics(rows: list[dict]) -> list[dict]:
    """
    Fill JIT/JIC counts from pipeline logs; model/tokens from token_usage.json
    (and gateway telemetry already in the row), with env fallback for model.
    """
    token_by_date = _load_token_usage_by_date()
    item_counts_by_date = _load_item_counts_by_date()
    models_by_date = _load_models_by_date()
    default_model = os.getenv("LITELLM_MODEL_1")

    for row in rows:
        covered = row["covered_date"]
        log_counts = item_counts_by_date.get(covered, {})
        row["jit_count"] = log_counts.get("jit_count")
        row["jic_count"] = log_counts.get("jic_count")

        log_entry = token_by_date.get(covered, {})
        log_tokens = log_entry.get("tokens_used")

        db_tokens = row.get("tokens_used")
        if db_tokens is None or db_tokens == 0:
            if log_tokens:
                row["tokens_used"] = log_tokens
                if log_entry.get("model_used"):
                    row["model_used"] = log_entry["model_used"]

        if not row.get("model_used"):
            row["model_used"] = (
                log_entry.get("model_used")
                or models_by_date.get(covered)
                or default_model
            )
        row["model_used"] = _short_model_name(row.get("model_used"))

        row["lesson_topic"] = _truncate_topic(row.get("lesson_topic"))
    return rows


def _collapse_retry_rows(rows: list[dict]) -> list[dict]:
    """
    Drop earlier consecutive rows when the same lesson topic was retried.

    Keeps the newest date per retry streak (rows are newest-first).
    """
    if not rows:
        return rows
    collapsed: list[dict] = []
    prev_topic = object()
    for row in rows:
        topic = row.get("lesson_topic")
        if topic and topic == prev_topic:
            continue
        collapsed.append(row)
        prev_topic = topic
    return collapsed


def _get_recent_runs(conn: sqlite3.Connection, n: int) -> list:
    """
    Return last n daily run summaries (6-column contract, locked TC-008).

    Columns: covered_date, jit_count, jic_count, lesson_topic, model_used, tokens_used.
    jit_count/jic_count come from pipeline logs when available. model/tokens come
    from gateway_telemetry_logs, then logs/token_usage.json, then env for model.
    """
    sql = """
        SELECT
            hl.covered_date,
            MAX(CASE WHEN hl.run_type IN ('JIC', 'LESSON') THEN hl.topic END) AS lesson_topic,
            telem.model_used,
            telem.tokens_used
        FROM historical_ledger hl
        LEFT JOIN (
            SELECT
                run_date,
                MAX(model) AS model_used,
                SUM(tokens_used) AS tokens_used
            FROM gateway_telemetry_logs
            GROUP BY run_date
        ) telem ON telem.run_date = hl.covered_date
        GROUP BY hl.covered_date
        ORDER BY hl.covered_date DESC
        LIMIT ?
    """
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(sql, (n,)).fetchall()]
    return _collapse_retry_rows(_enrich_run_metrics(rows))


def _format_run_metrics_table(rows: list[dict]) -> pd.DataFrame:
    """Build a display-ready dataframe; unknown counts show as 5+ (CL-056 minimum)."""
    display_rows = []
    for row in rows:
        display_rows.append({
            "Date": row["covered_date"],
            "Lesson Topic": row.get("lesson_topic") or "—",
            "JIT Items": _format_item_count_display(row.get("jit_count")),
            "JIC Items": _format_item_count_display(row.get("jic_count")),
            "Model": row.get("model_used") or "—",
            "Tokens": (
                f"{row['tokens_used']:,}"
                if isinstance(row.get("tokens_used"), int) and row["tokens_used"] > 0
                else "—"
            ),
        })
    return pd.DataFrame(display_rows)


def _validate_select_only(sql: str) -> None:
    """Raise ValueError if sql is not a SELECT statement (ZT-002 enforcement)."""
    if not sql.strip().upper().startswith("SELECT"):
        raise ValueError(
            f"ZT-002: only SELECT statements are permitted in the SQL console. "
            f"Received: {sql[:60]!r}"
        )


def _get_cooldown_topics(conn: sqlite3.Connection, n: int) -> list:
    """Return the last n historical_ledger rows for the cooldown-history table."""
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT topic, covered_date, run_type FROM historical_ledger "
        "ORDER BY covered_date DESC, id DESC LIMIT ?",
        (n,),
    ).fetchall()
    return [dict(r) for r in rows]


def _get_audit_entries(conn: sqlite3.Connection, n: int) -> list:
    """Return the last n system_exceptions rows as audit entries."""
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT severity, component, message, created_at "
        "FROM system_exceptions ORDER BY created_at DESC LIMIT ?",
        (n,),
    ).fetchall()
    return [dict(r) for r in rows]


def _run_safe_query(conn: sqlite3.Connection, sql: str) -> tuple:
    """Validate and execute a user-supplied SQL string. Returns (rows, error_or_None)."""
    try:
        _validate_select_only(sql)
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute(sql).fetchall()], None
    except ValueError as exc:
        return [], str(exc)
    except sqlite3.Error as exc:
        return [], f"SQL error: {exc}"


# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    """Open a SQLite connection to the production ledger database."""
    return sqlite3.connect(str(_DB_PATH))


# ---------------------------------------------------------------------------
# Panel renderers
# ---------------------------------------------------------------------------

_RUN_LOG_COLUMNS = ("run_date", "mode", "status", "lesson_topic", "lesson_ok", "lesson_quality", "jit_count",
                    "jic_count", "quiet_jit", "quiet_jic", "model_used", "fallback_used", "tokens_in",
                    "tokens_out", "cost_usd", "email_status", "run_id")


def _get_run_log(conn: sqlite3.Connection, n: int = 30) -> list:
    """v2 run history from run_log (CL-066); [] if the table is missing or empty."""
    try:
        cur = conn.execute(f"SELECT {', '.join(_RUN_LOG_COLUMNS)} FROM run_log ORDER BY id DESC LIMIT ?", (n,))
        return [dict(zip(_RUN_LOG_COLUMNS, r)) for r in cur.fetchall()]
    except sqlite3.Error:
        return []


def _cost_summary(conn: sqlite3.Connection, today: str) -> dict:
    """Spend today and month to date from run_log (cost_usd per run)."""
    try:
        day = conn.execute("SELECT COALESCE(SUM(cost_usd),0) FROM run_log WHERE run_date=?", (today,)).fetchone()[0]
        month = conn.execute("SELECT COALESCE(SUM(cost_usd),0) FROM run_log WHERE substr(run_date,1,7)=?",
                             (today[:7],)).fetchone()[0]
        return {"today": round(day or 0, 4), "month": round(month or 0, 4)}
    except sqlite3.Error:
        return {"today": 0.0, "month": 0.0}


def _panel_run_metrics(conn: sqlite3.Connection) -> None:
    st.header("Panel 1 — Daily Run Metrics")
    runs = _get_run_log(conn, 30)
    if runs:
        from datetime import date as _date
        cost = _cost_summary(conn, _date.today().isoformat())
        c1, c2, c3 = st.columns(3)
        c1.metric("Cost today (USD)", f"${cost['today']:.2f}")
        c2.metric("Cost month to date (USD)", f"${cost['month']:.2f}")
        c3.metric("Last run status", runs[0]["status"] or "running")
        df = pd.DataFrame(runs)
        df["lesson_topic"] = df["lesson_topic"].map(_truncate_topic)
        df["model_used"] = df["model_used"].map(_short_model_name)
        st.dataframe(df, use_container_width=True, hide_index=True)
        return
    rows = _get_recent_runs(conn, 30)
    if rows:
        st.caption(
            f"{len(rows)} runs · {rows[-1]['covered_date']}→{rows[0]['covered_date']} · "
            "JIT/JIC from logs · retries collapsed"
        )
        st.dataframe(_format_run_metrics_table(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No run data yet. Execute main.py to populate the ledger.")


def _panel_cooldown(conn: sqlite3.Connection) -> None:
    st.header("Panel 2 — Topic History & Cooldown Checker")
    query = st.text_input("Enter a topic to check cooldown status:")
    if query:
        from tools.memory import query_history
        st.json(query_history(query, conn=conn))
    st.subheader("Last 30 Covered Topics")
    st.dataframe(_get_cooldown_topics(conn, 30), use_container_width=True)


def _panel_queue() -> None:
    st.header("Panel 3 — Lesson Queue Manager")
    pool = json.loads(_POOL_PATH.read_text())
    topics, pointer = pool["topics"], pool["pointer"]
    st.write(f"Current pointer: **{pointer}** → `{topics[pointer % len(topics)]}`")
    st.dataframe(
        [{"index": i, "topic": t, "current": i == pointer} for i, t in enumerate(topics)],
        use_container_width=True,
    )
    _panel_queue_add(pool)
    _panel_queue_controls(pool, pointer, topics)


def _panel_queue_add(pool: dict) -> None:
    with st.form("add_topic"):
        new_topic = st.text_input("New topic (appended to end of queue):")
        if st.form_submit_button("Add") and new_topic.strip():
            pool["topics"].append(new_topic.strip())
            _POOL_PATH.write_text(json.dumps(pool, indent=2))
            st.success(f"Added: {new_topic.strip()}")


def _panel_queue_controls(pool: dict, pointer: int, topics: list) -> None:
    col1, col2 = st.columns(2)
    if col1.button("Move current topic up") and pointer > 0:
        topics[pointer], topics[pointer - 1] = topics[pointer - 1], topics[pointer]
        pool["pointer"] = pointer - 1
        _POOL_PATH.write_text(json.dumps(pool, indent=2))
        st.rerun()
    if col2.button("Skip current topic"):
        pool["pointer"] = (pointer + 1) % len(topics)
        _POOL_PATH.write_text(json.dumps(pool, indent=2))
        st.rerun()


def _panel_audit(conn: sqlite3.Connection) -> None:
    st.header("Panel 4 — Error & Audit Log")
    entries = _get_audit_entries(conn, 20)
    if entries:
        st.dataframe(entries, use_container_width=True)
    else:
        st.info("No errors logged in system_exceptions.")


def _panel_run_explorer(conn: sqlite3.Connection) -> None:
    st.header("Panel 7 — Run Explorer")
    runs = _get_run_log(conn, 60)
    if not runs:
        st.info("No v2 runs yet. Run `python3 main.py --dry-run` to create one.")
        return
    labels = {f"{r['run_id']} | {r['status'] or 'running'} | {r['mode']}": r for r in runs}
    pick = st.selectbox("Run:", list(labels))
    folder_row = conn.execute("SELECT run_folder FROM run_log WHERE run_id=?", (labels[pick]["run_id"],)).fetchone()
    folder = Path(folder_row[0]) if folder_row and folder_row[0] else None
    if not folder or not folder.exists():
        st.warning("Run folder not found on disk.")
        return
    tabs = st.tabs(["Summary", "JIT", "JIC", "Lesson", "Prompts", "Searches", "Newsletter"])
    with tabs[0]:
        st.json(_read_json(folder / "run.json"))
    for tab, sec in ((tabs[1], "jit"), (tabs[2], "jic")):
        with tab:
            st.subheader("Final items")
            st.json(_read_json(folder / "outputs" / f"{sec}.json"))
            st.subheader("Metrics")
            st.json(_read_json(folder / "outputs" / f"{sec}_metrics.json"))
            st.subheader("De-duplication decisions")
            st.dataframe(_read_json(folder / "outputs" / f"{sec}_dedupe.json") or [], use_container_width=True)
    with tabs[3]:
        st.subheader("Quality")
        st.json(_read_json(folder / "outputs" / "lesson_quality.json"))
        st.subheader("Final lesson")
        st.json(_read_json(folder / "outputs" / "lesson.json"))
    with tabs[4]:
        for p in sorted((folder / "inputs").glob("prompt_*.md")):
            with st.expander(p.name):
                st.code(p.read_text(encoding="utf-8"), language="markdown")
    with tabs[5]:
        path = folder / "inputs" / "searches.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        st.dataframe([{k: v for k, v in json.loads(x).items() if k != "results"} | {"results": len(json.loads(x).get("results", []))}
                      for x in lines], use_container_width=True)
    with tabs[6]:
        html_path = folder / "newsletter.html"
        if html_path.exists():
            st.components.v1.html(html_path.read_text(encoding="utf-8"), height=900, scrolling=True)
        else:
            st.info("No newsletter saved for this run.")


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


_PREBUILT_QUERIES = {
    "Runs (v2) with cost": (
        "SELECT run_date, mode, status, lesson_topic, jit_count, jic_count, model_used, fallback_used, "
        "tokens_in, tokens_out, cost_usd, email_status FROM run_log ORDER BY id DESC LIMIT 30"
    ),
    "Model calls (latest run)": (
        "SELECT stage, model, attempt, latency_s, prompt_tokens, completion_tokens, cost_usd, finish_reason, "
        "error_class FROM llm_calls WHERE run_id=(SELECT run_id FROM run_log ORDER BY id DESC LIMIT 1)"
    ),
    "Delivered news (last 14 days)": (
        "SELECT covered_date, section, headline, domain, category FROM news_ledger "
        "WHERE covered_date >= date('now','-14 day') ORDER BY id DESC"
    ),
    "Run errors (latest 30)": (
        "SELECT created_at, severity, component, model, error_class, http_status, attempt, action_taken, message "
        "FROM run_errors ORDER BY id DESC LIMIT 30"
    ),
    "Last 10 ledger rows": (
        "SELECT * FROM historical_ledger ORDER BY id DESC LIMIT 10"
    ),
    "Token usage by date": (
        "SELECT run_date, SUM(tokens_used) AS total_tokens "
        "FROM gateway_telemetry_logs GROUP BY run_date ORDER BY run_date DESC"
    ),
    "Recent errors": (
        "SELECT severity, component, message, created_at "
        "FROM system_exceptions ORDER BY created_at DESC LIMIT 20"
    ),
}


def _panel_sql(conn: sqlite3.Connection) -> None:
    st.header("Panel 5 — SQL Query Console")
    st.caption("ZT-002: SELECT statements only. Non-SELECT queries are blocked.")
    choice = st.selectbox("Pre-built queries:", ["(custom)"] + list(_PREBUILT_QUERIES))
    default = _PREBUILT_QUERIES.get(choice, "")
    sql = st.text_area("SQL:", value=default, height=100)
    if st.button("Run"):
        rows, err = _run_safe_query(conn, sql)
        if err:
            st.error(err)
        else:
            st.dataframe(rows, use_container_width=True)


def _panel_email_preview() -> None:
    st.header("Panel 6 — Email Template Preview")
    html = _TEMPLATE_PATH.read_text() if _TEMPLATE_PATH.exists() else "<p>Template not found.</p>"
    edited = st.text_area("Edit template HTML:", value=html, height=300)
    col1, col2 = st.columns(2)
    if col1.button("Save changes"):
        _TEMPLATE_PATH.write_text(edited)
        st.success("Template saved.")
    st.components.v1.html(edited, height=600, scrolling=True)
    to = os.getenv("TARGET_EMAIL", "")
    confirm = col2.checkbox("I understand Test Send emails this raw template")
    if col2.button("Test Send") and to and confirm:
        from core.delivery import send_email
        ok = send_email(html=edited, to=to)
        st.success("Sent!") if ok else st.error("Send failed — check logs.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="Daily AI Newsletter Dashboard", layout="wide")
    st.title("Daily JIT/JIC AI Newsletter — Dashboard")
    conn = _connect()
    panels = {
        "Run Metrics": lambda: _panel_run_metrics(conn),
        "Cooldown Checker": lambda: _panel_cooldown(conn),
        "Lesson Queue": _panel_queue,
        "Audit Log": lambda: _panel_audit(conn),
        "SQL Console": lambda: _panel_sql(conn),
        "Email Preview": _panel_email_preview,
        "Run Explorer": lambda: _panel_run_explorer(conn),
    }
    panel = st.sidebar.radio("Panel", list(panels.keys()))
    panels[panel]()


if __name__ == "__main__":
    main()
