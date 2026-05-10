import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TaskPriority, TaskStatus
from app.models.task import Task
from app.repositories import task_repository
from app.schemas.task import TaskCreate, TaskUpdate


async def create_task(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    data: TaskCreate,
) -> Task:
    return await task_repository.create_task(
        db,
        project_id=project_id,
        user_id=user_id,
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
        due_date=data.due_date,
    )


async def get_task_by_id(
    db: AsyncSession,
    task_id: uuid.UUID,
    project_id: uuid.UUID,
) -> Task | None:
    return await task_repository.get_task_by_id(
        db,
        task_id=task_id,
        project_id=project_id,
    )


async def get_project_tasks(
    db: AsyncSession,
    project_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
) -> list[Task]:
    return await task_repository.get_project_tasks(
        db,
        project_id=project_id,
        skip=skip,
        limit=limit,
        status=status,
        priority=priority,
    )


async def update_task(
    db: AsyncSession,
    task: Task,
    data: TaskUpdate,
) -> Task:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    return await task_repository.save_task(db, task)


async def update_task_by_id(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    data: TaskUpdate,
) -> Task | None:
    task = await get_task_by_id(db, task_id=task_id, project_id=project_id)
    if not task:
        return None

    return await update_task(db, task, data)


async def soft_delete_task(
    db: AsyncSession,
    task: Task,
) -> None:
    task.is_deleted = True
    task.deleted_at = datetime.now(timezone.utc)
    await task_repository.save_changes(db)


async def delete_task_by_id(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
) -> bool:
    task = await get_task_by_id(db, task_id=task_id, project_id=project_id)
    if not task:
        return False

    await soft_delete_task(db, task)
    return True
