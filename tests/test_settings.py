"""
MODULE: test_settings.py
PURPOSE: CL-062 config layer: settings defaults, registry helpers, prompt rendering.
CHANGE LOG: 1.0.0 | 2026-11-01 | CL-062 | Claude Code
"""
from core import settings


def test_t_set_c_001_defaults_match_decisions(monkeypatch):
    """T-SET-C-001: defaults follow D12-D14 and D15 v2 (global, medium, 180s, 0.85/0.92) when env unset."""
    for k in ("VERTEX_LOCATION", "REASONING_EFFORT", "LITELLM_TIMEOUT_SECONDS", "DEDUPE_OVERLAP_THRESHOLD",
              "DEDUPE_DUPLICATE_THRESHOLD"):
        monkeypatch.delenv(k, raising=False)
    s = settings.load_settings()
    assert (s.vertex_location, s.reasoning_effort, s.timeout_seconds, s.dedupe_overlap, s.dedupe_duplicate) == \
        ("global", "medium", 180, 0.85, 0.92)


def test_t_set_c_002_model_chain_reads_env_in_order(monkeypatch):
    """T-SET-C-002: LITELLM_MODEL_1..N become the chain (Argon then 3.8 Flash)."""
    monkeypatch.setenv("LITELLM_MODEL_1", "vertex_ai/gemini-4-argon")
    monkeypatch.setenv("LITELLM_MODEL_2", "vertex_ai/gemini-3.8-flash")
    monkeypatch.delenv("LITELLM_MODEL_3", raising=False)
    assert settings.load_settings().model_chain == ["vertex_ai/gemini-4-argon", "vertex_ai/gemini-3.8-flash"]


def test_t_set_c_003_registry_sections_and_windows():
    """T-SET-C-003: registry has JIT 7-day and JIC 14-day windows (D1, D11)."""
    reg = settings.load_registry()
    assert reg["sections"]["jit"]["window_days"] == 7
    assert reg["sections"]["jic"]["window_days"] == 14
    assert reg["sections"]["lesson"]["max_papers"] == 5


def test_t_set_c_004_domain_matching_supports_paths_and_subdomains():
    """T-SET-C-004: domain_matches handles subdomains and path-scoped domains."""
    assert settings.domain_matches("https://www.arxiv.org/abs/1", "arxiv.org")
    assert settings.domain_matches("https://blog.research.google/x", "research.google")
    assert settings.domain_matches("https://huggingface.co/papers/123", "huggingface.co/papers")
    assert not settings.domain_matches("https://huggingface.co/models", "huggingface.co/papers")
    assert not settings.domain_matches("https://notarxiv.org/x", "arxiv.org")


def test_t_set_n_001_blocked_domains_win():
    """T-SET-N-001: blocked list is checked before tiers."""
    assert settings.tier_of("https://medium.com/@x/post") == "blocked"
    assert settings.tier_of("https://arxiv.org/abs/1") == "T1"
    assert settings.tier_of("https://unknown.example/x") is None


def test_t_set_c_005_prompts_render_and_keep_unknown_placeholders():
    """T-SET-C-005: every prompt file renders; unknown placeholders stay visible instead of raising."""
    for name in ("jit_research", "jit_editor", "jic_research", "jic_editor", "lesson", "lesson_repair"):
        text = settings.render_prompt(name, today="2026-11-02")
        assert "2026-11-02" in text or "{today}" not in text
    assert "{lesson_topic}" in settings.render_prompt("jit_editor")
