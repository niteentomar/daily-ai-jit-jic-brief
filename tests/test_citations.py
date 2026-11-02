"""
MODULE: test_citations.py
PURPOSE: CL-064 paper verification and citation stars (lesson 3C, D8).
CHANGE LOG: 1.0.0 | 2026-11-01 | CL-064 | Claude Code
"""
from types import SimpleNamespace

from core import citations


class _Session:
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def get(self, url, params=None, timeout=None):
        self.calls.append(url)
        for key, (status, body) in self.routes.items():
            if key in url and (key != "/works" or "search" in (params or {})):
                return SimpleNamespace(status_code=status, json=lambda body=body: body)
        return SimpleNamespace(status_code=404, json=lambda: {})


def test_t_cit_c_001_star_bands():
    """T-CIT-C-001: >=1000 ★★★, 100-999 ★★, 10-99 ★, <10 new."""
    assert [citations.stars(n) for n in (120408, 1000, 999, 100, 99, 10, 9)] == \
        ["★★★", "★★★", "★★", "★★", "★", "★", "new"]


def test_t_cit_c_002_arxiv_id_looked_up_as_datacite_doi():
    """T-CIT-C-002: arXiv ID -> OpenAlex works/doi:10.48550/arXiv.<id>."""
    s = _Session({"doi:10.48550/arXiv.1706.03762": (200, {"display_name": "Attention Is All You Need",
                                                          "publication_year": 2017, "cited_by_count": 120408,
                                                          "doi": "https://doi.org/10.48550/arxiv.1706.03762"})})
    meta = citations.lookup({"arxiv_id": "1706.03762v5", "title": "Attention is all you need"}, session=s)
    assert meta["citations"] == 120408 and "arXiv.1706.03762" in s.calls[0]


def test_t_cit_c_003_verify_sorts_and_marks_highest_cited_seminal(mocker):
    """T-CIT-C-003: verified papers sorted by citations; highest cited = seminal; max 5; unverified dropped."""
    metas = {"A": {"citations": 50}, "B": {"citations": 5000}, "C": None, "D": {"citations": 300}}
    mocker.patch("core.citations.lookup", side_effect=lambda p, session=None: (
        None if metas[p["title"]] is None else {**metas[p["title"]], "verified_title": p["title"], "year": 2024, "doi": ""}))
    papers = [{"title": t, "arxiv_id": "2401.00001"} for t in "ABCD"]
    out, stats = citations.verify_papers(papers, max_papers=5)
    assert [p["title"] for p in out] == ["B", "D", "A"]
    assert out[0]["is_seminal"] and not out[1]["is_seminal"]
    assert out[0]["stars"] == "★★★" and stats["dropped_titles"] == ["C"]


def test_t_cit_n_001_title_search_requires_close_match():
    """T-CIT-N-001: title fallback rejects unrelated results (anti-hallucination)."""
    s = _Session({"/works": (200, {"results": [{"display_name": "A completely different paper"}]})})
    assert citations.lookup({"title": "Invented Paper About Quantum Transformers"}, session=s) is None


# ── CL-071: credibility score and selection rules ────────────────────────────
from datetime import date

TODAY = date(2026, 11, 1)


def _meta(title, cites, pub, venue="", vtype="repository", pct=None, oa=True, insts=(), rel=0.8, retracted=False,
          top1=False):
    m = {"openalex_id": f"W-{title}", "verified_title": title, "title": title, "citations": cites,
         "publication_date": pub, "year": int(pub[:4]), "venue": venue, "venue_type": vtype, "percentile": pct,
         "is_oa": oa, "institutions": list(insts), "is_retracted": retracted, "top_1pct": top1, "top_10pct": top1}
    m["relevance"] = rel
    m["score"], m["score_parts"] = citations.paper_score(m, rel, TODAY)
    return m


def test_t_cit_c_010_paper_score_formula():
    """T-CIT-C-010: score = 0.30 Rel + 0.25 Impact + 0.15 Venue + 0.15 Recency + 0.10 Open + 0.05 Authority."""
    m = _meta("Gershman 2015", 1200, "2015-07-17", venue="Science", vtype="journal", pct=0.99, oa=False,
              insts=["Princeton University"], rel=0.9)
    parts = m["score_parts"]
    assert parts == {"relevance": 0.9, "impact": 0.99, "venue": 1.0, "recency": 0.4, "openness": 0.2, "authority": 1.0}
    assert abs(m["score"] - (0.30 * 0.9 + 0.25 * 0.99 + 0.15 * 1.0 + 0.15 * 0.4 + 0.10 * 0.2 + 0.05 * 1.0)) < 0.001


