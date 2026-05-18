from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CommentCreate(BaseModel):
    body: str
    parent_id: UUID | None = None


class CommentUpdate(BaseModel):
    body: str


class CommentResponse(BaseModel):
    id: UUID
    author_id: UUID
    author_name: str
    parent_id: UUID | None
    body: str
    created_at: datetime
    updated_at: datetime
    replies: list[CommentResponse] = []

    model_config = {"from_attributes": True}
