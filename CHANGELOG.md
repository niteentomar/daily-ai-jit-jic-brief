# CHANGELOG
**Project:** Daily JIT/JIC AI Newsletter (`ai-aggregator-system`)  
**Format:** Append-only. Never edited retroactively. Entries numbered sequentially CL-001, CL-002, ...  
**Owner:** Niteen Tomar

---

## Entry Format

```markdown
## [CL-XXX] — YYYY-MM-DD — [STATUS]

**Type:** FEATURE / BUGFIX / RULE_CHANGE / STRUCTURAL / SECURITY / CONFIGURATION
**Author:** [Agent name or "Owner"]
**Task ID:** [TC-XXX if applicable]
**Status:** PROPOSED / IN_PROGRESS / COMPLETED / REJECTED

### Summary
One paragraph describing what changed and why.

### Files Affected
- `path/to/file.py` — [what changed]

### Rules Added/Modified
- [Rule ID] — [what changed]

### Tests Added/Modified
- [Test ID] — [status]

### Dependencies
- Depends on: [CL-XXX]
- Blocks: [CL-XXX]

### Rollback
[How to undo if needed]

### Owner Approval
- [ ] Approved by Niteen  (required for STRUCTURAL and RULE_CHANGE types)
```

---

## [CL-001] — 2026-06-15 — COMPLETED

**Type:** STRUCTURAL  
**Author:** Owner (Niteen Tomar, assisted by Claude/Cowork)  
**Task ID:** N/A (pre-development planning phase)  
**Status:** COMPLETED

### Summary
Project planning phase complete. MASTER_PLAN.md consolidated to v6.2, incorporating corrections from first Antigravity development attempt. Four confirmed bugs in LITELLM_SETUP.md reference code documented. AGENT_EXECUTION_PROTOCOL.md v1.0.0 created as behavioral contract for all implementing agents. TASK_CONTRACT.yaml template created. HANDOFF_PLAN.md created as single-document brief for Antigravity. Seed files (RULES.md, CHANGELOG.md, TEST_REGISTRY.md, API_REGISTRY.md) created to enable Antigravity's Phase 1 ANCHOR reads. Folder structure (`ai-aggregator-system/`) initialized with canonical layout from MASTER_PLAN Section 3.

### Files Affected
- `MASTER_PLAN.md` — Updated to v6.2: LiteLLM bugs documented, Section 3 folder structure corrected, Section 17 rewritten for protocol-based handoff, "Claude Code" references replaced with "implementing agent"
- `AGENT_EXECUTION_PROTOCOL.md` — Created v1.0.0: 5-phase behavioral contract, escalation tiers, central repository formats, phase checklists
- `TASK_CONTRACT.yaml` — Created: template for per-task scope, boundaries, and acceptance criteria
- `HANDOFF_PLAN.md` — Created: copy-paste brief for Antigravity including opening prompt, task sequence, bug table, escalation quick-card
- `RULES.md` — Created: 26 seed rules across GOV, SEC, ZT, DEV, TST, LOG, GIT, R domains
- `CHANGELOG.md` — Created: this file
- `TEST_REGISTRY.md` — Created: 13 seed test cases from MASTER_PLAN Section 10
- `docs/api_registry/API_REGISTRY.md` — Created: 7 seed API entries from AGENT_EXECUTION_PROTOCOL Section 3.4
- `ANTIGRAVITY_CONTROL_FRAMEWORK.md` — Retired (superseded by AGENT_EXECUTION_PROTOCOL.md); to be deleted from project root

### Rules Added/Modified
- GOV-X-001 through R-006 — All 26 initial rules added (see RULES.md)

### Tests Added/Modified
- T-ENV-C-001 through T-013 — All 13 seed test cases registered (see TEST_REGISTRY.md), status: PENDING

### Dependencies
- Depends on: None (first entry)
- Blocks: CL-002 (TC-001 implementation task)

### Rollback
Delete all files listed above. Revert MASTER_PLAN.md to v6.1.

### Owner Approval
- [x] Approved by Niteen — 2026-06-15 (planning phase, no code written)

---

---

## [CL-002] — 2026-06-15 — COMPLETED

**Type:** STRUCTURAL  
**Author:** Owner (Niteen Tomar, assisted by Claude/Cowork)  
**Task ID:** N/A (pre-development planning phase)  
**Status:** COMPLETED

### Summary
Implementing agent switched from Google Antigravity to Claude Code (CLI). Gate compliance report model introduced: Claude Code produces a structured Gate Compliance Report at the end of each execution phase; Niteen reviews and confirms before the next phase begins. This replaces the ad-hoc review approach that allowed the previous agent to proceed without owner verification. AGENT_EXECUTION_PROTOCOL updated to v1.1.0 with Section 6 (Gate Compliance Reports) added. HANDOFF_PLAN.md updated with Claude Code opening prompt and gate model explanation. MASTER_PLAN.md updated to v6.3.

### Files Affected
- `MASTER_PLAN.md` — Updated to v6.3: Antigravity → Claude Code throughout; Section 1 stack table updated; Section 17 tips updated
- `docs/protocol/AGENT_EXECUTION_PROTOCOL.md` — Updated to v1.1.0: Section 6 (Gate Compliance Reports) added; Section 7 renumbered to Section 8
- `HANDOFF_PLAN.md` — Updated: Antigravity → Claude Code; Section 1 purpose rewritten; Section 3 adds gate report requirement; Section 4 adds per-task gate model; Section 9 updated; Section 11 opening prompt rewritten for Claude Code CLI

### Rules Added/Modified
- None (gate compliance report is a protocol addition, not a rules change)

### Tests Added/Modified
- None

### Dependencies
- Depends on: CL-001
- Blocks: CL-003 (TC-001 implementation task, now assigned to Claude Code)

### Rollback
Revert MASTER_PLAN.md to v6.2, AGENT_EXECUTION_PROTOCOL to v1.0.0, HANDOFF_PLAN.md to prior version.

### Owner Approval
- [x] Approved by Niteen — 2026-06-15

---

---

## [CL-003] — 2026-06-15 — COMPLETED

**Type:** STRUCTURAL  
**Author:** Owner (Niteen Tomar, assisted by Claude/Cowork)  
**Task ID:** N/A (pre-development planning phase)  
**Status:** COMPLETED

### Summary
Two corrections applied. First: Claude Code UI (desktop) confirmed as the interface — not CLI terminal. Second and more significant: task self-management introduced. From TC-002 onward, Claude Code autonomously proposes the SPEC for the next task (SPEC-DRAFT) as part of the Phase 5 Full Task Compliance Report. Niteen reviews the SPEC-DRAFT and replies "approved" or "approved with changes". Claude Code then archives the current contract, writes the new TASK_CONTRACT, and begins the next task Phase 1 — no manual file management by Niteen. TC-001 SPEC is pre-filled as the bootstrap entry. AGENT_EXECUTION_PROTOCOL updated to v1.1.0 with full gate model and self-management logic in Section 6. TASK_CONTRACT.yaml restructured to include SPEC-NEXT section. HANDOFF_PLAN.md updated with simplified gate table and new opening prompt.

### Files Affected
- `docs/protocol/AGENT_EXECUTION_PROTOCOL.md` — v1.1.0: Section 6 fully rewritten with per-phase report format (6.2), full task compliance report (6.3), SPEC-DRAFT format (6.4), owner response options (6.5), autonomous vs. approval-required actions (6.6); Section 7 renamed to Section 8
- `docs/protocol/active/TASK_CONTRACT.yaml` — Restructured: header updated to v1.1.0, TC-001 SPEC pre-filled, SPEC-NEXT section added for Claude Code to propose next task, example updated from Antigravity to Claude Code
- `HANDOFF_PLAN.md` — "CLI" → "desktop UI" in header; Section 4 rewritten as gate-model table; Section 9 simplified to 3-line owner checklist; Section 11 opening prompt rewritten for Claude Code UI with explicit STEP 1/2/3 structure

### Rules Added/Modified
- None

### Tests Added/Modified
- None

### Dependencies
- Depends on: CL-002
- Blocks: CL-004 (TC-001 implementation — now with self-managed progression)

### Rollback
Revert AGENT_EXECUTION_PROTOCOL to v1.1.0 pre-edit, TASK_CONTRACT.yaml to blank template, HANDOFF_PLAN.md to prior version.

### Owner Approval
- [x] Approved by Niteen — 2026-06-15

---

## [CL-004] — 2026-06-16 — COMPLETED

**Type:** FEATURE
**Author:** Claude Code
**Task ID:** TC-001
**Status:** COMPLETED

### Summary
TC-001 complete — v1.0.0 repository scaffold. Created `.gitignore`, `.env.example`,
`requirements.txt`, `README.md`; environment validation in `scripts/check_env.py`
(`validate_env()` rejects missing/empty/placeholder required keys; `scan_for_secrets()`
implements the SEC-X-003 pre-commit scan); a scaffold-only `scripts/setup_db.py` stub
(`init_db()` raises `NotImplementedError`, full implementation deferred to TC-003 —
`database/schema.sql` doesn't exist yet); and the test harness (`tests/conftest.py`,
two mock fixture JSON files for TC-002/TC-003 use, `tests/test_env.py`,
`tests/test_security.py`) — 7/7 tests PASSING. Git repository initialized at the
project root; single initial commit `804c10fc7437c5f850b74863bfce2fba62629091`.

One structural finding during Phase 4 review: literal secret-pattern substring
matching produced 9 false positives when scanning the actual staged diff — the
bare `sk-` pattern coincidentally matches English compound words ("Task-level",
"task-specific") in `MASTER_PLAN.md` and `AGENT_EXECUTION_PROTOCOL.md`, and
`RULES.md` / `AGENT_EXECUTION_PROTOCOL.md` must literally document the SEC-X-003
pattern list to explain the rule. Commit was blocked until owner reviewed and
approved a 3-part fix: tightened `sk-` to a regex requiring a realistic key-length
run (`sk-[A-Za-z0-9_-]{16,}`), reworded two `TEST_REGISTRY.md` acceptance-criteria
cells to stop quoting the literal patterns, and added `RULES.md` +
`AGENT_EXECUTION_PROTOCOL.md` (both `files_forbidden`, cannot be reworded) to a
documented `SELF_EXCLUDED_FILES` allowlist in `check_env.py`. Re-scan after the fix:
0 findings.

### Files Affected
- `scripts/check_env.py` — Created: `validate_env()`, `scan_for_secrets()`, CLI entry point
- `scripts/setup_db.py` — Created: stub, `NotImplementedError` (TC-003 scope)
- `.env.example` — Created: all REQUIRED_KEYS + OPTIONAL_KEYS placeholders
- `.gitignore` — Created: union of all 3 source documents' required entries
- `requirements.txt` — Created: pinned versions for full MASTER_PLAN stack
- `README.md` — Created: setup guide, API key sources, security note
- `tests/conftest.py` — Created: `mock_llm`, `mock_search` fixtures
- `tests/mocks/mock_llm_responses.json` — Created: fixtures for TC-002
- `tests/mocks/mock_search_results.json` — Created: fixtures for TC-003
- `tests/test_env.py` — Created: T-ENV-C-001, E-001, N-001, N-002
- `tests/test_security.py` — Created: T-SEC-S-001, S-002, N-001
- `TEST_REGISTRY.md` — Updated: added T-ENV-E-001, T-SEC-N-001; all 7 TC-001 rows PASSING
- `AUDIT_LOG.md` — Created: AL-001, AL-002 (this task's session entries)
- `docs/plans/PLAN_TC001_repo_init.md` — Created: 7 implementation decisions documented (working doc, not committed)

### Rules Added/Modified
- None (SEC-X-003's *enforcement implementation* was refined; the rule text in RULES.md was not changed)

### Tests Added/Modified
- T-ENV-C-001 — PASSING
- T-ENV-E-001 — PASSING (new)
- T-ENV-N-001 — PASSING
- T-ENV-N-002 — PASSING
- T-SEC-S-001 — PASSING
- T-SEC-S-002 — PASSING
- T-SEC-N-001 — PASSING (new)

### Dependencies
- Depends on: CL-003
- Blocks: CL-005 (TC-002 — LiteLLM Gateway)

### Rollback
Delete `scripts/check_env.py`, `scripts/setup_db.py`, `tests/test_env.py`,
`tests/test_security.py`, `tests/conftest.py`, `tests/mocks/`. Revert the 7
TC-001 rows in `TEST_REGISTRY.md` to `PENDING`. Git history itself is the single
initial commit — reverting it returns the repo to an uninitialized state.

### Owner Approval
- [x] Approved by Niteen — 2026-06-16 (3-part secret-scan fix approved in-session; git init and commit message specified directly)

---

---

## [CL-005] — 2026-06-16 — COMPLETED

**Type:** FEATURE
**Author:** Claude Code
**Task ID:** TC-002
**Status:** COMPLETED

### Summary
TC-002 complete — LiteLLM gateway implementation. Created `core/__init__.py` and `core/gateway.py`
implementing the full LiteLLM SDK-direct gateway: `llm_call()` (returns `{response, model_used,
tokens_used, cost=0.0, timestamp}`), `_check_token_limit()`, `_require_provider_prefix()`,
`_today_str()`, `_log_token_usage()`, `_save_token_log()`, `_load_token_log()`, `_scrub_secrets()`,
`_build_model_chain()`, and `TokenBudgetExceededError`. All four bugs from MASTER_PLAN Section 4.4
fixed: BUG-001 (token limit reads `DAILY_TOKEN_LIMIT_GEMINI` env var, no wrong attribute reference),
BUG-002 (`_require_provider_prefix()` enforces `/` separator in model strings), BUG-003
(`os.makedirs("logs", exist_ok=True)` before every write), BUG-004 (`_scrub_secrets()` scrubs
all configured API key values from log output before emission). One additional bug found and fixed
in the TC-002 test helper `_set_env`: the unconditional `monkeypatch.delenv("MISTRAL_API_KEY")`
was deleting the key even when the caller had explicitly set it via `overrides`, making T-GAT-E-001
impossible to pass; fixed to skip the `delenv` when the key appears in `overrides`. Final result:
14/14 tests green (7 T-GAT-* + 7 TC-001 ENV/SEC, zero regressions). Python interpreter mismatch
also diagnosed and resolved post-OS-crash restart: `python3 -m pip install` required (not bare
`pip`) to target the correct Python 3.14 environment.

### Files Affected
- `core/__init__.py` — Created: package marker
- `core/gateway.py` — Created: full gateway implementation (BUG-001 through BUG-004 fixed)
- `tests/test_gateway.py` — Modified: `_set_env` helper — `delenv` now skipped when `MISTRAL_API_KEY` is in `overrides`

### Rules Added/Modified
- R-002 (cost control) — enforced via `_check_token_limit()` and failover chain
- ZT-001 (secret isolation) — enforced via `_scrub_secrets()` in all log paths

### Tests Added/Modified
- T-GAT-C-001 — PASSING (was FAILING)
- T-GAT-E-001 — PASSING (was FAILING; required `_set_env` fix)
- T-GAT-E-002 — PASSING (was FAILING)
- T-GAT-E-003 — PASSING (was FAILING)
- T-GAT-N-001 — PASSING (was FAILING)
- T-GAT-N-002 — PASSING (was FAILING)
- T-GAT-S-001 — PASSING (was FAILING)

### Dependencies
- Depends on: CL-004 (TC-001 — repo scaffold, `requirements.txt`, test harness)
- Blocks: CL-006 (TC-003 — tools layer: memory, search, database)

### Rollback
Delete `core/__init__.py` and `core/gateway.py`. Revert `tests/test_gateway.py:_set_env` to
unconditional `delenv`. Revert all 7 T-GAT-* rows in `TEST_REGISTRY.md` to `FAILING`.

### Owner Approval
- [ ] Approved by Niteen

---

---

## [CL-006] — 2026-06-16 — COMPLETED

**Type:** FEATURE
**Author:** Claude Code
**Task ID:** TC-003
**Status:** COMPLETED

### Summary
TC-003 complete — tools layer: memory, search, and database foundation. Created
`database/schema.sql` with three tables (`historical_ledger`, `gateway_telemetry_logs`,
`system_exceptions`) and a BEFORE DELETE trigger on `historical_ledger` that calls
`RAISE(ABORT, ...)` to enforce the R-004 append-only rule at the database level.
Implemented `tools/memory.py` with `query_history(topic, conn=None)` — queries the
ledger for the most recent coverage date, returns `{status, last_covered, delta_days}`;
`conn` is dependency-injected for tests (in-memory SQLite) and defaults to the
production `database/ledger.db` file. Implemented `tools/search.py` with
`search(query, n=5)` using Tavily as primary and DuckDuckGo as automatic fallback;
both raw response shapes are normalised to the locked contract `{title, url, summary, date}`.
Upgraded `scripts/setup_db.py` from TC-001 `NotImplementedError` stub to a full
`init_db()` that creates the `database/` directory and runs the schema script.
Added `test_db` fixture to `tests/conftest.py` (in-memory SQLite initialised from
`database/schema.sql`). Final result: 19/19 tests green (5 new T-MEM/T-SRC/T-DB +
14 prior, zero regressions).

### Files Affected
- `database/schema.sql` — Created: three-table schema + R-004 DELETE trigger
- `tools/__init__.py` — Created: package marker
- `tools/memory.py` — Created: `query_history()` with dependency-injected conn
- `tools/search.py` — Created: `search()` with Tavily→DuckDuckGo fallback, normalised output
- `scripts/setup_db.py` — Updated: full `init_db()` replacing NotImplementedError stub
- `tests/conftest.py` — Updated: added `test_db` fixture (v1.1.0)
- `tests/test_tools.py` — Created: 5 new test cases (T-MEM-C-001, T-MEM-E-001, T-SRC-C-001, T-SRC-E-001, T-DB-N-001)
- `TEST_REGISTRY.md` — Updated: 5 T-MEM/T-SRC/T-DB rows → PASSING, version → 1.2.0

### Rules Added/Modified
- R-001 (7-day cooldown) — enforced via `query_history()` return value
- R-004 (append-only ledger) — enforced via BEFORE DELETE trigger in `schema.sql`
- ZT-002 (no DELETE/DROP/ALTER) — `memory.py` uses SELECT only; trigger blocks DELETE

### Tests Added/Modified
- T-MEM-C-001 — PASSING (new)
- T-MEM-E-001 — PASSING (new)
- T-SRC-C-001 — PASSING (new)
- T-SRC-E-001 — PASSING (new)
- T-DB-N-001  — PASSING (new)

### Dependencies
- Depends on: CL-005 (TC-002 — gateway), CL-004 (TC-001 — scaffold/requirements)
- Blocks: CL-007 (TC-004 — topic manager + orchestration)

### Rollback
Delete `database/schema.sql`, `tools/__init__.py`, `tools/memory.py`, `tools/search.py`,
`tests/test_tools.py`. Revert `scripts/setup_db.py` to NotImplementedError stub.
Revert `tests/conftest.py` to v1.0.0 (remove `test_db` fixture). Revert 5 T-MEM/T-SRC/T-DB
rows in `TEST_REGISTRY.md` to `PENDING`.

### Owner Approval
- [ ] Approved by Niteen

---

---

## [CL-007] — 2026-06-16 — COMPLETED

**Type:** FEATURE
**Author:** Claude Code
**Task ID:** TC-004
**Status:** COMPLETED

### Summary
TC-004 complete — topic manager and orchestration layer. Created
`config/topic_pool.json` with the 25-topic JIC curriculum seed from MASTER_PLAN
Section 7.1 (`pointer: 0`). Implemented `tools/topic_manager.py` with
`get_next_topic(pool_path)` (returns `topics[pointer % len]`, wraps on exhaustion)
and `mark_topic_done(pool_path)` (increments pointer, persists JSON, wraps to 0
after last topic). Created `core/orchestration.py` with `run_agent(llm, tools,
prompt, max_iter=MAX_ITERATIONS)` — wraps LangChain `AgentExecutor` with hard
`max_iterations=5` (`early_stopping_method="force"`) and logs a WARNING when
LangChain's iteration-limit stop phrase is detected in the output, satisfying R-005.
Two new tests written (TDD): T-TOP-C-001 (topic pointer advances across tmp_path
fixture), T-ORC-C-001 (AgentExecutor constructed with max_iterations=5; WARNING
logged on limit hit). Final result: 21/21 tests green, zero regressions.

### Files Affected
- `config/topic_pool.json` — Created: 25-topic seed, pointer=0
- `tools/topic_manager.py` — Created: `get_next_topic()`, `mark_topic_done()`
- `core/orchestration.py` — Created: `run_agent()` wrapper, `MAX_ITERATIONS=5`
- `tests/test_tools.py` — Updated: T-TOP-C-001 appended (v1.1.0)
- `tests/test_orchestration.py` — Created: T-ORC-C-001
- `TEST_REGISTRY.md` — Updated: T-TOP-C-001, T-ORC-C-001 → PASSING, version → 1.3.0

### Rules Added/Modified
- R-005 (max_iterations=5 hard stop) — enforced via `AgentExecutor(max_iterations=MAX_ITERATIONS)`
- GOV-001 (deterministic topic order) — topic pointer is rule-based, never LLM-decided

### Tests Added/Modified
- T-TOP-C-001 — PASSING (new)
- T-ORC-C-001 — PASSING (new)

### Dependencies
- Depends on: CL-006 (TC-003 — tools layer)
- Blocks: CL-008 (TC-005 — synthesis + HTML rendering)

### Rollback
Delete `config/topic_pool.json`, `tools/topic_manager.py`, `core/orchestration.py`,
`tests/test_orchestration.py`. Revert `tests/test_tools.py` to v1.0.0 (remove
T-TOP-C-001 block and header import). Revert T-TOP-C-001 and T-ORC-C-001 rows in
`TEST_REGISTRY.md` to `PENDING`.

### Owner Approval
- [ ] Approved by Niteen

---

---

## [CL-008] — 2026-06-17 — COMPLETED

**Type:** FEATURE
**Author:** Claude Code
**Task ID:** TC-005
**Status:** COMPLETED

### Summary
TC-005 complete — synthesis layer. `config/email_template.html` (Jinja2, placed by
Cowork session) renders the full newsletter: header, critical-summary box, JIT news
table (5-column), JIC news table (5-column), daily lesson sections 3A–3I (What Is It,
Intuition, Key Research Papers, Where It Applies, Maturity Status, Historical Context,
Authoritative Voices, What's Coming Next, Glossary), and a footer with run metadata.
Implemented `core/synthesis.py` with `render(context)→str` (loads template via
Jinja2 `FileSystemLoader`, calls `validate()`, retries once on failure, returns
plain-text fallback on second failure — R-003) and `validate(html)→bool` (checks all
14 required section markers are present). T-SYN-C-002 test corrected: broadened
regex was scoped to JIT/JIC `<tbody>` blocks only (per the acceptance criteria wording
"JIT and JIC tables"); other lesson sub-tables (papers/voices/glossary) have
different column counts and are not subject to the 5-column rule. Final result:
25/25 tests green, zero regressions.

### Files Affected
- `config/email_template.html` — Placed by Cowork session; not modified
- `core/synthesis.py` — Created: `render()`, `validate()`, `_render_template()`, `_plain_text_fallback()`
- `tests/test_synthesis.py` — Placed by Cowork session (red phase); T-SYN-C-002 regex scoped to JIT/JIC bodies
- `TEST_REGISTRY.md` — Updated: T-SYN-C-001, T-SYN-C-002, T-SYN-N-001, T-FMT-C-001 → PASSING, version → 1.4.0

### Rules Added/Modified
- R-003 (retry-once on validation failure) — enforced in `render()`: retry + plain-text fallback

### Tests Added/Modified
- T-SYN-C-001 — PASSING (new)
- T-SYN-C-002 — PASSING (new, test corrected to scope JIT/JIC tbody only)
- T-SYN-N-001 — PASSING (new)
- T-FMT-C-001 — PASSING (new)

### Dependencies
- Depends on: CL-007 (TC-004 — topic manager + orchestration)
- Blocks: CL-009 (TC-006 — delivery layer)

### Rollback
Delete `core/synthesis.py`, `tests/test_synthesis.py`. Revert T-SYN-C-001,
T-SYN-C-002, T-SYN-N-001, T-FMT-C-001 rows in `TEST_REGISTRY.md` to `PENDING`.
`config/email_template.html` was placed externally and should be retained.

### Owner Approval
- [ ] Approved by Niteen

---

---

## [CL-009] — 2026-06-17 — COMPLETED

**Type:** FEATURE + GOVERNANCE UPDATE
**Author:** Claude Code
**Task ID:** TC-006
**Status:** COMPLETED

### Summary
TC-006 complete — delivery layer, SendGrid-only. Architecture correction applied
before implementation: Gmail SMTP dropped (GMAIL_APP_PASSWORD not available);
SendGrid is the sole provider. `core/delivery.py` implements `send_email(html, to)→bool`:
constructs a `sendgrid.helpers.mail.Mail` object, sends via `SendGridAPIClient`,
retries up to 3 times with exponential backoff via tenacity `@retry` on inner
`_send_with_retry()` (R-006). On exhaustion, logs CRITICAL and returns False —
pipeline does not crash. Credentials: `SENDGRID_API_KEY` and `TARGET_EMAIL` only.
`sendgrid==6.12.5` added to `requirements.txt`. Governance files updated: RULES.md
R-006 reworded (SendGrid-only, no fallback), ZT-003 Gmail SMTP removed from domain
whitelist. MASTER_PLAN.md Section 4.3 email table and Section 5.3 graceful-degradation
row updated to reflect SendGrid-only delivery. Final result: 27/27 tests green,
zero regressions.

### Files Affected
- `core/delivery.py` — Created: `send_email()`, `_send_with_retry()` (tenacity-wrapped)
- `tests/test_delivery.py` — Created: T-DEL-C-001, T-DEL-E-001
- `requirements.txt` — Updated: `sendgrid==6.12.5` added
- `RULES.md` — Updated: R-006 (SendGrid-only retry), ZT-003 (Gmail SMTP removed)
- `MASTER_PLAN.md` — Updated: Section 4.3 email table, Section 5.3 degradation row
- `TEST_REGISTRY.md` — Updated: T-DEL-C-001, T-DEL-E-001 → PASSING, version → 1.5.0

### Rules Added/Modified
- R-006 — Updated: Gmail removed; SendGrid retry 3× exponential backoff; False on exhaustion
- ZT-003 — Updated: Gmail SMTP removed from outbound domain whitelist

### Tests Added/Modified
- T-DEL-C-001 — PASSING (new; test name updated: SendGrid send success)
- T-DEL-E-001 — PASSING (new; test name updated: all retries fail → False + CRITICAL)

### Dependencies
- Depends on: CL-008 (TC-005 — synthesis layer)
- Blocks: CL-010 (TC-007 — integration / main.py)

### Rollback
Delete `core/delivery.py`, `tests/test_delivery.py`. Remove `sendgrid==6.12.5` from
`requirements.txt`. Revert T-DEL-C-001, T-DEL-E-001 rows in `TEST_REGISTRY.md` to
`PENDING`. Revert R-006 and ZT-003 in `RULES.md` and MASTER_PLAN.md Sections 4.3/5.3
to prior Gmail+SendGrid wording.

### Owner Approval
- [ ] Approved by Niteen

---

---

## [CL-010] — 2026-06-17 — COMPLETED

**Type:** FEATURE + GOVERNANCE UPDATE
**Author:** Claude Code
**Task ID:** TC-007
**Status:** COMPLETED

### Summary
TC-007 complete — integration layer: `main.py` and T-INT-I-001 end-to-end pipeline test.
Implements `run_daily_pipeline(pool_path, db_path) → bool` as the public pipeline entry point
with injectable paths for test isolation. Internal helpers: `_make_llm()` (lazy
`ChatLiteLLM` import), `_tools()` (LangChain Tool wrappers for `search` and `query_history`),
`_run_jit_agent()` / `_run_jic_agent()` / `_run_lesson_agent()` (each call `run_agent()` and
parse JSON from `result["output"]` with list/dict fallback on decode errors), `_build_context()`
(assembles Jinja2 context dict), `_write_ledger()` (append-only SQLite insert, R-004).
DEV-I-005 enforced: `llm_call()` is never imported or called from `main.py`; all LLM
interactions route through `core.orchestration.run_agent()`. GOV-001 satisfied: topic order
is deterministic (pointer-based, never LLM-decided). T-INT-I-001 mocks `main.run_agent`
(3× side_effect), `main.send_email`, `main.validate_env`, `main._make_llm`, and asserts
all four acceptance criteria: bool return, send_email called once, ledger ≥ 1 row, pool
pointer advanced to 1. Final result: 28/28 tests green, zero regressions.

### Files Affected
- `main.py` — Created: full pipeline entry point, 7 helper functions, DEV-I-005 compliant
- `tests/test_integration.py` — Created (red phase from prior session): T-INT-I-001
- `TEST_REGISTRY.md` — Updated: T-INT-I-001 → PASSING, version → 1.6.0
- `RULES.md` — DEV-I-005 already added in prior session (CL-010 pointer was reserved for it)

### Rules Added/Modified
- DEV-I-005 — Enforced: no direct `llm_call()` from `main.py`; all LLM via `run_agent()`

### Tests Added/Modified
- T-INT-I-001 — PASSING (new)

### Dependencies
- Depends on: CL-009 (TC-006 — delivery layer)
- Blocks: None (TC-007 is the final implementation task)

### Rollback
Delete `main.py`, `tests/test_integration.py`. Revert T-INT-I-001 row in `TEST_REGISTRY.md`
to `PENDING`. DEV-I-005 in `RULES.md` can be retained (governance only, no code dependency).

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-011] — 2026-06-17 — COMPLETED

**Type:** FEATURE
**Author:** Claude Code
**Task ID:** TC-008
**Status:** COMPLETED

### Summary
TC-008 complete — Streamlit dashboard (`frontend/app.py`). Created the `frontend/`
directory (pre-authorised in MASTER_PLAN Section 3 canonical structure). Six panels
implemented: Panel 1 (last-7-days run metrics table + token-usage line chart via
`_get_recent_runs()`), Panel 2 (cooldown checker calling `tools.memory.query_history()`
+ last-30-topics table), Panel 3 (topic queue view, add-topic form, move-up/skip
controls writing to `config/topic_pool.json`), Panel 4 (last-20 system_exceptions
audit entries), Panel 5 (free-text SQL console — `_validate_select_only()` enforces
ZT-002; three pre-built query templates), Panel 6 (email template HTML editor,
save-to-file, `st.components.v1.html` preview, "Test Send" calling
`core.delivery.send_email()`). Pure data-helper functions extracted for testability:
`_get_recent_runs()`, `_validate_select_only()`, `_get_cooldown_topics()`,
`_get_audit_entries()`, `_run_safe_query()`. Pre-confirmation: MASTER_PLAN Section 11.3
Panel 1 `status` column removed (no delivery-status column in current schema;
deferred to future migration task). 6-column contract for `_get_recent_runs()` locked.
Final result: 30/30 tests green, zero regressions. Streamlit UI rendering = manual
verification per MASTER_PLAN Section 14.

### Files Affected
- `frontend/__init__.py` — Created: package marker
- `frontend/app.py` — Created: full dashboard implementation (6 panels, 5 testable helpers)
- `tests/test_dashboard.py` — Created: T-DASH-C-001, T-DASH-N-001
- `TEST_REGISTRY.md` — Updated: T-DASH-C-001, T-DASH-N-001 → PASSING, version → 1.7.0
- `MASTER_PLAN.md` — Updated: Section 11.3 Panel 1 `status` column removed with deferred-migration note

### Rules Added/Modified
- ZT-002 — Enforced in `_validate_select_only()`: non-SELECT SQL raises ValueError before any DB execution

### Tests Added/Modified
- T-DASH-C-001 — PASSING (new)
- T-DASH-N-001 — PASSING (new)

### Dependencies
- Depends on: CL-010 (TC-007 — main.py), CL-006 (TC-003 — tools/memory.py, schema.sql)
- Blocks: CL-012 (TC-009 — launchd scheduler, if in scope)

### Rollback
Delete `frontend/__init__.py`, `frontend/app.py`, `tests/test_dashboard.py`. Revert
T-DASH-C-001, T-DASH-N-001 rows in `TEST_REGISTRY.md` to PENDING. Revert MASTER_PLAN.md
Section 11.3 Panel 1 to include `status` column in the prose description.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-012] — 2026-06-17 — COMPLETED

**Type:** FEATURE
**Author:** Claude Code
**Task ID:** TC-009
**Status:** COMPLETED

### Summary
TC-009 complete — macOS launchd scheduler. Created `scripts/setup_launchd.py` with
three public functions: `generate_plist(project_root, python_path) → str` (formats
the plist XML template with all paths resolved — no `/PATH/TO/` placeholders),
`write_plist(project_root, python_path) → None` (writes the generated XML to
`com.niteen.ai-aggregator.plist` at project root), `install_plist() → None` (copies
plist to `~/Library/LaunchAgents/` and prints the launchctl management cheatsheet —
no subprocess calls, no side effects on the test environment). Ran `python3 -m
scripts.setup_launchd` to generate `com.niteen.ai-aggregator.plist` at project root
with real paths: `sys.executable` for the interpreter and the resolved project root
for all file paths. The committed plist contains Niteen's absolute machine path
(`<home>/...`) — acceptable for a single-user personal system; not a
portability concern. T-SCH-C-001 validates plist content without invoking launchctl.
Final result: 31/31 tests green, zero regressions.

### Files Affected
- `scripts/setup_launchd.py` — Created: `generate_plist()`, `write_plist()`, `install_plist()`
- `com.niteen.ai-aggregator.plist` — Created at project root (generated by `write_plist()`)
- `tests/test_scheduler.py` — Created: T-SCH-C-001
- `TEST_REGISTRY.md` — Updated: T-SCH-C-001 → PASSING, version → 1.8.0

### Rules Added/Modified
- None — GIT-H-001 already excludes `logs/` (referenced by plist stdout/stderr paths)

### Tests Added/Modified
- T-SCH-C-001 — PASSING (new)

### Dependencies
- Depends on: CL-011 (TC-008 — dashboard), CL-010 (TC-007 — main.py entry point)
- Blocks: None (TC-009 is the final scheduled-infrastructure task)

### Rollback
Delete `scripts/setup_launchd.py`, `com.niteen.ai-aggregator.plist`,
`tests/test_scheduler.py`. Revert T-SCH-C-001 row in `TEST_REGISTRY.md` to PENDING.
If plist was installed: `launchctl unload ~/Library/LaunchAgents/com.niteen.ai-aggregator.plist`
then delete the file from `~/Library/LaunchAgents/`.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-013] — 2026-06-17 — COMPLETED

