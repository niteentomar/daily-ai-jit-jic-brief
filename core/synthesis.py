"""
MODULE: synthesis.py
PURPOSE: Jinja2 rendering of config/email_template.html + HTML schema validation
INPUTS: context dict (jit_items, jic_items, lesson, run_date, etc.)
OUTPUTS: validated HTML string; plain-text fallback on double validation failure
DEPENDENCIES: jinja2
RULE REFERENCES: R-003 (retry-once on HTML validation failure)
CHANGE LOG: 1.0.0 | 2026-06-17 | TC-005 initial implementation | Claude Code
            1.1.0 | 2026-06-22 | CL-031 added validate_lesson_output() — the
            lesson prompt asks for minimum item counts per section (5 papers,
            3 voices, 8 glossary terms), but nothing checked the LLM actually
            complied; two delivered lessons both returned only 5 glossary
            terms. Called from main.py's run_daily_pipeline() right after the
            lesson agent returns, so a truncated lesson fails the pipeline
            loudly instead of being silently delivered | Claude Code
            1.2.0 | 2026-06-26 | CL-056 added validate_jit_output() and
            validate_jic_output() — minimum 5 items before delivery; gap-fill
            may still leave partial output (graceful degrade) | Claude Code
            2.0.0 | 2026-11-01 | CL-065: template v2 markers (TL;DR, 3A, 3C, 3D,
            3E, 3H, 3I; 3B/3F/3G removed, D6/D8). Lesson markers only required
            when the lesson succeeded; "System status" footer always required | Claude Code
"""
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "config"
_TEMPLATE_NAME = "email_template.html"

# All markers must be present in valid rendered output (T-SYN-C-001, T-FMT-C-001)
JIT_JIC_MIN_ITEMS = 5

_JIT_REQUIRED_KEYS = ("topic", "source", "url", "date", "why_it_matters")
_JIC_REQUIRED_KEYS = ("topic", "source", "url", "date", "core_insight")

_REQUIRED_MARKERS = [
    "Just-In-Time",
    "Just-In-Case",
    "Today's Lesson",
    "System status",
]
_LESSON_MARKERS = ["TL;DR", "3A", "3C", "3D", "3E", "3H", "3I", "Glossary"]


def render(context: dict) -> str:
    """
    Render email_template.html with Jinja2 and validate the output.

    Retries once if validation fails (R-003). Returns a plain-text fallback
    string if the second attempt also fails — never raises.

    Args:
        context: Data dict with keys: run_date, critical_jit, critical_jic,
                 lesson_hook, jit_items, jic_items, lesson, run_timestamp,
                 model_used, topics_covered, pause_url.

    Returns:
        Validated HTML string, or plain-text fallback on double failure.
    """
    lesson_ok = context.get("lesson_ok", True)
    html = _render_template(context)
    if validate(html, lesson_ok=lesson_ok):
        return html

    logger.warning("R-003: HTML validation failed — retrying synthesis once")
    html = _render_template(context)
    if validate(html, lesson_ok=lesson_ok):
        return html

    logger.error("R-003: HTML validation failed twice — returning plain-text fallback")
    return _plain_text_fallback(context)


def validate(html: str, lesson_ok: bool = True) -> bool:
    """
    Validate rendered HTML against the required output schema.

    Checks all required section markers (section headers, sub-section labels,
    Glossary) are present in the rendered string.

    Args:
        html: Rendered HTML string to validate.

    Returns:
        True if all required markers are present, False otherwise.
    """
    markers = _REQUIRED_MARKERS + (_LESSON_MARKERS if lesson_ok else [])
    return all(marker in html for marker in markers)


def validate_lesson_output(lesson: dict) -> None:
    """
    Raise ValueError if lesson output violates minimum content rules.

    The lesson prompt (main.py _run_lesson_agent) asks for minimum item
    counts per section, but the LLM doesn't always comply — this is a
    post-generation check, called by run_daily_pipeline() before synthesis
    proceeds, so a truncated lesson fails the pipeline loudly rather than
    being silently delivered.

    Args:
        lesson: Parsed lesson dict (section_3a ... section_3i).

    Raises:
        ValueError: naming every section that falls short of its minimum.
    """
    errors = []
    glossary = lesson.get("section_3i", [])
    if len(glossary) < 8:
        errors.append(
            f"section_3i has {len(glossary)} terms — minimum 8 required."
        )
    voices = lesson.get("section_3g", [])
    if len(voices) < 3:
        errors.append(
            f"section_3g has {len(voices)} voices — minimum 3 required."
        )
    papers = lesson.get("section_3c", [])
    if len(papers) < 5:
        errors.append(
            f"section_3c has {len(papers)} papers — minimum 5 required."
        )
    if errors:
        raise ValueError("Lesson output failed validation:\n" + "\n".join(errors))


def _validate_section_items(
    items: list, section: str, required_keys: tuple[str, ...]
) -> None:
    """Raise ValueError if count or required keys fall short of JIT_JIC_MIN_ITEMS."""
    errors = []
    if len(items) < JIT_JIC_MIN_ITEMS:
        errors.append(
            f"{section} output has {len(items)} items — "
            f"minimum {JIT_JIC_MIN_ITEMS} required."
        )
    for idx, item in enumerate(items[:JIT_JIC_MIN_ITEMS]):
        if not isinstance(item, dict):
            errors.append(f"{section} item {idx} is not a dict.")
            continue
        missing = [key for key in required_keys if not item.get(key)]
        if missing:
            errors.append(
                f"{section} item {idx} missing keys: {', '.join(missing)}."
            )
    if errors:
        raise ValueError(f"{section} output failed validation:\n" + "\n".join(errors))


def validate_jit_output(items: list) -> None:
    """
    Raise ValueError if JIT output has fewer than JIT_JIC_MIN_ITEMS entries
    or any of the first JIT_JIC_MIN_ITEMS rows lack required keys.

    Called from run_daily_pipeline() after the agent (and any gap-fill pass)
    so thin JIT sections trigger broader search before email send.
    """
    _validate_section_items(items, "JIT", _JIT_REQUIRED_KEYS)


def validate_jic_output(items: list) -> None:
    """
    Raise ValueError if JIC output has fewer than JIT_JIC_MIN_ITEMS entries
    or any of the first JIT_JIC_MIN_ITEMS rows lack required keys.

    Same gate as validate_jit_output() for the JIC section.
    """
    _validate_section_items(items, "JIC", _JIC_REQUIRED_KEYS)


def _render_template(context: dict) -> str:
    """Load config/email_template.html and render it with Jinja2."""
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=False,
    )
    template = env.get_template(_TEMPLATE_NAME)
    return template.render(**context)


def _plain_text_fallback(context: dict) -> str:
    """Return a plain-text digest when HTML rendering fails twice (R-003)."""
    lines = [
        f"Daily AI Learning Brief — {context.get('run_date', 'N/A')}",
        "",
        "JIT Topics:",
    ]
    for item in context.get("jit_items", []):
        lines.append(f"  - {item.get('headline') or item.get('topic', '')}: {item.get('what_happened') or item.get('why_it_matters', '')}")
    lines.append("")
    lines.append("JIC Topics:")
    for item in context.get("jic_items", []):
        lines.append(f"  - {item.get('concept') or item.get('topic', '')}: {item.get('core_insight', '')}")
    lesson = context.get("lesson", {})
    lines.append("")
    lines.append(f"Today's Lesson: {lesson.get('topic_name', 'N/A')}")
    return "\n".join(lines)
