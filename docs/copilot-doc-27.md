# Copilot 문서 #27: 입금 Sweep 자동화 시스템

## 목표
사용자의 개별 입금 지갑으로 들어온 USDT를 파트너사의 중앙 지갑(TronLink)으로 자동으로 이동(Sweep)하는 시스템을 구축합니다. 이를 통해 자산을 중앙에서 효율적으로 관리하고 보안을 강화합니다.

## 전제 조건
- Copilot 문서 #24-26이 완료되어 있어야 합니다.
- 파트너사 TronLink 지갑이 연동되어 있어야 합니다.
- HD Wallet 키 생성 시스템이 구현되어 있어야 합니다.
- 블록체인 모니터링 서비스가 작동 중이어야 합니다.

## 🎯 Sweep 자동화 시스템 구조

### 📊 시스템 아키텍처
```
입금 Sweep 자동화
├── 🔑 HD Wallet 관리
│   ├── 마스터 시드 관리
│   ├── 사용자별 주소 파생
│   ├── 개인키 안전 보관
│   └── 주소 풀 관리
├── 👁️ 입금 모니터링
│   ├── 블록체인 실시간 스캔
│   ├── 입금 트랜잭션 감지
│   ├── 컨펌 대기 및 검증
│   └── 입금 알림 발송
├── 🔄 Sweep 실행
│   ├── Sweep 대상 필터링
│   ├── 트랜잭션 생성
│   ├── 가스비 계산 및 최적화
│   ├── 배치 처리 지원
│   └── 실패 시 재시도
├── 📋 Sweep 정책
│   ├── 최소 금액 설정
│   ├── 시간 기반 스케줄
│   ├── 가스비 임계값
│   ├── 우선순위 설정
│   └── 긴급 Sweep 옵션
└── 📊 모니터링 & 분석
    ├── Sweep 상태 추적
    ├── 비용 분석
    ├── 성공률 모니터링
    └── 최적화 제안
```

## 🛠️ 구현 단계

### Phase 1: HD Wallet 및 주소 관리 (1일)

#### 1.1 HD Wallet 모델
```python
# app/models/hd_wallet.py
"""HD Wallet 관리 관련 모델"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, JSON, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

class HDWalletMaster(Base):
    """HD Wallet 마스터 정보"""
    __tablename__ = "hd_wallet_masters"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False, unique=True)
    
    # 암호화된 마스터 시드
    encrypted_seed = Column(String(500), nullable=False, comment="암호화된 마스터 시드")
    public_key = Column(String(130), nullable=False, comment="마스터 공개키")
    
    # 파생 정보
    derivation_path = Column(String(100), default="m/44'/195'/0'/0", comment="파생 경로")
    last_index = Column(Integer, default=0, comment="마지막 사용 인덱스")
    
    # 보안 설정
    encryption_method = Column(String(50), default="AES-256-GCM", comment="암호화 방식")
    key_version = Column(Integer, default=1, comment="키 버전")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    addresses = relationship("UserDepositAddress", back_populates="hd_wallet")

class UserDepositAddress(Base):
    """사용자 입금 주소"""
    __tablename__ = "user_deposit_addresses"
    
    id = Column(Integer, primary_key=True, index=True)
    hd_wallet_id = Column(Integer, ForeignKey("hd_wallet_masters.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 주소 정보
    address = Column(String(42), nullable=False, unique=True, index=True, comment="입금 주소")
    derivation_index = Column(Integer, nullable=False, comment="파생 인덱스")
    encrypted_private_key = Column(String(500), nullable=False, comment="암호화된 개인키")
    
    # 상태 정보
    is_active = Column(Boolean, default=True, comment="활성 상태")
    total_received = Column(Numeric(18, 6), default=0, comment="총 입금액")
    last_sweep_at = Column(DateTime(timezone=True), comment="마지막 Sweep 시간")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    hd_wallet = relationship("HDWalletMaster", back_populates="addresses")
    sweep_logs = relationship("SweepLog", back_populates="deposit_address")
    
    # 인덱스
    __table_args__ = (
        Index("idx_deposit_address_user", "user_id"),
        Index("idx_deposit_address_active", "is_active"),
    )

class SweepConfiguration(Base):
    """Sweep 설정"""
    __tablename__ = "sweep_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False, unique=True)
    
    # Sweep 대상 지갑
    destination_wallet_id = Column(Integer, ForeignKey("partner_wallets.id"), nullable=False)
    
    # 기본 설정
    is_enabled = Column(Boolean, default=True, comment="Sweep 활성화")
    min_sweep_amount = Column(Numeric(18, 6), default=10, comment="최소 Sweep 금액")
    
    # 스케줄 설정
    sweep_interval_minutes = Column(Integer, default=60, comment="Sweep 간격 (분)")
    immediate_threshold = Column(Numeric(18, 6), default=1000, comment="즉시 Sweep 임계값")
    
    # 가스비 설정
    max_gas_price_sun = Column(Numeric(20, 0), default=1000, comment="최대 가스비 (SUN)")
    gas_optimization_enabled = Column(Boolean, default=True, comment="가스비 최적화")
    
    # 배치 설정
    batch_enabled = Column(Boolean, default=True, comment="배치 처리 활성화")
    max_batch_size = Column(Integer, default=20, comment="최대 배치 크기")
    
    # 알림 설정
    notification_enabled = Column(Boolean, default=True, comment="알림 활성화")
    notification_channels = Column(JSON, comment="알림 채널 설정")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    destination_wallet = relationship("PartnerWallet")

class SweepLog(Base):
    """Sweep 실행 로그"""
    __tablename__ = "sweep_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    deposit_address_id = Column(Integer, ForeignKey("user_deposit_addresses.id"), nullable=False)
    
    # Sweep 정보
    sweep_amount = Column(Numeric(18, 6), nullable=False, comment="Sweep 금액")
    gas_used = Column(Numeric(20, 0), comment="사용된 가스")
    gas_price = Column(Numeric(20, 0), comment="가스 가격")
    tx_hash = Column(String(66), index=True, comment="트랜잭션 해시")
    
    # 상태
    status = Column(String(20), default="pending", comment="상태")
    error_message = Column(String(500), comment="에러 메시지")
    retry_count = Column(Integer, default=0, comment="재시도 횟수")
    
    # 시간 정보
    initiated_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True), comment="확인 시간")
    
    # 관계 설정
    deposit_address = relationship("UserDepositAddress", back_populates="sweep_logs")
```

