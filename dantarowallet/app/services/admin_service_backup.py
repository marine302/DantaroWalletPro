"""
관리자 패널 서비스.
관리자 전용 기능들의 비즈니스 로직을 담당합니다.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from app.models.balance import Balance
from app.models.transaction import Transaction, TransactionDirection, TransactionStatus
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.admin import (
    PaginatedTransactionsResponse,
    PaginatedUsersResponse,
    SuspiciousActivityResponse,
    SystemRiskSummaryResponse,
    SystemStatsResponse,
    TransactionMonitorResponse,
    UserDetailResponse,
    UserListResponse,
    UserRiskAnalysisResponse,
)
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class AdminService:
    """관리자 패널 서비스 클래스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_system_stats(self) -> SystemStatsResponse:
        """시스템 전체 통계 조회"""

        # 총 사용자 수
        total_users_result = await self.db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar() or 0

        # 활성 사용자 수
        active_users_result = await self.db.execute(
            select(func.count(User.id)).filter(User.is_active == True)
        )
        active_users = active_users_result.scalar() or 0

        # 총 지갑 수
        total_wallets_result = await self.db.execute(select(func.count(Wallet.id)))
        total_wallets = total_wallets_result.scalar() or 0

        # 총 거래 수
        total_transactions_result = await self.db.execute(
            select(func.count(Transaction.id))
        )
        total_transactions = total_transactions_result.scalar() or 0

        # 시스템 총 잔고
        total_balance_result = await self.db.execute(select(func.sum(Balance.amount)))
        total_balance = total_balance_result.scalar() or Decimal("0")

        # 일일 거래 수 (24시간)
        day_ago = datetime.now() - timedelta(days=1)
        daily_transactions_result = await self.db.execute(
            select(func.count(Transaction.id)).filter(Transaction.created_at >= day_ago)
        )
        daily_transactions = daily_transactions_result.scalar() or 0

        # 월간 거래량 (30일)
        month_ago = datetime.now() - timedelta(days=30)
        monthly_volume_result = await self.db.execute(
            select(func.sum(Transaction.amount)).filter(
                Transaction.created_at >= month_ago,
                Transaction.status == TransactionStatus.COMPLETED,
            )
        )
        monthly_volume = monthly_volume_result.scalar() or Decimal("0")

        return SystemStatsResponse(
            total_users=total_users,
            active_users=active_users,
            total_wallets=total_wallets,
            total_transactions=total_transactions,
            total_balance=total_balance,
            daily_transactions=daily_transactions,
            monthly_volume=monthly_volume,
        )

    async def get_users_list(
        self,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_admin: Optional[bool] = None,
    ) -> PaginatedUsersResponse:
        """사용자 목록 조회 (페이지네이션)"""

        # 기본 쿼리
        query = select(User)
        count_query = select(func.count(User.id))

        # 필터 조건 적용
        conditions = []

        if search:
            conditions.append(User.email.ilike(f"%{search}%"))

        if is_active is not None:
            conditions.append(User.is_active == is_active)

        if is_admin is not None:
            conditions.append(User.is_admin == is_admin)

        if conditions:
            query = query.filter(and_(*conditions))
            count_query = count_query.filter(and_(*conditions))

        # 총 개수 조회
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 페이지네이션 적용
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(desc(User.created_at))

        # 사용자 목록 조회
        result = await self.db.execute(query)
        users = result.scalars().all()

        # 각 사용자의 추가 정보 조회
        user_list = []
        for user in users:
            # 사용자별 총 잔고
            balance_result = await self.db.execute(
                select(func.sum(Balance.amount)).filter(Balance.user_id == user.id)
            )
            total_balance = balance_result.scalar()

            # 사용자별 지갑 수
            wallet_count_result = await self.db.execute(
                select(func.count(Wallet.id)).filter(Wallet.user_id == user.id)
            )
            wallet_count = wallet_count_result.scalar() or 0

            user_list.append(
                UserListResponse(
                    id=user.id,
                    email=user.email,
                    is_active=bool(user.is_active),
                    is_verified=bool(user.is_verified),
                    is_admin=bool(user.is_admin),
                    created_at=user.created_at,
                    total_balance=total_balance,
                    wallet_count=wallet_count,
                )
            )

        return PaginatedUsersResponse(
            items=user_list,
            total=total,
            page=page,
            size=size,
            has_next=offset + size < total,
            has_prev=page > 1,
        )

    async def get_user_detail(self, user_id: int) -> Optional[UserDetailResponse]:
        """사용자 상세 정보 조회"""

        # 사용자 조회
        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return None

        # 총 잔고
        balance_result = await self.db.execute(
            select(func.sum(Balance.amount)).filter(Balance.user_id == user_id)
        )
        total_balance = balance_result.scalar() or Decimal("0")

        # 지갑 수
        wallet_count_result = await self.db.execute(
            select(func.count(Wallet.id)).filter(Wallet.user_id == user_id)
        )
        wallet_count = wallet_count_result.scalar() or 0

        # 거래 수
        transaction_count_result = await self.db.execute(
            select(func.count(Transaction.id)).filter(Transaction.user_id == user_id)
        )
        transaction_count = transaction_count_result.scalar() or 0

        # 마지막 거래 날짜
        last_tx_result = await self.db.execute(
            select(Transaction.created_at)
            .filter(Transaction.user_id == user_id)
            .order_by(desc(Transaction.created_at))
            .limit(1)
        )
        last_transaction_date = last_tx_result.scalar_one_or_none()

        return UserDetailResponse(
            id=user.id,
            email=user.email,
            is_active=bool(user.is_active),
            is_verified=bool(user.is_verified),
            is_admin=bool(user.is_admin),
            tron_address=user.tron_address,
            created_at=user.created_at,
            updated_at=user.updated_at,
            total_balance=total_balance,
            wallet_count=wallet_count,
            transaction_count=transaction_count,
            last_transaction_date=last_transaction_date,
        )

    async def update_user(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """사용자 정보 수정"""

        # 사용자 조회
        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return False

        # 업데이트 적용
        for key, value in updates.items():
            if hasattr(user, key):
                setattr(user, key, value)

        user.updated_at = datetime.now()

        try:
            await self.db.commit()
            return True
        except Exception:
            await self.db.rollback()
            return False

    async def get_transaction_monitor(
        self,
        page: int = 1,
        size: int = 50,
        status: Optional[str] = None,
        user_id: Optional[int] = None,
        hours: int = 24,
    ) -> PaginatedTransactionsResponse:
        """거래 모니터링 (최근 거래 내역)"""

        # 시간 범위 설정
        time_threshold = datetime.now() - timedelta(hours=hours)

        # 기본 쿼리
        query = (
            select(Transaction, User.email)
            .join(User, Transaction.user_id == User.id)
            .filter(Transaction.created_at >= time_threshold)
        )

        count_query = select(func.count(Transaction.id)).filter(
            Transaction.created_at >= time_threshold
        )

        # 필터 조건
        conditions = []

        if status:
            conditions.append(Transaction.status == status)

        if user_id:
            conditions.append(Transaction.user_id == user_id)

        if conditions:
            query = query.filter(and_(*conditions))
            count_query = count_query.filter(and_(*conditions))

        # 총 개수
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # 페이지네이션
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(desc(Transaction.created_at))

        # 거래 목록 조회
        result = await self.db.execute(query)
        transactions = result.all()

        transaction_list = []
        for tx, user_email in transactions:
            transaction_list.append(
                TransactionMonitorResponse(
                    id=tx.id,
                    user_id=tx.user_id,
                    user_email=user_email,
                    transaction_type=str(tx.type),
                    direction=str(tx.direction),
                    amount=tx.amount,
                    asset=tx.asset,
                    status=str(tx.status),
                    created_at=tx.created_at,
                    tx_hash=tx.tx_hash,
                    reference_id=tx.reference_id,
                )
            )

        return PaginatedTransactionsResponse(
            items=transaction_list,
            total=total,
            page=page,
            size=size,
            has_next=offset + size < total,
            has_prev=page > 1,
        )

    async def get_suspicious_activities(
        self, limit: int = 20
    ) -> List[SuspiciousActivityResponse]:
        """의심스러운 활동 탐지"""

        activities = []
        current_time = datetime.now()

        # 1. 대량 거래 (1시간 내 10회 이상)
        hour_ago = current_time - timedelta(hours=1)
        high_frequency_result = await self.db.execute(
            select(
                Transaction.user_id,
                User.email,
                func.count(Transaction.id).label("tx_count"),
                func.sum(Transaction.amount).label("total_amount"),
            )
            .join(User, Transaction.user_id == User.id)
            .filter(Transaction.created_at >= hour_ago)
            .group_by(Transaction.user_id, User.email)
            .having(func.count(Transaction.id) >= 10)
        )

        for row in high_frequency_result:
            activities.append(
                SuspiciousActivityResponse(
                    user_id=row.user_id,
                    user_email=row.email,
                    activity_type="HIGH_FREQUENCY_TRANSACTIONS",
                    risk_score=80,
                    description=f"1시간 내 {row.tx_count}회 거래",
                    detected_at=current_time,
                    amount=row.total_amount,
                    transaction_count=row.tx_count,
                )
            )

        # 2. 대액 거래 (단일 거래 100,000 이상)
        large_tx_result = await self.db.execute(
            select(Transaction, User.email)
            .join(User, Transaction.user_id == User.id)
            .filter(
                Transaction.amount >= Decimal("100000"),
                Transaction.created_at >= current_time - timedelta(days=1),
            )
            .order_by(desc(Transaction.created_at))
            .limit(10)
        )

        for tx, user_email in large_tx_result:
            activities.append(
                SuspiciousActivityResponse(
                    user_id=tx.user_id,
                    user_email=user_email,
                    activity_type="LARGE_AMOUNT_TRANSACTION",
                    risk_score=60,
                    description=f"대액 거래: {tx.amount} {tx.asset}",
                    detected_at=tx.created_at,
                    amount=tx.amount,
                    transaction_count=1,
                )
            )

        # 위험도 순으로 정렬
        activities.sort(key=lambda x: x.risk_score, reverse=True)

        return activities[:limit]

    async def get_user_risk_analysis(self, user_id: int) -> UserRiskAnalysisResponse:
        """특정 사용자의 리스크 분석"""
        # 최근 30일 거래
        from datetime import datetime, timedelta

        now = datetime.now()
        month_ago = now - timedelta(days=30)
        # 최근 대액 거래
        large_tx_result = await self.db.execute(
            select(func.count())
            .select_from(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.amount >= 10000,
                Transaction.created_at >= month_ago,
            )
        )
        recent_large_transactions = large_tx_result.scalar() or 0
        # 고빈도 거래(1시간 내 5회 이상)
        hour_ago = now - timedelta(hours=1)
        freq_result = await self.db.execute(
            select(func.count())
            .select_from(Transaction)
            .filter(Transaction.user_id == user_id, Transaction.created_at >= hour_ago)
        )
        high_frequency_periods = 1 if (freq_result.scalar() or 0) >= 5 else 0
        # 마지막 활동
        last_tx_result = await self.db.execute(
            select(Transaction.created_at)
            .filter(Transaction.user_id == user_id)
            .order_by(desc(Transaction.created_at))
            .limit(1)
        )
        last_activity = last_tx_result.scalar_one_or_none()
        # 위험 점수 계산
        risk_score = 0
        main_reason = ""
        if recent_large_transactions >= 3:
            risk_score += 50
            main_reason = "최근 대액 거래 다수"
        if high_frequency_periods:
            risk_score += 30
            main_reason = "고빈도 거래"
        if not main_reason:
            main_reason = "정상"
        risk_level = "low"
        if risk_score >= 70:
            risk_level = "high"
        elif risk_score >= 30:
            risk_level = "medium"
        # 사용자 이메일
        user_result = await self.db.execute(
            select(User.email).filter(User.id == user_id)
        )
        email = user_result.scalar_one_or_none() or ""
        return UserRiskAnalysisResponse(
            user_id=user_id,
            email=email,
            risk_score=risk_score,
            risk_level=risk_level,
            main_reason=main_reason,
            recent_large_transactions=recent_large_transactions,
            high_frequency_periods=high_frequency_periods,
            last_activity=last_activity,
        )

    async def get_system_risk_summary(self) -> SystemRiskSummaryResponse:
        """시스템 전체 리스크 요약"""
        # 전체 사용자 목록
        users_result = await self.db.execute(select(User))
        users = users_result.scalars().all()
        high, medium, low = 0, 0, 0
        for user_id, email in users:
            analysis = await self.get_user_risk_analysis(user_id)
            if analysis.risk_level == "high":
                high += 1
            elif analysis.risk_level == "medium":
                medium += 1
            else:
                low += 1
        return SystemRiskSummaryResponse(
            high_risk_users=high,
            medium_risk_users=medium,
            low_risk_users=low,
            total_users=len(users),
            updated_at=datetime.now(),
        )
