import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.projects import require_project_role
from app.models import ProjectMember, User
from app.models.enums import MemberRole, TaskPriority, TaskStatus
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.task_service import (
    create_task,
    get_project_tasks,
    get_task_by_id,
    soft_delete_task,
    update_task,
)

router = APIRouter()


# Create task


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_new_task(
    project_id: uuid.UUID,
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember | None = Depends(require_project_role()),
    current_user: User = Depends(get_current_user),
):
    """task within a project. Any project member can create tasks."""
    return await create_task(
        db=db, project_id=project_id, user_id=current_user.id, data=data
    )


#  List tasks


@router.get("/", response_model=list[TaskResponse])
async def list_tasks(
    project_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    task_status: TaskStatus | None = Query(None, alias="status"),
    priority: TaskPriority | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: ProjectMember | None = Depends(require_project_role()),
):
    return await get_project_tasks(
        db=db,
        project_id=project_id,
        skip=skip,
        limit=limit,
        status=task_status,
        priority=priority,
    )


#  Get single task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember | None = Depends(require_project_role()),
):
    task = await get_task_by_id(db, task_id=task_id, project_id=project_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return task


#  Update task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task_route(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember | None = Depends(
        require_project_role(MemberRole.OWNER, MemberRole.EDITOR)
    ),
):
    """requires project OWNER or EDITOR role."""
    task = await get_task_by_id(db, task_id=task_id, project_id=project_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return await update_task(db, task, data)


#  Delete task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember | None = Depends(
        require_project_role(MemberRole.OWNER, MemberRole.EDITOR)
    ),
):
    """requires project OWNER, EDITOR/system-admin role"""
    task = await get_task_by_id(db, task_id=task_id, project_id=project_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    await soft_delete_task(db, task)
