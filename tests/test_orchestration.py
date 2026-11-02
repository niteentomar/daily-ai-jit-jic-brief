"""
MODULE: test_orchestration.py
PURPOSE: Test cases for core/orchestration.py — LangChain ReACT agent wrapper
INPUTS: pytest fixtures (mocker, caplog)
OUTPUTS: Pass/fail assertions per TEST_REGISTRY T-ORC-*, T-TRC-* acceptance criteria
DEPENDENCIES: pytest, pytest-mock, core.orchestration
RULE REFERENCES: R-005 (max_iterations=5 hard stop)
CHANGE LOG: 1.0.0 | 2026-06-16 | TC-004 initial tests | Claude Code
             1.1.0 | 2026-06-17 | TC-010 added T-TRC-C-001 (run_name propagated to
             executor.invoke config for LangSmith trace labelling) | Claude Code
             1.2.0 | 2026-06-18 | CL-021 bugfix: patch target updated from
             create_react_agent to create_tool_calling_agent (orchestration.py
             switched from text-based ReACT parsing to native tool calling —
             modern models emit function-calling tokens the ReACT parser
             couldn't consume). T-ORC-C-001's mock exhaustion signal changed
             from the ReACT stop-phrase string to output=None, matching the
             new R-005 check. Added T-ORC-C-002, T-ORC-N-004 | Claude Code
             1.3.0 | 2026-06-18 | CL-022 added T-ORC-C-005 (_build_llm_for_model
             with an openrouter/ model returns ChatLiteLLM with OPENROUTER_API_KEY
             in model_kwargs) — OpenRouter is now LITELLM_MODEL_1/2/3 in .env
             but had no provider branch in _build_llm_for_model() | Claude Code
             1.4.0 | 2026-06-22 | CL-032 added T-ORC-C-006/007 (_is_refusal
             returns False for valid JSON output), T-ORC-N-008/009/010
             (_is_refusal detects 3 distinct refusal-prefix patterns) — free-tier
             models sometimes return HTTP 200 with a refusal string instead of
             raising an exception, so the existing failover loop never fired.
             Used T-ORC- (not T-ORCH-) to match this project's existing ID
             format | Claude Code
             1.5.0 | 2026-06-22 | CL-038 added T-ORC-N-012/013/014 (_is_refusal
             now catches conversational openers "i can help"/"let me" plus
             non-JSON prose >= 40 chars via a new layer-2 detector),
             T-ORC-C-008/009/010 (_is_refusal still False for valid JSON
             array/object/empty string on the new two-layer implementation),
             T-ORC-N-015 (_invoke_once raises BadRequestError on >=3
             consecutive empty-output tool-call steps — the original,
             narrower CL-038 target), T-ORC-C-011 (_invoke_once does not
             raise when intermediate_steps have real content), T-ORC-C-012
             (system prompt mandates tool use and forbids prose). A fifth
             live run showed Flash-Lite responding conversationally
             ("I can help you find...") instead of JSON, undetected by the
             CL-032 refusal prefixes | Claude Code
             1.6.0 | 2026-06-24 | CL-046 added T-ORC-N-016/017 (_invoke_once
             raises BadRequestError when intermediate_steps=[] and
             output is None/"" — a live run showed Gemini returning zero
             tool calls and zero text on the very first turn; confirmed via
             the installed langchain==0.3.7 source
             (agents/output_parsers/tools.py: parse_ai_message_to_tool_action)
             that ToolsAgentOutputParser returns AgentFinish immediately in
             this case, regardless of max_iterations — neither existing gate
             covered it), T-ORC-C-013 (regression: zero output but non-empty
             intermediate_steps does NOT raise — scopes the new gate to
             truly-zero-step turns, not an in-progress agent). Updated
             T-ORC-C-001/T-ORC-N-004's mocks to include a real
             intermediate_steps entry — without one, both were
             indistinguishable from the new zero-step failure mode and would
             have made run_agent() attempt real failover instead of
             returning the partial result they test for | Claude Code
             1.7.0 | 2026-06-25 | CL-050: added T-ORC-C-020/021/022 (CL-049
             streaming=False for gemini/, vertex_ai/, NOT openrouter/),
             T-ORC-C-023 (langchain_litellm import), T-ORC-N-024 (no
             langchain_community import in orchestration.py), T-ORC-N-025/026
             (CL-050B MALFORMED guard fires on non-empty steps + empty output/
             None), T-ORC-C-027/028 (MALFORMED guard does not fire on valid JSON
             output), T-ORC-N-029 (CL-046 zero-step gate still fires after
             CL-050B addition). Updated T-ORC-C-013: CL-046 gate scoped to
             empty steps only; CL-050B now fires when steps non-empty + output
             empty — T-ORC-C-013 updated to use non-empty output (happy path
             regression for both gates) | Claude Code
             1.8.0 | 2026-06-25 | CL-051: updated T-ORC-C-005 comment and
             T-ORC-C-020/021 mock setup to confirm vertex_ai/ as primary model
             prefix after Vertex-only migration | Claude Code
             1.9.0 | 2026-06-26 | CL-055: T-ORC-C-030/031 dispatch tests,
             T-ORC-N-030/031 SDK-path guard tests | Claude Code
"""
import pytest

from litellm.exceptions import BadRequestError, ServiceUnavailableError

from core.orchestration import (
    MAX_ITERATIONS,
    _FAILOVER_EXCEPTIONS,
    _apply_invoke_guards,
    _build_llm_for_model,
    _invoke_once,
    _is_refusal,
    _strip_agent_fences,
    run_agent,
)