### Phase 2: HD Wallet 및 Sweep 서비스 (2일)

#### 2.1 HD Wallet 관리 서비스
```python
# app/services/wallet/hd_wallet_service.py
"""HD Wallet 관리 서비스"""
from typing import Tuple, Optional
from cryptography.fernet import Fernet
from mnemonic import Mnemonic
from tronpy import Tron
from tronpy.keys import PrivateKey
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hd_wallet import HDWalletMaster, UserDepositAddress
from app.core.config import settings
from app.utils.logger import logger

class HDWalletService:
    """HD Wallet 생성 및 관리"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tron = Tron(network=settings.TRON_NETWORK)
        self.cipher = Fernet(settings.WALLET_ENCRYPTION_KEY.encode())
    
    async def create_master_wallet(self, partner_id: int) -> HDWalletMaster:
        """파트너용 마스터 지갑 생성"""
        try:
            # 기존 마스터 지갑 확인
            existing = await self.db.query(HDWalletMaster).filter(
                HDWalletMaster.partner_id == partner_id
            ).first()
            
            if existing:
                return existing
            
            # 니모닉 생성
            mnemo = Mnemonic("english")
            mnemonic_phrase = mnemo.generate(strength=256)
            
            # 시드 생성
            seed = mnemo.to_seed(mnemonic_phrase)
            
            # 마스터 키 생성
            master_key = self._generate_master_key(seed)
            
            # 암호화 저장
            encrypted_seed = self.cipher.encrypt(seed)
            
            # DB 저장
            hd_wallet = HDWalletMaster(
                partner_id=partner_id,
                encrypted_seed=encrypted_seed.decode(),
                public_key=master_key['public_key']
            )
            
            self.db.add(hd_wallet)
            await self.db.commit()
            await self.db.refresh(hd_wallet)
            
            logger.info(f"Master wallet created for partner {partner_id}")
            return hd_wallet
            
        except Exception as e:
            logger.error(f"Failed to create master wallet: {e}")
            raise
    
    async def generate_deposit_address(
        self, 
        partner_id: int, 
        user_id: int
    ) -> UserDepositAddress:
        """사용자용 입금 주소 생성"""
        try:
            # 기존 주소 확인
            existing = await self.db.query(UserDepositAddress).filter(
                UserDepositAddress.user_id == user_id,
                UserDepositAddress.is_active == True
            ).first()
            
            if existing:
                return existing
            
            # 마스터 지갑 조회
            hd_wallet = await self.db.query(HDWalletMaster).filter(
                HDWalletMaster.partner_id == partner_id
            ).first()
            
            if not hd_wallet:
                hd_wallet = await self.create_master_wallet(partner_id)
            
            # 파생 인덱스 증가
            derivation_index = hd_wallet.last_index + 1
            
            # 주소 파생
            address, private_key = await self._derive_address(
                hd_wallet,
                derivation_index
            )
            
            # 개인키 암호화
            encrypted_private_key = self.cipher.encrypt(private_key.encode())
            
            # 주소 생성
            deposit_address = UserDepositAddress(
                hd_wallet_id=hd_wallet.id,
                user_id=user_id,
                address=address,
                derivation_index=derivation_index,
                encrypted_private_key=encrypted_private_key.decode()
            )
            
            # 마스터 인덱스 업데이트
            hd_wallet.last_index = derivation_index
            
            self.db.add(deposit_address)
            await self.db.commit()
            await self.db.refresh(deposit_address)
            
            logger.info(f"Deposit address created for user {user_id}: {address}")
            return deposit_address
            
        except Exception as e:
            logger.error(f"Failed to generate deposit address: {e}")
            raise
    
    def _generate_master_key(self, seed: bytes) -> dict:
        """마스터 키 생성"""
        # TRON은 secp256k1 사용
        # 간단한 구현 (실제로는 BIP32 라이브러리 사용 권장)
        master_private = hashlib.sha256(seed).hexdigest()
        private_key = PrivateKey(bytes.fromhex(master_private))
        
        return {
            'private_key': master_private,
            'public_key': private_key.public_key.hex()
        }
    
    async def _derive_address(
        self, 
        hd_wallet: HDWalletMaster, 
        index: int
    ) -> Tuple[str, str]:
        """주소 파생"""
        # 시드 복호화
        encrypted_seed = hd_wallet.encrypted_seed.encode()
        seed = self.cipher.decrypt(encrypted_seed)
        
        # 파생 경로: m/44'/195'/0'/0/{index}
        derived_seed = hashlib.sha256(
            seed + index.to_bytes(4, 'big')
        ).digest()
        
        # 개인키 생성
        private_key = PrivateKey(derived_seed)
        
        # 주소 생성
        address = private_key.address
        
        return address, private_key.hex()
    
    async def get_private_key(self, address: str) -> Optional[str]:
        """주소의 개인키 조회 (Sweep용)"""
        deposit_address = await self.db.query(UserDepositAddress).filter(
            UserDepositAddress.address == address
        ).first()
        
        if not deposit_address:
            return None
        
        # 복호화
        encrypted_key = deposit_address.encrypted_private_key.encode()
        private_key = self.cipher.decrypt(encrypted_key).decode()
        
        return private_key
```

