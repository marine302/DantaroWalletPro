"""
TRON Energy Pool 관리 모델
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

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
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class EnergyPool(Base):
    """TRON Energy Pool 테이블 - 본사 에너지 풀 관리"""

    __tablename__ = "energy_pools"

    id = Column(Integer, primary_key=True, index=True)
    pool_name = Column(String(100), nullable=False, comment="에너지 풀 이름")
    wallet_address = Column(String(50), nullable=False, comment="본사 TRON 지갑 주소")

    # TRX Freezing 관련
    total_frozen_trx = Column(
        Numeric(precision=18, scale=6),
        nullable=False,
        default=0,
        comment="총 freeze된 TRX 양",
    )
    frozen_for_energy = Column(
        Numeric(precision=18, scale=6),
        nullable=False,
        default=0,
        comment="에너지용 freeze TRX",
    )
    frozen_for_bandwidth = Column(
        Numeric(precision=18, scale=6),
        nullable=False,
        default=0,
        comment="대역폭용 freeze TRX",
    )

    # Energy 상태
    available_energy = Column(
        BigInteger, nullable=False, default=0, comment="사용 가능한 에너지"
    )
    available_bandwidth = Column(
        BigInteger, nullable=False, default=0, comment="사용 가능한 대역폭"
    )

    # 소비 통계
    daily_energy_consumption = Column(
        BigInteger, nullable=False, default=0, comment="일일 에너지 소비량"
    )
    daily_bandwidth_consumption = Column(
        BigInteger, nullable=False, default=0, comment="일일 대역폭 소비량"
    )

    # 자동 관리 설정
    auto_refreeze_enabled = Column(Boolean, default=True, comment="자동 refreeze 활성화")
    energy_threshold = Column(
        BigInteger, nullable=False, default=100000, comment="에너지 부족 임계값"
    )
    bandwidth_threshold = Column(
        BigInteger, nullable=False, default=10000, comment="대역폭 부족 임계값"
    )

    # 비용 관리
    last_freeze_cost = Column(
        Numeric(precision=18, scale=6), nullable=True, comment="마지막 freeze 비용"
    )
    total_freeze_cost = Column(
        Numeric(precision=18, scale=6), nullable=False, default=0, comment="총 freeze 비용"
    )

    # 상태 관리
    is_active = Column(Boolean, default=True, comment="활성화 상태")
    last_updated = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="마지막 업데이트",
    )
    notes = Column(Text, nullable=True, comment="관리자 노트")

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # 관계 정의
    partner_allocations = relationship(
        "PartnerEnergyAllocation",
        back_populates="energy_pool",
        cascade="all, delete-orphan",
    )


class EnergyUsageLog(Base):
    """에너지 사용 로그 테이블"""

    __tablename__ = "energy_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    energy_pool_id = Column(Integer, nullable=False, comment="에너지 풀 ID")

    # 트랜잭션 정보
    transaction_hash = Column(String(64), nullable=True, comment="TRON 트랜잭션 해시")
    transaction_type = Column(
        String(50), nullable=False, comment="트랜잭션 타입 (USDT_TRANSFER, TRX_TRANSFER)"
    )

    # 사용량 정보
    energy_consumed = Column(BigInteger, nullable=False, default=0, comment="소비된 에너지")
    bandwidth_consumed = Column(
        BigInteger, nullable=False, default=0, comment="소비된 대역폭"
    )
    trx_cost_equivalent = Column(
        Numeric(precision=18, scale=6), nullable=True, comment="TRX 환산 비용"
    )

    # 사용자 정보
    user_id = Column(Integer, nullable=True, comment="사용자 ID")
    from_address = Column(String(50), nullable=True, comment="발신 주소")
    to_address = Column(String(50), nullable=True, comment="수신 주소")
    amount = Column(Numeric(precision=18, scale=6), nullable=True, comment="전송 금액")
    asset = Column(String(20), nullable=True, comment="자산 종류")

    # 메타데이터
    block_number = Column(BigInteger, nullable=True, comment="블록 번호")
    timestamp = Column(DateTime(timezone=True), nullable=False, comment="트랜잭션 시간")
    notes = Column(Text, nullable=True, comment="추가 메모")

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EnergyPriceHistory(Base):
    """에너지 가격 히스토리 테이블"""

    __tablename__ = "energy_price_history"

    id = Column(Integer, primary_key=True, index=True)

    # 가격 정보
    trx_price_usd = Column(
        Numeric(precision=18, scale=8), nullable=False, comment="TRX 가격 (USD)"
    )
    energy_per_trx = Column(BigInteger, nullable=False, comment="TRX당 획득 가능한 에너지")
    bandwidth_per_trx = Column(BigInteger, nullable=False, comment="TRX당 획득 가능한 대역폭")

    # 네트워크 상태
    total_frozen_trx = Column(
        Numeric(precision=18, scale=6), nullable=True, comment="전체 네트워크 freeze TRX"
    )
    energy_utilization = Column(
        Numeric(precision=5, scale=2), nullable=True, comment="네트워크 에너지 사용률 (%)"
    )

    # 비용 분석
    usdt_transfer_cost = Column(
        Numeric(precision=18, scale=6), nullable=True, comment="USDT 전송 비용 (TRX)"
    )
    trx_transfer_cost = Column(
        Numeric(precision=18, scale=6), nullable=True, comment="TRX 전송 비용 (TRX)"
    )

    # 기록 시간
    recorded_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    source = Column(String(50), nullable=True, comment="데이터 소스 (API, Manual)")

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
