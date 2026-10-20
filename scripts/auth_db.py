"""SQLite-backed account store for the GammaEx landing page.

A single small database (WAL mode) holds the users of the web app. Accounts
are identified by email only. Passwords are stored as salted scrypt hashes
(stdlib only, no extra dependencies). Every call opens a short-lived
connection: Streamlit fragments run in several threads, and per-call
connections sidestep sqlite3's cross-thread check while keeping the file
safe against concurrent writes.

Emails are stored lowercased and matched case-insensitively (NOCASE).

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
    email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    last_login    TEXT
);
CREATE TABLE IF NOT EXISTS password_resets (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    email      TEXT    NOT NULL COLLATE NOCASE,
    token_hash TEXT    NOT NULL UNIQUE,
    expires_at TEXT    NOT NULL,
    used_at    TEXT
);
CREATE INDEX IF NOT EXISTS idx_resets_email ON password_resets(email);
"""

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
        # Users table exists; make sure the resets table does too.
        conn.executescript(_SCHEMA)


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


def create_user(email: str, password: str) -> int:
    """Create an account; raise AuthError with a friendly message on failure."""
    email = (email or "").strip().lower()
    if not _EMAIL_RE.match(email):
        raise AuthError("Enter a valid email address")
    if not (_MIN_PASSWORD <= len(password or "") <= _MAX_PASSWORD):
        raise AuthError(f"Password must be {_MIN_PASSWORD}-{_MAX_PASSWORD} characters")
    try:
        with closing(_connect()) as conn:
            _ensure_schema(conn)
            cur = conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, hash_password(password)),
            )
            conn.commit()
            return int(cur.lastrowid)
    except sqlite3.IntegrityError as exc:
        raise AuthError("An account with that email already exists") from exc


def verify_user(email: str, password: str) -> dict:
    """Log in with an email; returns the account row as a dict."""
    email = (email or "").strip().lower()
    if not email:
        raise AuthError("Enter your email")
    with closing(_connect()) as conn:
        _ensure_schema(conn)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
    if row is None or not verify_password(password or "", row["password_hash"]):
        raise AuthError("Incorrect email or password")
    with closing(_connect()) as conn:
        conn.execute(
            "UPDATE users SET last_login = datetime('now') WHERE id = ?", (row["id"],)
        )
        conn.commit()
    return {"id": row["id"], "email": row["email"]}


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


# ---------------- password reset tokens ----------------

_RESET_TTL_MINUTES = 30


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_reset_token(email: str) -> str | None:
    """Create a single-use password-reset token; ``None`` for unknown emails.

    Only the SHA-256 hash of the token is stored, so the plaintext token can
    only travel in the emailed link. Unused tokens for the address are
    invalidated when a new one is requested.
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
        # A fresh request supersedes any pending link for this address.
        conn.execute("DELETE FROM password_resets WHERE email = ? AND used_at IS NULL", (email,))
        token = secrets.token_urlsafe(32)
        conn.execute(
            "INSERT INTO password_resets (email, token_hash, expires_at) VALUES (?, ?, datetime('now', ?))",
            (email, _token_hash(token), f"+{_RESET_TTL_MINUTES} minutes"),
        )
        conn.commit()
        return token


def validate_reset_token(token: str) -> str | None:
    """Return the account email if the token is unused and unexpired."""
    if not token:
        return None
    with closing(_connect()) as conn:
        _ensure_schema(conn)
        row = conn.execute(
            "SELECT email FROM password_resets WHERE token_hash = ? AND used_at IS NULL "
            "AND expires_at > datetime('now')",
            (_token_hash(token),),
        ).fetchone()
    return row[0] if row else None


def reset_password(token: str, new_password: str) -> str:
    """Consume a valid reset token and set the new password; return the email."""
    if not (_MIN_PASSWORD <= len(new_password or "") <= _MAX_PASSWORD):
        raise AuthError(f"Password must be {_MIN_PASSWORD}-{_MAX_PASSWORD} characters")
    with closing(_connect()) as conn:
        _ensure_schema(conn)
        row = conn.execute(
            "SELECT email FROM password_resets WHERE token_hash = ? AND used_at IS NULL "
            "AND expires_at > datetime('now')",
            (_token_hash(token or ""),),
        ).fetchone()
        if row is None:
            raise AuthError("This reset link is invalid or has expired. Request a new one.")
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE email = ?",
            (hash_password(new_password), row[0]),
        )
        conn.execute(
            "UPDATE password_resets SET used_at = datetime('now') WHERE token_hash = ?",
            (_token_hash(token),),
        )
        conn.commit()
        return row[0]
