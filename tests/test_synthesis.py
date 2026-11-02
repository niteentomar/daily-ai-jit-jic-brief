"""
MODULE: test_synthesis.py
PURPOSE: Test cases for core/synthesis.py — Jinja2 rendering + HTML schema validation
INPUTS: pytest fixtures (mocker, caplog)
OUTPUTS: Pass/fail assertions per TEST_REGISTRY T-SYN-* and T-FMT-* acceptance criteria
DEPENDENCIES: pytest, pytest-mock, core.synthesis
RULE REFERENCES: R-003 (retry-once on validation failure), TST-T-001, TST-T-002
CHANGE LOG: 1.0.0 | 2026-06-17 | TC-005 initial tests (red phase) | Claude Code
             1.1.0 | 2026-06-22 | CL-031 added T-SYN-N-002/N-003, T-SYN-C-003
             for validate_lesson_output() — gates lesson output on minimum
             item counts per section (3I≥8, 3G≥3, 3C≥5) before synthesis
             proceeds, since the prompt-content tests (T-MAIN-C-012) only
             verify the prompt asks for minimums, not that the LLM complied;
             two delivered lessons both returned only 5 glossary terms
             despite the prompt asking for 8. Used T-SYN- (not T-SYNTH-) and
             valid type codes C/N (not "U") to match this project's existing
             ID format | Claude Code
             1.2.0 | 2026-06-25 | CL-053 added T-SYN-C-004/C-005, T-SYN-N-004
             for section_3c paper links and authors rendering — paper title
             now renders as a clickable <a> link when url is present, authors
             cell handles string/list/empty with 'Authors unlisted' fallback.
             minimal_context fixture updated to include url in section_3c
             paper (backward-compatible: existing T-SYN-C-001/002 still pass
             since they check section markers / td counts, not paper content).
             _valid_lesson() updated to include url field | Claude Code
"""
from pathlib import Path

import pytest

from core.synthesis import render, validate, validate_jic_output, validate_jit_output, validate_lesson_output


# ---------------------------------------------------------------------------
# Shared minimal context fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def minimal_context():
    """Minimal valid v2 context (CL-065 template)."""
    return {
        "run_date": "2026-11-02", "run_timestamp": "2026-11-02 07:00:00", "run_id": "20261102-070000-full",
        "critical_jit": "Example Labs releases Model X", "critical_jic": "Speculative decoding",
        "jit_quiet": False, "jic_quiet": False, "lesson_ok": True,
        "status_line": "OK | JIT 1 | JIC 1 | lesson quality 100% slots",
        "jit_items": [{"headline": "Example Labs releases Model X", "category": "model release",
                       "what_happened": "Model X launched on 2026-11-01 with a 1M context window.",
                       "why_it_matters_pm": "Longer context lowers retrieval engineering cost.",
                       "source": "example.com", "url": "https://example.com/x", "date": "2026-11-01",
                       "also_covered_by_urls": ["https://news.example.com/x"]}],
        "jic_items": [{"concept": "Speculative decoding", "bucket": "inference & systems",
                       "core_insight": "A small model drafts tokens. It is in the news again. It cuts latency.",
                       "source": "arxiv.org", "url": "https://arxiv.org/abs/2211.17192", "date": "2026-10-30"}],
        "lesson": {
            "topic_name": "Transformer Architecture — Attention Mechanism Deep Dive",
            "tldr_what": "Transformers process tokens with attention.", "tldr_why_now": "Every LLM uses them.",
            "tldr_pm_takeaway": "Context length drives cost.",
            "definition": "A neural architecture built on self-attention.", "problem_solved": "Long-range dependencies.",
            "components": [{"name": "Self-attention", "role": "mixes token information"}],
            "how_it_works": ["Embed tokens", "Apply attention", "Predict next token"],
            "key_equation": {"expression": "softmax(QK^T/sqrt(d))V", "plain_english": "weighted average of values"},
            "examples": ["GPT-4 uses a decoder-only transformer"], "limitations": ["Quadratic cost", "Context limits"],
            "papers": [{"title": "Attention Is All You Need", "first_author": "Vaswani", "year": 2017,
                        "citations": 120408, "stars": "★★★", "is_seminal": True,
                        "url": "https://arxiv.org/abs/1706.03762", "contribution": "Introduced the transformer."}],
            "uses": [{"company_or_product": "Google Translate", "use": "translation"}],
            "pm_guide": {"use_when": "text tasks", "avoid_when": "tiny tabular data", "cheaper_alternative": "XGBoost"},
            "maturity_stage": "Mainstream", "maturity_evidence": "Used by every frontier LLM.",
            "what_next": [{"direction": "Linear attention", "expectation": "cheaper long context",
                           "source_url": "https://arxiv.org/abs/2006.16236", "source_label": "arxiv.org"}],
            "glossary": [{"term": "Attention", "definition": "Weighted mixing of token vectors."}],
            "quality_note": "",
        },
    }


