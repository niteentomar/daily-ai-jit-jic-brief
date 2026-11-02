"""
MODULE: test_news.py
PURPOSE: CL-065 JIT/JIC v2: editor maps only real candidates, caps, quiet days, research fallback.
CHANGE LOG: 1.0.0 | 2026-11-01 | CL-065 | Claude Code
"""
from datetime import date, timedelta

from core import news

TODAY = date.today().isoformat()


def _cands(n, domain="openai.com", d=TODAY):
    return [{"title": f"Story {i} about unique subject {i * 7}", "url": f"https://{domain}/s{i}", "date": d,
             "summary": f"Summary {i}"} for i in range(1, n + 1)]


def _editor(items):
    return lambda prompt, model_name=None, *, schema=None, stage="", schema_name="": {"parsed": {"items": items}}


def test_t_news_c_001_editor_cannot_invent_urls(mocker, tmp_path):
    """T-NEWS-C-001: items referencing unknown candidate ids are dropped; URL/date come from search results."""
    mocker.patch("core.news._research", return_value=_cands(3))
    mocker.patch("core.news.llm_call", side_effect=_editor([
        {"candidate_id": "C1", "headline": "Story one", "category": "model release", "what_happened": "x 1",
         "why_it_matters_pm": "y", "also_covered_by": ["C2"]},
        {"candidate_id": "C99", "headline": "Invented", "category": "product launch", "what_happened": "x",
         "why_it_matters_pm": "y", "also_covered_by": []}]))
    out = news.run_section("jit", "Some Lesson", str(tmp_path / "x.db"))
    assert [i["url"] for i in out["items"]] == ["https://openai.com/s1"]
    assert out["items"][0]["also_covered_by_urls"] == ["https://openai.com/s2"]
    assert out["quiet"] is True and out["metrics"]["count"] == 1


def test_t_news_c_002_category_cap_enforced_by_code(mocker, tmp_path):
    """T-NEWS-C-002: at most 3 items per JIT category even if the editor returns more."""
    mocker.patch("core.news._research", return_value=_cands(6))
    items = [{"candidate_id": f"C{i}", "headline": ["Acme ships Falcon", "Borealis opens Studio", "Cobalt posts benchmark",
                                                  "Delta frees Kestrel", "Ember trains Lyra"][i - 1],
              "category": "model release", "what_happened": f"different event number {i * 17}", "why_it_matters_pm": "y", "also_covered_by": []} for i in range(1, 6)]
    mocker.patch("core.news.llm_call", side_effect=_editor(items))
    out = news.run_section("jit", "L", str(tmp_path / "x.db"))
    assert len(out["items"]) == 3 and out["metrics"]["per_group"] == {"model release": 3}


def test_t_news_c_003_jic_media_cap_two(mocker, tmp_path):
    """T-NEWS-C-003: at most 2 JIC items from Tier-5 media."""
    mocker.patch("core.news._research", return_value=_cands(4, domain="towardsdatascience.com"))
    buckets = ["architecture", "evaluation", "data", "agents & tools"]
    items = [{"candidate_id": f"C{i}", "concept": ["Speculative decoding", "Preference optimisation", "Data curation",
                                                 "Tool planning"][i - 1], "bucket": buckets[i - 1],
              "core_insight": f"insight {i * 19}", "also_covered_by": []} for i in range(1, 5)]
    mocker.patch("core.news.llm_call", side_effect=_editor(items))
    out = news.run_section("jic", "L", str(tmp_path / "x.db"))
    assert len(out["items"]) == 2 and out["metrics"]["media_items"] == 2


def test_t_news_e_001_no_candidates_gives_quiet_failed_section(mocker, tmp_path):
    """T-NEWS-E-001: no search results -> empty quiet section, never raises (D9)."""
    mocker.patch("core.news._research", return_value=[])
    out = news.run_section("jit", "L", str(tmp_path / "x.db"))
    assert out == {**out, "items": [], "quiet": True, "failed": True}


def test_t_news_c_004_research_falls_back_to_query_plan(mocker):
    """T-NEWS-C-004: when the agent fails, the registry query plan still gathers results."""
    mocker.patch("core.news.run_litellm_tool_loop", side_effect=RuntimeError("agent down"))
    search = mocker.patch("core.news.search_sources", return_value=_cands(10))
    cfg = news.section_config("jit")
    res = news._research("jit", cfg, "L", ["openai.com"])
    assert search.called and len(res) >= 10
    assert all(c.kwargs["days"] == 7 for c in search.call_args_list)


def test_t_news_c_005_search_tool_enforces_limit_and_window(mocker):
    """T-NEWS-C-005: the agent's search tool caps searches at 6 and passes the section window."""
    s = mocker.patch("core.news.search_sources", return_value=_cands(2))
    collector = []
    tool = news._make_search_tool(collector, "jic", news.section_config("jic"), ["arxiv.org"])
    for _ in range(8):
        tool.func("query")
    assert s.call_count == 6 and s.call_args.kwargs["days"] == 14
    assert "limit reached" in tool.func("again")


