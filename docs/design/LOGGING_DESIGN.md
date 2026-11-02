# Daily Run Logging Design (DRAFT for review)

Goal: for every run, keep a complete, queryable record of what went in (prompts, searches), what came out (raw and validated model output, de-dup decisions), the exact newsletter HTML (saved **before** sending), and what it cost. Nothing is ever deleted (requirement 6).

---

## 1. Per-run folder (files, git-ignored)

```
logs/runs/2026-11-02/
├── run.json              # one-page summary: status, timings, models, tokens, cost, errors
├── config_snapshot.json  # model, thinking level, thresholds, registry + prompt file hashes
├── inputs/
│   ├── prompt_jit.md     # exact rendered prompts sent to the model
│   ├── prompt_jic.md
│   ├── prompt_lesson.md
│   └── searches.jsonl    # every search: provider, query, filters, results (url, title, date)
├── outputs/
│   ├── jit_raw.json      # model output as received
│   ├── jic_raw.json
│   ├── lesson_raw.json
│   ├── jit.json          # after validation, de-dup, cooldown (what the email used)
│   ├── jic.json
│   ├── lesson.json
│   ├── dedupe.json       # every pair compared: similarity score, decision (kept / merged / dropped as repeat)
│   └── quality.json      # slot checks, completeness %, verified papers, URL checks
├── newsletter.html       # final rendered email, written BEFORE send
└── send_result.json      # SendGrid status, message id, timestamp (or error)
```

## 2. Database tables (SQLite, queryable in dashboard Panel 5)

| Table | One row per | Key columns |
|---|---|---|
| `run_log` (new) | run | run_id, date, started, finished, status (ok / degraded / failed), jit_count, jic_count, lesson_ok, model_used, fallback_used, tokens_in, tokens_out, cost_usd, html_path, email_status |
| `llm_calls` (new) | model call | run_id, stage, model, attempt, latency_s, prompt_tokens, completion_tokens, cost_usd, finish_reason, error_class |
| `news_ledger` (new, from JIT design) | delivered news item | run_id, section, headline, url, domain, date, embedding, cluster_id |
| `system_exceptions` (existing, extended) | error | + run_id, model, http_status, attempt, action_taken |
| `historical_ledger` (existing) | delivered lesson | unchanged |

All append-only (no DELETE), consistent with R-004 / ZT-002.

## 3. Run modes (new command-line flags)

| Command | What it does | Use |
|---|---|---|
| `python3 main.py` | Full run: generate, save, send (launchd uses this) | Daily |
| `python3 main.py --dry-run` | Generate and save everything, **do not send**, pointer not advanced | Testing, preview the HTML before go-live |
| `python3 main.py --resend 2026-11-02` | Re-send the saved `newsletter.html` for that date, no LLM calls | Email failed but content was fine |

## 4. Dashboard changes

| Panel | Change |
|---|---|
| 1. Run Metrics | Reads `run_log`: status, sections, model, fallback used, tokens, **cost per day and month to date** |
| NEW: Run Explorer | Pick a date: view prompts, search results, raw vs final output, de-dup decisions, quality score, and the rendered newsletter |
| 4. Audit Log | Reads extended `system_exceptions` with run_id links |
| 5. SQL Console | New tables available |

## 5. Rules

| Rule | Detail |
|---|---|
| Secrets | All logged text passes through `_scrub_secrets()`; `logs/` stays git-ignored |
| Retention | Never deleted. Monthly roll-up: folders older than 90 days zipped into `logs/archive/YYYY-MM.zip` (moved, not deleted) |
| Size | About 0.3 MB per day, about 110 MB per year |
| Failure safety | Logging errors never stop the run; they are themselves recorded in `system_exceptions` |
| Watchdog input | `run.json` + `run_log` are the watchdog's single source of truth |

## 6. Decisions needed

1. Approve the folder layout and the 3 new tables?
2. Approve `--dry-run` and `--resend` modes?
3. Approve the new "Run Explorer" dashboard panel?
4. 90-day zip roll-up OK, or keep all folders unzipped?
