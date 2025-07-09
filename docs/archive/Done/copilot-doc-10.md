# Copilot 문서 #10: 출금 시스템 (수동 승인)

## 목표
사용자의 USDT 출금 요청을 처리하는 시스템을 구축합니다. 출금 요청, 관리자 승인, 수동 처리 가이드, 상태 추적을 포함합니다. 초기에는 수동 처리로 시작하여 안전성을 확보합니다.

## 전제 조건
- Copilot 문서 #1-9가 완료되어 있어야 합니다.
- 사용자 지갑과 잔고 시스템이 구축되어 있어야 합니다.
- 관리자 계정이 설정되어 있어야 합니다.

## 상세 지시사항

### 1. 출금 모델 (app/models/withdrawal.py)

```python
from sqlalchemy import Column, String, Integer, Numeric, Boolean, ForeignKey, Index, DateTime, Text
from decimal import Decimal
from datetime import datetime
from enum import Enum
from app.models.base import BaseModel

class WithdrawalStatus(str, Enum):
    """출금 상태"""
    PENDING = "pending"              # 대기 중
    REVIEWING = "reviewing"          # 검토 중
    APPROVED = "approved"            # 승인됨
    PROCESSING = "processing"        # 처리 중
    COMPLETED = "completed"          # 완료
    REJECTED = "rejected"            # 거부됨
    FAILED = "failed"               # 실패
    CANCELLED = "cancelled"          # 취소됨

class WithdrawalPriority(str, Enum):
    """출금 우선순위"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class Withdrawal(BaseModel):
    """출금 요청 모델"""
    
    # 사용자 정보
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 출금 정보
    to_address = Column(String(42), nullable=False, index=True)
    amount = Column(Numeric(precision=18, scale=6), nullable=False)
    fee = Column(Numeric(precision=18, scale=6), nullable=False)
    net_amount = Column(Numeric(precision=18, scale=6), nullable=False)  # 실제 받을 금액
    
    # 상태 정보
    status = Column(String(20), nullable=False, default=WithdrawalStatus.PENDING, index=True)
    priority = Column(String(10), nullable=False, default=WithdrawalPriority.NORMAL)
    
    # 처리 정보
    requested_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 관리자 정보
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 트랜잭션 정보
    tx_hash = Column(String(100), nullable=True, unique=True, index=True)
    tx_fee = Column(Numeric(precision=18, scale=6), nullable=True)  # 실제 네트워크 수수료
    
    # 추가 정보
    notes = Column(Text, nullable=True)  # 사용자 메모
    admin_notes = Column(Text, nullable=True)  # 관리자 메모
    rejection_reason = Column(Text, nullable=True)  # 거부 사유
    error_message = Column(Text, nullable=True)  # 에러 메시지
    
    # 보안 정보
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(200), nullable=True)
    
    # 인덱스
    __table_args__ = (
        Index('idx_withdrawal_user_status', 'user_id', 'status'),
        Index('idx_withdrawal_status_priority', 'status', 'priority'),
        Index('idx_withdrawal_requested_at', 'requested_at'),
    )
    
    def __repr__(self):
        return f"<Withdrawal(id={self.id}, amount={self.amount}, status={self.status})>"
    
    @property
    def total_amount(self) -> Decimal:
        """총 차감 금액 (출금액 + 수수료)"""
        return self.amount + self.fee
    
    def can_cancel(self) -> bool:
        """취소 가능한지 확인"""
        return self.status in [WithdrawalStatus.PENDING, WithdrawalStatus.REVIEWING]
    
    def can_approve(self) -> bool:
        """승인 가능한지 확인"""
        return self.status == WithdrawalStatus.REVIEWING
    
    def can_process(self) -> bool:
        """처리 가능한지 확인"""
        return self.status == WithdrawalStatus.APPROVED
```

### 2. 출금 서비스 (app/services/withdrawal_service.py)

