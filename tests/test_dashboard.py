"""
MODULE: test_dashboard.py
PURPOSE: Unit tests for Streamlit dashboard helper functions
INPUTS: pytest fixtures (test_db)
OUTPUTS: Pass/fail assertions per TEST_REGISTRY T-DASH-C-001, T-DASH-N-001
DEPENDENCIES: pytest, frontend.app
RULE REFERENCES: ZT-002 (SELECT-only SQL console enforcement)
CHANGE LOG: 1.0.0 | 2026-06-17 | TC-008 initial tests (red phase) | Claude Code
             1.1.0 | 2026-06-21 | CL-025 added T-DASH-N-002 (Panel 5 bare
             ternary at app.py:199 triggers Streamlit's magic-write feature,
             which probes the returned DeltaGenerator for _repr_html_() and
             crashes with StreamlitAPIException) — found via AppTest, not the
             originally hypothesized TypedDict/Python-3.14 incompatibility,
             which does not reproduce in this codebase | Claude Code
             1.2.0 | 2026-06-22 | CL-028 added T-DASH-N-003 (Panel 1's
             st.line_chart() call crashes — confirmed this time: altair==5.5.0
             itself fails to import under Python 3.14 with TypeError:
             _TypedDictMeta.__new__() got an unexpected keyword argument
             'closed'. Verified st.bar_chart() and a plain pd.DataFrame input
             fail identically — the bug is in altair's import, not the input
             shape, so the originally proposed pd.DataFrame conversion would
             not have fixed it. Removed the chart call entirely (the
             dataframe on the line above already shows the same data)) | Claude Code
             1.3.0 | 2026-06-25 | CL-054 added T-DASH-N-004 (lesson_topic
             must be non-NULL when only a JIC row is present for a date —
             regression guard for the IN ('JIC','LESSON') SQL fix) | Claude Code
             1.4.0 | 2026-07-28 | CL-060 updated T-DASH-C-001 for None jit/jic
             counts; added T-DASH-C-002 token-log enrichment and T-DASH-C-003
             retry-row collapse | Claude Code
             1.5.0 | 2026-07-28 | CL-060b added T-DASH-C-004 pipeline log item
             counts; updated T-DASH-C-001 for log-derived jit/jic | Claude Code
             1.6.0 | 2026-07-28 | CL-060c added T-DASH-C-005 5+ display default;
             T-DASH-C-006 token history ingestion | Claude Code
             1.7.0 | 2026-07-28 | CL-061 added T-DASH-C-007 langsmith cache precedence | Claude Code
"""
from datetime import date
import json
import sqlite3
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from frontend.app import (
    _collapse_retry_rows,
    _enrich_run_metrics,
    _format_item_count,
    _format_run_metrics_table,
    _get_recent_runs,
    _load_token_usage_by_date,
    _load_langsmith_tokens_from_cache,
    _parse_item_counts_from_log_text,
    _validate_select_only,
)


# ── T-DASH-C-001 ──────────────────────────────────────────────────────────────

def test_t_dash_c_001_run_metrics_query_returns_six_columns(test_db):
    """
    T-DASH-C-001: _get_recent_runs() returns correct 6-column shape from seeded DB.

    Acceptance criteria:
      - Returns non-empty list
      - Each element has exactly the 6 locked keys (covered_date, jit_count,
        jic_count, lesson_topic, model_used, tokens_used)
      - jit_count/jic_count are None when no pipeline log data exists for the date
      - model/tokens populated from gateway_telemetry_logs when present
    """
    today = date.today().isoformat()

    test_db.execute(
        "INSERT INTO historical_ledger (topic, covered_date, run_type) VALUES (?, ?, ?)",
        ("GPT-5 Release", today, "JIT"),
    )
    test_db.execute(
        "INSERT INTO historical_ledger (topic, covered_date, run_type) VALUES (?, ?, ?)",
        ("Transformer Architecture", today, "JIC"),
    )
    test_db.execute(
        "INSERT INTO historical_ledger (topic, covered_date, run_type) VALUES (?, ?, ?)",
        ("MCP Architecture", today, "LESSON"),
    )
    test_db.execute(
        "INSERT INTO gateway_telemetry_logs "
        "(model, tokens_used, fallback_triggered, run_date) VALUES (?, ?, ?, ?)",
        ("gemini/gemini-2.5-flash", 1500, 0, today),
    )
    test_db.commit()

    rows = _get_recent_runs(test_db, 7)

    assert len(rows) >= 1, "Expected at least one run row"
    expected_keys = {
        "covered_date", "jit_count", "jic_count",
        "lesson_topic", "model_used", "tokens_used",
    }
    for row in rows:
        assert set(row.keys()) == expected_keys, (
            f"Column mismatch — got {set(row.keys())}, want {expected_keys}"
        )
    today_row = next((r for r in rows if r["covered_date"] == today), None)
    assert today_row is not None, f"No row for {today} in results"
    assert today_row["jit_count"] is None, "jit_count unknown without pipeline logs in test"
    assert today_row["jic_count"] is None, "jic_count unknown without pipeline logs in test"
    assert today_row["model_used"] == "gemini-2.5-flash", (
        f"Expected short model name from telemetry, got {today_row['model_used']!r}"
    )
    assert today_row["tokens_used"] == 1500


