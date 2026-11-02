"""
MODULE: watchdog.py
PURPOSE: Deterministic daily watchdog (CL-075, R-016, requirement 6 fail-safes).
         Runs after the scheduled send (launchd, 09:30). No LLM calls. Checks today's
         run_log and run.json against fixed rules; if no email went out it triggers ONE
         catch-up run (main.py --scheduled, which itself refuses to double-send), then
         emails a short alert when anything is still wrong. Writes logs/watchdog/<date>.json.
INPUTS: database/ledger.db (run_log, run_errors), logs/runs/<date>/*/run.json, .env
OUTPUTS: logs/watchdog/<date>.json, logs/watchdog.log, optional alert email
DEPENDENCIES: sqlite3, subprocess, core.delivery.send_email
RULE REFERENCES: R-016 (schedule guards), R-012 (cost), requirement 6 (no loops: one catch-up per day)
CHANGE LOG: 1.0.0 | 2026-11-02 | CL-075 initial implementation | Claude Code
"""
import json
import os
import sqlite3
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

DB_PATH = PROJECT_ROOT / "database" / "ledger.db"
OUT_DIR = PROJECT_ROOT / "logs" / "watchdog"


def today_row(db_path: Path, day: str) -> dict | None:
    """Latest full run for `day` (sent runs preferred)."""
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute("SELECT * FROM run_log WHERE run_date = ? AND mode = 'full' "
                               "ORDER BY (email_status = 'sent') DESC, started_at DESC LIMIT 1", (day,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    except sqlite3.Error:
        return None


def critical_errors(db_path: Path, run_id: str) -> int:
    try:
        conn = sqlite3.connect(str(db_path))
        try:
            return conn.execute("SELECT COUNT(*) FROM run_errors WHERE run_id = ? AND severity = 'CRITICAL'",
                                (run_id,)).fetchone()[0]
        finally:
            conn.close()
    except sqlite3.Error:
        return 0


def evaluate(row: dict | None, cost_limit: float, crit: int = 0) -> list:
    """Fixed checks. Returns a list of {check, ok, detail}."""
    if not row:
        return [{"check": "W1 run exists", "ok": False, "detail": "no full run today (Mac asleep/off?)"}]
    return [
        {"check": "W1 run exists", "ok": True, "detail": row["run_id"]},
        {"check": "W2 email sent", "ok": row.get("email_status") == "sent", "detail": row.get("email_status")},
        {"check": "W3 status ok/degraded", "ok": row.get("status") in ("ok", "degraded"), "detail": row.get("status")},
        {"check": "W4 cost within limit", "ok": (row.get("cost_usd") or 0) <= cost_limit,
         "detail": f"${row.get('cost_usd') or 0:.3f} / ${cost_limit:.2f}"},
        {"check": "W5 no critical errors", "ok": crit == 0, "detail": f"{crit} critical"},
        {"check": "W6 lesson delivered", "ok": bool(row.get("lesson_ok")), "detail": row.get("lesson_topic")},
        {"check": "W7 news present", "ok": (row.get("jit_count") or 0) + (row.get("jic_count") or 0) > 0,
         "detail": f"JIT {row.get('jit_count')} / JIC {row.get('jic_count')}"},
    ]


def needs_catch_up(checks: list) -> bool:
    by = {c["check"][:2]: c["ok"] for c in checks}
    return not by.get("W1") or not by.get("W2", True)


def run(day: str | None = None, db_path: Path = DB_PATH, out_dir: Path = OUT_DIR, catch_up=None, alert=None) -> dict:
    """Evaluate today, catch up once if no email went out, alert if anything is still wrong."""
    day = day or date.today().isoformat()
    end = os.getenv("SCHEDULE_END_DATE", "").strip()
    if end and day > end:
        return {"date": day, "skipped": f"schedule ended {end}"}
    limit = float(os.getenv("DAILY_COST_LIMIT_USD", "2.0"))
    row = today_row(db_path, day)
    checks = evaluate(row, limit, critical_errors(db_path, row["run_id"]) if row else 0)
    report = {"date": day, "at": datetime.now().isoformat(timespec="seconds"), "checks": checks, "catch_up": None}
    marker = out_dir / f"catchup_{day}"
    if needs_catch_up(checks) and not marker.exists():
        out_dir.mkdir(parents=True, exist_ok=True)
        marker.write_text(datetime.now().isoformat())  # one catch-up per day, even if it crashes (no loops)
        code = (catch_up or _catch_up)()
        row = today_row(db_path, day)
        checks = evaluate(row, limit, critical_errors(db_path, row["run_id"]) if row else 0)
        report.update({"catch_up": {"exit_code": code}, "checks": checks})
    failed = [c for c in checks if not c["ok"]]
    report["ok"] = not failed
    if failed:
        report["alert_sent"] = (alert or _alert)(day, failed)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{day}.json").write_text(json.dumps(report, indent=1))
    with open(out_dir.parent / "watchdog.log", "a") as fh:
        fh.write(f"{report['at']} {'OK' if report['ok'] else 'ALERT'} "
                 + "; ".join(f"{c['check']}={'ok' if c['ok'] else c['detail']}" for c in checks) + "\n")
    return report


def _catch_up() -> int:
    py = PROJECT_ROOT / ".venv" / "bin" / "python"
    return subprocess.run([str(py if py.exists() else sys.executable), str(PROJECT_ROOT / "main.py"), "--scheduled"],
                          cwd=str(PROJECT_ROOT), timeout=3600).returncode


def _alert(day: str, failed: list) -> bool:
    from core.delivery import send_email
    rows = "".join(f"<li><b>{c['check']}</b>: {c['detail']}</li>" for c in failed)
    html = (f"<p>Watchdog for {day} found problems after one catch-up attempt:</p><ul>{rows}</ul>"
            "<p>Run folder and logs: logs/runs/ and logs/watchdog/. Dashboard: Run Explorer.</p>")
    return send_email(html=html, to=os.getenv("TARGET_EMAIL", ""), subject=f"[Watchdog] Daily brief {day}: action needed")


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r.get(k) for k in ("date", "ok", "catch_up", "skipped")}))
    sys.exit(0)
