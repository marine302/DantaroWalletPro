"""
출금 배치 처리 서비스 - 문서 #41 기반
"""

from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.withdrawal_queue import WithdrawalQueue, WithdrawalStatus
from app.models.withdrawal_batch import WithdrawalBatch, BatchStatus
from app.models.partner import Partner
from app.services.withdrawal.queue_manager import WithdrawalQueueManager
from app.services.energy.allocation_service import EnergyAllocationService
from app.core.logging import get_logger

logger = get_logger(__name__)


class WithdrawalBatchProcessor:
    """출금 배치 처리기"""

    def __init__(self, db: Session):
        self.db = db
        self.queue_manager = WithdrawalQueueManager(db)
        self.energy_service = EnergyAllocationService(db)

    async def create_batch(
        self,
        partner_id: int,
        withdrawal_ids: List[int],
        batch_type: str = "standard"
    ) -> WithdrawalBatch:
        """출금 배치 생성"""
        try:
            # 출금 요청들 조회
            withdrawals = self.db.query(WithdrawalQueue).filter(
                WithdrawalQueue.id.in_(withdrawal_ids),
                WithdrawalQueue.partner_id == partner_id,
                WithdrawalQueue.status == WithdrawalStatus.QUEUED
            ).all()

            if not withdrawals:
                raise ValueError("처리 가능한 출금 요청이 없습니다")

            # 배치 정보 계산
            total_amount = sum(w.amount_usdt for w in withdrawals)  # type: ignore
            total_energy = sum(w.energy_required for w in withdrawals)  # type: ignore

            # 배치 생성
            batch = WithdrawalBatch(
                batch_id=self._generate_batch_id(),
                partner_id=partner_id,
                total_withdrawals=len(withdrawals),
                total_amount_usdt=total_amount,
                total_energy_required=total_energy,
                status=BatchStatus.CREATED
            )

            # 비용 계산
            batch.energy_cost_trx = await self._calculate_energy_cost(total_energy)  # type: ignore
            batch.saas_fee_trx = Decimal("5.0")  # 기본 SaaS 수수료  # type: ignore
            batch.total_cost_trx = batch.energy_cost_trx + batch.saas_fee_trx  # type: ignore

            self.db.add(batch)
            self.db.commit()
            self.db.refresh(batch)

            # 출금들을 배치에 할당
            for withdrawal in withdrawals:
                self.db.query(WithdrawalQueue).filter(
                    WithdrawalQueue.id == withdrawal.id
                ).update({
                    'batch_id': batch.batch_id,
                    'status': WithdrawalStatus.IN_BATCH
                })

            self.db.commit()

            logger.info(f"출금 배치 생성: {batch.batch_id} ({len(withdrawals)}건)")
            return batch

        except Exception as e:
            logger.error(f"출금 배치 생성 실패: {e}")
            self.db.rollback()
            raise

    async def process_batch(self, batch_id: str) -> Dict:
        """배치 처리 실행"""
        try:
            batch = self.db.query(WithdrawalBatch).filter(
                WithdrawalBatch.batch_id == batch_id
            ).first()

            if not batch:
                raise ValueError("배치를 찾을 수 없습니다")

            if batch.status != BatchStatus.CREATED:
                raise ValueError(f"처리할 수 없는 배치 상태: {batch.status}")

            # 배치 처리 시작
            self.db.query(WithdrawalBatch).filter(
                WithdrawalBatch.batch_id == batch_id
            ).update({
                'status': BatchStatus.PROCESSING,
                'processing_started_at': datetime.utcnow()
            })

            self.db.commit()

            # 배치 내 출금들 조회
            withdrawals = self.db.query(WithdrawalQueue).filter(
                WithdrawalQueue.batch_id == batch_id,
                WithdrawalQueue.status == WithdrawalStatus.IN_BATCH
            ).all()

            results = {
                "batch_id": batch_id,
                "total_withdrawals": len(withdrawals),
                "processed": 0,
                "failed": 0,
                "successes": [],
                "failures": []
            }

            # 각 출금 처리
            for withdrawal in withdrawals:
                try:
                    # 에너지 할당
                    energy_result = await self.energy_service.allocate_energy_for_withdrawal(
                        partner_id=withdrawal.partner_id,  # type: ignore
                        withdrawal_request_id=withdrawal.id,  # type: ignore
                        target_address=withdrawal.to_address,  # type: ignore
                        energy_amount=withdrawal.energy_required  # type: ignore
                    )

                    if energy_result.get("success"):
                        # 출금 처리 성공
                        self.db.query(WithdrawalQueue).filter(
                            WithdrawalQueue.id == withdrawal.id
                        ).update({
                            'status': WithdrawalStatus.PROCESSING,
                            'processing_started_at': datetime.utcnow()
                        })

                        results["processed"] += 1
                        results["successes"].append({
                            "withdrawal_id": withdrawal.withdrawal_id,  # type: ignore
                            "amount": float(withdrawal.amount_usdt),  # type: ignore
                            "energy_allocated": energy_result.get("energy_amount")
                        })

                        logger.info(f"출금 처리 성공: {withdrawal.withdrawal_id}")

                    else:
                        # 출금 처리 실패
                        self.db.query(WithdrawalQueue).filter(
                            WithdrawalQueue.id == withdrawal.id
                        ).update({
                            'status': WithdrawalStatus.FAILED,
                            'failed_at': datetime.utcnow(),
                            'failure_reason': energy_result.get("message", "에너지 할당 실패")
                        })

                        results["failed"] += 1
                        results["failures"].append({
                            "withdrawal_id": withdrawal.withdrawal_id,  # type: ignore
                            "amount": float(withdrawal.amount_usdt),  # type: ignore
                            "error": energy_result.get("message")
                        })

                        logger.warning(f"출금 처리 실패: {withdrawal.withdrawal_id} - {energy_result.get('message')}")

                except Exception as e:
                    logger.error(f"출금 처리 오류: {withdrawal.withdrawal_id} - {e}")
                    results["failed"] += 1
                    results["failures"].append({
                        "withdrawal_id": withdrawal.withdrawal_id,  # type: ignore
                        "error": str(e)
                    })

            # 배치 상태 업데이트
            final_status = BatchStatus.COMPLETED
            if results["failed"] > 0 and results["processed"] == 0:
                final_status = BatchStatus.FAILED
            elif results["failed"] > 0:
                final_status = BatchStatus.PARTIAL

            self.db.query(WithdrawalBatch).filter(
                WithdrawalBatch.batch_id == batch_id
            ).update({
                'status': final_status,
                'processed_count': results["processed"],
                'failed_count': results["failed"],
                'completed_at': datetime.utcnow()
            })

            self.db.commit()

            logger.info(f"배치 처리 완료: {batch_id} - 성공: {results['processed']}, 실패: {results['failed']}")
            return results

        except Exception as e:
            logger.error(f"배치 처리 실패: {e}")
            self.db.rollback()
            raise

    async def get_batch_status(self, batch_id: str) -> Optional[Dict]:
        """배치 상태 조회"""
        try:
            batch = self.db.query(WithdrawalBatch).filter(
                WithdrawalBatch.batch_id == batch_id
            ).first()

            if not batch:
                return None

            # 배치 내 출금 상태 집계
            withdrawal_stats = self.db.query(
                WithdrawalQueue.status,
                func.count(WithdrawalQueue.id).label('count')
            ).filter(
                WithdrawalQueue.batch_id == batch_id
            ).group_by(WithdrawalQueue.status).all()

            status_counts = {stat.status.value: stat.count for stat in withdrawal_stats}

            return {
                "batch_id": batch.batch_id,
                "status": batch.status.value,  # type: ignore
                "total_withdrawals": batch.total_withdrawals,
                "total_amount_usdt": float(batch.total_amount_usdt),  # type: ignore
                "total_energy_required": batch.total_energy_required,
                "processed_count": batch.processed_count,
                "failed_count": batch.failed_count,
                "created_at": batch.created_at.isoformat(),  # type: ignore
                "processing_started_at": batch.processing_started_at.isoformat() if batch.processing_started_at else None,  # type: ignore
                "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,  # type: ignore
                "withdrawal_status_counts": status_counts
            }

        except Exception as e:
            logger.error(f"배치 상태 조회 실패: {e}")
            return None

    async def _calculate_energy_cost(self, total_energy: int) -> Decimal:
        """에너지 비용 계산"""
        # 에너지당 기본 비용 (TRX)
        base_cost_per_energy = Decimal("0.0001")
        return Decimal(str(total_energy)) * base_cost_per_energy

    def _generate_batch_id(self) -> str:
        """배치 ID 생성"""
        import uuid
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        return f"BATCH{timestamp}{uuid.uuid4().hex[:8].upper()}"

    async def get_active_batches(self, partner_id: Optional[int] = None) -> List[Dict]:
        """활성 배치 목록 조회"""
        try:
            query = self.db.query(WithdrawalBatch).filter(
                WithdrawalBatch.status.in_([
                    BatchStatus.CREATED,
                    BatchStatus.PROCESSING
                ])
            )

            if partner_id:
                query = query.filter(WithdrawalBatch.partner_id == partner_id)

            batches = query.order_by(WithdrawalBatch.created_at.desc()).all()

            results = []
            for batch in batches:
                batch_info = await self.get_batch_status(batch.batch_id)
                if batch_info:
                    results.append(batch_info)

            return results

        except Exception as e:
            logger.error(f"활성 배치 조회 실패: {e}")
            return []
