"""
MODULE: search.py
PURPOSE: Web search with a provider chain (CL-064, decision D4):
         Tavily -> Exa -> DuckDuckGo. Hard filters: trusted-domain allowlist
         (config/source_registry.json) and publication window. Monthly usage
         counters switch provider at 90% of a free allowance.
INPUTS: query, window days, domain allowlist
OUTPUTS: list of {title, url, summary, date, provider}
DEPENDENCIES: tavily-python, requests (Exa REST), ddgs
RULE REFERENCES: SEC-X-001 (keys from env), ZT-003 (outbound allowlist)
CHANGE LOG: 1.0.0-1.6.0 | 2026-06 | TC-004..CL-059b Tavily + DuckDuckGo history | Claude Code
            2.0.0 | 2026-11-01 | CL-064: provider chain Tavily -> Exa -> ddgs,
            registry-driven domain filters, explicit windows (JIT 7d, JIC 14d,
            lesson 365d/none), monthly usage counters, results logged to the
            run folder. duckduckgo-search replaced by ddgs (package renamed) | Claude Code
            2.1.0 | 2026-11-01 | CL-069: Tavily results were all dropped after
            return. include_published_date=True (Tavily only auto-dates topic=news),
            normalize_date() reads ISO and RFC-2822 dates, per-provider raw/kept
            counts and drop reasons logged to searches.jsonl | Claude Code
"""
import json
import logging
import os
import re
from collections import Counter
from email.utils import parsedate_to_datetime
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from tavily import TavilyClient

try:
    from ddgs import DDGS
except ImportError:  # pragma: no cover - legacy package name
    from duckduckgo_search import DDGS

from core import run_logger
from core.settings import domain_matches, load_registry, load_settings

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SOURCES_PATH = _PROJECT_ROOT / "config" / "search_sources.json"
_USAGE_PATH = _PROJECT_ROOT / "logs" / "search_usage.json"
_DATE_OPERATOR_RE = re.compile(r"\b(after|before):\d{4}-\d{2}-\d{2}\b", re.IGNORECASE)
_DEFAULT_SOURCES = {"jit_domains": [], "jic_domains": [], "gap_fill_queries": {"jit": [], "jic": []}}
_TAVILY_CREDITS_PER_SEARCH = 1
_EXA_URL = "https://api.exa.ai/search"


# ---------------------------------------------------------------------------
# Legacy helpers kept for backward compatibility (tests, gap-fill config)
# ---------------------------------------------------------------------------

def load_search_sources() -> dict:
    """Load legacy config/search_sources.json (gap-fill query templates)."""
    try:
        with open(_SOURCES_PATH, encoding="utf-8") as fh:
            return {**_DEFAULT_SOURCES, **json.load(fh)}
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning(f"Could not load search_sources.json, using defaults: {exc}")
        return dict(_DEFAULT_SOURCES)


def _normalize_query(query: str) -> str:
    """Strip Tavily-conflicting date operators and truncate to API limit."""
    query = _DATE_OPERATOR_RE.sub("", str(query or "")).strip()
    query = re.sub(r"\s{2,}", " ", query)
    return query[:400]


def domain_from_url(url: str) -> str:
    """Return the hostname for display as a source label."""
    try:
        return (urlparse(url).netloc or "").removeprefix("www.")
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Usage counters
# ---------------------------------------------------------------------------

def _month() -> str:
    return date.today().strftime("%Y-%m")


