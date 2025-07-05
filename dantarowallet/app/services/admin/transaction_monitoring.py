"""
트랜잭션 모니터링 서비스.
트랜잭션 모니터링 및 이상 활동 탐지를 담당합니다.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.models.transaction import Transaction, TransactionDirection, TransactionStatus
from app.schemas.admin import (
    PaginatedTransactionsResponse,
    SuspiciousActivityResponse,
    TransactionMonitorResponse,
)
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


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
    ) -> TransactionMonitorResponse:
        """트랜잭션 모니터링 데이터 조회"""
        
        # 시간 범위 설정
        time_filter = datetime.now() - timedelta(hours=hours)
        
        # 기본 쿼리
        query = select(Transaction).filter(Transaction.created_at >= time_filter)
        count_query = select(func.count(Transaction.id)).filter(Transaction.created_at >= time_filter)
        
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
        
        # 통계 정보 계산
        stats_query = select(
            func.count(Transaction.id).label('total_count'),
            func.sum(Transaction.amount).label('total_volume'),
            func.avg(Transaction.amount).label('avg_amount')
        ).filter(Transaction.created_at >= time_filter)
        
        if conditions:
            stats_query = stats_query.filter(and_(*conditions))
            
        stats_result = await self.db.execute(stats_query)
        stats = stats_result.first()
        
        return TransactionMonitorResponse(
            transactions=transactions,
            total_count=stats.total_count if stats else 0,
            total_volume=stats.total_volume if stats and stats.total_volume else Decimal("0"),
            avg_amount=stats.avg_amount if stats and stats.avg_amount else Decimal("0"),
            page=page,
            size=size,
            has_next=offset + size < total,
            has_prev=page > 1
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
            select(Transaction).filter(
                and_(
                    Transaction.created_at >= time_filter,
                    Transaction.amount >= large_amount_threshold,
                    Transaction.status == TransactionStatus.COMPLETED
                )
            ).limit(size)
        )
        
        suspicious_activities = []
        for tx in large_transactions.scalars():
            suspicious_activities.append(
                SuspiciousActivityResponse(
                    id=f"large_tx_{tx.id}",
                    type="LARGE_TRANSACTION",
                    severity="MEDIUM",
                    description=f"Large transaction: {tx.amount}",
                    user_id=tx.user_id,
                    transaction_id=tx.id,
                    detected_at=tx.created_at,
                    status="PENDING"
                )
            )
        
        return suspicious_activities[:size]
