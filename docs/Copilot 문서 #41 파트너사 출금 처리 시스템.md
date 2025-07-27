# Copilot 문서 #41: 파트너사 출금 처리 시스템 - 백엔드

## 목표

파트너사의 출금 요청을 효율적으로 관리하고, 본사의 에너지 대납 시스템과 원활하게 연동되는 출금 처리 백엔드 시스템을 구축합니다.

## 전제 조건

- Copilot 문서 #40 (에너지 풀 관리 시스템)이 완료되어 있어야 합니다
- 파트너사 관리 시스템이 구현되어 있어야 합니다
- 파트너사 핫/콜드 월렛 구조가 설정되어 있어야 합니다

## 🎯 시스템 구조

### 출금 처리 워크플로우

1. **사용자 출금 요청** → 파트너사 검토
2. **출금 승인** → 출금 큐 등록
3. **콜드→핫 월렛 자금 이동** → 준비 완료
4. **에너지 요청** → 본사 API 호출
5. **TRX 송금** → 에너지 비용 지불
6. **에너지 수신** → 출금 가능 상태
7. **USDT 전송** → 트랜잭션 서명 및 실행
8. **완료 확인** → 상태 업데이트

### 출금 유형

- **즉시 출금**: 30분 이내 처리
- **일반 출금**: 2시간 이내 처리
- **정기 출금**: 지정 시간 배치 처리

## 🛠️ 구현 단계

### Phase 1: 데이터베이스 모델 설계

### 1.1 출금 큐 모델

```python
# app/models/withdrawal_queue.py
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from decimal import Decimal
from datetime import datetime
import enum

class WithdrawalType(enum.Enum):
    """출금 유형"""
    IMMEDIATE = "immediate"      # 즉시 출금 (30분 이내)
    REGULAR = "regular"         # 일반 출금 (2시간 이내)
    SCHEDULED = "scheduled"     # 정기 출금 (지정 시간)

class WithdrawalStatus(enum.Enum):
    """출금 상태"""
    PENDING = "pending"              # 대기 중
    APPROVED = "approved"            # 승인됨
    QUEUED = "queued"               # 큐 등록
    WALLET_FUNDED = "wallet_funded"  # 자금 준비 완료
    ENERGY_REQUESTED = "energy_requested"  # 에너지 요청됨
    ENERGY_RECEIVED = "energy_received"    # 에너지 수신됨
    PROCESSING = "processing"        # 처리 중
    SIGNING = "signing"             # 서명 대기
    COMPLETED = "completed"         # 완료
    FAILED = "failed"              # 실패
    CANCELLED = "cancelled"        # 취소됨

class WithdrawalQueue(Base):
    """출금 대기열"""
    __tablename__ = "withdrawal_queue"

    id = Column(Integer, primary_key=True)
    withdrawal_id = Column(String(32), unique=True, nullable=False, index=True)

    # 파트너 및 사용자 정보
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 출금 정보
    withdrawal_type = Column(Enum(WithdrawalType), nullable=False)
    amount_usdt = Column(Numeric(20, 6), nullable=False)
    to_address = Column(String(34), nullable=False)
    memo = Column(String(255))

    # 우선순위 및 배치
    priority = Column(Integer, default=0)  # 낮을수록 우선
    batch_id = Column(String(32), index=True)
    batch_position = Column(Integer)

    # 에너지 관련
    energy_required = Column(Integer)
    energy_allocated = Column(Boolean, default=False)
    energy_allocation_id = Column(Integer, ForeignKey("energy_allocations.id"))

    # 상태 관리
    status = Column(Enum(WithdrawalStatus), default=WithdrawalStatus.PENDING)
    error_message = Column(String(500))
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime)
    queued_at = Column(DateTime)
    processing_started_at = Column(DateTime)
    completed_at = Column(DateTime)
    scheduled_for = Column(DateTime)  # 정기 출금용

    # 트랜잭션 정보
    funding_tx_hash = Column(String(64))  # 콜드→핫 월렛 이동
    withdrawal_tx_hash = Column(String(64))  # 실제 출금

    # 인덱스
    __table_args__ = (
        Index('idx_partner_status', 'partner_id', 'status'),
        Index('idx_batch_processing', 'batch_id', 'status'),
        Index('idx_scheduled_withdrawals', 'scheduled_for', 'status'),
    )

    # 관계
    partner = relationship("Partner", back_populates="withdrawal_queues")
    user = relationship("User", back_populates="withdrawal_queues")
    energy_allocation = relationship("EnergyAllocation", back_populates="withdrawal_queue")

```

### 1.2 파트너사 지갑 모델

