"""
에너지 모니터링 서비스 - 예측 서비스
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.energy_pool import EnergyPrediction, PartnerEnergyUsageLog

from .utils import safe_decimal_to_float

logger = logging.getLogger(__name__)


class EnergyPredictionService:
    """에너지 예측 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_prediction(
        self, energy_pool_id: int
    ) -> Optional[EnergyPrediction]:
        """에너지 예측 생성"""
        try:
            # 기존 예측 데이터 조회
            result = await self.db.execute(
                select(PartnerEnergyUsageLog)
                .where(PartnerEnergyUsageLog.energy_pool_id == energy_pool_id)
                .order_by(desc(PartnerEnergyUsageLog.created_at))
                .limit(100)
            )
            usage_logs = result.scalars().all()

            if not usage_logs:
                return None

            # 간단한 평균 기반 예측
            recent_usage = [
                safe_decimal_to_float(log.energy_consumed) for log in usage_logs[:30]
            ]
            avg_usage = sum(recent_usage) / len(recent_usage) if recent_usage else 0

            # 예측 생성
            prediction = EnergyPrediction(
                energy_pool_id=energy_pool_id,
                prediction_date=datetime.utcnow() + timedelta(days=1),
                predicted_usage=Decimal(str(int(avg_usage * 24))),  # 24시간 예측
                confidence_score=Decimal("75.0"),  # 신뢰도 점수
                historical_pattern={"avg_hourly": avg_usage},
                seasonal_factors={},
                trend_analysis={"trend": "stable"},
            )

            self.db.add(prediction)
            await self.db.commit()

            return prediction

        except Exception as e:
            logger.error(
                f"Failed to generate prediction for energy pool {energy_pool_id}: {e}"
            )
            return None

    async def get_latest_prediction(
        self, energy_pool_id: int
    ) -> Optional[EnergyPrediction]:
        """최신 예측 조회"""
        try:
            result = await self.db.execute(
                select(EnergyPrediction)
                .where(EnergyPrediction.energy_pool_id == energy_pool_id)
                .order_by(desc(EnergyPrediction.created_at))
                .limit(1)
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(
                f"Failed to get latest prediction for energy pool {energy_pool_id}: {e}"
            )
            return None

    async def predict_depletion_time(
        self, energy_pool_id: int, current_available: float, daily_avg_usage: float
    ) -> Optional[datetime]:
        """에너지 고갈 시간 예측"""
        try:
            if daily_avg_usage <= 0 or current_available <= 0:
                return None

            # 간단한 선형 예측 (일평균 사용량 기준)
            days_remaining = current_available / daily_avg_usage

            if days_remaining > 365:  # 1년 이상이면 예측 제외
                return None

            depletion_time = datetime.utcnow() + timedelta(days=days_remaining)
            return depletion_time

        except Exception as e:
            logger.error(f"Failed to predict depletion time: {e}")
            return None

    async def analyze_usage_trend(
        self, usage_logs: List[PartnerEnergyUsageLog]
    ) -> Dict[str, Any]:
        """사용량 트렌드 분석"""
        try:
            if len(usage_logs) < 7:  # 최소 7일 데이터 필요
                return {"trend": "insufficient_data", "slope": 0.0, "confidence": 0.0}

            # 최근 7일과 이전 7일 비교
            recent_logs = usage_logs[:7]
            previous_logs = usage_logs[7:14] if len(usage_logs) >= 14 else []

            recent_avg = sum(
                safe_decimal_to_float(log.energy_consumed) for log in recent_logs
            ) / len(recent_logs)

            if not previous_logs:
                return {"trend": "stable", "slope": 0.0, "confidence": 0.5}

            previous_avg = sum(
                safe_decimal_to_float(log.energy_consumed) for log in previous_logs
            ) / len(previous_logs)

            # 트렌드 계산
            if previous_avg == 0:
                slope = 0.0
            else:
                slope = (recent_avg - previous_avg) / previous_avg

            # 트렌드 분류
            if slope > 0.1:  # 10% 이상 증가
                trend = "increasing"
            elif slope < -0.1:  # 10% 이상 감소
                trend = "decreasing"
            else:
                trend = "stable"

            confidence = min(
                1.0, len(usage_logs) / 30.0
            )  # 30일 데이터가 있으면 신뢰도 100%

            return {
                "trend": trend,
                "slope": slope,
                "confidence": confidence,
                "recent_avg": recent_avg,
                "previous_avg": previous_avg,
            }

        except Exception as e:
            logger.error(f"Failed to analyze usage trend: {e}")
            return {"trend": "error", "slope": 0.0, "confidence": 0.0}

    async def predict_peak_usage_times(
        self, usage_logs: List[PartnerEnergyUsageLog]
    ) -> List[Dict[str, Any]]:
        """피크 사용 시간 예측"""
        try:
            hourly_usage = {}

            for log in usage_logs:
                try:
                    if hasattr(log, "created_at") and log.created_at is not None:
                        hour = log.created_at.hour
                        if hour not in hourly_usage:
                            hourly_usage[hour] = []
                        hourly_usage[hour].append(
                            safe_decimal_to_float(log.energy_consumed)
                        )
                except Exception:
                    continue

            # 시간별 평균 사용량 계산
            hourly_averages = {}
            for hour, usages in hourly_usage.items():
                hourly_averages[hour] = sum(usages) / len(usages)

            # 평균 사용량 기준으로 정렬
            sorted_hours = sorted(
                hourly_averages.items(), key=lambda x: x[1], reverse=True
            )

            # 상위 3개 시간대 반환
            peak_times = []
            for hour, avg_usage in sorted_hours[:3]:
                peak_times.append(
                    {
                        "hour": hour,
                        "average_usage": avg_usage,
                        "usage_percentage": (
                            (avg_usage / max(hourly_averages.values())) * 100
                            if hourly_averages
                            else 0
                        ),
                    }
                )

            return peak_times

        except Exception as e:
            logger.error(f"Failed to predict peak usage times: {e}")
            return []
