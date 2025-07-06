# Copilot 문서 #9: TRON 입금 모니터링 시스템

## 목표
TRON 블록체인에서 사용자 지갑으로의 USDT 입금을 자동으로 감지하고, DB 잔고를 업데이트하는 시스템을 구축합니다. 입금 감지, 확인, 알림을 포함합니다.

## 전제 조건
- Copilot 문서 #1-8이 완료되어 있어야 합니다.
- 사용자 지갑이 생성되어 있어야 합니다.
- TRON 테스트넷(Nile)에서 작동하도록 설정합니다.

## 상세 지시사항

### 1. 입금 트랜잭션 모델 추가 (app/models/deposit.py)

```python
from sqlalchemy import Column, String, Integer, Numeric, Boolean, ForeignKey, Index, DateTime
from sqlalchemy.orm import relationship
from decimal import Decimal
from datetime import datetime
from enum import Enum
from app.models.base import BaseModel

class DepositStatus(str, Enum):
    """입금 상태"""
    DETECTED = "detected"          # 감지됨
    CONFIRMING = "confirming"      # 확인 중
    CONFIRMED = "confirmed"        # 확인 완료
    CREDITED = "credited"          # 잔고 반영 완료
    FAILED = "failed"             # 실패
    ORPHANED = "orphaned"         # 고아 블록

class Deposit(BaseModel):
    """입금 트랜잭션 모델"""
    
    # 사용자 정보
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False, index=True)
    
    # 트랜잭션 정보
    tx_hash = Column(String(100), unique=True, nullable=False, index=True)
    from_address = Column(String(42), nullable=False)
    to_address = Column(String(42), nullable=False)
    
    # 금액 정보
    amount = Column(Numeric(precision=18, scale=6), nullable=False)
    token = Column(String(10), nullable=False, default="USDT")
    
    # 상태 정보
    status = Column(String(20), nullable=False, default=DepositStatus.DETECTED)
    confirmations = Column(Integer, default=0)
    required_confirmations = Column(Integer, default=20)
    
    # 블록 정보
    block_number = Column(Integer, nullable=True)
    block_timestamp = Column(DateTime(timezone=True), nullable=True)
    
    # 처리 정보
    detected_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    credited_at = Column(DateTime(timezone=True), nullable=True)
    
    # 추가 정보
    raw_data = Column(String, nullable=True)  # JSON 형태의 원본 트랜잭션 데이터
    error_message = Column(String, nullable=True)
    
    # 인덱스
    __table_args__ = (
        Index('idx_deposit_status_created', 'status', 'created_at'),
        Index('idx_deposit_user_status', 'user_id', 'status'),
        Index('idx_deposit_block', 'block_number'),
    )
    
    def __repr__(self):
        return f"<Deposit(tx_hash={self.tx_hash}, amount={self.amount}, status={self.status})>"
    
    def needs_more_confirmations(self) -> bool:
        """추가 확인이 필요한지 확인"""
        return self.confirmations < self.required_confirmations
    
    def can_credit(self) -> bool:
        """잔고 반영 가능한지 확인"""
        return (
            self.status == DepositStatus.CONFIRMED and
            self.confirmations >= self.required_confirmations
        )
```

### 2. TRON 블록체인 모니터링 서비스 (app/services/blockchain_monitor.py)

