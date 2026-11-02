"""
MODULE: citations.py
PURPOSE: Verify lesson papers and attach citation counts (CL-064, lesson spec 3C).
         Code, not the LLM, decides which papers exist: each paper is looked up
         in OpenAlex (free singleton lookups by DOI; arXiv IDs map to DOI
         10.48550/arXiv.<id>), then by title search. Unverified papers are dropped.
         Stars: >=1000 ★★★, 100-999 ★★, 10-99 ★, <10 "new". Seminal = highest cited.
INPUTS: list of paper dicts from the lesson model
OUTPUTS: verified, enriched, sorted list (max 5)
DEPENDENCIES: requests
RULE REFERENCES: lesson spec v2 (D8)
CHANGE LOG: 1.0.0 | 2026-11-01 | CL-064 initial implementation | Claude Code
            2.0.0 | 2026-11-01 | CL-071 paper credibility score (research: venue, citations
            normalised by field/year, recency, openness, authority; retracted excluded).
            OpenAlex candidate pool from the topic's short title; selection rules:
            1 seminal (most cited, relevance >= 0.70, age >= 3y) + up to 4 by score,
            >= 1 from the last 24 months if any qualifies; < 10 citations dropped unless
            <= 18 months old and peer-reviewed | Claude Code
            3.0.0 | 2026-11-02 | CL-073 dry run 2 picked off-topic papers (fuzzy logic,
            AlphaFold 3): absolute cosine is not relevance (anisotropy), vague search,
            prompt over-steered. Now: (1) category gate - arXiv cs.*/stat.ML or OpenAlex
            field Computer Science (classics outside CS pass only with grade 3);
            (2) keyword/tag overlap from OpenAlex keywords/topics and arXiv categories;
            (3) LLM relevance grader 0-3 (corrective-RAG grader pattern), gate >= 2;
            (4) candidates from arXiv API (AI categories) + OpenAlex (relevance sort,
            sub-concept queries) | Claude Code
"""
import logging
import os
import math
import re
from datetime import date

import time
import xml.etree.ElementTree as ET

import requests

from core import run_logger
from core.settings import render_prompt, section_config

logger = logging.getLogger(__name__)

_OPENALEX = "https://api.openalex.org"
_ARXIV_API = "https://export.arxiv.org/api/query"
_ATOM = "{http://www.w3.org/2005/Atom}"
_ARXIV_NS = "{http://arxiv.org/schemas/atom}"
_DEFAULT_FILTER = {"gate_prefixes": ["cs.", "stat.ML"], "openalex_fields": ["Computer Science"],
                   "search_categories": ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.IR", "cs.MA", "cs.NE", "cs.RO",
                                         "cs.HC", "cs.CY", "stat.ML"],
                   "min_grade": 2, "seminal_grade": 3, "arxiv_max_results": 10, "max_queries": 4,
                   "max_graded": 30}


def filter_config() -> dict:
    try:
        return {**_DEFAULT_FILTER, **(section_config("lesson").get("paper_filter") or {})}
    except Exception:  # noqa: BLE001
        return dict(_DEFAULT_FILTER)
_ARXIV_ID_RE = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?")

# CL-071 PaperScore weights and gates (DEDUP_TAVILY_PAPERS_DRAFT.md section 3, approved 2026-11-01)
WEIGHTS = {"relevance": 0.30, "impact": 0.25, "venue": 0.15, "recency": 0.15, "openness": 0.10, "authority": 0.05}
MIN_RELEVANCE = 0.60
SEMINAL_MIN_RELEVANCE = 0.70
SEMINAL_MIN_AGE_YEARS = 3
MIN_CITATIONS = 10
NEW_PAPER_MONTHS = 18
RECENT_MONTHS = 24
TOP_VENUES = ("neurips", "neural information processing systems", "icml", "international conference on machine learning",
              "iclr", "learning representations", "acl", "association for computational linguistics", "emnlp",
              "empirical methods in natural language", "naacl", "cvpr", "computer vision and pattern recognition",
              "iccv", "eccv", "aaai", "ijcai", "kdd", "sigir", "www", "colm", "nature", "science",
              "journal of machine learning research", "transactions on machine learning research",
              "ieee transactions on pattern analysis", "artificial intelligence", "proceedings of the national academy")