```python
# app/models/partner_wallet.py
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import enum

class WalletType(enum.Enum):
    """지갑 유형"""
    HOT = "hot"      # 핫 월렛 (출금 운영용)
    COLD = "cold"    # 콜드 월렛 (자금 보관용)

class PartnerWallet(Base):
    """파트너사 지갑"""
    __tablename__ = "partner_wallets"

    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    wallet_type = Column(Enum(WalletType), nullable=False)

    # 지갑 정보
    address = Column(String(34), unique=True, nullable=False)
    label = Column(String(100))

    # 잔액 정보
    usdt_balance = Column(Numeric(20, 6), default=0)
    trx_balance = Column(Numeric(20, 6), default=0)

    # 에너지 정보
    current_energy = Column(Integer, default=0)
    energy_limit = Column(Integer)
    last_energy_update = Column(DateTime)

    # 자동 충전 설정
    auto_sweep_enabled = Column(Boolean, default=True)
    sweep_threshold_usdt = Column(Numeric(20, 6), default=1000)

    auto_energy_recharge = Column(Boolean, default=True)
    energy_threshold = Column(Integer, default=100000)

    # 상태
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    partner = relationship("Partner", back_populates="wallets")
    wallet_transactions = relationship("WalletTransaction", back_populates="wallet")

```

### 1.3 출금 배치 모델

```python
# app/models/withdrawal_batch.py
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
import enum

class BatchStatus(enum.Enum):
    """배치 상태"""
    CREATED = "created"          # 생성됨
    PROCESSING = "processing"    # 처리 중
    COMPLETED = "completed"      # 완료
    PARTIAL = "partial"         # 부분 완료
    FAILED = "failed"           # 실패

class WithdrawalBatch(Base):
    """출금 배치"""
    __tablename__ = "withdrawal_batches"

    id = Column(Integer, primary_key=True)
    batch_id = Column(String(32), unique=True, nullable=False)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)

    # 배치 정보
    total_withdrawals = Column(Integer, default=0)
    total_amount_usdt = Column(Numeric(20, 6), default=0)
    total_energy_required = Column(Integer, default=0)

    # 에너지 비용
    energy_cost_trx = Column(Numeric(20, 6))
    saas_fee_trx = Column(Numeric(20, 6))
    total_cost_trx = Column(Numeric(20, 6))

    # 처리 정보
    processed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)

    # 상태
    status = Column(Enum(BatchStatus), default=BatchStatus.CREATED)

    # 메타데이터
    metadata = Column(JSON)  # 추가 정보 저장

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    processing_started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # 관계
    partner = relationship("Partner", back_populates="withdrawal_batches")
    withdrawals = relationship("WithdrawalQueue",
                             foreign_keys="[WithdrawalQueue.batch_id]",
                             primaryjoin="WithdrawalQueue.batch_id==WithdrawalBatch.batch_id")

```

### Phase 2: 출금 처리 서비스

### 2.1 출금 큐 관리 서비스