```python
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import asyncio
import logging
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from tronpy import AsyncTron
from tronpy.keys import to_base58check_address

from app.core.config import settings
from app.models.wallet import Wallet
from app.models.deposit import Deposit, DepositStatus
from app.models.transaction import Transaction, TransactionType, TransactionStatus, TransactionDirection
from app.services.balance_service import BalanceService
from app.services.alert_service import alert_service, AlertLevel
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

class BlockchainMonitor:
    """블록체인 모니터링 서비스"""
    
    def __init__(self):
        # 네트워크 설정
        if settings.TRON_NETWORK == "nile":
            self.tron = AsyncTron(network="nile")
            self.usdt_contract = "TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf"  # Nile USDT
        else:
            self.tron = AsyncTron()
            self.usdt_contract = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # Mainnet USDT
        
        self.last_scanned_block = None
        self.scan_interval = 10  # 10초마다 스캔
        self.is_running = False
    
    async def start(self):
        """모니터링 시작"""
        self.is_running = True
        logger.info("Blockchain monitor started")
        
        # 마지막 스캔 블록 번호 복구
        await self._recover_last_block()
        
        # 모니터링 루프 시작
        asyncio.create_task(self._monitor_loop())
        asyncio.create_task(self._confirmation_loop())
    
    async def stop(self):
        """모니터링 중지"""
        self.is_running = False
        logger.info("Blockchain monitor stopped")
    
    async def _recover_last_block(self):
        """마지막 스캔 블록 번호 복구"""
        async with AsyncSessionLocal() as db:
            # 가장 최근 입금의 블록 번호 조회
            result = await db.execute(
                select(Deposit.block_number)
                .filter(Deposit.block_number.isnot(None))
                .order_by(Deposit.block_number.desc())
                .limit(1)
            )
            last_deposit_block = result.scalar_one_or_none()
            
            if last_deposit_block:
                self.last_scanned_block = last_deposit_block
            else:
                # 현재 블록에서 100블록 전부터 시작
                current_block = await self.tron.get_latest_block_number()
                self.last_scanned_block = max(0, current_block - 100)
            
            logger.info(f"Starting scan from block {self.last_scanned_block}")
    
    async def _monitor_loop(self):
        """메인 모니터링 루프"""
        while self.is_running:
            try:
                await self._scan_blocks()
                await asyncio.sleep(self.scan_interval)
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await alert_service.send_alert(
                    "Blockchain Monitor Error",
                    f"Error scanning blocks: {str(e)}",
                    AlertLevel.ERROR,
                    "blockchain_monitor_error"
                )
                await asyncio.sleep(60)  # 에러 시 1분 대기
    
    async def _scan_blocks(self):
        """블록 스캔"""
        try:
            current_block = await self.tron.get_latest_block_number()
            
            # 너무 많은 블록을 한 번에 스캔하지 않도록 제한
            blocks_to_scan = min(10, current_block - self.last_scanned_block)
            
            if blocks_to_scan <= 0:
                return
            
            logger.debug(f"Scanning blocks {self.last_scanned_block + 1} to {self.last_scanned_block + blocks_to_scan}")
            
            # 모니터링 중인 지갑 주소 가져오기
            async with AsyncSessionLocal() as db:
                monitored_addresses = await self._get_monitored_addresses(db)
                
                if not monitored_addresses:
                    return
                
                # 각 블록 스캔
                for block_num in range(self.last_scanned_block + 1, self.last_scanned_block + blocks_to_scan + 1):
                    await self._scan_block(db, block_num, monitored_addresses)
                
                self.last_scanned_block = self.last_scanned_block + blocks_to_scan
                
        except Exception as e:
            logger.error(f"Error scanning blocks: {e}")
            raise
    
    async def _get_monitored_addresses(self, db: AsyncSession) -> Dict[str, int]:
        """모니터링 중인 지갑 주소 조회"""
        result = await db.execute(
            select(Wallet).filter(
                and_(
                    Wallet.is_active == True,
                    Wallet.is_monitored == True
                )
            )
        )
        wallets = result.scalars().all()
        
        # 주소 -> wallet_id 매핑
        return {wallet.address: wallet.id for wallet in wallets}
    
    async def _scan_block(self, db: AsyncSession, block_num: int, monitored_addresses: Dict[str, int]):
        """특정 블록 스캔"""
        try:
            # 블록 정보 조회
            block = await self.tron.get_block(block_num)
            
            if not block or "transactions" not in block:
                return
            
            # 블록의 모든 트랜잭션 확인
            for tx in block["transactions"]:
                await self._process_transaction(db, tx, block, monitored_addresses)
            
        except Exception as e:
            logger.error(f"Error scanning block {block_num}: {e}")
    
    async def _process_transaction(self, db: AsyncSession, tx: Dict[str, Any], block: Dict[str, Any], monitored_addresses: Dict[str, int]):
        """트랜잭션 처리"""
        try:
            # TRC20 전송인지 확인
            if not self._is_trc20_transfer(tx):
                return
            
            # USDT 전송인지 확인
            contract_address = self._get_contract_address(tx)
            if contract_address != self.usdt_contract:
                return
            
            # 전송 정보 추출
            transfer_info = self._extract_transfer_info(tx)
            if not transfer_info:
                return
            
            to_address = transfer_info["to"]
            
            # 모니터링 중인 주소로의 입금인지 확인
            if to_address not in monitored_addresses:
                return
            
            wallet_id = monitored_addresses[to_address]
            
            # 이미 처리된 트랜잭션인지 확인
            existing = await db.execute(
                select(Deposit).filter(Deposit.tx_hash == transfer_info["tx_hash"])
            )
            if existing.scalar_one_or_none():
                return
            
            # 입금 기록 생성
            await self._create_deposit_record(db, wallet_id, transfer_info, block)
            
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
    
    def _is_trc20_transfer(self, tx: Dict[str, Any]) -> bool:
        """TRC20 전송 트랜잭션인지 확인"""
        try:
            if "raw_data" not in tx:
                return False
            
            contract = tx["raw_data"].get("contract", [])
            if not contract:
                return False
            
            return contract[0]["type"] == "TriggerSmartContract"
        except:
            return False
    
    def _get_contract_address(self, tx: Dict[str, Any]) -> Optional[str]:
        """컨트랙트 주소 추출"""
        try:
            contract = tx["raw_data"]["contract"][0]
            hex_address = contract["parameter"]["value"]["contract_address"]
            return to_base58check_address(hex_address)
        except:
            return None
    
    def _extract_transfer_info(self, tx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """전송 정보 추출"""
        try:
            contract = tx["raw_data"]["contract"][0]
            data = contract["parameter"]["value"]["data"]
            
            # transfer(address,uint256) 메서드 시그니처
            if not data.startswith("a9059cbb"):
                return None
            
            # 파라미터 파싱
            to_hex = "41" + data[32:72]  # TRON 주소는 41로 시작
            amount_hex = data[72:136]
            
            to_address = to_base58check_address(to_hex)
            amount = int(amount_hex, 16) / 1_000_000  # USDT는 6 decimals
            
            # from 주소
            from_hex = contract["parameter"]["value"]["owner_address"]
            from_address = to_base58check_address(from_hex)
            
            return {
                "tx_hash": tx["txID"],
                "from": from_address,
                "to": to_address,
                "amount": Decimal(str(amount)),
                "raw_data": json.dumps(tx)
            }
        except Exception as e:
            logger.error(f"Error extracting transfer info: {e}")
            return None
    
    async def _create_deposit_record(self, db: AsyncSession, wallet_id: int, transfer_info: Dict[str, Any], block: Dict[str, Any]):
        """입금 기록 생성"""
        try:
            # 지갑 정보 조회
            wallet_result = await db.execute(
                select(Wallet).filter(Wallet.id == wallet_id)
            )
            wallet = wallet_result.scalar_one()
            
            # 입금 기록 생성
            deposit = Deposit(
                user_id=wallet.user_id,
                wallet_id=wallet_id,
                tx_hash=transfer_info["tx_hash"],
                from_address=transfer_info["from"],
                to_address=transfer_info["to"],
                amount=transfer_info["amount"],
                token="USDT",
                status=DepositStatus.DETECTED,
                confirmations=0,
                required_confirmations=self._get_required_confirmations(transfer_info["amount"]),
                block_number=block["block_header"]["raw_data"]["number"],
                block_timestamp=datetime.fromtimestamp(block["block_header"]["raw_data"]["timestamp"] / 1000),
                raw_data=transfer_info["raw_data"]
            )
            
            db.add(deposit)
            await db.commit()
            
            logger.info(f"New deposit detected: {transfer_info['amount']} USDT to {transfer_info['to']}")
            
            # 알림 전송
            await alert_service.send_alert(
                "New Deposit Detected",
                f"Amount: {transfer_info['amount']} USDT\n"
                f"From: {transfer_info['from']}\n"
                f"To: {transfer_info['to']}\n"
                f"TX: {transfer_info['tx_hash']}",
                AlertLevel.INFO,
                "new_deposit"
            )
            
        except Exception as e:
            logger.error(f"Error creating deposit record: {e}")
            await db.rollback()
    
    def _get_required_confirmations(self, amount: Decimal) -> int:
        """금액에 따른 필요 확인 수 결정"""
        if amount < 100:
            return 10
        elif amount < 1000:
            return 20
        elif amount < 10000:
            return 30
        else:
            return 60
    
    async def _confirmation_loop(self):
        """확인 수 업데이트 루프"""
        while self.is_running:
            try:
                await self._update_confirmations()
                await asyncio.sleep(30)  # 30초마다 확인
            except Exception as e:
                logger.error(f"Error in confirmation loop: {e}")
                await asyncio.sleep(60)
    
    async def _update_confirmations(self):
        """확인 수 업데이트"""
        async with AsyncSessionLocal() as db:
            # 미확정 입금 조회
            result = await db.execute(
                select(Deposit).filter(
                    Deposit.status.in_([DepositStatus.DETECTED, DepositStatus.CONFIRMING])
                )
            )
            pending_deposits = result.scalars().all()
            
            if not pending_deposits:
                return
            
            current_block = await self.tron.get_latest_block_number()
            
            for deposit in pending_deposits:
                if deposit.block_number:
                    # 확인 수 업데이트
                    deposit.confirmations = current_block - deposit.block_number
                    
                    # 상태 업데이트
                    if deposit.confirmations >= deposit.required_confirmations:
                        if deposit.status != DepositStatus.CONFIRMED:
                            deposit.status = DepositStatus.CONFIRMED
                            deposit.confirmed_at = datetime.utcnow()
                            logger.info(f"Deposit confirmed: {deposit.tx_hash}")
                            
                            # 잔고 반영
                            await self._credit_deposit(db, deposit)
                    elif deposit.confirmations > 0:
                        deposit.status = DepositStatus.CONFIRMING
            
            await db.commit()
    
    async def _credit_deposit(self, db: AsyncSession, deposit: Deposit):
        """입금을 사용자 잔고에 반영"""
        try:
            if deposit.status != DepositStatus.CONFIRMED or deposit.credited_at:
                return
            
            # 잔고 서비스를 통해 잔고 증가
            balance_service = BalanceService(db)
            await balance_service.adjust_balance(
                user_id=deposit.user_id,
                amount=deposit.amount,
                adjustment_type="deposit",
                description=f"Deposit from {deposit.from_address}",
                admin_id=0  # 시스템 자동 처리
            )
            
            # 입금 상태 업데이트
            deposit.status = DepositStatus.CREDITED
            deposit.credited_at = datetime.utcnow()
            
            # 트랜잭션 기록 업데이트 (reference로 tx_hash 사용)
            await db.execute(
                select(Transaction).filter(
                    Transaction.reference_id == deposit.tx_hash
                ).update({"tx_hash": deposit.tx_hash})
            )
            
            logger.info(f"Deposit credited: {deposit.amount} USDT to user {deposit.user_id}")
            
            # 알림 전송
            await alert_service.send_alert(
                "Deposit Credited",
                f"Amount: {deposit.amount} USDT\n"
                f"User ID: {deposit.user_id}\n"
                f"TX: {deposit.tx_hash}",
                AlertLevel.INFO,
                "deposit_credited"
            )
            
        except Exception as e:
            logger.error(f"Error crediting deposit: {e}")
            deposit.status = DepositStatus.FAILED
            deposit.error_message = str(e)

# 글로벌 모니터 인스턴스
blockchain_monitor = BlockchainMonitor()
```

