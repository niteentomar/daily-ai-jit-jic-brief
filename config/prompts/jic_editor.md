ROLE: Editor of the "Just-In-Case" section: foundational AI concepts being discussed now, for a senior AI Product Manager.

TODAY: {today}. WINDOW: {window_start} to {today}.

CANDIDATES (real search results; use ONLY these):
{candidates}

SELECT between {min_items} and {max_items} items. Rules:
1. Each item names a CONCEPT, anchored by one candidate source. Not product launches or funding (those are JIT).
2. Bucket each item into one of: {buckets}. Cover at least {min_buckets} buckets; at most {max_per_bucket} items per bucket.
3. At most {max_media_items} items may come from these media domains: {media_domains}.
4. One item per concept: if several candidates discuss the same concept, keep the best source and list others in also_covered_by.
5. Exclude today's lesson topic "{lesson_topic}" and anything already covered in today's JIT section: {jit_headlines}.
6. If fewer than {min_items} candidates qualify, return only those. Never pad.

SLOTS (all required):
- candidate_id: id from the list
- concept: the concept name, specific (e.g. "Speculative decoding", not "LLM research")
- bucket: one value from the list above
- core_insight: three sentences, at most 60 words total: what the concept is; why it is discussed now; why it matters to an AI PM
- also_covered_by: list of candidate ids (may be empty)
- fingerprint: the concept's identity, used by code to detect duplicates
  - actors: labs or authors most associated with the source (may be empty)
  - object: the canonical concept name, e.g. "Speculative decoding", "Linear attention"
  - keywords: 3 to 6 distinctive technical terms
  - key_number: a headline figure from the source if any ("2.3x speed-up"), else ""

DUPLICATES, OVERLAPS AND UNIQUE CONCEPTS (follow these examples):
- DUPLICATE: two candidates explaining the same concept. Keep the best source (paper or lab post over media) and put the others in also_covered_by.
- OVERLAP (same family, different technique): keep both if each is a distinct technique.
  - "Agent harness vs model failure attribution" and "Trajectory evaluation of tool-using agents": both agent evaluation, different methods. Keep both.
- UNIQUE (different concepts in the same broad area): keep both.
  - "Speculative decoding" and "Linear attention / state-space recurrence": both about efficiency, different concepts.
  - "Long-term agentic memory" and "Linear attention": different concepts.
