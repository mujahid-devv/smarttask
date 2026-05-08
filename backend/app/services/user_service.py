from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    return await UserRepository(db).get_by_email(email)


async def get_user_by_id(db: AsyncSession, user_id) -> User | None:
    return await UserRepository(db).get_by_id(user_id)


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    password_hash = get_password_hash(user_data.password)
    return await UserRepository(db).create(
        email=user_data.email,
        password_hash=password_hash,
        full_name=user_data.full_name,
    )
