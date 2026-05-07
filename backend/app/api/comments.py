import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.projects import require_project_role
from app.models import ProjectMember
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentResponse, CommentUpdate
from app.services.comment_service import (
    create_comment,
    delete_comment,
    edit_comment,
    get_comment_by_id,
    get_comment_thread,
    get_comments,
)
from app.services.task_service import get_task_by_id

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
    task = await get_task_by_id(db, task_id, project_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")

    if data.parent_id:
        parent = await get_comment_by_id(db, data.parent_id)
        if not parent:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Parent comment not found")
        if parent.parent_id is not None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot reply to a reply")
        if parent.task_id != task_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Parent comment does not belong to this task")

    return await create_comment(db, current_user.id, data, task_id=task_id)


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
    comment = await get_comment_by_id(db, comment_id)
    if not comment or comment.task_id != task_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")

    if comment.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only edit your own comments")

    return await edit_comment(db, comment, data)


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
    comment = await get_comment_by_id(db, comment_id)
    if not comment or comment.task_id != task_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")

    if comment.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only delete your own comments")

    await delete_comment(db, comment)


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
    thread = await get_comment_thread(db, comment_id)
    if not thread or thread.task_id != task_id:
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
    if data.parent_id:
        parent = await get_comment_by_id(db, data.parent_id)
        if not parent:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Parent comment not found")
        if parent.parent_id is not None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot reply to a reply")
        if parent.project_id != project_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Parent comment does not belong to this project")

    return await create_comment(db, current_user.id, data, project_id=project_id)


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
    comment = await get_comment_by_id(db, comment_id)
    if not comment or comment.project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")

    if comment.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only edit your own comments")

    return await edit_comment(db, comment, data)


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
    comment = await get_comment_by_id(db, comment_id)
    if not comment or comment.project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")

    if comment.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only delete your own comments")

    await delete_comment(db, comment)


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
    thread = await get_comment_thread(db, comment_id)
    if not thread or thread.project_id != project_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
    return thread
