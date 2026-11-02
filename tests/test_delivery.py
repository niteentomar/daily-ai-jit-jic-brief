"""
MODULE: test_delivery.py
PURPOSE: Test cases for core/delivery.py — SendGrid email delivery with R-006 retry logic
INPUTS: pytest fixtures (mocker, monkeypatch, caplog)
OUTPUTS: Pass/fail assertions per TEST_REGISTRY T-DEL-* acceptance criteria
DEPENDENCIES: pytest, pytest-mock, core.delivery
RULE REFERENCES: R-006 (retry SendGrid 3x exponential backoff; CRITICAL + False on exhaustion)
CHANGE LOG: 1.0.0 | 2026-06-17 | TC-006 initial tests (red phase) | Claude Code
             1.1.0 | 2026-06-22 | CL-027 bugfix: send_email() was using
             TARGET_EMAIL (the recipient) as the sender too. _set_env() now
             also sets EMAIL_FROM (distinct from TARGET_EMAIL, to prove the
             two are no longer conflated); T-DEL-C-001 asserts the Mail
             object's from_email matches EMAIL_FROM, not TARGET_EMAIL | Claude Code
             1.2.0 | 2026-06-24 | CL-044 added T-DEL-C-002 (send_email()
             uses a passed subject= kwarg), T-DEL-C-003 (falls back to the
             default _SUBJECT when omitted, regression guard) — Issue C,
             found independently while investigating Niteen's report of a
             generic "topic" field in JIT/JIC email rows (the actual bug,
             fixed in main.py's prompts); _SUBJECT had been a hardcoded
             constant with no way to vary it since TC-006 | Claude Code
"""
import pytest

from core.delivery import send_email


def _set_env(monkeypatch) -> None:
    """Inject required delivery env vars for each test."""
    monkeypatch.setenv("SENDGRID_API_KEY", "SG.test-key-0000")
    monkeypatch.setenv("TARGET_EMAIL", "test@example.com")
    monkeypatch.setenv("EMAIL_FROM", "sender@example.com")


# ── T-DEL-C-001 ──────────────────────────────────────────────────────────────

def test_t_del_c_001_sendgrid_send_success(mocker, monkeypatch):
    """
    T-DEL-C-001: send_email() returns True when SendGrid responds with 202.

    Acceptance criteria (TEST_REGISTRY):
      delivery.send_email() returns True; no exception raised.
    """
    _set_env(monkeypatch)

    mock_response = mocker.MagicMock()
    mock_response.status_code = 202

    mock_client = mocker.MagicMock()
    mock_client.send.return_value = mock_response

    mocker.patch("core.delivery.SendGridAPIClient", return_value=mock_client)

    result = send_email(html="<html><body>Test email</body></html>", to="test@example.com")

    assert result is True
    mock_client.send.assert_called_once()

    sent_message = mock_client.send.call_args.args[0]
    assert sent_message.from_email.email == "sender@example.com", (
        "from_email must come from EMAIL_FROM, not TARGET_EMAIL (CL-027 bugfix — "
        f"got: {sent_message.from_email.email!r}"
    )


# ── T-DEL-E-001 ──────────────────────────────────────────────────────────────

def test_t_del_e_001_all_retries_exhausted_returns_false(mocker, monkeypatch, caplog):
    """
    T-DEL-E-001: send_email() returns False and logs CRITICAL when all 3 retries fail.

    Acceptance criteria (TEST_REGISTRY):
      SendGrid raises 3 times; function returns False; CRITICAL log emitted.
      No fallback provider — False is the terminal outcome.

    Strategy: patch _send_with_retry (tenacity-wrapped inner function) to raise
    immediately, representing exhaustion after 3 attempts without incurring
    actual exponential backoff delays in the test suite.
    """
    _set_env(monkeypatch)

    mocker.patch(
        "core.delivery._send_with_retry",
        side_effect=Exception("SendGrid unavailable — all retries exhausted"),
    )

    with caplog.at_level("CRITICAL"):
        result = send_email(html="<html><body>Test email</body></html>", to="test@example.com")

    assert result is False
    assert any(record.levelname == "CRITICAL" for record in caplog.records)


# ── T-DEL-C-002 ──────────────────────────────────────────────────────────────

def test_t_del_c_002_send_email_uses_passed_subject(mocker, monkeypatch):
    """
    T-DEL-C-002: send_email() uses a passed subject= kwarg in the Mail
    object (CL-044, Issue C).
    """
    _set_env(monkeypatch)

    mock_response = mocker.MagicMock()
    mock_response.status_code = 202
    mock_client = mocker.MagicMock()
    mock_client.send.return_value = mock_response
    mocker.patch("core.delivery.SendGridAPIClient", return_value=mock_client)

    send_email(
        html="<html><body>Test email</body></html>",
        to="test@example.com",
        subject="Custom Subject",
    )

    sent_message = mock_client.send.call_args.args[0]
    assert sent_message.subject.subject == "Custom Subject", (
        f"Expected the passed subject, got: {sent_message.subject.subject!r}"
    )


# ── T-DEL-C-003 ──────────────────────────────────────────────────────────────

def test_t_del_c_003_send_email_defaults_to_generic_subject(mocker, monkeypatch):
    """
    T-DEL-C-003: send_email() falls back to the default "Your Daily AI
    Learning Brief" subject when no subject kwarg is passed — regression
    guard confirming the default preserves current behavior for any caller
    that omits it (CL-044, Issue C).
    """
    _set_env(monkeypatch)

    mock_response = mocker.MagicMock()
    mock_response.status_code = 202
    mock_client = mocker.MagicMock()
    mock_client.send.return_value = mock_response
    mocker.patch("core.delivery.SendGridAPIClient", return_value=mock_client)

    send_email(html="<html><body>Test email</body></html>", to="test@example.com")

    sent_message = mock_client.send.call_args.args[0]
    assert sent_message.subject.subject == "Your Daily AI Learning Brief", (
        f"Expected the default subject, got: {sent_message.subject.subject!r}"
    )


# ── T-DEL-N-010 (CL-063) ─────────────────────────────────────────────────────

def test_t_del_n_010_retry_only_429_5xx_and_network():
    """T-DEL-N-010 (API audit s.4): 4xx fail fast; 429, 5xx and network errors are retried."""
    from types import SimpleNamespace
    from core.delivery import _is_retryable
    assert _is_retryable(SimpleNamespace(status_code=429)) is True
    assert _is_retryable(SimpleNamespace(status_code=503)) is True
    assert _is_retryable(SimpleNamespace(status_code=401)) is False
    assert _is_retryable(SimpleNamespace(status_code=400)) is False
    assert _is_retryable(ConnectionError("down")) is True
