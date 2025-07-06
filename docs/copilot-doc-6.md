# Copilot 문서 #6: TRON 지갑 관리 시스템

## 목표
TRON 지갑 주소 생성 및 관리 시스템을 구현합니다. 사용자별 고유 지갑 주소 생성, 프라이빗 키 암호화 저장, 지갑 정보 조회를 포함합니다.

## 전제 조건
- Copilot 문서 #1-5가 완료되어 있어야 합니다.
- tronpy 라이브러리가 설치되어 있어야 합니다.
- 테스트넷(Nile)에서 작동하도록 설정합니다.

## 상세 지시사항

### 1. 지갑 모델 추가 (app/models/wallet.py)

```python
from sqlalchemy import Column, String, Boolean, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from typing import Optional
import json

class Wallet(BaseModel):
    """지갑 모델"""
    
    # 사용자 정보
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # 지갑 정보
    address = Column(String(42), unique=True, nullable=False, index=True)
    hex_address = Column(String(42), unique=True, nullable=False)  # TRON hex format
    
    # 암호화된 프라이빗 키 (AES-256 암호화)
    encrypted_private_key = Column(Text, nullable=False)
    encryption_salt = Column(String(32), nullable=False)
    
    # 지갑 상태
    is_active = Column(Boolean, default=True, nullable=False)
    is_monitored = Column(Boolean, default=True, nullable=False)  # 입금 모니터링 여부
    
    # 추가 정보
    metadata = Column(Text, nullable=True)  # JSON 형태의 추가 데이터
    
    # 관계
    # user = relationship("User", back_populates="wallet", uselist=False)
    
    # 인덱스
    __table_args__ = (
        Index('idx_wallet_user_active', 'user_id', 'is_active'),
        Index('idx_wallet_address_active', 'address', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Wallet(user_id={self.user_id}, address={self.address})>"
    
    def get_metadata(self) -> dict:
        """메타데이터 파싱"""
        if self.metadata:
            return json.loads(self.metadata)
        return {}
    
    def set_metadata(self, data: dict):
        """메타데이터 설정"""
        self.metadata = json.dumps(data)
```

### 2. 암호화 유틸리티 (app/core/encryption.py)

```python
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from app.core.config import settings
import secrets

class EncryptionService:
    """암호화/복호화 서비스"""
    
    @staticmethod
    def generate_salt() -> str:
        """솔트 생성"""
        return secrets.token_hex(16)  # 32 characters
    
    @staticmethod
    def derive_key(password: str, salt: str) -> bytes:
        """마스터 키에서 암호화 키 유도"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    @classmethod
    def encrypt(cls, data: str, salt: Optional[str] = None) -> tuple[str, str]:
        """데이터 암호화"""
        if salt is None:
            salt = cls.generate_salt()
        
        key = cls.derive_key(settings.WALLET_ENCRYPTION_KEY, salt)
        f = Fernet(key)
        encrypted = f.encrypt(data.encode())
        
        return base64.b64encode(encrypted).decode(), salt
    
    @classmethod
    def decrypt(cls, encrypted_data: str, salt: str) -> str:
        """데이터 복호화"""
        key = cls.derive_key(settings.WALLET_ENCRYPTION_KEY, salt)
        f = Fernet(key)
        
        encrypted = base64.b64decode(encrypted_data.encode())
        decrypted = f.decrypt(encrypted)
        
        return decrypted.decode()
    
    @classmethod
    def encrypt_dict(cls, data: dict, salt: Optional[str] = None) -> tuple[str, str]:
        """딕셔너리 암호화"""
        import json
        json_str = json.dumps(data)
        return cls.encrypt(json_str, salt)
    
    @classmethod
    def decrypt_dict(cls, encrypted_data: str, salt: str) -> dict:
        """딕셔너리 복호화"""
        import json
        json_str = cls.decrypt(encrypted_data, salt)
        return json.loads(json_str)
```

### 3. TRON 유틸리티 (app/core/tron.py)

