"""
MODULE: test_integration.py
PURPOSE: End-to-end tests for main.py v2 with every external service mocked
         (search providers, model calls, citations, SendGrid, network).
DEPENDENCIES: pytest, pytest-mock
RULE REFERENCES: R-001, R-003, R-004, R-006, D9, D12-D15, LOGGING_DESIGN
CHANGE LOG: 1.x (CL-007..CL-056): docs/history/test_integration_v1_CL060.py
            2.0.0 | 2026-11-01 | CL-065/066: rewritten for pipeline v2 (T-INT-I-101..106) | Claude Code
"""
import json
import sqlite3
from datetime import date

import pytest

import main
from core import news

TOPIC = "Transformer Architecture — Attention Mechanism Deep Dive"
TODAY = date.today().isoformat()

JIT_HEADLINES = ["Acme ships Falcon reasoning model", "Borealis launches enterprise agent studio",
                 "Cobalt publishes protein folding benchmark", "Delta open-sources Kestrel weights",
                 "Ember raises Series C for chips", "EU regulators finalise transparency code"]
JIT_RESULTS = [
    {"title": h, "url": f"https://openai.com/index/story-{i}", "date": TODAY, "summary": h}
    for i, h in enumerate(JIT_HEADLINES, start=1)
]
JIC_CONCEPTS = ["Speculative decoding", "Direct preference optimization", "KV cache quantization",
                "GraphRAG retrieval", "Tool-use planning agents", "LLM-as-judge calibration"]
JIC_RESULTS = [
    {"title": f"Concept paper {i}", "url": f"https://arxiv.org/abs/2610.{1000 + i}", "date": TODAY,
     "summary": f"Research on concept {i}."} for i in range(1, 7)
]
JIT_CATEGORIES = ["model release", "product launch", "research result", "open-source release",
                  "funding/M&A", "policy/regulation"]
JIC_BUCKETS = ["architecture", "training & alignment", "inference & systems", "retrieval & memory",
               "agents & tools", "evaluation"]


def _lesson() -> dict:
    return {
        "tldr_what": "Transformers process tokens with attention.", "tldr_why_now": "Every LLM uses them.",
        "tldr_pm_takeaway": "Context length drives cost.",
        "definition": "A neural network architecture built on the attention mechanism.",
        "problem_solved": "Capturing long-range dependencies in parallel.",
        "components": [{"name": "Self-attention", "role": "mixes token information"},
                       {"name": "Feed-forward block", "role": "transforms each token"},
                       {"name": "Positional encoding", "role": "adds order information"}],
        "how_it_works": ["Embed tokens.", "Apply multi-head attention.", "Predict the next token."],
        "key_equation": {"expression": "softmax(QK^T/sqrt(d))V", "plain_english": "a weighted average of values"},
        "examples": ["GPT-4 is a decoder-only transformer.", "BERT has 340M parameters."],
        "limitations": ["Attention cost grows quadratically.", "Context windows are finite."],
        "papers": [{"title": "Attention Is All You Need", "first_author": "Vaswani", "year": 2017,
                    "arxiv_id": "1706.03762", "doi": "", "contribution": "Introduced the transformer.",
                    "is_seminal": True}],
        "uses": [{"company_or_product": "Google Translate", "use": "translation"},
                 {"company_or_product": "GitHub Copilot", "use": "code completion"},
                 {"company_or_product": "ChatGPT", "use": "chat assistant"}],
        "pm_guide": {"use_when": "language tasks", "avoid_when": "small tabular data", "cheaper_alternative": "XGBoost"},
        "maturity_stage": "Mainstream", "maturity_evidence": "Used by every frontier model.",
        "what_next": [{"direction": "Linear attention", "expectation": "cheaper long context",
                       "source_url": "https://arxiv.org/abs/2006.16236"},
                      {"direction": "Mixture of experts", "expectation": "sparse compute",
                       "source_url": "https://arxiv.org/abs/2101.03961"},
                      {"direction": "State space hybrids", "expectation": "linear-time sequence models",
                       "source_url": "https://arxiv.org/abs/2312.00752"}],
        "glossary": [{"term": t, "definition": f"{t} definition."} for t in
                     ["Self-attention", "Feed-forward block", "Positional encoding", "Mechanism", "Token",
                      "Context", "Attention", "Transformer"]],
    }


