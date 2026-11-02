"""
MODULE: gateway.py
PURPOSE: LiteLLM SDK-direct gateway with failover chain and daily token-budget enforcement
INPUTS: prompt (str); model_name (str, optional, ignored — gateway drives failover internally)
OUTPUTS: dict {response, model_used, tokens_used, cost, timestamp}
DEPENDENCIES: litellm
RULE REFERENCES: R-002, ZT-001, SEC-X-001
CHANGE LOG: 1.0.0 | 2026-06-16 | TC-002 initial implementation | Claude Code
            1.1.0 | 2026-06-17 | Bugfix: replaced hardcoded GOOGLE_API_KEY with
            _get_api_key(model) helper — routes the correct key per provider in
            the failover chain (Mistral/Ollama were silently sent the Gemini key) | Claude Code
            1.2.0 | 2026-06-17 | Bugfix: _build_model_chain() now reads
            LITELLM_MODEL_1, _2, _3... from env sequentially until a key is
            missing, replacing the hardcoded model list. No more API-key-presence
            conditional (the old "skip Mistral if MISTRAL_API_KEY unset" behavior
            is removed by design — superseded T-GAT-E-003). _get_api_key() gained
            a groq/ branch. _scrub_secrets() now also scrubs GROQ_API_KEY | Claude Code
            1.3.0 | 2026-06-18 | CL-022 bugfix: .env's LITELLM_MODEL_1/2/3 are
            now all openrouter/ models, but _get_api_key() had no branch for
            them — every call was silently sent with no API key (fell through
            to the final `return None`). Added an openrouter/ branch | Claude Code
            1.4.0 | 2026-06-18 | CL-023 bugfix: added OPENROUTER_API_KEY to
            _scrub_secrets()'s redaction loop (SEC-X-001 gap — OpenRouter is
            now a live provider but its key was never scrubbed from log
            output) | Claude Code
            1.5.0 | 2026-06-22 | CL-033: GOOGLE_API_KEY retired — its Google
            AI Studio project's prepaid credits were exhausted (429
            RESOURCE_EXHAUSTED, noted around CL-016) and it is no longer
            used anywhere. GEMINI_API_KEY is the sole Gemini credential going
            forward: _get_api_key()'s gemini/ branch now reads it exclusively
            (no fallback to GOOGLE_API_KEY), and _scrub_secrets() redacts it
            instead. gemini/gemini-2.0-flash added as LITELLM_MODEL_2 in
            .env — the failover chain remains purely env-var driven via
            _build_model_chain(), no hardcoded model names | Claude Code
            1.6.0 | 2026-06-22 | CL-039 bugfix: a sixth live run showed
            Gemini 2.5 Flash-Lite (the lesson agent's direct llm_call() path,
            CL-037's DEV-I-005 exception) returning valid lesson JSON wrapped
            in markdown code fences (```json ... ```). json.loads() in
            _run_lesson_agent() rejected the fenced string outright, even
            though the JSON inside was complete and correct. Instruction-
            tuned models default to this formatting under RLHF training
            unless explicitly constrained. Fix: pass
            response_format={"type": "json_object"} to litellm.completion()
            (the primary, API-level fix — LiteLLM translates it to each
            provider's native param) plus a defensive _strip_fences() helper
            applied to the response text, covering any provider that ignores
            the hint (some free-tier OpenRouter models silently drop
            unsupported params). The AgentExecutor/tool-calling path used by
            JIT/JIC (core/orchestration.py) is untouched — it never returns
            fenced content and response_format would conflict with
            tool-calling mode | Claude Code
            1.7.0 | 2026-06-22 | CL-041: MODEL_1/2 migrated from gemini/
            (Google AI Studio free quota — 15 RPM) to vertex_ai/ (Vertex AI,
            $300 GCP credit — 1000 RPM on Flash). Vertex AI authenticates via
            GOOGLE_APPLICATION_CREDENTIALS (a service-account JSON file path)
            picked up automatically by Google's Application Default
            Credentials — not an api_key= string. Added an explicit
            vertex_ai/ branch to _get_api_key() returning None (passing an
            api_key= to litellm.completion() for a vertex_ai/ model would
            conflict with ADC). The gemini/ branch is unchanged and kept as
            a fallback for AI Studio models | Claude Code
            1.9.0 | 2026-06-27 | CL-059: _litellm_completion() wraps litellm.completion()
            with a brief OpenRouter 429 backoff (Retry-After or 3s default) before
            failover; exported for core.tool_agent SDK path | Claude Code
            1.8.0 | 2026-06-25 | CL-051: GEMINI_API_KEY removed from required
            env vars — MODEL_1/2 now use vertex_ai/ prefix exclusively.
            GEMINI_API_KEY retained in _scrub_secrets() and _get_api_key()'s
            gemini/ branch as a DEV-I-006 fallback (if Vertex AI credit runs
            out, operator adds GEMINI_API_KEY and changes MODEL_1/2 prefix
            back to gemini/ — no code changes needed). No code changes in this
            file — the vertex_ai/ branch in _get_api_key() was already correct
            (CL-041) and the scrub loop already handles unset keys gracefully
            (T-GAT-E-006 confirmed) | Claude Code
            2.0.0 | 2026-11-01 | CL-063: call_model() / call_with_fallback() for
            Gemini 3/4 on Vertex (D12-D14): vertex_location (global), reasoning_effort
            (medium), 180s timeout, JSON-schema output, classified errors (retry 429/5xx/
            timeout max 2x with backoff per Google guidance; fail fast on 400/401/403/404),
            network wait on connection errors, finish_reason checks (length, content
            filter, empty), per-call telemetry to run_logger, daily cost guard.
            llm_call() now routes through call_with_fallback() | Claude Code
"""
import json
import logging
import os
import time
from datetime import date, datetime

