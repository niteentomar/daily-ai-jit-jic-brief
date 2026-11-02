"""
MODULE: test_run_logger.py
PURPOSE: CL-066 run folder, run_log/llm_calls/run_errors rows, scrubbing, resend lookup.
CHANGE LOG: 1.0.0 | 2026-11-01 | CL-066 | Claude Code
"""
import json
import sqlite3
from datetime import datetime

from core import run_logger
from scripts.setup_db import init_db


def test_t_log_c_001_run_lifecycle_writes_folder_and_rows(tmp_path):
    """T-LOG-C-001: start -> calls/errors -> finish writes run.json and updates run_log."""
    db = str(tmp_path / "l.db")
    init_db(db)
    ctx = run_logger.RunContext(db, "dry-run", runs_dir=tmp_path / "runs", now=datetime(2026, 11, 2, 7, 0, 0))
    ctx.record_llm_call("lesson", "vertex_ai/gemini-4-argon", 1, 12.3, {"prompt_tokens": 100, "completion_tokens": 50}, 0.02, "stop")
    ctx.record_error("search", "tavily down", severity="WARNING", action_taken="next provider")
    ctx.save_text("newsletter.html", "<html></html>")
    ctx.set(lesson_topic="T", lesson_ok=True, jit_count=5, jic_count=6, email_status="skipped")
    ctx.finish("ok")
    assert (ctx.folder / "run.json").exists() and ctx.folder.name == "070000-dry-run"
    conn = sqlite3.connect(db)
    row = conn.execute("SELECT status, mode, tokens_in, tokens_out, cost_usd, lesson_ok FROM run_log").fetchone()
    assert row == ("ok", "dry-run", 100, 50, 0.02, 1)
    assert conn.execute("SELECT COUNT(*) FROM llm_calls").fetchone()[0] == 1
    assert conn.execute("SELECT component FROM run_errors").fetchone()[0] == "search"
    assert conn.execute("SELECT COUNT(*) FROM system_exceptions").fetchone()[0] == 1


def test_t_log_s_001_secrets_scrubbed_from_files(tmp_path, monkeypatch):
    """T-LOG-S-001 (SEC-X-001): env secrets never reach run files."""
    monkeypatch.setenv("SENDGRID_API_KEY", "SG.super-secret-value")
    ctx = run_logger.RunContext(str(tmp_path / "x.db"), "full", runs_dir=tmp_path / "runs")
    ctx.save_json("inputs/x.json", {"k": "SG.super-secret-value"})
    assert "super-secret" not in (ctx.folder / "inputs/x.json").read_text()


def test_t_log_e_001_logging_never_raises_on_bad_db(tmp_path):
    """T-LOG-E-001: an unwritable DB does not stop the run."""
    ctx = run_logger.RunContext(str(tmp_path / "missing" / "dir" / "x.db"), "full", runs_dir=tmp_path / "runs")
    ctx.record_error("x", "y")
    ctx.finish("failed")
    assert json.loads((ctx.folder / "run.json").read_text())["status"] == "failed"


def test_t_log_c_002_latest_html_picks_newest_run(tmp_path):
    """T-LOG-C-002: --resend uses the newest saved newsletter for the date."""
    for t in ("070000-full", "093000-dry-run"):
        d = tmp_path / "2026-11-02" / t
        d.mkdir(parents=True)
        (d / "newsletter.html").write_text(t)
    assert run_logger.latest_html("2026-11-02", runs_dir=tmp_path).read_text() == "093000-dry-run"
    assert run_logger.latest_html("2026-11-03", runs_dir=tmp_path) is None
