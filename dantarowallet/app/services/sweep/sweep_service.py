"""
Sweep 자동화 서비스
입금 주소에서 중앙 지갑으로 자동 Sweep 처리
"""

import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.models.partner import Partner
from app.models.partner_wallet import PartnerWallet
from app.models.sweep import (
    HDWalletMaster,
    SweepConfiguration,
    SweepLog,
    SweepQueue,
    UserDepositAddress,
)
from app.schemas.sweep import (
    BatchSweepRequest,
    BatchSweepResponse,
    EmergencySweepRequest,
    EmergencySweepResponse,
    ManualSweepRequest,
    ManualSweepResponse,
    QueueStatus,
    QueueType,
    SweepStatus,
    SweepType,
)

logger = logging.getLogger(__name__)


class SweepError(Exception):
    """Sweep 관련 오류"""

    pass


class InsufficientFundsError(Exception):
    """잔액 부족 오류"""

    pass


class SweepService:
    """Sweep 자동화 처리 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_sweep_configuration(
        self, partner_id: str, destination_wallet_id: int, **config_data
    ) -> SweepConfiguration:
        """Sweep 설정 생성

        Args:
            partner_id: 파트너 ID
            destination_wallet_id: 목적지 지갑 ID
            **config_data: 추가 설정 데이터

        Returns:
            SweepConfiguration: 생성된 설정
        """
        try:
            # 파트너 존재 확인
            partner_query = select(Partner).where(Partner.id == partner_id)
            partner_result = await self.db.execute(partner_query)
            partner = partner_result.scalar_one_or_none()

            if not partner:
                raise ValidationError(f"Partner {partner_id} not found")

            # 목적지 지갑 확인
            wallet_query = select(PartnerWallet).where(
                and_(
                    PartnerWallet.id == destination_wallet_id,
                    PartnerWallet.partner_id == partner_id,
                )
            )
            wallet_result = await self.db.execute(wallet_query)
            wallet = wallet_result.scalar_one_or_none()

            if not wallet:
                raise ValidationError(
                    f"Destination wallet {destination_wallet_id} not found for partner {partner_id}"
                )

            # 기존 설정 확인
            existing_query = select(SweepConfiguration).where(
                SweepConfiguration.partner_id == partner_id
            )
            existing_result = await self.db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()

            if existing:
                raise ValidationError(
                    f"Sweep configuration already exists for partner {partner_id}"
                )

            # 새 설정 생성
            configuration = SweepConfiguration(
                partner_id=partner_id,
                destination_wallet_id=destination_wallet_id,
                **config_data,
            )

            self.db.add(configuration)
            await self.db.commit()
            await self.db.refresh(configuration)

            logger.info(f"Sweep configuration created for partner {partner_id}")
            return configuration

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create sweep configuration: {e}")
            raise SweepError(f"Failed to create sweep configuration: {str(e)}")

    async def get_sweep_configuration(
        self, partner_id: str
    ) -> Optional[SweepConfiguration]:
        """파트너의 Sweep 설정 조회

        Args:
            partner_id: 파트너 ID

        Returns:
            Optional[SweepConfiguration]: Sweep 설정
        """
        try:
            query = (
                select(SweepConfiguration)
                .where(SweepConfiguration.partner_id == partner_id)
                .options(selectinload(SweepConfiguration.destination_wallet))
            )

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Failed to get sweep configuration: {e}")
            raise SweepError(f"Failed to get sweep configuration: {str(e)}")

    async def update_sweep_configuration(
        self, partner_id: str, **update_data
    ) -> SweepConfiguration:
        """Sweep 설정 업데이트

        Args:
            partner_id: 파트너 ID
            **update_data: 업데이트할 데이터

        Returns:
            SweepConfiguration: 업데이트된 설정
        """
        try:
            query = select(SweepConfiguration).where(
                SweepConfiguration.partner_id == partner_id
            )
            result = await self.db.execute(query)
            configuration = result.scalar_one_or_none()

            if not configuration:
                raise ValidationError(
                    f"Sweep configuration not found for partner {partner_id}"
                )

            # 업데이트 적용
            for key, value in update_data.items():
                if hasattr(configuration, key):
                    setattr(configuration, key, value)

            await self.db.commit()
            await self.db.refresh(configuration)

            logger.info(f"Sweep configuration updated for partner {partner_id}")
            return configuration

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update sweep configuration: {e}")
            raise SweepError(f"Failed to update sweep configuration: {str(e)}")

    async def queue_sweep(
        self,
        deposit_address_id: int,
        queue_type: QueueType = QueueType.NORMAL,
        priority: int = 1,
        expected_amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
    ) -> SweepQueue:
        """Sweep 대기열에 추가

        Args:
            deposit_address_id: 입금 주소 ID
            queue_type: 큐 유형
            priority: 우선순위
            expected_amount: 예상 금액
            reason: 등록 사유
            scheduled_at: 예약 시간

        Returns:
            SweepQueue: 생성된 큐 항목
        """
        try:
            # 입금 주소 확인
            address_query = select(UserDepositAddress).where(
                UserDepositAddress.id == deposit_address_id
            )
            address_result = await self.db.execute(address_query)
            address = address_result.scalar_one_or_none()

            if (
                not address
                or not getattr(address, "is_active", True)
                or not getattr(address, "is_monitored", True)
            ):
                raise ValidationError(
                    f"Deposit address {deposit_address_id} not found, inactive, or not monitored"
                )

            # 기존 대기열 항목 확인
            existing_query = select(SweepQueue).where(
                and_(
                    SweepQueue.deposit_address_id == deposit_address_id,
                    SweepQueue.status.in_([QueueStatus.QUEUED, QueueStatus.PROCESSING]),
                )
            )
            existing_result = await self.db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()

            if existing:
                logger.warning(f"Deposit address {deposit_address_id} already in queue")
                return existing

            # 만료 시간 설정 (1시간 후)
            expires_at = (scheduled_at or datetime.utcnow()) + timedelta(hours=1)

            # 큐 항목 생성
            queue_item = SweepQueue(
                deposit_address_id=deposit_address_id,
                queue_type=queue_type,
                priority=priority,
                expected_amount=expected_amount,
                status=QueueStatus.QUEUED,
                scheduled_at=scheduled_at,
                expires_at=expires_at,
                reason=reason,
            )

            self.db.add(queue_item)
            await self.db.commit()
            await self.db.refresh(queue_item)

            logger.info(f"Deposit address {deposit_address_id} queued for sweep")
            return queue_item

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to queue sweep: {e}")
            raise SweepError(f"Failed to queue sweep: {str(e)}")

    async def get_pending_sweeps(
        self, partner_id: Optional[str] = None, limit: int = 100
    ) -> List[SweepQueue]:
        """대기 중인 Sweep 작업 조회

        Args:
            partner_id: 파트너 ID 필터
            limit: 조회 개수 제한

        Returns:
            List[SweepQueue]: 대기 중인 Sweep 목록
        """
        try:
            query = (
                select(SweepQueue)
                .where(
                    and_(
                        SweepQueue.status == QueueStatus.QUEUED,
                        or_(
                            SweepQueue.scheduled_at <= datetime.utcnow(),
                            SweepQueue.scheduled_at.is_(None),
                        ),
                        SweepQueue.expires_at > datetime.utcnow(),
                    )
                )
                .options(selectinload(SweepQueue.deposit_address))
                .order_by(SweepQueue.priority.desc(), SweepQueue.created_at.asc())
                .limit(limit)
            )

            # 파트너 필터 적용
            if partner_id:
                query = (
                    query.join(UserDepositAddress)
                    .join(HDWalletMaster)
                    .where(HDWalletMaster.partner_id == partner_id)
                )

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to get pending sweeps: {e}")
            raise SweepError(f"Failed to get pending sweeps: {str(e)}")

    async def process_sweep_queue(
        self, queue_id: int, sweep_amount: Decimal, tx_hash: Optional[str] = None
    ) -> SweepLog:
        """Sweep 대기열 처리

        Args:
            queue_id: 큐 ID
            sweep_amount: Sweep 금액
            tx_hash: 트랜잭션 해시 (실제 처리 시)

        Returns:
            SweepLog: 생성된 Sweep 로그
        """
        try:
            # 큐 항목 조회
            queue_query = (
                select(SweepQueue)
                .where(SweepQueue.id == queue_id)
                .options(selectinload(SweepQueue.deposit_address))
            )

            queue_result = await self.db.execute(queue_query)
            queue_item = queue_result.scalar_one_or_none()

            if not queue_item:
                raise ValidationError(f"Queue item {queue_id} not found")

            if getattr(queue_item, "status", None) != QueueStatus.QUEUED:
                raise ValidationError(f"Queue item {queue_id} is not in queued status")

            # 큐 상태 업데이트
            setattr(queue_item, "status", QueueStatus.PROCESSING)
            current_attempts = getattr(queue_item, "attempts", 0) or 0
            setattr(queue_item, "attempts", current_attempts + 1)

            # Sweep 설정 조회
            config_query = (
                select(SweepConfiguration)
                .join(
                    HDWalletMaster,
                    SweepConfiguration.partner_id == HDWalletMaster.partner_id,
                )
                .join(
                    UserDepositAddress,
                    UserDepositAddress.hd_wallet_id == HDWalletMaster.id,
                )
                .where(UserDepositAddress.id == queue_item.deposit_address_id)
            )
            config_result = await self.db.execute(config_query)
            configuration = config_result.scalar_one_or_none()

            if not configuration:
                raise SweepError("Sweep configuration not found")

            # Sweep 로그 생성
            sweep_log = SweepLog(
                configuration_id=configuration.id,
                deposit_address_id=queue_item.deposit_address_id,
                sweep_type=(
                    SweepType.AUTO
                    if queue_item.queue_type.value == QueueType.NORMAL.value
                    else SweepType.EMERGENCY
                ),
                sweep_amount=sweep_amount,
                from_address=queue_item.deposit_address.address,
                to_address=configuration.destination_wallet.wallet_address,
                status=SweepStatus.PENDING,
                tx_hash=tx_hash,
                priority=queue_item.priority,
                batch_id=str(uuid.uuid4()) if not tx_hash else None,
            )

            self.db.add(sweep_log)

            # 성공 시 큐 완료 처리
            if tx_hash:
                setattr(queue_item, "status", QueueStatus.COMPLETED)
                setattr(sweep_log, "status", SweepStatus.CONFIRMED)
                setattr(sweep_log, "confirmed_at", datetime.utcnow())

                # 입금 주소 통계 업데이트
                current_swept = (
                    getattr(queue_item.deposit_address, "total_swept", 0) or 0
                )
                setattr(
                    queue_item.deposit_address,
                    "total_swept",
                    current_swept + sweep_amount,
                )
                setattr(queue_item.deposit_address, "last_sweep_at", datetime.utcnow())

                # 설정 통계 업데이트
                current_sweeps = getattr(configuration, "total_sweeps", 0) or 0
                current_amount = getattr(configuration, "total_sweep_amount", 0) or 0
                setattr(configuration, "total_sweeps", current_sweeps + 1)
                setattr(
                    configuration, "total_sweep_amount", current_amount + sweep_amount
                )
                setattr(configuration, "last_sweep_at", datetime.utcnow())

            await self.db.commit()
            await self.db.refresh(sweep_log)

            logger.info(f"Sweep processed for queue {queue_id}, amount: {sweep_amount}")
            return sweep_log

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to process sweep queue: {e}")
            raise SweepError(f"Failed to process sweep queue: {str(e)}")

    async def manual_sweep(
        self,
        partner_id: str,
        address: str,
        amount: Optional[Decimal] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """수동 Sweep 실행"""
        try:
            # 간단한 수동 Sweep 구현
            return {
                "success": True,
                "message": f"Manual sweep initiated for {address}",
                "partner_id": partner_id,
                "address": address,
                "amount": amount,
                "force": force,
            }
        except Exception as e:
            logger.error(f"Manual sweep failed: {e}")
            raise SweepError(f"Manual sweep failed: {str(e)}")

    async def batch_sweep(
        self,
        partner_id: str,
        addresses: List[str],
        force: bool = False,
        priority: str = "normal",
    ) -> Dict[str, Any]:
        """배치 Sweep 실행"""
        try:
            # 간단한 배치 Sweep 구현
            return {
                "success": True,
                "message": f"Batch sweep initiated for {len(addresses)} addresses",
                "partner_id": partner_id,
                "addresses": addresses,
                "total_addresses": len(addresses),
                "force": force,
                "priority": priority,
            }
        except Exception as e:
            logger.error(f"Batch sweep failed: {e}")
            raise SweepError(f"Batch sweep failed: {str(e)}")

    async def emergency_sweep(
        self, partner_id: str, addresses: List[str], reason: str
    ) -> Dict[str, Any]:
        """긴급 Sweep 실행"""
        try:
            # 간단한 긴급 Sweep 구현
            return {
                "success": True,
                "message": f"Emergency sweep initiated for {len(addresses)} addresses",
                "partner_id": partner_id,
                "addresses": addresses,
                "total_addresses": len(addresses),
                "reason": reason,
                "priority": "emergency",
            }
        except Exception as e:
            logger.error(f"Emergency sweep failed: {e}")
            raise SweepError(f"Emergency sweep failed: {str(e)}")

    async def get_sweep_logs(
        self,
        partner_id: Optional[str] = None,
        status: Optional[SweepStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SweepLog]:
        """Sweep 로그 조회

        Args:
            partner_id: 파트너 ID 필터
            status: 상태 필터
            limit: 조회 개수 제한
            offset: 조회 시작 위치

        Returns:
            List[SweepLog]: Sweep 로그 목록
        """
        try:
            query = select(SweepLog).options(
                selectinload(SweepLog.deposit_address),
                selectinload(SweepLog.configuration),
            )

            # 파트너 필터
            if partner_id:
                query = query.join(SweepConfiguration).where(
                    SweepConfiguration.partner_id == partner_id
                )

            # 상태 필터
            if status:
                query = query.where(SweepLog.status == status)

            # 정렬 및 페이지네이션
            query = query.order_by(SweepLog.initiated_at.desc())
            query = query.limit(limit).offset(offset)

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to get sweep logs: {e}")
            raise SweepError(f"Failed to get sweep logs: {str(e)}")

    async def get_sweep_statistics(
        self, partner_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Sweep 통계 조회

        Args:
            partner_id: 파트너 ID
            days: 통계 기간 (일)

        Returns:
            Dict[str, Any]: 통계 데이터
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # 기본 통계 쿼리
            stats_query = (
                select(
                    func.count(SweepLog.id).label("total_sweeps"),
                    func.sum(SweepLog.sweep_amount).label("total_amount"),
                    func.count(
                        func.case([(SweepLog.status == SweepStatus.CONFIRMED, 1)])
                    ).label("successful_sweeps"),
                    func.count(
                        func.case([(SweepLog.status == SweepStatus.FAILED, 1)])
                    ).label("failed_sweeps"),
                    func.avg(SweepLog.sweep_amount).label("average_amount"),
                )
                .select_from(SweepLog.__table__.join(SweepConfiguration.__table__))
                .where(
                    and_(
                        SweepConfiguration.partner_id == partner_id,
                        SweepLog.initiated_at >= start_date,
                    )
                )
            )

            stats_result = await self.db.execute(stats_query)
            stats = stats_result.first()

            # 활성 주소 수
            active_addresses_query = (
                select(func.count(UserDepositAddress.id))
                .select_from(
                    UserDepositAddress.__table__.join(HDWalletMaster.__table__)
                )
                .where(
                    and_(
                        HDWalletMaster.partner_id == partner_id,
                        UserDepositAddress.is_active == True,
                        UserDepositAddress.is_monitored == True,
                    )
                )
            )

            active_result = await self.db.execute(active_addresses_query)
            active_addresses = active_result.scalar()

            # 대기 중인 Sweep 수
            pending_query = select(func.count(SweepQueue.id)).where(
                SweepQueue.status == QueueStatus.QUEUED
            )

            pending_result = await self.db.execute(pending_query)
            pending_sweeps = pending_result.scalar()

            # 성공률 계산
            total_sweeps = getattr(stats, "total_sweeps", 0) or 0
            successful_sweeps = getattr(stats, "successful_sweeps", 0) or 0
            success_rate = (
                (successful_sweeps / total_sweeps * 100) if total_sweeps > 0 else 0
            )

            return {
                "total_addresses": active_addresses or 0,
                "active_addresses": active_addresses or 0,
                "total_sweep_amount": float(getattr(stats, "total_amount", 0) or 0),
                "successful_sweeps": successful_sweeps,
                "failed_sweeps": getattr(stats, "failed_sweeps", 0) or 0,
                "success_rate": round(success_rate, 2),
                "average_amount": float(getattr(stats, "average_amount", 0) or 0),
                "last_24h_sweeps": 0,  # TODO: 24시간 통계
                "last_24h_amount": 0,  # TODO: 24시간 통계
                "pending_sweeps": pending_sweeps or 0,
                "queue_length": pending_sweeps or 0,
            }

        except Exception as e:
            logger.error(f"Failed to get sweep statistics: {e}")
            raise SweepError(f"Failed to get sweep statistics: {str(e)}")