import socket

import litellm
from litellm import exceptions as llm_exc
from litellm.exceptions import RateLimitError

from core import run_logger
from core.settings import load_settings

logger = logging.getLogger(__name__)


class TokenBudgetExceededError(Exception):
    """Raised when a model's today token usage >= TOKEN_ALERT_THRESHOLD * daily limit."""


def _today_str() -> str:
    """Return ISO-format date string for today (YYYY-MM-DD)."""
    return date.today().isoformat()


def _require_provider_prefix(model: str) -> str:
    """
    Validate that model string includes a LiteLLM provider prefix (e.g. 'gemini/...').

    Args:
        model: Model identifier to validate.

    Returns:
        The unchanged model string if valid.

    Raises:
        ValueError: if '/' is absent — LiteLLM will silently fail without it (BUG-002 fix).
    """
    if "/" not in model:
        raise ValueError(
            f"Model string must include provider prefix (e.g. 'gemini/gemini-2.5-flash'), got: {model!r}"
        )
    return model


def _build_model_chain() -> list[str]:
    """
    Build the ordered failover chain from LITELLM_MODEL_1, _2, _3... env vars.

    Reads sequentially until a key is missing. No API-key-presence conditional —
    every configured entry is included unconditionally, regardless of whether
    its corresponding API key is set (superseded the old MISTRAL_API_KEY-gated
    skip behavior).

    Returns:
        List of provider-prefixed model strings in failover priority order.

    Raises:
        RuntimeError: if LITELLM_MODEL_1 is not set in the environment.
    """
    chain, i = [], 1
    while model := os.getenv(f"LITELLM_MODEL_{i}"):
        chain.append(model.strip())
        i += 1
    if not chain:
        raise RuntimeError("No LITELLM_MODEL_1 found in environment")
    return chain


_LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")


def _load_token_log() -> dict:
    """Read logs/token_usage.json; return empty dict if file absent."""
    log_path = os.path.join(_LOGS_DIR, "token_usage.json")
    if os.path.exists(log_path):
        with open(log_path) as f:
            return json.load(f)
    return {}


def _save_token_log(data: dict) -> None:
    """
    Persist token log to logs/token_usage.json.

    BUG-003 fix: os.makedirs ensures the logs/ directory exists before writing.
    CL-FIX: use absolute path derived from __file__ so launchd / sandbox runs
    (where cwd may be read-only) can still write token usage.
    """
    os.makedirs(_LOGS_DIR, exist_ok=True)
    with open(os.path.join(_LOGS_DIR, "token_usage.json"), "w") as f:
        json.dump(data, f, indent=2)


