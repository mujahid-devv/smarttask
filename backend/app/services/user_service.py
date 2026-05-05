from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreate, UserProfileUpdate


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(
        select(User).where(User.email == email, User.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id) -> User | None:
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def update_user_profile(
    db: AsyncSession, user: User, data: UserProfileUpdate
) -> tuple[User, str | None]:
    """Returns (updated_user, error_message). error_message is set if password check fails."""  # noqa: E501
    if data.new_password:
        if not verify_password(data.current_password, user.password_hash):
            return user, "Current password is incorrect"
        user.password_hash = get_password_hash(data.new_password)

    if data.full_name is not None:
        user.full_name = data.full_name

    if data.email is not None:
        user.email = data.email

    user.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(user)
    return user, None


async def soft_delete_user(db: AsyncSession, user: User) -> None:
    user.is_deleted = True
    user.is_active = False
    user.deleted_at = datetime.now(timezone.utc)
    await db.flush()


async def change_user_role(db: AsyncSession, user: User, role: UserRole) -> User:
    user.role = role
    user.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(user)
    return user


async def deactivate_user(db: AsyncSession, user: User) -> User:
    user.is_active = False
    user.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(user)
    return user


async def reactivate_user(db: AsyncSession, user: User) -> User:
    user.is_active = True
    user.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(user)
    return user
