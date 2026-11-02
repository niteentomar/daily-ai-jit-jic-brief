"""
MODULE: test_search.py
PURPOSE: Test cases for tools/search.py query truncation and DuckDuckGo failure isolation
INPUTS: pytest fixtures (mocker, caplog)
OUTPUTS: Pass/fail assertions per TEST_REGISTRY T-SRC-N-001, T-SRC-E-002 acceptance criteria
DEPENDENCIES: pytest, pytest-mock, tools.search
RULE REFERENCES: ZT-003 (outbound calls to whitelisted domains only)
CHANGE LOG: 1.0.0 | 2026-06-18 | CL-019 bugfix tests: T-SRC-N-001, T-SRC-E-002 | Claude Code
            1.1.0 | 2026-06-22 | CL-029 added T-SRC-C-002 (_tavily_search()
            passes days=7 AND topic="news" — Tavily's API documents that the
            `days` recency filter is only honored when topic="news"; passing
            days=7 alone with the default topic="general" would have been a
            silent no-op, identical in kind to the GMAIL_SENDER/TARGET_EMAIL
            no-op caught in CL-027) | Claude Code
            1.2.0 | 2026-06-22 | CL-030 added T-SRC-C-003 (search() default
            n changed from 5 to 10 — JIT/JIC counts doubled) | Claude Code
            1.3.0 | 2026-06-23 | CL-043 added T-SRC-N-002/003 (search()
            strips embedded after:/before:YYYY-MM-DD search-operator clauses
            before calling Tavily) — a live run showed every JIT/JIC search
            call failing with Tavily's 400 "When days is set, start_date or
            end_date cannot be set": Vertex AI's Gemini was creatively
            embedding "after:2026-06-16" into its search queries (a
            reasonable response to the prompt's recency instructions), which
            Tavily parses into an internal start_date param that conflicts
            with our explicit days=7. DuckDuckGo's fallback also failed
            (rate-limited) for every call, so JIT/JIC returned empty for the
            entire run | Claude Code
            1.4.0 | 2026-06-26 | CL-056 added T-SRC-C-004/005 (search_broad()
            uses 14-day window + include_domains; load_search_sources() reads
            config/search_sources.json) | Claude Code
"""
import inspect

import tools.search as search_mod
from tools.search import search


# ── T-SRC-N-001 ──────────────────────────────────────────────────────────────

def test_t_src_n_001_query_truncated_before_tavily(mocker):
    """T-SRC-N-001: query longer than 400 chars is truncated to 400 before reaching Tavily."""
    mock_tavily = mocker.patch.object(search_mod, "_tavily_search", return_value=[])

    search("x" * 500)

    called_query = mock_tavily.call_args.args[0]
    assert len(called_query) <= 400, (
        f"Expected truncated query <= 400 chars, got {len(called_query)}"
    )


# ── T-SRC-E-002 ──────────────────────────────────────────────────────────────

def test_t_src_e_002_duckduckgo_failure_returns_empty_list(mocker, caplog):
    """
    T-SRC-E-002: DuckDuckGo raises an exception -> search() returns [] without propagating.

    Patches DDGS (the underlying client _duckduckgo_search() constructs) rather
    than _duckduckgo_search() itself, so the fix under test — the try/except
    wrapped around _duckduckgo_search()'s own body — is what's actually exercised.
    """
    mocker.patch.object(search_mod, "_tavily_search", side_effect=Exception("Tavily down"))
    mocker.patch.object(search_mod, "DDGS", side_effect=Exception("DDG down"))

    with caplog.at_level("WARNING"):
        result = search("AI news today")

    assert result == []


# ── T-SRC-C-002 ──────────────────────────────────────────────────────────────

def test_t_src_c_002_tavily_search_passes_days_and_news_topic(mocker, monkeypatch):
    """
    T-SRC-C-002: _tavily_search() calls TavilyClient.search() with days=7 AND
    topic="news" (CL-029 — stale news fix).

    Tavily's API only honors the `days` recency filter when topic="news";
    with the default topic="general", days is silently ignored server-side.
    Both kwargs must be passed together or the recency fix is a no-op.
    """
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key-0000")
    mock_client_cls = mocker.patch.object(search_mod, "TavilyClient")
    mock_client_cls.return_value.search.return_value = {"results": []}

    search_mod._tavily_search("AI news today", 5)

    _, kwargs = mock_client_cls.return_value.search.call_args
    assert kwargs.get("days") == 7, f"Expected days=7, got call: {kwargs}"
    assert kwargs.get("topic") == "news", f"Expected topic='news', got call: {kwargs}"


