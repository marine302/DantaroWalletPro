# Copilot 문서 #40: 본사 에너지 풀 관리 시스템 - 백엔드

## 목표

본사가 멀티 에너지 공급원(자체 스테이킹 + 외부 공급사)을 통합 관리하고, 최적 공급원을 자동으로 선택하여 파트너사에게 에너지를 제공하는 백엔드 시스템을 구축합니다.

## 전제 조건

- Copilot 문서 #1-39가 완료되어 있어야 합니다
- FastAPI 백엔드 시스템이 구동 중이어야 합니다
- PostgreSQL 데이터베이스가 설정되어 있어야 합니다
- TRON 네트워크 연동이 구현되어 있어야 합니다

## 🎯 시스템 구조

### 에너지 공급원 우선순위

1. **자체 스테이킹** (가장 저렴, 우선순위 1)
2. **TronZap** (외부 공급사 1, 우선순위 2)
3. **TronNRG** (외부 공급사 2, 우선순위 3)
4. **파트너사 직접 처리** (모든 공급원 실패 시)

### 핵심 기능

- 멀티 공급원 통합 관리
- 실시간 가용 에너지 모니터링
- 비용 최적화 알고리즘
- 자동 공급원 전환 (장애 대응)
- 파트너사별 에너지 할당 추적

## 🛠️ 구현 단계

### Phase 1: 데이터베이스 모델 설계

### 1.1 에너지 공급원 모델

```python
# app/models/energy_supplier.py
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, Enum, JSON, BigInteger
from sqlalchemy.orm import relationship
from decimal import Decimal
from datetime import datetime
import enum

class SupplierType(enum.Enum):
    """에너지 공급원 유형"""
    SELF_STAKING = "self_staking"      # 자체 스테이킹
    TRONZAP = "tronzap"                # TronZap API
    TRONNRG = "tronnrg"                # TronNRG API

class SupplierStatus(enum.Enum):
    """공급원 상태"""
    ACTIVE = "active"                   # 정상 작동
    INACTIVE = "inactive"               # 비활성화
    MAINTENANCE = "maintenance"         # 점검 중
    ERROR = "error"                     # 오류 상태

class EnergySupplier(Base):
    """에너지 공급원 정보"""
    __tablename__ = "energy_suppliers"

    id = Column(Integer, primary_key=True)
    supplier_type = Column(Enum(SupplierType), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    priority = Column(Integer, nullable=False, default=1)  # 낮을수록 우선순위 높음

    # 공급원 상태
    status = Column(Enum(SupplierStatus), default=SupplierStatus.ACTIVE)
    is_active = Column(Boolean, default=True)
    last_checked_at = Column(DateTime)
    last_error = Column(String(500))

    # 에너지 정보
    available_energy = Column(BigInteger, default=0)
    max_energy_capacity = Column(BigInteger)
    daily_energy_generation = Column(BigInteger)  # 자체 스테이킹용

    # 비용 정보
    cost_per_energy = Column(Numeric(20, 10), nullable=False)
    min_order_amount = Column(Integer, default=32000)  # 최소 주문 에너지
    max_order_amount = Column(Integer)  # 최대 주문 에너지

    # API 정보 (외부 공급사용)
    api_endpoint = Column(String(255))
    api_key = Column(String(255))
    api_secret = Column(String(255))
    webhook_url = Column(String(255))

    # 통계
    total_energy_supplied = Column(BigInteger, default=0)
    total_orders = Column(Integer, default=0)
    success_rate = Column(Numeric(5, 2), default=Decimal("100.00"))
    average_response_time = Column(Integer)  # milliseconds

    # 메타데이터
    config = Column(JSON)  # 공급원별 추가 설정
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    allocations = relationship("EnergyAllocation", back_populates="supplier")
    price_history = relationship("EnergySupplierPriceHistory", back_populates="supplier")

```

### 1.2 에너지 할당 모델

