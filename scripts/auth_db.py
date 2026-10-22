"""SQLite-backed account store for the GammaEx landing page.

A single small database (WAL mode) holds the users of the web app. Accounts
are identified by email only and are passwordless: logins happen through a
one-time magic link mailed to the account address, and first-time users get
in after an administrator approves their access request. Tokens are stored
only as SHA-256 hashes and are single-use. Every call opens a short-lived
connection: Streamlit fragments run in several threads, and per-call
connections sidestep sqlite3's cross-thread check while keeping the file
safe against concurrent writes.

Emails are stored lowercased and matched case-insensitively (NOCASE).

Location: ``~/.local/share/gex_app/app.db`` (override with GEX_APP_DB env var).
"""
from contextlib import closing
import hashlib
import os
import re
import secrets
import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    last_login    TEXT
);
CREATE TABLE IF NOT EXISTS login_tokens (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    email      TEXT    NOT NULL COLLATE NOCASE,
    token_hash TEXT    NOT NULL UNIQUE,
    expires_at TEXT    NOT NULL,
    used_at    TEXT
);
CREATE TABLE IF NOT EXISTS signup_requests (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    email      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    token_hash TEXT    NOT NULL UNIQUE,
    expires_at TEXT    NOT NULL,
    used_at    TEXT
);
CREATE TABLE IF NOT EXISTS session_tokens (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash   TEXT    NOT NULL UNIQUE,
    expires_at   TEXT    NOT NULL,
    refreshed_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_login_tokens_email ON login_tokens(email);
CREATE INDEX IF NOT EXISTS idx_requests_email ON signup_requests(email);
CREATE INDEX IF NOT EXISTS idx_session_tokens_user ON session_tokens(user_id);
DROP TABLE IF EXISTS password_resets;
"""

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _db_path() -> Path:
    custom = os.environ.get("GEX_APP_DB")
    if custom:
        return Path(custom)
    return Path.home() / ".local/share/gex_app/app.db"


def _connect() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Create the tables if missing; migrate the old username+email schema."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
    if not cols:
        conn.executescript(_SCHEMA)
    elif "username" in cols and "email" in cols:
        # Legacy schema (username required, email optional): keep any rows
        # that carry an usable email, drop the rest, then rebuild.
        conn.executescript(
            """
            ALTER TABLE users RENAME TO users_legacy;
            """
        )
        conn.executescript(_SCHEMA)
        conn.execute(
            """
            INSERT OR IGNORE INTO users (id, email, password_hash, created_at, last_login)
            SELECT id, lower(trim(email)), password_hash, created_at, last_login
            FROM users_legacy
            WHERE email IS NOT NULL AND trim(email) <> ''
            """
        )
        conn.execute("DROP TABLE users_legacy")
        conn.commit()
    else:
        # Users table exists; make sure the token tables do too.
        conn.executescript(_SCHEMA)


# ---------------- password hashing ----------------

# Memory cap for scrypt: OpenSSL defaults to 32 MiB, which is exactly what
# n=2**15 * r=8 * 128 bytes needs — pass a larger cap to be safe.
_SCRYPT_MAXMEM = 128 * 1024 * 1024


def hash_password(password: str) -> str:
    """Salted scrypt hash: scrypt$n$r$p$salt_hex$hash_hex.

    Accounts are passwordless; this only generates the placeholder hash a
    new account starts with (unguessable, so nobody can ever log in with a
    password against the users table).
    """
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=2 ** 15, r=8, p=1, dklen=32,
        maxmem=_SCRYPT_MAXMEM,
    )
    return f"scrypt${2 ** 15}$8$1${salt.hex()}${key.hex()}"


# ---------------- account operations ----------------

class AuthError(Exception):
    """User-facing login/approval failure."""


def get_user(user_id: int) -> dict | None:
    with closing(_connect()) as conn:
        _ensure_schema(conn)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, email, created_at, last_login FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def user_count() -> int:
    with closing(_connect()) as conn:
        _ensure_schema(conn)
        return int(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0])


# ---------------- magic-link tokens & access requests ----------------

_TOKEN_TTL_MINUTES = 30
_APPROVAL_TTL_HOURS = 72

# Long-lived "remember me" sessions (persistent_session.py rides on these).
SESSION_TTL_DAYS = 30


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _new_token(conn: sqlite3.Connection, table: str, email: str,
               ttl_sql: str) -> str:
    """Mint a single-use token for ``table``; supersedes any pending one.

    Only the SHA-256 hash of the token is stored, so the plaintext token can
    only travel in the emailed link. ``table`` is always a module constant.
    """
    # A fresh request supersedes any pending link for this address.
    conn.execute(f"DELETE FROM {table} WHERE email = ? AND used_at IS NULL", (email,))
    token = secrets.token_urlsafe(32)
    conn.execute(
        f"INSERT INTO {table} (email, token_hash, expires_at) VALUES (?, ?, datetime('now', ?))",
        (email, _token_hash(token), ttl_sql),
    )
    return token


def create_login_token(email: str) -> str | None:
    """Create a one-time magic-link login token; ``None`` for unknown emails.

    Only known accounts get a link: unknown addresses are offered the
    administrator-approval flow instead.
    """
    email = (email or "").strip().lower()
    if not _EMAIL_RE.match(email):
        return None
    with closing(_connect()) as conn:
        _ensure_schema(conn)
        row = conn.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()
    if row is None:
        return None
    with closing(_connect()) as conn:
        _ensure_schema(conn)
        token = _new_token(conn, "login_tokens", email,
                           f"+{_TOKEN_TTL_MINUTES} minutes")
        conn.commit()
    return token


def login_with_token(token: str) -> dict:
    """Consume a valid magic-link token; return the account dict."""
    with closing(_connect()) as conn:
        _ensure_schema(conn)
        row = conn.execute(
            "SELECT email FROM login_tokens WHERE token_hash = ? AND used_at IS NULL "
            "AND expires_at > datetime('now')",
            (_token_hash(token or ""),),
        ).fetchone()
        if row is None:
            raise AuthError("This login link is invalid or has expired. Request a new one.")
        conn.execute(
            "UPDATE login_tokens SET used_at = datetime('now') WHERE token_hash = ?",
            (_token_hash(token),),
        )
        conn.execute(
            "UPDATE users SET last_login = datetime('now') WHERE email = ?", (row[0],)
        )
        user = conn.execute(
            "SELECT id FROM users WHERE email = ?", (row[0],)
        ).fetchone()
        conn.commit()
    return {"id": user[0], "email": row[0]}


def request_access(email: str) -> str:
    """File (or refresh) an access request for an address without an account.

    Returns the single-use approval token for the administrator link. A new
    request replaces the pending one for the address, so stale approval
    links stop working.
    """
    email = (email or "").strip().lower()
    if not _EMAIL_RE.match(email):
        raise AuthError("Enter a valid email address")
    with closing(_connect()) as conn:
        _ensure_schema(conn)
        # Keep at most one live request per address; freeing the row also
        # releases the UNIQUE(email) slot so re-requests stay possible.
        conn.execute("DELETE FROM signup_requests WHERE email = ? AND used_at IS NULL", (email,))
        token = secrets.token_urlsafe(32)
        conn.execute(
            "INSERT INTO signup_requests (email, token_hash, expires_at) VALUES (?, ?, datetime('now', ?))",
            (email, _token_hash(token), f"+{_APPROVAL_TTL_HOURS} hours"),
        )
        conn.commit()
    return token


def approve_request(token: str) -> str:
    """Consume a pending access request; create the account, return its email.

    Called when the administrator opens the emailed approval link. The
    caller then sends the new user a magic link — approval never logs
    anyone in by itself, so the new account's ``last_login`` stays empty
    until their first real login. The account is passwordless from birth:
    the scrypt placeholder hash stores an unguessable secret nobody can
    ever log in with.
    """
    with closing(_connect()) as conn:
        _ensure_schema(conn)
        row = conn.execute(
            "SELECT email FROM signup_requests WHERE token_hash = ? AND used_at IS NULL "
            "AND expires_at > datetime('now')",
            (_token_hash(token or ""),),
        ).fetchone()
        if row is None:
            raise AuthError("This approval link is invalid or has already been used.")
        conn.execute(
            "UPDATE signup_requests SET used_at = datetime('now') WHERE token_hash = ?",
            (_token_hash(token),),
        )
        if conn.execute(
            "SELECT 1 FROM users WHERE email = ?", (row[0],)
        ).fetchone() is None:
            conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (row[0], hash_password(secrets.token_urlsafe(32))),
            )
        conn.commit()
    return row[0]


# ---------------- persistent browser sessions ----------------

def create_session(user_id: int) -> str:
    """Mint a long-lived session bearer token for a user.

    Unlike magic links these are reusable (the browser sends the cookie on
    every request), expire after ``SESSION_TTL_DAYS``, and are stored only
    as SHA-256 hashes. Expired tokens are swept here.
    """
    token = secrets.token_urlsafe(32)
    with closing(_connect()) as conn:
        _ensure_schema(conn)
        conn.execute(
            "DELETE FROM session_tokens WHERE expires_at < datetime('now')"
        )
        conn.execute(
            "INSERT INTO session_tokens (user_id, token_hash, expires_at) "
            "VALUES (?, ?, datetime('now', ?))",
            (user_id, _token_hash(token), f"+{SESSION_TTL_DAYS} days"),
        )
        conn.commit()
    return token


def user_from_session(token: str) -> dict | None:
    """Resolve a session token to the account dict; sliding-renews expiry.

    Returns ``None`` for unknown, revoked, or expired tokens. The expiry is
    pushed out to a full TTL again whenever a session that has been in use
    for more than a day is validated, so active users are not logged out
    after exactly 30 days while abandoned ones eventually are.
    """
    token = token or ""
    if not token:
        return None
    with closing(_connect()) as conn:
        _ensure_schema(conn)
        row = conn.execute(
            "SELECT s.id, u.id, u.email FROM session_tokens s "
            "JOIN users u ON u.id = s.user_id "
            "WHERE s.token_hash = ? AND s.expires_at > datetime('now')",
            (_token_hash(token),),
        ).fetchone()
        if row is None:
            return None
        session_id, user_id, email = row[0], row[1], row[2]
        conn.execute(
            "UPDATE session_tokens SET expires_at = datetime('now', ?), "
            "refreshed_at = datetime('now') WHERE id = ? "
            "AND refreshed_at < datetime('now', '-1 day')",
            (f"+{SESSION_TTL_DAYS} days", session_id),
        )
        conn.commit()
    return {"id": user_id, "email": email}


def revoke_session(token: str) -> None:
    """Delete one session token (used by the Log out button)."""
    with closing(_connect()) as conn:
        _ensure_schema(conn)
        conn.execute(
            "DELETE FROM session_tokens WHERE token_hash = ?",
            (_token_hash(token or ""),),
        )
        conn.commit()
