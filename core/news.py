"""
MODULE: news.py
PURPOSE: JIT and JIC news sections v2 (CL-065; spec sections 3, 9, 10).
         Stage 1 (ReAct research): a tool-calling agent chooses searches; every
         result is captured by code from the tool calls (the agent's own text is
         ignored, so URLs cannot be invented). Stage 2 (editor): one structured-
         output call selects items from the captured candidates into fixed slots.
         Stage 3 (code): window/source checks, embedding de-dup against today's
         other sections and the news_ledger cooldown, coverage metrics.
INPUTS: section ('jit'|'jic'), lesson topic, db path, texts to avoid
OUTPUTS: dict {items, vectors, quiet, metrics}
DEPENDENCIES: core.tool_agent, core.gateway, core.dedupe, tools.search
RULE REFERENCES: R-001 (cooldown), D9 (no padding), D10/D15 (embedding de-dup), D11
CHANGE LOG: 1.0.0 | 2026-11-01 | CL-065 initial implementation | Claude Code
            1.1.0 | 2026-11-01 | CL-070: editor writes a story fingerprint (actors, object,
            event_type, keywords, key_number); items carry lead paragraph and source tier
            for duplicate detection v2 | Claude Code
            1.2.0 | 2026-11-02 | CL-073: when a better-tier source (J1/T1 first-party post) is in
            also_covered_by, it becomes the main link (dry run 2: 10% primary sources) | Claude Code
"""
import json
import logging
from datetime import date

from core import run_logger
from core.dedupe import _TIER_ORDER, dedupe_items, recent_ledger
from core.gateway import llm_call
from core.settings import (domain_matches, load_registry, load_settings, render_prompt, section_config,
                           tier_domains, tier_of, window_start)
from core.tool_agent import run_litellm_tool_loop
from core.tool_args import _coerce_tool_arg
from tools.search import domain_from_url, search_sources

logger = logging.getLogger(__name__)

MAX_SEARCHES = 6
MAX_CANDIDATES = 40
RESEARCH_MAX_ITER = 8
WORD_LIMITS = {"headline": 12, "what_happened": 30, "why_it_matters_pm": 30, "core_insight": 60}


_FINGERPRINT = {"type": "object", "required": ["actors", "object", "keywords", "key_number"], "properties": {
    "actors": {"type": "array", "items": {"type": "string"}},
    "object": {"type": "string"},
    "keywords": {"type": "array", "items": {"type": "string"}},
    "key_number": {"type": "string"}}}


def _schema(section: str, cfg: dict) -> dict:
    if section == "jit":
        props = {"candidate_id": {"type": "string"}, "headline": {"type": "string"},
                 "category": {"type": "string", "enum": cfg["categories"]},
                 "what_happened": {"type": "string"}, "why_it_matters_pm": {"type": "string"},
                 "also_covered_by": {"type": "array", "items": {"type": "string"}},
                 "fingerprint": _FINGERPRINT}
    else:
        props = {"candidate_id": {"type": "string"}, "concept": {"type": "string"},
                 "bucket": {"type": "string", "enum": cfg["buckets"]},
                 "core_insight": {"type": "string"},
                 "also_covered_by": {"type": "array", "items": {"type": "string"}},
                 "fingerprint": _FINGERPRINT}
    return {"type": "object", "required": ["items"], "properties": {
        "items": {"type": "array", "items": {"type": "object", "properties": props, "required": list(props)}}}}


def _make_search_tool(collector: list, section: str, cfg: dict, domains: list):
    from langchain_core.tools import Tool

    def _run(query):
        q = _coerce_tool_arg(query, ("query", "q", "search_query", "text"))
        if sum(1 for c in collector if c.get("_query") == "__count__") >= MAX_SEARCHES:
            return "Search limit reached. Reply DONE."
        collector.append({"_query": "__count__"})
        results = search_sources(q, n=8, days=cfg["window_days"], include_domains=domains,
                                 topic="news" if section == "jit" else "general", label=f"{section}-research")
        collector.extend(results)
        if not results:
            return "No results in the window from trusted sources. Try a different query."
        return "\n".join(f"- {r['title']} | {domain_from_url(r['url'])} | {r.get('date', '')}" for r in results[:8])

    return Tool(name="search", func=_run,
                description="Search trusted AI sources inside the date window. Pass a short plain-text query.")


