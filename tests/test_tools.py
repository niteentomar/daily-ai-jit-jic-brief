"""
MODULE: test_tools.py
PURPOSE: Test cases for tools/memory.py, tools/search.py, tools/topic_manager.py, database/schema.sql
INPUTS: pytest fixtures (test_db, mock_search, monkeypatch, mocker, caplog, tmp_path)
OUTPUTS: Pass/fail assertions per TEST_REGISTRY T-MEM-*, T-SRC-*, T-DB-*, T-TOP-* criteria
DEPENDENCIES: pytest, pytest-mock, tools.memory, tools.search, tools.topic_manager, sqlite3
RULE REFERENCES: R-001, R-004, ZT-002
CHANGE LOG: 1.0.0 | 2026-06-16 | TC-003 initial tests | Claude Code
             1.1.0 | 2026-06-16 | TC-004 added T-TOP-C-001 | Claude Code
             1.2.0 | 2026-06-22 | CL-026 added T-DB-N-002 (init_db() default
             db_path is cwd-relative — under launchd, cwd=/, so this raised
             OSError: Read-only file system '/database', the actual cause of
             the live 07:00 launchd failure) and T-MEM-E-002 (tools/memory.py's
             module-level DB_PATH is the same bug — query_history() is called
             from main.py's live agent tools with no conn arg, so it hits
             DB_PATH directly in production) | Claude Code
"""
import json
from datetime import date, timedelta

import pytest

from scripts.setup_db import init_db
from tools.memory import query_history
from tools.search import search
from tools.topic_manager import get_next_topic, mark_topic_done


def _insert_topic(conn, topic: str, days_ago: int, run_type: str = "JIT") -> None:
    """Insert a historical_ledger row with covered_date = today - days_ago."""
    covered = (date.today() - timedelta(days=days_ago)).isoformat()
    conn.execute(
        "INSERT INTO historical_ledger (topic, covered_date, run_type) VALUES (?, ?, ?)",
        (topic, covered, run_type),
    )
    conn.commit()


# ── T-MEM-C-001 ──────────────────────────────────────────────────────────────

def test_t_mem_c_001_cooldown_suppression_active(test_db):
    """T-MEM-C-001: topic covered 3 days ago → Found, delta_days == 3 (< 8, suppressed)."""
    _insert_topic(test_db, "Transformer Architecture", days_ago=3)

    result = query_history("Transformer Architecture", conn=test_db)

    assert result["status"] == "Found"
    assert result["last_covered"] is not None
    assert result["delta_days"] == 3
    assert result["delta_days"] < 8  # R-001: cooldown active


# ── T-MEM-E-001 ──────────────────────────────────────────────────────────────

def test_t_mem_e_001_day_8_topic_re_eligible(test_db):
    """T-MEM-E-001: topic covered exactly 8 days ago → Found, delta_days == 8 (re-eligible)."""
    _insert_topic(test_db, "RAG Architecture", days_ago=8)

    result = query_history("RAG Architecture", conn=test_db)

    assert result["status"] == "Found"
    assert result["delta_days"] == 8
    assert result["delta_days"] >= 8  # R-001: day-8 release — topic is eligible again


# ── T-MEM-E-002 ──────────────────────────────────────────────────────────────

def test_t_mem_e_002_query_history_works_from_any_cwd(monkeypatch, tmp_path):
    """
    T-MEM-E-002: query_history(topic) with no conn argument does not raise
    when cwd is a temp directory with no database/ subdirectory.

    Note: the actual exception this bug raises is sqlite3.OperationalError
    ("unable to open database file"), not OSError/FileNotFoundError as
    originally specified — verified empirically. sqlite3.connect() does not
    create missing parent directories, so a missing database/ dir under the
    relative DB_PATH surfaces as a DB-layer error, not an OS-layer one.
    Asserting on the real exception type so this test is meaningful (it must
    actually fail pre-fix, not pass vacuously by checking for the wrong type).
    """
    monkeypatch.chdir(tmp_path)

    import sqlite3
    try:
        query_history("Some Topic")
    except (OSError, FileNotFoundError, sqlite3.Error) as exc:
        pytest.fail(
            f"query_history() raised {type(exc).__name__} — "
            f"DB_PATH is cwd-relative: {exc}"
        )


# ── T-SRC-C-001 ──────────────────────────────────────────────────────────────

