"""
통합 잔고 관리 서비스
모든 잔고 관련 서비스를 통합하여 제공합니다.
기존 코드와의 호환성을 유지하기 위해 필요합니다.
"""
from app.services.balance.adjustment_service import BalanceAdjustmentService
from app.services.balance.query_service import BalanceQueryService
from app.services.balance.transaction_service import BalanceTransactionService
from app.services.balance.transfer_service import BalanceTransferService
from sqlalchemy.ext.asyncio import AsyncSession


class BalanceService(
    BalanceQueryService,
    BalanceTransactionService,
    BalanceTransferService,
    BalanceAdjustmentService,
):
    """
    통합 잔고 관리 서비스
    BalanceQueryService, BalanceTransactionService, BalanceTransferService,
    BalanceAdjustmentService를 상속하여 모든 잔고 관련 기능을 제공합니다.
    """

    def __init__(self, db: AsyncSession):
        super().__init__(db)
