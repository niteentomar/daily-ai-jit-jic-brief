"""
MODULE: test_scheduler.py
PURPOSE: Unit test for launchd plist generation helper
INPUTS: pytest (no fixtures required)
OUTPUTS: Pass/fail assertions per TEST_REGISTRY T-SCH-C-001
DEPENDENCIES: scripts.setup_launchd
RULE REFERENCES: GIT-H-001 (logs/ excluded from git)
CHANGE LOG: 1.0.0 | 2026-06-17 | TC-009 initial test (red phase) | Claude Code
"""
from pathlib import Path

from scripts.setup_launchd import generate_plist


# ── T-SCH-C-001 ───────────────────────────────────────────────────────────────

def test_t_sch_c_001_generate_plist_contains_required_elements():
    """
    T-SCH-C-001: generate_plist() returns XML with all four required elements.

    Acceptance criteria:
      - Contains <string>com.niteen.ai-aggregator</string>  (Label key)
      - Contains <integer>7</integer>                        (Hour = 7 AM trigger)
      - Contains the literal project_root path string        (ProgramArguments resolved)
      - Does NOT contain the substring PATH/TO               (no placeholder strings)
    """
    project_root = "<project-root>"
    python_path = "/usr/bin/python3"

    xml = generate_plist(project_root, python_path)

    assert "<string>com.niteen.ai-aggregator</string>" in xml, (
        "Missing Label key value in generated plist"
    )
    assert "<integer>7</integer>" in xml, (
        "Missing Hour=7 in StartCalendarInterval"
    )
    assert project_root in xml, (
        f"project_root path '{project_root}' not found in plist — placeholder not substituted"
    )
    assert "PATH/TO" not in xml, (
        "Placeholder string 'PATH/TO' found in generated plist — substitution failed"
    )


# ── CL-075 production scheduling ─────────────────────────────────────────────
import sqlite3
from datetime import date

import pytest


def test_t_sch_c_010_plists_use_scheduled_flag_venv_and_workdir():
    """T-SCH-C-010: pipeline job runs main.py --scheduled at 07:00 from the project dir; watchdog at 09:30."""
    from scripts.setup_launchd import generate_plist, generate_watchdog_plist
    root, py = "/Users/x/ai-aggregator-system", "/Users/x/ai-aggregator-system/.venv/bin/python"
    p = generate_plist(root, py)
    assert "<string>--scheduled</string>" in p and f"<string>{root}</string>" in p and py in p
    w = generate_watchdog_plist(root, py)
    assert "com.niteen.ai-aggregator.watchdog" in w and "scripts/watchdog.py" in w
    assert "<integer>9</integer>" in w and "<integer>30</integer>" in w


def _db_with_run(tmp_path, day, email="sent", status="ok", cost=0.15, lesson_ok=1, jit=10, jic=9):
    from scripts.setup_db import init_db
    db = tmp_path / "l.db"
    init_db(str(db))
    conn = sqlite3.connect(str(db))
    conn.execute("INSERT INTO run_log (run_id, run_date, mode, started_at, status, email_status, cost_usd, lesson_ok,"
                 " lesson_topic, jit_count, jic_count) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                 (f"r-{day}", day, "full", f"{day}T07:00:00", status, email, cost, lesson_ok, "T", jit, jic))
    conn.commit(); conn.close()
    return db


def test_t_sch_c_011_scheduled_run_never_sends_twice(tmp_path, mocker):
    """T-SCH-C-011 (R-016): if today's email was already sent, --scheduled does nothing."""
    import main
    today = date.today().isoformat()
    db = _db_with_run(tmp_path, today)
    run = mocker.patch("main.run_daily_pipeline", return_value=True)
    assert main.scheduled_run(db_path=str(db)) == 0 and run.call_count == 0


def test_t_sch_c_012_scheduled_run_stops_after_end_date(tmp_path, mocker, monkeypatch):
    """T-SCH-C-012 (R-016): after SCHEDULE_END_DATE nothing runs; before it, the pipeline runs once."""
    import main
    monkeypatch.setenv("SCHEDULE_END_DATE", "2026-11-17")
    run = mocker.patch("main.run_daily_pipeline", return_value=True)
    db = str(tmp_path / "e.db")
    assert main.scheduled_run(db_path=db, today=date(2026, 11, 18)) == 0 and run.call_count == 0
    assert main.scheduled_run(db_path=db, today=date(2026, 11, 17)) == 0 and run.call_count == 1


def test_t_sch_c_013_watchdog_ok_day_no_action(tmp_path):
    """T-SCH-C-013: a clean day passes all checks; no catch-up, no alert; report written."""
    from scripts import watchdog
    day = "2026-11-03"
    db = _db_with_run(tmp_path, day)
    called = []
    r = watchdog.run(day, db_path=db, out_dir=tmp_path / "wd", catch_up=lambda: called.append(1) or 0,
                     alert=lambda d, f: called.append(2) or True)
    assert r["ok"] and called == [] and (tmp_path / "wd" / f"{day}.json").exists()


def test_t_sch_c_014_watchdog_catches_up_once_then_alerts(tmp_path):
    """T-SCH-C-014 (no loops): no run today -> exactly one catch-up per day; still failing -> one alert."""
    from scripts import watchdog
    from scripts.setup_db import init_db
    db = tmp_path / "l.db"
    init_db(str(db))
    calls = {"catch": 0, "alert": 0}

    def catch():
        calls["catch"] += 1
        return 1

    def alert(d, failed):
        calls["alert"] += 1
        assert failed[0]["check"].startswith("W1")
        return True
    for _ in range(2):
        r = watchdog.run("2026-11-04", db_path=db, out_dir=tmp_path / "wd", catch_up=catch, alert=alert)
    assert calls == {"catch": 1, "alert": 2} and not r["ok"]


def test_t_sch_c_015_watchdog_flags_cost_and_lesson(tmp_path):
    """T-SCH-C-015: sent but over cost limit and lesson missing -> alert lists W4 and W6, no catch-up."""
    from scripts import watchdog
    day = "2026-11-05"
    db = _db_with_run(tmp_path, day, cost=3.5, lesson_ok=0)
    got = {}
    r = watchdog.run(day, db_path=db, out_dir=tmp_path / "wd", catch_up=lambda: pytest.fail("no catch-up expected"),
                     alert=lambda d, f: got.setdefault("f", [c["check"][:2] for c in f]) and True)
    assert got["f"] == ["W4", "W6"] and not r["ok"]
