"""
개선된 사용자 인증 시스템 설계

기존 시스템을 확장하여 3가지 사용자 유형을 지원:
1. SuperAdmin (슈퍼어드민)
2. PartnerAdmin (파트너어드민) 
3. EndUser (일반사용자)
"""

from enum import Enum
from typing import Optional
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship


class UserType(str, Enum):
    """사용자 유형 열거형"""
    SUPER_ADMIN = "super_admin"
    PARTNER_ADMIN = "partner_admin" 
    END_USER = "end_user"


class UserRole(str, Enum):
    """사용자 역할 열거형"""
    SYSTEM_ADMIN = "system_admin"           # 전체 시스템 관리
    PARTNER_OWNER = "partner_owner"         # 파트너사 소유자
    PARTNER_MANAGER = "partner_manager"     # 파트너사 관리자
    PARTNER_OPERATOR = "partner_operator"   # 파트너사 운영자
    CUSTOMER = "customer"                   # 일반 고객


# User 테이블 확장 제안
class EnhancedUser:
    """확장된 사용자 모델"""
    
    # 기존 필드들...
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    tron_address = Column(String(42), unique=True, nullable=True)
    
    # 새로 추가할 필드들
    user_type = Column(String(20), default=UserType.END_USER)  # 사용자 유형
    user_role = Column(String(30), default=UserRole.CUSTOMER)  # 사용자 역할
    partner_id = Column(String(36), ForeignKey("partners.id"), nullable=True)  # 소속 파트너
    
    # 관계
    partner = relationship("Partner", back_populates="users")


# 인증 토큰 페이로드 확장
class TokenPayload:
    """JWT 토큰 페이로드"""
    
    def __init__(self, user_id: str, user_type: UserType, user_role: UserRole, partner_id: Optional[str] = None):
        self.sub = user_id  # 사용자 ID
        self.user_type = user_type  # 사용자 유형
        self.user_role = user_role  # 사용자 역할
        self.partner_id = partner_id  # 파트너 ID (파트너 관련 사용자만)


# 개선된 의존성 함수들
async def get_current_super_admin():
    """슈퍼어드민만 허용"""
    # user_type이 SUPER_ADMIN인 사용자만 허용
    pass

async def get_current_partner_admin():
    """파트너어드민만 허용"""
    # user_type이 PARTNER_ADMIN인 사용자만 허용
    pass

async def get_current_end_user():
    """일반사용자만 허용"""
    # user_type이 END_USER인 사용자만 허용
    pass

async def get_current_partner_user():
    """특정 파트너 소속 사용자만 허용"""
    # partner_id가 있는 사용자만 허용
    pass
