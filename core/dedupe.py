"""
MODULE: dedupe.py
PURPOSE: Story-level duplicate detection v2 (CL-070, replaces single-threshold D15).
         Three verdicts per pair (research: Newscatcher dedup vs clustering,
         SemEval-2022 Task 8 entities/time, inverted-pyramid lead paragraph):
           DUPLICATE - same story (merged in-email; dropped against history)
           OVERLAP   - related story, different angle (kept, linked)
           UNIQUE    - different story (kept)
         Signals: cosine of headline + lead paragraph (Gemini embedding,
         task_type SEMANTIC_SIMILARITY) plus the editor's story fingerprint
         (actors, object, event_type, keywords, key_number). Falls back to
         token-Jaccard when the embedding call fails.
INPUTS: items (dicts with headline/concept, lead, fingerprint), news_ledger rows
OUTPUTS: kept items, decision log (verdict + reason per pair), kept vectors
DEPENDENCIES: litellm (embedding), sqlite3, array
RULE REFERENCES: R-001 (cooldown), R-004 (append-only news_ledger), R-013 (dedup v2)
CHANGE LOG: 1.0.0 | 2026-11-01 | CL-064 initial implementation | Claude Code
            2.0.0 | 2026-11-01 | CL-070 three-verdict classifier, fingerprints,
            SEMANTIC_SIMILARITY embeddings, parent = best source tier | Claude Code
"""
import array
import json
import logging
import math
import re
import sqlite3
from datetime import date, timedelta

from core import run_logger
from core.settings import load_settings

logger = logging.getLogger(__name__)

_STOP = set("a an the of for to in on and or with by from at as is are be new its it this that ai".split())
JACCARD_DUPLICATE = 0.6   # fallback thresholds when embeddings are unavailable
JACCARD_OVERLAP = 0.4
DUPLICATE, OVERLAP, UNIQUE = "DUPLICATE", "OVERLAP", "UNIQUE"
_TIER_ORDER = ["J1", "T1", "J2", "T2", "T3", "J3", "T4", "J4", "T5"]


def lead_paragraph(text: str, sentences: int = 2) -> str:
    """First `sentences` sentences of a snippet (inverted pyramid: the lead carries who/what/when)."""
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return " ".join(parts[:sentences])[:400]


def item_text(item: dict) -> str:
    """Text used for similarity: headline/concept + lead paragraph (falls back to the item summary)."""
    head = item.get("headline") or item.get("concept") or item.get("topic") or ""
    body = lead_paragraph(item.get("lead") or "") or item.get("what_happened") or item.get("core_insight") \
        or item.get("why_it_matters") or ""
    return f"{head}. {body}".strip() if body else head.strip()


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9\.\- ]", " ", (text or "").lower()).strip()


def fingerprint(item: dict) -> dict:
    """Story fingerprint written by the editor (CL-070). Missing fields are empty."""
    fp = item.get("fingerprint") or item
    return {
        "actors": sorted({_norm(a) for a in (fp.get("actors") or []) if _norm(a)}),
        "object": _norm(fp.get("object") or ""),
        "event_type": _norm(fp.get("event_type") or item.get("category") or item.get("bucket") or ""),
        "keywords": sorted({_norm(k) for k in (fp.get("keywords") or []) if _norm(k)}),
        "key_number": ",".join(re.findall(r"\d+(?:\.\d+)?", str(fp.get("key_number") or ""))),
    }


def _fp_terms(fp: dict) -> set:
    terms = set(fp["actors"]) | set(fp["keywords"])
    terms |= {t for t in fp["object"].split() if t not in _STOP}
    return terms


def _same_object(a: dict, b: dict) -> bool:
    if not a["object"] or not b["object"]:
        return False
    ta, tb = set(a["object"].split()), set(b["object"].split())
    return a["object"] == b["object"] or (len(ta & tb) / len(ta | tb) >= 0.6)


def has_fingerprint(fp: dict) -> bool:
    return bool(fp["object"] or fp["actors"] or fp["keywords"])


