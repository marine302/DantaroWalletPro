"""파트너사 관련 모델"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Numeric, JSON, Integer, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class Partner(Base):
    """파트너사 테이블"""
    __tablename__ = "partners"
    
    id = Column(String(36), primary_key=True, index=True, comment="파트너 ID (UUID)")
    name = Column(String(100), nullable=False, unique=True, comment="파트너사명")
    display_name = Column(String(100), comment="표시명")
    domain = Column(String(255), unique=True, comment="도메인")
    contact_email = Column(String(255), nullable=False, unique=True, comment="연락처 이메일")
    contact_phone = Column(String(50), comment="연락처 전화번호")
    business_type = Column(String(50), nullable=False, comment="비즈니스 유형")
    
    # API 관리
    api_key = Column(String(255), unique=True, nullable=False, comment="API 키")
    api_secret_hash = Column(String(255), nullable=False, comment="API 시크릿 해시")
    previous_api_key = Column(String(255), comment="이전 API 키")
    api_key_created_at = Column(DateTime(timezone=True), comment="API 키 생성일")
    
    # 상태 관리
    status = Column(String(20), default="pending", comment="파트너 상태")
    onboarding_status = Column(String(50), default="pending", comment="온보딩 상태")
    
    # 구독 및 제한
    subscription_plan = Column(String(50), default="basic", comment="구독 플랜")
    monthly_limit = Column(Numeric(18, 8), comment="월간 한도")
    commission_rate = Column(Numeric(5, 4), default=0, comment="수수료율")
    
    # 에너지 관리
    energy_balance = Column(Numeric(18, 8), default=0, comment="에너지 잔액")
    
    # 설정 (JSON)
    settings = Column(JSON, default={}, comment="파트너 설정")
    deployment_config = Column(JSON, default={}, comment="배포 설정")
    
    # 활동 추적
    last_activity_at = Column(DateTime(timezone=True), comment="마지막 활동 시간")
    activated_at = Column(DateTime(timezone=True), comment="활성화 시간")
    suspended_at = Column(DateTime(timezone=True), comment="정지 시간")
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정일")
    
    # 관계 정의 (실제 존재하는 테이블들과의 관계)
    api_usage_logs = relationship("PartnerApiUsage", back_populates="partner", cascade="all, delete-orphan")
    daily_statistics = relationship("PartnerDailyStatistics", back_populates="partner", cascade="all, delete-orphan")
    energy_allocations = relationship("PartnerEnergyAllocation", back_populates="partner", cascade="all, delete-orphan")
    partner_energy_usage_history = relationship("PartnerEnergyUsageHistory", back_populates="partner", cascade="all, delete-orphan")
    energy_usage_history = relationship("EnergyUsageHistory", back_populates="partner", cascade="all, delete-orphan")
    fee_revenues = relationship("PartnerFeeRevenue", back_populates="partner", cascade="all, delete-orphan")
    partner_fee_config_history = relationship("PartnerFeeConfigHistory", back_populates="partner", cascade="all, delete-orphan")
    onboarding_steps = relationship("PartnerOnboardingStep", back_populates="partner", cascade="all, delete-orphan")
    deployments = relationship("PartnerDeployment", back_populates="partner", cascade="all, delete-orphan")
    
    # 외부 지갑 관계 (TronLink 연동)
    wallets = relationship("PartnerWallet", back_populates="partner", cascade="all, delete-orphan")
    
    # Doc-26: 수수료 및 정책 관계
    fee_policy = relationship("PartnerFeePolicy", back_populates="partner", uselist=False, cascade="all, delete-orphan")
    withdrawal_policy = relationship("PartnerWithdrawalPolicy", back_populates="partner", uselist=False, cascade="all, delete-orphan")
    energy_policy = relationship("PartnerEnergyPolicy", back_populates="partner", uselist=False, cascade="all, delete-orphan")
    user_tiers = relationship("UserTier", back_populates="partner", cascade="all, delete-orphan")
    fee_calculation_logs = relationship("FeeCalculationLog", back_populates="partner", cascade="all, delete-orphan")
    policy_calculation_logs = relationship("PartnerPolicyCalculationLog", back_populates="partner", cascade="all, delete-orphan")
