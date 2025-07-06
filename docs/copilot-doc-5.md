# Copilot 문서 #5: 내부 잔고 관리 시스템 (오프체인)

## 목표
오프체인 잔고 관리 시스템을 구현합니다. 잔고 조회, 내부 이체, 트랜잭션 로그, 동시성 제어를 포함합니다.

## 전제 조건
- Copilot 문서 #1-4가 완료되어 있어야 합니다.
- 인증 시스템이 작동하고 있어야 합니다.
- Balance 모델이 생성되어 있어야 합니다.

## 상세 지시사항

### 1. 트랜잭션 모델 추가 (app/models/transaction.py)

```python
from decimal import Decimal
from enum import Enum
from sqlalchemy import Column, String, Numeric, ForeignKey, Index, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class TransactionType(str, Enum):
    """트랜잭션 타입"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    BONUS = "bonus"
    FEE = "fee"
    ADJUSTMENT = "adjustment"

class TransactionStatus(str, Enum):
    """트랜잭션 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TransactionDirection(str, Enum):
    """트랜잭션 방향"""
    IN = "in"
    OUT = "out"
    INTERNAL = "internal"

class Transaction(BaseModel):
    """트랜잭션 모델"""
    
    # 사용자 정보
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 트랜잭션 정보
    type = Column(SQLEnum(TransactionType), nullable=False, index=True)
    direction = Column(SQLEnum(TransactionDirection), nullable=False)
    status = Column(
        SQLEnum(TransactionStatus),
        nullable=False,
        default=TransactionStatus.PENDING,
        index=True
    )
    
    # 금액 정보
    asset = Column(String(10), nullable=False, default="USDT")
    amount = Column(
        Numeric(precision=18, scale=6),
        nullable=False
    )
    fee = Column(
        Numeric(precision=18, scale=6),
        nullable=False,
        default=Decimal("0.000000")
    )
    
    # 관련 정보
    related_user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )  # 이체 시 상대방
    
    reference_id = Column(String(100), unique=True, nullable=True, index=True)  # 외부 참조 ID
    tx_hash = Column(String(100), nullable=True, index=True)  # 블록체인 트랜잭션 해시
    
    # 추가 정보
    description = Column(Text, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON 형태의 추가 데이터
    
    # 인덱스
    __table_args__ = (
        Index('idx_tx_user_created', 'user_id', 'created_at'),
        Index('idx_tx_status_type', 'status', 'type'),
        Index('idx_tx_reference', 'reference_id'),
    )
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, type={self.type}, amount={self.amount})>"
    
    @property
    def net_amount(self) -> Decimal:
        """수수료를 제외한 순 금액"""
        if self.direction == TransactionDirection.OUT:
            return self.amount + self.fee
        return self.amount - self.fee
```

### 2. 모델 업데이트 (app/models/__init__.py)

```python
from app.models.base import BaseModel
from app.models.user import User
from app.models.balance import Balance
from app.models.transaction import Transaction, TransactionType, TransactionStatus, TransactionDirection

__all__ = [
    "BaseModel", "User", "Balance", "Transaction",
    "TransactionType", "TransactionStatus", "TransactionDirection"
]
```

### 3. 잔고 서비스 (app/services/balance_service.py)

