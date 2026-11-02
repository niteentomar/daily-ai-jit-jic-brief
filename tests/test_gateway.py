"""
MODULE: test_gateway.py
PURPOSE: Test cases for core/gateway.py — LiteLLM SDK-direct gateway with
         failover chain and daily token-budget enforcement
INPUTS: pytest tmp_path/monkeypatch fixtures, mocker for litellm.completion
OUTPUTS: Pass/fail assertions per TEST_REGISTRY T-GAT-* acceptance criteria
DEPENDENCIES: pytest, pytest-mock, core.gateway
RULE REFERENCES: R-002, ZT-001, SEC-X-001, TST-T-002
CHANGE LOG: 1.0.0 | 2026-06-16 | TC-002 initial tests | Claude Code
            1.1.0 | 2026-06-17 | Bugfix: removed GMAIL_APP_PASSWORD/GMAIL_SENDER
            from REQUIRED_ENV (dropped TC-006); added LITELLM_MODEL_1 baseline
            (chain now env-var driven, not hardcoded); T-GAT-E-001 fixture
            updated to set LITELLM_MODEL_1/2/3 explicitly; T-GAT-E-003 replaced
            (MISTRAL_API_KEY-conditional skip no longer exists by design);
            added T-GAT-C-002, T-GAT-N-004 | Claude Code
            1.2.0 | 2026-06-18 | CL-022 added T-GAT-N-005 (_get_api_key routes
            openrouter/ models to OPENROUTER_API_KEY) — .env's LITELLM_MODEL_1/2/3
            are now all openrouter/ models but _get_api_key() had no branch for
            them, so every call was silently sent with no API key | Claude Code
            1.3.0 | 2026-06-18 | CL-023 added T-GAT-N-006 (_scrub_secrets()
            redacts OPENROUTER_API_KEY) — SEC-X-001 gap: OpenRouter is now a
            live provider but its key was never in the scrub loop, so an
            OpenRouter error message echoing the key back would not be
            redacted from logs | Claude Code
            1.4.0 | 2026-06-22 | CL-033: GOOGLE_API_KEY retired (Google AI
            Studio project's credits exhausted, no longer referenced in
            gateway.py). GEMINI_API_KEY is the sole Gemini credential now —
            REQUIRED_ENV, T-GAT-N-003, and T-GAT-S-001 updated to use it
            instead. Added T-GAT-N-007 (_get_api_key routes gemini/ to
            GEMINI_API_KEY only, no GOOGLE_API_KEY fallback), T-GAT-N-008
            (_scrub_secrets redacts GEMINI_API_KEY) | Claude Code
            1.5.0 | 2026-06-22 | CL-036 added T-GAT-N-009 (.env's
            LITELLM_MODEL_2 not the shut-down gemini-2.0-flash slug);
            CL-037 added T-GAT-N-010 (.env's LITELLM_MODEL_1 is
            gemini-2.5-flash-lite), T-GAT-C-011 (_get_api_key routes
            flash-lite to GEMINI_API_KEY) | Claude Code
            1.6.0 | 2026-06-22 | CL-039 added T-GAT-C-012/013 (_strip_fences
            strips ```json/``` wrappers), T-GAT-E-004/005 (_strip_fences
            no-op when no fences present; handles surrounding whitespace),
            T-GAT-C-014/015 (llm_call() passes response_format and returns
            fence-stripped text) — a sixth live run showed Gemini wrapping
            the lesson's JSON response in markdown fences on the direct
            litellm.completion() path (llm_call(), not the AgentExecutor/
            tool-calling path JIT/JIC use), so json.loads() in
            _run_lesson_agent() discarded otherwise-valid content | Claude Code
             1.7.0 | 2026-06-22 | CL-041 added T-GAT-N-011/012 (_get_api_key
             returns None for vertex_ai/ models — Vertex AI authenticates via
             GOOGLE_APPLICATION_CREDENTIALS/ADC, not an api_key= string, which
             would conflict), T-GAT-C-016 (gemini/ branch still routes to
             GEMINI_API_KEY, kept as a fallback), T-GAT-E-006 (_scrub_secrets
             doesn't raise when GEMINI_API_KEY is unset) — MODEL_1/2 migrated
             from gemini/ (AI Studio free quota) to vertex_ai/ (Vertex AI,
             $300 GCP credit, 1000 RPM vs 15 RPM) | Claude Code
             1.8.0 | 2026-06-25 | CL-051: removed GEMINI_API_KEY from REQUIRED_ENV
             test fixture — GEMINI_API_KEY is now optional (vertex_ai/ models
             authenticate via GOOGLE_APPLICATION_CREDENTIALS/ADC). LITELLM_MODEL_1
             in REQUIRED_ENV updated to vertex_ai/gemini-2.5-flash-lite. Updated
             T-GAT-C-001 to assert model_used == vertex_ai/gemini-2.5-flash-lite.
             Added T-GAT-C-017 (_get_api_key vertex_ai/ returns None — confirms
             primary model auth path post-CL-051) | Claude Code
"""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from core import gateway

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_ENV = {
    "LANGCHAIN_API_KEY": "lsv2_test_key_0000",
    "LANGCHAIN_TRACING_V2": "true",
    "LANGCHAIN_PROJECT": "daily-jit-jic-newsletter",
    "TAVILY_API_KEY": "tvly-test-key-0000",
    "TARGET_EMAIL": "you@example.com",
    "DAILY_TOKEN_LIMIT_GEMINI": "1000",
    "TOKEN_ALERT_THRESHOLD": "0.95",
    "LITELLM_MODEL_1": "vertex_ai/gemini-2.5-flash-lite",
    "GOOGLE_APPLICATION_CREDENTIALS": "/tmp/test-sa.json",
}


