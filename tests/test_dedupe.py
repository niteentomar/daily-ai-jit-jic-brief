"""
MODULE: test_dedupe.py
PURPOSE: Duplicate detection v2 (CL-070): three verdicts, fingerprints, golden examples
         E1-E8 from DEDUP_TAVILY_PAPERS_DRAFT.md and the 2026-11-01 dry run, news_ledger memory.
CHANGE LOG: 1.0.0 | 2026-11-01 | CL-064 | Claude Code
            2.0.0 | 2026-11-01 | CL-070 golden set; threshold tests rewritten (0.70 -> 0.85/0.92) | Claude Code
"""
import math
import sqlite3

import pytest

from core import dedupe
from scripts.setup_db import init_db

D, O, U = dedupe.DUPLICATE, dedupe.OVERLAP, dedupe.UNIQUE


def fp(actors=(), obj="", event="", keywords=(), number=""):
    return dedupe.fingerprint({"fingerprint": {"actors": list(actors), "object": obj, "event_type": event,
                                               "keywords": list(keywords), "key_number": number}})


def unit(c):
    """2-d unit vector with cosine c to [1, 0]."""
    return [c, math.sqrt(max(0.0, 1 - c * c))]


# ── Golden set: rule-level verdicts (T-DED-G-001) ────────────────────────────
GOLDEN = [
    # id, A, B, cosine, expected
    ("E1 Genie 4 vs Gemini 4 Carbon (dry run 0.791)",
     fp(["Google DeepMind"], "Gemini 4 Carbon", "model release", ["frontier model", "reasoning"]),
     fp(["Google DeepMind"], "Genie 4", "model release", ["world model", "real-time simulation"]), 0.791, U),
    ("E2 GPT-6.1 Terra vs OpenAI-NVIDIA datacenter (0.701)",
     fp(["OpenAI"], "GPT-6.1 Terra", "model release", ["computer use", "visual reasoning"]),
     fp(["OpenAI", "NVIDIA"], "10-gigawatt datacenter", "compute/infrastructure", ["datacenter", "gpu"]), 0.701, U),
    ("E3 Speculative decoding vs linear attention (0.738)",
     fp([], "Linear attention", "architecture", ["state-space models", "linear attention"]),
     fp([], "Speculative decoding", "inference & systems", ["draft model", "latency"]), 0.738, U),
    ("E4 Harness failure attribution vs trajectory evaluation (0.814)",
     fp([], "Agent harness failure attribution", "evaluation", ["agent evaluation", "tool use", "harness"]),
     fp([], "Trajectory evaluation", "evaluation", ["agent evaluation", "tool use", "trajectory"]), 0.814, O),
    ("E5 Mistral Large 4 own post vs TechCrunch",
     fp(["Mistral"], "Mistral Large 4", "open-source release", ["open weights", "1 trillion parameters"]),
     fp(["Mistral AI"], "Mistral Large 4", "open-source release", ["open source", "1t parameters"]), 0.90, D),
    ("E6 Anthropic IPO, different messaging (Reuters vs Axios)",
     fp(["Anthropic"], "Anthropic IPO", "funding/M&A", ["ipo", "s-1 filing"]),
     fp(["Anthropic"], "Anthropic IPO filing", "funding/M&A", ["public listing", "valuation"]), 0.83, D),
    ("Dry run: Long-term agentic memory vs linear attention (0.768)",
     fp([], "Agentic memory architectures", "retrieval & memory", ["long-term memory", "agents"]),
     fp([], "Linear attention", "architecture", ["state-space models", "linear attention"]), 0.768, U),
    ("Dry run: Multi-agent topologies vs on-policy distillation (0.730)",
     fp([], "Multi-agent workflow topologies", "agents & tools", ["multi-agent", "orchestration"]),
     fp([], "On-policy distillation", "training & alignment", ["distillation", "reinforcement learning"]), 0.730, U),
    ("Dry run: Jailbreak vulnerability vs harness attribution (0.722)",
     fp([], "Jailbreak vulnerability", "safety", ["jailbreak", "instruction separation"]),
     fp([], "Agent harness failure attribution", "evaluation", ["agent evaluation", "harness"]), 0.722, U),
    ("Dry run: Liquid LFM3 vs Mistral Large 4 (0.724)",
     fp(["Liquid AI"], "LFM3", "model release", ["multimodal", "small model"]),
     fp(["Mistral"], "Mistral Large 4", "open-source release", ["open weights"]), 0.724, U),
    ("Very high cosine, same entities, no object match",
     fp(["Nvidia"], "Blackwell Ultra", "compute/infrastructure", ["gpu", "blackwell ultra"]),
     fp(["Nvidia"], "Blackwell Ultra GPU", "compute/infrastructure", ["gpu", "blackwell ultra"]), 0.95, D),
]


