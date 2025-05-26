import re
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_id: UUID
    xero: dict | None = None


class TokenData(BaseModel):
    email: str | None = None


class LoginCredentials(BaseModel):
    email: EmailStr
    password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator("new_password")
    def validate_password(cls, password):
        if not re.match(
            r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$", password
        ):
            raise ValueError(
                "Password must contain at least 8 characters, "
                "including one letter, one number, and one special character"
            )
        return password