```python
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
import logging
from datetime import datetime
import json

from app.models.user import User
from app.models.balance import Balance
from app.models.transaction import Transaction, TransactionType, TransactionStatus, TransactionDirection
from app.core.exceptions import NotFoundError, InsufficientBalanceError, ValidationError

logger = logging.getLogger(__name__)

class BalanceService:
    """잔고 관리 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_balance(self, user_id: int, asset: str = "USDT") -> Balance:
        """사용자 잔고 조회"""
        result = await self.db.execute(
            select(Balance).filter(
                and_(
                    Balance.user_id == user_id,
                    Balance.asset == asset
                )
            )
        )
        balance = result.scalar_one_or_none()
        
        if not balance:
            raise NotFoundError(f"Balance for asset {asset}")
        
        return balance
    
    async def get_or_create_balance(self, user_id: int, asset: str = "USDT") -> Balance:
        """잔고 조회 또는 생성"""
        try:
            return await self.get_balance(user_id, asset)
        except NotFoundError:
            # 잔고가 없으면 생성
            balance = Balance(
                user_id=user_id,
                asset=asset,
                amount=Decimal("0.000000"),
                locked_amount=Decimal("0.000000")
            )
            self.db.add(balance)
            await self.db.flush()
            return balance
    
    async def internal_transfer(
        self,
        sender_id: int,
        receiver_id: int,
        amount: Decimal,
        description: Optional[str] = None,
        asset: str = "USDT"
    ) -> Dict[str, Any]:
        """내부 이체 처리"""
        
        # 금액 검증
        if amount <= 0:
            raise ValidationError("Transfer amount must be positive")
        
        # 최소 금액 체크 (0.000001 USDT)
        if amount < Decimal("0.000001"):
            raise ValidationError("Amount too small")
        
        # 자기 자신에게 이체 방지
        if sender_id == receiver_id:
            raise ValidationError("Cannot transfer to yourself")
        
        # 트랜잭션 시작
        async with self.db.begin_nested():
            # 발신자 잔고 조회 (FOR UPDATE로 락)
            sender_balance = await self.db.execute(
                select(Balance).filter(
                    and_(
                        Balance.user_id == sender_id,
                        Balance.asset == asset
                    )
                ).with_for_update()
            )
            sender_balance = sender_balance.scalar_one_or_none()
            
            if not sender_balance:
                raise NotFoundError(f"Sender balance for {asset}")
            
            # 잔고 충분한지 확인
            if not sender_balance.can_withdraw(amount):
                raise InsufficientBalanceError(
                    required=float(amount),
                    available=float(sender_balance.available_amount)
                )
            
            # 수신자 잔고 조회 또는 생성
            receiver_balance = await self.get_or_create_balance(receiver_id, asset)
            
            # 잔고 업데이트
            sender_balance.amount -= amount
            receiver_balance.amount += amount
            
            # 트랜잭션 기록 생성
            reference_id = f"INT-{datetime.utcnow().timestamp()}"
            
            # 발신자 트랜잭션
            sender_tx = Transaction(
                user_id=sender_id,
                type=TransactionType.TRANSFER,
                direction=TransactionDirection.OUT,
                status=TransactionStatus.COMPLETED,
                asset=asset,
                amount=amount,
                fee=Decimal("0"),  # 내부 이체는 수수료 없음
                related_user_id=receiver_id,
                reference_id=f"{reference_id}-OUT",
                description=description or "Internal transfer"
            )
            
            # 수신자 트랜잭션
            receiver_tx = Transaction(
                user_id=receiver_id,
                type=TransactionType.TRANSFER,
                direction=TransactionDirection.IN,
                status=TransactionStatus.COMPLETED,
                asset=asset,
                amount=amount,
                fee=Decimal("0"),
                related_user_id=sender_id,
                reference_id=f"{reference_id}-IN",
                description=description or "Internal transfer received"
            )
            
            self.db.add(sender_tx)
            self.db.add(receiver_tx)
            
            await self.db.flush()
        
        # 커밋은 상위 레벨에서 처리
        logger.info(
            f"Internal transfer completed: {sender_id} -> {receiver_id}, "
            f"amount: {amount} {asset}"
        )
        
        return {
            "sender_balance": sender_balance.amount,
            "receiver_balance": receiver_balance.amount,
            "transaction_id": sender_tx.id,
            "reference_id": reference_id
        }
    
    async def adjust_balance(
        self,
        user_id: int,
        amount: Decimal,
        adjustment_type: str,
        description: str,
        admin_id: int,
        asset: str = "USDT"
    ) -> Balance:
        """관리자에 의한 잔고 조정 (입금 시뮬레이션, 보너스 등)"""
        
        balance = await self.get_or_create_balance(user_id, asset)
        
        # 금액 적용
        if amount > 0:
            balance.amount += amount
            direction = TransactionDirection.IN
        else:
            if balance.available_amount < abs(amount):
                raise InsufficientBalanceError(
                    required=float(abs(amount)),
                    available=float(balance.available_amount)
                )
            balance.amount += amount  # amount가 음수
            direction = TransactionDirection.OUT
        
        # 트랜잭션 기록
        tx = Transaction(
            user_id=user_id,
            type=TransactionType.ADJUSTMENT,
            direction=direction,
            status=TransactionStatus.COMPLETED,
            asset=asset,
            amount=abs(amount),
            fee=Decimal("0"),
            description=description,
            metadata=json.dumps({
                "adjustment_type": adjustment_type,
                "admin_id": admin_id,
                "timestamp": datetime.utcnow().isoformat()
            })
        )
        
        self.db.add(tx)
        await self.db.flush()
        
        logger.info(
            f"Balance adjustment: user={user_id}, amount={amount}, "
            f"type={adjustment_type}, admin={admin_id}"
        )
        
        return balance
    
    async def lock_amount(self, user_id: int, amount: Decimal, asset: str = "USDT") -> bool:
        """금액 잠금 (출금 준비 등)"""
        balance = await self.get_balance(user_id, asset)
        
        if balance.lock(amount):
            await self.db.flush()
            return True
        
        raise InsufficientBalanceError(
            required=float(amount),
            available=float(balance.available_amount)
        )
    
    async def unlock_amount(self, user_id: int, amount: Decimal, asset: str = "USDT") -> bool:
        """금액 잠금 해제"""
        balance = await self.get_balance(user_id, asset)
        
        if balance.unlock(amount):
            await self.db.flush()
            return True
        
        raise ValidationError(f"Cannot unlock {amount} {asset}")
    
    async def get_transaction_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        tx_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None
    ) -> List[Transaction]:
        """트랜잭션 내역 조회"""
        query = select(Transaction).filter(
            Transaction.user_id == user_id
        )
        
        if tx_type:
            query = query.filter(Transaction.type == tx_type)
        
        if status:
            query = query.filter(Transaction.status == status)
        
        query = query.order_by(Transaction.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_balance_summary(self, user_id: int) -> Dict[str, Any]:
        """잔고 요약 정보"""
        # 모든 잔고 조회
        result = await self.db.execute(
            select(Balance).filter(Balance.user_id == user_id)
        )
        balances = result.scalars().all()
        
        # 최근 트랜잭션
        recent_txs = await self.get_transaction_history(user_id, limit=10)
        
        # 통계 계산
        total_in = await self.db.execute(
            select(func.sum(Transaction.amount)).filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.direction == TransactionDirection.IN,
                    Transaction.status == TransactionStatus.COMPLETED
                )
            )
        )
        total_in = total_in.scalar() or Decimal("0")
        
        total_out = await self.db.execute(
            select(func.sum(Transaction.amount + Transaction.fee)).filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.direction == TransactionDirection.OUT,
                    Transaction.status == TransactionStatus.COMPLETED
                )
            )
        )
        total_out = total_out.scalar() or Decimal("0")
        
        return {
            "balances": [
                {
                    "asset": b.asset,
                    "amount": str(b.amount),
                    "locked_amount": str(b.locked_amount),
                    "available_amount": str(b.available_amount)
                }
                for b in balances
            ],
            "recent_transactions": recent_txs,
            "statistics": {
                "total_received": str(total_in),
                "total_sent": str(total_out),
                "net_flow": str(total_in - total_out)
            }
        }
```

