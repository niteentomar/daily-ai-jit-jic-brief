"""
MODULE: main.py
PURPOSE: Daily JIT/JIC newsletter pipeline entry point (v2).
INPUTS: config/topic_pool.json, config/source_registry.json, config/prompts/*.md, .env
OUTPUTS: email (SendGrid); logs/runs/<date>/<time>-<mode>/ (prompts, searches,
         outputs, newsletter.html, run.json); rows in run_log, llm_calls,
         news_ledger, historical_ledger; advanced topic pointer
USAGE:   python3 main.py              full run (launchd)
         python3 main.py --dry-run    generate + save, no email, no pointer change
         python3 main.py --resend YYYY-MM-DD   re-send that day's saved HTML
DEPENDENCIES: core.news, core.lesson, core.synthesis, core.delivery, core.run_logger
RULE REFERENCES: R-001 (cooldown via news_ledger), R-003 (HTML retry), R-004 (append-only),
                 R-006 (SendGrid retry), D9 (no padding), D12-D15, LOGGING_DESIGN
CHANGE LOG: 1.x (2026-06-17 to 2026-07-28, CL-001..CL-060): see docs/history/main_v1_CL060.py
            2.0.0 | 2026-11-01 | CL-065/CL-066: rewritten. ReAct research + structured
            editor for JIT/JIC (core.news); lesson v2 (core.lesson); sections are
            independent; topic pointer advances when the lesson succeeds; a lesson that
            fails twice is skipped; ledger rows written only after a successful send;
            newsletter.html saved before sending; --dry-run and --resend modes;
            network wait for laptop wake-up | Claude Code
"""
import argparse
import json
import logging
import os
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

from core import lesson as lesson_mod  # noqa: E402
from core import news, run_logger  # noqa: E402
from core.dedupe import record_delivered  # noqa: E402
from core.delivery import send_email  # noqa: E402
from core.gateway import wait_for_network  # noqa: E402
from core.settings import load_registry, load_settings  # noqa: E402
from core.synthesis import render  # noqa: E402
from scripts.check_env import validate_env  # noqa: E402
from scripts.setup_db import init_db  # noqa: E402
from tools.topic_manager import get_next_topic, mark_topic_done  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent
_DB_PATH = str(PROJECT_ROOT / "database" / "ledger.db")
_POOL_PATH = str(PROJECT_ROOT / "config" / "topic_pool.json")
MAX_LESSON_ATTEMPTS = 2


def _write_ledger(db_path: str, topic: str) -> None:
    """Append the delivered lesson to historical_ledger (R-004 append-only, never DELETE)."""
    try:
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("INSERT INTO historical_ledger (topic, covered_date, run_type) VALUES (?, ?, ?)",
                         (topic, date.today().isoformat(), "LESSON"))
            conn.commit()
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        run_logger.log_exception("historical_ledger", exc, severity="CRITICAL")


def _previous_lesson_failures(db_path: str, topic: str) -> int:
    """Count earlier full runs where this topic's lesson failed."""
    try:
        conn = sqlite3.connect(db_path)
        try:
            row = conn.execute("SELECT COUNT(*) FROM run_log WHERE mode='full' AND lesson_topic=? AND lesson_ok=0",
                               (topic,)).fetchone()
            return int(row[0] or 0)
        finally:
            conn.close()
    except sqlite3.Error:
        return 0


def _config_snapshot() -> dict:
    s = load_settings()
    prompts = {p.name: p.stat().st_mtime for p in (PROJECT_ROOT / "config" / "prompts").glob("*.md")}
    return {"models": s.model_chain, "vertex_location": s.vertex_location, "reasoning_effort": s.reasoning_effort,
            "timeout_s": s.timeout_seconds, "dedupe_overlap": s.dedupe_overlap, "dedupe_duplicate": s.dedupe_duplicate,
            "embedding_model": s.embedding_model, "registry_version": load_registry().get("version"),
            "prompt_files_mtime": prompts}