TOP_INSTITUTIONS = ("google", "deepmind", "openai", "anthropic", "meta", "facebook", "microsoft", "nvidia", "apple",
                    "amazon", "ibm", "stanford", "massachusetts institute of technology", "berkeley", "carnegie mellon",
                    "princeton", "harvard", "oxford", "cambridge", "eth zurich", "toronto", "mila", "montreal",
                    "tsinghua", "peking", "allen institute", "max planck", "university college london", "new york university")


def stars(citations: int | None) -> str:
    if citations is None:
        return ""
    if citations >= 1000:
        return "★★★"
    if citations >= 100:
        return "★★"
    if citations >= 10:
        return "★"
    return "new"


def _params() -> dict:
    mail = os.getenv("EMAIL_FROM")
    return {"mailto": mail} if mail else {}


def _norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def title_similarity(a: str, b: str) -> float:
    """Token Jaccard of normalised titles (subtitle after ':' ignored when one side lacks it)."""
    ta, tb = set(_norm_title(a).split()), set(_norm_title(b).split())
    full = len(ta & tb) / len(ta | tb) if ta and tb else 0.0
    ha, hb = set(_norm_title(a.split(":")[0]).split()), set(_norm_title(b.split(":")[0]).split())
    head = len(ha & hb) / len(ha | hb) if ha and hb else 0.0
    return max(full, head)


def _abstract(inv: dict | None, max_words: int = 120) -> str:
    """Rebuild text from OpenAlex abstract_inverted_index."""
    if not inv:
        return ""
    pos = sorted((i, w) for w, idxs in inv.items() for i in idxs)
    return " ".join(w for _, w in pos[:max_words])


def _from_work(work: dict) -> dict:
    doi = (work.get("doi") or "").replace("https://doi.org/", "")
    loc = work.get("primary_location") or {}
    src = loc.get("source") or {}
    pct = work.get("citation_normalized_percentile") or {}
    insts = [i.get("display_name") or "" for a in (work.get("authorships") or []) for i in (a.get("institutions") or [])]
    return {"openalex_id": work.get("id"), "verified_title": work.get("display_name") or work.get("title"),
            "year": work.get("publication_year"), "publication_date": work.get("publication_date") or "",
            "citations": work.get("cited_by_count"), "doi": doi, "fwci": work.get("fwci"),
            "percentile": pct.get("value"), "top_1pct": bool(pct.get("is_in_top_1_percent")),
            "top_10pct": bool(pct.get("is_in_top_10_percent")), "is_retracted": bool(work.get("is_retracted")),
            "venue": src.get("display_name") or "", "venue_type": src.get("type") or "",
            "is_oa": bool((work.get("open_access") or {}).get("is_oa")), "institutions": insts[:12],
            "abstract": _abstract(work.get("abstract_inverted_index")),
            "field": ((work.get("primary_topic") or {}).get("field") or {}).get("display_name") or "",
            "subfield": ((work.get("primary_topic") or {}).get("subfield") or {}).get("display_name") or "",
            "tags": [k.get("display_name") for k in (work.get("keywords") or []) if k.get("display_name")][:10]
                    + [t.get("display_name") for t in (work.get("topics") or [])[:3] if t.get("display_name")],
            "arxiv_id": _arxiv_from_work(work)}


def _arxiv_from_work(work: dict) -> str:
    doi = (work.get("doi") or "").lower()
    m = re.search(r"arxiv\.(\d{4}\.\d{4,5})", doi)
    if m:
        return m.group(1)
    for loc in work.get("locations") or []:
        m = _ARXIV_ID_RE.search((loc.get("landing_page_url") or "") if "arxiv" in (loc.get("landing_page_url") or "") else "")
        if m:
            return m.group(1)
    return ""


