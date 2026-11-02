"""
MODULE: output_normalize.py
PURPOSE: Normalize LLM JIT/JIC JSON output across provider field-name variants
INPUTS: raw dict items or JSON array strings from agent/LLM responses
OUTPUTS: schema-aligned item dicts; filtered valid lists
DEPENDENCIES: tools.search.domain_from_url, core.synthesis validation constants
RULE REFERENCES: DEV-I-001 (deterministic field mapping over re-prompting)
CHANGE LOG: 1.0.0 | 2026-06-27 | CL-059: map title→topic, summary→core_insight/
            why_it_matters; derive source from URL; post-parse array normalization
            for Nemotron/OpenRouter/Mistral/Gemini field drift | Claude Code
"""
import json
import logging
import re
from typing import Literal

from core.synthesis import JIT_JIC_MIN_ITEMS, _JIC_REQUIRED_KEYS, _JIT_REQUIRED_KEYS
from tools.search import domain_from_url

logger = logging.getLogger(__name__)

Section = Literal["jit", "jic"]

_JIT_INSIGHT_KEYS = (
    "why_it_matters",
    "why_it_matter",
    "why_it_is_important",
    "summary",
    "snippet",
    "description",
    "content",
    "insight",
    "core_insight",
    "text",
    "body",
)
_JIC_INSIGHT_KEYS = (
    "core_insight",
    "core_insights",
    "insight",
    "summary",
    "snippet",
    "description",
    "content",
    "why_it_matters",
    "text",
    "body",
)
_TOPIC_KEYS = ("topic", "title", "headline", "name", "subject")
_URL_KEYS = ("url", "link", "href", "source_url", "article_url")
_DATE_KEYS = ("date", "published", "published_date", "pub_date", "timestamp")
_SOURCE_KEYS = ("source", "publisher", "site", "domain", "source_name", "provider")


def _first_str(item: dict, keys: tuple[str, ...]) -> str:
    """Return the first non-empty string value for any key in keys."""
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _normalize_jit_item(item: dict) -> dict:
    """
    Map provider-specific JIT field names to the canonical schema.

    Common drift: title/url/date instead of topic/source/url/date/why_it_matters
    (confirmed: OpenRouter Nemotron, 2026-06-27 JIC failure).
    """
    if not isinstance(item, dict):
        return {}
    url = _first_str(item, _URL_KEYS)
    topic = _first_str(item, _TOPIC_KEYS) or "AI news item"
    source = _first_str(item, _SOURCE_KEYS) or domain_from_url(url) or "Web"
    date = _first_str(item, _DATE_KEYS)
    insight = _first_str(item, _JIT_INSIGHT_KEYS) or "See linked article for details."
    return {
        "topic": topic[:120],
        "source": source[:120],
        "url": url,
        "date": date,
        "why_it_matters": insight[:600],
    }


def _normalize_jic_item(item: dict) -> dict:
    """Map provider-specific JIC field names to the canonical schema."""
    if not isinstance(item, dict):
        return {}
    url = _first_str(item, _URL_KEYS)
    topic = _first_str(item, _TOPIC_KEYS) or "AI concept"
    source = _first_str(item, _SOURCE_KEYS) or domain_from_url(url) or "Web"
    date = _first_str(item, _DATE_KEYS)
    insight = _first_str(item, _JIC_INSIGHT_KEYS) or "See linked article for details."
    return {
        "topic": topic[:120],
        "source": source[:120],
        "url": url,
        "date": date,
        "core_insight": insight[:600],
    }


def _item_is_valid(item: dict, section: Section) -> bool:
    """Return True when normalized item has all required non-empty keys."""
    required = _JIT_REQUIRED_KEYS if section == "jit" else _JIC_REQUIRED_KEYS
    return all(isinstance(item.get(key), str) and item.get(key, "").strip() for key in required)


def _normalize_item(item: dict, section: Section) -> dict:
    if section == "jit":
        return _normalize_jit_item(item)
    return _normalize_jic_item(item)


def normalize_agent_json_array(items: list, section: Section) -> list[dict]:
    """
    Normalize and dedupe a parsed JSON array; drop rows that still lack required keys.

    Called immediately after _parse_agent_json() in main.py.
    """
    if not isinstance(items, list):
        return []
    seen_urls: set[str] = set()
    normalized: list[dict] = []
    for raw in items:
        item = _normalize_item(raw, section)
        if not _item_is_valid(item, section):
            logger.debug(
                f"{section.upper()} row dropped after normalization — "
                f"missing required keys in {raw!r}"
            )
            continue
        url = item.get("url", "")
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        normalized.append(item)
    return normalized


def parse_and_normalize_agent_output(raw: str, section: Section) -> list[dict]:
    """Parse tolerant JSON array text, then normalize items (orchestration guard helper)."""
    parsed = _coerce_json_array(raw)
    return normalize_agent_json_array(parsed, section)


def _coerce_json_array(raw: str) -> list:
    """Minimal JSON array extraction — mirrors main._parse_agent_json stages."""
    if not raw or not isinstance(raw, str):
        return []
    stripped = raw.strip()
    for candidate in (stripped, _strip_fences(stripped)):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group())
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    return []


def _strip_fences(text: str) -> str:
    """Remove markdown code fences from agent output."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        inner = lines[1:]
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        return "\n".join(inner).strip()
    return stripped


def count_valid_items(items: list, section: Section) -> int:
    """Count items that pass required-key validation after normalization."""
    return len(normalize_agent_json_array(items, section))


def section_from_run_name(run_name: str) -> Section | None:
    """Infer jit/jic from LangSmith run_name."""
    lowered = (run_name or "").lower()
    if "jit" in lowered:
        return "jit"
    if "jic" in lowered:
        return "jic"
    return None


def needs_gap_fill(items: list, section: Section) -> bool:
    """Return True when normalized items fail validate_* (count or schema)."""
    normalized = normalize_agent_json_array(items, section)
    if len(normalized) < JIT_JIC_MIN_ITEMS:
        return True
    return not all(_item_is_valid(item, section) for item in normalized[:JIT_JIC_MIN_ITEMS])
