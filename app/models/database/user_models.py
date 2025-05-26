import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("password")
    def validate_password(cls, v):
        if not re.match(
            r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$", v
        ):
            raise ValueError(
                "Password must contain at least 8 characters, "
                "including one letter, one number, and one special character"
            )
        return v


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    is_active: bool
    is_verified: bool
    last_login: datetime | None
    is_superuser: bool
    role: str | None
    brain_name: str | None
    brain_id: str | None
    xero_authenticated: bool | None = None
    active_tenant_id: str | None = None

    class Config:
        from_attributes = True
