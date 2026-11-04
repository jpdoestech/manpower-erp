import hashlib
import hmac
import os
import re
import secrets
from dataclasses import dataclass
from urllib.parse import urlsplit

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

COOKIE = "erp_session"
SESSION_SECONDS = 8 * 60 * 60
hasher = PasswordHasher(memory_cost=19456, time_cost=2, parallelism=1)
_dummy_hash = hasher.hash(secrets.token_urlsafe(32))


@dataclass(frozen=True)
class AuthSettings:
    origin: str
    cookie_secure: bool


def auth_settings() -> AuthSettings:
    origin = os.environ.get("AUTH_ORIGIN", "http://127.0.0.1:5173")
    secure = os.environ.get("AUTH_COOKIE_SECURE", "true")
    try:
        parsed = urlsplit(origin)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.path
            or parsed.query
            or parsed.fragment
            or secure not in {"true", "false"}
            or (parsed.port is not None and not 1 <= parsed.port <= 65535)
        ):
            raise ValueError
        loopback = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        if (secure == "false" and not loopback) or (
            parsed.scheme == "http" and not loopback
        ):
            raise ValueError
        return AuthSettings(origin, secure == "true")
    except ValueError:
        raise RuntimeError(
            "Valid authentication origin/cookie configuration is required"
        ) from None


def normalize_username(value: str) -> str:
    value = value.strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9_.-]{2,63}", value):
        raise ValueError("Invalid username")
    return value


def hash_password(password: str) -> str:
    if not 15 <= len(password) <= 128:
        raise ValueError("Password must contain 15 to 128 characters")
    return hasher.hash(password)


def verify_password(password: str, encoded: str | None) -> bool:
    try:
        return hasher.verify(encoded or _dummy_hash, password) and encoded is not None
    except (VerificationError, InvalidHashError):
        return False


def token_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def csrf_token(token: str) -> str:
    return hmac.new(token.encode(), b"csrf", hashlib.sha256).hexdigest()
