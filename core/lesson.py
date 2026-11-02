"""
MODULE: lesson.py
PURPOSE: Daily JIC lesson v2 (CL-065; spec section 8, decisions D6-D8).
         Fixed slots for every topic: TL;DR, 3A, 3C (max 5 verified papers with
         citation stars), 3D, 3E (1-2 lines), 3H, 3I. Grounded by 4 registry-
         driven searches. Code checks every slot (counts, word caps, required
         concepts from the topic subtitle, glossary terms used in text, URLs);
         one targeted repair call on failure; quality score logged.
INPUTS: topic string
OUTPUTS: dict {lesson, ok, quality, failures}
DEPENDENCIES: core.gateway, core.citations, tools.search
RULE REFERENCES: D6-D8, R-003
CHANGE LOG: 1.0.0 | 2026-11-01 | CL-065 initial implementation | Claude Code
            1.1.0 | 2026-11-01 | CL-071: searches use the topic's short title; OpenAlex scored
            shortlist goes into the prompt; papers selected by PaperScore; first-draft
            failures kept in lesson_quality.json | Claude Code
"""
import json
import logging
import re

import requests

from core import run_logger
from core.citations import shortlist, verify_papers
from core.gateway import llm_call
from core.settings import load_registry, render_prompt, section_config, tier_domains, tier_of
from tools.search import domain_from_url, search_sources

logger = logging.getLogger(__name__)

STAGES = ["Research", "Emerging", "Early production", "Mainstream", "Commoditized"]
_STOP = set("a an the of and or for to in on with by vs its what is are not how when why use using deep dive explained overview".split())

_STR = {"type": "string"}
LESSON_SCHEMA = {
    "type": "object",
    "required": ["tldr_what", "tldr_why_now", "tldr_pm_takeaway", "definition", "problem_solved", "components",
                 "how_it_works", "key_equation", "examples", "limitations", "papers", "uses", "pm_guide",
                 "maturity_stage", "maturity_evidence", "what_next", "glossary"],
    "properties": {
        "tldr_what": _STR, "tldr_why_now": _STR, "tldr_pm_takeaway": _STR,
        "definition": _STR, "problem_solved": _STR,
        "components": {"type": "array", "items": {"type": "object", "required": ["name", "role"],
                                                  "properties": {"name": _STR, "role": _STR}}},
        "how_it_works": {"type": "array", "items": _STR},
        "key_equation": {"type": "object", "required": ["expression", "plain_english"],
                         "properties": {"expression": _STR, "plain_english": _STR}},
        "examples": {"type": "array", "items": _STR},
        "limitations": {"type": "array", "items": _STR},
        "papers": {"type": "array", "items": {"type": "object",
                   "required": ["title", "first_author", "year", "arxiv_id", "doi", "contribution", "is_seminal"],
                   "properties": {"title": _STR, "first_author": _STR, "year": {"type": "integer"}, "arxiv_id": _STR,
                                  "doi": _STR, "contribution": _STR, "is_seminal": {"type": "boolean"}}}},
        "uses": {"type": "array", "items": {"type": "object", "required": ["company_or_product", "use"],
                                            "properties": {"company_or_product": _STR, "use": _STR}}},
        "pm_guide": {"type": "object", "required": ["use_when", "avoid_when", "cheaper_alternative"],
                     "properties": {"use_when": _STR, "avoid_when": _STR, "cheaper_alternative": _STR}},
        "maturity_stage": {"type": "string", "enum": STAGES},
        "maturity_evidence": _STR,
        "what_next": {"type": "array", "items": {"type": "object", "required": ["direction", "expectation", "source_url"],
                                                 "properties": {"direction": _STR, "expectation": _STR, "source_url": _STR}}},
        "glossary": {"type": "array", "items": {"type": "object", "required": ["term", "definition"],
                                                "properties": {"term": _STR, "definition": _STR}}},
    },
}


def required_terms(topic: str) -> list:
    """Sub-concepts listed after the dash in the topic title (automatic completeness check)."""
    parts = re.split(r"\s+[—–-]\s+|:\s+", topic, maxsplit=1)
    tail = parts[1] if len(parts) > 1 else ""
    terms = [t.strip(" .") for t in re.split(r",\s*(?:and\s+)?|\s+and\s+", tail) if t.strip(" .")]
    return [t for t in terms if t]


def short_title(topic: str) -> str:
    """Topic text before the dash/colon ('What AI Is — Computational Rationality, ...' -> 'What AI Is')."""
    return re.split(r"\s+[—–-]\s+|:\s+", topic, maxsplit=1)[0].strip()


def _term_tokens(term: str) -> list:
    return [t for t in re.findall(r"[A-Za-z0-9][A-Za-z0-9\-\+/\.]*", term) if t.lower() not in _STOP]


def term_covered(term: str, text: str) -> bool:
    low = text.lower()
    toks = _term_tokens(term)
    return bool(toks) and all(t.lower() in low for t in toks)


def _words(s) -> int:
    return len(str(s or "").split())


def _sentences(s) -> int:
    return len([x for x in re.split(r"(?<=[.!?])\s+", str(s or "").strip()) if x])


