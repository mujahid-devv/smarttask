import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user, require_permission
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import (
    MessageResponse,
    UserProfileUpdate,
    UserResponse,
    UserRoleUpdate,
)
from app.services.user_service import (
    change_user_role,
    deactivate_user,
    get_user_by_id,
    reactivate_user,
    soft_delete_user,
    update_user_profile,
)

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not data.full_name and not data.email and not data.new_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one field must be provided",
        )

    updated_user, error = await update_user_profile(db, current_user, data)
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return updated_user


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    is_self = current_user.id == user_id
    is_admin = current_user.role == UserRole.ADMIN

    if not is_self and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own account",
        )

    if is_self:
        target = current_user
    else:
        target = await get_user_by_id(db, user_id)
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

    await soft_delete_user(db, target)
    return MessageResponse(detail="User deleted successfully")


# Admin


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: uuid.UUID,
    data: UserRoleUpdate,
    current_user: User = Depends(require_permission("manage_users")),
    db: AsyncSession = Depends(get_db),
):
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins cannot change their own role",
        )

    target = await get_user_by_id(db, user_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return await change_user_role(db, target, data.role)


@router.patch("/{user_id}/deactivate", response_model=MessageResponse)
async def deactivate_user_endpoint(
    user_id: uuid.UUID,
    current_user: User = Depends(require_permission("manage_users")),
    db: AsyncSession = Depends(get_db),
):
    target = await get_user_by_id(db, user_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not target.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already deactivated",
        )

    await deactivate_user(db, target)
    return MessageResponse(detail="User deactivated successfully")


@router.patch("/{user_id}/reactivate", response_model=MessageResponse)
async def reactivate_user_endpoint(
    user_id: uuid.UUID,
    current_user: User = Depends(require_permission("manage_users")),
    db: AsyncSession = Depends(get_db),
):
    target = await get_user_by_id(db, user_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if target.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is already active"
        )

    await reactivate_user(db, target)
    return MessageResponse(detail="User reactivated successfully")
