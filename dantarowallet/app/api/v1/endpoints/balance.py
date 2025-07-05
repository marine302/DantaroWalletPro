"""
잔고 관련 API 엔드포인트.
잔고 조회, 내부 이체, 트랜잭션 내역 조회, 잔고 조정 등의 기능을 제공합니다.
"""
import logging
from datetime import datetime
from typing import List, Optional

from app.api import deps
from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.models.transaction import Transaction, TransactionStatus, TransactionType
from app.models.user import User
from app.schemas.balance import (
    BalanceAdjustmentRequest,
    BalanceResponse,
    BalanceSummaryResponse,
    TransactionResponse,
    TransferRequest,
    TransferResponse,
)
from app.services.balance_service import BalanceService
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=BalanceResponse)
async def get_balance(
    asset: str = Query("USDT", description="Asset type"),
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """현재 사용자의 잔고 조회"""
    service = BalanceService(db)
    balance = await service.get_or_create_balance(current_user.id, asset)
    return balance


@router.get("/summary", response_model=BalanceSummaryResponse)
async def get_balance_summary(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """잔고 요약 정보 조회"""
    service = BalanceService(db)
    summary = await service.get_balance_summary(current_user.id)
    return summary


@router.post("/transfer", response_model=TransferResponse)
async def internal_transfer(
    transfer_data: TransferRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """내부 이체"""
    # 수신자 찾기
    result = await db.execute(
        select(User).filter(User.email == transfer_data.receiver_email)
    )
    receiver = result.scalar_one_or_none()

    if not receiver:
        raise NotFoundError("Receiver not found")

    if receiver.id == current_user.id:
        raise ValidationError("Cannot transfer to yourself")

    if not receiver.is_active:
        raise ValidationError("Receiver account is not active")

    # 이체 처리
    service = BalanceService(db)
    result = await service.internal_transfer(
        sender_id=current_user.id,
        receiver_id=receiver.id,
        amount=transfer_data.amount,
        description=transfer_data.description,
    )

    await db.commit()

    return TransferResponse(
        transaction_id=result["transaction_id"],
        reference_id=result["reference_id"],
        amount=transfer_data.amount,
        receiver_email=receiver.email,
        sender_balance=result["sender_balance"],
        timestamp=datetime.utcnow(),
    )


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tx_type: Optional[TransactionType] = None,
    status: Optional[TransactionStatus] = None,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """트랜잭션 내역 조회"""
    service = BalanceService(db)
    transactions = await service.get_transaction_history(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        tx_type=tx_type,
        status=status,
    )
    return transactions


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction_detail(
    transaction_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """특정 트랜잭션 상세 조회"""
    result = await db.execute(
        select(Transaction).filter(
            Transaction.id == transaction_id, Transaction.user_id == current_user.id
        )
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise NotFoundError("Transaction not found")

    return transaction


# 관리자 전용 엔드포인트
@router.post(
    "/admin/adjust",
    response_model=BalanceResponse,
    dependencies=[Depends(deps.get_current_admin_user)],
)
async def adjust_balance(
    adjustment: BalanceAdjustmentRequest,
    admin_user: User = Depends(deps.get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """관리자 잔고 조정 (입금 시뮬레이션 등)"""
    service = BalanceService(db)
    balance = await service.adjust_balance(
        user_id=adjustment.user_id,
        amount=adjustment.amount,
        adjustment_type=adjustment.adjustment_type,
        description=adjustment.description,
        admin_id=admin_user.id,
    )

    await db.commit()

    logger.info(
        f"Admin balance adjustment: admin={admin_user.email}, "
        f"user={adjustment.user_id}, amount={adjustment.amount}"
    )

    return balance