@pytest.mark.parametrize("name,a,b,score,expected", GOLDEN, ids=[g[0][:40] for g in GOLDEN])
def test_t_ded_g_001_golden_verdicts(name, a, b, score, expected):
    """T-DED-G-001 (CL-070): every golden pair gets the expected verdict; no UNIQUE pair is merged."""
    verdict, why = dedupe.classify(a, b, score, overlap=0.85, duplicate=0.92)
    assert verdict == expected, f"{name}: got {verdict} ({why})"


# ── Item-level behaviour ─────────────────────────────────────────────────────

def _item(headline, url, tier, **f):
    return {"headline": headline, "url": url, "tier": tier, "fingerprint": f}


def test_t_ded_c_001_duplicate_merged_parent_is_best_tier(mocker):
    """T-DED-C-001 (E5): same story from TechCrunch then mistral.ai -> one item, mistral.ai is the parent."""
    mocker.patch("core.dedupe.embed", return_value=[unit(1.0), unit(0.90)])
    items = [_item("Mistral open-sources 1T model", "https://techcrunch.com/m", "J3", actors=["Mistral"],
                   object="Mistral Large 4", event_type="open-source release"),
             _item("Mistral releases Mistral Large 4 weights", "https://mistral.ai/news/l4", "J1", actors=["Mistral"],
                   object="Mistral Large 4", event_type="open-source release")]
    kept, decisions, vecs = dedupe.dedupe_items(items)
    assert [k["url"] for k in kept] == ["https://mistral.ai/news/l4"]
    assert kept[0]["also_covered_by_urls"] == ["https://techcrunch.com/m"]
    assert [d["decision"] for d in decisions] == ["kept", "merged"] and len(vecs) == 1


def test_t_ded_c_002_same_actor_different_object_both_kept(mocker):
    """T-DED-C-002 (E1): Genie 4 and Gemini 4 Carbon are both kept (old 0.70 threshold merged them)."""
    mocker.patch("core.dedupe.embed", return_value=[unit(1.0), unit(0.791)])
    items = [_item("DeepMind announces Gemini 4 Carbon", "https://deepmind.google/a", "J1",
                   actors=["Google DeepMind"], object="Gemini 4 Carbon", event_type="model release"),
             _item("DeepMind unveils Genie 4", "https://deepmind.google/b", "J1",
                   actors=["Google DeepMind"], object="Genie 4", event_type="model release")]
    kept, decisions, _ = dedupe.dedupe_items(items)
    assert len(kept) == 2 and decisions[1]["verdict"] == U


def test_t_ded_c_003_overlap_kept_with_related_link(mocker):
    """T-DED-C-003 (E4): overlapping concepts are both kept; the second links to the first."""
    mocker.patch("core.dedupe.embed", return_value=[unit(1.0), unit(0.814)])
    items = [{"concept": "Agent harness failure attribution", "url": "https://a", "fingerprint": {
                 "object": "Agent harness failure attribution", "event_type": "evaluation",
                 "keywords": ["agent evaluation", "tool use"]}},
             {"concept": "Trajectory evaluation", "url": "https://b", "fingerprint": {
                 "object": "Trajectory evaluation", "event_type": "evaluation",
                 "keywords": ["agent evaluation", "tool use"]}}]
    kept, decisions, _ = dedupe.dedupe_items(items)
    assert len(kept) == 2
    assert kept[1]["related"] == [{"title": "Agent harness failure attribution", "url": "https://a"}]
    assert decisions[1]["verdict"] == O


def _history(db, items, vecs, section="jit"):
    init_db(db)
    dedupe.record_delivered(db, "r1", section, items, vecs)
    return dedupe.recent_ledger(db, section, 7)


def test_t_ded_c_004_repeat_from_ledger_dropped(mocker, tmp_path):
    """T-DED-C-004 (R-001, E8): same object and event already delivered -> dropped as repeat."""
    db = str(tmp_path / "l.db")
    old = _item("Mistral releases Large 4", "https://mistral.ai/x", "J1", actors=["Mistral"],
                object="Mistral Large 4", event_type="open-source release")
    history = _history(db, [old], [unit(1.0)])
    assert len(history) == 1 and dedupe.from_blob(history[0][2]) == pytest.approx(unit(1.0))
    mocker.patch("core.dedupe.embed", return_value=[unit(0.88)])
    new = _item("Hands-on: Mistral Large 4 review", "https://venturebeat.com/y", "J3", actors=["Mistral"],
                object="Mistral Large 4", event_type="open-source release")
    kept, decisions, _ = dedupe.dedupe_items([new], history=history)
    assert kept == [] and decisions[0]["decision"] == "dropped"


