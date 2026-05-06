from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import MemberRole


class AddMemberRequest(BaseModel):
    user_id: UUID
    role: MemberRole = MemberRole.VIEWER


class MemberRoleUpdate(BaseModel):
    role: MemberRole


class MemberResponse(BaseModel):
    user_id: UUID
    full_name: str
    email: str
    role: MemberRole
    joined_at: datetime

    model_config = {"from_attributes": True}
