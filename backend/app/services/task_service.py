import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TaskPriority, TaskStatus
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


async def create_task(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    data: TaskCreate,
) -> Task:
    """Create a new task within a project"""
    task = Task(
        project_id=project_id,
        created_by=user_id,
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
        due_date=data.due_date,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def get_task_by_id(
    db: AsyncSession,
    task_id: uuid.UUID,
    project_id: uuid.UUID,
) -> Task | None:
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.project_id == project_id,
            Task.is_deleted.is_(False),
        )
    )
    return result.scalar_one_or_none()


async def get_project_tasks(
    db: AsyncSession,
    project_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
) -> list[Task]:
    query = select(Task).where(
        Task.project_id == project_id,
        Task.is_deleted.is_(False),
    )

    if status is not None:
        query = query.where(Task.status == status)
    if priority is not None:
        query = query.where(Task.priority == priority)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_task(
    db: AsyncSession,
    task: Task,
    data: TaskUpdate,
) -> Task:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    task.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(task)
    return task


async def soft_delete_task(
    db: AsyncSession,
    task: Task,
) -> None:
    task.is_deleted = True
    task.deleted_at = datetime.now(timezone.utc)
    await db.flush()
