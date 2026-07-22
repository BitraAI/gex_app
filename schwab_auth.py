#!/usr/bin/env python3
import os
import sys

from schwab import auth

from config import CALLBACK_URL, CLIENT_ID, CLIENT_SECRET, MAX_TOKEN_AGE, TOKEN_PATH


def _verify_token(path: str) -> bool:
    import json
    from datetime import datetime, timezone
    try:
        with open(path) as f:
            token = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
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
        print("Token expired (refresh token >7 days old).", file=__import__("sys").stderr)
        return False

    # Access token expired → still ok (library auto-refreshes)
    ei = raw.get("expires_in")
    if ei is not None and now > ct + ei:
        print("Access token expired; refresh will occur on next API call.", file=__import__("sys").stderr)

    return True


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: client_id and client_secret not found in config.toml or SCHWAB_CLIENT_ID/SCHWAB_CLIENT_SECRET env vars.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)

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
