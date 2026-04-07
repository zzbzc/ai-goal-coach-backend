"""用户相关 Schemas"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """用户注册请求"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    verification_code: str = Field(..., min_length=6, max_length=6)


class UserCreateNoVerification(BaseModel):
    """用户注册请求（无验证码模式）"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class SendVerificationCodeRequest(BaseModel):
    """发送验证码请求"""
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    """验证邮箱请求"""
    email: EmailStr
    verification_code: str = Field(..., min_length=6, max_length=6)


class UserLogin(BaseModel):
    """用户登录请求"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """用户更新请求"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    avatar_url: Optional[str] = None


class UserResponse(BaseModel):
    """用户响应"""
    id: UUID
    email: str
    username: str
    avatar_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token 响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    """Token 解析内容"""
    sub: str  # user id
    exp: datetime
    type: str  # access or refresh


class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求"""
    refresh_token: str