### 4. 잔고 스키마 (app/schemas/balance.py)

```python
from pydantic import BaseModel, Field, validator
from decimal import Decimal
from typing import Optional, List
from datetime import datetime
from app.models.transaction import TransactionType, TransactionStatus, TransactionDirection

class BalanceResponse(BaseModel):
    """잔고 응답 스키마"""
    asset: str
    amount: Decimal
    locked_amount: Decimal
    available_amount: Decimal
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TransferRequest(BaseModel):
    """내부 이체 요청 스키마"""
    receiver_email: str
    amount: Decimal = Field(..., gt=0, decimal_places=6)
    description: Optional[str] = Field(None, max_length=200)
    
    @validator('amount')
    def validate_amount(cls, v):
        if v < Decimal("0.000001"):
            raise ValueError("Amount must be at least 0.000001 USDT")
        if v > Decimal("1000000"):
            raise ValueError("Amount too large")
        return v

class TransferResponse(BaseModel):
    """이체 응답 스키마"""
    transaction_id: int
    reference_id: str
    amount: Decimal
    receiver_email: str
    sender_balance: Decimal
    timestamp: datetime

class TransactionResponse(BaseModel):
    """트랜잭션 응답 스키마"""
    id: int
    type: TransactionType
    direction: TransactionDirection
    status: TransactionStatus
    amount: Decimal
    fee: Decimal
    net_amount: Decimal
    asset: str
    description: Optional[str]
    related_user_id: Optional[int]
    tx_hash: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class BalanceSummaryResponse(BaseModel):
    """잔고 요약 응답 스키마"""
    balances: List[dict]
    recent_transactions: List[TransactionResponse]
    statistics: dict

class BalanceAdjustmentRequest(BaseModel):
    """잔고 조정 요청 스키마 (관리자용)"""
    user_id: int
    amount: Decimal
    adjustment_type: str = Field(..., pattern="^(deposit|bonus|correction|penalty)$")
    description: str = Field(..., min_length=5, max_length=200)
```