def lookup(paper: dict, session=requests, timeout: int = 20) -> dict | None:
    """Return OpenAlex metadata for a paper, or None if it cannot be verified."""
    arxiv = (paper.get("arxiv_id") or "").strip()
    doi = (paper.get("doi") or "").strip().replace("https://doi.org/", "")
    ids = []
    if arxiv:
        m = _ARXIV_ID_RE.search(arxiv)
        if m:
            ids.append(f"doi:10.48550/arXiv.{m.group(1)}")
    if doi:
        ids.append(f"doi:{doi}")
    want_title = paper.get("title") or ""
    for ident in ids:
        try:
            r = session.get(f"{_OPENALEX}/works/{ident}", params=_params(), timeout=timeout)
            if r.status_code == 200:
                meta = _from_work(r.json())
                # CL-074: an LLM-supplied DOI can point to a different paper (dry run 3: "Calculative Rationality"
                # DOI resolved to a distributed-AI paper). Accept the id only if the titles agree.
                if not want_title or title_similarity(want_title, meta.get("verified_title") or "") >= 0.5:
                    return meta
                logger.warning(f"{ident} resolves to '{meta.get('verified_title')}', not '{want_title}'; "
                               "trying title search")
        except requests.RequestException as exc:
            logger.warning(f"OpenAlex lookup failed for {ident}: {exc}")
    title = paper.get("title") or ""
    if title:
        try:
            r = session.get(f"{_OPENALEX}/works", timeout=timeout,
                            params={**_params(), "search": title[:200], "per-page": 3})
            if r.status_code == 200:
                want = _norm_title(title)
                for work in r.json().get("results", []):
                    got = _norm_title(work.get("display_name") or "")
                    if got and (got == want or (len(want) > 20 and (want in got or got in want))):
                        return _from_work(work)
        except requests.RequestException as exc:
            logger.warning(f"OpenAlex title search failed: {exc}")
    return None


def search_pool(queries, n: int = 25, session=requests, timeout: int = 20) -> list:
    """OpenAlex candidates for the topic's sub-concept queries, relevance-sorted (CL-073: no most-cited sort,
    which pulled in famous off-topic papers). Never raises."""
    if isinstance(queries, str):
        queries = [queries]
    pool, seen = [], set()
    for q in queries:
        try:
            r = session.get(f"{_OPENALEX}/works", timeout=timeout,
                            params={**_params(), "search": q[:200], "per-page": n, "filter": "is_retracted:false"})
            if r.status_code != 200:
                continue
            for work in r.json().get("results", []):
                meta = _from_work(work)
                if meta["openalex_id"] and meta["openalex_id"] not in seen:
                    seen.add(meta["openalex_id"])
                    pool.append({**meta, "source_of_candidate": "openalex"})
        except (requests.RequestException, ValueError) as exc:
            logger.warning(f"OpenAlex pool search failed: {exc}")
    return pool


def _parse_arxiv(xml_text: str) -> list:
    out = []
    root = ET.fromstring(xml_text)
    for e in root.findall(f"{_ATOM}entry"):
        m = _ARXIV_ID_RE.search(e.findtext(f"{_ATOM}id") or "")
        if not m:
            continue
        prim = e.find(f"{_ARXIV_NS}primary_category")
        out.append({"arxiv_id": m.group(1), "title": " ".join((e.findtext(f"{_ATOM}title") or "").split()),
                    "abstract": " ".join((e.findtext(f"{_ATOM}summary") or "").split())[:1200],
                    "published": (e.findtext(f"{_ATOM}published") or "")[:10],
                    "primary_category": prim.get("term") if prim is not None else "",
                    "categories": [c.get("term") for c in e.findall(f"{_ATOM}category") if c.get("term")]})
    return out


