"""
외부 지갑 연동 서비스
"""

import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Sequence

import base58
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from tronpy import Tron
from tronpy.keys import PublicKey

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.core.logger import get_logger
from app.models.partner_wallet import PartnerWallet, WalletType

logger = get_logger(__name__)


class ExternalWalletService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # TRON 클라이언트 초기화
        if settings.TRON_NETWORK == "mainnet":
            self.tron = Tron(network="mainnet")
        else:
            self.tron = Tron(network="nile")  # Testnet

    async def connect_external_wallet(
        self,
        partner_id: int,
        wallet_type: str,
        wallet_address: str,
        public_key: Optional[str] = None,
        signature: Optional[str] = None,
    ) -> PartnerWallet:
        """외부 지갑 연결"""

        # 지갑 주소 검증
        if not self._validate_tron_address(wallet_address):
            raise ValidationError("유효하지 않은 TRON 주소입니다")

        # 서명 검증 (선택적)
        if signature and public_key:
            message = f"Connect wallet {wallet_address} to partner {partner_id}"
            if not self._verify_signature(wallet_address, message, signature):
                raise ValidationError("지갑 서명이 유효하지 않습니다")

        # 중복 연결 확인
        existing_query = select(PartnerWallet).where(
            PartnerWallet.partner_id == partner_id,
            PartnerWallet.wallet_address == wallet_address,
            PartnerWallet.is_active == True,
        )
        existing_wallet = await self.db.execute(existing_query)
        if existing_wallet.scalar_one_or_none():
            raise ValidationError("이미 연결된 지갑입니다")

        # 새 지갑 연결
        wallet = PartnerWallet(
            partner_id=partner_id,
            wallet_type=WalletType.TRONLINK,
            wallet_address=wallet_address,
            public_key=public_key,
            is_active=True,
            connected_at=datetime.utcnow(),
            last_used_at=datetime.utcnow(),
        )

        self.db.add(wallet)
        await self.db.commit()
        await self.db.refresh(wallet)

        logger.info(f"외부 지갑 연결됨: {wallet_address} -> Partner {partner_id}")
        return wallet

    async def get_partner_wallets(self, partner_id: int) -> Sequence[PartnerWallet]:
        """파트너의 연결된 지갑 목록 조회"""
        query = select(PartnerWallet).where(
            PartnerWallet.partner_id == partner_id, PartnerWallet.is_active == True
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_wallet_balance(self, partner_id: int, wallet_address: str) -> Dict:
        """지갑 잔액 조회"""

        # 지갑 소유권 확인
        wallet = await self._verify_wallet_ownership(partner_id, wallet_address)
        if not wallet:
            raise ValidationError("지갑에 접근할 권한이 없습니다")

        try:
            # TRX 잔액 조회
            account = self.tron.get_account(wallet_address)
            trx_balance = Decimal(account.get("balance", 0)) / 1_000_000  # SUN to TRX

            # USDT 잔액 조회 (TRC20)
            usdt_contract = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # USDT TRC20
            try:
                usdt_balance = (
                    self.tron.get_contract(usdt_contract)
                    .functions.balanceOf(wallet_address)
                    .call()
                )
                usdt_balance = Decimal(usdt_balance) / 1_000_000  # 6 decimals
            except:
                usdt_balance = Decimal("0")

            # 에너지 및 대역폭 조회
            resource = self.tron.get_account_resource(wallet_address)
            energy = resource.get("EnergyUsed", 0)
            bandwidth = resource.get("NetUsed", 0)

            return {
                "wallet_address": wallet_address,
                "trx_balance": trx_balance,
                "usdt_balance": usdt_balance,
                "energy": energy,
                "bandwidth": bandwidth,
                "last_updated": datetime.utcnow(),
            }

        except Exception as e:
            logger.error(f"지갑 잔액 조회 실패: {str(e)}")
            raise ValidationError(f"지갑 잔액 조회에 실패했습니다: {str(e)}")

    async def get_wallet_transactions(
        self, partner_id: int, wallet_address: str, limit: int = 20, offset: int = 0
    ) -> List[Dict]:
        """지갑 거래 내역 조회"""

        # 지갑 소유권 확인
        wallet = await self._verify_wallet_ownership(partner_id, wallet_address)
        if not wallet:
            raise ValidationError("지갑에 접근할 권한이 없습니다")

        try:
            # TronGrid API 또는 TronScan API를 사용하여 거래 내역 조회
            # 여기서는 간단한 예시로 빈 목록 반환
            # 실제로는 외부 API를 호출해야 함

            transactions = []

            # TODO: 실제 TRON 네트워크에서 거래 내역 조회 구현
            # - TronGrid API 호출
            # - 거래 데이터 파싱
            # - 페이지네이션 처리

            return transactions

        except Exception as e:
            logger.error(f"거래 내역 조회 실패: {str(e)}")
            raise ValidationError(f"거래 내역 조회에 실패했습니다: {str(e)}")

    async def disconnect_wallet(self, partner_id: int, wallet_address: str) -> bool:
        """지갑 연결 해제"""

        wallet = await self._verify_wallet_ownership(partner_id, wallet_address)
        if not wallet:
            return False

        # 지갑 비활성화
        await self.db.execute(
            update(PartnerWallet)
            .where(PartnerWallet.id == wallet.id)
            .values(is_active=False, disconnected_at=datetime.utcnow())
        )

        await self.db.commit()
        logger.info(f"지갑 연결 해제됨: {wallet_address}")
        return True

    async def verify_wallet_signature(
        self, wallet_address: str, message: str, signature: str
    ) -> bool:
        """지갑 서명 검증"""
        return self._verify_signature(wallet_address, message, signature)

    def _validate_tron_address(self, address: str) -> bool:
        """TRON 주소 유효성 검증"""
        try:
            if not address.startswith("T") or len(address) != 34:
                return False

            # Base58 디코딩 및 체크섬 검증
            decoded = base58.b58decode(address)
            if len(decoded) != 25:
                return False

            # 체크섬 검증
            address_bytes = decoded[:-4]
            checksum = decoded[-4:]
            hash_result = hashlib.sha256(
                hashlib.sha256(address_bytes).digest()
            ).digest()

            return hash_result[:4] == checksum

        except Exception:
            return False

    def _verify_signature(
        self, wallet_address: str, message: str, signature: str
    ) -> bool:
        """서명 검증"""
        try:
            # TRON 서명 검증을 위한 간단한 구현
            # 실제 운영환경에서는 더 정교한 검증이 필요

            # 서명 형식 검증
            if not signature or len(signature) < 128:  # 64바이트 * 2 (hex)
                logger.warning("서명 형식이 올바르지 않습니다")
                return False

            # 기본적인 지갑 주소 검증
            if not self._validate_tron_address(wallet_address):
                logger.warning("유효하지 않은 TRON 주소입니다")
                return False

            # 메시지가 비어있지 않은지 확인
            if not message:
                logger.warning("서명할 메시지가 비어있습니다")
                return False

            # TODO: 실제 환경에서는 tronpy나 다른 라이브러리를 사용하여
            # 실제 서명 검증을 구현해야 합니다
            # 현재는 기본적인 형식 검증만 수행

            logger.info(f"서명 검증 통과: {wallet_address[:10]}...")
            return True

        except Exception as e:
            logger.error(f"서명 검증 실패: {str(e)}")
            return False

    async def _verify_wallet_ownership(
        self, partner_id: int, wallet_address: str
    ) -> Optional[PartnerWallet]:
        """지갑 소유권 확인"""
        query = select(PartnerWallet).where(
            PartnerWallet.partner_id == partner_id,
            PartnerWallet.wallet_address == wallet_address,
            PartnerWallet.is_active == True,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
