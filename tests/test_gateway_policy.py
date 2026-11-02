"""
MODULE: test_gateway_policy.py
PURPOSE: CL-063 gateway policy: Vertex kwargs, classified retries, finish-reason checks,
         chain fallback, cost guard, network wait. Mirrors the API audit (2026-11-01).
CHANGE LOG: 1.0.0 | 2026-11-01 | CL-063 | Claude Code
"""
import json
from types import SimpleNamespace

import pytest
from litellm import exceptions as llm_exc

from core import gateway, run_logger


def _resp(content="ok", finish="stop", tool_calls=None):
    msg = SimpleNamespace(content=content, tool_calls=tool_calls)
    usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15, completion_tokens_details=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg, finish_reason=finish)], usage=usage)


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("LITELLM_MODEL_1", "vertex_ai/gemini-4-argon")
    monkeypatch.setenv("LITELLM_MODEL_2", "vertex_ai/gemini-3.8-flash")
    monkeypatch.delenv("LITELLM_MODEL_3", raising=False)
    monkeypatch.delenv("LLM_MAX_RETRIES", raising=False)
    monkeypatch.setattr(gateway, "_LOGS_DIR", str(tmp_path))


def _err(cls, status):
    return cls(message=f"HTTP {status}", model="m", llm_provider="vertex_ai")


def test_t_gat_c_020_vertex_kwargs_global_medium_timeout(mocker):
    """T-GAT-C-020 (D12, D13): vertex_location=global, reasoning_effort=medium, timeout 180, stream False, no api_key."""
    m = mocker.patch("core.gateway.litellm.completion", return_value=_resp())
    gateway.call_model("vertex_ai/gemini-4-argon", [{"role": "user", "content": "hi"}], stage="t")
    kw = m.call_args.kwargs
    assert kw["vertex_location"] == "global" and kw["reasoning_effort"] == "medium"
    assert kw["timeout"] == 180 and kw["stream"] is False and "api_key" not in kw
    assert "temperature" not in kw, "Gemini 3/4: keep default temperature 1.0"


def test_t_gat_c_021_retryable_429_retried_then_succeeds(mocker):
    """T-GAT-C-021: 429 is retried on the same model (max 2 retries)."""
    m = mocker.patch("core.gateway.litellm.completion",
                     side_effect=[_err(llm_exc.RateLimitError, 429), _err(llm_exc.RateLimitError, 429), _resp("done")])
    r = gateway.call_model("vertex_ai/gemini-4-argon", [], stage="t")
    assert r.choices[0].message.content == "done" and m.call_count == 3


def test_t_gat_n_020_fatal_404_not_retried(mocker):
    """T-GAT-N-020: 404 (wrong model/region) fails fast: exactly one call."""
    m = mocker.patch("core.gateway.litellm.completion", side_effect=_err(llm_exc.NotFoundError, 404))
    with pytest.raises(gateway.ModelCallError) as ei:
        gateway.call_model("vertex_ai/gemini-4-argon", [], stage="t")
    assert m.call_count == 1 and ei.value.retryable is False


def test_t_gat_n_021_truncation_is_an_error(mocker):
    """T-GAT-N-021: finish_reason=length (probe: silent 9-char output) raises TruncatedOutputError after retries."""
    mocker.patch("core.gateway.litellm.completion", return_value=_resp("partial", finish="length"))
    with pytest.raises(gateway.ModelCallError):
        gateway.call_model("vertex_ai/gemini-4-argon", [], stage="t")


def test_t_gat_n_022_empty_output_and_safety_block_are_errors(mocker):
    """T-GAT-N-022: empty content or content_filter are failures, not silent successes."""
    mocker.patch("core.gateway.litellm.completion", return_value=_resp("", finish="stop"))
    with pytest.raises(gateway.ModelCallError):
        gateway.call_model("vertex_ai/gemini-4-argon", [], stage="t")
    mocker.patch("core.gateway.litellm.completion", return_value=_resp("x", finish="content_filter"))
    with pytest.raises(gateway.ModelCallError):
        gateway.call_model("vertex_ai/gemini-4-argon", [], stage="t")


