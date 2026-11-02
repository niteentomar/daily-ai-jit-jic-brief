"""
Tavily diagnostic (read-only; about 4 Tavily credits). Prints raw results and, for each,
why tools.search._filter keeps or drops it. Never prints the API key.
Run: .venv/bin/python scripts/tavily_diag.py
"""
import json, os, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv
load_dotenv()
from tavily import TavilyClient
from core.settings import load_registry, section_config, tier_domains, domain_matches
from tools.search import _host_only, _within_window

reg = load_registry()
client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY", ""))
cases = [
    ("jit", "news", "AI model release launch OpenAI Anthropic Google Meta", {"days": 7}),
    ("jit", "news", "AI model release launch OpenAI Anthropic Google Meta", {"time_range": "week"}),
    ("jic", "general", "transformer architecture attention mechanism state space models research",
     {"start_date": None}),
    ("jic", "general", "transformer architecture attention mechanism state space models research",
     {"start_date": None, "include_published_date": True}),
]
from datetime import date, timedelta
out = []
for section, topic, q, extra in cases:
    cfg = section_config(section)
    domains = tier_domains(cfg["search_tiers"], reg)
    kw = {"max_results": 8, "topic": topic, "include_domains": _host_only(domains), **extra}
    if "start_date" in kw:
        kw["start_date"] = (date.today() - timedelta(days=cfg["window_days"])).isoformat()
    try:
        raw = client.search(q, **kw)
    except Exception as e:
        print(f"\n### {section} {extra}: ERROR {type(e).__name__}: {str(e)[:200]}"); continue
    res = raw.get("results", [])
    print(f"\n### {section} topic={topic} extra={extra} -> {len(res)} raw results")
    reasons = Counter()
    for r in res:
        url, pd = r.get("url", ""), r.get("published_date")
        d = (pd or "")[:10]
        if not any(domain_matches(url, x) for x in domains):
            why = "dropped: not in allowlist (path-scoped domain?)"
        elif not d:
            why = "dropped: no published_date"
        elif not _within_window({"date": d}, cfg["window_days"]):
            why = f"dropped: date fails window/parse (sliced='{d}')"
        else:
            why = "KEPT"
        reasons[why.split(" (")[0]] += 1
        print(f"  - {why:45s} | published_date={pd!r} | {url[:80]}")
    print("  summary:", dict(reasons))
    out.append({"section": section, "extra": str(extra), "n": len(res), "reasons": dict(reasons)})
Path("logs/tavily_diag.json").write_text(json.dumps(out, indent=1))
print("\nSaved logs/tavily_diag.json")
