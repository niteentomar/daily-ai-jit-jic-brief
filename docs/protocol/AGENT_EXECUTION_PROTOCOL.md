# AGENT EXECUTION PROTOCOL
**Version:** 1.1.0  
**Status:** Active  
**Location:** `docs/protocol/AGENT_EXECUTION_PROTOCOL.md`  
**Applies to:** Claude Code (primary implementing agent); any future agent working on this project  
**Last Updated:** 2026-06-15  
**Owner:** Niteen Tomar  

---

## ⚠️ MANDATORY LOAD INSTRUCTION

**Every AI agent, every session, without exception:**  
Before writing a single line of code, creating any file, or making any change — read this document in full. Then read RULES.md, CHANGELOG.md, and TEST_REGISTRY.md. Only then proceed to Phase 1.

If any of these files cannot be found, **STOP** and raise an escalation. Do not proceed.

---

## SECTION 0 — IDENTITY & SCOPE

### 0.1 What This Protocol Is
This is the behavioral contract for all AI agents working on this project. It is not a suggestion. It is not a guideline. Every agent follows it completely, in sequence, without exception or improvisation.

### 0.2 What This Protocol Is Not
- It is not a prompt. It does not override explicit task instructions from the project owner.
- It is not negotiable. An agent cannot skip a phase because it "seems unnecessary."
- It is not exhaustive of domain knowledge. Agents must still read source documents.

### 0.3 Hierarchy of Authority
```
Project Owner (Niteen) — highest authority
    ↓
MASTER_PLAN.md — architectural source of truth
    ↓
AGENT_EXECUTION_PROTOCOL.md — behavioral source of truth (this file)
    ↓
RULES.md — operational rules
    ↓
TASK_CONTRACT.yaml — task-level spec
    ↓
Agent judgment — lowest authority, only fills gaps not covered above
```

When in conflict, higher authority wins. Agent judgment is never used to override any layer above it.

### 0.4 Structural Change Rule (GOV-001)
Once the system is developed and deployed:
- Future work operates **on** the existing architecture, not by replacing it.
- New functionality is added as modules, not rewrites.
- Any proposed structural change requires written justification and explicit owner approval before implementation begins.
- The agent documents the proposed change in CHANGELOG.md under status `PROPOSED`, waits for approval, then proceeds only after owner confirms.

---

## SECTION 1 — FOLDER & FILE GOVERNANCE

### 1.1 Project Root (Non-Negotiable)
All project files — including AI-generated plans, implementation files, documentation, and configuration — live under the project root:
```
<project-root>/
```

**An AI agent must never create project files in:**
- Its own working directory or scratch space
- Any path outside the project root
- Temporary folders, unless explicitly for scratch testing (must be deleted after)

If an agent cannot locate the project root, it must **STOP** and escalate. It must not create a new folder.

### 1.2 Canonical Folder Structure
```
ai-aggregator-system/
├── core/                    # Runtime application code only
├── config/                  # Configuration files (non-secret)
├── tests/                   # All test files
├── docs/
│   ├── protocol/            # This file + TASK_CONTRACT.yaml
│   ├── plans/               # AI-generated implementation plans (NOT committed to git)
│   ├── api_registry/        # API Registry (SECTION 3.4)
│   └── architecture/        # System architecture diagrams and notes
├── logs/                    # Runtime logs (NOT committed to git)
├── scripts/                 # Utility scripts
├── .env                     # Secrets — NEVER committed (see Section 2)
├── .env.example             # Placeholder template — safe to commit
├── .gitignore               # Must include all items in Section 2.3
├── RULES.md                 # Central rule repository
├── TEST_REGISTRY.md         # Central test case repository
├── CHANGELOG.md             # Running change log
├── AUDIT_LOG.md             # Audit log
└── MASTER_PLAN.md           # Architectural source of truth
```

### 1.3 Planning Files Rule
All AI-generated plans (implementation plans, design notes, task breakdowns) go in `docs/plans/`. They are named `PLAN_<TASK_ID>_<short_description>.md`.

Example: `docs/plans/PLAN_T003_gateway_implementation.md`

These files are working documents, not system files. They are listed in `.gitignore`.

### 1.4 What the Agent Checks Before Creating Any File
Before creating any file, the agent must:
1. Confirm the target path is inside the project root
2. Check whether a file with the same name already exists anywhere in the project
3. If it exists — read it first, then edit. Never overwrite without reading.
4. If unsure where to place a new file — escalate, do not guess.

---

## SECTION 2 — SECURITY & ZERO TRUST

### 2.1 Zero Trust Principles (ZT-001, ZT-002, ZT-003)

**ZT-001 — Secrets Never Leave `.env`**
- API keys, tokens, passwords, and credentials exist only in `.env`
- They are never hardcoded in any source file, config file, log file, or documentation
- They are never passed as command-line arguments
- They are never printed to stdout or written to any log

**ZT-002 — `.env` Never Reaches Git**
- `.env` is always in `.gitignore`
- The agent verifies `.gitignore` contains `.env` before any `git add` or commit action
- If `.gitignore` does not contain `.env`, the agent must add it and verify before proceeding

**ZT-003 — Pre-Commit Secret Scan**
Before any commit, the agent must verify that no modified or new file contains:
- Any string matching patterns: `sk-`, `AIza`, `Bearer `, `api_key =`, `token =`, `password =`
- Any reference to a real key value (not a placeholder)
- The agent runs this check on every file in the commit diff, not just files it touched in the current task

