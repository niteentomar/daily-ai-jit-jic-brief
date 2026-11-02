"""
MODULE: check_env.py
PURPOSE: Validate required .env keys are present, non-empty, and non-placeholder
         before the pipeline runs; scan project files for leaked secret patterns.
INPUTS: .env file path (default ".env"); list of file paths to scan for secrets
OUTPUTS: validate_env() raises ValueError on invalid config, else returns True.
         scan_for_secrets() returns a list of finding dicts (empty if clean).
DEPENDENCIES: re, sys, pathlib (stdlib only)
RULE REFERENCES: ZT-001, SEC-X-001, SEC-X-002, SEC-X-003
CHANGE LOG: 1.0.0 | 2026-06-16 | TC-001 initial implementation | Claude Code
            1.1.0 | 2026-06-16 | TC-002 out-of-band fix: removed LITELLM_MASTER_KEY
            and LITELLM_PORT from REQUIRED_KEYS — vestigial after the gateway's
            architecture was confirmed SDK-direct (litellm.completion(), no
            local proxy server to authenticate/configure) | Claude Code
            1.2.0 | 2026-06-17 | TC-010 GMAIL cleanup: removed GMAIL_APP_PASSWORD
            and GMAIL_SENDER from REQUIRED_KEYS (Gmail dropped in TC-006);
            promoted SENDGRID_API_KEY from OPTIONAL_KEYS to REQUIRED_KEYS
            (sole delivery provider since TC-006) | Claude Code
            1.3.0 | 2026-06-17 | Bugfix: added LITELLM_MODEL_1 to REQUIRED_KEYS
            (failover chain is now env-var driven, core/gateway.py); added
            GROQ_API_KEY to OPTIONAL_KEYS (Groq is now a configurable provider).
            LITELLM_PRIMARY_MODEL was never present in either list — nothing
            to remove there | Claude Code
            1.4.0 | 2026-06-18 | CL-022 added OPENROUTER_API_KEY to OPTIONAL_KEYS
            (fallback provider, not required — same tier as GROQ_API_KEY/
            MISTRAL_API_KEY) | Claude Code
            1.5.0 | 2026-06-21 | CL-024 bugfix: validate_env()'s default
            env_path was ".env" — resolved relative to the process cwd, not
            the project root. Under launchd (cwd is not the project root) this
            raised FileNotFoundError before any key validation ran, observed
            3 times in logs/launchd_stderr.log. Default now anchored to the
            existing PROJECT_ROOT constant (Path(__file__).resolve().parent.parent),
            so resolution is identical regardless of caller's cwd | Claude Code
            1.6.0 | 2026-06-22 | CL-027 added EMAIL_FROM to REQUIRED_KEYS —
            core/delivery.py was using TARGET_EMAIL (the recipient) as the
            sender address too; a dedicated, validated EMAIL_FROM decouples
            the two so a missing sender fails fast at startup, not silently
            at send time. GMAIL_SENDER was deliberately not revived — it was
            removed from REQUIRED_KEYS in CL-013 (Gmail dropped in TC-006) | Claude Code
            1.7.0 | 2026-06-22 | CL-033: GOOGLE_API_KEY removed from
            REQUIRED_KEYS — its Google AI Studio project's credits were
            exhausted and it is no longer referenced anywhere in core/gateway.py.
            GEMINI_API_KEY added as its replacement (sole Gemini credential,
            backs LITELLM_MODEL_2=gemini/gemini-2.0-flash) | Claude Code
            1.8.0 | 2026-06-22 | CL-034 .env cleanup: removed OPENAI_API_KEY
            from OPTIONAL_KEYS — never wired to any provider routing in
            core/gateway.py (_get_api_key() has no openai/ branch); confirmed
            zero test references before removing. GOOGLE_API_KEY,
            GMAIL_APP_PASSWORD, GMAIL_SENDER removed from .env itself (all
            three already had zero functional code references — only
            historical changelog comments) | Claude Code
            1.9.0 | 2026-06-22 | CL-041: added GOOGLE_APPLICATION_CREDENTIALS
            to REQUIRED_KEYS — MODEL_1/2 migrated from gemini/ (GEMINI_API_KEY,
            AI Studio free quota) to vertex_ai/ (Vertex AI, $300 GCP credit),
            which authenticates via a service-account JSON file path in this
            env var rather than an API key string. GEMINI_API_KEY stays
            required as a fallback for the gemini/ chain members | Claude Code
            2.0.0 | 2026-06-25 | CL-051: GEMINI_API_KEY removed from REQUIRED_KEYS
            — MODEL_1/2 migrated from gemini/ (Google AI Studio) to vertex_ai/
            (Vertex AI). vertex_ai/ authenticates via GOOGLE_APPLICATION_CREDENTIALS
            (ADC); no API key string needed. GEMINI_API_KEY moved to OPTIONAL_KEYS
            as a fallback for gemini/ prefix chain members if Vertex AI fails.
            GOOGLE_APPLICATION_CREDENTIALS stays required | Claude Code
"""
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_KEYS = [
    "LANGCHAIN_API_KEY",
    "LANGCHAIN_TRACING_V2",
    "LANGCHAIN_PROJECT",
    "TAVILY_API_KEY",
    "SENDGRID_API_KEY",
    "TARGET_EMAIL",
    "EMAIL_FROM",
    "DAILY_TOKEN_LIMIT_GEMINI",
    "TOKEN_ALERT_THRESHOLD",
    "LITELLM_MODEL_1",
    "GOOGLE_APPLICATION_CREDENTIALS",
]

