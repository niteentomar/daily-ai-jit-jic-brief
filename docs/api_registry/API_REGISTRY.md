# API_REGISTRY.md — Central API Registry
**Project:** Daily JIT/JIC AI Newsletter (`ai-aggregator-system`)  
**Version:** 1.0.0  
**Last Updated:** 2026-06-15  
**Owner:** Niteen Tomar

---

## PURPOSE

Central record of every external API used in the project. The implementing agent consults this file before making any API call (Phase 1 ANCHOR) and updates it when adding a new API dependency (Phase 5 HANDOFF). No API call is made unless the API is registered here.

**Rule:** If a module needs to call an API not in this registry, the agent must escalate (CLARIFY tier) before adding it.

---

## API REGISTRY TABLE

| API ID | Service Name | Endpoint / Model | Used In Stage | Used By Module | Input | Output | Condition to Call | Fallback | Error Handling | Rate Limit | Secret Variable | Cost Tier | Status |
|--------|-------------|-----------------|--------------|---------------|-------|--------|------------------|----------|----------------|------------|-----------------|-----------|--------|
| API-GEMINI-001 | Gemini 2.5 Flash | `gemini/gemini-2.5-flash` | IMPL | `core/gateway.py` | Prompt string, max_tokens | Text completion string | Primary LLM attempt — all LLM calls start here | API-GEMINI-002 | Log error, increment failure counter, route to fallback | 1,500 req/day free | `GOOGLE_API_KEY` | FREE | ACTIVE |
| API-GEMINI-002 | Gemini 2.5 Flash-Lite | `gemini/gemini-2.5-flash-lite` | IMPL | `core/gateway.py` | Prompt string, max_tokens | Text completion string | API-GEMINI-001 fails OR token usage ≥ 95% of primary limit | API-MISTRAL-001 | Log error, route to next fallback | 1,500 req/day free (shared quota with Flash) | `GOOGLE_API_KEY` | FREE | ACTIVE |
| API-MISTRAL-001 | Mistral 7B Instruct | `mistral/mistral-7b-instruct-v0.2` | IMPL | `core/gateway.py` | Prompt string, max_tokens | Text completion string | API-GEMINI-002 fails | API-OLLAMA-001 | Log error, route to local fallback | Free tier (La Plateforme) | `MISTRAL_API_KEY` | FREE | ACTIVE |
| API-OLLAMA-001 | Ollama llama3.2 (local) | `ollama/llama3.2` | IMPL | `core/gateway.py` | Prompt string | Text completion string | All cloud APIs fail (last resort) | STOP pipeline section + log CRITICAL | Log critical error; send alert email if delivery still possible | Unlimited (local CPU) | None | FREE | ACTIVE |
| API-TAVILY-001 | Tavily Search | `https://api.tavily.com/search` | IMPL | `tools/search.py` | Query string, max_results=5 | JSON list of `{title, url, content, published_date}` | Primary search — all JIT/JIC news queries | API-DDG-001 | Log error, switch to DuckDuckGo; log fallback event | 1,000 req/month free | `TAVILY_API_KEY` | FREE | ACTIVE |
| API-DDG-001 | DuckDuckGo Search | `duckduckgo-search` Python lib (unofficial) | IMPL | `tools/search.py` | Query string, max_results=5 | List of `{title, href, body}` dicts | API-TAVILY-001 fails | None — log WARNING if both fail; skip JIT/JIC section | Log warning; return empty list; pipeline continues without news sections | Unofficial — rate-limit cautiously (1 req/3s) | None | FREE | ACTIVE |
| API-GMAIL-001 | Gmail SMTP | `smtp.gmail.com:587` (TLS) | HANDOFF | `core/delivery.py` | HTML body string, recipient, subject | SMTP 250 OK | Primary email delivery — every daily run | API-SGRID-001 | Retry 3x with exponential backoff (2s/4s/8s); switch to SendGrid on 3rd failure; log each retry | Free with App Password (requires 2FA) | `GMAIL_APP_PASSWORD`, `GMAIL_SENDER` | FREE | ACTIVE |
| API-SGRID-001 | SendGrid Email | `https://api.sendgrid.com/v3/mail/send` | HANDOFF | `core/delivery.py` | HTML body, recipient, subject | HTTP 202 Accepted | API-GMAIL-001 fails after 3 retries | Log CRITICAL; mark `delivered=False` in ledger | Log error; mark run as delivery-failed; do not retry indefinitely | 100 emails/day free | `SENDGRID_API_KEY` | FREE | ACTIVE |
| API-LSMTH-001 | LangSmith Tracing | LangSmith SDK (env var injection) | ALL | All modules via env vars | Run name, inputs, outputs (automatic via SDK) | Trace object in LangSmith dashboard | Every LLM call (automatic when `LANGCHAIN_TRACING_V2=true`) | None — tracing is non-blocking | Log warning if trace fails; pipeline continues without trace; never crash for tracing failure | Free tier | `LANGCHAIN_API_KEY` | FREE | ACTIVE |

---

## ⚠️ SECURITY NOTE

The `.env` variables listed in the `Secret Variable` column above are the **only** place these credentials should exist. They must never appear in source code, config files, logs, or documentation. See RULES.md SEC-X-001 and ZT-001.

**Known compromised keys (as of 2026-06-15):** The Mistral API key and LangSmith API key that were visible in `LITELLM_SETUP.md` must be rotated before any live run. Generate new keys from the respective provider dashboards and place only in `.env`.

---

## ADDING NEW API ENTRIES

1. Assign the next SEQ number: `API-[SERVICE]-[SEQ]`
2. Fill all columns — no partial entries
3. Set `Status: ACTIVE`
4. Add the corresponding secret variable name to `.env.example` with a placeholder value
5. Update CHANGELOG.md with the new API ID
6. Set `api_registry_updated: true` in TASK_CONTRACT ACTUALS section

---

## API PROVIDER LINKS (for getting free keys)

| Provider | Dashboard URL | Free Tier Notes |
|----------|-------------|----------------|
| Google Gemini | https://aistudio.google.com → API Key | Free; separate from Antigravity IDE credits |
| Mistral | https://console.mistral.ai | Free tier available |
| Ollama | https://ollama.com | Local only — no key needed |
| Tavily | https://tavily.com | 1,000 req/month free |
| DuckDuckGo | No account needed | Unofficial lib — no key |
| Gmail SMTP | Gmail → Settings → Security → App Passwords | Requires 2FA enabled on account |
| SendGrid | https://sendgrid.com | 100 emails/day free |
| LangSmith | https://smith.langchain.com | Free tier |
