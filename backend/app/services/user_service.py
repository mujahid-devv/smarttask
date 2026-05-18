from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories import user_repository
from app.schemas.user import UserCreate, UserProfileUpdate


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    return await user_repository.get_user_by_email(db, email)


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    return await user_repository.get_user_by_id(db, user_id)


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    return await user_repository.create_user(
        db,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
    )


async def update_user_profile(
    db: AsyncSession, user: User, data: UserProfileUpdate
) -> tuple[User, str | None]:
    if not data.full_name and not data.email and not data.new_password:
        return user, "At least one field must be provided"

    if data.new_password:
        if not verify_password(data.current_password, user.password_hash):
            return user, "Current password is incorrect"
        user.password_hash = get_password_hash(data.new_password)

    if data.full_name is not None:
        user.full_name = data.full_name

    if data.email is not None:
        user.email = data.email

    updated_user = await user_repository.save_user(db, user)
    return updated_user, None


async def soft_delete_user(db: AsyncSession, user: User) -> None:
    if user.is_deleted:
        return

    user.is_deleted = True
    user.is_active = False
    user.deleted_at = datetime.now(timezone.utc)
    await user_repository.save_user(db, user)


async def delete_user_account(
    db: AsyncSession, current_user: User, user_id: UUID
) -> str | None:
    is_self = current_user.id == user_id
    is_admin = current_user.role == UserRole.ADMIN

    if not is_self and not is_admin:
        return "You can only delete your own account"

    if is_self:
        target = current_user
    else:
        target = await get_user_by_id(db, user_id)
        if not target:
            return "User not found"

    await soft_delete_user(db, target)
    return None


async def change_user_role(db: AsyncSession, user: User, role: UserRole) -> User:
    user.role = role
    return await user_repository.save_user(db, user)


async def change_target_user_role(
    db: AsyncSession, current_user: User, user_id: UUID, role: UserRole
) -> tuple[User | None, str | None]:
    if current_user.id == user_id:
        return None, "Admins cannot change their own role"

    target = await get_user_by_id(db, user_id)
    if not target:
        return None, "User not found"

    return await change_user_role(db, target, role), None


async def deactivate_user(db: AsyncSession, user: User) -> User:
    user.is_active = False
    return await user_repository.save_user(db, user)


async def deactivate_target_user(
    db: AsyncSession, user_id: UUID
) -> str | None:
    target = await get_user_by_id(db, user_id)
    if not target:
        return "User not found"

    if not target.is_active:
        return "User is already deactivated"

    await deactivate_user(db, target)
    return None


async def reactivate_user(db: AsyncSession, user: User) -> User:
    user.is_active = True
    return await user_repository.save_user(db, user)


async def reactivate_target_user(
    db: AsyncSession, user_id: UUID
) -> str | None:
    target = await get_user_by_id(db, user_id)
    if not target:
        return "User not found"

    if target.is_active:
        return "User is already active"

    await reactivate_user(db, target)
    return None
