"""
MODULE: orchestration.py
PURPOSE: LangChain ReACT agent wrapper with hard max_iterations enforcement and
         model failover on RateLimitError/AuthenticationError/BadRequestError/Timeout
INPUTS: llm (LangChain BaseLLM, optional), tools (list), prompt (str), max_iter (int),
        model (str, optional) — starting point in core.gateway's failover chain
OUTPUTS: dict {output: str, ...} — partial results if iteration limit hit;
         {"output": "All models exhausted", "error": str} if failover chain exhausted
DEPENDENCIES: langchain, langchain_core, litellm, core.gateway
RULE REFERENCES: R-005 (max_iterations=5 hard stop), R-002 (model failover on
         rate-limit/auth/bad-request/timeout failure — reuses core.gateway's
         _build_model_chain(), the agent-based pipeline path bypasses
         core.gateway.llm_call() per DEV-I-005 and previously had no failover
         of its own)
CHANGE LOG: 1.0.0 | 2026-06-16 | TC-004 initial implementation | Claude Code
            1.1.0 | 2026-06-17 | TC-010 added run_name parameter; passed to
            executor.invoke() config for LangSmith trace labelling | Claude Code
            1.2.0 | 2026-06-17 | Bugfix: added model failover — run_agent() now
            catches RateLimitError/AuthenticationError, rebuilds the LLM with
            the next model in core.gateway._build_model_chain(), and retries
            once per fallback model. Closes the gap where the live pipeline
            (ChatLiteLLM via AgentExecutor) had no failover at all, unlike
            core.gateway.llm_call() which the pipeline never calls | Claude Code
            1.3.0 | 2026-06-17 | Bugfix: _build_model_chain() is now deferred
            until actually needed — if `llm` is supplied and the first attempt
            succeeds, the chain is never built (avoids requiring LITELLM_MODEL_1
            for callers that already have a working LLM). Added BadRequestError
            and Timeout to _FAILOVER_EXCEPTIONS; added LITELLM_TIMEOUT_SECONDS
            (default 30) passed as request_timeout to ChatLiteLLM. Removed the
            dead os.getenv("LITELLM_PRIMARY_MODEL") fallback — chain[0] already
            covers it once the chain is built | Claude Code
            1.4.0 | 2026-06-18 | CL-021 bugfix: replaced create_react_agent
            (text-based Action:/Observation: parsing) with create_tool_calling_agent
            (native function-calling via ChatLiteLLM.bind_tools()). Root cause:
            modern models (e.g. Llama 3.3 70B) emit native tool-call tokens
            instead of ReACT-format text, so the ReACT output parser couldn't
            recognise any tool use — every iteration was wasted, exhausting
            max_iterations without ever producing valid output. _REACT_TEMPLATE
            and _STOP_PHRASE removed (no longer applicable — create_tool_calling_agent
            never emits the ReACT stop phrase). R-005 exhaustion is now detected
            via result.get("output") is None instead of stop-phrase matching | Claude Code
            1.5.0 | 2026-06-18 | CL-022 bugfix: a live run crashed the whole
            pipeline on an uncaught litellm.exceptions.APIConnectionError —
            an OpenRouter model emitted a malformed tool-call response, which
            litellm classified as APIConnectionError, not previously in
            _FAILOVER_EXCEPTIONS. Widened to also include APIConnectionError
            and NotFoundError so these degrade to the next chain model instead
            of crashing. Added an openrouter/ branch to _build_llm_for_model()
            (.env's LITELLM_MODEL_1/2/3 are now all openrouter/ models) | Claude Code
            1.6.0 | 2026-06-22 | CL-032 bugfix: free-tier models sometimes
            return HTTP 200 with a content-refusal string ("I'm unable to...",
            "I cannot...", "As an AI...") instead of the requested JSON — no
            exception is raised, so the failover loop never fired and
            main.py silently returned []. Added _is_refusal() and a check in
            _invoke_once() that raises BadRequestError (already in
            _FAILOVER_EXCEPTIONS) on detection, so the existing failover loop
            handles it the same way it handles a real provider error | Claude Code
            1.7.0 | 2026-06-22 | CL-038 bugfix: a live run after CL-037 showed
            three more failure modes. (B) Flash-Lite responded "I can help
            you find..." — conversational prose the CL-032 refusal prefixes
            didn't cover — so JIT silently returned []; _is_refusal() gained
            more prefixes plus a layer-2 non-JSON-prose detector (>=40 chars,
            doesn't start with '{'/'['/'"', json.loads() fails). (C) the
            system prompt's "Always return... as valid JSON" was too weak a
            hint; replaced with an explicit tool-use mandate that forbids
            conversational replies. (D) the original, narrower CL-038 target
            — gpt-oss-120b:free looping on finish_reason='tool_calls' with
            content='' every iteration, silently exhausting max_iter with no
            exception and no refusal string — fixed via
            return_intermediate_steps=True and _detect_empty_tool_loop(),
            raising BadRequestError on >=3 consecutive empty steps | Claude Code
            1.9.0 | 2026-06-24 | CL-049 bugfix: gemini/ prefix models were
            hitting streamGenerateContent (streaming=True default in ChatLiteLLM)
            during AgentExecutor tool-calling. Same empty-content-per-iteration
            bug previously fixed for vertex_ai/ (CL-036) — confirmed by live run
            showing 6 consecutive Pydantic serialiser warnings about empty Message
            and Choices objects, then JIT returning empty despite HTTP 200 on every
            call. Fix: _build_llm_for_model() now sets streaming=False for ALL
            non-openrouter models (vertex_ai/ branch removed — default branch now
            handles both vertex_ai/ and gemini/ with streaming=False) | Claude via Cowork
            2.0.0 | 2026-06-25 | CL-050A: migrated ChatLiteLLM import from
            langchain_community.chat_models (deprecated in LangChain 0.3.24,
            known tool-calling bugs) to langchain_litellm (official replacement,
            LangChain GitHub #31145, PyPI langchain-litellm). API is identical for
            our usage pattern; no behaviour change expected. CL-050B: added
            MALFORMED_FUNCTION_CALL silent-failure guard in _invoke_once() —
            LiteLLM maps Gemini's MALFORMED_FUNCTION_CALL finishReason to
            finish_reason="stop" with content=None/completion_tokens=0, no
            exception fired; existing guards don't catch it (empty-tool-loop
            needs >=3 steps; zero-step gate needs steps=[]; _is_refusal needs
            non-empty text). New guard: if intermediate_steps non-empty AND
            raw_output empty → raise BadRequestError → triggers existing failover
            loop. See LiteLLM issue #16651 | Claude Code
            2.1.0 | 2026-06-25 | CL-051: migrated MODEL_1/2 from gemini/ (Google
            AI Studio, GEMINI_API_KEY) to vertex_ai/ (Vertex AI, $300 GCP credit,
            GOOGLE_APPLICATION_CREDENTIALS). GEMINI_API_KEY removed from required
            env vars — vertex_ai/ authenticates via ADC, not an API key string.
            gemini/ branch kept in _get_api_key() as DEV-I-006 fallback | Claude Code
            2.2.0 | 2026-06-25 | CL-052: added APIError to _FAILOVER_EXCEPTIONS;
            _ChatLiteLLM strips num_ctx=None (langchain_litellm forwards it to
            OpenRouter, which rejects the Ollama-only kwarg and crashed the pipeline
            uncaught). Observed during Outlook recipient smoke test | Claude Code
            1.8.0 | 2026-06-24 | CL-046 bugfix: a live run (after CL-044
            raised max_iter 12->16) still showed JIT returning empty. Direct
            repro: intermediate_steps=[], output='' — Gemini returned zero
            tool calls AND zero text on the very first turn. Confirmed via
            the installed langchain==0.3.7 source
            (agents/output_parsers/tools.py: parse_ai_message_to_tool_action)
            that ToolsAgentOutputParser returns AgentFinish immediately when
            message.tool_calls is empty — a plain return, not an exception —
            regardless of max_iterations, so raising max_iter cannot fix
            this failure mode. Neither _is_refusal() (needs non-empty text)
            nor _detect_empty_tool_loop() (needs >=3 steps present) covered
            zero steps + empty output. Added a third gate raising the same
            BadRequestError already used by the other two, reusing the
            existing failover loop in run_agent() — no new mechanism | Claude Code
            2.3.0 | 2026-06-26 | CL-055: vertex_ai/ and gemini/ models bypass
            AgentExecutor in _invoke_once() — route to core.tool_agent
            run_litellm_tool_loop() with explicit litellm.completion(stream=False).
            OpenRouter/Mistral fallbacks keep AgentExecutor. Post-invoke guards
            extracted to _apply_invoke_guards() for both paths | Claude Code
            2.4.0 | 2026-06-27 | CL-059: schema-invalid output guard — parsed array
            with rows but zero valid normalized items raises BadRequestError for
            failover (Nemotron title/url/date drift) | Claude Code
"""
import json
import logging
import os

