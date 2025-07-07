"""
TRON Energy Pool 관리 모델
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
import enum

from app.models.base import Base
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    JSON,
    Enum,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class EnergyPoolStatus(enum.Enum):
    ACTIVE = "active"
    LOW = "low"  # 20% 미만
    CRITICAL = "critical"  # 10% 미만
    DEPLETED = "depleted"  # 0%
    MAINTENANCE = "maintenance"


class EnergyPoolModel(Base):
    """TRON Energy Pool 테이블 - 본사 에너지 풀 관리"""

    __tablename__ = "energy_pools"

    id = Column(Integer, primary_key=True, index=True)
    pool_name = Column(String(100), nullable=False)
    owner_address = Column(String(34), nullable=False)  # TRON 주소

    # TRX 동결 정보
    frozen_trx = Column(Numeric(20, 6), default=0)  # 동결된 TRX
    total_energy = Column(Integer, default=0)  # 총 에너지
    available_energy = Column(Integer, default=0)  # 사용 가능 에너지
    used_energy = Column(Integer, default=0)  # 사용된 에너지

    # 상태 및 임계값
    status = Column(Enum(EnergyPoolStatus), default=EnergyPoolStatus.ACTIVE)
    low_threshold = Column(Integer, default=20)  # 낮음 경고 임계값 (%)
    critical_threshold = Column(Integer, default=10)  # 위급 경고 임계값 (%)

    # 자동 관리 설정
    auto_refill = Column(Boolean, default=False)  # 자동 충전 활성화
    auto_refill_amount = Column(Numeric(20, 6), default=10000)  # 자동 충전 금액
    auto_refill_trigger = Column(Integer, default=15)  # 자동 충전 트리거 (%)

    # 통계
    daily_consumption = Column(JSON, default=dict)  # 일별 소비량
    peak_usage_hours = Column(JSON, default=dict)  # 피크 사용 시간대

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    last_refilled_at = Column(DateTime)
    last_checked_at = Column(DateTime)

    # 관계
    usage_logs = relationship("EnergyUsageLog", back_populates="pool")
    price_history = relationship("EnergyPriceHistory", back_populates="pool")


class EnergyUsageLog(Base):
    """에너지 사용 로그 테이블"""

    __tablename__ = "energy_usage_logs"

    id = Column(Integer, primary_key=True)
    pool_id = Column(Integer, ForeignKey("energy_pools.id"))
    transaction_id = Column(Integer, ForeignKey("transactions.id"))

    # 사용 정보
    energy_consumed = Column(Integer, nullable=False)  # 소비된 에너지
    transaction_type = Column(String(50))  # 거래 유형 (transfer, approve 등)
    user_id = Column(Integer, ForeignKey("users.id"))

    # 비용 계산
    energy_price = Column(Numeric(20, 8))  # 에너지 단가 (TRX/Energy)
    actual_cost = Column(Numeric(20, 6))  # 실제 비용 (TRX)

    # 타임스탬프
    used_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    pool = relationship("EnergyPoolModel", back_populates="usage_logs")
    transaction = relationship("Transaction")
    user = relationship("User")


class EnergyPriceHistory(Base):
    """에너지 가격 히스토리 테이블"""

    __tablename__ = "energy_price_history"

    id = Column(Integer, primary_key=True)
    pool_id = Column(Integer, ForeignKey("energy_pools.id"))

    # 가격 정보
    trx_price_usd = Column(Numeric(20, 8))  # TRX/USD 가격
    energy_price_trx = Column(Numeric(20, 8))  # Energy/TRX 가격
    energy_price_usd = Column(Numeric(20, 8))  # Energy/USD 가격

    # 시장 정보
    market_demand = Column(String(20))  # high, medium, low
    network_congestion = Column(Integer)  # 0-100%

    recorded_at = Column(DateTime, default=datetime.utcnow)

    pool = relationship("EnergyPoolModel", back_populates="price_history")