@pytest.fixture
def env(monkeypatch, tmp_path, mocker):
    for k, v in {"TARGET_EMAIL": "test@example.com", "EMAIL_FROM": "sender@example.com",
                 "LITELLM_MODEL_1": "vertex_ai/gemini-4-argon"}.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("LITELLM_MODEL_2", raising=False)
    mocker.patch("main.validate_env", return_value=True)
    pool = tmp_path / "topic_pool.json"
    pool.write_text(json.dumps({"pointer": 0, "topics": [TOPIC, "RAG Patterns"]}))
    db = tmp_path / "ledger.db"
    return {"pool": str(pool), "db": str(db)}


@pytest.fixture
def externals(mocker):
    """Mock every external boundary; return the mocks for assertions."""
    def fake_research(section, cfg, lesson_topic, domains):
        return [dict(r) for r in (JIT_RESULTS if section == "jit" else JIC_RESULTS)]

    def fake_llm_call(prompt, model_name=None, *, schema=None, stage="", schema_name=""):
        if stage == "jit-editor":
            items = [{"candidate_id": f"C{i}", "headline": JIT_HEADLINES[i - 1], "category": JIT_CATEGORIES[i - 1],
                      "what_happened": f"{JIT_HEADLINES[i - 1]} on {TODAY}.", "why_it_matters_pm": "Changes vendor options.",
                      "also_covered_by": []} for i in range(1, 7)]
            return {"parsed": {"items": items}}
        if stage == "jic-editor":
            items = [{"candidate_id": f"C{i}", "concept": JIC_CONCEPTS[i - 1], "bucket": JIC_BUCKETS[i - 1],
                      "core_insight": f"{JIC_CONCEPTS[i - 1]} is a technique.", "also_covered_by": []}
                     for i in range(1, 7)]
            return {"parsed": {"items": items}}
        return {"parsed": _lesson()}

    m = {
        "research": mocker.patch("core.news._research", side_effect=fake_research),
        "news_llm": mocker.patch("core.news.llm_call", side_effect=fake_llm_call),
        "lesson_llm": mocker.patch("core.lesson.llm_call", side_effect=fake_llm_call),
        "ground": mocker.patch("core.lesson._ground", return_value={"papers": [], "explainers": [], "industry": [],
                                                                   "future": []}),
        "lookup": mocker.patch("core.citations.lookup", return_value={"verified_title": "Attention Is All You Need",
                                                                      "year": 2017, "citations": 120408,
                                                                      "doi": "10.48550/arXiv.1706.03762"}),
        "url_ok": mocker.patch("core.lesson._url_ok", return_value=True),
        "send": mocker.patch("main.send_email", return_value=True),
    }
    return m


def _rows(db, sql):
    conn = sqlite3.connect(db)
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


def _pointer(pool):
    return json.loads(open(pool).read())["pointer"]


def test_t_int_i_101_full_run_sends_saves_and_records(env, externals):
    """T-INT-I-101: full run sends once, saves HTML first, writes ledgers, advances pointer, run_log ok."""
    assert main.run_daily_pipeline(env["pool"], env["db"]) is True
    assert externals["send"].call_count == 1
    html = externals["send"].call_args.kwargs["html"]
    assert "Acme ships Falcon reasoning model" in html and "Speculative decoding" in html and "TL;DR" in html
    assert "★★★" in html and "System status: OK" in html
    assert _pointer(env["pool"]) == 1
    assert _rows(env["db"], "SELECT topic, run_type FROM historical_ledger") == [(TOPIC, "LESSON")]
    assert _rows(env["db"], "SELECT section, COUNT(*) FROM news_ledger GROUP BY section ORDER BY section") == \
        [("jic", 6), ("jit", 6)]
    status, mode, email = _rows(env["db"], "SELECT status, mode, email_status FROM run_log")[0]
    assert (status, mode, email) == ("ok", "full", "sent")
    folder = _rows(env["db"], "SELECT run_folder FROM run_log")[0][0]
    from pathlib import Path
    for f in ("newsletter.html", "run.json", "config_snapshot.json", "send_result.json", "outputs/lesson.json",
              "outputs/jit.json", "outputs/jic_dedupe.json"):
        assert (Path(folder) / f).exists(), f


