import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user, require_permission
from app.models.user import User
from app.schemas.user import (
    MessageResponse,
    UserProfileUpdate,
    UserResponse,
    UserRoleUpdate,
)
from app.services.user_service import (
    change_target_user_role,
    deactivate_target_user,
    delete_user_account,
    reactivate_target_user,
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
    updated_user, error = await update_user_profile(db, current_user, data)
    if error == "At least one field must be provided":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error,
        )
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return updated_user


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    error = await delete_user_account(db, current_user, user_id)
    if error == "You can only delete your own account":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error)
    if error == "User not found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)

    return MessageResponse(detail="User deleted successfully")


# Admin


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: uuid.UUID,
    data: UserRoleUpdate,
    current_user: User = Depends(require_permission("manage_users")),
    db: AsyncSession = Depends(get_db),
):
    updated_user, error = await change_target_user_role(
        db, current_user, user_id, data.role
    )
    if error == "Admins cannot change their own role":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error)
    if error == "User not found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)

    return updated_user


@router.patch("/{user_id}/deactivate", response_model=MessageResponse)
async def deactivate_user_endpoint(
    user_id: uuid.UUID,
    _: User = Depends(require_permission("manage_users")),
    db: AsyncSession = Depends(get_db),
):
    error = await deactivate_target_user(db, user_id)
    if error == "User not found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return MessageResponse(detail="User deactivated successfully")


@router.patch("/{user_id}/reactivate", response_model=MessageResponse)
async def reactivate_user_endpoint(
    user_id: uuid.UUID,
    _: User = Depends(require_permission("manage_users")),
    db: AsyncSession = Depends(get_db),
):
    error = await reactivate_target_user(db, user_id)
    if error == "User not found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return MessageResponse(detail="User reactivated successfully")