### 3. 입금 조회 엔드포인트 (app/api/v1/endpoints/deposits.py)

```python
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta

from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.models.deposit import Deposit, DepositStatus
from app.schemas.deposit import DepositResponse, DepositListResponse

router = APIRouter()

@router.get("/", response_model=DepositListResponse)
async def get_deposits(
    status: Optional[DepositStatus] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """사용자 입금 내역 조회"""
    query = select(Deposit).filter(Deposit.user_id == current_user.id)
    
    if status:
        query = query.filter(Deposit.status == status)
    
    query = query.order_by(Deposit.created_at.desc())
    
    # 전체 개수
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.execute(count_query)
    total = total.scalar()
    
    # 페이지네이션
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    deposits = result.scalars().all()
    
    return DepositListResponse(
        items=deposits,
        total=total,
        limit=limit,
        offset=offset
    )

@router.get("/{deposit_id}", response_model=DepositResponse)
async def get_deposit_detail(
    deposit_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """특정 입금 상세 조회"""
    result = await db.execute(
        select(Deposit).filter(
            and_(
                Deposit.id == deposit_id,
                Deposit.user_id == current_user.id
            )
        )
    )
    deposit = result.scalar_one_or_none()
    
    if not deposit:
        raise NotFoundError("Deposit not found")
    
    return deposit

@router.get("/admin/pending", response_model=List[DepositResponse])
async def get_pending_deposits(
    current_user: User = Depends(deps.get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """미처리 입금 조회 (관리자)"""
    result = await db.execute(
        select(Deposit).filter(
            Deposit.status.in_([DepositStatus.DETECTED, DepositStatus.CONFIRMING])
        ).order_by(Deposit.created_at.desc())
    )
    
    return result.scalars().all()

@router.post("/admin/reprocess/{deposit_id}")
async def reprocess_deposit(
    deposit_id: int,
    current_user: User = Depends(deps.get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """입금 재처리 (관리자)"""
    result = await db.execute(
        select(Deposit).filter(Deposit.id == deposit_id)
    )
    deposit = result.scalar_one_or_none()
    
    if not deposit:
        raise NotFoundError("Deposit not found")
    
    if deposit.status == DepositStatus.CREDITED:
        raise ValidationError("Deposit already credited")
    
    # 수동으로 잔고 반영
    from app.services.blockchain_monitor import blockchain_monitor
    await blockchain_monitor._credit_deposit(db, deposit)
    
    await db.commit()
    
    return {"message": "Deposit reprocessed successfully"}
```