def classify(fa: dict, fb: dict, score: float, method: str = "cosine", *,
             overlap: float | None = None, duplicate: float | None = None) -> tuple[str, str]:
    """
    Classify a pair of stories.

    Args:
        fa, fb: fingerprints (see fingerprint()).
        score: cosine (or Jaccard when method == 'jaccard') of headline + lead.
        overlap, duplicate: cosine thresholds (defaults from settings: 0.85 / 0.92).

    Returns:
        (verdict, reason) with verdict in DUPLICATE / OVERLAP / UNIQUE.
    """
    s = load_settings()
    if method == "jaccard":
        ovl, dup = JACCARD_OVERLAP, JACCARD_DUPLICATE
    else:
        ovl = s.dedupe_overlap if overlap is None else overlap
        dup = s.dedupe_duplicate if duplicate is None else duplicate
    if not (has_fingerprint(fa) and has_fingerprint(fb)):
        if score >= dup:
            return DUPLICATE, f"{method} {score:.3f} >= {dup} (no fingerprint)"
        if score >= ovl:
            return OVERLAP, f"{method} {score:.3f} >= {ovl} (no fingerprint)"
        return UNIQUE, f"{method} {score:.3f} below {ovl}"
    same_obj = _same_object(fa, fb)
    same_event = bool(fa["event_type"]) and fa["event_type"] == fb["event_type"]
    ta, tb = _fp_terms(fa), _fp_terms(fb)
    ent = len(ta & tb) / len(ta | tb) if ta and tb else 0.0
    shared_actor = bool(set(fa["actors"]) & set(fb["actors"]))
    if same_obj and same_event:
        return DUPLICATE, f"same object '{fa['object']}' and event '{fa['event_type']}'"
    if score >= dup and ent >= 0.5:
        return DUPLICATE, f"{method} {score:.3f} >= {dup} and entity overlap {ent:.2f}"
    if same_obj:
        return OVERLAP, f"same object '{fa['object']}', different event"
    if score >= ovl and (shared_actor or ent >= 0.3):
        return OVERLAP, f"{method} {score:.3f} >= {ovl} with shared actor/keywords"
    shared_kw = set(fa["keywords"]) & set(fb["keywords"])
    if len(shared_kw) >= 2:
        return OVERLAP, f"shares keywords {sorted(shared_kw)}"
    if shared_actor:
        return UNIQUE, f"same actor, different object ({method} {score:.3f})"
    return UNIQUE, f"{method} {score:.3f}, entity overlap {ent:.2f}"


def new_development(fa: dict, fb_old: dict) -> bool:
    """True when a story about the same object adds a new event type or a new key number."""
    if fa["event_type"] and fa["event_type"] != fb_old["event_type"]:
        return True
    return bool(fa["key_number"]) and fa["key_number"] != fb_old["key_number"]


def _tier_rank(item: dict) -> int:
    t = item.get("tier") or ""
    return _TIER_ORDER.index(t) if t in _TIER_ORDER else len(_TIER_ORDER)


def _tokens(text: str) -> set:
    return {t.rstrip(".") for t in re.findall(r"[a-z0-9][a-z0-9\-\.]*", text.lower()) if t.rstrip(".") not in _STOP}


def jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    return len(ta & tb) / len(ta | tb) if ta and tb else 0.0


def cosine(a, b) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def embed(texts: list, task_type: str = "SEMANTIC_SIMILARITY") -> list | None:
    """Return one vector per text, or None if the embedding call fails.
    CL-070: task_type SEMANTIC_SIMILARITY (Google's setting for duplicate detection; LiteLLM's
    default RETRIEVAL_QUERY inflated same-topic scores)."""
    if not texts:
        return []
    s = load_settings()
    try:
        import litellm
        kwargs = {"model": s.embedding_model, "input": texts}
        if s.embedding_model.startswith("vertex_ai/"):
            kwargs["vertex_location"] = s.embedding_location
            kwargs["task_type"] = task_type
        if s.embedding_dims:
            kwargs["dimensions"] = s.embedding_dims
        resp = litellm.embedding(**kwargs)
        vectors = [d["embedding"] if isinstance(d, dict) else d.embedding for d in resp.data]
        return vectors if len(vectors) == len(texts) else None
    except Exception as exc:  # noqa: BLE001
        run_logger.log_exception("embedding", exc, action_taken="fallback to Jaccard")
        return None


