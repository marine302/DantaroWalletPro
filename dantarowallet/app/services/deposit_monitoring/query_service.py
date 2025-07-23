"""
트랜잭션 조회 관련 서비스
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.deposit import Deposit
from app.models.user import User
from app.models.wallet import Wallet


class DepositQueryService:
    """입금 트랜잭션 조회 서비스"""

    @staticmethod
    async def get_pending_deposits(
        db: AsyncSession, cutoff_time: Optional[datetime] = None
    ) -> List[Deposit]:
        """
        처리 중인 입금 트랜잭션 조회

        Args:
            db: 데이터베이스 세션
            cutoff_time: 특정 시간 이후의 트랜잭션만 조회

        Returns:
            처리 중인 입금 트랜잭션 목록
        """
        query = select(Deposit).filter(Deposit.status == "pending")

        if cutoff_time:
            query = query.filter(Deposit.created_at >= cutoff_time)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_active_wallets(db: AsyncSession) -> List[Wallet]:
        """
        활성화된 지갑 조회

        Args:
            db: 데이터베이스 세션

        Returns:
            활성화된 지갑 목록
        """
        query = (
            select(Wallet)
            .filter(Wallet.is_active == True)
            .options(selectinload(Wallet.user))
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_deposits_by_tx_hash(db: AsyncSession, tx_hash: str) -> List[Deposit]:
        """
        트랜잭션 해시로 입금 내역 조회

        Args:
            db: 데이터베이스 세션
            tx_hash: 트랜잭션 해시

        Returns:
            입금 내역 목록
        """
        query = select(Deposit).filter(Deposit.transaction_hash == tx_hash)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_user_wallets(db: AsyncSession, user_id: int) -> List[Wallet]:
        """
        사용자 ID로 지갑 조회

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID

        Returns:
            지갑 목록
        """
        query = select(Wallet).filter(Wallet.user_id == user_id)
        result = await db.execute(query)
        return list(result.scalars().all())
