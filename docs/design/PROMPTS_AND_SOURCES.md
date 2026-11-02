# JIC Prompt and Authoritative Source List (DRAFT for review)

Status: draft, not implemented. Covers (a) the JIC news agent and (b) the daily JIC lesson.
Implementation will follow the TDD gates as one CL entry after approval.

---

## 1. Problems found in the current setup

| # | Problem | Evidence (file:line) | Effect |
|---|---|---|---|
| P1 | Sources defined in 4 places that disagree | `main.py:139` `_JIT_SOURCES`, `:150` `_JIC_SOURCES`, `:165` `_LESSON_SOURCES`, plus `config/search_sources.json` | Editing one list does not change the others |
| P2 | Prompts only show the first 10 sources | `main.py:627`, `:679` use `[:10]` | NIST, LMSYS, MITRE ATLAS etc. are never shown to the model |
| P3 | Main search ignores the source list | `tools/search.py:82` `search()` has no domain filter; only `search_broad()` uses `include_domains`, and only the first 8 | "Priority sources" is a polite request, not a filter |
| P4 | No coverage rule for JIC news | `main.py:628-660` | 5 to 10 items can all be from one area (e.g. all agents) |
| P5 | Lesson grounding is thin | `main.py:762-763`: 2 searches, 5 results each (papers + voices) | 3D (applications), 3E (maturity) and 3H (future) are written from model memory |
| P6 | 3F asks for "earlier JIC topics" but never gets the list | `main.py:740` | The model invents what was "covered earlier" |
| P7 | No depth standard | lesson prompt sets minimum counts only | Depth varies by model and day; no link to your course level |
| P8 | Prompts live inside Python strings | `main.py` | Every prompt tweak is a code change (conflicts with requirement 9 and the modularity rule) |

---

## 2. Proposed authoritative source registry (single file: `config/source_registry.json`)

One file, read by the prompts AND passed to Tavily as `include_domains`. Tiers control where a source may be cited.