#### 2.2 Sweep 실행 서비스
```python
# app/services/sweep/sweep_executor_service.py
"""Sweep 실행 서비스"""
from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from tronpy import Tron
from tronpy.keys import PrivateKey

from app.models.hd_wallet import UserDepositAddress, SweepConfiguration, SweepLog
from app.models.partner_wallet import PartnerWallet
from app.services.wallet.hd_wallet_service import HDWalletService
from app.core.config import settings
from app.utils.logger import logger

class SweepExecutorService:
    """Sweep 실행 엔진"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tron = Tron(network=settings.TRON_NETWORK)
        self.hd_service = HDWalletService(db)
    
    async def execute_sweep_for_partner(self, partner_id: int) -> Dict:
        """파트너사의 Sweep 실행"""
        try:
            # Sweep 설정 조회
            config = await self.db.query(SweepConfiguration).filter(
                SweepConfiguration.partner_id == partner_id
            ).first()
            
            if not config or not config.is_enabled:
                return {"status": "disabled", "swept_count": 0}
            
            # Sweep 대상 조회
            addresses = await self._get_sweep_candidates(partner_id, config)
            
            if not addresses:
                return {"status": "no_candidates", "swept_count": 0}
            
            # 대상 지갑 조회
            destination_wallet = await self.db.query(PartnerWallet).filter(
                PartnerWallet.id == config.destination_wallet_id
            ).first()
            
            if not destination_wallet:
                raise ValueError("Destination wallet not found")
            
            # 배치 처리 여부 결정
            if config.batch_enabled and len(addresses) > 1:
                result = await self._execute_batch_sweep(
                    addresses,
                    destination_wallet.wallet_address,
                    config
                )
            else:
                result = await self._execute_individual_sweep(
                    addresses,
                    destination_wallet.wallet_address,
                    config
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute sweep for partner {partner_id}: {e}")
            raise
    
    async def _get_sweep_candidates(
        self,
        partner_id: int,
        config: SweepConfiguration
    ) -> List[Dict]:
        """Sweep 대상 주소 조회"""
        candidates = []
        
        # 활성 주소 조회
        addresses = await self.db.query(UserDepositAddress).join(
            HDWalletMaster
        ).filter(
            HDWalletMaster.partner_id == partner_id,
            UserDepositAddress.is_active == True
        ).all()
        
        for address in addresses:
            # 잔액 확인
            balance = await self._get_usdt_balance(address.address)
            
            if balance <= 0:
                continue
            
            # 최소 금액 확인
            if balance < config.min_sweep_amount:
                # 즉시 Sweep 임계값 확인
                if balance < config.immediate_threshold:
                    continue
            
            # 마지막 Sweep 시간 확인
            if address.last_sweep_at:
                time_since_sweep = datetime.utcnow() - address.last_sweep_at
                if time_since_sweep < timedelta(minutes=config.sweep_interval_minutes):
                    # 즉시 Sweep 임계값이 아니면 스킵
                    if balance < config.immediate_threshold:
                        continue
            
            candidates.append({
                "address": address,
                "balance": balance,
                "priority": balance >= config.immediate_threshold
            })
        
        # 우선순위 정렬 (금액 큰 순서)
        candidates.sort(key=lambda x: x["balance"], reverse=True)
        
        return candidates
    
    async def _execute_individual_sweep(
        self,
        candidates: List[Dict],
        destination: str,
        config: SweepConfiguration
    ) -> Dict:
        """개별 Sweep 실행"""
        swept_count = 0
        total_swept = Decimal("0")
        failed_count = 0
        
        for candidate in candidates:
            try:
                address = candidate["address"]
                balance = candidate["balance"]
                
                # 개인키 조회
                private_key = await self.hd_service.get_private_key(address.address)
                if not private_key:
                    logger.error(f"Private key not found for {address.address}")
                    continue
                
                # 트랜잭션 생성 및 전송
                tx_hash = await self._send_sweep_transaction(
                    from_address=address.address,
                    to_address=destination,
                    amount=balance,
                    private_key=private_key
                )
                
                # 로그 기록
                sweep_log = SweepLog(
                    deposit_address_id=address.id,
                    sweep_amount=balance,
                    tx_hash=tx_hash,
                    status="pending"
                )
                self.db.add(sweep_log)
                
                # 주소 업데이트
                address.last_sweep_at = datetime.utcnow()
                
                swept_count += 1
                total_swept += balance
                
                logger.info(f"Swept {balance} USDT from {address.address} (tx: {tx_hash})")
                
            except Exception as e:
                logger.error(f"Failed to sweep from {address.address}: {e}")
                failed_count += 1
        
        await self.db.commit()
        
        return {
            "status": "completed",
            "swept_count": swept_count,
            "failed_count": failed_count,
            "total_amount": float(total_swept)
        }
    
    async def _execute_batch_sweep(
        self,
        candidates: List[Dict],
        destination: str,
        config: SweepConfiguration
    ) -> Dict:
        """배치 Sweep 실행 (멀티시그 트랜잭션)"""
        # TODO: 배치 처리 구현
        # TRON은 멀티시그를 지원하지만, 복잡도가 높아 
        # 일단 개별 처리로 대체
        return await self._execute_individual_sweep(candidates, destination, config)
    
    async def _get_usdt_balance(self, address: str) -> Decimal:
        """USDT 잔액 조회"""
        try:
            contract = self.tron.get_contract(settings.USDT_CONTRACT_ADDRESS)
            balance = contract.functions.balanceOf(address)
            return Decimal(str(balance / 1e6))
        except Exception as e:
            logger.error(f"Failed to get balance for {address}: {e}")
            return Decimal("0")
    
    async def _send_sweep_transaction(
        self,
        from_address: str,
        to_address: str,
        amount: Decimal,
        private_key: str
    ) -> str:
        """Sweep 트랜잭션 전송"""
        try:
            # USDT 컨트랙트
            contract = self.tron.get_contract(settings.USDT_CONTRACT_ADDRESS)
            
            # 트랜잭션 생성
            txn = contract.functions.transfer(
                to_address,
                int(amount * 1e6)
            ).with_owner(from_address).build()
            
            # 서명
            private_key_obj = PrivateKey(bytes.fromhex(private_key))
            txn = txn.sign(private_key_obj)
            
            # 전송
            result = txn.broadcast()
            
            if result.get("result"):
                return result.get("txid")
            else:
                raise Exception(f"Broadcast failed: {result}")
                
        except Exception as e:
            logger.error(f"Failed to send sweep transaction: {e}")
            raise
```

