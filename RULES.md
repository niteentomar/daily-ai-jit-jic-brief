# RULES.md — Central Rule Repository
**Project:** Daily JIT/JIC AI Newsletter  
**Version:** 1.0.0  
**Last Updated:** 2026-06-15  
**Owner:** Niteen Tomar

---

## PURPOSE

Single source of truth for all operational rules governing agent behavior, system behavior, and development standards. The implementing agent reads this file in full during Phase 1 (ANCHOR) of every session. Rules with `Active: NO` are retained for history but not enforced.

**Conflict resolution principle:** Lower priority number wins. If two rules conflict, the rule with Priority 1 always overrides Priority 2, and so on. The `Conflict Resolution` column documents the specific override behavior.

---

## RULE TABLE

| Rule ID | Rule Name | Description | Applies To Stage | Priority | Active | Conflict Resolution | Added In | Last Reviewed |
|---------|-----------|-------------|-----------------|----------|--------|---------------------|----------|---------------|
| GOV-X-001 | Structural changes need approval | No architectural change (new folder, new module, new file not in MASTER_PLAN Section 3 folder structure) is implemented without owner's written approval. Agent documents change under `PROPOSED` status in CHANGELOG.md and waits. | ALL | 1 | YES | Overrides all DEV rules. If any DEV rule suggests a structural shortcut, GOV-X-001 wins. | CL-001 | 2026-06-15 |
| GOV-X-002 | Post-deployment structure frozen | After v1.9.0 is deployed: folder structure and module interfaces are frozen. New functionality added as modules only, not rewrites. | ALL | 2 | NO (pre-deployment) | Activates after v1.9.0 deployment. Until then, GOV-X-001 applies. | CL-001 | 2026-06-15 |
| SEC-X-001 | Secrets stay in .env only | API keys, tokens, passwords exist only in `.env`. Never in source files, config files, log files, documentation, or commit diffs. | ALL | 1 | YES | Overrides any convenience shortcut. No exception for "temporary" or "test" usage. | CL-001 | 2026-06-15 |
| SEC-X-002 | .env never committed | `.gitignore` must contain `.env` before any `git add` or commit action. Agent verifies this before every commit. | ALL | 1 | YES | If `.gitignore` does not contain `.env`, agent must add it and verify before proceeding. STOP if cannot verify. | CL-001 | 2026-06-15 |
| SEC-X-003 | Pre-commit secret scan | Before any commit, agent scans all files in the commit diff for secret patterns: `sk-`, `AIza`, `Bearer `, `api_key =`, `token =`, `password =`. Scan covers every file in diff, not just files touched in current task. | HANDOFF | 1 | YES | STOP commit if any match found. Do not proceed until scan is clean. | CL-001 | 2026-06-15 |
| ZT-001 | Fatal crash on key outside .env | If any API key is detected outside `.env` or found in a tracked file, pipeline aborts immediately. `check_env.py` enforces this at startup. | ALL | 1 | YES | Overrides all agent tasks. Aborts instantly. No workaround. | CL-001 | 2026-06-15 |
| ZT-002 | Database least privilege | Database connections permit SELECT and INSERT only. No DROP, DELETE, ALTER, UPDATE on `historical_ledger`. | ALL | 1 | YES | Rejects and logs any payload attempting a prohibited operation. Does not crash pipeline — logs and skips. | CL-001 | 2026-06-15 |
| ZT-003 | Outbound domain whitelist | Outbound network calls permitted only to: Tavily API, LangSmith, SendGrid API, and each configured LLM provider's API (Gemini, Mistral) reached via the LiteLLM Python SDK in-process. All other domains are dropped and logged. | ALL | 1 | YES | Drops unrecognized domain connections. Logs warning. Does not crash pipeline. **Updated 2026-06-16 (TC-002 Phase 1):** removed the "LiteLLM localhost:8000" entry — that assumed a separately-running LiteLLM proxy server, which this project does not use. The gateway calls `litellm.completion()` directly in-process (SDK-direct pattern); there is no local proxy process or `config/litellm_config.yaml`. **Updated 2026-06-17 (TC-006):** removed Gmail SMTP — delivery is SendGrid-only; GMAIL_APP_PASSWORD not available. | CL-001 | 2026-06-17 |
| DEV-A-001 | Read before creating | Agent reads any existing file before creating a same-named file or overwriting. Check-before-create applies to every file operation. | ANCHOR | 2 | YES | Prevents silent overwrite. If conflict found between existing file and task spec, escalate (CLARIFY tier). | CL-001 | 2026-06-15 |
| DEV-A-002 | Locate project root first | Agent verifies project root path before any file operation. Root: `ai-aggregator-system/` under `<home>/... JIT_JIC newsletter/`. | ANCHOR | 1 | YES | If project root not found, STOP. Do not create a new folder. Escalate to owner. | CL-001 | 2026-06-15 |
| DEV-I-001 | Prefer deterministic over probabilistic | Choose deterministic implementation over probabilistic where functionally equivalent. Rule-based routing over LLM-decided routing. Regex over LLM classification. Exact string comparison over fuzzy. | IMPL | 3 | YES | DEV-I-001 over agent judgment. If agent wants probabilistic approach, document reason in TASK_CONTRACT open_issues. | CL-001 | 2026-06-15 |
| DEV-I-002 | No scope creep | Agent implements only what is specified in `files_in_scope` in the TASK_CONTRACT. No additional functionality, files, or modules without escalation. | IMPL | 2 | YES | If agent identifies something useful not in scope, document in TASK_CONTRACT open_issues for next task. Do not implement. | CL-001 | 2026-06-15 |
| DEV-I-003 | Functions max 40 lines | No function body exceeds 40 lines. If longer, split into sub-functions with clear names. | IMPL | 3 | YES | Enforced during Phase 4 self-critique pass. | CL-001 | 2026-06-15 |
| DEV-I-004 | Files max 300 lines | No source file exceeds 300 lines. If longer, split module at logical seam. | IMPL | 3 | YES | Enforced during Phase 4 self-critique pass. | CL-001 | 2026-06-15 |
| DEV-I-005 | No direct llm_call() from pipeline entry points, except pure-synthesis tasks with no tool need | All LLM interactions in `main.py` (and any future pipeline entry point) must go through `core.orchestration.run_agent()`. `llm_call()` is an internal gateway primitive — it is called by `run_agent()` internally and must not be imported or called directly from `main.py`. EXCEPTION (CL-037): `_run_lesson_agent()` calls `llm_call()` directly — lesson synthesis needs no tools; routing it through `run_agent()`'s AgentExecutor caused valid Gemini JSON responses to be silently discarded because AgentExecutor expected tool-call format instead of a direct final answer. EXCEPTION (CL-055): `run_agent()` may call `core.tool_agent.run_litellm_tool_loop()` (SDK-direct `litellm.completion` with `stream=False`) for `vertex_ai/` and `gemini/` models inside `_invoke_once()` — AgentExecutor + ChatLiteLLM still hits Google's `streamGenerateContent` endpoint at invoke time despite `streaming=False` on the constructor (CL-047/049), causing empty JIT/JIC output. OpenRouter/Mistral fallbacks continue using AgentExecutor. JIT/JIC still enter via `run_agent()` from `main.py` — not via direct `llm_call()`. | IMPL | 2 | YES | If agent routes a pipeline step directly to `llm_call()` from `main.py` for a task that needs tools, reject and refactor through `run_agent()`. The CL-037 exception applies only to pure knowledge-synthesis tasks with no tool dependency. The CL-055 exception applies only inside `run_agent()` for Google-provider models — do not call `llm_call()` with tools from `main.py`. DEV-I-005 over DEV-I-001 when the two conflict on this point. | CL-010, CL-037, CL-055 | 2026-06-26 |
| DEV-I-006 | vertex_ai/ and gemini/ are different auth paths — never mix | `vertex_ai/` models (MODEL_1/2 since CL-041) authenticate via `GOOGLE_APPLICATION_CREDENTIALS` env var (absolute path to a service-account JSON file). `_get_api_key()` returns `None` for `vertex_ai/` models — LiteLLM picks up `GOOGLE_APPLICATION_CREDENTIALS` automatically via Google ADC. Do NOT pass `api_key=` to `litellm.completion()` for `vertex_ai/` models — it will conflict with ADC and cause an auth failure. The `gemini/` prefix (AI Studio) uses `GEMINI_API_KEY` and is kept in the codebase as a fallback branch — do not remove it. `vertex_ai/gemini-2.5-flash` and `gemini/gemini-2.5-flash` route to the same underlying model but authenticate completely differently — never assume they're interchangeable. | IMPL | 2 | YES | If agent adds `api_key=` to a `vertex_ai/` model's `litellm.completion()` call, reject — it conflicts with ADC. If agent removes the `gemini/` fallback branch from `_get_api_key()`, reject — needed if Vertex credit runs out. | CL-041 | 2026-06-22 |
| TST-T-001 | Tests before code | Test cases written and registered in TEST_REGISTRY.md before any implementation code is written. Tests must fail before implementation begins (confirms they test real behavior). | TEST | 1 | YES | No exceptions. If agent writes implementation before tests, Phase 2 checklist fails. Block handoff. | CL-001 | 2026-06-15 |
| TST-T-002 | Binary acceptance criteria | Every test case must have a binary pass condition — not "works correctly" but an exact assertion (return value, exit code, file state). | TEST | 2 | YES | Subjective criteria are rejected during Phase 4 review. | CL-001 | 2026-06-15 |
| TST-T-003 | Full suite before handoff | Before Phase 5 handoff, agent runs ALL tests in TEST_REGISTRY.md — not just the current task's tests. Any previously PASSING test that now fails is a regression. STOP and fix before handoff. | REVIEW | 1 | YES | Regressions block handoff entirely. No exceptions. | CL-001 | 2026-06-15 |
| LOG-H-001 | Changelog always updated | Every task must produce a CHANGELOG.md entry (CL-XXX format) before handoff. Entry must include files affected, tests added/modified, rules involved. | HANDOFF | 2 | YES | If CHANGELOG not updated, handoff is incomplete. Phase 5 checklist fails. | CL-001 | 2026-06-15 |
| LOG-H-002 | Audit log always appended | Every agent session must produce an AUDIT_LOG.md entry (AL-XXX format) before handoff. Append-only — never edited retroactively. | HANDOFF | 2 | YES | If AUDIT_LOG not appended, handoff is incomplete. | CL-001 | 2026-06-15 |
| GIT-H-001 | Plans and .env excluded from git | `docs/plans/`, `docs/protocol/active/`, `docs/protocol/archive/`, `.env`, `logs/`, `database/*.db` never appear in any commit. | HANDOFF | 1 | YES | Agent verifies `.gitignore` contains all required entries before any commit. STOP if any are missing. | CL-001 | 2026-06-15 |
| R-001 | News cooldown (JIT 7 days, JIC 14 days) | Every delivered JIT/JIC item is stored in `news_ledger` with an embedding. Items judged DUPLICATE of a delivered item (same URL, or rule R-013), or a follow-up on the same object without a new development, inside the section window are dropped by code. Re-eligible from day 8 (JIT) / day 15 (JIC). No gap-fill exception (R-001-GAP retired CL-065). | ALL | 2 | YES | Code check, not LLM judgment. Jaccard fallback if embeddings fail. | CL-001, CL-064 | 2026-11-01 |
| R-002 | Token budget auto-switch | If LiteLLM detects token usage ≥ 95% of primary model's daily free limit, automatically route to next fallback in order. Log the switch in `gateway_telemetry_logs`. Never bill user. | ALL | 1 | YES | Triggers fallback chain. Pipeline continues without interruption. | CL-001 | 2026-06-15 |
| R-003 | HTML validation before send | Re-run Jinja2 synthesis if HTML output fails schema validation. Retry once. If second attempt fails, send plain-text fallback. Never send invalid HTML. | ALL | 3 | YES | Retry once then degrade gracefully. Log outcome either way. | CL-001 | 2026-06-15 |
| R-004 | Append-only ledger | `historical_ledger` table in SQLite is append-only. No UPDATE on past records. New state always added as new row. | ALL | 1 | YES | ZT-002 enforces this at DB connection level. Any UPDATE attempt on historical_ledger is rejected and logged. | CL-001 | 2026-06-15 |
| R-005 | Agent iteration cap | Research agents (SDK tool loop) run at most 8 iterations and 6 searches; the editor stage is a single structured call. On the cap the code falls back to the registry query plan. | ALL | 1 | YES | Hard-coded in `core/news.py` (MAX_SEARCHES, RESEARCH_MAX_ITER). | CL-001, CL-065 | 2026-11-01 |
| R-006 | Email retry with backoff | Retry SendGrid send up to 3 times with exponential backoff (tenacity: min 2s, max 10s). Log each attempt. There is no fallback provider. | ALL | 2 | YES | After 3 SendGrid failures, log CRITICAL and return False — pipeline does not crash. **Updated 2026-06-17 (TC-006):** Gmail SMTP removed; SendGrid is the sole delivery provider. | CL-001 | 2026-06-17 |
| R-007 | Editor selects only real candidates | JIT/JIC items must reference a candidate id captured from search tool results; URL, source and date come from the candidate, never from the model. Unknown ids are dropped. | ALL | 1 | YES | Replaces CL-059 normalization for the v2 path (core/output_normalize.py kept for the legacy agent path). | CL-059, CL-065 | 2026-11-01 |
| R-008 | Classified model retries | Retry 429/5xx/timeouts on the same model at most 2 times with exponential backoff from 1 s (Retry-After honoured); never retry 400/401/403/404; then fall back to LITELLM_MODEL_2. Truncation, safety blocks and empty output are treated as errors. | ALL | 1 | YES | Google Vertex API errors guidance. | CL-063 | 2026-11-01 |
| R-009 | No padding on quiet days | If fewer than 5 clean items pass the checks, send only those with a visible quiet-day note. Never fill with repeats or off-window items. | ALL | 2 | YES | Overrides minimum-count rules (D9). | CL-065 | 2026-11-01 |
| R-010 | Save before send | `newsletter.html` and all inputs/outputs are written to the run folder before SendGrid is called; ledgers and pointer change only after a successful send. | ALL | 1 | YES | Enables --resend and audit. | CL-066 | 2026-11-01 |
| R-011 | Sources from the registry only | Search allowlists, windows and citation tiers come from `config/source_registry.json`; blocked domains are never cited. | ALL | 2 | YES | Edit the registry, not code (D3). | CL-062 | 2026-11-01 |
| R-012 | Daily cost guard | No further model calls once a run's cost reaches DAILY_COST_LIMIT_USD (default $2). | ALL | 1 | YES | Budget control (requirement 6). | CL-063 | 2026-11-01 |
| R-013 | Duplicate detection v2 (three verdicts) | DUPLICATE: same object + same event type, or cosine >= 0.92 with entity/keyword overlap >= 0.5 -> merged in-email (parent = best source tier) or dropped against history. OVERLAP: cosine 0.85-0.92 with shared actor/keywords, same object with a different event, or 2+ shared keywords -> kept and linked ("related"); against history a same-object follow-up is kept only with a new event type or key number ("Update"). UNIQUE: everything else, including same actor with a different object. Cosine is on headline + lead paragraph with task_type SEMANTIC_SIMILARITY. Lesson topic / other-section exclusion at cosine >= 0.85. | JIT, JIC | 2 | YES | Thresholds in .env (DEDUPE_OVERLAP_THRESHOLD, DEDUPE_DUPLICATE_THRESHOLD); golden set T-DED-G-001 must pass before any change. | CL-070 | 2026-11-01 |
| R-014 | Paper credibility score | Lesson papers must be verified in OpenAlex, not retracted, and pass three relevance gates (CL-073): (1) category - filed under Computer Science (arXiv cs.* or stat.ML, else OpenAlex field Computer Science); an LLM-proposed classic outside CS passes only with grade 3; (2) LLM grader >= 2 of 3 (3 = defines the topic, 2 = studies a sub-concept, 1 = only uses it, 0 = unrelated); (3) >= 10 citations unless <= 18 months old and peer-reviewed. Relevance = 0.8 x grade/3 + 0.2 x keyword/tag overlap. Score = 0.30 relevance + 0.25 impact + 0.15 venue + 0.15 recency + 0.10 openness + 0.05 authority. Seminal = most cited with grade 3 and age >= 3 years; up to 4 more by score, >= 1 from the last 24 months when one qualifies. Candidates: LLM's own picks first, plus arXiv API (AI categories) and OpenAlex (relevance sort) as optional extras. | LESSON | 2 | YES | Category list and grade thresholds in source_registry.json lesson.paper_filter; absolute embedding cosine is NOT used as relevance (anisotropy). | CL-071, CL-073 | 2026-11-02 |
| R-015 | Search drop reasons logged | Every search logs, per provider, raw results, kept results and why each was dropped (allowlist, no date, outside window, blocked). Exa tops up when Tavily keeps fewer than max(3, n/2). | ALL | 3 | YES | Found the 2026-11-01 Tavily parsing gap. | CL-069 | 2026-11-01 |
| R-016 | Production schedule guards | launchd runs `main.py --scheduled` at 07:00: nothing after SCHEDULE_END_DATE, never a second email on the same day. The watchdog (09:30, no LLM) checks W1-W7, triggers at most ONE catch-up run per day (marker file), then alerts by email if anything is still wrong. | ALL | 1 | YES | Requirement 6 fail-safes: no loops, no double sends, no silent misses. | CL-075 | 2026-11-02 |

---

## RULE ID NUMBERING REFERENCE

```
Format: [DOMAIN]-[STAGE]-[SEQ]

DOMAIN codes:
  GOV  — Governance / structural
  SEC  — Security / Zero Trust
  ZT   — Zero Trust (runtime pipeline rules)
  DEV  — Development standards
  TST  — Testing
  LOG  — Logging / audit
  GIT  — Git / version control
  R    — Runtime pipeline rules (cooldown, token limits, etc.)

STAGE codes:
  A  — Anchor phase
  T  — Test-first phase
  I  — Implementation phase
  R  — Review phase
  H  — Handoff phase
  X  — Cross-phase (applies to all)

SEQ: 3-digit sequence within domain+stage, e.g. 001, 002
```

---

## ADDING NEW RULES

1. Assign the next SEQ number within the appropriate DOMAIN-STAGE combination
2. Fill all columns — no partial entries
3. Set `Active: YES` and today's date in `Last Reviewed`
4. Add a CHANGELOG.md entry referencing the new Rule ID
5. Update the TASK_CONTRACT `rules_updated: true` in the ACTUALS section

*Rules are never deleted — set `Active: NO` with a note in `Conflict Resolution` explaining why it was retired.*
