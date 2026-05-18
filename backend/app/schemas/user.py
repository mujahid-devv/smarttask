from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, model_validator

from app.models.enums import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    detail: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    email: EmailStr
    otp: str
    new_password: str


class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    current_password: str | None = None
    new_password: str | None = None

    @model_validator(mode="after")
    def password_fields_consistent(self) -> "UserProfileUpdate":
        if self.new_password and not self.current_password:
            raise ValueError("current_password is required when setting a new password")
        return self


class UserRoleUpdate(BaseModel):
    role: UserRole