### 2.2 API Key Handling Rules
```
✅ ALLOWED:                          ❌ FORBIDDEN:
os.getenv("GEMINI_API_KEY")          api_key = "AIzaSy..."
load_dotenv() then os.getenv()       config["key"] = ACTUAL_KEY
.env.example with placeholder        logging.info(f"Key: {api_key}")
Masked display: key[:4]+"****"       print(api_key)
```

### 2.3 Mandatory `.gitignore` Entries
The agent verifies these are present in `.gitignore` before any commit:
```
.env
*.env
logs/
docs/plans/
__pycache__/
*.pyc
.DS_Store
token_usage.json
*_secrets.*
scratch/
```

### 2.4 `.env.example` Standard
Every secret variable in `.env` must have a corresponding placeholder in `.env.example`:
```
# .env.example — safe to commit, shows required variables
GEMINI_API_KEY=your_gemini_api_key_here
SENDGRID_API_KEY=your_sendgrid_api_key_here
LANGSMITH_API_KEY=your_langsmith_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```
Placeholder format: `your_<service>_key_here` — never a real value.

---

## SECTION 3 — CENTRAL REPOSITORIES

All four repositories below are living documents. The agent reads them at session start (Phase 1) and updates them at the appropriate phase. Failure to update is a protocol violation.

---

### 3.1 Rule Repository — `RULES.md`

#### Purpose
Single source of truth for all operational rules governing agent behavior, system behavior, and development standards.

#### Column Structure (every rule must follow this exactly)

| Column | Description |
|---|---|
| **Rule ID** | Alphanumeric. Format: `[DOMAIN]-[STAGE]-[SEQ]`. See numbering logic below. |
| **Rule Name** | Short imperative title (max 8 words) |
| **Description** | What the rule requires, in plain language |
| **Applies To Stage** | One or more of: ANCHOR, TEST, IMPL, REVIEW, HANDOFF, ALL |
| **Priority** | 1 (highest) to 5 (lowest). Lower number = enforced first when rules conflict. |
| **Active** | YES / NO. Inactive rules are retained for history but not enforced. |
| **Conflict Resolution** | If this rule conflicts with another, which wins and why |
| **Added In** | CHANGELOG entry ID that introduced this rule |
| **Last Reviewed** | Date |

#### Rule ID Numbering Logic
```
Format: [DOMAIN]-[STAGE]-[SEQ]

DOMAIN codes:
  GOV  — Governance / structural
  SEC  — Security / Zero Trust
  DEV  — Development standards
  TST  — Testing
  LOG  — Logging / audit
  API  — API usage
  GIT  — Git / version control

STAGE codes:
  A  — Anchor phase
  T  — Test-first phase
  I  — Implementation phase
  R  — Review phase
  H  — Handoff phase
  X  — Cross-phase (applies to all)

SEQ: 3-digit sequence within domain+stage, e.g. 001, 002

Examples:
  SEC-X-001  → Security rule, applies to all phases, first rule
  DEV-I-003  → Development rule, implementation phase, third rule
  TST-T-001  → Testing rule, test-first phase, first rule
  GOV-X-001  → Governance rule (GOV-001 = structural change rule)
```

#### Sample Rule Entries (illustrative, not exhaustive)

| Rule ID | Rule Name | Description | Applies To Stage | Priority | Active | Conflict Resolution | Added In | Last Reviewed |
|---|---|---|---|---|---|---|---|---|
| GOV-X-001 | Structural changes need approval | No architectural change is implemented without owner's written approval. Agent documents under `PROPOSED` in CHANGELOG, waits. | ALL | 1 | YES | Overrides all DEV rules | CL-001 | 2026-06-15 |
| SEC-X-001 | Secrets stay in .env | API keys and tokens exist only in .env, never in source files | ALL | 1 | YES | Overrides any convenience shortcut | CL-001 | 2026-06-15 |
| SEC-X-002 | .env never committed | .gitignore must contain .env before any commit | ALL | 1 | YES | If .gitignore missing, STOP | CL-001 | 2026-06-15 |
| SEC-X-003 | Pre-commit secret scan | Agent scans all files in commit diff for secret patterns before committing | HANDOFF | 1 | YES | STOP if any match found | CL-001 | 2026-06-15 |
| DEV-A-001 | Read before creating | Agent reads any existing file before creating a same-named file | ANCHOR | 2 | YES | Prevents overwrite; if conflict, escalate | CL-001 | 2026-06-15 |
| DEV-A-002 | Locate project root first | Agent verifies project root path before any file operation | ANCHOR | 1 | YES | If not found, STOP | CL-001 | 2026-06-15 |
| DEV-I-001 | Prefer deterministic | Choose deterministic implementation over probabilistic where functionally equivalent | IMPL | 3 | YES | DEV-I-001 over agent judgment | CL-001 | 2026-06-15 |
| TST-T-001 | Tests before code | Test cases written and registered before implementation begins | TEST | 1 | YES | No exceptions; block implementation if violated | CL-001 | 2026-06-15 |
| LOG-H-001 | Changelog always updated | Every task must produce a CHANGELOG entry before handoff | HANDOFF | 2 | YES | If changelog not updated, handoff incomplete | CL-001 | 2026-06-15 |
| GIT-H-001 | Plans excluded from git | docs/plans/ and .env never in any commit | HANDOFF | 1 | YES | Overrides convenience; STOP if violated | CL-001 | 2026-06-15 |

