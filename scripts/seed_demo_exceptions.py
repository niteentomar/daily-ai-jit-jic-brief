"""
MODULE: seed_demo_exceptions.py
PURPOSE: Insert labelled [DEMO] rows into system_exceptions for Panel 4
         (Error & Audit Log) screenshots. Safe to run multiple times —
         idempotent: skips insert if any [DEMO] row already exists.
INPUTS:  database/ledger.db (created if absent via setup_db.init_db)
OUTPUTS: 2-3 rows in system_exceptions with '[DEMO]' prefix in message
DEPENDENCIES: sqlite3, scripts.setup_db
RULE REFERENCES: ZT-002 (no DELETE/DROP/ALTER — we only INSERT)
CHANGE LOG: 1.0.0 | 2026-06-25 | CL-054 new demo-data helper | Claude Code
"""
import sqlite3
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_DB_PATH = _ROOT / "database" / "ledger.db"

_DEMO_ROWS = [
    (
        "WARNING",
        "search",
        "[DEMO] Tavily rate-limit hit (429). Retrying in 5 s — attempt 1/3.",
        "2026-06-25 08:01:00",
    ),
    (
        "ERROR",
        "gateway",
        "[DEMO] Primary model vertex_ai/gemini-2.5-flash-lite timed out after 30 s. "
        "Falling back to gemini/gemini-2.5-flash.",
        "2026-06-25 08:02:15",
    ),
    (
        "CRITICAL",
        "delivery",
        "[DEMO] SMTP authentication failed (535 5.7.8 Bad credentials). "
        "Email not delivered for 2026-06-25.",
        "2026-06-25 08:03:47",
    ),
]


def seed(db_path: str = str(_DB_PATH)) -> None:
    """
    Insert demo exception rows if none already exist.

    Idempotent: if any row with '[DEMO]' in its message is already present,
    the function prints a notice and exits without writing anything.
    """
    # Ensure the database file and schema exist
    if not Path(db_path).exists():
        from scripts.setup_db import init_db
        init_db(db_path)

    conn = sqlite3.connect(db_path)
    try:
        existing = conn.execute(
            "SELECT COUNT(*) FROM system_exceptions WHERE message LIKE '%[DEMO]%'"
        ).fetchone()[0]

        if existing > 0:
            print(
                f"[seed_demo_exceptions] {existing} demo row(s) already present — "
                "skipping insert."
            )
            return

        conn.executemany(
            "INSERT INTO system_exceptions (severity, component, message, created_at) "
            "VALUES (?, ?, ?, ?)",
            _DEMO_ROWS,
        )
        conn.commit()
        print(
            f"[seed_demo_exceptions] Inserted {len(_DEMO_ROWS)} [DEMO] rows into "
            f"system_exceptions at {db_path}"
        )
    finally:
        conn.close()


if __name__ == "__main__":
    seed()
