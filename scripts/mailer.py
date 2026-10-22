"""Magic-link login and approval email delivery over SMTP.

Settings come from ``[email]`` in config.toml (see scripts/config.py):
``smtp_host``/``smtp_port``/``smtp_user``/``smtp_password``/``from_addr`` and
``use_ssl`` (auto-on for port 465). Without ``smtp_host`` nothing is sent —
the landing page then falls back to writing the links to the app log so the
operator can still hand them out by hand.
"""
import logging
import smtplib
from email.message import EmailMessage
from email.utils import formatdate
from html import escape

from scripts import config

log = logging.getLogger("gex.mailer")


class MailError(Exception):
    """SMTP delivery failure with a user-presentable message."""


def smtp_configured() -> bool:
    return bool(config.SMTP_HOST)


def magic_link(token: str) -> str:
    """Full URL the user opens to reach the app and log in."""
    return f"{config.LINK_BASE}/?login={token}"


def approve_link(token: str) -> str:
    """Full URL the administrator opens to approve an access request."""
    return f"{config.LINK_BASE}/?approve={token}"


def _connect() -> smtplib.SMTP:
    if config.SMTP_USE_SSL:
        server = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=20)
    else:
        server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20)
    return server


def _send_email(to_email: str, subject: str, body: str,
                html_body: str | None = None) -> None:
    """Send one email (text, plus optional HTML part); raise MailError.

    Transient SMTP drops (Gmail occasionally severs connections after bursts
    of auth attempts) are retried once after a short pause before the error
    surfaces.
    """
    import time

    if not smtp_configured():
        raise MailError("Email delivery is not configured ([email] in config.toml)")

    msg = EmailMessage()
    msg["From"] = config.SMTP_FROM
    msg["To"] = to_email
    msg["Date"] = formatdate(localtime=False)
    msg["Subject"] = subject
    msg.set_content(body)
    if html_body is not None:
        msg.add_alternative(html_body, subtype="html")

    retryable = (
        smtplib.SMTPServerDisconnected, ConnectionError,
        BrokenPipeError, TimeoutError,
    )
    last_exc: Exception | None = None
    for attempt in range(2):
        try:
            with _connect() as server:
                server.ehlo()
                if not config.SMTP_USE_SSL and server.has_extn("starttls"):
                    server.starttls()
                    server.ehlo()
                if config.SMTP_USER:
                    server.login(config.SMTP_USER, config.SMTP_PASSWORD)
                server.send_message(msg)
            return
        except retryable as exc:
            last_exc = exc
            if attempt == 0:
                time.sleep(2)
            continue
        except smtplib.SMTPResponseException as exc:
            log.error("SMTP send to %s rejected: %s %s", to_email, exc.smtp_code, exc.smtp_error)
            raise MailError(f"SMTP rejected auth: {exc.smtp_error}") from exc
        except (smtplib.SMTPException, OSError) as exc:
            log.error("SMTP send to %s failed: %s", to_email, exc)
            raise MailError(f"Couldn't reach the mail server: {exc}") from exc

    log.error("SMTP send to %s failed after retry: %s", to_email, last_exc)
    raise MailError(f"Couldn't reach the mail server: {last_exc}") from last_exc


def send_magic_link(to_email: str, login_link_url: str) -> None:
    """Email a one-time magic link; raise MailError on any failure.

    Format follows the "Your login request to <app>" pattern: one headline,
    an expiry line, a prominently styled Log in button, and a plain link
    fallback. The text part mirrors it for non-HTML clients.
    """
    _send_email(
        to_email,
        "Your login request to GammaEx",
        "Your login request to GammaEx\n\n"
        "Click the link below to log into GammaEx. Your link expires in 30 "
        "minutes.\n\n"
        f"Log in: {login_link_url}\n\n"
        "If you're having trouble with the link above, copy it into your "
        "browser.\n",
        _login_email_html(login_link_url),
    )


def _login_email_html(login_link_url: str) -> str:
    """Card-style HTML layout for the magic-link email (Groq-style)."""
    return f"""
<div style="margin:0 auto;padding:24px 16px;max-width:560px;background:#ffffff;
            font-family:Helvetica,Arial,sans-serif;color:#040d14;">
  <h2 style="margin:0 0 16px;font-size:22px;font-weight:700;color:#040d14;">
    Your login request to GammaEx
  </h2>
  <p style="margin:0 0 24px;font-size:15px;line-height:1.6;color:#5e6a72;">
    Click the button below to log into GammaEx. Your link expires in 30
    minutes.
  </p>
  <a href="{login_link_url}"
     style="display:inline-block;padding:12px 34px;border-radius:999px;
            background:#00c805;color:#040d14;font-weight:700;
            font-size:16px;text-decoration:none;">
    Log in
  </a>
  <p style="margin:28px 0 0;font-size:14px;color:#5e6a72;">
    If you're having trouble with the button above, click
    <a href="{login_link_url}" style="color:#040d14;font-weight:600;">here</a>.
  </p>
</div>
"""


def send_approval_request(requester_email: str, approve_link_url: str) -> None:
    """Email the administrator about a first-time user asking for access.

    Opening the approval link creates the requester's account (with the
    requested email) and immediately emails them a one-time login link.
    Same card layout as the login email: an Approve button plus a plain
    "click here" fallback; the text part mirrors it for non-HTML clients.
    """
    to_email = config.SMTP_OPERATOR or config.SMTP_FROM
    _send_email(
        to_email,
        f"GammaEx access request: {requester_email}",
        f"GammaEx access request\n\n"
        f"A new visitor ({requester_email}) asked to use GammaEx but has no "
        "account yet.\n\n"
        "Click the link below to approve. Approving creates the account and "
        "immediately emails the requester a login link (the link expires in "
        "72 hours).\n\n"
        f"Approve: {approve_link_url}\n\n"
        "If you're having trouble with the link above, copy it into your "
        "browser.\n",
        _approval_email_html(requester_email, approve_link_url),
    )


def _approval_email_html(requester_email: str, approve_link_url: str) -> str:
    """Card-style HTML layout for the administrator approval email."""
    return f"""
<div style="margin:0 auto;padding:24px 16px;max-width:560px;background:#ffffff;
            font-family:Helvetica,Arial,sans-serif;color:#040d14;">
  <h2 style="margin:0 0 16px;font-size:22px;font-weight:700;color:#040d14;">
    GammaEx access request
  </h2>
  <p style="margin:0 0 24px;font-size:15px;line-height:1.6;color:#5e6a72;">
    A new visitor <b style="color:#040d14;">{escape(requester_email, quote=True)}</b> asked to use
    GammaEx but has no account yet. Click the button below to approve:
    approving creates the account and immediately emails the requester a
    login link. The link expires in 72 hours.
  </p>
  <a href="{approve_link_url}"
     style="display:inline-block;padding:12px 34px;border-radius:999px;
            background:#00c805;color:#040d14;font-weight:700;
            font-size:16px;text-decoration:none;">
    Approve
  </a>
  <p style="margin:28px 0 0;font-size:14px;color:#5e6a72;">
    If you're having trouble with the button above, click
    <a href="{approve_link_url}" style="color:#040d14;font-weight:600;">here</a>.
  </p>
</div>
"""