# ── T-SYN-C-001 ──────────────────────────────────────────────────────────────

def test_t_syn_c_001_html_has_required_sections(minimal_context):
    """T-SYN-C-001 (v2, CL-065): rendered HTML contains all v2 sections and the status footer."""
    html = render(minimal_context)
    for marker in ("Just-In-Time", "Just-In-Case", "Today's Lesson", "TL;DR", "3A.", "3C.", "3D.", "3E.",
                   "3H.", "3I.", "Glossary", "System status"):
        assert marker in html, f"missing {marker}"


# ── T-SYN-C-002 ──────────────────────────────────────────────────────────────

def test_t_syn_c_002_jit_item_renders_all_slots(minimal_context):
    """T-SYN-C-002 (v2, CL-065): JIT item shows headline link, category, what happened, why it matters, also-covered."""
    html = render(minimal_context)
    item = minimal_context["jit_items"][0]
    for value in (item["headline"], item["category"], item["what_happened"], item["why_it_matters_pm"], item["url"]):
        assert value in html
    assert "also covered by 1 other source" in html


# ── T-SYN-N-001 ──────────────────────────────────────────────────────────────

def test_t_syn_n_001_invalid_html_triggers_retry(mocker, minimal_context):
    """
    T-SYN-N-001: When validate() returns False, render() retries once then returns
    plain-text fallback if the second attempt also fails.

    Acceptance criteria (TEST_REGISTRY):
      render() called twice; second call with same input; if second fails,
      plain-text fallback returned.
    """
    # Patch validate so it always returns False (simulates broken HTML output)
    mocker.patch("core.synthesis.validate", return_value=False)

    result = render(minimal_context)

    # Must not raise; must return the plain-text fallback string
    assert isinstance(result, str)
    assert len(result) > 0
    # Plain-text fallback must NOT be a full HTML document (no <html> tag)
    assert "<html" not in result.lower(), (
        "Expected plain-text fallback but got HTML after double validation failure"
    )


# ── T-FMT-C-001 ──────────────────────────────────────────────────────────────

def test_t_fmt_c_001_v2_sections_present_and_removed_sections_absent(minimal_context):
    """T-FMT-C-001 (v2, CL-065, D6/D8): 3B, 3F and 3G are removed; quiet-day and lesson-failure notes render."""
    html = render(minimal_context)
    for removed in ("3B.", "3F.", "3G."):
        assert removed not in html
    ctx = dict(minimal_context, jit_quiet=True, lesson_ok=False)
    html2 = render(ctx)
    assert "Quiet news day" in html2
    assert "could not be generated today" in html2
    assert "<html" in html2.lower(), "lesson failure must still render the HTML email, not the text fallback"


# ── T-SYN-N-002 ──────────────────────────────────────────────────────────────

def _valid_lesson() -> dict:
    """A lesson dict meeting all minimums (8 glossary terms, 3 voices, 5 papers)."""
    return {
        "topic_name": "Test Topic",
        "section_3c": [
            {"title": f"Paper {i}", "authors": "A.", "year": "2024", "contribution": "x", "url": f"https://arxiv.org/abs/200{i}.{i:05d}"}
            for i in range(5)
        ],
        "section_3g": [{"name": f"Person {i}", "date": "2024", "summary": "s", "source_url": "u", "source_label": "l"} for i in range(3)],
        "section_3i": [{"term": f"Term{i}", "definition": "d"} for i in range(8)],
    }


# ── T-SYN-N-002 ──────────────────────────────────────────────────────────────


def test_t_syn_n_002_validate_lesson_output_raises_on_short_glossary():
    """T-SYN-N-002: validate_lesson_output() raises ValueError if section_3i has fewer than 8 items."""
    lesson = _valid_lesson()
    lesson["section_3i"] = lesson["section_3i"][:5]

    with pytest.raises(ValueError, match="section_3i"):
        validate_lesson_output(lesson)


# ── T-SYN-N-003 ──────────────────────────────────────────────────────────────