```python
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
import logging

from app.core.config import settings
from app.core.exceptions import ValidationError, InsufficientBalanceError, NotFoundError
from app.models.user import User
from app.models.withdrawal import Withdrawal, WithdrawalStatus, WithdrawalPriority
from app.models.balance import Balance
from app.models.transaction import Transaction, TransactionType, TransactionStatus, TransactionDirection
from app.services.balance_service import BalanceService
from app.services.wallet_service import WalletService
from app.services.alert_service import alert_service, AlertLevel

logger = logging.getLogger(__name__)

class WithdrawalService:
    """출금 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.balance_service = BalanceService(db)
        self.wallet_service = WalletService(db)
        
        # 출금 정책
        self.min_withdrawal = Decimal("10.0")  # 최소 출금액
        self.max_withdrawal_per_tx = Decimal("10000.0")  # 1회 최대
        self.max_withdrawal_per_day = Decimal("20000.0")  # 1일 최대
        self.withdrawal_fee = Decimal("1.0")  # 고정 수수료
        
    async def create_withdrawal_request(
        self,
        user_id: int,
        to_address: str,
        amount: Decimal,
        notes: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Withdrawal:
        """출금 요청 생성"""
        
        # 1. 금액 검증
        if amount < self.min_withdrawal:
            raise ValidationError(f"Minimum withdrawal amount is {self.min_withdrawal} USDT")
        
        if amount > self.max_withdrawal_per_tx:
            raise ValidationError(f"Maximum withdrawal amount per transaction is {self.max_withdrawal_per_tx} USDT")
        
        # 2. 주소 검증
        is_valid = await self.wallet_service.validate_withdrawal_address(to_address)
        if not is_valid:
            raise ValidationError("Invalid withdrawal address")
        
        # 3. 일일 한도 체크
        daily_total = await self._get_daily_withdrawal_total(user_id)
        if daily_total + amount > self.max_withdrawal_per_day:
            remaining = self.max_withdrawal_per_day - daily_total
            raise ValidationError(
                f"Daily withdrawal limit exceeded. Remaining: {remaining} USDT"
            )
        
        # 4. 잔고 확인
        balance = await self.balance_service.get_balance(user_id)
        total_amount = amount + self.withdrawal_fee
        
        if not balance.can_withdraw(total_amount):
            raise InsufficientBalanceError(
                required=float(total_amount),
                available=float(balance.available_amount)
            )
        
        # 5. 잔고 잠금
        await self.balance_service.lock_amount(user_id, total_amount)
        
        # 6. 출금 요청 생성
        withdrawal = Withdrawal(
            user_id=user_id,
            to_address=to_address,
            amount=amount,
            fee=self.withdrawal_fee,
            net_amount=amount,  # 수신자가 받을 금액
            status=WithdrawalStatus.PENDING,
            priority=self._determine_priority(amount),
            notes=notes,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(withdrawal)
        await self.db.flush()
        
        # 7. 트랜잭션 기록
        tx = Transaction(
            user_id=user_id,
            type=TransactionType.WITHDRAWAL,
            direction=TransactionDirection.OUT,
            status=TransactionStatus.PENDING,
            asset="USDT",
            amount=amount,
            fee=self.withdrawal_fee,
            reference_id=f"WD-{withdrawal.id}",
            description=f"Withdrawal to {to_address[:8]}...{to_address[-6:]}"
        )
        
        self.db.add(tx)
        await self.db.flush()
        
        logger.info(f"Withdrawal request created: {withdrawal.id} for user {user_id}")
        
        # 8. 알림 전송
        await alert_service.send_alert(
            "New Withdrawal Request",
            f"User ID: {user_id}\n"
            f"Amount: {amount} USDT\n"
            f"To: {to_address}\n"
            f"Priority: {withdrawal.priority}",
            AlertLevel.INFO,
            "new_withdrawal"
        )
        
        return withdrawal
    
    async def _get_daily_withdrawal_total(self, user_id: int) -> Decimal:
        """오늘 출금 총액 조회"""
        today = datetime.utcnow().date()
        result = await self.db.execute(
            select(func.sum(Withdrawal.amount)).filter(
                and_(
                    Withdrawal.user_id == user_id,
                    Withdrawal.requested_at >= today,
                    Withdrawal.status.notin_([
                        WithdrawalStatus.REJECTED,
                        WithdrawalStatus.CANCELLED,
                        WithdrawalStatus.FAILED
                    ])
                )
            )
        )
        total = result.scalar() or Decimal("0")
        return total
    
    def _determine_priority(self, amount: Decimal) -> WithdrawalPriority:
        """금액에 따른 우선순위 결정"""
        if amount >= 5000:
            return WithdrawalPriority.URGENT
        elif amount >= 1000:
            return WithdrawalPriority.HIGH
        elif amount >= 100:
            return WithdrawalPriority.NORMAL
        else:
            return WithdrawalPriority.LOW
    
    async def cancel_withdrawal(self, withdrawal_id: int, user_id: int) -> Withdrawal:
        """출금 취소 (사용자)"""
        result = await self.db.execute(
            select(Withdrawal).filter(
                and_(
                    Withdrawal.id == withdrawal_id,
                    Withdrawal.user_id == user_id
                )
            )
        )
        withdrawal = result.scalar_one_or_none()
        
        if not withdrawal:
            raise NotFoundError("Withdrawal request not found")
        
        if not withdrawal.can_cancel():
            raise ValidationError(
                f"Cannot cancel withdrawal in {withdrawal.status} status"
            )
        
        # 상태 업데이트
        withdrawal.status = WithdrawalStatus.CANCELLED
        
        # 잔고 잠금 해제
        await self.balance_service.unlock_amount(
            user_id,
            withdrawal.total_amount
        )
        
        # 트랜잭션 상태 업데이트
        await self.db.execute(
            select(Transaction).filter(
                Transaction.reference_id == f"WD-{withdrawal.id}"
            ).update({"status": TransactionStatus.CANCELLED})
        )
        
        logger.info(f"Withdrawal {withdrawal_id} cancelled by user {user_id}")
        
        return withdrawal
    
    async def review_withdrawal(
        self,
        withdrawal_id: int,
        admin_id: int,
        action: str,  # "approve" or "reject"
        admin_notes: Optional[str] = None,
        rejection_reason: Optional[str] = None
    ) -> Withdrawal:
        """출금 검토 (관리자)"""
        result = await self.db.execute(
            select(Withdrawal).filter(Withdrawal.id == withdrawal_id)
        )
        withdrawal = result.scalar_one_or_none()
        
        if not withdrawal:
            raise NotFoundError("Withdrawal request not found")
        
        # 상태 변경
        withdrawal.reviewed_at = datetime.utcnow()
        withdrawal.reviewed_by = admin_id
        
        if admin_notes:
            withdrawal.admin_notes = admin_notes
        
        if action == "approve":
            if withdrawal.status != WithdrawalStatus.PENDING:
                raise ValidationError(
                    f"Cannot approve withdrawal in {withdrawal.status} status"
                )
            
            withdrawal.status = WithdrawalStatus.APPROVED
            withdrawal.approved_at = datetime.utcnow()
            withdrawal.approved_by = admin_id
            
            logger.info(
                f"Withdrawal {withdrawal_id} approved by admin {admin_id}"
            )
            
            # 알림
            await alert_service.send_alert(
                "Withdrawal Approved",
                f"ID: {withdrawal_id}\n"
                f"Amount: {withdrawal.amount} USDT\n"
                f"Ready for processing",
                AlertLevel.INFO,
                "withdrawal_approved"
            )
            
        elif action == "reject":
            if not rejection_reason:
                raise ValidationError("Rejection reason is required")
            
            withdrawal.status = WithdrawalStatus.REJECTED
            withdrawal.rejection_reason = rejection_reason
            
            # 잔고 잠금 해제
            await self.balance_service.unlock_amount(
                withdrawal.user_id,
                withdrawal.total_amount
            )
            
            # 트랜잭션 상태 업데이트
            await self.db.execute(
                select(Transaction).filter(
                    Transaction.reference_id == f"WD-{withdrawal.id}"
                ).update({"status": TransactionStatus.FAILED})
            )
            
            logger.info(
                f"Withdrawal {withdrawal_id} rejected by admin {admin_id}: {rejection_reason}"
            )
        
        return withdrawal
    
    async def get_withdrawal_processing_guide(
        self,
        withdrawal_id: int
    ) -> Dict[str, Any]:
        """출금 처리 가이드 생성 (수동 처리용)"""
        result = await self.db.execute(
            select(Withdrawal).filter(Withdrawal.id == withdrawal_id)
        )
        withdrawal = result.scalar_one_or_none()
        
        if not withdrawal:
            raise NotFoundError("Withdrawal request not found")
        
        if not withdrawal.can_process():
            raise ValidationError(
                f"Cannot process withdrawal in {withdrawal.status} status"
            )
        
        # 회사 지갑 정보 (환경변수나 DB에서 가져와야 함)
        # 실제 구현에서는 안전하게 관리되어야 함
        guide = {
            "withdrawal_id": withdrawal.id,
            "status": withdrawal.status,
            "amount": str(withdrawal.amount),
            "fee": str(withdrawal.fee),
            "to_address": withdrawal.to_address,
            "instructions": [
                "1. Open TRON wallet application",
                "2. Select USDT (TRC20) token",
                "3. Click Send/Transfer",
                f"4. Enter recipient address: {withdrawal.to_address}",
                f"5. Enter amount: {withdrawal.amount} USDT",
                "6. Review transaction details carefully",
                "7. Confirm and submit transaction",
                "8. Wait for transaction confirmation",
                "9. Copy transaction hash",
                "10. Update withdrawal status with tx hash"
            ],
            "warnings": [
                "⚠️ Double-check the recipient address",
                "⚠️ Ensure sufficient USDT balance in company wallet",
                "⚠️ Ensure sufficient TRX for gas fees",
                "⚠️ Never share private keys"
            ],
            "checklist": [
                "□ Recipient address verified",
                "□ Amount verified",
                "□ Company wallet has sufficient balance",
                "□ Company wallet has sufficient TRX for fees",
                "□ No suspicious activity detected"
            ]
        }
        
        return guide
    
    async def mark_as_processing(
        self,
        withdrawal_id: int,
        admin_id: int
    ) -> Withdrawal:
        """처리 중으로 표시"""
        result = await self.db.execute(
            select(Withdrawal).filter(Withdrawal.id == withdrawal_id)
        )
        withdrawal = result.scalar_one_or_none()
        
        if not withdrawal:
            raise NotFoundError("Withdrawal request not found")
        
        if withdrawal.status != WithdrawalStatus.APPROVED:
            raise ValidationError("Only approved withdrawals can be processed")
        
        withdrawal.status = WithdrawalStatus.PROCESSING
        withdrawal.processed_at = datetime.utcnow()
        withdrawal.processed_by = admin_id
        
        await self.db.flush()
        
        return withdrawal
    
    async def complete_withdrawal(
        self,
        withdrawal_id: int,
        tx_hash: str,
        admin_id: int,
        tx_fee: Optional[Decimal] = None
    ) -> Withdrawal:
        """출금 완료 처리"""
        result = await self.db.execute(
            select(Withdrawal).filter(Withdrawal.id == withdrawal_id)
        )
        withdrawal = result.scalar_one_or_none()
        
        if not withdrawal:
            raise NotFoundError("Withdrawal request not found")
        
        if withdrawal.status != WithdrawalStatus.PROCESSING:
            raise ValidationError(
                f"Cannot complete withdrawal in {withdrawal.status} status"
            )
        
        # 출금 완료
        withdrawal.status = WithdrawalStatus.COMPLETED
        withdrawal.completed_at = datetime.utcnow()
        withdrawal.tx_hash = tx_hash
        if tx_fee:
            withdrawal.tx_fee = tx_fee
        
        # 잔고 차감 (잠금에서 실제 차감으로)
        balance = await self.balance_service.get_balance(withdrawal.user_id)
        balance.amount -= withdrawal.total_amount
        balance.locked_amount -= withdrawal.total_amount
        
        # 트랜잭션 완료
        await self.db.execute(
            select(Transaction).filter(
                Transaction.reference_id == f"WD-{withdrawal.id}"
            ).update({
                "status": TransactionStatus.COMPLETED,
                "tx_hash": tx_hash
            })
        )
        
        logger.info(
            f"Withdrawal {withdrawal_id} completed with tx {tx_hash}"
        )
        
        # 알림
        await alert_service.send_alert(
            "Withdrawal Completed",
            f"ID: {withdrawal_id}\n"
            f"Amount: {withdrawal.amount} USDT\n"
            f"TX: {tx_hash}",
            AlertLevel.INFO,
            "withdrawal_completed"
        )
        
        return withdrawal
    
    async def get_pending_withdrawals(
        self,
        status: Optional[WithdrawalStatus] = None,
        priority: Optional[WithdrawalPriority] = None
    ) -> List[Withdrawal]:
        """대기 중인 출금 목록 조회"""
        query = select(Withdrawal)
        
        if status:
            query = query.filter(Withdrawal.status == status)
        else:
            # 기본적으로 처리가 필요한 상태들
            query = query.filter(
                Withdrawal.status.in_([
                    WithdrawalStatus.PENDING,
                    WithdrawalStatus.APPROVED,
                    WithdrawalStatus.PROCESSING
                ])
            )
        
        if priority:
            query = query.filter(Withdrawal.priority == priority)
        
        # 우선순위와 요청 시간 순으로 정렬
        query = query.order_by(
            Withdrawal.priority.desc(),
            Withdrawal.requested_at.asc()
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
```

