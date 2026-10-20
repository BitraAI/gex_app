"""Password-reset / notification email delivery over SMTP.

Settings come from the ``[email]`` section of ``config.toml`` (parsed by
``scripts/config.py``): ``smtp_host``/``smtp_port``/``smtp_user``/
``smtp_password``/``from_addr``/``use_ssl`` (auto-on for port 465) and
``link_base``.  ``scripts/config.py`` also applies ``GEX_SMTP_USER`` /
``GEX_SMTP_PASSWORD`` environment overrides on top of the file values.

Without ``smtp_host`` nothing is sent — sends raise ``EmailConfigError`` so
callers can fall back to logging the message (mirroring ``mailer.py``).
"""
import ssl
import smtplib

from email.message import EmailMessage
from email.utils import formatdate

try:
    from scripts import config  # normal repo layout (scripts package)
except ImportError:  # installed standalone as top-level `email_service`
    import config


class EmailConfigError(Exception):
    """SMTP delivery is not configured ([email] in config.toml)."""


class EmailSendError(Exception):
    """SMTP delivery failure with a user-presentable message."""


def smtp_configured() -> bool:
    return bool(config.SMTP_HOST)


def _credentials() -> tuple[str, str]:
    user = config.SMTP_USER
    password = config.SMTP_PASSWORD
    if not user or not password:
        raise EmailConfigError(
            "smtp_user / smtp_password are missing from the [email] section "
            "of config.toml (or the GEX_SMTP_USER / GEX_SMTP_PASSWORD env vars)"
        )
    return user, password


def send_email(to_email: str, subject: str, body: str) -> None:
    """Send a plain-text email through authenticated SMTP.

    Retransient SMTP drops (Gmail briefly jails IPs / closes connections,
    e.g. right after bursts of auth attempts) are retried twice with a short
    backoff before the error surfaces as ``EmailSendError``.
    """
    import time

    if not smtp_configured():
        raise EmailConfigError(
            "Email delivery is not configured ([email] section in config.toml)"
        )

    smtp_user, smtp_password = _credentials()

    message = EmailMessage()
    message["From"] = config.SMTP_FROM or smtp_user
    message["To"] = to_email
    message["Date"] = formatdate(localtime=False)
    message["Subject"] = subject
    message.set_content(body)

    _RETRYABLE = (smtplib.SMTPServerDisconnected, ConnectionError, BrokenPipeError, TimeoutError)

    last_exc = None
    for attempt in range(3):
        try:
            with _connect() as server:
                server.ehlo()
                if not config.SMTP_USE_SSL and server.has_extn("starttls"):
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                server.login(smtp_user, smtp_password)
                server.send_message(message)
            return  # delivered
        except EmailConfigError:
            raise
        except smtplib.SMTPResponseException as exc:
            # Rejected by policy — retrying won't help.
            raise _map_send_error(exc) from exc
        except _RETRYABLE as exc:
            last_exc = exc
            if attempt < 2:
                time.sleep(1 + attempt)  # 1s, then 2s
                continue
        except smtplib.SMTPException as exc:
            raise _map_send_error(exc) from exc
        except OSError as exc:
            raise _map_send_error(exc) from exc

    raise _map_send_error(last_exc)


def _map_send_error(exc: Exception) -> EmailSendError:
    """Translate a final SMTP failure into a user-presentable message."""
    if isinstance(exc, smtplib.SMTPResponseException):
        if getattr(exc, "smtp_code", 0) in (534, 535) and "password" in str(exc.smtp_error).lower():
            return EmailSendError(
                f"SMTP rejected auth: {exc.smtp_error} — Google/Gmail rejects"
                " account passwords for SMTP: create a 16-character App"
                " Password (myaccount.google.com → Security → 2-Step"
                " Verification → App passwords) and put it in smtp_password"
                " in config.toml"
            )
        return EmailSendError(f"SMTP rejected auth: {exc.smtp_error}")
    if isinstance(exc, smtplib.SMTPServerDisconnected):
        return EmailSendError(
            f"{exc} — server closed the connection; if the attempt followed"
            " rebuffs of send bursts this is usually transient Google"
            " throttling (sends are retried automatically), or it can also"
            " be an auth rejection"
        )
    if isinstance(exc, OSError):
        return EmailSendError(f"Couldn't reach the mail server: {exc}")
    return EmailSendError(f"SMTP delivery failed: {exc}")


def _connect() -> smtplib.SMTP:
    if config.SMTP_USE_SSL:
        server = smtplib.SMTP_SSL(
            config.SMTP_HOST, config.SMTP_PORT, timeout=20,
            context=ssl.create_default_context(),
        )
    else:
        server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20)
    return server


def send_password_reset_email(
    to_email: str, reset_url: str | None = None, token: str | None = None
) -> None:
    """Send a password-reset link to the account owner.

    Pass either the full ``reset_url`` or just the ``token`` (in which case
    the URL is built from ``link_base`` in config.toml, same as mailer.py).
    """
    if reset_url is None:
        if token is None:
            raise ValueError("send_password_reset_email needs reset_url or token")
        try:
            from scripts.mailer import reset_link
        except ImportError:
            from mailer import reset_link

        reset_url = reset_link(token)

    subject = "Reset your password"

    body = (
        "We received a request to reset your password.\n\n"
        f"Reset your password using this link:\n{reset_url}\n\n"
        "If you did not request this, you can ignore this email.\n"
        "If the link has expired, request a new one."
    )

    send_email(to_email, subject, body)
