# System Development Plan: Automated JIT & JIC AI Newsletter
## Master Reference Document — Version 6.2
**Author:** Niteen Tomar (AI PM) | **Status:** Ready for Claude Code Implementation  
**Date:** 2026-06-15 | **Last Updated:** 2026-06-15 (v6.2 corrections)  
**Repository:** ai-aggregator-system (GitHub, private)

---

## VERSION HISTORY

| Version | Date | Change Summary |
|---------|------|---------------|
| 6.1 | 2026-06-15 | Initial consolidated plan (V1–V5 merge + June 2026 additions) |
| 6.2 | 2026-06-15 | Corrections from first Antigravity run: LITELLM_SETUP.md bugs fixed, folder structure aligned with AGENT_EXECUTION_PROTOCOL, Section 17 (Handoff) rewritten, ANTIGRAVITY_CONTROL_FRAMEWORK.md retired |
| 6.3 | 2026-06-15 | Implementing agent switched from Google Antigravity to Claude Code (CLI). Gate compliance report model added: Claude Code produces a Gate Compliance Report after each phase; Niteen reviews and confirms before next phase begins. |

---

## SECTION 0 — BEFORE YOU READ THIS DOCUMENT

This document is the single source of truth for building the Daily JIT/JIC Newsletter system. It consolidates all prior versions (V1–V5) and adds new requirements from the user's June 2026 deliberation. Every section is written to be read and acted on by the implementing agent (Claude Code). No section is informational-only; every requirement has an implementation obligation attached to it.

