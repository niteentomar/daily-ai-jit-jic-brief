"""
MODULE: test_lesson.py
PURPOSE: CL-065 lesson v2: required concepts from the title, slot checks, repair, verification.
CHANGE LOG: 1.0.0 | 2026-11-01 | CL-065 | Claude Code
"""
import copy

from core import lesson
from tests.test_integration import _lesson

TOPIC = "Transformer Architecture — Attention Mechanism Deep Dive"


def test_t_les_c_001_required_terms_from_subtitle():
    """T-LES-C-001: subtitle after the dash becomes the required-concept list."""
    assert lesson.required_terms("What AI Is — Computational Rationality, AI vs ML vs GenAI, and What AI Is Not") == \
        ["Computational Rationality", "AI vs ML vs GenAI", "What AI Is Not"]
    assert lesson.required_terms("No Subtitle Here") == []


def test_t_les_c_002_valid_lesson_passes_all_slot_checks():
    """T-LES-C-002: the reference lesson passes every slot check and is 100% complete."""
    failures, stats = lesson.check_slots(_lesson(), TOPIC)
    assert failures == [] and stats["completeness_pct"] == 100.0


def test_t_les_n_001_slot_violations_are_named():
    """T-LES-N-001: each broken slot produces a named failure."""
    bad = copy.deepcopy(_lesson())
    bad["components"] = bad["components"][:2]
    bad["limitations"] = ["only one"]
    bad["maturity_stage"] = "Hyped"
    bad["glossary"] = bad["glossary"][:5]
    bad["uses"] = bad["uses"][:1]
    failures, _ = lesson.check_slots(bad, TOPIC)
    joined = " | ".join(failures)
    for frag in ("3A components", "3A limitations", "3E stage", "3I glossary", "3D uses"):
        assert frag in joined


def test_t_les_n_002_missing_required_concept_detected():
    """T-LES-N-002: a lesson that never mentions 'Mechanism' fails completeness."""
    bad = copy.deepcopy(_lesson())
    bad["glossary"] = [g for g in bad["glossary"] if g["term"] != "Mechanism"]
    bad["definition"] = "A neural network architecture built on attention."
    _, stats = lesson.check_slots(bad, TOPIC)
    assert stats["missing_terms"] == ["Attention Mechanism Deep Dive"]


def test_t_les_c_003_repair_used_when_it_reduces_failures(mocker):
    """T-LES-C-003: one targeted repair call replaces the draft only if it has fewer failures."""
    broken = copy.deepcopy(_lesson())
    broken["limitations"] = ["one"]
    calls = iter([{"parsed": broken}, {"parsed": _lesson()}])
    llm = mocker.patch("core.lesson.llm_call", side_effect=lambda *a, **k: next(calls))
    mocker.patch("core.lesson._ground", return_value={"papers": [], "explainers": [], "industry": [], "future": []})
    mocker.patch("core.lesson.verify_papers", return_value=([{"title": "P", "is_seminal": True}],
                                                            {"requested": 1, "verified": 1, "dropped_titles": []}))
    mocker.patch("core.lesson._url_ok", return_value=True)
    res = lesson.generate(TOPIC)
    assert llm.call_count == 2 and res["ok"] and res["quality"]["repaired"] is True and res["failures"] == []


def test_t_les_e_001_model_failure_returns_not_ok(mocker):
    """T-LES-E-001: generation errors never raise; ok=False so the email shows 'retried tomorrow'."""
    mocker.patch("core.lesson._ground", side_effect=RuntimeError("search down"))
    res = lesson.generate(TOPIC)
    assert res["ok"] is False and res["lesson"]["topic_name"] == TOPIC


def test_t_les_c_004_what_next_urls_must_be_retrieved_or_trusted(mocker):
    """T-LES-C-004: 3H source URLs not retrieved and not on a trusted, resolving domain are blanked."""
    mocker.patch("core.lesson._url_ok", return_value=True)
    items = [{"direction": "a", "expectation": "b", "source_url": "https://arxiv.org/abs/1"},
             {"direction": "c", "expectation": "d", "source_url": "https://random-blog.example/x"}]
    out, stats = lesson._finalise_what_next(items, {"future": []})
    assert out[0]["source_url"] and not out[1]["source_url"] and stats["what_next_sources_ok"] == 1


def test_t_les_c_020_short_title_and_shortlist_in_prompt(mocker):
    """T-LES-C-020 (CL-071): searches use the short title; the scored OpenAlex shortlist reaches the prompt;
    first-draft failures are kept in the quality record."""
    from core import lesson
    assert lesson.short_title("What AI Is — Computational Rationality, AI vs ML") == "What AI Is"
    calls = []
    mocker.patch("core.lesson.search_sources", side_effect=lambda q, **k: calls.append(q) or [])
    cand = {"verified_title": "Computational rationality", "year": 2015, "citations": 1200, "venue": "Science",
            "doi": "10.1126/science.aac6076", "score": 0.81}
    mocker.patch("core.lesson.shortlist", return_value=([cand], [cand]))
    seen = {}
    mocker.patch("core.lesson.llm_call", side_effect=lambda prompt, **k: seen.setdefault("p", prompt) and {"parsed": {}})
    mocker.patch("core.lesson.verify_papers", return_value=([], {"requested": 0, "verified": 0, "dropped_titles": []}))
    out = lesson.generate("What AI Is — Computational Rationality, AI vs ML")
    assert all(q.startswith("What AI Is ") for q in calls)
    assert "Computational rationality (2015) | 1200 citations | Science | doi 10.1126/science.aac6076" in seen["p"]
    assert out["quality"]["first_draft_failures"]


def test_t_les_c_021_prompt_states_every_checked_limit():
    """T-LES-C-021 (CL-074): every numeric limit enforced by check_slots is stated in the lesson prompt
    (dry runs 1-3 each paid for a repair call because the 75-word TL;DR cap was never stated)."""
    from core.settings import render_prompt
    p = render_prompt("lesson", topic="T", required_terms="x", papers="", explainers="", industry="", future="",
                      max_papers=5, max_others=4)
    for phrase in ("75 words", "at most 30 words", "3 to 5 items", "role at most 15 words", "3 to 6", "1 or 2",
                   "exactly 2", "exactly 3", "at most 25 words", "8 to 12 terms"):
        assert phrase in p, phrase