def _research(section: str, cfg: dict, lesson_topic: str, domains: list) -> list:
    """Stage 1: ReAct agent searches; code captures results. Falls back to the registry query plan."""
    settings = load_settings()
    collector: list = []
    tool = _make_search_tool(collector, section, cfg, domains)
    groups = cfg["categories"] if section == "jit" else cfg["buckets"]
    prompt = render_prompt(f"{section}_research", today=date.today().isoformat(),
                           window_start=window_start(cfg["window_days"]), max_searches=MAX_SEARCHES,
                           categories="\n".join(f"- {g}" for g in groups), buckets="\n".join(f"- {g}" for g in groups))
    ctx = run_logger.current()
    if ctx:
        ctx.save_text(f"inputs/prompt_{section}_research.md", prompt)
    for model in settings.model_chain:
        try:
            run_litellm_tool_loop(model=model, tools=[tool], user_prompt=prompt, max_iter=RESEARCH_MAX_ITER,
                                  system_prompt="You are a careful research assistant. Use the search tool.",
                                  stage=f"{section}-research")
            break
        except Exception as exc:  # noqa: BLE001
            run_logger.log_exception(f"{section}-research", exc, model=model, action_taken="next model / query plan")
    results = [c for c in collector if "_query" not in c]
    if cfg.get("first_party_queries") and cfg.get("primary_tiers"):
        # CL-074: media dominate the news index (dry run 3: 28/40 candidates J3, 2 J1), so search first-party
        # company/lab posts directly; the editor can only prefer a source that is in the candidate list.
        fp_domains, first_party = tier_domains(cfg["primary_tiers"]), []
        for q in cfg["first_party_queries"]:
            first_party.extend(search_sources(q, n=8, days=cfg["window_days"], include_domains=fp_domains,
                                              topic="general", label=f"{section}-first-party"))
        results = first_party + results  # first, so the 40-candidate cap never cuts them
    if len({r["url"] for r in results}) < 8:
        logger.info(f"{section}: agent gathered {len(results)} results; running registry query plan")
        for q in cfg["query_plan"]:
            results.extend(search_sources(q, n=8, days=cfg["window_days"], include_domains=domains,
                                          topic="news" if section == "jit" else "general", label=f"{section}-plan"))
            if len({r["url"] for r in results}) >= 24:
                break
    return results


def _candidates(results: list, history_urls: set) -> list:
    seen, out = set(), []
    for r in results:
        url = r.get("url")
        if not url or url in seen or url in history_urls:
            continue
        seen.add(url)
        out.append({"id": f"C{len(out) + 1}", "title": r.get("title", "")[:200], "url": url,
                    "domain": domain_from_url(url), "date": r.get("date", ""),
                    "snippet": (r.get("summary") or "")[:300]})
        if len(out) >= MAX_CANDIDATES:
            break
    return out


def _words(text: str) -> int:
    return len((text or "").split())


def _metrics(section: str, items: list, cfg: dict, registry: dict, window: int) -> dict:
    key = "category" if section == "jit" else "bucket"
    groups = {}
    for it in items:
        groups[it.get(key)] = groups.get(it.get(key), 0) + 1
    tiers = [tier_of(it["url"], registry) for it in items]
    today = date.today()

    def _days_old(d):
        try:
            return (today - date.fromisoformat(str(d)[:10])).days
        except ValueError:
            return 10 ** 6
    in_window = sum(1 for it in items if it.get("date") and _days_old(it["date"]) <= window)
    over = {f: sum(1 for it in items if _words(it.get(f, "")) > lim) for f, lim in WORD_LIMITS.items()
            if any(f in it for it in items)}
    m = {"count": len(items), "groups_covered": len([g for g in groups if g]), "per_group": groups,
         "min_groups_target": cfg.get("min_categories") or cfg.get("min_buckets"),
         "dates_in_window_pct": round(100 * in_window / len(items), 1) if items else None,
         "word_limit_violations": over, "tiers": tiers}
    if section == "jit":
        m["primary_source_pct"] = round(100 * sum(1 for t in tiers if t in cfg["primary_tiers"]) / len(items), 1) if items else None
    else:
        m["media_items"] = sum(1 for t in tiers if t in cfg["media_tiers"])
        m["trusted_tier_pct"] = round(100 * sum(1 for t in tiers if t in ("T1", "T2", "T3")) / len(items), 1) if items else None
    return m


def _cap_groups(items: list, key: str, max_per: int) -> list:
    counts, out = {}, []
    for it in items:
        g = it.get(key)
        if counts.get(g, 0) >= max_per:
            continue
        counts[g] = counts.get(g, 0) + 1
        out.append(it)
    return out


