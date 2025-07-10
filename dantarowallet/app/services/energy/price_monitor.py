"""
에너지 가격 모니터링 모듈
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.models.energy_pool import EnergyPriceHistory
from app.core.logging import setup_logging

logger = setup_logging()


class EnergyPriceMonitor:
    """에너지 가격 모니터링"""
    
    def __init__(self, db: AsyncSession, redis_client=None):
        self.db = db
        self.redis_client = redis_client
    
    async def get_current_price(self) -> Decimal:
        """현재 에너지 가격 조회"""
        try:
            result = await self.db.execute(
                select(EnergyPriceHistory)
                .order_by(desc(EnergyPriceHistory.created_at))
                .limit(1)
            )
            
            latest_price = result.scalar_one_or_none()
            
            if latest_price:
                return latest_price.price_per_unit
            else:
                # 기본 가격 설정 (1 TRX = 1000 Energy)
                default_price = Decimal('0.001')
                await self.record_price(default_price)
                return default_price
                
        except Exception as e:
            logger.error(f"❌ 현재 에너지 가격 조회 실패: {e}")
            return Decimal('0.001')  # 기본 가격
    
    async def get_price_history(
        self,
        days: int = 30,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """가격 히스토리 조회"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            result = await self.db.execute(
                select(EnergyPriceHistory)
                .where(EnergyPriceHistory.created_at >= start_date)
                .order_by(desc(EnergyPriceHistory.created_at))
                .limit(limit)
            )
            
            history = result.scalars().all()
            
            return [
                {
                    "id": record.id,
                    "price_per_unit": float(record.price_per_unit),
                    "trx_price": float(record.trx_price) if record.trx_price else 0.0,
                    "source": record.source or "system",
                    "created_at": record.created_at,
                    "is_peak": False  # 피크 시간 계산 필요
                }
                for record in history
            ]
            
        except Exception as e:
            logger.error(f"❌ 가격 히스토리 조회 실패: {e}")
            return []
    
    async def record_price(
        self,
        price_per_unit: Decimal,
        trx_price: Optional[Decimal] = None,
        source: str = "system"
    ) -> bool:
        """가격 기록"""
        try:
            price_record = EnergyPriceHistory(
                price_per_unit=price_per_unit,
                trx_price=trx_price or Decimal('0.1'),  # 기본 TRX 가격
                source=source,
                created_at=datetime.utcnow()
            )
            
            self.db.add(price_record)
            await self.db.commit()
            
            logger.info(f"✅ 에너지 가격 기록 완료: {price_per_unit}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 에너지 가격 기록 실패: {e}")
            await self.db.rollback()
            return False
    
    async def get_price_trend(self, days: int = 7) -> Dict[str, Any]:
        """가격 트렌드 분석"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            result = await self.db.execute(
                select(
                    func.avg(EnergyPriceHistory.price_per_unit).label("avg_price"),
                    func.min(EnergyPriceHistory.price_per_unit).label("min_price"),
                    func.max(EnergyPriceHistory.price_per_unit).label("max_price"),
                    func.count(EnergyPriceHistory.id).label("record_count")
                ).where(
                    EnergyPriceHistory.created_at >= start_date
                )
            )
            
            stats = result.first()
            
            return {
                "period_days": days,
                "avg_price": float(getattr(stats, 'avg_price', 0) or 0),
                "min_price": float(getattr(stats, 'min_price', 0) or 0),
                "max_price": float(getattr(stats, 'max_price', 0) or 0),
                "record_count": getattr(stats, 'record_count', 0) or 0,
                "trend": "stable",  # 분석 로직 필요
                "prediction": "stable"  # 예측 로직 필요
            }
            
        except Exception as e:
            logger.error(f"❌ 가격 트렌드 분석 실패: {e}")
            return {
                "period_days": days,
                "error": str(e)
            }