**Type:** FEATURE + BUGFIX
**Author:** Claude Code
**Task ID:** TC-010
**Status:** COMPLETED

### Summary
TC-010 complete — LangSmith tracing integration and GMAIL key cleanup. Three changes:
(1) `core/orchestration.py`: `run_agent()` gains `run_name: str = "daily-jit-jic-agent"`
parameter; value is forwarded to `executor.invoke()` as `config={"run_name": run_name,
"tags": ["daily-newsletter"]}` so every agent step appears with a distinct, identifiable
label in LangSmith rather than an opaque UUID. (2) `main.py`: the three `run_agent()`
call sites now pass `run_name="jit-agent"`, `run_name="jic-agent"`, and
`run_name="lesson-agent"` respectively. (3) `scripts/check_env.py` (bugfix): removed
`GMAIL_APP_PASSWORD` and `GMAIL_SENDER` from `REQUIRED_KEYS` (Gmail was dropped in
TC-006 but the cleanup was missed; without this fix, ZT-001 would fatal-crash any real
run where these keys are absent from `.env`); promoted `SENDGRID_API_KEY` from
`OPTIONAL_KEYS` to `REQUIRED_KEYS` (sole delivery provider since TC-006). `tests/test_env.py`
fixture updated to match the corrected key contract; T-ENV-E-001 target key changed from
`GMAIL_SENDER` to `SENDGRID_API_KEY`. LangSmith tracing itself requires no code beyond
the env vars already in `REQUIRED_KEYS` (`LANGCHAIN_API_KEY`, `LANGCHAIN_TRACING_V2`,
`LANGCHAIN_PROJECT`) — LangChain traces automatically when `LANGCHAIN_TRACING_V2=true`.
Final result: 32/32 tests green, zero regressions.

### Files Affected
- `core/orchestration.py` — Updated: `run_name` param added; `executor.invoke()` now passes config
- `main.py` — Updated: three `run_agent()` call sites pass distinct `run_name` labels
- `scripts/check_env.py` — Bugfix: GMAIL keys removed from REQUIRED_KEYS; SENDGRID promoted
- `tests/test_env.py` — Updated: VALID_DEFAULTS corrected; T-ENV-E-001 target key updated
- `tests/test_orchestration.py` — Updated: T-TRC-C-001 added

### Rules Added/Modified
- None — existing ZT-001 (fatal crash on missing key) now enforces the corrected key list

### Tests Added/Modified
- T-TRC-C-001 — PASSING (new)
- T-ENV-C-001 — PASSING (fixture corrected; test logic unchanged)
- T-ENV-E-001 — PASSING (target key updated from GMAIL_SENDER to SENDGRID_API_KEY)

### Dependencies
- Depends on: CL-012 (TC-009), CL-009 (TC-006 — SendGrid-only delivery)
- Blocks: None

### Rollback
Revert `core/orchestration.py` `run_agent()` signature and `executor.invoke()` call.
Revert `main.py` three `run_agent()` call sites to remove `run_name=`. Revert
`scripts/check_env.py` REQUIRED_KEYS/OPTIONAL_KEYS to TC-009 state. Revert
`tests/test_env.py` VALID_DEFAULTS and T-ENV-E-001. Remove T-TRC-C-001 from
`tests/test_orchestration.py`.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-014] — 2026-06-17 — COMPLETED

**Type:** BUGFIX
**Author:** Claude Code
**Task ID:** N/A (out-of-band bugfix)
**Status:** COMPLETED

### Summary
`core/gateway.py`: replaced hardcoded `api_key=os.getenv("GOOGLE_API_KEY")` with a
new `_get_api_key(model)` helper, called as `api_key=_get_api_key(model)` in
`litellm.completion()`. The prior code sent the Gemini key to every model in the
failover chain regardless of provider — `mistral/...` calls would have been
authenticated with the wrong key, and `ollama/...` calls (which need no key)
would have received one anyway. `_get_api_key()` routes by provider prefix:
`gemini/` → `GOOGLE_API_KEY`, `mistral/` → `MISTRAL_API_KEY`, anything else
(currently `ollama/`) → `None`. Note: an initial bug report describing a missing
`api_key` parameter entirely was investigated first and found to not match the
current code (the parameter was already present, just hardcoded to one provider) —
this entry covers the narrower, correct bug. Final result: 33/33 tests green,
zero regressions. `python3 main.py` was not run — deferred to a separate live-run
task per owner instruction.

### Files Affected
- `core/gateway.py` — Added `_get_api_key(model) -> str | None`; `llm_call()` now calls it
- `tests/test_gateway.py` — Added T-GAT-N-003
- `TEST_REGISTRY.md` — Updated: T-GAT-N-003 → PASSING, version → 2.0.0

### Rules Added/Modified
- None — ZT-001 / SEC-X-001 already cover correct key handling; this fixes routing, not policy

### Tests Added/Modified
- T-GAT-N-003 — PASSING (new)

### Dependencies
- Depends on: CL-005 (TC-002 — gateway initial implementation)
- Blocks: None

### Rollback
Revert `core/gateway.py` to call `api_key=os.getenv("GOOGLE_API_KEY")` directly and
remove `_get_api_key()`. Remove T-GAT-N-003 from `tests/test_gateway.py`. Revert
T-GAT-N-003 row in `TEST_REGISTRY.md` to absent, version back to 1.9.0.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-015] — 2026-06-17 — COMPLETED (live pipeline still blocked — see note)

**Type:** BUGFIX
**Author:** Claude Code
**Task ID:** N/A (out-of-band bugfix)
**Status:** COMPLETED

### Summary
`main.py` `_make_llm()`: passed `api_key=os.getenv("GOOGLE_API_KEY")` to `ChatLiteLLM`
via `model_kwargs={"api_key": ...}` rather than as a direct constructor kwarg.
Investigation found `ChatLiteLLM` (langchain_community) has no top-level `api_key`
pydantic field — only provider-specific fields (`openai_api_key`, `anthropic_api_key`,
etc., none for Gemini/Google). A direct `api_key=` constructor kwarg is silently
dropped by pydantic with no error. `model_kwargs` is the field that flows through
`ChatLiteLLM._default_params` into the live `litellm.completion()` call — verified
empirically before implementing. T-MAIN-C-001 (new file `tests/test_main.py`) asserts
`_make_llm().model_kwargs["api_key"]` rather than a non-existent `.api_key` attribute,
since the originally-specified test target was not achievable.

**Live run after this fix still fails** with the same `key=None` symptom. Root cause
identified during the live verification step: `.env` is never loaded into the process
environment anywhere in this codebase — no `load_dotenv()` call exists in `main.py`,
`core/`, or `scripts/`. `scripts/check_env.py`'s `validate_env()` parses `.env` directly
via its own file-reading logic and never touches `os.environ`. Every existing test sets
env vars via `monkeypatch.setenv()`, so this gap was never exercised by the suite. This
fix (model_kwargs) is necessary but not sufficient — `os.getenv("GOOGLE_API_KEY")`
returns `None` at runtime regardless, because `.env`'s contents never reach `os.environ`.
A separate fix (likely `load_dotenv()` at the top of `main.py`) is required before the
live pipeline can succeed. Final result: 34/34 tests green, zero regressions.

### Files Affected
- `main.py` — `_make_llm()` now passes GOOGLE_API_KEY via `model_kwargs`
- `tests/test_main.py` — Created: T-MAIN-C-001
- `TEST_REGISTRY.md` — Updated: T-MAIN-C-001 → PASSING, version → 2.1.0

### Rules Added/Modified
- None

### Tests Added/Modified
- T-MAIN-C-001 — PASSING (new)

### Dependencies
- Depends on: CL-014 (gateway api_key bugfix), CL-010 (TC-007 main.py)
- Blocks: live pipeline first successful run (pending the .env-loading fix)

### Rollback
Revert `main.py` `_make_llm()` to `ChatLiteLLM(model=_DEFAULT_MODEL)`. Delete
`tests/test_main.py`. Revert T-MAIN-C-001 row in `TEST_REGISTRY.md`, version back to 2.0.0.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-016] — 2026-06-17 — COMPLETED

**Type:** BUGFIX
**Author:** Claude Code
**Task ID:** N/A (out-of-band bugfix)
**Status:** COMPLETED

### Summary
`main.py`: added `from dotenv import load_dotenv` / `load_dotenv()` immediately after
the stdlib imports and before any `from core` import. Root cause: `.env` was never
loaded into `os.environ` anywhere in this codebase — `scripts/check_env.py`'s
`validate_env()` parses `.env` directly via its own file-reading logic and never
touches `os.environ`; every test in the suite sets env vars via `monkeypatch.setenv()`,
so the gap was invisible to automated testing and only surfaced on a real,
unmocked run. T-MAIN-C-002 was revised mid-implementation: as originally specified
it called `load_dotenv(dotenv_path=...)` directly inside the test body, which tests
python-dotenv's own documented behavior, not whether `main.py` calls it — that version
passed even with no fix applied (confirmed empirically, no genuine red phase possible).
A first revision asserted on `os.getenv()` after `monkeypatch.chdir()` + module reload,
but `load_dotenv()`'s no-argument form discovers `.env` relative to the *calling
module's own file location* (main.py's directory), not the process cwd — so chdir
had no effect and the test loaded the real project `.env`, asserting against the
real (unpredictable, secret) key value. Final version mocks `dotenv.load_dotenv` and
asserts it is called once on reload — verifies the actual bug (the call never
happened) without depending on filesystem discovery semantics or real secret values.
Live verification after the fix: the live pipeline now sends the real `GOOGLE_API_KEY`
in the request (previously `key=None`); it fails for an unrelated, external reason —
the configured Google AI Studio project's prepaid credits are exhausted
(`429 RESOURCE_EXHAUSTED`). Final result: 35/35 tests green, zero regressions.

### Files Affected
- `main.py` — Added `load_dotenv()` call at module-import time
- `tests/test_main.py` — Added T-MAIN-C-002 (revised twice during implementation; see Summary)
- `TEST_REGISTRY.md` — Updated: T-MAIN-C-002 → PASSING, version → 2.2.0

### Rules Added/Modified
- None

### Tests Added/Modified
- T-MAIN-C-002 — PASSING (new)

### Dependencies
- Depends on: CL-015 (model_kwargs fix — necessary but insufficient alone)
- Blocks: None (live pipeline now correctly authenticates; remaining failure is account billing, out of code scope)

### Rollback
Remove the `from dotenv import load_dotenv` / `load_dotenv()` lines from `main.py`.
Delete T-MAIN-C-002 from `tests/test_main.py`. Revert T-MAIN-C-002 row in
`TEST_REGISTRY.md`, version back to 2.1.0.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-017] — 2026-06-17 — COMPLETED

**Type:** FEATURE (architectural gap fix)
**Author:** Claude Code
**Task ID:** N/A (out-of-band bugfix)
**Status:** COMPLETED

### Summary
`core/orchestration.py`: `run_agent()` now catches `litellm.exceptions.RateLimitError`
and `AuthenticationError`, rebuilds the LLM with the next model in
`core.gateway._build_model_chain()` (reused, not duplicated), and retries once per
fallback model. New helpers: `_build_llm_for_model(model)` (constructs `ChatLiteLLM`
with the correct `api_key` via `core.gateway._get_api_key()`) and `_invoke_once(...)`
(builds a fresh agent/executor and invokes — factored out of `run_agent()` to respect
DEV-I-003's 40-line function limit). `run_agent()` gained a `model: str = None`
parameter (falls back to `os.getenv("LITELLM_PRIMARY_MODEL")`, then the chain's first
entry) and `llm` became optional — if omitted, `run_agent()` builds its own starting
LLM. On total chain exhaustion: logs CRITICAL, returns
`{"output": "All models exhausted", "error": str(last_error)}`. Closes the
architectural gap identified during the CL-016 live-run report: the agent-based
pipeline (`ChatLiteLLM` via `AgentExecutor`) had no failover at all — `core.gateway`'s
multi-model chain only protected callers of `gateway.llm_call()`, which the live
pipeline never calls (DEV-I-005 routes everything through `run_agent()`).
`main.py`: `_run_jit_agent()`, `_run_jic_agent()`, `_run_lesson_agent()` now take a
`model` string instead of a pre-built `llm` — `run_agent()` builds (and fails over)
its own LLM internally. `run_daily_pipeline()` no longer calls `_make_llm()`; that
function is retained, unused by the pipeline, because `tests/test_main.py`
T-MAIN-C-001/T-MAIN-C-002 test it directly and removing it would break two passing
tests for no requested reason. `core/gateway.py` was not modified — only its existing
`_build_model_chain()` and `_get_api_key()` are imported and reused. Final result:
37/37 tests green, zero regressions.

### Files Affected
- `core/orchestration.py` — Added `_build_llm_for_model()`, `_invoke_once()`; `run_agent()` gains failover + `model` param
- `main.py` — Three wrapper functions take `model` instead of `llm`; `run_daily_pipeline()` no longer calls `_make_llm()`
- `tests/test_orchestration_failover.py` — Created: T-ORC-N-001, T-ORC-N-002
- `TEST_REGISTRY.md` — Updated: T-ORC-N-001, T-ORC-N-002 → PASSING, version → 2.3.0

### Rules Added/Modified
- R-002 — Extended: model failover now also covers the agent-based pipeline path, not just `gateway.llm_call()`

### Tests Added/Modified
- T-ORC-N-001 — PASSING (new)
- T-ORC-N-002 — PASSING (new)

### Dependencies
- Depends on: CL-016 (load_dotenv fix — surfaced this gap during live verification), CL-014 (`_get_api_key` reused here)
- Blocks: None

### Rollback
Revert `core/orchestration.py` to the CL-013 version (remove `_build_llm_for_model()`,
`_invoke_once()`, failover loop; restore the simple single-attempt `run_agent()`).
Revert `main.py`'s three wrapper functions to take `llm` and restore
`llm = _make_llm()` in `run_daily_pipeline()`. Delete
`tests/test_orchestration_failover.py`. Revert T-ORC-N-001/002 rows in
`TEST_REGISTRY.md`, version back to 2.2.0.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-018] — 2026-06-17 — COMPLETED

**Type:** FEATURE + BUGFIX (env-contract migration)
**Author:** Claude Code
**Task ID:** N/A (out-of-band bugfix, pre-confirmed via full audit)
**Status:** COMPLETED

### Summary
Migrated the LLM failover chain from hardcoded model strings to an env-var-driven
contract, and closed three additional gaps found during a full pre-implementation
audit. `.env` contract change (Niteen applies directly, not touched by this agent):
`LITELLM_MODEL_1..4` replace `LITELLM_PRIMARY_MODEL`/`LITELLM_FALLBACK_1`/`_2`; new
`LITELLM_TIMEOUT_SECONDS` (default 30).

**`core/gateway.py`**: `_build_model_chain()` rewritten to read `LITELLM_MODEL_1`,
`_2`, `_3`... sequentially from env until a key is missing, raising `RuntimeError`
if `LITELLM_MODEL_1` is absent. This removes the old `MISTRAL_API_KEY`-presence
conditional entirely — every configured entry is now included unconditionally
(superseded T-GAT-E-003, rewritten to test the new contract). `_get_api_key()`
gained a `groq/` → `GROQ_API_KEY` branch. `_scrub_secrets()` now also scrubs
`GROQ_API_KEY` (audit finding A — Groq is a live provider now, error messages may
echo the key).

**`core/orchestration.py`**: `_FAILOVER_EXCEPTIONS` widened to include
`BadRequestError` and `Timeout` (the live-run finding from the prior session —
Mistral's `BadRequestError: Invalid model` previously crashed the pipeline instead
of advancing the chain). `_build_llm_for_model()` now reads `LITELLM_TIMEOUT_SECONDS`
(default 30) and passes it as `request_timeout` to `ChatLiteLLM` — **not** `timeout`,
which was the original instruction; `ChatLiteLLM.model_fields` was checked directly
and confirmed it has no `timeout` field, only `request_timeout` (audit RISK 1 — same
class of silent-drop bug as the earlier `api_key=` mistake, caught before
implementation this time). `run_agent()` rewritten with a lazy chain-build: previously
`_build_model_chain()` was called unconditionally at the top, meaning T-ORC-C-001 and
T-TRC-C-001 (which pass a pre-built `llm` and never set `LITELLM_MODEL_1`) only worked
by accident, dependent on pytest's test-collection order having already triggered
`main.py`'s `load_dotenv()` (audit RISK 3). The chain is now only built on first
failure or when `llm` is `None`. The dead `os.getenv("LITELLM_PRIMARY_MODEL")` fallback
was removed (audit Fix D) — `chain[0]` already covers it once the chain exists.
Timeout failures log a distinct message: `"Model {model} timed out after {timeout}s,
trying next"`.

**`scripts/check_env.py`**: `LITELLM_MODEL_1` added to `REQUIRED_KEYS`; `GROQ_API_KEY`
added to `OPTIONAL_KEYS`. `LITELLM_PRIMARY_MODEL` was never present in either list —
nothing to remove there.

**Test fixture corrections required to reach 40/40** (audit RISKs 2/4, findings B/C):
`tests/test_env.py` `VALID_DEFAULTS` gained `LITELLM_MODEL_1` (RISK 4 — adding a
required key without updating the shared fixture would have broken T-ENV-C-001 and
friends). `tests/test_gateway.py` `REQUIRED_ENV` dropped the stale
`GMAIL_APP_PASSWORD`/`GMAIL_SENDER` entries (finding B — leftover from before TC-006)
and gained a `LITELLM_MODEL_1` baseline; T-GAT-E-001's fixture and assertions updated
to set `LITELLM_MODEL_1/2/3` explicitly and expect the new model strings (finding C).
Three new tests added: T-GAT-C-002, T-GAT-N-004 (direct `_build_model_chain()` unit
tests), T-ORC-N-003 (Timeout-triggered failover). T-GAT-E-003 rewritten in place,
same ID, to test unconditional inclusion instead of key-presence-conditional skip.

Full pre-implementation audit was performed and confirmed by owner before any file
was touched — five RISKs and four additional required fixes were surfaced and
resolved by explicit decision rather than discovered as regressions after the fact.
Final result: 40/40 tests green, zero regressions. `python3 main.py` was not run,
per instruction.

### Files Affected
- `core/gateway.py` — `_build_model_chain()` rewritten (env-var driven); `_get_api_key()` gained `groq/`; `_scrub_secrets()` scrubs `GROQ_API_KEY`
- `core/orchestration.py` — `_FAILOVER_EXCEPTIONS` widened; lazy chain-build; `request_timeout` support; dead `LITELLM_PRIMARY_MODEL` getenv removed
- `scripts/check_env.py` — `LITELLM_MODEL_1` → REQUIRED_KEYS; `GROQ_API_KEY` → OPTIONAL_KEYS
- `tests/test_env.py` — `VALID_DEFAULTS` gained `LITELLM_MODEL_1`
- `tests/test_gateway.py` — `REQUIRED_ENV` corrected (GMAIL removed, LITELLM_MODEL_1 added); T-GAT-E-001 fixture/assertions updated; T-GAT-E-003 rewritten; T-GAT-C-002, T-GAT-N-004 added
- `tests/test_orchestration_failover.py` — T-ORC-N-003 added
- `TEST_REGISTRY.md` — Updated: T-GAT-E-001, T-GAT-E-003 rows revised; T-GAT-C-002, T-GAT-N-004, T-ORC-N-003 added; version → 2.4.0

### Rules Added/Modified
- R-002 — Extended: failover now also triggers on `BadRequestError` and `Timeout`, not just `RateLimitError`/`AuthenticationError`

### Tests Added/Modified
- T-GAT-C-002 — PASSING (new)
- T-GAT-N-004 — PASSING (new)
- T-ORC-N-003 — PASSING (new)
- T-GAT-E-003 — PASSING (rewritten in place, same ID, supersedes prior behavior)
- T-GAT-E-001 — PASSING (fixture and assertions updated)

### Dependencies
- Depends on: CL-017 (failover mechanism this builds on), CL-016 (load_dotenv — the source of RISK 3's order-dependency)
- Blocks: Niteen's `.env` update (LITELLM_MODEL_1..4, LITELLM_TIMEOUT_SECONDS) — required before any live run

### Rollback
Revert `core/gateway.py`'s `_build_model_chain()` to the hardcoded list, `_get_api_key()`
to remove the `groq/` branch, `_scrub_secrets()` to remove `GROQ_API_KEY`. Revert
`core/orchestration.py` to the CL-017 version. Revert `scripts/check_env.py`
REQUIRED_KEYS/OPTIONAL_KEYS. Revert `tests/test_env.py`, `tests/test_gateway.py` to
their CL-017/CL-016 states. Delete T-ORC-N-003 from `tests/test_orchestration_failover.py`.
Revert `TEST_REGISTRY.md` to v2.3.0.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-019] — 2026-06-18 — COMPLETED

**Type:** BUGFIX
**Author:** Claude Code
**Task ID:** N/A (out-of-band bugfix, pre-confirmed via targeted audit)
**Status:** COMPLETED

### Summary
Targeted audit confirmed two live bugs and fixed both via TDD. **Bug 1** (`main.py`):
`_DEFAULT_MODEL = "gemini/gemini-2.5-flash"` was passed as the `model` argument to
all three `run_agent()` calls in `run_daily_pipeline()` (via `_run_jit_agent()`,
`_run_jic_agent()`, `_run_lesson_agent()`), silently overriding the env-driven
failover chain built by `core.gateway._build_model_chain()` (CL-018). The CL-017/
CL-018 failover mechanism was effectively dead code on the live path — every call
was pinned to Gemini regardless of `LITELLM_MODEL_1..4`. Fix: removed the constant
entirely; all three `run_agent()` calls now pass `model=None`, letting `run_agent()`
build the model from the chain itself. `_build_context()`'s `model_used` field now
reads `os.getenv("LITELLM_MODEL_1", "unknown")` instead of the removed constant.
`_make_llm()` is unchanged in behavior (now uses a literal model string inline) —
left in place because `tests/test_main.py` T-MAIN-C-001/T-MAIN-C-002 test it directly
and it is not called by the pipeline (per CL-017).

**Bug 2** (`tools/search.py`): no query length truncation existed before calling
Tavily or DuckDuckGo — an unbounded query string would be forwarded to both APIs
as-is. Fix: `search()` now truncates `query` to 400 chars before any API call.
Separately, `_duckduckgo_search()` had no try/except of its own — if Tavily failed
first (triggering the fallback) and then DuckDuckGo also failed, the second
exception was unguarded and propagated out of `search()` uncaught. Fix:
`_duckduckgo_search()`'s body is now wrapped in try/except; on any exception it
logs a WARNING and returns `[]`, so `search()` degrades to an empty result list
instead of crashing the calling agent.

TDD: three new tests written and confirmed RED before implementation —
T-SRC-N-001 (truncation), T-SRC-E-002 (DDG failure isolation — note: registered as
`E-002`, not `E-001`, because `T-SRC-E-001` already exists for a different scenario
— "DuckDuckGo fallback on Tavily fail" in `tests/test_tools.py`; reusing the ID
would have collided), and T-MAIN-C-003 (`run_agent()` called with `model=None` for
all three sub-agents). `tests/test_search.py` created as a new file (did not
previously exist; the original T-SRC-C-001/T-SRC-E-001 tests live in
`tests/test_tools.py` and were left untouched). Final result: 43/43 tests green,
zero regressions. `python3 main.py` was not run, per instruction.

### Files Affected
- `main.py` — Removed `_DEFAULT_MODEL`; all three `run_agent()` calls in `run_daily_pipeline()` pass `model=None`; `_build_context()`'s `model_used` reads `LITELLM_MODEL_1` from env; `_make_llm()` uses an inline literal model string (behavior unchanged)
- `tools/search.py` — `search()` truncates `query` to 400 chars before any API call; `_duckduckgo_search()` wrapped in try/except, returns `[]` and logs WARNING on any exception
- `tests/test_search.py` — Created: T-SRC-N-001, T-SRC-E-002
- `tests/test_main.py` — Added T-MAIN-C-003
- `TEST_REGISTRY.md` — Updated: T-SRC-N-001, T-SRC-E-002, T-MAIN-C-003 added, version → 2.5.0

### Rules Added/Modified
- R-002 — Reinforced: the env-driven failover chain (CL-018) now actually reaches the live pipeline; previously short-circuited by the hardcoded `_DEFAULT_MODEL`

### Tests Added/Modified
- T-SRC-N-001 — PASSING (new)
- T-SRC-E-002 — PASSING (new)
- T-MAIN-C-003 — PASSING (new)

### Dependencies
- Depends on: CL-018 (env-driven failover chain — this fix is what makes it reachable from the live pipeline), CL-006 (TC-003 — `tools/search.py` initial implementation)
- Blocks: None

### Rollback
Revert `main.py` to restore `_DEFAULT_MODEL = "gemini/gemini-2.5-flash"` and pass it
explicitly to all three `run_agent()` calls; revert `_build_context()`'s `model_used`
to the constant. Revert `tools/search.py` to remove the `query = query[:400]` line
and the try/except in `_duckduckgo_search()`. Delete `tests/test_search.py`. Remove
T-MAIN-C-003 from `tests/test_main.py`. Revert `TEST_REGISTRY.md` to v2.4.0.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-020] — 2026-06-18 — COMPLETED

**Type:** BUGFIX
**Author:** Claude Code
**Task ID:** N/A (out-of-band bugfix, pre-confirmed via targeted audit)
**Status:** COMPLETED

