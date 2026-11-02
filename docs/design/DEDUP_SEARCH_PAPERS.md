# Draft: duplicate detection v2, Tavily diagnosis, paper credibility score

Status: APPROVED 2026-11-01 and implemented (CL-069, CL-070, CL-071).
Source evidence: dry-run `logs/runs/2026-11-01/210455-dry-run` plus online research (sources at end).

---

## 1. Duplicate detection v2 (replaces D15 single threshold)

### 1.1 What the research says

| Source | Method | Lesson for us |
|---|---|---|
| Newscatcher news API | Embedding cosine >= 0.95 flags candidates, then text edit distance (title 0.97, content 0.92) confirms; most authoritative source becomes "parent"; 7-day lookback | Real duplicate thresholds are much higher than 0.70. Cosine alone only nominates; a second signal confirms. Keep the primary source as parent. |
| Newscatcher | Separates **deduplication** (near-copies, removed) from **clustering** (related stories, kept and grouped) | Exactly the user's "duplicate vs overlapping vs unique" split. |
| NewsBlur story clustering (2026) | Title significant-word overlap + semantic "more like this"; shows best version, lists others under it | Keyword overlap on headline is a cheap, strong confirm signal. |
| SemEval-2022 Task 8 (news similarity) | Same story judged on geography, **entities**, **time**, **narrative**; organisation entities correlated best (r=0.455), then dates (0.435) | Use entities (company, product/model) and event date as confirm signals. Caution from the paper: different stories about the **same entity** are the hardest case (our Genie 4 vs Gemini 4 Carbon). |
| Inverted pyramid (journalism style guides) | First paragraph carries who/what/when/where; least important detail is at the end | Use the **lead paragraph** as the main text signal. The last paragraph is mostly background or boilerplate, so it gets low weight (tie-breaker only). |
| Google Gemini embedding docs | `task_type=SEMANTIC_SIMILARITY` is the setting meant for duplicate detection; LiteLLM's default is `RETRIEVAL_QUERY` | We embedded with the wrong task type, which inflates scores for same-topic text. |

### 1.2 Proposed design

Per item the editor LLM already writes a headline and summary. Add a small **story fingerprint** to the editor output (structured, no extra call):

| Field | Example | Use |
|---|---|---|
| `actors` | ["Google DeepMind"] | entity overlap |
| `object` | "Genie 4" | the thing the story is about (model, product, paper, law, deal) |
| `event_type` | "model release" | same category as JIT/JIC group |
| `keywords` | ["world model", "real-time", "interactive"] | 3-6 distinctive terms |
| `key_number` | "10 GW" / "$X bn" / "1T params" or "" | separates follow-ups |

Text signals (code): headline + **lead paragraph** (first 2 sentences of the article snippet) embedded with `SEMANTIC_SIMILARITY`. Closing paragraph only as tie-breaker when available.

Decision rules (code, deterministic, every decision logged with reason):

| Verdict | Rule | Action |
|---|---|---|
| **DUPLICATE** | same URL; OR same `object` + same `event_type` within 3 days; OR cosine >= 0.92 AND entity/keyword overlap >= 0.5 | Merge. Keep highest-tier source as parent; others go to "also covered by". Against history: drop. |
| **OVERLAP** | cosine 0.85-0.92 with shared actor or keywords; OR same `object`, different `event_type` or new `key_number` | Keep both. Show "Related:" link. Against history: keep only as "Update" if it has a new `event_type` or `key_number`; otherwise drop as "follow-up without news". |
| **UNIQUE** | everything else, including same actor with different `object` | Keep. |

Thresholds 0.85 / 0.92 are starting values, calibrated by the golden-set test below (target: 0 false merges, all true duplicates caught).

### 1.3 Examples (go into the editor prompt and the golden test set)

| # | Item A | Item B | Old (0.70) | Expected | Why |
|---|---|---|---|---|---|
| E1 | DeepMind announces Gemini 4 Carbon frontier model | DeepMind unveils Genie 4 world simulator | merged (0.791) | **UNIQUE** | Same actor, different object |
| E2 | OpenAI releases GPT-6.1 Terra | OpenAI and NVIDIA partner on 10 GW datacenter | merged (0.701) | **UNIQUE** | Same actor, different event type |
| E3 | Speculative decoding | Linear attention and state-space recurrence | merged (0.738) | **UNIQUE** | Different concepts, same broad area |
| E4 | Agent harness vs model failure attribution | Trajectory and procedural agent evaluation | merged (0.814) | **OVERLAP** | Both agent evaluation; different technique. Keep both, link |
| E5 | Mistral releases open weights for Mistral Large 4 (mistral.ai) | Mistral open-sources 1-trillion-parameter model (techcrunch.com) | n/a | **DUPLICATE** | Same object + event, different wording. Parent = mistral.ai (J1) |
| E6 | Anthropic files for IPO (Reuters) | Anthropic seeks public listing at $X valuation (Axios) | n/a | **DUPLICATE** | Different messaging, same actor + event + date |
| E7 | Day 1: Anthropic files for IPO | Day 5: Anthropic sets IPO price range | n/a | **OVERLAP, keep as Update** | Same object, new key number |
| E8 | Day 1: Mistral Large 4 released | Day 4: Review: Mistral Large 4 hands-on | n/a | **DUPLICATE vs history (drop)** | Same object + event, no new development |

Golden test: E1-E8 plus all 10 merge decisions from this dry run, labelled. Test fails if any UNIQUE pair is merged.

---

## 2. Tavily diagnosis

