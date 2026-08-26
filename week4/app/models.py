from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, field_validator


class AuthRequest(BaseModel):
    email: str
    password: str

    @field_validator("email", "password")
    @classmethod
    def check_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class UserResponse(BaseModel):
    id: str
    email: Optional[str] = None
    created_at: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