```python
from tronpy import Tron
from tronpy.keys import PrivateKey
from typing import Dict, Any, Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class TronService:
    """TRON 블록체인 서비스"""
    
    def __init__(self):
        # 네트워크 설정 (테스트넷: nile, 메인넷: mainnet)
        if settings.TRON_NETWORK == "nile":
            self.client = Tron(network="nile")
        else:
            self.client = Tron()
        
        logger.info(f"TronService initialized with network: {settings.TRON_NETWORK}")
    
    def generate_wallet(self) -> Dict[str, str]:
        """새 지갑 생성"""
        # 프라이빗 키 생성
        private_key = PrivateKey.random()
        
        # 주소 생성
        address = private_key.public_key.to_base58check_address()
        hex_address = private_key.public_key.to_hex_address()
        
        wallet_info = {
            "address": address,
            "hex_address": hex_address,
            "private_key": private_key.hex(),
            "public_key": private_key.public_key.hex()
        }
        
        logger.info(f"New wallet generated: {address}")
        return wallet_info
    
    async def get_balance(self, address: str, token: str = "USDT") -> Dict[str, Any]:
        """지갑 잔고 조회"""
        try:
            if token == "TRX":
                # TRX 잔고
                balance = self.client.get_account_balance(address)
                return {
                    "token": "TRX",
                    "balance": balance,
                    "decimals": 6
                }
            else:
                # TRC20 토큰 잔고 (USDT)
                # 테스트넷 USDT 컨트랙트 주소
                if settings.TRON_NETWORK == "nile":
                    contract_address = "TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf"  # Nile testnet USDT
                else:
                    contract_address = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # Mainnet USDT
                
                contract = self.client.get_contract(contract_address)
                balance = contract.functions.balanceOf(address)
                decimals = contract.functions.decimals()
                
                return {
                    "token": token,
                    "balance": balance,
                    "decimals": decimals,
                    "formatted": balance / (10 ** decimals)
                }
        except Exception as e:
            logger.error(f"Error getting balance for {address}: {e}")
            return {
                "token": token,
                "balance": 0,
                "decimals": 6,
                "error": str(e)
            }
    
    async def validate_address(self, address: str) -> bool:
        """주소 유효성 검증"""
        try:
            # TRON 주소 형식 검증
            if not address.startswith('T') or len(address) != 34:
                return False
            
            # Base58 디코딩 시도
            from base58 import b58decode_check
            b58decode_check(address)
            return True
        except Exception:
            return False
    
    async def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """트랜잭션 정보 조회"""
        try:
            tx = self.client.get_transaction(tx_hash)
            return tx
        except Exception as e:
            logger.error(f"Error getting transaction {tx_hash}: {e}")
            return None
    
    def get_block_number(self) -> int:
        """현재 블록 번호 조회"""
        try:
            block = self.client.get_latest_block()
            return block["block_header"]["raw_data"]["number"]
        except Exception as e:
            logger.error(f"Error getting block number: {e}")
            return 0
```

### 4. 지갑 서비스 (app/services/wallet_service.py)