```python
# app/models/energy_allocation.py
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
import enum

class AllocationStatus(enum.Enum):
    """할당 상태"""
    PENDING = "pending"              # 대기 중
    PROCESSING = "processing"        # 처리 중
    COMPLETED = "completed"          # 완료
    FAILED = "failed"               # 실패
    CANCELLED = "cancelled"         # 취소됨
    FALLBACK = "fallback"           # 폴백 모드

class EnergyAllocation(Base):
    """에너지 할당 기록"""
    __tablename__ = "energy_allocations"

    id = Column(Integer, primary_key=True)
    allocation_id = Column(String(32), unique=True, nullable=False)  # 고유 할당 ID

    # 요청 정보
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    withdrawal_request_id = Column(Integer, ForeignKey("withdrawal_requests.id"))
    batch_id = Column(String(32))  # 배치 처리 ID

    # 공급원 정보
    supplier_id = Column(Integer, ForeignKey("energy_suppliers.id"))
    supplier_type = Column(Enum(SupplierType))

    # 할당 정보
    target_address = Column(String(34), nullable=False)  # 에너지 수신 주소
    energy_amount = Column(BigInteger, nullable=False)
    duration_days = Column(Integer, default=1)

    # 비용 정보
    energy_price = Column(Numeric(20, 10))  # 에너지당 가격
    base_cost_trx = Column(Numeric(20, 6))  # 기본 비용
    margin_rate = Column(Numeric(5, 2))  # 마진율
    margin_amount_trx = Column(Numeric(20, 6))  # 마진 금액
    saas_fee_trx = Column(Numeric(20, 6))  # SaaS 수수료
    total_cost_trx = Column(Numeric(20, 6))  # 총 비용

    # 트랜잭션 정보
    payment_tx_hash = Column(String(64))  # TRX 결제 트랜잭션
    delegation_tx_hash = Column(String(64))  # 에너지 위임 트랜잭션

    # 상태 관리
    status = Column(Enum(AllocationStatus), default=AllocationStatus.PENDING)
    error_message = Column(String(500))
    retry_count = Column(Integer, default=0)

    # 폴백 정보
    is_fallback = Column(Boolean, default=False)
    estimated_burn_trx = Column(Numeric(20, 6))  # 예상 TRX 소각량
    actual_burn_trx = Column(Numeric(20, 6))  # 실제 TRX 소각량

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    payment_confirmed_at = Column(DateTime)
    delegated_at = Column(DateTime)
    completed_at = Column(DateTime)
    expires_at = Column(DateTime)

    # 관계
    partner = relationship("Partner", back_populates="energy_allocations")
    supplier = relationship("EnergySupplier", back_populates="allocations")
    withdrawal_request = relationship("WithdrawalRequest", back_populates="energy_allocation")

```

### 1.3 본사 지갑 모델

```python
# app/models/company_wallet.py
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, Boolean
import enum

class CompanyWalletType(enum.Enum):
    """본사 지갑 유형"""
    REVENUE = "revenue"          # 수익금 수신 지갑
    STAKING = "staking"         # 스테이킹 지갑
    OPERATING = "operating"     # 운영비 지갑

class CompanyWallet(Base):
    """본사 지갑 정보"""
    __tablename__ = "company_wallets"

    id = Column(Integer, primary_key=True)
    wallet_type = Column(Enum(CompanyWalletType), unique=True, nullable=False)
    address = Column(String(34), unique=True, nullable=False)

    # 잔액 정보
    trx_balance = Column(Numeric(20, 6), default=0)
    usdt_balance = Column(Numeric(20, 6), default=0)

    # 스테이킹 정보 (스테이킹 지갑용)
    staked_amount = Column(Numeric(20, 6), default=0)
    available_energy = Column(BigInteger, default=0)
    energy_limit = Column(BigInteger)
    last_stake_at = Column(DateTime)
    next_unstake_available_at = Column(DateTime)

    # 상태
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

```

### Phase 2: 핵심 서비스 구현

### 2.1 에너지 공급원 관리 서비스

```python
# app/services/energy/supplier_manager.py
from typing import List, Optional, Dict
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import EnergySupplier, EnergyAllocation, CompanyWallet
from app.services.tron import TronService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EnergySupplierManager:
    """에너지 공급원 관리자"""

    def __init__(self, db: Session):
        self.db = db
        self.tron_service = TronService()

    async def find_optimal_supplier(
        self,
        energy_needed: int,
        urgency_level: str = "normal"
    ) -> Optional[EnergySupplier]:
        """최적 에너지 공급원 찾기"""
        try:
            # 활성화된 공급원을 우선순위 순으로 조회
            suppliers = self.db.query(EnergySupplier).filter(
                EnergySupplier.is_active == True,
                EnergySupplier.status == SupplierStatus.ACTIVE
            ).order_by(EnergySupplier.priority).all()

            for supplier in suppliers:
                # 공급원 상태 확인
                if not await self._check_supplier_health(supplier):
                    continue

                # 공급 가능 여부 확인
                if supplier.supplier_type == SupplierType.SELF_STAKING:
                    if await self._check_self_staking_availability(supplier, energy_needed):
                        logger.info(f"자체 스테이킹 사용 선택: {energy_needed} 에너지")
                        return supplier

                elif supplier.min_order_amount <= energy_needed:
                    if await self._check_external_supplier_availability(supplier, energy_needed):
                        logger.info(f"{supplier.name} 사용 선택: {energy_needed} 에너지")
                        return supplier

            # 모든 공급원 실패 시
            logger.warning(f"모든 공급원 실패, 폴백 모드 활성화")
            return None

        except Exception as e:
            logger.error(f"최적 공급원 검색 실패: {e}")
            return None

    async def _check_supplier_health(self, supplier: EnergySupplier) -> bool:
        """공급원 상태 확인"""
        try:
            # 마지막 확인 시간 체크
            if supplier.last_checked_at:
                time_since_check = datetime.utcnow() - supplier.last_checked_at
                if time_since_check < timedelta(minutes=5):
                    return supplier.status == SupplierStatus.ACTIVE

            # 실제 상태 확인
            is_healthy = await self._perform_health_check(supplier)

            # 상태 업데이트
            supplier.last_checked_at = datetime.utcnow()
            supplier.status = SupplierStatus.ACTIVE if is_healthy else SupplierStatus.ERROR
            self.db.commit()

            return is_healthy

        except Exception as e:
            logger.error(f"공급원 상태 확인 실패: {e}")
            return False

    async def _check_self_staking_availability(
        self,
        supplier: EnergySupplier,
        energy_needed: int
    ) -> bool:
        """자체 스테이킹 에너지 가용성 확인"""
        try:
            # 스테이킹 지갑 조회
            staking_wallet = self.db.query(CompanyWallet).filter(
                CompanyWallet.wallet_type == CompanyWalletType.STAKING
            ).first()

            if not staking_wallet:
                return False

            # 실제 에너지 잔량 확인
            account_info = await self.tron_service.get_account_resources(
                staking_wallet.address
            )
            available_energy = account_info.get("EnergyLimit", 0) - account_info.get("EnergyUsed", 0)

            # DB 업데이트
            supplier.available_energy = available_energy
            staking_wallet.available_energy = available_energy
            self.db.commit()

            return available_energy >= energy_needed

        except Exception as e:
            logger.error(f"자체 스테이킹 가용성 확인 실패: {e}")
            return False

    async def _check_external_supplier_availability(
        self,
        supplier: EnergySupplier,
        energy_needed: int
    ) -> bool:
        """외부 공급사 가용성 확인"""
        try:
            if supplier.supplier_type == SupplierType.TRONZAP:
                return await self._check_tronzap_availability(supplier, energy_needed)
            elif supplier.supplier_type == SupplierType.TRONNRG:
                return await self._check_tronnrg_availability(supplier, energy_needed)
            return False

        except Exception as e:
            logger.error(f"외부 공급사 가용성 확인 실패: {e}")
            return False

```

