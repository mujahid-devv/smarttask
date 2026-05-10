import random
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email import send_reset_email
from app.core.security import get_password_hash
from app.models.tokens import PasswordResetToken
from app.models.user import User
from app.repositories import password_reset_repository, user_repository
from app.services.user_service import get_user_by_email, get_user_by_id


def _generate_otp() -> str:
    return f"{random.SystemRandom().randint(0, 999999):06d}"


async def request_password_reset(db: AsyncSession, email: str) -> None:
    user = await get_user_by_email(db, email)
    if not user:
        return

    otp = await create_otp(db, user)
    await send_reset_email(user.email, otp)


async def confirm_password_reset(
    db: AsyncSession, email: str, otp: str, new_password: str
) -> bool:
    reset_token = await get_valid_otp(db, email, otp)
    if not reset_token:
        return False

    user = await get_user_by_id(db, reset_token.user_id)
    if not user:
        return False

    await update_user_password(db, user, new_password)
    await mark_otp_used(db, reset_token)
    return True


async def create_otp(db: AsyncSession, user: User) -> str:
    otp = _generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    await password_reset_repository.create_password_reset_token(
        db,
        user_id=user.id,
        otp_code=otp,
        expires_at=expires_at,
    )

    return otp


async def get_valid_otp(
    db: AsyncSession, email: str, otp: str
) -> PasswordResetToken | None:
    return await password_reset_repository.get_valid_password_reset_token(
        db,
        email=email,
        otp_code=otp,
        now=datetime.now(timezone.utc),
    )


async def mark_otp_used(db: AsyncSession, token_obj: PasswordResetToken) -> None:
    token_obj.used = True
    await password_reset_repository.save_password_reset_token(db, token_obj)


async def update_user_password(db: AsyncSession, user: User, new_password: str) -> None:
    user.password_hash = get_password_hash(new_password)
    await user_repository.save_user(db, user)
