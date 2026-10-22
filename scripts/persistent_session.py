"""Browser-cookie persistent sessions for the gex_app dashboard.

Streamlit's ``st.session_state`` dies with the websocket connection, so a
page refresh, a brief disconnect, or a server restart used to send everyone
back to the landing page even though they had logged in minutes earlier.

This module layers a long-lived ``gex_session`` cookie on top:

* After a magic-link login a random bearer token is minted (kept only as a
  SHA-256 hash in the ``session_tokens`` table, see ``auth_db``), queued in
  ``st.session_state``, and written to the browser as a 30-day cookie the
  next time the dashboard renders. ``issue()`` / ``flush()`` do this.
* On every fresh browser session the cookie is read back with
  ``st.context.cookies`` and, if it still maps to a live DB session, the
  user is signed in again automatically. ``restore()`` does this.
* **Log out** revokes the DB token and clears the cookie. ``end()`` does
  this.

Streamlit has no native cookie setter, so the write happens through a
zero-height same-origin component running ``document.cookie`` (plain
JavaScript); reads need no workaround because ``st.context.cookies``
surfaces the request headers. The token never appears in URLs or logs —
only in the cookie and its hash in the database.
"""
import json

import streamlit as st
import streamlit.components.v1 as components

from scripts import auth_db

COOKIE_NAME = "gex_session"
_MAX_AGE_SECS = auth_db.SESSION_TTL_DAYS * 86400


def _secure_context() -> bool:
    """True when the app is served over https (behind the tailscale proxy)."""
    try:
        proto = str(st.context.headers.get("X-Forwarded-Proto", "")).lower()
    except Exception:
        return False
    return proto == "https"


def _write_cookie(value: str, max_age: int | None) -> None:
    """Set (or, with ``max_age=0``, clear) the cookie via same-origin JS.

    An empty streamlit component injects the cookie write into the page; the
    iframe is same-origin, so the parent document receives the cookie.
    """
    cookie = f"{COOKIE_NAME}={value}; path=/; SameSite=Lax"
    if max_age is not None:
        cookie += f"; max-age={max_age}"
    if _secure_context():
        cookie += "; Secure"
    js = f"document.cookie = {json.dumps(cookie)};"
    components.html(
        f"<script>{js}</script>", height=1, scrolling=False,
    )


def issue(user: dict) -> None:
    """Queue a fresh session token for a just-signed-in user.

    The token lives in ``st.session_state`` until the dashboard's next run,
    when ``flush()`` writes it to the browser cookie. Doing it this way
    (after the landing module's ``st.rerun()``) guarantees the write
    component actually renders instead of being discarded.
    """
    token = auth_db.create_session(user["id"])
    st.session_state["gex_session_token"] = token


def flush() -> None:
    """Write any queued session token to the browser cookie, then forget."""
    token = st.session_state.get("gex_session_token")
    if token:
        _write_cookie(token, _MAX_AGE_SECS)
        st.session_state.pop("gex_session_token", None)


def restore() -> dict | None:
    """Sign the user back in from the cookie, if it resolves to a live session.

    Returns the user dict (and sets ``st.session_state["gex_user"]``), or
    ``None`` when there is no cookie or it has expired / was revoked.
    """
    try:
        token = st.context.cookies.get(COOKIE_NAME)
    except Exception:
        return None
    if not token:
        return None
    user = auth_db.user_from_session(token)
    if user:
        st.session_state["gex_user"] = user
    return user


def end() -> None:
    """Revoke the session server-side and clear the cookie in the browser."""
    token = (
        st.session_state.pop("gex_session_token", None)
        or st.context.cookies.get(COOKIE_NAME)
    )
    if token:
        try:
            auth_db.revoke_session(token)
        except Exception:
            pass  # logout must work even if the DB is momentarily unreachable
    _write_cookie("", 0)
