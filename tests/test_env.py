"""
MODULE: test_env.py
PURPOSE: Test cases for scripts/check_env.py environment variable validation
INPUTS: pytest tmp_path fixture for isolated, disposable .env files
OUTPUTS: Pass/fail assertions per TEST_REGISTRY T-ENV-* acceptance criteria
DEPENDENCIES: pytest, scripts.check_env
RULE REFERENCES: ZT-001, SEC-X-001, TST-T-002
CHANGE LOG: 1.0.0 | 2026-06-16 | TC-001 initial tests (T-ENV-C-001, E-001, N-001, N-002) | Claude Code
             1.1.0 | 2026-06-17 | TC-010 fixture updated: removed LITELLM_MASTER_KEY,
             LITELLM_PORT (vestigial), GMAIL_APP_PASSWORD, GMAIL_SENDER (dropped TC-006);
             added SENDGRID_API_KEY (promoted to required); T-ENV-E-001 target key updated
             from GMAIL_SENDER to SENDGRID_API_KEY | Claude Code
             1.2.0 | 2026-06-17 | Bugfix: added LITELLM_MODEL_1 to VALID_DEFAULTS —
             promoted to REQUIRED_KEYS now that the failover chain is env-var driven | Claude Code
             1.3.0 | 2026-06-21 | CL-024 added T-ENV-E-002 (validate_env() works
             from any cwd) — launchd_stderr.log showed 3 identical
             FileNotFoundError('.env') crashes because the default env_path was
             resolved relative to the process cwd, not the project root | Claude Code
             1.4.0 | 2026-06-22 | CL-027 added EMAIL_FROM to VALID_DEFAULTS —
             promoted to REQUIRED_KEYS so core/delivery.py's sender address is
             validated at startup, decoupled from TARGET_EMAIL (the recipient) | Claude Code
             1.5.0 | 2026-06-22 | CL-033: GOOGLE_API_KEY retired, replaced by
             GEMINI_API_KEY in VALID_DEFAULTS and REQUIRED_KEYS. T-ENV-N-001's
             placeholder target updated to GEMINI_API_KEY (testing a retired,
             no-longer-required key's placeholder would not raise). Added
             T-ENV-N-003 (GEMINI_API_KEY missing raises ValueError naming it) | Claude Code
             1.6.0 | 2026-06-22 | CL-041 added GOOGLE_APPLICATION_CREDENTIALS to
             VALID_DEFAULTS/REQUIRED_KEYS — MODEL_1/2 migrated from gemini/
             (GEMINI_API_KEY, AI Studio free quota) to vertex_ai/ (Vertex AI,
             $300 GCP credit), which authenticates via a service-account JSON
             file path in this env var rather than an API key string.
             GEMINI_API_KEY stays required as a fallback. Added T-ENV-N-004
             (missing GOOGLE_APPLICATION_CREDENTIALS raises ValueError naming
             it), T-ENV-C-002 (present and non-empty passes) | Claude Code
             1.7.0 | 2026-06-25 | CL-051: GEMINI_API_KEY removed from
             VALID_DEFAULTS and REQUIRED_KEYS — MODEL_1/2 migrated to vertex_ai/,
             which needs only GOOGLE_APPLICATION_CREDENTIALS. GEMINI_API_KEY
             is now OPTIONAL. Updated T-ENV-N-003 to confirm absence does NOT
             raise. Added T-ENV-N-005 (validate_env passes without GEMINI_API_KEY).
             Updated LITELLM_MODEL_1 in VALID_DEFAULTS to vertex_ai/ prefix | Claude Code
"""
import pytest

from scripts import check_env

VALID_DEFAULTS = {
    "LANGCHAIN_API_KEY": "lsv2_test_key_0000",
    "LANGCHAIN_TRACING_V2": "true",
    "LANGCHAIN_PROJECT": "daily-jit-jic-newsletter",
    "TAVILY_API_KEY": "tvly-test-key-0000",
    "SENDGRID_API_KEY": "SG.fake_valid_key_123",
    "TARGET_EMAIL": "you@example.com",
    "EMAIL_FROM": "you@example.com",
    "DAILY_TOKEN_LIMIT_GEMINI": "900000",
    "TOKEN_ALERT_THRESHOLD": "0.95",
    "LITELLM_MODEL_1": "vertex_ai/gemini-2.5-flash-lite",
    "GOOGLE_APPLICATION_CREDENTIALS": "/Users/test/.config/gcp/test-sa.json",
}


def _write_env(path, overrides=None, omit=None):
    """Write a temp .env file with valid defaults, applying overrides/omissions."""
    values = dict(VALID_DEFAULTS)
    if overrides:
        values.update(overrides)
    if omit:
        for key in omit:
            values.pop(key, None)
    path.write_text("\n".join(f"{k}={v}" for k, v in values.items()) + "\n")
    return path


def test_t_env_c_001_valid_env_loads_successfully(tmp_path):
    """T-ENV-C-001: all required vars present & non-placeholder -> validate_env returns True."""
    env_file = _write_env(tmp_path / ".env")
    assert check_env.validate_env(str(env_file)) is True


