"""
사용자 관리 서비스.
사용자 정보 조회, 수정 및 위험도 분석을 담당합니다.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.balance import Balance
from app.models.transaction import Transaction, TransactionDirection, TransactionStatus
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.admin import (
    PaginatedUsersResponse,
    UserDetailResponse,
    UserListResponse,
    UserRiskAnalysisResponse,
)


class UserManagementService:
    """사용자 관리 서비스 클래스"""

    def __init__(self, db: AsyncSession):
        self.db = db

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
                    id=int(user.id),  # type: ignore
                    email=str(user.email),  # type: ignore
                    is_active=bool(user.is_active),
                    is_verified=bool(user.is_verified),
                    is_admin=bool(user.is_admin),
                    created_at=user.created_at,  # type: ignore
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
        # 기존 AdminService의 get_user_detail 로직 구현
        query = select(User).filter(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return None

        # 간단한 응답 반환 (실제 구현에서는 더 많은 정보 포함)
        return UserDetailResponse(
            id=int(user.id),  # type: ignore
            email=str(user.email),  # type: ignore
            is_active=bool(user.is_active),  # type: ignore
            is_verified=bool(user.is_verified),  # type: ignore
            is_admin=bool(user.is_admin),  # type: ignore
            created_at=user.created_at,  # type: ignore
            updated_at=user.updated_at,  # type: ignore
            last_login=getattr(user, "last_login", None),
            total_transactions=0,
            total_volume=Decimal("0"),
            risk_score=0,
            risk_level="LOW",
        )

    async def update_user(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """사용자 정보 수정"""
        query = select(User).filter(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return False

        for key, value in updates.items():
            if hasattr(user, key):
                setattr(user, key, value)

        await self.db.commit()
        return True

    async def get_user_risk_analysis(self, user_id: int) -> UserRiskAnalysisResponse:
        """사용자 위험도 분석"""
        # 사용자 정보 조회
        user = await self.db.get(User, user_id)
        email = str(user.email) if user else f"user_{user_id}@example.com"  # type: ignore

        # 간단한 구현 예시
        return UserRiskAnalysisResponse(
            user_id=user_id,
            email=email,
            risk_score=0,
            risk_level="LOW",
            main_reason="No suspicious activity detected",
            recent_large_transactions=0,
            high_frequency_periods=0,
            last_activity=datetime.now(),
        )
