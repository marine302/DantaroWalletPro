"""
보안 관련 유틸리티 모듈.
JWT 토큰 생성 및 검증, 비밀번호 해싱 및 검증 기능을 제공합니다.
"""
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 설정
ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(data: Dict[str, Any]) -> str:
    """
    액세스 토큰 생성

    Args:
        data: 토큰에 포함할 데이터 (sub 필드에 사용자 ID 포함 필요)

    Returns:
        str: 인코딩된 JWT 토큰
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    리프레시 토큰 생성

    Args:
        data: 토큰에 포함할 데이터 (sub 필드에 사용자 ID 포함 필요)

    Returns:
        str: 인코딩된 JWT 토큰
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update(
        {
            "exp": expire,
            "type": "refresh",
            "jti": secrets.token_urlsafe(32),  # JWT ID for revocation
        }
    )
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    토큰 검증

    Args:
        token: 검증할 JWT 토큰
        token_type: 토큰 타입 ("access" 또는 "refresh")

    Returns:
        Optional[Dict[str, Any]]: 검증 성공시 페이로드, 실패시 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    비밀번호 검증

    Args:
        plain_password: 평문 비밀번호
        hashed_password: 해시된 비밀번호

    Returns:
        bool: 일치 여부
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    비밀번호 해싱

    Args:
        password: 평문 비밀번호

    Returns:
        str: 해시된 비밀번호
    """
    return pwd_context.hash(password)


def generate_verification_token() -> str:
    """
    이메일 인증 토큰 생성

    Returns:
        str: 랜덤 토큰
    """
    return secrets.token_urlsafe(32)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    비밀번호 강도 검증

    Args:
        password: 검증할 비밀번호

    Returns:
        tuple[bool, str]: (유효성 여부, 메시지)
    """
    if len(password) < 8:
        return False, "비밀번호는 최소 8자 이상이어야 합니다"

    if not any(char.isdigit() for char in password):
        return False, "비밀번호는 최소 하나의 숫자를 포함해야 합니다"

    if not any(char.isupper() for char in password):
        return False, "비밀번호는 최소 하나의 대문자를 포함해야 합니다"

    if not any(char.islower() for char in password):
        return False, "비밀번호는 최소 하나의 소문자를 포함해야 합니다"

    if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in password):
        return False, "비밀번호는 최소 하나의 특수문자를 포함해야 합니다"

    return True, "비밀번호가 유효합니다"