```python
# app/services/withdrawal/queue_manager.py
from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models import (
    WithdrawalQueue, WithdrawalStatus, WithdrawalType,
    PartnerWallet, WalletType, Partner
)
from app.core.config import settings
from app.utils.id_generator import generate_withdrawal_id
import logging

logger = logging.getLogger(__name__)

class WithdrawalQueueManager:
    """출금 큐 관리자"""

    def __init__(self, db: Session):
        self.db = db

    async def add_to_queue(
        self,
        partner_id: int,
        user_id: int,
        amount: Decimal,
        to_address: str,
        withdrawal_type: WithdrawalType,
        memo: Optional[str] = None,
        scheduled_for: Optional[datetime] = None
    ) -> WithdrawalQueue:
        """출금 요청을 큐에 추가"""
        try:
            # 우선순위 계산
            priority = self._calculate_priority(withdrawal_type, amount)

            # 출금 큐 생성
            withdrawal = WithdrawalQueue(
                withdrawal_id=generate_withdrawal_id(),
                partner_id=partner_id,
                user_id=user_id,
                withdrawal_type=withdrawal_type,
                amount_usdt=amount,
                to_address=to_address,
                memo=memo,
                priority=priority,
                scheduled_for=scheduled_for if withdrawal_type == WithdrawalType.SCHEDULED else None
            )

            # 에너지 필요량 계산
            withdrawal.energy_required = self._calculate_energy_required(amount, to_address)

            self.db.add(withdrawal)
            self.db.commit()
            self.db.refresh(withdrawal)

            logger.info(f"출금 요청 큐 추가: {withdrawal.withdrawal_id}")

            # 즉시 출금인 경우 자동 승인 처리
            if withdrawal_type == WithdrawalType.IMMEDIATE:
                await self.approve_withdrawal(withdrawal.id)

            return withdrawal

        except Exception as e:
            logger.error(f"출금 큐 추가 실패: {e}")
            self.db.rollback()
            raise

    async def approve_withdrawal(self, withdrawal_id: int) -> bool:
        """출금 승인"""
        try:
            withdrawal = self.db.query(WithdrawalQueue).filter(
                WithdrawalQueue.id == withdrawal_id
            ).first()

            if not withdrawal:
                raise ValueError("출금 요청을 찾을 수 없습니다")

            if withdrawal.status != WithdrawalStatus.PENDING:
                raise ValueError(f"승인할 수 없는 상태입니다: {withdrawal.status}")

            withdrawal.status = WithdrawalStatus.APPROVED
            withdrawal.approved_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"출금 승인: {withdrawal.withdrawal_id}")

            # 자동으로 큐에 등록
            await self.queue_for_processing(withdrawal.id)

            return True

        except Exception as e:
            logger.error(f"출금 승인 실패: {e}")
            self.db.rollback()
            raise

    async def queue_for_processing(self, withdrawal_id: int) -> bool:
        """처리를 위해 큐에 등록"""
        try:
            withdrawal = self.db.query(WithdrawalQueue).filter(
                WithdrawalQueue.id == withdrawal_id
            ).first()

            if withdrawal.status != WithdrawalStatus.APPROVED:
                raise ValueError("승인된 출금만 큐에 등록할 수 있습니다")

            withdrawal.status = WithdrawalStatus.QUEUED
            withdrawal.queued_at = datetime.utcnow()

            self.db.commit()

            # 배치 할당 체크
            await self._check_batch_assignment(withdrawal)

            return True

        except Exception as e:
            logger.error(f"큐 등록 실패: {e}")
            self.db.rollback()
            raise

    async def get_pending_withdrawals(
        self,
        partner_id: int,
        limit: int = 100
    ) -> List[WithdrawalQueue]:
        """대기 중인 출금 조회"""
        try:
            now = datetime.utcnow()

            withdrawals = self.db.query(WithdrawalQueue).filter(
                WithdrawalQueue.partner_id == partner_id,
                WithdrawalQueue.status == WithdrawalStatus.QUEUED,
                or_(
                    WithdrawalQueue.withdrawal_type != WithdrawalType.SCHEDULED,
                    and_(
                        WithdrawalQueue.withdrawal_type == WithdrawalType.SCHEDULED,
                        WithdrawalQueue.scheduled_for <= now
                    )
                )
            ).order_by(
                WithdrawalQueue.priority,
                WithdrawalQueue.created_at
            ).limit(limit).all()

            return withdrawals

        except Exception as e:
            logger.error(f"대기 출금 조회 실패: {e}")
            raise

    def _calculate_priority(
        self,
        withdrawal_type: WithdrawalType,
        amount: Decimal
    ) -> int:
        """출금 우선순위 계산"""
        base_priority = {
            WithdrawalType.IMMEDIATE: 0,
            WithdrawalType.REGULAR: 10,
            WithdrawalType.SCHEDULED: 20
        }

        priority = base_priority.get(withdrawal_type, 10)

        # 금액별 우선순위 조정
        if amount >= 10000:
            priority -= 1
        elif amount >= 50000:
            priority -= 2

        return max(0, priority)

    def _calculate_energy_required(
        self,
        amount: Decimal,
        to_address: str
    ) -> int:
        """필요 에너지 계산"""
        # 기본 USDT 전송 에너지
        base_energy = 31895

        # TODO: 수신자가 처음 USDT를 받는지 확인
        # 현재는 보수적으로 첫 수신으로 가정
        first_time_energy = 15000

        return base_energy + first_time_energy

    async def _check_batch_assignment(self, withdrawal: WithdrawalQueue):
        """배치 할당 확인"""
        # 즉시 출금은 개별 처리
        if withdrawal.withdrawal_type == WithdrawalType.IMMEDIATE:
            return

        # 동일 시간대 출금 찾기
        similar_withdrawals = self.db.query(WithdrawalQueue).filter(
            WithdrawalQueue.partner_id == withdrawal.partner_id,
            WithdrawalQueue.status == WithdrawalStatus.QUEUED,
            WithdrawalQueue.withdrawal_type == withdrawal.withdrawal_type,
            WithdrawalQueue.batch_id.is_(None)
        ).all()

        # 배치 생성 조건 확인 (10건 이상 또는 총액 10,000 USDT 이상)
        if len(similar_withdrawals) >= 10 or \
           sum(w.amount_usdt for w in similar_withdrawals) >= 10000:
            await self._create_batch(similar_withdrawals)

```

### 2.2 출금 배치 처리 서비스

