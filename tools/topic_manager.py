"""
MODULE: topic_manager.py
PURPOSE: Read and advance the ordered JIC lesson topic pool stored in topic_pool.json
INPUTS: pool_path (str) — path to topic_pool.json; defaults to config/topic_pool.json
OUTPUTS: current topic string (get_next_topic); updated JSON file (mark_topic_done)
DEPENDENCIES: json (stdlib only)
RULE REFERENCES: GOV-001 (topic order is deterministic, never LLM-decided — Section 9.E)
CHANGE LOG: 1.0.0 | 2026-06-16 | TC-004 initial implementation | Claude Code
             1.1.0 | 2026-06-22 | CL-026 bugfix: _DEFAULT_POOL was cwd-relative
             ("config/topic_pool.json") — same bug class as CL-024/main.py's
             _DB_PATH. Anchored to PROJECT_ROOT | Claude Code
"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_POOL = str(PROJECT_ROOT / "config" / "topic_pool.json")


def _read_pool(pool_path: str) -> dict:
    """Load topic_pool.json and return parsed dict."""
    with open(pool_path) as f:
        return json.load(f)


def _write_pool(pool_path: str, pool: dict) -> None:
    """Persist updated pool dict back to topic_pool.json atomically."""
    with open(pool_path, "w") as f:
        json.dump(pool, f, indent=2)


def get_next_topic(pool_path: str = _DEFAULT_POOL) -> str:
    """
    Return the topic at the current pointer position.

    Wraps around if pointer has somehow exceeded the list length (defensive).

    Args:
        pool_path: Path to topic_pool.json.

    Returns:
        Topic string at topics[pointer % len(topics)].
    """
    pool = _read_pool(pool_path)
    idx = pool["pointer"] % len(pool["topics"])
    topic = pool["topics"][idx]
    logger.debug(f"get_next_topic: pointer={pool['pointer']} → '{topic}'")
    return topic


def mark_topic_done(pool_path: str = _DEFAULT_POOL) -> None:
    """
    Increment the pointer by 1 and persist to topic_pool.json.

    Wraps back to 0 after the last topic so the curriculum loops.

    Args:
        pool_path: Path to topic_pool.json.
    """
    pool = _read_pool(pool_path)
    old = pool["pointer"]
    pool["pointer"] = (old + 1) % len(pool["topics"])
    _write_pool(pool_path, pool)
    logger.info(f"mark_topic_done: pointer {old} → {pool['pointer']}")
