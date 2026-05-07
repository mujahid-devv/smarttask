import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.projects import require_project_role
from app.models import ProjectMember, User
from app.models.enums import MemberRole, ProjectStatus
from app.schemas.member import AddMemberRequest, MemberResponse, MemberRoleUpdate
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project_service import add_member as svc_add_member
from app.services.project_service import archive_project
from app.services.project_service import change_member_role as svc_change_member_role
from app.services.project_service import (
    create_project,
    get_all_projects,
    get_project_by_id,
    get_project_member,
    get_project_members,
)
from app.services.project_service import remove_member as svc_remove_member
from app.services.project_service import (
    soft_delete_project,
    unarchive_project,
    update_project,
)
from app.services.user_service import get_user_by_id

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_new_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new project."""
    return await create_project(db=db, owner_id=current_user.id, data=data)


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 20,
    include_archived: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all projects for the authenticated user."""
    projects = await get_all_projects(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        include_archived=include_archived,
    )
    if not projects:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No projects yet"
        )

    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # check user is a member of the project
    membership = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    if not membership.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project",
        )

    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project_route(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # check user is a member of the project
    membership = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    if not membership.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project",
        )

    return await update_project(db, project, data)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft delete a project.[Project owner only]
    """
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Ownership check
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can delete this project",
        )

    await soft_delete_project(db, project)


# Member management


@router.post(
    "/{project_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    project_id: uuid.UUID,
    data: AddMemberRequest,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember | None = Depends(require_project_role(MemberRole.OWNER)),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")

    target_user = await get_user_by_id(db, data.user_id)
    if not target_user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    existing = await get_project_member(db, project_id, data.user_id)
    if existing:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "User is already a member of this project"
        )

    member = await svc_add_member(db, project_id, data.user_id, data.role)
    return MemberResponse(
        user_id=target_user.id,
        full_name=target_user.full_name,
        email=target_user.email,
        role=member.role,
        joined_at=member.created_at,
    )


@router.get("/{project_id}/members", response_model=list[MemberResponse])
async def list_members(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember | None = Depends(require_project_role()),
):
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")

    return await get_project_members(db, project_id)


@router.delete(
    "/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_member(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember | None = Depends(require_project_role(MemberRole.OWNER)),
):
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")

    if user_id == project.owner_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Cannot remove the project owner"
        )

    member = await get_project_member(db, project_id, user_id)
    if not member:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "User is not a member of this project"
        )

    await svc_remove_member(db, member)


@router.patch("/{project_id}/members/{user_id}/role", response_model=MemberResponse)
async def change_member_role(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    data: MemberRoleUpdate,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember | None = Depends(require_project_role(MemberRole.OWNER)),
):
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")

    if user_id == project.owner_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Cannot change the project owner's role"
        )

    member = await get_project_member(db, project_id, user_id)
    if not member:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "User is not a member of this project"
        )

    updated = await svc_change_member_role(db, member, data.role)
    user = await get_user_by_id(db, user_id)
    return MemberResponse(
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=updated.role,
        joined_at=updated.created_at,
    )


# ── Archive / Unarchive


@router.post("/{project_id}/archive", response_model=ProjectResponse)
async def archive_project_route(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember | None = Depends(require_project_role(MemberRole.OWNER)),
):
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")

    if project.status == ProjectStatus.ARCHIVED:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Project is already archived")

    return await archive_project(db, project)


@router.post("/{project_id}/unarchive", response_model=ProjectResponse)
async def unarchive_project_route(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember | None = Depends(require_project_role(MemberRole.OWNER)),
):
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")

    if project.status != ProjectStatus.ARCHIVED:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Project unarchived")

    return await unarchive_project(db, project)
