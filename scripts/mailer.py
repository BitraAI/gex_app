"""Password-reset email delivery over SMTP.

Settings come from ``[email]`` in config.toml (see scripts/config.py):
``smtp_host``/``smtp_port``/``smtp_user``/``smtp_password``/``from_addr`` and
``use_ssl`` (auto-on for port 465). Without ``smtp_host`` nothing is sent —
the landing page then falls back to writing the reset link to the app log so
the operator can still finish a reset by hand.
"""
import logging
import smtplib
from email.message import EmailMessage
from email.utils import formatdate

from scripts import config

log = logging.getLogger("gex.mailer")


class MailError(Exception):
    """SMTP delivery failure with a user-presentable message."""


def smtp_configured() -> bool:
    return bool(config.SMTP_HOST)


def reset_link(token: str) -> str:
    """Full URL the user opens to reach the app and reset the password."""
    return f"{config.RESET_LINK_BASE}/?reset={token}"


def _connect() -> smtplib.SMTP:
    if config.SMTP_USE_SSL:
        server = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=20)
    else:
        server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20)
    return server


def send_reset_email(to_email: str, reset_link_url: str) -> None:
    """Send the password-reset email; raise MailError on any failure."""
    if not smtp_configured():
        raise MailError("Email delivery is not configured ([email] in config.toml)")

    msg = EmailMessage()
    msg["From"] = config.SMTP_FROM
    msg["To"] = to_email
    msg["Date"] = formatdate(localtime=False)
    msg["Subject"] = "GammaEx password reset"
    msg.set_content(
        f"A password reset was requested for your GammaEx account.\n\n"
        f"Reset your password with this link (valid for 30 minutes):\n\n"
        f"{reset_link_url}\n\n"
        f"If you didn't request this, you can safely ignore the email — the\n"
        f"current password keeps working and the link expires on its own.\n"
    )

    try:
        with _connect() as server:
            server.ehlo()
            if not config.SMTP_USE_SSL and server.has_extn("starttls"):
                server.starttls()
                server.ehlo()
            if config.SMTP_USER:
                server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.send_message(msg)
    except (smtplib.SMTPException, OSError) as exc:
        log.error("SMTP send to %s failed: %s", to_email, exc)
        raise MailError(f"Couldn't reach the mail server: {exc}") from exc
