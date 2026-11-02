"""
MODULE: setup_db.py
PURPOSE: Initialize database/ledger.db from database/schema.sql
INPUTS: db_path (str) — target SQLite file path
OUTPUTS: None — creates/initialises the SQLite database file and all tables
DEPENDENCIES: sqlite3, database/schema.sql
RULE REFERENCES: ZT-002 (no DELETE/DROP/ALTER), R-004 (trigger installed by schema)
CHANGE LOG: 1.0.0 | 2026-06-16 | TC-001 scaffold/stub only (NotImplementedError) | Claude Code
             1.1.0 | 2026-06-16 | TC-003 full implementation | Claude Code
             1.2.0 | 2026-06-22 | CL-026 bugfix: default db_path was cwd-relative
             ("database/ledger.db"). Under launchd (cwd=/), os.makedirs resolved
             to /database — read-only, SIP-sealed system volume — raising
             OSError: Read-only file system. Anchored to PROJECT_ROOT, same
             pattern already used for SCHEMA_PATH | Claude Code
"""
import os
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"


def init_db(db_path: str = str(PROJECT_ROOT / "database" / "ledger.db")) -> None:
    """
    Initialise the SQLite ledger database from database/schema.sql.

    Creates all tables (historical_ledger, gateway_telemetry_logs, system_exceptions)
    and installs the R-004 DELETE-prevention trigger. Safe to call on an existing
    database — all statements use IF NOT EXISTS.

    Args:
        db_path: Target file path for the SQLite database.
    """
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    with open(SCHEMA_PATH) as f:
        schema = f.read()
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print("ledger.db initialised successfully.")
