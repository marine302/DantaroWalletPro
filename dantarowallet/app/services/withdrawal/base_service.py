"""
출금 서비스의 기본 클래스
공통 로직, 초기화, 기본 설정 등을 정의합니다.
"""
import logging
from decimal import Decimal

from app.models.withdrawal import WithdrawalPriority
from app.services.balance_service import BalanceService
from app.services.wallet_service import WalletService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BaseWithdrawalService:
    """출금 서비스 기본 클래스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.balance_service = BalanceService(db)
        self.wallet_service = WalletService(db)

        # 출금 정책
        self.min_withdrawal = Decimal("10.0")  # 최소 출금액
        self.max_withdrawal_per_tx = Decimal("10000.0")  # 1회 최대
        self.max_withdrawal_per_day = Decimal("20000.0")  # 1일 최대
        self.withdrawal_fee = Decimal("1.0")  # 고정 수수료

    def _determine_priority(self, amount: Decimal) -> WithdrawalPriority:
        """금액에 따른 우선순위 결정"""
        if amount >= 5000:
            return WithdrawalPriority.URGENT
        elif amount >= 1000:
            return WithdrawalPriority.HIGH
        elif amount >= 100:
            return WithdrawalPriority.NORMAL
        else:
            return WithdrawalPriority.LOW