# ── T-SRC-C-003 ──────────────────────────────────────────────────────────────

def test_t_src_c_003_search_default_n_is_10():
    """T-SRC-C-003: search()'s default n is 10 (CL-030 — JIT/JIC counts doubled 5→10)."""
    default_n = inspect.signature(search).parameters["n"].default
    assert default_n == 10, f"Expected default n=10, got: {default_n}"


# ── T-SRC-N-002 ──────────────────────────────────────────────────────────────

def test_t_src_n_002_after_date_operator_stripped_before_tavily(mocker):
    """
    T-SRC-N-002: search() strips an embedded "after:YYYY-MM-DD" clause before
    calling Tavily (CL-043 — Tavily's API rejects requests with 400 "When
    days is set, start_date or end_date cannot be set" when the query text
    contains a date-operator clause, since Tavily parses it into an internal
    start_date that conflicts with our explicit days=7 param).
    """
    mock_tavily = mocker.patch.object(search_mod, "_tavily_search", return_value=[])

    search("AI security site:openai.com/research after:2026-06-16")

    called_query = mock_tavily.call_args.args[0]
    assert "after:" not in called_query, (
        f"Expected 'after:' clause stripped from query, got: {called_query!r}"
    )
    assert "2026-06-16" not in called_query, (
        f"Expected the date stripped from query, got: {called_query!r}"
    )


# ── T-SRC-N-003 ──────────────────────────────────────────────────────────────

def test_t_src_n_003_before_date_operator_stripped_before_tavily(mocker):
    """T-SRC-N-003: search() also strips an embedded "before:YYYY-MM-DD" clause (CL-043)."""
    mock_tavily = mocker.patch.object(search_mod, "_tavily_search", return_value=[])

    search("AI security news before:2026-06-23")

    called_query = mock_tavily.call_args.args[0]
    assert "before:" not in called_query, (
        f"Expected 'before:' clause stripped from query, got: {called_query!r}"
    )


# ── T-SRC-C-004 ──────────────────────────────────────────────────────────────

def test_t_src_c_004_search_broad_uses_registry_window_and_domains(mocker, monkeypatch):
    """
    T-SRC-C-004 (rewritten CL-064): search_broad("jit") uses the registry JIT
    window (7 days, D11) and the J1-J4 domain hosts from config/source_registry.json.
    """
    from core.settings import section_config, tier_domains
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key-0000")
    mock_client_cls = mocker.patch.object(search_mod, "TavilyClient")
    mock_client_cls.return_value.search.return_value = {"results": []}

    search_mod.search_broad("AI news", n=3, section="jit")

    _, kwargs = mock_client_cls.return_value.search.call_args_list[0]
    assert kwargs.get("days") == 7
    assert kwargs.get("topic") == "news"
    expected_hosts = search_mod._host_only(tier_domains(section_config("jit")["search_tiers"]))
    assert kwargs.get("include_domains") == expected_hosts


# ── T-SRC-C-006 ──────────────────────────────────────────────────────────────

def test_t_src_c_006_search_broad_jic_uses_general_topic_and_14_day_start_date(mocker, monkeypatch):
    """T-SRC-C-006 (rewritten CL-064): JIC uses topic=general with start_date 14 days back (D1)."""
    from datetime import date, timedelta
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key-0000")
    mock_client_cls = mocker.patch.object(search_mod, "TavilyClient")
    mock_client_cls.return_value.search.return_value = {"results": [{
        "title": "Paper", "url": "https://arxiv.org/abs/1234", "content": "Abstract.",
        "published_date": date.today().isoformat()}]}

    results = search_mod.search_broad("AI architecture", n=5, section="jic")

    _, kwargs = mock_client_cls.return_value.search.call_args
    assert kwargs.get("topic") == "general"
    assert kwargs.get("start_date") == (date.today() - timedelta(days=14)).isoformat()
    assert len(results) == 1


# ── T-SRC-C-005 ──────────────────────────────────────────────────────────────

