"""
에너지 사용량 추적기 모듈
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import setup_logging
from app.models.energy_pool import EnergyUsageLog

logger = setup_logging()


class EnergyUsageTracker:
    """에너지 사용량 추적기"""

    def __init__(self, db: AsyncSession, redis_client=None):
        self.db = db
        self.redis_client = redis_client

    async def get_usage_stats(
        self,
        pool_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """에너지 사용량 통계 조회"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()

            # 기본 통계 조회
            result = await self.db.execute(
                select(
                    func.sum(EnergyUsageLog.amount).label("total_used"),
                    func.count(EnergyUsageLog.id).label("total_transactions"),
                    func.avg(EnergyUsageLog.amount).label("avg_per_transaction"),
                ).where(
                    EnergyUsageLog.pool_id == pool_id,
                    EnergyUsageLog.created_at >= start_date,
                    EnergyUsageLog.created_at <= end_date,
                )
            )

            stats = result.first()

            return {
                "pool_id": pool_id,
                "period": {"start": start_date, "end": end_date},
                "total_used": getattr(stats, "total_used", 0) or 0,
                "total_transactions": getattr(stats, "total_transactions", 0) or 0,
                "avg_per_transaction": float(
                    getattr(stats, "avg_per_transaction", 0) or 0
                ),
                "daily_average": 0,  # 계산 필요
                "peak_usage": 0,  # 계산 필요
                "efficiency_score": 95.0,
            }

        except Exception as e:
            logger.error(f"❌ 에너지 사용량 통계 조회 실패: {e}")
            return {"pool_id": pool_id, "error": str(e)}

    async def get_usage_logs(
        self,
        pool_id: int,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """에너지 사용량 로그 조회"""
        try:
            query = select(EnergyUsageLog).where(EnergyUsageLog.pool_id == pool_id)

            if user_id:
                query = query.where(EnergyUsageLog.user_id == user_id)

            query = query.order_by(desc(EnergyUsageLog.created_at))
            query = query.limit(limit).offset(offset)

            result = await self.db.execute(query)
            logs = result.scalars().all()

            return [
                {
                    "id": log.id,
                    "pool_id": log.pool_id,
                    "user_id": log.user_id,
                    "amount": log.amount,
                    "transaction_type": log.transaction_type,
                    "transaction_id": log.transaction_id,
                    "created_at": log.created_at,
                    "status": "completed",
                }
                for log in logs
            ]

        except Exception as e:
            logger.error(f"❌ 에너지 사용량 로그 조회 실패: {e}")
            return []

    async def record_usage(
        self,
        pool_id: int,
        user_id: int,
        amount: int,
        transaction_type: str,
        transaction_id: str,
    ) -> bool:
        """에너지 사용량 기록"""
        try:
            usage_log = EnergyUsageLog(
                pool_id=pool_id,
                user_id=user_id,
                amount=amount,
                transaction_type=transaction_type,
                transaction_id=transaction_id,
                created_at=datetime.utcnow(),
            )

            self.db.add(usage_log)
            await self.db.commit()

            logger.info(f"✅ 에너지 사용량 기록 완료: {amount} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 에너지 사용량 기록 실패: {e}")
            await self.db.rollback()
            return False
