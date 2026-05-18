import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.projects import require_project_role
from app.models import ProjectMember
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentResponse, CommentUpdate
from app.services.comment_service import (
    create_project_comment as svc_create_project_comment,
)
from app.services.comment_service import create_task_comment as svc_create_task_comment
from app.services.comment_service import (
    delete_scoped_comment,
    edit_scoped_comment,
    get_comments,
)
from app.services.comment_service import (
    get_project_comment_thread as svc_get_project_comment_thread,
)
from app.services.comment_service import (
    get_task_comment_thread as svc_get_task_comment_thread,
)

router = APIRouter()


# Task comments


@router.post(
    "/projects/{project_id}/tasks/{task_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task_comment(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: ProjectMember | None = Depends(require_project_role()),
):
    comment, error = await svc_create_task_comment(
        db,
        project_id=project_id,
        task_id=task_id,
        current_user=current_user,
        data=data,
    )
    if error == "Task not found" or error == "Parent comment not found":
        raise HTTPException(status.HTTP_404_NOT_FOUND, error)
    if error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, error)

    return comment


@router.get(
    "/projects/{project_id}/tasks/{task_id}/comments",
    response_model=list[CommentResponse],
)
async def list_task_comments(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember | None = Depends(require_project_role()),
):
    return await get_comments(db, task_id=task_id)


@router.patch(
    "/projects/{project_id}/tasks/{task_id}/comments/{comment_id}",
    response_model=CommentResponse,
)
async def edit_task_comment(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    comment_id: uuid.UUID,
    data: CommentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: ProjectMember | None = Depends(require_project_role()),
):
    comment, error = await edit_scoped_comment(
        db,
        comment_id=comment_id,
        current_user=current_user,
        data=data,
        task_id=task_id,
    )
    if error == "Comment not found":
        raise HTTPException(status.HTTP_404_NOT_FOUND, error)
    if error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, error)

    return comment


@router.delete(
    "/projects/{project_id}/tasks/{task_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task_comment(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: ProjectMember | None = Depends(require_project_role()),
):
    error = await delete_scoped_comment(
        db,
        comment_id=comment_id,
        current_user=current_user,
        task_id=task_id,
    )
    if error == "Comment not found":
        raise HTTPException(status.HTTP_404_NOT_FOUND, error)
    if error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, error)


@router.get(
    "/projects/{project_id}/tasks/{task_id}/comments/{comment_id}",
    response_model=CommentResponse,
)
async def get_task_comment_thread(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember | None = Depends(require_project_role()),
):
    thread = await svc_get_task_comment_thread(db, comment_id, task_id)
    if not thread:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
    return thread


#  Project comments


@router.post(
    "/projects/{project_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project_comment(
    project_id: uuid.UUID,
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: ProjectMember | None = Depends(require_project_role()),
):
    comment, error = await svc_create_project_comment(
        db,
        project_id=project_id,
        current_user=current_user,
        data=data,
    )
    if error == "Parent comment not found":
        raise HTTPException(status.HTTP_404_NOT_FOUND, error)
    if error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, error)

    return comment


@router.get(
    "/projects/{project_id}/comments",
    response_model=list[CommentResponse],
)
async def list_project_comments(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember | None = Depends(require_project_role()),
):
    return await get_comments(db, project_id=project_id)


@router.patch(
    "/projects/{project_id}/comments/{comment_id}",
    response_model=CommentResponse,
)
async def edit_project_comment(
    project_id: uuid.UUID,
    comment_id: uuid.UUID,
    data: CommentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: ProjectMember | None = Depends(require_project_role()),
):
    comment, error = await edit_scoped_comment(
        db,
        comment_id=comment_id,
        current_user=current_user,
        data=data,
        project_id=project_id,
    )
    if error == "Comment not found":
        raise HTTPException(status.HTTP_404_NOT_FOUND, error)
    if error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, error)

    return comment


@router.delete(
    "/projects/{project_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project_comment(
    project_id: uuid.UUID,
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: ProjectMember | None = Depends(require_project_role()),
):
    error = await delete_scoped_comment(
        db,
        comment_id=comment_id,
        current_user=current_user,
        project_id=project_id,
    )
    if error == "Comment not found":
        raise HTTPException(status.HTTP_404_NOT_FOUND, error)
    if error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, error)


@router.get(
    "/projects/{project_id}/comments/{comment_id}",
    response_model=CommentResponse,
)
async def get_project_comment_thread(
    project_id: uuid.UUID,
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember | None = Depends(require_project_role()),
):
    thread = await svc_get_project_comment_thread(db, comment_id, project_id)
    if not thread:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
    return thread
