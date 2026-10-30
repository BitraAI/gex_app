import os
import tomllib
from pathlib import Path


_CONFIG_PATH = Path(__file__).parent.parent / ".streamlit" / "config.toml"   # .streamlit/ subfolder

CLIENT_ID = ""
CLIENT_SECRET = ""
CALLBACK_URL = "https://127.0.0.1:8182/"
TOKEN_PATH = os.path.expanduser("~/.local/share/gex_app/schwab_token.json")
MAX_TOKEN_AGE = 7 * 24 * 3600

BOT_TOKEN = ""
CHAT_ID = ""
TELEGRAM_ENABLED = True

# Email (magic-link login + approval delivery) — see [email] in config.toml.
SMTP_HOST = ""
SMTP_PORT = 587
SMTP_USER = ""
SMTP_PASSWORD = ""
SMTP_FROM = "gex_app@localhost"
SMTP_USE_SSL = False
SMTP_OPERATOR = ""  # who receives access requests; falls back to SMTP_FROM
LINK_BASE = "http://localhost:8501"

if _CONFIG_PATH.exists():
    with open(_CONFIG_PATH, "rb") as f:
        _raw = tomllib.load(f)

    _schwab = _raw.get("schwab", {})
    CLIENT_ID = _schwab.get("client_id", CLIENT_ID)
    CLIENT_SECRET = _schwab.get("client_secret", CLIENT_SECRET)
    CALLBACK_URL = _schwab.get("callback_url", CALLBACK_URL)
    TOKEN_PATH = os.path.expanduser(_schwab.get("token_file", TOKEN_PATH))
    if "max_token_age_days" in _schwab:
        MAX_TOKEN_AGE = _schwab["max_token_age_days"] * 24 * 3600

    _tg = _raw.get("telegram", {})
    BOT_TOKEN = _tg.get("BOT_TOKEN", BOT_TOKEN)
    CHAT_ID = str(_tg.get("CHAT_ID", CHAT_ID))
    TELEGRAM_ENABLED = bool(_tg.get("enabled", TELEGRAM_ENABLED))

    # Email (magic-link login + approval delivery). Everything optional:
    # without an smtp_host the app falls back to logging links in the app
    # log. Access requests go to operator_addr (default: from_addr).
    _email = _raw.get("email", {})
    SMTP_HOST = str(_email.get("smtp_host", ""))
    SMTP_PORT = int(_email.get("smtp_port", 587))
    SMTP_USER = _email.get("smtp_user", "")
    SMTP_PASSWORD = _email.get("smtp_password", "")
    SMTP_FROM = str(_email.get("from_addr", SMTP_USER or "gex_app@localhost"))
    SMTP_USE_SSL = bool(_email.get("use_ssl", SMTP_PORT == 465))
    SMTP_OPERATOR = str(_email.get("operator_addr", ""))
    LINK_BASE = str(_email.get("link_base", "http://localhost:8501")).rstrip("/")

# Environment overrides work whether or not config.toml exists.
SMTP_USER = os.environ.get("GEX_SMTP_USER", SMTP_USER)
SMTP_PASSWORD = os.environ.get("GEX_SMTP_PASSWORD", SMTP_PASSWORD)

CLIENT_ID = os.environ.get("SCHWAB_CLIENT_ID", CLIENT_ID)
CLIENT_SECRET = os.environ.get("SCHWAB_CLIENT_SECRET", CLIENT_SECRET)
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", BOT_TOKEN)
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", CHAT_ID)


def validate_config() -> list[str]:
    """Return a list of human-readable error strings for any missing required
    configuration.  An empty list means everything is healthy.

    Never raises — used by the Streamlit app at startup so a misconfigured
    environment shows a clear setup page instead of a cryptic traceback when
    the user clicks Refresh.
    """
    errors: list[str] = []
    if not CLIENT_ID:
        errors.append(
            "[schwab] client_id missing — set it in config.toml or via the "
            "SCHWAB_CLIENT_ID environment variable."
        )
    if not CLIENT_SECRET:
        errors.append(
            "[schwab] client_secret missing — set it in config.toml or via the "
            "SCHWAB_CLIENT_SECRET environment variable."
        )
    if TELEGRAM_ENABLED:
        if not BOT_TOKEN:
            errors.append(
                "[telegram] BOT_TOKEN missing — set it in config.toml or via the "
                "TELEGRAM_BOT_TOKEN environment variable."
            )
        if not CHAT_ID:
            errors.append(
                "[telegram] CHAT_ID missing — set it in config.toml or via the "
                "TELEGRAM_CHAT_ID environment variable."
            )
    return errors

