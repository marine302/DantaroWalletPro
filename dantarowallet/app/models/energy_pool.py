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


# Doc #25: 파트너별 에너지 풀 고급 관리 모델들

class EnergyStatus(enum.Enum):
    """에너지 상태 (Doc #25)"""
    SUFFICIENT = "sufficient"      # 충분
    WARNING = "warning"           # 경고
    CRITICAL = "critical"         # 위험
    DEPLETED = "depleted"        # 고갈


class EnergyAlertType(enum.Enum):
    """알림 유형 (Doc #25)"""
    THRESHOLD_WARNING = "threshold_warning"
    THRESHOLD_CRITICAL = "threshold_critical"
    DEPLETION_IMMINENT = "depletion_imminent"
    RECOVERY_NEEDED = "recovery_needed"
    DAILY_REPORT = "daily_report"


class PartnerEnergyPool(Base):
    """파트너사 에너지 풀 상태 (Doc #25)"""
    __tablename__ = "partner_energy_pools"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, nullable=False, unique=True, comment="파트너사 ID")
    wallet_address = Column(String(42), nullable=False, comment="모니터링 지갑 주소")
    
    # 에너지 상태
    total_energy = Column(Numeric(20, 0), default=0, comment="총 에너지")
    available_energy = Column(Numeric(20, 0), default=0, comment="사용 가능 에너지")
    used_energy = Column(Numeric(20, 0), default=0, comment="사용된 에너지")
    energy_limit = Column(Numeric(20, 0), default=0, comment="에너지 한도")
    
    # 대역폭 상태
    total_bandwidth = Column(Numeric(20, 0), default=0, comment="총 대역폭")
    available_bandwidth = Column(Numeric(20, 0), default=0, comment="사용 가능 대역폭")
    
    # TRX 스테이킹 정보
    frozen_trx_amount = Column(Numeric(18, 6), default=0, comment="동결된 TRX")
    frozen_for_energy = Column(Numeric(18, 6), default=0, comment="에너지용 동결 TRX")
    frozen_for_bandwidth = Column(Numeric(18, 6), default=0, comment="대역폭용 동결 TRX")
    
    # 상태 및 예측
    status = Column(Enum(EnergyStatus), default=EnergyStatus.SUFFICIENT, comment="현재 상태")
    depletion_estimated_at = Column(DateTime(timezone=True), comment="예상 고갈 시간")
    daily_average_usage = Column(Numeric(20, 0), default=0, comment="일평균 사용량")
    peak_usage_hour = Column(Integer, comment="피크 사용 시간")
    
    # 임계값 설정
    warning_threshold = Column(Integer, default=30, comment="경고 임계값 (%)")
    critical_threshold = Column(Integer, default=10, comment="위험 임계값 (%)")
    auto_response_enabled = Column(Boolean, default=True, comment="자동 대응 활성화")
    
    # 메타데이터
    last_checked_at = Column(DateTime(timezone=True), comment="마지막 확인 시간")
    last_alert_sent_at = Column(DateTime(timezone=True), comment="마지막 알림 시간")
    metrics_history = Column(JSON, comment="과거 지표 (최근 24시간)")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    alerts = relationship("EnergyAlert", back_populates="energy_pool", cascade="all, delete-orphan")
    partner_usage_logs = relationship("PartnerEnergyUsageLog", back_populates="energy_pool", cascade="all, delete-orphan")


class EnergyAlert(Base):
    """에너지 알림 이력 (Doc #25)"""
    __tablename__ = "energy_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    energy_pool_id = Column(Integer, ForeignKey("partner_energy_pools.id"), nullable=False, comment="에너지 풀 ID")
    alert_type = Column(Enum(EnergyAlertType), nullable=False, comment="알림 유형")
    
    # 알림 내용
    severity = Column(String(20), nullable=False, comment="심각도")
    title = Column(String(200), nullable=False, comment="알림 제목")
    message = Column(String(1000), nullable=False, comment="알림 내용")
    
    # 상태 정보
    energy_percentage = Column(Integer, comment="에너지 잔량 (%)")
    available_energy = Column(Numeric(20, 0), comment="사용 가능 에너지")
    estimated_hours_remaining = Column(Integer, comment="예상 잔여 시간")
    
    # 알림 전송 정보
    sent_via = Column(JSON, comment="전송 채널 (email, telegram, webhook)")
    sent_to = Column(JSON, comment="수신자 목록")
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged = Column(Boolean, default=False, comment="확인 여부")
    acknowledged_at = Column(DateTime(timezone=True), comment="확인 시간")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    energy_pool = relationship("PartnerEnergyPool", back_populates="alerts")


class PartnerEnergyUsageLog(Base):
    """파트너별 에너지 사용 로그 (Doc #25)"""
    __tablename__ = "partner_energy_usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    energy_pool_id = Column(Integer, ForeignKey("partner_energy_pools.id"), nullable=False, comment="에너지 풀 ID")
    
    # 사용 정보
    transaction_type = Column(String(50), nullable=False, comment="트랜잭션 유형")
    transaction_hash = Column(String(66), comment="트랜잭션 해시")
    energy_consumed = Column(Numeric(20, 0), nullable=False, comment="소비된 에너지")
    bandwidth_consumed = Column(Numeric(20, 0), default=0, comment="소비된 대역폭")
    
    # 비용 정보
    energy_unit_price = Column(Numeric(10, 6), comment="에너지 단가 (TRX)")
    total_cost = Column(Numeric(18, 6), comment="총 비용 (TRX)")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    energy_pool = relationship("PartnerEnergyPool", back_populates="partner_usage_logs")


class EnergyPrediction(Base):
    """에너지 예측 데이터 (Doc #25)"""
    __tablename__ = "energy_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    energy_pool_id = Column(Integer, ForeignKey("partner_energy_pools.id"), nullable=False, comment="에너지 풀 ID")
    
    # 예측 정보
    prediction_date = Column(DateTime(timezone=True), nullable=False, comment="예측 날짜")
    predicted_usage = Column(Numeric(20, 0), nullable=False, comment="예측 사용량")
    predicted_depletion = Column(DateTime(timezone=True), comment="예측 고갈 시간")
    confidence_score = Column(Numeric(5, 2), comment="신뢰도 점수 (0-100)")
    
    # 예측 기반 데이터
    historical_pattern = Column(JSON, comment="과거 패턴 데이터")
    seasonal_factors = Column(JSON, comment="계절적 요인")
    trend_analysis = Column(JSON, comment="트렌드 분석")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