---

### 3.2 Test Case Repository — `TEST_REGISTRY.md`

#### Purpose
Single source of truth for all test cases across the project. No test is run unless it is registered here. No implementation is complete unless its required test cases are registered and passing.

#### Column Structure (every test case must follow this exactly)

| Column | Description |
|---|---|
| **Test ID** | Alphanumeric. Format: `T-[MODULE]-[TYPE]-[SEQ]`. See numbering logic below. |
| **Test Name** | Short descriptive title (max 10 words) |
| **What to Test** | Specific behavior, function, or condition being verified |
| **Test Type** | CORE / EDGE / NEGATIVE / INTEGRATION / SECURITY |
| **Maps To Stage** | ANCHOR / TEST / IMPL / REVIEW / HANDOFF |
| **Module** | Which system module this tests (e.g., GATEWAY, DELIVERY, ORCHESTRATION) |
| **Acceptance Criteria** | Exact pass condition — what must be true for this test to pass |
| **Status** | PENDING / PASSING / FAILING / SKIPPED |
| **Introduced By** | Task ID or CHANGELOG entry that required this test |
| **Last Run** | Date + result |

#### Test ID Numbering Logic
```
Format: T-[MODULE]-[TYPE]-[SEQ]

MODULE codes (3 letters):
  GAT  — Gateway (LiteLLM)
  DEL  — Delivery (email)
  ORC  — Orchestration (ReACT agent)
  SCH  — Scheduler
  DB   — Database
  API  — API Registry
  SEC  — Security
  ENV  — Environment setup
  INT  — Integration (cross-module)

TYPE codes (1 letter):
  C  — Core (happy path)
  E  — Edge case
  N  — Negative scenario
  I  — Integration
  S  — Security

SEQ: 3-digit sequence within module+type

Examples:
  T-GAT-C-001  → Gateway, core test, first
  T-GAT-E-001  → Gateway, edge case, first
  T-SEC-S-001  → Security, security test, first
  T-INT-I-001  → Integration, cross-module, first
  T-ENV-N-001  → Environment, negative test, first
```

#### Sample Test Case Entries (illustrative)

| Test ID | Test Name | What to Test | Test Type | Maps To Stage | Module | Acceptance Criteria | Status | Introduced By | Last Run |
|---|---|---|---|---|---|---|---|---|---|
| T-ENV-C-001 | Env vars loaded correctly | All required env vars present and non-placeholder | CORE | ANCHOR | ENV | `check_env.py` exits 0; all vars non-empty and not matching `*_here` | PASSING | CL-001 | 2026-06-15 |
| T-ENV-N-001 | Placeholder detection | `.env` with placeholder values is rejected | NEGATIVE | ANCHOR | ENV | `check_env.py` raises ValueError and exits non-zero | PASSING | CL-001 | 2026-06-15 |
| T-GAT-C-001 | Gemini Flash success + cost tracking | Mock Gemini response is returned and token count logged | CORE | IMPL | GAT | Response text non-empty; `token_usage.json` updated with correct delta | PENDING | CL-002 | — |
| T-GAT-E-001 | Failover on primary failure | When Gemini Flash fails, routes to Flash-Lite then Mistral | EDGE | IMPL | GAT | All three fallbacks attempted in order; final response from Mistral | PENDING | CL-002 | — |
| T-GAT-N-001 | Token budget enforcement | Request aborted when daily token limit reached | NEGATIVE | IMPL | GAT | Exception raised before API call; `token_usage.json` not incremented | PENDING | CL-002 | — |
| T-GAT-E-002 | Logs dir auto-created | `logs/` created if absent on first gateway init | EDGE | IMPL | GAT | No FileNotFoundError; `logs/token_usage.json` created successfully | PENDING | CL-002 | — |
| T-SEC-S-001 | No secrets in committed files | Pre-commit scan finds no API key patterns in diff | SECURITY | HANDOFF | SEC | Scan returns zero matches for all secret patterns | PENDING | CL-001 | — |

---

### 3.3 Change Log — `CHANGELOG.md`

#### Purpose
Running, append-only record of every feature, fix, rule change, and structural decision. Written in chronological order. Never edited retroactively — only appended.

#### Entry Format (every entry must follow this exactly)

```markdown
## [CL-XXX] — YYYY-MM-DD — [STATUS]

**Type:** FEATURE / BUGFIX / RULE_CHANGE / STRUCTURAL / SECURITY / CONFIGURATION
**Author:** [Agent name or "Owner"]
**Task ID:** [TASK_CONTRACT ID if applicable]
**Status:** PROPOSED / IN_PROGRESS / COMPLETED / REJECTED

### Summary
One paragraph describing what changed and why.

### Files Affected
- `path/to/file.py` — [what changed]
- `path/to/another.py` — [what changed]

### Rules Added/Modified
- [Rule ID] — [what changed]

### Tests Added/Modified
- [Test ID] — [what changed]

### Dependencies
- Depends on: [CL-XXX if this builds on prior entry]
- Blocks: [CL-XXX if future work depends on this]

### Rollback
[How to undo this change if needed]

### Owner Approval
- [ ] Approved by Niteen  (required for STRUCTURAL and RULE_CHANGE types)
```

#### Running Order Rule
Entries are numbered sequentially: CL-001, CL-002, CL-003...  
CL-001 is always the project initialization entry.  
No entry is ever deleted or renumbered.  
If a PROPOSED entry is rejected, it stays with status `REJECTED` and a rejection note.

