"""
MODULE: memory.py
PURPOSE: MCP-style DB tool for topic cooldown check and history query
INPUTS: topic (str); optional SQLite connection (pass for tests, omit for production)
OUTPUTS: dict {status, last_covered, delta_days}
DEPENDENCIES: sqlite3, database/ledger.db
RULE REFERENCES: R-001 (7-day cooldown), ZT-002 (SELECT only in this module)
CHANGE LOG: 1.0.0 | 2026-06-16 | TC-003 initial implementation | Claude Code
             1.1.0 | 2026-06-22 | CL-026 bugfix: DB_PATH was cwd-relative
             ("database/ledger.db") — query_history() is called with no conn
             arg by main.py's live agent tools, so this hit the bug directly
             in production (sqlite3.OperationalError: unable to open database
             file under a cwd lacking a database/ subdirectory). Anchored to
             PROJECT_ROOT, same pattern as CL-024 | Claude Code
"""
import logging
import sqlite3
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = str(PROJECT_ROOT / "database" / "ledger.db")


def query_history(topic: str, conn=None) -> dict:
    """
    Look up a topic in historical_ledger and return its cooldown status.

    Args:
        topic: Topic keyword string to search for (case-sensitive exact match).
        conn: SQLite connection to use. If None, opens DB_PATH (production path).
              Pass an in-memory connection in tests for isolation.

    Returns:
        dict with keys:
          status (str)       — "Found" if topic has prior coverage, else "Not Found"
          last_covered (str) — ISO date of most recent coverage, or None
          delta_days (int)   — Days since last coverage, or None

    Rule: R-001 — callers should suppress the topic when delta_days < 8.
    """
    _close = False
    if conn is None:
        conn = sqlite3.connect(DB_PATH)
        _close = True

    try:
        row = conn.execute(
            "SELECT covered_date FROM historical_ledger "
            "WHERE topic = ? ORDER BY covered_date DESC LIMIT 1",
            (topic,),
        ).fetchone()
    finally:
        if _close:
            conn.close()

    if row is None:
        return {"status": "Not Found", "last_covered": None, "delta_days": None}

    last_covered = row[0]
    delta_days = (date.today() - date.fromisoformat(last_covered)).days
    logger.debug(f"query_history: '{topic}' last covered {last_covered} ({delta_days}d ago)")
    return {"status": "Found", "last_covered": last_covered, "delta_days": delta_days}