```python
# app/services/withdrawal/batch_processor.py
from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import (
    WithdrawalQueue, WithdrawalBatch, BatchStatus,
    PartnerWallet, WalletType
)
from app.services.energy import EnergyAllocationService
from app.utils.id_generator import generate_batch_id
import logging

logger = logging.getLogger(__name__)

class WithdrawalBatchProcessor:
    """출금 배치 처리자"""

    def __init__(self, db: Session):
        self.db = db
        self.energy_service = EnergyAllocationService(db)

    async def create_withdrawal_batch(
        self,
        partner_id: int,
        withdrawal_ids: List[int]
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
                raise ValueError("유효한 출금 요청이 없습니다")

            # 배치 ID 생성
            batch_id = generate_batch_id()

            # 배치 생성
            batch = WithdrawalBatch(
                batch_id=batch_id,
                partner_id=partner_id,
                total_withdrawals=len(withdrawals),
                total_amount_usdt=sum(w.amount_usdt for w in withdrawals),
                total_energy_required=sum(w.energy_required for w in withdrawals)
            )

            self.db.add(batch)

            # 출금 요청에 배치 ID 할당
            for idx, withdrawal in enumerate(withdrawals):
                withdrawal.batch_id = batch_id
                withdrawal.batch_position = idx

            self.db.commit()
            self.db.refresh(batch)

            logger.info(f"출금 배치 생성: {batch_id}, {len(withdrawals)}건")

            return batch

        except Exception as e:
            logger.error(f"배치 생성 실패: {e}")
            self.db.rollback()
            raise

    async def optimize_batch(
        self,
        batch_id: str
    ) -> Dict:
        """배치 최적화"""
        try:
            batch = self.db.query(WithdrawalBatch).filter(
                WithdrawalBatch.batch_id == batch_id
            ).first()

            if not batch:
                raise ValueError("배치를 찾을 수 없습니다")

            withdrawals = self.db.query(WithdrawalQueue).filter(
                WithdrawalQueue.batch_id == batch_id
            ).order_by(WithdrawalQueue.batch_position).all()

            # 최적화 수행
            optimized_groups = self._optimize_withdrawal_order(withdrawals)

            # 에너지 절약 계산
            original_energy = sum(w.energy_required for w in withdrawals)
            optimized_energy = self._calculate_optimized_energy(optimized_groups)
            saved_energy = original_energy - optimized_energy

            # 배치 업데이트
            batch.total_energy_required = optimized_energy
            batch.metadata = {
                "optimization": {
                    "original_energy": original_energy,
                    "optimized_energy": optimized_energy,
                    "saved_energy": saved_energy,
                    "groups": len(optimized_groups)
                }
            }

            self.db.commit()

            return {
                "batch_id": batch_id,
                "original_energy": original_energy,
                "optimized_energy": optimized_energy,
                "saved_energy": saved_energy,
                "saved_percentage": (saved_energy / original_energy * 100) if original_energy > 0 else 0
            }

        except Exception as e:
            logger.error(f"배치 최적화 실패: {e}")
            raise

    async def request_energy_for_batch(
        self,
        batch_id: str
    ) -> Dict:
        """배치에 필요한 에너지 요청"""
        try:
            batch = self.db.query(WithdrawalBatch).filter(
                WithdrawalBatch.batch_id == batch_id
            ).first()

            if not batch:
                raise ValueError("배치를 찾을 수 없습니다")

            # 파트너 핫 월렛 조회
            hot_wallet = self.db.query(PartnerWallet).filter(
                PartnerWallet.partner_id == batch.partner_id,
                PartnerWallet.wallet_type == WalletType.HOT
            ).first()

            if not hot_wallet:
                raise ValueError("핫 월렛이 설정되지 않았습니다")

            # 에너지 계산 요청 (본사 API)
            energy_result = await self.energy_service.calculate_batch_energy(
                partner_id=batch.partner_id,
                energy_amount=batch.total_energy_required,
                withdrawal_count=batch.total_withdrawals
            )

            # 배치에 비용 정보 저장
            batch.energy_cost_trx = energy_result['base_cost_trx']
            batch.saas_fee_trx = energy_result['saas_fee_trx']
            batch.total_cost_trx = energy_result['total_cost_trx']

            self.db.commit()

            logger.info(f"배치 에너지 비용 계산 완료: {batch_id}")

            return {
                "batch_id": batch_id,
                "energy_required": batch.total_energy_required,
                "total_cost_trx": float(batch.total_cost_trx),
                "hot_wallet_address": hot_wallet.address,
                "payment_required": True
            }

        except Exception as e:
            logger.error(f"에너지 요청 실패: {e}")
            raise

    async def process_batch(
        self,
        batch_id: str
    ) -> Dict:
        """배치 처리 실행"""
        try:
            batch = self.db.query(WithdrawalBatch).filter(
                WithdrawalBatch.batch_id == batch_id
            ).first()

            if not batch:
                raise ValueError("배치를 찾을 수 없습니다")

            if batch.status != BatchStatus.CREATED:
                raise ValueError(f"처리할 수 없는 배치 상태: {batch.status}")

            # 상태 업데이트
            batch.status = BatchStatus.PROCESSING
            batch.processing_started_at = datetime.utcnow()
            self.db.commit()

            # 출금 요청들 처리
            withdrawals = self.db.query(WithdrawalQueue).filter(
                WithdrawalQueue.batch_id == batch_id
            ).order_by(WithdrawalQueue.batch_position).all()

            processed = 0
            failed = 0

            for withdrawal in withdrawals:
                try:
                    await self._process_single_withdrawal(withdrawal)
                    processed += 1
                except Exception as e:
                    logger.error(f"출금 처리 실패: {withdrawal.withdrawal_id}, {e}")
                    withdrawal.status = WithdrawalStatus.FAILED
                    withdrawal.error_message = str(e)
                    failed += 1

            # 배치 상태 업데이트
            batch.processed_count = processed
            batch.failed_count = failed

            if failed == 0:
                batch.status = BatchStatus.COMPLETED
            elif processed == 0:
                batch.status = BatchStatus.FAILED
            else:
                batch.status = BatchStatus.PARTIAL

            batch.completed_at = datetime.utcnow()
            self.db.commit()

            return {
                "batch_id": batch_id,
                "total": batch.total_withdrawals,
                "processed": processed,
                "failed": failed,
                "status": batch.status.value
            }

        except Exception as e:
            logger.error(f"배치 처리 실패: {e}")
            if batch:
                batch.status = BatchStatus.FAILED
                self.db.commit()
            raise

    def _optimize_withdrawal_order(
        self,
        withdrawals: List[WithdrawalQueue]
    ) -> List[List[WithdrawalQueue]]:
        """출금 순서 최적화 (동일 주소 그룹핑)"""
        groups = {}

        for withdrawal in withdrawals:
            if withdrawal.to_address not in groups:
                groups[withdrawal.to_address] = []
            groups[withdrawal.to_address].append(withdrawal)

        # 그룹 크기순 정렬 (큰 그룹 먼저)
        sorted_groups = sorted(
            groups.values(),
            key=lambda g: len(g),
            reverse=True
        )

        return sorted_groups

    def _calculate_optimized_energy(
        self,
        groups: List[List[WithdrawalQueue]]
    ) -> int:
        """최적화된 에너지 계산"""
        total_energy = 0

        for group in groups:
            # 첫 번째 전송
            total_energy += 31895 + 15000  # 기본 + 첫 수신

            # 추가 전송 (같은 주소로는 첫 수신 에너지 불필요)
            if len(group) > 1:
                total_energy += 31895 * (len(group) - 1)

        return total_energy

```

