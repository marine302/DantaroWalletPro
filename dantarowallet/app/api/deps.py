"""
API 엔드포인트 의존성 모듈.
FastAPI 의존성 주입을 통해 인증 및 권한 체크를 제공합니다.
"""
from typing import Optional

from app.core.database import get_db
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import verify_token
from app.models.user import User
from app.models.partner import Partner
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Bearer 토큰 스키마 - auto_error=False로 설정하여 토큰이 없어도 예외를 발생시키지 않음
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    현재 인증된 사용자 가져오기

    Args:
        credentials: Bearer 토큰 인증 정보
        db: 데이터베이스 세션

    Returns:
        User: 인증된 현재 사용자 객체

    Raises:
        AuthenticationError: 인증 실패 시
    """
    if not credentials:
        raise AuthenticationError("인증 정보가 없습니다")

    token = credentials.credentials

    # 토큰 검증
    payload = verify_token(token, token_type="access")
    if not payload:
        raise AuthenticationError("유효하지 않은 인증 정보입니다")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("토큰에 사용자 식별자가 없습니다")

    # 사용자 조회
    result = await db.execute(select(User).filter(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError("사용자를 찾을 수 없습니다")

    if not bool(user.is_active):
        raise AuthenticationError("비활성화된 계정입니다")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    활성 사용자만 허용

    Args:
        current_user: 현재 인증된 사용자

    Returns:
        User: 활성화된 사용자 객체

    Raises:
        AuthorizationError: 사용자가 활성화되지 않은 경우
    """
    if not bool(current_user.is_active):
        raise AuthorizationError("비활성화된 계정입니다")
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    이메일이 인증된 사용자만 허용

    Args:
        current_user: 현재 인증된 활성 사용자

    Returns:
        User: 이메일이 인증된 사용자 객체

    Raises:
        AuthorizationError: 이메일이 인증되지 않은 경우
    """
    if not bool(current_user.is_verified):
        raise AuthorizationError("이메일이 인증되지 않았습니다")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    관리자만 허용

    Args:
        current_user: 현재 인증된 활성 사용자

    Returns:
        User: 관리자 권한이 있는 사용자 객체

    Raises:
        AuthorizationError: 관리자가 아닌 경우
    """
    if not bool(current_user.is_admin):
        raise AuthorizationError("관리자 권한이 없습니다")
    return current_user


# Optional user dependency (for public endpoints that may have auth)
async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    선택적 인증 - 인증되지 않아도 접근 가능

    Args:
        credentials: Bearer 토큰 인증 정보 (선택적)
        db: 데이터베이스 세션

    Returns:
        Optional[User]: 인증된 사용자 객체 또는 None
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except AuthenticationError:
        return None


async def get_current_partner(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Partner:
    """
    현재 인증된 파트너 반환
    """
    # 임시로 기본 파트너 반환 (실제로는 JWT 토큰에서 파트너 정보 추출)
    # TODO: JWT 토큰에서 파트너 ID 추출하여 실제 파트너 반환
    query = select(Partner).where(Partner.id == "test_partner_001")
    result = await db.execute(query)
    partner = result.scalar_one_or_none()

    if not partner:
        raise AuthenticationError("파트너를 찾을 수 없습니다")

    return partner


# === 개선된 사용자 유형별 인증 함수들 ===

async def get_current_super_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    슈퍼어드민만 허용
    전체 시스템 관리 권한이 있는 사용자
    """
    if not bool(current_user.is_admin):
        raise AuthorizationError("슈퍼어드민 권한이 없습니다")
    
    # TODO: 추가 슈퍼어드민 검증 로직
    # user_type이 'super_admin'인지 확인
    
    return current_user


async def get_current_partner_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> tuple[User, Partner]:
    """
    파트너어드민만 허용
    특정 파트너사의 관리 권한이 있는 사용자
    
    Returns:
        tuple[User, Partner]: (사용자, 소속 파트너) 튜플
    """
    if not credentials:
        raise AuthenticationError("인증 정보가 없습니다")

    token = credentials.credentials
    payload = verify_token(token, token_type="access")
    if not payload:
        raise AuthenticationError("유효하지 않은 인증 정보입니다")

    user_id = payload.get("sub")
    partner_id = payload.get("partner_id")  # JWT에서 파트너 ID 추출
    
    if not user_id:
        raise AuthenticationError("토큰에 사용자 식별자가 없습니다")
    
    if not partner_id:
        raise AuthorizationError("파트너 권한이 없습니다")

    # 사용자 조회
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise AuthenticationError("사용자를 찾을 수 없습니다")

    # 파트너 조회
    result = await db.execute(select(Partner).where(Partner.id == partner_id))
    partner = result.scalar_one_or_none()
    if not partner:
        raise AuthenticationError("파트너를 찾을 수 없습니다")

    return user, partner


async def get_current_end_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    일반 최종 사용자만 허용
    개인 지갑 및 에너지 사용 권한
    """
    # TODO: 사용자 유형이 'end_user'인지 확인
    # 현재는 어드민이 아닌 모든 사용자를 일반 사용자로 간주
    
    if bool(current_user.is_admin):
        raise AuthorizationError("일반 사용자 전용 기능입니다")
    
    return current_user


async def get_current_user_with_partner(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> tuple[User, Optional[Partner]]:
    """
    사용자와 소속 파트너 정보 함께 반환
    파트너 소속 여부와 관계없이 모든 인증된 사용자 허용
    
    Returns:
        tuple[User, Optional[Partner]]: (사용자, 파트너 또는 None)
    """
    # TODO: 사용자 테이블에 partner_id 필드 추가 후 조회
    # 현재는 임시로 None 반환
    partner = None
    
    return current_user, partner


async def require_super_admin_or_partner_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> tuple[User, Optional[Partner]]:
    """
    슈퍼어드민 또는 파트너어드민만 허용
    관리자 권한이 필요한 기능에 사용
    
    Returns:
        tuple[User, Optional[Partner]]: (사용자, 파트너 또는 None)
    """
    if not credentials:
        raise AuthenticationError("인증 정보가 없습니다")

    # 먼저 일반 사용자 인증
    user = await get_current_user(credentials, db)
    
    # 슈퍼어드민인 경우
    if bool(user.is_admin):
        return user, None
    
    # 파트너어드민인지 확인
    try:
        user, partner = await get_current_partner_admin(credentials, db)
        return user, partner
    except (AuthenticationError, AuthorizationError):
        raise AuthorizationError("관리자 권한이 없습니다")