# ── T-DASH-C-002 ──────────────────────────────────────────────────────────────

def test_t_dash_c_002_token_log_enrichment(test_db, tmp_path, monkeypatch):
    """Token/model data falls back to logs/token_usage.json when DB telemetry is empty."""
    run_date = "2026-07-16"
    test_db.execute(
        "INSERT INTO historical_ledger (topic, covered_date, run_type) VALUES (?, ?, ?)",
        ("LangSmith Lesson", run_date, "JIC"),
    )
    test_db.commit()

    token_log = tmp_path / "token_usage.json"
    token_log.write_text(json.dumps({
        "vertex_ai/gemini-2.5-flash-lite": {"tokens_used": 50000, "date": run_date},
        "vertex_ai/gemini-2.5-flash": {"tokens_used": 22000, "date": run_date},
    }))
    monkeypatch.setattr("frontend.app._TOKEN_LOG_PATH", token_log)
    monkeypatch.setattr(
        "frontend.app._LANGSMITH_TOKENS_PATH",
        tmp_path / "missing_langsmith_cache.json",
    )

    rows = _get_recent_runs(test_db, 5)
    row = next(r for r in rows if r["covered_date"] == run_date)
    assert row["tokens_used"] == 72000
    assert row["model_used"] == "gemini-2.5-flash-lite"


# ── T-DASH-C-004 ──────────────────────────────────────────────────────────────

def test_t_dash_c_004_pipeline_log_item_counts():
    """JIT/JIC counts are parsed from gap-fill, validation, and fallback log lines."""
    sample_log = """
INFO:__main__:Pipeline start — lesson topic: 'LangSmith'
WARNING:__main__:JIT validation failed — running gap-fill. JIT output failed validation:
JIT output has 0 items — minimum 5 required.
INFO:__main__:JIT gap-fill reached minimum — 11 items (added 10)
WARNING:__main__:JIC validation failed — running gap-fill. JIC output failed validation:
JIC output has 1 items — minimum 5 required.
INFO:__main__:JIC gap-fill reached minimum — 10 items (added 9)
INFO:__main__:Ledger updated — topic='LangSmith', date=2026-07-16
INFO:__main__:Pipeline complete — delivered=True, topic='LangSmith'
INFO:__main__:Pipeline start — lesson topic: 'Retry Topic'
ERROR:__main__:JIT validation failed — substituting fallback. Details: JIT output failed validation:
JIT output has 0 items — minimum 5 required.
ERROR:__main__:JIC validation failed — substituting fallback. Details: JIC output failed validation:
JIC output has 0 items — minimum 5 required.
INFO:__main__:Ledger updated — topic='Retry Topic', date=2026-07-15
INFO:__main__:Pipeline complete — delivered=True, topic='Retry Topic'
"""
    counts = _parse_item_counts_from_log_text(sample_log)
    assert counts["2026-07-16"] == {"jit_count": 11, "jic_count": 10}
    assert counts["2026-07-15"] == {"jit_count": 5, "jic_count": 5}


def test_t_dash_c_004_enrich_run_metrics_applies_log_counts(test_db, monkeypatch):
    """_enrich_run_metrics() fills jit/jic counts from parsed pipeline logs."""
    run_date = "2026-07-16"
    test_db.execute(
        "INSERT INTO historical_ledger (topic, covered_date, run_type) VALUES (?, ?, ?)",
        ("LangSmith", run_date, "JIC"),
    )
    test_db.commit()

    sample_log = """
INFO:__main__:Pipeline start — lesson topic: 'LangSmith'
INFO:__main__:JIC gap-fill reached minimum — 10 items (added 9)
INFO:__main__:Ledger updated — topic='LangSmith', date=2026-07-16
INFO:__main__:Pipeline complete — delivered=True, topic='LangSmith'
"""
    monkeypatch.setattr(
        "frontend.app._PIPELINE_LOG_PATHS",
        (),
    )
    monkeypatch.setattr(
        "frontend.app._load_item_counts_by_date",
        lambda: _parse_item_counts_from_log_text(sample_log),
    )

    rows = _get_recent_runs(test_db, 5)
    row = next(r for r in rows if r["covered_date"] == run_date)
    assert row["jic_count"] == 10
    assert row["jit_count"] is None