#### 2.3 Sweep 모니터링 서비스
```python
# app/services/sweep/sweep_monitor_service.py
"""Sweep 모니터링 서비스"""
from typing import Dict, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.hd_wallet import SweepLog, UserDepositAddress
from app.utils.logger import logger

class SweepMonitorService:
    """Sweep 상태 모니터링"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def check_pending_sweeps(self) -> None:
        """대기 중인 Sweep 확인"""
        # 10분 이상 pending 상태인 Sweep 조회
        timeout = datetime.utcnow() - timedelta(minutes=10)
        
        pending_sweeps = await self.db.query(SweepLog).filter(
            SweepLog.status == "pending",
            SweepLog.initiated_at < timeout
        ).all()
        
        for sweep in pending_sweeps:
            # 트랜잭션 상태 확인
            status = await self._check_transaction_status(sweep.tx_hash)
            
            if status == "confirmed":
                sweep.status = "completed"
                sweep.confirmed_at = datetime.utcnow()
            elif status == "failed":
                sweep.status = "failed"
                sweep.error_message = "Transaction failed on chain"
        
        await self.db.commit()
    
    async def get_sweep_statistics(
        self,
        partner_id: int,
        period_days: int = 7
    ) -> Dict:
        """Sweep 통계 조회"""
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        # 총 Sweep 수 및 금액
        total_stats = await self.db.query(
            func.count(SweepLog.id).label("total_count"),
            func.sum(SweepLog.sweep_amount).label("total_amount"),
            func.avg(SweepLog.gas_used).label("avg_gas")
        ).join(
            UserDepositAddress
        ).join(
            HDWalletMaster
        ).filter(
            HDWalletMaster.partner_id == partner_id,
            SweepLog.initiated_at >= start_date
        ).first()
        
        # 상태별 통계
        status_stats = await self.db.query(
            SweepLog.status,
            func.count(SweepLog.id).label("count")
        ).join(
            UserDepositAddress
        ).join(
            HDWalletMaster
        ).filter(
            HDWalletMaster.partner_id == partner_id,
            SweepLog.initiated_at >= start_date
        ).group_by(SweepLog.status).all()
        
        # 일별 통계
        daily_stats = await self.db.query(
            func.date(SweepLog.initiated_at).label("date"),
            func.count(SweepLog.id).label("count"),
            func.sum(SweepLog.sweep_amount).label("amount")
        ).join(
            UserDepositAddress
        ).join(
            HDWalletMaster
        ).filter(
            HDWalletMaster.partner_id == partner_id,
            SweepLog.initiated_at >= start_date
        ).group_by(
            func.date(SweepLog.initiated_at)
        ).all()
        
        return {
            "period_days": period_days,
            "total": {
                "count": total_stats.total_count or 0,
                "amount": float(total_stats.total_amount or 0),
                "avg_gas": float(total_stats.avg_gas or 0)
            },
            "by_status": {
                stat.status: stat.count
                for stat in status_stats
            },
            "daily": [
                {
                    "date": stat.date.isoformat(),
                    "count": stat.count,
                    "amount": float(stat.amount)
                }
                for stat in daily_stats
            ]
        }
    
    async def _check_transaction_status(self, tx_hash: str) -> str:
        """트랜잭션 상태 확인"""
        try:
            from tronpy import Tron
            tron = Tron()
            
            tx_info = tron.get_transaction_info(tx_hash)
            
            if tx_info.get("blockNumber"):
                return "confirmed"
            elif tx_info.get("result") == "FAILED":
                return "failed"
            else:
                return "pending"
                
        except Exception as e:
            logger.error(f"Failed to check transaction status: {e}")
            return "unknown"
```

