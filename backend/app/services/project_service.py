import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, ProjectMember, User
from app.models.enums import MemberRole
from app.schemas.member import MemberResponse
from app.schemas.project import ProjectCreate, ProjectUpdate


async def get_project_by_id(db: AsyncSession, project_id: uuid.UUID) -> Project | None:

    result = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.is_deleted == False  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def get_all_projects(
    db: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 10
) -> list[Project]:
    """
    Get all projects for a user where they are a member.
    """
    query = (
        select(Project)
        .join(ProjectMember, Project.id == ProjectMember.project_id)
        .where(
            ProjectMember.user_id == user_id, Project.is_deleted == False  # noqa: E712
        )  # noqa:E712
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_project(
    db: AsyncSession,
    owner_id: uuid.UUID,
    data: ProjectCreate,
) -> Project:
    project = Project(
        owner_id=owner_id,
        name=data.name,
        description=data.description,
        status=data.status,
        tags=data.tags,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    db.add(project)
    await db.flush()

    member = ProjectMember(
        project_id=project.id,
        user_id=owner_id,
        role=MemberRole.OWNER,
    )
    db.add(member)
    await db.flush()

    await db.refresh(project)
    return project


async def update_project(
    db: AsyncSession,
    project: Project,
    data: ProjectUpdate,
) -> Project:
    """Update only the fields that were explicitly sent in the request."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

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


async def add_member(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    role: MemberRole,
) -> ProjectMember:
    member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
    db.add(member)
    await db.flush()
    await db.refresh(member)
    return member


async def get_project_members(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[MemberResponse]:
    result = await db.execute(
        select(ProjectMember, User)
        .join(User, ProjectMember.user_id == User.id)
        .where(
            ProjectMember.project_id == project_id,
            User.is_deleted.is_(False),
        )
    )

    return [
        MemberResponse(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            role=member.role,
            joined_at=member.created_at,
        )
        for member, user in result.all()
    ]


async def remove_member(db: AsyncSession, member: ProjectMember) -> None:
    await db.delete(member)
    await db.flush()


async def change_member_role(
    db: AsyncSession, member: ProjectMember, role: MemberRole
) -> ProjectMember:
    member.role = role
    await db.flush()
    await db.refresh(member)
    return member


async def soft_delete_project(
    db: AsyncSession,
    project: Project,
) -> None:
    project.is_deleted = True
    project.deleted_at = datetime.now(timezone.utc)
    await db.flush()
