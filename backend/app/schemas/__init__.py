"""Pydantic schemas package."""
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    MessageResponse,
)
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentDeleteResponse,
)

__all__ = [
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserResponse",
    "TokenResponse",
    "MessageResponse",
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentDeleteResponse",
]
