"""
에너지 가격 모니터링 서비스
"""
import httpx
import json
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.energy_pool import EnergyPriceHistory
from app.core.logger import get_logger

logger = get_logger(__name__)


class EnergyPriceMonitor:
    def __init__(self, db: AsyncSession, redis_client):
        self.db = db
        self.redis = redis_client
        self.http_client = httpx.AsyncClient()

    async def update_energy_price(self) -> Dict:
        """에너지 가격 업데이트 (외부 소스에서)"""
        try:
            # TRX 가격 조회 (CoinGecko 등)
            trx_price = await self.get_trx_market_price()

            # 에너지 시장 가격 조회 (TRON 에너지 거래소)
            energy_market_data = await self.get_energy_market_data()

            # 네트워크 혼잡도 확인
            network_stats = await self.get_network_statistics()

            # 가격 계산
            energy_price_trx = energy_market_data.get('price_per_energy', 0.000065)
            energy_price_usd = energy_price_trx * trx_price

            # 가격 이력 저장
            price_history = EnergyPriceHistory(
                pool_id=1,  # 기본 풀
                trx_price_usd=Decimal(str(trx_price)),
                energy_price_trx=Decimal(str(energy_price_trx)),
                energy_price_usd=Decimal(str(energy_price_usd)),
                market_demand=self.calculate_market_demand(energy_market_data),
                network_congestion=network_stats.get('congestion_level', 0)
            )

            self.db.add(price_history)
            await self.db.commit()

            # 캐시 업데이트
            await self.redis.setex(
                "energy_price:current",
                300,  # 5분
                json.dumps({
                    "trx_price_usd": float(trx_price),
                    "energy_price_trx": float(energy_price_trx),
                    "energy_price_usd": float(energy_price_usd),
                    "updated_at": datetime.utcnow().isoformat()
                })
            )

            logger.info(f"에너지 가격 업데이트 완료: TRX ${trx_price:.4f}, Energy {energy_price_trx:.8f} TRX")

            return {
                "trx_price_usd": float(trx_price),
                "energy_price_trx": float(energy_price_trx),
                "energy_price_usd": float(energy_price_usd),
                "market_demand": price_history.market_demand,
                "network_congestion": price_history.network_congestion
            }

        except Exception as e:
            logger.error(f"에너지 가격 업데이트 실패: {str(e)}")
            # 실패 시 기본값 사용
            return await self.get_default_energy_price()

    async def get_trx_market_price(self) -> float:
        """TRX 시장 가격 조회"""
        try:
            # CoinGecko API를 사용하여 TRX 가격 조회
            response = await self.http_client.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=tron&vs_currencies=usd",
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                trx_price = data.get('tron', {}).get('usd', 0.08)
                return float(trx_price)
            else:
                logger.warning(f"CoinGecko API 호출 실패: {response.status_code}")
                return 0.08  # 기본값

        except Exception as e:
            logger.warning(f"TRX 가격 조회 실패: {str(e)}")
            return 0.08  # 기본값

    async def get_energy_market_data(self) -> Dict:
        """에너지 시장 데이터 조회"""
        try:
            # TRON 에너지 거래소 API 호출
            # 실제로는 여러 소스에서 데이터를 수집하여 평균값 계산
            sources = [
                "https://api.tronenergymarket.com/price",
                "https://api.justlend.org/energy/price"
            ]

            prices = []
            for source in sources:
                try:
                    response = await self.http_client.get(source, timeout=5.0)
                    if response.status_code == 200:
                        data = response.json()
                        price = data.get('price_per_energy', 0)
                        if price > 0:
                            prices.append(price)
                except Exception as e:
                    logger.debug(f"에너지 가격 소스 조회 실패 ({source}): {str(e)}")
                    continue

            if prices:
                avg_price = sum(prices) / len(prices)
                return {
                    "price_per_energy": avg_price,
                    "sources_count": len(prices),
                    "timestamp": datetime.utcnow().isoformat(),
                    "market_activity": "active" if len(prices) > 1 else "limited"
                }
            else:
                # 기본값
                return {
                    "price_per_energy": 0.000065,
                    "sources_count": 0,
                    "timestamp": datetime.utcnow().isoformat(),
                    "market_activity": "unavailable"
                }

        except Exception as e:
            logger.warning(f"에너지 시장 데이터 조회 실패: {str(e)}")
            return {"price_per_energy": 0.000065}

    async def get_network_statistics(self) -> Dict:
        """TRON 네트워크 통계 조회"""
        try:
            # TRON 네트워크 API를 통한 통계 조회
            # 실제 구현에서는 tronpy나 TronGrid API 사용
            
            # 기본값으로 중간 혼잡도 반환
            return {
                "congestion_level": 25,  # 0-100%
                "total_transactions_24h": 5000000,
                "energy_utilization": 45.2,
                "average_confirmation_time": 3.0
            }

        except Exception as e:
            logger.warning(f"네트워크 통계 조회 실패: {str(e)}")
            return {
                "congestion_level": 20,
                "total_transactions_24h": 4000000,
                "energy_utilization": 40.0,
                "average_confirmation_time": 3.0
            }

    def calculate_market_demand(self, market_data: Dict) -> str:
        """시장 수요 계산"""
        activity = market_data.get('market_activity', 'limited')
        sources_count = market_data.get('sources_count', 0)
        
        if activity == "unavailable" or sources_count == 0:
            return "low"
        elif sources_count >= 3:
            return "high"
        else:
            return "medium"

    async def get_default_energy_price(self) -> Dict:
        """기본 에너지 가격 반환"""
        return {
            "trx_price_usd": 0.08,
            "energy_price_trx": 0.000065,
            "energy_price_usd": 0.000065 * 0.08,
            "market_demand": "medium",
            "network_congestion": 20
        }

    async def get_price_history(self, days: int = 7) -> List[Dict]:
        """에너지 가격 히스토리 조회"""
        try:
            from datetime import timedelta
            since = datetime.utcnow() - timedelta(days=days)

            query = (
                select(EnergyPriceHistory)
                .where(EnergyPriceHistory.recorded_at >= since)
                .order_by(desc(EnergyPriceHistory.recorded_at))
            )

            result = await self.db.execute(query)
            history = result.scalars().all()

            return [
                {
                    "recorded_at": record.recorded_at.isoformat(),
                    "trx_price_usd": float(record.trx_price_usd),
                    "energy_price_trx": float(record.energy_price_trx),
                    "energy_price_usd": float(record.energy_price_usd),
                    "market_demand": record.market_demand,
                    "network_congestion": record.network_congestion
                }
                for record in history
            ]

        except Exception as e:
            logger.error(f"가격 히스토리 조회 실패: {str(e)}")
            return []

    async def get_price_trend_analysis(self, days: int = 30) -> Dict:
        """가격 트렌드 분석"""
        try:
            history = await self.get_price_history(days)
            
            if len(history) < 2:
                return {"trend": "insufficient_data"}

            # 최근 가격과 이전 가격 비교
            latest = history[0]
            oldest = history[-1]

            trx_change = (latest['trx_price_usd'] - oldest['trx_price_usd']) / oldest['trx_price_usd'] * 100
            energy_change = (latest['energy_price_trx'] - oldest['energy_price_trx']) / oldest['energy_price_trx'] * 100

            # 평균 값 계산
            avg_trx_price = sum(h['trx_price_usd'] for h in history) / len(history)
            avg_energy_price = sum(h['energy_price_trx'] for h in history) / len(history)
            avg_congestion = sum(h['network_congestion'] for h in history) / len(history)

            # 트렌드 결정
            if energy_change > 10:
                trend = "rising"
            elif energy_change < -10:
                trend = "falling"
            else:
                trend = "stable"

            return {
                "trend": trend,
                "trx_price_change_percent": round(trx_change, 2),
                "energy_price_change_percent": round(energy_change, 2),
                "average_trx_price": round(avg_trx_price, 4),
                "average_energy_price": round(avg_energy_price, 8),
                "average_congestion": round(avg_congestion, 1),
                "data_points": len(history),
                "period_days": days
            }

        except Exception as e:
            logger.error(f"가격 트렌드 분석 실패: {str(e)}")
            return {"trend": "error"}

    async def close(self):
        """리소스 정리"""
        await self.http_client.aclose()
