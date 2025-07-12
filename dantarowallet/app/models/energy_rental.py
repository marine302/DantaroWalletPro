"""
에너지 렌탈 서비스 모델

본사가 파트너사에게 TRON 에너지를 렌탈하는 서비스를 위한 데이터베이스 모델
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, Enum, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from decimal import Decimal
import enum
from datetime import datetime, timezone

Base = declarative_base()

class RentalPlanType(enum.Enum):
    """렌탈 플랜 유형"""
    PAY_AS_YOU_GO = "pay_as_you_go"  # 종량제
    SUBSCRIPTION = "subscription"      # 구독제
    HYBRID = "hybrid"                 # 하이브리드

class SubscriptionTier(enum.Enum):
    """구독 등급"""
    BRONZE = "bronze"    # 월 50만 에너지
    SILVER = "silver"    # 월 500만 에너지
    GOLD = "gold"       # 월 5000만 에너지
    ENTERPRISE = "enterprise"  # 무제한

class UsageStatus(enum.Enum):
    """사용량 상태"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    BILLED = "billed"
    DISPUTED = "disputed"

class PaymentStatus(enum.Enum):
    """결제 상태"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class EnergyRentalPlan(Base):
    """에너지 렌탈 플랜"""
    __tablename__ = "energy_rental_plans"
    
    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    plan_name = Column(String(100), nullable=False)
    plan_type = Column(Enum(RentalPlanType), nullable=False)
    subscription_tier = Column(Enum(SubscriptionTier))
    
    # 가격 설정
    price_per_energy = Column(Numeric(20, 10), default=Decimal("0.00008"))  # TRX per 에너지
    monthly_fee = Column(Numeric(20, 6))  # 월 구독료
    
    # 할당량 및 사용량
    monthly_energy_quota = Column(Integer, default=0)
    monthly_energy_used = Column(Integer, default=0)
    daily_limit = Column(Integer)
    
    # 할인 및 프로모션
    discount_rate = Column(Numeric(5, 4), default=Decimal("0"))
    promotional_end_date = Column(DateTime)
    
    # 결제 설정
    payment_method = Column(String(50))  # "prepaid", "postpaid"
    auto_recharge_enabled = Column(Boolean, default=False)
    auto_recharge_threshold = Column(Integer)  # 잔여 에너지 임계값
    auto_recharge_amount = Column(Numeric(20, 6))  # 자동 충전 금액
    
    # 상태
    is_active = Column(Boolean, default=True)
    activated_at = Column(DateTime, default=datetime.now(timezone.utc))
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # 관계
    # partner = relationship("Partner", back_populates="rental_plans")
    usage_records = relationship("EnergyUsageRecord", back_populates="rental_plan")
    billing_records = relationship("EnergyBillingRecord", back_populates="rental_plan")

class EnergyUsageRecord(Base):
    """에너지 사용 기록"""
    __tablename__ = "energy_usage_records"
    
    id = Column(Integer, primary_key=True)
    rental_plan_id = Column(Integer, ForeignKey("energy_rental_plans.id"), nullable=False)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    
    # 사용량 정보
    energy_used = Column(Integer, nullable=False)  # 사용한 에너지
    transaction_hash = Column(String(64))  # 관련 트랜잭션 해시
    from_address = Column(String(42))  # 에너지 제공 주소
    to_address = Column(String(42))  # 에너지 수신 주소
    
    # 비용 정보
    unit_price = Column(Numeric(20, 10), nullable=False)  # 단가
    total_cost = Column(Numeric(20, 6), nullable=False)  # 총 비용
    
    # 상태
    status = Column(Enum(UsageStatus), default=UsageStatus.PENDING)
    used_at = Column(DateTime, nullable=False)
    recorded_at = Column(DateTime, default=datetime.now(timezone.utc))
    
    # 메타데이터
    meta_data = Column(JSON)  # 추가 정보
    
    # 관계
    rental_plan = relationship("EnergyRentalPlan", back_populates="usage_records")
    # partner = relationship("Partner", back_populates="energy_usage_records")

class EnergyBillingRecord(Base):
    """에너지 청구 기록"""
    __tablename__ = "energy_billing_records"
    
    id = Column(Integer, primary_key=True)
    rental_plan_id = Column(Integer, ForeignKey("energy_rental_plans.id"), nullable=False)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    
    # 청구 기간
    billing_period_start = Column(DateTime, nullable=False)
    billing_period_end = Column(DateTime, nullable=False)
    
    # 사용량 요약
    total_energy_used = Column(Integer, nullable=False)
    total_cost = Column(Numeric(20, 6), nullable=False)
    
    # 월 구독료
    monthly_fee = Column(Numeric(20, 6), default=Decimal("0"))
    
    # 할인 및 크레딧
    discount_amount = Column(Numeric(20, 6), default=Decimal("0"))
    credit_applied = Column(Numeric(20, 6), default=Decimal("0"))
    
    # 최종 청구 금액
    final_amount = Column(Numeric(20, 6), nullable=False)
    
    # 결제 상태
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_method = Column(String(50))
    payment_tx_hash = Column(String(64))
    paid_at = Column(DateTime)
    
    # 청구서 정보
    invoice_number = Column(String(50), unique=True)
    invoice_url = Column(String(255))
    due_date = Column(DateTime)
    
    # 상태
    is_disputed = Column(Boolean, default=False)
    dispute_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # 관계
    rental_plan = relationship("EnergyRentalPlan", back_populates="billing_records")
    # partner = relationship("Partner", back_populates="energy_billing_records")

class EnergyPool(Base):
    """에너지 풀 관리"""
    __tablename__ = "energy_pools"
    
    id = Column(Integer, primary_key=True)
    pool_name = Column(String(100), nullable=False)
    
    # 에너지 현황
    total_energy = Column(Integer, nullable=False)
    available_energy = Column(Integer, nullable=False)
    reserved_energy = Column(Integer, default=0)
    
    # TRX 스테이킹 정보
    staked_trx = Column(Numeric(20, 6), nullable=False)
    stake_address = Column(String(42), nullable=False)
    
    # 효율성 지표
    energy_per_trx = Column(Numeric(10, 6))  # TRX당 에너지
    daily_energy_generation = Column(Integer)
    
    # 상태
    is_active = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=datetime.now(timezone.utc))
    
    # 임계값 설정
    low_energy_threshold = Column(Integer, default=1000000)  # 100만 에너지
    emergency_threshold = Column(Integer, default=500000)   # 50만 에너지
    
    # 메타데이터
    meta_data = Column(JSON)

class EnergyPricing(Base):
    """에너지 가격 정책"""
    __tablename__ = "energy_pricing"
    
    id = Column(Integer, primary_key=True)
    pricing_name = Column(String(100), nullable=False)
    
    # 가격 설정
    base_price = Column(Numeric(20, 10), nullable=False)  # 기본 가격
    
    # 볼륨 할인
    volume_discount_tiers = Column(JSON)  # 볼륨별 할인 정책
    
    # 시간대별 가격
    peak_hours_multiplier = Column(Numeric(3, 2), default=Decimal("1.0"))
    off_peak_hours_multiplier = Column(Numeric(3, 2), default=Decimal("0.8"))
    
    # 유효 기간
    effective_from = Column(DateTime, nullable=False)
    effective_to = Column(DateTime)
    
    # 상태
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    
    # 메타데이터
    description = Column(Text)

class EnergyAllocation(Base):
    """에너지 할당 관리"""
    __tablename__ = "energy_allocations"
    
    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    energy_pool_id = Column(Integer, ForeignKey("energy_pools.id"), nullable=False)
    
    # 할당량
    allocated_energy = Column(Integer, nullable=False)
    used_energy = Column(Integer, default=0)
    remaining_energy = Column(Integer, nullable=False)
    
    # 할당 기간
    allocation_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime)
    
    # 상태
    is_active = Column(Boolean, default=True)
    
    # 관계
    # partner = relationship("Partner", back_populates="energy_allocations")
    energy_pool = relationship("EnergyPool")

def get_subscription_tier_limits(tier: SubscriptionTier) -> dict:
    """구독 등급별 제한 정보 반환"""
    limits = {
        SubscriptionTier.BRONZE: {
            "monthly_quota": 500000,      # 50만 에너지
            "daily_limit": 20000,         # 2만 에너지
            "monthly_fee": Decimal("50.0")
        },
        SubscriptionTier.SILVER: {
            "monthly_quota": 5000000,     # 500만 에너지
            "daily_limit": 200000,        # 20만 에너지
            "monthly_fee": Decimal("400.0")
        },
        SubscriptionTier.GOLD: {
            "monthly_quota": 50000000,    # 5000만 에너지
            "daily_limit": 2000000,       # 200만 에너지
            "monthly_fee": Decimal("3000.0")
        },
        SubscriptionTier.ENTERPRISE: {
            "monthly_quota": None,        # 무제한
            "daily_limit": None,          # 무제한
            "monthly_fee": Decimal("10000.0")
        }
    }
    return limits.get(tier, {})

def calculate_energy_cost(energy_amount: int, plan: EnergyRentalPlan) -> Decimal:
    """에너지 비용 계산"""
    price_per_energy = Decimal(str(getattr(plan, "price_per_energy", 0)))
    base_cost = Decimal(str(energy_amount)) * price_per_energy
    
    # 할인 적용
    discount_rate = float(getattr(plan, "discount_rate", 0))
    if discount_rate > 0:
        discount_amount = base_cost * Decimal(str(discount_rate))
        base_cost -= discount_amount
    
    return base_cost