def _load_usage() -> dict:
    try:
        data = json.loads(_USAGE_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        data = {}
    if data.get("month") != _month():
        data = {"month": _month(), "tavily_credits": 0, "exa_usd": 0.0, "ddgs_calls": 0}
    return data


def _save_usage(data: dict) -> None:
    try:
        _USAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _USAGE_PATH.write_text(json.dumps(data, indent=1))
    except OSError as exc:
        logger.error(f"search usage not saved: {exc}")


def _tavily_available(usage: dict) -> bool:
    s = load_settings()
    return bool(os.getenv("TAVILY_API_KEY")) and usage["tavily_credits"] < s.tavily_monthly_credits * s.provider_switch_ratio


def _exa_available(usage: dict) -> bool:
    s = load_settings()
    return bool(os.getenv("EXA_API_KEY")) and usage["exa_usd"] < s.exa_monthly_budget_usd * s.provider_switch_ratio


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------

def normalize_date(value) -> str:
    """Return YYYY-MM-DD from ISO ('2026-10-29T..'), RFC-2822 ('Wed, 29 Oct 2026 10:00:00 GMT')
    or common long forms; '' if unknown. CL-069: Tavily news dates are not always ISO."""
    if not value:
        return ""
    text = str(value).strip()
    try:  # full ISO timestamp with zone -> local calendar date (CL-072: one clock everywhere)
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return (dt.astimezone() if dt.tzinfo else dt).date().isoformat()
    except ValueError:
        pass
    try:
        return date.fromisoformat(text[:10]).isoformat()
    except ValueError:
        pass
    try:
        dt = parsedate_to_datetime(text)
        return (dt.astimezone() if dt.tzinfo else dt).date().isoformat()
    except (TypeError, ValueError, IndexError):
        pass
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[:40].strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def _host_only(domains: list | None) -> list | None:
    """Tavily filters by host; strip any path part and de-duplicate."""
    if not domains:
        return None
    out = []
    for d in domains:
        host = d.split("/", 1)[0]
        if host not in out:
            out.append(host)
    return out


def _tavily_search(query: str, n: int, *, days: int | None = 7, include_domains: list | None = None,
                   topic: str = "news") -> list:
    """Call Tavily and normalise to {title, url, summary, date}."""
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY", ""))
    kwargs = {"max_results": n, "topic": topic, "include_published_date": True}
    if days:
        if topic == "news":
            kwargs["days"] = days
        else:
            kwargs["start_date"] = (date.today() - timedelta(days=days)).isoformat()
    hosts = _host_only(include_domains)
    if hosts:
        kwargs["include_domains"] = hosts
    raw = client.search(query, **kwargs)
    return [{"title": r.get("title", ""), "url": r.get("url", ""), "summary": r.get("content", ""),
             "date": normalize_date(r.get("published_date"))} for r in raw.get("results", [])]


def _exa_search(query: str, n: int, *, days: int | None = None, include_domains: list | None = None) -> tuple[list, float]:
    """Call Exa /search (build-with-exa skill: highlights; allowlist + window are explicit requirements)."""
    body = {"query": query, "type": "auto", "contents": {"highlights": True}}
    if n != 10:
        body["numResults"] = n
    if include_domains:
        body["includeDomains"] = include_domains
    if days:
        start = datetime.now(timezone.utc) - timedelta(days=days)
        body["startPublishedDate"] = start.strftime("%Y-%m-%dT00:00:00.000Z")
    resp = requests.post(_EXA_URL, json=body, timeout=30, headers={"x-api-key": os.getenv("EXA_API_KEY", "")})
    if resp.status_code >= 400:
        raise RuntimeError(f"Exa HTTP {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    cost = float((data.get("costDollars") or {}).get("total", 0.0) or 0.0)
    results = [{"title": r.get("title") or "", "url": r.get("url", ""),
                "summary": " ".join(r.get("highlights") or [])[:1000],
                "date": normalize_date(r.get("publishedDate"))} for r in data.get("results", [])]
    return results, cost


def _duckduckgo_search(query: str, n: int) -> list:
    """Last-resort search via ddgs. Never raises (D4: failure tolerated)."""
    try:
        raw = list(DDGS().text(query, max_results=n))
        return [{"title": r.get("title", ""), "url": r.get("href", ""), "summary": r.get("body", ""), "date": ""}
                for r in raw]
    except Exception as exc:
        logger.warning(f"DuckDuckGo search failed: {exc}")
        return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _within_window(item: dict, days: int | None) -> bool:
    if not days:
        return True
    d = item.get("date") or ""
    if not d:
        return False
    try:
        return date.fromisoformat(d[:10]) >= date.today() - timedelta(days=days)
    except ValueError:
        return False


def _filter(results: list, include_domains: list | None, days: int | None, require_date: bool,
            reasons: Counter | None = None) -> list:
    """Apply blocked list, allowlist and window. Drop reasons are counted into `reasons` (CL-069)."""
    registry = load_registry()
    blocked = registry.get("blocked", [])
    reasons = reasons if reasons is not None else Counter()
    out, seen = [], set()
    for r in results:
        url = r.get("url") or ""
        if not url or url in seen:
            reasons["duplicate_or_no_url"] += 1
            continue
        if any(domain_matches(url, b) for b in blocked):
            reasons["blocked_domain"] += 1
            continue
        if include_domains and not any(domain_matches(url, d) for d in include_domains):
            reasons["not_in_allowlist"] += 1
            continue
        if require_date and days and not r.get("date"):
            reasons["no_date"] += 1
            continue
        if r.get("date") and not _within_window(r, days):
            reasons["outside_window"] += 1
            continue
        seen.add(url)
        out.append(r)
    return out


def search_sources(query: str, *, n: int = 10, days: int | None = 7, include_domains: list | None = None,
                   topic: str = "news", require_date: bool = True, label: str = "") -> list:
    """
    Search through the provider chain and return filtered results.

    Args:
        query: search text.
        n: max results requested from the provider.
        days: publication window (None = no window).
        include_domains: allowlist (registry domains, may include paths).
        topic: Tavily topic ('news' for JIT, 'general' for research).
        require_date: drop undated results when a window is set.
        label: tag for the run log (e.g. 'jit', 'lesson-papers').
    """
    query = _normalize_query(query)
    usage = _load_usage()
    results, provider, errors, attempts = [], None, [], []

    def _attempt(name: str, raw: list) -> list:
        reasons: Counter = Counter()
        kept = _filter(raw, include_domains, days, require_date if name != "ddgs" else False, reasons)
        attempts.append({"provider": name, "raw": len(raw), "kept": len(kept), "dropped": dict(reasons)})
        for r in kept:
            r["provider"] = name
        return kept

    if _tavily_available(usage):
        try:
            raw = _tavily_search(query, n, days=days, include_domains=include_domains, topic=topic)
            usage["tavily_credits"] += _TAVILY_CREDITS_PER_SEARCH
            results = _attempt("tavily", raw)
            provider = "tavily"
        except Exception as exc:  # noqa: BLE001
            errors.append(f"tavily: {exc}")
    if len(results) < max(3, n // 2) and _exa_available(usage):
        # CL-069: top up when Tavily keeps too few (path-scoped allowlist entries filter many hosts)
        try:
            raw, cost = _exa_search(query, n, days=days, include_domains=include_domains)
            usage["exa_usd"] = round(usage["exa_usd"] + cost, 4)
            have = {r["url"] for r in results}
            extra = [r for r in _attempt("exa", raw) if r["url"] not in have]
            provider = "tavily+exa" if results and extra else ("exa" if extra else provider)
            results = results + extra
        except Exception as exc:  # noqa: BLE001
            errors.append(f"exa: {exc}")
    if not results:
        results = _attempt("ddgs", _duckduckgo_search(query, n))
        usage["ddgs_calls"] += 1
        provider = "ddgs" if results else provider
    _save_usage(usage)
    for r in results:
        r.setdefault("provider", provider)
    ctx = run_logger.current()
    if ctx:
        ctx.append_jsonl("inputs/searches.jsonl", {"label": label, "query": query, "days": days,
                                                   "domains": len(include_domains or []), "provider": provider,
                                                   "attempts": attempts, "errors": errors, "results": results})
        for e in errors:
            ctx.record_error("search", e, severity="WARNING", action_taken="next provider")
    if errors:
        logger.warning(f"search({query!r}): provider errors {errors}; served by {provider or 'none'} "
                       "(chain: Tavily -> Exa -> DuckDuckGo)")
    return results


def search(query: str, n: int = 10) -> list:
    """Backward-compatible: 7-day news search without domain filter."""
    return search_sources(query, n=n, days=7, include_domains=None, topic="news", require_date=False, label="legacy")


def search_broad(query: str, n: int = 10, *, section: str = "jit") -> list:
    """Backward-compatible broad search: section window and registry tiers."""
    from core.settings import section_config, tier_domains
    cfg = section_config(section)
    return search_sources(query, n=n, days=cfg["window_days"], include_domains=tier_domains(cfg["search_tiers"]),
                          topic="news" if section == "jit" else "general", label=f"{section}-broad")
