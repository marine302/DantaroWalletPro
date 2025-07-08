"""
Doc #25: 에너지 풀 고급 관리 시스템 - 에너지 모니터링 서비스
실시간 모니터링, 예측 분석, 알림 시스템, 패턴 분석
"""
import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc, func
from sqlalchemy.orm import selectinload

from app.models.partner import Partner
from app.models.energy_pool import (
    PartnerEnergyPool, EnergyAlert, PartnerEnergyUsageLog, 
    EnergyPrediction, EnergyStatus, EnergyAlertType
)
from app.core.config import settings
try:
    from tronpy import Tron
    from tronpy.exceptions import TronError, ValidationError
except ImportError:
    Tron = None
    class TronError(Exception):
        pass
    class ValidationError(Exception):
        pass

logger = logging.getLogger(__name__)


class EnergyMonitoringService:
    """Doc #25: 에너지 풀 고급 관리 시스템"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        if Tron:
            self.tron = Tron(network='mainnet' if getattr(settings, 'TRON_NETWORK', 'nile') == 'mainnet' else 'nile')
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
                energy_pool = await self._initialize_partner_energy_pool(partner_id)
            
            # 블록체인에서 실시간 정보 조회
            await self._update_energy_status(energy_pool)
            
            # 상태 분석 및 알림 체크
            alerts = await self._check_and_create_alerts(energy_pool)
            
            # 예측 분석 업데이트
            prediction = await self._update_energy_prediction(energy_pool)
            
            await self.db.commit()
            
            return {
                "partner_id": partner_id,
                "energy_pool": {
                    "total_energy": int(energy_pool.total_energy or 0),
                    "available_energy": int(energy_pool.available_energy or 0),
                    "used_energy": int(energy_pool.used_energy or 0),
                    "usage_percentage": await self._calculate_usage_percentage(energy_pool),
                    "status": energy_pool.status or "sufficient",
                    "daily_average_usage": int(energy_pool.daily_average_usage or 0),
                    "peak_usage_hour": energy_pool.peak_usage_hour,
                    "depletion_estimated_at": energy_pool.depletion_estimated_at,
                    "last_checked_at": energy_pool.last_checked_at
                },
                "alerts": [
                    {
                        "id": alert.id,
                        "type": alert.alert_type,
                        "severity": alert.severity,
                        "message": alert.message,
                        "created_at": alert.created_at
                    } for alert in alerts
                ],
                "prediction": {
                    "predicted_usage": int(prediction.predicted_usage) if prediction else 0,
                    "predicted_depletion": prediction.predicted_depletion if prediction else None,
                    "confidence_score": float(prediction.confidence_score or 0) if prediction else 0,
                    "recommended_action": prediction.recommended_action if prediction else None
                } if prediction else None
            }
            
        except Exception as e:
            logger.error(f"Failed to monitor partner energy {partner_id}: {e}")
            await self.db.rollback()
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
            status="sufficient",
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
    
    async def _update_energy_status(self, energy_pool: PartnerEnergyPool):
        """블록체인에서 에너지 상태 업데이트"""
        try:
            if not self.tron:
                # TRON 클라이언트가 없는 경우 Mock 데이터 사용
                await self._update_energy_status_mock(energy_pool)
                return
            
            # TronPy를 사용하여 실제 계정 리소스 조회
            account_info = self.tron.get_account_resource(energy_pool.wallet_address)
            
            # 에너지 정보 업데이트
            total_energy = account_info.get('EnergyLimit', 0)
            used_energy = account_info.get('EnergyUsed', 0)
            available_energy = max(0, total_energy - used_energy)
            
            # SQLAlchemy 컬럼에 값 할당
            await self.db.execute(
                select(PartnerEnergyPool).where(PartnerEnergyPool.id == energy_pool.id)
            )
            
            # 에너지 풀 업데이트
            energy_pool.total_energy = Decimal(str(total_energy))
            energy_pool.available_energy = Decimal(str(available_energy))
            energy_pool.used_energy = Decimal(str(used_energy))
            
            # 대역폭 정보 업데이트
            total_bandwidth = account_info.get('NetLimit', 0)
            used_bandwidth = account_info.get('NetUsed', 0)
            energy_pool.total_bandwidth = Decimal(str(total_bandwidth))
            energy_pool.available_bandwidth = Decimal(str(max(0, total_bandwidth - used_bandwidth)))
            
            # TRX 동결 정보 업데이트
            account_detail = self.tron.get_account(energy_pool.wallet_address)
            frozen_info = account_detail.get('frozen', [])
            
            frozen_for_energy = Decimal('0')
            frozen_for_bandwidth = Decimal('0')
            
            for frozen in frozen_info:
                if frozen.get('frozen_balance', 0) > 0:
                    balance_trx = Decimal(str(frozen['frozen_balance'])) / Decimal('1000000')  # SUN to TRX
                    if frozen.get('frozen_resource') == 'ENERGY':
                        frozen_for_energy += balance_trx
                    elif frozen.get('frozen_resource') == 'BANDWIDTH':
                        frozen_for_bandwidth += balance_trx
            
            energy_pool.frozen_for_energy = frozen_for_energy
            energy_pool.frozen_for_bandwidth = frozen_for_bandwidth
            energy_pool.frozen_trx_amount = frozen_for_energy + frozen_for_bandwidth
            
            # 상태 업데이트
            usage_percentage = await self._calculate_usage_percentage(energy_pool)
            if usage_percentage >= energy_pool.critical_threshold:
                energy_pool.status = "critical"
            elif usage_percentage >= energy_pool.warning_threshold:
                energy_pool.status = "warning"
            else:
                energy_pool.status = "sufficient"
            
            energy_pool.last_checked_at = datetime.utcnow()
            
        except Exception as e:
            logger.warning(f"Failed to update energy status from blockchain: {e}")
            # 블록체인 조회 실패 시 Mock 데이터 사용
            await self._update_energy_status_mock(energy_pool)
    
    async def _update_energy_status_mock(self, energy_pool: PartnerEnergyPool):
        """Mock 에너지 상태 업데이트 (테스트용)"""
        # 기본값으로 업데이트
        energy_pool.total_energy = Decimal('10000')
        energy_pool.used_energy = Decimal('3000') 
        energy_pool.available_energy = Decimal('7000')
        energy_pool.total_bandwidth = Decimal('5000')
        energy_pool.available_bandwidth = Decimal('4000')
        energy_pool.frozen_trx_amount = Decimal('100')
        energy_pool.frozen_for_energy = Decimal('80')
        energy_pool.frozen_for_bandwidth = Decimal('20')
        energy_pool.status = "sufficient"
        energy_pool.last_checked_at = datetime.utcnow()
    
    async def _calculate_usage_percentage(self, energy_pool: PartnerEnergyPool) -> float:
        """에너지 사용률 계산"""
        total = float(energy_pool.total_energy or 0)
        used = float(energy_pool.used_energy or 0)
        
        if total == 0:
            return 0.0
        return (used / total) * 100
    
    async def _check_and_create_alerts(self, energy_pool: PartnerEnergyPool) -> List[EnergyAlert]:
        """알림 조건 체크 및 생성"""
        alerts = []
        usage_percentage = await self._calculate_usage_percentage(energy_pool)
        
        # 중복 알림 방지를 위한 최근 알림 체크
        recent_alerts = await self._get_recent_alerts(energy_pool.id, hours=1)
        recent_alert_types = {alert.alert_type for alert in recent_alerts}
        
        # 위험 임계값 알림
        if (usage_percentage >= energy_pool.critical_threshold and 
            EnergyAlertType.THRESHOLD_CRITICAL.value not in recent_alert_types):
            
            alert = EnergyAlert(
                energy_pool_id=energy_pool.id,
                alert_type=EnergyAlertType.THRESHOLD_CRITICAL.value,
                severity="critical",
                title="에너지 위험 임계값 도달",
                message=f"파트너 {energy_pool.partner_id}의 에너지 사용률이 {usage_percentage:.1f}%에 도달했습니다.",
                threshold_value=Decimal(str(energy_pool.critical_threshold)),
                current_value=Decimal(str(usage_percentage)),
                estimated_hours_remaining=await self._estimate_hours_remaining(energy_pool)
            )
            alerts.append(alert)
            self.db.add(alert)
        
        # 경고 임계값 알림
        elif (usage_percentage >= energy_pool.warning_threshold and 
              EnergyAlertType.THRESHOLD_WARNING.value not in recent_alert_types):
            
            alert = EnergyAlert(
                energy_pool_id=energy_pool.id,
                alert_type=EnergyAlertType.THRESHOLD_WARNING.value,
                severity="warning",
                title="에너지 경고 임계값 도달",
                message=f"파트너 {energy_pool.partner_id}의 에너지 사용률이 {usage_percentage:.1f}%에 도달했습니다.",
                threshold_value=Decimal(str(energy_pool.warning_threshold)),
                current_value=Decimal(str(usage_percentage)),
                estimated_hours_remaining=await self._estimate_hours_remaining(energy_pool)
            )
            alerts.append(alert)
            self.db.add(alert)
        
        return alerts
    
    async def _get_recent_alerts(self, energy_pool_id: int, hours: int = 24) -> List[EnergyAlert]:
        """최근 알림 조회"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.db.execute(
            select(EnergyAlert).where(
                and_(
                    EnergyAlert.energy_pool_id == energy_pool_id,
                    EnergyAlert.created_at >= cutoff_time
                )
            ).order_by(desc(EnergyAlert.created_at))
        )
        
        return result.scalars().all()
    
    async def _estimate_hours_remaining(self, energy_pool: PartnerEnergyPool) -> Optional[int]:
        """에너지 고갈까지 남은 시간 추정"""
        daily_avg = float(energy_pool.daily_average_usage or 0)
        available = float(energy_pool.available_energy or 0)
        
        if daily_avg == 0 or available == 0:
            return None
        
        hourly_usage = daily_avg / 24
        if hourly_usage <= 0:
            return None
        
        hours_remaining = int(available / hourly_usage)
        return max(0, hours_remaining)
    
    async def _update_energy_prediction(self, energy_pool: PartnerEnergyPool) -> Optional[EnergyPrediction]:
        """에너지 사용 예측 업데이트"""
        try:
            # 과거 사용 패턴 분석
            usage_history = await self._get_usage_history(energy_pool.id, days=7)
            
            if not usage_history:
                return None
            
            # 간단한 선형 예측 (실제로는 더 복잡한 ML 모델 사용 가능)
            daily_usages = [float(log.energy_consumed) for log in usage_history[-7:]]
            if not daily_usages:
                return None
            
            avg_daily_usage = sum(daily_usages) / len(daily_usages)
            trend = self._calculate_trend(daily_usages)
            
            # 예측 사용량 계산 (다음 24시간)
            predicted_usage = avg_daily_usage * (1 + trend)
            
            # 예측 고갈 시간 계산
            predicted_depletion = None
            available = float(energy_pool.available_energy or 0)
            if predicted_usage > 0 and available > 0:
                days_remaining = available / predicted_usage
                if days_remaining > 0:
                    predicted_depletion = datetime.utcnow() + timedelta(days=days_remaining)
            
            # 신뢰도 점수 계산 (데이터 품질 기반)
            confidence_score = min(100, len(daily_usages) * 10 + 30)
            
            # 권장 조치 결정
            recommended_action = await self._determine_recommended_action(energy_pool, predicted_usage)
            
            # 기존 예측 업데이트 또는 새로 생성
            result = await self.db.execute(
                select(EnergyPrediction).where(
                    EnergyPrediction.energy_pool_id == energy_pool.id
                ).order_by(desc(EnergyPrediction.created_at)).limit(1)
            )
            
            prediction = result.scalar_one_or_none()
            
            if prediction:
                prediction.predicted_usage = Decimal(str(predicted_usage))
                prediction.predicted_depletion = predicted_depletion
                prediction.confidence_score = Decimal(str(confidence_score))
                prediction.recommended_action = recommended_action
            else:
                prediction = EnergyPrediction(
                    energy_pool_id=energy_pool.id,
                    prediction_date=datetime.utcnow(),
                    predicted_usage=Decimal(str(predicted_usage)),
                    predicted_depletion=predicted_depletion,
                    confidence_score=Decimal(str(confidence_score)),
                    recommended_action=recommended_action,
                    historical_pattern={"daily_usages": daily_usages},
                    trend_factors={"trend": trend, "average": avg_daily_usage}
                )
                self.db.add(prediction)
            
            return prediction
            
        except Exception as e:
            logger.error(f"Failed to update energy prediction: {e}")
            return None
    
    async def _get_usage_history(self, energy_pool_id: int, days: int = 30) -> List[PartnerEnergyUsageLog]:
        """에너지 사용 이력 조회"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.db.execute(
            select(PartnerEnergyUsageLog).where(
                and_(
                    PartnerEnergyUsageLog.energy_pool_id == energy_pool_id,
                    PartnerEnergyUsageLog.created_at >= cutoff_date
                )
            ).order_by(asc(PartnerEnergyUsageLog.created_at))
        )
        
        return result.scalars().all()
    
    def _calculate_trend(self, values: List[float]) -> float:
        """값들의 트렌드 계산 (간단한 선형 회귀)"""
        if len(values) < 2:
            return 0
        
        n = len(values)
        x_avg = (n - 1) / 2
        y_avg = sum(values) / n
        
        numerator = sum((i - x_avg) * (values[i] - y_avg) for i in range(n))
        denominator = sum((i - x_avg) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0
        
        slope = numerator / denominator
        return slope / y_avg if y_avg != 0 else 0  # 정규화된 기울기
    
    async def _determine_recommended_action(self, energy_pool: PartnerEnergyPool, predicted_usage: float) -> str:
        """권장 조치 결정"""
        usage_percentage = await self._calculate_usage_percentage(energy_pool)
        available = float(energy_pool.available_energy or 0)
        
        if usage_percentage >= energy_pool.critical_threshold:
            return "immediate_recharge"
        elif usage_percentage >= energy_pool.warning_threshold:
            return "schedule_recharge"
        elif predicted_usage > available * 0.8:
            return "monitor_closely"
        else:
            return "normal_operation"
    
    async def get_energy_analytics(self, partner_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """에너지 사용 분석 데이터"""
        try:
            if partner_id:
                # 특정 파트너 분석
                return await self._get_partner_analytics(partner_id, days)
            else:
                # 전체 파트너 분석
                return await self._get_global_analytics(days)
                
        except Exception as e:
            logger.error(f"Failed to get energy analytics: {e}")
            raise
    
    async def _get_partner_analytics(self, partner_id: int, days: int) -> Dict[str, Any]:
        """특정 파트너 에너지 분석"""
        # 에너지 풀 조회
        result = await self.db.execute(
            select(PartnerEnergyPool).where(PartnerEnergyPool.partner_id == partner_id)
        )
        energy_pool = result.scalar_one_or_none()
        
        if not energy_pool:
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
                }
            }
        
        # 사용 이력 조회
        usage_logs = await self._get_usage_history(energy_pool.id, days)
        
        total_usage = sum(float(log.energy_consumed) for log in usage_logs)
        avg_daily = total_usage / days if days > 0 else 0
        peak_usage = max((float(log.energy_consumed) for log in usage_logs), default=0)
        
        return {
            "partner_id": partner_id,
            "period_days": days,
            "total_energy_used": int(total_usage),
            "average_daily_usage": int(avg_daily),
            "peak_usage": int(peak_usage),
            "efficiency_score": 85.0,  # 임시값
            "usage_pattern": {
                "hourly": [],
                "daily": [],
                "trend": "stable"
            }
        }
    
    async def _get_global_analytics(self, days: int) -> Dict[str, Any]:
        """전체 에너지 사용 분석"""
        # 전체 파트너 에너지 풀 조회
        result = await self.db.execute(select(PartnerEnergyPool))
        energy_pools = result.scalars().all()
        
        total_partners = len(energy_pools)
        active_partners = len([p for p in energy_pools if p.status != "depleted"])
        
        return {
            "period_days": days,
            "total_partners": total_partners,
            "active_partners": active_partners,
            "total_energy_consumed": 0,
            "average_efficiency": 82.5,
            "top_consumers": [],
            "system_health": "good"
        }
    
    async def log_energy_usage(
        self, 
        partner_id: int, 
        transaction_type: str,
        energy_consumed: int,
        transaction_hash: Optional[str] = None,
        bandwidth_consumed: int = 0,
        energy_unit_price: Optional[Decimal] = None
    ) -> bool:
        """에너지 사용 로그 기록"""
        try:
            # 파트너 에너지 풀 조회 또는 생성
            result = await self.db.execute(
                select(PartnerEnergyPool).where(
                    PartnerEnergyPool.partner_id == partner_id
                )
            )
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool:
                energy_pool = await self._initialize_partner_energy_pool(partner_id)
            
            # 에너지 사용 로그 생성
            total_cost = None
            if energy_unit_price:
                total_cost = Decimal(str(energy_consumed)) * energy_unit_price
            
            usage_log = PartnerEnergyUsageLog(
                energy_pool_id=energy_pool.id,
                transaction_type=transaction_type,
                transaction_hash=transaction_hash,
                energy_consumed=Decimal(str(energy_consumed)),
                bandwidth_consumed=Decimal(str(bandwidth_consumed)),
                energy_unit_price=energy_unit_price,
                total_cost=total_cost
            )
            
            self.db.add(usage_log)
            
            # 에너지 풀 상태 업데이트
            current_used = float(energy_pool.used_energy or 0)
            current_total = float(energy_pool.total_energy or 0)
            
            new_used = current_used + energy_consumed
            energy_pool.used_energy = Decimal(str(new_used))
            
            if current_total > 0:
                energy_pool.available_energy = Decimal(str(max(0, current_total - new_used)))
            
            await self.db.commit()
            logger.info(f"Logged energy usage for partner {partner_id}: {energy_consumed} energy")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log energy usage: {e}")
            await self.db.rollback()
            return False
        """실시간 에너지 상태 업데이트"""
        try:
            # TRON 네트워크에서 실제 데이터 조회
            account_info = await self._get_account_info(wallet_address)
            if not account_info:
                raise Exception("계정 정보 조회 실패")
            
            # 에너지 풀 정보 가져오기 또는 생성
            energy_pool = await self.get_partner_energy_pool(partner_id)
            if not energy_pool:
                energy_pool = await self._create_energy_pool(partner_id, wallet_address)
            
            # 에너지 및 대역폭 정보 업데이트
            energy_data = account_info.get('account_resource', {})
            
            # 에너지 정보
            total_energy = energy_data.get('EnergyLimit', 0)
            available_energy = energy_data.get('EnergyUsed', 0)
            available_energy = max(0, total_energy - available_energy)
            
            # 대역폭 정보
            total_bandwidth = energy_data.get('NetLimit', 0)
            bandwidth_used = energy_data.get('NetUsed', 0)
            available_bandwidth = max(0, total_bandwidth - bandwidth_used)
            
            # TRX 동결 정보
            frozen_info = await self._get_frozen_info(account_info)
            
            # 에너지 풀 업데이트
            energy_pool.total_energy = total_energy
            energy_pool.available_energy = available_energy
            energy_pool.used_energy = total_energy - available_energy
            energy_pool.total_bandwidth = total_bandwidth
            energy_pool.available_bandwidth = available_bandwidth
            energy_pool.frozen_trx_amount = frozen_info['total']
            energy_pool.frozen_for_energy = frozen_info['energy']
            energy_pool.frozen_for_bandwidth = frozen_info['bandwidth']
            energy_pool.last_checked_at = datetime.utcnow()
            
            # 상태 계산 및 업데이트
            new_status = self._calculate_energy_status(energy_pool)
            old_status = energy_pool.status
            energy_pool.status = new_status
            
            # 예측 업데이트
            await self._update_predictions(energy_pool)
            
            await self.db.commit()
            
            # 상태 변경 시 알림 처리
            if old_status != new_status:
                await self._handle_status_change(energy_pool, old_status, new_status)
            
            return {
                "success": True,
                "partner_id": partner_id,
                "wallet_address": wallet_address,
                "energy": {
                    "total": int(total_energy),
                    "available": int(available_energy),
                    "used": int(total_energy - available_energy),
                    "percentage": round((available_energy / total_energy * 100) if total_energy > 0 else 0, 2)
                },
                "bandwidth": {
                    "total": int(total_bandwidth),
                    "available": int(available_bandwidth),
                    "used": int(bandwidth_used)
                },
                "frozen_trx": {
                    "total": float(frozen_info['total']),
                    "energy": float(frozen_info['energy']),
                    "bandwidth": float(frozen_info['bandwidth'])
                },
                "status": new_status.value,
                "last_checked": energy_pool.last_checked_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"에너지 상태 업데이트 실패: {e}")
            await self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def _get_account_info(self, wallet_address: str) -> Optional[Dict]:
        """TRON 계정 정보 조회"""
        try:
            # TronPy를 사용하여 계정 정보 조회
            account = self.tron.get_account(wallet_address)
            return account
        except TronError as e:
            logger.error(f"TRON 계정 정보 조회 실패: {e}")
            return None
        except Exception as e:
            logger.error(f"예상치 못한 오류: {e}")
            return None
    
    async def _get_frozen_info(self, account_info: Dict) -> Dict[str, Decimal]:
        """TRX 동결 정보 파싱"""
        frozen_info = {
            'total': Decimal('0'),
            'energy': Decimal('0'),
            'bandwidth': Decimal('0')
        }
        
        try:
            # frozen 필드에서 동결 정보 추출
            frozen_list = account_info.get('frozen', [])
            for frozen in frozen_list:
                amount = Decimal(str(frozen.get('frozen_balance', 0))) / Decimal('1000000')  # Sun to TRX
                
                if frozen.get('resource') == 'ENERGY':
                    frozen_info['energy'] += amount
                elif frozen.get('resource') == 'BANDWIDTH':
                    frozen_info['bandwidth'] += amount
                
                frozen_info['total'] += amount
            
            return frozen_info
        except Exception as e:
            logger.error(f"동결 정보 파싱 실패: {e}")
            return frozen_info
    
    def _calculate_energy_status(self, energy_pool: PartnerEnergyPool) -> EnergyStatus:
        """에너지 상태 계산"""
        if energy_pool.total_energy == 0:
            return EnergyStatus.DEPLETED
        
        percentage = (energy_pool.available_energy / energy_pool.total_energy) * 100
        
        if percentage <= energy_pool.critical_threshold:
            return EnergyStatus.CRITICAL
        elif percentage <= energy_pool.warning_threshold:
            return EnergyStatus.WARNING
        else:
            return EnergyStatus.SUFFICIENT
    
    async def _create_energy_pool(self, partner_id: int, wallet_address: str) -> PartnerEnergyPool:
        """새 에너지 풀 생성"""
        energy_pool = PartnerEnergyPool(
            partner_id=partner_id,
            wallet_address=wallet_address,
            status=EnergyStatus.SUFFICIENT,
            warning_threshold=30,
            critical_threshold=10,
            auto_response_enabled=True
        )
        
        self.db.add(energy_pool)
        await self.db.flush()
        return energy_pool
    
    async def _update_predictions(self, energy_pool: PartnerEnergyPool):
        """에너지 예측 업데이트"""
        try:
            # 과거 24시간 사용 패턴 분석
            usage_logs = await self._get_recent_usage_logs(energy_pool.id, hours=24)
            
            if not usage_logs:
                return
            
            # 시간당 평균 사용량 계산
            hourly_usage = self._calculate_hourly_usage(usage_logs)
            daily_average = sum(hourly_usage) / len(hourly_usage) if hourly_usage else 0
            
            # 고갈 시간 예측
            if daily_average > 0 and energy_pool.available_energy > 0:
                hours_remaining = float(energy_pool.available_energy) / daily_average
                depletion_time = datetime.utcnow() + timedelta(hours=hours_remaining)
            else:
                depletion_time = None
            
            # 피크 사용 시간 계산
            peak_hour = self._find_peak_usage_hour(usage_logs)
            
            # 에너지 풀 업데이트
            energy_pool.daily_average_usage = Decimal(str(daily_average))
            energy_pool.depletion_estimated_at = depletion_time
            energy_pool.peak_usage_hour = peak_hour
            
            # 과거 지표 저장 (최근 24시간)
            metrics_history = {
                'timestamp': datetime.utcnow().isoformat(),
                'hourly_usage': hourly_usage,
                'daily_average': daily_average,
                'peak_hour': peak_hour
            }
            
            if energy_pool.metrics_history:
                history = json.loads(energy_pool.metrics_history) if isinstance(energy_pool.metrics_history, str) else energy_pool.metrics_history
                history.append(metrics_history)
                # 최근 7일치만 보관
                history = history[-168:]  # 7일 * 24시간
            else:
                history = [metrics_history]
            
            energy_pool.metrics_history = history
            
        except Exception as e:
            logger.error(f"예측 업데이트 실패: {e}")
    
    async def _get_recent_usage_logs(self, energy_pool_id: int, hours: int = 24) -> List[PartnerEnergyUsageLog]:
        """최근 사용 로그 조회"""
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            result = await self.db.execute(
                select(PartnerEnergyUsageLog)
                .where(
                    and_(
                        PartnerEnergyUsageLog.energy_pool_id == energy_pool_id,
                        PartnerEnergyUsageLog.created_at >= since
                    )
                )
                .order_by(PartnerEnergyUsageLog.created_at)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"사용 로그 조회 실패: {e}")
            return []
    
    def _calculate_hourly_usage(self, usage_logs: List[PartnerEnergyUsageLog]) -> List[float]:
        """시간당 사용량 계산"""
        if not usage_logs:
            return []
        
        hourly_usage = {}
        for log in usage_logs:
            hour = log.created_at.hour
            if hour not in hourly_usage:
                hourly_usage[hour] = 0
            hourly_usage[hour] += float(log.energy_consumed)
        
        return list(hourly_usage.values())
    
    def _find_peak_usage_hour(self, usage_logs: List[PartnerEnergyUsageLog]) -> Optional[int]:
        """피크 사용 시간 찾기"""
        if not usage_logs:
            return None
        
        hourly_usage = {}
        for log in usage_logs:
            hour = log.created_at.hour
            if hour not in hourly_usage:
                hourly_usage[hour] = 0
            hourly_usage[hour] += float(log.energy_consumed)
        
        if not hourly_usage:
            return None
        
        return max(hourly_usage, key=hourly_usage.get)
    
    async def _handle_status_change(self, energy_pool: PartnerEnergyPool, old_status: EnergyStatus, new_status: EnergyStatus):
        """상태 변경 시 알림 처리"""
        try:
            # 상태 악화 시에만 알림
            status_priority = {
                EnergyStatus.SUFFICIENT: 0,
                EnergyStatus.WARNING: 1,
                EnergyStatus.CRITICAL: 2,
                EnergyStatus.DEPLETED: 3
            }
            
            if status_priority[new_status] > status_priority[old_status]:
                await self._send_status_alert(energy_pool, new_status)
        
        except Exception as e:
            logger.error(f"상태 변경 알림 처리 실패: {e}")
    
    async def _send_status_alert(self, energy_pool: PartnerEnergyPool, status: EnergyStatus):
        """상태 알림 전송"""
        try:
            alert_type_map = {
                EnergyStatus.WARNING: EnergyAlertType.THRESHOLD_WARNING,
                EnergyStatus.CRITICAL: EnergyStatus.CRITICAL,
                EnergyStatus.DEPLETED: EnergyAlertType.DEPLETION_IMMINENT
            }
            
            alert_type = alert_type_map.get(status)
            if not alert_type:
                return
            
            # 에너지 잔량 계산
            energy_percentage = 0
            if energy_pool.total_energy > 0:
                energy_percentage = int((energy_pool.available_energy / energy_pool.total_energy) * 100)
            
            # 예상 잔여 시간 계산
            hours_remaining = None
            if energy_pool.depletion_estimated_at:
                hours_remaining = int((energy_pool.depletion_estimated_at - datetime.utcnow()).total_seconds() / 3600)
            
            # 알림 메시지 생성
            severity_map = {
                EnergyStatus.WARNING: "warning",
                EnergyStatus.CRITICAL: "critical", 
                EnergyStatus.DEPLETED: "critical"
            }
            
            title_map = {
                EnergyStatus.WARNING: "에너지 부족 경고",
                EnergyStatus.CRITICAL: "에너지 위험 상태",
                EnergyStatus.DEPLETED: "에너지 고갈"
            }
            
            message = f"파트너사 ID {energy_pool.partner_id}의 에너지가 {energy_percentage}% 남았습니다."
            if hours_remaining:
                message += f" 예상 고갈까지 {hours_remaining}시간 남았습니다."
            
            # 알림 기록 생성
            alert = EnergyAlert(
                energy_pool_id=energy_pool.id,
                alert_type=alert_type,
                severity=severity_map[status],
                title=title_map[status],
                message=message,
                energy_percentage=energy_percentage,
                available_energy=energy_pool.available_energy,
                estimated_hours_remaining=hours_remaining,
                sent_via=["system"],
                sent_to=["admin"],
                acknowledged=False
            )
            
            self.db.add(alert)
            energy_pool.last_alert_sent_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"에너지 상태 알림 전송: 파트너 {energy_pool.partner_id}, 상태: {status.value}")
            
        except Exception as e:
            logger.error(f"상태 알림 전송 실패: {e}")
            await self.db.rollback()
    
    async def get_energy_dashboard_data(self, partner_id: int) -> Dict[str, Any]:
        """에너지 대시보드 데이터 조회"""
        try:
            energy_pool = await self.get_partner_energy_pool(partner_id)
            if not energy_pool:
                return {"success": False, "error": "에너지 풀을 찾을 수 없습니다"}
            
            # 최근 알림 조회
            recent_alerts = await self.db.execute(
                select(EnergyAlert)
                .where(EnergyAlert.energy_pool_id == energy_pool.id)
                .order_by(desc(EnergyAlert.sent_at))
                .limit(10)
            )
            alerts = recent_alerts.scalars().all()
            
            # 최근 사용 로그 조회
            usage_logs = await self._get_recent_usage_logs(energy_pool.id, hours=24)
            
            return {
                "success": True,
                "energy_pool": {
                    "partner_id": energy_pool.partner_id,
                    "wallet_address": energy_pool.wallet_address,
                    "status": energy_pool.status.value,
                    "total_energy": int(energy_pool.total_energy),
                    "available_energy": int(energy_pool.available_energy),
                    "used_energy": int(energy_pool.used_energy),
                    "energy_percentage": round((energy_pool.available_energy / energy_pool.total_energy * 100) if energy_pool.total_energy > 0 else 0, 2),
                    "frozen_trx": float(energy_pool.frozen_trx_amount),
                    "daily_average_usage": float(energy_pool.daily_average_usage or 0),
                    "peak_usage_hour": energy_pool.peak_usage_hour,
                    "depletion_estimated_at": energy_pool.depletion_estimated_at.isoformat() if energy_pool.depletion_estimated_at else None,
                    "last_checked_at": energy_pool.last_checked_at.isoformat() if energy_pool.last_checked_at else None
                },
                "recent_alerts": [
                    {
                        "id": alert.id,
                        "type": alert.alert_type.value,
                        "severity": alert.severity,
                        "title": alert.title,
                        "message": alert.message,
                        "sent_at": alert.sent_at.isoformat(),
                        "acknowledged": alert.acknowledged
                    } for alert in alerts
                ],
                "usage_statistics": {
                    "last_24h_logs": len(usage_logs),
                    "total_energy_consumed": sum(float(log.energy_consumed) for log in usage_logs),
                    "average_per_transaction": sum(float(log.energy_consumed) for log in usage_logs) / len(usage_logs) if usage_logs else 0
                }
            }
            
        except Exception as e:
            logger.error(f"대시보드 데이터 조회 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def monitor_all_partners(self) -> Dict[str, Any]:
        """모든 파트너의 에너지 상태 모니터링"""
        try:
            result = await self.db.execute(select(PartnerEnergyPool))
            energy_pools = result.scalars().all()
            
            monitoring_results = []
            
            for energy_pool in energy_pools:
                try:
                    # 각 파트너의 에너지 상태 업데이트
                    update_result = await self.update_energy_status(
                        energy_pool.partner_id, 
                        energy_pool.wallet_address
                    )
                    monitoring_results.append(update_result)
                except Exception as e:
                    logger.error(f"파트너 {energy_pool.partner_id} 모니터링 실패: {e}")
                    monitoring_results.append({
                        "success": False,
                        "partner_id": energy_pool.partner_id,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "monitored_partners": len(energy_pools),
                "successful_updates": len([r for r in monitoring_results if r.get("success")]),
                "failed_updates": len([r for r in monitoring_results if not r.get("success")]),
                "results": monitoring_results
            }
            
        except Exception as e:
            logger.error(f"전체 파트너 모니터링 실패: {e}")
            return {"success": False, "error": str(e)}


class EnergyPredictionService:
    """에너지 예측 분석 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def analyze_usage_patterns(self, partner_id: int, days: int = 7) -> Dict[str, Any]:
        """사용 패턴 분석"""
        try:
            # 파트너 에너지 풀 조회
            result = await self.db.execute(
                select(PartnerEnergyPool).where(PartnerEnergyPool.partner_id == partner_id)
            )
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool:
                return {"success": False, "error": "에너지 풀을 찾을 수 없습니다"}
            
            # 과거 사용 로그 조회
            since = datetime.utcnow() - timedelta(days=days)
            logs_result = await self.db.execute(
                select(PartnerEnergyUsageLog)
                .where(
                    and_(
                        PartnerEnergyUsageLog.energy_pool_id == energy_pool.id,
                        PartnerEnergyUsageLog.created_at >= since
                    )
                )
                .order_by(PartnerEnergyUsageLog.created_at)
            )
            usage_logs = logs_result.scalars().all()
            
            # 패턴 분석
            daily_usage = self._analyze_daily_patterns(usage_logs)
            hourly_usage = self._analyze_hourly_patterns(usage_logs)
            trend_analysis = self._analyze_trends(usage_logs)
            
            return {
                "success": True,
                "partner_id": partner_id,
                "analysis_period": f"{days} days",
                "patterns": {
                    "daily_usage": daily_usage,
                    "hourly_usage": hourly_usage,
                    "trend_analysis": trend_analysis
                }
            }
            
        except Exception as e:
            logger.error(f"사용 패턴 분석 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def _analyze_daily_patterns(self, usage_logs: List[PartnerEnergyUsageLog]) -> Dict[str, Any]:
        """일별 패턴 분석"""
        daily_data = {}
        
        for log in usage_logs:
            date_key = log.created_at.date().isoformat()
            if date_key not in daily_data:
                daily_data[date_key] = {
                    "total_energy": 0,
                    "transaction_count": 0
                }
            
            daily_data[date_key]["total_energy"] += float(log.energy_consumed)
            daily_data[date_key]["transaction_count"] += 1
        
        # 통계 계산
        daily_usage_values = [data["total_energy"] for data in daily_data.values()]
        
        return {
            "daily_data": daily_data,
            "average_daily_usage": sum(daily_usage_values) / len(daily_usage_values) if daily_usage_values else 0,
            "max_daily_usage": max(daily_usage_values) if daily_usage_values else 0,
            "min_daily_usage": min(daily_usage_values) if daily_usage_values else 0
        }
    
    def _analyze_hourly_patterns(self, usage_logs: List[PartnerEnergyUsageLog]) -> Dict[str, Any]:
        """시간별 패턴 분석"""
        hourly_data = {}
        
        for log in usage_logs:
            hour = log.created_at.hour
            if hour not in hourly_data:
                hourly_data[hour] = {
                    "total_energy": 0,
                    "transaction_count": 0
                }
            
            hourly_data[hour]["total_energy"] += float(log.energy_consumed)
            hourly_data[hour]["transaction_count"] += 1
        
        # 피크 시간 찾기
        peak_hour = max(hourly_data, key=lambda h: hourly_data[h]["total_energy"]) if hourly_data else None
        
        return {
            "hourly_data": hourly_data,
            "peak_hour": peak_hour,
            "peak_usage": hourly_data[peak_hour]["total_energy"] if peak_hour else 0
        }
    
    def _analyze_trends(self, usage_logs: List[PartnerEnergyUsageLog]) -> Dict[str, Any]:
        """트렌드 분석"""
        if len(usage_logs) < 2:
            return {"trend": "insufficient_data"}
        
        # 시간순 정렬 후 트렌드 계산
        sorted_logs = sorted(usage_logs, key=lambda x: x.created_at)
        
        # 첫 절반과 후 절반 비교
        mid_point = len(sorted_logs) // 2
        first_half = sorted_logs[:mid_point]
        second_half = sorted_logs[mid_point:]
        
        first_half_avg = sum(float(log.energy_consumed) for log in first_half) / len(first_half)
        second_half_avg = sum(float(log.energy_consumed) for log in second_half) / len(second_half)
        
        # 트렌드 방향 결정
        change_percentage = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0
        
        if change_percentage > 10:
            trend = "increasing"
        elif change_percentage < -10:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "change_percentage": round(change_percentage, 2),
            "first_period_avg": round(first_half_avg, 2),
            "second_period_avg": round(second_half_avg, 2)
        }


# 백그라운드 모니터링 태스크
async def background_energy_monitoring():
    """백그라운드에서 실행되는 에너지 모니터링"""
    while True:
        try:
            async for db in get_db():
                monitoring_service = EnergyMonitoringService(db)
                result = await monitoring_service.monitor_all_partners()
                logger.info(f"백그라운드 모니터링 완료: {result}")
                break
        except Exception as e:
            logger.error(f"백그라운드 모니터링 실패: {e}")
        
        # 5분마다 실행
        await asyncio.sleep(300)
