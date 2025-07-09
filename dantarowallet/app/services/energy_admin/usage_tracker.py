"""
에너지 사용량 추적 서비스
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update

from app.models.energy_pool import EnergyPoolModel, EnergyUsageLog
from app.models.transaction import Transaction
from app.models.user import User
from app.core.logger import get_logger

logger = get_logger(__name__)


class EnergyUsageTracker:
    def __init__(self, db: AsyncSession, redis_client):
        self.db = db
        self.redis = redis_client

    async def record_energy_usage(
        self,
        pool_id: int,
        transaction_id: int,
        energy_consumed: int,
        transaction_type: str,
        user_id: int
    ) -> EnergyUsageLog:
        """에너지 사용 기록"""
        try:
            # 현재 에너지 가격 조회
            energy_price = await self.get_current_energy_price()
            actual_cost = Decimal(energy_consumed) * energy_price

            # 사용 로그 생성
            usage_log = EnergyUsageLog(
                pool_id=pool_id,
                transaction_id=transaction_id,
                energy_consumed=energy_consumed,
                transaction_type=transaction_type,
                user_id=user_id,
                energy_price=energy_price,
                actual_cost=actual_cost
            )

            self.db.add(usage_log)

            # 에너지 풀 업데이트
            pool = await self.db.get(EnergyPoolModel, pool_id)
            if pool:
                # SQLAlchemy update 쿼리 사용
                await self.db.execute(
                    update(EnergyPoolModel)
                    .where(EnergyPoolModel.id == pool_id)
                    .values(
                        used_energy=EnergyPoolModel.used_energy + energy_consumed,
                        available_energy=EnergyPoolModel.available_energy - energy_consumed
                    )
                )

            # 일일 통계 업데이트
            await self.update_daily_stats(pool_id, energy_consumed)

            await self.db.commit()

            # 실시간 모니터링을 위한 이벤트 발행
            await self.publish_usage_event(usage_log)

            logger.info(f"에너지 사용 기록 완료: {energy_consumed} energy (pool:{pool_id}, tx:{transaction_id})")
            return usage_log

        except Exception as e:
            logger.error(f"에너지 사용 기록 실패: {str(e)}")
            await self.db.rollback()
            raise

    async def get_usage_statistics(
        self,
        pool_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """에너지 사용 통계 조회"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        # 기간별 사용량 집계
        daily_usage_query = (
            select(
                func.date(EnergyUsageLog.used_at).label('date'),
                func.sum(EnergyUsageLog.energy_consumed).label('total_energy'),
                func.sum(EnergyUsageLog.actual_cost).label('total_cost'),
                func.count(EnergyUsageLog.id).label('transaction_count')
            )
            .where(
                EnergyUsageLog.pool_id == pool_id,
                EnergyUsageLog.used_at >= start_date,
                EnergyUsageLog.used_at <= end_date
            )
            .group_by(func.date(EnergyUsageLog.used_at))
            .order_by(func.date(EnergyUsageLog.used_at))
        )

        usage_stats_result = await self.db.execute(daily_usage_query)
        usage_stats = usage_stats_result.fetchall()

        # 거래 유형별 통계
        type_stats_query = (
            select(
                EnergyUsageLog.transaction_type,
                func.sum(EnergyUsageLog.energy_consumed).label('total_energy'),
                func.count(EnergyUsageLog.id).label('count')
            )
            .where(
                EnergyUsageLog.pool_id == pool_id,
                EnergyUsageLog.used_at >= start_date,
                EnergyUsageLog.used_at <= end_date
            )
            .group_by(EnergyUsageLog.transaction_type)
        )

        type_stats_result = await self.db.execute(type_stats_query)
        type_stats = type_stats_result.fetchall()

        # 시간대별 사용 패턴
        hourly_stats_query = (
            select(
                func.extract('hour', EnergyUsageLog.used_at).label('hour'),
                func.avg(EnergyUsageLog.energy_consumed).label('avg_energy')
            )
            .where(
                EnergyUsageLog.pool_id == pool_id,
                EnergyUsageLog.used_at >= start_date,
                EnergyUsageLog.used_at <= end_date
            )
            .group_by(func.extract('hour', EnergyUsageLog.used_at))
        )

        hourly_stats_result = await self.db.execute(hourly_stats_query)
        hourly_stats = hourly_stats_result.fetchall()

        # 결과 포맷팅
        daily_usage_list = []
        for row in usage_stats:
            daily_usage_list.append({
                "date": row.date.isoformat(),
                "total_energy": row.total_energy or 0,
                "total_cost": float(row.total_cost or 0),
                "transaction_count": row.transaction_count or 0
            })

        by_type_list = []
        for row in type_stats:
            by_type_list.append({
                "type": row.transaction_type,
                "total_energy": row.total_energy or 0,
                "count": row.count or 0
            })

        hourly_pattern_list = []
        for row in hourly_stats:
            hourly_pattern_list.append({
                "hour": int(row.hour),
                "avg_energy": float(row.avg_energy or 0)
            })

        # 요약 통계
        total_energy_consumed = sum(row['total_energy'] for row in daily_usage_list)
        total_cost = sum(row['total_cost'] for row in daily_usage_list)
        total_transactions = sum(row['transaction_count'] for row in daily_usage_list)
        avg_energy_per_transaction = (
            total_energy_consumed / total_transactions
        ) if total_transactions > 0 else 0

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "daily_usage": daily_usage_list,
            "by_type": by_type_list,
            "hourly_pattern": hourly_pattern_list,
            "summary": {
                "total_energy_consumed": total_energy_consumed,
                "total_cost": total_cost,
                "total_transactions": total_transactions,
                "avg_energy_per_transaction": avg_energy_per_transaction
            }
        }

    async def get_current_energy_price(self) -> Decimal:
        """현재 에너지 가격 조회"""
        try:
            # 캐시에서 먼저 조회
            cached_price = await self.redis.get("energy_price:current")
            if cached_price:
                price_data = json.loads(cached_price)
                return Decimal(str(price_data['energy_price_trx']))

            # 기본값
            return Decimal('0.000065')

        except Exception as e:
            logger.warning(f"에너지 가격 조회 실패: {str(e)}")
            return Decimal('0.000065')

    async def update_daily_stats(self, pool_id: int, energy_consumed: int):
        """일일 통계 업데이트"""
        try:
            today = datetime.utcnow().date()
            cache_key = f"daily_stats:{pool_id}:{today}"

            # 현재 일일 통계 조회
            current_stats = await self.redis.get(cache_key)
            if current_stats:
                stats = json.loads(current_stats)
                stats['total_consumption'] += energy_consumed
                stats['transaction_count'] += 1
            else:
                stats = {
                    'total_consumption': energy_consumed,
                    'transaction_count': 1,
                    'date': today.isoformat()
                }

            # 캐시 업데이트 (다음 날 자정까지)
            tomorrow = datetime.combine(today + timedelta(days=1), datetime.min.time())
            ttl = int((tomorrow - datetime.utcnow()).total_seconds())

            await self.redis.setex(cache_key, ttl, json.dumps(stats))

        except Exception as e:
            logger.warning(f"일일 통계 업데이트 실패: {str(e)}")

    async def publish_usage_event(self, usage_log: EnergyUsageLog):
        """에너지 사용 이벤트 발행 (실시간 모니터링용)"""
        try:
            event_data = {
                "event_type": "energy_usage",
                "pool_id": usage_log.pool_id,
                "energy_consumed": usage_log.energy_consumed,
                "transaction_type": usage_log.transaction_type,
                "user_id": usage_log.user_id,
                "actual_cost": float(usage_log.actual_cost) if hasattr(usage_log, 'actual_cost') and usage_log.actual_cost is not None else 0,  # type: ignore
                "timestamp": usage_log.used_at.isoformat()
            }

            # Redis pub/sub로 이벤트 발행
            await self.redis.publish("energy_events", json.dumps(event_data))

        except Exception as e:
            logger.warning(f"에너지 사용 이벤트 발행 실패: {str(e)}")

    async def get_top_energy_consumers(
        self,
        pool_id: int,
        days: int = 7,
        limit: int = 10
    ) -> List[Dict]:
        """상위 에너지 소비자 조회"""
        since = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                EnergyUsageLog.user_id,
                func.sum(EnergyUsageLog.energy_consumed).label('total_energy'),
                func.sum(EnergyUsageLog.actual_cost).label('total_cost'),
                func.count(EnergyUsageLog.id).label('transaction_count')
            )
            .where(
                EnergyUsageLog.pool_id == pool_id,
                EnergyUsageLog.used_at >= since,
                EnergyUsageLog.user_id.isnot(None)
            )
            .group_by(EnergyUsageLog.user_id)
            .order_by(func.sum(EnergyUsageLog.energy_consumed).desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        consumers = result.fetchall()

        consumer_list = []
        for row in consumers:
            # 사용자 정보 조회
            user = await self.db.get(User, row.user_id)
            consumer_list.append({
                "user_id": row.user_id,
                "username": user.username if user else f"User_{row.user_id}",
                "total_energy": row.total_energy,
                "total_cost": float(row.total_cost),
                "transaction_count": row.transaction_count,
                "avg_energy_per_tx": row.total_energy / row.transaction_count if row.transaction_count > 0 else 0
            })

        return consumer_list

    async def get_energy_efficiency_report(self, pool_id: int, days: int = 30) -> Dict:
        """에너지 효율성 리포트"""
        since = datetime.utcnow() - timedelta(days=days)

        # 기본 통계
        stats = await self.get_usage_statistics(pool_id, since)

        # 효율성 지표 계산
        peak_hours = sorted(
            stats['hourly_pattern'], 
            key=lambda x: x['avg_energy'], 
            reverse=True
        )[:3]

        off_peak_hours = sorted(
            stats['hourly_pattern'], 
            key=lambda x: x['avg_energy']
        )[:3]

        return {
            "period_days": days,
            "summary": stats['summary'],
            "peak_usage_hours": [h['hour'] for h in peak_hours],
            "off_peak_hours": [h['hour'] for h in off_peak_hours],
            "most_efficient_type": min(
                stats['by_type'], 
                key=lambda x: x['total_energy'] / x['count'] if x['count'] > 0 else float('inf')
            )['type'] if stats['by_type'] else None,
            "recommendations": self._generate_efficiency_recommendations(stats)
        }

    def _generate_efficiency_recommendations(self, stats: Dict) -> List[str]:
        """효율성 개선 권장사항 생성"""
        recommendations = []

        # 사용량 패턴 분석
        if stats['hourly_pattern']:
            peak_hour = max(stats['hourly_pattern'], key=lambda x: x['avg_energy'])
            if peak_hour['avg_energy'] > 20000:  # 임계값
                recommendations.append(f"피크 시간대({peak_hour['hour']}시) 사용량이 높습니다. 분산 처리를 고려해보세요.")

        # 거래 유형별 분석
        if stats['by_type']:
            for tx_type in stats['by_type']:
                avg_energy = tx_type['total_energy'] / tx_type['count'] if tx_type['count'] > 0 else 0
                if avg_energy > 30000:  # 높은 에너지 소비
                    recommendations.append(f"{tx_type['type']} 거래의 에너지 효율성을 검토해보세요.")

        # 일반적인 권장사항
        if stats['summary']['total_energy_consumed'] > 1000000:  # 높은 총 소비량
            recommendations.append("높은 에너지 소비가 감지되었습니다. 에너지 풀 확장을 고려해보세요.")

        return recommendations if recommendations else ["현재 에너지 사용량이 효율적입니다."]
