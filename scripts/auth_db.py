"""SQLite-backed account store for the GammaEx landing page.

A single small database (WAL mode) holds the users of the web app. Passwords
are stored as salted scrypt hashes (stdlib only, no extra dependencies). Every
call opens a short-lived connection: Streamlit fragments run in several threads,
and per-call connections sidestep sqlite3's cross-thread check while keeping
the file safe against concurrent writes.

Location: ``~/.local/share/gex_app/app.db`` (override with GEX_APP_DB env var).
"""
from contextlib import closing
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    email         TEXT             COLLATE NOCASE UNIQUE,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    last_login    TEXT
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
"""

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{2,31}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_MIN_PASSWORD = 8
_MAX_PASSWORD = 128


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
    conn.executescript(_SCHEMA)
    return conn


# ---------------- password hashing ----------------

# Memory cap for scrypt: OpenSSL defaults to 32 MiB, which is exactly what
# n=2**15 * r=8 * 128 bytes needs — pass a larger cap to be safe.
_SCRYPT_MAXMEM = 128 * 1024 * 1024


def hash_password(password: str) -> str:
    """Salted scrypt hash: scrypt$n$r$p$salt_hex$hash_hex."""
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=2 ** 15, r=8, p=1, dklen=32,
        maxmem=_SCRYPT_MAXMEM,
    )
    return f"scrypt${2 ** 15}$8$1${salt.hex()}${key.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_hex, key_hex = stored.split("$")
        if scheme != "scrypt":
            return False
        key = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n), r=int(r), p=int(p), dklen=len(key_hex) // 2,
            maxmem=_SCRYPT_MAXMEM,
        )
        return hmac.compare_digest(key.hex(), key_hex)
    except (ValueError, TypeError):
        return False


# ---------------- account operations ----------------

class AuthError(Exception):
    """User-facing signup/login failure."""


def create_user(username: str, email: str, password: str) -> int:
    """Create an account; raise AuthError with a friendly message on failure."""
    username = (username or "").strip()
    email = (email or "").strip() or None
    if not _USERNAME_RE.match(username or ""):
        raise AuthError("Username must be 3-32 characters: letters, numbers, ., _, -")
    if email and not _EMAIL_RE.match(email):
        raise AuthError("That email address doesn't look right")
    if not (_MIN_PASSWORD <= len(password or "") <= _MAX_PASSWORD):
        raise AuthError(f"Password must be {_MIN_PASSWORD}-{_MAX_PASSWORD} characters")
    try:
        with closing(_connect()) as conn:
            cur = conn.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, hash_password(password)),
            )
            conn.commit()
            return int(cur.lastrowid)
    except sqlite3.IntegrityError as exc:
        msg = str(exc).lower()
        if "username" in msg:
            raise AuthError("That username is taken") from exc
        if "email" in msg:
            raise AuthError("An account with that email already exists") from exc
        raise AuthError("Could not create the account") from exc


def verify_user(identifier: str, password: str) -> dict:
    """Log in with username or email; returns the account row as a dict."""
    ident = (identifier or "").strip()
    if not ident:
        raise AuthError("Enter your username or email")
    with closing(_connect()) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? OR (email IS NOT NULL AND email = ?)",
            (ident, ident),
        ).fetchone()
    if row is None or not verify_password(password or "", row["password_hash"]):
        raise AuthError("Incorrect username or password")
    with closing(_connect()) as conn:
        conn.execute(
            "UPDATE users SET last_login = datetime('now') WHERE id = ?", (row["id"],)
        )
        conn.commit()
    return {"id": row["id"], "username": row["username"], "email": row["email"]}


def get_user(user_id: int) -> dict | None:
    with closing(_connect()) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, username, email, created_at, last_login FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def user_count() -> int:
    with closing(_connect()) as conn:
        return int(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0])