### Summary
Targeted audit confirmed the iteration-cap finding from the prior live run
(CL-019's report): `core.orchestration.MAX_ITERATIONS = 5` is the module-wide
default, and `max_iter` was already a per-call override parameter on
`run_agent()` (added in CL-013/CL-017's `_invoke_once()` refactor) — but
`main.py`'s three sub-agent helpers (`_run_jit_agent()`, `_run_jic_agent()`,
`_run_lesson_agent()`) never passed it, so all three silently fell back to the
5-iteration default. The live run showed all three hitting that cap and
returning the LangChain stop phrase instead of valid JSON (R-005 warning logged
each time), producing an email with empty JIT/JIC/lesson content.

Fix: `_run_jit_agent()` and `_run_jic_agent()` now pass `max_iter=8` to
`run_agent()`; `_run_lesson_agent()` passes `max_iter=15` (deeper task — 9
sub-sections per call vs. JIT/JIC's single flat list).
`core/orchestration.py` was **not modified** — `MAX_ITERATIONS=5` remains the
module default for any other caller (e.g. `tests/test_orchestration.py`
T-ORC-C-001, which asserts the default cap directly).

TDD: three new tests written and confirmed RED before implementation —
T-MAIN-C-004, T-MAIN-C-005 (JIT/JIC `max_iter=8`), T-MAIN-C-006 (lesson
`max_iter=15`) — each calls the helper directly with `main.run_agent` mocked
and asserts the `max_iter` kwarg. Final result: 46/46 tests green, zero
regressions. `python3 main.py` was not run, per instruction.

### Files Affected
- `main.py` — `_run_jit_agent()`/`_run_jic_agent()` pass `max_iter=8`; `_run_lesson_agent()` passes `max_iter=15`, on their respective `run_agent()` calls
- `tests/test_main.py` — Added T-MAIN-C-004, T-MAIN-C-005, T-MAIN-C-006
- `TEST_REGISTRY.md` — Updated: T-MAIN-C-004/005/006 added, version → 2.6.0

### Rules Added/Modified
- R-005 — Reinforced: hard iteration cap is still enforced (no caller can exceed `AgentExecutor.max_iterations`), but the per-agent budget is now tuned to each task's actual complexity instead of one global default

### Tests Added/Modified
- T-MAIN-C-004 — PASSING (new)
- T-MAIN-C-005 — PASSING (new)
- T-MAIN-C-006 — PASSING (new)

### Dependencies
- Depends on: CL-019 (live run that surfaced the iteration-cap finding), CL-017 (added the `max_iter` parameter to `run_agent()`)
- Blocks: None

### Rollback
Revert `main.py`'s three `run_agent()` call sites to drop the `max_iter=` kwarg
(reverts to the `core.orchestration.MAX_ITERATIONS=5` default for all three).
Remove T-MAIN-C-004/005/006 from `tests/test_main.py`. Revert
`TEST_REGISTRY.md` to v2.5.0.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-021] — 2026-06-18 — COMPLETED

**Type:** BUGFIX
**Author:** Claude Code
**Task ID:** N/A (out-of-band bugfix, pre-confirmed via targeted audit)
**Status:** COMPLETED

### Summary
Root cause of the CL-020 finding (all three sub-agents still hitting their
iteration cap and returning the literal LangChain ReACT stop phrase, even
after raising `max_iter` to 8/8/15) identified and fixed: `_invoke_once()`
used `create_react_agent`, which parses the model's raw text output for a
`Action:`/`Observation:` convention. Modern models (e.g. Llama 3.3 70B via
Groq, and other LITELLM_MODEL_n entries) emit native function-calling tokens
instead of that text format — the ReACT parser couldn't recognise any tool
invocation in that output, so every iteration was wasted on unparseable text
regardless of how high `max_iter` was raised, until the executor force-stopped
and returned `"Agent stopped due to iteration limit or time limit."` as
`output`. Audit confirmed `ChatLiteLLM` (`langchain_community==0.3.7`) inherits
`bind_tools()` from `BaseChatModel`, so native tool calling is available; it
was simply never used.

Fix: `core/orchestration.py` now imports `create_tool_calling_agent` instead
of `create_react_agent`, and `ChatPromptTemplate` instead of `PromptTemplate`.
`_invoke_once()` builds a `ChatPromptTemplate` with a system message instructing
JSON-schema-conformant output, a `("human", "{input}")` message, and an
`("placeholder", "{agent_scratchpad}")` slot, then calls
`create_tool_calling_agent(llm, tools, chat_prompt)`. `_REACT_TEMPLATE` and
`_STOP_PHRASE` are removed — `create_tool_calling_agent` never emits the old
stop phrase, so R-005 exhaustion detection changed from string-matching the
stop phrase to checking `result.get("output") is None`.
`_build_llm_for_model()`, `run_agent()`, `_FAILOVER_EXCEPTIONS`, and
`MAX_ITERATIONS` were **not modified**, per instruction.

Five pre-existing tests patched `core.orchestration.create_react_agent` by
exact import name (`T-ORC-C-001`, `T-TRC-C-001` in `tests/test_orchestration.py`;
`T-ORC-N-001/002/003` via the shared `_patch_agent_internals()` helper in
`tests/test_orchestration_failover.py`) — these were updated to patch
`create_tool_calling_agent` instead, a mechanical consequence of the rename
required to avoid `AttributeError` at patch time (TST-T-003: no regressions).
`T-ORC-C-001`'s mock exhaustion signal was also updated from the old stop-phrase
string to `{"output": None}`, matching the new detection logic; its WARNING
assertion (`"iteration" in record.message.lower()`) still passes unchanged
since the log message still contains "max_iterations".

TDD: two new tests written and confirmed RED before implementation —
`T-ORC-C-002` (`_invoke_once()` succeeds via `create_tool_calling_agent`,
returns dict with `"output"` key) and `T-ORC-N-004` (`_invoke_once()` returns
`{"output": None}` and logs WARNING on exhaustion). Confirmed all 7 affected
tests (5 pre-existing + 2 new) were RED together before implementing, proving
the patch-target rename was load-bearing. Final result: 48/48 tests green,
zero regressions. `python3 main.py` was not run, per instruction.

### Files Affected
- `core/orchestration.py` — `create_react_agent`/`PromptTemplate` → `create_tool_calling_agent`/`ChatPromptTemplate`; `_invoke_once()` rewritten to build a `ChatPromptTemplate` and use tool-calling agent construction; `_REACT_TEMPLATE`/`_STOP_PHRASE` removed; R-005 exhaustion check changed to `result.get("output") is None`
- `tests/test_orchestration.py` — Patch targets updated (`create_react_agent` → `create_tool_calling_agent`) in T-ORC-C-001, T-TRC-C-001; T-ORC-C-001's mock exhaustion signal updated; added T-ORC-C-002, T-ORC-N-004
- `tests/test_orchestration_failover.py` — Patch target updated in shared `_patch_agent_internals()` helper, covering T-ORC-N-001/002/003
- `TEST_REGISTRY.md` — Updated: T-ORC-C-002, T-ORC-N-004 added, version → 2.7.0

### Rules Added/Modified
- R-005 — Reinforced: hard iteration cap (`max_iterations`) still enforced via `AgentExecutor`; the *detection* of exhaustion changed (no stop-phrase under tool-calling agents) but the cap itself is identical

### Tests Added/Modified
- T-ORC-C-002 — PASSING (new)
- T-ORC-N-004 — PASSING (new)
- T-ORC-C-001 — PASSING (patch target + mock signal updated, same ID)
- T-TRC-C-001 — PASSING (patch target updated, same ID)
- T-ORC-N-001 — PASSING (patch target updated, same ID)
- T-ORC-N-002 — PASSING (patch target updated, same ID)
- T-ORC-N-003 — PASSING (patch target updated, same ID)

### Dependencies
- Depends on: CL-020 (live run that surfaced this as the deeper root cause behind the iteration-cap finding)
- Blocks: A live run to confirm tool-calling actually produces valid JSON end-to-end (not attempted this session, per instruction)

### Rollback
Revert `core/orchestration.py` to the CL-018 version (`create_react_agent`,
`PromptTemplate`, `_REACT_TEMPLATE`, `_STOP_PHRASE`, stop-phrase-based R-005
check). Revert the patch-target changes in `tests/test_orchestration.py` and
`tests/test_orchestration_failover.py` back to `create_react_agent`; revert
T-ORC-C-001's mock to the stop-phrase string. Remove T-ORC-C-002, T-ORC-N-004
from `tests/test_orchestration.py`. Revert `TEST_REGISTRY.md` to v2.6.0.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-022] — 2026-06-18 — COMPLETED

**Type:** BUGFIX
**Author:** Claude Code
**Task ID:** N/A (out-of-band bugfix, pre-confirmed via targeted audit)
**Status:** COMPLETED

### Summary
Fixes the crash from the last live run, where an OpenRouter model's malformed
tool-call response surfaced as `litellm.exceptions.APIConnectionError` — not
covered by `_FAILOVER_EXCEPTIONS` — and propagated uncaught through
`run_agent()`, crashing the entire pipeline mid-run with no email, no ledger
write, and no pointer advance. Audit also found a deeper, related gap:
`.env`'s `LITELLM_MODEL_1/2/3` are now all `openrouter/...` models, but
neither `core/orchestration.py`'s `_build_llm_for_model()` nor
`core/gateway.py`'s `_get_api_key()` had any branch for the `openrouter/`
prefix — every OpenRouter call in the chain was silently being sent with
`api_key=None`, which independently explains the malformed-response failures
(an unauthenticated OpenRouter call returns something the model layer
mishandles, rather than a clean 401).

**Fix 1** (`core/orchestration.py`): `_FAILOVER_EXCEPTIONS` widened to also
include `litellm.exceptions.APIConnectionError` and `NotFoundError`, alongside
the existing `RateLimitError`, `AuthenticationError`, `BadRequestError`,
`Timeout`. Both new exception types confirmed importable from
`litellm.exceptions` before use.

**Fix 2** (`core/orchestration.py`): `_build_llm_for_model()` gained an
`openrouter/` branch that builds `ChatLiteLLM` with
`model_kwargs={"api_key": os.getenv("OPENROUTER_API_KEY")}`, mirroring the
existing fallback path's shape. Audit note: this branch is functionally
redundant with the fallback path once Fix 3 lands, since the fallback already
calls `_get_api_key(model)` (now openrouter-aware) — both paths resolve to the
same `OPENROUTER_API_KEY` value. Implemented as explicitly specified rather
than collapsed into the fallback, since the instruction was literal and the
duplication is harmless (same value, two call paths).

**Fix 3** (`core/gateway.py`): `_get_api_key()` gained an `openrouter/` branch
returning `os.getenv("OPENROUTER_API_KEY")`. `GROQ_API_KEY` was already present
in the `_scrub_secrets()` loop from CL-018 — no change needed there. Audit
finding not in scope for this task: `OPENROUTER_API_KEY` itself is not yet in
the `_scrub_secrets()` loop, so an OpenRouter error message that echoes the key
back would not be redacted from logs (SEC-X-001 gap) — flagged for a follow-up
task, not fixed here since it wasn't part of the specified scope.

**Fix 4** (`scripts/check_env.py`): `OPENROUTER_API_KEY` added to
`OPTIONAL_KEYS` (fallback provider, same tier as `MISTRAL_API_KEY`/
`GROQ_API_KEY` — absence never triggers a fatal ZT-001 crash).

TDD: four new tests written and confirmed RED before implementation —
`T-ORC-N-006` (APIConnectionError triggers failover), `T-ORC-N-007`
(NotFoundError triggers failover), `T-ORC-C-005` (`_build_llm_for_model()`
returns `OPENROUTER_API_KEY` in `model_kwargs` for an `openrouter/` model),
`T-GAT-N-005` (`_get_api_key()` routes `openrouter/` to `OPENROUTER_API_KEY`).
No ID conflicts found against the existing registry before assigning. Final
result: 52/52 tests green, zero regressions. `python3 main.py` was not run,
per instruction.

### Files Affected
- `core/orchestration.py` — `_FAILOVER_EXCEPTIONS` widened (+`APIConnectionError`, `+NotFoundError`); `_build_llm_for_model()` gained an `openrouter/` branch
- `core/gateway.py` — `_get_api_key()` gained an `openrouter/` branch
- `scripts/check_env.py` — `OPENROUTER_API_KEY` added to `OPTIONAL_KEYS`
- `tests/test_orchestration_failover.py` — Added T-ORC-N-006, T-ORC-N-007
- `tests/test_orchestration.py` — Added T-ORC-C-005
- `tests/test_gateway.py` — Added T-GAT-N-005
- `TEST_REGISTRY.md` — Updated: T-ORC-C-005, T-ORC-N-006, T-ORC-N-007, T-GAT-N-005 added, version → 2.8.0

### Rules Added/Modified
- R-002 — Extended: model failover now also triggers on `APIConnectionError` and `NotFoundError`, not just rate-limit/auth/bad-request/timeout
- ZT-003 — Implicitly extended: OpenRouter is now a reachable LLM provider via the LiteLLM SDK-direct pattern (no rule text change needed — ZT-003 already covers "each configured LLM provider's API ... reached via the LiteLLM Python SDK")

### Tests Added/Modified
- T-ORC-N-006 — PASSING (new)
- T-ORC-N-007 — PASSING (new)
- T-ORC-C-005 — PASSING (new)
- T-GAT-N-005 — PASSING (new)

### Dependencies
- Depends on: CL-021 (tool-calling agent switch — the malformed-tool-call failure mode this fix addresses only exists because of that change), CL-018 (env-driven model chain — `.env` populating `LITELLM_MODEL_1/2/3` with OpenRouter entries is what surfaced this gap)
- Blocks: Niteen must set `OPENROUTER_API_KEY` in `.env` before the next live run — see report below for the exact value needed

### Rollback
Revert `core/orchestration.py`'s `_FAILOVER_EXCEPTIONS` to the 4-exception
tuple and remove the `openrouter/` branch in `_build_llm_for_model()`. Revert
`core/gateway.py`'s `_get_api_key()` to remove the `openrouter/` branch.
Remove `OPENROUTER_API_KEY` from `scripts/check_env.py` `OPTIONAL_KEYS`.
Delete T-ORC-N-006/007 from `tests/test_orchestration_failover.py`, T-ORC-C-005
from `tests/test_orchestration.py`, T-GAT-N-005 from `tests/test_gateway.py`.
Revert `TEST_REGISTRY.md` to v2.7.0.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-023] — 2026-06-21 — COMPLETED

**Type:** BUGFIX (security gap)
**Author:** Claude Code
**Task ID:** N/A (out-of-band bugfix, SEC-X-001 gap identified in CL-022 review)
**Status:** COMPLETED

### Summary
Added `OPENROUTER_API_KEY` to the `_scrub_secrets()` redaction loop in
`core/gateway.py`. This closes the SEC-X-001 gap flagged in CL-022: OpenRouter
is now a live provider in the model chain (`LITELLM_MODEL_1/2/3`), and any
error response from OpenRouter that echoes back the raw key value would have
been written to logs unredacted. Fix: `"OPENROUTER_API_KEY"` added to the
`for env_var in (...)` tuple in `_scrub_secrets()`. TDD: T-GAT-N-006 written
RED first, confirmed failing, then implementation applied. Final result:
53/53 tests green, zero regressions.

### Files Affected
- `core/gateway.py` — `_scrub_secrets()` tuple gains `"OPENROUTER_API_KEY"`
- `tests/test_gateway.py` — Added T-GAT-N-006
- `TEST_REGISTRY.md` — T-GAT-N-006 added, version → v2.9.0

### Rules Added/Modified
- SEC-X-001 — Enforced: `OPENROUTER_API_KEY` value now redacted from all log output

### Tests Added/Modified
- T-GAT-N-006 — PASSING (new)

### Dependencies
- Depends on: CL-022 (OpenRouter provider branch — the gap this closes)
- Blocks: None

### Rollback
Remove `"OPENROUTER_API_KEY"` from the `_scrub_secrets()` tuple in
`core/gateway.py`. Delete T-GAT-N-006 from `tests/test_gateway.py`. Revert
`TEST_REGISTRY.md` to v2.8.0.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-024] — 2026-06-21 — COMPLETED

**Type:** BUGFIX
**Author:** Claude Code
**Task ID:** N/A (launchd live-run failure — discovered from launchd_stderr.log)
**Status:** COMPLETED

### Summary
`validate_env()` in `scripts/check_env.py` used `env_path: str = ".env"` as its
default — a cwd-relative path. In interactive terminal sessions the cwd happened
to be the project root, so the bug was invisible. Under launchd the cwd is not
the project root, causing `FileNotFoundError: '.env'` on every unattended 07:00
run. All 3 firings logged in `logs/launchd_stderr.log` (Jun 19) failed identically
at this point before any LLM/email/DB logic ran.

Fix: changed the default to `str(PROJECT_ROOT / ".env")`, reusing the module's
existing `PROJECT_ROOT = Path(__file__).resolve().parent.parent` constant —
an absolute path anchored at `scripts/check_env.py`'s own location, independent
of cwd. T-ENV-E-002 reproduces the exact launchd failure (monkeypatch.chdir to
a tmp dir with no .env, assert no FileNotFoundError) and confirmed RED before fix.

First fully successful end-to-end live run confirmed immediately after fix:
all three agents completed, email delivered (SendGrid 202), ledger updated,
topic pointer advanced. 54/54 tests green, zero regressions.

### Files Affected
- `scripts/check_env.py` — `validate_env()` default `env_path` changed from `".env"` to `str(PROJECT_ROOT / ".env")`
- `tests/test_env.py` — Added T-ENV-E-002

### Rules Added/Modified
- None — ZT-001 already requires env isolation; this fixes path resolution, not policy

### Tests Added/Modified
- T-ENV-E-002 — PASSING (new)

### Dependencies
- Depends on: CL-023 (last completed fix before this live run)
- Blocks: None

### Rollback
Revert `validate_env()` default back to `".env"` in `scripts/check_env.py`.
Delete T-ENV-E-002 from `tests/test_env.py`. Revert TEST_REGISTRY.md to v2.9.0.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-025] — 2026-06-21 — COMPLETED

**Type:** BUGFIX
**Author:** Claude Code
**Task ID:** N/A (Streamlit dashboard audit — task hypothesized 3 issues, only 1 reproduced)
**Status:** COMPLETED

### Summary
Audited a reported set of 3 Streamlit dashboard issues: TypedDict/Python 3.14
incompatibility (Panel 1), `_repr_html_()` crash (Panel 5), and a Streamlit
launch failure. Only one of the three was reproducible.

**Fix 1 (TypedDict) and Fix 3 (Streamlit launch) were not reproducible.**
`typing_extensions` is already at 4.15.0 — well past the version that
introduced the Python 3.13/3.14 `TypedDict` `closed`-keyword incompatibility —
and `frontend/app.py` contains no `TypedDict` usage anywhere. Streamlit
launched cleanly via `python3 -m streamlit run frontend/app.py` with no port
conflict, no import error, and Panel 1 (the default panel) rendered without
exception when verified via `streamlit.testing.v1.AppTest`. No changes were
made to `requirements.txt` or any package version.

**Fix 2 (Panel 5 `_repr_html_()` crash) was confirmed and fixed.** Root cause:
`_panel_sql()` (line 199) used a bare ternary *expression statement* —
`st.error(err) if err else st.dataframe(rows, use_container_width=True)` —
not assigned to anything. Streamlit's "magic" output feature auto-wraps any
bare top-level expression statement in `st.write(...)`. When `err` is falsy,
the ternary evaluates `st.dataframe(...)` first (rendering the table as a
side effect, returning a `DeltaGenerator`), and that return value is then
passed into `st.write()`, which probes it for `_repr_html_()` and raises
`StreamlitAPIException`. Fix: replaced the bare ternary with a proper
`if/else:` block, which Streamlit's magic-write never touches. Confirmed via
`AppTest` simulating "select a pre-built query → click Run" before (crash)
and after (clean render) the fix.

T-DASH-N-002 written first and confirmed RED (reproducing the exact
`StreamlitAPIException` via `AppTest` with a mocked `_connect()`), then the
fix applied. Final result: 55/55 tests green, zero regressions.

New file: `scripts/maintenance.sh` — a single shell script with 10 commented
maintenance functions (start/stop dashboard, run pipeline, check env, run
tests, reset pointer, reset database, check scheduler, view logs, reinstall
deps), `chmod +x`'d.

### Files Affected
- `frontend/app.py` — `_panel_sql()` bare ternary replaced with `if/else:` block
- `tests/test_dashboard.py` — Added T-DASH-N-002
- `scripts/maintenance.sh` — Created (new file, executable)
- `TEST_REGISTRY.md` — T-DASH-N-002 added, version → v3.1.0

### Rules Added/Modified
- None — this is a UI bugfix with no rule-governed behavior change

### Tests Added/Modified
- T-DASH-N-002 — PASSING (new)

### Dependencies
- Depends on: CL-011 (TC-008 — original dashboard implementation)
- Blocks: None

### Rollback
Revert `frontend/app.py`'s `_panel_sql()` to the bare-ternary form. Delete
T-DASH-N-002 from `tests/test_dashboard.py`. Delete `scripts/maintenance.sh`.
Revert `TEST_REGISTRY.md` to v3.0.0.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-026] — 2026-06-22 — COMPLETED

**Type:** BUGFIX
**Author:** Claude Code
**Task ID:** N/A (discovered by reading `logs/launchd_stderr.log` after today's 07:00 launchd firing)
**Status:** COMPLETED

### Summary
Same class of bug as CL-024, in different files. `com.niteen.ai-aggregator.plist`
has no `WorkingDirectory` key, so launchd runs the pipeline with cwd defaulting
to `/` (the SIP-sealed, read-only macOS system volume). Four locations used
cwd-relative path strings, all of which broke under that cwd:

- `main.py`: `_DB_PATH = "database/ledger.db"`, `_POOL_PATH = "config/topic_pool.json"`
- `scripts/setup_db.py`: `init_db(db_path: str = "database/ledger.db")`
- `tools/topic_manager.py`: `_DEFAULT_POOL = "config/topic_pool.json"`
- `tools/memory.py`: `DB_PATH = "database/ledger.db"` — notable because
  `query_history()` is called with no `conn` argument by `main.py`'s live
  agent tools, so this one is exercised in production on every JIT/JIC agent
  cooldown check, not just at pipeline startup.

Today's actual 07:00 failure (the 4th, freshest traceback in
`logs/launchd_stderr.log` — the first 3 were stale, pre-CL-024 `.env`
tracebacks left over from an append-only log that's never been cleared) was:
```
OSError: [Errno 30] Read-only file system: '/database'
```
from `scripts/setup_db.py:29`'s `os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)`.
This confirms CL-024 worked — the pipeline got past `validate_env()` for the
first time under launchd and crashed one step later, at `init_db()`.

Fix: anchored all four locations to `PROJECT_ROOT` via
`Path(__file__).resolve().parent` (or `.parent.parent` for files one level
deeper than the project root), identical pattern to CL-024's `.env` fix. The
plist's `WorkingDirectory` key was deliberately **not** added — path
anchoring in code is the correct fix; pinning cwd in the scheduler config
would just relocate the same class of latent bug to the next untested path.

TDD: three tests written and confirmed RED before implementation —
T-MAIN-C-007 (`run_daily_pipeline()`'s default paths are absolute,
regardless of cwd — verified via mocked downstream calls, no real file I/O),
T-DB-N-002 (`init_db()` does not raise `OSError` when cwd is `/` — exact
reproduction of today's live failure), T-MEM-E-002 (`query_history()` with no
`conn` arg does not raise when cwd lacks a `database/` subdirectory).
**Correction during TEST phase:** T-MEM-E-002's actual failure mode is
`sqlite3.OperationalError: unable to open database file`, not
`OSError`/`FileNotFoundError` as originally specified — `sqlite3.connect()`
does not create missing parent directories, so a missing directory surfaces
as a DB-layer error, not an OS-layer one. Broadened the except clause to
`(OSError, FileNotFoundError, sqlite3.Error)` so the test is meaningful
(fails on the real bug) rather than vacuously checking the wrong exception
type. Final result: 58/58 tests green (55 prior + 3 new — one more than the
2 originally scoped, since T-MEM-E-002 was added mid-session after the
`tools/memory.py` finding), zero regressions.

### Files Affected
- `main.py` — `_DB_PATH`/`_POOL_PATH` anchored to `PROJECT_ROOT = Path(__file__).resolve().parent`
- `scripts/setup_db.py` — `init_db()`'s default `db_path` anchored to `PROJECT_ROOT` (reused existing `SCHEMA_PATH` pattern)
- `tools/topic_manager.py` — `_DEFAULT_POOL` anchored to `PROJECT_ROOT`
- `tools/memory.py` — `DB_PATH` anchored to `PROJECT_ROOT`
- `tests/test_main.py` — Added T-MAIN-C-007
- `tests/test_tools.py` — Added T-DB-N-002, T-MEM-E-002
- `TEST_REGISTRY.md` — T-MAIN-C-007, T-DB-N-002, T-MEM-E-002 added, version → v3.2.0
- `scripts/maintenance.sh` — `check_scheduler()` comment added noting stale vs. fresh `launchd_stderr.log` tracebacks

### Rules Added/Modified
- None — this is a path-resolution bugfix, no rule-governed behavior change

### Tests Added/Modified
- T-MAIN-C-007 — PASSING (new)
- T-DB-N-002 — PASSING (new)
- T-MEM-E-002 — PASSING (new)

### Dependencies
- Depends on: CL-024 (established the `PROJECT_ROOT`-anchoring pattern this reuses), CL-011 (`tools/memory.py`/`tools/topic_manager.py` original implementations)
- Blocks: None

### Rollback
Revert `main.py`'s `_DB_PATH`/`_POOL_PATH` to the relative string literals.
Revert `scripts/setup_db.py`'s `init_db()` default to `"database/ledger.db"`.
Revert `tools/topic_manager.py`'s `_DEFAULT_POOL` to `"config/topic_pool.json"`.
Revert `tools/memory.py`'s `DB_PATH` to `"database/ledger.db"`. Delete
T-MAIN-C-007 from `tests/test_main.py`; delete T-DB-N-002, T-MEM-E-002 from
`tests/test_tools.py`. Revert `TEST_REGISTRY.md` to v3.1.0.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-027] — 2026-06-22 — COMPLETED

**Type:** BUGFIX
**Author:** Claude Code
**Task ID:** N/A (sender/recipient conflation found while drafting a separate Cowork prompt)
**Status:** COMPLETED

### Summary
**Part 1 — sender address bug in `core/delivery.py`.** `send_email()` read
`sender = os.getenv("TARGET_EMAIL", "")` — the same env var `main.py` uses as
the *recipient* address. Every email sent from-and-to the same address.

The originally proposed fix was to switch to `GMAIL_SENDER` — rejected after
verification: `GMAIL_SENDER` was deliberately removed from `check_env.py`'s
`REQUIRED_KEYS` in CL-013 ("Gmail dropped in TC-006"), so it's unvalidated at
startup; reviving it would also not actually decouple anything, since its
current `.env` value is byte-identical to `TARGET_EMAIL`'s today — confirmed
programmatically without printing either value. Instead, introduced a
dedicated `EMAIL_FROM` env var: `core/delivery.py` now reads
`os.getenv("EMAIL_FROM", "")` for the sender, and `EMAIL_FROM` was added to
`scripts/check_env.py`'s `REQUIRED_KEYS` so a missing sender fails fast at
startup (`validate_env()`/ZT-001) rather than silently producing an empty
`from_email` at send time. `EMAIL_FROM` turned out to already exist in `.env`
with a valid, non-placeholder value (identical to `TARGET_EMAIL`/`GMAIL_SENDER`)
— no `.env` edit was needed. `tests/test_delivery.py`'s `_set_env()` updated
to set `EMAIL_FROM` to a *distinct* value from `TARGET_EMAIL`, and
T-DEL-C-001 now asserts the constructed `Mail` object's `from_email.email`
matches `EMAIL_FROM` specifically — proving the two are no longer conflated
(this assertion would have caught the original bug). `tests/test_env.py`'s
`VALID_DEFAULTS` fixture updated to include `EMAIL_FROM`.

**Part 2 — topic pointer reset.** `config/topic_pool.json`'s `"pointer"` key
(confirmed via direct read before editing) was at `3`; reset to `0` so the
daily lesson restarts from topic 1 ("Transformer Architecture"). Also removed
a stray, unused `"current_index"` key — a leftover artifact from the
`reset_pointer()` bug in `scripts/maintenance.sh` (caught and fixed in the
prior session; only `"pointer"` is ever read by `tools/topic_manager.py`).

No new test IDs were added (per scope) — T-DEL-C-001's existing assertions
were strengthened, and `VALID_DEFAULTS` fixtures updated to keep existing
tests passing under the new required key. Final result: 58/58 tests green,
zero regressions. `validate_env()` confirmed to still pass against the real
`.env` (`EMAIL_FROM` already present and valid).

### Files Affected
- `core/delivery.py` — `sender` now reads `EMAIL_FROM` instead of `TARGET_EMAIL`
- `scripts/check_env.py` — `EMAIL_FROM` added to `REQUIRED_KEYS`
- `tests/test_delivery.py` — `_set_env()` sets `EMAIL_FROM` distinctly from `TARGET_EMAIL`; T-DEL-C-001 asserts `from_email` matches `EMAIL_FROM`
- `tests/test_env.py` — `VALID_DEFAULTS` gained `EMAIL_FROM`
- `config/topic_pool.json` — `"pointer"` reset to `0`; stray `"current_index"` key removed

### Rules Added/Modified
- ZT-001 — Enforced: a missing sender address now fails fast at startup via `validate_env()`, not silently at send time

### Tests Added/Modified
- T-DEL-C-001 — PASSING (strengthened, same ID — now asserts `from_email`)
- T-ENV-C-001 and other `VALID_DEFAULTS`-dependent tests — PASSING (fixture updated, same IDs)

### Dependencies
- Depends on: CL-013 (the GMAIL_SENDER removal this fix respects rather than reverts)
- Blocks: None

### Rollback
Revert `core/delivery.py`'s `sender` line to `os.getenv("TARGET_EMAIL", "")`.
Remove `EMAIL_FROM` from `scripts/check_env.py`'s `REQUIRED_KEYS`. Revert
`tests/test_delivery.py`'s `_set_env()` and T-DEL-C-001 assertion. Revert
`tests/test_env.py`'s `VALID_DEFAULTS`. Revert `config/topic_pool.json`'s
`"pointer"` to its prior value (`3`) — note `"current_index"` removal is not
reversible without knowing its prior value, but it was unused/vestigial.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-028] — 2026-06-22 — COMPLETED

**Type:** BUGFIX + DATA CORRECTION
**Author:** Claude Code
**Task ID:** N/A (Streamlit dashboard crash + ledger data integrity issue)
**Status:** COMPLETED

### Summary
**Part 1 — Panel 1 chart crash.** `frontend/app.py`'s `_panel_run_metrics()`
called `st.line_chart({r["covered_date"]: r["tokens_used"] for r in rows})`,
which crashed with `TypeError: _TypedDictMeta.__new__() got an unexpected
keyword argument 'closed'`. The proposed fix (convert the dict to a
`pd.DataFrame` and call `st.line_chart()` on that) was verified **not** to
work before implementing: `st.line_chart()`'s `generate_chart()` does
`import altair as alt` unconditionally, and `altair==5.5.0` itself fails to
import under Python 3.14 (its own schema file uses
`TypedDict(closed=True, ...)`, unsupported by this Python version) —
confirmed by reproducing the identical crash with a plain `pd.DataFrame`
input and with `st.bar_chart()` (same `generate_chart()` path). The bug is
entirely in `altair`'s import, independent of the chart's input shape. Fix:
removed the `st.line_chart()` call — the `st.dataframe()` call immediately
above already displays the same data. T-DASH-N-003 written first and
confirmed RED (reproducing the exact `TypeError`) before the fix.

**Part 2 — ledger data correction.** `historical_ledger` held 3 rows, all
dated 2026-06-22 (Transformer, MCP, ReACT, all `run_type=JIC`) — these were
test/debug artifacts from dashboard troubleshooting, not real deliveries. A
proposed "correction" (Transformer on 2026-06-21 + ReACT on 2026-06-22) was
checked against this session's own live-run logs before acting and found to
contradict the verifiable history: the actual confirmed deliveries are MCP
(2026-06-18), ReACT (2026-06-18), and RAG (2026-06-21, the most recent — full
`Pipeline complete — delivered=True` + `SendGrid 202` + `Ledger updated`
trace exists for this run from the CL-024 verification session). No delivery
of "Transformer Architecture" exists anywhere in the session history.
Corrected via a one-off script (`scripts/correct_ledger.py`, run once then
deleted per plan): dropped the R-004 `prevent_delete_historical_ledger`
trigger, deleted the 3 stale rows, reset `sqlite_sequence`, inserted the 3
correct rows, and recreated the trigger using the exact DDL from
`database/schema.sql`. R-004 enforcement verified restored immediately after
(a live `DELETE` attempt was rejected).