def _set_env(monkeypatch, overrides=None):
    """Set a valid baseline env for gateway tests; MISTRAL_API_KEY absent by default."""
    values = dict(REQUIRED_ENV)
    if overrides:
        values.update(overrides)
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    # Only remove MISTRAL_API_KEY when it was not explicitly supplied in overrides
    if not (overrides and "MISTRAL_API_KEY" in overrides):
        monkeypatch.delenv("MISTRAL_API_KEY", raising=False)


def _isolate_logs_dir(monkeypatch, tmp_path):
    """Redirect gateway token log I/O away from the repo logs/ dir (test isolation)."""
    monkeypatch.setattr(gateway, "_LOGS_DIR", str(tmp_path / "logs"))


def _fake_response(content, model, prompt_tokens=10, completion_tokens=20):
    """Build a SimpleNamespace shaped like a real litellm.completion() response."""
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        model=model,
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
    )


def test_t_gat_c_001_vertex_ai_flash_lite_success_and_token_logging(tmp_path, monkeypatch, mocker):
    """T-GAT-C-001: mock Vertex AI response returned; token usage logged (CL-051 — primary model is now vertex_ai/)."""
    monkeypatch.chdir(tmp_path)
    _isolate_logs_dir(monkeypatch, tmp_path)
    _set_env(monkeypatch)
    mock_completion = mocker.patch(
        "core.gateway.litellm.completion",
        return_value=_fake_response("Mock summary", "vertex_ai/gemini-2.5-flash-lite"),
    )

    result = gateway.llm_call("Summarize this.")

    assert mock_completion.call_count == 1
    assert set(result.keys()) == {"response", "parsed", "model_used", "tokens_used", "cost", "timestamp"}
    assert result["response"] == "Mock summary"
    assert result["model_used"] == "vertex_ai/gemini-2.5-flash-lite"
    assert result["tokens_used"] == 30
    assert result["cost"] == 0.0

    log_path = tmp_path / "logs" / "token_usage.json"
    assert log_path.exists()
    logged = json.loads(log_path.read_text())
    assert logged["vertex_ai/gemini-2.5-flash-lite"]["tokens_used"] == 30