def test_t_cit_c_011_gates_drop_retracted_irrelevant_and_low_cited():
    """T-CIT-C-011: retracted, relevance < 0.60, and < 10 citations (unless new and peer-reviewed) are rejected."""
    cands = [_meta("Retracted", 500, "2020-01-01", retracted=True),
             _meta("Off topic", 900, "2019-01-01", rel=0.4),
             _meta("Old preprint, 3 cites", 3, "2024-01-01"),
             _meta("New NeurIPS paper, 2 cites", 2, "2026-06-01", venue="NeurIPS", vtype="conference"),
             _meta("Solid", 400, "2021-01-01")]
    sel, rej = citations.select_papers(cands, max_papers=5, today=TODAY)
    assert {r["title"] for r in rej} == {"Retracted", "Off topic", "Old preprint, 3 cites"}
    assert {s["title"] for s in sel} == {"New NeurIPS paper, 2 cites", "Solid"}


def test_t_cit_c_012_seminal_is_most_cited_relevant_and_old_enough():
    """T-CIT-C-012: seminal = most cited with relevance >= 0.70 and age >= 3 years (not a hot new paper)."""
    cands = [_meta("Hot 2026 paper", 5000, "2026-01-10", rel=0.95),
             _meta("Classic 2015", 3000, "2015-05-01", rel=0.85),
             _meta("Loosely related classic", 90000, "2012-01-01", rel=0.65)]
    sel, _ = citations.select_papers(cands, max_papers=5, today=TODAY)
    assert sel[0]["title"] == "Classic 2015" and sel[0]["is_seminal"]
    assert sum(1 for s in sel if s["is_seminal"]) == 1


def test_t_cit_c_013_at_least_one_recent_paper_when_available():
    """T-CIT-C-013: if no paper from the last 24 months makes the cut, the weakest pick is swapped for one."""
    cands = [_meta(f"Old {i}", 2000 + i, f"201{i}-01-01", venue="ICML", vtype="conference", pct=0.99, rel=0.95)
             for i in range(6)] + [_meta("Recent", 40, "2026-02-01", rel=0.61, pct=0.5)]
    sel, _ = citations.select_papers(cands, max_papers=5, today=TODAY)
    assert len(sel) == 5 and "Recent" in [s["title"] for s in sel]


def test_t_cit_c_014_search_pool_relevance_sorted_without_repeats():
    """T-CIT-C-014 (CL-073): pool runs one relevance-sorted query per sub-concept, no most-cited sort, no repeats;
    reads field, keywords and topics."""
    work = {"id": "W1", "display_name": "Computational rationality", "publication_year": 2015, "cited_by_count": 1200,
            "primary_location": {"source": {"display_name": "Science", "type": "journal"}},
            "citation_normalized_percentile": {"value": 0.99, "is_in_top_1_percent": True},
            "primary_topic": {"field": {"display_name": "Computer Science"}, "subfield": {"display_name": "Artificial Intelligence"}},
            "keywords": [{"display_name": "Bounded rationality"}],
            "abstract_inverted_index": {"Computational": [0], "rationality": [1]}}
    s = _Session({"/works": (200, {"results": [work]})})
    pool = citations.search_pool(["computational rationality", "ai vs ml"], session=s)
    assert len(pool) == 1 and pool[0]["venue"] == "Science" and pool[0]["top_1pct"]
    assert pool[0]["field"] == "Computer Science" and "Bounded rationality" in pool[0]["tags"]
    assert pool[0]["abstract"] == "Computational rationality" and len(s.calls) == 2


def test_t_cit_c_015_verify_scores_with_topic_and_badges(mocker):
    """T-CIT-C-015: verify_papers grades relevance, records scores/rejections and adds the Top 1% badge."""
    metas = {"Good": {"citations": 1500, "publication_date": "2015-07-17", "top_1pct": True, "venue": "Science",
                      "venue_type": "journal", "verified_title": "Good", "doi": "", "field": "Computer Science"},
             "Weak": {"citations": 900, "publication_date": "2019-01-01", "verified_title": "Weak", "doi": "",
                      "field": "Computer Science"}}
    mocker.patch("core.citations.lookup", side_effect=lambda p, session=None: dict(metas[p["title"]]))
    mocker.patch("core.citations.grade_papers", return_value=[{"grade": 3, "reason": "defines it"},
                                                               {"grade": 1, "reason": "only uses it"}])
    out, stats = citations.verify_papers([{"title": "Good"}, {"title": "Weak"}], topic="What AI Is", today=TODAY)
    assert [p["title"] for p in out] == ["Good"] and out[0]["badge"] == "Top 1%"
    assert stats["rejected"][0]["title"] == "Weak" and "grade 1/3" in stats["rejected"][0]["why"]
    assert stats["scores"][0]["seminal"] and stats["scores"][0]["grade"] == 3