def test_t_ded_c_005_follow_up_with_new_number_kept_as_update(mocker, tmp_path):
    """T-DED-C-005 (E7): same object with a new key number is kept and flagged as an update."""
    db = str(tmp_path / "l.db")
    old = _item("Anthropic files for IPO", "https://reuters.com/a", "J3", actors=["Anthropic"],
                object="Anthropic IPO", event_type="funding/M&A", key_number="")
    history = _history(db, [old], [unit(1.0)])
    mocker.patch("core.dedupe.embed", return_value=[unit(0.90)])
    new = _item("Anthropic sets IPO price range", "https://axios.com/b", "J3", actors=["Anthropic"],
                object="Anthropic IPO", event_type="funding/M&A", key_number="$120-$135 per share")
    kept, _, _ = dedupe.dedupe_items([new], history=history)
    assert len(kept) == 1 and kept[0]["update_of"].startswith("Anthropic files for IPO")


def test_t_ded_c_006_same_url_dropped_even_without_embeddings(mocker):
    """T-DED-C-006: an exact URL already delivered is always dropped."""
    mocker.patch("core.dedupe.embed", return_value=None)
    history = [("Old headline", "https://same/url", None, "jit", None)]
    kept, _, _ = dedupe.dedupe_items([{"headline": "Totally new words", "url": "https://same/url"}], history=history)
    assert kept == []


def test_t_ded_e_001_embedding_failure_falls_back_to_jaccard(mocker):
    """T-DED-E-001 (D10): embedding failure -> token-Jaccard still merges near-identical headlines."""
    mocker.patch("core.dedupe.embed", return_value=None)
    items = [{"headline": "Nvidia unveils Blackwell Ultra GPU"}, {"headline": "Nvidia unveils Blackwell Ultra GPU today"},
             {"headline": "Google announces Gemini 4 Argon"}]
    kept, _, vecs = dedupe.dedupe_items(items)
    assert len(kept) == 2 and vecs is None


def test_t_ded_c_007_excluded_texts_block_overlap(mocker):
    """T-DED-C-007: an item overlapping the lesson topic (cosine >= overlap threshold) is dropped."""
    mocker.patch("core.dedupe.embed", return_value=[unit(1.0), unit(0.90)])
    kept, decisions, _ = dedupe.dedupe_items([{"concept": "Transformer attention"}],
                                             exclude_texts=["Transformer Architecture"])
    assert kept == [] and "overlaps" in decisions[0]["why"]


def test_t_ded_c_008_embed_uses_semantic_similarity_task(mocker, monkeypatch):
    """T-DED-C-008 (CL-070): Vertex embeddings request task_type=SEMANTIC_SIMILARITY."""
    monkeypatch.setenv("EMBEDDING_MODEL", "vertex_ai/gemini-embedding-001")
    resp = mocker.Mock(data=[{"embedding": [0.1, 0.2]}])
    m = mocker.patch("litellm.embedding", return_value=resp)
    assert dedupe.embed(["a"]) == [[0.1, 0.2]]
    assert m.call_args.kwargs["task_type"] == "SEMANTIC_SIMILARITY"


def test_t_ded_c_009_lead_paragraph_used_in_item_text():
    """T-DED-C-009: item text = headline + first two sentences of the lead (inverted pyramid)."""
    it = {"headline": "H", "lead": "One. Two! Three? Four.", "what_happened": "ignored"}
    assert dedupe.item_text(it) == "H. One. Two!"


def test_t_ded_c_010_old_ledger_gets_fingerprint_column(tmp_path):
    """T-DED-C-010 (migration): a pre-v2 news_ledger without `fingerprint` is upgraded in place."""
    db = str(tmp_path / "old.db")
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE news_ledger (id INTEGER PRIMARY KEY, run_id TEXT, section TEXT, headline TEXT, url TEXT,"
                 " domain TEXT, item_date TEXT, covered_date TEXT, category TEXT, embedding BLOB)")
    conn.commit(); conn.close()
    dedupe.record_delivered(db, "r", "jit", [{"headline": "X", "url": "https://x"}], None)
    rows = dedupe.recent_ledger(db, "jit", 7)
    assert len(rows) == 1 and '"object"' in rows[0][4]


def test_t_ded_n_001_news_ledger_is_append_only(tmp_path):
    """T-DED-N-001 (R-004): DELETE on news_ledger is blocked by trigger."""
    db = str(tmp_path / "l.db")
    init_db(db)
    dedupe.record_delivered(db, "r1", "jic", [{"concept": "X", "url": "https://x"}], None)
    conn = sqlite3.connect(db)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM news_ledger")