def test_t_gat_e_001_failover_through_full_chain_to_mistral(tmp_path, monkeypatch, mocker):
    """T-GAT-E-001: first two models fail; third (Mistral) succeeds."""
    monkeypatch.chdir(tmp_path)
    _isolate_logs_dir(monkeypatch, tmp_path)
    _set_env(monkeypatch, overrides={
        "LITELLM_MODEL_1": "gemini/gemini-2.0-flash",
        "LITELLM_MODEL_2": "gemini/gemini-3.0-flash",
        "LITELLM_MODEL_3": "mistral/mistral-small-latest",
        "MISTRAL_API_KEY": "test-mistral-key-0000",
    })
    monkeypatch.delenv("LITELLM_MODEL_4", raising=False)
    monkeypatch.setenv("LLM_MAX_RETRIES", "0")  # CL-063: isolate chain failover from same-model retries
    responses = [
        Exception("Gemini 2.0 Flash rate limited"),
        Exception("Gemini 3.0 Flash rate limited"),
        _fake_response("Fallback summary", "mistral/mistral-small-latest"),
    ]
    mock_completion = mocker.patch("core.gateway.litellm.completion", side_effect=responses)

    result = gateway.llm_call("Summarize this.")

    assert mock_completion.call_count == 3
    called_models = [call.kwargs["model"] for call in mock_completion.call_args_list]
    assert called_models == [
        "gemini/gemini-2.0-flash",
        "gemini/gemini-3.0-flash",
        "mistral/mistral-small-latest",
    ]
    assert result["model_used"] == "mistral/mistral-small-latest"


def test_t_gat_e_003_all_litellm_model_n_included_unconditionally(tmp_path, monkeypatch, mocker):
    """
    T-GAT-E-003 (superseded 2026-06-17): _build_model_chain() includes every
    LITELLM_MODEL_n entry unconditionally — the old "skip Mistral if
    MISTRAL_API_KEY is unset" behavior no longer exists by design; the new
    chain builder is purely env-var driven, with no API-key-presence check.
    """
    monkeypatch.chdir(tmp_path)
    _isolate_logs_dir(monkeypatch, tmp_path)
    _set_env(monkeypatch, overrides={
        "LITELLM_MODEL_1": "gemini/gemini-2.0-flash",
        "LITELLM_MODEL_2": "mistral/mistral-small-latest",
    })
    monkeypatch.delenv("LITELLM_MODEL_3", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)  # deliberately absent
    monkeypatch.setenv("LLM_MAX_RETRIES", "0")  # CL-063: isolate chain failover from same-model retries
    responses = [
        Exception("Gemini 2.0 Flash rate limited"),
        _fake_response("Fallback summary", "mistral/mistral-small-latest"),
    ]
    mock_completion = mocker.patch("core.gateway.litellm.completion", side_effect=responses)

    result = gateway.llm_call("Summarize this.")

    assert mock_completion.call_count == 2
    called_models = [call.kwargs["model"] for call in mock_completion.call_args_list]
    assert called_models == ["gemini/gemini-2.0-flash", "mistral/mistral-small-latest"], (
        "Mistral entry must be tried even though MISTRAL_API_KEY is unset"
    )
    assert result["model_used"] == "mistral/mistral-small-latest"


def test_t_gat_n_001_token_budget_enforcement(tmp_path, monkeypatch, caplog):
    """T-GAT-N-001: _check_token_limit raises when usage >= 95% of daily limit (BUG-001 fix)."""
    monkeypatch.chdir(tmp_path)
    _isolate_logs_dir(monkeypatch, tmp_path)
    _set_env(monkeypatch)
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "token_usage.json").write_text(json.dumps({
        "gemini/gemini-2.5-flash": {"tokens_used": 960, "date": gateway._today_str()}
    }))

    with caplog.at_level("WARNING"):
        with pytest.raises(gateway.TokenBudgetExceededError):
            gateway._check_token_limit("gemini/gemini-2.5-flash")

    assert any("gemini/gemini-2.5-flash" in record.message for record in caplog.records)
    logged = json.loads((log_dir / "token_usage.json").read_text())
    assert logged["gemini/gemini-2.5-flash"]["tokens_used"] == 960


def test_t_gat_e_002_logs_dir_auto_created(tmp_path, monkeypatch, mocker):
    """T-GAT-E-002: logs/ created if absent on first write (BUG-003 fix)."""
    monkeypatch.chdir(tmp_path)
    _isolate_logs_dir(monkeypatch, tmp_path)
    _set_env(monkeypatch)
    assert not (tmp_path / "logs").exists()
    mocker.patch(
        "core.gateway.litellm.completion",
        return_value=_fake_response("Mock summary", "gemini/gemini-2.5-flash"),
    )

    gateway.llm_call("Summarize this.")

    assert (tmp_path / "logs" / "token_usage.json").exists()


