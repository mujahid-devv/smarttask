from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.models.enums import ProjectStatus


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    tags: list[str] | None = None
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("end_date", mode="after")
    @classmethod
    def end_after_start(cls, end_date, info):
        start = info.data.get("start_date")
        if start and end_date and end_date < start:
            raise ValueError("end_date must be on or after start_date")
        return end_date


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None
    tags: list[str] | None = None
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("end_date", mode="after")
    @classmethod
    def end_after_start(cls, end_date, info):
        start = info.data.get("start_date")
        if start and end_date and end_date < start:
            raise ValueError("end_date must be on or after start_date")
        return end_date


class ProjectResponse(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    description: str | None
    status: ProjectStatus
    tags: list[str] | None
    start_date: date | None
    end_date: date | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
