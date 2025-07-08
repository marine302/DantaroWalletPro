"""
Doc #25: 에너지 풀 고급 관리 시스템 - 에너지 모니터링 서비스 (타입 안전 버전)
실시간 모니터링, 예측 분석, 알림 시스템, 패턴 분석
"""
import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Union
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc, func, update
from sqlalchemy.orm import selectinload

from app.models.partner import Partner
from app.models.energy_pool import (
    PartnerEnergyPool, EnergyAlert, PartnerEnergyUsageLog, 
    EnergyPrediction, EnergyStatus, EnergyAlertType
)
from app.core.config import settings

# TRON 관련 import 수정
try:
    from tronpy import Tron
    from tronpy.exceptions import TronError
    TRON_AVAILABLE = True
except ImportError:
    Tron = None
    TronError = Exception
    TRON_AVAILABLE = False

logger = logging.getLogger(__name__)


def safe_get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """SQLAlchemy 모델 속성을 안전하게 가져오는 헬퍼 함수"""
    if obj is None:
        return default
    
    value = getattr(obj, attr, default)
    
    # SQLAlchemy Column 타입인 경우 실제 값 추출
    if hasattr(value, 'value'):
        return value.value
    elif hasattr(value, '__getitem__') and hasattr(value, 'keys'):
        # dict-like object
        return value
    else:
        return value


