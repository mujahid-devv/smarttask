import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tokens import RefreshToken
from app.repositories.token_repository import TokenRepository


async def store_refresh_token(
    db: AsyncSession, user_id: uuid.UUID, raw_token: str
) -> RefreshToken:
    return await TokenRepository(db).store(user_id, raw_token)


async def validate_refresh_token(
    db: AsyncSession, raw_token: str
) -> RefreshToken | None:
    return await TokenRepository(db).find_valid(raw_token)


async def revoke_refresh_token(db: AsyncSession, token_row: RefreshToken) -> None:
    await TokenRepository(db).revoke(token_row)


async def revoke_all_user_tokens(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Revoke all active refresh tokens for a user (logout-all)."""
    await TokenRepository(db).revoke_all_for_user(user_id)