### 5. 잔고 엔드포인트 (app/api/v1/endpoints/balance.py)

```python
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.api import deps
from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.models.user import User
from app.models.transaction import TransactionType, TransactionStatus
from app.services.balance_service import BalanceService
from app.schemas.balance import (
    BalanceResponse, TransferRequest, TransferResponse,
    TransactionResponse, BalanceSummaryResponse,
    BalanceAdjustmentRequest
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=BalanceResponse)
async def get_balance(
    asset: str = Query("USDT", description="Asset type"),
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """현재 사용자의 잔고 조회"""
    service = BalanceService(db)
    balance = await service.get_or_create_balance(current_user.id, asset)
    return balance

@router.get("/summary", response_model=BalanceSummaryResponse)
async def get_balance_summary(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """잔고 요약 정보 조회"""
    service = BalanceService(db)
    summary = await service.get_balance_summary(current_user.id)
    return summary

@router.post("/transfer", response_model=TransferResponse)
async def internal_transfer(
    transfer_data: TransferRequest,
    current_user: User = Depends(deps.get_current_verified_user),
    db: AsyncSession = Depends(get_db)
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
        description=transfer_data.description
    )
    
    await db.commit()
    
    return TransferResponse(
        transaction_id=result["transaction_id"],
        reference_id=result["reference_id"],
        amount=transfer_data.amount,
        receiver_email=receiver.email,
        sender_balance=result["sender_balance"],
        timestamp=datetime.utcnow()
    )

@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tx_type: Optional[TransactionType] = None,
    status: Optional[TransactionStatus] = None,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """트랜잭션 내역 조회"""
    service = BalanceService(db)
    transactions = await service.get_transaction_history(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        tx_type=tx_type,
        status=status
    )
    return transactions

@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction_detail(
    transaction_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """특정 트랜잭션 상세 조회"""
    result = await db.execute(
        select(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id
        )
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise NotFoundError("Transaction not found")
    
    return transaction

# 관리자 전용 엔드포인트
@router.post("/admin/adjust", response_model=BalanceResponse, dependencies=[Depends(deps.get_current_admin_user)])
async def adjust_balance(
    adjustment: BalanceAdjustmentRequest,
    admin_user: User = Depends(deps.get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """관리자 잔고 조정 (입금 시뮬레이션 등)"""
    service = BalanceService(db)
    balance = await service.adjust_balance(
        user_id=adjustment.user_id,
        amount=adjustment.amount,
        adjustment_type=adjustment.adjustment_type,
        description=adjustment.description,
        admin_id=admin_user.id
    )
    
    await db.commit()
    
    logger.info(
        f"Admin balance adjustment: admin={admin_user.email}, "
        f"user={adjustment.user_id}, amount={adjustment.amount}"
    )
    
    return balance
```

### 6. API 라우터 업데이트 (app/api/v1/api.py)

```python
from fastapi import APIRouter
from app.api.v1.endpoints import auth, balance  # balance 추가

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(balance.router, prefix="/balance", tags=["balance"])  # 추가

@api_router.get("/test")
async def test_endpoint():
    return {"message": "API v1 is working"}
```

### 7. 마이그레이션 생성

```bash
# 트랜잭션 테이블 추가 마이그레이션
poetry run alembic revision --autogenerate -m "Add transaction table"
poetry run alembic upgrade head
```

### 8. 잔고 테스트 (tests/test_balance.py)

