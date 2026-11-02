"""
MODULE: test_output_normalize.py
PURPOSE: CL-059 output field normalization tests
"""
import json

import pytest

from core.output_normalize import (
    _normalize_jic_item,
    _normalize_jit_item,
    normalize_agent_json_array,
    parse_and_normalize_agent_output,
)
from core.synthesis import validate_jic_output, validate_jit_output


# June 27, 2026 — OpenRouter Nemotron returned title/url/date instead of schema keys
NEMOTRON_JIC_FIXTURE = [
    {
        "title": "Mixture of Experts Scaling Laws",
        "url": "https://arxiv.org/abs/2401.04088",
        "date": "2026-06-25",
    },
    {
        "title": "Constitutional AI for Alignment",
        "url": "https://anthropic.com/research/constitutional-ai",
        "date": "2026-06-24",
    },
    {
        "title": "Gemini 2.5 Flash Tool Use",
        "url": "https://deepmind.google/research/gemini-tool-use",
        "date": "2026-06-23",
    },
    {
        "title": "RAG Evaluation Benchmarks",
        "url": "https://arxiv.org/abs/2406.01234",
        "date": "2026-06-22",
    },
    {
        "title": "Agentic Retrieval Loops",
        "url": "https://openai.com/research/agentic-retrieval",
        "date": "2026-06-21",
    },
]


def test_t_main_c_045_normalize_jit_maps_title_and_summary():
    """T-MAIN-C-045: _normalize_jit_item maps title→topic and summary→why_it_matters."""
    raw = {
        "title": "OpenAI releases GPT-5",
        "url": "https://openai.com/blog/gpt-5",
        "date": "2026-06-27",
        "summary": "Major model release with improved reasoning.",
    }
    item = _normalize_jit_item(raw)
    assert item["topic"] == "OpenAI releases GPT-5"
    assert item["why_it_matters"] == "Major model release with improved reasoning."
    assert item["source"] == "openai.com"
    assert item["url"] == "https://openai.com/blog/gpt-5"


def test_t_main_c_046_normalize_jic_maps_title_and_summary():
    """T-MAIN-C-046: _normalize_jic_item maps title→topic and summary→core_insight."""
    raw = {
        "title": "Retrieval-Augmented Generation",
        "url": "https://arxiv.org/abs/2005.11401",
        "date": "2026-06-27",
        "summary": "Combines retrieval with generation for grounded answers.",
    }
    item = _normalize_jic_item(raw)
    assert item["topic"] == "Retrieval-Augmented Generation"
    assert item["core_insight"] == "Combines retrieval with generation for grounded answers."
    assert item["source"] == "arxiv.org"


def test_t_main_c_047_nemotron_fixture_passes_jic_validation():
    """T-MAIN-C-047: June 27 Nemotron title/url/date fixture normalizes to valid JIC."""
    normalized = normalize_agent_json_array(NEMOTRON_JIC_FIXTURE, "jic")
    assert len(normalized) == 5
    validate_jic_output(normalized)


# T-MAIN-N-035 retired in CL-065: _gap_fill_items() removed with main.py v1
# (gap-fill replaced by the registry query plan in core/news.py; see TEST_REGISTRY).


def test_t_main_c_048_parse_and_normalize_agent_output():
    """T-MAIN-C-048: parse_and_normalize_agent_output handles fenced Nemotron JSON."""
    raw = "```json\n" + json.dumps(NEMOTRON_JIC_FIXTURE) + "\n```"
    items = parse_and_normalize_agent_output(raw, "jic")
    assert len(items) == 5
    validate_jic_output(items)


def test_t_norm_n_001_drops_rows_without_url():
    """T-NORM-N-001: rows missing url after normalization are dropped."""
    items = normalize_agent_json_array(
        [{"title": "No URL item", "date": "2026-06-27", "summary": "text"}],
        "jit",
    )
    assert items == []


def test_t_norm_c_001_jit_array_dedupes_urls():
    """T-NORM-C-001: normalize_agent_json_array dedupes by url."""
    raw = [
        {"topic": "A", "source": "X", "url": "https://example.com/a", "date": "2026-06-27", "why_it_matters": "One."},
        {"topic": "B", "source": "X", "url": "https://example.com/a", "date": "2026-06-27", "why_it_matters": "Dup."},
    ]
    items = normalize_agent_json_array(raw, "jit")
    assert len(items) == 1
