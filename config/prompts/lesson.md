ROLE: Instructor writing one graduate-level lesson for a senior AI Product Manager (PM lens, MSBA-level depth).

TOPIC: {topic}

REQUIRED CONCEPTS: every one of these must be explained in 3A or defined in the glossary: {required_terms}

GROUNDING SOURCES (retrieved today; prefer these, do not invent sources):
PAPERS:
{papers}
EXPLAINERS:
{explainers}
INDUSTRY USE (last 12 months):
{industry}
FUTURE DIRECTIONS (last 12 months):
{future}

WRITE THESE SLOTS (fixed structure, same for every topic):

TL;DR (3 sentences, at most 75 words in total: keep each sentence under 25 words)
- tldr_what: one sentence, what it is
- tldr_why_now: one sentence, why it matters now
- tldr_pm_takeaway: one sentence, what a PM should do or decide with this

3A WHAT IT IS
- definition: one sentence, at most 30 words
- problem_solved: one sentence
- components: 3 to 5 items, each with name and role (role at most 15 words)
- how_it_works: 3 to 6 ordered steps, one sentence each
- key_equation: if the topic has a central equation give expression (plain text) and plain_english; otherwise expression "none" and plain_english gives the reason
- examples: 1 or 2 concrete examples; each must contain a number or a named product/company
- limitations: exactly 2, one sentence each

3C KEY PAPERS (aim for {max_papers}; some may be dropped by verification)
- exactly one item with is_seminal true (the paper that introduced or defined the topic) and up to {max_others} others
- each: title, first_author, year, arxiv_id (e.g. "1706.03762") or doi, contribution (at most 20 words)
- FIRST name the papers you know introduced or defined this topic and its sub-concepts (classics included); then add strong items from PAPERS above only if they are directly about the topic
- use real papers only; give the arXiv id or DOI ONLY if you are certain (a wrong DOI points to a different paper and gets yours dropped), else leave it empty and the title is used (the pipeline verifies every paper, checks it is filed under Computer Science, grades its relevance and drops the rest)

3D WHERE IT APPLIES
- uses: exactly 3, each with company_or_product and use (at most 20 words)
- pm_guide: use_when, avoid_when, cheaper_alternative (each at most 20 words)

3E MATURITY
- stage: one of Research, Emerging, Early production, Mainstream, Commoditized
- evidence: one sentence, at most 25 words

3H WHAT NEXT
- exactly 3 items: direction (at most 12 words), expectation (at most 30 words), source_url (from the FUTURE or PAPERS lists)

3I GLOSSARY
- 8 to 12 terms, each definition at most 25 words; every term must appear somewhere in the lesson text