def _check_token_limit(model: str) -> None:
    """
    Raise TokenBudgetExceededError if today's token usage >= threshold * daily limit.

    BUG-001 fix: reads DAILY_TOKEN_LIMIT_GEMINI from env (no wrong attribute reference).

    Args:
        model: Provider-prefixed model string to check.

    Raises:
        TokenBudgetExceededError: when usage >= threshold. Rule: R-002.
    """
    daily_limit = int(os.getenv("DAILY_TOKEN_LIMIT_GEMINI", "900000"))
    threshold = float(os.getenv("TOKEN_ALERT_THRESHOLD", "0.95"))

    token_log = _load_token_log()
    model_data = token_log.get(model, {})

    if model_data.get("date") != _today_str():
        return  # No usage logged today for this model

    tokens_used = model_data.get("tokens_used", 0)
    if tokens_used >= daily_limit * threshold:
        logger.warning(
            f"Token budget exceeded for {model}: {tokens_used}/{daily_limit} tokens "
            f"(>= {threshold * 100:.0f}% threshold)"
        )
        raise TokenBudgetExceededError(f"Token budget exceeded for {model}")


def _log_token_usage(model: str, tokens: int) -> None:
    """
    Append token count to logs/token_usage.json; resets counter when the date changes.

    Args:
        model: Provider-prefixed model string.
        tokens: Number of tokens to add to today's running total.
    """
    token_log = _load_token_log()
    today = _today_str()
    model_data = token_log.get(model, {})

    if model_data.get("date") != today:
        model_data = {"tokens_used": 0, "date": today}

    model_data["tokens_used"] = model_data.get("tokens_used", 0) + tokens
    token_log[model] = model_data
    _save_token_log(token_log)


def _scrub_secrets(message: str) -> str:
    """
    Replace configured API key values in a string with [REDACTED].

    Prevents key leakage into log output even when provider error messages echo them back.
    Rule: ZT-001 (secret isolation).
    """
    for env_var in ("GEMINI_API_KEY", "MISTRAL_API_KEY", "LANGCHAIN_API_KEY", "TAVILY_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY", "SENDGRID_API_KEY", "EXA_API_KEY"):
        secret = os.getenv(env_var, "")
        if secret:
            message = message.replace(secret, "[REDACTED]")
    return message


def _strip_fences(text: str) -> str:
    """
    Remove markdown code fences from LLM response text.

    Instruction-tuned models (Gemini, Mistral, OpenRouter-hosted) sometimes
    wrap JSON output in ```json ... ``` or ``` ... ``` fences by default,
    even when response_format=json_object is requested — particularly free-tier
    or fallback models that silently ignore the response_format hint.

    This is a defensive layer. The primary fix is passing response_format in
    llm_call() so providers constrain output at the API level. This function
    handles any residual fence wrapping that slips through.

    Called only in llm_call() before returning the response key.
    NOT called in orchestration.py — AgentExecutor/tool-calling path never
    returns fenced content and must not be touched (JIT/JIC path, CL-038 confirmed).
    """
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        # Remove opening fence line (```json or ```) and closing fence (```)
        inner_lines = lines[1:]  # drop first line
        # Find and remove closing fence
        if inner_lines and inner_lines[-1].strip() == "```":
            inner_lines = inner_lines[:-1]
        return "\n".join(inner_lines).strip()
    return stripped


_OPENROUTER_RETRY_ATTEMPTS = 2
_OPENROUTER_RETRY_DEFAULT_SECONDS = 3.0


def _retry_after_seconds(exc: Exception) -> float:
    """Read Retry-After from a LiteLLM/OpenRouter rate-limit error when present."""
    retry_after = getattr(exc, "retry_after", None)
    if retry_after is not None:
        try:
            return max(float(retry_after), 1.0)
        except (TypeError, ValueError):
            pass
    return _OPENROUTER_RETRY_DEFAULT_SECONDS


