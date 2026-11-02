"""
MODULE: tool_args.py
PURPOSE: Coerce LLM tool-call arguments to plain strings for search/query_history tools
INPUTS: arg (str, dict, or other), candidate_keys tuple of dict key names to probe
OUTPUTS: str — coerced query/topic text for tool invocation
DEPENDENCIES: none
RULE REFERENCES: DEV-I-005 (shared by main._tools() and core.tool_agent SDK path)
CHANGE LOG: 1.0.0 | 2026-06-26 | CL-055: moved from main.py — Vertex protobuf-shaped
            tool args must be unwrapped on both LangChain Tool wrappers and the
            SDK-direct litellm tool loop | Claude Code
"""


def _coerce_tool_arg(arg, candidate_keys: tuple) -> str:
    """
    Coerce an LLM tool-call argument to a plain string (CL-042/043).

    Most models pass a flat dict like {"query": "..."} (or already a bare
    string). Vertex AI's Gemini has also been observed passing a nested
    protobuf Struct/Value-shaped dict instead, e.g.:
        {"key": "fields", "value": {"struct_value": {"key": "__arg1",
         "value": {"string_value": "actual query text"}}}}
    Recursively unwraps known protobuf Struct/Value wrapper keys
    ("value", "struct_value", "string_value", "fields") to find the actual
    string content. Falls back to str(arg) if nothing can be found —
    callers never raise, matching query_history's CL-038/040 contract.
    """
    if isinstance(arg, str):
        return arg
    if not isinstance(arg, dict):
        return str(arg)
    for key in candidate_keys:
        if key in arg and isinstance(arg[key], str):
            return arg[key]
    if "fields" in arg and isinstance(arg["fields"], dict):
        for key in candidate_keys + ("__arg1",):
            if key in arg["fields"]:
                return _coerce_tool_arg(arg["fields"][key], candidate_keys)
    for wrapper_key in ("string_value", "struct_value", "value"):
        if wrapper_key in arg:
            unwrapped = _coerce_tool_arg(arg[wrapper_key], candidate_keys)
            if unwrapped:
                return unwrapped
    return str(arg)
