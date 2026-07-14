import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


_CONFIG_PATH = Path(__file__).parent / "config.toml"

APP_NAME = "gex_app"
CLIENT_ID = ""
CLIENT_SECRET = ""
CALLBACK_URL = "https://127.0.0.1:8182/"
TOKEN_PATH = os.path.expanduser("~/.local/share/gex_app/schwab_token.json")
BASE_URL = "https://api.schwabapi.com"
MAX_TOKEN_AGE = 7 * 24 * 3600

if _CONFIG_PATH.exists():
    with open(_CONFIG_PATH, "rb") as f:
        cfg = tomllib.load(f).get("schwab", {})
    CLIENT_ID = cfg.get("client_id", CLIENT_ID)
    CLIENT_SECRET = cfg.get("client_secret", CLIENT_SECRET)
    CALLBACK_URL = cfg.get("callback_url", CALLBACK_URL)
    TOKEN_PATH = os.path.expanduser(cfg.get("token_file", TOKEN_PATH))
    BASE_URL = cfg.get("base_url", BASE_URL)
    if "max_token_age_days" in cfg:
        MAX_TOKEN_AGE = cfg["max_token_age_days"] * 24 * 3600

CLIENT_ID = os.environ.get("SCHWAB_CLIENT_ID", CLIENT_ID)
CLIENT_SECRET = os.environ.get("SCHWAB_CLIENT_SECRET", CLIENT_SECRET)

# Telegram bot config (loaded from [telegram] section of config.toml)
BOT_TOKEN = ""
CHAT_ID = ""
TELEGRAM_ENABLED = True

if _CONFIG_PATH.exists():
    with open(_CONFIG_PATH, "rb") as f:
        _tg = tomllib.load(f).get("telegram", {})
    BOT_TOKEN = _tg.get("BOT_TOKEN", BOT_TOKEN)
    CHAT_ID = str(_tg.get("CHAT_ID", CHAT_ID))
    TELEGRAM_ENABLED = bool(_tg.get("enabled", TELEGRAM_ENABLED))

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", BOT_TOKEN)
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", CHAT_ID)

DEFAULT_STRIKE_COUNT = 50
DEFAULT_EXPIRATION_WINDOW = 90


@dataclass
class AppConfig:
    theme: str = "light"
    min_open_interest: int = 0
    min_volume: int = 0
    show_calls: bool = True
    show_puts: bool = True
    show_net_gex: bool = True
    show_itm: bool = True
    show_otm: bool = True
    liquidity_filter: bool = False
    weekly_only: bool = False
    monthly_only: bool = False
    selected_expirations: list[str] = field(default_factory=list)
    selection_mode: str = "all"