**Part 3 — pointer correction.** `config/topic_pool.json`'s topics array has
MCP/ReACT/RAG at indices 1/2/3 respectively — exactly matching the
1→2→3 delivery order, confirming the array's current ordering is internally
consistent with the corrected ledger. Set `"pointer"` to **4** (continuing
to `topics[4]` = "Mixture of Experts (MoE)...") — not 3, which would have
re-delivered RAG. A separate, unrelated crashed RAG attempt (CL-022 era,
malformed tool call) produced no ledger row and was not counted.

**Part 4 — verification.** Full suite: 59/59 green (58 prior + T-DASH-N-003).
Re-ran `correct_ledger.py`'s result through `AppTest` against the real,
corrected `database/ledger.db`: Panel 1 (0 exceptions), Panel 2 (shows
exactly the 3 corrected rows with correct dates), Panel 3 (pointer=4 →
"Mixture of Experts (MoE)..."). Streamlit relaunched on `localhost:8501`,
confirmed serving (`HTTP 200`) with the process alive.

### Files Affected
- `frontend/app.py` — `_panel_run_metrics()`'s `st.line_chart()` call removed
- `tests/test_dashboard.py` — Added T-DASH-N-003
- `database/ledger.db` — `historical_ledger` corrected to 3 real rows (MCP, ReACT, RAG); R-004 trigger dropped and recreated as part of the one-off correction, confirmed still enforced
- `config/topic_pool.json` — `"pointer"` set to `4`
- `TEST_REGISTRY.md` — T-DASH-N-003 added, version → v3.3.0
- `HANDOVER.md` — §3 CL-027/CL-028 rows added (CL-027's row was missed in its own session); §5 Live Run Status replaced with corrected delivery history; §9 KEY FILES versions updated
- `HANDOVER_FINAL.md` — §2 status updated to CL-028 with corrected live-run history; §5 KEY FILES versions updated; §7 deferred-items list updated
- `scripts/correct_ledger.py` — Created, run once, then deleted (one-off correction script, per plan)

### Rules Added/Modified
- R-004 — Temporarily bypassed (trigger dropped) only for this one-time historical correction, then restored and verified still enforced; no policy change

### Tests Added/Modified
- T-DASH-N-003 — PASSING (new)

### Dependencies
- Depends on: CL-024 (most recent confirmed live delivery, RAG, is the basis for the ledger correction), CL-025 (established the AppTest verification pattern reused here)
- Blocks: None

### Rollback
Revert `frontend/app.py`'s `_panel_run_metrics()` to include the
`st.line_chart()` call. Delete T-DASH-N-003 from `tests/test_dashboard.py`.
Revert `TEST_REGISTRY.md` to v3.2.0. The ledger correction itself has no
clean rollback path (R-004 prevents restoring deleted rows) — the 3
pre-correction test/debug rows were not preserved before deletion, since
they were confirmed to be artifacts, not real data, before the one-off
script ran. Revert `config/topic_pool.json`'s `"pointer"` to `0` if needed.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-029] — 2026-06-22 — COMPLETED

**Type:** BUGFIX
**Author:** Claude Code
**Task ID:** N/A (output-quality issue observed in delivered emails)
**Status:** COMPLETED

### Summary
Delivered emails contained news items dated 2-3 weeks old. Two causes, both
fixed: (1) `tools/search.py`'s `_tavily_search()` called Tavily with no
recency filter at all; (2) `main.py`'s JIT/JIC prompts gave the LLM no hard
date cutoff, so even filtered results could be waved through.

**Part 1.** Verified `TavilyClient.search()`'s own source before implementing:
its `days` parameter is passed through to the API regardless of `topic`, but
Tavily's API documentation states `days` is only honored when
`topic="news"` — with the default `topic="general"`, `days` is silently
ignored server-side. Adding `days=7` alone (as originally proposed) would
have been a no-op, the same failure pattern already caught twice this
session (CL-027's `GMAIL_SENDER`, CL-028's `pd.DataFrame` chart fix). Added
both `days=7` **and** `topic="news"` to the call.

**Part 2.** Rewrote both `_run_jit_agent()` and `_run_jic_agent()`'s prompts
to state today's date and an explicit 7-day cutoff date, instruct discarding
any result older than that, and request richer 2-3 sentence summaries
(previously 1 sentence) for `why_it_matters`/`core_insight`.

**Part 3 — test IDs.** The original plan named `T-MAIN-C-003`/`T-MAIN-C-004`
for the new prompt-content assertions, but those IDs already test unrelated
things (`model=None` propagation and JIT `max_iter=8` respectively) — neither
checks prompt text. Added new IDs (`T-MAIN-C-008`, `T-MAIN-C-009`) instead of
retrofitting unrelated tests. Similarly used `T-SRC-C-002` (matching this
project's established `SRC` module code) rather than the originally
suggested `T-SRCH-U-004`, which uses a module code and type code (`U`) not
in this project's `TEST_REGISTRY.md` ID format.

TDD: all 3 new tests written and confirmed RED before implementation. Final
result: 62/62 tests green (59 prior + 3 new — not 59/59 as originally
scoped, since 3 new tests were added, consistent with the count corrections
in CL-026/CL-028), zero regressions.

### Files Affected
- `tools/search.py` — `_tavily_search()` now passes `days=7` and `topic="news"` to `TavilyClient.search()`
- `main.py` — `_run_jit_agent()`/`_run_jic_agent()` prompts rewritten with explicit date/cutoff, discard-older-results instruction, and 2-3 sentence summary length; `timedelta` added to the `datetime` import
- `tests/test_search.py` — Added T-SRC-C-002
- `tests/test_main.py` — Added T-MAIN-C-008, T-MAIN-C-009
- `TEST_REGISTRY.md` — T-SRC-C-002, T-MAIN-C-008, T-MAIN-C-009 added, version → v3.4.0
- `HANDOVER.md` — §3 CL-029 row updated (62/62, v3.4.0), §4 search description updated to mention `topic="news"`, §7/§9 stale references updated

### Rules Added/Modified
- None — this is an output-quality bugfix, no rule-governed behavior change

### Tests Added/Modified
- T-SRC-C-002 — PASSING (new)
- T-MAIN-C-008 — PASSING (new)
- T-MAIN-C-009 — PASSING (new)

### Dependencies
- Depends on: CL-019 (query truncation/DDG isolation — `tools/search.py`'s prior bugfix baseline)
- Blocks: CL-030 (source authority injection, 10-item counts, richer lesson prompts — not yet run)

### Rollback
Revert `tools/search.py`'s `_tavily_search()` to omit `topic`/`days`. Revert
`main.py`'s JIT/JIC prompts to the pre-CL-029 wording; remove `timedelta`
from the `datetime` import if unused elsewhere. Delete T-SRC-C-002 from
`tests/test_search.py`; delete T-MAIN-C-008/009 from `tests/test_main.py`.
Revert `TEST_REGISTRY.md` to v3.3.0.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-030] — 2026-06-22 — COMPLETED

**Type:** FEATURE
**Author:** Claude Code
**Task ID:** N/A (output-quality issue — low-authority sources, item count, lesson depth)
**Status:** COMPLETED

### Summary
Three improvements to delivered email quality, all additive on top of CL-029's
recency fix: source-authority injection, doubled JIT/JIC item counts, and
richer lesson content requirements.

**Source authority.** Added `_JIT_SOURCES`, `_JIC_SOURCES`, `_LESSON_SOURCES`
tuples of high-authority domains (OpenAI, Anthropic, DeepMind, Google
Research, NVIDIA, Hugging Face, arXiv, Karpathy, Andrew Ng, MIT, Stanford,
NIST, etc.). All three prompts (`_run_jit_agent`, `_run_jic_agent`,
`_run_lesson_agent`) now inject a "PRIORITY SOURCES" instruction listing the
first 10 entries of the relevant tuple, with an explicit instruction to
deprioritise low-authority blogs and content farms.

**Item counts.** JIT/JIC item counts doubled from 5 to 10 per call.
`tools/search.py`'s `search()` default `n` raised 5→10 to match. JIT/JIC
`max_iter` raised 8→12 (the larger item count needs a bigger iteration
budget) — required updating the two existing tests that hardcoded the old
value (`T-MAIN-C-004`, `T-MAIN-C-005`, previously asserting `max_iter=8`).

**Lesson depth.** `_run_lesson_agent()`'s prompt gained explicit minimum
counts per section (4+ bullets for 3A/3B/3D/3H, 5+ papers for 3C, 3+ bullets
for 3E/3F, 3+ voices for 3G, 8+ glossary terms for 3I) and named-expert
preferences (Karpathy, Ng, Wolfe, MIT, Stanford, DeepMind, OpenAI, Anthropic,
arXiv).

**Topic pool.** Appended 6 new topics (AI Security, AI Governance,
Responsible AI, AI Evaluation, Constitutional AI/Alignment, AI in
Enterprise) — pool grew 25→31 topics. Pointer left unchanged at 4.

**Test ID corrections found during Phase 2/3:** two of the acceptance-criteria
substrings named in the originating plan don't actually appear in the
specified prompt wording — `"minimum 3 voices"` vs. the actual
`"minimum 3 authoritative voices"`, and `"minimum 8 terms"` vs. the actual
`"minimum 8 glossary terms"` (an extra word sits between the count and the
noun in both cases — same class of near-miss already caught for CL-029's
`T-DASH`/`T-SRC` IDs). `T-MAIN-C-012` asserts the real wording instead.

TDD: all 5 new tests (`T-MAIN-C-010`, `T-MAIN-C-011`, `T-MAIN-C-012`,
`T-MAIN-C-013`, `T-SRC-C-003`) written and confirmed RED before
implementation, with the 62 pre-existing tests confirmed still green at that
point. Final result: 67/67 tests green (62 prior + 5 new), zero regressions.

### Files Affected
- `main.py` — `_JIT_SOURCES`/`_JIC_SOURCES`/`_LESSON_SOURCES` constants added; all three prompts rewritten (item counts, PRIORITY SOURCES, per-section minimums); JIT/JIC `max_iter` 8→12
- `tools/search.py` — `search()`'s default `n` changed 5→10
- `config/topic_pool.json` — 6 new topics appended (25→31 total); pointer unchanged at 4
- `tests/test_main.py` — Added T-MAIN-C-010/011/012/013; updated T-MAIN-C-004/005 (max_iter 8→12, function names renamed to match)
- `tests/test_search.py` — Added T-SRC-C-003
- `TEST_REGISTRY.md` — T-MAIN-C-010/011/012/013, T-SRC-C-003 added; T-MAIN-C-004/005 descriptions updated; version → v3.5.0

### Rules Added/Modified
- None — output-quality feature work, no rule-governed behavior change

### Tests Added/Modified
- T-MAIN-C-010 — PASSING (new)
- T-MAIN-C-011 — PASSING (new)
- T-MAIN-C-012 — PASSING (new)
- T-MAIN-C-013 — PASSING (new)
- T-SRC-C-003 — PASSING (new)
- T-MAIN-C-004 — PASSING (updated: max_iter 8→12)
- T-MAIN-C-005 — PASSING (updated: max_iter 8→12)

### Dependencies
- Depends on: CL-029 (recency fix this builds on — same prompts, additive changes)
- Blocks: None

### Rollback
Revert `main.py` to remove the `_JIT_SOURCES`/`_JIC_SOURCES`/`_LESSON_SOURCES`
constants and restore the pre-CL-030 prompt wording (5 items, max_iter=8, no
source injection, no per-section minimums). Revert `tools/search.py`'s
`search()` default `n` to 5. Remove the 6 appended topics from
`config/topic_pool.json`. Revert T-MAIN-C-004/005 to assert `max_iter=8`;
delete T-MAIN-C-010/011/012/013 from `tests/test_main.py`; delete
T-SRC-C-003 from `tests/test_search.py`. Revert `TEST_REGISTRY.md` to v3.4.0.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-031] — 2026-06-22 — COMPLETED

**Type:** BUGFIX
**Author:** Claude Code
**Task ID:** N/A (output-quality issue — section drift in delivered lessons)
**Status:** COMPLETED

### Summary
Evaluated two delivered lessons against each section's stated intent and
found systematic drift: 3B ("intuition with analogy") gave implementation
details instead; 3F ("extends or contradicts earlier JIC topics") gave
future-research text or implementation steps instead; 3G ("authoritative
voices") cited product pages (Microsoft Azure AI Search, MindStudio) and a
YouTube tutorial instead of named researchers; 3H ("future directions") gave
hands-on tutorials/best-practice tips instead; 3C (papers) cited "Medium
Community" and "Towards AI Editorial Team" as paper authors. Root cause in
all five cases: the prompt named the section's *topic* but never said what
to exclude, and gave no concrete example — the LLM filled the ambiguity with
whatever was easiest to generate. Separately, 3I (glossary) consistently
returned only 5 terms despite the prompt asking for a minimum of 8 — proving
that a prompt instruction alone doesn't guarantee compliance.

**Fix 1 — prompt rewrite.** All five drifting sections gained an explicit
negative instruction ("Do NOT...") plus a concrete worked example. 3C
additionally requires real, listed researcher names for `authors` and
excludes blog/Medium/YouTube/Towards AI sources outright.

**Fix 2 — output validation.** Added `validate_lesson_output()` to
`core/synthesis.py`, checking minimum item counts for `section_3c` (≥5),
`section_3g` (≥3), and `section_3i` (≥8) — the three sections most prone to
truncation. Wired into `run_daily_pipeline()` right after the lesson agent
returns: a `ValueError` is logged and re-raised, so a truncated lesson fails
the pipeline loudly instead of being silently delivered. This directly
fixes the 3I-glossary-undercount problem, since the prompt-content tests
(`T-MAIN-C-012`) only verify the prompt *asks* for minimums — they can't
verify the LLM complied.

**Naming corrections (Phase 1, before any code changed):** the originating
plan's `T-SYNTH-U-001/002/003` used a module code (`SYNTH`) and type code
(`U`) absent from this project's `TEST_REGISTRY.md` format — renamed to
`T-SYN-N-002`, `T-SYN-N-003`, `T-SYN-C-003` (matching the existing `T-SYN-*`
convention; valid type codes are C/E/N/I/S). Five more near-miss substrings
were found while writing T-MAIN-C-014–018 (e.g. "contrasts with" vs. the
specified "contrasting with"; "exclude Medium" vs. the specified "Medium
articles") — same recurring pattern as CL-029/030 — corrected to assert on
the actual achievable wording in each case, documented inline per test.

**Regressions found and fixed during Phase 3** (wiring in
`validate_lesson_output()` unconditionally broke 4 existing tests that don't
test lesson validation at all): `T-INT-I-001`'s `_LESSON_FIXTURE` only had 1
paper/1 voice/1 glossary term — expanded to meet the new minimums.
`T-MAIN-C-003` and `T-MAIN-C-007` mock a lesson result that also failed the
new gate — both now also mock `validate_lesson_output`. `T-MAIN-C-012`
(CL-030) asserted the old "minimum N papers/voices/terms" phrasing, which
CL-031's rewrite replaced with more detailed "minimum N items): <description>"
wording — updated to match.

TDD: all 8 new tests written and confirmed RED before implementation. Final
result: 75/75 tests green (67 prior + 8 new), zero regressions after the
4 fixes above.

### Files Affected
- `main.py` — lesson prompt rewritten (3B/3C/3F/3G/3H gain negative instructions + examples); `validate_lesson_output()` imported and called after the lesson agent returns
- `core/synthesis.py` — `validate_lesson_output()` added (checks section_3c≥5, section_3g≥3, section_3i≥8)
- `tests/test_main.py` — Added T-MAIN-C-014/015/016/017/018; updated T-MAIN-C-003/007 (mock `validate_lesson_output`); updated T-MAIN-C-012 (new prompt wording)
- `tests/test_synthesis.py` — Added T-SYN-N-002, T-SYN-N-003, T-SYN-C-003
- `tests/test_integration.py` — `_LESSON_FIXTURE` expanded to meet the new minimums (5 papers, 3 voices, 8 glossary terms)
- `TEST_REGISTRY.md` — T-MAIN-C-014–018, T-SYN-N-002/N-003, T-SYN-C-003 added; T-MAIN-C-012 description updated; version → v3.6.0

### Rules Added/Modified
- None — output-quality bugfix, no rule-governed behavior change

### Tests Added/Modified
- T-MAIN-C-014 — PASSING (new)
- T-MAIN-C-015 — PASSING (new)
- T-MAIN-C-016 — PASSING (new)
- T-MAIN-C-017 — PASSING (new)
- T-MAIN-C-018 — PASSING (new)
- T-SYN-N-002 — PASSING (new)
- T-SYN-N-003 — PASSING (new)
- T-SYN-C-003 — PASSING (new)
- T-MAIN-C-003, T-MAIN-C-007 — PASSING (updated: mock `validate_lesson_output`)
- T-MAIN-C-012 — PASSING (updated: new prompt wording)

### Dependencies
- Depends on: CL-030 (the lesson prompt this rewrites; `_LESSON_SOURCES` reused unchanged)
- Blocks: None

### Rollback
Revert `main.py`'s lesson prompt to the pre-CL-031 (CL-030) wording; remove
the `validate_lesson_output` import and call from `run_daily_pipeline()`.
Remove `validate_lesson_output()` from `core/synthesis.py`. Revert
`tests/test_integration.py`'s `_LESSON_FIXTURE` to single-item sections.
Revert `tests/test_main.py`'s T-MAIN-C-003/007/012 to their CL-030 forms;
delete T-MAIN-C-014–018. Delete T-SYN-N-002/N-003/C-003 from
`tests/test_synthesis.py`. Revert `TEST_REGISTRY.md` to v3.5.0.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-032] — 2026-06-22 — COMPLETED

**Type:** BUGFIX
**Author:** Claude Code
**Task ID:** N/A (output-quality issue — silent empty output from content-refusals)
**Status:** COMPLETED

### Summary
`run_agent()` only catches `_FAILOVER_EXCEPTIONS` (`RateLimitError`,
`AuthenticationError`, `BadRequestError`, `Timeout`, `APIConnectionError`,
`NotFoundError`). Free-tier OpenRouter models occasionally return HTTP 200
with a refusal string ("I'm unable to...", "I cannot...", "As an AI...")
instead of the requested JSON — no exception is raised, so the failover loop
never fires. `main.py`'s existing `JSONDecodeError` catch then silently
returns `[]`/`{}` for that agent, with no retry on a different model.

Fix: added `_is_refusal(output)` to `core/orchestration.py`, checking the
output string against 9 known refusal-prefix patterns (case-insensitive,
prefix match after stripping whitespace). `_invoke_once()` now checks
`_is_refusal()` on the raw output before returning, and raises
`BadRequestError` (already in `_FAILOVER_EXCEPTIONS`) when a refusal is
detected — `run_agent()`'s existing failover loop handles it identically to
a real provider error, with no changes needed to the loop itself.

`main.py` was **not modified** — its `JSONDecodeError` catch remains as a
last-resort safety net for any other malformed output that isn't a refusal
and isn't caught by `_is_refusal()`.

**Naming correction (Phase 1, before any code changed):** the originating
plan's `T-ORCH-*` IDs don't match this project's actual prefix, `T-ORC-`
(Orchestration) — used the next available `T-ORC-C-006/007` (valid-JSON →
not a refusal) and `T-ORC-N-008/009/010` (refusal detection) in
`tests/test_orchestration.py`, and `T-ORC-N-011` (the failover integration
test) in `tests/test_orchestration_failover.py`, alongside the other
"exception type X triggers failover" tests of the same shape.

TDD: all 6 new tests written and confirmed RED before implementation (5 via
`ImportError` since `_is_refusal` didn't exist yet, 1 via a genuine
assertion failure showing the refusal string passed through unchanged).
Verified the failover integration test exercises the real `_invoke_once()`
logic, not a mocked stand-in — only `AgentExecutor.invoke()` is mocked, so
`_is_refusal()` and the `BadRequestError` raise run for real. Final result:
81/81 tests green (75 prior + 6 new), zero regressions.

### Files Affected
- `core/orchestration.py` — `_REFUSAL_PREFIXES` tuple and `_is_refusal()` added; `_invoke_once()` raises `BadRequestError` on refusal detection before returning
- `tests/test_orchestration.py` — Added T-ORC-C-006, T-ORC-C-007, T-ORC-N-008, T-ORC-N-009, T-ORC-N-010
- `tests/test_orchestration_failover.py` — Added T-ORC-N-011
- `TEST_REGISTRY.md` — 6 new T-ORC-* rows added, version → v3.7.0

### Rules Added/Modified
- R-002 — Extended: model failover now also triggers on a detected HTTP-200 content-refusal, not just a raised provider exception

### Tests Added/Modified
- T-ORC-C-006 — PASSING (new)
- T-ORC-C-007 — PASSING (new)
- T-ORC-N-008 — PASSING (new)
- T-ORC-N-009 — PASSING (new)
- T-ORC-N-010 — PASSING (new)
- T-ORC-N-011 — PASSING (new)

### Dependencies
- Depends on: CL-022 (`_FAILOVER_EXCEPTIONS` widening — `BadRequestError` was already a member, reused here rather than adding a new exception type)
- Blocks: None

### Rollback
Remove `_REFUSAL_PREFIXES` and `_is_refusal()` from `core/orchestration.py`;
revert `_invoke_once()` to return immediately after the `max_iterations`
warning check. Delete T-ORC-C-006/007, T-ORC-N-008/009/010 from
`tests/test_orchestration.py`; delete T-ORC-N-011 from
`tests/test_orchestration_failover.py`. Revert `TEST_REGISTRY.md` to v3.6.0.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-033] — 2026-06-22 — COMPLETED

**Type:** FEATURE + BUGFIX (credential retirement)
**Author:** Claude Code
**Task ID:** N/A (add Gemini Flash to the failover chain; retire a stale credential)
**Status:** COMPLETED

### Summary
**Major plan correction found during ANCHOR (before any code changed):**
`_get_api_key()` already had a `gemini/` branch — it has existed since
CL-005/CL-014, returning `GOOGLE_API_KEY`. `GOOGLE_API_KEY` was also already
in `check_env.py`'s `REQUIRED_KEYS` and `_scrub_secrets()`'s redaction list.
`.env` already had both `GOOGLE_API_KEY` and `GEMINI_API_KEY` set, and — checked
programmatically without printing either value — they were byte-identical.
The originally proposed plan (add a *new*, parallel `GEMINI_API_KEY` branch
alongside the existing `GOOGLE_API_KEY` one) would have built a second,
redundant credential path to the same destination — the same "fix that
doesn't change behavior, plus now-duplicated maintenance surface" pattern
already caught repeatedly this session (CL-027's `GMAIL_SENDER`, CL-029's
Tavily `days`).

Raised this before writing any code. Owner decision: `GOOGLE_API_KEY` is
stale (its Google AI Studio project's credits were exhausted — noted around
CL-016) and is being retired outright, not kept as a fallback.
`GEMINI_API_KEY` becomes the sole Gemini credential going forward, with **no
fallback to `GOOGLE_API_KEY`** — confirmed via T-GAT-N-007 (sets both, sets
`GOOGLE_API_KEY` to an obviously-wrong sentinel value, asserts
`_get_api_key()` returns `GEMINI_API_KEY`'s value).

**Implementation:**
- `core/gateway.py`: `_get_api_key()`'s `gemini/` branch now reads
  `GEMINI_API_KEY` exclusively. `_scrub_secrets()`'s redaction tuple swapped
  `GOOGLE_API_KEY` → `GEMINI_API_KEY`.
- `scripts/check_env.py`: `REQUIRED_KEYS` swapped `GOOGLE_API_KEY` →
  `GEMINI_API_KEY`.
- `.env`: `gemini/gemini-2.0-flash` inserted as `LITELLM_MODEL_2`; the prior
  `MODEL_2`/`MODEL_3`/`MODEL_4` (two OpenRouter free models + Mistral) shifted
  down to `MODEL_3`/`MODEL_4`/`MODEL_5`. `MODEL_1` unchanged. The failover
  chain remains purely driven by `LITELLM_MODEL_1..N` — no hardcoded model
  names anywhere in code (`_build_model_chain()` untouched). `GEMINI_API_KEY`'s
  existing value was **not** modified — owner will replace it manually and
  explicitly does not want the current value assumed valid.
- `core/orchestration.py` — **not modified**: `_build_llm_for_model()` has no
  provider-specific `gemini/` branch of its own; it already falls through to
  the generic path that calls `_get_api_key(model)`, so the retirement is
  transparent to it.
- `main.py` — **not modified** (explicitly out of scope): `_make_llm()` still
  reads `GOOGLE_API_KEY` directly and is tested directly by T-MAIN-C-001/002;
  it's dead code on the live pipeline path (unused since CL-017) and was left
  as-is per the DO-NOT-TOUCH boundary, not because it's correct — flagged as
  a known stale reference for a future cleanup task.

**Regressions found and fixed:** two existing tests asserted the
soon-to-be-wrong `GOOGLE_API_KEY` behavior and would have broken: T-GAT-N-003
(asserted `gemini/` routes to `GOOGLE_API_KEY`) and T-GAT-S-001 (asserted
`GOOGLE_API_KEY` is the value scrubbed from logs) — both updated to use
`GEMINI_API_KEY`. T-ENV-N-001 targeted `GOOGLE_API_KEY` for its placeholder
check — since it's no longer in `REQUIRED_KEYS`, that check would silently
stop firing; retargeted to `GEMINI_API_KEY`. `REQUIRED_ENV` (test_gateway.py)
and `VALID_DEFAULTS` (test_env.py) baseline fixtures both renamed
`GOOGLE_API_KEY` → `GEMINI_API_KEY`.

**Naming/ID corrections (ANCHOR, before any test written):** the originating
plan's `T-GW-*` IDs don't match this project's actual gateway-test prefix,
`T-GAT-`. Used `T-GAT-N-007`/`T-GAT-N-008` (next available) instead, and
`T-ENV-N-003` for the env-side check, matching `test_env.py`'s existing `T-ENV-*`
convention exactly (this one the plan got right).

**Documentation cleanup (per owner instruction):** `RULES.md` was checked and
found to have no literal `GOOGLE_API_KEY` reference (only a generic "Gemini"
mention in ZT-003, still accurate) — nothing to change there. `HANDOVER.md`
§8's `GOOGLE_API_KEY`/`GEMINI_API_KEY` rows updated to reflect the retirement
and the new sole-credential status.

TDD: all 3 new tests (T-GAT-N-007, T-GAT-N-008, T-ENV-N-003) written and
confirmed RED before implementation. Verified the real, unmocked
`_get_api_key()` against the actual `.env` afterward (no key values printed)
— confirmed `gemini/gemini-2.0-flash` resolves to the `GEMINI_API_KEY` value.
Final result: 84/84 tests green (81 prior + 3 new), zero regressions after
the 3 fixes above. `python3 main.py` was not run, per instruction.

### Files Affected
- `.env` — `LITELLM_MODEL_2` set to `gemini/gemini-2.0-flash`; prior MODEL_2/3/4 shifted to MODEL_3/4/5
- `core/gateway.py` — `_get_api_key()`'s `gemini/` branch reads `GEMINI_API_KEY` (no fallback); `_scrub_secrets()` redacts `GEMINI_API_KEY` instead of `GOOGLE_API_KEY`
- `scripts/check_env.py` — `REQUIRED_KEYS` swapped `GOOGLE_API_KEY` → `GEMINI_API_KEY`
- `tests/test_gateway.py` — `REQUIRED_ENV` renamed key; T-GAT-N-003/T-GAT-S-001 updated; added T-GAT-N-007, T-GAT-N-008
- `tests/test_env.py` — `VALID_DEFAULTS` renamed key; T-ENV-N-001 retargeted; added T-ENV-N-003
- `TEST_REGISTRY.md` — T-GAT-N-007/008, T-ENV-N-003 added; T-GAT-N-003/S-001, T-ENV-N-001 descriptions updated; version → v3.8.0
- `HANDOVER.md` — §3 CL-033 row updated; §8 `GOOGLE_API_KEY`/`GEMINI_API_KEY` rows updated

### Rules Added/Modified
- None — RULES.md checked, no literal `GOOGLE_API_KEY` reference existed to clean up

### Tests Added/Modified
- T-GAT-N-007 — PASSING (new)
- T-GAT-N-008 — PASSING (new)
- T-ENV-N-003 — PASSING (new)
- T-GAT-N-003, T-GAT-S-001, T-ENV-N-001 — PASSING (updated, same IDs)

### Dependencies
- Depends on: CL-018 (env-driven `_build_model_chain()` — what makes a pure `.env` edit sufficient to add a new chain model), CL-014 (`_get_api_key()`'s original per-provider routing this modifies)
- Blocks: A live run to confirm `gemini/gemini-2.0-flash` actually succeeds as MODEL_2 — not attempted this session (`python3 main.py` not run, per instruction); also blocked on the owner replacing `GEMINI_API_KEY`'s value, since the current value is not confirmed working

### Rollback
Revert `core/gateway.py`'s `_get_api_key()` `gemini/` branch to
`os.getenv("GOOGLE_API_KEY")`; revert `_scrub_secrets()`'s tuple to
`GOOGLE_API_KEY`. Revert `scripts/check_env.py`'s `REQUIRED_KEYS` to
`GOOGLE_API_KEY`. Revert `.env`'s `LITELLM_MODEL_2..5` to the pre-CL-033
4-model chain (`MODEL_2`/`_3`/`_4` back to their prior OpenRouter/Mistral
values, `MODEL_5` removed). Revert `tests/test_gateway.py` and
`tests/test_env.py` to their CL-032 forms; delete T-GAT-N-007/008,
T-ENV-N-003. Revert `TEST_REGISTRY.md` to v3.7.0.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-034] — 2026-06-22 — COMPLETED

**Type:** CHORE (credential/config cleanup)
**Author:** Claude Code
**Task ID:** N/A (`.env` hygiene — owner instruction following CL-033)
**Status:** COMPLETED

### Summary
Following CL-033's `GOOGLE_API_KEY` retirement, audited every key name in
`.env` against actual code usage before removing anything. Confirmed via
`grep` across the whole codebase (not just `.env`) that four entries had
**zero functional references** anywhere — only historical changelog
comments documenting their prior removal from `REQUIRED_KEYS`:

- `GOOGLE_API_KEY` — retired in CL-033 (this session); confirmed identical
  in value to `GEMINI_API_KEY` before CL-033 touched anything; owner
  confirmed it should be removed from `.env` outright (not just the code
  paths CL-033 already updated).
- `OPENAI_API_KEY` — never had a corresponding `openai/` branch in
  `_get_api_key()`; sat in `check_env.py`'s `OPTIONAL_KEYS` since TC-001
  with no functional wiring anywhere. Removed from both `.env` and
  `OPTIONAL_KEYS` — confirmed zero test references first.
- `GMAIL_APP_PASSWORD`, `GMAIL_SENDER` — Gmail SMTP was dropped in TC-006/CL-006;
  both were removed from `REQUIRED_KEYS` in CL-013, but the `.env` lines
  themselves were never deleted until now.

Also fixed a stale header comment at the top of `.env` that literally read
"`.env.example` — committed to git..." — a leftover artifact from when
`.env` was first created by copying `.env.example`; this is the real,
never-committed `.env`, not the example file.

`OPENAI_API_KEY` was additionally removed from `scripts/check_env.py`'s
`OPTIONAL_KEYS` list, since `OPTIONAL_KEYS` membership is the only place it
was ever referenced in code — confirmed no test asserts on `OPTIONAL_KEYS`'
contents before removing.

No test changes were needed — none of the four removed keys, nor
`OPTIONAL_KEYS`'s exact membership, were directly asserted on by any
existing test. `tests/test_main.py`'s `T-MAIN-C-001`/`T-MAIN-C-002` (which
exercise `main.py`'s unused `_make_llm()`, still hardcoded to
`GOOGLE_API_KEY`) set the env var via `monkeypatch.setenv()` within the test
itself, independent of `.env`'s real contents — confirmed unaffected.
Final result: 84/84 tests green (no change in count), zero regressions.
`python3 scripts/check_env.py` re-verified against the real, cleaned `.env`.

### Files Affected
- `.env` — removed `GOOGLE_API_KEY`, `OPENAI_API_KEY`, `GMAIL_APP_PASSWORD`, `GMAIL_SENDER` lines; fixed stale header comment
- `scripts/check_env.py` — `OPENAI_API_KEY` removed from `OPTIONAL_KEYS`
- `HANDOVER.md` — §3 CL-034 row added; §7 deferred items cleaned up (GMAIL_SENDER/rotation items resolved or restated accurately); §8 API keys table updated (GOOGLE_API_KEY/GMAIL_SENDER rows removed, model-chain position numbers corrected)

### Rules Added/Modified
- None — config/credential hygiene, no rule-governed behavior change

### Tests Added/Modified
- None — confirmed via `grep` that no test asserts on any of the four removed keys or on `OPTIONAL_KEYS`'s exact contents

### Dependencies
- Depends on: CL-033 (retired `GOOGLE_API_KEY` from code; this completes the cleanup by removing it from `.env` itself)
- Blocks: None

### Rollback
Re-add `GOOGLE_API_KEY=<value>`, `OPENAI_API_KEY=<value>`,
`GMAIL_APP_PASSWORD=<value>`, `GMAIL_SENDER=<value>` lines to `.env` (values
not recorded in this entry — restore from a pre-CL-034 backup if needed).
Revert `scripts/check_env.py`'s `OPTIONAL_KEYS` to include `OPENAI_API_KEY`.
Revert `.env`'s header comment to its prior wording.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-035] — 2026-06-22 — COMPLETED

**Type:** BUGFIX (lesson agent resilience)
**Author:** Claude Code
**Task ID:** N/A (post-live-run incident fix)
**Status:** COMPLETED

### Summary
Live run on 2026-06-22 15:01 crashed with no email sent, despite JIT/JIC
completing successfully. Root cause was two independent failures chained
together:

1. **Gemini never fired.** `_run_lesson_agent(None, topic)` passed
   `model=None` to `run_agent()`, which starts the failover chain at MODEL_1
   (OpenRouter `gpt-oss-120b:free`). The 9-section structured lesson prompt
   exhausted `max_iter=15` on that free model and returned `{"output": "{}"}`
   — valid JSON, not a refusal string, so neither `_is_refusal()` (CL-032)
   nor a `JSONDecodeError` fired. A model that "succeeds" with useless
   output is invisible to the exception-based failover loop in
   `core/orchestration.py`.
2. **Pipeline crash on empty lesson.** `validate_lesson_output({})` raised
   `ValueError` (0 papers, 0 voices, 0 glossary terms), which
   `run_daily_pipeline()` logged and then re-raised, killing the entire run
   before `send_email()` was ever called. JIT/JIC output, already fetched
   successfully, was discarded.

Two independent fixes, both confined to `main.py`:

- **Fix A** — `_run_lesson_agent()` now defaults to `LITELLM_MODEL_2`
  (`gemini/gemini-2.0-flash`) instead of `None`/MODEL_1 when no explicit
  model is passed: `lesson_model = model or os.getenv("LITELLM_MODEL_2")`.
  The failover loop still handles Gemini failures by advancing to
  MODEL_3+; callers that pass an explicit model string are unchanged. JIT
  and JIC agents are untouched — they still pass `model=None` and start the
  chain at MODEL_1 as before, since their simpler list-output prompts have
  not shown this failure mode.
- **Fix B** — `run_daily_pipeline()` no longer re-raises on
  `validate_lesson_output()` failure. It logs the error, substitutes a new
  `_LESSON_FALLBACK` dict (clearly labelled "Lesson Unavailable", with
  diagnostic bullets pointing at LangSmith traces), and continues to
  `_build_context()` / `render()` / `send_email()` so JIT/JIC content is
  still delivered. `mark_topic_done()` is now gated on
  `lesson is not _LESSON_FALLBACK` — when the fallback was used, the topic
  pointer is **not** advanced, so the same topic is retried on tomorrow's
  run instead of being silently skipped.

Updated `T-MAIN-C-003` (CL-019) to reflect the new default: it now asserts
JIT/JIC calls still get `model=None` while the lesson call gets
`LITELLM_MODEL_2`'s value, rather than asserting `None` for all three.
`T-MAIN-C-006` (lesson `max_iter=15`) needed no change — it doesn't assert
on the `model` kwarg.

### Files Affected
- `main.py` — added `_LESSON_FALLBACK` constant; `_run_lesson_agent()` defaults to `LITELLM_MODEL_2`; `run_daily_pipeline()` catches `ValueError` from `validate_lesson_output()` instead of re-raising, gates `mark_topic_done()` on fallback usage
- `tests/test_main.py` — updated `T-MAIN-C-003`; added `T-MAIN-C-019`/`020`/`021`/`022`
- `TEST_REGISTRY.md` — added T-MAIN-C-019 through T-MAIN-C-022; version → 3.9.0
- `HANDOVER.md` — §3 CL-035 row updated to completed; §7 deferred item resolved

### Rules Added/Modified
- None — bugfix only, no new rule-governed behavior

### Tests Added/Modified
- `T-MAIN-C-019` — `_run_lesson_agent(None, topic)` calls `run_agent()` with `model=os.getenv("LITELLM_MODEL_2")`
- `T-MAIN-C-020` — `run_daily_pipeline()` does not raise when `validate_lesson_output()` raises `ValueError`
- `T-MAIN-C-021` — `send_email()` still called with a non-empty `html` kwarg on lesson validation failure; `mark_topic_done()` not called
- `T-MAIN-C-022` — `_LESSON_FALLBACK` has all keys the context builder/template expect
- `T-MAIN-C-003` (updated) — JIT/JIC calls get `model=None`; lesson call gets `LITELLM_MODEL_2`'s value
- 88/88 tests green (84 + 4 new)

### Dependencies
- Depends on: CL-031 (`validate_lesson_output()`), CL-033 (`LITELLM_MODEL_2` = Gemini Flash)
- Blocks: None

### Rollback
In `main.py`: revert `_run_lesson_agent()`'s `lesson_model = model or os.getenv("LITELLM_MODEL_2")` line back to passing `model` directly to `run_agent()`. Revert the `run_daily_pipeline()` `validate_lesson_output` block to re-raise on `ValueError` instead of substituting `_LESSON_FALLBACK`. Remove the `_LESSON_FALLBACK` constant. Revert `tests/test_main.py`'s `T-MAIN-C-003` and remove `T-MAIN-C-019`–`022`.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-036] — 2026-06-22 — COMPLETED

