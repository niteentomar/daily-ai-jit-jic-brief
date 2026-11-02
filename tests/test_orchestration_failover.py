"""
MODULE: test_orchestration_failover.py
PURPOSE: Test cases for core/orchestration.py run_agent() model failover
INPUTS: pytest fixtures (mocker)
OUTPUTS: Pass/fail assertions per TEST_REGISTRY T-ORC-N-* acceptance criteria
DEPENDENCIES: pytest, pytest-mock, core.orchestration, litellm.exceptions
RULE REFERENCES: R-002 (model failover), R-005 (max_iterations=5)
CHANGE LOG: 1.0.0 | 2026-06-17 | Bugfix tests: T-ORC-N-001, T-ORC-N-002 | Claude Code
            1.1.0 | 2026-06-17 | Added T-ORC-N-003 (Timeout triggers failover) | Claude Code
            1.2.0 | 2026-06-18 | CL-021 bugfix: patch target updated from
            create_react_agent to create_tool_calling_agent | Claude Code
            1.3.0 | 2026-06-18 | CL-022 added T-ORC-N-006 (APIConnectionError
            triggers failover), T-ORC-N-007 (NotFoundError triggers failover) —
            widened _FAILOVER_EXCEPTIONS after a live run crashed the whole
            pipeline on an uncaught APIConnectionError from a malformed
            tool-call response | Claude Code
            1.4.0 | 2026-06-22 | CL-032 added T-ORC-N-011 (a model content-
            refusal — HTTP 200 with "I'm unable..." instead of an exception —
            triggers failover via _is_refusal()/BadRequestError, the same way
            a real exception does) | Claude Code
            1.5.0 | 2026-06-26 | CL-055: failover mocks target
            run_litellm_tool_loop for gemini/ chain members (SDK path) | Claude Code
"""
from litellm.exceptions import APIConnectionError, NotFoundError, RateLimitError, Timeout

from core.orchestration import run_agent

_CHAIN = ["gemini/gemini-2.5-flash", "gemini/gemini-2.5-flash-lite", "ollama/llama3.2"]


def _rate_limit_error(model: str) -> RateLimitError:
    """Build a RateLimitError shaped like a real litellm failure, for test purposes."""
    return RateLimitError(message="rate limited", llm_provider="gemini", model=model)


def _patch_agent_internals(mocker):
    """Patch chain, LLM builder, SDK loop, and AgentExecutor for failover tests."""
    mocker.patch("core.orchestration._build_model_chain", return_value=_CHAIN)
    mock_build_llm = mocker.patch(
        "core.orchestration._build_llm_for_model", return_value=mocker.MagicMock()
    )
    mocker.patch("core.orchestration.create_tool_calling_agent", return_value=mocker.MagicMock())
    mock_sdk = mocker.patch("core.orchestration.run_litellm_tool_loop")
    mock_executor_cls = mocker.patch("core.orchestration.AgentExecutor")
    return mock_build_llm, mock_sdk, mock_executor_cls


# ── T-ORC-N-001 ──────────────────────────────────────────────────────────────

def test_t_orc_n_001_failover_tries_second_model(mocker):
    """T-ORC-N-001: first model raises RateLimitError -> second model is tried."""
    mock_build_llm, mock_sdk, _ = _patch_agent_internals(mocker)
    mock_sdk.side_effect = [
        _rate_limit_error(_CHAIN[0]),
        {"output": "success on second model", "intermediate_steps": [("search", "ok")]},
    ]

    result = run_agent(tools=[], prompt="Test prompt.", model=_CHAIN[0])

    assert result["output"] == "success on second model"
    called_models = [call.args[0] for call in mock_build_llm.call_args_list]
    assert _CHAIN[1] in called_models, (
        f"Expected second model {_CHAIN[1]!r} to be tried, got calls: {called_models}"
    )


# ── T-ORC-N-002 ──────────────────────────────────────────────────────────────

def test_t_orc_n_002_all_models_exhausted_returns_error(mocker):
    """T-ORC-N-002: every model in the chain raises -> return dict has 'error' key."""
    _, mock_sdk, mock_executor_cls = _patch_agent_internals(mocker)
    mock_sdk.side_effect = [_rate_limit_error(m) for m in _CHAIN[:2]]
    mock_executor_cls.return_value.invoke.side_effect = _rate_limit_error(_CHAIN[2])

    result = run_agent(tools=[], prompt="Test prompt.", model=_CHAIN[0])

    assert "error" in result, f"Expected 'error' key in result, got: {result}"
    assert result["output"] == "All models exhausted"