try:  # CL-067: langchain 0.3 AgentExecutor fails to import on Python 3.14 (pydantic forward refs).
    from langchain.agents import AgentExecutor, create_tool_calling_agent
except Exception as _agent_import_error:  # noqa: BLE001 - legacy non-Google path only
    AgentExecutor = None
    create_tool_calling_agent = None
    _AGENT_IMPORT_ERROR = _agent_import_error
else:
    _AGENT_IMPORT_ERROR = None
from langchain_core.prompts import ChatPromptTemplate
from litellm.exceptions import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    Timeout,
)

from core.gateway import _build_model_chain, _get_api_key
from core.output_normalize import (
    _coerce_json_array,
    parse_and_normalize_agent_output,
    section_from_run_name,
)
from core.synthesis import JIT_JIC_MIN_ITEMS
from core.gateway import ModelCallError
from core.tool_agent import AGENT_SYSTEM_PROMPT, _uses_google_sdk_path, run_litellm_tool_loop

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 5

_FAILOVER_EXCEPTIONS = (
    ModelCallError,  # CL-063: call_model already applied same-model retries
    RateLimitError,
    AuthenticationError,
    BadRequestError,
    Timeout,
    APIConnectionError,
    APIError,
    NotFoundError,
    ServiceUnavailableError,
)