def test_t_src_c_001_tavily_search_returns_results(mocker, mock_search, monkeypatch):
    """T-SRC-C-001: Tavily returns normalised list of {title, url, summary, date}."""
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key-0000")
    mock_client = mocker.patch("tools.search.TavilyClient")
    # CL-064: results outside the window are now dropped client-side, so use today's date
    fresh = [{**r, "published_date": date.today().isoformat()} for r in mock_search["tavily_success"]]
    mock_client.return_value.search.return_value = {"results": fresh}

    results = search("AI news today")

    assert len(results) >= 1
    for r in results:
        assert set(r.keys()) >= {"title", "url", "summary", "date"}  # CL-064 adds "provider"
        assert isinstance(r["title"], str)
        assert isinstance(r["url"], str)


# ── T-SRC-E-001 ──────────────────────────────────────────────────────────────

def test_t_src_e_001_duckduckgo_fallback_on_tavily_fail(mocker, mock_search, caplog, monkeypatch):
    """T-SRC-E-001: Tavily raises → DuckDuckGo called; fallback logged; results normalised."""
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key-0000")
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    mocker.patch("tools.search.TavilyClient", side_effect=Exception("Tavily API down"))
    mock_ddgs = mocker.patch("tools.search.DDGS")
    mock_ddgs.return_value.text.return_value = mock_search["duckduckgo_fallback"]

    with caplog.at_level("WARNING"):
        results = search("AI news today")

    assert len(results) >= 1
    for r in results:
        assert set(r.keys()) >= {"title", "url", "summary", "date"}
    assert any("DuckDuckGo" in record.message for record in caplog.records)


# ── T-DB-N-001 ───────────────────────────────────────────────────────────────

def test_t_db_n_001_no_delete_on_historical_ledger(test_db):
    """T-DB-N-001: R-004 trigger blocks DELETE from historical_ledger."""
    _insert_topic(test_db, "MCP Architecture", days_ago=1)
    count_before = test_db.execute(
        "SELECT COUNT(*) FROM historical_ledger"
    ).fetchone()[0]
    assert count_before == 1

    with pytest.raises(Exception):
        test_db.execute(
            "DELETE FROM historical_ledger WHERE topic = ?", ("MCP Architecture",)
        )

    # Rollback any aborted implicit transaction so SELECT can proceed cleanly
    test_db.rollback()

    count_after = test_db.execute(
        "SELECT COUNT(*) FROM historical_ledger"
    ).fetchone()[0]
    assert count_after == 1


# ── T-DB-N-002 ───────────────────────────────────────────────────────────────

def test_t_db_n_002_init_db_works_when_cwd_is_root(monkeypatch):
    """
    T-DB-N-002: init_db() (default db_path) does not raise OSError when cwd
    is "/" — launchd's actual default cwd (no WorkingDirectory key in the
    plist). Reproduces the exact failure from logs/launchd_stderr.log's 4th
    traceback: OSError: [Errno 30] Read-only file system: '/database'.

    Safe to run for real (no mocking): after the fix, db_path resolves to the
    real project's database/ledger.db, and CREATE TABLE IF NOT EXISTS makes
    re-running the schema idempotent — no data is altered or lost.
    """
    monkeypatch.chdir("/")

    try:
        init_db()
    except OSError as exc:
        pytest.fail(f"init_db() raised OSError — default db_path is cwd-relative: {exc}")


# ── T-TOP-C-001 ───────────────────────────────────────────────────────────────

def test_t_top_c_001_topic_pointer_advances(tmp_path):
    """T-TOP-C-001: mark_topic_done() increments pointer; get_next_topic() returns next topic."""
    pool = {"pointer": 0, "topics": ["Topic A", "Topic B", "Topic C"]}
    pool_file = tmp_path / "topic_pool.json"
    pool_file.write_text(json.dumps(pool))

    # Initial state: pointer=0 → first topic
    assert get_next_topic(pool_path=str(pool_file)) == "Topic A"

    # Advance pointer
    mark_topic_done(pool_path=str(pool_file))

    # Pointer must be 1 in persisted JSON
    updated = json.loads(pool_file.read_text())
    assert updated["pointer"] == 1

    # Next call returns the second topic
    assert get_next_topic(pool_path=str(pool_file)) == "Topic B"
