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
except ImportError:
    class TronError(Exception):
        pass
    TRON_AVAILABLE = True
except ImportError:
    Tron = None
    TronError = Exception
    TRON_AVAILABLE = False

logger = logging.getLogger(__name__)


def safe_decimal_to_int(value: Union[Decimal, int, None], default: int = 0) -> int:
    """Decimal 값을 안전하게 int로 변환"""
    if value is None:
        return default
    if isinstance(value, Decimal):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        return int(Decimal(str(value)))
    except (ValueError, TypeError):
        return default


def safe_decimal_to_float(value: Union[Decimal, float, int, None], default: float = 0.0) -> float:
    """Decimal 값을 안전하게 float로 변환"""
    if value is None:
        return default
    if isinstance(value, (Decimal, float, int)):
        return float(value)
    try:
        return float(Decimal(str(value)))
    except (ValueError, TypeError):
        return default


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


def safe_datetime(value: Any, default: Optional[datetime] = None) -> Optional[datetime]:
    """안전한 datetime 변환"""
    if value is None:
        return default
    
    if hasattr(value, 'value'):
        value = value.value
    
    if isinstance(value, datetime):
        return value
    
    return default


def safe_decimal_to_float(value: Union[Decimal, float, int, None], default: float = 0.0) -> float:
    """Decimal 값을 안전하게 float로 변환"""
    if value is None:
        return default
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(Decimal(str(value)))
    except (ValueError, TypeError):
        return default


def safe_get_column_value(obj: Any, attr: str, default: Any = None) -> Any:
    """SQLAlchemy Column 값을 안전하게 가져오는 헬퍼 함수"""
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


def safe_int_from_column(value: Any, default: int = 0) -> int:
    """SQLAlchemy Column에서 안전하게 int 값 추출"""
    if value is None:
        return default
    
    # SQLAlchemy Column 타입인 경우 실제 값 추출
    if hasattr(value, 'value'):
        value = value.value
    elif hasattr(value, '__getitem__') and hasattr(value, 'keys'):
        # dict-like object인 경우 스킵
        return default
    
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float_from_column(value: Any, default: float = 0.0) -> float:
    """SQLAlchemy Column에서 안전하게 float 값 추출"""
    if value is None:
        return default
    
    # SQLAlchemy Column 타입인 경우 실제 값 추출
    if hasattr(value, 'value'):
        value = value.value
    elif hasattr(value, '__getitem__') and hasattr(value, 'keys'):
        # dict-like object인 경우 스킵
        return default
    
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_str_from_column(value: Any, default: str = "") -> str:
    """SQLAlchemy Column에서 안전하게 str 값 추출"""
    if value is None:
        return default
    
    # SQLAlchemy Column 타입인 경우 실제 값 추출
    if hasattr(value, 'value'):
        value = value.value
    elif hasattr(value, '__getitem__') and hasattr(value, 'keys'):
        # dict-like object인 경우 스킵
        return default
    
    try:
        return str(value)
    except (TypeError, ValueError):
        return default


def safe_datetime_from_column(value: Any, default: Optional[datetime] = None) -> Optional[datetime]:
    """SQLAlchemy Column에서 안전하게 datetime 값 추출"""
    if value is None:
        return default
    
    # SQLAlchemy Column 타입인 경우 실제 값 추출
    if hasattr(value, 'value'):
        value = value.value
    elif hasattr(value, '__getitem__') and hasattr(value, 'keys'):
        # dict-like object인 경우 스킵
        return default
    
    if isinstance(value, datetime):
        return value
    
    return default


def safe_bool_from_column(value: Any, default: bool = False) -> bool:
    """SQLAlchemy Column에서 안전하게 bool 값 추출"""
    if value is None:
        return default
    
    # SQLAlchemy Column 타입인 경우 실제 값 추출
    if hasattr(value, 'value'):
        value = value.value
    elif hasattr(value, '__getitem__') and hasattr(value, 'keys'):
        # dict-like object인 경우 스킵
        return default
    
    try:
        return bool(value)
    except (TypeError, ValueError):
        return default