def _build_llm_for_model(model: str):
    """Construct a ChatLiteLLM instance for model, with the correct api_key and timeout (R-002).

    streaming=False is required for ALL models used in AgentExecutor tool-calling mode.
    Google's streamGenerateContent endpoint (used by both vertex_ai/ and gemini/ prefixes)
    returns content='' with finish_reason='tool_calls' on every iteration when tool-calling
    is active — confirmed for vertex_ai/ (CL-036) and now also for gemini/ prefix (CL-049).
    openrouter/ models use default streaming; num_ctx is stripped via _ChatLiteLLM (CL-052).
    """
    from langchain_litellm import ChatLiteLLM

    class _ChatLiteLLM(ChatLiteLLM):
        """Drop Ollama-only kwargs langchain_litellm always forwards when unset."""

        @property
        def _default_params(self):
            params = super()._default_params
            if params.get("num_ctx") is None:
                return {k: v for k, v in params.items() if k != "num_ctx"}
            return params

    timeout = int(os.getenv("LITELLM_TIMEOUT_SECONDS", "30"))
    if model.startswith("openrouter/"):
        return _ChatLiteLLM(
            model=model,
            model_kwargs={"api_key": os.getenv("OPENROUTER_API_KEY")},
            request_timeout=timeout,
        )
    # vertex_ai/ and gemini/ both hit Google's API — both need streaming=False
    # to avoid the streamGenerateContent empty-content-per-tool-call bug.
    return _ChatLiteLLM(
        model=model,
        model_kwargs={"api_key": _get_api_key(model)},
        request_timeout=timeout,
        streaming=False,
    )


_REFUSAL_PREFIXES = (
    "i'm unable",
    "i am unable",
    "i cannot",
    "i can't",
    "as an ai",
    "i don't have access",
    "i do not have access",
    "sorry, i",
    "unfortunately, i",
    "i can help",
    "i'll help",
    "i will help",
    "let me ",
    "sure! here",
    "sure, here",
    "of course,",
    "here are",
    "here is",
    "i've searched",
    "i have searched",
    "i found",
)

_MIN_PROSE_LENGTH = 40  # chars — below this, short valid JSON fragments pass through


def _is_refusal(output: str) -> bool:
    """
    Return True if output is a model content-refusal or conversational prose
    rather than the requested structured JSON data.

    Two detection layers:
    1. Prefix match — known refusal/conversational openers (fast path).
    2. Non-JSON prose detection — if output is >= _MIN_PROSE_LENGTH chars,
       doesn't start with '[' or '{', and json.loads() fails, treat as prose
       and trigger failover.

    Empty string is intentionally NOT a refusal here — it is the
    empty-tool-call-loop signal, handled separately by _detect_empty_tool_loop().

    Free-tier models sometimes return HTTP 200 with a refusal or conversational
    string instead of raising an exception, so no _FAILOVER_EXCEPTIONS member
    ever fires for this case on its own.
    """
    if not isinstance(output, str):
        return False
    stripped = output.strip()
    if not stripped:
        return False  # empty string — handled by _detect_empty_tool_loop
    lowered = stripped.lower()
    if any(lowered.startswith(p) for p in _REFUSAL_PREFIXES):
        return True
    if len(stripped) >= _MIN_PROSE_LENGTH and stripped[0] not in ("{", "[", "\""):
        try:
            json.loads(stripped)
            return False  # valid JSON — not a refusal
        except (ValueError, TypeError):
            return True  # non-JSON prose of sufficient length — treat as refusal
    return False


