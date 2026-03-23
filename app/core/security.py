import base64
import hashlib
import hmac
import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.core.config import settings


def hash_password(password: str, iterations: int = 390000) -> str:
    salt = base64.urlsafe_b64encode(hashlib.sha256(uuid.uuid4().bytes).digest()[:16]).decode()
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        base64.urlsafe_b64decode(salt.encode("utf-8")),
        iterations,
    )
    digest = base64.urlsafe_b64encode(dk).decode("utf-8")
    return f"pbkdf2_sha256${iterations}${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, raw_iterations, salt, expected_digest = password_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False

        iterations = int(raw_iterations)
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            base64.urlsafe_b64decode(salt.encode("utf-8")),
            iterations,
        )
        actual_digest = base64.urlsafe_b64encode(derived).decode("utf-8")
        return hmac.compare_digest(actual_digest, expected_digest)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: str, username: str) -> str:
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "usr": username,
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