| Tier | Use | May be cited in | Domains |
|---|---|---|---|
| **T1 Primary research** | Papers, lab research | JIC news, 3C papers, 3G voices | arxiv.org, openreview.net, aclanthology.org, proceedings.mlr.press, papers.nips.cc, huggingface.co/papers, research.google, deepmind.google, ai.meta.com, anthropic.com/research, openai.com/research, microsoft.com/en-us/research, research.nvidia.com, allenai.org, bair.berkeley.edu, hai.stanford.edu, csail.mit.edu |
| **T2 Expert explainers** | Named, credentialed authors | JIC news, 3A-3H, 3G voices | karpathy.github.io, magazine.sebastianraschka.com, cameronrwolfe.substack.com, lilianweng.github.io, huyenchip.com, eugeneyan.com, interconnects.ai (Nathan Lambert), simonwillison.net, hamel.dev, jalammar.github.io, deeplearning.ai/the-batch, huggingface.co/blog, blog.langchain.com, epoch.ai |
| **T3 Governance, safety, security** | Standards and regulators | JIC news, 3D-3H | nist.gov, oecd.ai, artificialintelligenceact.eu, aisi.gov.uk, atlas.mitre.org, genai.owasp.org, partnershiponai.org, aiindex.stanford.edu |
| **T4 Syllabus references** | Textbooks and course sites behind your ETB, RLL, DM and AIBD classes | Lessons only (3A, 3B, 3C) | incompleteideas.net (Sutton & Barto), spinningup.openai.com, statlearning.com (ISLR), d2l.ai, cs231n.stanford.edu, web.stanford.edu/class/cs224n, exp-platform.com (Kohavi, A/B testing) |
| **T5 Reputable media** | Context only, never as a paper or voice | JIC news (max 2 items), 3D, 3E | towardsdatascience.com, technologyreview.com, arstechnica.com, venturebeat.com |
| **Blocked** | Low authority | Never | medium.com (except T2 authors' own blogs), towardsai.net, generic SEO "top 10" sites, YouTube, undated pages |

Notes: Papers With Code was shut down in 2025 (Hugging Face Papers replaces it). Domains will be validated with a live Tavily call during the test run; dead ones get dropped.

---

## 3. JIC news agent: proposed prompt

```
ROLE: Research editor for a senior AI Product Manager's daily brief.

TODAY: {today}. WINDOW: sources dated {jic_window_start} to {today}.

WHAT A JIC ITEM IS: a foundational CONCEPT (architecture, training or
alignment method, inference or systems principle, retrieval or memory
technique, agent pattern, evaluation method, safety or security technique,
governance framework, data practice) that is being actively discussed in
this window. The item names the CONCEPT, anchored by one dated source.
NOT a product launch, funding round or company news (those are JIT).

COVERAGE RULES (breadth):
- Buckets: architecture | training & alignment | inference & systems |
  retrieval & memory | agents & tools | evaluation | safety & security |
  governance & policy | data.
- Return 5 to 10 items spanning AT LEAST 4 buckets, MAX 2 items per bucket.
- Exclude today's lesson topic: "{lesson_topic}".
- Exclude concepts in cooldown (check with query_history).

SOURCE RULES (authority):
- Cite only Tier 1, 2 or 3 sources: {tier123_domains}.
- At most 2 items may use Tier 5 media: {tier5_domains}.
- Never cite: {blocked_domains}. Discard undated pages.

SEARCH PLAN (max 6 searches): group buckets into 3-4 searches; if a bucket
is empty after that, use search_broad for it.

SELF-CHECK BEFORE OUTPUT: count buckets (>= 4), max 2 per bucket, all dates
inside window, no duplicates, no lesson topic. Fix and re-check if any fail.

OUTPUT: JSON array. Keys: topic (the concept, specific, unique), bucket,
source, url, date (YYYY-MM-DD), core_insight (3 sentences: what the concept
is; why it is being discussed now; why it matters to an AI PM).
```

---

## 4. Daily JIC lesson: depth standard and proposed prompt changes

> Superseded by section 8 (lesson spec v2) and decisions D6-D8. Kept for history.

### Depth standard (from your Notion notes)

Your ETB, RLL, Data Mining and AIBD notes follow a consistent shape: core idea, mechanism step by step, key equation read in plain English (Bellman, PPO clip), worked example, limitation, business mapping, "when to use what", one-paragraph executive summary, glossary. The lesson will target that level: **graduate course, PM lens**.

| Section | Current rule | Proposed rule (depth) |
|---|---|---|
| 3A What it is | >= 4 bullets | Definition, components, **step-by-step mechanism**, **key equation with a plain-English reading** (when the topic has one), limitations |
| 3B Intuition | analogy per bullet | Keep analogy + add **one worked mini-example with numbers or a concrete case** |
| 3C Papers | >= 5, from retrieved list | Keep; add the **seminal paper + latest (last 12 months)** rule |
| 3D Where it applies | >= 4 named uses | Add **PM decision guide: when to use / when not to use / cheaper alternative** |
| 3E Maturity | label + 3 bullets | Ground in retrieved industry evidence (new search) |
| 3F Links to earlier JIC | invented | Receives the **actual list of earlier lesson topics**; Day 1 relates to general CS/ML knowledge and must not invent prior coverage |
| 3G Voices | >= 3 | Must come from retrieved T1/T2 sources, dated, with URL |
| 3H What next | >= 4 | Grounded in a new "future directions" search, last 12 months |
| 3I Glossary | >= 8 terms | >= 10 terms, consistent with your Notion glossary style |
| NEW: TL;DR | none | 3-4 sentence executive summary at the top (needs a small template change) |

### Grounding searches (from 2 to 5)

| Search | Feeds | Domains |
|---|---|---|
| Papers (seminal + recent) | 3C | T1 |
| Expert explainers | 3A, 3B | T2 + T4 |
| Named voices | 3G | T1 + T2 |
| Industry use and maturity (12 months) | 3D, 3E | T2 + T3 + T5 |
| Future directions (12 months) | 3H | T1 + T2 |

Budget check: about 5 lesson + 6 JIC + 6 JIT = about 17 Tavily searches per day, about 510 per month. That fits the free tier of 1,000 credits per month (to re-verify on Tavily's pricing page).

---

## 5. Structural change (needs your approval under GOV-X-001)

| Change | Why |
|---|---|
| New `config/source_registry.json` replaces 3 Python tuples + `search_sources.json` | Fixes P1, P2, P3 |
| New `config/prompts/jic_news.md`, `config/prompts/lesson.md` (templates with `{placeholders}`) | Fixes P8; you can edit prompts without code changes (requirement 9) |
| `search()` accepts `include_domains` | Fixes P3 |
| Lesson receives `earlier_topics` from `topic_pool.json` | Fixes P6 |
| Optional `bucket` key on JIC items, logged for the watchdog | Coverage becomes measurable |

## 6. Decisions needed

1. Approve the source registry (add or remove any domains?)
2. JIC window: keep 7 days, or 14 days (foundational research moves slower; JIT stays at 7)?
3. Add the TL;DR section to the lesson (small HTML template change)?
4. Approve moving prompts and sources into `config/` files (structural change)?

---

## 7. Decisions log (2026-11-01)

| # | Decision | Status |
|---|---|---|
| D1 | JIC window = 14 days (JIT stays 7) | Approved |
| D2 | Add TL;DR section to lesson + template | Approved |
| D3 | Move prompts to `config/prompts/`, sources to `config/source_registry.json` | Approved (GOV-X-001) |
| D4 | Search provider chain instead of multiple Tavily accounts (ToS s.3.1, 3.2) | Proposed |
| D5 | Measurable coverage: section rubric + per-topic concept checklist + JIC bucket metrics | Proposed |

---

## 8. Lesson spec v2 (fixed slots, measurable, no per-topic review)

**Principle:** every section has the SAME fixed slots for every topic. The LLM fills slots; code checks counts, word limits and sources. Topic completeness is checked automatically against the topic title's own subtitle terms, so no human review of each topic is needed.

**Sections kept:** TL;DR, 3A, 3C, 3D, 3E, 3H, 3I. **Removed:** 3B (intuition), 3F (links to earlier topics), 3G (voices).

| Section | Fixed slots | Deterministic check (code) |
|---|---|---|
| **TL;DR** | `what` (1 sentence), `why_now` (1 sentence), `pm_takeaway` (1 sentence) | 3 sentences, total <= 75 words |
| **3A What it is** | `definition` (1 sentence, <= 30 words); `problem_solved` (1 sentence); `components` 3-5 x {name, role <= 15 words}; `how_it_works` 3-6 ordered steps; `key_equation` {expression, plain_english} or "none: <reason>"; `examples` 1-2 x {setting, example}; `limitations` exactly 2 | Counts and word caps; every example contains a number or a named product/company; every component name appears in 3I or in `how_it_works` |
| **3C Key papers** | max 5: exactly 1 `seminal`, up to 4 others; each {title, authors, year, arxiv_id or doi, contribution <= 20 words} | ID must resolve (Semantic Scholar, then OpenAlex); unresolved papers dropped; **citation count fetched by code, not the LLM**; stars: ★★★ >= 1,000, ★★ 100-999, ★ 10-99, "new" < 10; seminal = highest-cited; others sorted by citations; at least 1 paper from the last 12 months if any exists |
| **3D Where it applies** | exactly 3 x {company_or_product, use <= 20 words}; `pm_guide` {use_when, avoid_when, cheaper_alternative}, each <= 20 words | Counts, caps, all 3 pm_guide fields present |
| **3E Maturity** | `stage` from fixed list [Research, Emerging, Early production, Mainstream, Commoditized] + `evidence` (1 sentence <= 25 words) | Enum value valid; <= 2 lines rendered |
| **3H What next** | exactly 3 x {direction <= 12 words, expectation <= 30 words, source_url} | Source dated within last 12 months; URL resolves |
| **3I Glossary** | 8-12 x {term, definition <= 25 words} | Each term appears somewhere in TL;DR-3H (ties glossary to content) |

**Automatic topic completeness (no review):** the topic title already lists its sub-concepts after the dash (e.g. "What AI Is: Computational Rationality, AI vs ML vs GenAI, and What AI Is Not"). Code splits the subtitle into required terms; each must appear in 3A or 3I. Score = hits / required; pass = 100%.

**Daily quality score (logged, watchdog-read):** slots_pass % | completeness % | verified_papers / 5 | resolving_urls % | registry_domains %. On any fail: 1 targeted retry for the failing slots only; then deliver with a small "quality note" and log.

**Example, Day 1 "What AI Is", 3A slots (illustrative):**
- definition: "Artificial intelligence is the science and engineering of building systems that choose actions to best achieve goals given what they perceive."
- components: Perception (turns inputs into state) | Reasoning/decision (chooses actions) | Learning (improves from data) | Action (affects environment)
- key_equation: none: Day 1 is conceptual (rational agent maximizes expected utility is stated in words)
- examples: "TikTok's feed picks the next video to maximize predicted watch time" | "A card issuer's fraud model blocks a payment when fraud probability exceeds a set threshold, e.g. 0.9"
- limitations: "Rational on its objective, not on human values" | "Only as good as the objective and data it is given"

**Template impact:** `email_template.html` drops 3B and 3F blocks, adds a TL;DR box at the top of the lesson, star badges in 3C, and a one-line 3E.

**Search providers:** Tavily -> Exa -> DuckDuckGo. Exa follows its official skill: `/search` with `contents.highlights`; `includeDomains` = approved registry (explicit allowlist), `startPublishedDate` = enforced window (14 days JIC news, 12 months lesson sources). Python SDK `exa-py`.

**Citation lookups:** Semantic Scholar (merges arXiv + venue counts; free, rate-limited) then OpenAlex singleton lookup by DOI (free, unlimited singleton calls per OpenAlex docs).

| D6 | Remove 3G (voices) | Approved |
| D7 | 3A slots: run as specified, review after first 2 live runs, then adjust | Approved |
| D8 | Lesson spec v2 confirmed (TL;DR, 3A, 3C max 5 with stars, 3D, 3E 1-2 lines, 3H, 3I) | Approved |

---

## 9. JIT: root causes of past failures (from code + archived logs, Jun 18 to Jul 16)

| Symptom you saw | Root cause | Evidence |
|---|---|---|
| Same news repeated next day | Only the lesson topic is ever written to the ledger. JIT/JIC news items are never stored, so the 7-day cooldown check always returns "Not Found" | `main.py:904` writes `lesson_topic` only |
| (same) | Cooldown lookup is an exact, case-sensitive string match, so a reworded headline never matches | `tools/memory.py:50` `WHERE topic = ?` |
| (same) | When the agent returned < 5 valid items, gap-fill **deliberately ignores cooldown** | `main.py:476` "R-001-GAP: cooldown is not checked here" |
| Same story from different sources in one email | De-duplication is by URL only; TechCrunch and VentureBeat covering one launch = 2 items | `core/output_normalize.py:125`, `main.py:501` |
| Lesson sometimes missing | Lesson JSON failed validation, fallback "Lesson Unavailable" sent; JSON was free-form text parsed after the fact | log: "Lesson validation failed, substituting fallback" |
| Same lesson sent next day | Pointer advances only if JIT **and** JIC **and** lesson all succeed; a JIT or JIC failure re-sent the same lesson | `main.py:906-908` |
| Gap-fill was common | JIT failed validation 12 times and JIC 14 times in ~20 runs; flash-lite model + loose prompt | archived `launchd_stderr.log` |

## 10. JIT fix design (fixed slots, measurable, code-enforced)

### A. Deterministic memory and de-duplication (code, not LLM)

| Fix | How | Measure |
|---|---|---|
| New append-only `news_ledger` table | Every delivered JIT/JIC item stored: section, headline, story_key, url, domain, date | Rows written = items delivered |
| `story_key` | Lower-case, strip stop-words, keep entities + key nouns, sort tokens | Same story = same key |
| In-email de-dup | Merge items whose keys have Jaccard similarity >= 0.5, or same primary entity + same event type; keep the primary source, list others as "also covered by" | Duplicate stories per email = 0 |
| Cross-day cooldown | Code drops any item whose story_key matched in the last 7 days (JIT) / 14 days (JIC). Rule from your brief: allowed again from day 8 / day 15 | Repeats inside window = 0 |
| Cross-section de-dup | JIT vs JIC vs lesson topic checked against each other | Overlap = 0 |
| Gap-fill obeys the same rules | Remove the R-001-GAP exception | Repeats from gap-fill = 0 |

### B. JIT item fixed slots

| Slot | Rule |
|---|---|
| headline | <= 12 words, names the actor and the event |
| category | one of: model release, product launch, research result, open-source release, funding/M&A, policy/regulation, compute/infrastructure, safety/security incident |
| what_happened | 1 sentence, <= 30 words, includes a number or named product |
| why_it_matters_pm | 1 sentence, <= 30 words, PM lens |
| source, url, date | date within 7 days; primary source preferred |
| also_covered_by | 0-3 URLs (filled by code during de-dup) |

**Section rules:** 5-10 items; >= 4 categories; <= 3 per category; >= 50% primary sources (company or lab's own announcement); 100% dates in window.

### C. JIT source registry (additions to `config/source_registry.json`)

| Tier | Domains |
|---|---|
| **J1 Primary announcements** | openai.com/index, anthropic.com/news, blog.google, deepmind.google/discover/blog, ai.meta.com/blog, blogs.microsoft.com, nvidianews.nvidia.com, mistral.ai/news, huggingface.co/blog, aws.amazon.com/blogs/machine-learning, x.ai/news, qwenlm.github.io, github.blog |
| **J2 Expert curators** | deeplearning.ai/the-batch, simonwillison.net, interconnects.ai, jack-clark.net (Import AI), latent.space, lmarena.ai |
| **J3 Reputable media** | reuters.com/technology, techcrunch.com, theverge.com, venturebeat.com, arstechnica.com, technologyreview.com, wired.com, axios.com/technology |
| **J4 Policy** | digital-strategy.ec.europa.eu, artificialintelligenceact.eu, nist.gov, whitehouse.gov, gov.uk/government/organisations/ai-security-institute |
| Blocked | same as JIC + press-release wires (prnewswire.com, globenewswire.com, businesswire.com) |

### D. Reliability fixes that affect all sections

| Fix | Effect |
|---|---|
| **Structured output**: pass a JSON schema to Gemini (`response_format` json_schema) for JIT, JIC and lesson | Model must return valid slots; removes most "failed validation" |
| **Independent sections**: pointer advances when the lesson succeeds, regardless of JIT/JIC | No more same-lesson-next-day caused by news failures |
| Ledger row written only after successful send | No duplicate ledger rows on failed runs |
| Lesson failure: 1 in-run retry; if still failing, email goes out with a note and the topic retries once next day, then is skipped and logged | Lesson missing at most 1 day per topic |
| Fewer items over repeats: if < 5 clean items after gap-fill, send 3-4 with a "quiet news day" note | Never pads with repeats |