def test_t_gat_n_002_unprefixed_model_raises_value_error():
    """T-GAT-N-002: unsupported/unprefixed model string raises ValueError (BUG-002 fix)."""
    with pytest.raises(ValueError):
        gateway._require_provider_prefix("gemini-2.5-flash")


def test_t_gat_c_002_build_model_chain_reads_litellm_model_n(monkeypatch):
    """T-GAT-C-002: _build_model_chain() reads LITELLM_MODEL_1, _2... from env."""
    monkeypatch.setenv("LITELLM_MODEL_1", "gemini/x")
    monkeypatch.setenv("LITELLM_MODEL_2", "mistral/y")
    monkeypatch.delenv("LITELLM_MODEL_3", raising=False)

    assert gateway._build_model_chain() == ["gemini/x", "mistral/y"]


def test_t_gat_n_004_no_litellm_model_1_raises(monkeypatch):
    """T-GAT-N-004: _build_model_chain() raises RuntimeError when LITELLM_MODEL_1 is absent."""
    monkeypatch.delenv("LITELLM_MODEL_1", raising=False)

    with pytest.raises(RuntimeError):
        gateway._build_model_chain()


def test_t_gat_n_003_get_api_key_routes_per_provider(monkeypatch):
    """T-GAT-N-003: _get_api_key() returns the correct key per provider prefix."""
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestValidKeyForTestingOnly0000")
    monkeypatch.setenv("MISTRAL_API_KEY", "test-mistral-key-0000")

    assert gateway._get_api_key("gemini/gemini-2.5-flash") == "AIzaSyTestValidKeyForTestingOnly0000"
    assert gateway._get_api_key("mistral/mistral-small") == "test-mistral-key-0000"
    assert gateway._get_api_key("ollama/llama3") is None


def test_t_gat_n_005_get_api_key_routes_openrouter(monkeypatch):
    """T-GAT-N-005: _get_api_key() routes openrouter/ models to OPENROUTER_API_KEY."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key-0000")

    assert gateway._get_api_key("openrouter/openai/gpt-oss-120b:free") == "sk-or-test-key-0000"


def test_t_gat_n_006_scrub_secrets_redacts_openrouter_key(monkeypatch):
    """T-GAT-N-006: _scrub_secrets() replaces the OPENROUTER_API_KEY value with [REDACTED]."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key-0000")

    result = gateway._scrub_secrets("Error calling model: test-openrouter-key-0000 was rejected")

    assert "[REDACTED]" in result
    assert "test-openrouter-key-0000" not in result


def test_t_gat_s_001_api_key_never_appears_in_logs(tmp_path, monkeypatch, mocker, caplog):
    """T-GAT-S-001 (security, new): configured API key never leaks into log output, even on failure."""
    monkeypatch.chdir(tmp_path)
    _isolate_logs_dir(monkeypatch, tmp_path)
    _set_env(monkeypatch, overrides={"GEMINI_API_KEY": "AIzaSyTESTSECRETVALUE12345"})
    mocker.patch(
        "core.gateway.litellm.completion",
        side_effect=Exception("Invalid API key: AIzaSyTESTSECRETVALUE12345"),
    )

    with caplog.at_level("DEBUG"):
        with pytest.raises(Exception):
            gateway.llm_call("Summarize this.")

    assert "AIzaSyTESTSECRETVALUE12345" not in caplog.text


# ── T-GAT-N-007 ──────────────────────────────────────────────────────────────

def test_t_gat_n_007_get_api_key_routes_gemini_to_gemini_key_only(monkeypatch):
    """
    T-GAT-N-007: _get_api_key("gemini/...") returns GEMINI_API_KEY exclusively
    — no fallback to GOOGLE_API_KEY (CL-033: GOOGLE_API_KEY retired, its
    Google AI Studio project's credits were exhausted).
    """
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key-0000")
    monkeypatch.setenv("GOOGLE_API_KEY", "stale-google-key-should-not-be-used")

    assert gateway._get_api_key("gemini/gemini-2.0-flash") == "gemini-test-key-0000"