def arxiv_search(queries, session=requests, timeout: int = 30, sleep=time.sleep) -> list:
    """arXiv API search restricted to the AI categories (owner request 2026-11-02). Never raises."""
    cfg = filter_config()
    cats = " OR ".join(f"cat:{c}" for c in cfg["search_categories"])
    out, seen = [], set()
    for i, q in enumerate(queries if isinstance(queries, list) else [queries]):
        if i:
            sleep(3)  # arXiv API etiquette: 3 s between calls
        phrase = q.replace('"', "")
        try:
            r = session.get(_ARXIV_API, timeout=timeout, params={
                "search_query": f'(ti:"{phrase}" OR abs:"{phrase}") AND ({cats})',
                "max_results": cfg["arxiv_max_results"], "sortBy": "relevance"})
            if r.status_code != 200:
                continue
            for e in _parse_arxiv(r.text):
                if e["arxiv_id"] not in seen:
                    seen.add(e["arxiv_id"])
                    out.append(e)
        except (requests.RequestException, ET.ParseError) as exc:
            logger.warning(f"arXiv search failed: {exc}")
    return out


def arxiv_categories(ids: list, session=requests, timeout: int = 30) -> dict:
    """Map arXiv id -> list of categories (one batched id_list call). Never raises."""
    ids = [i for i in dict.fromkeys(ids) if i]
    if not ids:
        return {}
    try:
        r = session.get(_ARXIV_API, timeout=timeout, params={"id_list": ",".join(ids), "max_results": len(ids)})
        if r.status_code == 200:
            return {e["arxiv_id"]: e["categories"] for e in _parse_arxiv(r.text)}
    except (requests.RequestException, ET.ParseError) as exc:
        logger.warning(f"arXiv category lookup failed: {exc}")
    return {}


def category_ok(meta: dict) -> tuple[bool | None, str]:
    """Category gate: arXiv cs.*/stat.ML, else OpenAlex field Computer Science. None = unknown."""
    cfg = filter_config()
    cats = meta.get("arxiv_categories") or []
    if cats:
        hit = [c for c in cats if any(c == p or c.startswith(p) for p in cfg["gate_prefixes"])]
        return (True, f"arXiv {','.join(hit[:3])}") if hit else (False, f"arXiv {','.join(cats[:3])} not CS")
    field = meta.get("field") or ""
    if field:
        return (True, f"field {field}") if field in cfg["openalex_fields"] else (False, f"field {field} not CS")
    return None, "category unknown"


_KW_STOP = set("a an the of and or for to in on with by vs its what is are not how when why use using deep dive "
               "explained overview".split())


def topic_terms(topic: str) -> list:
    """Short title + sub-concepts, lower-cased (e.g. ['what ai is', 'computational rationality', ...])."""
    head = re.split(r"\s+[—–-]\s+|:\s+", topic, maxsplit=1)
    tail = head[1] if len(head) > 1 else ""
    parts = [head[0]] + re.split(r",\s*(?:and\s+)?|\s+and\s+", tail)
    return [p.strip(" .").lower() for p in parts if p.strip(" .")]


def keyword_overlap(topic: str, meta: dict) -> float:
    """Share of topic terms whose significant words all appear in the paper's tags, title or abstract."""
    text = " ".join([meta.get("verified_title") or meta.get("title") or "", meta.get("abstract") or "",
                     " ".join(meta.get("tags") or []), " ".join(meta.get("arxiv_categories") or [])]).lower()
    counted = hits = 0
    for t in topic_terms(topic):
        words = [w for w in re.findall(r"[a-z0-9][a-z0-9\-]*", t) if w not in _KW_STOP and len(w) > 2]
        if not words:
            continue
        counted += 1
        hits += all(w in text for w in words)
    return round(hits / counted, 3) if counted else 0.0