# ── T-ORC-C-001 ──────────────────────────────────────────────────────────────

def test_t_orc_c_001_max_iterations_enforced(mocker, caplog):
    """
    T-ORC-C-001: AgentExecutor created with max_iterations=5; truncation logged on limit hit.

    intermediate_steps includes one real (non-empty) step (CL-046) — genuine
    R-005 exhaustion happens after the agent has taken real action across
    multiple turns, not on the very first turn with nothing at all. Without
    a populated intermediate_steps, this mock is indistinguishable from
    CL-046's new zero-step-empty-output failure mode, which would make
    run_agent() attempt real failover instead of returning the partial
    result this test expects.
    """
    mocker.patch("core.orchestration.create_tool_calling_agent", return_value=mocker.MagicMock())
    mock_executor_cls = mocker.patch("core.orchestration.AgentExecutor")
    # Simulate iteration exhaustion under create_tool_calling_agent: output is None, not a stop phrase
    mock_executor_cls.return_value.invoke.return_value = {
        "output": None,
        "intermediate_steps": [(mocker.MagicMock(), "some real search result")],
    }

    with caplog.at_level("WARNING"):
        result = run_agent(
            llm=mocker.MagicMock(),
            tools=[],
            prompt="Summarise today's AI news.",
        )

    # AgentExecutor must be constructed with max_iterations=MAX_ITERATIONS (R-005)
    _, kwargs = mock_executor_cls.call_args
    assert kwargs.get("max_iterations") == MAX_ITERATIONS

    # Result is a dict (partial results returned, not an exception)
    assert isinstance(result, dict)
    assert "output" in result

    # Truncation must be logged as a WARNING
    assert any("iteration" in record.message.lower() for record in caplog.records)


# ── T-TRC-C-001 ──────────────────────────────────────────────────────────────

def test_t_trc_c_001_run_agent_passes_run_name_to_invoke(mocker):
    """
    T-TRC-C-001: run_agent() propagates run_name into executor.invoke() config.

    Acceptance criteria:
      - executor.invoke() receives a 'config' keyword argument
      - config["run_name"] equals the run_name value passed to run_agent()
    """
    mocker.patch("core.orchestration.create_tool_calling_agent", return_value=mocker.MagicMock())
    mock_executor_cls = mocker.patch("core.orchestration.AgentExecutor")
    mock_executor_cls.return_value.invoke.return_value = {"output": "done"}

    run_agent(
        llm=mocker.MagicMock(),
        tools=[],
        prompt="Test prompt.",
        run_name="test-run",
    )

    _, invoke_kwargs = mock_executor_cls.return_value.invoke.call_args
    assert "config" in invoke_kwargs, (
        "executor.invoke() must receive a 'config' kwarg for LangSmith trace labelling"
    )
    assert invoke_kwargs["config"]["run_name"] == "test-run", (
        f"Expected run_name='test-run' in config, got: {invoke_kwargs['config']}"
    )


# ── T-ORC-C-002 ──────────────────────────────────────────────────────────────

def test_t_orc_c_002_invoke_once_succeeds_with_tool_calling_agent(mocker):
    """
    T-ORC-C-002: _invoke_once() with a bind_tools()-capable llm succeeds and
    returns a dict with an "output" key (create_tool_calling_agent path).
    """
    mock_llm = mocker.MagicMock()
    mock_llm.bind_tools = mocker.MagicMock()
    mocker.patch("core.orchestration.create_tool_calling_agent", return_value=mocker.MagicMock())
    mock_executor_cls = mocker.patch("core.orchestration.AgentExecutor")
    mock_executor_cls.return_value.invoke.return_value = {"output": '{"result": "ok"}'}

    result = _invoke_once(mock_llm, [], "Test prompt.", 5, "test-run")

    assert "output" in result
    assert result["output"] == '{"result": "ok"}'


# ── T-ORC-N-004 ──────────────────────────────────────────────────────────────

def test_t_orc_n_004_invoke_once_logs_r005_warning_then_raises_on_empty_output(mocker, caplog):
    """
    T-ORC-N-004: _invoke_once() logs a R-005 WARNING when output=None (iteration
    exhaustion), then raises BadRequestError via the CL-050B MALFORMED guard.

    With CL-050B in place: when output=None and intermediate_steps is non-empty,
    the code first logs "R-005: agent hit max_iterations" (step 2), then the
    MALFORMED_FUNCTION_CALL guard fires (step 8) since intermediate_steps is
    non-empty and raw_output="". Both behaviors are confirmed in one test:
    1. R-005 WARNING is logged (iteration log still fires before the guard)
    2. BadRequestError is raised (CL-050B, triggers failover)

    intermediate_steps includes one real (non-empty) step — without it, the
    CL-046 zero-step gate (not CL-050B) would fire, and the warning would not
    have been logged.
    """
    mock_llm = mocker.MagicMock()
    mocker.patch("core.orchestration.create_tool_calling_agent", return_value=mocker.MagicMock())
    mock_executor_cls = mocker.patch("core.orchestration.AgentExecutor")
    mock_executor_cls.return_value.invoke.return_value = {
        "output": None,
        "intermediate_steps": [(mocker.MagicMock(), "some real search result")],
    }

    with caplog.at_level("WARNING"):
        with pytest.raises(BadRequestError):
            _invoke_once(mock_llm, [], "Test prompt.", 5, "test-run")

    # R-005 warning must have been logged before the CL-050B guard raised
    assert any("iteration" in record.message.lower() for record in caplog.records)