# ── T-DASH-C-005 ──────────────────────────────────────────────────────────────

def test_t_dash_c_005_unknown_item_counts_display_as_five_plus():
    """Unknown JIT/JIC counts render as 5+ (CL-056 pipeline minimum)."""
    assert _format_item_count(None) == "5+"
    assert _format_item_count(10) == 10

    table = _format_run_metrics_table([{
        "covered_date": "2026-07-14",
        "lesson_topic": "LangGraph",
        "jit_count": None,
        "jic_count": 8,
        "model_used": "gemini-2.5-flash",
        "tokens_used": None,
    }])
    row = table.iloc[0]
    assert row["JIT Items"] == "5+"
    assert row["JIC Items"] == "8"


# ── T-DASH-C-006 ──────────────────────────────────────────────────────────────

def test_t_dash_c_006_token_log_history_and_smoke_test_skip(tmp_path, monkeypatch):
    """token_usage.json history entries aggregate; smoke_test key is ignored."""
    token_log = tmp_path / "token_usage.json"
    token_log.write_text(json.dumps({
        "smoke_test": True,
        "vertex_ai/gemini-2.5-flash-lite": {
            "tokens_used": 50000,
            "date": "2026-07-16",
            "history": [
                {"date": "2026-07-10", "tokens_used": 42000},
            ],
        },
        "vertex_ai/gemini-2.5-flash": {
            "tokens_used": 22000,
            "date": "2026-07-16",
            "history": [
                {"date": "2026-07-10", "tokens_used": 18000},
            ],
        },
    }))
    monkeypatch.setattr("frontend.app._TOKEN_LOG_PATH", token_log)
    monkeypatch.setattr(
        "frontend.app._LANGSMITH_TOKENS_PATH",
        tmp_path / "missing_langsmith_cache.json",
    )
    monkeypatch.setattr("frontend.app._PIPELINE_LOG_PATHS", ())

    by_date = _load_token_usage_by_date()
    assert by_date["2026-07-16"]["tokens_used"] == 72000
    assert by_date["2026-07-10"]["tokens_used"] == 60000


# ── T-DASH-C-007 ──────────────────────────────────────────────────────────────

def test_t_dash_c_007_langsmith_cache_takes_precedence(tmp_path, monkeypatch):
    """LangSmith cache supplies tokens; token_usage.json fills gaps only."""
    cache = tmp_path / "langsmith_tokens_by_date.json"
    cache.write_text(json.dumps({
        "tokens_by_date": {
            "2026-07-16": 80000,
            "2026-07-10": 55000,
        },
    }))
    token_log = tmp_path / "token_usage.json"
    token_log.write_text(json.dumps({
        "vertex_ai/gemini-2.5-flash-lite": {
            "tokens_used": 50000,
            "date": "2026-07-16",
        },
        "vertex_ai/gemini-2.5-flash": {
            "tokens_used": 22000,
            "date": "2026-07-16",
        },
        "vertex_ai/gemini-2.5-flash": {
            "tokens_used": 10000,
            "date": "2026-07-04",
        },
    }))
    monkeypatch.setattr("frontend.app._LANGSMITH_TOKENS_PATH", cache)
    monkeypatch.setattr("frontend.app._TOKEN_LOG_PATH", token_log)
    monkeypatch.setattr("frontend.app._PIPELINE_LOG_PATHS", ())

    by_date = _load_token_usage_by_date()
    assert by_date["2026-07-16"]["tokens_used"] == 80000
    assert by_date["2026-07-10"]["tokens_used"] == 55000
    assert by_date["2026-07-04"]["tokens_used"] == 10000


def test_t_dash_c_007_load_langsmith_flat_map(tmp_path, monkeypatch):
    """Cache loader accepts legacy flat {date: tokens} shape."""
    cache = tmp_path / "langsmith_tokens_by_date.json"
    cache.write_text(json.dumps({"2026-07-08": 42000}))
    monkeypatch.setattr("frontend.app._LANGSMITH_TOKENS_PATH", cache)
    monkeypatch.setattr("frontend.app._TOKEN_LOG_PATH", tmp_path / "missing.json")
    monkeypatch.setattr("frontend.app._PIPELINE_LOG_PATHS", ())

    by_date: dict[str, dict] = {}
    _load_langsmith_tokens_from_cache(by_date)
    assert by_date["2026-07-08"]["tokens_used"] == 42000