**Type:** BUGFIX (model deprecation)
**Author:** Claude Code
**Task ID:** N/A (post-live-run incident fix)
**Status:** COMPLETED

### Summary
Third live run (~17:32) failed with `litellm.NotFoundError`:
`VertexAIException - "This model models/gemini-2.0-flash is no longer
available."` Google's model docs (ai.google.dev/gemini-api/docs/models)
list `gemini-2.0-flash` under "Previous models — Shut down"; the stable
replacement is `gemini-2.5-flash`.

`.env`'s `LITELLM_MODEL_2` was found already updated to
`gemini/gemini-2.5-flash` at the start of this session (Phase 1 ANCHOR
confirmed this — no `sed` edit was needed). The only stale reference left
was a human-readable definition string inside `main.py`'s `_LESSON_FALLBACK`
glossary (`section_3i`), which still named `gemini-2.0-flash` — updated to
`gemini-2.5-flash`.

Added `T-GAT-N-009`, which reads `.env` directly (not `os.environ`, since
nothing in `test_gateway.py` loads dotenv) and asserts the `LITELLM_MODEL_2=`
line does not contain `gemini-2.0-flash`. Used `T-GAT-N-009` rather than
`T-GAT-N-008` since that ID was already taken (CL-033's `_scrub_secrets`
GEMINI_API_KEY test).

Smoke test confirmed Gemini 2.5 Flash responds correctly via
`GEMINI_API_KEY`: `litellm.completion(model="gemini/gemini-2.5-flash", ...)`
returned `"working"` with `finish_reason="stop"`. The prompt's literal
`max_tokens=10` smoke script returned `None`/`finish_reason="length"` first
try — Gemini 2.5 Flash spends hidden reasoning tokens before the visible
completion (`total_tokens=27` vs `completion_tokens=1` even for a one-word
reply), unlike 2.0-flash. Raising `max_tokens` to 50 confirmed the model
itself works correctly. Not a production concern: confirmed via `grep` that
neither `core/orchestration.py` nor `core/gateway.py` set `max_tokens` on
any real pipeline call, so this truncation is a smoke-test-script artifact
only.

### Files Affected
- `main.py` — `_LESSON_FALLBACK`'s `section_3i` `LITELLM_MODEL_2` definition string updated to reference `gemini-2.5-flash`
- `tests/test_gateway.py` — added `T-GAT-N-009`
- `TEST_REGISTRY.md` — added T-GAT-N-009; version → 3.10.0
- `HANDOVER.md` — §3 CL-036 row added; §5 third-live-run note added; §8 model chain description updated

### Rules Added/Modified
- None — bugfix only (model-deprecation follow-up to CL-033)

### Tests Added/Modified
- `T-GAT-N-009` — `.env`'s `LITELLM_MODEL_2=` line does not contain `gemini-2.0-flash`
- 89/89 tests green (88 + 1 new)
- Smoke test (manual, not in pytest suite): `litellm.completion()` against `gemini/gemini-2.5-flash` returns `"working"`

### Dependencies
- Depends on: CL-033 (introduced `LITELLM_MODEL_2` = Gemini Flash), CL-035 (introduced `_LESSON_FALLBACK`)
- Blocks: None

### Rollback
Revert `main.py`'s `_LESSON_FALLBACK` `LITELLM_MODEL_2` definition string back to `gemini-2.0-flash` (cosmetic only — does not affect runtime behavior, which reads the slug from `.env`'s `LITELLM_MODEL_2` env var, not from this string). Remove `T-GAT-N-009` from `tests/test_gateway.py`. `.env`'s actual model slug was not changed by this entry (already current) — no env rollback needed.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-037] — 2026-06-22 — COMPLETED

**Type:** BUGFIX (architecture fix + model swap)
**Author:** Claude Code
**Task ID:** N/A (post-live-run incident fix)
**Status:** COMPLETED

### Summary
Fourth live run (~18:06) delivered zero JIC items and a fallback lesson
despite both MODEL_1 and Gemini responding HTTP 200 — two structural
failures, not transient errors:

- **Root cause A:** `openrouter/openai/gpt-oss-120b:free` (LITELLM_MODEL_1)
  does not reliably execute tool calls. 18 consecutive API calls all
  returned `finish_reason='tool_calls'` with `content=''`. JIC exhausted
  all 12 iterations and returned an empty list; JIT barely survived around
  iteration 7.
- **Root cause B:** `_run_lesson_agent()` routed through `run_agent()`'s
  `AgentExecutor` with `tools=_tools()`, but the lesson prompt is a pure
  knowledge-synthesis task with no tool-call need. Gemini 2.5 Flash returned
  valid JSON in a single HTTP 200 call, but `AgentExecutor` discarded it
  because it expected tool-call format, not a direct final answer.

Phase 1 anchor confirmed `.env` was already updated (by the owner) to the
target 6-model chain: `LITELLM_MODEL_1=gemini/gemini-2.5-flash-lite`,
`MODEL_2=gemini/gemini-2.5-flash` (unchanged), `MODEL_3..6` = the prior
MODEL_1/3/4/5 shifted down. Confirmed `_get_api_key()`'s `gemini/` branch
already matches `gemini-2.5-flash-lite` by prefix — zero gateway code
changes needed.

Fix B: `_run_lesson_agent()` now calls `core.gateway.llm_call()` directly,
bypassing `AgentExecutor` entirely (DEV-I-005 exception — lesson synthesis
needs no tools; JIT/JIC are unaffected and still route through `run_agent()`
since they use the search/query_history tools). The `_LESSON_SOURCES`/
`PRIORITY SOURCES` hint is preserved verbatim in the prompt.

**Addendum (anti-hallucination grounding):** since `llm_call()` does no
retrieval, the LLM would otherwise generate paper titles, authors, and
researcher quotes entirely from training weights. Added a pre-retrieval step
before `llm_call()`: two `tools.search.search()` calls (one for arXiv papers,
one for named authoritative voices) format their results into a
`RETRIEVED SOURCES` block appended to the prompt, with explicit instructions
to cite only from that list (or well-known papers/researchers with a real
URL) rather than fabricating citations.

Updating the implementation required updating every test that previously
mocked `main.run_agent` to exercise `_run_lesson_agent()` — `T-MAIN-C-003`,
`006`, `012`, `014`–`019`, `020`, `021`, plus `test_t_main_c_007` and
`test_integration.py`'s `T-INT-I-001` — to mock `main.llm_call` (and
`tools.search.search`, to avoid the grounding step making real network
calls) instead. `T-MAIN-C-006` was repurposed (it tested `max_iter=15` on
`run_agent()`, a path that no longer exists) to instead confirm `llm_call()`
is called with no `tools`/`max_iter` kwargs. `T-MAIN-C-019` was repurposed
(per the option to update-or-delete) to assert `run_agent()` is NOT called
for the lesson, since `T-MAIN-C-023` now covers the "calls llm_call instead"
ground directly.

### Files Affected
- `main.py` — added `from core.gateway import llm_call` import; `_run_lesson_agent()` rewritten to call `llm_call()` directly with a pre-retrieval grounding block, instead of `run_agent()`+`AgentExecutor`; module docstring's RULE REFERENCES and CHANGE LOG updated
- `RULES.md` — DEV-I-005 entry updated with the CL-037 exception for pure-synthesis tasks
- `tests/test_main.py` — added `_patch_lesson_llm()` helper; updated `T-MAIN-C-003`, `006`, `007`, `012`, `014`–`019`, `020`, `021` to mock `llm_call`/`tools.search.search` instead of `run_agent` for the lesson path; added `T-MAIN-C-023`/`024`/`025`
- `tests/test_integration.py` — `T-INT-I-001` updated: `run_agent` mock reduced from 3 side effects to 2 (JIT, JIC); added `llm_call` and `tools.search.search` mocks for the lesson fixture
- `tests/test_gateway.py` — added `T-GAT-N-010`, `T-GAT-C-011`
- `TEST_REGISTRY.md` — updated T-MAIN-C-003/006/019; added T-MAIN-C-023/024/025, T-GAT-N-010, T-GAT-C-011; version → 3.11.0
- `HANDOVER.md` — §3 CL-037 row; §4 DEV-I-005; §5 fourth-live-run note; §6 pending-prompt cleared; §8 model chain (6 models)
- `.env` — no change (owner had already applied the target 6-model chain before this session)

### Rules Added/Modified
- `DEV-I-005` amended: pure knowledge-synthesis pipeline steps with no tool dependency may call `llm_call()` directly, bypassing `run_agent()`/`AgentExecutor`. Tool-dependent steps (JIT/JIC) are unaffected and still required to route through `run_agent()`.

### Tests Added/Modified
- `T-MAIN-C-023` — `_run_lesson_agent()` calls `llm_call()`, not `run_agent()`
- `T-MAIN-C-024` — lesson prompt retains `PRIORITY SOURCES` and gains `RETRIEVED SOURCES` grounding block
- `T-MAIN-C-025` — `_run_lesson_agent()` returns `{}` on non-JSON `llm_call()` response
- `T-GAT-N-010` — `.env`'s `LITELLM_MODEL_1` is `gemini/gemini-2.5-flash-lite`
- `T-GAT-C-011` — `_get_api_key("gemini/gemini-2.5-flash-lite")` routes to `GEMINI_API_KEY`
- Updated `T-MAIN-C-003` (run_agent call_count 3→2), `T-MAIN-C-006` (repurposed: no tools/max_iter kwargs to llm_call), `T-MAIN-C-019` (repurposed: run_agent NOT called), `T-MAIN-C-007`, `012`, `014`–`018`, `020`, `021` (mock target changed), `T-INT-I-001` (mock target changed)
- 94/94 tests green (89 + 5 new), full suite now runs in ~5s with zero real network/API calls (previously `T-MAIN-C-007` was inadvertently hitting the real Gemini API before this fix — caught and corrected during Phase 4)

### Dependencies
- Depends on: CL-033 (introduced `LITELLM_MODEL_2`=Gemini), CL-035 (introduced `_run_lesson_agent`'s model-selection logic, now superseded), CL-036 (confirmed `gemini-2.5-flash` slug)
- Blocks: CL-038 (empty-tool-call-loop detection in `_invoke_once()` — deferred until CL-037 is confirmed working on a live run, per HANDOVER.md §6)

### Rollback
In `main.py`: revert `_run_lesson_agent()` to build `lesson_model = model or os.getenv("LITELLM_MODEL_2")` and call `run_agent(model=lesson_model, tools=_tools(), prompt=prompt, run_name="lesson-agent", max_iter=15)`, parsing `result.get("output", "{}")` instead of `result.get("response", "{}")`; remove the grounding-block pre-retrieval code and the `llm_call` import. Revert `.env`'s `LITELLM_MODEL_1` to `openrouter/openai/gpt-oss-120b:free` and shift `MODEL_3-6` back up if reverting the model swap too. Revert `RULES.md`'s DEV-I-005 entry. Revert test files to their pre-CL-037 state (see CL-035/036 changelog entries for the prior test bodies).

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-038] — 2026-06-22 — COMPLETED

**Type:** BUGFIX (4 root causes — JIT/JIC agent reliability)
**Author:** Claude Code
**Task ID:** N/A (post-live-run incident fix)
**Status:** COMPLETED

### Summary
A fifth live run (~20:41), after CL-037 fixed the lesson agent and MODEL_1
swap, revealed three new failure modes on top of the original (narrower)
CL-038 target — a hard crash this time, with no email sent at all:

- **Root cause A (hard crash):** `query_history`'s `Tool` lambda
  (`lambda topic: str(query_history(topic))`) had no dict→str coercion.
  Flash-Lite, following strict function-calling schema, called it with
  `{"topic": "Vector Databases"}` (a dict) instead of a bare string.
  SQLite's parameterised query rejected the dict:
  `sqlite3.ProgrammingError: type 'dict' is not supported` — crashing the
  whole pipeline. JIC was lost entirely; lesson was never reached.
- **Root cause B (silent failure):** Flash-Lite responded
  `"I can help you find..."` — conversational prose, not a refusal in the
  CL-032 sense. `_is_refusal()`'s prefix list didn't cover conversational
  openers, so the prose reached `json.loads()`, raised `JSONDecodeError`,
  and JIT silently returned `[]` with no failover.
- **Root cause C (structural):** `_invoke_once()`'s system prompt
  (`"Always return your final answer as valid JSON..."`) was a weak hint.
  Models sometimes responded conversationally without calling a tool, or
  summarised tool results in prose instead of the requested schema.
- **Root cause D (silent exhaustion — the original CL-038 target):** some
  models return `finish_reason='tool_calls'` with `content=''` on every
  iteration. No exception, no refusal string (output is `''`, and
  `_is_refusal()` intentionally treats empty as not-a-refusal) — the agent
  silently exhausts `max_iter` and failover never fires.

All four fixes landed together since they share `main.py` and
`core/orchestration.py`:

- **Fix A:** the `query_history` `Tool`'s `func` now coerces
  `topic["topic"] if isinstance(topic, dict) else topic` before calling
  `query_history()`. Defensive — string callers are unaffected.
- **Fix B:** `_REFUSAL_PREFIXES` gained 11 new conversational-opener
  prefixes (`"i can help"`, `"let me "`, `"here are"`, etc.), and
  `_is_refusal()` gained a layer-2 detector: prose >= 40 chars that doesn't
  start with `{`/`[`/`"` and fails `json.loads()` is now also treated as a
  refusal. Empty string remains explicitly not-a-refusal (Root Cause D's
  signal, handled separately).
- **Fix C:** the system prompt now explicitly mandates tool use
  (`"You MUST use the search tool..."`, `"You MUST use the query_history
  tool..."`), forbids conversational replies and prose summaries, and states
  the only valid output is JSON matching the schema — no soft hints.
- **Fix D:** `AgentExecutor`'s `return_intermediate_steps` flipped to `True`
  (adds `intermediate_steps` to the result dict; does not change
  `result["output"]`, so existing output parsing is unaffected). A new
  `_detect_empty_tool_loop()` checks the last 3 intermediate steps for
  all-empty tool output and raises `BadRequestError` (already in
  `_FAILOVER_EXCEPTIONS`) on detection, checked before the `_is_refusal()`
  check in `_invoke_once()`.

Wrote 11 new tests (2 in `tests/test_main.py`, 9 in `tests/test_orchestration.py`)
before any implementation change, per TST-T-001. 6 of the 11 asserted
genuinely new behavior and were RED at Phase 2 (`T-MAIN-C-026`,
`T-ORC-N-012/013/014/015`, `T-ORC-C-012`); the other 5 (`T-MAIN-C-027`,
`T-ORC-C-008/009/010/011`) are regression guards confirming unchanged
behavior on the new code paths and were already GREEN, which is expected —
they lock down that the rewrite doesn't break what already worked.

### Files Affected
- `main.py` — `_tools()`'s `query_history` `Tool` lambda now coerces dict args to their `"topic"` string value; module CHANGE LOG updated
- `core/orchestration.py` — `_REFUSAL_PREFIXES` expanded; `_is_refusal()` gained a layer-2 non-JSON-prose detector; `_invoke_once()`'s system prompt rewritten to mandate tool use; `return_intermediate_steps=True`; new `_EMPTY_TOOL_LOOP_THRESHOLD`/`_detect_empty_tool_loop()`; `import json` added; module CHANGE LOG updated
- `tests/test_main.py` — added `T-MAIN-C-026`/`027`; imported `_tools`
- `tests/test_orchestration.py` — added `T-ORC-N-012`–`015`, `T-ORC-C-008`–`012`
- `TEST_REGISTRY.md` — added all 11 new test rows; version → 3.12.0
- `HANDOVER.md` — §3 CL-038 row (completed); §5 fifth-live-run note; §6 CL-038 archived

### Rules Added/Modified
- None — bugfix only, no new rule-governed behavior (R-002/R-005 failover and iteration-limit rules are unchanged in substance, just given more triggers)

### Tests Added/Modified
- `T-MAIN-C-026` — `query_history` tool coerces dict arg to its string value
- `T-MAIN-C-027` — `query_history` tool still works with a plain str arg (regression)
- `T-ORC-N-012`/`013` — `_is_refusal()` detects "I can help"/"Let me" conversational openers
- `T-ORC-N-014` — `_is_refusal()`'s layer-2 detector flags non-JSON prose >= 40 chars
- `T-ORC-C-008`/`009`/`010` — `_is_refusal()` still False for JSON array/object/empty string (regression)
- `T-ORC-N-015` — `_invoke_once()` raises `BadRequestError` on >=3 consecutive empty tool-call steps
- `T-ORC-C-011` — `_invoke_once()` does not raise with real intermediate-step content (regression)
- `T-ORC-C-012` — system prompt mandates tool use, forbids prose, restricts output to JSON
- 105/105 tests green (94 + 11 new)

### Dependencies
- Depends on: CL-032 (introduced `_is_refusal()` and `_REFUSAL_PREFIXES`), CL-037 (MODEL_1 swap to Flash-Lite — the model whose strict function-calling schema surfaced root causes A/B/C)
- Blocks: None — no pending CLs after this one; next step is monitoring live runs for stability, not further code changes

### Rollback
In `main.py`: revert the `query_history` `Tool`'s `func` to `lambda topic: str(query_history(topic))` (drops dict coercion). In `core/orchestration.py`: revert `_REFUSAL_PREFIXES` to the CL-032 9-entry tuple and `_is_refusal()` to its single-layer prefix-only check; revert the system prompt in `_invoke_once()` to `"You are a helpful AI assistant..."`; revert `return_intermediate_steps` to `False`; remove `_EMPTY_TOOL_LOOP_THRESHOLD`/`_detect_empty_tool_loop()` and the empty-loop check in `_invoke_once()`; remove the `import json` if otherwise unused. Remove the 11 new tests from `tests/test_main.py`/`tests/test_orchestration.py`.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-039] — 2026-06-22 — COMPLETED

**Type:** BUGFIX (lesson JSON parsing)
**Author:** Claude Code
**Task ID:** N/A (post-live-run incident fix)
**Status:** COMPLETED

### Summary
A sixth live run (~21:50), the first after CL-038, confirmed JIT and JIC are
now stable — Flash-Lite correctly called tools and returned JSON arrays for
both. The lesson agent was the only remaining failure: `llm_call()` (the
direct `litellm.completion()` path, established as a DEV-I-005 exception in
CL-037) received HTTP 200 with `finish_reason=stop`, but the response
content was valid JSON wrapped in markdown code fences:
``` ```json\n{"topic_name": "Vector Databases", ...}\n``` ```. `json.loads()`
in `_run_lesson_agent()` rejected the fenced string outright —
`JSONDecodeError` — discarding otherwise-complete, correct JSON. The
`_LESSON_FALLBACK` substituted as designed (CL-035); JIT/JIC and email
delivery were unaffected.

Root cause: `litellm.completion()` was called with no `response_format`
parameter. Without it, instruction-tuned models are free to apply their
default "helpful" formatting — which, per Google's own structured-output
docs (ai.google.dev/gemini-api/docs/structured-output) and LiteLLM's JSON
mode docs (docs.litellm.ai/docs/completion/json_mode), routinely means
wrapping long JSON in fences, since RLHF training rewarded that as "clear
formatting." This only affects the lesson's direct `llm_call()` path — the
JIT/JIC `AgentExecutor`/tool-calling path (`core/orchestration.py`) never
returns fenced content, because `create_tool_calling_agent` reads
function-call tokens, not free-form prose, and confirmed working in CL-038.

Two-layer fix, confined entirely to `core/gateway.py`:

- **Layer 1 (primary, API-level):** `litellm.completion()` now passes
  `response_format={"type": "json_object"}`. LiteLLM translates this to each
  provider's native param — Gemini's `generationConfig.responseFormat.text.
  mimeType`, Mistral's `response_format`, and pass-through for OpenRouter.
  Confirmed by official docs for all 6 chain members; Gemini 2.5 Flash/
  Flash-Lite explicitly listed in Google's structured-output support table.
- **Layer 2 (defensive):** new `_strip_fences()` helper strips ` ```json
  ... ``` ` or ` ``` ... ``` ` wrappers from the response text before
  `llm_call()` returns it. Covers any provider that silently ignores
  `response_format` — some free-tier OpenRouter models (MODEL_3/4/5 in the
  fallback chain) drop unsupported params without erroring.

`response_format` was deliberately NOT added to `core/orchestration.py` or
`_invoke_once()` — it would conflict with `ChatLiteLLM`'s tool-calling mode,
and the JIT/JIC path was confirmed working in CL-038 and is out of scope per
the task's explicit "DO NOT TOUCH" list. `_run_lesson_agent()`,
`validate_lesson_output()`, and `_LESSON_FALLBACK` are unchanged — the fix
is entirely upstream of them, in `llm_call()`'s own response handling.

### Files Affected
- `core/gateway.py` — added `_strip_fences()` helper; `llm_call()`'s `litellm.completion()` call now passes `response_format={"type": "json_object"}`; response text now passed through `_strip_fences()` before being returned; module CHANGE LOG updated
- `tests/test_gateway.py` — added `T-GAT-C-012`/`013`/`014`/`015`, `T-GAT-E-004`/`005`; module CHANGE LOG updated (also backfilled the CL-036/037 entries it was missing)
- `TEST_REGISTRY.md` — added 6 new test rows; version → 3.13.0
- `HANDOVER.md` — §3 CL-039 row (completed); §5 sixth-live-run note; §6 CL-039 archived

### Rules Added/Modified
- None — bugfix only, no new rule-governed behavior

### Tests Added/Modified
- `T-GAT-C-012`/`013` — `_strip_fences()` strips ` ```json ``` `/ ` ``` ``` ` wrappers
- `T-GAT-E-004`/`005` — `_strip_fences()` no-op when no fences present; handles surrounding whitespace
- `T-GAT-C-014` — `llm_call()` passes `response_format={"type": "json_object"}` to `litellm.completion()`
- `T-GAT-C-015` — `llm_call()` returns fence-stripped text even when the model returns fenced JSON
- 111/111 tests green (105 + 6 new)

### Dependencies
- Depends on: CL-037 (introduced `llm_call()` as the lesson agent's direct path), CL-038 (confirmed JIT/JIC stable, narrowing this fix to the lesson path only)
- Blocks: None — no pending CLs after this one; next step is a live run to confirm the fix, then monitoring for 3 consecutive clean daily runs

### Rollback
In `core/gateway.py`: remove the `response_format={"type": "json_object"}` kwarg from the `litellm.completion()` call in `llm_call()`; remove the `_strip_fences()` helper and revert `text = _strip_fences(response.choices[0].message.content or "")` to `text = response.choices[0].message.content`. Remove the 6 new tests from `tests/test_gateway.py`.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-040] — 2026-06-22 — COMPLETED

**Type:** BUGFIX (query_history tool — unknown dict key)
**Author:** Cowork (Claude)
**Task ID:** N/A (post-live-run incident fix, seventh live run)
**Status:** COMPLETED

