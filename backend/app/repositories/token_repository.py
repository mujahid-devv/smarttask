import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_token
from app.core.settings import settings
from app.models.tokens import RefreshToken


class TokenRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def store(self, user_id: uuid.UUID, raw_token: str) -> RefreshToken:
        token_row = RefreshToken(
            user_id=user_id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(token_row)
        await self.db.flush()
        return token_row

    async def find_valid(self, raw_token: str) -> RefreshToken | None:
        hashed = hash_token(raw_token)
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hashed,
                RefreshToken.revoked == False,  # noqa: E712
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()

    async def revoke(self, token_row: RefreshToken) -> None:
        token_row.revoked = True
        await self.db.flush()

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        """Revoke all active refresh tokens for a user (logout-all)."""
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,  # noqa: E712
            )
        )
        for token_row in result.scalars():
            token_row.revoked = True
        await self.db.flush()
