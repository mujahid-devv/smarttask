import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tokens import RefreshToken


async def create_refresh_token(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    token_hash: str,
    expires_at: datetime,
) -> RefreshToken:
    token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(token)
    await db.flush()
    return token


async def get_valid_refresh_token(
    db: AsyncSession,
    *,
    token_hash: str,
    now: datetime,
) -> RefreshToken | None:
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,  # noqa: E712
            RefreshToken.expires_at > now,
        )
    )
    return result.scalar_one_or_none()


async def get_active_user_refresh_tokens(
    db: AsyncSession, user_id: uuid.UUID
) -> list[RefreshToken]:
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,  # noqa: E712
        )
    )
    return list(result.scalars().all())


async def save_refresh_token(db: AsyncSession, token: RefreshToken) -> RefreshToken:
    await db.flush()
    return token


async def save_changes(db: AsyncSession) -> None:
    await db.flush()