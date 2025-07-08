"""파트너사 수수료 및 정책 관련 모델 - Doc #26"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, JSON, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base
import enum


class FeeType(enum.Enum):
    """수수료 유형"""
    FLAT = "flat"              # 고정 수수료
    PERCENTAGE = "percentage"   # 비율 수수료
    TIERED = "tiered"          # 구간별 수수료
    DYNAMIC = "dynamic"        # 동적 수수료


class WithdrawalPolicy(enum.Enum):
    """출금 정책"""
    REALTIME = "realtime"      # 실시간 처리
    BATCH = "batch"            # 일괄 처리
    HYBRID = "hybrid"          # 혼합 (조건부)
    MANUAL = "manual"          # 수동 처리


class EnergyPolicy(enum.Enum):
    """에너지 부족 대응 정책"""
    WAIT_QUEUE = "wait_queue"           # 대기열 등록
    TRX_PAYMENT = "trx_payment"         # TRX 직접 결제
    PRIORITY_QUEUE = "priority_queue"   # 우선순위 큐
    REJECT = "reject"                   # 거부


class PartnerFeePolicy(Base):
    """파트너사 수수료 정책"""
    __tablename__ = "partner_fee_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(String(36), ForeignKey("partners.id"), nullable=False, unique=True)
    
    # 기본 수수료 설정
    fee_type = Column(Enum(FeeType), default=FeeType.PERCENTAGE, comment="수수료 유형")
    base_fee_rate = Column(Numeric(5, 4), default=0.001, comment="기본 수수료율 (0.1%)")
    min_fee_amount = Column(Numeric(18, 6), default=0.1, comment="최소 수수료")
    max_fee_amount = Column(Numeric(18, 6), comment="최대 수수료")
    
    # 거래 유형별 수수료
    withdrawal_fee_rate = Column(Numeric(5, 4), default=0.001, comment="출금 수수료율")
    internal_transfer_fee_rate = Column(Numeric(5, 4), default=0, comment="내부 이체 수수료율")
    
    # 사용자 등급별 할인
    vip_discount_rates = Column(JSON, comment="VIP 등급별 할인율")
    
    # 프로모션 설정
    promotion_active = Column(Boolean, default=False, comment="프로모션 활성화")
    promotion_fee_rate = Column(Numeric(5, 4), comment="프로모션 수수료율")
    promotion_end_date = Column(DateTime(timezone=True), comment="프로모션 종료일")
    
    # 수익 분배
    platform_share_rate = Column(Numeric(5, 4), default=0.3, comment="플랫폼 수수료 분배율 (30%)")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    partner = relationship("Partner", back_populates="fee_policy")
    fee_tiers = relationship("FeeTier", back_populates="fee_policy")


class FeeTier(Base):
    """구간별 수수료 설정"""
    __tablename__ = "fee_tiers"
    
    id = Column(Integer, primary_key=True, index=True)
    fee_policy_id = Column(Integer, ForeignKey("partner_fee_policies.id"), nullable=False)
    
    min_amount = Column(Numeric(18, 6), nullable=False, comment="최소 금액")
    max_amount = Column(Numeric(18, 6), comment="최대 금액 (NULL=무제한)")
    fee_rate = Column(Numeric(5, 4), nullable=False, comment="수수료율")
    fixed_fee = Column(Numeric(18, 6), default=0, comment="고정 수수료")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    fee_policy = relationship("PartnerFeePolicy", back_populates="fee_tiers")


class PartnerWithdrawalPolicy(Base):
    """파트너사 출금 정책"""
    __tablename__ = "partner_withdrawal_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(String(36), ForeignKey("partners.id"), nullable=False, unique=True)
    
    # 출금 방식
    policy_type = Column(Enum(WithdrawalPolicy), default=WithdrawalPolicy.HYBRID, comment="출금 정책")
    
    # 실시간 출금 설정
    realtime_enabled = Column(Boolean, default=True, comment="실시간 출금 활성화")
    realtime_max_amount = Column(Numeric(18, 6), default=1000, comment="실시간 최대 금액")
    auto_approve_enabled = Column(Boolean, default=False, comment="자동 승인 활성화")
    auto_approve_max_amount = Column(Numeric(18, 6), default=100, comment="자동 승인 최대 금액")
    
    # 일괄 출금 설정
    batch_enabled = Column(Boolean, default=True, comment="일괄 출금 활성화")
    batch_schedule = Column(JSON, comment="일괄 처리 스케줄")
    batch_min_amount = Column(Numeric(18, 6), default=10, comment="일괄 처리 최소 금액")
    
    # 출금 한도
    daily_limit_per_user = Column(Numeric(18, 6), default=10000, comment="사용자별 일일 한도")
    daily_limit_total = Column(Numeric(18, 6), default=1000000, comment="전체 일일 한도")
    single_transaction_limit = Column(Numeric(18, 6), default=5000, comment="단일 거래 한도")
    
    # 화이트리스트
    whitelist_required = Column(Boolean, default=False, comment="화이트리스트 필수")
    whitelist_addresses = Column(JSON, comment="화이트리스트 주소 목록")
    
    # 보안 설정
    require_2fa = Column(Boolean, default=True, comment="2FA 필수")
    confirmation_blocks = Column(Integer, default=19, comment="확인 블록 수")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    partner = relationship("Partner", back_populates="withdrawal_policy")


class PartnerEnergyPolicy(Base):
    """파트너사 에너지 대응 정책"""
    __tablename__ = "partner_energy_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(String(36), ForeignKey("partners.id"), nullable=False, unique=True)
    
    # 기본 대응 정책
    default_policy = Column(Enum(EnergyPolicy), default=EnergyPolicy.WAIT_QUEUE, comment="기본 대응 정책")
    
    # TRX 직접 결제 설정
    trx_payment_enabled = Column(Boolean, default=True, comment="TRX 결제 활성화")
    trx_payment_markup = Column(Numeric(5, 4), default=0.1, comment="TRX 결제 마크업 (10%)")
    trx_payment_max_fee = Column(Numeric(18, 6), default=20, comment="최대 TRX 수수료")
    
    # 대기열 설정
    queue_enabled = Column(Boolean, default=True, comment="대기열 활성화")
    queue_max_wait_hours = Column(Integer, default=24, comment="최대 대기 시간")
    queue_notification_enabled = Column(Boolean, default=True, comment="대기열 알림")
    
    # 우선순위 설정
    priority_queue_enabled = Column(Boolean, default=True, comment="우선순위 큐 활성화")
    vip_priority_levels = Column(JSON, comment="VIP 등급별 우선순위")
    
    # 에너지 절약 모드
    energy_saving_enabled = Column(Boolean, default=False, comment="에너지 절약 모드")
    energy_saving_threshold = Column(Integer, default=20, comment="절약 모드 임계값 (%)")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    partner = relationship("Partner", back_populates="energy_policy")


class UserTier(Base):
    """사용자 등급 관리"""
    __tablename__ = "user_tiers"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(String(36), ForeignKey("partners.id"), nullable=False)
    
    tier_name = Column(String(50), nullable=False, comment="등급명")
    tier_level = Column(Integer, nullable=False, comment="등급 레벨 (높을수록 VIP)")
    min_volume = Column(Numeric(18, 6), default=0, comment="최소 거래량")
    fee_discount_rate = Column(Numeric(5, 4), default=0, comment="수수료 할인율")
    withdrawal_limit_multiplier = Column(Numeric(5, 2), default=1.0, comment="출금 한도 배수")
    
    # 혜택 설정
    benefits = Column(JSON, comment="등급별 혜택")
    
    # 승급 조건
    upgrade_conditions = Column(JSON, comment="승급 조건")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    partner = relationship("Partner", back_populates="user_tiers")


class FeeCalculationLog(Base):
    """수수료 계산 로그"""
    __tablename__ = "partner_fee_calculation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(String(36), ForeignKey("partners.id"), nullable=False)
    transaction_id = Column(String(100), comment="관련 거래 ID")
    
    # 계산 정보
    transaction_amount = Column(Numeric(18, 6), nullable=False, comment="거래 금액")
    base_fee_rate = Column(Numeric(5, 4), comment="기본 수수료율")
    applied_fee_rate = Column(Numeric(5, 4), comment="적용 수수료율")
    discount_rate = Column(Numeric(5, 4), default=0, comment="할인율")
    
    # 수수료 분석
    calculated_fee = Column(Numeric(18, 6), comment="계산된 수수료")
    platform_share = Column(Numeric(18, 6), comment="플랫폼 분배액")
    partner_share = Column(Numeric(18, 6), comment="파트너 분배액")
    
    # 적용된 정책
    policy_details = Column(JSON, comment="적용된 정책 상세")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    partner = relationship("Partner", back_populates="fee_logs")
