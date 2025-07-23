"""
대시보드 관련 Pydantic 스키마
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class DashboardOverview(BaseModel):
    """대시보드 개요 정보"""

    model_config = {"from_attributes": True}

    total_balance: Decimal
    total_wallets: int
    total_transactions: int
    pending_transactions: int
    last_transaction_date: Optional[datetime]
    monthly_volume: Decimal


class RecentTransactionResponse(BaseModel):
    """최근 거래 응답"""

    model_config = {"from_attributes": True}

    id: int
    transaction_type: str
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
    wallet_address: str


class BalanceHistoryResponse(BaseModel):
    """잔고 변화 이력 응답"""

    model_config = {"from_attributes": True}

    date: datetime
    balance: Decimal
    change: Decimal


class WalletStatsResponse(BaseModel):
    """지갑 통계 응답"""

    model_config = {"from_attributes": True}

    active_wallets: int
    inactive_wallets: int
    total_received: Decimal
    total_sent: Decimal
    average_balance: Decimal
    wallet_distribution: List[dict]