### 4. 입금 스키마 (app/schemas/deposit.py)

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from app.models.deposit import DepositStatus

class DepositResponse(BaseModel):
    """입금 응답 스키마"""
    id: int
    user_id: int
    tx_hash: str
    from_address: str
    to_address: str
    amount: Decimal
    token: str
    status: DepositStatus
    confirmations: int
    required_confirmations: int
    block_number: Optional[int]
    block_timestamp: Optional[datetime]
    detected_at: datetime
    confirmed_at: Optional[datetime]
    credited_at: Optional[datetime]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True

class DepositListResponse(BaseModel):
    """입금 목록 응답"""
    items: List[DepositResponse]
    total: int
    limit: int
    offset: int
```

### 5. 백그라운드 태스크 업데이트 (app/core/background.py)

기존 파일에 블록체인 모니터 추가:

```python
async def startup(self):
    """애플리케이션 시작 시 태스크 실행"""
    from app.tasks.daily_report import DailyReportTask
    from app.services.blockchain_monitor import blockchain_monitor
    
    # 일일 리포트 태스크
    daily_report = DailyReportTask()
    self.add_task(daily_report.run_forever, "daily_report")
    
    # 블록체인 모니터 시작
    await blockchain_monitor.start()
```

### 6. 모델 업데이트 (app/models/__init__.py)

```python
from app.models.base import BaseModel
from app.models.user import User
from app.models.balance import Balance
from app.models.transaction import Transaction, TransactionType, TransactionStatus, TransactionDirection
from app.models.wallet import Wallet
from app.models.deposit import Deposit, DepositStatus

