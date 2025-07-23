"""
출금 조회 서비스
출금 요청 목록 조회, 상세 조회 등의 기능을 제공합니다.
"""

import logging
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.withdrawal import Withdrawal, WithdrawalPriority, WithdrawalStatus
from app.services.withdrawal.base_service import BaseWithdrawalService

logger = logging.getLogger(__name__)


class WithdrawalQueryService(BaseWithdrawalService):
    """출금 조회 서비스"""

    async def get_pending_withdrawals(
        self,
        status: Optional[WithdrawalStatus] = None,
        priority: Optional[WithdrawalPriority] = None,
    ) -> List[Withdrawal]:
        """대기 중인 출금 목록 조회"""
        query = select(Withdrawal).options(selectinload(Withdrawal.user))

        if status:
            query = query.filter(Withdrawal.status == status.value)
        else:
            # 기본적으로 처리가 필요한 상태들
            query = query.filter(
                Withdrawal.status.in_(
                    [
                        WithdrawalStatus.PENDING.value,
                        WithdrawalStatus.APPROVED.value,
                        WithdrawalStatus.PROCESSING.value,
                    ]
                )
            )

        if priority:
            query = query.filter(Withdrawal.priority == priority.value)

        # 우선순위와 요청 시간 순으로 정렬
        query = query.order_by(
            Withdrawal.priority.desc(), Withdrawal.requested_at.asc()
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_user_withdrawals(
        self,
        user_id: int,
        status: Optional[WithdrawalStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Withdrawal], int]:
        """사용자 출금 내역 조회"""
        query = select(Withdrawal).filter(Withdrawal.user_id == user_id)

        if status:
            query = query.filter(Withdrawal.status == status.value)

        # 전체 개수
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        # 페이지네이션
        query = query.order_by(Withdrawal.requested_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        withdrawals = result.scalars().all()

        return withdrawals, total