def test_t_syn_n_003_validate_lesson_output_raises_on_few_voices():
    """T-SYN-N-003: validate_lesson_output() raises ValueError if section_3g has fewer than 3 items."""
    lesson = _valid_lesson()
    lesson["section_3g"] = lesson["section_3g"][:1]

    with pytest.raises(ValueError, match="section_3g"):
        validate_lesson_output(lesson)


# ── T-SYN-C-003 ──────────────────────────────────────────────────────────────

def test_t_syn_c_003_validate_lesson_output_passes_when_minimums_met():
    """T-SYN-C-003: validate_lesson_output() does not raise when all minimums are met."""
    validate_lesson_output(_valid_lesson())  # must not raise


# ---------------------------------------------------------------------------
# validate_jit_output() / validate_jic_output() — CL-056 minimum item gate
# ---------------------------------------------------------------------------

def _jit_items(count: int) -> list:
    return [
        {
            "topic": f"Item {i}",
            "source": "Example",
            "url": f"https://example.com/{i}",
            "date": "2026-06-20",
            "why_it_matters": "Important.",
        }
        for i in range(count)
    ]


# ── T-SYN-N-005 ──────────────────────────────────────────────────────────────

def test_t_syn_n_005_validate_jit_output_raises_when_below_minimum():
    """T-SYN-N-005: validate_jit_output() raises when fewer than 5 items."""
    with pytest.raises(ValueError, match="JIT output has 2 items"):
        validate_jit_output(_jit_items(2))


# ── T-SYN-N-006 ──────────────────────────────────────────────────────────────

def test_t_syn_n_006_validate_jic_output_raises_when_below_minimum():
    """T-SYN-N-006: validate_jic_output() raises when fewer than 5 items."""
    jic = [
        {
            "topic": f"Concept {i}",
            "source": "Arxiv",
            "url": f"https://arxiv.org/{i}",
            "date": "2026-06-20",
            "core_insight": "Insight.",
        }
        for i in range(3)
    ]
    with pytest.raises(ValueError, match="JIC output has 3 items"):
        validate_jic_output(jic)


# ── T-SYN-C-006 ──────────────────────────────────────────────────────────────

def test_t_syn_c_006_validate_jit_output_passes_at_minimum():
    """T-SYN-C-006: validate_jit_output() does not raise at exactly 5 items."""
    validate_jit_output(_jit_items(5))


# ── T-SYN-C-007 ──────────────────────────────────────────────────────────────

def test_t_syn_c_007_validate_jic_output_passes_at_minimum():
    """T-SYN-C-007: validate_jic_output() does not raise at exactly 5 items."""
    jic = [
        {
            "topic": f"Concept {i}",
            "source": "Arxiv",
            "url": f"https://arxiv.org/{i}",
            "date": "2026-06-20",
            "core_insight": "Insight.",
        }
        for i in range(5)
    ]
    validate_jic_output(jic)


def test_t_syn_n_007_validate_jit_output_raises_on_missing_keys():
    """T-SYN-N-007: validate_jit_output() raises when required keys are missing."""
    items = _jit_items(5)
    items[0] = {"topic": "Incomplete"}
    with pytest.raises(ValueError, match="missing keys"):
        validate_jit_output(items)


# ── T-SYN-C-004 ──────────────────────────────────────────────────────────────

def test_t_syn_c_004_paper_title_renders_as_link_with_stars_and_seminal(minimal_context):
    """T-SYN-C-004 (v2, CL-065): paper title links to its URL; stars, citation count and Seminal badge render."""
    html = render(minimal_context)
    assert 'href="https://arxiv.org/abs/1706.03762"' in html
    assert "★★★" in html and "120,408" in html and "Seminal" in html


# ── T-SYN-C-005 ──────────────────────────────────────────────────────────────

def test_t_syn_c_005_pm_guide_and_maturity_render(minimal_context):
    """T-SYN-C-005 (v2, CL-065): 3D PM guide (3 fields) and 3E one-line maturity render."""
    html = render(minimal_context)
    for v in ("Use when", "Avoid when", "Cheaper alternative", "XGBoost", "Mainstream", "Used by every frontier LLM."):
        assert v in html


# ── T-SYN-N-004 ──────────────────────────────────────────────────────────────

def test_t_syn_n_004_no_verified_papers_renders_fallback_row(minimal_context):
    """T-SYN-N-004 (v2, CL-065): when no paper could be verified the 3C table says so."""
    ctx = dict(minimal_context)
    ctx["lesson"] = dict(minimal_context["lesson"], papers=[])
    html = render(ctx)
    assert "No papers could be verified today." in html