### 3. 출금 스키마 (app/schemas/withdrawal.py)

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from app.models.withdrawal import WithdrawalStatus, WithdrawalPriority

class WithdrawalRequest(BaseModel):
    """출금 요청 스키마"""
    to_address: str = Field(..., min_length=34, max_length=34)
    amount: Decimal = Field(..., gt=0, decimal_places=6)
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('amount')
    def validate_amount(cls, v):
        if v < Decimal("10"):
            raise ValueError("Minimum withdrawal amount is 10 USDT")
        if v > Decimal("10000"):
            raise ValueError("Maximum withdrawal amount is 10,000 USDT")
        return v

class WithdrawalResponse(BaseModel):
    """출금 응답 스키마"""
    id: int
    user_id: int
    to_address: str
    amount: Decimal
    fee: Decimal
    net_amount: Decimal
    total_amount: Decimal
    status: WithdrawalStatus
    priority: WithdrawalPriority
    requested_at: datetime
    reviewed_at: Optional[datetime]
    approved_at: Optional[datetime]
    completed_at: Optional[datetime]
    tx_hash: Optional[str]
    notes: Optional[str]
    rejection_reason: Optional[str]
    
    class Config:
        from_attributes = True

class WithdrawalListResponse(BaseModel):
    """출금 목록 응답"""
    items: List[WithdrawalResponse]
    total: int
    pending_count: int
    total_pending_amount: Decimal

