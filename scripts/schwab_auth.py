#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timezone

from schwab import auth

# Allow running this file directly (python3 scripts/schwab_auth.py): put the
# repo root on sys.path so the scripts.* package imports resolve.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from scripts.config import CALLBACK_URL, CLIENT_ID, CLIENT_SECRET, MAX_TOKEN_AGE, TOKEN_PATH
from scripts._utils import load_json, ensure_dir


def _verify_token(path: str) -> bool:
    try:
        token = load_json(path)
        if token is None:
            return False
    except Exception:
        return False

    required_keys = {"access_token", "refresh_token"}
    raw = token.get("token", token)
    if not required_keys.issubset(raw.keys()):
        return False

    ct = token.get("creation_timestamp")
    if ct is None:
        return False

    now = datetime.now(timezone.utc).timestamp()

    # Refresh token expired → must re-auth
    if now > ct + MAX_TOKEN_AGE:
        print("Token expired (refresh token >7 days old).", file=sys.stderr)
        return False

    # Access token expired → still ok (library auto-refreshes)
    ei = raw.get("expires_in")
    if ei is not None and now > ct + ei:
        print("Access token expired; refresh will occur on next API call.", file=sys.stderr)

    return True


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: client_id and client_secret not found in config.toml or SCHWAB_CLIENT_ID/SCHWAB_CLIENT_SECRET env vars.", file=sys.stderr)
        sys.exit(1)

    ensure_dir(TOKEN_PATH)

    print("Opening browser for Schwab OAuth login...")
    print(f"Callback URL: {CALLBACK_URL}")
    print(f"Token will be saved to: {TOKEN_PATH}")

    auth.client_from_login_flow(
        CLIENT_ID,
        CLIENT_SECRET,
        CALLBACK_URL,
        TOKEN_PATH,
        asyncio=False,
        enforce_enums=True,
    )

    if _verify_token(TOKEN_PATH):
        print("Authentication successful!")
        print(f"Token saved to: {TOKEN_PATH}")
    else:
        print("Warning: Token file was not written or is invalid.", file=sys.stderr)
        print("Check that:")
        print(f"  1. Your callback URL in Schwab's developer portal matches: {CALLBACK_URL}")
        print("  2. Port 8182 is not in use by another process")
        print(f"  3. The directory {os.path.dirname(TOKEN_PATH)} is writable")
        sys.exit(1)


if __name__ == "__main__":
    main()
