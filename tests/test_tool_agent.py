"""
MODULE: test_tool_agent.py
PURPOSE: Test cases for core/tool_agent.py — SDK-direct litellm tool loop (CL-055)
INPUTS: pytest fixtures (mocker)
OUTPUTS: Pass/fail assertions per TEST_REGISTRY T-TOOL-* acceptance criteria
DEPENDENCIES: pytest, pytest-mock, core.tool_agent
RULE REFERENCES: DEV-I-005 (CL-055 SDK exception), DEV-I-006 (vertex_ai/ ADC)
CHANGE LOG: 1.0.0 | 2026-06-26 | CL-055 initial tests T-TOOL-C-001/002, T-TOOL-N-001 | Claude Code
"""
import json
from types import SimpleNamespace

from langchain_core.tools import Tool

from core.tool_agent import _execute_tool_call, run_litellm_tool_loop


def _fake_message(content=None, tool_calls=None):
    return SimpleNamespace(content=content, tool_calls=tool_calls or [])


def _fake_tool_call(call_id, name, arguments):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=arguments),
    )


def _fake_response(message, total_tokens=30, finish_reason="stop"):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message, finish_reason=finish_reason)],
        usage=SimpleNamespace(total_tokens=total_tokens),
    )


# ── T-TOOL-C-001 ─────────────────────────────────────────────────────────────

def test_t_tool_c_001_run_litellm_tool_loop_calls_completion_with_stream_false(mocker):
    """
    T-TOOL-C-001 (updated CL-063): run_litellm_tool_loop() calls the policy
    gateway call_model() with the tool schemas; stream=False / vertex_location /
    reasoning_effort are now set inside call_model (see T-GAT-C-020).
    """
    mock_completion = mocker.patch(
        "core.tool_agent.call_model",
        return_value=_fake_response(_fake_message(content='[{"topic": "ok"}]')),
    )

    tools = [
        Tool(name="search", func=lambda q: "results", description="Search the web."),
    ]

    run_litellm_tool_loop(
        model="vertex_ai/gemini-2.5-flash-lite",
        tools=tools,
        user_prompt="Gather JIT news.",
        max_iter=5,
    )

    mock_completion.assert_called_once()
    args, kwargs = mock_completion.call_args
    assert args[0] == "vertex_ai/gemini-2.5-flash-lite"
    assert kwargs["tools"]
    assert kwargs["tools"][0]["function"]["name"] == "search"


# ── T-TOOL-C-002 ─────────────────────────────────────────────────────────────

def test_t_tool_c_002_run_litellm_tool_loop_executes_tool_then_returns_json(mocker):
    """
    T-TOOL-C-002: One tool call → tool result appended → final JSON returned.
    """
    search_func = mocker.MagicMock(return_value="tavily hits")
    tools = [
        Tool(name="search", func=search_func, description="Search the web."),
    ]
    mocker.patch(
        "core.tool_agent.call_model",
        side_effect=[
            _fake_response(_fake_message(
                tool_calls=[_fake_tool_call("call-1", "search", '{"query": "AI news"}')],
            ), finish_reason="tool_calls"),
            _fake_response(_fake_message(content='[{"topic": "GPT-5"}]')),
        ],
    )

    result = run_litellm_tool_loop(
        model="vertex_ai/gemini-2.5-flash-lite",
        tools=tools,
        user_prompt="Return JIT JSON.",
        max_iter=5,
    )

    search_func.assert_called_once_with("AI news")
    assert result["output"] == '[{"topic": "GPT-5"}]'
    assert len(result["intermediate_steps"]) == 1
    assert result["intermediate_steps"][0] == ("search", "tavily hits")


# ── T-TOOL-N-001 ─────────────────────────────────────────────────────────────

def test_t_tool_n_001_execute_tool_call_unwraps_vertex_protobuf_shape():
    """
    T-TOOL-N-001: Vertex protobuf-shaped tool args are coerced to plain strings.
    """
    nested = {
        "key": "fields",
        "value": {
            "struct_value": {
                "key": "__arg1",
                "value": {"string_value": "Vector Databases news"},
            }
        },
    }
    captured = []

    def _search(query):
        captured.append(query)
        return "ok"

    tool = Tool(name="search", func=_search, description="Search.")
    observation = _execute_tool_call(tool, nested)

    assert observation == "ok"
    assert captured == ["Vector Databases news"]


# ── T-TOOL-C-010 (CL-063) ────────────────────────────────────────────────────

def test_t_tool_c_010_history_keeps_thought_signature():
    """T-TOOL-C-010: the assistant tool-call message is sent back unchanged (Gemini 3/4 thought signature)."""
    from core.tool_agent import _message_for_history

    class Msg:
        def model_dump(self):
            return {"role": "assistant", "content": None, "tool_calls": [{"id": "1"}],
                    "provider_specific_fields": {"thought_signatures": ["sig-abc"]}}

    out = _message_for_history(Msg())
    assert out["provider_specific_fields"]["thought_signatures"] == ["sig-abc"]