# ── T-ORC-C-005 ──────────────────────────────────────────────────────────────

def test_t_orc_c_005_build_llm_for_model_openrouter(monkeypatch):
    """
    T-ORC-C-005: _build_llm_for_model() with an openrouter/ model returns a
    ChatLiteLLM instance with OPENROUTER_API_KEY in model_kwargs.
    """
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key-0000")

    llm = _build_llm_for_model("openrouter/openai/gpt-oss-120b:free")

    assert llm.model_kwargs.get("api_key") == "sk-or-test-key-0000", (
        f"Expected model_kwargs['api_key'] == 'sk-or-test-key-0000', got: {llm.model_kwargs!r}"
    )


# ── T-ORC-N-008 ──────────────────────────────────────────────────────────────

def test_t_orc_n_008_is_refusal_detects_im_unable():
    """T-ORC-N-008: _is_refusal() detects "I'm unable..." as a content-refusal."""
    assert _is_refusal("I'm unable to complete this task.") is True


# ── T-ORC-N-009 ──────────────────────────────────────────────────────────────

def test_t_orc_n_009_is_refusal_detects_i_cannot():
    """T-ORC-N-009: _is_refusal() detects "I cannot..." as a content-refusal."""
    assert _is_refusal("I cannot search the web.") is True


# ── T-ORC-N-010 ──────────────────────────────────────────────────────────────

def test_t_orc_n_010_is_refusal_detects_as_an_ai():
    """T-ORC-N-010: _is_refusal() detects "As an AI..." as a content-refusal."""
    assert _is_refusal("As an AI, I don't have access to real-time search.") is True


# ── T-ORC-C-006 ──────────────────────────────────────────────────────────────

def test_t_orc_c_006_is_refusal_false_for_json_array():
    """T-ORC-C-006: _is_refusal() returns False for valid JIT/JIC-shaped JSON output."""
    assert _is_refusal('[{"topic": "foo"}]') is False


# ── T-ORC-C-007 ──────────────────────────────────────────────────────────────

def test_t_orc_c_007_is_refusal_false_for_json_object():
    """T-ORC-C-007: _is_refusal() returns False for valid lesson-shaped JSON output."""
    assert _is_refusal('{"topic_name": "MoE"}') is False


# ── T-ORC-N-012 ──────────────────────────────────────────────────────────────

def test_t_orc_n_012_is_refusal_detects_i_can_help(mocker):
    """
    T-ORC-N-012: _is_refusal() detects "I can help..." as a content-refusal
    (CL-038 — a live run showed Flash-Lite responding "I can help you find
    the latest AI news." instead of JSON; the CL-032 refusal prefixes didn't
    cover conversational openers like this).
    """
    assert _is_refusal("I can help you find the latest AI news.") is True


# ── T-ORC-N-013 ──────────────────────────────────────────────────────────────

def test_t_orc_n_013_is_refusal_detects_let_me(mocker):
    """T-ORC-N-013: _is_refusal() detects "Let me..." as a content-refusal (CL-038)."""
    assert _is_refusal("Let me search for recent AI developments.") is True


# ── T-ORC-N-014 ──────────────────────────────────────────────────────────────

def test_t_orc_n_014_is_refusal_detects_non_json_prose():
    """
    T-ORC-N-014: _is_refusal() detects non-JSON prose >= 40 chars as a
    content-refusal via its new layer-2 detector, even when the text doesn't
    match any known prefix (CL-038 — catches conversational summaries that
    don't start with a recognised opener).
    """
    assert _is_refusal(
        "The latest developments in AI include several breakthroughs."
    ) is True


# ── T-ORC-C-008 ──────────────────────────────────────────────────────────────

def test_t_orc_c_008_is_refusal_false_for_json_array_with_real_content():
    """
    T-ORC-C-008: _is_refusal() still returns False for valid JIT-shaped JSON
    output after the CL-038 two-layer rewrite (regression guard, distinct
    example from T-ORC-C-006).
    """
    assert _is_refusal('[{"topic": "MCP", "source": "openai.com"}]') is False


# ── T-ORC-C-009 ──────────────────────────────────────────────────────────────

def test_t_orc_c_009_is_refusal_false_for_json_object_with_real_content():
    """
    T-ORC-C-009: _is_refusal() still returns False for valid lesson-shaped
    JSON output after the CL-038 two-layer rewrite (regression guard,
    distinct example from T-ORC-C-007).
    """
    assert _is_refusal('{"topic_name": "Vector Databases"}') is False


# ── T-ORC-C-010 ──────────────────────────────────────────────────────────────

def test_t_orc_c_010_is_refusal_false_for_empty_string():
    """
    T-ORC-C-010: _is_refusal() returns False for an empty string — empty
    output is the empty-tool-call-loop signal (CL-038 Root Cause D), handled
    separately by _detect_empty_tool_loop(), not by _is_refusal().
    """
    assert _is_refusal("") is False


# ── T-ORC-N-015 ──────────────────────────────────────────────────────────────