def _litellm_completion(**kwargs):
    """
    Call litellm.completion with a brief OpenRouter 429 retry (CL-059).

    OpenRouter free tier returns HTTP 429 with Retry-After; one backoff retry
    often succeeds without burning the full failover chain.
    """
    model = str(kwargs.get("model", ""))
    attempts = _OPENROUTER_RETRY_ATTEMPTS if model.startswith("openrouter/") else 1
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return litellm.completion(**kwargs)
        except RateLimitError as exc:
            last_error = exc
            if attempt >= attempts - 1:
                raise
            delay = _retry_after_seconds(exc)
            logger.warning(
                f"Rate limit on {model} — backing off {delay:.0f}s before retry "
                f"({attempt + 1}/{attempts})"
            )
            time.sleep(delay)
    if last_error:
        raise last_error
    raise RuntimeError("litellm.completion retry loop exited without result")


def _get_api_key(model: str) -> str | None:
    """
    Return the correct API key env var value for a provider-prefixed model string.

    Args:
        model: Provider-prefixed model string (e.g. "gemini/gemini-2.5-flash").

    Returns:
        The matching API key string, or None for providers that need no key
        (Ollama, vertex_ai/, and any future local/keyless provider).
    """
    if model.startswith("vertex_ai/"):
        return None  # Vertex AI authenticates via GOOGLE_APPLICATION_CREDENTIALS
                     # env var (JSON key file path). LiteLLM picks it up automatically
                     # via Google ADC. Do NOT pass an api_key= arg — it will conflict.
    if model.startswith("gemini/"):
        return os.getenv("GEMINI_API_KEY")
    if model.startswith("mistral/"):
        return os.getenv("MISTRAL_API_KEY")
    if model.startswith("groq/"):
        return os.getenv("GROQ_API_KEY")
    if model.startswith("openrouter/"):
        return os.getenv("OPENROUTER_API_KEY")
    return None


def llm_call(prompt: str, model_name: str = None, *, schema: dict | None = None,
             stage: str = "llm_call", schema_name: str = "output") -> dict:
    """
    Send a single-turn prompt through the model chain (CL-063).

    Args:
        prompt: user message text.
        model_name: ignored (gateway drives model choice from LITELLM_MODEL_N).
        schema: optional JSON schema; when given the model must return JSON
            matching it (Vertex structured output) and the parsed dict is
            returned under "parsed".
        stage: label for telemetry (e.g. "lesson", "jit-editor").
        schema_name: name passed with the schema.

    Returns:
        dict: response (str), parsed (dict|None), model_used, tokens_used,
        cost, timestamp.

    Raises:
        ModelCallError: when every model in the chain failed.
    """
    response_format = (
        {"type": "json_schema", "json_schema": {"name": schema_name, "schema": schema}}
        if schema else {"type": "json_object"}
    )
    response, model = call_with_fallback(
        [{"role": "user", "content": prompt}], stage=stage, response_format=response_format,
    )
    text = _strip_fences(response.choices[0].message.content or "")
    parsed = None
    if schema:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ModelCallError(f"{stage}: schema output was not valid JSON: {exc}") from exc
    usage = getattr(response, "usage", None)
    return {
        "response": text,
        "parsed": parsed,
        "model_used": model,
        "tokens_used": getattr(usage, "total_tokens", 0) if usage else 0,
        "cost": _cost(response),
        "timestamp": datetime.utcnow().isoformat(),
    }



# ---------------------------------------------------------------------------
# CL-063: policy-driven model calls (Gemini 3/4 on Vertex)
# ---------------------------------------------------------------------------

class ModelCallError(Exception):
    """A model call failed after the retry policy (or for a non-retryable reason)."""

    def __init__(self, message: str, *, retryable: bool = False, cause: Exception | None = None):
        super().__init__(message)
        self.retryable = retryable
        self.cause = cause


class TruncatedOutputError(ModelCallError):
    """finish_reason == length: output cut off, no exception from the API."""


class ContentBlockedError(ModelCallError):
    """finish_reason indicates a safety/content block."""


class EmptyOutputError(ModelCallError):
    """No text and no tool calls returned."""


