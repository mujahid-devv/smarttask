import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, ProjectMember, User
from app.models.enums import MemberRole, ProjectStatus, UserRole
from app.repositories import project_repository
from app.schemas.member import MemberResponse
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.user_service import get_user_by_id


def _member_response(member: ProjectMember, user) -> MemberResponse:
    return MemberResponse(
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=member.role,
        joined_at=member.created_at,
    )


async def get_project_by_id(db: AsyncSession, project_id: uuid.UUID) -> Project | None:
    return await project_repository.get_project_by_id(db, project_id)


async def get_all_projects(
    db: AsyncSession,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 10,
    include_archived: bool = False,
) -> list[Project]:
    return await project_repository.get_user_projects(
        db,
        user_id=user_id,
        skip=skip,
        limit=limit,
        include_archived=include_archived,
    )


async def create_project(
    db: AsyncSession,
    owner_id: uuid.UUID,
    data: ProjectCreate,
) -> Project:
    project = await project_repository.create_project(
        db,
        owner_id=owner_id,
        name=data.name,
        description=data.description,
        status=data.status,
        tags=data.tags,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    await project_repository.create_project_member(
        db,
        project_id=project.id,
        user_id=owner_id,
        role=MemberRole.OWNER,
    )
    return project


async def update_project(
    db: AsyncSession,
    project: Project,
    data: ProjectUpdate,
) -> Project:
    """Update only the fields that were explicitly sent in the request."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    return await project_repository.save_project(db, project)


async def get_project_for_user(
    db: AsyncSession, project_id: uuid.UUID, current_user: User
) -> tuple[Project | None, str | None]:
    project = await get_project_by_id(db, project_id)
    if not project:
        return None, "Project not found"

    if current_user.role == UserRole.ADMIN:
        return project, None

    member = await get_project_member(db, project_id, current_user.id)
    if not member:
        return None, "You do not have access to this project"

    return project, None


async def update_project_for_user(
    db: AsyncSession,
    project_id: uuid.UUID,
    current_user: User,
    data: ProjectUpdate,
) -> tuple[Project | None, str | None]:
    project, error = await get_project_for_user(db, project_id, current_user)
    if error:
        return None, error

    return await update_project(db, project, data), None


async def delete_project_for_owner(
    db: AsyncSession, project_id: uuid.UUID, owner_id: uuid.UUID
) -> str | None:
    project = await get_project_by_id(db, project_id)
    if not project:
        return "Project not found"

    if project.owner_id != owner_id:
        return "Only the project owner can delete this project"

    await soft_delete_project(db, project)
    return None


async def get_project_member(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> ProjectMember | None:
    return await project_repository.get_project_member(db, project_id, user_id)


async def add_member(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    role: MemberRole,
) -> ProjectMember:
    return await project_repository.create_project_member(
        db,
        project_id=project_id,
        user_id=user_id,
        role=role,
    )


async def get_project_members(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[MemberResponse]:
    rows = await project_repository.get_project_members_with_users(db, project_id)

    return [_member_response(member, user) for member, user in rows]


async def add_project_member(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    role: MemberRole,
) -> tuple[MemberResponse | None, str | None]:
    project = await get_project_by_id(db, project_id)
    if not project:
        return None, "Project not found"

    target_user = await get_user_by_id(db, user_id)
    if not target_user:
        return None, "User not found"

    existing = await get_project_member(db, project_id, user_id)
    if existing:
        return None, "User is already a member of this project"

    member = await add_member(db, project_id, user_id, role)
    return _member_response(member, target_user), None


async def get_project_members_for_project(
    db: AsyncSession, project_id: uuid.UUID
) -> tuple[list[MemberResponse] | None, str | None]:
    project = await get_project_by_id(db, project_id)
    if not project:
        return None, "Project not found"

    return await get_project_members(db, project_id), None


async def remove_member(db: AsyncSession, member: ProjectMember) -> None:
    await project_repository.delete_project_member(db, member)


async def remove_project_member(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> str | None:
    project = await get_project_by_id(db, project_id)
    if not project:
        return "Project not found"

    if user_id == project.owner_id:
        return "Cannot remove the project owner"

    member = await get_project_member(db, project_id, user_id)
    if not member:
        return "User is not a member of this project"

    await remove_member(db, member)
    return None


async def change_member_role(
    db: AsyncSession, member: ProjectMember, role: MemberRole
) -> ProjectMember:
    member.role = role
    return await project_repository.save_project_member(db, member)


async def change_project_member_role(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    role: MemberRole,
) -> tuple[MemberResponse | None, str | None]:
    project = await get_project_by_id(db, project_id)
    if not project:
        return None, "Project not found"

    if user_id == project.owner_id:
        return None, "Cannot change the project owner's role"

    member = await get_project_member(db, project_id, user_id)
    if not member:
        return None, "User is not a member of this project"

    user = await get_user_by_id(db, user_id)
    if not user:
        return None, "User not found"

    updated = await change_member_role(db, member, role)
    return _member_response(updated, user), None


async def archive_project_by_id(
    db: AsyncSession, project_id: uuid.UUID
) -> tuple[Project | None, str | None]:
    project = await get_project_by_id(db, project_id)
    if not project:
        return None, "Project not found"

    if project.status == ProjectStatus.ARCHIVED:
        return None, "Project is already archived"
    project.status = ProjectStatus.ARCHIVED
    return await project_repository.save_project(db, project), None


async def unarchive_project_by_id(
    db: AsyncSession, project_id: uuid.UUID
) -> tuple[Project | None, str | None]:
    project = await get_project_by_id(db, project_id)
    if not project:
        return None, "Project not found"

    if project.status != ProjectStatus.ARCHIVED:
        return None, "Project unarchived"

    project.status = ProjectStatus.ACTIVE
    return await project_repository.save_project(db, project), None


async def soft_delete_project(
    db: AsyncSession,
    project: Project,
) -> None:
    project.is_deleted = True
    project.deleted_at = datetime.now(timezone.utc)
    await project_repository.save_changes(db)
