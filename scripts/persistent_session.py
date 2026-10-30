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
* **Sliding renewal**: the DB session's expiry slides forward on use, so the
  browser cookie's ``max-age`` is refreshed on successful restores too. A
  cookie written once at login would otherwise expire at its fixed 30-day
  mark while the DB session stayed alive — kicking active users back to the
  landing page "automatically". Both windows now slide together.

Streamlit has no native cookie setter, so the write happens through a
zero-height same-origin component running ``document.cookie`` (plain
JavaScript); the write targets the parent window first (most reliable when
same-origin access is allowed) and falls back to the iframe's own document.
Reads need no workaround because ``st.context.cookies`` surfaces the request
headers. The token never appears in URLs or logs — only in the cookie and
its hash in the database.
"""
import json
import logging
import time as _time

import streamlit as st
import streamlit.components.v1 as components

from scripts import auth_db

log = logging.getLogger("gex.persistent_session")
# Streamlit's default handler only surfaces WARNING+ from custom loggers,
# which would hide the restore breadcrumbs; attach a dedicated handler so
# session-diagnosis lines always reach the console/journal.
if not log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s %(name)s: %(message)s"))
    log.addHandler(_h)
log.setLevel(logging.INFO)

COOKIE_NAME = "gex_session"
_MAX_AGE_SECS = auth_db.SESSION_TTL_DAYS * 86400

# Rate-limit the periodic cookie rewrite: at most once per hour per browser
# session. Each rewrite renders a 1px component; frequent rewrites would
# churn the DOM every fragment tick for no benefit.
_REWRITE_INTERVAL = 3600.0


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
    iframe is same-origin, so the parent document receives the cookie. The
    write is attempted on the parent window first and then on the iframe's
    own document (same cookie jar when same-origin access is allowed);
    failures are swallowed individually so either successful path wins.
    """
    cookie = f"{COOKIE_NAME}={value}; path=/; SameSite=Lax"
    if max_age is not None:
        cookie += f"; max-age={max_age}"
    if _secure_context():
        cookie += "; Secure"
    js = json.dumps(cookie)
    script = (
        "(function(){"
        f"var c={js};"
        "var ok=false;"
        "try{window.parent.document.cookie=c;ok=true;}catch(e){}"
        "try{document.cookie=c;ok=true;}catch(e){}"
        "return ok;"
        "})()"
    )
    components.html(
        f"<script>{script}</script>", height=1, scrolling=False,
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
    # Reset the rewrite gate so the mandatory first write is not skipped.
    st.session_state["_gex_cookie_last_write"] = 0.0


def flush() -> None:
    """Write any queued session token to the browser cookie, then forget."""
    token = st.session_state.get("gex_session_token")
    if token:
        _write_cookie(token, _MAX_AGE_SECS)
        st.session_state.pop("gex_session_token", None)
        st.session_state["_gex_cookie_last_write"] = _time.time()
        log.info("session cookie written for a fresh login")


def restore() -> dict | None:
    """Sign the user back in from the cookie, if it resolves to a live session.

    Returns the user dict (and sets ``st.session_state["gex_user"]``), or
    ``None`` when there is no cookie or it has expired / was revoked.

    On success the cookie's ``max-age`` is refreshed (throttled to once per
    hour) so the browser window slides together with the DB session, and the
    outcome is logged so logout mysteries leave a breadcrumb in the app log.
    """
    try:
        token = st.context.cookies.get(COOKIE_NAME)
    except Exception as exc:  # context unavailable outside a script run
        log.warning("cookie read failed: %s", exc)
        return None
    if not token:
        # No cookie at all: normal for first-time visitors; beyond that it
        # means a previous write never reached the browser (blocked cookie,
        # private-mode cookie jar, or a different address than the login).
        log.info("no %s cookie present; signing-in state cannot be restored", COOKIE_NAME)
        return None
    try:
        user = auth_db.user_from_session(token)
    except Exception as exc:
        # Transient DB trouble (lock, WAL hiccup) must NOT look like a
        # logout: log it and behave as "not restored" for this run only,
        # leaving the cookie in place for the next attempt.
        log.warning("session lookup failed (kept cookie): %s", exc)
        return None
    if not user:
        log.warning("session cookie no longer valid (expired or revoked)")
        return None
    st.session_state["gex_user"] = user

    # Sliding cookie renewal — see module docstring.
    last_write = st.session_state.get("_gex_cookie_last_write", 0.0)
    if _time.time() - last_write >= _REWRITE_INTERVAL:
        _write_cookie(token, _MAX_AGE_SECS)
        st.session_state["_gex_cookie_last_write"] = _time.time()
        log.info("session cookie renewed for user %s", user.get("email"))
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
    st.session_state.pop("_gex_cookie_last_write", None)