**Development Environment:** Claude Code (Niteen's IDE — included in Google AI Pro membership). Claude Code orchestrates multi-agent workflows powered by Gemini and provides the agentic development surface for building this system.

**⚠️ MANDATORY BEFORE ANY WORK BEGINS**  
The implementing agent MUST read `AGENT_EXECUTION_PROTOCOL.md` before this document. The protocol defines the behavioral contract (5-phase execution, escalation tiers, phase checklists) that governs how this specification is implemented. MASTER_PLAN.md is the *what*; AGENT_EXECUTION_PROTOCOL.md is the *how*. Both are required.

**How the implementing agent must use this document:**
1. Read `AGENT_EXECUTION_PROTOCOL.md` first (mandatory). Then read this document in full before writing a single line of code.
2. Each task is assigned via a filled `TASK_CONTRACT.yaml` — do not start a task without a completed SPEC section in the contract.
3. Check existing files/modules before creating new ones — always search first.
4. Follow the TDD protocol: write the test file before writing the implementation file.
5. If a structural change is required that is not in this document, STOP and escalate per the protocol's GOV-X-001 rule. Do not proceed.
6. Update `CHANGELOG.md` for every version increment.
7. Update `tests/TEST_REGISTRY.md` for every new or modified test.

---

## SECTION 1 — EXECUTIVE SUMMARY

| Dimension | Definition |
|-----------|-----------|
| **System Name** | Daily JIT/JIC AI Newsletter |
| **Core Purpose** | Autonomous daily pipeline that delivers Top 5 JIT + Top 5 JIC AI news topics and one structured deep-dive JIC lesson to Niteen's email inbox every morning |
| **Primary User** | Niteen Tomar — AI Product Manager wanting daily structured AI/ML learning |
| **Stack Philosophy** | Free-tier only, deterministic where possible, modular for swap-ability, Zero Trust by default |
| **Development Agent** | Claude Code (CLI) — implementing agent; Niteen manages gates via Gate Compliance Reports in Claude desktop |
| **Orchestration** | LangChain ReACT agent — the runtime agent inside the newsletter pipeline that runs every morning |
| **LLM** | Gemini 2.5 Flash (primary, free tier) → fallback chain: Gemini 2.5 Flash-Lite → Mistral-7B-Instruct (free) → Ollama local |
| **LLM Gateway** | LiteLLM proxy (self-hosted, free) — abstraction layer for all model calls |
| **Tracing** | LangSmith free tier |
| **Database** | SQLite (local) — append-only for history ledger; JSON files for topic pool and rules |
| **Frontend** | Streamlit dashboard (local, single-page) |
| **Scheduler** | macOS `launchd` plist (cron-style, runs daily at 7:00 AM local time) |
| **Email Delivery** | Gmail SMTP via App Password (free); fallback: SendGrid free tier |
| **Search** | Tavily API (free tier, 1000 req/month) → fallback: DuckDuckGo via `duckduckgo-search` Python lib |
| **Version Control** | GitHub (private repo); `.env` never committed |

---

## SECTION 2 — SYSTEM ARCHITECTURE

### 2.1 High-Level Architecture Diagram (Text)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         macOS launchd (7:00 AM)                     │
│                         Triggers: main.py                           │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GATEWAY LAYER (gateway.py)                       │
│         LiteLLM Proxy — Token tracking, limit enforcement,          │
│         model failover routing, LangSmith trace injection           │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                ORCHESTRATION LAYER (orchestration.py)               │
│     LangChain ReACT Agent — max_iterations=5, tool dispatcher       │
│     ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│     │ JIT Sub-Agent│  │ JIC Sub-Agent│  │ Daily Lesson Agent   │   │
│     │ (news fetch) │  │ (news fetch) │  │ (topic pool → 3A–3I) │   │
│     └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
└────────────┼─────────────────┼────────────────────┼────────────────┘
             │                 │                      │
             ▼                 ▼                      ▼
┌────────────────────────────────────────────────────────────────────┐
│                  TOOL LAYER (MCP-style tool wrappers)              │
│  ┌──────────────────┐  ┌─────────────────┐  ┌───────────────────┐ │
│  │ tavily_search()  │  │query_history()  │  │ get_next_topic()  │ │
│  │ DuckDuckGo fallb.│  │ check_cooldown()│  │ mark_topic_done() │ │
│  └──────────────────┘  └─────────────────┘  └───────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
             │                 │                      │
             ▼                 ▼                      ▼
┌────────────────────────────────────────────────────────────────────┐
│              DATA LAYER (database/ + config/)                      │
│  ledger.db (SQLite)     topic_pool.json    rules_repo.json         │
│  - historical_ledger    - ordered list     - active rules          │
│  - gateway_telemetry    - pointer index    - priorities            │
│  - system_exceptions    - user-added       - conflict map          │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│            SYNTHESIS LAYER (synthesis.py + templates/)             │
│   Jinja2 renders email_template.html with structured content       │
│   Validates HTML output against schema before sending              │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│              DELIVERY LAYER (delivery.py)                          │
│   Gmail SMTP (App Password) → SendGrid SMTP fallback               │
│   Sends HTML email to you@example.com                        │
└────────────────────────────────────────────────────────────────────┘

SIDE CHANNEL — ALWAYS RUNNING:
┌──────────────────────────────────────────────────────────────────┐
│  OBSERVABILITY: LangSmith traces + local logs (logs/)            │
│  FRONTEND: Streamlit app.py — dashboard for metrics/query/admin  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Interaction Contracts

All components communicate through **defined Python interfaces**, not direct imports between modules. This is the modular contract rule: if you swap `gateway.py` for a different LLM gateway, no other file should need editing except the gateway's own interface file.

| From Component | To Component | Interface Method | Contract |
|---------------|-------------|-----------------|---------|
| `orchestration.py` | `gateway.py` | `llm_call(prompt, model_name)` → `dict` | All LLM calls go through gateway only. Returns `{response, model_used, tokens_used, cost, timestamp}`; callers that only need the text use `result["response"]`. (Corrected 2026-06-16, TC-002 Phase 1 — originally documented as `→ str`; `model_name` is accepted for future flexibility but the gateway always drives failover from its own internal chain, never from caller input.) |
| `orchestration.py` | `tools/*.py` | `tool.run(input: dict)` → `dict` | ReACT tool interface (LangChain Tool class) |
| `tools/search.py` | External API | `search(query, n=5)` → `list[dict]` | Returns list of {title, url, summary, date} |
| `tools/memory.py` | `database/ledger.db` | `query_history(topic)` → `dict` | Returns {status, last_covered, delta_days} |
| `synthesis.py` | `config/email_template.html` | `render(context: dict)` → `str` | Returns validated HTML string |
| `delivery.py` | Gmail SMTP | `send_email(html: str, to: str)` → `bool` | Returns True on success |
| `app.py` | `database/ledger.db` | Direct SQLite read-only queries | Dashboard reads only |

---

## SECTION 3 — FOLDER STRUCTURE (CANONICAL)

This structure is **frozen post-deployment**. Structural changes during development require user approval (GOV-001). Changes post-deployment are prohibited (GOV-002).

```
ai-aggregator-system/
│
├── .env                          # LOCAL ONLY — never committed to git
├── .env.example                  # Committed — shows required keys with empty values
├── .gitignore                    # Bars: .env, __pycache__, *.db, *.pyc, .DS_Store, logs/, docs/protocol/active/
├── README.md                     # Setup guide, deployment steps, API key sources
├── requirements.txt              # All Python dependencies with pinned versions
├── main.py                       # Entry point — orchestrates full daily pipeline
├── MASTER_PLAN.md                # THIS DOCUMENT — architectural source of truth (root, NOT docs/)
├── RULES.md                      # Central rule repository (root)
├── TEST_REGISTRY.md              # Central test case registry (root — see Section 10)
├── CHANGELOG.md                  # Version history (root)
├── AUDIT_LOG.md                  # Immutable agent session log (root)
│
├── config/
│   ├── rules_repo.json           # Central rule engine (see Section 8) — runtime rules for pipeline
│   ├── litellm_config.yaml       # LiteLLM proxy model list and fallback order
│   ├── email_template.html       # Jinja2 HTML template for email output
│   └── topic_pool.json           # Ordered list of JIC lesson topics + pointer
│
├── core/
│   ├── orchestration.py          # LangChain ReACT agent setup and pipeline runner
│   ├── gateway.py                # LiteLLM proxy wrapper, token tracker, failover logic
│   ├── synthesis.py              # Jinja2 rendering + HTML schema validation
│   └── delivery.py               # Email sending via Gmail SMTP / SendGrid fallback
│
├── tools/
│   ├── __init__.py
│   ├── search.py                 # Tavily search + DuckDuckGo fallback
│   ├── memory.py                 # MCP-style DB tool: cooldown check, history query
│   └── topic_manager.py          # Get next lesson topic, mark complete, add topics
│
├── database/
│   ├── ledger.db                 # SQLite: historical_ledger, gateway_telemetry, exceptions (not committed)
│   └── schema.sql                # SQL schema for all tables (used in setup + tests)
│
├── frontend/
│   └── app.py                    # Streamlit dashboard (metrics, query, topic manager)
│
├── logs/                         # NOT committed to git
│   ├── run_YYYY-MM-DD.log        # Daily execution log (structured JSON lines)
│   ├── token_usage.json          # LiteLLM token tracking file (auto-created by gateway.py)
│   └── audit_YYYY-MM-DD.log      # Audit trail: test runs, changes, rule firings
│
├── tests/
│   ├── conftest.py               # Pytest fixtures: mock LLM, mock search, in-memory DB
│   ├── mocks/
│   │   ├── mock_llm_responses.json   # Deterministic LLM response fixtures
│   │   └── mock_search_results.json  # Deterministic search result fixtures
│   ├── test_units.py             # Unit tests for all core functions
│   ├── test_integration.py       # End-to-end pipeline tests (mocked externals)
│   └── test_formatting.py        # HTML output schema validation tests
│
├── scripts/
│   ├── setup_db.py               # Initializes ledger.db from schema.sql
│   ├── setup_launchd.py          # Creates/installs macOS launchd plist
│   └── check_env.py              # Validates all required .env keys are present
│
├── docs/
│   ├── protocol/
│   │   ├── AGENT_EXECUTION_PROTOCOL.md   # Behavioral contract for all agents (read-only)
│   │   ├── active/
│   │   │   └── TASK_CONTRACT.yaml        # Active task contract (NOT committed to git)
│   │   └── archive/
│   │       └── (completed TASK_CONTRACT files — NOT committed to git)
│   ├── api_registry/
│   │   └── API_REGISTRY.md              # Registry of all external APIs used
│   ├── plans/                           # AI-generated implementation plans (NOT committed to git)
│   ├── ARCHITECTURE.md                  # Architecture notes
│   └── API_KEYS_GUIDE.md                # Where to get each free API key (no actual keys)
│
└── com.niteen.ai-aggregator.plist       # macOS launchd scheduler config
```

> **Note (v6.2):** MASTER_PLAN.md, RULES.md, TEST_REGISTRY.md, CHANGELOG.md, and AUDIT_LOG.md live at the **project root**, not under `docs/`. This aligns with AGENT_EXECUTION_PROTOCOL.md Section 1.2 and ensures the implementing agent's mandatory Phase 1 reads resolve correctly.

---

## SECTION 4 — FREE-TIER API STRATEGY & FALLBACK CHAIN

### 4.1 LLM Providers (Free Tier Only)

> **Note — April 2026 change:** Gemini 1.5 Pro and 1.0 Pro are no longer available on the free API tier. Only Flash and Flash-Lite models retain free access. The table below reflects current (June 2026) free-tier availability.

| Priority | Model | Free Tier Limits | Why |
|---------|-------|-----------------|-----|
| 1 — Primary | Gemini 2.5 Flash | 1,500 req/day, free | Best free model available; fast, capable, sufficient for one daily run |
| 2 — Fallback 1 | Gemini 2.5 Flash-Lite | 1,500 req/day, free | Same API key, lighter/cheaper; same quota pool as Flash |
| 3 — Fallback 2 | Mistral-7B-Instruct (La Plateforme) | Free tier | No Google dependency; open weights; separate quota |
| 4 — Emergency | Ollama local (llama3.2:3b) | Unlimited — runs on CPU locally | Zero cost, zero internet needed; last resort if all APIs fail |

**Important note:** Claude Code uses its own model for development work. The newsletter pipeline at runtime uses the free Gemini API — these are separate. The pipeline must use `GOOGLE_API_KEY` from `.env`, never any key belonging to the development environment.

**Rule R-002:** If LiteLLM detects token usage ≥ 95% of primary model's daily free limit → automatically route to next fallback in order. Log the switch in `gateway_telemetry_logs`. Do not fail the pipeline.

### 4.2 Search Providers (Free Tier Only)

| Priority | Provider | Free Tier | Notes |
|---------|---------|----------|-------|
| 1 | Tavily API | 1,000 req/month | Best structured results for AI news |
| 2 | DuckDuckGo (`duckduckgo-search` lib) | Unlimited (unofficial) | No API key needed; rate-limit cautiously |

### 4.3 Email Providers

| Priority | Provider | Free Tier | Notes |
|---------|---------|----------|-------|
| 1 | SendGrid | 100 emails/day free | Requires account + verified sender. SENDGRID_API_KEY + TARGET_EMAIL env vars. |

> **Updated 2026-06-17 (TC-006):** Gmail SMTP removed — GMAIL_APP_PASSWORD not available. SendGrid is the sole delivery provider. R-006 retry logic applies to SendGrid only (3 attempts, exponential backoff via tenacity); no fallback provider.

### 4.4 LLM Gateway — LiteLLM

LiteLLM runs as a **local proxy process** (`litellm --config litellm_config.yaml --port 8000`). All LLM calls in the codebase hit `http://localhost:8000` — never a provider's URL directly. This means:
- Swapping from Gemini to any other provider = edit `litellm_config.yaml` only, zero code changes.
- Token counts, costs, and request logs are captured by LiteLLM automatically.
- LangSmith receives traces via LiteLLM's callback integration.

**Modular gateway swap rule:** If switching from LiteLLM to Helicone or Portkey in future, only `gateway.py` and `litellm_config.yaml` change. All other code stays the same because it talks to `gateway.py`'s interface, not LiteLLM directly.

**⚠️ Known Bugs in LITELLM_SETUP.md Reference Code (v6.2 — implementing agent must fix these):**

The reference code in `LITELLM_SETUP.md` has four confirmed bugs. The implementing agent must apply all four fixes in `core/gateway.py`:

| Bug # | Location | Bug | Fix |
|-------|----------|-----|-----|
| BUG-001 | `_check_token_limit()` line ~177 | Attribute mismatch: uses `self.daily_token_limit_gemini` but `__init__` sets `self.daily_limit_gemini` | Standardize to `self.daily_limit_gemini` and `self.daily_limit_mistral` throughout |
| BUG-002 | `model_chain` list in `__init__` | Missing LiteLLM provider prefix — `"gemini-2.5-flash"` will fail; LiteLLM requires `"gemini/gemini-2.5-flash"` | Change all model strings to include provider prefix: `"gemini/gemini-2.5-flash"`, `"gemini/gemini-2.5-flash-lite"`, `"mistral/mistral-7b-instruct-v0.2"` |
| BUG-003 | `_log_token_usage()` | Writes to `logs/token_usage.json` without ensuring `logs/` directory exists — will crash on first run | Add `os.makedirs("logs", exist_ok=True)` before the first file write |
| BUG-004 | `LITELLM_SETUP.md` file itself | Real API keys are hardcoded in the `.env` example block (Mistral key and LangSmith key) | **Rotate both keys immediately.** The file is a guide only — implementing agent must use `.env` exclusively and never reference LITELLM_SETUP.md key values |

Test cases T-GAT-C-001 through T-GAT-E-002 in the TEST_REGISTRY must cover all four of these bugs as their primary acceptance criteria.

---

## SECTION 5 — CORE PIPELINE LOGIC

### 5.1 Daily Pipeline Flow (main.py)

```python
# Pseudocode — actual implementation in main.py
def run_daily_pipeline():
    # Step 1: Environment validation (ZT-001)
    check_env_vars()  # Fatal crash if any key missing
    
    # Step 2: Token budget check (R-002)
    if gateway.get_token_usage_pct() >= 0.95:
        log_warning("Approaching token limit — routing to fallback")
        gateway.set_primary_model("fallback_1")
    
    # Step 3: Run JIT sub-agent (max 5 iterations)
    jit_results = run_jit_agent()  # Returns list of ≤5 items
    
    # Step 4: Run JIC sub-agent (max 5 iterations)
    jic_results = run_jic_agent()  # Returns list of ≤5 items
    
    # Step 5: Get today's lesson topic
    lesson_topic = topic_manager.get_next_topic()
    lesson_content = run_lesson_agent(lesson_topic)  # Returns structured dict
    
    # Step 6: Render HTML
    html_output = synthesis.render(jit_results, jic_results, lesson_content)
    
    # Step 7: Validate HTML output (R-003)
    if not synthesis.validate(html_output):
        log_error("HTML validation failed — retrying synthesis")
        html_output = synthesis.render_with_retry(...)
    
    # Step 8: Send email
    success = delivery.send_email(html=html_output, to=os.getenv("TARGET_EMAIL"))
    
    # Step 9: Persist to ledger (append-only)
    db.append_run_record(jit_results, jic_results, lesson_topic, success)
    topic_manager.mark_topic_done(lesson_topic)
```

### 5.2 JIT/JIC Agent Logic (7-Day Cooldown)

```
FOR each candidate topic from search results (sorted by recency/relevance):
    result = tools.memory.query_history(topic_name)
    IF result.status == "Found" AND result.delta_days < 8:
        SKIP this topic (7-day suppression active)
        CONTINUE to next candidate
    ELSE IF result.status == "Found" AND result.delta_days >= 8:
        INCLUDE (resurgent topic — document new developments)
    ELSE:  # "Not Found"
        INCLUDE (novel topic)
    
    IF included_count == 5:
        BREAK
```

### 5.3 Graceful Degradation Rules

| Failure Scenario | System Response |
|-----------------|----------------|
| Tavily API fails | Switch to DuckDuckGo; log the switch |
| DuckDuckGo also fails | Skip JIT/JIC news; send lesson-only email; log |
| Primary LLM hits 95% limit | Switch to fallback model automatically |
| All LLM fallbacks exhausted | Skip that pipeline section; log CRITICAL error |
| Email send fails (SendGrid) | Retry 3 times with exponential backoff (tenacity); log CRITICAL and return False on exhaustion — no fallback provider (R-006) |
| HTML validation fails | Retry synthesis once; if still failing, send raw text fallback |
| DB write fails | Log CRITICAL; do not crash (email already sent) |

---

## SECTION 6 — OUTPUT FORMAT SPECIFICATION

### 6.1 Email HTML Template Structure

The email is a **single HTML file** rendered by Jinja2 from `config/email_template.html`. Claude Code must implement this exact structure — no deviations without user approval.

```
[HEADER]
  Date | "Your Daily AI Learning Brief"
  
[SECTION A — CRITICAL SUMMARY BOX] (highlighted background)
  • Most critical JIT insight (1 sentence)
  • Most critical JIC insight (1 sentence)  
  • Today's lesson topic (1 sentence hook)

[SECTION B — TOP 5 JIT NEWS]
  <h2>Just-In-Time: What's Happening Now</h2>
  <table>
    | # | Topic | Source | Date | Why It Matters (1 sentence) |
    (5 rows max)
  </table>

[SECTION C — TOP 5 JIC NEWS]
  <h2>Just-In-Case: Foundational Concepts in News</h2>
  <table>
    | # | Topic | Source | Date | Core Insight (1 sentence) |
    (5 rows max)
  </table>

[SECTION D — DAILY JIC DEEP DIVE]
  <h2>Today's Lesson: [Topic Name]</h2>
  
  <h3>3A. What Is It</h3>
    [Bullet points — no paragraphs]
  
  <h3>3B. Intuition</h3>
    [Bullet points with analogy if helpful]
  
  <h3>3C. Key Research Papers</h3>
    <table> | Paper Title | Authors | Year | Core Contribution | </table>
  
  <h3>3D. Where It Applies</h3>
    [Bullet points — concrete production examples]
  
  <h3>3E. Current Maturity Status</h3>
    [One of: Experimental / Rapidly Developing / Production-Stable / Mature / Legacy]
    [Bullet points explaining the status]
  
  <h3>3F. Historical Context (vs Earlier JIC)</h3>
    [Bullet: supports / extends / contradicts — with specifics]
  
  <h3>3G. Authoritative Voices</h3>
    <table> | Name | Date | Summary of What They Said | Source | </table>
  
  <h3>3H. What's Coming Next</h3>
    [Bullet points — concrete forecasts, not vague guesses]
  
  <h3>3I. Glossary</h3>
    <table> | Term | Definition | </table>

[FOOTER]
  Run timestamp | Model used | Topics covered | Unsubscribe/Pause link
```

### 6.2 HTML Design Rules

- **No inline JavaScript.** Email clients block it.
- **Inline CSS only.** External CSS does not render in most email clients.
- **Max width 700px.** Mobile-readable.
- **Tables use `border-collapse: collapse`, `padding: 8px`.** Clean Notion-paste.
- **All bullet points use `<ul><li>` tags**, not dashes.
- **Color scheme:** White background, #1a1a2e headers, #e94560 accent, #f5f5f5 table alternating rows.
- **Source links** must be actual `<a href="...">` tags, not plain text.

---

## SECTION 7 — DAILY JIC LESSON TOPIC POOL

Topics are stored in `config/topic_pool.json` as an ordered list with a pointer index. System advances the pointer daily. User can add topics via Streamlit UI or by editing the JSON.

### 7.1 Initial Topic Pool (Ordered Curriculum)

```json
{
  "pointer": 0,
  "topics": [
    "Model Context Protocol (MCP) — Architecture and Client-Server Spec",
    "ReACT Reasoning Pattern — Reason + Act Loop for Agents",
    "Retrieval-Augmented Generation (RAG) — Architecture and Variants",
    "Transformer Architecture — Attention Mechanism Deep Dive",
    "Mixture of Experts (MoE) — Routing and Sparse Activation",
    "Vector Databases — Embeddings, Indexing, Similarity Search",
    "Knowledge Graphs — Structure, Querying, and LLM Integration",
    "Multi-Agent Orchestration — Patterns, Frameworks, Coordination",
    "LLM Evaluation — Benchmarks, RLHF, Evals Frameworks",
    "Fine-Tuning vs Prompt Engineering — When to Use Each",
    "ARIMA / SARIMA — Classical Time-Series Forecasting",
    "XGBoost for Tabular Data — Architecture, Use in Forecasting",
    "Diffusion Models — Architecture, Training, Applications",
    "Multimodal Models — Vision-Language Architecture (GPT-4V, Gemini)",
    "LLM Inference Optimization — KV Cache, Speculative Decoding, Quantization",
    "Agentic Planning — Plan-and-Solve, Tree of Thought, ReWOO",
    "Safety and Alignment — RLHF, Constitutional AI, DPO",
    "LLM Memory Systems — Short-term, Long-term, External Memory",
    "Actuarial AI Applications — Risk Pricing, Dynamic Underwriting with ML",
    "AI Product Management — Frameworks, Metrics, Build vs Buy",
    "Prompt Engineering — Chain of Thought, Few-Shot, System Prompts",
    "LangChain / LangGraph Architecture — Components and Patterns",
    "Embeddings Deep Dive — Sentence Transformers, OpenAI Embeddings",
    "Function Calling and Tool Use in LLMs — How Agents Use Tools",
    "Graph Neural Networks (GNNs) — Concepts and Applications"
  ]
}
```

### 7.2 LLM Reference Example — Daily Lesson Execution

```
[FORMATTING AGENT INSTRUCTION — DO NOT DEVIATE FROM THIS STRUCTURE]
Topic: Model Context Protocol (MCP)

3A. Definition bullets (3–5 points, one sentence each):
  • MCP is an open protocol standardizing how LLM applications expose tools and resources to agents.
  • It uses a client-server model: the LLM application is the client; tool providers are servers.
  • MCP servers expose three primitives: Resources (files/data), Tools (executable functions), Prompts (templates).

3C. Papers table — search for: "Anthropic MCP specification 2024", "tool use LLM papers"
  Format: | Title | Authors | Year | Contribution |

3G. Voices table — search for: "Sam Altman MCP", "Anthropic MCP announcement", 
     "developer reactions MCP open standard"
  Format: | Name | Date | Summary | Source URL |

3I. Glossary — must include: Client, Server, Resource, Tool, Prompt, Schema, stdio, HTTP+SSE
```

---

## SECTION 8 — CENTRAL RULE REPOSITORY

All rules are stored in `config/rules_repo.json`. The orchestration layer reads this file at startup. Rules can be toggled active/inactive without code changes.

| Rule ID | Component | Description | Active | Priority | Conflict Resolution | Best Practice |
|---------|-----------|-------------|--------|----------|--------------------|----|
| ZT-001 | Security | Fatal crash if any API key detected outside `.env` or found in tracked file | Yes | 1 (Highest) | Overrides all agent tasks — aborts instantly | Secret Isolation |
| ZT-002 | Security | Database connections: SELECT + INSERT only. No DROP/DELETE/ALTER | Yes | 1 (Highest) | Rejects and logs any payload attempting deletion | Least Privilege |
| ZT-003 | Security | Outbound calls to whitelisted domains only (Tavily, LiteLLM, LangSmith, Gmail) | Yes | 1 (Highest) | Drops unrecognized domain connections | Network Perimeter |
| R-001 | Orchestration | 7-day cooldown: suppress topics covered in last 7 days; allow on day 8 | Yes | 2 (High) | Overrides popularity signal; topic released on day 8 | Spaced Repetition |
| R-002 | LLM Gateway | Abort/switch model if token usage ≥ 95% of free-tier daily limit | Yes | 1 (Highest) | Triggers fallback chain; logs switch; never bills user | Cost Control |
| R-003 | Layout | Re-run synthesis if HTML output fails schema validation | Yes | 3 (Medium) | Retries once; sends text-only fallback if second failure | Output Quality |
| R-004 | Database | Append-only writes to `historical_ledger`. No UPDATE on past records | Yes | 1 (Highest) | Logs attempt and aborts write; does not crash pipeline | Immutable Ledger |
| R-005 | Orchestration | ReACT agent max_iterations=5. Hard stop — never allow infinite loops | Yes | 1 (Highest) | Graceful exit with partial results; logs truncation | Determinism |
| R-006 | Delivery | Retry email send 3 times with exponential backoff before switching provider | Yes | 2 (High) | Switch to SendGrid on 3rd Gmail failure | Reliability |
| GOV-001 | Governance | Structural changes during development require explicit user approval | Yes | 1 (Highest) | Freeze code generation until user confirms | Human-in-Loop |
| GOV-002 | Governance | Post-deployment: folder structure and module interfaces are frozen | Yes | 2 (High) | Block file ops creating unmapped directories | Architectural Stability |

---

## SECTION 9 — DEVELOPMENT DISCIPLINE & CODING STANDARDS

This section defines **how** the system must be built, not just what. The implementing agent must follow these standards on every file it creates or modifies.

### 9.A — Check Before Creating

**Before creating any new file or writing new code:**
1. Run `ls` / `Glob` to check if a file with that name already exists.
2. Run `Grep` to check if the function/class you're about to write already exists in an existing file.
3. If it exists: **extend the existing file**. Do not create a duplicate.
4. If it doesn't exist: confirm the new file's location matches the canonical folder structure (Section 3).

### 9.B — Code Compactness

- Functions: maximum 40 lines. If longer, split into sub-functions with clear names.
- Files: maximum 300 lines. If longer, split the module at a logical seam.
- No commented-out dead code in committed files.
- Imports: at top, grouped (stdlib → third-party → local), sorted alphabetically within groups.
- No magic numbers in code logic — define as named constants in a `constants.py` file.

### 9.C — Code Commentary Standards (Python)

Every Python file must have:
```python
"""
MODULE: <module_name>.py
PURPOSE: <one sentence — what this module does>
INPUTS: <what data/params it receives>
OUTPUTS: <what it returns or side effects>
DEPENDENCIES: <which other modules it imports from this project>
RULE REFERENCES: <which rules from Section 8 govern this module>
CHANGE LOG: <version | date | what changed | author>
"""
```

Every function must have a docstring:
```python
def query_history(topic: str) -> dict:
    """
    Check if a topic was covered in the last 7 days.
    
    Args:
        topic: The topic keyword string to look up.
    
    Returns:
        dict with keys: status ("Found"/"Not Found"), last_covered (ISO date or None),
        delta_days (int or None)
    
    Rule: R-001 (7-day cooldown)
    """
```

Inline comments for non-obvious logic:
```python
# R-001: Topic suppression window — skip if covered within 7 days
if delta_days < 8:
    continue
```

### 9.D — Dependency Impact Analysis (Before Any Change)

Before modifying any existing file, the implementing agent must explicitly document:

```
CHANGE IMPACT ANALYSIS
File to change: core/gateway.py
Change: Add Helicone as gateway option
Downstream dependencies:
  - core/orchestration.py calls gateway.llm_call() → interface unchanged ✓
  - tests/test_units.py has mock for gateway → mock needs updating ⚠
  - config/rules_repo.json has R-002 referencing gateway → rule unchanged ✓
  - requirements.txt → add helicone package ⚠
Tests to update: test_units.py::test_gateway_fallback
Tests to add: test_units.py::test_helicone_routing
Risk: Low — gateway.py uses facade pattern; other modules unaffected
```

This analysis must be written as a comment block at the top of the PR commit message or the change log entry.

### 9.E — Deterministic Over Probabilistic

- **Search queries** must be templated strings, not generated by LLM on the fly.
  - ✅ `f"Top AI model releases {today.strftime('%B %Y')}"` 
  - ❌ `llm.generate("write a search query for today's AI news")`
- **Cooldown calculations** use pure Python date arithmetic, not LLM judgment.
- **HTML rendering** uses Jinja2 template + structured data dict — LLM fills the data, Jinja2 builds the HTML.
- **LLM calls** are used only for: summarizing search results, generating 3A–3I content, writing the critical summary bullet.
- The LLM must never decide: which topics to include (rule-based), whether to send email (always send), what model to use next (gateway decides by rule).

### 9.F — Error Handling Pattern

Every external call (LLM, search, DB, email) must follow this pattern:

```python
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_search_api(query: str) -> list:
    try:
        result = tavily_client.search(query)
        logger.info(f"Search success: {query[:50]}")
        return result
    except TavilyRateLimitError:
        logger.warning("Tavily rate limit hit — switching to DuckDuckGo")
        return duckduckgo_search(query)  # Fallback (no retry needed here)
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise  # Let tenacity retry
```

### 9.G — Change Log Discipline

After every code change, update `docs/CHANGELOG.md` with:
- Version tag (semantic: vMAJOR.MINOR.PATCH)
- Date
- What changed (feature / bug / refactor / config)
- Which files were modified
- Which tests were added/modified
- Which rules from Section 8 were involved

### 9.H — New Test Requirements

For every new or modified function:
1. Write the test first (TDD: red → green → refactor).
2. Add the test to `tests/TEST_REGISTRY.md`.
3. Categorize it: Unit / Integration / Formatting, Category A (initial) or B (update).
4. The pipeline in `main.py` must not run if `pytest tests/` returns any failures.

---

## SECTION 10 — TEST-DRIVEN DEVELOPMENT (TDD) PROTOCOL

### 10.1 Test Registry (TEST_REGISTRY.md — initial seed)

| Test ID | File | Function | Category | Type | A/B | Status |
|---------|------|----------|----------|------|-----|--------|
| T-001 | test_units.py | test_cooldown_suppression | Unit | Logic | A | Pending |
| T-002 | test_units.py | test_cooldown_day8_release | Unit | Logic | A | Pending |
| T-003 | test_units.py | test_gateway_fallback_on_limit | Unit | Gateway | A | Pending |
| T-004 | test_units.py | test_env_var_missing_fatal | Unit | Security | A | Pending |
| T-005 | test_units.py | test_max_5_results_enforced | Unit | Logic | A | Pending |
| T-006 | test_units.py | test_topic_pointer_advances | Unit | Logic | A | Pending |
| T-007 | test_units.py | test_db_no_delete_allowed | Unit | Security | A | Pending |
| T-008 | test_integration.py | test_full_pipeline_mock | Integration | E2E | A | Pending |
| T-009 | test_integration.py | test_search_fallback_duckduckgo | Integration | Fallback | A | Pending |
| T-010 | test_integration.py | test_email_retry_sendgrid | Integration | Fallback | A | Pending |
| T-011 | test_formatting.py | test_html_output_has_required_sections | Formatting | Output | A | Pending |
| T-012 | test_formatting.py | test_html_tables_valid_structure | Formatting | Output | A | Pending |
| T-013 | test_formatting.py | test_3a_through_3i_all_present | Formatting | Output | A | Pending |

### 10.2 Mandatory Gating Rule

**No code is considered "done" until:**
1. All tests in TEST_REGISTRY.md pass (`pytest tests/ -v` returns 0 exit code).
2. `scripts/check_env.py` confirms all required environment variables are present.
3. A CHANGELOG.md entry exists for the change.
4. The relevant TEST_REGISTRY.md row is updated to "Passing".

### 10.3 API Mocking Strategy

All external calls are mocked in `tests/conftest.py` using `pytest-mock` and `responses` library. Mock files are static JSON in `tests/mocks/`:

```python
# conftest.py — shared fixtures
@pytest.fixture
def mock_llm():
    """Returns deterministic LLM responses from mock_llm_responses.json"""
    with open("tests/mocks/mock_llm_responses.json") as f:
        return json.load(f)

@pytest.fixture
def mock_search():
    """Returns deterministic search results from mock_search_results.json"""
    with open("tests/mocks/mock_search_results.json") as f:
        return json.load(f)

@pytest.fixture
def test_db():
    """Creates fresh in-memory SQLite instance for each test"""
    conn = sqlite3.connect(":memory:")
    with open("database/schema.sql") as f:
        conn.executescript(f.read())
    yield conn
    conn.close()
```

---

## SECTION 11 — OBSERVABILITY & TOKEN TRACKING

### 11.1 LangSmith Integration

LangSmith receives traces automatically when environment variable `LANGCHAIN_TRACING_V2=true` is set. No additional code needed beyond setting these env vars:

```
LANGCHAIN_API_KEY=<your langsmith free key>
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=daily-jit-jic-newsletter
```

### 11.2 LiteLLM Token Dashboard

LiteLLM exposes a dashboard at `http://localhost:4000/ui` (when running in proxy mode with `--ui`). This shows:
- Token usage per model per day
- Cost estimates
- Request count
- Fallback events

Data is also logged to `database/ledger.db → gateway_telemetry_logs`.

### 11.3 Streamlit Dashboard Panels

`frontend/app.py` provides these panels in a single-page layout:

**Panel 1 — Daily Run Metrics**
- Table: last 7 days of runs (date, JIT count, JIC count, lesson topic, model used, tokens used)
  > Note (2026-06-17, TC-008 scope): `status` (email delivered yes/no) removed — no delivery-status column exists in the current schema (`historical_ledger`, `gateway_telemetry_logs`, `system_exceptions`). Deferred to a future migration task requiring GOV-001 approval + ZT-002 review before any schema ALTER.
- Chart: token usage over time

**Panel 2 — Topic History & Cooldown Checker**
- Query box: enter a topic → see if it's in cooldown
- Table: last 30 covered topics with dates

**Panel 3 — Lesson Queue Manager**
- View current topic pool (ordered)
- Add new topic (appends to JSON)
- Reorder topics (drag-and-drop or move up/down buttons)
- Skip current topic

**Panel 4 — Error & Audit Log**
- Table: last 20 error log entries with severity
- Table: last 20 audit entries (test runs, rule firings, model switches)

**Panel 5 — SQL Query Console**
- Free-text SQL input (SELECT only — ZT-002)
- Results displayed as table
- Pre-built query templates (from Section 5 of Combined V4)

**Panel 6 — Email Template Preview**
- Renders current `config/email_template.html` in an iframe
- Edit button opens Streamlit text editor → saves back to file
- "Test Send" button sends preview email

---

## SECTION 12 — SECURITY (ZERO TRUST)

### 12.1 .env File (Never Committed)

```
# All keys must be present — check_env.py will fatal-crash if any are missing (ZT-001)

# LLM Providers
GOOGLE_API_KEY=
OPENAI_API_KEY=
MISTRAL_API_KEY=

# LLM Gateway
LITELLM_MASTER_KEY=
LITELLM_PORT=8000

# Observability
LANGCHAIN_API_KEY=
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=daily-jit-jic-newsletter

# Search
TAVILY_API_KEY=

# Email
GMAIL_APP_PASSWORD=
GMAIL_SENDER=you@example.com
SENDGRID_API_KEY=
TARGET_EMAIL=you@example.com

# Token Limits (customize these)
DAILY_TOKEN_LIMIT_GEMINI=900000
TOKEN_ALERT_THRESHOLD=0.95
```

### 12.2 .gitignore (Canonical)

```
.env
__pycache__/
*.pyc
*.pyo
database/*.db
logs/
.DS_Store
*.egg-info/
dist/
build/
.pytest_cache/
```

### 12.3 .env.example (Committed to Repo)

Same structure as `.env` but all values replaced with `<your_key_here>` placeholders. This file is committed so new developers know exactly what keys are needed.

---

## SECTION 13 — SCHEDULER (macOS launchd)

### 13.1 plist Configuration

File: `com.niteen.ai-aggregator.plist` (at project root during development; installed to `~/Library/LaunchAgents/` for production)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.niteen.ai-aggregator</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/PATH/TO/ai-aggregator-system/main.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>7</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/PATH/TO/ai-aggregator-system/logs/launchd_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/PATH/TO/ai-aggregator-system/logs/launchd_stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
```

### 13.2 Scheduler Management Commands

```bash
# Install (first time)
launchctl load ~/Library/LaunchAgents/com.niteen.ai-aggregator.plist

# Test run immediately
launchctl start com.niteen.ai-aggregator

# Stop
launchctl stop com.niteen.ai-aggregator

# Uninstall
launchctl unload ~/Library/LaunchAgents/com.niteen.ai-aggregator.plist

# Check status
launchctl list | grep ai-aggregator
```

These commands are also available via the Streamlit dashboard (Panel 1 — "Scheduler Control" buttons).

---

## SECTION 14 — CHANGE LOG TEMPLATE

File: `docs/CHANGELOG.md`

```markdown
# CHANGELOG

All changes to this system must be logged here before being considered complete.

## Format
### [vX.Y.Z] — YYYY-MM-DD
**Type:** Feature / Bug Fix / Refactor / Config / Test / Security
**Files Modified:** list
**Tests Added/Modified:** list (with TEST_REGISTRY.md IDs)
**Rules Involved:** list (from Section 8)
**Impact Analysis:** brief (who/what else could be affected)
**Status:** In Progress / Complete / Rolled Back

---

## [v1.0.0] — Pending
**Type:** Feature (Initial Build)
**Description:** Repository setup, .env, .gitignore, folder structure
**Files Modified:** All (initial)
**Tests Added:** T-004 (env check)
**Rules Involved:** ZT-001, ZT-002, ZT-003
**Status:** In Progress

## [v1.1.0] — Pending
**Type:** Feature
**Description:** LangChain ReACT agent + tool wrappers + LiteLLM gateway
**Files Modified:** core/orchestration.py, core/gateway.py, tools/search.py, tools/memory.py
**Tests Added:** T-001, T-002, T-003, T-005, T-008, T-009
**Rules Involved:** R-001, R-002, R-005
**Status:** In Progress

## [v1.2.0] — Pending
**Type:** Feature
**Description:** Synthesis layer (Jinja2) + HTML email template
**Files Modified:** core/synthesis.py, core/delivery.py, config/email_template.html
**Tests Added:** T-010, T-011, T-012, T-013
**Rules Involved:** R-003, R-006
**Status:** In Progress

## [v1.3.0] — Pending
**Type:** Feature
**Description:** SQLite database + topic pool management
**Files Modified:** database/schema.sql, tools/topic_manager.py, scripts/setup_db.py
**Tests Added:** T-006, T-007
**Rules Involved:** R-004, ZT-002
**Status:** In Progress

## [v1.4.0] — Pending
**Type:** Feature
**Description:** Streamlit dashboard
**Files Modified:** frontend/app.py
**Tests Added:** (UI testing manual for now)
**Rules Involved:** ZT-002 (read-only SQL in dashboard)
**Status:** In Progress

## [v1.5.0] — Pending
**Type:** Feature
**Description:** macOS launchd scheduler setup
**Files Modified:** com.niteen.ai-aggregator.plist, scripts/setup_launchd.py
**Tests Added:** (manual scheduler test)
**Status:** In Progress

## [v1.6.0] — Pending
**Type:** Feature
**Description:** LangSmith tracing + full end-to-end integration test
**Files Modified:** core/orchestration.py (tracing hooks), tests/test_integration.py
**Tests Added:** T-008 final
**Status:** In Progress
```

---

## SECTION 15 — AI PM LEARNING INTEGRATION

This system is designed to teach Niteen how AI systems are actually built, not just talked about. The following learning touchpoints are embedded into the development process itself:

| Development Phase | What You Will Learn | How |
|-----------------|--------------------|----|
| v1.0 — Setup | Git hygiene, `.env` security, Python virtual environments | Doing it |
| v1.1 — ReACT Agent | How LangChain orchestrates tool use, what MCP means in practice | Reading the orchestration.py code |
| v1.1 — Gateway | How LLM providers differ, what token budgeting means in production | LiteLLM dashboard |
| v1.2 — Synthesis | How Jinja2 separates content from presentation (same principle as React) | Template editing |
| v1.3 — Database | SQL schema design, append-only patterns, why DELETE is dangerous in AI systems | schema.sql + rules |
| v1.4 — Dashboard | How Streamlit turns Python into a UI — the "demo fast" principle for PMs | app.py |
| v1.5 — Scheduler | How production AI systems run without human intervention | launchd |
| Every day — Output | The JIC daily lesson system teaches you the AI/ML curriculum you designed | Email inbox |

**As AI PM, your job is to:** understand the architecture (not write all the code), make decisions when the implementing agent (Claude Code) presents trade-offs requiring GOV-001 approval, add topics to the pool as your interests evolve, and read the daily output.

---

## SECTION 16 — WHAT CLAUDE CODE NEEDS FROM YOU (NITEEN)

Before development can start, collect these:

| Item | How to Get It | Where to Put It |
|------|--------------|----------------|
| Google Gemini API Key | https://aistudio.google.com → API Key | `.env → GOOGLE_API_KEY` |
| Tavily API Key | https://tavily.com → Free account | `.env → TAVILY_API_KEY` |
| LangSmith API Key | https://smith.langchain.com → Free account | `.env → LANGCHAIN_API_KEY` |
| Gmail App Password | Gmail → Settings → Security → App Passwords (need 2FA on) | `.env → GMAIL_APP_PASSWORD` |
| OpenAI API Key (optional) | https://platform.openai.com ($5 free credit) | `.env → OPENAI_API_KEY` |
| Python 3.11+ | `python3 --version` on your Mac | Already installed or `brew install python` |
| GitHub account | Already have | For private repo |

**Optional but recommended:**
- Mistral API Key (https://console.mistral.ai — free tier) → `.env → MISTRAL_API_KEY`
- SendGrid account (https://sendgrid.com — 100/day free) → `.env → SENDGRID_API_KEY`

---

## SECTION 17 — STEPS TO HAND OFF TO GOOGLE ANTIGRAVITY

> **v6.2 note:** This section has been rewritten. The previous version predated the Agent Execution Protocol and Task Contract system. All handoffs now go through those documents. See `HANDOFF_PLAN.md` for the complete ready-to-use brief.

### Protocol Files the Agent Receives

Before any task begins, Claude Code must have access to all three of these:

| File | Location in Project | Purpose |
|------|--------------------|---------| 
| `AGENT_EXECUTION_PROTOCOL.md` | `docs/protocol/` | Behavioral contract — 5-phase execution, escalation tiers, all checklists |
| `TASK_CONTRACT.yaml` | `docs/protocol/active/` | Task-level spec — filled SPEC section defines scope, boundaries, acceptance criteria |
| `MASTER_PLAN.md` | Project root | Architectural source of truth — what to build |

### Step 1: Prepare the Task Contract
Before assigning any task, fill the SPEC section of `docs/protocol/active/TASK_CONTRACT.yaml`:
- `task_id`, `task_name`, `assigned_to: "Claude Code"`
- `context_why` — the strategic reason for this task
- `source_documents` — list every file Claude Code must read
- `files_in_scope` — exact list of files Claude Code may touch
- `files_forbidden` — at minimum: `.env`, `MASTER_PLAN.md`, `AGENT_EXECUTION_PROTOCOL.md`
- `tests_required` — test IDs from TEST_REGISTRY.md that must pass before handoff
- `acceptance_criteria` — binary pass/fail conditions

### Step 2: Opening Prompt to Claude Code
In the Claude Code chat/agent panel, paste this exact text (update file paths as needed):

```
You are beginning a new development task. Before writing a single line of code:

1. Read this file in full: <project-root>/docs/protocol/AGENT_EXECUTION_PROTOCOL.md
   This is your behavioral contract. It is mandatory and non-negotiable.

2. Read this file in full: <project-root>/MASTER_PLAN.md
   This is the architectural specification for the system.

3. Read this file in full: <project-root>/docs/protocol/active/TASK_CONTRACT.yaml
   This is your task specification for this session. The SPEC section defines your exact scope.

4. Then proceed through Phase 1 (ANCHOR) as defined in the protocol. Do not begin Phase 2 until Phase 1 checklist is complete.

Confirm you have read all three documents by reciting:
- Your task ID and task name from the TASK_CONTRACT
- The files you are allowed to create or modify (files_in_scope)
- The files you are forbidden to touch (files_forbidden)
- The first required test ID (tests_required[0])
- What escalation action you take if you find a structural ambiguity (answer: STOP, not guess)
```

### Step 3: Verify Claude Code's Anchor Response
Claude Code's confirmation response must include:
- Correct task ID and name
- Complete list of files_in_scope (no extras)
- Correct escalation behavior (STOP for architectural ambiguity)

If any item is wrong or missing — do not proceed. Correct it before Claude Code begins Phase 2.

### Step 4: Collect API Keys (if first-time setup)
Use the table in Section 16. Minimum to start: **Google Gemini API key** (from AI Studio — separate from your Claude Code Pro membership) and **Tavily API key**.

⚠️ **Rotate the keys exposed in LITELLM_SETUP.md** (Mistral and LangSmith) before any live run — those keys were committed in plaintext and must be treated as compromised.

### Step 5: Version Gates
Follow the version sequence in CHANGELOG (v1.0 → v1.1 → v1.2 → ...). After each version:
- Claude Code runs `pytest tests/ -v` — full suite, not just the current task's tests
- All tests must pass before the next TASK_CONTRACT is issued
- This is a hard gate enforced by the TASK_CONTRACT `all_required_tests_passing` completion gate

### Step 6: First Live Test
After v1.5 (scheduler), trigger a manual run from the Claude Code terminal:
```bash
cd ~/Projects/ai-aggregator-system
python main.py
```
Check your email inbox. Then open the Streamlit dashboard:
```bash
streamlit run frontend/app.py
```

### Claude Code Tips
- Claude Code runs in your terminal (`claude` command). Open it in the `ai-aggregator-system/` directory.
- Paste the opening prompt from `HANDOFF_PLAN.md` Section 11 directly into the Claude Code session.
- Claude Code will produce a **Gate Compliance Report** at the end of each phase — review it in the terminal before confirming the next phase begins.
- If Claude Code proposes deviating from `files_in_scope` or suggests a structural change → respond with "STOP — raise GOV-X-001 escalation" and wait for the written justification before approving.

---

## SECTION 18 — BEST PRACTICES CROSS-REFERENCE

| Best Practice | Where Applied | Rule Reference |
|--------------|--------------|---------------|
| Twelve-Factor App (config in env) | `.env` + `check_env.py` | ZT-001 |
| Facade Pattern (gateway abstraction) | `gateway.py` interface | R-002 |
| Principle of Least Privilege | DB connection = SELECT+INSERT only | ZT-002 |
| Graceful Degradation | Search fallback, email retry, lesson-only mode | R-006, Section 5.3 |
| Immutable Ledger | Append-only `historical_ledger` table | R-004 |
| Dependency Inversion | All components talk through interfaces | Section 9.D |
| Spaced Repetition | 7-day cooldown rule | R-001 |
| Determinism > Probability | Static search queries, rule-based decisions | Section 9.E |
| TDD | Tests written before implementation | Section 10 |
| Human-in-the-Loop | GOV-001: structural changes need approval | GOV-001 |
| Zero Trust | Env isolation, network whitelist, least privilege | ZT-001/002/003 |
| Modular Design | MCP-style interfaces, single responsibility | Section 2.2 |

---

*End of MASTER_PLAN.md — Version 6.1*  
*This document is the implementation contract. Deviations require either a GOV-001 approval (during development) or a CHANGELOG entry and rule update (post-deployment).*
