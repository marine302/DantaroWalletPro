"""
출금 관련 API 엔드포인트.
출금 요청, 검토, 승인, 완료 등의 API를 제공합니다.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.models.withdrawal import Withdrawal, WithdrawalPriority, WithdrawalStatus
from app.schemas.withdrawal import (
    WithdrawalCompleteRequest,
    WithdrawalListResponse,
    WithdrawalProcessingGuide,
    WithdrawalRequest,
    WithdrawalResponse,
    WithdrawalReviewRequest,
    WithdrawalStats,
)
from app.services.withdrawal_service import WithdrawalService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/request", response_model=WithdrawalResponse)
async def request_withdrawal(
    withdrawal_data: WithdrawalRequest,
    request: Request,
    current_user: User = Depends(deps.get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """출금 요청"""
    service = WithdrawalService(db)

    # IP 주소와 User-Agent 추출
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    withdrawal = await service.create_withdrawal_request(
        user_id=getattr(current_user, "id", 0),
        to_address=withdrawal_data.to_address,
        amount=withdrawal_data.amount,
        asset=withdrawal_data.asset,
        notes=withdrawal_data.notes,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    await db.commit()

    return withdrawal


@router.get("/", response_model=WithdrawalListResponse)
async def get_withdrawals(
    status: Optional[WithdrawalStatus] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """출금 내역 조회"""
    service = WithdrawalService(db)
    withdrawals, total = await service.get_user_withdrawals(
        user_id=getattr(current_user, "id", 0),
        status=status,
        limit=limit,
        offset=offset,
    )

    # 대기 중인 출금 정보
    pending_result = await db.execute(
        select(
            func.count(Withdrawal.id), func.coalesce(func.sum(Withdrawal.amount), 0)
        ).filter(
            and_(
                Withdrawal.user_id == getattr(current_user, "id", 0),
                Withdrawal.status.in_(
                    [
                        WithdrawalStatus.PENDING,
                        WithdrawalStatus.REVIEWING,
                        WithdrawalStatus.APPROVED,
                    ]
                ),
            )
        )
    )
    pending_count, pending_amount = pending_result.one()

    return WithdrawalListResponse(
        items=[WithdrawalResponse.from_orm(w) for w in withdrawals],
        total=total,
        pending_count=pending_count or 0,
        total_pending_amount=Decimal(str(pending_amount or 0)),
    )


@router.get("/{withdrawal_id}", response_model=WithdrawalResponse)
async def get_withdrawal_detail(
    withdrawal_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """출금 상세 조회"""
    result = await db.execute(
        select(Withdrawal).filter(
            and_(
                Withdrawal.id == withdrawal_id,
                Withdrawal.user_id == getattr(current_user, "id", 0),
            )
        )
    )
    withdrawal = result.scalar_one_or_none()

    if not withdrawal:
        raise HTTPException(status_code=404, detail="출금 요청을 찾을 수 없습니다")

    return withdrawal


@router.post("/{withdrawal_id}/cancel", response_model=WithdrawalResponse)
async def cancel_withdrawal(
    withdrawal_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """출금 취소"""
    service = WithdrawalService(db)
    withdrawal = await service.cancel_withdrawal(
        withdrawal_id, getattr(current_user, "id", 0)
    )
    await db.commit()

    return withdrawal


# 관리자 전용 엔드포인트


@router.get("/admin/pending", response_model=List[WithdrawalResponse])
async def get_pending_withdrawals(
    status: Optional[WithdrawalStatus] = None,
    priority: Optional[WithdrawalPriority] = None,
    current_user: User = Depends(deps.get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """대기 중인 출금 목록 (관리자)"""
    service = WithdrawalService(db)
    withdrawals = await service.get_pending_withdrawals(status, priority)
    return withdrawals


@router.post("/admin/{withdrawal_id}/review", response_model=WithdrawalResponse)
async def review_withdrawal(
    withdrawal_id: int,
    review_data: WithdrawalReviewRequest,
    current_user: User = Depends(deps.get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """출금 검토 (관리자)"""
    service = WithdrawalService(db)
    withdrawal = await service.review_withdrawal(
        withdrawal_id=withdrawal_id,
        admin_id=getattr(current_user, "id", 0),
        action=review_data.action,
        admin_notes=review_data.admin_notes,
        rejection_reason=review_data.rejection_reason,
    )
    await db.commit()

    return withdrawal


@router.get(
    "/admin/{withdrawal_id}/processing-guide", response_model=WithdrawalProcessingGuide
)
async def get_processing_guide(
    withdrawal_id: int,
    current_user: User = Depends(deps.get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """출금 처리 가이드 (관리자)"""
    service = WithdrawalService(db)
    guide = await service.get_withdrawal_processing_guide(withdrawal_id)
    return guide


@router.post("/admin/{withdrawal_id}/process")
async def mark_as_processing(
    withdrawal_id: int,
    current_user: User = Depends(deps.get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """처리 시작 표시 (관리자)"""
    service = WithdrawalService(db)
    withdrawal = await service.mark_as_processing(
        withdrawal_id, getattr(current_user, "id", 0)
    )
    await db.commit()

    return {"message": "출금 처리가 시작되었습니다", "withdrawal_id": withdrawal.id}


@router.post("/admin/{withdrawal_id}/complete", response_model=WithdrawalResponse)
async def complete_withdrawal(
    withdrawal_id: int,
    complete_data: WithdrawalCompleteRequest,
    current_user: User = Depends(deps.get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """출금 완료 처리 (관리자)"""
    service = WithdrawalService(db)
    withdrawal = await service.complete_withdrawal(
        withdrawal_id=withdrawal_id,
        tx_hash=complete_data.tx_hash,
        admin_id=getattr(current_user, "id", 0),
        tx_fee=complete_data.tx_fee,
    )
    await db.commit()

    return withdrawal


@router.get("/admin/stats", response_model=WithdrawalStats)
async def get_withdrawal_stats(
    current_user: User = Depends(deps.get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """출금 통계 (관리자)"""
    # 상태별 통계
    status_stats = await db.execute(
        select(
            Withdrawal.status, func.count(Withdrawal.id), func.sum(Withdrawal.amount)
        ).group_by(Withdrawal.status)
    )

    stats_by_status = {}
    for status, count, total in status_stats:
        stats_by_status[status] = {"count": count, "total_amount": str(total or 0)}

    # 오늘 통계
    today = datetime.utcnow().date()
    today_stats = await db.execute(
        select(func.count(Withdrawal.id), func.sum(Withdrawal.amount)).filter(
            Withdrawal.requested_at >= today
        )
    )
    today_count, today_amount = today_stats.one()

    # 우선순위별 대기 통계
    priority_stats = await db.execute(
        select(Withdrawal.priority, func.count(Withdrawal.id))
        .filter(
            Withdrawal.status.in_([WithdrawalStatus.PENDING, WithdrawalStatus.APPROVED])
        )
        .group_by(Withdrawal.priority)
    )

    pending_priority = {}
    for priority, count in priority_stats:
        pending_priority[priority] = count

    return WithdrawalStats(
        by_status=stats_by_status,
        today={"count": today_count or 0, "amount": str(today_amount or 0)},
        pending_priority=pending_priority,
    )