def test_t_news_n_001_word_limit_violations_measured(mocker, tmp_path):
    """T-NEWS-N-001: over-long slots are measured in metrics (spec: headline <= 12 words)."""
    mocker.patch("core.news._research", return_value=_cands(1))
    long = " ".join(["word"] * 20)
    mocker.patch("core.news.llm_call", side_effect=_editor([{"candidate_id": "C1", "headline": long,
                 "category": "model release", "what_happened": "1", "why_it_matters_pm": "y", "also_covered_by": []}]))
    out = news.run_section("jit", "L", str(tmp_path / "x.db"))
    assert out["metrics"]["word_limit_violations"]["headline"] == 1


def test_t_news_c_010_fingerprint_lead_and_tier_reach_dedupe(mocker, tmp_path):
    """T-NEWS-C-010 (CL-070): the editor schema requires a fingerprint; items carry lead, tier and the
    fingerprint (event_type = category) into duplicate detection; prompt carries the examples."""
    mocker.patch("core.news._research", return_value=_cands(2))
    seen = {}

    def editor(prompt, model_name=None, *, schema=None, stage="", schema_name=""):
        seen["schema"], seen["prompt"] = schema, prompt
        return {"parsed": {"items": [{"candidate_id": "C1", "headline": "OpenAI ships GPT-6.1 Terra",
                                      "category": "model release", "what_happened": "On 26 Oct 1 model.",
                                      "why_it_matters_pm": "y", "also_covered_by": [],
                                      "fingerprint": {"actors": ["OpenAI"], "object": "GPT-6.1 Terra",
                                                      "keywords": ["computer use"], "key_number": ""}}]}}
    mocker.patch("core.news.llm_call", side_effect=editor)
    out = news.run_section("jit", "Some Lesson", str(tmp_path / "x.db"))
    item_schema = seen["schema"]["properties"]["items"]["items"]
    assert "fingerprint" in item_schema["required"]
    assert "Gemini 4 Carbon" in seen["prompt"] and "DUPLICATE" in seen["prompt"]
    it = out["items"][0]
    assert it["fingerprint"]["event_type"] == "model release" and it["tier"] == "J1"
    assert it["lead"] == "Summary 1"


def test_t_news_c_011_first_party_source_becomes_main_link(mocker, tmp_path):
    """T-NEWS-C-011 (CL-073): editor picked TechCrunch, Google's own post is in also_covered_by -> Google's post
    becomes the main link; TechCrunch moves to also covered."""
    cands = [{"title": "Google launches Gemini 4 Carbon", "url": "https://techcrunch.com/g4", "date": TODAY, "summary": "tc"},
             {"title": "Introducing Gemini 4 Carbon", "url": "https://blog.google/technology/g4", "date": TODAY,
              "summary": "Google post"}]
    mocker.patch("core.news._research", return_value=cands)
    mocker.patch("core.news.llm_call", side_effect=_editor([
        {"candidate_id": "C1", "headline": "Google launches Gemini 4 Carbon", "category": "model release",
         "what_happened": "On 28 Oct 4 launched.", "why_it_matters_pm": "y", "also_covered_by": ["C2"],
         "fingerprint": {"actors": ["Google"], "object": "Gemini 4 Carbon", "keywords": [], "key_number": ""}}]))
    it = news.run_section("jit", "Some Lesson", str(tmp_path / "x.db"))["items"][0]
    assert it["url"] == "https://blog.google/technology/g4" and it["tier"] == "J1"
    assert it["also_covered_by_urls"] == ["https://techcrunch.com/g4"] and it["lead"] == "Google post"


def test_t_news_c_012_first_party_search_runs_and_leads_candidates(mocker, tmp_path):
    """T-NEWS-C-012 (CL-074): JIT runs first-party searches restricted to primary tiers; their results come first
    so the 40-candidate cap cannot cut them."""
    from core.settings import section_config, tier_domains
    calls = []

    def fake_search(q, **k):
        calls.append(k)
        if k.get("label") == "jit-first-party":
            return [{"title": "Introducing X", "url": f"https://openai.com/index/x{len(calls)}", "date": TODAY, "summary": ""}]
        return [{"title": f"Media {i}", "url": f"https://techcrunch.com/{len(calls)}-{i}", "date": TODAY, "summary": ""}
                for i in range(8)]
    mocker.patch("core.news.search_sources", side_effect=fake_search)
    mocker.patch("core.news.run_litellm_tool_loop", return_value=None)
    cfg = section_config("jit")
    results = news._research("jit", cfg, "Lesson", tier_domains(cfg["search_tiers"]))
    fp = [k for k in calls if k.get("label") == "jit-first-party"]
    assert len(fp) == len(cfg["first_party_queries"])
    assert fp[0]["include_domains"] == tier_domains(cfg["primary_tiers"])
    assert results[0]["url"].startswith("https://openai.com/")
