"""
트랜잭션 모니터링 서비스.
트랜잭션 모니터링 및 이상 활동 탐지를 담당합니다.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction, TransactionDirection, TransactionStatus
from app.schemas.admin import (
    PaginatedTransactionsResponse,
    SuspiciousActivityResponse,
    TransactionMonitorResponse,
)


class TransactionMonitoringService:
    """트랜잭션 모니터링 서비스 클래스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_transaction_monitor(
        self,
        page: int = 1,
        size: int = 50,
        status: Optional[str] = None,
        direction: Optional[str] = None,
        hours: int = 24,
        user_id: Optional[int] = None,
    ) -> PaginatedTransactionsResponse:
        """트랜잭션 모니터링 데이터 조회"""

        time_filter = datetime.now() - timedelta(hours=hours)

        # 기본 쿼리
        query = select(Transaction).filter(Transaction.created_at >= time_filter)
        count_query = select(func.count(Transaction.id)).filter(
            Transaction.created_at >= time_filter
        )

        # 필터 조건 적용
        conditions = []

        if status:
            try:
                status_enum = TransactionStatus(status)
                conditions.append(Transaction.status == status_enum)
            except ValueError:
                pass  # 잘못된 status는 무시

        if direction:
            try:
                direction_enum = TransactionDirection(direction)
                conditions.append(Transaction.direction == direction_enum)
            except ValueError:
                pass  # 잘못된 direction은 무시

        if conditions:
            query = query.filter(and_(*conditions))
            count_query = count_query.filter(and_(*conditions))

        # 총 개수 조회
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 페이지네이션 적용
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(desc(Transaction.created_at))

        # 트랜잭션 목록 조회
        result = await self.db.execute(query)
        transactions = result.scalars().all()

        # TransactionMonitorResponse 객체로 변환
        transaction_items = []
        for tx in transactions:
            transaction_items.append(
                TransactionMonitorResponse(
                    id=int(tx.id),  # type: ignore
                    user_id=int(tx.user_id),  # type: ignore
                    user_email=f"user_{tx.user_id}@example.com",  # 임시 이메일
                    transaction_type=str(tx.type),
                    direction=str(tx.direction),
                    amount=tx.amount,  # type: ignore
                    asset=str(tx.asset),  # type: ignore
                    status=str(tx.status),
                    created_at=tx.created_at,  # type: ignore
                    tx_hash=tx.tx_hash,  # type: ignore
                    reference_id=tx.reference_id,  # type: ignore
                )
            )

        # 페이지네이션 응답 생성
        return PaginatedTransactionsResponse(
            items=transaction_items,
            total=total,
            page=page,
            size=size,
            has_next=offset + size < total,
            has_prev=page > 1,
        )

    async def get_suspicious_activities(
        self,
        page: int = 1,
        size: int = 20,
        severity: Optional[str] = None,
        hours: int = 24,
    ) -> List[SuspiciousActivityResponse]:
        """의심스러운 활동 조회"""

        # 간단한 구현 예시 - 실제로는 더 복잡한 로직 필요
        time_filter = datetime.now() - timedelta(hours=hours)

        # 큰 금액 트랜잭션 탐지 (예시)
        large_amount_threshold = Decimal("10000")
        large_transactions = await self.db.execute(
            select(Transaction)
            .filter(
                and_(
                    Transaction.created_at >= time_filter,
                    Transaction.amount >= large_amount_threshold,
                    Transaction.status == TransactionStatus.COMPLETED,
                )
            )
            .limit(size)
        )

        suspicious_activities = []
        for tx in large_transactions.scalars():
            suspicious_activities.append(
                SuspiciousActivityResponse(
                    user_id=getattr(tx, "user_id", 0),
                    user_email=f"user_{getattr(tx, 'user_id', 0)}@example.com",  # 임시 이메일
                    activity_type="LARGE_TRANSACTION",
                    risk_score=7,  # 중간 위험도
                    description=f"Large transaction: {getattr(tx, 'amount', 0)}",
                    detected_at=getattr(tx, "created_at", datetime.utcnow()),
                    amount=getattr(tx, "amount", None),
                    transaction_count=1,
                )
            )

        return suspicious_activities[:size]