def test_t_src_c_005_load_search_sources_reads_config():
    """T-SRC-C-005: load_search_sources() returns jit_domains from config file."""
    sources = search_mod.load_search_sources()
    assert "jit_domains" in sources
    assert "arxiv.org" in sources.get("jic_domains", [])
    assert sources.get("gap_fill_queries", {}).get("jit")


# ── CL-069: Tavily date handling and drop-reason logging ─────────────────────

def test_t_src_c_010_normalize_date_iso_rfc2822_and_long_forms():
    """T-SRC-C-010: normalize_date reads ISO, RFC-2822 (Tavily news) and long dates; unknown -> ''."""
    nd = search_mod.normalize_date
    assert nd("2026-10-29T12:00:00Z") == "2026-10-29"
    assert nd("Wed, 29 Oct 2026 12:00:00 GMT") == "2026-10-29"
    assert nd("October 29, 2026") == "2026-10-29"
    assert nd("Oct 29, 2026") == "2026-10-29"
    assert nd(None) == "" and nd("") == "" and nd("last week") == ""


def test_t_src_c_011_tavily_requests_published_date_and_keeps_rfc_dated_news(mocker, monkeypatch):
    """T-SRC-C-011: Tavily is asked for dates on every call, and an RFC-2822 dated in-window
    news result is kept (the 2026-11-01 dry run dropped all Tavily results)."""
    from datetime import date
    from email.utils import format_datetime
    from datetime import datetime, timezone
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key-0000")
    rfc = format_datetime(datetime.now(timezone.utc))  # read back as the local date (CL-072)
    mock_client_cls = mocker.patch.object(search_mod, "TavilyClient")
    mock_client_cls.return_value.search.return_value = {"results": [
        {"title": "OpenAI ships X", "url": "https://openai.com/index/x", "content": "c", "published_date": rfc}]}
    results = search_mod.search_sources("AI news", n=3, days=7, include_domains=["openai.com"], topic="news")
    _, kwargs = mock_client_cls.return_value.search.call_args
    assert kwargs.get("include_published_date") is True
    assert len(results) == 1 and results[0]["date"] == date.today().isoformat()
    assert results[0]["provider"] == "tavily"


def test_t_src_c_012_drop_reasons_logged_per_provider(mocker, monkeypatch, tmp_path):
    """T-SRC-C-012: searches.jsonl records raw/kept counts and drop reasons for each provider tried."""
    import json
    from core import run_logger
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key-0000")
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    mocker.patch.object(search_mod, "_tavily_search", return_value=[
        {"title": "a", "url": "https://example.com/a", "summary": "", "date": "2026-10-30"},
        {"title": "b", "url": "https://openai.com/b", "summary": "", "date": ""}])
    mocker.patch.object(search_mod, "_duckduckgo_search", return_value=[])
    ctx = run_logger.start_run(str(tmp_path / "db.sqlite"), mode="dry-run", runs_dir=str(tmp_path / "runs"))
    try:
        search_mod.search_sources("q", n=3, days=7, include_domains=["openai.com"], topic="news", label="t")
        line = (ctx.folder / "inputs" / "searches.jsonl").read_text().splitlines()[0]
    finally:
        run_logger.end_run()
    rec = json.loads(line)
    tav = rec["attempts"][0]
    assert tav["provider"] == "tavily" and tav["raw"] == 2 and tav["kept"] == 0
    assert tav["dropped"] == {"not_in_allowlist": 1, "no_date": 1}


def test_t_src_c_013_exa_tops_up_when_tavily_keeps_too_few(mocker, monkeypatch):
    """T-SRC-C-013 (CL-069): Tavily keeping 1 of n results triggers an Exa top-up; URLs not repeated."""
    from datetime import date
    today = date.today().isoformat()
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key-0000")
    monkeypatch.setenv("EXA_API_KEY", "exa-test")
    mocker.patch.object(search_mod, "_tavily_search", return_value=[
        {"title": "a", "url": "https://openai.com/a", "summary": "", "date": today}])
    mocker.patch.object(search_mod, "_exa_search", return_value=([
        {"title": "a", "url": "https://openai.com/a", "summary": "", "date": today},
        {"title": "b", "url": "https://openai.com/b", "summary": "", "date": today}], 0.005))
    res = search_mod.search_sources("q", n=8, days=7, include_domains=["openai.com"], topic="news")
    assert [r["url"] for r in res] == ["https://openai.com/a", "https://openai.com/b"]
    assert [r["provider"] for r in res] == ["tavily", "exa"]