# ── T-ORC-N-003 ──────────────────────────────────────────────────────────────

def test_t_orc_n_003_timeout_triggers_failover(mocker):
    """T-ORC-N-003: first model raises litellm.exceptions.Timeout -> second model is tried."""
    mock_build_llm, mock_sdk, _ = _patch_agent_internals(mocker)
    mock_sdk.side_effect = [
        Timeout(message="timed out", model=_CHAIN[0], llm_provider="gemini"),
        {"output": "success on second model", "intermediate_steps": [("search", "ok")]},
    ]

    result = run_agent(tools=[], prompt="Test prompt.", model=_CHAIN[0])

    assert result["output"] == "success on second model"
    called_models = [call.args[0] for call in mock_build_llm.call_args_list]
    assert _CHAIN[1] in called_models, (
        f"Expected second model {_CHAIN[1]!r} to be tried, got calls: {called_models}"
    )


# ── T-ORC-N-006 ──────────────────────────────────────────────────────────────

def test_t_orc_n_006_api_connection_error_triggers_failover(mocker):
    """
    T-ORC-N-006: first model raises litellm.exceptions.APIConnectionError ->
    second model is tried. A live run crashed the whole pipeline when a
    malformed tool-call response from an OpenRouter model surfaced as this
    exception type, which was previously absent from _FAILOVER_EXCEPTIONS.
    """
    mock_build_llm, mock_sdk, _ = _patch_agent_internals(mocker)
    mock_sdk.side_effect = [
        APIConnectionError(message="connection failed", llm_provider="gemini", model=_CHAIN[0]),
        {"output": "success on second model", "intermediate_steps": [("search", "ok")]},
    ]

    result = run_agent(tools=[], prompt="Test prompt.", model=_CHAIN[0])

    assert result["output"] == "success on second model"
    called_models = [call.args[0] for call in mock_build_llm.call_args_list]
    assert _CHAIN[1] in called_models, (
        f"Expected second model {_CHAIN[1]!r} to be tried, got calls: {called_models}"
    )


# ── T-ORC-N-011 ──────────────────────────────────────────────────────────────

def test_t_orc_n_011_content_refusal_triggers_failover(mocker):
    """
    T-ORC-N-011: first model returns an HTTP-200 content-refusal string (no
    exception raised by litellm/AgentExecutor) -> _invoke_once() detects it
    via _is_refusal() and raises BadRequestError, triggering the existing
    failover loop to the second model, which returns valid JSON.
    """
    mock_build_llm, mock_sdk, _ = _patch_agent_internals(mocker)
    mock_sdk.side_effect = [
        {"output": "I'm unable to complete this task.", "intermediate_steps": []},
        {"output": '{"topic": "valid"}', "intermediate_steps": [("search", "ok")]},
    ]

    result = run_agent(tools=[], prompt="Test prompt.", model=_CHAIN[0])

    assert result["output"] == '{"topic": "valid"}'
    called_models = [call.args[0] for call in mock_build_llm.call_args_list]
    assert _CHAIN[1] in called_models, (
        f"Expected second model {_CHAIN[1]!r} to be tried, got calls: {called_models}"
    )


# ── T-ORC-N-007 ──────────────────────────────────────────────────────────────

def test_t_orc_n_007_not_found_error_triggers_failover(mocker):
    """T-ORC-N-007: first model raises litellm.exceptions.NotFoundError -> second model is tried."""
    mock_build_llm, mock_sdk, _ = _patch_agent_internals(mocker)
    mock_sdk.side_effect = [
        NotFoundError(message="model not found", model=_CHAIN[0], llm_provider="gemini"),
        {"output": "success on second model", "intermediate_steps": [("search", "ok")]},
    ]

    result = run_agent(tools=[], prompt="Test prompt.", model=_CHAIN[0])

    assert result["output"] == "success on second model"
    called_models = [call.args[0] for call in mock_build_llm.call_args_list]
    assert _CHAIN[1] in called_models, (
        f"Expected second model {_CHAIN[1]!r} to be tried, got calls: {called_models}"
    )
