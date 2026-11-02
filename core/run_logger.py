"""
MODULE: run_logger.py
PURPOSE: Per-run audit trail (CL-066, LOGGING_DESIGN): a dated run folder with
         inputs, outputs, final HTML and send result, plus rows in run_log,
         llm_calls and run_errors. Logging never stops the pipeline.
INPUTS: calls from main.py, gateway, news, lesson
OUTPUTS: logs/runs/<YYYY-MM-DD>/<HHMMSS>-<mode>/...; SQLite rows
DEPENDENCIES: stdlib only
RULE REFERENCES: R-004 (append-only), SEC-X-001 (secrets scrubbed), requirement 6
CHANGE LOG: 1.0.0 | 2026-11-01 | CL-066 initial implementation | Claude Code
"""
import json
import logging
import os
import sqlite3
import traceback
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = PROJECT_ROOT / "logs" / "runs"
_SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD")

_current = None


def scrub(text) -> str:
    """Replace any secret-looking env value found in text with [REDACTED]."""
    text = str(text)
    for name, value in os.environ.items():
        if value and len(value) >= 8 and any(m in name.upper() for m in _SECRET_MARKERS):
            text = text.replace(value, "[REDACTED]")
    return text


class RunContext:
    """Collects everything about one pipeline run."""

    def __init__(self, db_path: str, mode: str = "full", runs_dir: Path | None = None, now: datetime | None = None):
        runs_dir = RUNS_DIR if runs_dir is None else runs_dir  # CL-072: resolve at call time (tests patch RUNS_DIR)
        now = now or datetime.now()
        self.db_path = db_path
        self.mode = mode
        self.run_date = now.strftime("%Y-%m-%d")
        self.run_id = f"{now.strftime('%Y%m%d-%H%M%S')}-{mode}"
        self.folder = Path(runs_dir) / self.run_date / f"{now.strftime('%H%M%S')}-{mode}"
        self.started_at = now.isoformat(timespec="seconds")
        self.summary: dict = {"run_id": self.run_id, "mode": mode, "started_at": self.started_at,
                              "errors": [], "llm_calls": 0, "tokens_in": 0, "tokens_out": 0,
                              "cost_usd": 0.0, "fallback_used": 0, "model_used": None}
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.error(f"Run folder not created: {exc}")
        self._db_exec(
            "INSERT INTO run_log (run_id, run_date, mode, started_at, run_folder) VALUES (?,?,?,?,?)",
            (self.run_id, self.run_date, mode, self.started_at, str(self.folder)),
        )

    # ---------- storage helpers (never raise) ----------
    def _db_exec(self, sql: str, params: tuple) -> None:
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute(sql, params)
                conn.commit()
            finally:
                conn.close()
        except Exception as exc:  # logging must never stop the run
            logger.error(f"run_logger DB write failed: {exc}")

    def save_text(self, rel_path: str, text: str) -> Path | None:
        try:
            path = self.folder / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(scrub(text), encoding="utf-8")
            return path
        except Exception as exc:
            logger.error(f"run_logger could not save {rel_path}: {exc}")
            return None

    def save_json(self, rel_path: str, obj) -> Path | None:
        return self.save_text(rel_path, json.dumps(obj, indent=1, default=str, ensure_ascii=False))

    def append_jsonl(self, rel_path: str, obj) -> None:
        try:
            path = self.folder / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(scrub(json.dumps(obj, default=str, ensure_ascii=False)) + "\n")
        except Exception as exc:
            logger.error(f"run_logger could not append {rel_path}: {exc}")

    # ---------- telemetry ----------
    def record_llm_call(self, stage: str, model: str, attempt: int, latency_s: float,
                        usage: dict | None = None, cost_usd: float = 0.0,
                        finish_reason: str | None = None, error_class: str | None = None) -> None:
        usage = usage or {}
        p_tok = int(usage.get("prompt_tokens") or 0)
        c_tok = int(usage.get("completion_tokens") or 0)
        self.summary["llm_calls"] += 1
        self.summary["tokens_in"] += p_tok
        self.summary["tokens_out"] += c_tok
        self.summary["cost_usd"] = round(self.summary["cost_usd"] + (cost_usd or 0.0), 6)
        if not error_class:
            self.summary["model_used"] = self.summary["model_used"] or model
        self._db_exec(
            "INSERT INTO llm_calls (run_id, stage, model, attempt, latency_s, prompt_tokens, "
            "completion_tokens, reasoning_tokens, cost_usd, finish_reason, error_class) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (self.run_id, stage, model, attempt, round(latency_s, 2), p_tok, c_tok,
             usage.get("reasoning_tokens"), cost_usd, finish_reason, error_class),
        )
        self.append_jsonl("llm_calls.jsonl", {"stage": stage, "model": model, "attempt": attempt,
                                              "latency_s": round(latency_s, 2), **usage,
                                              "cost_usd": cost_usd, "finish_reason": finish_reason,
                                              "error_class": error_class})

    def record_error(self, component: str, message, *, severity: str = "ERROR", model: str | None = None,
                     error_class: str | None = None, http_status: int | None = None,
                     attempt: int | None = None, action_taken: str | None = None) -> None:
        msg = scrub(message)[:2000]
        entry = {"component": component, "severity": severity, "model": model, "error_class": error_class,
                 "http_status": http_status, "attempt": attempt, "action_taken": action_taken, "message": msg}
        self.summary["errors"].append(entry)
        self._db_exec(
            "INSERT INTO run_errors (run_id, severity, component, model, error_class, http_status, attempt, "
            "action_taken, message) VALUES (?,?,?,?,?,?,?,?,?)",
            (self.run_id, severity, component, model, error_class, http_status, attempt, action_taken, msg),
        )
        self._db_exec(
            "INSERT INTO system_exceptions (severity, component, message) VALUES (?,?,?)",
            (severity, component, f"[{self.run_id}] {error_class or ''} {msg}"[:2000]),
        )

    def set(self, **values) -> None:
        self.summary.update(values)

    def finish(self, status: str) -> dict:
        s = self.summary
        s["status"] = status
        s["finished_at"] = datetime.now().isoformat(timespec="seconds")
        self.save_json("run.json", s)
        self._db_exec(
            "UPDATE run_log SET finished_at=?, status=?, lesson_topic=?, lesson_ok=?, lesson_quality=?, "
            "jit_count=?, jic_count=?, quiet_jit=?, quiet_jic=?, model_used=?, fallback_used=?, "
            "tokens_in=?, tokens_out=?, cost_usd=?, email_status=? WHERE run_id=?",
            (s["finished_at"], status, s.get("lesson_topic"), _b(s.get("lesson_ok")), s.get("lesson_quality"),
             s.get("jit_count"), s.get("jic_count"), _b(s.get("quiet_jit")), _b(s.get("quiet_jic")),
             s.get("model_used"), s.get("fallback_used"), s.get("tokens_in"), s.get("tokens_out"),
             s.get("cost_usd"), s.get("email_status"), self.run_id),
        )
        return s