def test_t_orc_n_015_invoke_once_raises_on_empty_tool_loop(mocker):
    """
    T-ORC-N-015: _invoke_once() raises BadRequestError when intermediate_steps
    shows >=3 consecutive empty-output tool-call steps (CL-038 Root Cause D
    — confirmed with gpt-oss-120b:free on OpenRouter: finish_reason='tool_calls'
    with content='' on every iteration, no exception, no refusal string, so
    the agent silently exhausts max_iter and the existing failover never fires).
    """
    from litellm.exceptions import BadRequestError

    mock_llm = mocker.MagicMock()
    mocker.patch("core.orchestration.create_tool_calling_agent", return_value=mocker.MagicMock())
    mock_executor_cls = mocker.patch("core.orchestration.AgentExecutor")
    mock_executor_cls.return_value.invoke.return_value = {
        "output": None,
        "intermediate_steps": [
            (mocker.MagicMock(), ""),
            (mocker.MagicMock(), ""),
            (mocker.MagicMock(), ""),
        ],
    }

    with pytest.raises(BadRequestError):
        _invoke_once(mock_llm, [], "Test prompt.", 5, "test-run")


# ── T-ORC-C-011 ──────────────────────────────────────────────────────────────

def test_t_orc_c_011_invoke_once_does_not_raise_with_real_content(mocker):
    """
    T-ORC-C-011: _invoke_once() does NOT raise when intermediate_steps have
    real (non-empty) content — regression guard for the CL-038 empty-tool-loop
    detector, confirming it doesn't false-positive on a normal successful run.
    """
    mock_llm = mocker.MagicMock()
    mocker.patch("core.orchestration.create_tool_calling_agent", return_value=mocker.MagicMock())
    mock_executor_cls = mocker.patch("core.orchestration.AgentExecutor")
    mock_executor_cls.return_value.invoke.return_value = {
        "output": '[{"topic": "test"}]',
        "intermediate_steps": [(mocker.MagicMock(), "search result here")],
    }

    result = _invoke_once(mock_llm, [], "Test prompt.", 5, "test-run")

    assert result.get("output") == '[{"topic": "test"}]'


# ── T-ORC-C-012 ──────────────────────────────────────────────────────────────

def test_t_orc_c_012_system_prompt_mandates_tool_use(mocker):
    """
    T-ORC-C-012: _invoke_once()'s system prompt mandates tool use before
    answering, forbids conversational replies, and restricts output to JSON
    only (CL-038 Root Cause C — the prior prompt's weak hint, "Always return
    your final answer as valid JSON," let Flash-Lite respond conversationally
    or summarise tool results in prose instead of the requested schema).

    Note: the originating acceptance criteria named the literal substring
    "only valid output is a JSON", but the specified wording is "Your ONLY
    valid final output is a JSON array or JSON object..." — asserting on the
    actual phrase (case-sensitive "ONLY", includes "final").
    """
    mock_llm = mocker.MagicMock()
    mock_create_agent = mocker.patch(
        "core.orchestration.create_tool_calling_agent", return_value=mocker.MagicMock()
    )
    mock_executor_cls = mocker.patch("core.orchestration.AgentExecutor")
    mock_executor_cls.return_value.invoke.return_value = {"output": "[]", "intermediate_steps": []}

    _invoke_once(mock_llm, [], "Test prompt.", 5, "test-run")
    chat_prompt = mock_create_agent.call_args.args[2]
    system_message = chat_prompt.messages[0].prompt.template
    assert "MUST use" in system_message, (
        f"Expected 'MUST use' in system message, got: {system_message!r}"
    )
    assert "Do NOT respond conversationally" in system_message, (
        f"Expected 'Do NOT respond conversationally' in system message, got: {system_message!r}"
    )
    assert "ONLY valid final output is a JSON" in system_message, (
        f"Expected 'ONLY valid final output is a JSON' in system message, got: {system_message!r}"
    )


# ── T-ORC-N-016 ──────────────────────────────────────────────────────────────

def test_t_orc_n_016_invoke_once_raises_on_zero_steps_none_output(mocker):
    """
    T-ORC-N-016: _invoke_once() raises BadRequestError when intermediate_steps
    is empty AND output is None — zero tool calls, no final answer at all, on
    the very first turn (CL-046). Confirmed via the installed langchain==0.3.7
    source (langchain/agents/output_parsers/tools.py,
    parse_ai_message_to_tool_action): when message.tool_calls is empty,
    ToolsAgentOutputParser returns AgentFinish(return_values={"output":
    message.content}, ...) immediately — a plain return, not an exception —
    regardless of max_iterations. Neither _is_refusal() (needs non-empty
    text) nor _detect_empty_tool_loop() (needs >=3 steps present) catches
    this shape, so without this gate the empty result would silently reach
    json.loads() in _run_jit_agent()/_run_jic_agent().
    """
    from litellm.exceptions import BadRequestError

    mock_llm = mocker.MagicMock()
    mocker.patch("core.orchestration.create_tool_calling_agent", return_value=mocker.MagicMock())
    mock_executor_cls = mocker.patch("core.orchestration.AgentExecutor")
    mock_executor_cls.return_value.invoke.return_value = {
        "output": None,
        "intermediate_steps": [],
    }

    with pytest.raises(BadRequestError):
        _invoke_once(mock_llm, [], "Test prompt.", 5, "test-run")


# ── T-ORC-N-017 ──────────────────────────────────────────────────────────────