def lesson_text(lesson: dict) -> str:
    return json.dumps(lesson, ensure_ascii=False)


def check_slots(lesson: dict, topic: str) -> tuple[list, dict]:
    """Deterministic slot checks. Returns (failures, stats)."""
    f = []
    tldr = " ".join(lesson.get(k, "") for k in ("tldr_what", "tldr_why_now", "tldr_pm_takeaway"))
    if not all(lesson.get(k) for k in ("tldr_what", "tldr_why_now", "tldr_pm_takeaway")):
        f.append("TL;DR: all 3 sentences required")
    if _words(tldr) > 75:
        f.append(f"TL;DR: {_words(tldr)} words (max 75)")
    if not lesson.get("definition") or _words(lesson.get("definition")) > 30:
        f.append("3A definition: one sentence, max 30 words")
    comps = lesson.get("components") or []
    if not 3 <= len(comps) <= 5:
        f.append(f"3A components: {len(comps)} (need 3-5)")
    if any(_words(c.get("role")) > 15 for c in comps):
        f.append("3A components: role max 15 words")
    steps = lesson.get("how_it_works") or []
    if not 3 <= len(steps) <= 6:
        f.append(f"3A how_it_works: {len(steps)} steps (need 3-6)")
    eq = lesson.get("key_equation") or {}
    if not eq.get("expression") or not eq.get("plain_english"):
        f.append("3A key_equation: expression and plain_english required (or 'none' + reason)")
    ex = lesson.get("examples") or []
    if not 1 <= len(ex) <= 2:
        f.append(f"3A examples: {len(ex)} (need 1-2)")
    if any(not re.search(r"\d|[A-Z][a-z]+[A-Z]|[A-Z]{2,}|[A-Z][a-z]{2,}", e) for e in ex):
        f.append("3A examples: each needs a number or named product/company")
    if len(lesson.get("limitations") or []) != 2:
        f.append("3A limitations: exactly 2")
    uses = lesson.get("uses") or []
    if len(uses) != 3:
        f.append(f"3D uses: {len(uses)} (need exactly 3)")
    pg = lesson.get("pm_guide") or {}
    if not all(pg.get(k) for k in ("use_when", "avoid_when", "cheaper_alternative")):
        f.append("3D pm_guide: use_when, avoid_when, cheaper_alternative required")
    if lesson.get("maturity_stage") not in STAGES:
        f.append("3E stage: must be one of " + ", ".join(STAGES))
    if _words(lesson.get("maturity_evidence")) > 25 or _sentences(lesson.get("maturity_evidence")) > 2:
        f.append("3E evidence: one sentence, max 25 words")
    nxt = lesson.get("what_next") or []
    if len(nxt) != 3:
        f.append(f"3H what_next: {len(nxt)} (need exactly 3)")
    gloss = lesson.get("glossary") or []
    if not 8 <= len(gloss) <= 12:
        f.append(f"3I glossary: {len(gloss)} terms (need 8-12)")
    body = lesson_text({k: v for k, v in lesson.items() if k != "glossary"}).lower()
    unused = [g.get("term") for g in gloss if g.get("term") and g["term"].lower() not in body]
    if len(unused) > 2:
        f.append(f"3I glossary: terms not used in lesson text: {unused[:5]}")
    req = required_terms(topic)
    text = lesson_text(lesson)
    missing = [t for t in req if not term_covered(t, text)]
    if missing:
        f.append(f"Completeness: required concepts missing: {missing}")
    stats = {"required_terms": req, "missing_terms": missing,
             "completeness_pct": round(100 * (len(req) - len(missing)) / len(req), 1) if req else 100.0}
    return f, stats


def _ground(topic: str) -> dict:
    cfg = section_config("lesson")["grounding"]
    blocks = {}
    for name, g in cfg.items():
        results = search_sources(g["query"].format(topic=topic, short=short_title(topic)), n=g.get("n", 6), days=g.get("window_days"),
                                 include_domains=tier_domains(g["tiers"]), topic="general",
                                 require_date=bool(g.get("window_days")), label=f"lesson-{name}")
        blocks[name] = results
    return blocks


def _fmt_shortlist(cands: list) -> str:
    lines = []
    for c in cands:
        ident = f"doi {c.get('doi')}" if c.get("doi") else (c.get("openalex_id") or "")
        lines.append(f"- {c.get('verified_title', '')[:150]} ({c.get('year')}) | {c.get('citations') or 0} citations | "
                     f"{c.get('venue') or 'preprint'} | {ident} | score {c.get('score')}")
    return "\n".join(lines)


def _fmt(results: list) -> str:
    lines = [f"- {r.get('title', '')[:150]} | {r.get('url', '')} | {r.get('date', '')}" for r in results if r.get("url")]
    return "\n".join(lines) if lines else "(none retrieved)"


def _url_ok(url: str) -> bool:
    try:
        r = requests.head(url, allow_redirects=True, timeout=8)
        if r.status_code in (403, 405) or r.status_code >= 500:
            r = requests.get(url, allow_redirects=True, timeout=8, stream=True)
        return r.status_code < 400
    except requests.RequestException:
        return False