---

### 3.4 API Registry — `docs/api_registry/API_REGISTRY.md`

#### Purpose
Central record of every external API used in the project. Agents consult this before making any API call and update it when adding a new API dependency.

#### Column Structure

| Column | Description |
|---|---|
| **API ID** | Format: `API-[SERVICE]-[SEQ]` e.g. `API-GEMINI-001` |
| **Service Name** | Human-readable name (e.g. Gemini Flash) |
| **Endpoint / Model** | Exact endpoint URL or model string |
| **Used In Stage** | Which execution phase calls this API |
| **Used By Module** | Which code module makes this call |
| **Input** | What the module sends (schema or description) |
| **Output** | What the API returns (schema or description) |
| **Condition to Call** | When this API is called (e.g. "primary LLM attempt") |
| **Fallback** | What happens if this API fails (next API ID or action) |
| **Error Handling** | How errors are caught and logged |
| **Rate Limit** | Known rate or quota limit |
| **Secret Variable** | Which `.env` variable holds the key |
| **Cost Tier** | FREE / PAID / CONDITIONAL |
| **Status** | ACTIVE / DEPRECATED / STANDBY |

#### Sample API Registry Entries

| API ID | Service Name | Endpoint / Model | Used In Stage | Used By Module | Input | Output | Condition to Call | Fallback | Error Handling | Rate Limit | Secret Variable | Cost Tier | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| API-GEMINI-001 | Gemini 2.5 Flash | `gemini/gemini-2.5-flash` | IMPL | GATEWAY | Prompt string, max_tokens | Text completion | Primary LLM attempt | API-GEMINI-002 | Log error, increment failure counter, route to fallback | 1,500 req/day free | `GEMINI_API_KEY` | FREE | ACTIVE |
| API-GEMINI-002 | Gemini 2.5 Flash-Lite | `gemini/gemini-2.5-flash-lite` | IMPL | GATEWAY | Prompt string, max_tokens | Text completion | API-GEMINI-001 fails | API-MISTRAL-001 | Log error, route to next fallback | 1,500 req/day free | `GEMINI_API_KEY` | FREE | ACTIVE |
| API-MISTRAL-001 | Mistral 7B Instruct | `mistral/mistral-7b-instruct-v0.2` | IMPL | GATEWAY | Prompt string, max_tokens | Text completion | API-GEMINI-002 fails | API-OLLAMA-001 | Log error, route to local | Free tier | `MISTRAL_API_KEY` | FREE | ACTIVE |
| API-OLLAMA-001 | Ollama llama3.2 local | `ollama/llama3.2` | IMPL | GATEWAY | Prompt string | Text completion | All cloud APIs fail | STOP + alert email | Log critical, send alert | Local, no limit | None | FREE | ACTIVE |
| API-TAVILY-001 | Tavily Search | `https://api.tavily.com/search` | IMPL | ORCHESTRATION | Query string, max_results | JSON results list | Primary search attempt | API-DDG-001 | Log error, use fallback | 1,000 req/month free | `TAVILY_API_KEY` | FREE | ACTIVE |
| API-SGRID-001 | SendGrid Email | `https://api.sendgrid.com/v3/mail/send` | HANDOFF | DELIVERY | HTML body, recipient, subject | HTTP 202 accepted | Primary email delivery | Gmail SMTP fallback | Log error, retry once, then Gmail | 100 emails/day free | `SENDGRID_API_KEY` | FREE | ACTIVE |
| API-LSMTH-001 | LangSmith Tracing | LangSmith SDK | ALL | ALL modules | Run name, inputs, outputs | Trace object | Every LLM call | Log warning, continue without trace | Non-blocking; log warning only | Free tier | `LANGSMITH_API_KEY` | FREE | ACTIVE |

---

### 3.5 Audit Log — `AUDIT_LOG.md`

#### Purpose
Immutable record of every agent session: what was read, what was created/modified, what tests ran, what escalations were raised. Append-only. Never edited.

#### Entry Format

```markdown
## [AL-XXX] — YYYY-MM-DD HH:MM — Agent: [agent_name]

**Session Task:** [TASK_CONTRACT ID]
**Phase Executed:** [ANCHOR / TEST / IMPL / REVIEW / HANDOFF]

| Action | File / Resource | Result |
|---|---|---|
| READ | MASTER_PLAN.md | OK |
| READ | RULES.md | OK |
| READ | CHANGELOG.md | OK |
| READ | TEST_REGISTRY.md | OK |
| CREATED | core/gateway.py | OK |
| MODIFIED | TEST_REGISTRY.md | Added T-GAT-C-001, T-GAT-E-001 |
| RAN TEST | T-GAT-C-001 | PASSING |
| RAN TEST | T-GAT-E-001 | FAILING — logged |
| ESCALATED | GOV-X-001 | Raised to owner: proposed change to gateway structure |
| GIT SCAN | All modified files | CLEAN — no secrets found |
```

---

## SECTION 4 — EXECUTION PHASES

Phases are sequential. An agent never skips a phase. An agent never begins a phase until the previous phase checklist is fully complete.

---

### PHASE 1 — ANCHOR

**Purpose:** Ground the agent completely in existing state before any action.

