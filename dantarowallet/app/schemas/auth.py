"""
인증 관련 스키마 모듈.
회원가입, 로그인, 토큰, 비밀번호 변경 등의 스키마를 정의합니다.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    """회원가입 요청 스키마"""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    password_confirm: str

    @field_validator("password_confirm")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("비밀번호가 일치하지 않습니다")
        return v


class UserLogin(BaseModel):
    """로그인 요청 스키마"""

    email: EmailStr
    password: str


class Token(BaseModel):
    """토큰 응답 스키마"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenRefresh(BaseModel):
    """토큰 갱신 요청 스키마"""

    refresh_token: str


class UserResponse(BaseModel):
    """사용자 응답 스키마"""

    id: int
    email: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """비밀번호 변경 요청 스키마"""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    new_password_confirm: str

    @field_validator("new_password_confirm")
    @classmethod
    def passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("새 비밀번호가 일치하지 않습니다")
        return v


class PasswordReset(BaseModel):
    """비밀번호 재설정 요청 스키마"""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """비밀번호 재설정 확인 스키마"""

    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