### 2.2 에너지 할당 서비스

```python
# app/services/energy/allocation_service.py
from typing import Dict, Optional, List
from decimal import Decimal
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.orm import Session
from app.models import (
    EnergyAllocation, EnergySupplier, Partner,
    WithdrawalRequest, AllocationStatus
)
from app.services.energy.supplier_manager import EnergySupplierManager
from app.services.external_apis import TronZapAPI, TronNRGAPI
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EnergyAllocationService:
    """에너지 할당 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.supplier_manager = EnergySupplierManager(db)
        self.tronzap_api = TronZapAPI()
        self.tronnrg_api = TronNRGAPI()

    async def allocate_energy_for_withdrawal(
        self,
        partner_id: int,
        withdrawal_request_id: int,
        target_address: str,
        energy_amount: int
    ) -> Dict:
        """출금을 위한 에너지 할당"""
        try:
            # 할당 기록 생성
            allocation = EnergyAllocation(
                allocation_id=self._generate_allocation_id(),
                partner_id=partner_id,
                withdrawal_request_id=withdrawal_request_id,
                target_address=target_address,
                energy_amount=energy_amount,
                status=AllocationStatus.PENDING
            )
            self.db.add(allocation)
            self.db.commit()

            # 최적 공급원 찾기
            supplier = await self.supplier_manager.find_optimal_supplier(energy_amount)

            if not supplier:
                # 폴백 모드 활성화
                return await self._activate_fallback_mode(allocation)

            # 공급원별 처리
            allocation.supplier_id = supplier.id
            allocation.supplier_type = supplier.supplier_type

            if supplier.supplier_type == SupplierType.SELF_STAKING:
                result = await self._allocate_from_self_staking(allocation, supplier)
            else:
                result = await self._allocate_from_external_supplier(allocation, supplier)

            return result

        except Exception as e:
            logger.error(f"에너지 할당 실패: {e}")
            if allocation:
                allocation.status = AllocationStatus.FAILED
                allocation.error_message = str(e)
                self.db.commit()
            raise

    async def _allocate_from_self_staking(
        self,
        allocation: EnergyAllocation,
        supplier: EnergySupplier
    ) -> Dict:
        """자체 스테이킹에서 에너지 할당"""
        try:
            allocation.status = AllocationStatus.PROCESSING
            self.db.commit()

            # 비용 계산
            allocation.energy_price = supplier.cost_per_energy
            allocation.base_cost_trx = Decimal(allocation.energy_amount) * supplier.cost_per_energy
            allocation.margin_rate = Decimal(settings.DEFAULT_MARGIN_RATE)
            allocation.margin_amount_trx = allocation.base_cost_trx * allocation.margin_rate
            allocation.saas_fee_trx = Decimal(settings.SAAS_FEE_PER_TRANSACTION)
            allocation.total_cost_trx = (
                allocation.base_cost_trx +
                allocation.margin_amount_trx +
                allocation.saas_fee_trx
            )

            # 에너지 위임 실행
            delegation_result = await self.tron_service.delegate_energy(
                from_address=self._get_staking_wallet_address(),
                to_address=allocation.target_address,
                energy_amount=allocation.energy_amount,
                duration_days=allocation.duration_days
            )

            if delegation_result['success']:
                allocation.delegation_tx_hash = delegation_result['tx_hash']
                allocation.status = AllocationStatus.COMPLETED
                allocation.delegated_at = datetime.utcnow()
                allocation.completed_at = datetime.utcnow()
                allocation.expires_at = datetime.utcnow() + timedelta(days=allocation.duration_days)

                # 공급원 통계 업데이트
                supplier.total_energy_supplied += allocation.energy_amount
                supplier.total_orders += 1
                supplier.available_energy -= allocation.energy_amount

                self.db.commit()

                logger.info(f"자체 스테이킹 에너지 할당 완료: {allocation.allocation_id}")

                return {
                    "success": True,
                    "allocation_id": allocation.allocation_id,
                    "energy_amount": allocation.energy_amount,
                    "total_cost_trx": float(allocation.total_cost_trx),
                    "delegation_tx_hash": allocation.delegation_tx_hash,
                    "expires_at": allocation.expires_at.isoformat()
                }
            else:
                raise Exception(f"에너지 위임 실패: {delegation_result.get('error')}")

        except Exception as e:
            logger.error(f"자체 스테이킹 할당 실패: {e}")
            allocation.status = AllocationStatus.FAILED
            allocation.error_message = str(e)
            self.db.commit()
            raise

    async def _allocate_from_external_supplier(
        self,
        allocation: EnergyAllocation,
        supplier: EnergySupplier
    ) -> Dict:
        """외부 공급사에서 에너지 할당"""
        try:
            allocation.status = AllocationStatus.PROCESSING
            self.db.commit()

            # 공급사별 API 호출
            if supplier.supplier_type == SupplierType.TRONZAP:
                result = await self._purchase_from_tronzap(allocation, supplier)
            elif supplier.supplier_type == SupplierType.TRONNRG:
                result = await self._purchase_from_tronnrg(allocation, supplier)
            else:
                raise ValueError(f"지원하지 않는 공급사: {supplier.supplier_type}")

            return result

        except Exception as e:
            logger.error(f"외부 공급사 할당 실패: {e}")
            allocation.status = AllocationStatus.FAILED
            allocation.error_message = str(e)
            self.db.commit()

            # 다음 공급원으로 재시도
            return await self._retry_with_next_supplier(allocation)

    async def _activate_fallback_mode(self, allocation: EnergyAllocation) -> Dict:
        """폴백 모드 활성화 (파트너사 직접 처리)"""
        try:
            allocation.is_fallback = True
            allocation.status = AllocationStatus.FALLBACK

            # 예상 TRX 소각량 계산
            allocation.estimated_burn_trx = Decimal(allocation.energy_amount) * Decimal("0.000413")

            self.db.commit()

            # 파트너사에 알림
            await self._notify_partner_fallback_mode(allocation)

            logger.warning(f"폴백 모드 활성화: {allocation.allocation_id}")

            return {
                "success": False,
                "fallback_mode": True,
                "allocation_id": allocation.allocation_id,
                "energy_amount": allocation.energy_amount,
                "estimated_burn_trx": float(allocation.estimated_burn_trx),
                "message": "모든 에너지 공급원이 실패했습니다. 직접 TRX를 사용하여 처리해주세요."
            }

        except Exception as e:
            logger.error(f"폴백 모드 활성화 실패: {e}")
            raise

```