# ── T-GAT-N-008 ──────────────────────────────────────────────────────────────

def test_t_gat_n_008_scrub_secrets_redacts_gemini_key(monkeypatch):
    """T-GAT-N-008: _scrub_secrets() replaces the GEMINI_API_KEY value with [REDACTED]."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key-0000")

    result = gateway._scrub_secrets("Error calling model: test-gemini-key-0000 was rejected")

    assert "[REDACTED]" in result
    assert "test-gemini-key-0000" not in result


# ── T-GAT-N-009 ──────────────────────────────────────────────────────────────

def test_t_gat_n_009_env_litellm_model_2_not_shutdown_slug():
    """
    T-GAT-N-009: .env's LITELLM_MODEL_2 line does not reference the shut-down
    gemini-2.0-flash slug (CL-036 — third live run hit litellm.NotFoundError:
    "This model models/gemini-2.0-flash is no longer available." Google's
    model docs list gemini-2.0-flash under "Previous models — Shut down";
    gemini-2.5-flash is the stable replacement).

    Reads .env directly (model slug only, not any key value) rather than
    os.environ, since nothing in this test module loads dotenv.
    """
    env_lines = (PROJECT_ROOT / ".env").read_text().splitlines()
    model_2_lines = [line for line in env_lines if line.startswith("LITELLM_MODEL_2=")]
    assert model_2_lines, "Expected a LITELLM_MODEL_2= line in .env"
    assert "gemini-2.0-flash" not in model_2_lines[0], (
        f"LITELLM_MODEL_2 still references the shut-down gemini-2.0-flash slug: {model_2_lines[0]!r}"
    )


# ── T-GAT-N-010 ──────────────────────────────────────────────────────────────

def test_t_gat_n_010_env_model_chain_is_argon_then_flash():
    """
    T-GAT-N-010: .env model chain matches decisions D12/D14 (CL-068):
    LITELLM_MODEL_1 = vertex_ai/gemini-4-argon (primary, Pro tier) and
    LITELLM_MODEL_2 = vertex_ai/gemini-3.8-flash (fallback).
    History: CL-037 set gemini-2.5-flash-lite; CL-041 moved it to vertex_ai/.
    Reads .env directly (model slugs only, never secrets).
    """
    env_lines = (PROJECT_ROOT / ".env").read_text().splitlines()
    models = {line.split("=", 1)[0]: line.split("=", 1)[1].strip()
              for line in env_lines if line.startswith("LITELLM_MODEL_")}
    assert models.get("LITELLM_MODEL_1") == "vertex_ai/gemini-4-argon", models.get("LITELLM_MODEL_1")
    assert models.get("LITELLM_MODEL_2") == "vertex_ai/gemini-3.8-flash", models.get("LITELLM_MODEL_2")


# ── T-GAT-C-011 ──────────────────────────────────────────────────────────────

def test_t_gat_c_011_get_api_key_routes_flash_lite_to_gemini_key(monkeypatch):
    """
    T-GAT-C-011: _get_api_key("gemini/gemini-2.5-flash-lite") returns
    GEMINI_API_KEY — confirming the existing gemini/ prefix branch already
    covers the new MODEL_1 slug with zero gateway code changes (CL-037).
    """
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key-0000")

    assert gateway._get_api_key("gemini/gemini-2.5-flash-lite") == "gemini-test-key-0000"


# ── T-GAT-C-012 ──────────────────────────────────────────────────────────────

def test_t_gat_c_012_strip_fences_strips_json_fence():
    """
    T-GAT-C-012: _strip_fences() strips a ```json ... ``` wrapper (CL-039 —
    a sixth live run showed Gemini wrapping the lesson's JSON response in
    markdown fences on the direct litellm.completion() path, which
    json.loads() then rejected).
    """
    result = gateway._strip_fences('```json\n{"topic_name": "test"}\n```')
    assert result == '{"topic_name": "test"}', f"Expected fence-free JSON, got: {result!r}"


# ── T-GAT-C-013 ──────────────────────────────────────────────────────────────

def test_t_gat_c_013_strip_fences_strips_plain_fence():
    """T-GAT-C-013: _strip_fences() strips a ``` ... ``` wrapper with no language tag (CL-039)."""
    result = gateway._strip_fences('```\n{"topic_name": "test"}\n```')
    assert result == '{"topic_name": "test"}', f"Expected fence-free JSON, got: {result!r}"


# ── T-GAT-E-004 ──────────────────────────────────────────────────────────────

def test_t_gat_e_004_strip_fences_unchanged_when_no_fences():
    """
    T-GAT-E-004: _strip_fences() returns the input unchanged (modulo
    whitespace stripping) when no fences are present — zero cost for the
    common case where a model honours response_format and returns raw JSON.
    """
    result = gateway._strip_fences('{"topic_name": "test"}')
    assert result == '{"topic_name": "test"}', f"Expected unchanged text, got: {result!r}"


# ── T-GAT-E-005 ──────────────────────────────────────────────────────────────

def test_t_gat_e_005_strip_fences_handles_surrounding_whitespace():
    """
    T-GAT-E-005: _strip_fences() handles leading/trailing whitespace around
    fences — output is parseable JSON regardless of surrounding whitespace.
    """
    result = gateway._strip_fences('  ```json\n{"k": "v"}\n```  ')
    assert json.loads(result) == {"k": "v"}, f"Expected parseable JSON, got: {result!r}"


# ── T-GAT-C-014 ──────────────────────────────────────────────────────────────

def test_t_gat_c_014_llm_call_passes_response_format(tmp_path, monkeypatch, mocker):
    """
    T-GAT-C-014: llm_call() passes response_format={"type": "json_object"}
    to litellm.completion() — the primary CL-039 fix, instructing every
    provider in the failover chain to constrain output to raw JSON at the
    API level (LiteLLM translates this to each provider's native param).
    """
    monkeypatch.chdir(tmp_path)
    _isolate_logs_dir(monkeypatch, tmp_path)
    _set_env(monkeypatch)
    mock_completion = mocker.patch(
        "core.gateway.litellm.completion",
        return_value=_fake_response('{"status": "ok"}', "gemini/gemini-2.5-flash"),
    )

    gateway.llm_call("Summarize this.")

    assert mock_completion.call_args.kwargs.get("response_format") == {"type": "json_object"}, (
        f"Expected response_format={{'type': 'json_object'}}, got: {mock_completion.call_args}"
    )


# ── T-GAT-C-015 ──────────────────────────────────────────────────────────────

def test_t_gat_c_015_llm_call_strips_fences_from_response(tmp_path, monkeypatch, mocker):
    """
    T-GAT-C-015: llm_call() returns fence-stripped text even when the model
    returns fenced JSON — the CL-039 defensive layer, covering any provider
    that ignores response_format (e.g. some free-tier OpenRouter models).
    """
    monkeypatch.chdir(tmp_path)
    _isolate_logs_dir(monkeypatch, tmp_path)
    _set_env(monkeypatch)
    mocker.patch(
        "core.gateway.litellm.completion",
        return_value=_fake_response('```json\n{"status": "ok"}\n```', "gemini/gemini-2.5-flash"),
    )

    result = gateway.llm_call("Summarize this.")

    assert result["response"] == '{"status": "ok"}', (
        f"Expected fence-stripped response, got: {result['response']!r}"
    )


# ── T-GAT-N-011 ──────────────────────────────────────────────────────────────

def test_t_gat_n_011_get_api_key_returns_none_for_vertex_ai_flash_lite():
    """
    T-GAT-N-011: _get_api_key("vertex_ai/gemini-2.5-flash-lite") returns None
    — Vertex AI authenticates via GOOGLE_APPLICATION_CREDENTIALS (a service
    account JSON file path picked up automatically by Google ADC), not an
    api_key= string. Passing one would conflict with ADC and cause auth
    failure (CL-041 — MODEL_1 migrated from gemini/ AI Studio free quota to
    vertex_ai/, $300 GCP credit, 1000 RPM vs 15 RPM).
    """
    assert gateway._get_api_key("vertex_ai/gemini-2.5-flash-lite") is None


# ── T-GAT-N-012 ──────────────────────────────────────────────────────────────

def test_t_gat_n_012_get_api_key_returns_none_for_vertex_ai_flash():
    """T-GAT-N-012: _get_api_key("vertex_ai/gemini-2.5-flash") returns None (CL-041, MODEL_2)."""
    assert gateway._get_api_key("vertex_ai/gemini-2.5-flash") is None


# ── T-GAT-C-016 ──────────────────────────────────────────────────────────────

def test_t_gat_c_016_get_api_key_gemini_branch_preserved(monkeypatch):
    """
    T-GAT-C-016: _get_api_key("gemini/gemini-2.5-flash") still returns
    GEMINI_API_KEY — the gemini/ branch is kept as a fallback for AI Studio
    models even after CL-041's vertex_ai/ migration (regression guard).
    """
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key-0000")

    assert gateway._get_api_key("gemini/gemini-2.5-flash") == "gemini-test-key-0000"


# ── T-GAT-E-006 ──────────────────────────────────────────────────────────────

def test_t_gat_e_006_scrub_secrets_handles_missing_gemini_key(monkeypatch):
    """
    T-GAT-E-006: _scrub_secrets() does not raise when GEMINI_API_KEY is unset
    — GEMINI_API_KEY is optional after CL-051 (downgraded from REQUIRED) so
    the scrubber must stay safe whether it's set or not.
    """
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = gateway._scrub_secrets("Some error message with no secrets in it.")

    assert result == "Some error message with no secrets in it."


# ── T-GAT-C-017 ──────────────────────────────────────────────────────────────

def test_t_gat_c_017_get_api_key_returns_none_for_primary_vertex_model(monkeypatch):
    """
    T-GAT-C-017: _get_api_key() returns None for the primary model string
    "vertex_ai/gemini-2.5-flash-lite" — confirms the post-CL-051 default
    MODEL_1 has no api_key= passed to litellm.completion(), relying on
    GOOGLE_APPLICATION_CREDENTIALS/ADC for auth (DEV-I-006).

    Distinct from T-GAT-N-011 (flash-lite variant confirms MODEL_1 slug).
    """
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/tmp/test-sa.json")
    # GEMINI_API_KEY intentionally absent — confirms vertex_ai/ branch doesn't
    # fall through to gemini/ branch or return a stale key value
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    assert gateway._get_api_key("vertex_ai/gemini-2.5-flash-lite") is None, (
        "vertex_ai/ primary model must use ADC (None api_key=), not a key string"
    )


# ── T-GAT-S-002 ──────────────────────────────────────────────────────────────

def test_t_gat_s_002_scrub_secrets_redacts_sendgrid_key(monkeypatch):
    """
    T-GAT-S-002: _scrub_secrets() replaces the SENDGRID_API_KEY value with
    [REDACTED] (CL-041 — SENDGRID_API_KEY was never in the scrub loop; added
    alongside the vertex_ai/ migration's other gateway.py changes).
    """
    monkeypatch.setenv("SENDGRID_API_KEY", "SG.test-sendgrid-key-0000")

    result = gateway._scrub_secrets("Error calling delivery: SG.test-sendgrid-key-0000 was rejected")

    assert "[REDACTED]" in result
    assert "SG.test-sendgrid-key-0000" not in result


# ── T-GAT-C-018 ──────────────────────────────────────────────────────────────

def test_t_gat_c_018_openrouter_429_retries_once(mocker, monkeypatch):
    """
    T-GAT-C-018: _litellm_completion() retries once on OpenRouter RateLimitError
    before re-raising (CL-059).
    """
    from litellm.exceptions import RateLimitError

    mock_sleep = mocker.patch("core.gateway.time.sleep")
    mock_completion = mocker.patch("core.gateway.litellm.completion")
    mock_completion.side_effect = [
        RateLimitError(message="rate limited", llm_provider="openrouter", model="openrouter/x"),
        _fake_response('{"ok": true}', "openrouter/x"),
    ]

    result = gateway._litellm_completion(
        model="openrouter/openai/gpt-4o-mini:free",
        messages=[{"role": "user", "content": "hi"}],
    )

    assert mock_completion.call_count == 2
    mock_sleep.assert_called_once()
    assert result.choices[0].message.content == '{"ok": true}'