### Phase 3: Sweep API 및 스케줄러 (1일)

#### 3.1 Sweep 관리 API
```python
# app/api/v1/endpoints/partner/sweep.py
"""파트너 Sweep 관리 API"""
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_partner
from app.models.partner import Partner
from app.schemas.sweep import (
    SweepConfigResponse,
    SweepConfigUpdate,
    SweepExecuteRequest,
    SweepStatusResponse,
    DepositAddressResponse
)
from app.services.sweep.sweep_executor_service import SweepExecutorService
from app.services.sweep.sweep_monitor_service import SweepMonitorService
from app.services.wallet.hd_wallet_service import HDWalletService

router = APIRouter(tags=["파트너 Sweep 관리"])

@router.get("/config", response_model=SweepConfigResponse)
async def get_sweep_config(
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """Sweep 설정 조회"""
    from app.models.hd_wallet import SweepConfiguration
    
    config = await db.query(SweepConfiguration).filter(
        SweepConfiguration.partner_id == current_partner.id
    ).first()
    
    if not config:
        # 기본 설정 생성
        from app.models.partner_wallet import PartnerWallet
        
        # 주 지갑 조회
        main_wallet = await db.query(PartnerWallet).filter(
            PartnerWallet.partner_id == current_partner.id,
            PartnerWallet.is_primary == True
        ).first()
        
        if not main_wallet:
            raise HTTPException(
                status_code=400,
                detail="No primary wallet found. Please connect a wallet first."
            )
        
        config = SweepConfiguration(
            partner_id=current_partner.id,
            destination_wallet_id=main_wallet.id
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)
    
    return SweepConfigResponse.from_orm(config)

@router.put("/config", response_model=SweepConfigResponse)
async def update_sweep_config(
    config_update: SweepConfigUpdate,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """Sweep 설정 업데이트"""
    from app.models.hd_wallet import SweepConfiguration
    
    config = await db.query(SweepConfiguration).filter(
        SweepConfiguration.partner_id == current_partner.id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Sweep config not found")
    
    # 설정 업데이트
    update_data = config_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    
    await db.commit()
    await db.refresh(config)
    
    return SweepConfigResponse.from_orm(config)

@router.post("/execute")
async def execute_sweep(
    background_tasks: BackgroundTasks,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """수동 Sweep 실행"""
    executor = SweepExecutorService(db)
    
    # 백그라운드에서 실행
    background_tasks.add_task(
        executor.execute_sweep_for_partner,
        current_partner.id
    )
    
    return {
        "status": "initiated",
        "message": "Sweep execution started in background"
    }

@router.get("/statistics", response_model=Dict)
async def get_sweep_statistics(
    period_days: int = 7,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """Sweep 통계 조회"""
    monitor = SweepMonitorService(db)
    
    stats = await monitor.get_sweep_statistics(
        partner_id=current_partner.id,
        period_days=period_days
    )
    
    return stats

@router.post("/deposit-address", response_model=DepositAddressResponse)
async def create_deposit_address(
    user_id: int,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """사용자 입금 주소 생성"""
    hd_service = HDWalletService(db)
    
    address = await hd_service.generate_deposit_address(
        partner_id=current_partner.id,
        user_id=user_id
    )
    
    return DepositAddressResponse(
        user_id=user_id,
        address=address.address,
        created_at=address.created_at
    )
```

