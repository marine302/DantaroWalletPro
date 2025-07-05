"""
인증 관련 API 엔드포인트 모듈.
회원가입, 로그인, 토큰 갱신, 사용자 정보 조회 등의 기능을 제공합니다.
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict

from app.api import deps
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, ConflictError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    validate_password_strength,
    verify_password,
    verify_token,
)
from app.models.balance import Balance
from app.models.user import User
from app.schemas.auth import (
    PasswordChange,
    Token,
    TokenRefresh,
    UserLogin,
    UserRegister,
    UserResponse,
)
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserRegister,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    사용자 회원가입
    """
    # 이메일 중복 확인
    result = await db.execute(select(User).filter(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise ConflictError("이미 등록된 이메일입니다")

    # 비밀번호 강도 검증
    is_valid, message = validate_password_strength(user_data.password)
    if not is_valid:
        raise ValidationError(message)

    # 사용자 생성
    user = User(
        email=user_data.email, password_hash=get_password_hash(user_data.password)
    )
    db.add(user)
    await db.flush()

    # 기본 잔고 생성
    balance = Balance(
        user_id=user.id, asset="USDT", amount=Decimal("0"), locked_amount=Decimal("0")
    )
    db.add(balance)
    await db.commit()

    logger.info(f"새 사용자 등록: {user.email}")
    return user


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    사용자 로그인
    """
    result = await db.execute(select(User).filter(User.email == user_data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_data.password, user.password_hash):
        raise AuthenticationError("이메일 또는 비밀번호가 올바르지 않습니다")

    if not user.is_active:
        raise AuthenticationError("비활성화된 계정입니다")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh):
    """
    토큰 갱신
    """
    payload = verify_token(token_data.refresh_token, "refresh")
    if not payload:
        raise AuthenticationError("유효하지 않은 리프레시 토큰입니다")

    user_id = payload.get("sub")
    access_token = create_access_token({"sub": user_id})
    refresh_token = create_refresh_token({"sub": user_id})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: User = Depends(deps.get_current_active_user)):
    """
    현재 사용자 정보 조회
    """
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    비밀번호 변경
    """
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise AuthenticationError("현재 비밀번호가 올바르지 않습니다")

    is_valid, message = validate_password_strength(password_data.new_password)
    if not is_valid:
        raise ValidationError(message)

    current_user.password_hash = get_password_hash(password_data.new_password)
    await db.commit()

    return {"message": "비밀번호가 성공적으로 변경되었습니다"}
