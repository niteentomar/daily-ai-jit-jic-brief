"""
MODULE: conftest.py
PURPOSE: Shared pytest fixtures for the ai-aggregator-system test suite
INPUTS: None (fixture definitions only)
OUTPUTS: Fixtures consumed by test_*.py files
DEPENDENCIES: pytest, json, sqlite3, pathlib
RULE REFERENCES: TST-T-001, TST-T-002
CHANGE LOG: 1.0.0 | 2026-06-16 | TC-001 initial fixtures (mock_llm, mock_search) | Claude Code
             1.1.0 | 2026-06-16 | TC-003 added test_db fixture | Claude Code
             1.2.0 | 2026-06-26 | CL-056 autouse stub for search_broad to
             keep JIT/JIC gap-fill tests offline | Claude Code
             2.0.0 | 2026-11-01 | CL-064/066: offline stubs now target the v2
             provider chain (_tavily_search/_exa_search/_duckduckgo_search) and
             embeddings; search usage counters and run folders go to tmp_path | Claude Code
"""
import json
import os
import sqlite3
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def mock_llm():
    """Deterministic LLM response fixtures for gateway tests (TC-002+)."""
    with open(PROJECT_ROOT / "tests" / "mocks" / "mock_llm_responses.json") as f:
        return json.load(f)


@pytest.fixture
def mock_search():
    """Deterministic search result fixtures for search tool tests (TC-003+)."""
    with open(PROJECT_ROOT / "tests" / "mocks" / "mock_search_results.json") as f:
        return json.load(f)


@pytest.fixture(autouse=True)
def _offline_and_isolated(request, mocker, tmp_path, monkeypatch):
    """Keep the suite offline and write counters/run folders to tmp_path."""
    import tools.search as search_mod
    from core import run_logger
    monkeypatch.setattr(search_mod, "_USAGE_PATH", tmp_path / "search_usage.json")
    monkeypatch.setattr(run_logger, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setenv("NETWORK_WAIT_SECONDS", "0")
    if not os.getenv("LITELLM_MODEL_1"):
        monkeypatch.setenv("LITELLM_MODEL_1", "vertex_ai/gemini-4-argon")
    mocker.patch("core.gateway._sleep", return_value=None)
    if not request.module.__name__.endswith("test_gateway_policy"):
        mocker.patch("core.gateway.wait_for_network", return_value=True)
        mocker.patch("main.wait_for_network", return_value=True)
    mocker.patch("litellm.completion", side_effect=RuntimeError("real LLM calls are disabled in tests"))
    mocker.patch("requests.post", side_effect=RuntimeError("real HTTP POST disabled in tests"))
    if request.module.__name__.endswith("test_search") and not os.getenv("TAVILY_API_KEY"):
        monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key-0000")
    if not request.module.__name__.endswith(("test_search", "test_tools")):
        mocker.patch("tools.search._tavily_search", return_value=[])
        mocker.patch("tools.search._exa_search", return_value=([], 0.0))
        mocker.patch("tools.search._duckduckgo_search", return_value=[])
    if not request.module.__name__.endswith("test_dedupe"):
        mocker.patch("core.dedupe.embed", return_value=None)
    if not request.module.__name__.endswith("test_citations"):
        mocker.patch("core.citations.search_pool", return_value=[])  # CL-071: no live OpenAlex in tests
        mocker.patch("core.citations.arxiv_search", return_value=[])  # CL-073: no live arXiv in tests
        mocker.patch("core.citations.arxiv_categories", return_value={})
        mocker.patch("core.citations.grade_papers", return_value=None)
    run_logger.end_run()
    yield
    run_logger.end_run()


@pytest.fixture
def test_db():
    """Fresh in-memory SQLite database initialised from database/schema.sql for each test."""
    # check_same_thread=False: Streamlit AppTest runs the script in its own thread
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    with open(PROJECT_ROOT / "database" / "schema.sql") as f:
        conn.executescript(f.read())
    yield conn
    conn.close()

# ── CL-072: write guard. Tests must never change real project files (logs, config, database). ──
_GUARDED = ("logs", "config", "database")


def _snapshot(root):
    snap = {}
    for top in _GUARDED:
        base = root / top
        if base.exists():
            for f in base.rglob("*"):
                # runner logs (logs/*.log, e.g. setup_v2.log written by `tee` while pytest runs) are not test output
                if f.is_file() and "__pycache__" not in f.parts and not (f.parent == root / "logs" and f.suffix == ".log"):
                    snap[str(f.relative_to(root))] = f.stat().st_mtime_ns
    return snap


@pytest.fixture(scope="session", autouse=True)
def _project_write_guard():
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    before = _snapshot(root)
    yield
    after = _snapshot(root)
    changed = sorted(k for k in after if before.get(k) != after[k])
    assert not changed, f"Tests wrote to real project files (CL-072 write guard): {changed[:10]}"
