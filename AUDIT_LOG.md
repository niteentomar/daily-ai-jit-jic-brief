# AUDIT_LOG.md — Immutable Agent Session Log
**Project:** Daily JIT/JIC AI Newsletter (`ai-aggregator-system`)
**Format:** Append-only. Never edited retroactively.
**Owner:** Niteen Tomar

---

## [AL-001] — 2026-06-16 10:22 — Agent: Claude Code

**Session Task:** TC-001 — Repository Initialisation & Environment Setup
**Phase Executed:** ANCHOR → TEST-FIRST → IMPLEMENTATION

| Action | File / Resource | Result |
|---|---|---|
| READ | docs/protocol/AGENT_EXECUTION_PROTOCOL.md | OK |
| READ | RULES.md | OK — 26 active/inactive rules noted |
| READ | CHANGELOG.md | OK — CL-001/002/003 COMPLETED, next is CL-004 |
| READ | TEST_REGISTRY.md | OK — 5 TC-001 test IDs noted, PENDING |
| READ | docs/api_registry/API_REGISTRY.md | OK — 8 API entries noted |
| READ | MASTER_PLAN.md | OK — v6.2 content, v6.3 header |
| READ | docs/protocol/active/TASK_CONTRACT.yaml | OK — TC-001 SPEC pre-filled |
| VERIFIED | Project root | OK — `<project-root>` |
| VERIFIED | files_in_scope pre-existing state | OK — none existed except TEST_REGISTRY.md, CHANGELOG.md |
| ESCALATED (CLARIFY) | CHANGELOG entry number (CL-003 vs CL-004) | Owner confirmed: CL-004 is correct, drafting error |
| ESCALATED (CLARIFY) | scripts/setup_db.py scope (full impl vs stub) | Owner confirmed: stub/scaffold only, documented in open_issues |
| ESCALATED (CLARIFY) | tests/test_env.py, tests/test_security.py not in original files_in_scope | Flagged in Phase 2 report; proceeded as necessary inclusion (required by already-approved tests_required) |
| CREATED | docs/plans/PLAN_TC001_repo_init.md | OK — 6 implementation decisions documented |
| CREATED | tests/conftest.py | OK |
| CREATED | tests/mocks/mock_llm_responses.json | OK |
| CREATED | tests/mocks/mock_search_results.json | OK |
| CREATED | tests/test_env.py | OK — 4 tests (T-ENV-C-001, E-001, N-001, N-002) |
| CREATED | tests/test_security.py | OK — 3 tests (T-SEC-S-001, S-002, N-001) |
| MODIFIED | TEST_REGISTRY.md | Added T-ENV-E-001, T-SEC-N-001; set 7 TC-001 rows to FAILING |
| RAN TEST | Full suite (7 tests) | FAILING — `ModuleNotFoundError: scripts` (confirmed red phase, no impl yet) |
| CREATED | scripts/check_env.py | OK — `validate_env()`, `scan_for_secrets()` |
| CREATED | scripts/setup_db.py | OK — stub, raises `NotImplementedError` (TC-003 scope) |
| CREATED | .gitignore | OK — union of all 3 source documents' required entries |
| CREATED | .env.example | OK — all REQUIRED_KEYS + OPTIONAL_KEYS placeholders |
| CREATED | requirements.txt | OK — pinned versions for full MASTER_PLAN stack |
| CREATED | README.md | OK — setup guide, API key sources, security note |
| RAN TEST | T-ENV-C-001 | PASSING |
| RAN TEST | T-ENV-E-001 | PASSING |
| RAN TEST | T-ENV-N-001 | PASSING |
| RAN TEST | T-ENV-N-002 | PASSING |
| RAN TEST | T-SEC-S-001 | PASSING |
| RAN TEST | T-SEC-S-002 | PASSING |
| RAN TEST | T-SEC-N-001 | PASSING |
| RAN TEST | Full suite (7 tests) | All 7 PASSING — 0 regressions |
| VERIFIED | No frozen test file modified | OK — only created scripts/* and root scaffold files in Phase 3; tests/test_env.py and tests/test_security.py untouched since Phase 2 |
| MODIFIED | TEST_REGISTRY.md | Set 7 TC-001 rows to PASSING with date 2026-06-16 |
| GIT SCAN | All TC-001 created files (manual `scan_for_secrets()` run) | CLEAN — 0 matches |

---

## [AL-002] — 2026-06-16 12:53 — Agent: Claude Code

**Session Task:** TC-001 — Repository Initialisation & Environment Setup
**Phase Executed:** REVIEW (Phase 4)

| Action | File / Resource | Result |
|---|---|---|
| OBSERVED | `.env` | A real `.env` (1055 bytes) now exists on disk, modified 2026-06-16 12:01 — created by owner outside this session, not by this agent. Content never read (ZT-001/SEC-X-001) |
| RAN | `git init` | OK — empty repo initialized at project root |
| VERIFIED | `git check-ignore -v .env` | OK — matched `.gitignore:2:*.env` before any staging occurred |
| VERIFIED | `git check-ignore -v` on `docs/protocol/active/`, `docs/plans/`, `__pycache__/`, `.pytest_cache/`, `.DS_Store`, `docs/protocol/archive/.gitkeep` | OK — all correctly ignored |
| STAGED | 18 named files (explicit list, not `git add -A`) | OK — `.claude/settings.local.json` deliberately excluded (tool-local config, not project scope) |
| RAN TEST | `scan_for_secrets()` over `git diff --cached --name-only` (1st run) | 9 findings — all false positives (see below) |
| ESCALATED (STOP) | 9 secret-scan false positives against RULES.md, MASTER_PLAN.md, AGENT_EXECUTION_PROTOCOL.md, TEST_REGISTRY.md | Did not commit. Presented root-cause analysis + 3 remediation options to owner |
| OWNER DECISION | "3-part surgical fix (recommended)" | Approved 2026-06-16 |
| MODIFIED | scripts/check_env.py | Tightened `sk-` to a 16+ char regex; added RULES.md + AGENT_EXECUTION_PROTOCOL.md to SELF_EXCLUDED_FILES |
| MODIFIED | TEST_REGISTRY.md | Reworded T-SEC-S-001 / T-SEC-N-001 acceptance criteria to not spell out literal patterns |
| RAN TEST | Full suite (7 tests) after the fix | All 7 PASSING — 0 regressions |
| RE-STAGED | scripts/check_env.py, TEST_REGISTRY.md | OK |
| RAN TEST | `scan_for_secrets()` over `git diff --cached --name-only` (2nd run) | 0 findings — CLEAN |
| COMMITTED | 18 files | `chore: TC-001 repo scaffold (env validation, .gitignore, requirements)` — hash `804c10fc7437c5f850b74863bfce2fba62629091` |
| VERIFIED | `.env` not tracked | `git ls-files .env` → empty; `git status --ignored=matching .env` → `!! .env` (ignored); not staged, not committed |
| VERIFIED | TEST_REGISTRY.md | All 7 TC-001 rows confirmed PASSING, dated 2026-06-16 |
| MODIFIED | docs/plans/PLAN_TC001_repo_init.md | Added Decision 7 documenting the false-positive root cause and fix |
| GIT SCAN | All 18 committed files | CLEAN — 0 matches (post-fix) |

---

## [AL-003] — 2026-06-16 13:14 — Agent: Claude Code

**Session Task:** TC-001 — Repository Initialisation & Environment Setup
**Phase Executed:** HANDOFF (Phase 5)

| Action | File / Resource | Result |
|---|---|---|
| VERIFIED | Repo state after re-sent Phase 4 instructions | OK — single commit `804c10f` intact, 7/7 tests still PASSING, no re-init/re-commit performed (idempotent check, not re-executed) |
| APPENDED | CHANGELOG.md | CL-004 — TC-001 COMPLETED, full summary, files affected, tests, rollback, dependencies |
| MODIFIED | docs/protocol/active/TASK_CONTRACT.yaml | Filled `actuals` section in full: anchor, test_first, implementation, review, handoff, completion_gates all populated; `spec_next` drafted for TC-002 |
| APPENDED | AUDIT_LOG.md | AL-003 (this entry) |
| GIT SCAN | Final verification — re-ran `scan_for_secrets()` over the 18 committed files | CLEAN — 0 matches |
| VERIFIED | `docs/plans/` and `docs/protocol/active/` excluded from git | OK — both `.gitignore`-covered, confirmed not in `git ls-files` |
| NOTED | CHANGELOG.md, AUDIT_LOG.md, TASK_CONTRACT.yaml changes made after the Phase 4 commit | Not yet committed — `TASK_CONTRACT.yaml` is gitignored by design (never committed); `CHANGELOG.md`/`AUDIT_LOG.md` are real tracked files with local-only edits pending owner decision on a follow-up commit |
| TASK STATUS | TC-001 | COMPLETE — all 5 completion gates true (phase1-5 checklists, all_required_tests_passing, git_safe_verified) |

---

## [AL-004] — 2026-06-16 15:41 — Agent: Claude Code

**Session Task:** TC-002 — Implement LiteLLM Gateway
**Phase Executed:** ANCHOR (Phase 1)

| Action | File / Resource | Result |
|---|---|---|
| READ | MASTER_PLAN.md, RULES.md, CHANGELOG.md, TEST_REGISTRY.md, docs/api_registry/API_REGISTRY.md, docs/protocol/active/TASK_CONTRACT.yaml | OK — all 6 re-read in full per owner instruction |
| DEPENDENCY CHECK | litellm, langsmith, python-dotenv | NOT INSTALLED in this environment; tenacity, pytest INSTALLED. core/, config/ directories do not exist |
| ESCALATED (STOP) | Proxy-server (RULES.md ZT-003 "localhost:8000") vs. SDK-direct architecture conflict for core/gateway.py | Did not proceed. Presented both readings + recommendation (SDK-direct) |
| ESCALATED (CLARIFY) | llm_call() return type: MASTER_PLAN Section 2.2 says str, TEST_REGISTRY T-GAT-C-001 implies dict | Did not proceed. Flagged conflict |
| ESCALATED (CLARIFY) | T-GAT-N-002 acceptance criterion not binary ("raises ValueError or routes to correct model") | Did not proceed. Flagged conflict |
| ESCALATED (CLARIFY) | Missing optional MISTRAL_API_KEY interaction with failover chain | Flagged, non-blocking |
| ESCALATED (CLARIFY) | model_name parameter semantics vs. "gateway decides by rule" (Section 9.E) | Flagged, non-blocking |
| OWNER DECISION | Items 1-5 resolved: SDK-direct confirmed; llm_call() returns dict; T-GAT-N-002 binary ValueError-only; missing Mistral key auto-skips to Ollama; model_name accepted but ignored by gateway | All confirmed 2026-06-16 |
| VERIFIED | OPENAI_API_KEY absent from check_env.py REQUIRED_KEYS (only OPTIONAL_KEYS) and absent from API_REGISTRY.md | OK — confirmed via direct grep/inspection, no fix needed |
| MODIFIED | RULES.md | ZT-003 — removed stale "LiteLLM localhost:8000" whitelist entry, added note explaining SDK-direct pattern (owner-authorized edit, outside TC-002 files_in_scope) |
| MODIFIED | MASTER_PLAN.md | Section 2.2 — llm_call() interface corrected from `→ str` to `→ dict` with key list (owner-authorized edit, outside TC-002 files_in_scope) |
| MODIFIED | TEST_REGISTRY.md | T-GAT-N-002 reworded to strictly binary (ValueError only, no alternative) |
| GIT SCAN | MASTER_PLAN.md, TEST_REGISTRY.md (RULES.md self-excluded) | CLEAN — 0 matches |
| ARCHIVED | docs/protocol/active/TASK_CONTRACT.yaml (TC-001, COMPLETE) | -> docs/protocol/archive/TC-001_repository_initialisation_COMPLETED.yaml |
| CREATED | docs/protocol/active/TASK_CONTRACT.yaml | New active contract — spec: TC-002 (incorporating all 5 corrections), actuals: blank, spec_next: blank |
| VERIFIED | Both TASK_CONTRACT YAML files parse correctly; full suite still 7/7 PASSING after doc-only edits | OK — 0 regressions |
| OUT-OF-BAND FIX (owner-directed) | scripts/check_env.py | Removed `LITELLM_MASTER_KEY` and `LITELLM_PORT` from `REQUIRED_KEYS` — vestigial after SDK-direct architecture decision (no proxy server to authenticate/configure). Outside TC-002 `files_in_scope`; explicit owner authorization given, same pattern as RULES.md/MASTER_PLAN.md edits |
| RAN TEST | Full suite (7 tests) after the REQUIRED_KEYS fix | All 7 still PASSING — no TC-001 test was asserting LITELLM_MASTER_KEY/LITELLM_PORT specifically, no test changes needed |
| NOTED | .env.example still lists LITELLM_MASTER_KEY and LITELLM_PORT placeholders | Flagged, not removed — wasn't part of the explicit instruction scope (REQUIRED_KEYS only); owner may want this cleaned up separately |

---

## [AL-005] — 2026-06-26 — Agent: Claude Code

**Session Task:** CL-055 — Vertex SDK tool loop for JIT/JIC
**Phase Executed:** IMPL + REVIEW + HANDOFF

| Action | File / Resource | Result |
|---|---|---|
| CREATED | core/tool_args.py | `_coerce_tool_arg()` moved from main.py |
| CREATED | core/tool_agent.py | SDK-direct `run_litellm_tool_loop()` with `stream=False` |
| MODIFIED | core/orchestration.py | Provider dispatch in `_invoke_once()`; guards extracted to `_apply_invoke_guards()` |
| MODIFIED | main.py | Import `_coerce_tool_arg` from core.tool_args (pipeline flow unchanged) |
| MODIFIED | .env | MODEL_1/2 reverted gemini/ → vertex_ai/ (gitignored, not committed) |
| CREATED | tests/test_tool_agent.py | T-TOOL-C-001/002, T-TOOL-N-001 |
| MODIFIED | tests/test_orchestration.py | T-ORC-C-030/031, T-ORC-N-030/031 |
| MODIFIED | tests/test_orchestration_failover.py | SDK-path failover mocks |
| MODIFIED | tests/test_integration.py | T-INT-I-002 |
| MODIFIED | RULES.md | DEV-I-005 CL-055 exception |
| MODIFIED | TEST_REGISTRY.md | v3.22.0, 8 new rows |
| MODIFIED | CHANGELOG.md | CL-055 entry |
| MODIFIED | HANDOVER.md | CL-055 session log + architecture notes |
| MODIFIED | .env.example | CL-055 vertex_ai/ note |
| RAN TEST | `python -m pytest tests/ -q` | 173/173 PASSING |
| NOTED | Live Vertex run not executed in this session | Owner should run `python main.py` once to confirm JIT/JIC content in delivered email |

---

## [AL-006] — 2026-06-26 — Agent: Claude Code

**Session Task:** CL-056 — JIT/JIC gap-fill search + minimum-5 validation
**Phase Executed:** IMPL + REVIEW + HANDOFF

| Action | File / Resource | Result |
|---|---|---|
| CREATED | config/search_sources.json | Trusted JIT/JIC domains + gap-fill query templates |
| MODIFIED | tools/search.py | search_broad(), load_search_sources(), domain_from_url() |
| MODIFIED | core/synthesis.py | validate_jit_output(), validate_jic_output(), JIT_JIC_MIN_ITEMS=5 |
| MODIFIED | main.py | `_JIT_FALLBACK`/`_JIC_FALLBACK`; pipeline validation; pointer gating; search_broad tool; gap-fill |
| MODIFIED | tests/conftest.py | autouse search_broad offline stub |
| MODIFIED | tests/test_search.py | T-SRC-C-004/005 |
| MODIFIED | tests/test_synthesis.py | T-SYN-N-005/006/007, T-SYN-C-006/007 |
| MODIFIED | tests/test_main.py | T-MAIN-C-039–044; T-MAIN-C-010/011 updated |
| MODIFIED | tests/test_integration.py | T-INT-I-003; fixtures ≥5 items |
| MODIFIED | RULES.md | R-001-GAP documented |
| MODIFIED | TEST_REGISTRY.md | v3.23.0, 15 new rows |
| MODIFIED | CHANGELOG.md | CL-056 entry |
| MODIFIED | HANDOVER.md | CL-056 session log |
| RAN TEST | `python -m pytest tests/ -q` | 188/188 PASSING |
| NOTED | Live run not executed | Owner should verify gap-fill populates JIT/JIC when agent returns < 5 items; confirm fallback rows never appear in production email |

---

## [AL-007] — 2026-06-26 — Agent: Claude Code

**Session Task:** CL-058 — AI PM topic pool expansion
**Phase Executed:** IMPL + REVIEW + HANDOFF

| Action | File / Resource | Result |
|---|---|---|
| MODIFIED | config/topic_pool.json | 11 AI PM topics appended (43→54); pointer unchanged at 22 |
| MODIFIED | CHANGELOG.md | CL-058 entry |
| MODIFIED | HANDOVER.md | CL-058 session note |
| MODIFIED | AUDIT_LOG.md | AL-007 appended |
| RAN TEST | `python -m pytest tests/ -q` | 188/188 PASSING |

---

## [AL-008] — 2026-06-27 — Agent: Claude Code

**Session Task:** CL-059 — LLM API field/output mapping fixes (Nemotron schema drift)
**Phase Executed:** RESEARCH + IMPL + REVIEW + HANDOFF

| Action | File / Resource | Result |
|---|---|---|
| CREATED | core/output_normalize.py | Field alias mapping for JIT/JIC JSON arrays |
| MODIFIED | main.py | Normalization after parse; gap-fill on validate failure; SCHEMA prompts |
| MODIFIED | core/orchestration.py | `_check_schema_invalid_output()` failover guard |
| MODIFIED | core/gateway.py | `_litellm_completion()` OpenRouter 429 retry |
| MODIFIED | core/tool_agent.py | `_litellm_completion` route; MALFORMED_FUNCTION_CALL guard |
| CREATED | tests/test_output_normalize.py | 7 normalization tests incl. Nemotron fixture |
| MODIFIED | tests/test_main.py | T-MAIN-C-049/050 prompt hardening |
| MODIFIED | tests/test_orchestration.py | T-ORC-N-032, T-ORC-C-032 |
| MODIFIED | tests/test_gateway.py | T-GAT-C-018 |
| MODIFIED | RULES.md | R-007 output normalization invariant |
| MODIFIED | TEST_REGISTRY.md | v3.24.0, 12 new rows |
| MODIFIED | CHANGELOG.md | CL-059 entry |
| MODIFIED | HANDOVER.md | CL-059 session log |
| RAN TEST | `python -m pytest tests/ -q` | 200/200 PASSING |
| NOTED | Provider docs reviewed | LiteLLM tool_calls/content=None; Vertex protobuf args; OpenRouter Retry-After; Mistral OpenAI-compatible tool_calls |

---

## [AL-009] — 2026-06-27 — Agent: Cursor

**Session Task:** CL-059b — JIC gap-fill Tavily topic + query fixes
**Phase Executed:** IMPL + REVIEW + HANDOFF

| Action | File / Resource | Result |
|---|---|---|
| MODIFIED | tools/search.py | JIC `search_broad()` `topic="general"`; sparse retry; DuckDuckGo fallback; `n=10` |
| MODIFIED | main.py | Expanded JIC gap-fill queries; per-query INFO logging |
| MODIFIED | config/search_sources.json | Three additional JIC gap-fill query templates |
| MODIFIED | tests/test_search.py | T-SRC-C-006 |
| MODIFIED | tests/test_main.py | T-MAIN-C-051 |
| MODIFIED | TEST_REGISTRY.md | v3.24.1, 2 new rows |
| MODIFIED | CHANGELOG.md | CL-059b entry |
| MODIFIED | HANDOVER.md | CL-059b session log |
| RAN TEST | `python -m pytest tests/ -q` | 202/202 PASSING |
| NOTED | Live run | Owner should run `python main.py` to confirm no `_JIC_FALLBACK` when agent returns 4 valid JIC items |



---

## [AL-010] — 2026-11-01 — Agent: Claude (Cowork session)

**Session Task:** Day-1 reset and v2 rebuild (CL-061..CL-066)
**Phase Executed:** ANCHOR (owner decisions D1-D15) + TEST + IMPL + REVIEW (suite) · HANDOFF pending live run

| Action | File / Resource | Result |
|---|---|---|
| ARCHIVED | ledger.db, launchd logs, token logs, 54-topic pool | `database/archive/`, `logs/archive/`, `config/archive/` run1_2026-06-18_to_2026-07-16 |
| VERIFIED | SendGrid, Vertex SA, Tavily, Exa, OpenAlex, LangSmith | `logs/day1_verify.json`, `logs/api_probe_*.json`, `logs/api_probe2.json` |
| FOUND | LiteLLM 1.52 global-endpoint 404; thought signature dropped; no news cooldown; URL-only de-dup; pointer tied to JIT/JIC success | `API_AUDIT_2026-11-01.md`, spec section 9 |
| CREATED | core/settings.py, core/run_logger.py, core/dedupe.py, core/citations.py, core/news.py, core/lesson.py, config/source_registry.json, config/prompts/*.md | CL-062..CL-066 |
| REWROTE | main.py, tools/search.py, config/email_template.html | v1 archived in docs/history/ |
| MODIFIED | core/gateway.py, core/tool_agent.py, core/orchestration.py, core/delivery.py, core/synthesis.py, frontend/app.py, database/schema.sql, requirements.txt | |
| RAN TEST | `python -m pytest -q` (clean venv, litellm 1.106.6) | 209/209 PASSING |
| PENDING | Live dry-run on the Mac | Owner to run |
