import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.models.enums import UserRole
from app.models.user import User
from app.repositories import comment_repository
from app.schemas.comment import CommentCreate, CommentResponse, CommentUpdate
from app.services.task_service import get_task_by_id


def _to_response(
    comment: Comment, replies: list[CommentResponse] = []
) -> CommentResponse:
    return CommentResponse(
        id=comment.id,
        author_id=comment.author_id,
        author_name=comment.author.full_name,
        parent_id=comment.parent_id,
        body=comment.body,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        replies=replies,
    )


async def get_comment_by_id(
    db: AsyncSession,
    comment_id: uuid.UUID,
) -> Comment | None:
    return await comment_repository.get_comment_by_id(db, comment_id)


async def create_comment(
    db: AsyncSession,
    author_id: uuid.UUID,
    data: CommentCreate,
    *,
    task_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
) -> CommentResponse:
    comment = await comment_repository.create_comment(
        db,
        author_id=author_id,
        task_id=task_id,
        project_id=project_id,
        parent_id=data.parent_id,
        body=data.body,
    )
    comment = await comment_repository.get_comment_with_author(db, comment.id)
    return _to_response(comment, replies=[])


async def create_task_comment(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: User,
    data: CommentCreate,
) -> tuple[CommentResponse | None, str | None]:
    task = await get_task_by_id(db, task_id, project_id)
    if not task:
        return None, "Task not found"

    if data.parent_id:
        parent_error = await validate_parent_comment(
            db, data.parent_id, task_id=task_id, project_id=None
        )
        if parent_error:
            return None, parent_error

    return await create_comment(db, current_user.id, data, task_id=task_id), None


async def create_project_comment(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    current_user: User,
    data: CommentCreate,
) -> tuple[CommentResponse | None, str | None]:
    if data.parent_id:
        parent_error = await validate_parent_comment(
            db, data.parent_id, task_id=None, project_id=project_id
        )
        if parent_error:
            return None, parent_error

    return await create_comment(db, current_user.id, data, project_id=project_id), None


async def validate_parent_comment(
    db: AsyncSession,
    parent_id: uuid.UUID,
    *,
    task_id: uuid.UUID | None,
    project_id: uuid.UUID | None,
) -> str | None:
    parent = await get_comment_by_id(db, parent_id)
    if not parent:
        return "Parent comment not found"
    if parent.parent_id is not None:
        return "Cannot reply to a reply"
    if task_id is not None and parent.task_id != task_id:
        return "Parent comment does not belong to this task"
    if project_id is not None and parent.project_id != project_id:
        return "Parent comment does not belong to this project"
    return None


async def get_comment_thread(
    db: AsyncSession,
    comment_id: uuid.UUID,
) -> CommentResponse | None:
    parent = await get_comment_by_id(db, comment_id)
    if not parent:
        return None

    replies = [
        _to_response(reply)
        for reply in await comment_repository.get_replies(db, comment_id)
    ]
    return _to_response(parent, replies=replies)


async def get_task_comment_thread(
    db: AsyncSession, comment_id: uuid.UUID, task_id: uuid.UUID
) -> CommentResponse | None:
    parent = await get_comment_by_id(db, comment_id)
    if not parent or parent.task_id != task_id:
        return None

    replies = [
        _to_response(reply)
        for reply in await comment_repository.get_replies(db, comment_id)
    ]
    return _to_response(parent, replies=replies)


async def get_project_comment_thread(
    db: AsyncSession, comment_id: uuid.UUID, project_id: uuid.UUID
) -> CommentResponse | None:
    parent = await get_comment_by_id(db, comment_id)
    if not parent or parent.project_id != project_id:
        return None

    replies = [
        _to_response(reply)
        for reply in await comment_repository.get_replies(db, comment_id)
    ]
    return _to_response(parent, replies=replies)


async def get_comments(
    db: AsyncSession,
    *,
    task_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
) -> list[CommentResponse]:
    top_level = await comment_repository.get_top_level_comments(
        db,
        task_id=task_id,
        project_id=project_id,
    )

    if not top_level:
        return []

    top_level_ids = [c.id for c in top_level]
    replies = await comment_repository.get_replies_for_comments(
        db,
        parent_ids=top_level_ids,
        task_id=task_id,
        project_id=project_id,
    )

    replies_map: dict[uuid.UUID, list[CommentResponse]] = {}
    for reply in replies:
        replies_map.setdefault(reply.parent_id, []).append(_to_response(reply))

    return [_to_response(c, replies_map.get(c.id, [])) for c in top_level]


async def edit_comment(
    db: AsyncSession,
    comment: Comment,
    data: CommentUpdate,
) -> CommentResponse:
    comment.body = data.body
    comment.updated_at = datetime.now(timezone.utc)
    await comment_repository.save_comment(db, comment)

    comment = await comment_repository.get_comment_with_author(db, comment.id)
    return _to_response(comment, replies=[])


async def edit_scoped_comment(
    db: AsyncSession,
    *,
    comment_id: uuid.UUID,
    current_user: User,
    data: CommentUpdate,
    task_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
) -> tuple[CommentResponse | None, str | None]:
    comment = await get_comment_by_id(db, comment_id)
    if not comment:
        return None, "Comment not found"
    if task_id is not None and comment.task_id != task_id:
        return None, "Comment not found"
    if project_id is not None and comment.project_id != project_id:
        return None, "Comment not found"
    if comment.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        return None, "You can only edit your own comments"

    return await edit_comment(db, comment, data), None


async def delete_comment(db: AsyncSession, comment: Comment) -> None:
    now = datetime.now(timezone.utc)

    if comment.parent_id is None:
        replies = await comment_repository.get_replies(db, comment.id)
        for reply in replies:
            reply.is_deleted = True
            reply.deleted_at = now

    comment.is_deleted = True
    comment.deleted_at = now
    await comment_repository.save_changes(db)


async def delete_scoped_comment(
    db: AsyncSession,
    *,
    comment_id: uuid.UUID,
    current_user: User,
    task_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
) -> str | None:
    comment = await get_comment_by_id(db, comment_id)
    if not comment:
        return "Comment not found"
    if task_id is not None and comment.task_id != task_id:
        return "Comment not found"
    if project_id is not None and comment.project_id != project_id:
        return "Comment not found"
    if comment.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        return "You can only delete your own comments"

    await delete_comment(db, comment)
    return None
