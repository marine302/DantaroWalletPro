"""에너지 풀 관리 서비스"""
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc, func
from sqlalchemy.orm import selectinload

from app.models.energy_pool import EnergyPoolModel, EnergyPoolStatus, EnergyUsageLog, EnergyPriceHistory
from app.models.user import User
from app.schemas.energy import (
    CreateEnergyPoolRequest,
    EnergyPoolResponse,
    EnergyPoolStatusResponse,
    EnergyUsageStatsResponse,
    EnergyUsageLogResponse,
    EnergySimulationRequest,
    EnergySimulationResponse,
    AutoManagementSettings,
    EnergyPriceHistoryResponse,
    MessageResponse
)
from app.core.exceptions import EnergyInsufficientError, ValidationError
from app.core.logger import get_logger

logger = get_logger(__name__)

class EnergyPoolModelService:
    """에너지 풀 관리 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_energy_status(self) -> EnergyPoolStatus:
        """현재 에너지 풀 상태를 조회합니다."""
        try:
            # 에너지 풀 정보 조회
            result = await self.db.execute(
                select(EnergyPoolModel).order_by(desc(EnergyPoolModel.id)).limit(1)
            )
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool:
                # 기본 에너지 풀 생성
                energy_pool = EnergyPoolModel(
                    total_energy=1000000,
                    available_energy=1000000,
                    reserved_energy=0,
                    daily_consumption=0
                )
                self.db.add(energy_pool)
                await self.db.commit()
                await self.db.refresh(energy_pool)
            
            # 에너지 충분 여부 확인
            energy_sufficient = energy_pool.available_energy > energy_pool.alert_threshold
            
            return EnergyPoolStatus(
                total_energy=energy_pool.total_energy,
                available_energy=energy_pool.available_energy,
                reserved_energy=energy_pool.reserved_energy,
                daily_consumption=energy_pool.daily_consumption,
                energy_sufficient=energy_sufficient,
                alert_threshold=energy_pool.alert_threshold,
                is_emergency_mode=energy_pool.is_emergency_mode,
                last_recharge_at=energy_pool.last_recharge_at
            )
            
        except Exception as e:
            logger.error(f"에너지 상태 조회 실패: {str(e)}")
            raise
    
    async def consume_energy(self, amount: int, transaction_type: str, 
                           user_id: Optional[int] = None, 
                           transaction_id: Optional[str] = None) -> bool:
        """에너지를 소모합니다."""
        try:
            # 현재 에너지 풀 조회
            result = await self.db.execute(
                select(EnergyPoolModel).order_by(desc(EnergyPoolModel.id)).limit(1)
            )
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool or energy_pool.available_energy < amount:
                raise EnergyInsufficientError("에너지가 부족합니다.")
            
            # 에너지 소모 처리
            await self.db.execute(
                update(EnergyPoolModel)
                .where(EnergyPoolModel.id == energy_pool.id)
                .values(
                    available_energy=EnergyPoolModel.available_energy - amount,
                    daily_consumption=EnergyPoolModel.daily_consumption + amount,
                    updated_at=func.now()
                )
            )
            
            # 에너지 거래 내역 저장
            energy_transaction = EnergyTransaction(
                transaction_type=transaction_type,
                energy_amount=amount,
                transaction_id=transaction_id,
                user_id=user_id,
                status="completed"
            )
            self.db.add(energy_transaction)
            
            await self.db.commit()
            
            # 에너지 부족 알림 확인
            await self._check_energy_alerts()
            
            logger.info(f"에너지 소모 완료: {amount} units, 유형: {transaction_type}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"에너지 소모 실패: {str(e)}")
            raise
    
    async def recharge_energy(self, request: EnergyRechargeRequest) -> bool:
        """에너지 풀을 충전합니다."""
        try:
            # 현재 에너지 풀 조회
            result = await self.db.execute(
                select(EnergyPoolModel).order_by(desc(EnergyPoolModel.id)).limit(1)
            )
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool:
                raise ValidationError("에너지 풀이 존재하지 않습니다.")
            
            # 에너지 충전 처리
            await self.db.execute(
                update(EnergyPoolModel)
                .where(EnergyPoolModel.id == energy_pool.id)
                .values(
                    total_energy=EnergyPoolModel.total_energy + request.amount,
                    available_energy=EnergyPoolModel.available_energy + request.amount,
                    last_recharge_at=func.now(),
                    is_emergency_mode=False,
                    updated_at=func.now()
                )
            )
            
            await self.db.commit()
            
            logger.info(f"에너지 충전 완료: {request.amount} units, 사유: {request.reason}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"에너지 충전 실패: {str(e)}")
            raise
    
    async def add_to_queue(self, user_id: int, request: EnergyQueueCreate) -> int:
        """에너지 부족 시 대기열에 추가합니다."""
        try:
            # 현재 대기열 크기 확인
            queue_size_result = await self.db.execute(
                select(func.count(EnergyQueue.id))
                .where(EnergyQueue.status == "pending")
            )
            queue_size = queue_size_result.scalar() or 0
            
            # 예상 대기 시간 계산 (대기열 크기 * 5분)
            estimated_wait_time = queue_size * 5
            
            # 대기열 추가
            queue_item = EnergyQueue(
                user_id=user_id,
                transaction_type=request.transaction_type,
                amount=request.amount,
                to_address=request.to_address,
                estimated_energy=request.estimated_energy,
                priority=request.priority,
                estimated_wait_time=estimated_wait_time,
                status="pending"
            )
            
            self.db.add(queue_item)
            await self.db.commit()
            await self.db.refresh(queue_item)
            
            logger.info(f"대기열 추가 완료: 사용자 {user_id}, 대기 순서: {queue_size + 1}")
            return queue_item.id
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"대기열 추가 실패: {str(e)}")
            raise
    
    async def get_queue_status(self, user_id: int) -> Optional[QueueStatus]:
        """사용자의 대기열 상태를 조회합니다."""
        try:
            # 사용자의 대기 중인 항목 조회
            result = await self.db.execute(
                select(EnergyQueue)
                .where(
                    EnergyQueue.user_id == user_id,
                    EnergyQueue.status == "pending"
                )
                .order_by(EnergyQueue.created_at)
                .limit(1)
            )
            queue_item = result.scalar_one_or_none()
            
            if not queue_item:
                return None
            
            # 앞에 있는 대기열 수 계산
            position_result = await self.db.execute(
                select(func.count(EnergyQueue.id))
                .where(
                    EnergyQueue.status == "pending",
                    EnergyQueue.created_at < queue_item.created_at
                )
            )
            queue_position = (position_result.scalar() or 0) + 1
            
            # 전체 대기열 크기
            total_size_result = await self.db.execute(
                select(func.count(EnergyQueue.id))
                .where(EnergyQueue.status == "pending")
            )
            total_queue_size = total_size_result.scalar() or 0
            
            # 현재 에너지 상태
            energy_status = await self.get_energy_status()
            
            return QueueStatus(
                queue_position=queue_position,
                estimated_wait_time=queue_position * 5,  # 5분 * 순서
                total_queue_size=total_queue_size,
                current_energy_status=energy_status
            )
            
        except Exception as e:
            logger.error(f"대기열 상태 조회 실패: {str(e)}")
            raise
    
    async def process_queue(self) -> List[int]:
        """대기열을 처리합니다."""
        try:
            # 처리 가능한 대기열 항목들 조회 (우선순위 순)
            result = await self.db.execute(
                select(EnergyQueue)
                .where(EnergyQueue.status == "pending")
                .order_by(desc(EnergyQueue.priority), EnergyQueue.created_at)
                .limit(10)  # 한 번에 최대 10개 처리
            )
            queue_items = result.scalars().all()
            
            processed_ids = []
            
            for item in queue_items:
                # 에너지 충분 여부 확인
                energy_status = await self.get_energy_status()
                
                if energy_status.available_energy >= item.estimated_energy:
                    # 에너지 소모 처리
                    await self.consume_energy(
                        amount=item.estimated_energy,
                        transaction_type=item.transaction_type,
                        user_id=item.user_id,
                        transaction_id=str(item.id)
                    )
                    
                    # 대기열 상태 업데이트
                    await self.db.execute(
                        update(EnergyQueue)
                        .where(EnergyQueue.id == item.id)
                        .values(
                            status="processed",
                            processed_at=func.now()
                        )
                    )
                    
                    processed_ids.append(item.id)
                else:
                    break  # 에너지 부족 시 중단
            
            await self.db.commit()
            
            if processed_ids:
                logger.info(f"대기열 처리 완료: {len(processed_ids)}개 항목")
            
            return processed_ids
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"대기열 처리 실패: {str(e)}")
            raise
    
    async def _check_energy_alerts(self):
        """에너지 부족 알림을 확인하고 생성합니다."""
        try:
            energy_status = await self.get_energy_status()
            
            # 임계값 미만 시 알림 생성
            if energy_status.available_energy < energy_status.alert_threshold:
                # 기존 활성 알림 확인
                existing_alert_result = await self.db.execute(
                    select(EnergyAlert)
                    .where(
                        EnergyAlert.alert_type == "low_energy",
                        EnergyAlert.is_active == True
                    )
                )
                existing_alert = existing_alert_result.scalar_one_or_none()
                
                if not existing_alert:
                    # 새 알림 생성
                    alert = EnergyAlert(
                        alert_type="low_energy",
                        title="에너지 부족 경고",
                        message=f"현재 에너지: {energy_status.available_energy}, 임계값: {energy_status.alert_threshold}",
                        severity="warning"
                    )
                    self.db.add(alert)
                    await self.db.commit()
                    
                    logger.warning(f"에너지 부족 알림 생성: {energy_status.available_energy}")
            
        except Exception as e:
            logger.error(f"에너지 알림 확인 실패: {str(e)}")
    
    async def get_usage_stats(self) -> EnergyUsageStats:
        """에너지 사용 통계를 조회합니다."""
        try:
            today = datetime.now().date()
            
            # 오늘 사용된 총 에너지
            total_used_result = await self.db.execute(
                select(func.sum(EnergyTransaction.energy_amount))
                .where(func.date(EnergyTransaction.created_at) == today)
            )
            total_used_today = total_used_result.scalar() or 0
            
            # 거래 수
            count_result = await self.db.execute(
                select(func.count(EnergyTransaction.id))
                .where(func.date(EnergyTransaction.created_at) == today)
            )
            transactions_count = count_result.scalar() or 0
            
            # 평균 에너지 사용량
            average_per_transaction = (
                total_used_today / transactions_count if transactions_count > 0 else 0
            )
            
            return EnergyUsageStats(
                total_used_today=total_used_today,
                average_per_transaction=average_per_transaction,
                peak_hour_usage=total_used_today,  # 단순화
                transactions_count=transactions_count
            )
            
        except Exception as e:
            logger.error(f"에너지 사용 통계 조회 실패: {str(e)}")
            raise

    async def process_emergency_withdrawal(
        self, user_id: int, withdrawal_data: EmergencyWithdrawalCreate
    ) -> EmergencyWithdrawalResponse:
        """긴급 출금을 처리합니다."""
        try:
            # 임시 응답 (실제 구현 시 블록체인 연동 필요)
            transaction_id = f"emergency_{user_id}_{datetime.now().timestamp()}"
            
            # 높은 수수료 계산 (일반 수수료의 3배)
            base_fee = Decimal("5.0")  # TRX
            high_fee = base_fee * 3
            
            return EmergencyWithdrawalResponse(
                transaction_id=transaction_id,
                status="pending",
                estimated_confirmation_time=5,  # 5분
                fee_amount=high_fee,
                message="긴급 출금이 처리 중입니다. 높은 수수료로 우선 처리됩니다."
            )
            
        except Exception as e:
            logger.error(f"긴급 출금 처리 실패: {str(e)}")
            raise

    async def get_active_alerts(self) -> List[EnergyAlert]:
        """활성 에너지 알림을 조회합니다."""
        try:
            result = await self.db.execute(
                select(EnergyAlert)
                .where(EnergyAlert.is_active == True)
                .order_by(desc(EnergyAlert.created_at))
            )
            alerts = result.scalars().all()
            
            return [
                EnergyAlert(
                    id=alert.id,
                    alert_type=alert.alert_type,
                    title=alert.title,
                    message=alert.message,
                    severity=alert.severity,
                    is_active=alert.is_active,
                    created_at=alert.created_at,
                    resolved_at=alert.resolved_at
                )
                for alert in alerts
            ]
            
        except Exception as e:
            logger.error(f"활성 알림 조회 실패: {str(e)}")
            raise

    async def cancel_queue_item(self, queue_id: int, user_id: int) -> bool:
        """대기열 항목을 취소합니다."""
        try:
            # 사용자 권한 확인 및 상태 업데이트
            result = await self.db.execute(
                update(EnergyQueue)
                .where(
                    EnergyQueue.id == queue_id,
                    EnergyQueue.user_id == user_id,
                    EnergyQueue.status == "pending"
                )
                .values(
                    status="cancelled",
                    processed_at=func.now()
                )
            )
            
            await self.db.commit()
            
            # 업데이트된 행이 있는지 확인
            return result.rowcount > 0
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"대기열 항목 취소 실패: {str(e)}")
            raise

    async def get_total_energy_status(self) -> dict:
        """슈퍼 어드민용 전체 에너지 풀 현황"""
        try:
            result = await self.db.execute(
                select(EnergyPoolModel).order_by(desc(EnergyPoolModel.id)).limit(1)
            )
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool:
                return {
                    "total_energy": 0,
                    "available_energy": 0,
                    "reserved_energy": 0,
                    "daily_consumption": 0,
                    "utilization_rate": 0.0,
                    "pool_health": "empty"
                }
            
            utilization_rate = ((energy_pool.total_energy - energy_pool.available_energy) / 
                              energy_pool.total_energy) * 100 if energy_pool.total_energy > 0 else 0
            
            # 풀 상태 판정
            if energy_pool.available_energy <= energy_pool.alert_threshold:
                pool_health = "critical"
            elif energy_pool.available_energy <= energy_pool.alert_threshold * 2:
                pool_health = "warning"
            else:
                pool_health = "healthy"
            
            return {
                "total_energy": int(energy_pool.total_energy),
                "available_energy": int(energy_pool.available_energy),
                "reserved_energy": int(energy_pool.reserved_energy),
                "daily_consumption": int(energy_pool.daily_consumption),
                "utilization_rate": round(utilization_rate, 2),
                "pool_health": pool_health,
                "alert_threshold": int(energy_pool.alert_threshold),
                "last_updated": energy_pool.updated_at
            }
            
        except Exception as e:
            logger.error(f"Failed to get total energy status: {e}")
            raise
    
    async def allocate_energy_to_partner(self, partner_id: str, amount: int) -> bool:
        """파트너에게 에너지 할당"""
        try:
            # 에너지 풀에서 사용 가능한 에너지 확인
            result = await self.db.execute(
                select(EnergyPoolModel).order_by(desc(EnergyPoolModel.id)).limit(1)
            )
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool or energy_pool.available_energy < amount:
                raise EnergyInsufficientError("Insufficient energy in pool")
            
            # 파트너 에너지 잔액 업데이트 (실제 구현에서는 Partner 모델에 energy_balance 필드 사용)
            # 임시로 에너지 풀에서 차감
            energy_pool.available_energy -= amount
            energy_pool.reserved_energy += amount
            
            await self.db.commit()
            
            logger.info(f"Allocated {amount} energy to partner {partner_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to allocate energy to partner {partner_id}: {e}")
            raise
    
    async def get_partner_energy_usage(self, partner_id: str, days: int = 30) -> dict:
        """파트너의 에너지 사용량 조회"""
        try:
            # 실제 구현에서는 energy_usage_history 테이블에서 조회
            # 임시 데이터 반환
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # 일별 사용량 (임시 데이터)
            daily_usage = []
            for i in range(days):
                date = start_date + timedelta(days=i)
                usage = 100 + (i % 7) * 50  # 임시 패턴
                daily_usage.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "energy_used": usage,
                    "transaction_count": usage // 10
                })
            
            total_used = sum(day["energy_used"] for day in daily_usage)
            avg_daily = total_used // days if days > 0 else 0
            
            return {
                "partner_id": partner_id,
                "period_days": days,
                "total_energy_used": total_used,
                "average_daily_usage": avg_daily,
                "peak_daily_usage": max(day["energy_used"] for day in daily_usage),
                "daily_breakdown": daily_usage,
                "efficiency_score": 85.5  # 임시 값
            }
            
        except Exception as e:
            logger.error(f"Failed to get partner energy usage for {partner_id}: {e}")
            raise
    
    async def recharge_energy_pool(self, amount: int, admin_id: str) -> bool:
        """에너지 풀 충전 (슈퍼 어드민용)"""
        try:
            result = await self.db.execute(
                select(EnergyPoolModel).order_by(desc(EnergyPoolModel.id)).limit(1)
            )
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool:
                # 새 에너지 풀 생성
                energy_pool = EnergyPoolModel(
                    total_energy=amount,
                    available_energy=amount,
                    reserved_energy=0,
                    daily_consumption=0
                )
                self.db.add(energy_pool)
            else:
                # 기존 풀에 추가
                energy_pool.total_energy += amount
                energy_pool.available_energy += amount
            
            await self.db.commit()
            
            logger.info(f"Energy pool recharged with {amount} units by admin {admin_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to recharge energy pool: {e}")
            raise
    
    async def monitor_energy_alerts(self) -> List[dict]:
        """에너지 관련 알림 모니터링"""
        try:
            alerts = []
            
            # 현재 에너지 상태 확인
            status = await self.get_total_energy_status()
            
            # 임계값 체크
            if status["pool_health"] == "critical":
                alerts.append({
                    "id": "energy_critical",
                    "type": "critical",
                    "title": "에너지 풀 위험",
                    "message": f"사용 가능한 에너지가 {status['available_energy']}로 매우 부족합니다.",
                    "created_at": datetime.utcnow(),
                    "severity": "high"
                })
            elif status["pool_health"] == "warning":
                alerts.append({
                    "id": "energy_warning", 
                    "type": "warning",
                    "title": "에너지 풀 경고",
                    "message": f"사용 가능한 에너지가 {status['available_energy']}로 부족합니다.",
                    "created_at": datetime.utcnow(),
                    "severity": "medium"
                })
            
            # 사용률 체크
            if status["utilization_rate"] > 90:
                alerts.append({
                    "id": "high_utilization",
                    "type": "info",
                    "title": "높은 에너지 사용률",
                    "message": f"현재 에너지 사용률이 {status['utilization_rate']}%입니다.",
                    "created_at": datetime.utcnow(),
                    "severity": "low"
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to monitor energy alerts: {e}")
            return []
    
    async def get_energy_usage_history(
        self, 
        partner_id: Optional[str] = None, 
        days: int = 30
    ) -> List[dict]:
        """에너지 사용 이력 조회"""
        try:
            # 실제 구현에서는 energy_usage_history 테이블에서 조회
            # 임시 데이터 반환
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            history = []
            for i in range(days):
                date = start_date + timedelta(days=i)
                
                # 파트너별 또는 전체 이력
                if partner_id:
                    records = [{
                        "partner_id": partner_id,
                        "energy_amount": 50 + (i % 5) * 20,
                        "transaction_type": "api_call",
                        "created_at": date
                    }]
                else:
                    # 전체 파트너 이력 (임시)
                    records = []
                    for p_id in ["partner_1", "partner_2", "partner_3"]:
                        records.append({
                            "partner_id": p_id,
                            "energy_amount": 30 + (i % 3) * 15,
                            "transaction_type": "api_call",
                            "created_at": date
                        })
                
                history.extend(records)
            
            return sorted(history, key=lambda x: x["created_at"], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to get energy usage history: {e}")
            return []
    
    async def get_energy_analytics(self, days: int = 30) -> dict:
        """에너지 사용 분석 (슈퍼 어드민용)"""
        try:
            # 실제 구현에서는 실제 데이터로 계산
            # 임시 분석 데이터
            
            total_consumed = 45000
            avg_daily = total_consumed // days
            peak_usage = avg_daily * 1.5
            
            # 파트너별 사용량 순위 (임시)
            partner_rankings = [
                {"partner_id": "partner_1", "partner_name": "Partner A", "energy_used": 15000, "percentage": 33.3},
                {"partner_id": "partner_2", "partner_name": "Partner B", "energy_used": 18000, "percentage": 40.0},
                {"partner_id": "partner_3", "partner_name": "Partner C", "energy_used": 12000, "percentage": 26.7}
            ]
            
            # 시간대별 사용 패턴
            hourly_pattern = []
            for hour in range(24):
                # 9-18시가 피크 시간대
                if 9 <= hour <= 18:
                    usage = 1000 + (hour - 9) * 200
                else:
                    usage = 200 + hour * 50
                
                hourly_pattern.append({
                    "hour": hour,
                    "average_usage": usage
                })
            
            return {
                "period_days": days,
                "total_energy_consumed": total_consumed,
                "average_daily_consumption": avg_daily,
                "peak_daily_usage": int(peak_usage),
                "efficiency_trends": {
                    "cost_per_transaction": 5.2,
                    "energy_per_user": 125.5,
                    "optimization_score": 78.5
                },
                "partner_rankings": partner_rankings,
                "hourly_usage_pattern": hourly_pattern,
                "predictions": {
                    "next_week_consumption": avg_daily * 7 * 1.1,
                    "monthly_forecast": avg_daily * 30 * 1.05,
                    "recharge_recommendation": 100000
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get energy analytics: {e}")
            raise