### Summary
Seventh live run (2026-06-22 ~22:19) crashed at JIT agent startup with `KeyError: 'topic'`. Root cause: the `query_history` Tool lambda in `main.py` assumed dicts passed by the model always use key `"topic"`. Flash-Lite passed `{"title": "..."}` instead. CL-038 fixed the `sqlite3.ProgrammingError` for `{"topic": "..."}` dicts but left a fragile single-key lookup. Fix: replaced `topic["topic"]` with a `next(... for k in ("topic", "title", "name", "query") ...)` key-priority probe with `str(topic)` as final fallback — no KeyError is possible regardless of what key the model uses. JIT/JIC/lesson path and all other files untouched.

### Files Affected
- `main.py` — `_tools()` `query_history` lambda: robust multi-key fallback replacing single `["topic"]` lookup
- `tests/test_main.py` — added T-MAIN-N-028 (`"title"` key) and T-MAIN-N-029 (unknown key fallback)

### Rules Added/Modified
- None — bugfix only

### Tests Added/Modified
- `T-MAIN-N-028` — query_history tool coerces `{"title": "..."}` dict correctly — PASSING
- `T-MAIN-N-029` — query_history tool falls back to `str(dict)` for unknown keys — PASSING
- 113/113 tests green (111 + 2 new)

### Dependencies
- Depends on: CL-038 (introduced the dict-coercion pattern for `query_history` tool)
- Blocks: None

### Rollback
In `main.py`, revert the `query_history` Tool lambda back to:
`query_history(topic["topic"] if isinstance(topic, dict) else topic)`
Remove T-MAIN-N-028 and T-MAIN-N-029 from `tests/test_main.py`.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-041] — 2026-06-22 — COMPLETED

**Type:** CONFIGURATION + SECURITY (model provider migration)
**Author:** Claude Code
**Task ID:** N/A (owner-initiated cost optimization)
**Status:** COMPLETED

### Summary
Niteen migrated MODEL_1/MODEL_2 from Google AI Studio (`gemini/` prefix,
`GEMINI_API_KEY`, free-tier quota — 15 RPM on Flash) to Vertex AI
(`vertex_ai/` prefix, service-account JSON via `GOOGLE_APPLICATION_CREDENTIALS`,
$300 GCP credit — 1000 RPM on Flash). AI Studio API keys were incurring
real cost; Vertex AI's $300 credit covers the same underlying Gemini models
at far higher capacity with no token-per-day cap during the credit period.

Phase 1 anchor found `.env` already updated with the target `vertex_ai/`
slugs and a `GOOGLE_APPLICATION_CREDENTIALS` line — but the path was a
mismatched filename (`<gcp-project>.json`,
which didn't exist) rather than the real service-account file at
`<service-account>.json` (confirmed by `project_id` match in
the JSON's contents). Flagged to the owner before proceeding; owner
corrected the `.env` path before implementation began.

`core/gateway.py`'s `_get_api_key()` gained an explicit `vertex_ai/` branch
returning `None` — Vertex AI authenticates via Google's Application Default
Credentials (ADC), which `litellm.completion()` picks up automatically from
`GOOGLE_APPLICATION_CREDENTIALS`; passing an `api_key=` argument for a
`vertex_ai/` model would conflict with ADC and cause an auth failure. This
was a no-behavior-change-but-explicit-intent fix in practice — `_get_api_key()`
already fell through to `None` for any unrecognized prefix, so the new
branch documents the design decision rather than altering runtime behavior.
The `gemini/` branch is unchanged and kept as a fallback. `scripts/check_env.py`
gained `GOOGLE_APPLICATION_CREDENTIALS` in `REQUIRED_KEYS` (GEMINI_API_KEY
stays required too, as the fallback's credential). `_scrub_secrets()` also
gained `SENDGRID_API_KEY` in its redaction loop, per the task's explicit
Phase 3 instruction (a previously-unrelated SEC-X-001 gap bundled into this
CL).

Smoke-tested the real Vertex AI auth path directly via `litellm.completion()`
and hit `ModuleNotFoundError: No module named 'google.auth'` — LiteLLM's
`vertex_ai/` support requires the `google-auth` package, never previously
installed since nothing in this codebase used the Vertex AI path before.
Installed `google-auth==2.55.0` and added it to `requirements.txt`. Re-ran
the smoke test: `vertex_ai/gemini-2.5-flash-lite` authenticated successfully
via the service-account JSON and returned `"working"` with no auth errors.

Added `RULES.md` rule `DEV-I-006` (the task's prompt referenced replacing an
existing CL-033 rule about `vertex_ai/` vs `gemini/` prefixes, but no such
rule text existed in `RULES.md` — added as a new rule instead, since no
prior rule covered this routing distinction).

### Files Affected
- `.env` — model slug path corrected by owner (`GOOGLE_APPLICATION_CREDENTIALS` pointed at a non-existent filename; fixed to the real service-account JSON path) — no other `.env` changes were needed, `LITELLM_MODEL_1/2` were already on `vertex_ai/` slugs
- `core/gateway.py` — `_get_api_key()` gained an explicit `vertex_ai/` branch returning `None`; `_scrub_secrets()`'s redaction loop gained `SENDGRID_API_KEY`; module CHANGE LOG updated
- `scripts/check_env.py` — `GOOGLE_APPLICATION_CREDENTIALS` added to `REQUIRED_KEYS`; module CHANGE LOG updated
- `requirements.txt` — added `google-auth==2.55.0` (newly required by LiteLLM's `vertex_ai/` path; not previously a dependency)
- `RULES.md` — added `DEV-I-006` documenting the `vertex_ai/`/`gemini/` auth-path distinction
- `tests/test_gateway.py` — added `T-GAT-N-011`/`012`, `T-GAT-C-016`, `T-GAT-E-006`, `T-GAT-S-002`; updated `T-GAT-N-010`'s assertion to match on the model-name substring instead of the full `gemini/`-prefixed string, since the prefix changed
- `tests/test_env.py` — added `GOOGLE_APPLICATION_CREDENTIALS` to `VALID_DEFAULTS`; added `T-ENV-N-004`, `T-ENV-C-002`
- `TEST_REGISTRY.md` — added 6 new test rows; version → 3.15.0
- `HANDOVER.md` — §3 CL-041 row (completed); §8 API keys table + model chain description

### Rules Added/Modified
- `DEV-I-006` (new) — `vertex_ai/` and `gemini/` are different auth paths; never mix or assume interchangeable; never pass `api_key=` to a `vertex_ai/` `litellm.completion()` call

### Tests Added/Modified
- `T-GAT-N-011`/`012` — `_get_api_key()` returns `None` for `vertex_ai/` flash-lite/flash
- `T-GAT-C-016` — `_get_api_key()`'s `gemini/` branch still returns `GEMINI_API_KEY` (regression)
- `T-GAT-E-006` — `_scrub_secrets()` doesn't raise when `GEMINI_API_KEY` is unset
- `T-GAT-S-002` — `_scrub_secrets()` redacts `SENDGRID_API_KEY`
- `T-ENV-N-004` — `validate_env()` raises naming `GOOGLE_APPLICATION_CREDENTIALS` when missing
- `T-ENV-C-002` — `validate_env()` passes when `GOOGLE_APPLICATION_CREDENTIALS` is present
- Updated `T-GAT-N-010` — now asserts on the `gemini-2.5-flash-lite` model-name substring rather than the full `gemini/`-prefixed string
- 120/120 tests green (113 + 7 new)

### Dependencies
- Depends on: CL-037 (introduced `LITELLM_MODEL_1`=Flash-Lite, now migrated to `vertex_ai/`), CL-036 (introduced `LITELLM_MODEL_2`=Flash, now migrated to `vertex_ai/`)
- Blocks: None — next scheduled run is 2026-06-24 07:00 via launchd; this CL must be confirmed working before then (smoke test already confirmed)

### Rollback
In `.env`: set `LITELLM_MODEL_1=gemini/gemini-2.5-flash-lite` and `LITELLM_MODEL_2=gemini/gemini-2.5-flash` (no code change needed — `GEMINI_API_KEY` stays set, the failover chain is purely env-driven). In `core/gateway.py`: the `vertex_ai/` branch in `_get_api_key()` and the `SENDGRID_API_KEY` scrub addition can stay (harmless if unused) or be removed. In `scripts/check_env.py`: remove `GOOGLE_APPLICATION_CREDENTIALS` from `REQUIRED_KEYS` if reverting fully. Remove the 7 new tests from `tests/test_gateway.py`/`tests/test_env.py`.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-042] — 2026-06-23 — COMPLETED

**Type:** BUGFIX (search tool crash)
**Author:** Claude Code
**Task ID:** N/A (live-run incident found while smoke-testing CL-041)
**Status:** COMPLETED

### Summary
After CL-041's Vertex AI migration was smoke-tested via `litellm.completion()`,
Niteen approved running the full pipeline (`python3 main.py`) live, ahead of
the next scheduled launchd run, to confirm the migration end-to-end. The
first attempt (eighth live run) crashed the whole pipeline immediately at
the JIT agent's first tool call:

```
KeyError: slice(None, 400, None)
  File "tools/search.py", line 44, in search
    query = query[:400]
```

Root cause: Vertex AI's Flash-Lite passed the `search` tool a dict argument
(e.g. `{"query": "..."}`) instead of a bare string, per strict
function-calling schema. `tools/search.py`'s `query[:400]` slices a dict the
same way it would a list — Python raises `KeyError(slice(...))` rather than
`TypeError`, since `dict.__getitem__` doesn't support slice keys. This is
the exact same bug class CL-038/040 already fixed for the `query_history`
tool — but `search` was never hardened, since the prior MODEL_1
(`gpt-oss-120b:free` via OpenRouter, then `gemini-2.5-flash-lite` via AI
Studio) apparently never triggered it. Vertex AI's Gemini, called through a
different LiteLLM code path (`vertex_ai/` vs `gemini/`), surfaced it.

Fix mirrors CL-038/040 exactly: `main.py`'s `_tools()` now wraps `search` in
a lambda that probes a dict argument for `("query", "q", "search_query",
"text")` keys before falling back to `str(query)`, same pattern as
`query_history`'s multi-key probe. `tools/search.py` itself is unchanged —
the coercion lives in the Tool wrapper, consistent with where the
`query_history` fix was applied.

Confirmed fixed via a second live run immediately after: pipeline completed
end-to-end — JIT succeeded, email delivered (SendGrid 202), ledger updated,
topic pointer advanced 6→7 ("Knowledge Graphs — Structure, Querying, and
LLM Integration"). No data was written or corrupted by the first (crashed)
run — the crash occurred before `_write_ledger()`/`mark_topic_done()` are
ever reached in `run_daily_pipeline()`.

**Known follow-up, not fixed in this CL:** JIC returned an empty list on the
successful run. Live logs show several of JIC's search queries arrived as a
deeply nested protobuf-shaped string (e.g. `{'key': 'fields', 'value':
{'struct_value': {'key': '__arg1', 'value': {'string_value': '...'}}}}`) —
Vertex AI's native function-calling format apparently sometimes nests args
this way, which doesn't match the flat `("query", "q", "search_query",
"text")` key probe, so the fallback `str(query)` produced a garbled query
string. Both Tavily (400 Bad Request on the garbled query) and the
DuckDuckGo fallback (rate-limited) failed for those calls, so JIC's agent
ultimately had nothing to work with and returned non-JSON output. This is a
quality degradation, not a crash — flagged for a future CL, not blocking.

### Files Affected
- `main.py` — `_tools()`'s `search` Tool `func` now wraps `search()` with the same dict-coercion pattern as `query_history`
- `tests/test_main.py` — added `T-MAIN-N-030`/`031`/`032`

### Rules Added/Modified
- None — bugfix only, same pattern as CL-038/040

### Tests Added/Modified
- `T-MAIN-N-030` — `search` Tool coerces a dict arg to its string value
- `T-MAIN-N-031` — `search` Tool still works with a plain str arg (regression)
- `T-MAIN-N-032` — `search` Tool falls back to `str(dict)` on an unknown key
- 123/123 tests green (120 + 3 new)

### Dependencies
- Depends on: CL-038/040 (established the dict-coercion pattern for `query_history`), CL-041 (Vertex AI migration that surfaced this gap)
- Blocks: None. Follow-up needed: nested protobuf-shaped tool-call args degrading JIC's search query quality (see Summary) — not yet filed as its own CL

### Rollback
In `main.py`: revert the `search` Tool's `func` to `func=search` (drops dict coercion — reintroduces the crash risk if a model passes a dict arg again). Remove `T-MAIN-N-030`/`031`/`032` from `tests/test_main.py`.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-043] — 2026-06-23 — COMPLETED

**Type:** BUGFIX (JIC empty-results investigation — two root causes)
**Author:** Claude Code
**Task ID:** N/A (live-run investigation requested after CL-042)
**Status:** COMPLETED

### Summary
Investigated why JIC returned an empty list on the ninth live run (the run
that confirmed CL-042's fix). Found two distinct issues:

**Root cause A (defensive hardening, not confirmed as this run's actual
cause):** the ninth live run's logs showed a DuckDuckGo fallback query
containing a garbled, str()-rendered nested dict —
`{'key': 'fields', 'value': {'struct_value': {'key': '__arg1', 'value':
{'string_value': '...'}}}}` — consistent with a protobuf Struct/Value
shape that CL-042's flat key-probe (`("query", "q", "search_query",
"text")`) wouldn't match. Centralized the dict-coercion logic from CL-042
into a new `_coerce_tool_arg()` helper in `main.py`, shared by both the
`search` and `query_history` Tool wrappers, and taught it to recursively
unwrap `value`/`struct_value`/`string_value`/`fields` wrapper keys before
falling back to `str(arg)`. Verified against the exact literal structure
captured from the production log — correctly extracts the real query text.
Direct repro attempts (multiple live calls to `_run_jic_agent()` and
`run_agent()`) did not reproduce this exact shape again, so it could not be
confirmed as the dominant cause of the empty JIC result on investigation —
but the evidence in the original log was concrete, so the hardening stands
as defense-in-depth regardless.

**Root cause B (confirmed, the actual dominant cause):** while
investigating, found that the ninth live run's logs showed **every single
JIT/JIC search call** failing with `Tavily search failed — falling back to
DuckDuckGo: 400 Client Error`, and the DuckDuckGo fallback also failing
(rate-limited) on every call — meaning JIT/JIC had *zero* real search
results to work with for the entire run, independent of any tool-arg
parsing question. Reproduced directly against the live Tavily API and
found the real cause via Tavily's own error body:
`{"detail":{"error":"When days is set, start_date or end_date cannot be
set"}}`. Vertex AI's Gemini was embedding `after:YYYY-MM-DD` (and
presumably `before:YYYY-MM-DD`) search-operator syntax into its search
queries — a reasonable response to the JIT/JIC prompts' "today is X, find
items after 7-day cutoff Y" recency instructions — and Tavily's API parses
that operator out of the query text into an internal `start_date`, which
collides with `tools/search.py`'s own explicit `days=7` parameter (added in
CL-029). Confirmed via a direct Tavily API call with and without the
`after:` clause: identical query, `days=7`, `topic="news"` — 400 with the
clause present, 200 with 10 real results without it.

Fix: `search()` now strips `after:YYYY-MM-DD`/`before:YYYY-MM-DD` clauses
from the query text before calling Tavily (recency is already enforced via
`days=7`, so the model's own date clause is redundant anyway, not just
broken). Verified fixed by re-running the exact previously-failing query
directly against the live Tavily API — now returns 10 results.

**Known follow-up, not fixed in this CL:** after both fixes, a direct
`_run_jic_agent()` repro still returned an empty list once, with
`result.get("output") == ""` — the agent exhausted `max_iter=12` without
ever producing a final JSON answer, despite real search results now being
available (no refusal, no empty-tool-loop, no crash — pure iteration
exhaustion). JIC's task (10 distinct foundational-concept searches each
needing a search + a `query_history` cooldown check) may need more than 12
iterations now that searches are actually succeeding and returning content
to process, where they previously failed fast and let the agent give up
early. Flagged for a future CL (likely: raise JIC's `max_iter`, mirroring
the lesson agent's `max_iter=15`, or reduce the per-item tool-call
overhead) — not fixed here since it's a capacity/budget question requiring
its own measurement, not a one-line fix.

### Files Affected
- `main.py` — added `_coerce_tool_arg()` helper (centralizes and extends the CL-042 dict-coercion logic with protobuf Struct/Value unwrapping); both `search` and `query_history` Tool wrappers now use it; module CHANGE LOG updated
- `tools/search.py` — `search()` now strips embedded `after:`/`before:YYYY-MM-DD` clauses before calling Tavily; module CHANGE LOG updated
- `tests/test_main.py` — added `T-MAIN-N-033`/`034`; imported `_coerce_tool_arg`
- `tests/test_search.py` — added `T-SRC-N-002`/`003`
- `TEST_REGISTRY.md` — added 4 new test rows; version → 3.17.0
- `HANDOVER.md` — §5 tenth-live-run-investigation note; §7 deferred item for the JIC max_iter follow-up

### Rules Added/Modified
- None — bugfix only

### Tests Added/Modified
- `T-MAIN-N-033` — `_coerce_tool_arg()` unwraps a nested protobuf Struct/Value shape
- `T-MAIN-N-034` — the `search` Tool unwraps that shape end-to-end
- `T-SRC-N-002`/`003` — `search()` strips embedded `after:`/`before:YYYY-MM-DD` clauses
- 127/127 tests green (123 + 4 new)

### Dependencies
- Depends on: CL-029 (introduced `days=7` recency filter, now in conflict with model-embedded date operators), CL-042 (introduced the dict-coercion pattern this CL centralizes and extends)
- Blocks: None. Follow-up needed: JIC's `max_iter=12` may be insufficient now that searches reliably succeed — not yet filed as its own CL, needs measurement first

### Rollback
In `tools/search.py`: remove the `_DATE_OPERATOR_RE` strip step in `search()` (reintroduces the Tavily 400 risk if a model embeds a date operator again). In `main.py`: revert `search`/`query_history` Tool wrappers to their CL-042 inline-lambda form instead of calling `_coerce_tool_arg()` (loses the protobuf-unwrap defense, keeps the flat-key probe). Remove the 4 new tests.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-044] — 2026-06-24 — IMPLEMENTED (live smoke test pending owner approval)

**Type:** BUGFIX (3 issues — prompt clarity, iteration budget, hardcoded subject)
**Author:** Claude Code
**Task ID:** N/A (Niteen-reported issue, root-cause corrected mid-investigation)
**Status:** Code complete, 133/133 tests green. Issue A's live-API smoke test
(confirming the LLM actually stops repeating the category name) is
recommended but not yet run — awaiting Niteen's explicit go-ahead per this
project's standing rule on live-API spend.

### Summary
Niteen reported the last two emails had "topic names replaced by a generic
common term." An earlier planning pass misdiagnosed this as the email
subject line; Niteen corrected this with a screenshot showing the actual
JIT table's "Topic" column reading "Just-In-Time AI" for every row, while
Source/Date/Why-It-Matters correctly differed per row.

**Issue A (primary, confirmed root cause):** both `_run_jit_agent()` and
`_run_jic_agent()`'s prompts open with a category-naming sentence ("Find
exactly 10 Just-In-Time AI news items..." / "...Just-In-Case foundational
AI/ML concepts...") and then ask for a bare `topic (str)` field with no
example or disambiguation. The model echoes the salient category phrase
from its own instructions into every item's `topic` key instead of
synthesizing each item's specific headline — the same bug class CL-031
already fixed for the lesson's 3B/3F/3G/3H/3C sections. Confirmed
unrelated to model quality or the Vertex AI migration: a more capable
model doesn't fix an ambiguous instruction, it follows it more
*consistently* (all 10 rows, not some). Fix: rewrote the `topic` key's
description in both prompts with a negative instruction + concrete
example, mirroring CL-031's pattern exactly. Pure prompt-text change — the
JSON schema, keys, `json.loads()` parsing, and `config/email_template.html`'s
`{{ item.topic }}` rendering are all unchanged; only the LLM's chosen
content for that key should improve.

**Issue B:** `_run_jit_agent()`/`_run_jic_agent()` both raised `max_iter`
12→16 (+4), per Niteen's request and CL-043's deferred finding (a direct
repro had shown `_run_jic_agent()` exhausting 12 iterations with
`output=""` and no crash/refusal/empty-loop, once searches reliably
succeed post-CL-043 and give the agent more content to process per item).

**Issue C (secondary, found independently while investigating Issue A, not
what Niteen originally reported):** `core/delivery.py`'s `send_email()`
had used a hardcoded `_SUBJECT = "Your Daily AI Learning Brief"` constant
with no parameter to vary it since the very first implementation (TC-006).
`send_email()` now accepts an optional `subject` parameter (default
unchanged, so every existing caller is unaffected); `main.py` passes a
dynamic subject built from `lesson_topic` — the deterministic topic from
`get_next_topic()`/`topic_pool.json`, never from `lesson.get("topic_name")`,
since that's `"Lesson Unavailable"` on a `_LESSON_FALLBACK` day.

All three fixes verified via TDD: 6 new tests written RED before any
implementation, all confirmed RED for the correct reason, then GREEN after
the corresponding fix. 3 existing tests (`T-MAIN-C-004`/`005`/`013`,
hardcoded `max_iter==12`) updated to `max_iter==16`.

### Files Affected
- `main.py` — JIT/JIC prompts' `topic` key description rewritten with negative instruction + example; `max_iter` 12→16 in both `_run_jit_agent()`/`_run_jic_agent()`; `send_email()` call site now passes a dynamic `subject` built from `lesson_topic`
- `core/delivery.py` — `send_email()` gained an optional `subject` parameter (default = `_SUBJECT`); module CHANGE LOG updated
- `tests/test_main.py` — added `T-MAIN-C-028`/`029` (topic-field instruction), `T-MAIN-C-030`/`031` (dynamic subject, including the fallback-day case); updated `T-MAIN-C-004`/`005`/`013` to `max_iter==16`
- `tests/test_delivery.py` — added `T-DEL-C-002`/`003`; module CHANGE LOG updated

### Rules Added/Modified
- None — bugfix only, same negative-instruction-plus-example pattern CL-031 already established as this project's convention for fixing ambiguous LLM field descriptions

### Tests Added/Modified
- `T-MAIN-C-028` — JIT prompt forbids repeating the category name, requires a unique-per-item headline with an example
- `T-MAIN-C-029` — same for JIC's category phrase
- `T-MAIN-C-030` — `run_daily_pipeline()` calls `send_email()` with a subject containing the real `lesson_topic`
- `T-MAIN-C-031` — subject still contains the real `lesson_topic` (not `"Lesson Unavailable"`) on a `_LESSON_FALLBACK` day
- `T-DEL-C-002` — `send_email()` uses a passed `subject` kwarg
- `T-DEL-C-003` — `send_email()` falls back to the default subject when omitted (regression guard)
- Updated `T-MAIN-C-004`/`005`/`013` — `max_iter` assertion 12→16
- 133/133 tests green (127 + 6 new)

### Dependencies
- Depends on: CL-031 (established the negative-instruction-plus-example pattern this CL reuses for Issue A), CL-043 (deferred the max_iter finding this CL resolves for Issue B)
- Blocks: None. Issue A's live-API smoke test (confirming the actual LLM output, not just the prompt text) is recommended before the next scheduled launchd run but requires Niteen's explicit go-ahead first

### Rollback
In `main.py`: revert the `topic` key wording in both prompts to the bare `"topic (str), source (str), ..."` form; revert `max_iter` 16→12 in both `_run_jit_agent()`/`_run_jic_agent()`; revert the `send_email()` call site to `send_email(html=html, to=to)` with no `subject` kwarg. In `core/delivery.py`: revert `send_email()`'s signature to drop the `subject` parameter. Remove the 6 new tests and revert the 3 updated `max_iter` assertions back to 12.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-046] — 2026-06-24 — COMPLETED

**Type:** BUGFIX (failover gap — zero-step empty-output turns)
**Author:** Claude Code
**Task ID:** N/A (live-run follow-up to CL-044; Phase 0 doc research mandated by Cowork before implementation)
**Status:** COMPLETED

### Summary
A live run after CL-044 (which raised JIT/JIC `max_iter` 12→16) still showed
JIT returning empty (`"JIT agent output was not valid JSON"`). A direct,
non-destructive call to `_invoke_once()` with the exact JIT prompt
reproduced it: `intermediate_steps=[]`, `output=''` — Gemini returned zero
tool calls and zero text on the very first turn.

Per Niteen's explicit instruction, this was investigated via official
documentation and the actual installed dependency source rather than
further live-API trial-and-error. **Correction to record:** the original
planning pass (written before this implementation) cited GitHub issue
[langchain-ai/langchain#34989](https://github.com/langchain-ai/langchain/issues/34989)
as confirming "AgentExecutor exits the instant zero tool_calls." That issue
is actually about agent *latency*, on `langchain` 1.1.x/`langchain_classic`
— an unrelated topic on a far-newer major version line than our pinned
`langchain==0.3.7`. That citation is retracted.

The correct, stronger evidence came from reading the installed `0.3.7`
source directly: `langchain/agents/output_parsers/tools.py`'s
`parse_ai_message_to_tool_action()` —
```python
if message.tool_calls:
    tool_calls = message.tool_calls
else:
    if not message.additional_kwargs.get("tool_calls"):
        return AgentFinish(return_values={"output": message.content}, ...)
```
— confirms `ToolsAgentOutputParser` returns `AgentFinish` immediately via a
**plain return, not an exception**, the moment a turn has zero tool calls,
independent of `max_iterations`. This is why CL-044's `max_iter` increase
could not have fixed this failure mode: the failure occurs on iteration 0,
before any iteration budget is consumed. Also read
`langchain_community/chat_models/litellm.py`'s `ChatLiteLLM.bind_tools()`
directly: it accepts an optional `tool_choice` kwarg, passed straight to
LiteLLM; `core/orchestration.py` never supplies one, so whatever Vertex/
Gemini's server-side default is applies unmodified. LiteLLM's Vertex AI
docs confirm `tool_choice="required"` is the documented way to force tool
calls — but adopting it globally would prevent the agent from ever
submitting its plain-text final JSON answer (not a tool call), so it can't
cleanly replace today's fix without a larger redesign (e.g. a dedicated
"submit_answer" tool); flagged for Niteen as a possible future enhancement,
not implemented here.

Neither of `_invoke_once()`'s existing two gates — `_is_refusal()` (needs
non-empty text) and `_detect_empty_tool_loop()` (needs ≥3 steps present) —
covered zero steps with an empty final answer. Added a third gate, raising
the same `BadRequestError` already used by the other two (already in
`_FAILOVER_EXCEPTIONS`), so the *existing* failover loop in `run_agent()`
handles it — no new mechanism.

**Regression risk caught before implementation, not after:** auditing
every mocked `AgentExecutor.invoke()` return value across
`tests/test_orchestration.py` and `tests/test_orchestration_failover.py`
found two pre-existing tests (`T-ORC-C-001`, `T-ORC-N-004`) whose mocks used
`{"output": None}` with no `intermediate_steps` key — indistinguishable
from the new zero-step failure shape. Without correction, the new gate
would have made `run_agent()` attempt real failover in both tests instead
of returning the partial result they're testing for — and since an
earlier-imported test module's `load_dotenv()` populates `os.environ` with
the real `.env` by the time `test_orchestration.py` runs, `_build_model_chain()`
would have succeeded rather than raising cleanly, producing a slow, fragile,
env-coupled test outcome instead of a clean failure. Both mocks were
corrected to include one real (non-empty) intermediate step, accurately
modeling genuine multi-turn iteration exhaustion (the design intent since
`return_intermediate_steps=True` was introduced in CL-038) rather than an
unrealistic zero-step combination.

**Deviation from the Cowork-authored plan, documented:** the plan's Phase 2
asked for two additional tests that reuse `T-ORC-N-015`'s and
`T-ORC-C-011`'s bodies verbatim under new IDs, to prove no regression in
the two existing gates. Skipped the literal duplication — the *existing*
`T-ORC-N-015`/`T-ORC-C-011` already provide that proof every time the suite
runs; an exact copy under a new ID adds no additional coverage. Both were
explicitly re-run and confirmed still green with the new gate in place
(see Tests section). Net: 3 new tests instead of the plan's 4, landing at
136/136 instead of the stated 137 minimum — gate intent satisfied via the
existing tests rather than duplicates.

### Files Affected
- `core/orchestration.py` — `_invoke_once()` gained a third gate (zero `intermediate_steps` + falsy `output` → `BadRequestError`), positioned after `_detect_empty_tool_loop()` and before `_is_refusal()`; module CHANGE LOG updated
- `tests/test_orchestration.py` — added `T-ORC-N-016`/`017`, `T-ORC-C-013`; corrected `T-ORC-C-001`/`T-ORC-N-004`'s mocks to include a real intermediate step; module CHANGE LOG updated

**Confirmed untouched (explicit guardrail, verified via diff):** `main.py`, `tools/search.py`, `core/delivery.py`, `core/gateway.py`, `config/email_template.html`, `core/synthesis.py`, the lesson path (`_run_lesson_agent()` never calls `_invoke_once()` — structurally unreachable by this change).

### Rules Added/Modified
- None — bugfix only, reuses the existing `BadRequestError`/failover mechanism CL-032 and CL-038 already established

### Tests Added/Modified
- `T-ORC-N-016` — zero `intermediate_steps` + `output=None` raises `BadRequestError`
- `T-ORC-N-017` — zero `intermediate_steps` + `output=""` raises `BadRequestError` (the exact live-reproduced shape)
- `T-ORC-C-013` — zero `output` but non-empty `intermediate_steps` does NOT raise (scoping regression guard)
- Corrected `T-ORC-C-001`, `T-ORC-N-004` — mocks now include a real intermediate step, avoiding false-positive collision with the new gate
- Re-confirmed `T-ORC-N-015`, `T-ORC-C-011` (pre-existing empty-tool-loop gates) still green, satisfying the plan's regression-coverage intent without literal duplication
- 136/136 tests green (133 + 3 new)

### Dependencies
- Depends on: CL-032 (introduced the `BadRequestError`/failover-on-detection pattern), CL-038 (introduced `return_intermediate_steps=True` and `_detect_empty_tool_loop()`, the adjacent gate this CL extends), CL-044 (raised `max_iter`, ruled out as a fix for this specific failure mode)
- Blocks: None. Open question for Niteen, not blocking: whether to pursue `tool_choice="required"` + a dedicated "submit_answer" tool as a more architecturally correct future fix

### Rollback
In `core/orchestration.py`: remove the new `if not intermediate_steps and not result.get("output"):` block from `_invoke_once()` (the two existing gates and their order are unaffected). Remove `T-ORC-N-016`/`017`/`T-ORC-C-013` from `tests/test_orchestration.py`; the `T-ORC-C-001`/`T-ORC-N-004` mock corrections may stay regardless (harmless, more realistic either way).

### Owner Approval
- [ ] Approved by Niteen