class DailyCostExceededError(ModelCallError):
    """This run's spend passed DAILY_COST_LIMIT_USD; no further model calls."""


_RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}
_sleep = time.sleep  # indirection so tests can stub waits without touching the global time module
_NON_RETRYABLE = tuple(c for c in (
    getattr(llm_exc, "UnsupportedParamsError", None), getattr(llm_exc, "ContextWindowExceededError", None),
    getattr(llm_exc, "ContentPolicyViolationError", None), getattr(llm_exc, "AuthenticationError", None),
    getattr(llm_exc, "PermissionDeniedError", None), getattr(llm_exc, "NotFoundError", None),
    getattr(llm_exc, "BadRequestError", None),
) if c is not None)
_RETRYABLE = tuple(c for c in (
    getattr(llm_exc, "RateLimitError", None), getattr(llm_exc, "Timeout", None),
    getattr(llm_exc, "APIConnectionError", None), getattr(llm_exc, "ServiceUnavailableError", None),
    getattr(llm_exc, "InternalServerError", None),
) if c is not None)
_BLOCK_REASONS = {"content_filter", "safety", "recitation", "blocklist", "prohibited_content", "spii"}


def classify_error(exc: Exception) -> str:
    """Return 'retryable', 'network', or 'fatal' for an exception from litellm."""
    if isinstance(exc, ModelCallError):
        return "retryable" if exc.retryable else "fatal"
    name = type(exc).__name__
    if "Timeout" in name:
        return "retryable"
    if isinstance(exc, getattr(llm_exc, "APIConnectionError", ())) or "Connection" in name:
        return "network"
    if isinstance(exc, _RETRYABLE):
        return "retryable"
    if isinstance(exc, _NON_RETRYABLE):
        return "fatal"
    status = getattr(exc, "status_code", None)
    if status in _RETRYABLE_STATUS:
        return "retryable"
    return "fatal" if status else "retryable"


def wait_for_network(host: str = "aiplatform.googleapis.com", max_wait: int | None = None,
                     interval: int = 15, sleep=None) -> bool:
    """Block until DNS resolves host (laptop waking from sleep) or max_wait passes."""
    sleep = sleep or _sleep
    max_wait = load_settings().network_wait_seconds if max_wait is None else max_wait
    waited = 0
    while True:
        try:
            socket.getaddrinfo(host, 443)
            return True
        except OSError:
            if waited >= max_wait:
                return False
            logger.warning(f"Network not ready ({host}); waiting {interval}s ({waited}/{max_wait}s)")
            sleep(interval)
            waited += interval


def _cost(response) -> float:
    try:
        return float(litellm.completion_cost(completion_response=response) or 0.0)
    except Exception:
        return 0.0


def _usage_dict(response) -> dict:
    usage = getattr(response, "usage", None)
    if not usage:
        return {}
    details = getattr(usage, "completion_tokens_details", None)
    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
        "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
        "reasoning_tokens": getattr(details, "reasoning_tokens", None) if details else None,
    }


def _model_kwargs(model: str, settings) -> dict:
    """Provider-specific kwargs (D12-D13)."""
    kwargs = {"timeout": settings.timeout_seconds, "stream": False}
    if model.startswith("vertex_ai/"):
        kwargs["vertex_location"] = settings.vertex_location
        if settings.reasoning_effort:
            kwargs["reasoning_effort"] = settings.reasoning_effort
    api_key = _get_api_key(model)
    if api_key:
        kwargs["api_key"] = api_key
    return kwargs


def _check_finish(response, model: str, allow_tool_calls: bool) -> None:
    choice = response.choices[0]
    reason = str(getattr(choice, "finish_reason", "") or "").lower()
    message = choice.message
    has_tools = bool(getattr(message, "tool_calls", None))
    if reason == "length":
        raise TruncatedOutputError(f"{model}: output truncated (finish_reason=length)", retryable=True)
    if reason in _BLOCK_REASONS:
        raise ContentBlockedError(f"{model}: output blocked (finish_reason={reason})", retryable=True)
    if not (message.content or "").strip() and not (allow_tool_calls and has_tools):
        raise EmptyOutputError(f"{model}: empty output (finish_reason={reason or 'none'})", retryable=True)


