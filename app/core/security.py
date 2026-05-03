import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.core.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def normalize_password(password: str) -> str:
    """
    Convert password into a fixed-length SHA-256 hash
    to avoid bcrypt 72-byte limitation.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_password_hash(password: str):

    safe_password = normalize_password(password)
    return pwd_context.hash(safe_password)


def verify_password(plain_password: str, hashed_password: str):
    safe_password = normalize_password(plain_password)
    return pwd_context.verify(safe_password, hashed_password)


def create_access_token(data: dict) -> str:

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def create_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def hash_token(token: str) -> str:
    """SHA-256 hash a token for safe DB storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