def _finalise_what_next(items: list, grounding: dict) -> tuple[list, dict]:
    registry = load_registry()
    retrieved = {r.get("url") for block in grounding.values() for r in block}
    out, ok = [], 0
    for it in items:
        url = it.get("source_url", "")
        good = bool(url) and (url in retrieved or (tier_of(url, registry) not in (None, "blocked") and _url_ok(url)))
        ok += good
        out.append({**it, "source_url": url if good else "", "source_label": domain_from_url(url) if good else ""})
    return out, {"what_next_sources_ok": ok, "what_next_total": len(items)}


def generate(topic: str) -> dict:
    """Generate, verify and score today's lesson. Never raises."""
    ctx = run_logger.current()
    try:
        grounding = _ground(topic)
        max_papers = section_config("lesson").get("max_papers", 5)
        picked, pool = shortlist(topic, short_title(topic))
        if ctx:
            ctx.save_json("outputs/paper_shortlist.json", [{k: c.get(k) for k in (
                "verified_title", "year", "citations", "venue", "relevance", "score", "score_parts", "is_seminal",
                "grade", "grade_reason", "category_note", "keyword_overlap", "source_of_candidate")}
                for c in picked])
            ctx.save_json("outputs/paper_pool.json", [{k: c.get(k) for k in (
                "verified_title", "year", "citations", "category_note", "keyword_overlap", "grade", "grade_reason",
                "rejected_because", "source_of_candidate")} for c in pool])
        papers_block = ("OPTIONAL CANDIDATES (Computer Science, graded relevant; use only if directly about the topic):\n"
                        + _fmt_shortlist(picked) + "\n\nWEB RESULTS:\n" if picked else "") \
            + _fmt(grounding.get("papers", []))
        prompt = render_prompt("lesson", topic=topic, required_terms="; ".join(required_terms(topic)) or "none",
                               papers=papers_block, explainers=_fmt(grounding.get("explainers", [])),
                               industry=_fmt(grounding.get("industry", [])), future=_fmt(grounding.get("future", [])),
                               max_papers=max_papers, max_others=max_papers - 1)
        if ctx:
            ctx.save_text("inputs/prompt_lesson.md", prompt)
        lesson = llm_call(prompt, schema=LESSON_SCHEMA, stage="lesson", schema_name="lesson")["parsed"] or {}
        if ctx:
            ctx.save_json("outputs/lesson_raw.json", lesson)
        failures, stats = check_slots(lesson, topic)
        first_draft_failures = list(failures)
        repaired = False
        if failures:
            repair = render_prompt("lesson_repair", failures="\n".join(f"- {x}" for x in failures),
                                   lesson_json=json.dumps(lesson, ensure_ascii=False))
            try:
                fixed = llm_call(prompt + "\n\n" + repair, schema=LESSON_SCHEMA, stage="lesson-repair",
                                 schema_name="lesson")["parsed"] or {}
                f2, s2 = check_slots(fixed, topic)
                if len(f2) < len(failures):
                    lesson, failures, stats, repaired = fixed, f2, s2, True
            except Exception as exc:  # noqa: BLE001
                run_logger.log_exception("lesson-repair", exc, severity="WARNING", action_taken="keep first draft")
        prior = {c.get("openalex_id"): c for c in pool if c.get("grade") is not None}
        papers, pstats = verify_papers(lesson.get("papers", []), max_papers=max_papers, topic=topic, prior_grades=prior)
        lesson["papers"] = papers
        lesson["what_next"], wstats = _finalise_what_next(lesson.get("what_next", []), grounding)
        lesson["topic_name"] = topic
        slot_checks = 17
        quality = {
            "slots_pass_pct": round(100 * (slot_checks - min(len(failures), slot_checks)) / slot_checks, 1),
            "completeness_pct": stats["completeness_pct"], "missing_terms": stats["missing_terms"],
            "papers_verified": pstats["verified"], "papers_requested": pstats["requested"],
            "papers_dropped": pstats["dropped_titles"], "papers_rejected": pstats.get("rejected", []),
            "paper_scores": pstats.get("scores", []), "shortlist_size": len(picked),
            **wstats, "repaired": repaired, "first_draft_failures": first_draft_failures, "failures": failures,
        }
        ok = bool(lesson.get("definition")) and len(lesson.get("glossary") or []) >= 5
        lesson["quality_note"] = "" if not failures and pstats["verified"] >= 3 else (
            "Quality note: " + "; ".join(failures[:3]) + (f"; only {pstats['verified']} papers verified"
                                                          if pstats["verified"] < 3 else ""))
        if ctx:
            ctx.save_json("outputs/lesson.json", lesson)
            ctx.save_json("outputs/lesson_quality.json", quality)
        return {"lesson": lesson, "ok": ok, "quality": quality, "failures": failures}
    except Exception as exc:  # noqa: BLE001
        run_logger.log_exception("lesson", exc, severity="ERROR", action_taken="lesson unavailable today")
        return {"lesson": {"topic_name": topic}, "ok": False, "quality": {"error": str(exc)[:200]},
                "failures": [str(exc)[:200]]}
