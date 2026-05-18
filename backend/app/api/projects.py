import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.projects import require_project_role
from app.models import ProjectMember, User
from app.models.enums import MemberRole
from app.schemas.member import AddMemberRequest, MemberResponse, MemberRoleUpdate
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project_service import (
    add_project_member,
    archive_project_by_id,
    change_project_member_role,
    create_project,
    delete_project_for_owner,
    get_all_projects,
    get_project_for_user,
    get_project_members_for_project,
    remove_project_member,
    unarchive_project_by_id,
    update_project_for_user,
)

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
    project, error = await get_project_for_user(db, project_id, current_user)
    if error == "Project not found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error,
        )
    if error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error,
        )

    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project_route(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project, error = await update_project_for_user(
        db, project_id, current_user, data
    )
    if error == "Project not found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error,
        )
    if error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error,
        )

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft delete a project.[Project owner only]
    """
    error = await delete_project_for_owner(db, project_id, current_user.id)
    if error == "Project not found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error,
        )
    if error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error,
        )


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
):
    member, error = await add_project_member(db, project_id, data.user_id, data.role)
    if error == "Project not found" or error == "User not found":
        raise HTTPException(status.HTTP_404_NOT_FOUND, error)
    if error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, error)

    return member


@router.get("/{project_id}/members", response_model=list[MemberResponse])
async def list_members(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember | None = Depends(require_project_role()),
):
    members, error = await get_project_members_for_project(db, project_id)
    if error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error)

    return members


@router.delete(
    "/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_member(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember | None = Depends(require_project_role(MemberRole.OWNER)),
):
    error = await remove_project_member(db, project_id, user_id)
    if error == "Project not found" or error == "User is not a member of this project":
        raise HTTPException(status.HTTP_404_NOT_FOUND, error)
    if error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, error)


@router.patch("/{project_id}/members/{user_id}/role", response_model=MemberResponse)
async def change_member_role(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    data: MemberRoleUpdate,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember | None = Depends(require_project_role(MemberRole.OWNER)),
):
    member, error = await change_project_member_role(db, project_id, user_id, data.role)
    if error in {
        "Project not found",
        "User is not a member of this project",
        "User not found",
    }:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error)
    if error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, error)

    return member


# ── Archive / Unarchive


@router.post("/{project_id}/archive", response_model=ProjectResponse)
async def archive_project_route(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember | None = Depends(require_project_role(MemberRole.OWNER)),
):
    project, error = await archive_project_by_id(db, project_id)
    if error == "Project not found":
        raise HTTPException(status.HTTP_404_NOT_FOUND, error)
    if error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, error)

    return project


@router.post("/{project_id}/unarchive", response_model=ProjectResponse)
async def unarchive_project_route(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember | None = Depends(require_project_role(MemberRole.OWNER)),
):
    project, error = await unarchive_project_by_id(db, project_id)
    if error == "Project not found":
        raise HTTPException(status.HTTP_404_NOT_FOUND, error)
    if error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, error)

    return project