### 2.3 지갑 자금 관리 서비스

```python
# app/services/withdrawal/wallet_funding_service.py
from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import (
    PartnerWallet, WalletType, WalletTransaction,
    TransactionType, WithdrawalQueue
)
from app.services.tron import TronService
import logging

logger = logging.getLogger(__name__)

class WalletFundingService:
    """지갑 자금 관리 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.tron_service = TronService()

    async def check_hot_wallet_balance(
        self,
        partner_id: int
    ) -> Dict:
        """핫 월렛 잔액 확인"""
        try:
            hot_wallet = self.db.query(PartnerWallet).filter(
                PartnerWallet.partner_id == partner_id,
                PartnerWallet.wallet_type == WalletType.HOT
            ).first()

            if not hot_wallet:
                raise ValueError("핫 월렛이 설정되지 않았습니다")

            # 블록체인에서 실시간 잔액 조회
            balance_info = await self.tron_service.get_account_balance(hot_wallet.address)

            # DB 업데이트
            hot_wallet.usdt_balance = Decimal(str(balance_info['usdt']))
            hot_wallet.trx_balance = Decimal(str(balance_info['trx']))

            # 에너지 정보 업데이트
            resources = await self.tron_service.get_account_resources(hot_wallet.address)
            hot_wallet.current_energy = resources['EnergyLimit'] - resources['EnergyUsed']
            hot_wallet.last_energy_update = datetime.utcnow()

            self.db.commit()

            return {
                "address": hot_wallet.address,
                "usdt_balance": float(hot_wallet.usdt_balance),
                "trx_balance": float(hot_wallet.trx_balance),
                "current_energy": hot_wallet.current_energy,
                "energy_limit": resources['EnergyLimit']
            }

        except Exception as e:
            logger.error(f"핫 월렛 잔액 확인 실패: {e}")
            raise

    async def fund_hot_wallet(
        self,
        partner_id: int,
        amount_usdt: Decimal
    ) -> Dict:
        """콜드 월렛에서 핫 월렛으로 자금 이동"""
        try:
            # 지갑 조회
            cold_wallet = self.db.query(PartnerWallet).filter(
                PartnerWallet.partner_id == partner_id,
                PartnerWallet.wallet_type == WalletType.COLD
            ).first()

            hot_wallet = self.db.query(PartnerWallet).filter(
                PartnerWallet.partner_id == partner_id,
                PartnerWallet.wallet_type == WalletType.HOT
            ).first()

            if not cold_wallet or not hot_wallet:
                raise ValueError("콜드/핫 월렛이 설정되지 않았습니다")

            # 콜드 월렛 잔액 확인
            cold_balance = await self.tron_service.get_account_balance(cold_wallet.address)
            if Decimal(str(cold_balance['usdt'])) < amount_usdt:
                raise ValueError("콜드 월렛 잔액 부족")

            # USDT 전송 트랜잭션 생성 (파트너가 서명해야 함)
            transfer_data = await self.tron_service.create_usdt_transfer(
                from_address=cold_wallet.address,
                to_address=hot_wallet.address,
                amount=amount_usdt
            )

            # 트랜잭션 기록
            wallet_tx = WalletTransaction(
                partner_id=partner_id,
                transaction_type=TransactionType.COLD_TO_HOT,
                from_wallet_id=cold_wallet.id,
                to_wallet_id=hot_wallet.id,
                amount_usdt=amount_usdt,
                tx_data=transfer_data['unsigned_tx'],
                status="pending_signature"
            )

            self.db.add(wallet_tx)
            self.db.commit()

            logger.info(f"자금 이동 트랜잭션 생성: {amount_usdt} USDT")

            return {
                "transaction_id": wallet_tx.id,
                "from": cold_wallet.address,
                "to": hot_wallet.address,
                "amount": float(amount_usdt),
                "unsigned_tx": transfer_data['unsigned_tx'],
                "message": "트랜잭션 서명이 필요합니다"
            }

        except Exception as e:
            logger.error(f"자금 이동 실패: {e}")
            self.db.rollback()
            raise

    async def check_funding_requirements(
        self,
        withdrawal_ids: List[int]
    ) -> Dict:
        """출금에 필요한 자금 확인"""
        try:
            withdrawals = self.db.query(WithdrawalQueue).filter(
                WithdrawalQueue.id.in_(withdrawal_ids)
            ).all()

            if not withdrawals:
                return {"required_usdt": 0, "required_trx": 0}

            partner_id = withdrawals[0].partner_id

            # 필요 자금 계산
            total_usdt = sum(w.amount_usdt for w in withdrawals)

            # 핫 월렛 현재 잔액
            hot_wallet_balance = await self.check_hot_wallet_balance(partner_id)

            # 부족분 계산
            usdt_shortage = max(0, total_usdt - Decimal(str(hot_wallet_balance['usdt_balance'])))

            # TRX는 에너지 비용 계산 후 확인
            # (에너지 대납 서비스 사용 시 TRX는 본사에 지불)

            return {
                "total_required_usdt": float(total_usdt),
                "current_usdt_balance": hot_wallet_balance['usdt_balance'],
                "usdt_shortage": float(usdt_shortage),
                "funding_required": usdt_shortage > 0
            }

        except Exception as e:
            logger.error(f"자금 요구사항 확인 실패: {e}")
            raise

```