def test_t_orc_n_017_invoke_once_raises_on_zero_steps_empty_string_output(mocker):
    """
    T-ORC-N-017: _invoke_once() raises BadRequestError when intermediate_steps
    is empty AND output is "" — the exact shape reproduced from a live run's
    direct _invoke_once() call with the real JIT prompt (CL-046). Same gate
    as T-ORC-N-016; both None and "" must be caught since
    `result.get("output", "")` downstream defaults missing keys to "" while
    AgentFinish can also carry a literal empty string in message.content.
    """
    from litellm.exceptions import BadRequestError

    mock_llm = mocker.MagicMock()
    mocker.patch("core.orchestration.create_tool_calling_agent", return_value=mocker.MagicMock())
    mock_executor_cls = mocker.patch("core.orchestration.AgentExecutor")
    mock_executor_cls.return_value.invoke.return_value = {
        "output": "",
        "intermediate_steps": [],
    }

    with pytest.raises(BadRequestError):
        _invoke_once(mock_llm, [], "Test prompt.", 5, "test-run")


# ── T-ORC-C-013 ──────────────────────────────────────────────────────────────

def test_t_orc_c_013_invoke_once_does_not_raise_on_normal_success_with_steps(mocker):
    """
    T-ORC-C-013: _invoke_once() does NOT raise on normal successful completion
    where both output is non-empty JSON AND intermediate_steps is non-empty
    (CL-046 + CL-050B combined regression guard).

    CL-046 gate: fires only on intermediate_steps=[] + empty output.
    CL-050B gate: fires only on intermediate_steps non-empty + empty output.
    Neither gate fires when output is valid JSON — this test confirms both
    boundary conditions together.

    Updated in CL-050B: previously the test used output="" (checking CL-046
    boundary), but CL-050B's new guard fires exactly when steps non-empty
    AND output empty. The test now uses non-empty JSON output so it is a
    clean happy-path regression guard for both gates simultaneously.
    """
    mock_llm = mocker.MagicMock()
    mocker.patch("core.orchestration.create_tool_calling_agent", return_value=mocker.MagicMock())
    mock_executor_cls = mocker.patch("core.orchestration.AgentExecutor")
    mock_executor_cls.return_value.invoke.return_value = {
        "output": '[{"topic": "test"}]',
        "intermediate_steps": [(mocker.MagicMock(), "real search result")],
    }

    result = _invoke_once(mock_llm, [], "Test prompt.", 5, "test-run")

    assert result.get("output") == '[{"topic": "test"}]'


# ── T-ORC-U-014 — _strip_agent_fences ────────────────────────────────────────

def test_t_orc_u_014_strip_agent_fences_removes_json_fences():
    """
    T-ORC-U-014: _strip_agent_fences() removes ```json ... ``` wrapping.

    Gemini Flash wraps its final agent output in markdown fences even in
    tool-calling mode (confirmed in live run 2026-06-24). Without stripping,
    _is_refusal() fires on the backtick-prefixed string and raises BadRequestError,
    discarding a valid result.
    """
    fenced = "```json\n[{\"topic\": \"test\"}]\n```"
    assert _strip_agent_fences(fenced) == '[{"topic": "test"}]'


def test_t_orc_u_015_strip_agent_fences_plain_json_unchanged():
    """
    T-ORC-U-015: _strip_agent_fences() returns plain JSON unchanged.

    Valid JSON that doesn't start with fences must pass through unmodified
    so the normal parse path is not disrupted.
    """
    plain = '[{"topic": "test"}]'
    assert _strip_agent_fences(plain) == plain


def test_t_orc_u_016_strip_agent_fences_none_returns_empty_string():
    """
    T-ORC-U-016: _strip_agent_fences() returns "" for None input.

    AgentExecutor returns output=None when max_iterations is hit. The
    `output or ""` guard converts it to "", but _strip_agent_fences must
    also be safe against None in case call order changes.
    """
    assert _strip_agent_fences(None) == ""


def test_t_orc_u_017_strip_agent_fences_plain_backtick_fence():
    """
    T-ORC-U-017: _strip_agent_fences() handles plain ``` fences (no language tag).
    """
    fenced = "```\n[{\"topic\": \"test\"}]\n```"
    assert _strip_agent_fences(fenced) == '[{"topic": "test"}]'


# ── T-ORC-U-018 — ServiceUnavailableError in _FAILOVER_EXCEPTIONS ─────────────

def test_t_orc_u_018_service_unavailable_error_in_failover_exceptions():
    """
    T-ORC-U-018: ServiceUnavailableError is a member of _FAILOVER_EXCEPTIONS.

    Google AI Studio returns HTTP 503 during high demand. Before CL-047
    this was not in _FAILOVER_EXCEPTIONS so it propagated as an unhandled
    exception and crashed the pipeline instead of failing over to MODEL_2.
    """
    assert ServiceUnavailableError in _FAILOVER_EXCEPTIONS


# ── T-ORC-U-030 — APIError in _FAILOVER_EXCEPTIONS ───────────────────────────

def test_t_orc_u_030_api_error_in_failover_exceptions():
    """
    T-ORC-U-030: APIError is a member of _FAILOVER_EXCEPTIONS.

    OpenRouter rejects langchain_litellm's num_ctx=None with APIError (CL-052).
    Before CL-052 this propagated uncaught and crashed the pipeline.
    """
    from litellm.exceptions import APIError

    assert APIError in _FAILOVER_EXCEPTIONS


# ── T-ORC-N-019 — force-stop literal triggers BadRequestError ────────────────