def _strip_agent_fences(text: str) -> str:
    """
    Remove markdown code fences from agent final output.

    Some models (confirmed: Gemini Flash via AgentExecutor) wrap their JSON
    response in ```json...``` even in tool-calling mode where no fences are
    expected. This causes _is_refusal() to fire (output starts with '`',
    not '[' or '{'), discarding valid results. Strip fences defensively
    before the refusal check. Does not affect gateway.py's _strip_fences()
    which serves the llm_call() path.

    Returns empty string for None/non-string input (guards against
    AgentExecutor returning output=None when max_iterations is hit).
    """
    if not isinstance(text, str):
        return ""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        inner = lines[1:]
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        return "\n".join(inner).strip()
    return stripped


_EMPTY_TOOL_LOOP_THRESHOLD = 3


def _detect_empty_tool_loop(intermediate_steps: list) -> bool:
    """
    Return True if the last _EMPTY_TOOL_LOOP_THRESHOLD steps are all
    empty-output tool calls. Indicates a model looping on
    finish_reason='tool_calls' with content='' on every iteration — confirmed
    with gpt-oss-120b:free on OpenRouter. No exception is raised in that case
    and _is_refusal() doesn't fire (output is empty), so the agent silently
    exhausts max_iter; this detector triggers failover instead (CL-038).
    """
    if len(intermediate_steps) < _EMPTY_TOOL_LOOP_THRESHOLD:
        return False
    recent = intermediate_steps[-_EMPTY_TOOL_LOOP_THRESHOLD:]
    return all(isinstance(step, tuple) and step[1] == "" for step in recent)


def _invoke_agent_executor(llm, tools: list, prompt: str, max_iter: int, run_name: str) -> dict:
    """Build a fresh tool-calling agent/executor for llm and invoke once. Rule: R-005."""
    if AgentExecutor is None or create_tool_calling_agent is None:
        raise RuntimeError(f"LangChain AgentExecutor unavailable on this Python: {_AGENT_IMPORT_ERROR}. "
                           "Use a vertex_ai/ or gemini/ model (SDK tool loop path).")
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", AGENT_SYSTEM_PROMPT),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    agent = create_tool_calling_agent(llm, tools, chat_prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=max_iter,
        early_stopping_method="force",
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )
    return executor.invoke(
        {"input": prompt},
        config={"run_name": run_name, "tags": ["daily-newsletter"]},
    )


def _check_schema_invalid_output(raw_output: str, run_name: str) -> None:
    """
    Raise BadRequestError when the model returned a full-sized JSON array but
    no rows pass JIT/JIC schema validation after normalization (CL-059).

    Only fires at count >= JIT_JIC_MIN_ITEMS so partial/incomplete test or
    single-item outputs defer to main.py gap-fill instead of burning failover.
    """
    section = section_from_run_name(run_name)
    if not section or not raw_output.strip():
        return
    raw_items = _coerce_json_array(raw_output)
    if len(raw_items) < JIT_JIC_MIN_ITEMS:
        return
    valid_items = parse_and_normalize_agent_output(raw_output, section)
    if valid_items:
        return
    raise BadRequestError(
        message=(
            f"Agent returned {len(raw_items)} {section.upper()} items but none "
            "passed schema validation after field normalization — triggering "
            "model failover."
        ),
        model=run_name,
        llm_provider="litellm",
        response=None,
    )


