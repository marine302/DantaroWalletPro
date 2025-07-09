"""
통합 출금 서비스
모든 출금 관련 서비스를 통합하여 제공합니다.
기존 코드와의 호환성을 유지하기 위해 필요합니다.
"""
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from app.models.withdrawal import Withdrawal, WithdrawalPriority, WithdrawalStatus
from app.services.withdrawal.processing_service import WithdrawalProcessingService
from app.services.withdrawal.query_service import WithdrawalQueryService
from app.services.withdrawal.request_service import WithdrawalRequestService
from sqlalchemy.ext.asyncio import AsyncSession


class WithdrawalService(
    WithdrawalRequestService, WithdrawalProcessingService, WithdrawalQueryService
):
    """
    통합 출금 서비스
    WithdrawalRequestService, WithdrawalProcessingService, WithdrawalQueryService를 상속하여
    모든 출금 관련 기능을 제공합니다.
    """

    def __init__(self, db: AsyncSession):
        super().__init__(db)