**Finding:** not ReAct. The agent wrote sensible queries, and Exa returned 6-8 in-window results for the exact same queries. Tavily was called 16 times (16 credits); 14 window-limited searches ended with 0 kept results, so Exa did the work.

| # | Suspected cause | Layer | Evidence | Status |
|---|---|---|---|---|
| H1 | JIC uses `topic=general`; Tavily returns `published_date` only when `include_published_date=true` (auto only for `news`). Our filter requires a date, so every JIC result is dropped | **System parameters** | Tavily API reference | Confirmed by docs; diag will show |
| H2 | JIT (`topic=news`): our code keeps `published_date[:10]`. If Tavily returns a non-ISO format (for example "Wed, 29 Oct 2026 ..."), the slice cannot be parsed and the window check drops it | **Parsing** | Code review; format to confirm | Pending diag |
| H3 | We pass `days=7`; current Tavily docs list `time_range` and `start_date`/`end_date` only (SDK still accepts `days`) | Parameters | Tavily API reference | Low risk; switch anyway |
| H4 | Tavily `news` index is mainstream media; lab blogs (openai.com etc.) may rarely appear | Source coverage | Tavily docs ("mainstream media") | Diag will show domain mix |

**Proposed fix:** set `include_published_date=True` on all calls; parse dates with ISO then RFC-2822 fallback; use `start_date` (and `time_range=week` for news); log raw vs kept counts and drop reasons per search in `searches.jsonl`; if Tavily keeps 0 for a search, still count it but flag it on the dashboard.

**Your step:** `.venv/bin/python scripts/tavily_diag.py` (about 4 Tavily credits, no LLM calls). It prints each raw result and why it is kept or dropped.

---

## 3. Lesson papers: credibility dimensions and score

### 3.1 What the research says

| Audience | Signals they use | Source |
|---|---|---|
| Researchers / academics | Venue reputation and peer review; author and institution; citation count ("at least two digits" even for recent work); recency for empirical work (theory can be older); methods transparency; open data and code | Integrating replicability into scholarly search (arXiv 2311.00653) |
| Bibliometrics | Raw citations favour old papers; normalise by field and year (FWCI, citation percentile) | OpenAlex fields; Bradford metrics guide |
| Semantic Scholar | "Highly influential citations": the cited paper materially shaped the citing paper | Semantic Scholar FAQ |
| ML practitioners / business | Public code ("no code = no trust"), standard benchmarks, recent strong baselines, honest limitations, independent reproduction | Reading ML papers guide (codesota) |
| Integrity | Exclude retracted work | OpenAlex `is_retracted` |

### 3.2 Proposed formula (all inputs from free OpenAlex fields)

Gates (must pass): verified in OpenAlex; not retracted; relevance >= 0.60.

`PaperScore = 0.30 Relevance + 0.25 Impact + 0.15 Venue + 0.15 RecencyFit + 0.10 Openness + 0.05 Authority`

| Dimension | Measure (0-1) | Data |
|---|---|---|
| Relevance | cosine(topic short title + definition, paper title + abstract) | embedding |
| Impact | `citation_normalized_percentile.value` (field and year normalised); fallback min(1, log10(1 + citations per year) / 3) | OpenAlex |
| Venue | 1.0 top venue list (NeurIPS, ICML, ICLR, ACL, EMNLP, CVPR, Nature, Science, JMLR, TMLR...); 0.7 other peer-reviewed journal/conference; 0.4 preprint | `primary_location.source` |
| RecencyFit | 1.0 if <= 2 years; 0.7 if <= 5; 0.4 older (seminal slot exempt) | `publication_year` |
| Openness | 1.0 open access + code link; 0.6 open access; 0.2 closed | `open_access`, abstract/URL |
| Authority | 1.0 if a T1 lab or top-100 institution; else 0.5 | `authorships.institutions` |

Selection (max 5):
1. **Seminal (1):** highest citations among papers with relevance >= 0.70 and age >= 3 years.
2. **Others (up to 4):** highest PaperScore; at least 1 from the last 24 months if any qualifies.
3. Drop any paper with < 10 citations unless it is <= 18 months old and Venue >= 0.7.

Retrieval change: add an OpenAlex search on the topic's **short title** (before the dash) as a candidate source, next to the web grounding, so classics like Gershman et al. 2015 (computational rationality) are found.

Display: keep stars; add "Top 1%" / "Top 10%" badge from the percentile.

---

## 4. Sources

- Newscatcher, Articles deduplication: https://www.newscatcherapi.com/docs/news-api/guides-and-concepts/articles-deduplication
- NewsBlur, Story clustering (2026): https://blog.newsblur.com/2026/03/18/story-clustering/
- GateNLP-UShef at SemEval-2022 Task 8: https://arxiv.org/pdf/2205.15812
- Inverted pyramid: https://owl.purdue.edu/owl/subject_specific_writing/journalism_and_journalistic_writing/the_inverted_pyramid.html
- Gemini embeddings (task types): https://ai.google.dev/gemini-api/docs/embeddings
- Tavily Search API reference: https://docs.tavily.com/documentation/api-reference/endpoint/search
- Integrating replicability into scholarly search: https://arxiv.org/pdf/2311.00653
- Semantic Scholar influential citations: https://www.semanticscholar.org/faq/influential-citations
- Reading ML papers (practitioner checklist): https://codesota.com/guides/reading-ml-papers
- OpenAlex Works fields: https://developers.openalex.org/api-reference/works
- Pros and cons of key metrics (Bradford): https://www.brad.ac.uk/library/my-library/research-support/bibliometrics-and-altmetrics/The_pros_and_cons_of_key_metrics.pdf