**Mandatory reads (in this order):**
1. `MASTER_PLAN.md` — architectural source of truth
2. `RULES.md` — all active rules (Active = YES)
3. `CHANGELOG.md` — full history, most recent 10 entries minimum
4. `TEST_REGISTRY.md` — all test cases relevant to this task's modules
5. `docs/api_registry/API_REGISTRY.md` — all APIs used by in-scope modules
6. `TASK_CONTRACT.yaml` (SPEC section) — assigned task boundaries
7. Every file listed in `source_documents` in the TASK_CONTRACT
8. Every file listed in `files_in_scope` in the TASK_CONTRACT
9. Every file that any in-scope file imports or depends on

**Dependency check:**
- List all modules the in-scope code imports
- For each import: does the imported module already exist? Does it behave as expected?
- If a dependency is missing or broken, **STOP** and escalate before proceeding

**Pre-existing file check:**
- For every file the task requires creating: does it already exist?
- If yes: read it, identify what exists, plan to extend not overwrite

**Phase 1 Checklist (all must be YES before Phase 2):**
- [ ] MASTER_PLAN.md read and task aligns with it
- [ ] All active rules in RULES.md read
- [ ] CHANGELOG.md reviewed — no conflicting in-progress work
- [ ] TEST_REGISTRY.md reviewed — relevant test IDs noted
- [ ] API_REGISTRY.md reviewed — all APIs for this task noted
- [ ] TASK_CONTRACT SPEC section read — boundaries clear
- [ ] All source_documents read
- [ ] All files_in_scope read
- [ ] All dependencies verified as existing and functional
- [ ] No pre-existing file will be overwritten without reading it first
- [ ] Project root confirmed — all file paths verified against Section 1.2

---

### PHASE 2 — TEST-FIRST

**Purpose:** Define exactly what "done" looks like before writing any implementation code.

**Steps:**
1. For each functional requirement in the TASK_CONTRACT, write at minimum:
   - 1 CORE test (happy path)
   - 1 EDGE test (boundary or unusual input)
   - 1 NEGATIVE test (failure, invalid input, missing dependency)
2. For security-relevant functionality, add 1 SECURITY test
3. For cross-module functionality, add 1 INTEGRATION test
4. Register every test case in `TEST_REGISTRY.md` before writing implementation
5. Write test code in `tests/` — named `test_<module>.py`
6. Run tests — they must **fail** at this point (no implementation yet). If they pass, the test is wrong.
7. Record test IDs and FAILING status in AUDIT_LOG.md

**Acceptance criteria rule:**
Every test case must have a binary pass condition — not "works correctly" but "function returns dict with keys `status`, `tokens_used`, `response_text` and `status == 'success'`."

**Self-critique check:**
Before moving to Phase 3, ask: "Do these tests cover what the system must do, what it must not do, and what happens when things go wrong?" If any answer is no, add tests.

**Phase 2 Checklist (all must be YES before Phase 3):**
- [ ] At minimum 1 CORE, 1 EDGE, 1 NEGATIVE test per functional requirement
- [ ] All tests registered in TEST_REGISTRY.md with correct IDs
- [ ] Test code exists in `tests/` directory
- [ ] Tests run and FAIL (confirming they test real behavior)
- [ ] Acceptance criteria are binary (pass/fail, not subjective)
- [ ] AUDIT_LOG.md updated with test IDs and FAILING status

---

### PHASE 3 — IMPLEMENTATION

**Purpose:** Write code that makes the Phase 2 tests pass — no more, no less.

**Steps:**
1. Implement only what is specified in the TASK_CONTRACT `files_in_scope`
2. Prefer deterministic implementations over probabilistic ones where functionally equivalent
3. After writing each function: run its corresponding test immediately
4. Self-review cycle per function (Draft → Verify → Critique → Revise):
   - **Draft:** write the function
   - **Verify:** run the test; check against acceptance criteria
   - **Critique:** does it handle the edge case? the negative case? does it leak secrets?
   - **Revise:** fix issues before moving to next function
5. Do not add functionality not specified in the TASK_CONTRACT (no scope creep)
6. API calls must use the pattern in API_REGISTRY.md — no new API patterns without updating registry
7. Secrets accessed only via `os.getenv()` — never hardcoded

**Deterministic preference examples:**
```
PREFER:                                AVOID (unless required):
Rule-based routing logic               LLM deciding routing
Regex for pattern matching             LLM classifying patterns
Exact string comparison                Fuzzy/semantic comparison
Explicit fallback order                Agent deciding fallback order
```

**Phase 3 Checklist (all must be YES before Phase 4):**
- [ ] Every function has a corresponding test in TEST_REGISTRY.md
- [ ] All newly created tests are PASSING
- [ ] No file outside `files_in_scope` was modified
- [ ] No secrets hardcoded — all via `os.getenv()`
- [ ] No new API calls without updating API_REGISTRY.md
- [ ] Self-review cycle (Draft→Verify→Critique→Revise) completed per function
- [ ] No scope creep — only what TASK_CONTRACT specified

---

### PHASE 4 — REVIEW

**Purpose:** Verify correctness, completeness, and downstream impact before handoff.

**Steps:**