def _b(value):
    return None if value is None else int(bool(value))


def start_run(db_path: str, mode: str = "full", **kwargs) -> RunContext:
    """Create and register the current run context."""
    global _current
    _current = RunContext(db_path, mode, **kwargs)
    return _current


def current() -> RunContext | None:
    """Return the active run context, or None outside a pipeline run (e.g. tests, scripts)."""
    return _current


def end_run() -> None:
    global _current
    _current = None


def log_exception(component: str, exc: Exception, **kwargs) -> None:
    """Convenience: record an exception on the current run if one is active."""
    ctx = current()
    logger.error(f"{component}: {type(exc).__name__}: {scrub(exc)}")
    if ctx:
        ctx.record_error(component, f"{exc}\n{traceback.format_exc(limit=3)}",
                         error_class=type(exc).__name__,
                         http_status=getattr(exc, "status_code", None), **kwargs)


def latest_html(run_date: str, runs_dir: Path | None = None) -> Path | None:
    """Return the newest saved newsletter.html for run_date (used by --resend)."""
    day = Path(RUNS_DIR if runs_dir is None else runs_dir) / run_date
    if not day.exists():
        return None
    candidates = sorted(day.glob("*/newsletter.html"), key=lambda p: p.parent.name, reverse=True)
    return candidates[0] if candidates else None