## [CL-047] — 2026-06-24 — COMPLETED

**Type:** BUGFIX (multi-fix — live pipeline producing empty JIT/JIC output)
**Author:** Cowork (direct fixes, bypassing Claude Code per owner instruction)
**Task ID:** N/A
**Status:** COMPLETED

### Summary
Live runs after CL-046 still showed JIT/JIC returning empty output. Root cause
analysis confirmed the `vertex_ai/` prefix is incompatible with
`ChatLiteLLM + AgentExecutor`: LangChain overrides `streaming=False` at
invocation time, routing through `streamGenerateContent` which returns
`content=''` on every tool-call iteration. All JIT/JIC agent output was being
silently discarded.

Nine further defensive fixes were applied simultaneously by Cowork:

A. `.env` MODEL_1/2 reverted from `vertex_ai/` → `gemini/` prefix (Google AI
   Studio, uses `GEMINI_API_KEY` and `generativelanguage.googleapis.com`), which
   supports tool-calling correctly with `AgentExecutor`.
B. `ServiceUnavailableError` (HTTP 503) added to `_FAILOVER_EXCEPTIONS` — was
   crashing the pipeline on Google 503s instead of failing over to MODEL_2.
C. `output or ""` guard in `_invoke_once()` — `result.get("output")` returns
   `None` (not `""`) when `AgentExecutor` exhausts `max_iterations`.
D. `"Agent stopped due to max iterations."` literal detection in `_invoke_once()`
   — LangChain hardcodes this string as `output` when `early_stopping_method=
   "force"` hits the cap. Now raises `BadRequestError` to trigger failover
   instead of returning the literal as valid output.
E. `_strip_agent_fences()` helper — Gemini Flash wraps final JSON output in
   ` ```json ``` ` fences even in tool-calling mode. Added stripping before
   `_is_refusal()` so valid fenced JSON is not discarded.
F. `vertex_ai/` branch in `_build_llm_for_model()` with `streaming=False`
   (partial guard; harmless since the real fix is `gemini/` prefix).
G. JIT/JIC `max_iter` reduced 16→10 with explicit "max 6 searches then output
   JSON immediately" prompt instruction — prevents Flash from exhausting all
   iterations on tool calls with no synthesis budget remaining.
H. `_parse_agent_json()` in `main.py` — 3-stage JSON extraction (direct parse
   → fence strip → regex `[...]`) replacing bare `json.loads()` to tolerate
   fenced or prose-wrapped output.
I. `logger.error` when model chain is exhausted in `run_agent()`.

### Files Affected
- `.env` — MODEL_1: `vertex_ai/gemini-2.5-flash-lite` → `gemini/gemini-2.5-flash-lite`; MODEL_2: `vertex_ai/gemini-2.5-flash` → `gemini/gemini-2.5-flash`
- `core/orchestration.py` — `_FAILOVER_EXCEPTIONS`, `_strip_agent_fences()`, `_invoke_once()`, `_build_llm_for_model()`, `run_agent()` updated
- `main.py` — `_parse_agent_json()` added; `_run_jit_agent()` / `_run_jic_agent()` max_iter 16→10; prompt updated

### Rules Added/Modified
- None — no new rules; existing failover and refusal patterns extended

### Tests Added/Modified
- None at time of CL-047 — tests written in CL-048

### Dependencies
- Depends on: CL-046 (empty-output gate), CL-032 (failover pattern)
- Blocks: CL-048 (tests)

### Rollback
Revert `.env` MODEL_1/2 to `vertex_ai/` prefix (warning: will break JIT/JIC
agent output). In `core/orchestration.py`: remove `_strip_agent_fences()`,
revert `_invoke_once()` force-stop literal detection and fence-stripping,
remove `ServiceUnavailableError` from `_FAILOVER_EXCEPTIONS`. In `main.py`:
remove `_parse_agent_json()`, restore `json.loads()` calls, restore
`max_iter=16`.

### Owner Approval
- [x] Approved by Niteen (owner directed all changes)


## [CL-048] — 2026-06-24 — COMPLETED

**Type:** TEST (coverage for all CL-047 direct fixes)
**Author:** Cowork
**Task ID:** N/A
**Status:** COMPLETED

### Summary
Wrote 11 new test cases covering all CL-047 fixes that lacked test coverage.
Also updated 3 pre-existing tests (T-MAIN-C-004, T-MAIN-C-005, T-MAIN-C-013)
that were asserting `max_iter=16` after CL-047 reduced it to 10 — those tests
were correct for CL-044 state but were now stale, causing 3 failures in a
136-pass suite. Updated assertions to `max_iter=10` with updated docstrings
recording the reduction history.

Final state: **147/147 tests green**.

### Files Affected
- `tests/test_orchestration.py` — 6 new tests: T-ORC-U-014 through T-ORC-U-019
- `tests/test_main.py` — 5 new tests: T-MAIN-C-032 through T-MAIN-C-036; updated T-MAIN-C-004, T-MAIN-C-005, T-MAIN-C-013 assertions from max_iter=16 → 10

### Rules Added/Modified
- None