### Phase 3: API 엔드포인트 구현

### 3.1 슈퍼어드민 에너지 관리 API

```python
# app/api/v1/endpoints/superadmin/energy_pool.py
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.api import deps
from app.models import EnergySupplier, EnergyAllocation, CompanyWallet
from app.schemas.energy import (
    EnergySupplierResponse, EnergySupplierCreate, EnergySupplierUpdate,
    EnergyAllocationResponse, EnergyCalculateRequest, EnergyCalculateResponse,
    CompanyWalletResponse
)
from app.services.energy import EnergySupplierManager, EnergyAllocationService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/suppliers", response_model=List[EnergySupplierResponse])
async def get_energy_suppliers(
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_superadmin)
):
    """모든 에너지 공급원 상태 조회"""
    try:
        suppliers = db.query(EnergySupplier).order_by(EnergySupplier.priority).all()

        # 실시간 상태 업데이트
        supplier_manager = EnergySupplierManager(db)
        for supplier in suppliers:
            await supplier_manager._check_supplier_health(supplier)

        return suppliers

    except Exception as e:
        logger.error(f"에너지 공급원 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="에너지 공급원 조회에 실패했습니다")

@router.post("/suppliers", response_model=EnergySupplierResponse)
async def add_energy_supplier(
    supplier_data: EnergySupplierCreate,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_superadmin)
):
    """새 에너지 공급원 추가"""
    try:
        # 중복 확인
        existing = db.query(EnergySupplier).filter(
            EnergySupplier.supplier_type == supplier_data.supplier_type
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"이미 존재하는 공급원 유형입니다: {supplier_data.supplier_type}"
            )

        supplier = EnergySupplier(**supplier_data.dict())
        db.add(supplier)
        db.commit()
        db.refresh(supplier)

        logger.info(f"새 에너지 공급원 추가: {supplier.name}")
        return supplier

    except Exception as e:
        logger.error(f"에너지 공급원 추가 실패: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/suppliers/{supplier_id}/priority")
async def update_supplier_priority(
    supplier_id: int,
    priority: int = Query(..., ge=1, le=10),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_superadmin)
):
    """공급원 우선순위 변경"""
    try:
        supplier = db.query(EnergySupplier).filter(
            EnergySupplier.id == supplier_id
        ).first()

        if not supplier:
            raise HTTPException(status_code=404, detail="공급원을 찾을 수 없습니다")

        # 다른 공급원들의 우선순위 조정
        if priority != supplier.priority:
            # 우선순위가 낮아지는 경우
            if priority > supplier.priority:
                db.query(EnergySupplier).filter(
                    EnergySupplier.priority > supplier.priority,
                    EnergySupplier.priority <= priority,
                    EnergySupplier.id != supplier_id
                ).update({EnergySupplier.priority: EnergySupplier.priority - 1})
            # 우선순위가 높아지는 경우
            else:
                db.query(EnergySupplier).filter(
                    EnergySupplier.priority >= priority,
                    EnergySupplier.priority < supplier.priority,
                    EnergySupplier.id != supplier_id
                ).update({EnergySupplier.priority: EnergySupplier.priority + 1})

        supplier.priority = priority
        db.commit()

        logger.info(f"공급원 우선순위 변경: {supplier.name} -> {priority}")
        return {"message": "우선순위가 변경되었습니다"}

    except Exception as e:
        logger.error(f"우선순위 변경 실패: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate", response_model=EnergyCalculateResponse)
async def calculate_energy_cost(
    request: EnergyCalculateRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_superadmin)
):
    """출금 요청에 대한 에너지 비용 계산"""
    try:
        # 총 에너지 계산
        total_energy = 0
        for withdrawal in request.withdrawal_requests:
            # USDT 전송 기본 에너지
            base_energy = 31895

            # 첫 USDT 수신 시 추가 에너지
            # TODO: 수신자의 USDT 보유 여부 확인
            first_time_bonus = 15000 if request.assume_first_time else 0

            total_energy += base_energy + first_time_bonus

        # 배치 처리 시 에너지 절약 (약 10%)
        if request.batch_mode and len(request.withdrawal_requests) > 1:
            total_energy = int(total_energy * 0.9)

        # 최적 공급원 찾기
        supplier_manager = EnergySupplierManager(db)
        optimal_supplier = await supplier_manager.find_optimal_supplier(total_energy)

        if optimal_supplier:
            # 정상 모드 비용 계산
            energy_price = float(optimal_supplier.cost_per_energy)
            base_cost = total_energy * energy_price
            margin_rate = float(settings.DEFAULT_MARGIN_RATE)
            margin_amount = base_cost * margin_rate
            saas_fee = float(settings.SAAS_FEE_PER_TRANSACTION) * len(request.withdrawal_requests)
            total_cost = base_cost + margin_amount + saas_fee

            return EnergyCalculateResponse(
                total_energy_required=total_energy,
                base_cost_trx=base_cost,
                margin_trx=margin_amount,
                saas_fee_trx=saas_fee,
                total_cost_trx=total_cost,
                energy_price=energy_price,
                supplier_type=optimal_supplier.supplier_type.value,
                fallback_mode=False,
                fallback_burn_trx=0,
                valid_until=(datetime.utcnow() + timedelta(minutes=10)).isoformat()
            )
        else:
            # 폴백 모드 비용 계산
            fallback_burn = total_energy * 0.000413

            return EnergyCalculateResponse(
                total_energy_required=total_energy,
                base_cost_trx=0,
                margin_trx=0,
                saas_fee_trx=0,
                total_cost_trx=0,
                energy_price=0,
                supplier_type="fallback",
                fallback_mode=True,
                fallback_burn_trx=fallback_burn,
                valid_until=(datetime.utcnow() + timedelta(minutes=10)).isoformat()
            )

    except Exception as e:
        logger.error(f"에너지 비용 계산 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/allocate", response_model=Dict)
async def allocate_energy(
    partner_id: int,
    target_address: str,
    energy_amount: int,
    withdrawal_request_id: Optional[int] = None,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_superadmin)
):
    """최적 공급원에서 에너지 할당"""
    try:
        allocation_service = EnergyAllocationService(db)
        result = await allocation_service.allocate_energy_for_withdrawal(
            partner_id=partner_id,
            withdrawal_request_id=withdrawal_request_id,
            target_address=target_address,
            energy_amount=energy_amount
        )

        return result

    except Exception as e:
        logger.error(f"에너지 할당 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/wallets", response_model=List[CompanyWalletResponse])
async def get_company_wallets(
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_superadmin)
):
    """본사 지갑 현황 조회"""
    try:
        wallets = db.query(CompanyWallet).all()

        # 실시간 잔액 업데이트
        tron_service = TronService()
        for wallet in wallets:
            balance_info = await tron_service.get_account_balance(wallet.address)
            wallet.trx_balance = Decimal(str(balance_info.get('trx', 0)))
            wallet.usdt_balance = Decimal(str(balance_info.get('usdt', 0)))

            if wallet.wallet_type == CompanyWalletType.STAKING:
                resources = await tron_service.get_account_resources(wallet.address)
                wallet.available_energy = resources.get('EnergyLimit', 0) - resources.get('EnergyUsed', 0)

        db.commit()
        return wallets

    except Exception as e:
        logger.error(f"지갑 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="지갑 조회에 실패했습니다")

@router.get("/allocations", response_model=List[EnergyAllocationResponse])
async def get_energy_allocations(
    partner_id: Optional[int] = None,
    status: Optional[AllocationStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_superadmin)
):
    """에너지 할당 이력 조회"""
    try:
        query = db.query(EnergyAllocation)

        if partner_id:
            query = query.filter(EnergyAllocation.partner_id == partner_id)
        if status:
            query = query.filter(EnergyAllocation.status == status)
        if start_date:
            query = query.filter(EnergyAllocation.created_at >= start_date)
        if end_date:
            query = query.filter(EnergyAllocation.created_at <= end_date)

        total = query.count()
        allocations = query.order_by(
            EnergyAllocation.created_at.desc()
        ).offset(skip).limit(limit).all()

        return {
            "total": total,
            "items": allocations
        }

    except Exception as e:
        logger.error(f"할당 이력 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="할당 이력 조회에 실패했습니다")

```

