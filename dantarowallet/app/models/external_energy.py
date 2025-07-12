"""
외부 에너지 공급자 연동 모델
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, Enum, JSON, ForeignKey
from sqlalchemy.orm import relationship
from decimal import Decimal
import enum
from datetime import datetime

from app.core.database import Base


class EnergyProviderType(enum.Enum):
    """에너지 공급자 유형"""
    JUSTLEND = "justlend"          # JustLend Energy Market
    TRONNRG = "tronnrg"            # TronNRG
    TRONSCAN = "tronscan"          # TRONSCAN Energy
    P2P = "p2p"                    # P2P Trading Platform
    SPOT = "spot"                  # Spot Market


class PurchaseStatus(enum.Enum):
    """구매 상태"""
    PENDING = "pending"            # 대기중
    APPROVED = "approved"          # 승인됨
    EXECUTING = "executing"        # 실행중
    COMPLETED = "completed"        # 완료
    FAILED = "failed"              # 실패
    CANCELLED = "cancelled"        # 취소됨


class ExternalEnergyProvider(Base):
    """외부 에너지 공급자"""
    __tablename__ = "external_energy_providers"
    
    id = Column(Integer, primary_key=True)
    provider_type = Column(Enum(EnergyProviderType), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    api_endpoint = Column(String(500))
    api_key = Column(String(255))
    api_secret = Column(String(255))
    
    # 공급자 설정
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)  # 낮을수록 우선순위 높음
    max_daily_purchase = Column(Numeric(20, 6))  # 일일 최대 구매량
    min_purchase_amount = Column(Integer)  # 최소 구매 에너지
    max_purchase_amount = Column(Integer)  # 최대 구매 에너지
    
    # 가격 정보
    last_price = Column(Numeric(20, 10))  # 마지막 조회 가격
    price_updated_at = Column(DateTime)
    average_price_24h = Column(Numeric(20, 10))
    
    # 신뢰도 및 성능
    success_rate = Column(Numeric(5, 2), default=Decimal("100"))
    average_response_time = Column(Integer)  # milliseconds
    total_purchases = Column(Integer, default=0)
    total_energy_purchased = Column(Numeric(20, 0), default=0)
    
    # 메타데이터
    provider_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    price_history = relationship("EnergyPriceHistory", back_populates="provider")
    purchases = relationship("ExternalEnergyPurchase", back_populates="provider")


class EnergyPriceHistory(Base):
    """에너지 가격 히스토리"""
    __tablename__ = "external_energy_price_history"
    
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("external_energy_providers.id"))
    
    price_per_energy = Column(Numeric(20, 10), nullable=False)
    available_amount = Column(Integer)  # 구매 가능량
    min_order = Column(Integer)
    max_order = Column(Integer)
    
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    provider = relationship("ExternalEnergyProvider", back_populates="price_history")


class ExternalEnergyPurchase(Base):
    """외부 에너지 구매 기록"""
    __tablename__ = "external_energy_purchases"
    
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("external_energy_providers.id"))
    
    # 구매 정보
    energy_amount = Column(Integer, nullable=False)
    price_per_energy = Column(Numeric(20, 10), nullable=False)
    total_cost = Column(Numeric(20, 6), nullable=False)
    payment_currency = Column(String(10))  # "TRX", "USDT"
    
    # 상태 관리
    status = Column(Enum(PurchaseStatus), default=PurchaseStatus.PENDING)
    purchase_type = Column(String(20))  # "auto", "manual", "emergency"
    
    # 승인 정보
    requested_by = Column(Integer, ForeignKey("users.id"))
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    
    # 실행 정보
    transaction_hash = Column(String(64))
    energy_received_at = Column(DateTime)
    actual_energy_received = Column(Integer)
    
    # 마진 및 재판매
    margin_rate = Column(Numeric(5, 4), default=Decimal("0.2"))  # 20% 기본 마진
    resale_price = Column(Numeric(20, 10))
    
    # 자동 구매 트리거
    trigger_reason = Column(String(100))  # "low_energy", "scheduled", "emergency"
    energy_level_at_purchase = Column(Integer)  # 구매 시점 에너지 잔량
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # 관계
    provider = relationship("ExternalEnergyProvider", back_populates="purchases")


class EnergyPurchaseRule(Base):
    """에너지 자동 구매 규칙"""
    __tablename__ = "energy_purchase_rules"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)
    
    # 트리거 조건
    trigger_type = Column(String(50))  # "threshold", "schedule", "prediction"
    energy_threshold = Column(Integer)  # 에너지 임계값
    threshold_percentage = Column(Numeric(5, 2))  # 임계 비율
    schedule_cron = Column(String(100))  # 스케줄 (cron 표현식)
    
    # 구매 설정
    purchase_amount = Column(Integer)  # 구매할 에너지량
    purchase_percentage = Column(Numeric(5, 2))  # 전체 용량의 %
    max_price = Column(Numeric(20, 10))  # 최대 허용 가격
    preferred_providers = Column(JSON)  # 선호 공급자 목록
    
    # 마진 설정
    margin_type = Column(String(20))  # "fixed", "dynamic"
    base_margin = Column(Numeric(5, 4), default=Decimal("0.2"))
    emergency_margin = Column(Numeric(5, 4), default=Decimal("0.5"))
    
    # 실행 제한
    max_daily_executions = Column(Integer, default=10)
    cooldown_minutes = Column(Integer, default=30)
    last_executed_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