__all__ = [
    "BaseModel", "User", "Balance", "Transaction", "Wallet", "Deposit",
    "TransactionType", "TransactionStatus", "TransactionDirection", "DepositStatus"
]
```

### 7. API 라우터 업데이트 (app/api/v1/api.py)

```python
from fastapi import APIRouter
from app.api.v1.endpoints import auth, balance, wallet, monitoring, deposits  # deposits 추가

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(balance.router, prefix="/balance", tags=["balance"])
api_router.include_router(wallet.router, prefix="/wallet", tags=["wallet"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(deposits.router, prefix="/deposits", tags=["deposits"])  # 추가

@api_router.get("/test")
async def test_endpoint():
    return {"message": "API v1 is working"}
```

### 8. 마이그레이션 생성

```bash
# Deposit 테이블 추가
poetry run alembic revision --autogenerate -m "Add deposit table"
poetry run alembic upgrade head
```

### 9. 입금 시뮬레이션 스크립트 (scripts/simulate_deposit.py)

```python
"""
테스트용 입금 시뮬레이션 스크립트
실제 테스트넷에서 USDT를 전송하는 대신 사용
"""
import asyncio
from decimal import Decimal
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.models.deposit import Deposit, DepositStatus
from app.models.wallet import Wallet
from sqlalchemy import select
import random
import string

async def simulate_deposit(user_email: str, amount: Decimal):
    """입금 시뮬레이션"""
    async with AsyncSessionLocal() as db:
        # 사용자 지갑 찾기
        from app.models.user import User
        user_result = await db.execute(
            select(User).filter(User.email == user_email)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            print(f"User {user_email} not found")
            return
        
        wallet_result = await db.execute(
            select(Wallet).filter(Wallet.user_id == user.id)
        )
        wallet = wallet_result.scalar_one_or_none()
        
        if not wallet:
            print(f"Wallet not found for user {user_email}")
            return
        
        # 가짜 트랜잭션 해시 생성
        tx_hash = ''.join(random.choices(string.ascii_lowercase + string.digits, k=64))
        from_address = "T" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=33))
        
        # 입금 기록 생성
        deposit = Deposit(
            user_id=user.id,
            wallet_id=wallet.id,
            tx_hash=tx_hash,
            from_address=from_address,
            to_address=wallet.address,
            amount=amount,
            token="USDT",
            status=DepositStatus.CONFIRMED,  # 바로 확인됨으로 설정
            confirmations=20,
            required_confirmations=20,
            block_number=1000000 + random.randint(1, 1000),
            block_timestamp=datetime.utcnow(),
            confirmed_at=datetime.utcnow()
        )
        
        db.add(deposit)
        await db.commit()
        
        print(f"Simulated deposit created: {amount} USDT to {wallet.address}")
        print(f"TX Hash: {tx_hash}")
        
        # 블록체인 모니터의 credit 함수 직접 호출
        from app.services.blockchain_monitor import blockchain_monitor
        await blockchain_monitor._credit_deposit(db, deposit)
        await db.commit()
        
        print("Deposit credited to user balance")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python simulate_deposit.py <email> <amount>")
        sys.exit(1)
    
    email = sys.argv[1]
    amount = Decimal(sys.argv[2])
    
    asyncio.run(simulate_deposit(email, amount))
```

### 10. 입금 테스트 (tests/test_deposits.py)

```python
import pytest
from httpx import AsyncClient
from decimal import Decimal
from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.wallet import Wallet
from app.models.deposit import Deposit, DepositStatus
from sqlalchemy import select

async def create_test_user_with_wallet(email: str):
    """테스트용 사용자와 지갑 생성"""
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
        
        # 이메일 인증
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).filter(User.email == email))
            user = result.scalar_one()
            user.is_verified = True
            await db.commit()
        
        # 로그인
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Test123!@#"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 지갑 생성
        await client.post("/api/v1/wallet/create", headers=headers)
        
        return headers