#### 3.2 Sweep 스케줄러
```python
# app/services/sweep/sweep_scheduler.py
"""Sweep 자동 실행 스케줄러"""
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.hd_wallet import SweepConfiguration
from app.services.sweep.sweep_executor_service import SweepExecutorService
from app.core.config import settings
from app.utils.logger import logger

class SweepScheduler:
    """Sweep 자동 실행 스케줄러"""
    
    def __init__(self):
        self.engine = create_async_engine(settings.DATABASE_URL)
        self.AsyncSessionLocal = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        self.running = False
    
    async def start(self):
        """스케줄러 시작"""
        self.running = True
        logger.info("Sweep scheduler started")
        
        while self.running:
            try:
                await self._execute_scheduled_sweeps()
                await asyncio.sleep(60)  # 1분마다 확인
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)
    
    async def stop(self):
        """스케줄러 중지"""
        self.running = False
        logger.info("Sweep scheduler stopped")
    
    async def _execute_scheduled_sweeps(self):
        """스케줄된 Sweep 실행"""
        async with self.AsyncSessionLocal() as db:
            # 활성화된 모든 Sweep 설정 조회
            configs = await db.query(SweepConfiguration).filter(
                SweepConfiguration.is_enabled == True
            ).all()
            
            for config in configs:
                try:
                    # 마지막 실행 시간 확인
                    should_run = await self._should_run_sweep(config)
                    
                    if should_run:
                        executor = SweepExecutorService(db)
                        await executor.execute_sweep_for_partner(config.partner_id)
                        
                        logger.info(f"Executed sweep for partner {config.partner_id}")
                        
                except Exception as e:
                    logger.error(f"Failed to execute sweep for partner {config.partner_id}: {e}")
    
    async def _should_run_sweep(self, config: SweepConfiguration) -> bool:
        """Sweep 실행 여부 확인"""
        # TODO: 마지막 실행 시간과 스케줄 확인
        # 간단히 sweep_interval_minutes 기준으로 판단
        return True
```