def test_t_orc_n_019_invoke_once_raises_on_force_stop_literal(mocker):
    """
    T-ORC-N-019: _invoke_once() raises BadRequestError when AgentExecutor
    returns the LangChain force-stop literal "Agent stopped due to max iterations."

    LangChain emits this exact string as output when early_stopping_method="force"
    hits the iteration cap and the model never synthesised a final answer. Before
    CL-047 this string passed all gates and was returned to main.py, which then
    failed json.loads() and silently returned []. Now it triggers failover.
    """
    mock_llm = mocker.MagicMock()
    mocker.patch("core.orchestration.create_tool_calling_agent", return_value=mocker.MagicMock())
    mock_executor_cls = mocker.patch("core.orchestration.AgentExecutor")
    mock_executor_cls.return_value.invoke.return_value = {
        "output": "Agent stopped due to max iterations.",
        "intermediate_steps": [(mocker.MagicMock(), "some result")],
    }

    with pytest.raises(BadRequestError):
        _invoke_once(mock_llm, [], "Test prompt.", 10, "jic-agent")


# ── CL-049 tests: streaming=False for all non-openrouter models ───────────────

# ── T-ORC-C-020 ──────────────────────────────────────────────────────────────

def test_t_orc_c_020_build_llm_for_model_gemini_sets_streaming_false(monkeypatch):
    """
    T-ORC-C-020: _build_llm_for_model() with a gemini/ prefix model sets
    streaming=False (CL-049 constructor-level guard; CL-055 routes runtime
    JIT/JIC on Google models through SDK path, not AgentExecutor invoke).
    """
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key-0000")

    llm = _build_llm_for_model("gemini/gemini-2.5-flash")

    assert llm.streaming is False, (
        f"Expected streaming=False for gemini/ model, got: {llm.streaming!r}"
    )


# ── T-ORC-C-021 ──────────────────────────────────────────────────────────────

def test_t_orc_c_021_build_llm_for_model_vertex_ai_sets_streaming_false(monkeypatch):
    """
    T-ORC-C-021: _build_llm_for_model() with a vertex_ai/ prefix model sets
    streaming=False (CL-047 + CL-049 — vertex_ai/ hits the same
    streamGenerateContent endpoint as gemini/; originally fixed only for
    vertex_ai/ in CL-047, then extended to all non-openrouter in CL-049).
    Regression guard: confirms CL-049's branch restructure did not remove
    the streaming=False for vertex_ai/.
    """
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/tmp/test-sa.json")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    llm = _build_llm_for_model("vertex_ai/gemini-2.5-flash-lite")

    assert llm.streaming is False, (
        f"Expected streaming=False for vertex_ai/ model, got: {llm.streaming!r}"
    )


# ── T-ORC-C-022 ──────────────────────────────────────────────────────────────

def test_t_orc_c_022_build_llm_for_model_openrouter_branch_constructs_correctly(monkeypatch):
    """
    T-ORC-C-022: _build_llm_for_model() with an openrouter/ prefix model uses
    its separate code branch (CL-049 — openrouter/ is excluded from the
    explicit streaming=False kwarg; their tool-call failure mode is handled by
    _detect_empty_tool_loop()). Confirms the if/else boundary is correct by
    verifying the openrouter/ LLM has the correct api_key routing.

    Note: langchain_litellm.ChatLiteLLM defaults streaming to False regardless
    of whether it is explicitly set — this differs from the old
    langchain_community.ChatLiteLLM which defaulted to True. The test was
    updated from an `llm.streaming is not False` assertion to an api_key
    routing assertion since both branches now produce streaming=False; the
    meaningful code distinction is in api_key handling and the code structure.
    """
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key-0000")

    llm = _build_llm_for_model("openrouter/openai/gpt-4o-mini")

    assert llm is not None
    assert llm.model_kwargs.get("api_key") == "sk-or-test-key-0000", (
        f"openrouter/ model must route OPENROUTER_API_KEY to model_kwargs, got: {llm.model_kwargs!r}"
    )


# ── CL-050A tests: langchain_litellm import migration ─────────────────────────

# ── T-ORC-C-023 ──────────────────────────────────────────────────────────────

def test_t_orc_c_023_build_llm_for_model_returns_langchain_litellm_instance(monkeypatch):
    """
    T-ORC-C-023: _build_llm_for_model() returns a ChatLiteLLM instance from
    langchain_litellm (CL-050A — migrated import from deprecated
    langchain_community.chat_models; official replacement confirmed via
    LangChain GitHub #31145 and PyPI langchain-litellm).
    """
    import langchain_litellm

    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key-0000")

    llm = _build_llm_for_model("openrouter/openai/gpt-4o-mini")

    assert isinstance(llm, langchain_litellm.ChatLiteLLM), (
        f"Expected langchain_litellm.ChatLiteLLM, got: {type(llm)!r}"
    )


# ── T-ORC-N-024 ──────────────────────────────────────────────────────────────

def test_t_orc_n_024_langchain_community_chat_models_not_imported_in_orchestration():
    """
    T-ORC-N-024: core/orchestration.py does NOT contain an import statement
    referencing langchain_community.chat_models (CL-050A regression guard —
    ensures the deprecated import path cannot silently re-enter via a merge
    or revert). Checks for the import statement specifically (not docstring
    mentions, which are allowed as historical references).
    """
    import inspect
    import core.orchestration

    source = inspect.getsource(core.orchestration)
    assert "from langchain_community.chat_models import" not in source, (
        "Deprecated 'from langchain_community.chat_models import' found in orchestration.py — "
        "must use langchain_litellm instead (CL-050A)"
    )
    assert "from langchain_litellm import ChatLiteLLM" in source, (
        "langchain_litellm ChatLiteLLM import not found in orchestration.py"
    )


