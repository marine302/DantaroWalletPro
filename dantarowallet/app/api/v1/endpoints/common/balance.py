"""
잔고 관련 API 엔드포인트.
잔고 조회, 내부 이체, 트랜잭션 내역 조회, 잔고 조정 등의 기능을 제공합니다.
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=BalanceResponse)
async def get_balance(
    asset: str = Query("USDT", description="Asset type"),
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get User's Internal Balance

    Retrieves the user's internal system balance (database-stored balance).
    This is different from on-chain wallet balance - it represents the balance
    managed within the DantaroWallet system for faster transactions.
    """
    service = BalanceService(db)
    # 사용자 ID 가져오기 (타입 체크 우회)
    user_id = getattr(current_user, "id", None)
    if user_id is None:
        raise HTTPException(status_code=400, detail="Invalid user")
    balance = await service.get_or_create_balance(user_id, asset)
    return balance


@router.get("/summary", response_model=BalanceSummaryResponse)
async def get_balance_summary(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get Balance Summary

    Retrieves comprehensive balance summary including all assets,
    pending transactions, and account statistics.
    """
    service = BalanceService(db)
    user_id = getattr(current_user, "id", None)
    if user_id is None:
        raise HTTPException(status_code=400, detail="Invalid user")
    summary = await service.get_balance_summary(user_id)
    return summary


@router.post("/transfer", response_model=TransferResponse)
async def internal_transfer(
    transfer_data: TransferRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Internal Balance Transfer

    Transfers balance between users within the DantaroWallet system.
    This is an internal transfer using system-managed balances,
    not blockchain transactions.
    """
    # 수신자 찾기
    result = await db.execute(
        select(User).filter(User.email == transfer_data.receiver_email)
    )
    receiver = result.scalar_one_or_none()

    if not receiver:
        raise NotFoundError("Receiver not found")

    # 타입 안전 비교
    receiver_id = getattr(receiver, "id", None)
    current_user_id = getattr(current_user, "id", None)
    receiver_is_active = getattr(receiver, "is_active", False)
    receiver_email = getattr(receiver, "email", "")

    if receiver_id == current_user_id:
        raise ValidationError("Cannot transfer to yourself")

    if not receiver_is_active:
        raise ValidationError("Receiver account is not active")

    # 이체 처리
    service = BalanceService(db)
    # 유효성 검사
    if current_user_id is None or receiver_id is None:
        raise HTTPException(status_code=400, detail="Invalid user IDs")

    result = await service.internal_transfer(
        sender_id=current_user_id,
        receiver_email=receiver_email,
        amount=transfer_data.amount,
        asset="USDT",  # 기본 자산
    )

    await db.commit()

    return TransferResponse(
        transaction_id=result["transaction_id"],
        reference_id=result["reference_id"],
        amount=transfer_data.amount,
        receiver_email=receiver_email,
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
    """Get Transaction History

    Retrieves paginated transaction history for the current user
    with optional filtering by transaction type and status.
    """
    service = BalanceService(db)
    user_id = getattr(current_user, "id", None)
    if user_id is None:
        raise HTTPException(status_code=400, detail="Invalid user")
    transactions = await service.get_transaction_history(
        user_id=user_id,
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
    """Get Transaction Details

    Retrieves detailed information for a specific transaction
    belonging to the current user.
    """
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
    """Admin Balance Adjustment

    Allows administrators to adjust user balances for various purposes
    such as deposit simulation, corrections, or manual adjustments.
    Requires admin privileges and logs all adjustments.
    """
    service = BalanceService(db)
    balance = await service.adjust_balance(
        user_id=adjustment.user_id,
        asset="USDT",  # 기본 자산
        amount=adjustment.amount,
        reason=f"Admin adjustment: {adjustment.description} (Type: {adjustment.adjustment_type})",
    )

    await db.commit()

    admin_id = getattr(admin_user, "id", "unknown")
    logger.info(
        f"Admin balance adjustment: admin={getattr(admin_user, 'email', 'unknown')}, "
        f"user={adjustment.user_id}, amount={adjustment.amount}"
    )

    return balance
