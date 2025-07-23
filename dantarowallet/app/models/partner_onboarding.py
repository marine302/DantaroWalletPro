"""
파트너사 온보딩 자동화 모델 - Doc #29
새 파트너사의 완전 자동화된 온보딩 프로세스를 관리합니다.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base, BaseModel


class OnboardingStatus(str, Enum):
    """온보딩 상태"""

    PENDING = "pending"  # 대기 중
    REGISTRATION = "registration"  # 등록 진행
    ACCOUNT_SETUP = "account_setup"  # 계정 설정
    WALLET_SETUP = "wallet_setup"  # 지갑 설정
    SYSTEM_CONFIG = "system_config"  # 시스템 구성
    DEPLOYMENT = "deployment"  # 배포 중
    TESTING = "testing"  # 테스트 중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"  # 실패


class OnboardingStepStatus(str, Enum):
    """온보딩 단계 상태"""

    PENDING = "pending"  # 대기 중
    RUNNING = "running"  # 실행 중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"  # 실패
    SKIPPED = "skipped"  # 건너뜀


class ChecklistCategory(str, Enum):
    """체크리스트 카테고리"""

    SECURITY = "security"  # 보안
    INTEGRATION = "integration"  # 통합
    COMPLIANCE = "compliance"  # 컴플라이언스
    TECHNICAL = "technical"  # 기술
    BUSINESS = "business"  # 비즈니스


class PartnerOnboarding(Base):
    """파트너 온보딩 프로세스"""

    __tablename__ = "partner_onboardings"

    id = Column(Integer, primary_key=True, index=True)
    # 파트너 정보
    partner_id = Column(
        String(50), ForeignKey("partners.id"), nullable=False, unique=True
    )

    # 온보딩 상태
    status = Column(
        SQLEnum(OnboardingStatus), nullable=False, default=OnboardingStatus.PENDING
    )

    # 진행 상태
    current_step = Column(Integer, nullable=False, default=1)
    total_steps = Column(Integer, nullable=False, default=6)
    progress_percentage = Column(Integer, nullable=False, default=0)

    # 단계별 완료 상태
    registration_completed = Column(Boolean, nullable=False, default=False)
    account_setup_completed = Column(Boolean, nullable=False, default=False)
    wallet_setup_completed = Column(Boolean, nullable=False, default=False)
    system_config_completed = Column(Boolean, nullable=False, default=False)
    deployment_completed = Column(Boolean, nullable=False, default=False)
    testing_completed = Column(Boolean, nullable=False, default=False)

    # 설정 데이터
    configuration_data = Column(JSON, nullable=True, default=dict)  # 온보딩 설정
    deployment_info = Column(JSON, nullable=True, default=dict)  # 배포 정보
    test_results = Column(JSON, nullable=True, default=dict)  # 테스트 결과

    # 자동화 설정
    auto_proceed = Column(Boolean, nullable=False, default=True)  # 자동 진행 여부
    manual_approval_required = Column(
        Boolean, nullable=False, default=False
    )  # 수동 승인 필요

    # 알림 설정
    notification_email = Column(String(255), nullable=True)
    notification_webhook = Column(String(500), nullable=True)
    send_progress_updates = Column(Boolean, nullable=False, default=True)

    # 오류 처리
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    last_error = Column(Text, nullable=True)

    # 타임스탬프
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계 설정
    partner = relationship("Partner", back_populates="onboarding")
    steps = relationship(
        "OnboardingStep", back_populates="onboarding", cascade="all, delete-orphan"
    )
    checklist = relationship(
        "OnboardingChecklist", back_populates="onboarding", cascade="all, delete-orphan"
    )
    logs = relationship(
        "OnboardingLog", back_populates="onboarding", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<PartnerOnboarding(partner_id={self.partner_id}, status={self.status})>"
        )

    def is_completed(self) -> bool:
        """온보딩 완료 여부"""
        return str(self.status) == OnboardingStatus.COMPLETED.value

    def is_failed(self) -> bool:
        """온보딩 실패 여부"""
        return str(self.status) == OnboardingStatus.FAILED.value

    def can_retry(self) -> bool:
        """재시도 가능 여부"""
        retry_count = getattr(self, "retry_count", 0) or 0
        max_retries = getattr(self, "max_retries", 3) or 3
        return retry_count < max_retries


class OnboardingStep(Base):
    """온보딩 단계 상세"""

    __tablename__ = "onboarding_steps"

    id = Column(Integer, primary_key=True, index=True)
    # 온보딩 연결
    onboarding_id = Column(
        Integer, ForeignKey("partner_onboardings.id"), nullable=False
    )

    # 단계 정보
    step_number = Column(Integer, nullable=False)
    step_name = Column(String(100), nullable=False)
    step_description = Column(Text, nullable=True)
    status = Column(
        SQLEnum(OnboardingStepStatus),
        nullable=False,
        default=OnboardingStepStatus.PENDING,
    )

    # 실행 정보
    handler_function = Column(String(200), nullable=True)  # 핸들러 함수명
    dependencies = Column(JSON, nullable=True, default=list)  # 의존성 단계들
    estimated_duration = Column(Integer, nullable=True)  # 예상 소요 시간 (분)
    actual_duration = Column(Integer, nullable=True)  # 실제 소요 시간 (분)

    # 결과 데이터
    result_data = Column(JSON, nullable=True, default=dict)
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)

    # 자동화 설정
    is_automated = Column(Boolean, nullable=False, default=True)
    requires_manual_intervention = Column(Boolean, nullable=False, default=False)

    # 타임스탬프
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계 설정
    onboarding = relationship("PartnerOnboarding", back_populates="steps")

    def __repr__(self) -> str:
        return f"<OnboardingStep(step_number={self.step_number}, name={self.step_name}, status={self.status})>"


class OnboardingChecklist(Base):
    """온보딩 체크리스트"""

    __tablename__ = "onboarding_checklists"

    id = Column(Integer, primary_key=True, index=True)
    # 온보딩 연결
    onboarding_id = Column(
        Integer, ForeignKey("partner_onboardings.id"), nullable=False
    )

    # 체크리스트 정보
    category = Column(SQLEnum(ChecklistCategory), nullable=False)
    item_name = Column(String(200), nullable=False)
    item_description = Column(Text, nullable=True)

    # 완료 상태
    is_required = Column(Boolean, nullable=False, default=True)
    is_completed = Column(Boolean, nullable=False, default=False)
    is_automated = Column(Boolean, nullable=False, default=False)

    # 검증 정보
    verification_method = Column(String(100), nullable=True)  # 검증 방법
    verification_data = Column(JSON, nullable=True)  # 검증 데이터
    notes = Column(Text, nullable=True)

    # 완료 정보
    completed_by = Column(String(100), nullable=True)  # 완료자
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계 설정
    onboarding = relationship("PartnerOnboarding", back_populates="checklist")

    def __repr__(self) -> str:
        return f"<OnboardingChecklist(category={self.category}, item={self.item_name}, completed={self.is_completed})>"


class OnboardingLog(Base):
    """온보딩 로그"""

    __tablename__ = "onboarding_logs"

    id = Column(Integer, primary_key=True, index=True)
    # 온보딩 연결
    onboarding_id = Column(
        Integer, ForeignKey("partner_onboardings.id"), nullable=False
    )

    # 로그 정보
    level = Column(String(20), nullable=False)  # info, warning, error
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)

    # 컨텍스트 정보
    step_number = Column(Integer, nullable=True)
    action = Column(String(100), nullable=True)
    actor = Column(String(100), nullable=True)  # system, admin, user

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정
    onboarding = relationship("PartnerOnboarding", back_populates="logs")

    def __repr__(self) -> str:
        return f"<OnboardingLog(level={self.level}, message={self.message[:50]})>"


# 인덱스 설정
Index("idx_partner_onboarding_partner_id", PartnerOnboarding.partner_id)
Index("idx_partner_onboarding_status", PartnerOnboarding.status)
Index("idx_onboarding_step_onboarding_id", OnboardingStep.onboarding_id)
Index("idx_onboarding_step_number", OnboardingStep.step_number)
Index("idx_onboarding_checklist_onboarding_id", OnboardingChecklist.onboarding_id)
Index("idx_onboarding_checklist_category", OnboardingChecklist.category)
Index("idx_onboarding_log_onboarding_id", OnboardingLog.onboarding_id)
Index("idx_onboarding_log_level", OnboardingLog.level)
