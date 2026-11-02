"""
MODULE: delivery.py
PURPOSE: Send HTML email via SendGrid with R-006 retry logic (no fallback provider)
INPUTS: html (str) — rendered email body; to (str) — recipient address
OUTPUTS: bool — True on success, False after all retries exhausted
DEPENDENCIES: sendgrid, tenacity
RULE REFERENCES: R-006 (retry SendGrid 3x exponential backoff; CRITICAL + False on exhaustion)
                 ZT-001 (SENDGRID_API_KEY from env only), ZT-003 (SendGrid domain only)
CHANGE LOG: 1.0.0 | 2026-06-17 | TC-006 initial implementation | Claude Code
            1.1.0 | 2026-06-22 | CL-027 bugfix: sender used TARGET_EMAIL — the
            recipient address (set by main.py) was also being used as the
            from_email, so every email sent from-and-to the same address.
            Introduced a dedicated EMAIL_FROM env var, validated as required
            in scripts/check_env.py so a missing sender fails fast at startup
            rather than silently at send time. GMAIL_SENDER was considered but
            rejected — it was deliberately removed from check_env.py's
            REQUIRED_KEYS in CL-013 (Gmail dropped in TC-006) and would have
            revived an unvalidated, deprecated env var | Claude Code
            1.2.0 | 2026-06-24 | CL-044 added an optional subject parameter
            (default = _SUBJECT, so every existing caller is unaffected) —
            _SUBJECT had been a hardcoded constant with no way to vary it
            since TC-006, meaning every delivered email had an identical
            generic subject regardless of the day's topic. main.py now
            passes a subject built from the day's real lesson_topic | Claude Code
            2.0.0 | 2026-11-01 | CL-063: retry only 429/5xx/network (tenacity
            retry_if_exception); 4xx fail fast | Claude Code
"""
import logging
import os

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

_SUBJECT = "Your Daily AI Learning Brief"


def _is_retryable(exc: Exception) -> bool:
    """
    CL-063: retry only rate limits, server errors and network failures.
    4xx errors (400 payload, 401/403 key or sender, 413 size) will not succeed on
    retry, so they fail fast (API audit section 4).
    """
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if isinstance(status, int):
        return status == 429 or status >= 500
    return True  # network / unknown errors


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception(_is_retryable),
    reraise=True,
)
def _send_with_retry(client: SendGridAPIClient, message: Mail) -> object:
    """
    Send a SendGrid Mail object; tenacity retries up to 3 times on any exception.

    Args:
        client: Authenticated SendGridAPIClient instance.
        message: Populated Mail object.

    Returns:
        SendGrid response object on success.

    Raises:
        Exception: Re-raised by tenacity after the 3rd failed attempt (R-006).
    """
    return client.send(message)


def send_email(html: str, to: str, subject: str = _SUBJECT) -> bool:
    """
    Send an HTML email to `to` via SendGrid.

    Retries the SendGrid call up to 3 times with exponential backoff (R-006).
    Logs CRITICAL and returns False if all attempts fail — there is no fallback
    provider. Credentials are read exclusively from env (ZT-001):
      SENDGRID_API_KEY — SendGrid API key
      EMAIL_FROM       — used as the sender address

    Args:
        html:    Full HTML body string (pre-validated by synthesis.py).
        to:      Recipient email address.
        subject: Email subject line. Defaults to the generic _SUBJECT
                 constant; callers should pass a topic-specific subject.

    Returns:
        True on a successful SendGrid 2xx response, False on exhaustion.
    """
    api_key = os.getenv("SENDGRID_API_KEY", "")
    sender = os.getenv("EMAIL_FROM", "")

    message = Mail(
        from_email=sender,
        to_emails=to,
        subject=subject,
        html_content=html,
    )
    client = SendGridAPIClient(api_key=api_key)

    try:
        response = _send_with_retry(client, message)
        logger.info(f"Email sent to {to} — SendGrid status {response.status_code}")
        return True
    except Exception as exc:
        logger.critical(
            f"R-006: SendGrid failed after 3 attempts — email not delivered. Error: {exc}"
        )
        return False
