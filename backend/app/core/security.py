from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import UTC, datetime, timedelta

import jwt

ITERATIONS = 240_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt), int(iterations))
        return hmac.compare_digest(candidate, base64.b64decode(expected))
    except (ValueError, TypeError):
        return False


def create_token(user_id: int, role: str) -> str:
    now = datetime.now(UTC)
    payload = {"sub": str(user_id), "role": role, "iat": now, "exp": now + timedelta(hours=8)}
    return jwt.encode(payload, os.getenv("JWT_SECRET", "development-only-change-me"), algorithm="HS256")


def decode_token(token: str) -> dict[str, object]:
    return jwt.decode(token, os.getenv("JWT_SECRET", "development-only-change-me"), algorithms=["HS256"])