def test_t_gat_c_022_fallback_to_3_8_flash_after_primary_fails(mocker):
    """T-GAT-C-022 (D14): primary exhausted -> gemini-3.8-flash used; fallback flagged on the run."""
    calls = []

    def fake(**kw):
        calls.append(kw["model"])
        if kw["model"].endswith("argon"):
            raise _err(llm_exc.ServiceUnavailableError, 503)
        return _resp("from flash")

    mocker.patch("core.gateway.litellm.completion", side_effect=fake)
    ctx = run_logger.start_run(":memory:", "full")
    resp, model = gateway.call_with_fallback([{"role": "user", "content": "x"}], stage="t")
    assert model == "vertex_ai/gemini-3.8-flash" and calls.count("vertex_ai/gemini-4-argon") == 3
    assert ctx.summary["fallback_used"] == 1


def test_t_gat_c_023_llm_call_with_schema_returns_parsed(mocker):
    """T-GAT-C-023: schema -> response_format json_schema and parsed dict returned."""
    m = mocker.patch("core.gateway.litellm.completion", return_value=_resp(json.dumps({"a": 1})))
    out = gateway.llm_call("p", schema={"type": "object"}, stage="lesson")
    assert out["parsed"] == {"a": 1}
    assert m.call_args.kwargs["response_format"]["type"] == "json_schema"


def test_t_gat_n_023_daily_cost_guard_blocks_calls(mocker, monkeypatch):
    """T-GAT-N-023: once run cost passes DAILY_COST_LIMIT_USD no more model calls are made."""
    monkeypatch.setenv("DAILY_COST_LIMIT_USD", "1.0")
    m = mocker.patch("core.gateway.litellm.completion", return_value=_resp())
    ctx = run_logger.start_run(":memory:", "full")
    ctx.summary["cost_usd"] = 1.5
    with pytest.raises(gateway.DailyCostExceededError):
        gateway.call_with_fallback([], stage="t")
    m.assert_not_called()


def test_t_gat_c_024_wait_for_network_polls_until_dns_resolves(mocker):
    """T-GAT-C-024: DNS failure then success -> returns True after one wait (laptop waking)."""
    mocker.patch("core.gateway.socket.getaddrinfo", side_effect=[OSError("no dns"), [("ok",)]])
    sleeps = []
    assert gateway.wait_for_network(max_wait=60, interval=15, sleep=sleeps.append) is True
    assert sleeps == [15]


def test_t_gat_n_024_wait_for_network_gives_up(mocker):
    """T-GAT-N-024: network never returns -> False after max_wait."""
    mocker.patch("core.gateway.socket.getaddrinfo", side_effect=OSError("no dns"))
    assert gateway.wait_for_network(max_wait=30, interval=15, sleep=lambda s: None) is False


def test_t_gat_c_025_classify_error_matrix():
    """T-GAT-C-025: Google guidance: retry 429/5xx/timeout; never 400/401/403/404."""
    assert gateway.classify_error(_err(llm_exc.RateLimitError, 429)) == "retryable"
    assert gateway.classify_error(_err(llm_exc.InternalServerError, 500)) == "retryable"
    assert gateway.classify_error(llm_exc.Timeout(message="t", model="m", llm_provider="x")) == "retryable"
    for cls in (llm_exc.BadRequestError, llm_exc.AuthenticationError, llm_exc.NotFoundError):
        assert gateway.classify_error(_err(cls, 400)) == "fatal"


def test_t_gat_s_020_errors_recorded_without_secrets(mocker, monkeypatch, tmp_path):
    """T-GAT-S-020: failed attempts are logged to run_errors with secrets scrubbed."""
    import sqlite3
    from scripts.setup_db import init_db
    db = str(tmp_path / "l.db")
    init_db(db)
    monkeypatch.setenv("EXA_API_KEY", "exa-secret-value-123456")
    mocker.patch("core.gateway.litellm.completion",
                 side_effect=_err(llm_exc.NotFoundError, 404).__class__(message="bad exa-secret-value-123456",
                                                                       model="m", llm_provider="v"))
    run_logger.start_run(db, "full")
    with pytest.raises(gateway.ModelCallError):
        gateway.call_model("vertex_ai/gemini-4-argon", [], stage="lesson")
    rows = sqlite3.connect(db).execute("SELECT message, error_class FROM run_errors").fetchall()
    assert rows and "exa-secret-value-123456" not in rows[0][0] and rows[0][1] == "NotFoundError"
