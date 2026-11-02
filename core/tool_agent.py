"""
MODULE: tool_agent.py
PURPOSE: SDK-direct litellm.completion tool loop for Google provider models (vertex_ai/, gemini/)
INPUTS: model (str), tools (LangChain Tool list), user_prompt (str), max_iter (int)
OUTPUTS: dict {output: str|None, intermediate_steps: list} — same shape as AgentExecutor
DEPENDENCIES: litellm, core.gateway (_get_api_key, _log_token_usage), core.tool_args
RULE REFERENCES: DEV-I-005 (CL-055 exception — SDK tool loop inside run_agent()),
                 DEV-I-006 (vertex_ai/ uses ADC — no api_key= when None)
CHANGE LOG: 1.0.0 | 2026-06-26 | CL-055: bypass LangChain AgentExecutor for Google
            models — ChatLiteLLM still hits streamGenerateContent at invoke time
            despite streaming=False on the constructor (CL-047). Explicit
            litellm.completion(stream=False) matches the working lesson path | Claude Code
            1.1.0 | 2026-06-27 | CL-059: route through gateway._litellm_completion()
            (OpenRouter 429 retry); strip fences on final output; detect
            MALFORMED_FUNCTION_CALL / empty tool-call turns | Claude Code
"""
import json
import logging
import os

from litellm.exceptions import BadRequestError

from core.gateway import _get_api_key, _litellm_completion, _log_token_usage, call_model
from core.output_normalize import _strip_fences
from core.tool_args import _coerce_tool_arg

logger = logging.getLogger(__name__)

AGENT_SYSTEM_PROMPT = (
    "You are a data-gathering AI assistant. "
    "You MUST use the search tool to gather real, current data before returning any answer. "
    "You MUST use the query_history tool to verify each topic is not in cooldown. "
    "Do NOT respond conversationally. Do NOT explain what you are going to do. "
    "Do NOT summarise results in prose. "
    "Your ONLY valid final output is a JSON array or JSON object matching the exact "
    "schema specified in the user message — nothing else. "
    "Call tools first. Return JSON last. No exceptions."
)

_TOOL_ARG_KEYS = {
    "search": ("query", "q", "search_query", "text"),
    "search_broad": ("query", "q", "search_query", "text"),
    "query_history": ("topic", "title", "name", "query"),
}

_TOOL_PARAM_NAMES = {
    "search": "query",
    "search_broad": "query",
    "query_history": "topic",
}


def _uses_google_sdk_path(model: str | None) -> bool:
    """Return True when model should use the SDK-direct tool loop (CL-055)."""
    return bool(model and (model.startswith("vertex_ai/") or model.startswith("gemini/")))


def _tools_to_openai_schema(tools: list) -> list[dict]:
    """Map LangChain Tool objects to OpenAI function schemas for litellm.completion."""
    schemas = []
    for tool in tools:
        param = _TOOL_PARAM_NAMES.get(tool.name, "input")
        schemas.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": {
                    "type": "object",
                    "properties": {
                        param: {
                            "type": "string",
                            "description": f"The {param} argument for {tool.name}",
                        }
                    },
                    "required": [param],
                },
            },
        })
    return schemas


def _parse_tool_arguments(raw_args) -> object:
    """Parse tool-call arguments from litellm (JSON string or dict)."""
    if isinstance(raw_args, dict):
        return raw_args
    if isinstance(raw_args, str):
        try:
            return json.loads(raw_args)
        except (json.JSONDecodeError, TypeError):
            return raw_args
    return raw_args


def _execute_tool_call(tool, raw_args) -> str:
    """Run a LangChain Tool with coerced arguments (CL-042/043 protobuf defense)."""
    parsed = _parse_tool_arguments(raw_args)
    keys = _TOOL_ARG_KEYS.get(tool.name, ("input",))
    coerced = _coerce_tool_arg(parsed, keys)
    return str(tool.func(coerced))


def _assistant_message_dict(message) -> dict:
    """Build an OpenAI-style assistant message dict from a litellm message."""
    tool_calls = getattr(message, "tool_calls", None) or []
    payload = {
        "role": "assistant",
        "content": message.content,
    }
    if tool_calls:
        payload["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in tool_calls
        ]
    return payload


def _completion_kwargs(model: str, messages: list, tool_schemas: list) -> dict:
    """Build litellm.completion kwargs with explicit stream=False (CL-055)."""
    timeout = int(os.getenv("LITELLM_TIMEOUT_SECONDS", "30"))
    kwargs = {
        "model": model,
        "messages": messages,
        "tools": tool_schemas,
        "stream": False,
        "timeout": timeout,
    }
    api_key = _get_api_key(model)
    if api_key is not None:
        kwargs["api_key"] = api_key
    return kwargs


def _message_for_history(message) -> dict:
    """
    Return the assistant message exactly as the model sent it (CL-063).

    Gemini 3/4 attach a thought signature to tool calls; it must be sent back
    unchanged or the model loses its reasoning state (probe 2026-11-01: rebuilt
    messages doubled reasoning tokens and one call took 163 s). model_dump()
    keeps provider_specific_fields; _assistant_message_dict() is the fallback
    for non-pydantic test doubles.
    """
    if hasattr(message, "model_dump"):
        try:
            dumped = message.model_dump()
            if isinstance(dumped, dict) and dumped.get("role"):
                return dumped
        except Exception:  # noqa: BLE001
            pass
    return _assistant_message_dict(message)


def run_litellm_tool_loop(
    model: str,
    tools: list,
    user_prompt: str,
    max_iter: int,
    system_prompt: str = AGENT_SYSTEM_PROMPT,
    stage: str = "tool-loop",
) -> dict:
    """
    Run a manual tool-calling loop via core.gateway.call_model (stream=False).

    Returns the same dict shape as AgentExecutor.invoke() for guard reuse in
    orchestration._invoke_once(): keys "output" and "intermediate_steps".
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    tool_map = {tool.name: tool for tool in tools}
    tool_schemas = _tools_to_openai_schema(tools)
    intermediate_steps: list = []

    for _ in range(max_iter):
        response = call_model(model, messages, stage=stage, tools=tool_schemas)

        choice = response.choices[0]
        message = choice.message
        finish_reason = getattr(choice, "finish_reason", None) or ""
        tool_calls = getattr(message, "tool_calls", None) or []

        if finish_reason == "MALFORMED_FUNCTION_CALL" or (
            finish_reason in ("stop", "length")
            and not tool_calls
            and not (message.content or "").strip()
            and intermediate_steps
        ):
            raise BadRequestError(
                message=(
                    "SDK tool loop received MALFORMED_FUNCTION_CALL or empty final "
                    "turn after tool use — triggering model failover."
                ),
                model=model,
                llm_provider="litellm",
                response=None,
            )

        if tool_calls:
            messages.append(_message_for_history(message))
            for tool_call in tool_calls:
                tool = tool_map.get(tool_call.function.name)
                if tool is None:
                    observation = f"Unknown tool: {tool_call.function.name}"
                    logger.warning(observation)
                else:
                    observation = _execute_tool_call(tool, tool_call.function.arguments)
                intermediate_steps.append((tool_call.function.name, observation))
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": observation,
                })
            continue

        return {
            "output": _strip_fences(message.content or ""),
            "intermediate_steps": intermediate_steps,
        }

    logger.warning(
        f"R-005: SDK tool loop hit max_iterations={max_iter} — returning partial result"
    )
    return {"output": None, "intermediate_steps": intermediate_steps}