# ── CL-050B tests: MALFORMED_FUNCTION_CALL silent failure guard ───────────────

# ── T-ORC-N-025 ──────────────────────────────────────────────────────────────

def test_t_orc_n_025_invoke_once_raises_on_nonempty_steps_empty_string_output(mocker):
    """
    T-ORC-N-025: _invoke_once() raises BadRequestError when intermediate_steps
    is non-empty but output is an empty string (CL-050B — LiteLLM maps Gemini's
    MALFORMED_FUNCTION_CALL finishReason to finish_reason="stop" with
    content=None/completion_tokens=0; no exception fires. Steps exist up to
    the point of MALFORMED, so existing guards don't catch it: empty-tool-loop
    needs >=3 consecutive empty steps; zero-step gate needs steps=[];
    _is_refusal needs non-empty text). Confirmed by LiteLLM issue #16651.
    """
    mock_llm = mocker.MagicMock()
    mocker.patch("core.orchestration.create_tool_calling_agent", return_value=mocker.MagicMock())
    mock_executor_cls = mocker.patch("core.orchestration.AgentExecutor")
    mock_executor_cls.return_value.invoke.return_value = {
        "output": "",
        "intermediate_steps": [("mock_action", "mock_observation")],
    }

    with pytest.raises(BadRequestError) as exc_info:
        _invoke_once(mock_llm, [], "Test prompt.", 10, "jit-agent")

    assert "MALFORMED_FUNCTION_CALL" in str(exc_info.value) or "empty final output" in str(exc_info.value), (
        f"Expected MALFORMED_FUNCTION_CALL error message, got: {exc_info.value}"
    )


# ── T-ORC-N-026 ──────────────────────────────────────────────────────────────

def test_t_orc_n_026_invoke_once_raises_on_nonempty_steps_none_output(mocker):
    """
    T-ORC-N-026: _invoke_once() raises BadRequestError when intermediate_steps
    is non-empty but output is None (CL-050B). output=None (not just "") must
    also trigger the guard — AgentExecutor can return None on max_iter exhaustion
    with partial steps (the `or ""` coercion converts it to "" before the guard).
    """
    mock_llm = mocker.MagicMock()
    mocker.patch("core.orchestration.create_tool_calling_agent", return_value=mocker.MagicMock())
    mock_executor_cls = mocker.patch("core.orchestration.AgentExecutor")
    mock_executor_cls.return_value.invoke.return_value = {
        "output": None,
        "intermediate_steps": [("mock_action", "mock_observation")],
    }

    with pytest.raises(BadRequestError):
        _invoke_once(mock_llm, [], "Test prompt.", 10, "jit-agent")


# ── T-ORC-C-027 ──────────────────────────────────────────────────────────────

def test_t_orc_c_027_invoke_once_does_not_raise_on_nonempty_steps_valid_json(mocker):
    """
    T-ORC-C-027: _invoke_once() does NOT raise BadRequestError when both
    intermediate_steps and output are non-empty (CL-050B regression guard —
    confirms the MALFORMED guard does not fire on successful agent completion).
    """
    mock_llm = mocker.MagicMock()
    mocker.patch("core.orchestration.create_tool_calling_agent", return_value=mocker.MagicMock())
    mock_executor_cls = mocker.patch("core.orchestration.AgentExecutor")
    mock_executor_cls.return_value.invoke.return_value = {
        "output": '[{"topic": "test"}]',
        "intermediate_steps": [("mock_action", "mock_observation")],
    }

    result = _invoke_once(mock_llm, [], "Test prompt.", 10, "jit-agent")

    assert result["output"] == '[{"topic": "test"}]', (
        "MALFORMED guard must not fire on successful JSON output"
    )


# ── T-ORC-C-028 ──────────────────────────────────────────────────────────────

def test_t_orc_c_028_invoke_once_does_not_raise_on_empty_steps_valid_json(mocker):
    """
    T-ORC-C-028: _invoke_once() does NOT raise BadRequestError when steps=[]
    and output is valid JSON (CL-050B boundary condition — the MALFORMED guard
    condition is `intermediate_steps AND NOT raw_output`; with empty steps the
    AND is False so the guard cannot fire regardless of output).
    """
    mock_llm = mocker.MagicMock()
    mocker.patch("core.orchestration.create_tool_calling_agent", return_value=mocker.MagicMock())
    mock_executor_cls = mocker.patch("core.orchestration.AgentExecutor")
    mock_executor_cls.return_value.invoke.return_value = {
        "output": '[{"topic": "test"}]',
        "intermediate_steps": [],
    }

    result = _invoke_once(mock_llm, [], "Test prompt.", 10, "jit-agent")

    assert result["output"] == '[{"topic": "test"}]'


# ── T-ORC-N-029 ──────────────────────────────────────────────────────────────

def test_t_orc_n_029_zero_step_gate_still_fires_after_cl050b(mocker):
    """
    T-ORC-N-029: CL-046's zero-step gate (_invoke_once raises BadRequestError
    when intermediate_steps=[] AND output is empty) still fires after CL-050B's
    new guard is inserted (CL-050B regression guard — the two guards cover
    complementary failure shapes and must not interfere).

    CL-046 shape: steps=[], output=None/""  →  zero-step gate raises
    CL-050B shape: steps=non-empty, output="" → MALFORMED gate raises
    """
    mock_llm = mocker.MagicMock()
    mocker.patch("core.orchestration.create_tool_calling_agent", return_value=mocker.MagicMock())
    mock_executor_cls = mocker.patch("core.orchestration.AgentExecutor")
    mock_executor_cls.return_value.invoke.return_value = {
        "output": "",
        "intermediate_steps": [],
    }

    with pytest.raises(BadRequestError) as exc_info:
        _invoke_once(mock_llm, [], "Test prompt.", 10, "jit-agent")

    assert "zero tool calls" in str(exc_info.value) or "first turn" in str(exc_info.value), (
        f"Expected CL-046 zero-step gate message, got: {exc_info.value}"
    )