def grade_papers(topic: str, metas: list) -> list | None:
    """LLM relevance grader (0-3 with reason) for each paper; None if the call fails."""
    if not metas:
        return []
    from core.gateway import llm_call
    lines = [f"P{i + 1}: {m.get('verified_title') or m.get('title')} ({m.get('year')}). "
             f"{(m.get('abstract') or '')[:400]}" for i, m in enumerate(metas)]
    prompt = render_prompt("paper_grader", topic=topic, papers="\n".join(lines))
    schema = {"type": "object", "required": ["grades"], "properties": {"grades": {"type": "array", "items": {
        "type": "object", "required": ["id", "grade", "reason"], "properties": {
            "id": {"type": "string"}, "grade": {"type": "integer"}, "reason": {"type": "string"}}}}}}
    try:
        out = llm_call(prompt, schema=schema, stage="paper-grader", schema_name="paper_grades")
        by_id = {g.get("id"): g for g in (out.get("parsed") or {}).get("grades", [])}
        return [{"grade": max(0, min(3, int(by_id.get(f"P{i + 1}", {}).get("grade", 0)))),
                 "reason": by_id.get(f"P{i + 1}", {}).get("reason", "not graded")} for i in range(len(metas))]
    except Exception as exc:  # noqa: BLE001
        run_logger.log_exception("paper-grader", exc, severity="WARNING", action_taken="keyword overlap only")
        return None


def assess(topic: str, metas: list, proposed_by_llm: bool = False) -> list:
    """Attach categories, keyword overlap, grade and relevance; mark gate failures in 'rejected_because'."""
    cfg = filter_config()
    cats = arxiv_categories([m.get("arxiv_id") for m in metas if m.get("arxiv_id") and not m.get("arxiv_categories")])
    for m in metas:
        if m.get("arxiv_id") in cats:
            m["arxiv_categories"] = cats[m["arxiv_id"]]
        m["keyword_overlap"] = keyword_overlap(topic, m)
        m["category_ok"], m["category_note"] = category_ok(m)
    todo = [m for m in metas if m.get("grade") is None]  # CL-074: reuse grades from the shortlist (consistency)
    new = grade_papers(topic, todo) if todo else []
    by_obj = {id(m): (new[k] if new else None) for k, m in enumerate(todo)}
    for i, m in enumerate(metas):
        g = by_obj[id(m)] if id(m) in by_obj else {"grade": m["grade"], "reason": m.get("grade_reason", "")}
        m["grade"] = g["grade"] if g else None
        m["grade_reason"] = g["reason"] if g else "grader unavailable"
        # relevance for the PaperScore: grader first, keyword overlap as tie-breaker (or alone if grader failed)
        m["relevance"] = round(0.8 * (g["grade"] / 3) + 0.2 * m["keyword_overlap"], 3) if g \
            else round(max(MIN_RELEVANCE, m["keyword_overlap"]), 3)
        reason = None
        if g and g["grade"] < cfg["min_grade"]:
            reason = f"grade {g['grade']}/3: {g['reason'][:80]}"
        elif m["category_ok"] is False and not (proposed_by_llm and g and g["grade"] >= cfg["seminal_grade"]):
            reason = f"category: {m['category_note']}"
        if reason:
            m["rejected_because"] = reason
    return metas


def _age_months(meta: dict, today: date | None = None) -> float:
    today = today or date.today()
    d = meta.get("publication_date") or ""
    try:
        pub = date.fromisoformat(d[:10])
    except ValueError:
        y = meta.get("year")
        if not y:
            return 999.0
        pub = date(int(y), 7, 1)
    return max(0.0, (today - pub).days / 30.44)


def venue_score(meta: dict) -> float:
    name = (meta.get("venue") or "").lower()
    if any(v in name for v in TOP_VENUES):
        return 1.0
    if meta.get("venue_type") in ("journal", "conference"):
        return 0.7
    return 0.4


def impact_score(meta: dict, today: date | None = None) -> float:
    if meta.get("percentile") is not None:
        return max(0.0, min(1.0, float(meta["percentile"])))
    years = max(1.0, _age_months(meta, today) / 12)
    per_year = (meta.get("citations") or 0) / years
    return min(1.0, math.log10(1 + per_year) / 3)


def recency_score(meta: dict, today: date | None = None) -> float:
    m = _age_months(meta, today)
    return 1.0 if m <= 24 else 0.7 if m <= 60 else 0.4


