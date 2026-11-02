# HANDOVER.md
**Date:** 2026-11-01 · **State:** v2 implemented (CL-061..CL-066), 254/254 tests passing on Python 3.14 (CL-067..CL-075). Production: launchd 07:00 + watchdog 09:30 (scripts/install_production.sh). First live dry run 2026-11-01 OK ($0.13); CL-069..071 fix its findings.
**Previous handovers:** `docs/history/HANDOVER_v1_CL060.md`, `docs/history/HANDOVER_FINAL_v1.md`

## 1. What the system does now
| Stage | Module | Notes |
|---|---|---|
| Entry | `main.py` | `python3 main.py` (full) · `--dry-run` · `--resend YYYY-MM-DD` |
| JIT / JIC | `core/news.py` | ReAct research agent (search tool, max 6 searches) -> structured editor selects only captured candidates -> code checks + embedding de-dup + cooldown |
| Lesson | `core/lesson.py` | 4 grounding searches -> fixed-slot JSON -> slot checks -> 1 repair -> OpenAlex paper verification + stars |
| Models | `core/gateway.py` | Argon (global, medium) -> 3.8 Flash fallback; classified retries; cost guard; network wait |
| Search | `tools/search.py` | Tavily -> Exa -> DuckDuckGo; registry allowlists; monthly counters in `logs/search_usage.json` |
| Memory | `core/dedupe.py` | `news_ledger` embeddings, threshold 0.70 |
| Logs | `core/run_logger.py` | `logs/runs/<date>/<time>-<mode>/`; tables run_log, llm_calls, run_errors |
| Dashboard | `frontend/app.py` | Panel 1 run_log + cost; Panel 7 Run Explorer |
| Config | `config/source_registry.json`, `config/prompts/*.md`, `config/topic_pool.json` (88 topics, pointer 0), `.env` |

## 2. Decisions in force (2026-11-01)
D1 JIC window 14 days · D2 TL;DR · D3 config files · D4 search chain · D6 no 3G · D7 review 3A after 2 runs · D8 lesson spec v2 · D9 no padding · D10 embedding de-dup · D11 JIT tiers · D12 Argon · D13 medium thinking · D14 3.8 Flash fallback · D15 threshold 0.70. Details: `JIC_prompt_and_sources_DRAFT.md`, `API_AUDIT_2026-11-01.md`, `LOGGING_DESIGN_DRAFT.md`.

## 3. Next actions (in order)
1. On the Mac: create `.venv`, `pip install -r requirements.txt`, run `pytest -q` (expect 254 passed).
2. Update `.env` model block (see `.env.example`): MODEL_1 Argon, MODEL_2 3.8 Flash, remove MODEL_3-6, add VERTEX_LOCATION=global etc.
3. `python main.py --dry-run` -> review `logs/runs/<today>/.../newsletter.html` and Run Explorer; fix issues one by one.
4. Point launchd at `.venv/bin/python` (`scripts/setup_launchd.py`), schedule 15 days; add Mac wake schedule.
5. Build the deterministic watchdog (reads run_log / run.json).

## 4. Known gaps / watch items
- `gemini-3.8-flash` availability on this project not yet verified (fallback only).
- Embedding `dimensions=768` param on Vertex via LiteLLM not yet verified live; threshold calibrated at 3,072 dims.
- Exa `includeDomains` with path-scoped domains to be verified live.
- `core/orchestration.py` + `core/output_normalize.py` are legacy (not on the v2 path); kept for tests; candidate for removal.
- Laptop dependency: launchd only runs when the Mac is awake and online.
