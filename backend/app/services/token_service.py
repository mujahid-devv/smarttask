import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_token
from app.core.settings import settings
from app.models.tokens import RefreshToken
from app.repositories import token_repository


async def store_refresh_token(
    db: AsyncSession, user_id: uuid.UUID, raw_token: str
) -> RefreshToken:
    return await token_repository.create_refresh_token(
        db,
        user_id=user_id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


async def validate_refresh_token(
    db: AsyncSession, raw_token: str
) -> RefreshToken | None:
    return await token_repository.get_valid_refresh_token(
        db,
        token_hash=hash_token(raw_token),
        now=datetime.now(timezone.utc),
    )


async def revoke_refresh_token(db: AsyncSession, token_row: RefreshToken) -> None:
    token_row.revoked = True
    await token_repository.save_refresh_token(db, token_row)


async def revoke_all_user_tokens(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Revoke all active refresh tokens for a user (logout-all)."""
    tokens = await token_repository.get_active_user_refresh_tokens(db, user_id)
    for token_row in tokens:
        token_row.revoked = True
    if tokens:
        await token_repository.save_changes(db)