### Phase 4: 외부 API 통합

### 4.1 TronZap API 클라이언트

```python
# app/services/external_apis/tronzap.py
import aiohttp
import asyncio
from typing import Dict, Optional
from datetime import datetime
import hmac
import hashlib
import json
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class TronZapAPI:
    """TronZap 에너지 공급사 API 클라이언트"""

    def __init__(self):
        self.base_url = settings.TRONZAP_API_URL
        self.api_key = settings.TRONZAP_API_KEY
        self.api_secret = settings.TRONZAP_API_SECRET
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _generate_signature(self, payload: Dict) -> str:
        """API 서명 생성"""
        message = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    async def check_availability(self, energy_amount: int) -> Dict:
        """에너지 가용성 확인"""
        try:
            endpoint = f"{self.base_url}/energy/availability"
            payload = {
                "amount": energy_amount,
                "timestamp": int(datetime.utcnow().timestamp())
            }

            headers = {
                "X-API-Key": self.api_key,
                "X-Signature": self._generate_signature(payload)
            }

            async with self.session.get(
                endpoint,
                params=payload,
                headers=headers
            ) as response:
                data = await response.json()

                if response.status == 200:
                    return {
                        "available": data.get("available", False),
                        "current_stock": data.get("current_stock", 0),
                        "price_per_energy": data.get("price", 0)
                    }
                else:
                    logger.error(f"TronZap 가용성 확인 실패: {data}")
                    return {"available": False}

        except Exception as e:
            logger.error(f"TronZap API 오류: {e}")
            return {"available": False}

    async def purchase_energy(
        self,
        target_address: str,
        energy_amount: int,
        duration_hours: int = 1
    ) -> Dict:
        """에너지 구매"""
        try:
            endpoint = f"{self.base_url}/energy/purchase"
            payload = {
                "target_address": target_address,
                "amount": energy_amount,
                "duration_hours": duration_hours,
                "timestamp": int(datetime.utcnow().timestamp())
            }

            headers = {
                "X-API-Key": self.api_key,
                "X-Signature": self._generate_signature(payload),
                "Content-Type": "application/json"
            }

            async with self.session.post(
                endpoint,
                json=payload,
                headers=headers
            ) as response:
                data = await response.json()

                if response.status == 200:
                    return {
                        "success": True,
                        "order_id": data.get("order_id"),
                        "tx_hash": data.get("tx_hash"),
                        "total_cost": data.get("total_cost"),
                        "expires_at": data.get("expires_at")
                    }
                else:
                    logger.error(f"TronZap 구매 실패: {data}")
                    return {
                        "success": False,
                        "error": data.get("error", "Unknown error")
                    }

        except Exception as e:
            logger.error(f"TronZap 구매 API 오류: {e}")
            return {
                "success": False,
                "error": str(e)
            }

```