def to_blob(vec) -> bytes | None:
    return array.array("f", vec).tobytes() if vec else None


def from_blob(blob) -> list | None:
    if not blob:
        return None
    arr = array.array("f")
    arr.frombytes(blob)
    return list(arr)


def _ensure_fingerprint_column(conn) -> None:
    """CL-070 migration: add news_ledger.fingerprint to databases created before v2."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(news_ledger)")}
    if cols and "fingerprint" not in cols:
        conn.execute("ALTER TABLE news_ledger ADD COLUMN fingerprint TEXT")
        conn.commit()


def recent_ledger(db_path: str, section: str | None, days: int) -> list:
    """Rows delivered in the last `days` days: (headline, url, embedding, section, fingerprint_json)."""
    since = (date.today() - timedelta(days=days)).isoformat()
    try:
        conn = sqlite3.connect(db_path)
        try:
            _ensure_fingerprint_column(conn)
            sql = "SELECT headline, url, embedding, section, fingerprint FROM news_ledger WHERE covered_date >= ?"
            params: tuple = (since,)
            if section:
                sql += " AND section = ?"
                params += (section,)
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()
    except sqlite3.Error as exc:
        logger.error(f"news_ledger read failed: {exc}")
        return []


def _hist_fp(row) -> dict:
    raw = row[4] if len(row) > 4 else None
    try:
        return fingerprint(json.loads(raw)) if raw else fingerprint({})
    except (TypeError, ValueError):
        return fingerprint({})


def dedupe_items(items: list, *, history: list | None = None, exclude_texts: list | None = None,
                 overlap: float | None = None, duplicate: float | None = None) -> tuple[list, list, list | None]:
    """
    Apply the three-verdict rules (CL-070) to editor-selected items.

    Order of checks per item: same URL in history -> history verdicts -> excluded texts
    (lesson topic, other section) -> items already kept today.

    Args:
        items: candidate items in priority order.
        history: news_ledger rows inside the cooldown window.
        exclude_texts: texts that must not be repeated (lesson topic, today's JIT headlines).
        overlap, duplicate: cosine thresholds (default settings 0.85 / 0.92).

    Returns:
        (kept_items, decisions, kept_vectors)
    """
    s = load_settings()
    ovl = s.dedupe_overlap if overlap is None else overlap
    dup = s.dedupe_duplicate if duplicate is None else duplicate
    history = history or []
    exclude_texts = exclude_texts or []
    texts = [item_text(it) for it in items]
    fps = [fingerprint(it) for it in items]
    hist_texts = [h[0] for h in history]
    hist_fps = [_hist_fp(h) for h in history]
    hist_urls = {h[1] for h in history if h[1]}
    all_texts = texts + exclude_texts + [t for t, h in zip(hist_texts, history) if not h[2]]
    vecs = embed(all_texts)
    n_items, n_excl = len(texts), len(exclude_texts)
    item_vecs = vecs[:n_items] if vecs else None
    excl_vecs = vecs[n_items:n_items + n_excl] if vecs else None
    fresh_hist = iter(vecs[n_items + n_excl:]) if vecs else iter(())
    hist_vecs = [from_blob(h[2]) if h[2] else next(fresh_hist, None) for h in history]

    def _score(i: int, other_text: str, other_vec) -> tuple[float, str]:
        if item_vecs is not None and other_vec is not None:
            return round(cosine(item_vecs[i], other_vec), 3), "cosine"
        return round(jaccard(texts[i], other_text), 3), "jaccard"

    def _log(i, decision, verdict, why, score=None, method=None, other=None):
        d = {"item": texts[i][:120], "decision": decision, "verdict": verdict, "why": why}
        if score is not None:
            d.update({"score": score, "method": method})
        if other:
            d["other"] = other[:120]
        decisions.append(d)

    decisions, kept_idx = [], []
    for i, it in enumerate(items):
        if it.get("url") and it["url"] in hist_urls:
            _log(i, "dropped", DUPLICATE, "repeat (same URL already delivered)", 1.0, "url")
            continue
        dropped = False
        for k, ht in enumerate(hist_texts):
            score, method = _score(i, ht, hist_vecs[k])
            verdict, why = classify(fps[i], hist_fps[k], score, method, overlap=ovl, duplicate=dup)
            if verdict == UNIQUE:
                continue
            if _same_object(fps[i], hist_fps[k]) and new_development(fps[i], hist_fps[k]):
                it["update_of"] = ht[:120]          # E7: same story, new development -> keep as Update
                continue
            if verdict == DUPLICATE or _same_object(fps[i], hist_fps[k]):
                label = "repeat of earlier item" if verdict == DUPLICATE else "follow-up without news"
                _log(i, "dropped", verdict, f"{label}: {why}", score, method, ht)
                dropped = True
                break
        if dropped:
            continue
        for k, et in enumerate(exclude_texts):
            score, method = _score(i, et, excl_vecs[k] if excl_vecs is not None else None)
            limit = ovl if method == "cosine" else JACCARD_OVERLAP
            if score >= limit:
                _log(i, "dropped", OVERLAP, f"overlaps '{et[:60]}' ({method} {score} >= {limit})", score, method, et)
                dropped = True
                break
        if dropped:
            continue
        merged, related = False, []
        for k in kept_idx:
            score, method = _score(i, texts[k], item_vecs[k] if item_vecs is not None else None)
            verdict, why = classify(fps[i], fps[k], score, method, overlap=ovl, duplicate=dup)
            if verdict == DUPLICATE:
                parent, child = (i, k) if _tier_rank(items[i]) < _tier_rank(items[k]) else (k, i)
                if parent == i:  # better source arrives later: it becomes the parent in k's slot
                    items[i]["also_covered_by_urls"] = list(items[i].get("also_covered_by_urls", []))
                    items[k], items[i] = items[i], items[k]
                    texts[k], texts[i] = texts[i], texts[k]
                    fps[k], fps[i] = fps[i], fps[k]
                    if item_vecs is not None:
                        item_vecs[k], item_vecs[i] = item_vecs[i], item_vecs[k]
                extra = [items[i].get("url")] + list(items[i].get("also_covered_by_urls", []))
                items[k].setdefault("also_covered_by_urls", [])
                items[k]["also_covered_by_urls"] += [u for u in extra if u and u not in items[k]["also_covered_by_urls"]]
                _log(i, "merged", verdict, why, score, method, texts[k])
                merged = True
                break
            if verdict == OVERLAP:
                related.append((k, why, score, method))
        if not merged:
            kept_idx.append(i)
            if related:
                k, why, score, method = related[0]
                it["related"] = [{"title": (items[r[0]].get("headline") or items[r[0]].get("concept") or "")[:120],
                                  "url": items[r[0]].get("url")} for r in related]
                _log(i, "kept", OVERLAP, f"related to kept item: {why}", score, method, texts[k])
            else:
                _log(i, "kept", UNIQUE, "no duplicate found")
    kept = [items[k] for k in kept_idx]
    kept_vecs = [item_vecs[k] for k in kept_idx] if item_vecs is not None else None
    return kept, decisions, kept_vecs


def record_delivered(db_path: str, run_id: str, section: str, items: list, vectors: list | None) -> None:
    """Append delivered items to news_ledger (called only after a successful send)."""
    today = date.today().isoformat()
    from tools.search import domain_from_url
    try:
        conn = sqlite3.connect(db_path)
        try:
            _ensure_fingerprint_column(conn)
            for i, it in enumerate(items):
                vec = vectors[i] if vectors and i < len(vectors) else None
                conn.execute(
                    "INSERT INTO news_ledger (run_id, section, headline, url, domain, item_date, covered_date, "
                    "category, embedding, fingerprint) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (run_id, section, item_text(it)[:500], it.get("url"), domain_from_url(it.get("url", "")),
                     it.get("date"), today, it.get("category") or it.get("bucket"), to_blob(vec),
                     json.dumps(fingerprint(it))),
                )
            conn.commit()
        finally:
            conn.close()
    except sqlite3.Error as exc:
        run_logger.log_exception("news_ledger", exc)