# ── T-ORC-C-030 ──────────────────────────────────────────────────────────────

def test_t_orc_c_030_invoke_once_vertex_skips_agent_executor(mocker):
    """
    T-ORC-C-030: _invoke_once() with vertex_ai/ model does NOT instantiate
    AgentExecutor — routes to SDK tool loop instead (CL-055).
    """
    mock_sdk = mocker.patch(
        "core.orchestration.run_litellm_tool_loop",
        return_value={
            "output": '[{"topic": "test"}]',
            "intermediate_steps": [("search", "results")],
        },
    )
    mock_executor_cls = mocker.patch("core.orchestration.AgentExecutor")

    result = _invoke_once(
        mocker.MagicMock(),
        [],
        "Test prompt.",
        10,
        "jit-agent",
        model="vertex_ai/gemini-2.5-flash-lite",
    )

    mock_sdk.assert_called_once()
    mock_executor_cls.assert_not_called()
    assert result["output"] == '[{"topic": "test"}]'


# ── T-ORC-C-031 ──────────────────────────────────────────────────────────────

def test_t_orc_c_031_invoke_once_openrouter_uses_agent_executor(mocker):
    """
    T-ORC-C-031: _invoke_once() with openrouter/ model still uses AgentExecutor.
    """
    mock_sdk = mocker.patch("core.orchestration.run_litellm_tool_loop")
    mock_executor_cls = mocker.patch("core.orchestration.AgentExecutor")
    mock_executor_cls.return_value.invoke.return_value = {
        "output": '[{"topic": "test"}]',
        "intermediate_steps": [("search", "results")],
    }
    mocker.patch("core.orchestration.create_tool_calling_agent", return_value=mocker.MagicMock())

    result = _invoke_once(
        mocker.MagicMock(),
        [],
        "Test prompt.",
        10,
        "jit-agent",
        model="openrouter/openai/gpt-4o-mini:free",
    )

    mock_executor_cls.assert_called_once()
    mock_sdk.assert_not_called()
    assert result["output"] == '[{"topic": "test"}]'


# ── T-ORC-N-030 ──────────────────────────────────────────────────────────────

def test_t_orc_n_030_sdk_path_empty_tool_loop_triggers_failover(mocker):
    """
    T-ORC-N-030: SDK path empty tool loop (3+ empty observations) raises
    BadRequestError for failover (CL-055 guard reuse).
    """
    mocker.patch(
        "core.orchestration.run_litellm_tool_loop",
        return_value={
            "output": "",
            "intermediate_steps": [
                ("search", ""),
                ("search", ""),
                ("search", ""),
            ],
        },
    )

    with pytest.raises(BadRequestError) as exc_info:
        _invoke_once(
            mocker.MagicMock(),
            [],
            "Test prompt.",
            10,
            "jit-agent",
            model="vertex_ai/gemini-2.5-flash-lite",
        )

    assert "Empty tool-call loop" in str(exc_info.value)


# ── T-ORC-N-031 ──────────────────────────────────────────────────────────────

def test_t_orc_n_031_sdk_path_zero_step_empty_output_triggers_failover(mocker):
    """
    T-ORC-N-031: SDK path zero-step empty output raises BadRequestError
    (CL-046 gate reused on SDK path).
    """
    mocker.patch(
        "core.orchestration.run_litellm_tool_loop",
        return_value={"output": "", "intermediate_steps": []},
    )

    with pytest.raises(BadRequestError) as exc_info:
        _invoke_once(
            mocker.MagicMock(),
            [],
            "Test prompt.",
            10,
            "jit-agent",
            model="gemini/gemini-2.5-flash-lite",
        )

    assert "zero tool calls" in str(exc_info.value) or "first turn" in str(exc_info.value)


# ── T-ORC-N-032 ──────────────────────────────────────────────────────────────

def test_t_orc_n_032_schema_invalid_output_triggers_failover(mocker):
    """
    T-ORC-N-032: parsed array with rows but zero valid normalized items raises
    BadRequestError (CL-059 — field drift without recoverable url).
    """
    import json

    bad_json = json.dumps([{"title": f"No URL {i}", "summary": "text"} for i in range(5)])

    with pytest.raises(BadRequestError) as exc_info:
        _apply_invoke_guards(
            {"output": bad_json, "intermediate_steps": [("search", "ok")]},
            max_iter=10,
            run_name="jic-agent",
        )

    assert "schema validation" in str(exc_info.value).lower()


def test_t_orc_c_032_nemotron_shape_passes_schema_guard():
    """
    T-ORC-C-032: title/url/date Nemotron output passes guard after normalization.
    """
    import json

    from tests.test_output_normalize import NEMOTRON_JIC_FIXTURE

    result = _apply_invoke_guards(
        {"output": json.dumps(NEMOTRON_JIC_FIXTURE), "intermediate_steps": [("search", "ok")]},
        max_iter=10,
        run_name="jic-agent",
    )
    assert result["output"]