**4A — Full Test Suite Run:**
- Run ALL tests in TEST_REGISTRY.md (not just this task's tests)
- Any test that was PASSING before must still be PASSING
- If any previously passing test now fails: this is a regression — STOP, fix before proceeding

**4B — Dependency & Downstream Impact Check:**
- List every module that imports from any file modified in Phase 3
- For each: does the modification break its interface or behavior?
- Run integration tests if they exist

**4C — Rule Compliance Check:**
- Re-read all Priority 1 and Priority 2 rules in RULES.md
- Confirm implementation complies with each

**4D — Security Review:**
- Run pre-commit secret scan (ZT-003)
- Verify `.gitignore` contains all required entries (Section 2.3)
- Confirm `.env.example` is up to date with any new variables

**4E — Self-critique Pass:**
- Read every file modified in Phase 3 from top to bottom as if reviewing someone else's code
- Ask: "What could go wrong? What did I miss? What assumption did I make that might be wrong?"
- Fix any issues found

**Phase 4 Checklist (all must be YES before Phase 5):**
- [ ] Full test suite run — all previously PASSING tests still PASSING
- [ ] No regressions introduced
- [ ] Downstream modules verified unbroken
- [ ] All Priority 1 + 2 rules complied with
- [ ] Pre-commit secret scan: CLEAN
- [ ] `.gitignore` verified
- [ ] `.env.example` up to date
- [ ] Self-critique pass complete

---

### PHASE 5 — HANDOFF

**Purpose:** Update all repositories, produce structured output, close the task.

**Steps:**
1. Update `TEST_REGISTRY.md` — set status to PASSING/FAILING for all tests run
2. Update `RULES.md` — add any new rules introduced by this task
3. Update `API_REGISTRY.md` — add any new APIs used
4. Append to `CHANGELOG.md` — one CL-XXX entry following the format in Section 3.3
5. Append to `AUDIT_LOG.md` — one AL-XXX entry following the format in Section 3.5
6. Fill in the ACTUALS section of `TASK_CONTRACT.yaml`
7. Verify no planning files in `docs/plans/` are in the git staging area

**Phase 5 Checklist (all must be YES before submission):**
- [ ] TEST_REGISTRY.md updated
- [ ] RULES.md updated (if new rules added)
- [ ] API_REGISTRY.md updated (if new APIs used)
- [ ] CHANGELOG.md entry appended (CL-XXX)
- [ ] AUDIT_LOG.md entry appended (AL-XXX)
- [ ] TASK_CONTRACT.yaml ACTUALS section filled
- [ ] `docs/plans/` files NOT in git staging
- [ ] `git_safe_verified: true` in TASK_CONTRACT ACTUALS

---

## SECTION 5 — ESCALATION PROTOCOL

Three tiers. The agent does not exercise judgment about which tier applies — it applies the tier defined by the situation.

| Tier | Trigger | Action | Wait For |
|---|---|---|---|
| **STOP** | Ambiguity in architecture or structure; missing source document; security violation found; GOV-X-001 triggered; project root not found | Halt all work immediately. Write escalation note to AUDIT_LOG.md. Notify owner. | Explicit written approval from owner |
| **CLARIFY** | Implementation ambiguity within a bounded task; two valid approaches with different trade-offs; missing test acceptance criteria | Document the question and the two options in TASK_CONTRACT under `open_issues`. Continue non-blocked work if any. | Owner response before proceeding on blocked item |
| **EXECUTE** | Task is fully specified, all source documents available, no ambiguity | Proceed through phases. Log all actions in AUDIT_LOG.md. | Nothing — proceed |

**What agents must NOT do:**
- Make an architectural assumption and proceed (STOP, not EXECUTE)
- Choose between two approaches without flagging (CLARIFY, not EXECUTE)
- Invent a folder structure not in Section 1.2 (STOP)
- Create a file outside the project root (STOP)

---

## SECTION 6 — GATE COMPLIANCE REPORTS & TASK SELF-MANAGEMENT

### 6.1 The Gate Model

Claude Code produces a **Gate Compliance Report** at the end of every phase. The report is shown to Niteen in the Claude Code UI. Nothing proceeds until Niteen explicitly confirms.

**Two types of gate confirmation Niteen gives:**
- **"confirmed"** — phase report accepted, proceed to next phase within the same task
- **"approved"** or **"approved with changes: [X]"** — SPEC for the next task accepted (with any corrections noted), begin Phase 1 of the next task

Niteen never needs to manually create, copy, or fill a TASK_CONTRACT. Claude Code handles all of that from TC-002 onward. TC-001 SPEC is pre-filled in the template (see `docs/protocol/active/TASK_CONTRACT.yaml`).

---

### 6.2 Per-Phase Gate Report Format

Produced after each of the 5 phases. Claude Code does not proceed to the next phase until Niteen replies "confirmed."

```markdown
## GATE COMPLIANCE REPORT — Phase [N]: [Phase Name]
**Task:** TC-XXX — [Task Name]
**Date:** YYYY-MM-DD
**Agent:** Claude Code

### Phase Checklist
| # | Checklist Item | Status | Notes |
|---|---------------|--------|-------|
| 1 | [Item from phase checklist] | ✅ PASS / ❌ FAIL / ⚠️ PARTIAL | [Detail if not PASS] |
| 2 | ... | ... | ... |

### What Was Done This Phase
- [Concrete action 1 — file created/read/tested/etc.]
- [Concrete action 2]

### Test Status (if tests run this phase)
| Test ID | Name | Result |
|---------|------|--------|
| T-XXX | ... | ✅ PASSING / ❌ FAILING |

### Gate Result
**[PASS — ready for Phase N+1]**
OR
**[FAIL — blocked on: (specific item). Owner action needed: (what decision/input is required)]**

---
*Awaiting your "confirmed" to proceed to Phase [N+1].*
```

---

### 6.3 Full Task Compliance Report (Phase 5 — Handoff)

At Phase 5 the report expands to cover the full task. Produced before SPEC-DRAFT for the next task.

```markdown
## FULL TASK COMPLIANCE REPORT — TC-XXX: [Task Name]
**Date:** YYYY-MM-DD
**Agent:** Claude Code

### Phase Summary
| Phase | Result | Key Outcome |
|-------|--------|-------------|
| 1 — ANCHOR | ✅ PASS | [X files read, Y dependencies verified] |
| 2 — TEST-FIRST | ✅ PASS | [X tests registered, all FAILING before impl — confirmed] |
| 3 — IMPLEMENTATION | ✅ PASS | [X files created, Y files modified] |
| 4 — REVIEW | ✅ PASS | [Full suite: X/X passing, 0 regressions] |
| 5 — HANDOFF | ✅ PASS | [All repos updated, git scan clean] |

### Files Created / Modified
| File | Action | Description |
|------|--------|-------------|
| `core/gateway.py` | Created | LiteLLMGateway class with failover chain |
| `TEST_REGISTRY.md` | Modified | Added T-GAT-C-001 through T-GAT-E-002 |
| ... | ... | ... |

### Test Results
| Test ID | Name | Result |
|---------|------|--------|
| T-GAT-C-001 | Gemini Flash success | ✅ PASSING |
| ... | ... | ... |
| **Full suite total** | | **X/X passing — 0 regressions** |

### Rules
| Status | Rule IDs |
|--------|---------|
| Followed | [list all rules referenced in this task] |
| New rules added | [Rule ID: description] / None |

### Security Compliance
| Check | Result |
|-------|--------|
| No secrets in committed files | ✅ CLEAN / ❌ VIOLATIONS |
| `.env` in `.gitignore` | ✅ VERIFIED |
| `.env.example` up to date | ✅ VERIFIED |

### Repositories Updated
| File | Updated? |
|------|---------|
| TEST_REGISTRY.md | ✅ Yes |
| CHANGELOG.md | ✅ CL-XXX appended |
| AUDIT_LOG.md | ✅ AL-XXX appended |
| API_REGISTRY.md | ✅ Yes / N/A — no new APIs |
| RULES.md | ✅ Yes / N/A — no new rules |

### Completion Gates
| Gate | Status |
|------|--------|
| All required tests passing | ✅ / ❌ |
| No regressions introduced | ✅ / ❌ |
| Git scan clean | ✅ / ❌ |
| All 5 phase checklists complete | ✅ / ❌ |
| TASK_CONTRACT ACTUALS filled | ✅ / ❌ |

### Overall Result: **TC-XXX [COMPLETE / INCOMPLETE]**

[If INCOMPLETE: specific items outstanding and what owner must resolve]
```

---

### 6.4 SPEC-DRAFT for Next Task (produced immediately after Full Task Compliance Report)

Once the full task compliance report is shown, Claude Code immediately proposes the SPEC for the next task (TC-XXX+1). Claude Code derives this from the version sequence in MASTER_PLAN.md Section 14 (CHANGELOG version plan).

This is presented **in the same message** as the full task compliance report, clearly separated.

```markdown
---

## PROPOSED SPEC — Next Task: TC-XXX+1: [Next Task Name]

*Derived from MASTER_PLAN.md version [vX.X.X]. Review and reply "approved" or "approved with changes: [your corrections]".*

| Field | Proposed Value |
|-------|---------------|
| **task_id** | TC-XXX+1 |
| **task_name** | [e.g. "Implement LiteLLM Gateway"] |
| **assigned_to** | Claude Code |
| **context_why** | [Why this task matters in the system — what it unblocks] |
| **phase_scope** | TEST → HANDOFF |
| **depends_on** | TC-XXX (just completed) |

**Source documents Claude Code will read in Phase 1:**
- MASTER_PLAN.md, RULES.md, CHANGELOG.md, TEST_REGISTRY.md, API_REGISTRY.md
- [Any task-specific documents]

**Files in scope (Claude Code may only create/modify these):**
- [Exact list derived from MASTER_PLAN folder structure]

**Files forbidden:**
- .env, MASTER_PLAN.md, AGENT_EXECUTION_PROTOCOL.md
- [Any files belonging to other tasks]

**Tests required (must be PASSING before handoff):**
- [Test IDs from TEST_REGISTRY.md relevant to this task's modules]

**Acceptance criteria:**
- [Binary pass/fail conditions]

---
*Reply "approved" to begin TC-XXX+1 Phase 1, or "approved with changes: [corrections]" to amend before starting.*
```

---

### 6.5 Owner Response Options

| Niteen's Reply | What Claude Code Does |
|----------------|----------------------|
| `"confirmed"` | Proceeds to next phase within the current task |
| `"approved"` | Accepts SPEC-DRAFT as-is, writes it to `docs/protocol/active/TASK_CONTRACT.yaml`, archives previous contract, begins Phase 1 |
| `"approved with changes: [X]"` | Applies Niteen's corrections to the SPEC, shows corrected version, waits for final "approved" |
| Specific feedback on a FAIL | Addresses the gap, re-runs the relevant check, re-presents the report |
| `"stop"` | Halts all work, raises STOP-tier escalation, awaits instructions |

---

### 6.6 What Claude Code Does Autonomously (No Owner Input Needed)

- Archives the completed TASK_CONTRACT to `docs/protocol/archive/TC-XXX_[task_name]_COMPLETED.yaml`
- Writes the approved SPEC into `docs/protocol/active/TASK_CONTRACT.yaml`
- Advances CHANGELOG, TEST_REGISTRY, AUDIT_LOG, RULES, API_REGISTRY
- Manages the `docs/plans/` working files
- Increments task IDs (TC-001 → TC-002 → ...)

**Claude Code never does autonomously:**
- Start a new phase without owner "confirmed"
- Start a new task without owner "approved" on the SPEC
- Make a structural change (GOV-X-001 — always requires owner approval)

---

## SECTION 7 — OUTPUT EXAMPLES

### Example: Well-Formed TASK_CONTRACT.yaml (SPEC + ACTUALS)
See `TASK_CONTRACT.yaml` in this folder for the complete template.

### Example: Well-Formed CHANGELOG Entry
```markdown
## [CL-003] — 2026-06-16 — COMPLETED

**Type:** FEATURE
**Author:** Claude Code
**Task ID:** TC-003
**Status:** COMPLETED

### Summary
Implemented LiteLLM gateway (`core/gateway.py`) with Gemini 2.5 Flash as primary,
Flash-Lite and Mistral as fallbacks, daily token tracking in `logs/token_usage.json`,
and LangSmith trace injection. Fixed three bugs from LITELLM_SETUP.md: variable name
mismatch, missing provider prefixes, and missing logs directory creation.

### Files Affected
- `core/gateway.py` — Created: LiteLLMGateway class with failover chain
- `tests/test_gateway.py` — Created: T-GAT-C-001, T-GAT-E-001, T-GAT-N-001, T-GAT-E-002
- `TEST_REGISTRY.md` — Updated: 4 new test cases registered
- `docs/api_registry/API_REGISTRY.md` — Updated: Confirmed API-GEMINI-001/002, API-MISTRAL-001

### Rules Added/Modified
- None (existing rules sufficient)

### Tests Added/Modified
- T-GAT-C-001 — PASSING
- T-GAT-E-001 — PASSING
- T-GAT-N-001 — PASSING
- T-GAT-E-002 — PASSING

### Dependencies
- Depends on: CL-002 (environment setup)
- Blocks: CL-004 (orchestration layer requires gateway)

### Rollback
Delete `core/gateway.py`; restore prior TEST_REGISTRY.md entries to PENDING.

### Owner Approval
- [x] Approved by Niteen — 2026-06-16
```

### Example: Well-Formed Audit Log Entry
```markdown
## [AL-003] — 2026-06-16 09:14 — Agent: Antigravity

**Session Task:** TC-003
**Phase Executed:** ANCHOR → TEST → IMPL → REVIEW → HANDOFF

| Action | File / Resource | Result |
|---|---|---|
| READ | MASTER_PLAN.md | OK |
| READ | RULES.md | OK — 10 active rules noted |
| READ | CHANGELOG.md | OK — CL-002 most recent |
| READ | TEST_REGISTRY.md | OK — T-ENV-C-001 PASSING noted |
| READ | API_REGISTRY.md | OK — API-GEMINI-001 noted as primary |
| READ | core/ directory | OK — gateway.py does not yet exist |
| READ | LITELLM_SETUP.md | OK — 3 bugs identified, documented |
| CREATED | core/gateway.py | OK |
| CREATED | tests/test_gateway.py | OK |
| MODIFIED | TEST_REGISTRY.md | Added T-GAT-C-001, T-GAT-E-001, T-GAT-N-001, T-GAT-E-002 |
| RAN TEST | T-GAT-C-001 | PASSING |
| RAN TEST | T-GAT-E-001 | PASSING |
| RAN TEST | T-GAT-N-001 | PASSING |
| RAN TEST | T-GAT-E-002 | PASSING |
| RAN TEST | Full suite | All 6 tests PASSING — no regressions |
| GIT SCAN | All modified files | CLEAN |
| APPENDED | CHANGELOG.md | CL-003 |
| APPENDED | AUDIT_LOG.md | AL-003 (this entry) |
```

---

## SECTION 8 — QUICK REFERENCE CARD

```
╔══════════════════════════════════════════════════════════════════╗
║           AGENT EXECUTION PROTOCOL — QUICK REFERENCE            ║
╠══════════════════════════════════════════════════════════════════╣
║  BEFORE ANYTHING: Read MASTER_PLAN → RULES → CHANGELOG → TESTS  ║
╠══════════════════════════════════════════════════════════════════╣
║  PHASE 1 ANCHOR   → Read everything. Check dependencies.         ║
║  PHASE 2 TEST     → Write tests FIRST. They must FAIL.           ║
║  PHASE 3 IMPL     → Code to pass tests. Draft→Verify→Critique.   ║
║  PHASE 4 REVIEW   → Full suite. Downstream check. Secret scan.   ║
║  PHASE 5 HANDOFF  → Update all repos. Fill ACTUALS. Log it.      ║
╠══════════════════════════════════════════════════════════════════╣
║  STOP if:   No project root / secret in file / arch ambiguity    ║
║  CLARIFY if: Two valid approaches / missing acceptance criteria   ║
║  EXECUTE if: Fully specified, no ambiguity                        ║
╠══════════════════════════════════════════════════════════════════╣
║  NEVER:  Hardcode secrets / Create files outside project root     ║
║          Skip phases / Overwrite without reading first            ║
║          Change architecture without owner approval               ║
╚══════════════════════════════════════════════════════════════════╝
```
