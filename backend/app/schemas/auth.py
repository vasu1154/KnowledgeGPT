from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ── Request Schemas ──

class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["Jaydeep"])
    email: EmailStr = Field(..., examples=["user@example.com"])
    password: str = Field(..., min_length=8, max_length=100)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Response Schemas ──

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    message: str