def test_t_int_i_102_dry_run_saves_but_does_not_send_or_advance(env, externals):
    """T-INT-I-102: --dry-run generates and saves the newsletter; no email, ledgers and pointer untouched."""
    assert main.run_daily_pipeline(env["pool"], env["db"], mode="dry-run") is True
    externals["send"].assert_not_called()
    assert _pointer(env["pool"]) == 0
    assert _rows(env["db"], "SELECT COUNT(*) FROM news_ledger")[0][0] == 0
    assert _rows(env["db"], "SELECT COUNT(*) FROM historical_ledger")[0][0] == 0
    assert _rows(env["db"], "SELECT mode, email_status FROM run_log")[0] == ("dry-run", "skipped")


def test_t_int_i_103_lesson_failure_retries_once_then_skips(env, externals, mocker):
    """T-INT-I-103: a failed lesson keeps the pointer (email still sent); a second failure skips the topic."""
    mocker.patch("core.lesson.generate", return_value={"lesson": {"topic_name": TOPIC}, "ok": False,
                                                       "quality": {}, "failures": ["boom"]})
    assert main.run_daily_pipeline(env["pool"], env["db"]) is True
    assert externals["send"].call_count == 1
    assert "could not be generated today" in externals["send"].call_args.kwargs["html"]
    assert _pointer(env["pool"]) == 0
    assert _rows(env["db"], "SELECT status FROM run_log")[0][0] == "degraded"
    assert main.run_daily_pipeline(env["pool"], env["db"]) is True
    assert _pointer(env["pool"]) == 1, "second failure on the same topic must skip it"


def test_t_int_i_104_repeats_are_dropped_not_padded(env, externals):
    """T-INT-I-104 (D9, R-001): items delivered yesterday are dropped today; section goes quiet, never padded."""
    assert main.run_daily_pipeline(env["pool"], env["db"]) is True
    assert main.run_daily_pipeline(env["pool"], env["db"]) is True
    html = externals["send"].call_args.kwargs["html"]
    assert "Quiet news day: 0 new stories" in html
    assert "Acme ships Falcon reasoning model" not in html


def test_t_int_i_105_resend_uses_saved_html_without_llm_calls(env, externals):
    """T-INT-I-105: --resend re-sends the saved newsletter.html; no model calls."""
    main.run_daily_pipeline(env["pool"], env["db"])
    first_html = externals["send"].call_args.kwargs["html"]
    calls_before = externals["news_llm"].call_count + externals["lesson_llm"].call_count
    assert main.resend(TODAY, db_path=env["db"]) is True
    assert externals["send"].call_args.kwargs["html"] == first_html
    assert externals["news_llm"].call_count + externals["lesson_llm"].call_count == calls_before
    assert "(re-sent)" in externals["send"].call_args.kwargs["subject"]


def test_t_int_i_106_network_down_aborts_without_email(env, externals, mocker):
    """T-INT-I-106: when the network never comes up (Mac asleep) the run fails cleanly, no email."""
    mocker.patch("main.wait_for_network", return_value=False)
    assert main.run_daily_pipeline(env["pool"], env["db"]) is False
    externals["send"].assert_not_called()
    assert _rows(env["db"], "SELECT status FROM run_log")[0][0] == "failed"
    assert _rows(env["db"], "SELECT component, severity FROM run_errors")[0] == ("network", "CRITICAL")