def safe_str(value: Any, default: str = '') -> str:
    """안전한 str 변환"""
    if value is None:
        return default
    
    if hasattr(value, 'value'):
        value = value.value
    
    try:
        return str(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """안전한 int 변환"""
    if value is None:
        return default
    
    if hasattr(value, 'value'):
        value = value.value
    
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_decimal_to_int(value: Any, default: int = 0) -> int:
    """Decimal 값을 안전하게 int로 변환"""
    if value is None:
        return default
    
    if hasattr(value, 'value'):
        value = value.value
    
    if isinstance(value, Decimal):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        return int(Decimal(str(value)))
    except (ValueError, TypeError):
        return default


def safe_decimal_to_float(value: Any, default: float = 0.0) -> float:
    """Decimal 값을 안전하게 float로 변환"""
    if value is None:
        return default
    
    if hasattr(value, 'value'):
        value = value.value
    
    if isinstance(value, (Decimal, float, int)):
        return float(value)
    try:
        return float(Decimal(str(value)))
    except (ValueError, TypeError):
        return default


def safe_datetime(value: Any, default: Optional[datetime] = None) -> Optional[datetime]:
    """안전한 datetime 변환"""
    if value is None:
        return default
    
    if hasattr(value, 'value'):
        value = value.value
    
    if isinstance(value, datetime):
        return value
    
    return default


class EnergyMonitoringService:
    """에너지 모니터링 서비스 - 타입 안전 버전"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tron = None
        if TRON_AVAILABLE:
            try:
                self.tron = Tron()
            except Exception as e:
                logger.warning(f"Failed to initialize Tron client: {e}")
    
    async def get_energy_pool_status(self, partner_id: str) -> Dict[str, Any]:
        """파트너의 에너지 풀 상태 조회"""
        try:
            # 파트너 에너지 풀 조회
            query = select(PartnerEnergyPool).where(
                PartnerEnergyPool.partner_id == partner_id
            )
            result = await self.db.execute(query)
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool:
                return {
                    "status": "not_found",
                    "message": "Energy pool not found for this partner"
                }
            
            # 최근 예측 정보 조회
            prediction_query = select(EnergyPrediction).where(
                EnergyPrediction.energy_pool_id == safe_get_attr(energy_pool, 'id')
            ).order_by(desc(EnergyPrediction.created_at)).limit(1)
            prediction_result = await self.db.execute(prediction_query)
            prediction = prediction_result.scalar_one_or_none()
            
            # 결과 구성
            result = {
                "partner_id": partner_id,
                "pool_id": safe_str(safe_get_attr(energy_pool, 'id')),
                "energy_stats": {
                    "total_energy": safe_decimal_to_int(safe_get_attr(energy_pool, 'total_energy')),
                    "available_energy": safe_decimal_to_int(safe_get_attr(energy_pool, 'available_energy')),
                    "used_energy": safe_decimal_to_int(safe_get_attr(energy_pool, 'used_energy')),
                    "total_bandwidth": safe_decimal_to_int(safe_get_attr(energy_pool, 'total_bandwidth')),
                    "available_bandwidth": safe_decimal_to_int(safe_get_attr(energy_pool, 'available_bandwidth')),
                    "daily_average_usage": safe_decimal_to_int(safe_get_attr(energy_pool, 'daily_average_usage')),
                    "frozen_trx_amount": safe_decimal_to_float(safe_get_attr(energy_pool, 'frozen_trx_amount')),
                    "status": safe_str(safe_get_attr(energy_pool, 'status')),
                },
                "prediction": {
                    "predicted_usage": safe_decimal_to_int(safe_get_attr(prediction, 'predicted_usage')) if prediction else 0,
                    "depletion_estimated_at": safe_datetime(safe_get_attr(prediction, 'predicted_depletion')).isoformat() if prediction and safe_datetime(safe_get_attr(prediction, 'predicted_depletion')) else None,
                    "confidence_score": safe_decimal_to_float(safe_get_attr(prediction, 'confidence_score')) if prediction else 0,
                }
            }
            
            last_checked = safe_datetime(safe_get_attr(energy_pool, 'last_checked_at'))
            result["last_checked"] = last_checked.isoformat() if last_checked else None
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting energy pool status: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def check_energy_levels(self, partner_id: str) -> Dict[str, Any]:
        """에너지 레벨 체크 및 알림 생성"""
        try:
            # 파트너 에너지 풀 조회
            query = select(PartnerEnergyPool).where(
                PartnerEnergyPool.partner_id == partner_id
            )
            result = await self.db.execute(query)
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool:
                return {"status": "not_found", "message": "Energy pool not found"}
            
            # 실제 TRON 네트워크에서 에너지 상태 확인
            if self.tron:
                try:
                    # 실제 에너지 확인 로직 (예시)
                    pool_address = safe_str(safe_get_attr(energy_pool, 'pool_address'))
                    if pool_address:
                        account_info = self.tron.get_account(pool_address)
                        actual_energy = account_info.get('account_resource', {}).get('energy_limit', 0)
                        total_energy = safe_decimal_to_int(safe_get_attr(energy_pool, 'total_energy'))
                        
                        # 에너지 풀 상태 업데이트
                        await self._update_energy_status(
                            safe_int(safe_get_attr(energy_pool, 'id')),
                            actual_energy,
                            total_energy
                        )
                        
                except TronError as e:
                    logger.warning(f"Failed to check TRON energy levels: {e}")
                    
            return {
                "status": "success",
                "energy_level": safe_decimal_to_int(safe_get_attr(energy_pool, 'available_energy')),
                "total_energy": safe_decimal_to_int(safe_get_attr(energy_pool, 'total_energy')),
                "usage_percentage": self._calculate_usage_percentage(energy_pool)
            }
            
        except Exception as e:
            logger.error(f"Error checking energy levels: {e}")
            return {"status": "error", "message": str(e)}
    
    async def predict_energy_depletion(self, partner_id: str, days_ahead: int = 7) -> Dict[str, Any]:
        """에너지 고갈 예측"""
        try:
            # 파트너 에너지 풀 조회
            query = select(PartnerEnergyPool).where(
                PartnerEnergyPool.partner_id == partner_id
            )
            result = await self.db.execute(query)
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool:
                return {"status": "not_found", "message": "Energy pool not found"}
            
            # 현재 가용 에너지와 일일 평균 사용량
            available = safe_decimal_to_float(safe_get_attr(energy_pool, 'available_energy'))
            daily_avg = safe_decimal_to_float(safe_get_attr(energy_pool, 'daily_average_usage'))
            
            if daily_avg <= 0:
                return {
                    "status": "insufficient_data",
                    "message": "Insufficient usage data for prediction"
                }
            
            # 예측 계산
            days_remaining = available / daily_avg if daily_avg > 0 else float('inf')
            predicted_depletion = datetime.utcnow() + timedelta(days=days_remaining)
            
            # 신뢰도 점수 계산 (간단한 예시)
            confidence_score = min(0.95, 0.3 + (0.65 * min(days_remaining, 30) / 30))
            
            # 예측 결과 저장
            prediction = EnergyPrediction(
                energy_pool_id=safe_int(safe_get_attr(energy_pool, 'id')),
                predicted_usage=Decimal(str(daily_avg * days_ahead)),
                predicted_depletion=predicted_depletion,
                confidence_score=Decimal(str(confidence_score)),
                created_at=datetime.utcnow()
            )
            
            self.db.add(prediction)
            await self.db.commit()
            
            return {
                "status": "success",
                "days_remaining": round(days_remaining, 1),
                "predicted_depletion": predicted_depletion.isoformat(),
                "confidence_score": confidence_score,
                "available_energy": available,
                "daily_average_usage": daily_avg
            }
            
        except Exception as e:
            logger.error(f"Error predicting energy depletion: {e}")
            await self.db.rollback()
            return {"status": "error", "message": str(e)}
    
    async def get_usage_analytics(self, partner_id: str, days: int = 30) -> Dict[str, Any]:
        """에너지 사용량 분석"""
        try:
            # 파트너 에너지 풀 조회
            query = select(PartnerEnergyPool).where(
                PartnerEnergyPool.partner_id == partner_id
            )
            result = await self.db.execute(query)
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool:
                return {"status": "not_found", "message": "Energy pool not found"}
            
            # 사용량 로그 조회
            usage_logs = await self._get_usage_history(safe_int(safe_get_attr(energy_pool, 'id')), days)
            
            # 통계 계산
            total_usage = sum(safe_decimal_to_float(safe_get_attr(log, 'energy_consumed')) for log in usage_logs)
            avg_usage = total_usage / len(usage_logs) if usage_logs else 0
            peak_usage = max((safe_decimal_to_float(safe_get_attr(log, 'energy_consumed')) for log in usage_logs), default=0)
            
            # 시간대별 사용량 분석
            hourly_usage = self._analyze_hourly_usage(usage_logs)
            daily_usage = self._analyze_daily_usage(usage_logs)
            
            return {
                "status": "success",
                "period_days": days,
                "total_usage": total_usage,
                "average_usage": avg_usage,
                "peak_usage": peak_usage,
                "hourly_patterns": hourly_usage,
                "daily_patterns": daily_usage,
                "recommendations": self._generate_usage_recommendations(energy_pool, usage_logs)
            }
            
        except Exception as e:
            logger.error(f"Error getting usage analytics: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _update_energy_status(self, energy_pool_id: int, available_energy: float, total_energy: float):
        """에너지 상태 업데이트"""
        try:
            # 사용량 백분율 계산
            usage_percentage = ((total_energy - available_energy) / total_energy * 100) if total_energy > 0 else 0
            
            # 상태 결정
            if usage_percentage >= 90:
                status = EnergyStatus.CRITICAL
            elif usage_percentage >= 70:
                status = EnergyStatus.WARNING
            else:
                status = EnergyStatus.NORMAL
            
            # 에너지 풀 업데이트
            update_query = (
                update(PartnerEnergyPool)
                .where(PartnerEnergyPool.id == energy_pool_id)
                .values(
                    available_energy=Decimal(str(available_energy)),
                    used_energy=Decimal(str(total_energy - available_energy)),
                    status=status,
                    last_checked_at=datetime.utcnow()
                )
            )
            await self.db.execute(update_query)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating energy status: {e}")
            await self.db.rollback()
    
    async def _get_usage_history(self, energy_pool_id: int, days: int) -> List[PartnerEnergyUsageLog]:
        """사용량 기록 조회"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = select(PartnerEnergyUsageLog).where(
                and_(
                    PartnerEnergyUsageLog.energy_pool_id == energy_pool_id,
                    PartnerEnergyUsageLog.created_at >= start_date
                )
            ).order_by(desc(PartnerEnergyUsageLog.created_at))
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting usage history: {e}")
            return []
    
    def _analyze_hourly_usage(self, usage_logs: List[PartnerEnergyUsageLog]) -> Dict[int, float]:
        """시간대별 사용량 분석"""
        hourly_usage = {hour: 0.0 for hour in range(24)}
        
        for log in usage_logs:
            log_created_at = safe_datetime(safe_get_attr(log, 'created_at'))
            if log_created_at:
                hour = log_created_at.hour
                hourly_usage[hour] += safe_decimal_to_float(safe_get_attr(log, 'energy_consumed'))
        
        return hourly_usage
    
    def _analyze_daily_usage(self, usage_logs: List[PartnerEnergyUsageLog]) -> Dict[str, float]:
        """일별 사용량 분석"""
        daily_usage = {}
        
        for log in usage_logs:
            log_created_at = safe_datetime(safe_get_attr(log, 'created_at'))
            if log_created_at:
                date = log_created_at.strftime('%Y-%m-%d')
                if date not in daily_usage:
                    daily_usage[date] = 0.0
                daily_usage[date] += safe_decimal_to_float(safe_get_attr(log, 'energy_consumed'))
        
        return daily_usage
    
    def _calculate_usage_percentage(self, energy_pool: PartnerEnergyPool) -> float:
        """사용률 계산"""
        total = safe_decimal_to_float(safe_get_attr(energy_pool, 'total_energy'))
        used = safe_decimal_to_float(safe_get_attr(energy_pool, 'used_energy'))
        
        if total <= 0:
            return 0.0
        
        return round((used / total) * 100, 2)
    
    def _generate_usage_recommendations(self, energy_pool: PartnerEnergyPool, usage_logs: List[PartnerEnergyUsageLog]) -> List[str]:
        """사용량 기반 추천사항 생성"""
        recommendations = []
        
        # 현재 상태 분석
        frozen_amount = safe_decimal_to_float(safe_get_attr(energy_pool, 'frozen_trx_amount'))
        usage_percentage = self._calculate_usage_percentage(energy_pool)
        
        if usage_percentage > 80:
            recommendations.append("Consider increasing frozen TRX amount to boost energy capacity")
        
        if frozen_amount < 1000:
            recommendations.append("Low frozen TRX amount detected - consider freezing more TRX for better energy efficiency")
        
        # 사용 패턴 분석
        if usage_logs:
            recent_usage = [safe_decimal_to_float(safe_get_attr(log, 'energy_consumed')) for log in usage_logs[:30]]
            if recent_usage:
                avg_recent = sum(recent_usage) / len(recent_usage)
                if avg_recent > 1000:
                    recommendations.append("High energy consumption detected - consider optimizing transaction patterns")
        
        return recommendations if recommendations else ["Energy usage is within normal parameters"]
    
    async def get_energy_pool_summary(self) -> Dict[str, Any]:
        """전체 에너지 풀 요약 정보"""
        try:
            # 모든 에너지 풀 조회
            query = select(PartnerEnergyPool)
            result = await self.db.execute(query)
            energy_pools = result.scalars().all()
            
            if not energy_pools:
                return {"status": "no_data", "message": "No energy pools found"}
            
            # 통계 계산
            total_pools = len(energy_pools)
            pools_summary = []
            
            total_energy_all = 0
            total_available_all = 0
            critical_pools = 0
            warning_pools = 0
            
            for pool in energy_pools:
                pool_data = {
                    "partner_id": safe_str(safe_get_attr(pool, 'partner_id')),
                    "status": safe_str(safe_get_attr(pool, 'status')),
                    "available_energy": safe_decimal_to_int(safe_get_attr(pool, 'available_energy')),
                    "total_energy": safe_decimal_to_int(safe_get_attr(pool, 'total_energy')),
                }
                
                # 사용률 계산
                total = safe_decimal_to_float(safe_get_attr(pool, 'total_energy'))
                used = safe_decimal_to_float(safe_get_attr(pool, 'used_energy'))
                
                if total > 0:
                    pool_data["usage_percentage"] = round((used / total) * 100, 2)
                else:
                    pool_data["usage_percentage"] = 0
                
                # 상태별 카운트
                pool_status = safe_str(safe_get_attr(pool, 'status'))
                if pool_status == str(EnergyStatus.CRITICAL):
                    critical_pools += 1
                elif pool_status == str(EnergyStatus.WARNING):
                    warning_pools += 1
                
                total_energy_all += total
                total_available_all += safe_decimal_to_float(safe_get_attr(pool, 'available_energy'))
                
                pools_summary.append(pool_data)
            
            return {
                "status": "success",
                "summary": {
                    "total_pools": total_pools,
                    "critical_pools": critical_pools,
                    "warning_pools": warning_pools,
                    "normal_pools": total_pools - critical_pools - warning_pools,
                    "total_energy_all_pools": total_energy_all,
                    "total_available_all_pools": total_available_all,
                    "overall_usage_percentage": round(((total_energy_all - total_available_all) / total_energy_all * 100), 2) if total_energy_all > 0 else 0
                },
                "pools": pools_summary
            }
            
        except Exception as e:
            logger.error(f"Error getting energy pool summary: {e}")
            return {"status": "error", "message": str(e)}
    
    async def create_energy_alert(self, partner_id: str, alert_type: EnergyAlertType, message: str) -> bool:
        """에너지 알림 생성"""
        try:
            # 파트너 에너지 풀 조회
            query = select(PartnerEnergyPool).where(
                PartnerEnergyPool.partner_id == partner_id
            )
            result = await self.db.execute(query)
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool:
                return False
            
            # 알림 생성
            alert = EnergyAlert(
                energy_pool_id=safe_int(safe_get_attr(energy_pool, 'id')),
                alert_type=alert_type,
                message=message,
                is_resolved=False,
                created_at=datetime.utcnow()
            )
            
            self.db.add(alert)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating energy alert: {e}")
            await self.db.rollback()
            return False
    
    async def get_energy_alerts(self, partner_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """에너지 알림 조회"""
        try:
            # 파트너 에너지 풀 조회
            query = select(PartnerEnergyPool).where(
                PartnerEnergyPool.partner_id == partner_id
            )
            result = await self.db.execute(query)
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool:
                return []
            
            # 알림 조회
            alerts_query = select(EnergyAlert).where(
                EnergyAlert.energy_pool_id == safe_int(safe_get_attr(energy_pool, 'id'))
            ).order_by(desc(EnergyAlert.created_at)).limit(limit)
            
            alerts_result = await self.db.execute(alerts_query)
            alerts = alerts_result.scalars().all()
            
            return [
                {
                    "id": safe_int(safe_get_attr(alert, 'id')),
                    "alert_type": safe_str(safe_get_attr(alert, 'alert_type')),
                    "message": safe_str(safe_get_attr(alert, 'message')),
                    "is_resolved": safe_get_attr(alert, 'is_resolved', False),
                    "created_at": safe_datetime(safe_get_attr(alert, 'created_at')).isoformat() if safe_datetime(safe_get_attr(alert, 'created_at')) else None
                }
                for alert in alerts
            ]
            
        except Exception as e:
            logger.error(f"Error getting energy alerts: {e}")
            return []
    
    async def resolve_energy_alert(self, alert_id: int) -> bool:
        """에너지 알림 해결"""
        try:
            update_query = (
                update(EnergyAlert)
                .where(EnergyAlert.id == alert_id)
                .values(
                    is_resolved=True,
                    resolved_at=datetime.utcnow()
                )
            )
            await self.db.execute(update_query)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error resolving energy alert: {e}")
            await self.db.rollback()
            return False
    
    async def monitor_all_energy_pools(self) -> Dict[str, Any]:
        """모든 에너지 풀 모니터링"""
        try:
            # 모든 에너지 풀 조회
            query = select(PartnerEnergyPool)
            result = await self.db.execute(query)
            energy_pools = result.scalars().all()
            
            monitoring_results = []
            
            for pool in energy_pools:
                partner_id = safe_str(safe_get_attr(pool, 'partner_id'))
                
                # 각 풀의 상태 체크
                pool_status = await self.check_energy_levels(partner_id)
                
                # 예측 수행
                prediction = await self.predict_energy_depletion(partner_id)
                
                monitoring_results.append({
                    "partner_id": partner_id,
                    "pool_id": safe_str(safe_get_attr(pool, 'id')),
                    "status": pool_status,
                    "prediction": prediction
                })
            
            return {
                "status": "success",
                "timestamp": datetime.utcnow().isoformat(),
                "monitored_pools": len(energy_pools),
                "results": monitoring_results
            }
            
        except Exception as e:
            logger.error(f"Error monitoring all energy pools: {e}")
            return {"status": "error", "message": str(e)}