### Phase 3: 파트너 API 엔드포인트

### 3.1 출금 관리 API

```python
# app/api/v1/endpoints/partner/withdrawals.py
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from app.api import deps
from app.models import WithdrawalQueue, WithdrawalType, WithdrawalStatus
from app.schemas.withdrawal import (
    WithdrawalQueueCreate, WithdrawalQueueResponse,
    WithdrawalBatchCreate, WithdrawalBatchResponse,
    EnergyRequestResponse
)
from app.services.withdrawal import (
    WithdrawalQueueManager, WithdrawalBatchProcessor,
    WalletFundingService
)
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/queue", response_model=WithdrawalQueueResponse)
async def add_to_withdrawal_queue(
    withdrawal_data: WithdrawalQueueCreate,
    db: Session = Depends(deps.get_db),
    current_partner=Depends(deps.get_current_partner)
):
    """출금 요청을 큐에 추가"""
    try:
        queue_manager = WithdrawalQueueManager(db)

        withdrawal = await queue_manager.add_to_queue(
            partner_id=current_partner.id,
            user_id=withdrawal_data.user_id,
            amount=withdrawal_data.amount,
            to_address=withdrawal_data.to_address,
            withdrawal_type=withdrawal_data.withdrawal_type,
            memo=withdrawal_data.memo,
            scheduled_for=withdrawal_data.scheduled_for
        )

        return withdrawal

    except Exception as e:
        logger.error(f"출금 큐 추가 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/queue/pending", response_model=List[WithdrawalQueueResponse])
async def get_pending_withdrawals(
    limit: int = Query(100, le=500),
    withdrawal_type: Optional[WithdrawalType] = None,
    db: Session = Depends(deps.get_db),
    current_partner=Depends(deps.get_current_partner)
):
    """대기 중인 출금 목록 조회"""
    try:
        queue_manager = WithdrawalQueueManager(db)

        withdrawals = await queue_manager.get_pending_withdrawals(
            partner_id=current_partner.id,
            limit=limit
        )

        # 타입 필터링
        if withdrawal_type:
            withdrawals = [w for w in withdrawals if w.withdrawal_type == withdrawal_type]

        return withdrawals

    except Exception as e:
        logger.error(f"대기 출금 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch/create", response_model=WithdrawalBatchResponse)
async def create_withdrawal_batch(
    batch_data: WithdrawalBatchCreate,
    db: Session = Depends(deps.get_db),
    current_partner=Depends(deps.get_current_partner)
):
    """출금 배치 생성"""
    try:
        batch_processor = WithdrawalBatchProcessor(db)

        batch = await batch_processor.create_withdrawal_batch(
            partner_id=current_partner.id,
            withdrawal_ids=batch_data.withdrawal_ids
        )

        # 배치 최적화
        optimization_result = await batch_processor.optimize_batch(batch.batch_id)

        return {
            "batch": batch,
            "optimization": optimization_result
        }

    except Exception as e:
        logger.error(f"배치 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/energy/request", response_model=EnergyRequestResponse)
async def request_energy_for_withdrawals(
    batch_id: Optional[str] = None,
    withdrawal_ids: Optional[List[int]] = None,
    db: Session = Depends(deps.get_db),
    current_partner=Depends(deps.get_current_partner)
):
    """출금을 위한 에너지 요청"""
    try:
        if batch_id:
            # 배치 에너지 요청
            batch_processor = WithdrawalBatchProcessor(db)
            result = await batch_processor.request_energy_for_batch(batch_id)

        elif withdrawal_ids:
            # 개별 출금 에너지 요청
            from app.services.energy import EnergyCalculationService
            calc_service = EnergyCalculationService(db)

            withdrawals = db.query(WithdrawalQueue).filter(
                WithdrawalQueue.id.in_(withdrawal_ids),
                WithdrawalQueue.partner_id == current_partner.id
            ).all()

            if not withdrawals:
                raise ValueError("유효한 출금 요청이 없습니다")

            total_energy = sum(w.energy_required for w in withdrawals)

            result = await calc_service.calculate_energy_cost(
                partner_id=current_partner.id,
                energy_amount=total_energy,
                withdrawal_count=len(withdrawals)
            )
        else:
            raise ValueError("batch_id 또는 withdrawal_ids가 필요합니다")

        return result

    except Exception as e:
        logger.error(f"에너지 요청 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/wallet/balance")
async def get_wallet_balance(
    db: Session = Depends(deps.get_db),
    current_partner=Depends(deps.get_current_partner)
):
    """지갑 잔액 조회"""
    try:
        funding_service = WalletFundingService(db)
        balance = await funding_service.check_hot_wallet_balance(current_partner.id)

        return balance

    except Exception as e:
        logger.error(f"지갑 잔액 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/wallet/fund")
async def fund_hot_wallet(
    amount_usdt: Decimal,
    db: Session = Depends(deps.get_db),
    current_partner=Depends(deps.get_current_partner)
):
    """콜드→핫 월렛 자금 이동"""
    try:
        funding_service = WalletFundingService(db)
        result = await funding_service.fund_hot_wallet(
            partner_id=current_partner.id,
            amount_usdt=amount_usdt
        )

        return result

    except Exception as e:
        logger.error(f"자금 이동 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_withdrawal_stats(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(deps.get_db),
    current_partner=Depends(deps.get_current_partner)
):
    """출금 통계 조회"""
    try:
        query = db.query(WithdrawalQueue).filter(
            WithdrawalQueue.partner_id == current_partner.id
        )

        if start_date:
            query = query.filter(WithdrawalQueue.created_at >= start_date)
        if end_date:
            query = query.filter(WithdrawalQueue.created_at <= end_date)

        total_count = query.count()

        # 상태별 집계
        status_counts = {}
        for status in WithdrawalStatus:
            count = query.filter(WithdrawalQueue.status == status).count()
            status_counts[status.value] = count

        # 타입별 집계
        type_counts = {}
        for w_type in WithdrawalType:
            count = query.filter(WithdrawalQueue.withdrawal_type == w_type).count()
            type_counts[w_type.value] = count

        # 총액 계산
        from sqlalchemy import func
        total_amount = query.with_entities(
            func.sum(WithdrawalQueue.amount_usdt)
        ).scalar() or 0

        return {
            "total_count": total_count,
            "total_amount": float(total_amount),
            "status_breakdown": status_counts,
            "type_breakdown": type_counts
        }

    except Exception as e:
        logger.error(f"통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

```

