"""
파트너 에너지 할당 및 마진 관리 모델

수퍼어드민이 파트너사에게 에너지를 할당하고 마진을 관리하는 시스템
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class AllocationStatus(enum.Enum):
    """할당 상태"""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class BillingCycle(enum.Enum):
    """정산 주기"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class BillingStatus(enum.Enum):
    """정산 상태"""

    PENDING = "pending"
    BILLED = "billed"
    PAID = "paid"
    OVERDUE = "overdue"
    DISPUTED = "disputed"


class PartnerTier(enum.Enum):
    """파트너 등급"""

    STARTUP = "startup"  # 스타트업 (35% 마진)
    BUSINESS = "business"  # 중소기업 (25% 마진)
    ENTERPRISE = "enterprise"  # 대기업 (15% 마진)


class PartnerEnergyAllocation(Base):
    """파트너 에너지 할당"""

    __tablename__ = "partner_energy_allocations"

    id = Column(Integer, primary_key=True)
    partner_id = Column(String(100), nullable=False, index=True)
    partner_name = Column(String(200), nullable=False)
    partner_tier = Column(
        Enum(PartnerTier), nullable=False, default=PartnerTier.BUSINESS
    )

    # 할당 정보
    allocated_amount = Column(Integer, nullable=False)  # 할당된 에너지량
    remaining_amount = Column(Integer, nullable=False)  # 남은 에너지량

    # 가격 정보
    purchase_price = Column(Float, nullable=False)  # 구매 단가 (TRX/Energy)
    markup_percentage = Column(Float, nullable=False)  # 마진율 (%)
    rental_price = Column(Float, nullable=False)  # 렌탈 단가 (TRX/Energy)

    # 계약 정보
    billing_cycle = Column(
        Enum(BillingCycle), nullable=False, default=BillingCycle.MONTHLY
    )
    status = Column(
        Enum(AllocationStatus), nullable=False, default=AllocationStatus.ACTIVE
    )

    # 날짜 정보
    allocation_date = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    expiry_date = Column(DateTime, nullable=True)
    last_usage_date = Column(DateTime, nullable=True)

    # 메타 정보
    notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    created_by = Column(String(100), nullable=False)  # 생성한 관리자 ID

    # 관계
    usage_records = relationship("PartnerEnergyUsage", back_populates="allocation")
    billing_records = relationship("PartnerEnergyBilling", back_populates="allocation")

    def __repr__(self):
        return f"<PartnerEnergyAllocation(partner={self.partner_name}, amount={self.allocated_amount}, price={self.rental_price})>"

    @property
    def used_amount(self):
        """사용된 에너지량"""
        return self.allocated_amount - self.remaining_amount

    @property
    def utilization_rate(self):
        """사용률"""
        if self.allocated_amount == 0:
            return 0.0
        return (self.used_amount / self.allocated_amount) * 100

    @property
    def total_revenue(self):
        """총 수익 (마진 * 사용량)"""
        margin_per_unit = self.rental_price - self.purchase_price
        return margin_per_unit * self.used_amount


