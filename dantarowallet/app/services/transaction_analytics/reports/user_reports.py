"""
사용자 분석 보고서 생성 모듈
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction_analytics import UserTransactionProfile
from sqlalchemy import func, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class UserReportService:
    """사용자 분석 보고서 생성 서비스"""

    async def generate_user_profile(
        self, db: AsyncSession, user_id: int, days_back: int = 30
    ) -> UserTransactionProfile:
        """사용자 거래 프로필 생성"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)

            # 사용자 기본 정보
            user_info = await self._get_user_info(db, user_id)
            
            # 거래 통계
            transaction_stats = await self._get_user_transaction_stats(
                db, user_id, start_date, end_date
            )
            
            # 활동 패턴
            activity_patterns = await self._get_user_activity_patterns(
                db, user_id, start_date, end_date
            )

            return UserTransactionProfile(
                user_id=user_id,
                user_info=user_info,
                period_start=start_date,
                period_end=end_date,
                transaction_stats=transaction_stats,
                activity_patterns=activity_patterns,
            )

        except Exception as e:
            logger.error(f"사용자 프로필 생성 실패: {str(e)}")
            raise

    async def _get_user_info(self, db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """사용자 기본 정보 조회"""
        result = await db.execute(
            text("""
            SELECT 
                id, email, created_at, is_active,
                (SELECT COUNT(*) FROM transactions WHERE user_id = :user_id) as total_transactions,
                (SELECT SUM(amount) FROM transactions WHERE user_id = :user_id) as total_volume
            FROM users WHERE id = :user_id
            """),
            {"user_id": user_id}
        )
        
        user_row = result.fetchone()
        if not user_row:
            return {}
            
        return {
            "user_id": user_row.id,
            "email": user_row.email,
            "member_since": user_row.created_at.isoformat(),
            "is_active": user_row.is_active,
            "lifetime_transactions": user_row.total_transactions or 0,
            "lifetime_volume": float(user_row.total_volume or 0),
        }

    async def _get_user_transaction_stats(
        self, db: AsyncSession, user_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """사용자 거래 통계"""
        result = await db.execute(
            text("""
            SELECT 
                COUNT(*) as transaction_count,
                SUM(amount) as total_volume,
                AVG(amount) as avg_transaction_size,
                MIN(amount) as min_transaction,
                MAX(amount) as max_transaction,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                SUM(CASE WHEN transaction_type = 'deposit' THEN 1 ELSE 0 END) as deposit_count,
                SUM(CASE WHEN transaction_type = 'withdrawal' THEN 1 ELSE 0 END) as withdrawal_count
            FROM transactions 
            WHERE user_id = :user_id 
            AND created_at >= :start_date 
            AND created_at <= :end_date
            """),
            {"user_id": user_id, "start_date": start_date, "end_date": end_date}
        )
        
        stats = result.fetchone()
        
        return {
            "transaction_count": stats.transaction_count or 0,
            "total_volume": float(stats.total_volume or 0),
            "avg_transaction_size": float(stats.avg_transaction_size or 0),
            "min_transaction": float(stats.min_transaction or 0),
            "max_transaction": float(stats.max_transaction or 0),
            "success_rate": (
                stats.successful_count / stats.transaction_count
                if stats.transaction_count > 0 else 0
            ),
            "deposit_count": stats.deposit_count or 0,
            "withdrawal_count": stats.withdrawal_count or 0,
        }

    async def _get_user_activity_patterns(
        self, db: AsyncSession, user_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """사용자 활동 패턴 분석"""
        # 시간대별 활동
        hourly_result = await db.execute(
            text("""
            SELECT 
                EXTRACT(HOUR FROM created_at) as hour,
                COUNT(*) as transaction_count
            FROM transactions 
            WHERE user_id = :user_id 
            AND created_at >= :start_date 
            AND created_at <= :end_date
            GROUP BY EXTRACT(HOUR FROM created_at)
            ORDER BY hour
            """),
            {"user_id": user_id, "start_date": start_date, "end_date": end_date}
        )
        
        hourly_pattern = {
            row.hour: row.transaction_count 
            for row in hourly_result.fetchall()
        }
        
        # 요일별 활동
        weekday_result = await db.execute(
            text("""
            SELECT 
                EXTRACT(DOW FROM created_at) as weekday,
                COUNT(*) as transaction_count
            FROM transactions 
            WHERE user_id = :user_id 
            AND created_at >= :start_date 
            AND created_at <= :end_date
            GROUP BY EXTRACT(DOW FROM created_at)
            ORDER BY weekday
            """),
            {"user_id": user_id, "start_date": start_date, "end_date": end_date}
        )
        
        weekday_pattern = {
            int(row.weekday): row.transaction_count 
            for row in weekday_result.fetchall()
        }
        
        return {
            "hourly_activity": hourly_pattern,
            "weekday_activity": weekday_pattern,
            "most_active_hour": max(hourly_pattern, key=hourly_pattern.get) if hourly_pattern else 0,
            "most_active_weekday": max(weekday_pattern, key=weekday_pattern.get) if weekday_pattern else 0,
        }

    async def generate_top_users_report(
        self, db: AsyncSession, limit: int = 50, days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """상위 사용자 보고서 생성"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        result = await db.execute(
            text("""
            SELECT 
                u.id,
                u.email,
                COUNT(t.id) as transaction_count,
                SUM(t.amount) as total_volume,
                AVG(t.amount) as avg_transaction_size,
                MAX(t.created_at) as last_transaction
            FROM users u
            LEFT JOIN transactions t ON u.id = t.user_id 
                AND t.created_at >= :start_date 
                AND t.created_at <= :end_date
            GROUP BY u.id, u.email
            HAVING COUNT(t.id) > 0
            ORDER BY total_volume DESC
            LIMIT :limit
            """),
            {"start_date": start_date, "end_date": end_date, "limit": limit}
        )
        
        return [
            {
                "user_id": row.id,
                "email": row.email,
                "transaction_count": row.transaction_count,
                "total_volume": float(row.total_volume or 0),
                "avg_transaction_size": float(row.avg_transaction_size or 0),
                "last_transaction": row.last_transaction.isoformat() if row.last_transaction else None,
            }
            for row in result.fetchall()
        ]
