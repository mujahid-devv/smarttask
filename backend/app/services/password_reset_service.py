import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.tokens import PasswordResetToken
from app.models.user import User


def _generate_otp() -> str:
    return f"{random.SystemRandom().randint(0, 999999):06d}"


async def create_otp(db: AsyncSession, user: User) -> str:
    otp = _generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    reset_token = PasswordResetToken(
        user_id=user.id,
        otp_code=otp,
        expires_at=expires_at,
    )
    db.add(reset_token)
    await db.flush()

    return otp


async def get_valid_otp(
    db: AsyncSession, email: str, otp: str
) -> PasswordResetToken | None:
    result = await db.execute(
        select(PasswordResetToken)
        .join(PasswordResetToken.user)
        .where(
            PasswordResetToken.otp_code == otp,
            PasswordResetToken.used.is_(False),
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
            User.email == email,
        )
        .order_by(PasswordResetToken.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def mark_otp_used(db: AsyncSession, token_obj: PasswordResetToken) -> None:
    token_obj.used = True
    await db.flush()


async def update_user_password(db: AsyncSession, user: User, new_password: str) -> None:
    user.password_hash = get_password_hash(new_password)
    await db.flush()