class PartnerEnergyUsage(Base):
    """파트너 에너지 사용량"""

    __tablename__ = "partner_energy_usage"

    id = Column(Integer, primary_key=True)
    allocation_id = Column(
        Integer, ForeignKey("partner_energy_allocations.id"), nullable=False
    )
    partner_id = Column(String(100), nullable=False, index=True)

    # 사용량 정보
    used_amount = Column(Integer, nullable=False)  # 사용량
    unit_price = Column(Float, nullable=False)  # 단가
    total_cost = Column(Float, nullable=False)  # 총 비용

    # 사용 정보
    usage_date = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    transaction_hash = Column(String(200), nullable=True)  # TRON 트랜잭션 해시

    # 정산 정보
    billing_status = Column(
        Enum(BillingStatus), nullable=False, default=BillingStatus.PENDING
    )
    billing_date = Column(DateTime, nullable=True)
    payment_date = Column(DateTime, nullable=True)

    # 메타 정보
    description = Column(String(500), nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # 관계
    allocation = relationship("PartnerEnergyAllocation", back_populates="usage_records")

    def __repr__(self):
        return f"<PartnerEnergyUsage(partner={self.partner_id}, amount={self.used_amount}, cost={self.total_cost})>"


class PartnerEnergyBilling(Base):
    """파트너 에너지 정산"""

    __tablename__ = "partner_energy_billing"

    id = Column(Integer, primary_key=True)
    allocation_id = Column(
        Integer, ForeignKey("partner_energy_allocations.id"), nullable=False
    )
    partner_id = Column(String(100), nullable=False, index=True)

    # 정산 기간
    billing_period_start = Column(DateTime, nullable=False)
    billing_period_end = Column(DateTime, nullable=False)

    # 사용량 및 비용
    total_usage = Column(Integer, nullable=False)  # 총 사용량
    total_amount = Column(Float, nullable=False)  # 총 금액
    tax_amount = Column(Float, nullable=False, default=0.0)  # 세금
    final_amount = Column(Float, nullable=False)  # 최종 금액

    # 정산 정보
    billing_date = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    due_date = Column(DateTime, nullable=False)
    payment_status = Column(
        Enum(BillingStatus), nullable=False, default=BillingStatus.PENDING
    )
    payment_date = Column(DateTime, nullable=True)

    # 결제 정보
    payment_method = Column(String(50), nullable=True)
    payment_reference = Column(String(200), nullable=True)

    # 메타 정보
    notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    created_by = Column(String(100), nullable=False)

    # 관계
    allocation = relationship(
        "PartnerEnergyAllocation", back_populates="billing_records"
    )

    def __repr__(self):
        return f"<PartnerEnergyBilling(partner={self.partner_id}, amount={self.final_amount}, status={self.payment_status})>"


class EnergyPurchaseRecord(Base):
    """에너지 구매 기록"""

    __tablename__ = "energy_purchase_records"

    id = Column(Integer, primary_key=True)

    # 공급업체 정보
    supplier_name = Column(String(100), nullable=False)  # TronNRG, EnergyTron 등
    supplier_id = Column(String(100), nullable=False)

    # 구매 정보
    purchase_amount = Column(Integer, nullable=False)  # 구매량
    unit_price = Column(Float, nullable=False)  # 단가
    total_cost = Column(Float, nullable=False)  # 총 비용

    # 할인 정보
    volume_discount = Column(Float, nullable=False, default=0.0)  # 볼륨 할인율
    final_cost = Column(Float, nullable=False)  # 최종 비용

    # 구매 정보
    purchase_date = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    transaction_hash = Column(String(200), nullable=True)

    # 계약 정보
    contract_period = Column(String(50), nullable=True)  # 계약 기간
    payment_terms = Column(String(100), nullable=True)  # 결제 조건

    # 메타 정보
    notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    created_by = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<EnergyPurchaseRecord(supplier={self.supplier_name}, amount={self.purchase_amount}, cost={self.final_cost})>"

    @property
    def average_cost_per_unit(self):
        """단위당 평균 비용"""
        if self.purchase_amount == 0:
            return 0.0
        return self.final_cost / self.purchase_amount


class EnergyMarginConfig(Base):
    """에너지 마진 설정"""

    __tablename__ = "energy_margin_config"

    id = Column(Integer, primary_key=True)

    # 파트너 등급별 마진
    partner_tier = Column(Enum(PartnerTier), nullable=False, unique=True)
    default_margin_percentage = Column(Float, nullable=False)  # 기본 마진율
    min_margin_percentage = Column(Float, nullable=False)  # 최소 마진율
    max_margin_percentage = Column(Float, nullable=False)  # 최대 마진율

    # 볼륨 기반 마진 조정
    volume_threshold_1 = Column(
        Integer, nullable=False, default=1000000
    )  # 100만 에너지
    volume_margin_1 = Column(Float, nullable=False, default=0.0)  # 볼륨 할인 1
    volume_threshold_2 = Column(
        Integer, nullable=False, default=10000000
    )  # 1000만 에너지
    volume_margin_2 = Column(Float, nullable=False, default=0.0)  # 볼륨 할인 2

    # 설정 정보
    effective_date = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    is_active = Column(Boolean, nullable=False, default=True)

    # 메타 정보
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    created_by = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<EnergyMarginConfig(tier={self.partner_tier}, margin={self.default_margin_percentage}%)>"

    def calculate_margin(self, volume: int) -> float:
        """볼륨에 따른 마진율 계산"""
        base_margin = self.default_margin_percentage

        if volume >= self.volume_threshold_2:
            return max(base_margin - self.volume_margin_2, self.min_margin_percentage)
        elif volume >= self.volume_threshold_1:
            return max(base_margin - self.volume_margin_1, self.min_margin_percentage)
        else:
            return base_margin