@pytest.mark.asyncio
async def test_deposit_detection():
    """입금 감지 테스트"""
    headers = await create_test_user_with_wallet("deposit_test@example.com")
    
    # 사용자 정보 가져오기
    async with AsyncSessionLocal() as db:
        user_result = await db.execute(
            select(User).filter(User.email == "deposit_test@example.com")
        )
        user = user_result.scalar_one()
        
        wallet_result = await db.execute(
            select(Wallet).filter(Wallet.user_id == user.id)
        )
        wallet = wallet_result.scalar_one()
        
        # 테스트 입금 생성
        deposit = Deposit(
            user_id=user.id,
            wallet_id=wallet.id,
            tx_hash="test_tx_hash_123",
            from_address="TExternalAddress123",
            to_address=wallet.address,
            amount=Decimal("100.0"),
            token="USDT",
            status=DepositStatus.DETECTED,
            confirmations=0,
            required_confirmations=10,
            block_number=1000000
        )
        db.add(deposit)
        await db.commit()
    
    # 입금 내역 조회
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/deposits/", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["tx_hash"] == "test_tx_hash_123"
    assert data["items"][0]["status"] == "detected"

@pytest.mark.asyncio
async def test_deposit_list_pagination():
    """입금 목록 페이지네이션 테스트"""
    headers = await create_test_user_with_wallet("pagination_test@example.com")
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/deposits/?limit=10&offset=0",
            headers=headers
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["limit"] == 10
    assert data["offset"] == 0