# ── T-DASH-C-003 ──────────────────────────────────────────────────────────────

def test_t_dash_c_003_collapse_consecutive_retry_rows():
    """Consecutive same-topic rows keep only the newest date."""
    rows = [
        {"covered_date": "2026-07-16", "lesson_topic": "LangSmith"},
        {"covered_date": "2026-07-15", "lesson_topic": "LangSmith"},
        {"covered_date": "2026-07-14", "lesson_topic": "LangGraph"},
    ]
    collapsed = _collapse_retry_rows(rows)
    assert [r["covered_date"] for r in collapsed] == ["2026-07-16", "2026-07-14"]


# ── T-DASH-N-001 ──────────────────────────────────────────────────────────────

def test_t_dash_n_001_non_select_sql_rejected():
    """
    T-DASH-N-001: _validate_select_only() rejects non-SELECT SQL (ZT-002).

    Acceptance criteria:
      - DELETE / DROP / UPDATE each raise ValueError
      - SELECT (and leading-whitespace SELECT) does not raise
    """
    with pytest.raises(ValueError):
        _validate_select_only("DELETE FROM historical_ledger")

    with pytest.raises(ValueError):
        _validate_select_only("DROP TABLE historical_ledger")

    with pytest.raises(ValueError):
        _validate_select_only("UPDATE historical_ledger SET topic = 'x' WHERE id = 1")

    # Valid SELECT statements must not raise
    _validate_select_only("SELECT * FROM historical_ledger")
    _validate_select_only("  select id from historical_ledger where id = 1")


# ── T-DASH-N-002 ──────────────────────────────────────────────────────────────

def test_t_dash_n_002_sql_console_run_does_not_crash(test_db):
    """
    T-DASH-N-002: Panel 5 (SQL Console) runs a pre-built query without raising.

    Root cause (found via AppTest, not the originally hypothesized TypedDict
    issue): app.py:199 was a bare ternary expression statement —
    `st.error(err) if err else st.dataframe(rows, use_container_width=True)`.
    Streamlit's "magic" output feature auto-wraps any bare top-level expression
    statement in st.write(...). When err is falsy, the ternary evaluates
    st.dataframe(...) first (rendering the table as a side effect and
    returning a DeltaGenerator), and that return value is then passed into
    st.write(), which probes it for _repr_html_() and crashes with
    StreamlitAPIException. Simulates: select a pre-built query, click Run.
    """
    test_db.execute(
        "INSERT INTO historical_ledger (topic, covered_date, run_type) VALUES (?, ?, ?)",
        ("Test Topic", date.today().isoformat(), "JIT"),
    )
    test_db.commit()

    at = AppTest.from_file("frontend/app.py", default_timeout=30)
    with patch("frontend.app._connect", return_value=test_db):
        at.run()
        at.sidebar.radio[0].set_value("SQL Console").run()
        at.selectbox[0].set_value("Last 10 ledger rows").run()
        at.button[0].click().run()

    assert len(at.exception) == 0, (
        f"Expected no exception after running a pre-built query, got: {at.exception}"
    )


# ── T-DASH-N-003 ──────────────────────────────────────────────────────────────

def test_t_dash_n_003_run_metrics_panel_does_not_crash(test_db):
    """
    T-DASH-N-003: Panel 1 (Run Metrics, the default panel) renders without
    raising when historical_ledger has rows.

    Root cause: app.py's st.line_chart() call triggers Streamlit's
    generate_chart(), which does `import altair as alt`. altair==5.5.0 itself
    fails to import under Python 3.14: TypeError: _TypedDictMeta.__new__()
    got an unexpected keyword argument 'closed' (altair's own schema file
    uses TypedDict(closed=True), unsupported by this Python version).
    Verified empirically that st.bar_chart() and a plain pd.DataFrame input
    fail identically — the bug is in altair's import itself, not in the
    dict-keyed-by-date input shape, so converting to a pd.DataFrame would not
    have fixed it. Fix: removed the chart call; the dataframe immediately
    above already displays the same data.
    """
    test_db.execute(
        "INSERT INTO historical_ledger (topic, covered_date, run_type) VALUES (?, ?, ?)",
        ("Test Topic", date.today().isoformat(), "JIT"),
    )
    test_db.commit()

    at = AppTest.from_file("frontend/app.py", default_timeout=30)
    with patch("frontend.app._connect", return_value=test_db):
        at.run()

    assert len(at.exception) == 0, (
        f"Expected no exception rendering Panel 1, got: {at.exception}"
    )