def openness_score(meta: dict, has_code: bool = False) -> float:
    if meta.get("is_oa"):
        return 1.0 if has_code else 0.6
    return 0.2


def authority_score(meta: dict) -> float:
    insts = " ".join(meta.get("institutions") or []).lower()
    return 1.0 if any(t in insts for t in TOP_INSTITUTIONS) else 0.5


def paper_score(meta: dict, relevance: float, today: date | None = None, has_code: bool = False) -> tuple[float, dict]:
    """PaperScore = 0.30 Rel + 0.25 Impact + 0.15 Venue + 0.15 Recency + 0.10 Openness + 0.05 Authority."""
    parts = {"relevance": round(relevance, 3), "impact": round(impact_score(meta, today), 3),
             "venue": venue_score(meta), "recency": recency_score(meta, today),
             "openness": openness_score(meta, has_code), "authority": authority_score(meta)}
    return round(sum(WEIGHTS[k] * v for k, v in parts.items()), 3), parts


def select_papers(cands: list, max_papers: int = 5, today: date | None = None) -> tuple[list, list]:
    """
    Apply gates and selection rules to scored candidates (each has meta fields, relevance, score).

    Returns:
        (selected, rejected) where rejected items carry a 'rejected_because' reason.
    """
    passed, rejected = [], []
    for c in cands:
        age = _age_months(c, today)
        if c.get("rejected_because"):
            rejected.append(c)
        elif c.get("is_retracted"):
            rejected.append({**c, "rejected_because": "retracted"})
        elif c["relevance"] < MIN_RELEVANCE:
            rejected.append({**c, "rejected_because": f"relevance {c['relevance']} < {MIN_RELEVANCE}"})
        elif (c.get("citations") or 0) < MIN_CITATIONS and not (age <= NEW_PAPER_MONTHS and venue_score(c) >= 0.7):
            rejected.append({**c, "rejected_because": f"{c.get('citations') or 0} citations and not a new peer-reviewed paper"})
        else:
            passed.append(c)
    seminal_pool = [c for c in passed if c["relevance"] >= SEMINAL_MIN_RELEVANCE
                    and (c.get("grade") is None or c.get("grade", 0) >= filter_config()["seminal_grade"])
                    and _age_months(c, today) >= 12 * SEMINAL_MIN_AGE_YEARS] or passed
    selected, seminal = [], None
    if seminal_pool:
        seminal = max(seminal_pool, key=lambda c: c.get("citations") or 0)
        selected.append({**seminal, "is_seminal": True})
    rest = sorted([c for c in passed if c is not seminal], key=lambda c: c["score"], reverse=True)
    others = rest[: max_papers - len(selected)]
    recent = [c for c in rest if _age_months(c, today) <= RECENT_MONTHS]
    if recent and others and not any(_age_months(c, today) <= RECENT_MONTHS for c in others):
        others[-1] = recent[0]
    selected += [{**c, "is_seminal": False} for c in others]
    return selected, rejected


