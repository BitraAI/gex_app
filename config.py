import os
import tomllib
from pathlib import Path


_CONFIG_PATH = Path(__file__).parent / "config.toml"

CLIENT_ID = ""
CLIENT_SECRET = ""
CALLBACK_URL = "https://127.0.0.1:8182/"
TOKEN_PATH = os.path.expanduser("~/.local/share/gex_app/schwab_token.json")
MAX_TOKEN_AGE = 7 * 24 * 3600

BOT_TOKEN = ""
CHAT_ID = ""
TELEGRAM_ENABLED = True

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

