"""
에너지 공급원 모델 - 문서 #40 기반
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, Enum, JSON, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from decimal import Decimal
from datetime import datetime
from app.models.base import BaseModel
import enum

class SupplierType(enum.Enum):
    """에너지 공급원 유형"""
    SELF_STAKING = "self_staking"      # 자체 스테이킹
    TRONZAP = "tronzap"                # TronZap API
    TRONNRG = "tronnrg"                # TronNRG API

class SupplierStatus(enum.Enum):
    """공급원 상태"""
    ACTIVE = "active"                   # 정상 작동
    INACTIVE = "inactive"               # 비활성화
    MAINTENANCE = "maintenance"         # 점검 중
    ERROR = "error"                     # 오류 상태

class EnergySupplier(BaseModel):
    """에너지 공급원 정보"""

    supplier_type = Column(Enum(SupplierType), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    priority = Column(Integer, nullable=False, default=1)  # 낮을수록 우선순위 높음

    # 공급원 상태
    status = Column(Enum(SupplierStatus), default=SupplierStatus.ACTIVE)
    is_active = Column(Boolean, default=True)
    last_checked_at = Column(DateTime)
    last_error = Column(String(500))

    # 에너지 정보
    available_energy = Column(BigInteger, default=0)
    max_energy_capacity = Column(BigInteger)
    daily_energy_generation = Column(BigInteger)  # 자체 스테이킹용

    # 비용 정보
    cost_per_energy = Column(Numeric(20, 10), nullable=False)
    min_order_amount = Column(Integer, default=32000)  # 최소 주문 에너지
    max_order_amount = Column(Integer)  # 최대 주문 에너지

    # API 정보 (외부 공급사용)
    api_endpoint = Column(String(255))
    api_key = Column(String(255))
    api_secret = Column(String(255))
    webhook_url = Column(String(255))

    # 통계
    total_energy_supplied = Column(BigInteger, default=0)
    total_orders = Column(Integer, default=0)
    success_rate = Column(Numeric(5, 2), default=Decimal("100.00"))
    average_response_time = Column(Integer)  # milliseconds

    # 메타데이터
    config = Column(JSON)  # 공급원별 추가 설정

    def __repr__(self):
        return f"<EnergySupplier {self.supplier_type.value} {self.name} {self.available_energy}>"
