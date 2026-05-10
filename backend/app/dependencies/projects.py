import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.enums import MemberRole, UserRole
from app.models.project_member import ProjectMember
from app.models.user import User
from app.services.project_service import get_project_by_id, get_project_member


def require_project_role(*roles: MemberRole) -> Callable:
    async def dependency(
        project_id: uuid.UUID = Path(...),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> ProjectMember | None:
        project = await get_project_by_id(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # system admin bypasses membership checks
        if current_user.role == UserRole.ADMIN:
            return None

        member = await get_project_member(db, project_id, current_user.id)

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this project",
            )

        if roles and member.role not in roles:
            required = ", ".join(r.value for r in roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires project role: {required}",
            )

        return member

    return dependency
