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
from app.models.partner import Partner
from app.models.system_admin import SuperAdminUser
from app.schemas.auth import (
    PasswordChange,
    Token,
    TokenRefresh,
    UserLogin,
    UserRegister,
    UserResponse,
)
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select, update
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

    if not user or not verify_password(user_data.password, str(user.password_hash)):
        raise AuthenticationError("이메일 또는 비밀번호가 올바르지 않습니다")

    if not bool(user.is_active):
        raise AuthenticationError("비활성화된 계정입니다")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
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
        token_type="bearer",
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
    if not verify_password(password_data.current_password, str(current_user.password_hash)):
        raise AuthenticationError("현재 비밀번호가 올바르지 않습니다")

    is_valid, message = validate_password_strength(password_data.new_password)
    if not is_valid:
        raise ValidationError(message)

    # SQLAlchemy 세션을 통해 업데이트
    await db.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(password_hash=get_password_hash(password_data.new_password))
    )
    await db.commit()

    return {"message": "비밀번호가 성공적으로 변경되었습니다"}


@router.post("/super-admin/quick-login")
async def super_admin_quick_login(user_data: UserLogin):
    """
    슈퍼어드민 빠른 로그인 (테스트용)
    """
    if user_data.email == "admin@dantarowallet.com" and user_data.password == "Secret123!":
        return {
            "access_token": "fake_token_for_testing",
            "refresh_token": "fake_refresh_token",
            "token_type": "bearer",
            "expires_in": 3600
        }
    else:
        raise AuthenticationError("이메일 또는 비밀번호가 올바르지 않습니다")


@router.post("/super-admin/login", response_model=Token)
async def super_admin_login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    슈퍼어드민 로그인
    """
    logger.info(f"슈퍼어드민 로그인 시도: {user_data.email}")
    logger.info(f"받은 비밀번호 길이: {len(user_data.password)}")
    logger.info(f"받은 비밀번호 repr: {repr(user_data.password)}")
    
    result = await db.execute(
        select(SuperAdminUser).filter(SuperAdminUser.email == user_data.email)
    )
    admin = result.scalar_one_or_none()
    
    logger.info(f"사용자 조회 결과: {admin is not None}")
    
    if not admin:
        logger.warning(f"슈퍼어드민 사용자를 찾을 수 없음: {user_data.email}")
        raise AuthenticationError("이메일 또는 비밀번호가 올바르지 않습니다")
    
    logger.info(f"DB 해시: {admin.hashed_password}")
    logger.info(f"비밀번호 검증 시작")
    
    # bcrypt 비밀번호 검증 (보안 강화)
    from app.core.security import verify_password
    password_valid = verify_password(user_data.password, str(admin.hashed_password))
    logger.info(f"비밀번호 검증 결과: {password_valid}")
    
    if not password_valid:
        logger.warning(f"잘못된 비밀번호: {user_data.email}")
        raise AuthenticationError("이메일 또는 비밀번호가 올바르지 않습니다")

    if not bool(admin.is_active):
        logger.warning(f"비활성화된 계정: {user_data.email}")
        raise AuthenticationError("비활성화된 계정입니다")

    # JWT 토큰 생성 (슈퍼어드민용)
    access_token = create_access_token(
        data={"sub": str(admin.email), "type": "super_admin", "admin_id": str(admin.id)}
    )

    refresh_token = create_refresh_token(
        data={"sub": str(admin.email), "type": "refresh", "admin_id": str(admin.id)}
    )

    logger.info(f"토큰 생성 완료")
    
    # 로그인 시간 업데이트 (간단하게 처리)
    from sqlalchemy import update
    await db.execute(
        update(SuperAdminUser)
        .where(SuperAdminUser.id == admin.id)
        .values(last_login_at=datetime.utcnow())
    )
    await db.commit()

    logger.info(f"슈퍼어드민 로그인: {admin.email}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


# === 사용자 유형별 로그인 엔드포인트 ===

@router.post("/partner/login", response_model=Token)
async def partner_login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    파트너어드민 로그인
    파트너사 직원/관리자 전용 로그인
    """
    # 사용자 인증
    result = await db.execute(select(User).filter(User.email == user_data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_data.password, str(user.password_hash)):
        raise AuthenticationError("이메일 또는 비밀번호가 올바르지 않습니다")

    if not bool(user.is_active):
        raise AuthenticationError("비활성화된 계정입니다")

    # TODO: 파트너 소속 확인
    # user.partner_id가 있는지 확인
    
    # 임시로 test_partner_001 파트너에 속한다고 가정
    partner_id = "test_partner_001"
    
    # 파트너 존재 확인
    result = await db.execute(select(Partner).where(Partner.id == partner_id))
    partner = result.scalar_one_or_none()
    
    if not partner:
        raise AuthenticationError("소속 파트너를 찾을 수 없습니다")

    # 파트너 정보를 포함한 토큰 생성
    access_token = create_access_token({
        "sub": str(user.id),
        "user_type": "partner_admin",
        "partner_id": partner_id,
        "partner_name": partner.name
    })
    refresh_token = create_refresh_token({
        "sub": str(user.id),
        "user_type": "partner_admin", 
        "partner_id": partner_id
    })

    logger.info(f"파트너어드민 로그인 성공: {user.email} (파트너: {partner.name})")

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/user/login", response_model=Token)  
async def user_login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    일반 사용자 로그인
    최종 고객 전용 로그인
    """
    # 사용자 인증
    result = await db.execute(select(User).filter(User.email == user_data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_data.password, str(user.password_hash)):
        raise AuthenticationError("이메일 또는 비밀번호가 올바르지 않습니다")

    if not bool(user.is_active):
        raise AuthenticationError("비활성화된 계정입니다")

    # 관리자가 아닌 일반 사용자만 허용
    if bool(user.is_admin):
        raise AuthenticationError("일반 사용자 로그인을 이용해주세요")

    # 일반 사용자 토큰 생성
    access_token = create_access_token({
        "sub": str(user.id),
        "user_type": "end_user"
    })
    refresh_token = create_refresh_token({
        "sub": str(user.id),
        "user_type": "end_user"
    })

    logger.info(f"일반 사용자 로그인 성공: {user.email}")

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/test")
async def test_endpoint():
    """테스트 엔드포인트"""
    return {"message": "OK", "status": "working"}