def test_t_env_n_001_placeholder_value_rejected(tmp_path):
    """T-ENV-N-001: a *_here placeholder value raises ValueError naming the key."""
    env_file = _write_env(tmp_path / ".env", overrides={"TAVILY_API_KEY": "your_tavily_api_key_here"})
    with pytest.raises(ValueError, match="TAVILY_API_KEY"):
        check_env.validate_env(str(env_file))


def test_t_env_n_002_missing_required_key_raises(tmp_path):
    """T-ENV-N-002: a required key entirely absent from .env raises ValueError naming it."""
    env_file = _write_env(tmp_path / ".env", omit=["TAVILY_API_KEY"])
    with pytest.raises(ValueError, match="TAVILY_API_KEY"):
        check_env.validate_env(str(env_file))


def test_t_env_e_001_empty_string_value_treated_as_invalid(tmp_path):
    """T-ENV-E-001 (edge): a required key present but set to an empty string is
    rejected via the same code path as a missing key."""
    env_file = _write_env(tmp_path / ".env", overrides={"SENDGRID_API_KEY": ""})
    with pytest.raises(ValueError, match="SENDGRID_API_KEY"):
        check_env.validate_env(str(env_file))


def test_t_env_e_002_validate_env_works_from_any_cwd(tmp_path, monkeypatch):
    """
    T-ENV-E-002: validate_env() succeeds (path-resolution-wise) even when the
    process cwd is not the project root.

    launchd starts the pipeline with a cwd that is not the project root, so
    the old default env_path=".env" resolved relative to cwd and raised
    FileNotFoundError before any key validation ran. This test changes cwd to
    an empty tmp_path with no .env file and calls validate_env() with no
    arguments (default path) — a ValueError for missing keys is acceptable
    (proves path resolution reached the project root's real .env); a
    FileNotFoundError means the bug is still present.
    """
    monkeypatch.chdir(tmp_path)

    try:
        check_env.validate_env()
    except FileNotFoundError:
        pytest.fail("validate_env() raised FileNotFoundError — default env_path is cwd-relative")
    except ValueError:
        pass  # acceptable — proves the .env file was found and parsed


def test_t_env_n_003_gemini_api_key_is_now_optional(tmp_path):
    """
    T-ENV-N-003: GEMINI_API_KEY absent from .env does NOT raise ValueError
    (CL-051 — MODEL_1/2 migrated from gemini/ to vertex_ai/; GEMINI_API_KEY
    downgraded from REQUIRED to OPTIONAL. vertex_ai/ authenticates via
    GOOGLE_APPLICATION_CREDENTIALS/ADC — no API key string needed for
    primary models. GEMINI_API_KEY kept as optional fallback per DEV-I-006).
    """
    env_file = _write_env(tmp_path / ".env")
    # VALID_DEFAULTS already excludes GEMINI_API_KEY — this confirms full
    # validate_env() passes without it
    assert check_env.validate_env(str(env_file)) is True


def test_t_env_n_004_google_application_credentials_required(tmp_path):
    """
    T-ENV-N-004: GOOGLE_APPLICATION_CREDENTIALS missing from .env raises
    ValueError naming it (CL-041 — MODEL_1/2 migrated to vertex_ai/, which
    authenticates via this env var pointing to a service-account JSON file,
    not an API key string).
    """
    env_file = _write_env(tmp_path / ".env", omit=["GOOGLE_APPLICATION_CREDENTIALS"])
    with pytest.raises(ValueError, match="GOOGLE_APPLICATION_CREDENTIALS"):
        check_env.validate_env(str(env_file))


def test_t_env_c_002_google_application_credentials_present_passes(tmp_path):
    """
    T-ENV-C-002: validate_env() passes when GOOGLE_APPLICATION_CREDENTIALS is
    set to a non-empty string (file-existence check is out of scope here —
    validate_env() only checks presence/non-empty/non-placeholder, same as
    every other required key).
    """
    env_file = _write_env(tmp_path / ".env")
    assert check_env.validate_env(str(env_file)) is True


# ── T-ENV-N-005 ───────────────────────────────────────────────────────────────

def test_t_env_n_005_gemini_api_key_in_optional_keys(tmp_path):
    """
    T-ENV-N-005: GEMINI_API_KEY is listed in check_env.OPTIONAL_KEYS (not
    REQUIRED_KEYS) after CL-051 — confirms the env var's classification was
    correctly updated when MODEL_1/2 moved from gemini/ to vertex_ai/ prefix.

    Regression guard: if someone accidentally moves GEMINI_API_KEY back into
    REQUIRED_KEYS, this test catches the mistake before the change ships.
    """
    from scripts.check_env import OPTIONAL_KEYS, REQUIRED_KEYS

    assert "GEMINI_API_KEY" not in REQUIRED_KEYS, (
        "GEMINI_API_KEY must NOT be required after CL-051 Vertex-only migration"
    )
    assert "GEMINI_API_KEY" in OPTIONAL_KEYS, (
        "GEMINI_API_KEY must be OPTIONAL (DEV-I-006 fallback for gemini/ prefix)"
    )