# ── T-DASH-N-004 ──────────────────────────────────────────────────────────────

def test_t_dash_n_004_lesson_topic_populated_from_jic_row(test_db):
    """
    T-DASH-N-004: lesson_topic is non-NULL when a JIC row (no LESSON row) exists.

    Root cause (CL-054): _get_recent_runs() CASE expression used
    `run_type = 'LESSON'` only. JIC runs also carry a lesson topic in their
    `topic` column, so restricting to LESSON caused lesson_topic to be NULL
    whenever the day's newsletter was a JIC run (no LESSON row written).
    Fix: widened to `run_type IN ('JIC', 'LESSON')`.

    This test seeds ONLY a JIC row (no LESSON row) and asserts lesson_topic
    is the JIC topic string, not NULL.
    """
    today = date.today().isoformat()

    test_db.execute(
        "INSERT INTO historical_ledger (topic, covered_date, run_type) VALUES (?, ?, ?)",
        ("Retrieval-Augmented Generation", today, "JIC"),
    )
    test_db.execute(
        "INSERT INTO historical_ledger (topic, covered_date, run_type) VALUES (?, ?, ?)",
        ("LLM Benchmarking", today, "JIT"),
    )
    test_db.commit()

    rows = _get_recent_runs(test_db, 7)

    today_row = next((r for r in rows if r["covered_date"] == today), None)
    assert today_row is not None, f"No row for {today} in results"
    assert today_row["lesson_topic"] is not None, (
        "lesson_topic should be non-NULL when a JIC row exists for the date "
        "(regression: was NULL because CASE only checked run_type = 'LESSON')"
    )
    assert today_row["lesson_topic"] == "Retrieval-Augmented Generation", (
        f"Expected lesson_topic='Retrieval-Augmented Generation', "
        f"got {today_row['lesson_topic']!r}"
    )


# ── T-DASH-C-010 / C-011 (CL-066) ────────────────────────────────────────────

def _file_db(tmp_path):
    from scripts.setup_db import init_db
    db = tmp_path / "ledger.db"
    init_db(str(db))
    return db


def test_t_dash_c_010_run_log_panel_and_cost_summary(tmp_path, monkeypatch):
    """T-DASH-C-010: Panel 1 reads run_log; cost today and month-to-date are summed and shown."""
    from datetime import date
    from frontend.app import _cost_summary, _get_run_log
    db = _file_db(tmp_path)
    today = date.today().isoformat()
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO run_log (run_id, run_date, mode, started_at, status, cost_usd) VALUES (?,?,?,?,?,?)",
                 ("r1", today, "full", today, "ok", 0.21))
    conn.execute("INSERT INTO run_log (run_id, run_date, mode, started_at, status, cost_usd) VALUES (?,?,?,?,?,?)",
                 ("r2", today, "dry-run", today, "degraded", 0.04))
    conn.commit()
    assert [r["run_id"] for r in _get_run_log(conn)] == ["r2", "r1"]
    assert _cost_summary(conn, today) == {"today": 0.25, "month": 0.25}
    monkeypatch.setenv("NEWSLETTER_DB_PATH", str(db))
    at = AppTest.from_file("frontend/app.py", default_timeout=30)
    at.run()
    assert len(at.exception) == 0 and any("Cost today" in m.label for m in at.metric)


def test_t_dash_c_011_run_explorer_shows_saved_run(tmp_path, monkeypatch):
    """T-DASH-C-011: Run Explorer loads a run folder and renders without exceptions."""
    import json as _json
    db = _file_db(tmp_path)
    folder = tmp_path / "runs" / "2026-11-02" / "070000-full"
    (folder / "outputs").mkdir(parents=True)
    (folder / "inputs").mkdir()
    (folder / "run.json").write_text(_json.dumps({"status": "ok"}))
    (folder / "outputs" / "jit.json").write_text("[]")
    (folder / "newsletter.html").write_text("<html><body>Hello</body></html>")
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO run_log (run_id, run_date, mode, started_at, status, run_folder) VALUES (?,?,?,?,?,?)",
                 ("r1", "2026-11-02", "full", "2026-11-02", "ok", str(folder)))
    conn.commit()
    monkeypatch.setenv("NEWSLETTER_DB_PATH", str(db))
    at = AppTest.from_file("frontend/app.py", default_timeout=30)
    at.run()
    at.sidebar.radio[0].set_value("Run Explorer").run()
    assert len(at.exception) == 0 and "Panel 7" in at.header[0].value