### Phase 4: 출금 처리 자동화

### 4.1 출금 처리 워커

```python
# app/workers/withdrawal_processor.py
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import (
    WithdrawalQueue, WithdrawalStatus, WithdrawalType,
    PartnerWallet, WalletType
)
from app.services.withdrawal import WithdrawalQueueManager
from app.services.tron import TronService
from app.core.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

class WithdrawalProcessor:
    """출금 처리 워커"""

    def __init__(self):
        self.running = False
        self.tron_service = TronService()

    async def start(self):
        """워커 시작"""
        self.running = True
        logger.info("출금 처리 워커 시작")

        while self.running:
            try:
                await self.process_pending_withdrawals()
                await asyncio.sleep(30)  # 30초마다 체크

            except Exception as e:
                logger.error(f"출금 처리 워커 오류: {e}")
                await asyncio.sleep(60)

    async def process_pending_withdrawals(self):
        """대기 중인 출금 처리"""
        db = SessionLocal()
        try:
            # 처리 대상 출금 조회
            now = datetime.utcnow()

            withdrawals = db.query(WithdrawalQueue).filter(
                WithdrawalQueue.status == WithdrawalStatus.ENERGY_RECEIVED,
                or_(
                    # 즉시 출금
                    and_(
                        WithdrawalQueue.withdrawal_type == WithdrawalType.IMMEDIATE,
                        WithdrawalQueue.created_at <= now - timedelta(minutes=5)
                    ),
                    # 일반 출금
                    and_(
                        WithdrawalQueue.withdrawal_type == WithdrawalType.REGULAR,
                        WithdrawalQueue.created_at <= now - timedelta(hours=1)
                    ),
                    # 정기 출금
                    and_(
                        WithdrawalQueue.withdrawal_type == WithdrawalType.SCHEDULED,
                        WithdrawalQueue.scheduled_for <= now
                    )
                )
            ).limit(10).all()

            for withdrawal in withdrawals:
                await self.process_single_withdrawal(db, withdrawal)

        finally:
            db.close()

    async def process_single_withdrawal(
        self,
        db: Session,
        withdrawal: WithdrawalQueue
    ):
        """단일 출금 처리"""
        try:
            # 상태 업데이트
            withdrawal.status = WithdrawalStatus.PROCESSING
            withdrawal.processing_started_at = datetime.utcnow()
            db.commit()

            # 핫 월렛 조회
            hot_wallet = db.query(PartnerWallet).filter(
                PartnerWallet.partner_id == withdrawal.partner_id,
                PartnerWallet.wallet_type == WalletType.HOT
            ).first()

            if not hot_wallet:
                raise ValueError("핫 월렛이 설정되지 않았습니다")

            # USDT 전송 트랜잭션 생성
            tx_data = await self.tron_service.create_usdt_transfer(
                from_address=hot_wallet.address,
                to_address=withdrawal.to_address,
                amount=withdrawal.amount_usdt,
                memo=withdrawal.memo
            )

            # 서명 대기 상태로 변경
            withdrawal.status = WithdrawalStatus.SIGNING
            db.commit()

            logger.info(f"출금 트랜잭션 생성 완료: {withdrawal.withdrawal_id}")

            # TODO: 파트너에게 서명 요청 알림
            await self._notify_partner_for_signature(withdrawal, tx_data)

        except Exception as e:
            logger.error(f"출금 처리 실패: {withdrawal.withdrawal_id}, {e}")
            withdrawal.status = WithdrawalStatus.FAILED
            withdrawal.error_message = str(e)
            withdrawal.retry_count += 1
            db.commit()

            # 재시도 가능 여부 확인
            if withdrawal.retry_count < withdrawal.max_retries:
                await self._schedule_retry(withdrawal)

```