def _status_line(status: str, jit: dict, jic: dict, lesson_res: dict, ctx) -> str:
    q = lesson_res.get("quality", {})
    lesson_part = (f"lesson quality {q.get('slots_pass_pct', '-')}% slots, {q.get('completeness_pct', '-')}% concepts, "
                   f"{q.get('papers_verified', 0)} papers verified") if lesson_res.get("ok") else "lesson unavailable"
    s = ctx.summary if ctx else {}
    model = (s.get("model_used") or "-").split("/")[-1]
    fb = " (fallback used)" if s.get("fallback_used") else ""
    return (f"{status.upper()} | JIT {len(jit['items'])}{' quiet' if jit['quiet'] else ''} | "
            f"JIC {len(jic['items'])}{' quiet' if jic['quiet'] else ''} | {lesson_part} | "
            f"model {model}{fb} | cost so far ${s.get('cost_usd', 0):.2f}")


def build_context(jit: dict, jic: dict, lesson_res: dict, status_line: str, run_id: str) -> dict:
    now = datetime.now()
    jit_items, jic_items = jit["items"], jic["items"]
    return {
        "run_date": now.strftime("%Y-%m-%d"), "run_timestamp": now.strftime("%Y-%m-%d %H:%M:%S"), "run_id": run_id,
        "critical_jit": jit_items[0]["headline"] if jit_items else "No new stories passed today's checks.",
        "critical_jic": jic_items[0]["concept"] if jic_items else "No new concepts passed today's checks.",
        "jit_items": jit_items, "jic_items": jic_items, "jit_quiet": jit["quiet"], "jic_quiet": jic["quiet"],
        "lesson": lesson_res["lesson"], "lesson_ok": lesson_res["ok"], "status_line": status_line,
    }


def _overall_status(jit: dict, jic: dict, lesson_res: dict, sent: bool, mode: str) -> str:
    if mode == "full" and not sent:
        return "failed"
    if jit.get("failed") or jic.get("failed") or not lesson_res.get("ok"):
        return "degraded"
    return "ok"


def run_daily_pipeline(pool_path: str = _POOL_PATH, db_path: str = _DB_PATH, mode: str = "full") -> bool:
    """
    Run the pipeline once. Returns True when the email was sent (or, for --dry-run,
    when the newsletter was generated and saved).
    """
    validate_env()
    init_db(db_path)
    ctx = run_logger.start_run(db_path, mode)
    status, success = "failed", False
    try:
        ctx.save_json("config_snapshot.json", _config_snapshot())
        if not wait_for_network():
            ctx.record_error("network", "No network after waiting (Mac asleep or offline?)", severity="CRITICAL",
                             action_taken="run aborted; no email")
            return False
        topic = get_next_topic(pool_path=pool_path)
        ctx.set(lesson_topic=topic)
        logger.info(f"Pipeline start ({mode}) - lesson topic: '{topic}'")

        jit = news.run_section("jit", topic, db_path)
        jic = news.run_section("jic", topic, db_path, avoid_texts=[i["headline"] for i in jit["items"]])
        lesson_res = lesson_mod.generate(topic)
        ctx.set(jit_count=len(jit["items"]), jic_count=len(jic["items"]), quiet_jit=jit["quiet"],
                quiet_jic=jic["quiet"], lesson_ok=lesson_res["ok"],
                lesson_quality=lesson_res.get("quality", {}).get("slots_pass_pct"),
                quality={"jit": jit["metrics"], "jic": jic["metrics"], "lesson": lesson_res.get("quality")})

        provisional = _overall_status(jit, jic, lesson_res, True, mode)
        html = render(build_context(jit, jic, lesson_res, _status_line(provisional, jit, jic, lesson_res, ctx),
                                    ctx.run_id))
        ctx.save_text("newsletter.html", html)
        subject = f"Your Daily AI Learning Brief: {topic.split(' — ')[0]}"
        ctx.set(subject=subject)

        if mode == "dry-run":
            ctx.set(email_status="skipped")
            success = True
        else:
            success = send_email(html=html, to=os.getenv("TARGET_EMAIL", ""), subject=subject)
            ctx.set(email_status="sent" if success else "failed")
            ctx.save_json("send_result.json", {"sent": success, "at": datetime.now().isoformat(timespec="seconds")})
            if success:
                record_delivered(db_path, ctx.run_id, "jit", jit["items"], jit.get("vectors"))
                record_delivered(db_path, ctx.run_id, "jic", jic["items"], jic.get("vectors"))
                if lesson_res["ok"]:
                    _write_ledger(db_path, topic)
                    mark_topic_done(pool_path=pool_path)
                elif _previous_lesson_failures(db_path, topic) + 1 >= MAX_LESSON_ATTEMPTS:
                    ctx.record_error("lesson", f"Lesson '{topic}' failed {MAX_LESSON_ATTEMPTS} times; skipping topic",
                                     severity="ERROR", action_taken="topic skipped")
                    mark_topic_done(pool_path=pool_path)
        status = _overall_status(jit, jic, lesson_res, success, mode)
        return success
    except Exception as exc:  # noqa: BLE001
        run_logger.log_exception("pipeline", exc, severity="CRITICAL", action_taken="run aborted")
        return False
    finally:
        ctx.finish(status)
        run_logger.end_run()
        logger.info(f"Pipeline finished: status={status}, run={ctx.run_id}, folder={ctx.folder}")


