"""
본사 지갑 모델 - 문서 #40 기반
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, Boolean, BigInteger
from decimal import Decimal
from datetime import datetime
from app.models.base import BaseModel
import enum

class CompanyWalletType(enum.Enum):
    """본사 지갑 유형"""
    REVENUE = "revenue"          # 수익금 수신 지갑
    STAKING = "staking"         # 스테이킹 지갑
    OPERATING = "operating"     # 운영비 지갑

class CompanyWallet(BaseModel):
    """본사 지갑 정보"""

    wallet_type = Column(Enum(CompanyWalletType), unique=True, nullable=False)
    address = Column(String(34), unique=True, nullable=False)

    # 잔액 정보
    trx_balance = Column(Numeric(20, 6), default=0)
    usdt_balance = Column(Numeric(20, 6), default=0)

    # 스테이킹 정보 (스테이킹 지갑용)
    staked_amount = Column(Numeric(20, 6), default=0)
    available_energy = Column(BigInteger, default=0)
    energy_limit = Column(BigInteger)
    last_stake_at = Column(DateTime)
    next_unstake_available_at = Column(DateTime)

    # 상태
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<CompanyWallet {self.wallet_type.value} {self.address}>"
