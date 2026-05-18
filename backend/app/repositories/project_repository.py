import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, ProjectMember, User
from app.models.enums import MemberRole, ProjectStatus


async def get_project_by_id(db: AsyncSession, project_id: uuid.UUID) -> Project | None:
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.is_deleted == False,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def get_user_projects(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    skip: int,
    limit: int,
    include_archived: bool,
) -> list[Project]:
    query = (
        select(Project)
        .join(ProjectMember, Project.id == ProjectMember.project_id)
        .where(
            ProjectMember.user_id == user_id,
            Project.is_deleted == False,  # noqa: E712
        )
    )

    if not include_archived:
        query = query.where(Project.status != ProjectStatus.ARCHIVED)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_project(
    db: AsyncSession,
    *,
    owner_id: uuid.UUID,
    name: str,
    description: str | None,
    status: ProjectStatus,
    tags: list[str] | None,
    start_date,
    end_date,
) -> Project:
    project = Project(
        owner_id=owner_id,
        name=name,
        description=description,
        status=status,
        tags=tags,
        start_date=start_date,
        end_date=end_date,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


async def save_project(db: AsyncSession, project: Project) -> Project:
    project.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(project)
    return project


async def get_project_member(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> ProjectMember | None:
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def create_project_member(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    role: MemberRole,
) -> ProjectMember:
    member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
    db.add(member)
    await db.flush()
    await db.refresh(member)
    return member


async def get_project_members_with_users(
    db: AsyncSession, project_id: uuid.UUID
) -> list[tuple[ProjectMember, User]]:
    result = await db.execute(
        select(ProjectMember, User)
        .join(User, ProjectMember.user_id == User.id)
        .where(
            ProjectMember.project_id == project_id,
            User.is_deleted.is_(False),
        )
    )
    return list(result.all())


async def save_project_member(db: AsyncSession, member: ProjectMember) -> ProjectMember:
    await db.flush()
    await db.refresh(member)
    return member


async def delete_project_member(db: AsyncSession, member: ProjectMember) -> None:
    await db.delete(member)
    await db.flush()


async def save_changes(db: AsyncSession) -> None:
    await db.flush()
