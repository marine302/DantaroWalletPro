"""에너지 풀 관리 서비스"""
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc, func
from sqlalchemy.orm import selectinload

from app.models.energy import EnergyPool, EnergyTransaction, EnergyQueue, EnergyAlert
from app.models.user import User
from app.schemas.energy import (
    EnergyPoolStatus, EnergyRechargeRequest, EnergyUsageStats,
    EnergyQueueCreate, QueueStatus, CreateEnergyAlert,
    EmergencyWithdrawalCreate, EmergencyWithdrawalResponse
)
from app.core.exceptions import EnergyInsufficientError, ValidationError
from app.core.logger import get_logger

logger = get_logger(__name__)

class EnergyPoolService:
    """에너지 풀 관리 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_energy_status(self) -> EnergyPoolStatus:
        """현재 에너지 풀 상태를 조회합니다."""
        try:
            # 에너지 풀 정보 조회
            result = await self.db.execute(
                select(EnergyPool).order_by(desc(EnergyPool.id)).limit(1)
            )
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool:
                # 기본 에너지 풀 생성
                energy_pool = EnergyPool(
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
                select(EnergyPool).order_by(desc(EnergyPool.id)).limit(1)
            )
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool or energy_pool.available_energy < amount:
                raise EnergyInsufficientError("에너지가 부족합니다.")
            
            # 에너지 소모 처리
            await self.db.execute(
                update(EnergyPool)
                .where(EnergyPool.id == energy_pool.id)
                .values(
                    available_energy=EnergyPool.available_energy - amount,
                    daily_consumption=EnergyPool.daily_consumption + amount,
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
                select(EnergyPool).order_by(desc(EnergyPool.id)).limit(1)
            )
            energy_pool = result.scalar_one_or_none()
            
            if not energy_pool:
                raise ValidationError("에너지 풀이 존재하지 않습니다.")
            
            # 에너지 충전 처리
            await self.db.execute(
                update(EnergyPool)
                .where(EnergyPool.id == energy_pool.id)
                .values(
                    total_energy=EnergyPool.total_energy + request.amount,
                    available_energy=EnergyPool.available_energy + request.amount,
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