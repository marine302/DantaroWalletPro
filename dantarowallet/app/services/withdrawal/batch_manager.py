"""
일괄 출금 스케줄 관리 모듈
출금 배치 생성, 조회, 실행을 담당합니다.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models.withdrawal import Withdrawal, WithdrawalStatus
from app.models.withdrawal import WithdrawalBatch
from app.core.exceptions import ValidationError, NotFoundError
from app.core.logger import get_logger
from .utils import safe_str, safe_int

logger = get_logger(__name__)


class BatchManager:
    """출금 배치 관리자"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_withdrawal_batch(
        self,
        partner_id: str,
        withdrawal_ids: List[int],
        scheduled_time: Optional[datetime] = None
    ) -> WithdrawalBatch:
        """출금 배치를 생성합니다."""
        try:
            # 출금 요청들이 모두 존재하고 대기 상태인지 확인
            withdrawals_result = await self.db.execute(
                select(Withdrawal).where(
                    and_(
                        Withdrawal.id.in_(withdrawal_ids),
                        Withdrawal.partner_id == partner_id,
                        Withdrawal.status == WithdrawalStatus.PENDING
                    )
                )
            )
            withdrawals = list(withdrawals_result.scalars().all())
            
            if len(withdrawals) != len(withdrawal_ids):
                found_ids = {safe_int(w.id) for w in withdrawals}
                missing_ids = set(withdrawal_ids) - found_ids
                raise ValidationError(f"유효하지 않은 출금 요청들: {missing_ids}")
            
            # 총 금액 계산
            total_amount = sum(w.amount for w in withdrawals)
            
            # 배치 생성
            batch_id = str(uuid.uuid4())
            batch = WithdrawalBatch(
                id=batch_id,
                partner_id=partner_id,
                withdrawal_count=len(withdrawals),
                total_amount=total_amount,
                status="pending",
                scheduled_time=scheduled_time or datetime.utcnow()
            )
            
            self.db.add(batch)
            
            # 출금 요청들에 배치 ID 할당 (SQLAlchemy update 사용)
            from sqlalchemy import update
            await self.db.execute(
                update(Withdrawal)
                .where(Withdrawal.id.in_(withdrawal_ids))
                .values(
                    batch_id=batch_id,
                    status=WithdrawalStatus.REVIEWING
                )
            )
            
            await self.db.commit()
            await self.db.refresh(batch)
            
            logger.info(f"출금 배치 생성: {batch_id} (파트너: {partner_id}, 개수: {len(withdrawals)})")
            return batch
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"출금 배치 생성 실패: {str(e)}")
            raise
    
    async def get_pending_batches(
        self,
        partner_id: str,
        limit: int = 10
    ) -> List[WithdrawalBatch]:
        """대기 중인 배치들을 조회합니다."""
        result = await self.db.execute(
            select(WithdrawalBatch)
            .where(
                and_(
                    WithdrawalBatch.partner_id == partner_id,
                    WithdrawalBatch.status == "pending"
                )
            )
            .order_by(WithdrawalBatch.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def execute_batch_with_tronlink(
        self,
        batch_id: str,
        partner_id: str
    ) -> Dict[str, Any]:
        """TronLink를 사용하여 배치를 실행합니다."""
        try:
            # 배치 조회
            batch_result = await self.db.execute(
                select(WithdrawalBatch).where(
                    and_(
                        WithdrawalBatch.id == batch_id,
                        WithdrawalBatch.partner_id == partner_id
                    )
                )
            )
            batch = batch_result.scalar_one_or_none()
            
            if not batch:
                raise NotFoundError(f"배치를 찾을 수 없습니다: {batch_id}")
            
            # 배치 상태 업데이트 (SQLAlchemy update 사용)
            from sqlalchemy import update
            await self.db.execute(
                update(WithdrawalBatch)
                .where(WithdrawalBatch.id == batch_id)
                .values(
                    status="processing",
                    started_at=datetime.utcnow()
                )
            )
            
            await self.db.commit()
            
            # 새로 조회해서 업데이트된 값 확인
            updated_batch_result = await self.db.execute(
                select(WithdrawalBatch).where(WithdrawalBatch.id == batch_id)
            )
            updated_batch = updated_batch_result.scalar_one()
            
            # 여기서 실제 TronLink 자동 서명 로직 구현
            # 임시로 성공 응답 반환
            
            started_at_str = safe_str(updated_batch.started_at)
            
            return {
                "batch_id": batch_id,
                "status": "processing",
                "started_at": started_at_str if started_at_str else None,
                "message": "배치 실행이 시작되었습니다"
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"배치 실행 실패: {str(e)}")
            raise