### 4.2 TronNRG API 클라이언트

```python
# app/services/external_apis/tronnrg.py
import aiohttp
from typing import Dict
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class TronNRGAPI:
    """TronNRG 에너지 공급사 API 클라이언트"""

    def __init__(self):
        self.base_url = settings.TRONNRG_API_URL
        self.api_key = settings.TRONNRG_API_KEY

    async def get_energy_price(self) -> float:
        """현재 에너지 가격 조회"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}

                async with session.get(
                    f"{self.base_url}/price/current",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("price_per_energy", 0)
                    return 0

        except Exception as e:
            logger.error(f"TronNRG 가격 조회 실패: {e}")
            return 0

    async def rent_energy(
        self,
        receiver_address: str,
        energy_amount: int,
        duration_hours: int = 1
    ) -> Dict:
        """에너지 임대"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "receiver": receiver_address,
                    "energy": energy_amount,
                    "duration": duration_hours
                }

                async with session.post(
                    f"{self.base_url}/energy/rent",
                    json=payload,
                    headers=headers
                ) as response:
                    data = await response.json()

                    if response.status == 200:
                        return {
                            "success": True,
                            "rental_id": data.get("rental_id"),
                            "tx_hash": data.get("tx_hash"),
                            "cost": data.get("cost"),
                            "expires_at": data.get("expires_at")
                        }
                    else:
                        return {
                            "success": False,
                            "error": data.get("message", "Rental failed")
                        }

        except Exception as e:
            logger.error(f"TronNRG 임대 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }

```

