"""
잔고 조정 서비스
관리자에 의한 잔고 조정 기능을 제공합니다.
"""

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InsufficientBalanceError
from app.models.balance import Balance
from app.models.transaction import (
    Transaction,
    TransactionDirection,
    TransactionStatus,
    TransactionType,
)
from app.services.balance.base_service import BaseBalanceService

logger = logging.getLogger(__name__)


class BalanceAdjustmentService(BaseBalanceService):
    """잔고 조정 서비스"""

    async def adjust_balance(
        self,
        user_id: int,
        amount: Decimal,
        adjustment_type: str,
        description: str,
        admin_id: int,
        asset: str = "USDT",
    ) -> Balance:
        """관리자에 의한 잔고 조정 (입금 시뮬레이션, 보너스 등)"""

        balance = await self.get_or_create_balance(user_id, asset)

        # 금액 적용
        if amount > 0:
            balance.amount += amount
            direction = TransactionDirection.IN
        else:
            if balance.available_amount < abs(amount):
                raise InsufficientBalanceError(
                    required=float(abs(amount)),
                    available=float(balance.available_amount),
                )
            balance.amount += amount  # amount가 음수
            direction = TransactionDirection.OUT

        # 트랜잭션 기록
        tx = Transaction(
            user_id=user_id,
            type=TransactionType.ADJUSTMENT,
            direction=direction,
            status=TransactionStatus.COMPLETED,
            asset=asset,
            amount=abs(amount),
            fee=Decimal("0"),
            description=description,
            metadata=json.dumps(
                {
                    "adjustment_type": adjustment_type,
                    "admin_id": admin_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
        )

        self.db.add(tx)
        await self.db.flush()

        logger.info(
            f"Balance adjustment: user={user_id}, amount={amount}, "
            f"type={adjustment_type}, admin={admin_id}"
        )

        return balance
