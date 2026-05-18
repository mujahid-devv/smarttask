import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.comment import Comment


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
    *,
    author_id: uuid.UUID,
    body: str,
    parent_id: uuid.UUID | None,
    task_id: uuid.UUID | None,
    project_id: uuid.UUID | None,
) -> Comment:
    comment = Comment(
        author_id=author_id,
        task_id=task_id,
        project_id=project_id,
        parent_id=parent_id,
        body=body,
    )
    db.add(comment)
    await db.flush()
    return comment


async def get_comment_with_author(
    db: AsyncSession,
    comment_id: uuid.UUID,
) -> Comment:
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.author))
        .where(Comment.id == comment_id)
    )
    return result.scalar_one()


async def get_replies(
    db: AsyncSession,
    comment_id: uuid.UUID,
) -> list[Comment]:
    """Return direct replies for one comment."""
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.author))
        .where(
            Comment.parent_id == comment_id,
            Comment.is_deleted.is_(False),
        )
        .order_by(Comment.created_at.asc())
    )
    return list(result.scalars().all())


async def get_top_level_comments(
    db: AsyncSession,
    *,
    task_id: uuid.UUID | None,
    project_id: uuid.UUID | None,
) -> list[Comment]:
    """Return root comments for a task or project."""
    result = await db.execute(
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
    return list(result.scalars().all())


async def get_replies_for_comments(
    db: AsyncSession,
    *,
    parent_ids: list[uuid.UUID],
    task_id: uuid.UUID | None,
    project_id: uuid.UUID | None,
) -> list[Comment]:
    """Return replies for multiple parent comments."""
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.author))
        .where(
            Comment.task_id == task_id,
            Comment.project_id == project_id,
            Comment.parent_id.in_(parent_ids),
            Comment.is_deleted.is_(False),
        )
        .order_by(Comment.created_at.asc())
    )
    return list(result.scalars().all())


async def save_comment(db: AsyncSession, comment: Comment) -> None:
    await db.flush()


async def save_changes(db: AsyncSession) -> None:
    await db.flush()
