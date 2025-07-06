"""에너지 풀 관련 모델"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

class EnergyPool(Base):
    """에너지 풀 테이블"""
    __tablename__ = "energy_pools"
    
    id = Column(Integer, primary_key=True, index=True)
    total_energy = Column(Integer, nullable=False, default=0, comment="총 에너지량")
    available_energy = Column(Integer, nullable=False, default=0, comment="사용 가능한 에너지")
    reserved_energy = Column(Integer, nullable=False, default=0, comment="예약된 에너지")
    daily_consumption = Column(Integer, nullable=False, default=0, comment="일일 소모량")
    last_recharge_at = Column(DateTime(timezone=True), comment="마지막 충전 시간")
    alert_threshold = Column(Integer, nullable=False, default=100000, comment="알림 임계값")
    is_emergency_mode = Column(Boolean, default=False, comment="긴급 모드 여부")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class EnergyTransaction(Base):
    """에너지 사용 내역 테이블"""
    __tablename__ = "energy_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_type = Column(String(50), nullable=False, comment="거래 유형 (withdrawal, transfer)")
    energy_amount = Column(Integer, nullable=False, comment="사용된 에너지량")
    transaction_id = Column(String(255), comment="연관된 거래 ID")
    user_id = Column(Integer, ForeignKey("users.id"), comment="사용자 ID")
    status = Column(String(50), default="completed", comment="상태")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    user = relationship("User", back_populates="energy_transactions")

class EnergyQueue(Base):
    """에너지 부족 시 대기열 테이블"""
    __tablename__ = "energy_queues"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    transaction_type = Column(String(50), nullable=False)
    amount = Column(Numeric(18, 8), nullable=False, comment="거래 금액")
    to_address = Column(String(255), comment="목적지 주소")
    estimated_energy = Column(Integer, nullable=False, comment="예상 에너지 소모량")
    priority = Column(Integer, default=1, comment="우선순위 (1-10)")
    status = Column(String(50), default="pending", comment="상태")
    estimated_wait_time = Column(Integer, comment="예상 대기 시간(분)")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), comment="처리 시간")
    
    # 관계 설정
    user = relationship("User")

class EnergyAlert(Base):
    """에너지 부족 알림 테이블"""
    __tablename__ = "energy_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), nullable=False, comment="알림 유형")
    title = Column(String(200), nullable=False, comment="알림 제목")
    message = Column(Text, comment="알림 내용")
    severity = Column(String(20), default="info", comment="심각도 (info, warning, critical)")
    is_active = Column(Boolean, default=True, comment="활성 상태")
    resolved_at = Column(DateTime(timezone=True), comment="해결 시간")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