```python
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging

from app.models.user import User
from app.models.wallet import Wallet
from app.core.tron import TronService
from app.core.encryption import EncryptionService
from app.core.exceptions import ConflictError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)

class WalletService:
    """지갑 관리 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tron = TronService()
        self.encryption = EncryptionService()
    
    async def create_wallet(self, user_id: int) -> Wallet:
        """사용자 지갑 생성"""
        # 이미 지갑이 있는지 확인
        result = await self.db.execute(
            select(Wallet).filter(Wallet.user_id == user_id)
        )
        existing_wallet = result.scalar_one_or_none()
        
        if existing_wallet:
            if existing_wallet.is_active:
                raise ConflictError("User already has an active wallet")
            else:
                # 비활성 지갑이 있으면 재활성화
                existing_wallet.is_active = True
                await self.db.flush()
                return existing_wallet
        
        # 새 지갑 생성
        wallet_info = self.tron.generate_wallet()
        
        # 프라이빗 키 암호화
        encrypted_key, salt = self.encryption.encrypt(wallet_info["private_key"])
        
        # 지갑 정보 저장
        wallet = Wallet(
            user_id=user_id,
            address=wallet_info["address"],
            hex_address=wallet_info["hex_address"],
            encrypted_private_key=encrypted_key,
            encryption_salt=salt,
            is_active=True,
            is_monitored=True
        )
        
        # 메타데이터 저장 (공개키 등)
        wallet.set_metadata({
            "public_key": wallet_info["public_key"],
            "network": settings.TRON_NETWORK,
            "created_at": datetime.utcnow().isoformat()
        })
        
        self.db.add(wallet)
        await self.db.flush()
        
        # User 모델의 tron_address 업데이트
        result = await self.db.execute(
            select(User).filter(User.id == user_id)
        )
        user = result.scalar_one()
        user.tron_address = wallet.address
        
        logger.info(f"Wallet created for user {user_id}: {wallet.address}")
        return wallet
    
    async def get_wallet(self, user_id: int) -> Optional[Wallet]:
        """사용자 지갑 조회"""
        result = await self.db.execute(
            select(Wallet).filter(
                and_(
                    Wallet.user_id == user_id,
                    Wallet.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_wallet_by_address(self, address: str) -> Optional[Wallet]:
        """주소로 지갑 조회"""
        result = await self.db.execute(
            select(Wallet).filter(
                and_(
                    Wallet.address == address,
                    Wallet.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    def decrypt_private_key(self, wallet: Wallet) -> str:
        """프라이빗 키 복호화 (주의: 보안에 민감한 작업)"""
        return self.encryption.decrypt(
            wallet.encrypted_private_key,
            wallet.encryption_salt
        )
    
    async def get_wallet_balance(self, wallet: Wallet) -> Dict[str, Any]:
        """온체인 지갑 잔고 조회"""
        # TRX 잔고
        trx_balance = await self.tron.get_balance(wallet.address, "TRX")
        
        # USDT 잔고
        usdt_balance = await self.tron.get_balance(wallet.address, "USDT")
        
        return {
            "address": wallet.address,
            "balances": {
                "TRX": trx_balance,
                "USDT": usdt_balance
            },
            "last_checked": datetime.utcnow().isoformat()
        }
    
    async def validate_withdrawal_address(self, address: str) -> bool:
        """출금 주소 유효성 검증"""
        # 기본 형식 검증
        is_valid = await self.tron.validate_address(address)
        if not is_valid:
            return False
        
        # 내부 주소인지 확인 (내부 주소로는 출금 불가)
        internal_wallet = await self.get_wallet_by_address(address)
        if internal_wallet:
            raise ValidationError("Cannot withdraw to internal wallet address")
        
        return True
    
    async def get_all_monitored_wallets(self) -> list[Wallet]:
        """모니터링 중인 모든 지갑 조회 (입금 감지용)"""
        result = await self.db.execute(
            select(Wallet).filter(
                and_(
                    Wallet.is_active == True,
                    Wallet.is_monitored == True
                )
            )
        )
        return result.scalars().all()
    
    async def toggle_monitoring(self, user_id: int, enable: bool) -> Wallet:
        """지갑 모니터링 활성화/비활성화"""
        wallet = await self.get_wallet(user_id)
        if not wallet:
            raise NotFoundError("Wallet not found")
        
        wallet.is_monitored = enable
        await self.db.flush()
        
        logger.info(f"Wallet monitoring {'enabled' if enable else 'disabled'} for user {user_id}")
        return wallet
```

### 5. 지갑 스키마 (app/schemas/wallet.py)

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class WalletResponse(BaseModel):
    """지갑 응답 스키마"""
    address: str
    hex_address: str
    is_active: bool
    is_monitored: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class WalletCreateResponse(BaseModel):
    """지갑 생성 응답 스키마"""
    address: str
    hex_address: str
    network: str
    message: str = "Wallet created successfully"

class WalletBalanceResponse(BaseModel):
    """지갑 잔고 응답 스키마"""
    address: str
    balances: Dict[str, Dict[str, Any]]
    last_checked: str

class AddressValidationRequest(BaseModel):
    """주소 검증 요청 스키마"""
    address: str = Field(..., min_length=34, max_length=34)

class AddressValidationResponse(BaseModel):
    """주소 검증 응답 스키마"""
    address: str
    is_valid: bool
    is_internal: bool = False
    message: Optional[str] = None

class WalletMonitoringRequest(BaseModel):
    """모니터링 설정 요청 스키마"""
    enable: bool
