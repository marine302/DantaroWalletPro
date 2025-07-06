"""수수료 설정 관련 모델"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class FeeConfig(Base):
    """수수료 설정 테이블"""
    __tablename__ = "fee_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_type = Column(String(50), nullable=False, comment="거래 유형")
    base_fee = Column(Numeric(18, 8), nullable=False, comment="기본 수수료")
    percentage_fee = Column(Numeric(5, 4), nullable=False, comment="비율 수수료")
    min_fee = Column(Numeric(18, 8), nullable=False, comment="최소 수수료")
    max_fee = Column(Numeric(18, 8), nullable=False, comment="최대 수수료")
    partner_id = Column(Integer, nullable=True, comment="파트너사 ID (NULL이면 글로벌)")
    is_active = Column(Boolean, default=True, comment="활성 상태")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 정의
    partner_history = relationship("PartnerFeeConfigHistory", back_populates="fee_config", cascade="all, delete-orphan")


class FeeHistory(Base):
    """수수료 변경 이력 테이블"""
    __tablename__ = "fee_history"
    
    id = Column(Integer, primary_key=True, index=True)
    fee_config_id = Column(Integer, nullable=False, comment="수수료 설정 ID")
    old_values = Column(Text, comment="이전 설정값 (JSON)")
    new_values = Column(Text, comment="새 설정값 (JSON)")
    changed_by = Column(Integer, nullable=False, comment="변경한 관리자 ID")
    change_reason = Column(String(500), comment="변경 사유")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DynamicFeeRule(Base):
    """동적 수수료 규칙 테이블"""
    __tablename__ = "dynamic_fee_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), nullable=False, comment="규칙 이름")
    transaction_type = Column(String(50), nullable=False, comment="거래 유형")
    condition_type = Column(String(50), nullable=False, comment="조건 유형 (network_congestion, time_based, volume_based)")
    condition_value = Column(Text, comment="조건 설정 (JSON)")
    fee_multiplier = Column(Numeric(5, 4), nullable=False, comment="수수료 배율")
    priority = Column(Integer, default=1, comment="우선순위")
    is_active = Column(Boolean, default=True, comment="활성 상태")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FeeCalculationLog(Base):
    """수수료 계산 로그 테이블"""
    __tablename__ = "fee_calculation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(255), comment="거래 ID")
    user_id = Column(Integer, comment="사용자 ID")
    partner_id = Column(Integer, comment="파트너사 ID")
    transaction_type = Column(String(50), nullable=False, comment="거래 유형")
    transaction_amount = Column(Numeric(18, 8), nullable=False, comment="거래 금액")
    base_fee = Column(Numeric(18, 8), nullable=False, comment="기본 수수료")
    percentage_fee = Column(Numeric(18, 8), nullable=False, comment="비율 수수료")
    dynamic_multiplier = Column(Numeric(5, 4), default=1.0, comment="동적 배율")
    final_fee = Column(Numeric(18, 8), nullable=False, comment="최종 수수료")
    fee_config_id = Column(Integer, comment="적용된 수수료 설정 ID")
    applied_rules = Column(Text, comment="적용된 동적 규칙 (JSON)")
    calculation_details = Column(Text, comment="계산 세부사항 (JSON)")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FeeRevenueStats(Base):
    """수수료 매출 통계 테이블"""
    __tablename__ = "fee_revenue_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), nullable=False, comment="날짜")
    partner_id = Column(Integer, comment="파트너사 ID (NULL이면 전체)")
    transaction_type = Column(String(50), comment="거래 유형")
    total_transactions = Column(Integer, default=0, comment="총 거래 수")
    total_fee_collected = Column(Numeric(18, 8), default=0, comment="총 수수료 수집액")
    average_fee = Column(Numeric(18, 8), default=0, comment="평균 수수료")
    min_fee = Column(Numeric(18, 8), default=0, comment="최소 수수료")
    max_fee = Column(Numeric(18, 8), default=0, comment="최대 수수료")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