```python
import pytest
from httpx import AsyncClient
from decimal import Decimal
from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.balance import Balance
from app.core.security import get_password_hash

async def create_test_user(email: str, is_admin: bool = False) -> dict:
    """테스트용 사용자 생성 헬퍼"""
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
        
        # 관리자 권한 부여 (필요시)
        if is_admin:
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(User).filter(User.email == email))
                user = result.scalar_one()
                user.is_admin = True
                user.is_verified = True
                await db.commit()
        
        # 로그인
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Test123!@#"}
        )
        
        return response.json()

@pytest.mark.asyncio
async def test_get_initial_balance():
    """초기 잔고 조회 테스트"""
    auth_data = await create_test_user("balance_test1@example.com")
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/balance/",
            headers={"Authorization": f"Bearer {auth_data['access_token']}"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["asset"] == "USDT"
    assert Decimal(data["amount"]) == Decimal("0.000000")
    assert Decimal(data["locked_amount"]) == Decimal("0.000000")

@pytest.mark.asyncio
async def test_internal_transfer():
    """내부 이체 테스트"""
    # 두 사용자 생성
    sender_auth = await create_test_user("sender@example.com")
    receiver_auth = await create_test_user("receiver@example.com")
    
    # 발신자에게 잔고 추가 (관리자 권한으로)
    admin_auth = await create_test_user("admin@example.com", is_admin=True)
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 관리자가 발신자에게 100 USDT 입금
        await client.post(
            "/api/v1/balance/admin/adjust",
            json={
                "user_id": 1,  # sender의 ID (테스트 환경에서는 순차적)
                "amount": "100.000000",
                "adjustment_type": "deposit",
                "description": "Test deposit"
            },
            headers={"Authorization": f"Bearer {admin_auth['access_token']}"}
        )
        
        # 발신자가 수신자에게 10 USDT 이체
        response = await client.post(
            "/api/v1/balance/transfer",
            json={
                "receiver_email": "receiver@example.com",
                "amount": "10.000000",
                "description": "Test transfer"
            },
            headers={"Authorization": f"Bearer {sender_auth['access_token']}"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["amount"]) == Decimal("10.000000")
    assert Decimal(data["sender_balance"]) == Decimal("90.000000")

@pytest.mark.asyncio
async def test_insufficient_balance():
    """잔고 부족 테스트"""
    auth_data = await create_test_user("poor_user@example.com")
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/balance/transfer",
            json={
                "receiver_email": "someone@example.com",
                "amount": "100.000000",
                "description": "Will fail"
            },
            headers={"Authorization": f"Bearer {auth_data['access_token']}"}
        )
    
    assert response.status_code == 400
    assert response.json()["error"] == "INSUFFICIENT_BALANCE"

@pytest.mark.asyncio
async def test_transaction_history():
    """트랜잭션 내역 조회 테스트"""
    auth_data = await create_test_user("history_test@example.com")
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/balance/transactions",
            headers={"Authorization": f"Bearer {auth_data['access_token']}"}
        )
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_balance_summary():
    """잔고 요약 조회 테스트"""
    auth_data = await create_test_user("summary_test@example.com")
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/balance/summary",
            headers={"Authorization": f"Bearer {auth_data['access_token']}"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "balances" in data
    assert "recent_transactions" in data
    assert "statistics" in data

@pytest.mark.asyncio
async def test_self_transfer_prevention():
    """자기 자신에게 이체 방지 테스트"""
    auth_data = await create_test_user("self_transfer@example.com")
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/balance/transfer",
            json={
                "receiver_email": "self_transfer@example.com",
                "amount": "10.000000",
                "description": "Self transfer"
            },
            headers={"Authorization": f"Bearer {auth_data['access_token']}"}
        )
    
    assert response.status_code == 422
    assert "Cannot transfer to yourself" in response.json()["message"]
```

### 9. 추가 import 필요 (기존 파일들)

datetime import 추가가 필요한 경우:
```python
from datetime import datetime
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
   make test tests/test_balance.py
   ```

4. API 문서 확인:
   http://localhost:8000/api/v1/docs

## 검증 포인트

- [ ] 잔고 조회가 정상 작동하는가?
- [ ] 내부 이체가 정상 처리되는가?
- [ ] 트랜잭션이 올바르게 기록되는가?
- [ ] 동시성 제어가 작동하는가? (이중 차감 방지)
- [ ] 잔고 부족 시 적절한 에러가 발생하는가?
- [ ] 트랜잭션 내역 조회가 작동하는가?
- [ ] 관리자 잔고 조정이 작동하는가?
- [ ] 모든 테스트가 통과하는가?

이 문서를 완료하면 오프체인 잔고 관리 시스템이 완성되며, 내부 이체와 트랜잭션 추적이 가능해집니다.