def _apply_invoke_guards(result: dict, max_iter: int, run_name: str) -> dict:
    """Shared post-invoke validation for AgentExecutor and SDK tool-loop paths."""
    if result.get("output") is None:
        logger.warning(
            f"R-005: agent hit max_iterations={max_iter} — "
            "returning partial result; task may be incomplete"
        )

    intermediate_steps = result.get("intermediate_steps", [])
    if _detect_empty_tool_loop(intermediate_steps):
        raise BadRequestError(
            message=(
                f"Empty tool-call loop detected: {_EMPTY_TOOL_LOOP_THRESHOLD}+ "
                "consecutive empty tool responses — triggering model failover."
            ),
            model=run_name,
            llm_provider="litellm",
            response=None,
        )

    if not intermediate_steps and not result.get("output"):
        raise BadRequestError(
            message=(
                "Agent returned zero tool calls and an empty final answer "
                "on the first turn — triggering model failover."
            ),
            model=run_name,
            llm_provider="litellm",
            response=None,
        )

    raw_output = result.get("output") or ""

    if raw_output.strip() == "Agent stopped due to max iterations.":
        raise BadRequestError(
            message="Agent hit max_iterations without synthesising output — triggering failover.",
            model=run_name,
            llm_provider="litellm",
            response=None,
        )

    if intermediate_steps and not raw_output:
        raise BadRequestError(
            message=(
                "Agent returned non-empty intermediate steps but empty final output — "
                "possible MALFORMED_FUNCTION_CALL (Gemini silent failure). "
                "Triggering model failover."
            ),
            model=run_name,
            llm_provider="litellm",
            response=None,
        )

    stripped_output = _strip_agent_fences(raw_output)
    if stripped_output != raw_output:
        logger.debug("Stripped markdown fences from agent output before refusal check")
        result = dict(result)
        result["output"] = stripped_output
        raw_output = stripped_output
    if _is_refusal(raw_output):
        raise BadRequestError(
            message=f"Model content-refusal or prose output: {raw_output[:120]}",
            model=run_name,
            llm_provider="litellm",
            response=None,
        )
    _check_schema_invalid_output(raw_output, run_name)
    return result


def _invoke_once(
    llm,
    tools: list,
    prompt: str,
    max_iter: int,
    run_name: str,
    model: str = None,
) -> dict:
    """Invoke once via SDK tool loop (Google) or AgentExecutor (other providers)."""
    if _uses_google_sdk_path(model):
        result = run_litellm_tool_loop(
            model=model,
            tools=tools,
            user_prompt=prompt,
            max_iter=max_iter,
        )
    else:
        result = _invoke_agent_executor(llm, tools, prompt, max_iter, run_name)
    return _apply_invoke_guards(result, max_iter, run_name)


def _next_model(chain: list, current_model: str) -> str | None:
    """Return the model after current_model in chain, or None if exhausted."""
    idx = chain.index(current_model) + 1 if current_model in chain else 0
    return chain[idx] if idx < len(chain) else None


def run_agent(
    llm=None,
    tools: list = None,
    prompt: str = "",
    max_iter: int = MAX_ITERATIONS,
    run_name: str = "daily-jit-jic-agent",
    model: str = None,
) -> dict:
    """
    Run a LangChain ReACT agent with a hard iteration cap and model failover.

    core.gateway._build_model_chain() is deferred until actually needed — if
    `llm` is supplied and the first attempt succeeds, the chain is never built.
    On RateLimitError, AuthenticationError, BadRequestError, or Timeout, rebuilds
    the LLM with the next model in the chain and retries once per fallback (R-002).

    Args:
        llm: Optional pre-built LangChain LLM for the first attempt. If None,
            one is built from `model` (or the chain's first entry).
        tools: List of LangChain Tool objects available to the agent.
        prompt: User-facing task description.
        max_iter: Hard iteration ceiling (default MAX_ITERATIONS = 5).
        run_name: Label sent to LangSmith via executor.invoke() config.
        model: Starting model name, used for logging and chain position.
            Required if `llm` is None and not otherwise resolvable from the chain.

    Returns:
        dict with key "output". If the entire failover chain is exhausted,
        also has key "error" and output is "All models exhausted".
    """
    tools = tools or []
    timeout = int(os.getenv("LITELLM_TIMEOUT_SECONDS", "30"))
    chain = None
    current_model = model
    current_llm = llm
    last_error = None

    while True:
        if current_llm is None:
            if chain is None:
                chain = _build_model_chain()
                current_model = current_model or chain[0]
            current_llm = _build_llm_for_model(current_model)

        try:
            return _invoke_once(
                current_llm, tools, prompt, max_iter, run_name, current_model
            )
        except _FAILOVER_EXCEPTIONS as exc:
            if isinstance(exc, Timeout):
                logger.warning(f"Model {current_model} timed out after {timeout}s, trying next")
            else:
                logger.warning(f"Model {current_model} failed: {exc} — trying next in chain")
            last_error = exc

        chain = chain or _build_model_chain()
        next_model = _next_model(chain, current_model)
        if next_model is None:
            logger.error(
                f"Failover chain exhausted — all models tried, last error: {last_error}. "
                "Agent will return empty for this run."
            )
            break
        current_model, current_llm = next_model, None

    logger.critical(f"R-002: all models in failover chain exhausted: {last_error}")
    return {"output": "All models exhausted", "error": str(last_error)}
