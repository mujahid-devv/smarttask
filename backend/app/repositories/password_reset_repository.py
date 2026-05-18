import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tokens import PasswordResetToken
from app.models.user import User


async def create_password_reset_token(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    otp_code: str,
    expires_at: datetime,
) -> PasswordResetToken:
    reset_token = PasswordResetToken(
        user_id=user_id,
        otp_code=otp_code,
        expires_at=expires_at,
    )
    db.add(reset_token)
    await db.flush()
    return reset_token


async def get_valid_password_reset_token(
    db: AsyncSession,
    *,
    email: str,
    otp_code: str,
    now: datetime,
) -> PasswordResetToken | None:
    result = await db.execute(
        select(PasswordResetToken)
        .join(PasswordResetToken.user)
        .where(
            PasswordResetToken.otp_code == otp_code,
            PasswordResetToken.used.is_(False),
            PasswordResetToken.expires_at > now,
            User.email == email,
        )
        .order_by(PasswordResetToken.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def save_password_reset_token(db: AsyncSession, token: PasswordResetToken) -> None:
    await db.flush()