class EnergyMonitoringService:
    """Doc #25: 에너지 풀 고급 관리 시스템 (타입 안전 버전)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        if TRON_AVAILABLE and Tron:
            network = getattr(settings, 'TRON_NETWORK', 'nile')
            self.tron = Tron(network='mainnet' if network == 'mainnet' else 'nile')
        else:
            self.tron = None
    
    async def monitor_partner_energy(self, partner_id: int) -> Dict[str, Any]:
        """파트너 에너지 실시간 모니터링"""
        try:
            # 파트너 에너지 풀 조회 또는 생성
            result = await self.db.execute(
                select(PartnerEnergyPool).where(
                    PartnerEnergyPool.partner_id == partner_id
                )
            )
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool:
                # 에너지 풀 초기화
                energy_pool = await self._initialize_partner_energy_pool(partner_id)
                await self.db.commit()
                await self.db.refresh(energy_pool)
            
            # 실시간 블록체인 데이터로 업데이트
            await self._update_energy_pool_from_blockchain(energy_pool)
            
            # 예측 데이터 조회
            prediction_result = await self.db.execute(
                select(EnergyPrediction)
                .where(EnergyPrediction.energy_pool_id == energy_pool.id)
                .order_by(desc(EnergyPrediction.created_at))
                .limit(1)
            )
            prediction = prediction_result.scalar_one_or_none()
            
            return {
                "partner_id": partner_id,
                "energy_pool": {
                    "id": energy_pool.id,
                    "wallet_address": energy_pool.wallet_address,
                    "total_energy": safe_decimal_to_int(safe_get_attr(energy_pool, 'total_energy')),
                    "available_energy": safe_decimal_to_int(safe_get_attr(energy_pool, 'available_energy')),
                    "used_energy": safe_decimal_to_int(safe_get_attr(energy_pool, 'used_energy')),
                    "total_bandwidth": safe_decimal_to_int(safe_get_attr(energy_pool, 'total_bandwidth')),
                    "available_bandwidth": safe_decimal_to_int(safe_get_attr(energy_pool, 'available_bandwidth')),
                    "daily_average_usage": safe_decimal_to_int(safe_get_attr(energy_pool, 'daily_average_usage')),
                    "frozen_trx_amount": safe_decimal_to_float(safe_get_attr(energy_pool, 'frozen_trx_amount')),
                    "status": safe_str(safe_get_attr(energy_pool, 'status')),
                    "warning_threshold": energy_pool.warning_threshold or 30,
                    "critical_threshold": energy_pool.critical_threshold or 10
                },
                "predictions": {
                    "predicted_usage": safe_decimal_to_int(safe_get_attr(prediction, 'predicted_usage')) if prediction else 0,
                    "depletion_estimated_at": safe_datetime(safe_get_attr(prediction, 'predicted_depletion')).isoformat() if prediction and safe_datetime(safe_get_attr(prediction, 'predicted_depletion')) else None,
                    "confidence_score": safe_decimal_to_float(safe_get_attr(prediction, 'confidence_score')) if prediction else 0,
                    "hours_remaining": self._calculate_hours_remaining(energy_pool),
                },
            }
            
            last_checked = safe_datetime(safe_get_attr(energy_pool, 'last_checked_at'))
            result["last_checked"] = last_checked.isoformat() if last_checked else None
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to monitor partner energy for {partner_id}: {e}")
            raise
    
    async def _initialize_partner_energy_pool(self, partner_id: int) -> PartnerEnergyPool:
        """파트너 에너지 풀 초기화"""
        # 파트너 정보 조회
        result = await self.db.execute(
            select(Partner).where(Partner.id == partner_id)
        )
        partner = result.scalar_one_or_none()
        
        if not partner:
            raise ValueError(f"Partner {partner_id} not found")
        
        # 기본 지갑 주소 설정 (실제로는 파트너의 주 지갑 주소 사용)
        wallet_address = getattr(partner, 'wallet_address', f"TPartner{partner_id}DefaultWallet")
        
        energy_pool = PartnerEnergyPool(
            partner_id=partner_id,
            wallet_address=wallet_address,
            total_energy=Decimal('0'),
            available_energy=Decimal('0'),
            used_energy=Decimal('0'),
            energy_limit=Decimal('0'),
            total_bandwidth=Decimal('0'),
            available_bandwidth=Decimal('0'),
            frozen_trx_amount=Decimal('0'),
            frozen_for_energy=Decimal('0'),
            frozen_for_bandwidth=Decimal('0'),
            status=EnergyStatus.SUFFICIENT,
            daily_average_usage=Decimal('0'),
            warning_threshold=30,
            critical_threshold=10,
            auto_response_enabled=True,
            last_checked_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        self.db.add(energy_pool)
        await self.db.flush()
        
        logger.info(f"Initialized energy pool for partner {partner_id}")
        return energy_pool
    
    async def _update_energy_pool_from_blockchain(self, energy_pool: PartnerEnergyPool):
        """블록체인에서 에너지 풀 정보 업데이트"""
        if not self.tron:
            logger.warning("TRON client not available, using mock data")
            await self._update_with_mock_data(energy_pool)
            return
        
        try:
            # 지갑 주소를 문자열로 변환
            wallet_address = str(energy_pool.wallet_address)
            
            # 계정 리소스 정보 조회
            account_info = self.tron.get_account_resource(wallet_address)
            
            # 에너지 정보 추출
            total_energy = account_info.get('EnergyLimit', 0)
            used_energy = account_info.get('EnergyUsed', 0)
            available_energy = max(0, total_energy - used_energy)
            
            # 대역폭 정보 조회
            account_detail = self.tron.get_account(wallet_address)
            
            # 대역폭 정보 추출
            total_bandwidth = account_detail.get('bandwidth', {}).get('net_limit', 0)
            used_bandwidth = account_detail.get('bandwidth', {}).get('net_used', 0)
            
            # 동결 정보 조회
            frozen_info = await self._get_frozen_info(account_detail)
            
            # DB 업데이트 (SQL 업데이트 쿼리 사용)
            await self.db.execute(
                update(PartnerEnergyPool)
                .where(PartnerEnergyPool.id == energy_pool.id)
                .values(
                    total_energy=Decimal(str(total_energy)),
                    available_energy=Decimal(str(available_energy)),
                    used_energy=Decimal(str(used_energy)),
                    total_bandwidth=Decimal(str(total_bandwidth)),
                    available_bandwidth=Decimal(str(max(0, total_bandwidth - used_bandwidth))),
                    frozen_for_energy=frozen_info['energy'],
                    frozen_for_bandwidth=frozen_info['bandwidth'],
                    frozen_trx_amount=frozen_info['energy'] + frozen_info['bandwidth'],
                    last_checked_at=datetime.utcnow()
                )
            )
            
            # 상태 업데이트
            await self._update_energy_status(energy_pool.id, available_energy, total_energy)
            
        except Exception as e:
            logger.error(f"Failed to update energy pool from blockchain: {e}")
            await self._update_with_mock_data(energy_pool)
    
    async def _update_with_mock_data(self, energy_pool: PartnerEnergyPool):
        """테스트용 목 데이터로 업데이트"""
        await self.db.execute(
            update(PartnerEnergyPool)
            .where(PartnerEnergyPool.id == energy_pool.id)
            .values(
                total_energy=Decimal('10000'),
                used_energy=Decimal('3000'),
                available_energy=Decimal('7000'),
                total_bandwidth=Decimal('5000'),
                available_bandwidth=Decimal('4000'),
                frozen_trx_amount=Decimal('100'),
                frozen_for_energy=Decimal('80'),
                frozen_for_bandwidth=Decimal('20'),
                last_checked_at=datetime.utcnow()
            )
        )
    
    async def _update_energy_status(self, energy_pool_id: int, available_energy: int, total_energy: int):
        """에너지 상태 업데이트"""
        if total_energy == 0:
            usage_percentage = 0
            status = EnergyStatus.SUFFICIENT
        else:
            usage_percentage = ((total_energy - available_energy) / total_energy) * 100
            
            if usage_percentage >= 90:  # critical_threshold
                status = EnergyStatus.CRITICAL
            elif usage_percentage >= 70:  # warning_threshold
                status = EnergyStatus.WARNING
            else:
                status = EnergyStatus.SUFFICIENT
        
        await self.db.execute(
            update(PartnerEnergyPool)
            .where(PartnerEnergyPool.id == energy_pool_id)
            .values(status=status)
        )
    
    def _calculate_hours_remaining(self, energy_pool: PartnerEnergyPool) -> Optional[int]:
        """잔여 시간 계산"""
        available = safe_decimal_to_float(energy_pool.available_energy)
        daily_avg = safe_decimal_to_float(energy_pool.daily_average_usage)
        
        if daily_avg > 0 and available > 0:
            hours_remaining = (available / daily_avg) * 24
            return int(hours_remaining)
        return None
    
    async def _get_frozen_info(self, account_info: Dict) -> Dict[str, Decimal]:
        """TRX 동결 정보 파싱"""
        frozen_info = {
            'energy': Decimal('0'),
            'bandwidth': Decimal('0')
        }
        
        try:
            # 동결 정보 추출 (TRON 네트워크 구조에 따라)
            if 'frozen' in account_info:
                for frozen in account_info['frozen']:
                    frozen_balance = Decimal(str(frozen.get('frozen_balance', 0) / 1e6))
                    resource_type = frozen.get('resource', 'BANDWIDTH')
                    
                    if resource_type == 'ENERGY':
                        frozen_info['energy'] = frozen_balance
                    else:  # BANDWIDTH
                        frozen_info['bandwidth'] = frozen_balance
            
            return frozen_info
            
        except Exception as e:
            logger.error(f"Failed to parse frozen info: {e}")
            return frozen_info
    
    async def get_energy_analytics(self, partner_id: int, days: int = 30) -> Dict[str, Any]:
        """에너지 사용 분석"""
        try:
            # 에너지 풀 조회
            result = await self.db.execute(
                select(PartnerEnergyPool).where(PartnerEnergyPool.partner_id == partner_id)
            )
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool:
                return self._empty_analytics_response(partner_id, days)
            
            # 사용 이력 조회
            usage_logs = await self._get_usage_history(energy_pool.id, days)
            
            total_usage = sum(safe_decimal_to_float(log.energy_consumed) for log in usage_logs)
            avg_daily = total_usage / days if days > 0 else 0
            peak_usage = max((safe_decimal_to_float(log.energy_consumed) for log in usage_logs), default=0)
            
            return {
                "partner_id": partner_id,
                "period_days": days,
                "total_energy_used": int(total_usage),
                "average_daily_usage": int(avg_daily),
                "peak_usage": int(peak_usage),
                "efficiency_score": 85.0,  # 임시값
                "usage_pattern": {
                    "hourly": await self._get_hourly_pattern(usage_logs),
                    "daily": await self._get_daily_pattern(usage_logs),
                    "trend": "stable"  # 임시값
                },
                "recommendations": await self._get_recommendations(energy_pool),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get energy analytics for partner {partner_id}: {e}")
            return self._empty_analytics_response(partner_id, days)
    
    def _empty_analytics_response(self, partner_id: int, days: int) -> Dict[str, Any]:
        """빈 분석 응답"""
        return {
            "partner_id": partner_id,
            "period_days": days,
            "total_energy_used": 0,
            "average_daily_usage": 0,
            "peak_usage": 0,
            "efficiency_score": 0.0,
            "usage_pattern": {
                "hourly": [],
                "daily": [],
                "trend": "no_data"
            },
            "recommendations": [],
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def _get_usage_history(self, energy_pool_id: int, days: int) -> List[PartnerEnergyUsageLog]:
        """에너지 사용 이력 조회"""
        since = datetime.utcnow() - timedelta(days=days)
        
        result = await self.db.execute(
            select(PartnerEnergyUsageLog)
            .where(
                and_(
                    PartnerEnergyUsageLog.energy_pool_id == energy_pool_id,
                    PartnerEnergyUsageLog.created_at >= since
                )
            )
            .order_by(desc(PartnerEnergyUsageLog.created_at))
        )
        
        return list(result.scalars().all())
    
    async def _get_hourly_pattern(self, usage_logs: List[PartnerEnergyUsageLog]) -> List[Dict]:
        """시간별 사용 패턴 분석"""
        hourly_usage = {}
        for log in usage_logs:
            if log.created_at:
                hour = log.created_at.hour
                if hour not in hourly_usage:
                    hourly_usage[hour] = 0
                hourly_usage[hour] += safe_decimal_to_float(log.energy_consumed)
        
        return [{"hour": h, "usage": usage} for h, usage in sorted(hourly_usage.items())]
    
    async def _get_daily_pattern(self, usage_logs: List[PartnerEnergyUsageLog]) -> List[Dict]:
        """일별 사용 패턴 분석"""
        daily_usage = {}
        for log in usage_logs:
            if log.created_at:
                date = log.created_at.date().isoformat()
                if date not in daily_usage:
                    daily_usage[date] = 0
                daily_usage[date] += safe_decimal_to_float(log.energy_consumed)
        
        return [{"date": d, "usage": usage} for d, usage in sorted(daily_usage.items())]
    
    async def _get_recommendations(self, energy_pool: PartnerEnergyPool) -> List[str]:
        """추천 사항 생성"""
        recommendations = []
        
        usage_percentage = 0
        total = safe_decimal_to_float(energy_pool.total_energy)
        used = safe_decimal_to_float(energy_pool.used_energy)
        
        if total > 0:
            usage_percentage = (used / total) * 100
        
        if usage_percentage > 80:
            recommendations.append("에너지 사용량이 높습니다. 추가 TRX 스테이킹을 고려하세요.")
        
        if usage_percentage > 90:
            recommendations.append("에너지가 곧 부족할 수 있습니다. 즉시 충전을 권장합니다.")
        
        frozen_amount = safe_decimal_to_float(energy_pool.frozen_trx_amount)
        if frozen_amount < 100:
            recommendations.append("더 많은 TRX를 스테이킹하여 안정적인 에너지를 확보하세요.")
        
        return recommendations
    
    async def monitor_all_partners(self) -> Dict[str, Any]:
        """모든 파트너 모니터링"""
        try:
            # 모든 파트너 에너지 풀 조회
            result = await self.db.execute(
                select(PartnerEnergyPool).order_by(PartnerEnergyPool.partner_id)
            )
            energy_pools = result.scalars().all()
            
            partner_statuses = []
            total_critical = 0
            total_warning = 0
            total_sufficient = 0
            
            for pool in energy_pools:
                status_info = {
                    "partner_id": pool.partner_id,
                    "status": pool.status.value if pool.status else "unknown",
                    "available_energy": safe_decimal_to_int(pool.available_energy),
                    "total_energy": safe_decimal_to_int(pool.total_energy),
                    "usage_percentage": 0
                }
                
                total = safe_decimal_to_float(pool.total_energy)
                used = safe_decimal_to_float(pool.used_energy)
                if total > 0:
                    status_info["usage_percentage"] = int((used / total) * 100)
                
                partner_statuses.append(status_info)
                
                # 상태별 카운트
                if pool.status == EnergyStatus.CRITICAL:
                    total_critical += 1
                elif pool.status == EnergyStatus.WARNING:
                    total_warning += 1
                else:
                    total_sufficient += 1
            
            return {
                "success": True,
                "summary": {
                    "total_partners": len(energy_pools),
                    "critical": total_critical,
                    "warning": total_warning,
                    "sufficient": total_sufficient
                },
                "partner_statuses": partner_statuses,
                "monitored_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to monitor all partners: {e}")
            return {
                "success": False,
                "error": str(e),
                "monitored_at": datetime.utcnow().isoformat()
            }


class EnergyPredictionService:
    """에너지 예측 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_prediction(self, energy_pool_id: int) -> Optional[EnergyPrediction]:
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
            recent_usage = [safe_decimal_to_float(log.energy_consumed) for log in usage_logs[:30]]
            avg_usage = sum(recent_usage) / len(recent_usage) if recent_usage else 0
            
            # 예측 생성
            prediction = EnergyPrediction(
                energy_pool_id=energy_pool_id,
                prediction_date=datetime.utcnow() + timedelta(days=1),
                predicted_usage=Decimal(str(int(avg_usage * 24))),  # 24시간 예측
                confidence_score=Decimal('75.0'),  # 임시 신뢰도
                historical_pattern={"avg_hourly": avg_usage},
                seasonal_factors={},
                trend_analysis={"trend": "stable"}
            )
            
            self.db.add(prediction)
            await self.db.commit()
            
            return prediction
            
        except Exception as e:
            logger.error(f"Failed to generate prediction for energy pool {energy_pool_id}: {e}")
            return None
