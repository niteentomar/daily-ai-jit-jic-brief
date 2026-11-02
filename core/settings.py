"""
MODULE: settings.py
PURPOSE: Single place that reads runtime settings (.env), the source registry and
         prompt templates, so behaviour changes are config edits, not code edits.
INPUTS: environment variables; config/source_registry.json; config/prompts/*.md
OUTPUTS: Settings dataclass; registry dict; rendered prompt strings
DEPENDENCIES: stdlib only
RULE REFERENCES: GOV-X-001 (approved structural change, decision D3), SEC-X-001
CHANGE LOG: 1.0.0 | 2026-11-01 | CL-062 initial implementation | Claude Code
"""
import json
import os
from dataclasses import dataclass, field
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
REGISTRY_PATH = CONFIG_DIR / "source_registry.json"
PROMPTS_DIR = CONFIG_DIR / "prompts"


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass
class Settings:
    """Runtime settings with safe defaults (decisions D12-D15)."""
    model_chain: list = field(default_factory=list)
    vertex_location: str = "global"
    reasoning_effort: str = "medium"
    timeout_seconds: int = 180
    max_retries: int = 2
    embedding_model: str = "vertex_ai/gemini-embedding-001"
    embedding_location: str = "us-central1"
    embedding_dims: int = 768
    dedupe_overlap: float = 0.85     # CL-070 (D15 v2)
    dedupe_duplicate: float = 0.92
    network_wait_seconds: int = 300
    tavily_monthly_credits: int = 1000
    exa_monthly_budget_usd: float = 10.0
    provider_switch_ratio: float = 0.90
    daily_cost_limit_usd: float = 2.0


def load_settings() -> Settings:
    """Read settings from the environment on every call (tests can monkeypatch env)."""
    chain, i = [], 1
    while model := os.getenv(f"LITELLM_MODEL_{i}"):
        chain.append(model.strip())
        i += 1
    return Settings(
        model_chain=chain,
        vertex_location=os.getenv("VERTEX_LOCATION", "global"),
        reasoning_effort=os.getenv("REASONING_EFFORT", "medium"),
        timeout_seconds=_env_int("LITELLM_TIMEOUT_SECONDS", 180),
        max_retries=_env_int("LLM_MAX_RETRIES", 2),
        embedding_model=os.getenv("EMBEDDING_MODEL", "vertex_ai/gemini-embedding-001"),
        embedding_location=os.getenv("EMBEDDING_LOCATION", "us-central1"),
        embedding_dims=_env_int("EMBEDDING_DIMS", 768),
        dedupe_overlap=_env_float("DEDUPE_OVERLAP_THRESHOLD", 0.85),
        dedupe_duplicate=_env_float("DEDUPE_DUPLICATE_THRESHOLD", 0.92),
        network_wait_seconds=_env_int("NETWORK_WAIT_SECONDS", 300),
        tavily_monthly_credits=_env_int("TAVILY_MONTHLY_CREDITS", 1000),
        exa_monthly_budget_usd=_env_float("EXA_MONTHLY_BUDGET_USD", 10.0),
        provider_switch_ratio=_env_float("PROVIDER_SWITCH_RATIO", 0.90),
        daily_cost_limit_usd=_env_float("DAILY_COST_LIMIT_USD", 2.0),
    )


@lru_cache(maxsize=4)
def _load_registry_cached(path: str, mtime: float) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_registry(path: Path = REGISTRY_PATH) -> dict:
    """Load config/source_registry.json (cached until the file changes)."""
    return _load_registry_cached(str(path), os.path.getmtime(path))


def tier_domains(tiers: list, registry: dict | None = None) -> list:
    """Return the de-duplicated domain list for the given tier names, in order."""
    registry = registry or load_registry()
    seen, out = set(), []
    for tier in tiers or []:
        for dom in registry["tiers"].get(tier, {}).get("domains", []):
            if dom not in seen:
                seen.add(dom)
                out.append(dom)
    return out


def section_config(section: str, registry: dict | None = None) -> dict:
    """Return the registry block for 'jit', 'jic' or 'lesson'."""
    registry = registry or load_registry()
    return registry["sections"][section]


def _host_and_path(url: str) -> tuple[str, str]:
    parsed = urlparse(url or "")
    host = (parsed.netloc or "").lower().removeprefix("www.")
    return host, parsed.path or ""


def domain_matches(url: str, domain: str) -> bool:
    """True when url belongs to domain (domain may include a path, e.g. 'openai.com/research')."""
    host, path = _host_and_path(url)
    dom_host, _, dom_path = domain.partition("/")
    host_ok = host == dom_host or host.endswith("." + dom_host)
    return host_ok and (not dom_path or path.lstrip("/").startswith(dom_path))


def tier_of(url: str, registry: dict | None = None) -> str | None:
    """Return the first tier whose domain list contains url, 'blocked', or None."""
    registry = registry or load_registry()
    if any(domain_matches(url, d) for d in registry.get("blocked", [])):
        return "blocked"
    for name, tier in registry["tiers"].items():
        if any(domain_matches(url, d) for d in tier.get("domains", [])):
            return name
    return None


class _SafeDict(dict):
    """format_map helper: leaves unknown {placeholders} visible instead of raising."""
    def __missing__(self, key):
        return "{" + key + "}"


def render_prompt(name: str, **values) -> str:
    """Load config/prompts/<name>.md and fill {placeholders}."""
    text = (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")
    return text.format_map(_SafeDict({k: v for k, v in values.items()}))


def window_start(days: int, today: date | None = None) -> str:
    """ISO date `days` before today."""
    return ((today or date.today()) - timedelta(days=days)).isoformat()