### Phase 4: Sweep 대시보드 UI (1일)

#### 4.1 Sweep 관리 대시보드
```typescript
// frontend/components/sweep/SweepDashboard.tsx
import React, { useState, useEffect } from 'react';
import { Card, Button, Switch, Input, Select, Alert } from '@/components/ui';
import { RefreshCw, Settings, TrendingUp, AlertTriangle } from 'lucide-react';
import { useSweepConfig } from '@/hooks/useSweepConfig';
import { SweepStatistics } from './SweepStatistics';
import { DepositAddressList } from './DepositAddressList';

export const SweepDashboard: React.FC = () => {
  const { config, statistics, loading, updateConfig, executeSweep } = useSweepConfig();
  const [isExecuting, setIsExecuting] = useState(false);

  const handleManualSweep = async () => {
    setIsExecuting(true);
    try {
      await executeSweep();
      toast.success('Sweep 실행이 시작되었습니다');
    } catch (error) {
      toast.error('Sweep 실행 실패');
    } finally {
      setIsExecuting(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      {/* Sweep 상태 개요 */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Sweep 자동화</h2>
          <Button 
            onClick={handleManualSweep}
            disabled={isExecuting || !config?.is_enabled}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isExecuting ? 'animate-spin' : ''}`} />
            수동 실행
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-gray-600">오늘 Sweep</p>
            <p className="text-2xl font-bold">{statistics?.today?.count || 0}건</p>
            <p className="text-sm text-gray-500">
              {statistics?.today?.amount || 0} USDT
            </p>
          </div>
          
          <div className="text-center">
            <p className="text-gray-600">대기 중</p>
            <p className="text-2xl font-bold text-yellow-600">
              {statistics?.pending || 0}건
            </p>
          </div>
          
          <div className="text-center">
            <p className="text-gray-600">평균 가스비</p>
            <p className="text-2xl font-bold">
              {statistics?.avg_gas || 0} TRX
            </p>
          </div>
        </div>
      </Card>

      {/* Sweep 설정 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">
          <Settings className="w-5 h-5 inline mr-2" />
          Sweep 설정
        </h3>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span>Sweep 활성화</span>
            <Switch
              checked={config?.is_enabled || false}
              onChange={(checked) => updateConfig({ is_enabled: checked })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              대상 지갑
            </label>
            <Select
              value={config?.destination_wallet_id || ''}
              onChange={(e) => updateConfig({ 
                destination_wallet_id: parseInt(e.target.value) 
              })}
              disabled={!config?.is_enabled}
            >
              <option value="">선택하세요</option>
              {/* 지갑 목록 */}
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                최소 Sweep 금액 (USDT)
              </label>
              <Input
                type="number"
                value={config?.min_sweep_amount || 10}
                onChange={(e) => updateConfig({ 
                  min_sweep_amount: parseFloat(e.target.value) 
                })}
                disabled={!config?.is_enabled}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">
                Sweep 간격 (분)
              </label>
              <Input
                type="number"
                value={config?.sweep_interval_minutes || 60}
                onChange={(e) => updateConfig({ 
                  sweep_interval_minutes: parseInt(e.target.value) 
                })}
                disabled={!config?.is_enabled}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              즉시 Sweep 임계값 (USDT)
            </label>
            <Input
              type="number"
              value={config?.immediate_threshold || 1000}
              onChange={(e) => updateConfig({ 
                immediate_threshold: parseFloat(e.target.value) 
              })}
              disabled={!config?.is_enabled}
            />
            <p className="text-sm text-gray-500 mt-1">
              이 금액 이상 입금 시 즉시 Sweep 실행
            </p>
          </div>
        </div>
      </Card>

      {/* Sweep 통계 */}
      <SweepStatistics statistics={statistics} />

      {/* 입금 주소 목록 */}
      <DepositAddressList />
    </div>
  );
};
```

## 🔧 데이터베이스 마이그레이션

```sql
-- HD Wallet 마스터 테이블
CREATE TABLE hd_wallet_masters (
    id SERIAL PRIMARY KEY,
    partner_id INTEGER NOT NULL UNIQUE REFERENCES partners(id),
    encrypted_seed VARCHAR(500) NOT NULL,
    public_key VARCHAR(130) NOT NULL,
    derivation_path VARCHAR(100) DEFAULT 'm/44''/195''/0''/0',
    last_index INTEGER DEFAULT 0,
    encryption_method VARCHAR(50) DEFAULT 'AES-256-GCM',
    key_version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 사용자 입금 주소 테이블
CREATE TABLE user_deposit_addresses (
    id SERIAL PRIMARY KEY,
    hd_wallet_id INTEGER NOT NULL REFERENCES hd_wallet_masters(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    address VARCHAR(42) NOT NULL UNIQUE,
    derivation_index INTEGER NOT NULL,
    encrypted_private_key VARCHAR(500) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    total_received DECIMAL(18,6) DEFAULT 0,
    last_sweep_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_deposit_address_user (user_id),
    INDEX idx_deposit_address_active (is_active),
    INDEX idx_deposit_address (address)
);

-- Sweep 설정 테이블
CREATE TABLE sweep_configurations (
    id SERIAL PRIMARY KEY,
    partner_id INTEGER NOT NULL UNIQUE REFERENCES partners(id),
    destination_wallet_id INTEGER NOT NULL REFERENCES partner_wallets(id),
    is_enabled BOOLEAN DEFAULT TRUE,
    min_sweep_amount DECIMAL(18,6) DEFAULT 10,
    sweep_interval_minutes INTEGER DEFAULT 60,
    immediate_threshold DECIMAL(18,6) DEFAULT 1000,
    max_gas_price_sun NUMERIC(20,0) DEFAULT 1000,
    gas_optimization_enabled BOOLEAN DEFAULT TRUE,
    batch_enabled BOOLEAN DEFAULT TRUE,
    max_batch_size INTEGER DEFAULT 20,
    notification_enabled BOOLEAN DEFAULT TRUE,
    notification_channels JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sweep 로그 테이블
CREATE TABLE sweep_logs (
    id SERIAL PRIMARY KEY,
    deposit_address_id INTEGER NOT NULL REFERENCES user_deposit_addresses(id),
    sweep_amount DECIMAL(18,6) NOT NULL,
    gas_used NUMERIC(20,0),
    gas_price NUMERIC(20,0),
    tx_hash VARCHAR(66),
    status VARCHAR(20) DEFAULT 'pending',
    error_message VARCHAR(500),
    retry_count INTEGER DEFAULT 0,
    initiated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confirmed_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_sweep_logs_address (deposit_address_id),
    INDEX idx_sweep_logs_status (status),
    INDEX idx_sweep_logs_tx_hash (tx_hash)
);
```

## ✅ 검증 포인트

- [ ] HD Wallet이 안전하게 생성되고 암호화되는가?
- [ ] 사용자별 입금 주소가 정확히 파생되는가?
- [ ] 입금이 실시간으로 감지되는가?
- [ ] 최소 금액 및 스케줄에 따라 Sweep가 실행되는가?
- [ ] 즉시 Sweep 임계값이 작동하는가?
- [ ] 가스비 최적화가 정상 작동하는가?
- [ ] Sweep 실패 시 재시도가 되는가?
- [ ] 통계 및 모니터링이 정확한가?

## 🎉 기대 효과

1. **보안 강화**: 중앙 지갑으로 자산 집중 관리
2. **운영 효율**: 자동화를 통한 수동 작업 최소화
3. **비용 최적화**: 배치 처리 및 가스비 최적화
4. **투명성**: 모든 Sweep 이력 추적 가능
5. **유연성**: 파트너사별 맞춤 정책 설정

이 시스템을 통해 사용자 입금을 안전하고 효율적으로 중앙 관리할 수 있습니다.