### Phase 5: 재투자 및 스테이킹 관리

### 5.1 자동 재투자 서비스

```python
# app/services/energy/reinvestment_service.py
from typing import Dict
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import (
    CompanyWallet, CompanyWalletType, EnergyAllocation,
    StakingHistory, StakingOperation
)
from app.services.tron import TronService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class ReinvestmentService:
    """수익 재투자 및 스테이킹 관리 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.tron_service = TronService()

    async def calculate_monthly_profit(self) -> Dict:
        """월간 수익 계산"""
        try:
            # 이번 달 시작일
            now = datetime.utcnow()
            month_start = datetime(now.year, now.month, 1)

            # 완료된 할당의 수익 합계
            result = self.db.query(
                func.sum(EnergyAllocation.margin_amount_trx),
                func.sum(EnergyAllocation.saas_fee_trx),
                func.count(EnergyAllocation.id)
            ).filter(
                EnergyAllocation.status == AllocationStatus.COMPLETED,
                EnergyAllocation.completed_at >= month_start
            ).first()

            margin_revenue = result[0] or Decimal("0")
            saas_revenue = result[1] or Decimal("0")
            total_orders = result[2] or 0

            total_revenue = margin_revenue + saas_revenue

            # 비용 계산 (외부 공급사 사용 비용)
            external_cost = self.db.query(
                func.sum(EnergyAllocation.base_cost_trx)
            ).filter(
                EnergyAllocation.status == AllocationStatus.COMPLETED,
                EnergyAllocation.completed_at >= month_start,
                EnergyAllocation.supplier_type.in_([
                    SupplierType.TRONZAP,
                    SupplierType.TRONNRG
                ])
            ).scalar() or Decimal("0")

            net_profit = total_revenue - external_cost

            return {
                "month": now.strftime("%Y-%m"),
                "total_revenue": float(total_revenue),
                "margin_revenue": float(margin_revenue),
                "saas_revenue": float(saas_revenue),
                "external_cost": float(external_cost),
                "net_profit": float(net_profit),
                "total_orders": total_orders,
                "reinvestment_amount": float(net_profit * Decimal("0.5"))  # 50% 재투자
            }

        except Exception as e:
            logger.error(f"월간 수익 계산 실패: {e}")
            raise

    async def execute_reinvestment(self, amount_trx: Decimal) -> Dict:
        """재투자 실행 (TRX 스테이킹)"""
        try:
            # 수익 지갑에서 스테이킹 지갑으로 이체
            revenue_wallet = self.db.query(CompanyWallet).filter(
                CompanyWallet.wallet_type == CompanyWalletType.REVENUE
            ).first()

            staking_wallet = self.db.query(CompanyWallet).filter(
                CompanyWallet.wallet_type == CompanyWalletType.STAKING
            ).first()

            if not revenue_wallet or not staking_wallet:
                raise ValueError("필수 지갑이 설정되지 않았습니다")

            # TRX 이체
            transfer_result = await self.tron_service.transfer_trx(
                from_address=revenue_wallet.address,
                to_address=staking_wallet.address,
                amount=amount_trx
            )

            if not transfer_result['success']:
                raise Exception(f"TRX 이체 실패: {transfer_result.get('error')}")

            # 스테이킹 실행
            stake_result = await self.tron_service.freeze_balance_v2(
                address=staking_wallet.address,
                amount=amount_trx,
                resource_type="ENERGY"
            )

            if stake_result['success']:
                # 스테이킹 이력 기록
                staking_history = StakingHistory(
                    wallet_address=staking_wallet.address,
                    operation=StakingOperation.STAKE,
                    amount_trx=amount_trx,
                    tx_hash=stake_result['tx_hash'],
                    energy_gained=int(amount_trx * 1500),  # 대략적인 에너지 계산
                    executed_at=datetime.utcnow()
                )
                self.db.add(staking_history)

                # 지갑 정보 업데이트
                staking_wallet.staked_amount += amount_trx
                staking_wallet.last_stake_at = datetime.utcnow()

                self.db.commit()

                logger.info(f"재투자 스테이킹 완료: {amount_trx} TRX")

                return {
                    "success": True,
                    "amount_staked": float(amount_trx),
                    "tx_hash": stake_result['tx_hash'],
                    "estimated_energy": int(amount_trx * 1500)
                }
            else:
                raise Exception(f"스테이킹 실패: {stake_result.get('error')}")

        except Exception as e:
            logger.error(f"재투자 실행 실패: {e}")
            self.db.rollback()
            raise

    async def get_staking_roi(self) -> Dict:
        """스테이킹 ROI 계산"""
        try:
            # 총 스테이킹 금액
            staking_wallet = self.db.query(CompanyWallet).filter(
                CompanyWallet.wallet_type == CompanyWalletType.STAKING
            ).first()

            if not staking_wallet:
                return {"roi": 0, "message": "스테이킹 지갑이 없습니다"}

            total_staked = staking_wallet.staked_amount

            if total_staked == 0:
                return {"roi": 0, "message": "스테이킹된 TRX가 없습니다"}

            # 자체 스테이킹으로 절약한 비용 계산
            saved_cost = self.db.query(
                func.sum(
                    EnergyAllocation.energy_amount *
                    (Decimal("0.00002") - Decimal("0.00001"))  # 외부 가격 - 자체 비용
                )
            ).filter(
                EnergyAllocation.supplier_type == SupplierType.SELF_STAKING,
                EnergyAllocation.status == AllocationStatus.COMPLETED
            ).scalar() or Decimal("0")

            # ROI 계산 (연간 기준)
            monthly_saving = saved_cost
            annual_saving = monthly_saving * 12
            roi = (annual_saving / total_staked) * 100

            return {
                "total_staked": float(total_staked),
                "monthly_saving": float(monthly_saving),
                "annual_saving": float(annual_saving),
                "roi_percentage": float(roi),
                "self_supply_ratio": await self._calculate_self_supply_ratio()
            }

        except Exception as e:
            logger.error(f"ROI 계산 실패: {e}")
            raise

    async def _calculate_self_supply_ratio(self) -> float:
        """자체 공급 비율 계산"""
        try:
            # 전체 에너지 공급량
            total_energy = self.db.query(
                func.sum(EnergyAllocation.energy_amount)
            ).filter(
                EnergyAllocation.status == AllocationStatus.COMPLETED
            ).scalar() or 0

            # 자체 스테이킹 공급량
            self_energy = self.db.query(
                func.sum(EnergyAllocation.energy_amount)
            ).filter(
                EnergyAllocation.supplier_type == SupplierType.SELF_STAKING,
                EnergyAllocation.status == AllocationStatus.COMPLETED
            ).scalar() or 0

            if total_energy == 0:
                return 0

            return (self_energy / total_energy) * 100

        except Exception as e:
            logger.error(f"자체 공급 비율 계산 실패: {e}")
            return 0

```