def run_section(section: str, lesson_topic: str, db_path: str, avoid_texts: list | None = None) -> dict:
    """Produce one news section. Never raises: returns an empty, quiet section on failure."""
    cfg = section_config(section)
    registry = load_registry()
    ctx = run_logger.current()
    domains = tier_domains(cfg["search_tiers"], registry)
    history = recent_ledger(db_path, section, cfg["window_days"])
    try:
        results = _research(section, cfg, lesson_topic, domains)
        cands = _candidates(results, {h[1] for h in history if h[1]})
        if ctx:
            ctx.save_json(f"outputs/{section}_candidates.json", cands)
        if not cands:
            raise RuntimeError("no candidates from any search provider")
        media = [d for d in tier_domains(cfg.get("media_tiers", []), registry)]
        prompt = render_prompt(
            f"{section}_editor", today=date.today().isoformat(), window_start=window_start(cfg["window_days"]),
            candidates=json.dumps(cands, ensure_ascii=False, indent=0), min_items=cfg["min_items"],
            max_items=cfg["max_items"], categories=", ".join(cfg.get("categories", [])),
            buckets=", ".join(cfg.get("buckets", [])), min_categories=cfg.get("min_categories"),
            max_per_category=cfg.get("max_per_category"), min_buckets=cfg.get("min_buckets"),
            max_per_bucket=cfg.get("max_per_bucket"), max_media_items=cfg.get("max_media_items"),
            media_domains=", ".join(media), lesson_topic=lesson_topic,
            jit_headlines="; ".join(avoid_texts or []) or "none")
        if ctx:
            ctx.save_text(f"inputs/prompt_{section}_editor.md", prompt)
        out = llm_call(prompt, schema=_schema(section, cfg), stage=f"{section}-editor", schema_name=f"{section}_items")
        raw = (out.get("parsed") or {}).get("items", [])
        if ctx:
            ctx.save_json(f"outputs/{section}_raw.json", raw)
    except Exception as exc:  # noqa: BLE001
        run_logger.log_exception(section, exc, severity="ERROR", action_taken="section empty (quiet)")
        return {"items": [], "vectors": None, "quiet": True, "failed": True,
                "metrics": {"count": 0, "error": str(exc)[:200]}}

    by_id = {c["id"]: c for c in cands}
    items = []
    for r in raw:
        c = by_id.get(r.get("candidate_id"))
        if not c:
            continue
        if any(domain_matches(c["url"], b) for b in registry.get("blocked", [])):
            continue
        group = [c] + [by_id[x] for x in r.get("also_covered_by", []) if x in by_id and x != c["id"]]
        best = min(group, key=lambda g: _TIER_ORDER.index(tier_of(g["url"], registry))
                   if tier_of(g["url"], registry) in _TIER_ORDER else len(_TIER_ORDER))
        if best is not c:  # CL-073: show the first-party source (company/lab post) as the main link
            r = {**r, "also_covered_by": [x for x in [c["id"]] + list(r.get("also_covered_by", [])) if x != best["id"]]}
            c = best
        fp = dict(r.get("fingerprint") or {})
        fp["event_type"] = r.get("category") or r.get("bucket") or ""
        item = {**r, "url": c["url"], "source": c["domain"], "date": c["date"] or date.today().isoformat(),
                "lead": c.get("snippet", ""), "tier": tier_of(c["url"], registry), "fingerprint": fp,
                "also_covered_by_urls": [by_id[x]["url"] for x in r.get("also_covered_by", []) if x in by_id]}
        item["topic"] = item.get("headline") or item.get("concept")
        if section == "jit":
            item["why_it_matters"] = item.get("why_it_matters_pm", "")
        items.append(item)
    key = "category" if section == "jit" else "bucket"
    items = _cap_groups(items, key, cfg.get("max_per_category") or cfg.get("max_per_bucket") or 99)
    if section == "jic":
        media = set(cfg.get("media_tiers", []))
        n_media, kept = 0, []
        for it in items:
            if tier_of(it["url"], registry) in media:
                n_media += 1
                if n_media > cfg.get("max_media_items", 2):
                    continue
            kept.append(it)
        items = kept
    exclude = [lesson_topic] + list(avoid_texts or [])
    kept, decisions, vectors = dedupe_items(items, history=history, exclude_texts=exclude)
    kept = kept[: cfg["max_items"]]
    vectors = vectors[: len(kept)] if vectors else None
    metrics = _metrics(section, kept, cfg, registry, cfg["window_days"])
    metrics.update({"candidates": len(cands), "selected_by_editor": len(raw), "after_dedupe": len(kept)})
    quiet = len(kept) < cfg["min_items"]
    if ctx:
        ctx.save_json(f"outputs/{section}.json", kept)
        ctx.save_json(f"outputs/{section}_dedupe.json", decisions)
        ctx.save_json(f"outputs/{section}_metrics.json", metrics)
    return {"items": kept, "vectors": vectors, "quiet": quiet, "failed": False, "metrics": metrics}
