"""
지갑 관리 서비스.
지갑 생성, 조회, 온체인 잔고 확인 등의 비즈니스 로직을 처리합니다.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.encryption import EncryptionService
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.tron import TronService
from app.models.user import User
from app.models.wallet import Wallet
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class WalletService:
    """지갑 관리 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.tron = TronService()
        self.encryption = EncryptionService()

    async def update_monitoring_status(self, user_id: int, enable: bool) -> Wallet:
        """지갑 모니터링 상태 변경"""
        result = await self.db.execute(select(Wallet).filter(Wallet.user_id == user_id))
        wallet = result.scalar_one_or_none()

        if not wallet:
            raise NotFoundError("Wallet not found")

        setattr(wallet, "is_monitored", enable)
        await self.db.flush()
        return wallet

    async def create_wallet(self, user_id: int) -> Wallet:
        """사용자 지갑 생성"""
        # 이미 지갑이 있는지 확인
        result = await self.db.execute(select(Wallet).filter(Wallet.user_id == user_id))
        existing_wallet = result.scalar_one_or_none()

        if existing_wallet:
            if getattr(existing_wallet, "is_active", False):
                raise ConflictError("User already has an active wallet")
            else:
                # 비활성 지갑이 있으면 재활성화
                setattr(existing_wallet, "is_active", True)
                await self.db.flush()
                return existing_wallet

        # 새 지갑 생성
        wallet_info = self.tron.generate_wallet()

        # 프라이빗 키 암호화
        encrypted_key, salt = self.encryption.encrypt(wallet_info["private_key"])

        # 지갑 정보 저장
        wallet = Wallet()
        for attr, value in {
            "user_id": user_id,
            "address": wallet_info["address"],
            "hex_address": wallet_info["hex_address"],
            "encrypted_private_key": encrypted_key,
            "encryption_salt": salt,
            "is_active": True,
            "is_monitored": True,
        }.items():
            setattr(wallet, attr, value)

        # 메타데이터 저장 (공개키 등)
        wallet.set_metadata(
            {
                "public_key": wallet_info["public_key"],
                "network": settings.TRON_NETWORK,
                "created_at": datetime.utcnow().isoformat(),
            }
        )

        self.db.add(wallet)
        await self.db.flush()

        # User 모델의 tron_address 필드가 있다면 업데이트
        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            # User 모델에 tron_address 필드가 있는지 확인하고 업데이트
            try:
                setattr(user, "tron_address", str(getattr(wallet, "address")))
            except AttributeError:
                # tron_address 필드가 없으면 무시
                pass

        logger.info(
            f"Wallet created for user {user_id}: {getattr(wallet, 'address', '')}"
        )
        return wallet

    async def get_wallet(self, user_id: int) -> Optional[Wallet]:
        """사용자 지갑 조회"""
        result = await self.db.execute(
            select(Wallet).filter(
                and_(Wallet.user_id == user_id, Wallet.is_active == True)
            )
        )
        return result.scalar_one_or_none()

    async def get_wallet_by_address(self, address: str) -> Optional[Wallet]:
        """주소로 지갑 조회"""
        result = await self.db.execute(
            select(Wallet).filter(
                and_(Wallet.address == address, Wallet.is_active == True)
            )
        )
        return result.scalar_one_or_none()

    def decrypt_private_key(self, wallet: Wallet) -> str:
        """프라이빗 키 복호화 (주의: 보안에 민감한 작업)"""
        return self.encryption.decrypt(
            str(getattr(wallet, "encrypted_private_key")),
            str(getattr(wallet, "encryption_salt")),
        )

    async def get_wallet_balance(self, wallet: Wallet) -> Dict[str, Any]:
        """온체인 지갑 잔고 조회"""
        address = str(getattr(wallet, "address"))

        # TRX 잔고
        trx_balance = await self.tron.get_balance(address, "TRX")

        # USDT 잔고
        usdt_balance = await self.tron.get_balance(address, "USDT")

        return {
            "address": address,
            "balances": {"TRX": trx_balance, "USDT": usdt_balance},
            "last_checked": datetime.utcnow().isoformat(),
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

    async def get_all_monitored_wallets(self) -> List[Wallet]:
        """모니터링 중인 모든 지갑 조회 (입금 감지용)"""
        result = await self.db.execute(
            select(Wallet).filter(
                and_(Wallet.is_active == True, Wallet.is_monitored == True)
            )
        )
        wallets = result.scalars().all()
        return list(wallets)