## 🧪 테스트 시나리오

### 1. 공급원 우선순위 테스트

```python
# tests/test_energy_supplier.py
import pytest
from app.services.energy import EnergySupplierManager

@pytest.mark.asyncio
async def test_supplier_priority():
    """공급원 우선순위 테스트"""
    # 1. 자체 스테이킹 우선 선택 확인
    # 2. 자체 스테이킹 부족 시 TronZap 선택
    # 3. TronZap 실패 시 TronNRG 선택
    # 4. 모든 공급원 실패 시 폴백 모드

```

### 2. 에너지 할당 플로우 테스트

```python
@pytest.mark.asyncio
async def test_energy_allocation_flow():
    """전체 에너지 할당 플로우 테스트"""
    # 1. 파트너사 출금 요청
    # 2. 에너지 계산
    # 3. TRX 결제 확인
    # 4. 에너지 할당
    # 5. 완료 확인

```

### 3. 폴백 모드 테스트

```python
@pytest.mark.asyncio
async def test_fallback_mode():
    """폴백 모드 활성화 테스트"""
    # 1. 모든 공급원 실패 시뮬레이션
    # 2. 폴백 모드 활성화 확인
    # 3. 파트너사 알림 확인
    # 4. 직접 처리 기록

```

## 📋 체크리스트

### 기능 구현

- [ ]  에너지 공급원 모델 구현
- [ ]  에너지 할당 모델 구현
- [ ]  공급원 관리 서비스 구현
- [ ]  할당 서비스 구현
- [ ]  슈퍼어드민 API 구현
- [ ]  외부 API 클라이언트 구현
- [ ]  재투자 서비스 구현

### 테스트

- [ ]  단위 테스트 작성
- [ ]  통합 테스트 작성
- [ ]  부하 테스트
- [ ]  장애 시나리오 테스트

### 모니터링

- [ ]  공급원 상태 모니터링
- [ ]  할당 성공률 추적
- [ ]  비용 분석 대시보드
- [ ]  알림 시스템 구현

## 🎉 기대 효과

1. **비용 최적화**: 최적 공급원 자동 선택으로 비용 절감
2. **안정성 향상**: 다중 공급원으로 서비스 중단 방지
3. **확장성**: 새로운 공급원 쉽게 추가 가능
4. **수익성**: 마진 관리 및 재투자로 지속 가능한 성장

이 시스템을 통해 본사는 안정적이고 수익성 있는 에너지 대납 서비스를 제공할 수 있습니다!