```

### 6. 지갑 엔드포인트 (app/api/v1/endpoints/wallet.py)

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.api import deps
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.services.wallet_service import WalletService
from app.schemas.wallet import (
    WalletResponse, WalletCreateResponse, WalletBalanceResponse,
    AddressValidationRequest, AddressValidationResponse,
    WalletMonitoringRequest
)
from app.core.config import settings
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/create", response_model=WalletCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_wallet(
    current_user: User = Depends(deps.get_current_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """사용자 지갑 생성"""
    service = WalletService(db)
    wallet = await service.create_wallet(current_user.id)
    await db.commit()
    
    return WalletCreateResponse(
        address=wallet.address,
        hex_address=wallet.hex_address,
        network=settings.TRON_NETWORK
    )

@router.get("/", response_model=WalletResponse)
async def get_wallet(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """현재 사용자 지갑 정보 조회"""
    service = WalletService(db)
    wallet = await service.get_wallet(current_user.id)
    
    if not wallet:
        raise NotFoundError("Wallet not found. Please create a wallet first.")
    
    return wallet

@router.get("/balance", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """지갑 온체인 잔고 조회"""
    service = WalletService(db)
    wallet = await service.get_wallet(current_user.id)
    
    if not wallet:
        raise NotFoundError("Wallet not found")
    
    balance_info = await service.get_wallet_balance(wallet)
    return balance_info

@router.post("/validate-address", response_model=AddressValidationResponse)
async def validate_address(
    request: AddressValidationRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """TRON 주소 유효성 검증"""
    service = WalletService(db)
    
    # 기본 유효성 검증
    is_valid = await service.tron.validate_address(request.address)
    
    if not is_valid:
        return AddressValidationResponse(
            address=request.address,
            is_valid=False,
            message="Invalid TRON address format"
        )
    
    # 내부 주소인지 확인
    internal_wallet = await service.get_wallet_by_address(request.address)
    is_internal = internal_wallet is not None
    
    return AddressValidationResponse(
        address=request.address,
        is_valid=True,
        is_internal=is_internal,
        message="Internal wallet address" if is_internal else "Valid external address"
    )

@router.post("/monitoring", response_model=WalletResponse)
async def toggle_monitoring(
    request: WalletMonitoringRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """지갑 모니터링 설정 변경"""
    service = WalletService(db)
    wallet = await service.toggle_monitoring(current_user.id, request.enable)
    await db.commit()
    
    return wallet

@router.get("/network-info")
async def get_network_info(
    current_user: User = Depends(deps.get_current_active_user)
):
    """네트워크 정보 조회"""
    service = WalletService(None)  # DB 불필요
    
    block_number = service.tron.get_block_number()
    
    return {
        "network": settings.TRON_NETWORK,
        "current_block": block_number,
        "usdt_contract": "TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf" if settings.TRON_NETWORK == "nile" else "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
        "explorer_url": "https://nile.tronscan.org" if settings.TRON_NETWORK == "nile" else "https://tronscan.org"
    }
```

### 7. API 라우터 업데이트 (app/api/v1/api.py)

```python
from fastapi import APIRouter
from app.api.v1.endpoints import auth, balance, wallet  # wallet 추가

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(balance.router, prefix="/balance", tags=["balance"])
api_router.include_router(wallet.router, prefix="/wallet", tags=["wallet"])  # 추가

@api_router.get("/test")
async def test_endpoint():
    return {"message": "API v1 is working"}
```

### 8. 모델 업데이트 (app/models/__init__.py)

```python
from app.models.base import BaseModel
from app.models.user import User
from app.models.balance import Balance
from app.models.transaction import Transaction, TransactionType, TransactionStatus, TransactionDirection
from app.models.wallet import Wallet

__all__ = [
    "BaseModel", "User", "Balance", "Transaction", "Wallet",
    "TransactionType", "TransactionStatus", "TransactionDirection"
]
```

### 9. 환경 변수 추가 (.env)

```env
# 기존 변수들...

# Wallet Encryption
WALLET_ENCRYPTION_KEY=your-very-secure-wallet-encryption-key-32-chars

# TRON
TRON_NETWORK=nile
TRON_API_KEY=your-trongrid-api-key-if-needed
```

### 10. 설정 파일 업데이트 (app/core/config.py)

```python
class Settings(BaseSettings):
    # 기존 설정들...
    
    # Wallet
    WALLET_ENCRYPTION_KEY: str
    
    # TRON
    TRON_NETWORK: str = "nile"
    TRON_API_KEY: Optional[str] = None
    
    # 기존 설정 계속...
```

### 11. 마이그레이션 생성

```bash
# Wallet 테이블 추가
poetry run alembic revision --autogenerate -m "Add wallet table"
poetry run alembic upgrade head
```

### 12. 지갑 테스트 (tests/test_wallet.py)