class WithdrawalReviewRequest(BaseModel):
    """출금 검토 요청"""
    action: str = Field(..., pattern="^(approve|reject)$")
    admin_notes: Optional[str] = Field(None, max_length=500)
    rejection_reason: Optional[str] = Field(None, max_length=500)
    
    @validator('rejection_reason')
    def validate_rejection_reason(cls, v, values):
        if values.get('action') == 'reject' and not v:
            raise ValueError("Rejection reason is required when rejecting")
        return v

class WithdrawalCompleteRequest(BaseModel):
    """출금 완료 요청"""
    tx_hash: str = Field(..., min_length=64, max_length=66)
    tx_fee: Optional[Decimal] = Field(None, decimal_places=6)

class WithdrawalProcessingGuide(BaseModel):
    """출금 처리 가이드"""
    withdrawal_id: int
    status: str
    amount: str
    fee: str
    to_address: str
    instructions: List[str]
    warnings: List[str]
    checklist: List[str]
```

### 4. 출금 엔드포인트 (app/api/v1/endpoints/withdrawals.py)

```python
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import logging

from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.models.withdrawal import Withdrawal, WithdrawalStatus, WithdrawalPriority
from app.services.withdrawal_service import WithdrawalService
from app.schemas.withdrawal import (
    WithdrawalRequest, WithdrawalResponse, WithdrawalListResponse,
    WithdrawalReviewRequest, WithdrawalCompleteRequest,
    WithdrawalProcessingGuide
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/request", response_model=WithdrawalResponse)
async def request_withdrawal(
    withdrawal_data: WithdrawalRequest,
    request: Request,
    current_user: User = Depends(deps.get_current_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """출금 요청"""
    service = WithdrawalService(db)
    
    # IP 주소와 User-Agent 추출
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent")
    
    withdrawal = await service.create_withdrawal_request(
        user_id=current_user.id,
        to_address=withdrawal_data.to_address,
        amount=withdrawal_data.amount,
        notes=withdrawal_data.notes,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    await db.commit()
    
    return withdrawal

@router.get("/", response_model=WithdrawalListResponse)
async def get_withdrawals(
    status: Optional[WithdrawalStatus] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """출금 내역 조회"""
    query = select(Withdrawal).filter(Withdrawal.user_id == current_user.id)
    
    if status:
        query = query.filter(Withdrawal.status == status)
    
    # 전체 개수
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()
    
    # 대기 중인 출금 정보
    pending_result = await db.execute(
        select(
            func.count(Withdrawal.id),
            func.coalesce(func.sum(Withdrawal.amount), 0)
        ).filter(
            and_(
                Withdrawal.user_id == current_user.id,
                Withdrawal.status.in_([
                    WithdrawalStatus.PENDING,
                    WithdrawalStatus.REVIEWING,
                    WithdrawalStatus.APPROVED
                ])
            )
        )
    )
    pending_count, pending_amount = pending_result.one()
    
    # 페이지네이션
    query = query.order_by(Withdrawal.requested_at.desc())
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    withdrawals = result.scalars().all()
    
    return WithdrawalListResponse(
        items=withdrawals,
        total=total,
        pending_count=pending_count or 0,
        total_pending_amount=pending_amount or Decimal("0")
    )

@router.get("/{withdrawal_id}", response_model=WithdrawalResponse)
async def get_withdrawal_detail(
    withdrawal_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """출금 상세 조회"""
    result = await db.execute(
        select(Withdrawal).filter(
            and_(
                Withdrawal.id == withdrawal_id,
                Withdrawal.user_id == current_user.id
            )
        )
    )
    withdrawal = result.scalar_one_or_none()
    
    if not withdrawal:
        raise NotFoundError("Withdrawal not found")
    
    return withdrawal

@router.post("/{withdrawal_id}/cancel", response_model=WithdrawalResponse)
async def cancel_withdrawal(
    withdrawal_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """출금 취소"""
    service = WithdrawalService(db)
    withdrawal = await service.cancel_withdrawal(withdrawal_id, current_user.id)
    await db.commit()
    
    return withdrawal

# 관리자 전용 엔드포인트

@router.get("/admin/pending", response_model=List[WithdrawalResponse])
async def get_pending_withdrawals(
    status: Optional[WithdrawalStatus] = None,
    priority: Optional[WithdrawalPriority] = None,
    current_user: User = Depends(deps.get_current_admin_user),
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
):
    """출금 검토 (관리자)"""
    service = WithdrawalService(db)
    withdrawal = await service.review_withdrawal(
        withdrawal_id=withdrawal_id,
        admin_id=current_user.id,
        action=review_data.action,
        admin_notes=review_data.admin_notes,
        rejection_reason=review_data.rejection_reason
    )
    await db.commit()
    
    return withdrawal

@router.get("/admin/{withdrawal_id}/processing-guide", response_model=WithdrawalProcessingGuide)
async def get_processing_guide(
    withdrawal_id: int,
    current_user: User = Depends(deps.get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """출금 처리 가이드 (관리자)"""
    service = WithdrawalService(db)
    guide = await service.get_withdrawal_processing_guide(withdrawal_id)
    return guide

@router.post("/admin/{withdrawal_id}/process")
async def mark_as_processing(
    withdrawal_id: int,
    current_user: User = Depends(deps.get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """처리 시작 표시 (관리자)"""
    service = WithdrawalService(db)
    withdrawal = await service.mark_as_processing(withdrawal_id, current_user.id)
    await db.commit()
    
    return {"message": "Withdrawal marked as processing", "withdrawal_id": withdrawal.id}

@router.post("/admin/{withdrawal_id}/complete", response_model=WithdrawalResponse)
async def complete_withdrawal(
    withdrawal_id: int,
    complete_data: WithdrawalCompleteRequest,
    current_user: User = Depends(deps.get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """출금 완료 처리 (관리자)"""
    service = WithdrawalService(db)
    withdrawal = await service.complete_withdrawal(
        withdrawal_id=withdrawal_id,
        tx_hash=complete_data.tx_hash,
        admin_id=current_user.id,
        tx_fee=complete_data.tx_fee
    )
    await db.commit()
    
    return withdrawal

@router.get("/admin/stats")
async def get_withdrawal_stats(
    current_user: User = Depends(deps.get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """출금 통계 (관리자)"""
    # 상태별 통계
    status_stats = await db.execute(
        select(
            Withdrawal.status,
            func.count(Withdrawal.id),
            func.sum(Withdrawal.amount)
        ).group_by(Withdrawal.status)
    )
    
    stats_by_status = {}
    for status, count, total in status_stats:
        stats_by_status[status] = {
            "count": count,
            "total_amount": str(total or 0)
        }
    
    # 오늘 통계
    today = datetime.utcnow().date()
    today_stats = await db.execute(
        select(
            func.count(Withdrawal.id),
            func.sum(Withdrawal.amount)
        ).filter(Withdrawal.requested_at >= today)
    )
    today_count, today_amount = today_stats.one()
    
    return {
        "by_status": stats_by_status,
        "today": {
            "count": today_count or 0,
            "amount": str(today_amount or 0)
        },
        "pending_priority": await _get_priority_stats(db)
    }

async def _get_priority_stats(db: AsyncSession):
    """우선순위별 통계"""
    result = await db.execute(
        select(
            Withdrawal.priority,
            func.count(Withdrawal.id)
        ).filter(
            Withdrawal.status.in_([
                WithdrawalStatus.PENDING,
                WithdrawalStatus.APPROVED
            ])
        ).group_by(Withdrawal.priority)
    )
    
    stats = {}
    for priority, count in result:
        stats[priority] = count
    
    return stats
```

### 5. 모델 업데이트 (app/models/__init__.py)

```python
from app.models.base import BaseModel
from app.models.user import User
from app.models.balance import Balance
from app.models.transaction import Transaction, TransactionType, TransactionStatus, TransactionDirection
from app.models.wallet import Wallet
from app.models.deposit import Deposit, DepositStatus
from app.models.withdrawal import Withdrawal, WithdrawalStatus, WithdrawalPriority

__all__ = [
    "BaseModel", "User", "Balance", "Transaction", "Wallet", "Deposit", "Withdrawal",
    "TransactionType", "TransactionStatus", "TransactionDirection", 
    "DepositStatus", "WithdrawalStatus", "WithdrawalPriority"
]
```

### 6. API 라우터 업데이트 (app/api/v1/api.py)

```python
from fastapi import APIRouter
from app.api.v1.endpoints import auth, balance, wallet, monitoring, deposits, withdrawals

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(balance.router, prefix="/balance", tags=["balance"])
api_router.include_router(wallet.router, prefix="/wallet", tags=["wallet"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(deposits.router, prefix="/deposits", tags=["deposits"])
api_router.include_router(withdrawals.router, prefix="/withdrawals", tags=["withdrawals"])

@api_router.get("/test")
async def test_endpoint():
    return {"message": "API v1 is working"}
```

### 7. 마이그레이션 생성

```bash
# Withdrawal 테이블 추가
poetry run alembic revision --autogenerate -m "Add withdrawal table"
poetry run alembic upgrade head
```

### 8. 출금 처리 가이드 문서 (docs/withdrawal-processing-guide.md)

```markdown
# DantaroWallet 출금 처리 가이드

## 1. 출금 처리 흐름

1. **사용자 요청** → 2. **관리자 검토** → 3. **승인/거부** → 4. **수동 처리** → 5. **완료 기록**

## 2. 관리자 체크리스트

### 출금 검토 시
- [ ] 사용자 KYC 상태 확인
- [ ] 출금 주소 유효성 확인 
- [ ] 최근 거래 패턴 확인
- [ ] 일일 한도 확인
- [ ] 의심스러운 활동 여부

### 출금 처리 시
- [ ] 회사 지갑 USDT 잔고 확인
- [ ] 회사 지갑 TRX (가스비) 확인
- [ ] 수신 주소 재확인
- [ ] 금액 재확인
- [ ] 테스트 전송 (대량 출금 시)

## 3. TRON 지갑 사용법

### TronLink 사용
1. TronLink 확장 프로그램 열기
2. 회사 지갑 선택
3. USDT (TRC20) 선택
4. Send 버튼 클릭
5. 수신 주소 입력 (복사-붙여넣기)
6. 금액 입력
7. 수수료 확인
8. 비밀번호 입력 및 전송

### 트랜잭션 확인
1. TronScan에서 tx hash 검색
2. 상태가 "SUCCESS"인지 확인
3. 수신 주소와 금액 재확인

## 4. 보안 주의사항

⚠️ **절대 하지 말아야 할 것**
- 프라이빗 키를 누구와도 공유하지 않기
- 의심스러운 주소로 전송하지 않기
- 브라우저에 프라이빗 키 입력하지 않기

✅ **항상 해야 할 것**
- 주소 처음과 끝 6자리 이상 확인
- 금액 소수점까지 정확히 확인
- 전송 전 모든 정보 재확인
- 트랜잭션 완료 후 즉시 기록

## 5. 긴급 상황 대응

### 잘못된 주소로 전송한 경우
1. 즉시 상급자에게 보고
2. 트랜잭션 정보 기록
3. 수신자 연락 시도 (가능한 경우)

### 트랜잭션 실패
1. 에러 메시지 캡처
2. 가스비 부족 여부 확인
3. 네트워크 상태 확인
4. 재시도 전 원인 파악

## 6. 일일 체크리스트

- [ ] 회사 지갑 잔고 확인
- [ ] 대기 중인 출금 요청 확인
- [ ] 처리 완료된 출금 기록
- [ ] 이상 거래 모니터링
- [ ] 일일 리포트 작성
```

### 9. 출금 테스트 (tests/test_withdrawals.py)

```python
import pytest
from httpx import AsyncClient
from decimal import Decimal
from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.balance import Balance
from sqlalchemy import select

async def create_test_user_with_balance(email: str, balance: Decimal = Decimal("1000")):
    """테스트용 사용자 생성 및 잔고 설정"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 회원가입
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "Test123!@#",
                "password_confirm": "Test123!@#"
            }
        )
        
        # 검증 및 잔고 설정
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).filter(User.email == email))
            user = result.scalar_one()
            user.is_verified = True
            
            # 관리자 권한 부여 (필요한 경우)
            if "admin" in email:
                user.is_admin = True
            
            # 잔고 설정
            balance_result = await db.execute(
                select(Balance).filter(Balance.user_id == user.id)
            )
            user_balance = balance_result.scalar_one()
            user_balance.amount = balance
            
            await db.commit()
        
        # 로그인
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Test123!@#"}
        )
        
        return response.json()["access_token"]

@pytest.mark.asyncio
async def test_withdrawal_request():
    """출금 요청 테스트"""
    token = await create_test_user_with_balance("withdrawal_test@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/withdrawals/request",
            json={
                "to_address": "TN9RRaXkCFtTXRso2GdTZxSxxwufzxLQPP",
                "amount": "100.0",
                "notes": "Test withdrawal"
            },
            headers=headers
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == "100.000000"
    assert data["fee"] == "1.000000"
    assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_insufficient_balance():
    """잔고 부족 테스트"""
    token = await create_test_user_with_balance(
        "poor_withdrawal@example.com",
        Decimal("5.0")
    )
    headers = {"Authorization": f"Bearer {token}"}
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/withdrawals/request",
            json={
                "to_address": "TN9RRaXkCFtTXRso2GdTZxSxxwufzxLQPP",
                "amount": "10.0"
            },
            headers=headers
        )
    
    assert response.status_code == 400
    assert "INSUFFICIENT_BALANCE" in response.json()["error"]

@pytest.mark.asyncio
async def test_withdrawal_limits():
    """출금 한도 테스트"""
    token = await create_test_user_with_balance(
        "limits_test@example.com",
        Decimal("50000")
    )
    headers = {"Authorization": f"Bearer {token}"}
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 최소 금액 미만
        response = await client.post(
            "/api/v1/withdrawals/request",
            json={
                "to_address": "TN9RRaXkCFtTXRso2GdTZxSxxwufzxLQPP",
                "amount": "5.0"
            },
            headers=headers
        )
        assert response.status_code == 422
        
        # 최대 금액 초과
        response = await client.post(
            "/api/v1/withdrawals/request",
            json={
                "to_address": "TN9RRaXkCFtTXRso2GdTZxSxxwufzxLQPP",
                "amount": "15000.0"
            },
            headers=headers
        )
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_withdrawal_cancel():
    """출금 취소 테스트"""
    token = await create_test_user_with_balance("cancel_test@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 출금 요청
        response = await client.post(
            "/api/v1/withdrawals/request",
            json={
                "to_address": "TN9RRaXkCFtTXRso2GdTZxSxxwufzxLQPP",
                "amount": "100.0"
            },
            headers=headers
        )
        withdrawal_id = response.json()["id"]
        
        # 취소
        response = await client.post(
            f"/api/v1/withdrawals/{withdrawal_id}/cancel",
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

@pytest.mark.asyncio
async def test_admin_withdrawal_review():
    """관리자 출금 검토 테스트"""
    # 일반 사용자 출금 요청
    user_token = await create_test_user_with_balance("review_user@example.com")
    user_headers = {"Authorization": f"Bearer {user_token}"}
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/withdrawals/request",
            json={
                "to_address": "TN9RRaXkCFtTXRso2GdTZxSxxwufzxLQPP",
                "amount": "100.0"
            },
            headers=user_headers
        )
        withdrawal_id = response.json()["id"]
    
    # 관리자로 검토
    admin_token = await create_test_user_with_balance("admin@example.com")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 승인
        response = await client.post(
            f"/api/v1/withdrawals/admin/{withdrawal_id}/review",
            json={
                "action": "approve",
                "admin_notes": "Verified"
            },
            headers=admin_headers
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "approved"
```

## 실행 및 검증

1. 마이그레이션 실행:
   ```bash
   make db-upgrade
   ```

2. 서버 재시작:
   ```bash
   make dev
   ```

3. 테스트 실행:
   ```bash
   make test tests/test_withdrawals.py
   ```

4. 출금 처리 흐름 테스트:
   - 사용자로 출금 요청
   - 관리자로 로그인하여 검토/승인
   - 처리 가이드 확인
   - 수동으로 TRON 지갑에서 전송
   - 트랜잭션 해시로 완료 처리

## 검증 포인트

- [ ] 출금 요청이 생성되는가?
- [ ] 잔고가 올바르게 잠기는가?
- [ ] 출금 한도가 적용되는가?
- [ ] 관리자가 출금을 검토할 수 있는가?
- [ ] 출금 취소 시 잔고가 복구되는가?
- [ ] 처리 가이드가 표시되는가?
- [ ] 출금 완료 처리가 작동하는가?
- [ ] 알림이 전송되는가?

## 주의사항

- 초기에는 **수동 처리**로 안전성을 확보합니다.
- 충분한 테스트 후 자동화를 고려할 수 있습니다.
- 모든 출금은 로그와 알림으로 추적됩니다.
- 관리자는 출금 처리 시 이중 확인을 해야 합니다.

이 문서를 완료하면 안전한 출금 시스템이 구축되며, 관리자 승인과 수동 처리를 통해 보안을 유지하면서 출금 서비스를 제공할 수 있습니다.