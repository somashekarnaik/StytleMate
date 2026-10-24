import base64
import hashlib
import hmac
import json
import secrets
import time

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

SESSION_COOKIE = "stylemate_session"
SESSION_SECONDS = 60 * 60 * 24 * 7
PASSWORD_ITERATIONS = 600_000
DEV_AUTH_SECRET = "local-development-only-stylemate-secret"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${_encode(salt)}${_encode(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, expected = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        if iterations < 100_000 or iterations > 2_000_000:
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            _decode(salt_text),
            iterations,
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(_encode(actual), expected)


def create_session_token(user_id: int) -> str:
    issued_at = int(time.time())
    payload = _encode(
        json.dumps(
            {"sub": user_id, "iat": issued_at, "exp": issued_at + SESSION_SECONDS},
            separators=(",", ":"),
        ).encode("utf-8")
    )
    signature = _encode(
        hmac.new(_secret(), payload.encode("ascii"), hashlib.sha256).digest()
    )
    return f"{payload}.{signature}"


def get_session_user_id(token: str) -> int | None:
    try:
        payload, signature = token.split(".")
        expected = _encode(
            hmac.new(_secret(), payload.encode("ascii"), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(signature, expected):
            return None
        claims = json.loads(_decode(payload))
        user_id = claims.get("sub")
        if (
            not isinstance(user_id, int)
            or not isinstance(claims.get("exp"), int)
            or claims["exp"] <= int(time.time())
        ):
            return None
        return user_id
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    token = request.cookies.get(SESSION_COOKIE)
    user_id = get_session_user_id(token) if token else None
    user = db.get(User, user_id) if user_id is not None else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please sign in to access your wardrobe.",
        )
    return user


def _secret() -> bytes:
    secret = settings.auth_secret
    if not secret:
        if settings.app_environment.lower() == "production":
            raise RuntimeError("AUTH_SECRET must be configured in production.")
        secret = DEV_AUTH_SECRET
    return secret.encode("utf-8")


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