```python
import pytest
from httpx import AsyncClient
from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select

async def get_auth_headers(email: str = "wallet_test@example.com"):
    """인증 헤더 생성 헬퍼"""
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
        
        # 이메일 인증 처리 (테스트용)
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
        return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_create_wallet():
    """지갑 생성 테스트"""
    headers = await get_auth_headers("create_wallet@example.com")
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/wallet/create", headers=headers)
    
    assert response.status_code == 201
    data = response.json()
    assert "address" in data
    assert data["address"].startswith("T")
    assert len(data["address"]) == 34
    assert data["network"] == "nile"

@pytest.mark.asyncio
async def test_duplicate_wallet_creation():
    """중복 지갑 생성 방지 테스트"""
    headers = await get_auth_headers("duplicate_wallet@example.com")
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 첫 번째 생성
        response1 = await client.post("/api/v1/wallet/create", headers=headers)
        assert response1.status_code == 201
        
        # 두 번째 생성 시도
        response2 = await client.post("/api/v1/wallet/create", headers=headers)
        assert response2.status_code == 409

@pytest.mark.asyncio
async def test_get_wallet():
    """지갑 정보 조회 테스트"""
    headers = await get_auth_headers("get_wallet@example.com")
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 지갑 생성
        await client.post("/api/v1/wallet/create", headers=headers)
        
        # 지갑 조회
        response = await client.get("/api/v1/wallet/", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "address" in data
    assert "is_active" in data
    assert data["is_active"] is True

@pytest.mark.asyncio
async def test_wallet_balance():
    """지갑 잔고 조회 테스트"""
    headers = await get_auth_headers("balance_check@example.com")
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 지갑 생성
        await client.post("/api/v1/wallet/create", headers=headers)
        
        # 잔고 조회
        response = await client.get("/api/v1/wallet/balance", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "balances" in data
    assert "TRX" in data["balances"]
    assert "USDT" in data["balances"]

@pytest.mark.asyncio
async def test_address_validation():
    """주소 유효성 검증 테스트"""
    headers = await get_auth_headers("validate_test@example.com")
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 유효한 주소
        response = await client.post(
            "/api/v1/wallet/validate-address",
            json={"address": "TN9RRaXkCFtTXRso2GdTZxSxxwufzxLQPP"},
            headers=headers
        )
        assert response.status_code == 200
        assert response.json()["is_valid"] is True
        
        # 무효한 주소
        response = await client.post(
            "/api/v1/wallet/validate-address",
            json={"address": "invalid_address"},
            headers=headers
        )
        assert response.status_code == 422  # Pydantic validation

@pytest.mark.asyncio
async def test_wallet_monitoring_toggle():
    """지갑 모니터링 토글 테스트"""
    headers = await get_auth_headers("monitoring_test@example.com")
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 지갑 생성
        await client.post("/api/v1/wallet/create", headers=headers)
        
        # 모니터링 비활성화
        response = await client.post(
            "/api/v1/wallet/monitoring",
            json={"enable": False},
            headers=headers
        )
        assert response.status_code == 200
        assert response.json()["is_monitored"] is False
        
        # 모니터링 재활성화
        response = await client.post(
            "/api/v1/wallet/monitoring",
            json={"enable": True},
            headers=headers
        )
        assert response.status_code == 200
        assert response.json()["is_monitored"] is True

@pytest.mark.asyncio
async def test_network_info():
    """네트워크 정보 조회 테스트"""
    headers = await get_auth_headers("network_test@example.com")
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/wallet/network-info", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["network"] == "nile"
    assert "current_block" in data
    assert "usdt_contract" in data
```

## 실행 및 검증

1. 환경 변수 설정 확인 (.env 파일)

2. 마이그레이션 실행:
   ```bash
   make db-upgrade
   ```

3. 서버 재시작:
   ```bash
   make dev
   ```

4. 테스트 실행:
   ```bash
   make test tests/test_wallet.py
   ```

5. API 문서에서 지갑 엔드포인트 확인:
   http://localhost:8000/api/v1/docs

## 검증 포인트

- [ ] 지갑 생성이 정상 작동하는가?
- [ ] TRON 주소가 올바른 형식으로 생성되는가?
- [ ] 프라이빗 키가 안전하게 암호화되어 저장되는가?
- [ ] 중복 지갑 생성이 방지되는가?
- [ ] 지갑 정보 조회가 작동하는가?
- [ ] 주소 유효성 검증이 작동하는가?
- [ ] 온체인 잔고 조회가 작동하는가? (테스트넷)
- [ ] 모든 테스트가 통과하는가?

## 주의사항

- 이 구현은 **테스트넷(Nile)**에서 작동하도록 설정되어 있습니다.
- 실제 운영 환경에서는 추가적인 보안 조치가 필요합니다:
  - HSM(Hardware Security Module) 사용
  - 프라이빗 키 분산 저장
  - 다중 서명 구현
  - 콜드 월렛 분리

이 문서를 완료하면 TRON 지갑 생성 및 관리 시스템이 완성되며, 사용자별로 고유한 입금 주소를 제공할 수 있습니다.