def resend(run_date: str, db_path: str = _DB_PATH) -> bool:
    """Re-send the newsletter saved for run_date. No LLM calls, no ledger changes."""
    validate_env()
    init_db(db_path)
    path = run_logger.latest_html(run_date)
    if not path:
        logger.error(f"No saved newsletter.html for {run_date}")
        return False
    ctx = run_logger.start_run(db_path, "resend")
    try:
        subject = "Your Daily AI Learning Brief (re-sent)"
        try:
            subject = json.loads((path.parent / "run.json").read_text()).get("subject", subject) + " (re-sent)"
        except (OSError, json.JSONDecodeError):
            pass
        ok = send_email(html=path.read_text(encoding="utf-8"), to=os.getenv("TARGET_EMAIL", ""), subject=subject)
        ctx.set(email_status="sent" if ok else "failed", resent_from=str(path))
        return ok
    finally:
        ctx.finish("ok" if ctx.summary.get("email_status") == "sent" else "failed")
        run_logger.end_run()


def sent_today(db_path: str = _DB_PATH, day: str | None = None) -> bool:
    """True if a full run already delivered an email today (prevents double sends)."""
    day = day or date.today().isoformat()
    try:
        conn = sqlite3.connect(db_path)
        try:
            row = conn.execute("SELECT COUNT(*) FROM run_log WHERE run_date = ? AND mode = 'full' "
                               "AND email_status = 'sent'", (day,)).fetchone()
            return bool(row and row[0])
        finally:
            conn.close()
    except sqlite3.Error:
        return False


def scheduled_run(pool_path: str = _POOL_PATH, db_path: str = _DB_PATH, today: date | None = None) -> int:
    """
    Entry point for launchd and the watchdog catch-up (CL-075, R-016).

    Guards: (1) after SCHEDULE_END_DATE (YYYY-MM-DD in .env) do nothing; (2) never send twice on one day.
    Returns a process exit code.
    """
    today = today or date.today()
    end = os.getenv("SCHEDULE_END_DATE", "").strip()
    if end:
        try:
            if today > date.fromisoformat(end):
                logger.info(f"Schedule ended on {end}; nothing to do (R-016).")
                return 0
        except ValueError:
            logger.error(f"SCHEDULE_END_DATE '{end}' is not YYYY-MM-DD; running anyway")
    init_db(db_path)
    if sent_today(db_path, today.isoformat()):
        logger.info("Newsletter already sent today; skipping (R-016 no double send).")
        return 0
    return 0 if run_daily_pipeline(pool_path, db_path, mode="full") else 1


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Daily JIT/JIC AI newsletter")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", help="generate and save, do not send or advance")
    group.add_argument("--resend", metavar="YYYY-MM-DD", help="re-send the saved newsletter for that date")
    group.add_argument("--scheduled", action="store_true",
                       help="scheduler entry: respects SCHEDULE_END_DATE and never sends twice a day")
    args = parser.parse_args(argv)
    if args.resend:
        return 0 if resend(args.resend) else 1
    if args.scheduled:
        return scheduled_run()
    return 0 if run_daily_pipeline(mode="dry-run" if args.dry_run else "full") else 1


if __name__ == "__main__":
    sys.exit(main())