# Optional per MASTER_PLAN.md Section 16 — absence never triggers a fatal crash.
# Note (TC-006): GMAIL_APP_PASSWORD and GMAIL_SENDER removed — Gmail delivery
# was dropped; SENDGRID_API_KEY promoted to REQUIRED_KEYS (sole provider).
# Note (CL-051): GEMINI_API_KEY downgraded from REQUIRED to OPTIONAL — MODEL_1/2
# migrated from gemini/ (AI Studio) to vertex_ai/ (Vertex AI). GEMINI_API_KEY
# is retained as a fallback for gemini/ prefix chain members per DEV-I-006.
OPTIONAL_KEYS = [
    "EXA_API_KEY",
    "GEMINI_API_KEY",
    "MISTRAL_API_KEY",
    "GROQ_API_KEY",
    "OPENROUTER_API_KEY",
]

# Case-sensitive. Mirrors Python source assignment style ("api_key = ...")
# rather than .env KEY=value style, so .env.example's placeholder lines never
# false-positive. Patterns from RULES.md SEC-X-003. "sk-" is a compiled regex
# requiring a realistic key-length run after the prefix (real OpenAI-style keys
# are 20-50+ chars) — a bare "sk-" substring also matches common English
# hyphenated words ("Task-level", "task-specific"), which produced false
# positives against MASTER_PLAN.md / AGENT_EXECUTION_PROTOCOL.md during Phase 4
# review. The other five patterns stay literal substrings.
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    "AIza",
    "Bearer ",
    "api_key =",
    "token =",
    "password =",
]

# A value is a placeholder if it ends in "_here" or contains "changeme"/"xxx".
PLACEHOLDER_RE = re.compile(r"(_here$|changeme|xxx)", re.IGNORECASE)

# Files known to legitimately contain pattern-shaped strings as documentation
# or test fixtures, not real secrets. Excluded from scan_for_secrets()
# regardless of caller input — mirrors how real scanners (gitleaks, trufflehog)
# allowlist their own rule-definition and fixture files.
# - check_env.py: defines the patterns themselves (Decision 3)
# - tests/test_env.py, tests/test_security.py: fake key-shaped fixture values
#   and a deliberately planted fake secret (Decision 3)
# - RULES.md, docs/protocol/AGENT_EXECUTION_PROTOCOL.md: files_forbidden (this
#   agent cannot reword them) and both must literally document the SEC-X-003
#   pattern list and a "FORBIDDEN" code example to explain the rule — found
#   during Phase 4 pre-commit scan, owner-approved fix (3-part surgical fix)
SELF_EXCLUDED_FILES = {
    Path(__file__).resolve(),
    PROJECT_ROOT / "tests" / "test_env.py",
    PROJECT_ROOT / "tests" / "test_security.py",
    PROJECT_ROOT / "RULES.md",
    PROJECT_ROOT / "docs" / "protocol" / "AGENT_EXECUTION_PROTOCOL.md",
}


def _parse_env_file(env_path) -> dict:
    """Parse a simple KEY=value .env file into a dict. Skips blanks/comments."""
    values = {}
    for line in Path(env_path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


def validate_env(env_path: str = str(PROJECT_ROOT / ".env")) -> bool:
    """
    Validate that every REQUIRED_KEYS entry is present in env_path, non-empty,
    and not a placeholder value.

    Args:
        env_path: Path to the .env-style file to validate.

    Returns:
        True if all required keys are valid.

    Raises:
        ValueError: naming the first offending key (missing, empty, or placeholder).

    Rule: ZT-001 (fatal crash on invalid/missing key)
    """
    values = _parse_env_file(env_path)
    for key in REQUIRED_KEYS:
        if key not in values:
            raise ValueError(f"Missing required environment variable: {key}")
        value = values[key]
        if value == "":
            raise ValueError(f"Required environment variable is empty: {key}")
        if PLACEHOLDER_RE.search(value):
            raise ValueError(f"Required environment variable still has a placeholder value: {key}")
    return True


def scan_for_secrets(file_paths) -> list:
    """
    Scan each given file for secret patterns from RULES.md SEC-X-003.

    Args:
        file_paths: Iterable of file paths (str or Path) to scan.

    Returns:
        List of {"file", "pattern", "line_number"} dicts — empty if clean.

    Rule: SEC-X-003 (pre-commit secret scan)
    """
    findings = []
    for raw_path in file_paths:
        path = Path(raw_path)
        if path.resolve() in SELF_EXCLUDED_FILES or not path.is_file():
            continue
        for line_number, line in enumerate(path.read_text(errors="ignore").splitlines(), start=1):
            for pattern in SECRET_PATTERNS:
                matched = pattern.search(line) if isinstance(pattern, re.Pattern) else pattern in line
                if matched:
                    label = pattern.pattern if isinstance(pattern, re.Pattern) else pattern
                    findings.append({"file": str(raw_path), "pattern": label, "line_number": line_number})
    return findings


if __name__ == "__main__":
    try:
        validate_env()
        print("Environment OK — all required variables present and valid.")
        sys.exit(0)
    except (ValueError, FileNotFoundError) as exc:
        print(f"Environment validation failed: {exc}")
        sys.exit(1)