def call_model(model: str, messages: list, *, stage: str, tools: list | None = None,
               response_format: dict | None = None, sleep=None):
    """
    One model, classified retries (Google guidance: max 2 retries, exponential
    backoff from 1s; never retry 400/401/403/404). Returns the litellm response.
    """
    sleep = sleep or _sleep
    settings = load_settings()
    ctx = run_logger.current()
    if ctx and settings.daily_cost_limit_usd and ctx.summary.get("cost_usd", 0) >= settings.daily_cost_limit_usd:
        raise DailyCostExceededError(f"Run cost reached DAILY_COST_LIMIT_USD={settings.daily_cost_limit_usd}")
    kwargs = {"model": model, "messages": messages, **_model_kwargs(model, settings)}
    if tools:
        kwargs["tools"] = tools
    if response_format:
        kwargs["response_format"] = response_format
    attempts = 1 + max(settings.max_retries, 0)
    last: Exception | None = None
    for attempt in range(1, attempts + 1):
        t0 = time.time()
        try:
            _check_token_limit(model)
            response = litellm.completion(**kwargs)
            _check_finish(response, model, allow_tool_calls=bool(tools))
            usage = _usage_dict(response)
            cost = _cost(response)
            _log_token_usage(model, usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0))
            if ctx:
                ctx.record_llm_call(stage, model, attempt, time.time() - t0, usage, cost,
                                    getattr(response.choices[0], "finish_reason", None))
            return response
        except TokenBudgetExceededError as exc:
            raise ModelCallError(str(exc), retryable=False, cause=exc) from exc
        except Exception as exc:  # noqa: BLE001 - classified below
            last = exc
            kind = classify_error(exc)
            if ctx:
                ctx.record_llm_call(stage, model, attempt, time.time() - t0, {}, 0.0, None, type(exc).__name__)
                ctx.record_error(stage, _scrub_secrets(str(exc)), severity="WARNING" if kind != "fatal" else "ERROR",
                                 model=model, error_class=type(exc).__name__,
                                 http_status=getattr(exc, "status_code", None), attempt=attempt,
                                 action_taken="retry" if kind != "fatal" and attempt < attempts else "give up")
            logger.warning(f"{stage}: {model} attempt {attempt}/{attempts} failed ({kind}): "
                           f"{_scrub_secrets(str(exc))[:200]}")
            if kind == "fatal" or attempt >= attempts:
                break
            if kind == "network" and not wait_for_network(sleep=sleep):
                break
            delay = _retry_after_seconds(exc) if isinstance(exc, RateLimitError) else float(2 ** (attempt - 1))
            sleep(delay)
    retryable = classify_error(last) != "fatal" if last else False
    raise ModelCallError(f"{stage}: {model} failed: {_scrub_secrets(str(last))[:300]}",
                         retryable=retryable, cause=last)


def call_with_fallback(messages: list, *, stage: str, tools: list | None = None,
                       response_format: dict | None = None, chain: list | None = None, sleep=None):
    """
    Try each model in LITELLM_MODEL_1..N (D12 primary, D14 fallback) with call_model().
    Returns (response, model_used). Raises ModelCallError when all fail.
    """
    chain = chain or load_settings().model_chain
    if not chain:
        raise RuntimeError("No LITELLM_MODEL_1 found in environment")
    ctx = run_logger.current()
    last: Exception | None = None
    for idx, model in enumerate(chain):
        try:
            response = call_model(model, messages, stage=stage, tools=tools,
                                  response_format=response_format, sleep=sleep)
            if idx > 0 and ctx:
                ctx.set(fallback_used=1)
            return response, model
        except DailyCostExceededError:
            raise
        except ModelCallError as exc:
            last = exc
            logger.error(f"{stage}: {model} exhausted ({exc}); "
                         f"{'trying ' + chain[idx + 1] if idx + 1 < len(chain) else 'no fallback left'}")
    raise ModelCallError(f"{stage}: all models failed; last error: {last}", cause=last)
