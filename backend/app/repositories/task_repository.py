import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TaskPriority, TaskStatus
from app.models.task import Task


async def create_task(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str,
    description: str | None,
    status: TaskStatus,
    priority: TaskPriority,
    due_date,
) -> Task:
    task = Task(
        project_id=project_id,
        created_by=user_id,
        title=title,
        description=description,
        status=status,
        priority=priority,
        due_date=due_date,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def get_task_by_id(
    db: AsyncSession,
    *,
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
    *,
    project_id: uuid.UUID,
    skip: int,
    limit: int,
    status: TaskStatus | None,
    priority: TaskPriority | None,
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


async def save_task(db: AsyncSession, task: Task) -> Task:
    task.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(task)
    return task


async def save_changes(db: AsyncSession) -> None:
    await db.flush()