## 🧪 테스트 시나리오

### 1. 출금 큐 테스트

```python
# tests/test_withdrawal_queue.py
import pytest
from app.services.withdrawal import WithdrawalQueueManager

@pytest.mark.asyncio
async def test_withdrawal_queue_flow():
    """출금 큐 전체 플로우 테스트"""
    # 1. 출금 요청 생성
    # 2. 큐 등록
    # 3. 승인 처리
    # 4. 배치 할당
    # 5. 상태 변경 확인

```

### 2. 배치 최적화 테스트

```python
@pytest.mark.asyncio
async def test_batch_optimization():
    """배치 최적화 테스트"""
    # 1. 동일 주소 출금 생성
    # 2. 배치 생성
    # 3. 최적화 실행
    # 4. 에너지 절약 확인

```

### 3. 자금 이동 테스트

```python
@pytest.mark.asyncio
async def test_wallet_funding():
    """지갑 자금 이동 테스트"""
    # 1. 콜드 월렛 잔액 확인
    # 2. 자금 이동 요청
    # 3. 트랜잭션 생성 확인
    # 4. 서명 후 완료 확인

```

## 📋 체크리스트

### 기능 구현

- [ ]  출금 큐 모델 구현
- [ ]  파트너 지갑 모델 구현
- [ ]  출금 배치 모델 구현
- [ ]  큐 관리 서비스 구현
- [ ]  배치 처리 서비스 구현
- [ ]  자금 관리 서비스 구현
- [ ]  파트너 API 구현
- [ ]  출금 처리 워커 구현

### 최적화

- [ ]  동일 주소 그룹핑
- [ ]  에너지 사용 최적화
- [ ]  배치 크기 최적화
- [ ]  우선순위 큐 구현

### 모니터링

- [ ]  출금 상태 추적
- [ ]  처리 시간 모니터링
- [ ]  실패율 추적
- [ ]  자금 흐름 모니터링

## 🎉 기대 효과

1. **효율적 처리**: 배치 처리로 에너지 비용 절감
2. **유연한 정책**: 출금 유형별 차별화된 처리
3. **자동화**: 대부분의 프로세스 자동 처리
4. **투명성**: 모든 단계 추적 가능
5. **안정성**: 재시도 및 폴백 메커니즘

이 시스템을 통해 파트너사는 안정적이고 효율적인 출금 서비스를 제공할 수 있습니다!