def verify_papers(papers: list, max_papers: int = 5, session=requests, topic: str | None = None,
                  pool: list | None = None, today: date | None = None,
                  prior_grades: dict | None = None) -> tuple[list, dict]:
    """
    Verify the lesson's papers in OpenAlex, assess (category, keywords, grade), score and select (CL-071/073).

    Args:
        papers: papers written by the lesson model (title, arxiv_id/doi, contribution, first_author).
        topic: lesson topic (None -> no relevance assessment, legacy behaviour).
        pool: unused (kept for compatibility).

    Returns:
        (selected_papers, stats) with stats {requested, verified, dropped_titles, rejected, scores}
    """
    verified, dropped = [], []
    for p in papers or []:
        meta = lookup(p, session=session)
        if not meta:
            dropped.append(p.get("title", "")[:80])
            continue
        doi = meta.get("doi") or ""
        arxiv = (p.get("arxiv_id") or meta.get("arxiv_id") or "").strip()
        url = f"https://arxiv.org/abs/{arxiv}" if arxiv else (f"https://doi.org/{doi}" if doi else meta.get("openalex_id"))
        verified.append({**meta, **{k: v for k, v in p.items() if k not in ("year", "arxiv_id")}, "arxiv_id": arxiv,
                         "title": meta.get("verified_title") or p.get("title"), "year": meta.get("year") or p.get("year"),
                         "url": url})
    if topic:
        for c in verified:
            prior = (prior_grades or {}).get(c.get("openalex_id"))
            if prior and prior.get("grade") is not None:
                c["grade"], c["grade_reason"] = prior["grade"], prior.get("grade_reason", "")
        assess(topic, verified, proposed_by_llm=True)
    else:
        for c in verified:
            c["relevance"] = 1.0
    for c in verified:
        c["score"], c["score_parts"] = paper_score(c, c["relevance"], today)
    selected, rejected = select_papers(verified, max_papers=max_papers, today=today)
    for p in selected:
        p["stars"] = stars(p.get("citations"))
        p["badge"] = "Top 1%" if p.get("top_1pct") else ("Top 10%" if p.get("top_10pct") else "")
    stats = {"requested": len(papers or []), "verified": len(selected), "dropped_titles": dropped,
             "rejected": [{"title": (r.get("title") or "")[:80], "why": r["rejected_because"]} for r in rejected],
             "scores": [{"title": (p.get("title") or "")[:80], "score": p["score"], "parts": p["score_parts"],
                         "grade": p.get("grade"), "category": p.get("category_note"),
                         "keyword_overlap": p.get("keyword_overlap"), "seminal": p["is_seminal"]} for p in selected]}
    ctx = run_logger.current()
    if ctx and (dropped or rejected):
        ctx.record_error("citations", f"Dropped unverified {dropped}; rejected {stats['rejected']}", severity="WARNING",
                         action_taken="dropped")
    return selected, stats


def shortlist(topic: str, short: str, n: int = 8, session=requests, today: date | None = None) -> tuple[list, list]:
    """
    Scored candidate shortlist for the lesson prompt: (top n candidates, all assessed candidates).

    Candidates: arXiv API (AI categories) + OpenAlex (relevance sort) for the short title and sub-concepts.
    Category gate applies strictly here (no exception for papers outside Computer Science).
    """
    cfg = filter_config()
    terms = topic_terms(topic)
    queries = ([terms[0]] + terms[1:])[: cfg["max_queries"]] if terms else [short]
    pool = search_pool(queries, session=session)
    ax = arxiv_search(queries, session=session)
    have = {m.get("arxiv_id") for m in pool if m.get("arxiv_id")}
    for e in ax:  # verify arXiv hits in OpenAlex for citations; keep arXiv categories
        if e["arxiv_id"] in have:
            for m in pool:
                if m.get("arxiv_id") == e["arxiv_id"]:
                    m["arxiv_categories"] = e["categories"]
            continue
        meta = lookup({"arxiv_id": e["arxiv_id"], "title": e["title"]}, session=session) or {
            "openalex_id": f"arXiv:{e['arxiv_id']}", "verified_title": e["title"], "year": int(e["published"][:4] or 0),
            "publication_date": e["published"], "citations": 0, "doi": "", "venue": "", "venue_type": "repository",
            "is_oa": True, "institutions": [], "abstract": e["abstract"], "tags": []}
        pool.append({**meta, "arxiv_id": e["arxiv_id"], "arxiv_categories": e["categories"],
                     "abstract": meta.get("abstract") or e["abstract"], "source_of_candidate": "arxiv"})
    if not pool:
        return [], []
    for m in pool:
        m["category_ok"], m["category_note"] = category_ok(m)
    in_cs = [m for m in pool if m["category_ok"] is not False]
    in_cs.sort(key=lambda m: keyword_overlap(topic, m), reverse=True)
    graded = assess(topic, in_cs[: cfg["max_graded"]], proposed_by_llm=False)
    for c in graded:
        c["score"], c["score_parts"] = paper_score(c, c["relevance"], today)
    picked, _ = select_papers(graded, max_papers=n, today=today)
    return picked, pool
