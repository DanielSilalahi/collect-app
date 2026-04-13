from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: int
    name: str
    username: str
    role: str
    phone: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class UpdateFcmTokenRequest(BaseModel):
    fcm_token: str


class CreateUserRequest(BaseModel):
    name: str
    username: str
    password: str
    role: str = "agent"
    phone: Optional[str] = None


TokenResponse.model_rebuild()