@pytest.mark.asyncio
async def test_deposit_status_filter():
    """입금 상태 필터 테스트"""
    headers = await create_test_user_with_wallet("filter_test@example.com")
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/deposits/?status=confirmed",
            headers=headers
        )
    
    assert response.status_code == 200
    data = response.json()
    # 확인된 입금만 반환되어야 함
    for item in data["items"]:
        assert item["status"] == "confirmed"
```

### 11. 의존성 추가 (pyproject.toml)

```toml
# dependencies 섹션에 추가
tronpy = {extras = ["async"], version = "^0.4.0"}
```

## 실행 및 검증

1. 의존성 설치:
   ```bash
   poetry add "tronpy[async]"
   ```

2. 마이그레이션 실행:
   ```bash
   make db-upgrade
   ```

3. 서버 재시작:
   ```bash
   make dev
   ```

4. 입금 시뮬레이션 테스트:
   ```bash
   # 사용자 생성 후 지갑 생성
   # 그 다음 입금 시뮬레이션
   poetry run python scripts/simulate_deposit.py test@example.com 100
   ```

5. API 문서에서 입금 엔드포인트 확인:
   http://localhost:8000/api/v1/docs

## 검증 포인트

- [ ] 블록체인 모니터가 시작되는가?
- [ ] 입금이 감지되고 기록되는가?
- [ ] 확인 수가 업데이트되는가?
- [ ] 필요한 확인 수에 도달하면 잔고가 반영되는가?
- [ ] 입금 내역 조회가 작동하는가?
- [ ] 입금 알림이 전송되는가?
- [ ] 시뮬레이션 스크립트가 작동하는가?
- [ ] 에러 발생 시 적절히 처리되는가?

## 주의사항

- 이것은 **테스트넷** 구현입니다. 실제 메인넷에서는 추가 보안 조치가 필요합니다.
- 블록 재구성(reorg) 처리가 단순화되어 있습니다. 실제 운영에서는 더 정교한 처리가 필요합니다.
- 대량의 트랜잭션 처리를 위해서는 성능 최적화가 필요합니다.

이 문서를 완료하면 TRON 블록체인에서 USDT 입금을 자동으로 감지하고 사용자 잔고에 반영하는 시스템이 구축됩니다.