# ── CL-073: category gate, keywords, grader, arXiv ───────────────────────────
ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
 <entry><id>http://arxiv.org/abs/1706.03762v7</id><title>Attention Is All
  You Need</title><summary>The dominant sequence transduction models...</summary><published>2017-06-12T17:57:34Z</published>
  <arxiv:primary_category term="cs.CL" scheme="http://arxiv.org/schemas/atom"/>
  <category term="cs.CL" scheme="http://arxiv.org/schemas/atom"/><category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/></entry>
 <entry><id>http://arxiv.org/abs/2401.00001v1</id><title>Protein folding</title><summary>bio</summary>
  <published>2024-01-01T00:00:00Z</published><arxiv:primary_category term="q-bio.BM"/>
  <category term="q-bio.BM"/></entry>
</feed>"""


def test_t_cit_c_020_arxiv_atom_parsed_with_categories():
    """T-CIT-C-020: arXiv Atom feed -> id, title, categories, primary category."""
    rows = citations._parse_arxiv(ARXIV_XML)
    assert rows[0]["arxiv_id"] == "1706.03762" and rows[0]["title"] == "Attention Is All You Need"
    assert rows[0]["categories"] == ["cs.CL", "cs.LG"] and rows[0]["primary_category"] == "cs.CL"
    assert rows[1]["categories"] == ["q-bio.BM"]


def test_t_cit_c_021_category_gate():
    """T-CIT-C-021 (owner rule 2026-11-02): cs.* / stat.ML or OpenAlex field Computer Science pass; others fail."""
    assert citations.category_ok({"arxiv_categories": ["cs.CL", "cs.LG"]})[0] is True
    assert citations.category_ok({"arxiv_categories": ["stat.ML"]})[0] is True
    assert citations.category_ok({"arxiv_categories": ["q-bio.BM"]})[0] is False
    assert citations.category_ok({"field": "Computer Science"})[0] is True
    assert citations.category_ok({"field": "Psychology"})[0] is False
    assert citations.category_ok({})[0] is None


def test_t_cit_c_022_keyword_overlap_uses_tags_and_subconcepts():
    """T-CIT-C-022: share of topic terms (short title + sub-concepts) found in title/abstract/tags."""
    topic = "What AI Is — Computational Rationality, AI vs ML vs GenAI, and What AI Is Not"
    m = {"verified_title": "Computational rationality: a converging paradigm", "abstract": "",
         "tags": ["Machine learning", "GenAI"]}
    assert citations.keyword_overlap(topic, m) == 1.0   # both countable terms hit: 'computational rationality', 'genai'
    m["tags"] = ["Machine learning"]
    assert citations.keyword_overlap(topic, m) == 0.5   # only 'computational rationality' hits
    assert citations.keyword_overlap(topic, {"verified_title": "Thematic analysis in psychology"}) == 0.0


def test_t_cit_c_023_off_topic_famous_papers_rejected_classic_outside_cs_kept(mocker):
    """T-CIT-C-023 (dry run 2 regression): famous off-topic papers rejected by grade or category; an LLM-proposed
    classic outside Computer Science (Turing 1950, philosophy) is kept when graded 3."""
    metas = {"Turing": {"verified_title": "Computing machinery and intelligence", "citations": 10290,
                        "publication_date": "1950-10-01", "field": "Philosophy", "doi": ""},
             "Fuzzy": {"verified_title": "The concept of a linguistic variable", "citations": 12187,
                       "publication_date": "1975-01-01", "field": "Computer Science", "doi": ""},
             "Thematic": {"verified_title": "Using thematic analysis in psychology", "citations": 194414,
                          "publication_date": "2006-01-01", "field": "Psychology", "doi": ""}}
    mocker.patch("core.citations.lookup", side_effect=lambda p, session=None: dict(metas[p["title"]]))
    mocker.patch("core.citations.grade_papers", return_value=[{"grade": 3, "reason": "defines machine intelligence"},
                                                               {"grade": 0, "reason": "fuzzy logic, not the topic"},
                                                               {"grade": 0, "reason": "unrelated"}])
    out, stats = citations.verify_papers([{"title": t} for t in ("Turing", "Fuzzy", "Thematic")],
                                         topic="What AI Is — Computational Rationality", today=TODAY)
    assert [p["title"] for p in out] == ["Computing machinery and intelligence"] and out[0]["is_seminal"]
    assert {r["title"][:10] for r in stats["rejected"]} == {"The concep", "Using them"}


def test_t_cit_c_024_shortlist_drops_non_cs_before_grading(mocker):
    """T-CIT-C-024: shortlist applies the category gate strictly, then grades only CS candidates."""
    pool = [{"openalex_id": "W1", "verified_title": "Computational rationality in AI agents", "field": "Computer Science",
             "citations": 300, "publication_date": "2020-01-01", "abstract": "", "tags": []},
            {"openalex_id": "W2", "verified_title": "Using thematic analysis in psychology", "field": "Psychology",
             "citations": 194414, "publication_date": "2006-01-01", "abstract": "", "tags": []}]
    mocker.patch("core.citations.search_pool", return_value=pool)
    mocker.patch("core.citations.arxiv_search", return_value=[])
    mocker.patch("core.citations.arxiv_categories", return_value={})
    g = mocker.patch("core.citations.grade_papers", return_value=[{"grade": 3, "reason": "on topic"}])
    picked, allp = citations.shortlist("What AI Is — Computational Rationality", "What AI Is", today=TODAY)
    assert [p["verified_title"] for p in picked] == ["Computational rationality in AI agents"]
    assert len(g.call_args.args[1]) == 1   # psychology paper never sent to the grader


def test_t_cit_c_025_grader_prompt_and_parsing(mocker):
    """T-CIT-C-025: grader prompt carries rubric and examples; grades clamped 0-3 and mapped by id."""
    seen = {}

    def fake(prompt, **k):
        seen["p"] = prompt
        return {"parsed": {"grades": [{"id": "P2", "grade": 7, "reason": "x"}, {"id": "P1", "grade": 1, "reason": "y"}]}}
    mocker.patch("core.gateway.llm_call", side_effect=fake)
    out = citations.grade_papers("Topic", [{"verified_title": "A"}, {"verified_title": "B"}])
    assert out == [{"grade": 1, "reason": "y"}, {"grade": 3, "reason": "x"}]
    assert "AlphaFold" in seen["p"] and "3 = introduces" in seen["p"]


def test_t_cit_c_026_wrong_doi_falls_back_to_title_search():
    """T-CIT-C-026 (CL-074): an LLM DOI resolving to a different paper is not accepted; title search decides."""
    s = _Session({"doi:10.1016/0004-3702(91)90051-K": (200, {"display_name": "Open Information Systems Semantics for "
                                                                           "Distributed Artificial Intelligence"}),
                  "/works": (200, {"results": [{"display_name": "Something else entirely about databases"}]})})
    assert citations.lookup({"title": "Calculative Rationality: Foundational Assumptions of AI",
                             "doi": "10.1016/0004-3702(91)90051-K"}, session=s) is None
    ok = _Session({"doi:10.1126/science.aac6076": (200, {"display_name": "Computational rationality: A converging "
                                                                          "paradigm for intelligence in brains, minds, and machines"})})
    assert citations.lookup({"title": "Computational rationality: A converging paradigm", "doi": "10.1126/science.aac6076"},
                            session=ok)["verified_title"].startswith("Computational rationality")


def test_t_cit_c_027_shortlist_grades_reused_not_regraded(mocker):
    """T-CIT-C-027 (CL-074): a paper already graded in the shortlist keeps that grade (no second, possibly different, grade)."""
    mocker.patch("core.citations.lookup", return_value={"openalex_id": "W9", "verified_title": "Comp rationality",
                                                         "citations": 674, "publication_date": "2015-07-17",
                                                         "field": "Computer Science", "doi": ""})
    g = mocker.patch("core.citations.grade_papers", return_value=[])
    out, _ = citations.verify_papers([{"title": "Comp rationality"}], topic="What AI Is", today=TODAY,
                                     prior_grades={"W9": {"grade": 3, "grade_reason": "defines"}})
    assert out[0]["grade"] == 3 and g.call_count == 0