### Tests Added/Modified
- T-ORC-U-014: `_strip_agent_fences()` strips ` ```json ``` ` fences
- T-ORC-U-015: `_strip_agent_fences()` passes plain JSON unchanged
- T-ORC-U-016: `_strip_agent_fences()` returns `""` for `None` input
- T-ORC-U-017: `_strip_agent_fences()` handles plain ` ``` ` fences (no language tag)
- T-ORC-U-018: `ServiceUnavailableError` is in `_FAILOVER_EXCEPTIONS`
- T-ORC-N-019: `_invoke_once()` raises `BadRequestError` on force-stop literal
- T-MAIN-C-032: `_parse_agent_json()` parses plain JSON array
- T-MAIN-C-033: `_parse_agent_json()` strips ` ```json ``` ` fences and parses
- T-MAIN-C-034: `_parse_agent_json()` extracts `[...]` from prose-wrapped output
- T-MAIN-C-035: `_parse_agent_json()` returns `[]` on empty string
- T-MAIN-C-036: `_parse_agent_json()` returns `[]` on force-stop literal

### Dependencies
- Depends on: CL-047

### Rollback
Remove T-ORC-U-014 through T-ORC-N-019 from `tests/test_orchestration.py`.
Remove T-MAIN-C-032 through T-MAIN-C-036 from `tests/test_main.py`. Restore
T-MAIN-C-004, T-MAIN-C-005, T-MAIN-C-013 to assert `max_iter=16`.

### Owner Approval
- [x] Approved by Niteen (owner directed all test work)


## [CL-049] — 2026-06-24 — COMPLETED (code applied; tests pending for Claude Code)

**Type:** BUGFIX
**Author:** Cowork (direct fix during live debugging session)
**Task ID:** N/A
**Status:** CODE APPLIED — tests pending

### Summary

Extended `streaming=False` from `vertex_ai/` models only (CL-047 item D) to ALL
non-openrouter models in `_build_llm_for_model()`. Root cause confirmed via online
research against LiteLLM GitHub issues #19403 and #21041: both `gemini/` and
`vertex_ai/` prefixes route to Google's `streamGenerateContent` endpoint when
streaming is enabled. With streaming on, every tool-call iteration returns
`content=''` with `finish_reason='tool_calls'` — no exception fires, the agent
exhausts `max_iter`, and `run_agent()` returns `output=""`.

Confirmed by live run 2026-06-24 at 13:48: 6 consecutive Pydantic serializer
warnings (`Expected Message — content=''`, `Expected StreamingChoices —
finish_reason='to...'`) then `WARNING: JIT agent output was empty — returning
empty list`. Flash-Lite was 503 (failover to Flash), but Flash showed identical
behaviour because both are `gemini/` prefix with streaming on.

The `vertex_ai/` branch in `_build_llm_for_model()` was removed — the default
branch now sets `streaming=False` for all models, with `openrouter/` as the only
exception (kept at default streaming; their failure mode is handled by
`_detect_empty_tool_loop()`, and streaming=False for OpenRouter may introduce
different issues).

### Files Affected
- `core/orchestration.py` — `_build_llm_for_model()`: removed separate `vertex_ai/`
  branch with `streaming=False`; default branch now sets `streaming=False`; module
  docstring updated with CL-049 entry (v1.9.0)

### Rules Added/Modified
- None — extends existing CL-047 streaming fix to cover `gemini/` prefix

### Tests Added/Modified
- **NONE — tests not yet written. Claude Code must write them in the CL-049/050 session.**
- See `CL049_CL050_PLAN.md` for full test list.

### Dependencies
- Depends on: CL-047 (original streaming=False for vertex_ai/)
- Blocks: CL-050 (must confirm CL-049 tests pass before applying CL-050 changes)

### Rollback
In `core/orchestration.py` `_build_llm_for_model()`: restore the separate
`vertex_ai/` branch with `streaming=False`; change default branch back to no
`streaming=` argument.

### Owner Approval
- [x] Approved by Niteen (directed the fix after online research confirmed root cause)


## [CL-050] — COMPLETE — Migrate to langchain-litellm + MALFORMED_FUNCTION_CALL guard

**Type:** BUGFIX (structural) + FEATURE (guard)
**Author:** Claude Code
**Date:** 2026-06-25
**Status:** COMPLETE — 159/159 tests green

### Summary

Two changes packaged together because they both touch `core/orchestration.py`:

**CL-050A — Migrate `ChatLiteLLM` import from `langchain_community` to `langchain_litellm`:**
`langchain_community.chat_models.ChatLiteLLM` was deprecated in LangChain 0.3.24.
Official replacement: `pip install langchain-litellm` + `from langchain_litellm import ChatLiteLLM`.
Known tool-calling bugs in the community version are fixed in the dedicated package.
Confirmed via LangChain GitHub issue #31145 and PyPI page.

Dependency note: `langchain-litellm>=0.7.0` requires `litellm>=1.83.14` (newer than
our pinned `litellm==1.52.0`). The highest compatible version with our existing stack
is `langchain-litellm==0.6.4`, which installed successfully alongside `langchain==0.3.7`
and `litellm==1.52.0` (pip reports version incompatibility warnings but all 159 tests pass).
`requirements.txt` updated to pin `langchain-litellm==0.6.4`.

Note: `langchain_litellm.ChatLiteLLM` defaults `streaming=False` (unlike the old
`langchain_community` version which defaulted to `True`). This means the `openrouter/`
branch (which intentionally didn't set `streaming=False` explicitly) now also defaults
to `streaming=False`. This is acceptable — `streaming=False` is safer for tool-calling.

**CL-050B — MALFORMED_FUNCTION_CALL silent failure guard:**
Added guard in `_invoke_once()` at position 8 (after force-stop literal check, before
fence-strip): if `intermediate_steps` non-empty AND `raw_output` empty →
`raise BadRequestError("...MALFORMED_FUNCTION_CALL...")` → triggers existing failover.
Confirmed by LiteLLM issue #16651.

Guard ordering after CL-050B:
1. `executor.invoke()` → `result`
2. `if result.get("output") is None` → log R-005 warning
3. `intermediate_steps = result.get("intermediate_steps", [])`
4. `if _detect_empty_tool_loop(...)` → raise BadRequestError  [CL-038]
5. `if not intermediate_steps and not result.get("output")` → raise BadRequestError  [CL-046]
6. `raw_output = result.get("output") or ""`
7. `if raw_output.strip() == "Agent stopped due to max iterations."` → raise  [CL-047]
8. `if intermediate_steps and not raw_output` → raise BadRequestError  [CL-050B]  ← NEW
9. `stripped_output = _strip_agent_fences(raw_output)`
10. `if _is_refusal(stripped_output)` → raise BadRequestError  [CL-032/038]
11. `return result`

Side effect: T-ORC-N-004's mock (output=None + non-empty steps) now triggers CL-050B
instead of returning a partial result. Updated T-ORC-N-004 to expect BadRequestError
while still verifying the R-005 warning is logged (it fires before the guard). Updated
T-ORC-C-013 (empty-output + non-empty-steps → don't raise) to use non-empty JSON output
since CL-050B now fires in that shape — T-ORC-C-013 becomes a happy-path regression guard.

### Files Affected
- `requirements.txt` — added `langchain-litellm==0.6.4`
- `core/orchestration.py` — (A) `_build_llm_for_model()`: changed import from
  `langchain_community.chat_models` to `langchain_litellm`; (B) `_invoke_once()`:
  added MALFORMED_FUNCTION_CALL guard at position 8; (C) module docstring CL-050 entry
- `tests/test_orchestration.py` — added T-ORC-C-020/021/022 (CL-049 streaming),
  T-ORC-C-023 (langchain_litellm instance), T-ORC-N-024 (no community import),
  T-ORC-N-025/026 (MALFORMED fires on empty output), T-ORC-C-027/028 (no false-positive
  on valid output), T-ORC-N-029 (CL-046 zero-step gate still works); updated T-ORC-N-004
  and T-ORC-C-013

### Rules Added/Modified
- None — extends existing guards

### Tests Added/Modified
- T-ORC-C-020, T-ORC-C-021, T-ORC-C-022, T-ORC-C-023, T-ORC-N-024, T-ORC-N-025,
  T-ORC-N-026, T-ORC-C-027, T-ORC-C-028, T-ORC-N-029 (new)
- T-ORC-N-004, T-ORC-C-013 (updated for CL-050B behavior change)

### Dependencies
- Depends on: CL-049 (streaming=False prerequisite)

### Owner Approval
- [x] Approved by Niteen (directed implementation)


## [CL-051] — COMPLETE — Vertex AI only migration (delete GEMINI_API_KEY)

**Type:** MIGRATION
**Author:** Claude Code
**Date:** 2026-06-25
**Status:** COMPLETE — 159/159 tests green

### Summary

Full migration from Google AI Studio (`gemini/` prefix + `GEMINI_API_KEY`) to Vertex AI
only (`vertex_ai/` prefix + `GOOGLE_APPLICATION_CREDENTIALS` service-account JSON).

**Root cause context:** CL-041 originally migrated to `vertex_ai/`, but CL-047 reverted
to `gemini/` because `ChatLiteLLM` + `AgentExecutor` ignored `streaming=False` for
`vertex_ai/` models (LangChain internals override). CL-049 fixed this by applying
`streaming=False` to ALL non-openrouter models, removing the platform-specific
streaming bug. CL-050A's migration to `langchain_litellm.ChatLiteLLM` resolves the
root cause of the tool-calling issues. Together, CL-049 + CL-050 make vertex_ai/
fully viable for AgentExecutor, unblocking this migration.

### Changes

**`scripts/check_env.py`:**
- `GEMINI_API_KEY` removed from `REQUIRED_KEYS`
- `GEMINI_API_KEY` added to `OPTIONAL_KEYS` as a `gemini/` prefix fallback (DEV-I-006)
- Module docstring updated with CL-051 entry

**`.env.example`:**
- Fully rewritten to reflect Vertex AI setup as primary
- `GOOGLE_APPLICATION_CREDENTIALS` shown as primary credential
- `LITELLM_MODEL_1` = `vertex_ai/gemini-2.5-flash-lite`
- `LITELLM_MODEL_2` = `vertex_ai/gemini-2.5-flash`
- `GEMINI_API_KEY` shown as OPTIONAL comment

**`core/gateway.py`:**
- Module docstring updated with CL-051 entry
- No code changes — `vertex_ai/` branch in `_get_api_key()` was already correct (CL-041)
  returning `None` (uses ADC), and `_scrub_secrets()` already handles unset GEMINI_API_KEY
  gracefully (T-GAT-E-006 confirmed)
- `GEMINI_API_KEY` stays in `_scrub_secrets()` loop as a no-op when unset

**`tests/test_gateway.py`:**
- `REQUIRED_ENV` fixture: removed `GEMINI_API_KEY`, changed `LITELLM_MODEL_1` to
  `vertex_ai/gemini-2.5-flash-lite`, added `GOOGLE_APPLICATION_CREDENTIALS`
- T-GAT-C-001 renamed + updated: now uses `vertex_ai/gemini-2.5-flash-lite` as
  the primary model, asserts `model_used == "vertex_ai/gemini-2.5-flash-lite"`
- Added T-GAT-C-017: `_get_api_key("vertex_ai/gemini-2.5-flash-lite")` returns None
  when `GEMINI_API_KEY` is explicitly absent (confirms primary model auth path)

**`tests/test_env.py`:**
- `VALID_DEFAULTS` fixture: removed `GEMINI_API_KEY`, changed `LITELLM_MODEL_1` to
  `vertex_ai/gemini-2.5-flash-lite`
- T-ENV-N-001 updated: placeholder test now uses `TAVILY_API_KEY` instead of
  `GEMINI_API_KEY` (since GEMINI_API_KEY is no longer required)
- T-ENV-N-003 rewritten: "GEMINI_API_KEY absent → raises ValueError" flipped to
  "GEMINI_API_KEY absent → does NOT raise" (it's now optional)
- Added T-ENV-N-005: asserts `GEMINI_API_KEY` is in `OPTIONAL_KEYS` and NOT in
  `REQUIRED_KEYS` (regression guard)

**User action required:**
Update your `.env` file:
1. Change `LITELLM_MODEL_1=gemini/gemini-2.5-flash-lite` → `vertex_ai/gemini-2.5-flash-lite`
2. Change `LITELLM_MODEL_2=gemini/gemini-2.5-flash` → `vertex_ai/gemini-2.5-flash`
3. Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to a valid service-account JSON file
4. `GEMINI_API_KEY` can be removed (or left as an optional fallback)

### Files Affected
- `scripts/check_env.py` — `REQUIRED_KEYS` / `OPTIONAL_KEYS` change + docstring
- `.env.example` — rewritten for Vertex AI primary setup
- `core/gateway.py` — docstring only
- `tests/test_gateway.py` — REQUIRED_ENV fixture + T-GAT-C-001 update + T-GAT-C-017 new
- `tests/test_env.py` — VALID_DEFAULTS + T-ENV-N-001/003 updates + T-ENV-N-005 new

### Rules Added/Modified
- DEV-I-006: already covers vertex_ai/ vs gemini/ auth path distinction; no change needed

### Tests Added/Modified
- T-GAT-C-017 (new), T-ENV-N-005 (new)
- T-GAT-C-001, T-ENV-N-001, T-ENV-N-003 (updated)

### Owner Approval
- [x] Approved by Niteen ("Delete Gemini API key, use only Vertex API")

---

## [CL-053] — 2026-06-25 — COMPLETED

**Type:** BUGFIX
**Author:** Claude Code
**Task ID:** N/A (owner-requested fix: blank authors + missing paper links in delivered emails)
**Status:** COMPLETED

### Summary
Two visual defects in the delivered email's section 3C (Key Research Papers). **Root cause A — blank authors:** the lesson prompt asked for `authors` as a Python list, but the Jinja2 template rendered `{{ paper.authors }}` directly — a list displays as `['Lewis P.', 'Perez E.']` repr, and an empty list or empty string renders as a completely blank cell with no fallback. **Root cause B — no paper links:** the `section_3c` prompt schema had no `url` field, so the LLM never emitted URLs despite the grounding block already injecting real arXiv URLs as context and even explicitly instructing "include their real arXiv URL" for supplementary papers. JIT/JIC news sections already had clickable `source` links via `<a href="{{ item.url }}">` — papers had no equivalent. Fix: prompt schema adds `url` to `section_3c` items and changes `authors` to a comma-separated string with an explicit `'Authors unlisted'` failover phrase. `email_template.html` renders paper title as a clickable `<a>` link when `url` is present (same style as JIT/JIC), and the authors cell handles string/list/empty with `Authors unlisted` fallback.

### Files Affected
- `main.py` — `section_3c` prompt schema: adds `url` field with arXiv URL example, changes `authors` to comma-separated string, adds `'Authors unlisted'` failover instruction; module docstring updated (v1.10.0 CL-053 entry)
- `config/email_template.html` — section 3C paper table: paper title cell now renders as `<a href="...">` when `url` present, falls back to plain `<span>` when absent; authors cell handles string/list/empty with `Authors unlisted` fallback via Jinja2 `is string` test + `| join(", ")` filter
- `tests/test_synthesis.py` — added T-SYN-C-004 (paper title link renders), T-SYN-C-005 (list authors join), T-SYN-N-004 (empty authors fallback); `minimal_context` fixture adds `url` to section_3c paper; `_valid_lesson()` adds `url` to paper entries; module docstring updated (v1.2.0 CL-053 entry)
- `tests/test_main.py` — added T-MAIN-C-038 (lesson prompt section_3c schema contains `url` field, arXiv example, `Authors unlisted` failover); module docstring updated (v1.10.0 CL-053 entry)

### Rules Added/Modified
None — uses existing R-003 (HTML validation retry), R-005 (max iterations). Template failover follows same "graceful degradation" pattern established in CL-035 for `_LESSON_FALLBACK`.

### Tests Added/Modified
- T-SYN-C-004 — NEW: paper title renders as clickable link when url present
- T-SYN-C-005 — NEW: list authors joined with ", " in rendered HTML
- T-SYN-N-004 — NEW: empty string/list authors shows "Authors unlisted" fallback
- T-MAIN-C-038 — NEW: lesson prompt section_3c schema has url field + Authors unlisted

### Dependencies
- Depends on: CL-031 (lesson prompt rewrite establishing section_3c peer-reviewed-papers-only rule), CL-037 (lesson agent grounding block that injects real arXiv URLs as context)

### Rollback
Revert `config/email_template.html` section 3C tbody to plain `{{ paper.title }}` / `{{ paper.authors }}` and revert `main.py` `section_3c` prompt line back to `{title,authors,year,contribution}` with `authors must be a list`. Remove T-SYN-C-004/C-005/N-004 and T-MAIN-C-038.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-054] — 2026-06-25 — COMPLETED

**Type:** BUGFIX
**Author:** Claude Code
**Task ID:** N/A (owner-requested dashboard-only fix)
**Status:** COMPLETED

### Summary
Panel 1 (Daily Run Metrics) showed `NULL` in the `lesson_topic` column for any date where the newsletter was a JIC run (no `LESSON`-typed row). Root cause: `_get_recent_runs()` in `frontend/app.py` used `MAX(CASE WHEN hl.run_type = 'LESSON' THEN hl.topic END)` — a JIC run writes a `run_type='JIC'` row whose `topic` field carries the lesson subject, so restricting to `'LESSON'` left JIC dates with a NULL. Fix: widened the CASE expression to `run_type IN ('JIC', 'LESSON')`. A new idempotent `scripts/seed_demo_exceptions.py` helper inserts 3 labelled `[DEMO]` rows into `system_exceptions` for Panel 4 screenshots. New regression test T-DASH-N-004 guards the fix. No newsletter-generation code was touched.

### Files Affected
- `frontend/app.py` — `_get_recent_runs()` CASE expression: `= 'LESSON'` → `IN ('JIC', 'LESSON')`; module docstring v1.3.0
- `scripts/seed_demo_exceptions.py` — NEW: inserts 3 `[DEMO]` rows into `system_exceptions`; idempotent
- `tests/test_dashboard.py` — added T-DASH-N-004; module docstring v1.3.0

### Rules Added/Modified
None — change is entirely within the dashboard read path; append-only ledger (R-004) and SELECT-only console (ZT-002) unchanged.

### Tests Added/Modified
- T-DASH-N-004 (new): asserts `lesson_topic` is non-NULL when only a JIC row exists for a date

### Dependencies
- Depends on: TC-008 (dashboard initial implementation), CL-025 (Panel 5 bare-ternary fix)

### Rollback
Revert `frontend/app.py` CASE expression back to `run_type = 'LESSON'`. Remove `scripts/seed_demo_exceptions.py`. Remove T-DASH-N-004 from `tests/test_dashboard.py`.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-055] — 2026-06-26 — COMPLETED

**Type:** BUGFIX
**Author:** Claude Code
**Task ID:** N/A (owner-approved Vertex SDK workaround for JIT/JIC tool-calling)
**Status:** COMPLETED

### Summary
JIT/JIC agents returned empty output on `vertex_ai/` models despite HTTP 200 responses. Root cause: LangChain `AgentExecutor` + `ChatLiteLLM` still routed Google models through `streamGenerateContent` at invoke time even with `streaming=False` on the constructor (CL-047/049) — every tool-call iteration returned `content=''`, exhausting `max_iter` silently. The lesson agent was unaffected because it uses `litellm.completion(stream=False)` directly via `core.gateway.llm_call()`. Fix: new `core/tool_agent.py` implements an SDK-direct tool loop with explicit `stream=False` for `vertex_ai/` and `gemini/` models; `orchestration._invoke_once()` dispatches Google models to this path while OpenRouter/Mistral fallbacks keep `AgentExecutor`. `_coerce_tool_arg()` moved to `core/tool_args.py` for shared protobuf arg coercion. Post-invoke guards (CL-038/046/050B) extracted to `_apply_invoke_guards()` and reused on both paths. `.env` MODEL_1/2 reverted from emergency `gemini/` back to `vertex_ai/`.

### Files Affected
- `core/tool_args.py` — NEW: `_coerce_tool_arg()` moved from `main.py`
- `core/tool_agent.py` — NEW: `run_litellm_tool_loop()`, OpenAI tool schemas, `_execute_tool_call()`
- `core/orchestration.py` — `_invoke_once()` dispatches by provider; `_apply_invoke_guards()` extracted; `run_agent()` passes `current_model`
- `main.py` — imports `_coerce_tool_arg` from `core.tool_args` (pipeline flow unchanged)
- `tests/test_tool_agent.py` — NEW: T-TOOL-C-001/002, T-TOOL-N-001
- `tests/test_orchestration.py` — T-ORC-C-030/031, T-ORC-N-030/031
- `tests/test_orchestration_failover.py` — failover mocks target SDK path for `gemini/` chain members
- `tests/test_integration.py` — T-INT-I-002 (SDK path E2E HTML)
- `tests/test_main.py` — import `_coerce_tool_arg` from `core.tool_args`
- `RULES.md` — DEV-I-005 amended (CL-055 SDK tool-loop exception inside `run_agent()`)
- `TEST_REGISTRY.md` — v3.22.0; 8 new test rows
- `HANDOVER.md` — CL-055 session entry
- `AUDIT_LOG.md` — AL-005 appended
- `.env.example` — CL-055 note on vertex_ai/ requirement
- `.env` — MODEL_1/2 reverted to `vertex_ai/` (not committed — gitignored)

### Rules Added/Modified
- DEV-I-005 — Amended: `run_agent()` may call SDK-direct `litellm.completion` tool loop for `vertex_ai/`/`gemini/` inside `_invoke_once()` (CL-055 exception, same rationale as CL-037 lesson bypass)

### Tests Added/Modified
- T-TOOL-C-001 — NEW: `litellm.completion` called with `stream=False` and `tools=`
- T-TOOL-C-002 — NEW: tool execution then final JSON returned
- T-TOOL-N-001 — NEW: Vertex protobuf arg coercion in SDK path
- T-ORC-C-030 — NEW: `vertex_ai/` skips AgentExecutor
- T-ORC-C-031 — NEW: `openrouter/` keeps AgentExecutor
- T-ORC-N-030 — NEW: SDK path empty tool loop → failover
- T-ORC-N-031 — NEW: SDK path zero-step empty output → failover
- T-INT-I-002 — NEW: mocked SDK E2E renders JIT/JIC in HTML
- T-ORC-N-002 — updated: mixed SDK + AgentExecutor chain exhaustion mock

### Dependencies
- Depends on: CL-037 (lesson SDK-direct precedent), CL-047/049 (streaming bug diagnosis), CL-051 (vertex_ai/ primary models), CL-043 (`_coerce_tool_arg` protobuf defense)

### Rollback
Remove `core/tool_agent.py` and `core/tool_args.py`. Restore `_coerce_tool_arg()` inline in `main.py`. Revert `orchestration._invoke_once()` to AgentExecutor-only path. Remove dispatch + `_apply_invoke_guards` extraction (inline guards back into single function). Revert `.env` MODEL_1/2 to `gemini/` if emergency fallback needed without Vertex.

### Owner Approval
- [x] Approved by Niteen (Vertex-only JIT/JIC workaround plan)

---

## [CL-056] — 2026-06-26 — COMPLETED

**Type:** FEATURE
**Author:** Claude Code
**Task ID:** N/A (JIT/JIC gap-fill when below minimum 5 or cooldown blocks topics)
**Status:** COMPLETED

### Summary
Live runs often returned thin or empty JIT/JIC sections when the 7-day search window and R-001 cooldown filtered out too many candidates. Added `search_broad()` (14-day Tavily window + trusted domains from `config/search_sources.json`), a `search_broad` agent tool for JIT/JIC, and deterministic `_gap_fill_items()` that runs after the primary agent pass when count < 5. `validate_jit_output()`/`validate_jic_output()` enforce minimum 5 items plus required keys; `run_daily_pipeline()` substitutes `_JIT_FALLBACK`/`_JIC_FALLBACK` (5 placeholder rows each) on validation failure and still sends email. `mark_topic_done()` is gated on JIT + JIC + lesson all passing (no fallback). JIT/JIC prompts now request "at least 5 and up to 10" items and instruct agents to use `search_broad` when cooldown blocks topics. R-001 amended with R-001-GAP: cooldown is waived only inside gap-fill (ledger writes unchanged).

### Files Affected
- `config/search_sources.json` — NEW: trusted JIT/JIC domains (TechCrunch, VentureBeat, Ars, Wired, HF, Google AI, Rundown, Ben's Bites, arXiv, MIT) + gap-fill query templates
- `tools/search.py` — `search_broad()`, `load_search_sources()`, `domain_from_url()`; `_tavily_search()` accepts `days` and `include_domains`
- `core/synthesis.py` — `JIT_JIC_MIN_ITEMS`, `validate_jit_output()`, `validate_jic_output()` with required-key checks
- `main.py` — `_JIT_FALLBACK`/`_JIC_FALLBACK`; `search_broad` tool; `_gap_fill_items()`, `_ensure_section_minimum()`; pipeline validation + pointer gating; prompt updates
- `core/tool_agent.py` — `search_broad` in tool arg maps
- `tests/conftest.py` — autouse `search_broad` stub (offline suite)
- `tests/test_search.py` — T-SRC-C-004/005
- `tests/test_synthesis.py` — T-SYN-N-005/006/007, T-SYN-C-006/007
- `tests/test_main.py` — T-MAIN-C-039–044; T-MAIN-C-010/011 updated for minimum-5 wording
- `tests/test_integration.py` — fixtures ≥5 items; T-INT-I-003
- `RULES.md` — R-001-GAP exception documented in R-001 row
- `TEST_REGISTRY.md` — v3.23.0; 15 new test rows
- `HANDOVER.md` — CL-056 session entry
- `AUDIT_LOG.md` — AL-006 appended

### Rules Added/Modified
- R-001 — Amended with R-001-GAP: gap-fill may include cooldown topics when primary pass < 5 items

### Tests Added/Modified
- T-SRC-C-004, T-SRC-C-005 — NEW: broad search + config loader
- T-SYN-N-005, T-SYN-N-006, T-SYN-N-007, T-SYN-C-006, T-SYN-C-007 — NEW: JIT/JIC minimum + key validation
- T-MAIN-C-039–044 — NEW: tool wiring, prompts, gap-fill, fallbacks, pointer gating
- T-INT-I-003 — NEW: JIT fallback E2E skips pointer advance
- T-INT-I-001, T-INT-I-002 — fixtures expanded to ≥5 JIT/JIC items
- T-MAIN-C-010, T-MAIN-C-011 — updated: "at least 5 and up to 10" wording

### Dependencies
- Depends on: CL-029/030 (search recency + item counts), CL-031 (validate_lesson_output pattern), CL-043 (date operator strip)

### Rollback
Remove `config/search_sources.json`. Revert `search_broad()` and gap-fill helpers from `tools/search.py` and `main.py`. Remove `validate_jit_output()`/`validate_jic_output()` from `core/synthesis.py`. Revert R-001 row. Remove `search_broad` from `_tools()` and `core/tool_agent.py` maps.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-057] — 2026-06-26 — COMPLETED

**Type:** CONFIG
**Author:** Claude Code
**Task ID:** N/A (owner-approved topic pool expansion — frameworks and training stack)
**Status:** COMPLETED

### Summary
Appended 12 owner-approved JIC lesson topics to `config/topic_pool.json` covering vector retrieval (FAISS, Pinecone), agent/orchestration frameworks (LangChain, CrewAI, LangGraph, Haystack), observability (LangSmith), RAG tooling (LlamaIndex), model efficiency (Knowledge Distillation, Model Quantization, SFT, PEFT). Pool grew 31→43 topics. Pointer left unchanged at 22.

### Files Affected
- `config/topic_pool.json` — 12 new topics appended (31→43 total); pointer unchanged at 22
- `CHANGELOG.md` — CL-057 entry
- `HANDOVER.md` — CL-057 session note

### Rules Added/Modified
- None — config-only change, no pipeline behavior change

### Tests Added/Modified
- None — existing suite re-run to confirm no regressions

### Dependencies
- Depends on: CL-030 (prior topic pool expansion pattern)

### Rollback
Remove the 12 appended topic strings from `config/topic_pool.json` (indices 31–42). Restore pool size to 31 topics.

### Owner Approval
- [x] Approved by Niteen (12 proposed framework/training topics)

---

## [CL-058] — 2026-06-26 — COMPLETED

**Type:** CONFIG
**Author:** Claude Code
**Task ID:** N/A (owner-approved topic pool expansion — AI PM curriculum)
**Status:** COMPLETED

### Summary
Appended 11 owner-approved JIC lesson topics to `config/topic_pool.json` covering AI product management: LLM cost modeling, production guardrails, feature A/B testing, vendor selection, incident response, human-in-the-loop design, roadmap prioritization, data flywheel, stakeholder communication, latency/UX tradeoffs, and MCP product strategy. Pool grew 43→54 topics. Pointer left unchanged at 22.

### Files Affected
- `config/topic_pool.json` — 11 new topics appended (43→54 total); pointer unchanged at 22
- `CHANGELOG.md` — CL-058 entry
- `HANDOVER.md` — CL-058 session note
- `AUDIT_LOG.md` — AL-007 appended

### Rules Added/Modified
- None — config-only change, no pipeline behavior change

### Tests Added/Modified
- None — existing suite re-run to confirm no regressions

### Dependencies
- Depends on: CL-057 (prior topic pool expansion pattern)

### Rollback
Remove the 11 appended topic strings from `config/topic_pool.json` (indices 43–53). Restore pool size to 43 topics.

### Owner Approval
- [x] Approved by Niteen (10 AI PM Part 2 topics + optional MCP Product Strategy)

---

## [CL-059] — 2026-06-27 — COMPLETED

**Type:** BUGFIX
**Author:** Claude Code
**Task ID:** N/A (June 27 JIC failure — Nemotron title/url/date schema drift; gap-fill skipped at len==5)
**Status:** COMPLETED

### Summary
OpenRouter Nemotron returned 5 JIC items using `title`/`url`/`date` instead of the required `topic`/`source`/`url`/`date`/`core_insight` keys. Gap-fill was skipped because `len(items)==5`, so validation failed silently and `_JIC_FALLBACK` was substituted. Added `core/output_normalize.py` to deterministically map provider field aliases (title→topic, summary→core_insight/why_it_matters, derive source from URL) before validation. Gap-fill now runs when `validate_*` fails on count or schema, not only when count < 5. Orchestration raises `BadRequestError` for failover when ≥5 parsed rows normalize to zero valid items. OpenRouter 429 gets one brief retry via `gateway._litellm_completion()`. JIT/JIC prompts hardened with explicit SCHEMA key names. SDK tool loop strips fences and detects MALFORMED_FUNCTION_CALL empty turns.

### Files Affected
- `core/output_normalize.py` — NEW: `_normalize_jit_item()`, `_normalize_jic_item()`, `normalize_agent_json_array()`, `parse_and_normalize_agent_output()`
- `main.py` — normalization after parse; gap-fill on validation failure; SCHEMA prompt hardening
- `core/orchestration.py` — `_check_schema_invalid_output()` guard (≥5 unrecoverable rows)
- `core/gateway.py` — `_litellm_completion()` with OpenRouter 429 retry
- `core/tool_agent.py` — uses `_litellm_completion`; fence strip; MALFORMED_FUNCTION_CALL guard
- `tests/test_output_normalize.py` — NEW: T-MAIN-C-045/046/047/048, T-MAIN-N-035, T-NORM-C-001, T-NORM-N-001
- `tests/test_main.py` — T-MAIN-C-049/050
- `tests/test_orchestration.py` — T-ORC-N-032, T-ORC-C-032
- `tests/test_gateway.py` — T-GAT-C-018
- `tests/test_tool_agent.py` — patch target updated to `_litellm_completion`
- `RULES.md` — R-007 output normalization invariant
- `TEST_REGISTRY.md` — v3.24.0; 12 new test rows
- `HANDOVER.md` — CL-059 session entry
- `AUDIT_LOG.md` — AL-008 appended

### Rules Added/Modified
- R-007 — NEW: all JIT/JIC LLM JSON arrays pass through `core/output_normalize.py` before validation

### Tests Added/Modified
- T-MAIN-C-045 through T-MAIN-C-050, T-MAIN-N-035 — normalization, Nemotron replay, gap-fill schema failure, prompt hardening
- T-NORM-C-001, T-NORM-N-001 — dedupe and drop invalid rows
- T-ORC-N-032, T-ORC-C-032 — schema-invalid failover guard
- T-GAT-C-018 — OpenRouter 429 retry
- T-TOOL-C-001/002 — updated mock path for `_litellm_completion`

### Dependencies
- Depends on: CL-056 (validate_jit/jic_output, gap-fill), CL-055 (SDK tool loop), provider docs research (LiteLLM, Vertex, OpenRouter, Mistral)

### Rollback
Remove `core/output_normalize.py`. Revert normalization imports and gap-fill validation logic in `main.py`. Remove `_check_schema_invalid_output()` from `orchestration.py`. Revert `_litellm_completion()` in `gateway.py` to direct `litellm.completion()`. Revert tool_agent MALFORMED guard and fence strip.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-059b] — 2026-06-27 — COMPLETED

**Type:** BUGFIX
**Author:** Claude Code
**Task ID:** N/A (June 27 live run — JIC gap-fill added 0 items; fallback substituted)
**Status:** COMPLETED

### Summary
CL-059 live run returned 4 valid JIC items from the agent; gap-fill added 0 and `_JIC_FALLBACK` was substituted while JIT gap-fill worked (+5). Root cause: `search_broad()` used `topic="news"` for both sections. Tavily's news topic returns only ~2 duplicate OpenAI security posts across all JIC queries on research domains (arxiv, alignment docs). When the agent already held those URLs, URL dedup left gap-fill with nothing to add. Fix: JIC `search_broad()` now uses `topic="general"`, retries without `include_domains` when sparse, falls back to DuckDuckGo on empty Tavily results, requests `n=10`, expands JIC gap-fill query templates, drops redundant `site:` prefixes, and logs each query attempt at INFO.

### Files Affected
- `tools/search.py` — section-specific Tavily topic; sparse JIC retry; empty-result DDG fallback
- `main.py` — expanded gap-fill queries; per-query INFO logging; `n=10`
- `config/search_sources.json` — three additional JIC gap-fill query templates
- `tests/test_search.py` — T-SRC-C-006
- `tests/test_main.py` — T-MAIN-C-051
- `TEST_REGISTRY.md` — v3.24.1; 2 new test rows

### Rules Added/Modified
- None

### Tests Added/Modified
- T-SRC-C-006 — JIC search_broad uses topic=general
- T-MAIN-C-051 — JIC gap-fill from 4 valid agent items

### Dependencies
- Depends on: CL-056 (search_broad, gap-fill), CL-059 (validation-triggered gap-fill)

### Rollback
Revert `search_broad()` topic logic and sparse retry in `tools/search.py`. Restore prior `_gap_fill_items()` query construction in `main.py`. Revert JIC query templates in `config/search_sources.json`.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-060] — 2026-07-28 — COMPLETED

**Type:** BUGFIX
**Author:** Claude Code
**Task ID:** TC-008
**Status:** COMPLETED

### Summary
Panel 1 (Run Metrics) showed misleading jit_count=0, jic_count=1 (ledger row counts, not newsletter items), model_used=None, and tokens_used=0 because gateway_telemetry_logs is empty on the live path and token data lives in logs/token_usage.json. Dashboard now shows em-dash for untracked JIT/JIC item counts, enriches model/tokens from telemetry DB then token_usage.json, shortens model names and topics for display, and collapses consecutive retry rows for the same lesson topic.

### Files Affected
- `frontend/app.py` — rewritten `_get_recent_runs()` enrichment and display formatting
- `tests/test_dashboard.py` — updated T-DASH-C-001; added T-DASH-C-002, T-DASH-C-003

### Tests Added/Modified
- T-DASH-C-001 — None jit/jic counts; telemetry model/tokens
- T-DASH-C-002 — token_usage.json fallback
- T-DASH-C-003 — retry-row collapse

### Dependencies
- None

### Rollback
Revert `frontend/app.py` Panel 1 helpers and restore prior COUNT-based SQL.

### Owner Approval
- [ ] Approved by Niteen

---

## [CL-061] — 2026-11-01 — COMPLETED

**Type:** MAINTENANCE (dependency upgrade)
**Author:** Claude (Cowork session, implemented directly with owner approval)
**Status:** COMPLETED

### Summary
`requirements.txt` was not installable (litellm 1.52.0 removed from PyPI; langchain 0.3.7 vs langchain-litellm 0.6.4 conflict). LiteLLM 1.52 built the wrong URL for Vertex's `global` endpoint, causing 404 on every Gemini 3/4 call (API probe, logs/api_probe_current.json). Upgraded to a verified-compatible set.

### Files Affected
- `requirements.txt` — litellm 1.106.6, langchain 0.3.30, langchain-core 0.3.86, langchain-community 0.3.31, langchain-litellm 0.3.5, langsmith 0.14.16, tavily-python 0.8.5, ddgs 9.16.1 (replaces duckduckgo-search), mcp 2.3.0, jinja2 3.1.6
- `pytest.ini` — testpaths = tests

### Rollback
Restore previous requirements.txt (note: it does not install).

### Owner Approval
- [x] Approved by Niteen (2026-11-01, "all good to go")

---

## [CL-062] — 2026-11-01 — COMPLETED

**Type:** FEATURE (structural, GOV-X-001 approved as decision D3)
**Status:** COMPLETED

### Summary
Single source registry and editable prompt files. Sources, windows, caps and query plans now live in `config/source_registry.json`; prompts in `config/prompts/*.md`; runtime settings in `.env` read by `core/settings.py`.

### Files Affected
- NEW `config/source_registry.json` (tiers T1-T5, J1-J4, blocked list, section rules: JIT 7 days, JIC 14 days, lesson grounding)
- NEW `config/prompts/` jit_research, jit_editor, jic_research, jic_editor, lesson, lesson_repair
- NEW `core/settings.py`

### Tests Added
T-SET-C-001..005, T-SET-N-001

### Owner Approval
- [x] Approved by Niteen (decisions D1, D3, D11)

---

## [CL-063] — 2026-11-01 — COMPLETED

**Type:** FEATURE + BUGFIX
**Status:** COMPLETED

### Summary
Gemini 4 Argon primary with Gemini 3.8 Flash fallback (D12, D14). `vertex_location=global`, `reasoning_effort=medium` (D13), 180 s timeout, JSON-schema structured output, classified errors per Google guidance (retry 429/5xx/timeout max 2x with backoff; fail fast on 400/401/403/404), network wait (laptop wake-up, Jul 7/13 misses), finish_reason checks (length, content filter, empty), per-call telemetry, daily cost guard. Tool loop now sends the model's full message back (thought signature; probe showed doubled reasoning tokens and a 163 s call without it). SendGrid retries only 429/5xx/network.

### Files Affected
- `core/gateway.py` (call_model, call_with_fallback, classify_error, wait_for_network; llm_call routed through policy)
- `core/tool_agent.py` (_message_for_history; call_model)
- `core/orchestration.py` (ModelCallError in failover set)
- `core/delivery.py` (_is_retryable)
- `.env.example`, `scripts/check_env.py` (EXA_API_KEY optional)

### Tests Added / Modified
T-GAT-C-020..025, T-GAT-N-020..024, T-GAT-S-020, T-TOOL-C-010, T-DEL-N-010; T-GAT-C-001, T-GAT-E-001, T-GAT-E-003, T-TOOL-C-001/002 updated

### Owner Approval
- [x] Approved by Niteen (decisions D12-D14)

---

## [CL-064] — 2026-11-01 — COMPLETED

**Type:** FEATURE
**Status:** COMPLETED

### Summary
Search provider chain Tavily -> Exa -> DuckDuckGo (D4; no extra Tavily accounts, Tavily ToS s.3.1/3.2) with registry allowlists, enforced windows and monthly usage counters (switch at 90%). Embedding de-dup with `gemini-embedding-001` (768 dims), cosine threshold 0.70 (D10, D15), Jaccard fallback, `news_ledger` memory for cross-day repeats (fixes R-001 never applying to news). Paper verification and citation counts via OpenAlex; unverified papers dropped.

### Files Affected
- `tools/search.py` (rewritten), NEW `core/dedupe.py`, NEW `core/citations.py`, `database/schema.sql` (news_ledger)

### Tests Added / Modified
T-DED-C-001..005, T-DED-E-001, T-DED-N-001, T-CIT-C-001..003, T-CIT-N-001; T-SRC-C-004/006 rewritten; T-SRC-C-001, T-SRC-E-001 updated

### Owner Approval
- [x] Approved by Niteen (decisions D4, D9, D10, D15)

---

## [CL-065] — 2026-11-01 — COMPLETED

**Type:** FEATURE (JIT/JIC v2, lesson v2, template v2)
**Status:** COMPLETED

### Summary
JIT/JIC: ReAct research agent (search tool, max 6 searches) + structured editor call that may only select captured candidates (no invented URLs) + code checks (caps per category/bucket, media cap, window, de-dup, metrics). Quiet days send fewer items, never padding (D9). Lesson v2 fixed slots (TL;DR, 3A, 3C max 5 verified papers with stars, 3D uses + PM guide, 3E one line, 3H, 3I); 3B/3F/3G removed (D6, D8); automatic completeness from the topic subtitle; one targeted repair; quality score. 88-topic curriculum (approved 2026-11-01). New email template with quiet-day notes and system status footer.

### Files Affected
- NEW `core/news.py`, NEW `core/lesson.py`, `core/synthesis.py`, `config/email_template.html`, `config/topic_pool.json`
- `main.py` rewritten (v1 archived as `docs/history/main_v1_CL060.py`)

### Tests Added / Modified / Retired
Added T-NEWS-C-001..005, T-NEWS-E-001, T-NEWS-N-001, T-LES-C-001..004, T-LES-N-001/002, T-LES-E-001, T-INT-I-101..106. Rewritten T-SYN-C-001/002/004/005, T-FMT-C-001, T-SYN-N-004. Retired: 55 T-MAIN-* (main.py v1 internals), T-INT-I-001..003, T-MAIN-N-035 (archived under docs/history/).

### Owner Approval
- [x] Approved by Niteen (decisions D2, D5-D9, D11; topic list approved)

---

## [CL-066] — 2026-11-01 — COMPLETED

**Type:** FEATURE (observability)
**Status:** COMPLETED

### Summary
Per-run folder `logs/runs/<date>/<time>-<mode>/` with prompts, searches, raw and final outputs, de-dup decisions, quality, `newsletter.html` (saved before send) and send result. New tables `run_log`, `llm_calls`, `news_ledger`, `run_errors` (append-only triggers). Run modes `--dry-run`, `--resend YYYY-MM-DD`. Sections independent; pointer advances on lesson success; a lesson that fails twice is skipped; ledgers written only after a successful send. Dashboard: Panel 1 from run_log with cost today / month to date; new Panel 7 Run Explorer; new SQL presets; Test Send requires confirmation.

### Files Affected
- NEW `core/run_logger.py`, `database/schema.sql`, `main.py`, `frontend/app.py`, `tests/conftest.py`

### Tests Added
T-LOG-C-001/002, T-LOG-S-001, T-LOG-E-001, T-DASH-C-010/011, T-INT-I-101..106

### Owner Approval
- [x] Approved by Niteen (LOGGING_DESIGN decisions 1-4)

---

## [CL-067] — 2026-11-01 — COMPLETED

**Type:** BUGFIX (Python 3.14 compatibility)
**Status:** COMPLETED

### Summary
First go-live check on the Mac (Python 3.14.5) stopped at the test gate: `langchain.agents` (LangChain 0.3 AgentExecutor) fails to import on Python 3.14 (pydantic forward-ref evaluation: "Unable to evaluate type annotation 'Optional[dict[str, Any]]'"). Reproduced on Python 3.14.6 in a clean environment. The v2 pipeline never uses AgentExecutor (Vertex models use the SDK tool loop), so the legacy import is now guarded and `Tool` is imported from `langchain_core.tools`.

### Files Affected
- `core/orchestration.py` (guarded import; clear error if the legacy path is ever used)
- `core/news.py`, `tests/test_tool_agent.py` (`langchain_core.tools.Tool`)

### Tests
209/209 PASSING on Python 3.13 and Python 3.14.6.

### Owner Approval
- [x] Covered by go-live approval (2026-11-01)

---

## [CL-068] — 2026-11-01 — COMPLETED

**Type:** TEST UPDATE
**Status:** COMPLETED

### Summary
T-GAT-N-010 still asserted the June model (`gemini-2.5-flash-lite`) in `.env`, so the go-live test gate failed once `.env` moved to Argon. The test now asserts the approved chain: MODEL_1 `vertex_ai/gemini-4-argon` (D12), MODEL_2 `vertex_ai/gemini-3.8-flash` (D14).

### Files Affected
- `tests/test_gateway.py`, `TEST_REGISTRY.md`

### Tests
209/209 PASSING (Python 3.14).

### Owner Approval
- [x] Covered by go-live approval (2026-11-01)


---

## [CL-069] — 2026-11-01 — COMPLETED

**Type:** BUGFIX
**Status:** COMPLETED

### Summary
Dry run 2026-11-01: 16 Tavily searches, 0 results kept, Exa served everything. `scripts/tavily_diag.py` (owner-run) confirmed: JIT (topic=news) 15/15 results dropped because the date could not be parsed; JIC (topic=general) 8/8 had no `published_date` (Tavily dates only `news` unless `include_published_date=true`); with dates on, 6/7 JIC results were outside the path-scoped allowlist. Not a ReAct problem.

### Changes
- `include_published_date=True` on every Tavily call; `normalize_date()` reads ISO, RFC-2822 and long dates (Tavily and Exa).
- Per-provider raw/kept/drop-reason counts in `searches.jsonl` (R-015).
- Exa tops up when Tavily keeps fewer than max(3, n/2) results.

### Files Affected
`tools/search.py`, `scripts/tavily_diag.py` (new), `tests/test_search.py`

### Tests
T-SRC-C-010..013 PASSING.

### Owner Approval
- [x] Approved 2026-11-01 ("sound nice to make changes")

---

## [CL-070] — 2026-11-01 — COMPLETED

**Type:** FEATURE (replaces D15 single threshold)
**Status:** COMPLETED

### Summary
Dry run: threshold 0.70 merged distinct stories (Genie 4 into Gemini 4 Carbon 0.791; speculative decoding into linear attention 0.738), cutting JIC from 10 to 3. Research (Newscatcher dedup vs clustering, NewsBlur, SemEval-2022 Task 8, inverted pyramid, Gemini embedding task types) led to a three-verdict design: DUPLICATE / OVERLAP / UNIQUE (R-013).

### Changes
- Embeddings use `task_type=SEMANTIC_SIMILARITY` (LiteLLM default was RETRIEVAL_QUERY).
- Similarity text = headline + lead paragraph (first 2 sentences).
- Editor writes a story fingerprint (actors, object, keywords, key_number); event_type = category/bucket.
- Rules: duplicate 0.92 / overlap 0.85 + fingerprint rules; parent = best source tier; related links; "Update" for follow-ups with a new development; follow-ups without news dropped.
- Editor prompts carry the approved examples (E1-E8 family).
- `news_ledger.fingerprint` column (auto-migrated on old databases).
- Settings: DEDUPE_OVERLAP_THRESHOLD=0.85, DEDUPE_DUPLICATE_THRESHOLD=0.92 (DEDUPE_THRESHOLD retired).
- Template shows "related" links and "Update" flag.

### Files Affected
`core/dedupe.py`, `core/news.py`, `core/settings.py`, `config/prompts/jit_editor.md`, `config/prompts/jic_editor.md`, `config/email_template.html`, `database/schema.sql`, `main.py`, `.env.example`, `tests/test_dedupe.py` (rewritten), `tests/test_news.py`, `tests/test_settings.py`

### Tests
T-DED-G-001 (golden set), T-DED-C-001..010, T-NEWS-C-010, T-SET-C-001 PASSING.

### Owner Approval
- [x] Approved 2026-11-01

---

## [CL-071] — 2026-11-01 — COMPLETED

**Type:** FEATURE
**Status:** COMPLETED

### Summary
Dry run: 3 of 4 lesson papers had 0-3 citations. Research on how researchers, bibliometrics and practitioners judge papers led to a credibility score (R-014).

### Changes
- OpenAlex fields: citation percentile, top 1%/10%, venue and type, open access, institutions, abstract, retracted.
- PaperScore = 0.30 relevance + 0.25 impact + 0.15 venue + 0.15 recency + 0.10 openness + 0.05 authority; gates and selection rules per R-014.
- OpenAlex shortlist on the topic's short title goes into the lesson prompt; grounding searches use the short title.
- Scores, rejections and first-draft failures saved to `lesson_quality.json`; `paper_shortlist.json` saved; "Top 1%/10%" badge in 3C.

### Files Affected
`core/citations.py`, `core/lesson.py`, `config/source_registry.json`, `config/email_template.html`, `tests/test_citations.py`, `tests/test_lesson.py`, `tests/conftest.py`

### Tests
T-CIT-C-010..015, T-LES-C-020 PASSING. Full suite 237/237 on Python 3.14.

### Owner Approval
- [x] Approved 2026-11-01

---

## [CL-072] — 2026-11-01 — COMPLETED

**Type:** BUGFIX + PROCESS
**Status:** COMPLETED

### Summary
Mac test gate failed on T-SRC-C-011: the test built a UTC timestamp and compared it with the local date (Mac is UTC-6; UTC had already rolled to Nov 2). Root-cause sweep found a hidden defect in the same class: `RunContext(runs_dir=RUNS_DIR)` bound the folder at import time, so the tests' isolation patch never applied and every test run wrote fake run folders into the real `logs/runs` (13 on the Mac, shown in the dashboard Run Explorer).

### Changes
- `run_logger`: runs folder resolved at call time.
- `normalize_date`: timezone-aware dates converted to the local calendar date (one clock everywhere).
- Test write guard (conftest, session scope): the suite fails if any file under `logs/`, `config/` or `database/` changes (runner logs `logs/*.log` excluded: setup_v2.sh tees its output there while tests run).
- Verification process: Claude now runs the full suite itself on a copy of the Mac project (Linux VM, Python 3.14, real config and .env, TZ=America/Chicago, plus UTC and Asia/Kolkata) before asking the owner to run anything. The owner runs only steps that need live APIs.
- 13 leaked test run folders moved to `_to_delete/leaked_test_runs/`.

### Files Affected
`core/run_logger.py`, `tools/search.py`, `tests/conftest.py`, `tests/test_search.py`

### Tests
237/237 PASSING under TZ America/Chicago, UTC, Asia/Kolkata; write guard verified with a probe test.

### Owner Approval
- [x] Covered by go-live approval (2026-11-01)


---

## [CL-073] — 2026-11-02 — COMPLETED

**Type:** BUGFIX + FEATURE
**Status:** COMPLETED

### Summary
Dry run 2 (2026-11-01 22:07): JIT 10 / JIC 9 items, Tavily 102/116 kept, no wrong merges. But lesson 3C held five off-topic papers (fuzzy logic 1975, ReLU, AlphaFold 3, football, LPIPS) and JIT first-party sources fell to 10%. Root causes: (1) absolute embedding cosine is not relevance (unrelated papers scored 0.73-0.84; embedding anisotropy); (2) OpenAlex search on generic words plus most-cited sort; (3) prompt told the LLM to prefer the shortlist. Owner added: papers must be filed under Computer Science (arXiv cs.*), then use keywords/tags.

### Changes
- Category gate (owner rule): arXiv cs.* or stat.ML, else OpenAlex field Computer Science; strict for searched candidates; LLM-proposed classics outside CS (e.g. Turing 1950, philosophy) only with grade 3.
- Keyword/tag overlap from OpenAlex keywords/topics, arXiv categories, title and abstract vs short title + sub-concepts.
- LLM relevance grader (corrective-RAG pattern), new prompt `config/prompts/paper_grader.md`; gate grade >= 2; seminal needs grade 3.
- Candidates: arXiv API search in AI categories (3 s etiquette delay) + OpenAlex relevance-sorted per sub-concept; most-cited sort removed.
- Lesson prompt: LLM names defining papers first; candidates are optional.
- JIT: a first-party source in also_covered_by becomes the main link.
- Logs: `paper_pool.json` (every candidate with category, overlap, grade, rejection reason), richer `paper_shortlist.json` and `lesson_quality.json` scores.

### Files Affected
`core/citations.py`, `core/lesson.py`, `core/news.py`, `config/prompts/paper_grader.md` (new), `config/prompts/lesson.md`, `config/source_registry.json`, `tests/test_citations.py`, `tests/test_news.py`, `tests/conftest.py`, `RULES.md` (R-014), `TEST_REGISTRY.md`, `HANDOVER.md`

### Tests
T-CIT-C-014/015 rewritten; T-CIT-C-020..025, T-NEWS-C-011 new. 244/244 PASSING.

### Owner Approval
- [x] Approved 2026-11-02 ("Yes!" plus category/keyword direction)


---

## [CL-074] — 2026-11-02 — COMPLETED

**Type:** BUGFIX
**Status:** COMPLETED

### Summary
Dry run 3 (2026-11-02 07:27, $0.16): 3C now on topic (Turing 1950 seminal, grade 3; Gershman et al. 2015, grade 3) but only 2 papers; JIT first-party share still 10%; lesson-repair call hit the 180 s timeout once (retry succeeded in 38 s). Root causes found by tracing each to its log line:
1. Hallucinated DOI: the LLM gave a DOI for "Calculative Rationality" that resolves to a different paper; lookup trusted the DOI, so the wrong paper was graded 1 and dropped.
2. Grader inconsistency: "Computational Rationality as a Theory of Interaction" got grade 2 in the shortlist and 1 at verification (two separate calls).
3. JIT candidates were 28/40 media and 2/40 first-party: the editor cannot prefer a source that was never retrieved.
4. Prompt/check mismatch: check_slots enforces a 75-word TL;DR, the prompt never stated it, so every run (3 of 3) paid for a full repair call (about 40 s and $0.03; today 3 minutes with the timeout).

### Changes
- `lookup`: id result accepted only if its title matches the requested title (Jaccard >= 0.5), else title search.
- Shortlist grades reused at verification (prior_grades).
- JIT: 3 first-party searches restricted to primary tiers (registry `first_party_queries`), placed first so the 40-candidate cap keeps them.
- Lesson prompt states the 75-word TL;DR cap, asks for the full 5 papers, and warns against uncertain DOIs. New test checks every enforced limit is stated in the prompt.

### Files Affected
`core/citations.py`, `core/lesson.py`, `core/news.py`, `config/prompts/lesson.md`, `config/source_registry.json`, `tests/test_citations.py`, `tests/test_news.py`, `tests/test_lesson.py`, `TEST_REGISTRY.md`, `HANDOVER.md`

### Tests
T-NEWS-C-012, T-CIT-C-026/027, T-LES-C-021 new; T-CIT-C-002 test title corrected. 248/248 PASSING (America/Chicago, UTC).

### Owner Approval
- [x] Bug fixes within approved CL-073 design (2026-11-02)


---

## [CL-075] — 2026-11-02 — COMPLETED

**Type:** FEATURE (production) + RELEASE
**Status:** COMPLETED

### Summary
Owner decision 2026-11-02: move to production, publish code to GitHub (no archives, .env, old files or PPT).

### Changes
- `main.py --scheduled`: stops after SCHEDULE_END_DATE; never sends twice a day (R-016).
- `scripts/watchdog.py`: deterministic checks W1-W7 at 09:30; one catch-up run per day; alert email.
- `scripts/setup_launchd.py` v2: two jobs (pipeline 07:00, watchdog 09:30), .venv Python, WorkingDirectory.
- `scripts/install_production.sh`: sets a 15-run window, installs and loads both jobs, wakes the Mac at 06:55 (pmset); `--uninstall` reverses it.
- GitHub: new `.gitignore` (secrets, runtime data, archives, drafts, PPT/PDF/slides, plists, one-off probes), MIT `LICENSE`, v2 `README.md` with a sample email image, approved design drafts moved to `docs/design/`, `scripts/publish_github.sh` (re-index, secret scan, commit, gh create/push).

### Files Affected
`main.py`, `scripts/watchdog.py` (new), `scripts/setup_launchd.py`, `scripts/install_production.sh` (new), `scripts/publish_github.sh` (new), `tests/test_scheduler.py`, `.gitignore`, `LICENSE` (new), `README.md`, `docs/assets/sample_email.png`, `.env.example`, `RULES.md` (R-016), `TEST_REGISTRY.md`, `HANDOVER.md`

### Tests
T-SCH-C-010..015 new. 254/254 PASSING.

### Owner Approval
- [x] Approved 2026-11-02 ("we shall move for production; push all to Github")
