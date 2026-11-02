-- database/schema.sql
-- PURPOSE: SQLite schema for the ai-aggregator-system ledger database
-- RULE REFERENCES: R-004 (append-only historical_ledger), ZT-002 (no DELETE/DROP/ALTER)
-- CHANGE LOG: 1.0.0 | 2026-06-16 | TC-003 initial schema | Claude Code

-- ── historical_ledger ────────────────────────────────────────────────────────
-- Stores every topic covered per daily run. Append-only: the R-004 trigger
-- below blocks any DELETE at the database level regardless of caller.

CREATE TABLE IF NOT EXISTS historical_ledger (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    topic        TEXT    NOT NULL,
    covered_date TEXT    NOT NULL,          -- ISO format YYYY-MM-DD
    run_type     TEXT    NOT NULL DEFAULT 'JIT',  -- 'JIT', 'JIC', or 'LESSON'
    created_at   TEXT    NOT NULL DEFAULT (date('now'))
);

-- R-004: DELETE on historical_ledger is forbidden at the database level.
-- RAISE(ABORT) fires before any row is removed, rolling back only that statement.
CREATE TRIGGER IF NOT EXISTS prevent_delete_historical_ledger
BEFORE DELETE ON historical_ledger
BEGIN
    SELECT RAISE(ABORT, 'DELETE on historical_ledger is forbidden: R-004 append-only rule');
END;

-- ── gateway_telemetry_logs ───────────────────────────────────────────────────
-- One row per LLM call: model used, token count, whether a fallback was triggered.

CREATE TABLE IF NOT EXISTS gateway_telemetry_logs (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    model              TEXT    NOT NULL,
    tokens_used        INTEGER NOT NULL DEFAULT 0,
    fallback_triggered INTEGER NOT NULL DEFAULT 0,  -- 0 = primary, 1 = fallback
    run_date           TEXT    NOT NULL,             -- ISO format YYYY-MM-DD
    created_at         TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ── system_exceptions ────────────────────────────────────────────────────────
-- Structured error log. Append-only by convention (no trigger needed — errors
-- are never deleted; historical record of failures is kept for audit purposes).

CREATE TABLE IF NOT EXISTS system_exceptions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    severity   TEXT NOT NULL,   -- 'WARNING', 'ERROR', 'CRITICAL'
    component  TEXT NOT NULL,   -- e.g. 'gateway', 'search', 'delivery'
    message    TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ════════════════════════════════════════════════════════════════════════════
-- CL-066 (2026-11-01): run logging, per-call telemetry, news memory.
-- All tables append-only by design (R-004 / ZT-002). Triggers block DELETE.
-- ════════════════════════════════════════════════════════════════════════════

-- ── run_log ──────────────────────────────────────────────────────────────────
-- One row per pipeline run (full, dry-run or resend).
CREATE TABLE IF NOT EXISTS run_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        TEXT    NOT NULL UNIQUE,
    run_date      TEXT    NOT NULL,
    mode          TEXT    NOT NULL,              -- 'full', 'dry-run', 'resend'
    started_at    TEXT    NOT NULL,
    finished_at   TEXT,
    status        TEXT,                          -- 'ok', 'degraded', 'failed'
    lesson_topic  TEXT,
    lesson_ok     INTEGER,
    lesson_quality REAL,
    jit_count     INTEGER,
    jic_count     INTEGER,
    quiet_jit     INTEGER,
    quiet_jic     INTEGER,
    model_used    TEXT,
    fallback_used INTEGER,
    tokens_in     INTEGER,
    tokens_out    INTEGER,
    cost_usd      REAL,
    email_status  TEXT,                          -- 'sent', 'failed', 'skipped'
    run_folder    TEXT,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ── llm_calls ────────────────────────────────────────────────────────────────
-- One row per model call attempt (including retries and failures).
CREATE TABLE IF NOT EXISTS llm_calls (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id            TEXT,
    stage             TEXT,
    model             TEXT,
    attempt           INTEGER,
    latency_s         REAL,
    prompt_tokens     INTEGER,
    completion_tokens INTEGER,
    reasoning_tokens  INTEGER,
    cost_usd          REAL,
    finish_reason     TEXT,
    error_class       TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ── news_ledger ──────────────────────────────────────────────────────────────
-- One row per delivered JIT/JIC item; embedding powers repeat detection (D10, D15).
CREATE TABLE IF NOT EXISTS news_ledger (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT,
    section     TEXT NOT NULL,                   -- 'jit' or 'jic'
    headline    TEXT NOT NULL,
    url         TEXT,
    domain      TEXT,
    item_date   TEXT,
    covered_date TEXT NOT NULL,
    category    TEXT,
    embedding   BLOB,                            -- float32 array; NULL if embedding failed
    fingerprint TEXT,                            -- CL-070 story fingerprint JSON
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ── run_errors ───────────────────────────────────────────────────────────────
-- Structured error detail; a summary row also goes to system_exceptions (Panel 4).
CREATE TABLE IF NOT EXISTS run_errors (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id       TEXT,
    severity     TEXT NOT NULL,
    component    TEXT NOT NULL,
    model        TEXT,
    error_class  TEXT,
    http_status  INTEGER,
    attempt      INTEGER,
    action_taken TEXT,
    message      TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TRIGGER IF NOT EXISTS prevent_delete_run_log
BEFORE DELETE ON run_log
BEGIN
    SELECT RAISE(ABORT, 'DELETE on run_log is forbidden: R-004 append-only rule');
END;

CREATE TRIGGER IF NOT EXISTS prevent_delete_news_ledger
BEFORE DELETE ON news_ledger
BEGIN
    SELECT RAISE(ABORT, 'DELETE on news_ledger is forbidden: R-004 append-only rule');
END;
