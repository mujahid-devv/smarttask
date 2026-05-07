import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentResponse, CommentUpdate


def _to_response(comment: Comment, replies: list[CommentResponse] = []) -> CommentResponse:
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
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.author))
        .where(
            Comment.id == comment_id,
            Comment.is_deleted.is_(False),
        )
    )
    return result.scalar_one_or_none()


async def create_comment(
    db: AsyncSession,
    author_id: uuid.UUID,
    data: CommentCreate,
    *,
    task_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
) -> CommentResponse:
    comment = Comment(
        author_id=author_id,
        task_id=task_id,
        project_id=project_id,
        parent_id=data.parent_id,
        body=data.body,
    )
    db.add(comment)
    await db.flush()

    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.author))
        .where(Comment.id == comment.id)
    )
    return _to_response(result.scalar_one(), replies=[])


async def get_comment_thread(
    db: AsyncSession,
    comment_id: uuid.UUID,
) -> CommentResponse | None:
    parent = await get_comment_by_id(db, comment_id)
    if not parent:
        return None

    replies_result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.author))
        .where(
            Comment.parent_id == comment_id,
            Comment.is_deleted.is_(False),
        )
        .order_by(Comment.created_at.asc())
    )
    replies = [_to_response(r) for r in replies_result.scalars().all()]
    return _to_response(parent, replies=replies)


async def get_comments(
    db: AsyncSession,
    *,
    task_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
) -> list[CommentResponse]:
    top_level_result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.author))
        .where(
            Comment.task_id == task_id,
            Comment.project_id == project_id,
            Comment.parent_id.is_(None),
            Comment.is_deleted.is_(False),
        )
        .order_by(Comment.created_at.asc())
    )
    top_level = list(top_level_result.scalars().all())

    if not top_level:
        return []

    top_level_ids = [c.id for c in top_level]
    replies_result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.author))
        .where(
            Comment.task_id == task_id,
            Comment.project_id == project_id,
            Comment.parent_id.in_(top_level_ids),
            Comment.is_deleted.is_(False),
        )
        .order_by(Comment.created_at.asc())
    )
    replies = list(replies_result.scalars().all())

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
    await db.flush()

    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.author))
        .where(Comment.id == comment.id)
    )
    return _to_response(result.scalar_one(), replies=[])


async def delete_comment(db: AsyncSession, comment: Comment) -> None:
    now = datetime.now(timezone.utc)

    if comment.parent_id is None:
        replies_result = await db.execute(
            select(Comment).where(
                Comment.parent_id == comment.id,
                Comment.is_deleted.is_(False),
            )
        )
        for reply in replies_result.scalars().all():
            reply.is_deleted = True
            reply.deleted_at = now

    comment.is_deleted = True
    comment.deleted_at = now
    await db.flush()
