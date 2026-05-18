from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, verify_password
from app.models.user import User
from app.schemas.user import TokenResponse, UserCreate, UserLogin
from app.services.token_service import (
    revoke_refresh_token,
    store_refresh_token,
    validate_refresh_token,
)
from app.services.user_service import create_user, get_user_by_email, get_user_by_id


def _create_user_access_token(user) -> str:
    return create_access_token(
        data={"sub": user.email, "user_id": str(user.id), "role": user.role.value}
    )


async def register_user(db: AsyncSession, user_data: UserCreate) -> User | None:
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        return None

    return await create_user(db, user_data)


async def login_user(db: AsyncSession, credentials: UserLogin) -> TokenResponse | None:
    user = await get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.password_hash):
        return None

    access_token = _create_user_access_token(user)
    raw_refresh = create_refresh_token()
    await store_refresh_token(db, user.id, raw_refresh)

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        token_type="bearer",
    )


async def refresh_user_token(
    db: AsyncSession, raw_refresh_token: str
) -> TokenResponse | None:
    token_row = await validate_refresh_token(db, raw_refresh_token)
    if not token_row:
        return None

    await revoke_refresh_token(db, token_row)

    user = await get_user_by_id(db, token_row.user_id)
    if not user:
        return None

    access_token = _create_user_access_token(user)
    new_raw_refresh = create_refresh_token()
    await store_refresh_token(db, user.id, new_raw_refresh)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_raw_refresh,
        token_type="bearer",
    )


async def logout_user(db: AsyncSession, raw_refresh_token: str) -> str | None:
    token_row = await validate_refresh_token(db, raw_refresh_token)
    if not token_row:
        return "Invalid or expired refresh token"

    await revoke_refresh_token(db, token_row)
    return None