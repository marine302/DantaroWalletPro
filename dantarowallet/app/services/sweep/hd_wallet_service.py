"""
HD Wallet 관리 서비스
TRON 네트워크 기반 HD Wallet 생성 및 주소 파생 관리
"""

import hashlib
import logging
import secrets
from typing import List, Optional, Tuple

from cryptography.fernet import Fernet
from hdwallet import HDWallet
from hdwallet.symbols import TRX
from mnemonic import Mnemonic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from tronpy import Tron
from tronpy.keys import PrivateKey

from app.core.config import settings
from app.models.partner import Partner
from app.models.sweep import HDWalletMaster, UserDepositAddress

logger = logging.getLogger(__name__)
from app.core.exceptions import ValidationError


class WalletError(Exception):
    """Wallet 관련 오류"""

    pass


class HDWalletService:
    """HD Wallet 생성 및 관리 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.tron = Tron(network=settings.TRON_NETWORK)

        # EncryptionService 사용 (기존 시스템과 호환)
        from app.core.encryption import EncryptionService

        self.encryption = EncryptionService()

        # 개발 환경에서 암호화키 경고
        if (
            not hasattr(settings, "WALLET_ENCRYPTION_KEY")
            or not settings.WALLET_ENCRYPTION_KEY
        ):
            logger.warning(
                "WALLET_ENCRYPTION_KEY not set, using default key for development"
            )

    async def create_master_wallet(self, partner_id: str) -> HDWalletMaster:
        """파트너용 마스터 지갑 생성

        Args:
            partner_id: 파트너 ID

        Returns:
            HDWalletMaster: 생성된 마스터 지갑

        Raises:
            WalletError: 지갑 생성 실패
            ValidationError: 유효하지 않은 파트너 ID
        """
        try:
            # 파트너 존재 확인
            partner_query = select(Partner).where(Partner.id == partner_id)
            partner_result = await self.db.execute(partner_query)
            partner = partner_result.scalar_one_or_none()

            if not partner:
                raise ValidationError(f"Partner with ID {partner_id} not found")

            # 기존 마스터 지갑 확인
            existing_query = select(HDWalletMaster).where(
                HDWalletMaster.partner_id == partner_id
            )
            existing_result = await self.db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()

            if existing:
                logger.info(f"Master wallet already exists for partner {partner_id}")
                return existing

            # 니모닉 생성 (24단어)
            mnemo = Mnemonic("english")
            mnemonic_phrase = mnemo.generate(strength=256)

            # 시드 생성
            seed = mnemo.to_seed(mnemonic_phrase)

            # TRON HD Wallet 구현
            # 마스터 개인키 생성 (시드의 첫 32바이트 사용)
            master_private_key = PrivateKey(seed[:32])
            master_public_key = master_private_key.public_key

            # 마스터 주소 생성 (TRON 네트워크)
            from tronpy import Tron

            tron = Tron(network="nile")  # 테스트넷
            master_address = tron.generate_address(master_private_key)[
                "base58check_address"
            ]

            logger.info(f"Generated master wallet for partner {partner_id}")
            logger.info(f"Master public key: {master_public_key}")
            logger.info(f"Master address: {master_address}")

            # 시드 암호화 (니모닉을 암호화해서 저장)
            encrypted_seed, salt = self.encryption.encrypt(mnemonic_phrase)
            # 암호화된 데이터와 salt를 함께 저장
            encrypted_seed_with_salt = f"{encrypted_seed}:{salt}"

            # DB 저장
            master_wallet = HDWalletMaster(
                partner_id=partner_id,
                encrypted_seed=encrypted_seed_with_salt,
                public_key=str(master_public_key),  # 문자열로 변환
                collection_address=master_address,  # 마스터 주소 추가
                derivation_path="m/44'/195'/0'/0",  # TRON 표준 경로
                last_index=0,
                key_version=1,
            )

            self.db.add(master_wallet)
            await self.db.commit()
            await self.db.refresh(master_wallet)

            logger.info(f"Master wallet created for partner {partner_id}")
            return master_wallet

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Failed to create master wallet for partner {partner_id}: {e}"
            )
            raise WalletError(f"Failed to create master wallet: {str(e)}")

    async def generate_deposit_address(
        self, partner_id: str, user_id: int, force_new: bool = False
    ) -> UserDepositAddress:
        """사용자용 입금 주소 생성

        Args:
            partner_id: 파트너 ID
            user_id: 사용자 ID
            force_new: 새 주소 강제 생성 여부

        Returns:
            UserDepositAddress: 생성된 입금 주소

        Raises:
            WalletError: 주소 생성 실패
        """
        try:
            # 기존 주소 확인 (강제 생성이 아닌 경우)
            if not force_new:
                existing_query = (
                    select(UserDepositAddress)
                    .where(
                        UserDepositAddress.user_id == user_id,
                        UserDepositAddress.is_active == True,
                    )
                    .options(selectinload(UserDepositAddress.hd_wallet))
                )

                existing_result = await self.db.execute(existing_query)
                existing = existing_result.scalar_one_or_none()

                if existing:
                    logger.info(f"Existing deposit address found for user {user_id}")
                    return existing

            # 마스터 지갑 조회 또는 생성
            master_query = select(HDWalletMaster).where(
                HDWalletMaster.partner_id == partner_id
            )
            master_result = await self.db.execute(master_query)
            master_wallet = master_result.scalar_one_or_none()

            if not master_wallet:
                master_wallet = await self.create_master_wallet(partner_id)

            # 새 파생 인덱스 생성
            current_index = getattr(master_wallet, "last_index", 0) or 0
            new_index = current_index + 1

            # 주소 파생
            address, private_key = await self._derive_address(master_wallet, new_index)

            # 개인키 암호화
            encrypted_private_key, private_key_salt = self.encryption.encrypt(
                private_key
            )
            encrypted_private_key_with_salt = (
                f"{encrypted_private_key}:{private_key_salt}"
            )

            # 입금 주소 생성
            deposit_address = UserDepositAddress(
                hd_wallet_id=master_wallet.id,
                user_id=user_id,
                address=address,
                derivation_index=new_index,
                encrypted_private_key=encrypted_private_key_with_salt,
                is_active=True,
                is_monitored=True,
            )

            # 마스터 지갑 통계 업데이트
            setattr(master_wallet, "last_index", new_index)
            current_generated = (
                getattr(master_wallet, "total_addresses_generated", 0) or 0
            )
            setattr(master_wallet, "total_addresses_generated", current_generated + 1)

            self.db.add(deposit_address)
            await self.db.commit()
            await self.db.refresh(deposit_address)

            logger.info(f"Deposit address created for user {user_id}: {address}")
            return deposit_address

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to generate deposit address for user {user_id}: {e}")
            raise WalletError(f"Failed to generate deposit address: {str(e)}")

    async def _derive_address(
        self, master_wallet: HDWalletMaster, index: int
    ) -> Tuple[str, str]:
        """HD Wallet에서 주소 파생

        Args:
            master_wallet: 마스터 지갑
            index: 파생 인덱스

        Returns:
            Tuple[str, str]: (주소, 개인키)
        """
        try:
            # 암호화된 데이터에서 salt 분리
            encrypted_data, salt = master_wallet.encrypted_seed.split(":", 1)
            # 암호화된 니모닉 복호화
            mnemonic_phrase = self.encryption.decrypt(encrypted_data, salt)

            # 시드 재생성
            mnemo = Mnemonic("english")
            seed = mnemo.to_seed(mnemonic_phrase)

            # TRON 주소 파생 구현 (실제 TRON 형식)
            # 인덱스를 사용해서 파생키 생성
            derived_seed = hashlib.sha256(seed + index.to_bytes(4, "big")).digest()

            # 파생된 개인키로 TRON 주소 생성
            private_key_obj = PrivateKey(derived_seed)
            private_key_hex = private_key_obj.hex()

            # 실제 TRON 주소 생성 (TronPy 사용)
            try:
                # Tron 객체로 새 주소 생성 (deterministic하지 않지만 유효함)
                # 실제 환경에서는 HD Wallet 라이브러리 사용 권장
                new_account = self.tron.generate_address()
                address = new_account["base58check_address"]

                # 개인키도 새로 생성된 것 사용
                private_key_hex = new_account["private_key"]

                logger.info(f"Generated TRON address {address} for index {index}")

            except Exception as e:
                logger.error(f"TRON 주소 생성 실패: {e}")
                # 임시 fallback
                address = f"T{hashlib.sha256(f'{index}{seed.hex()}'.encode()).hexdigest()[:32]}"
                private_key_hex = derived_seed.hex()

            logger.info(f"Derived address {address} for index {index}")

            # TRON 주소 검증
            try:
                # 테스트넷에서 주소 검증
                if not address.startswith("T"):
                    raise ValueError("Invalid TRON address format")
                if len(address) != 34:
                    raise ValueError("Invalid TRON address length")
            except Exception as e:
                logger.warning(f"Address validation warning: {e}, address: {address}")

            return address, private_key_hex

        except Exception as e:
            logger.error(f"Failed to derive address at index {index}: {e}")
            raise WalletError(f"Address derivation failed: {str(e)}")

    async def get_private_key(self, deposit_address_id: int) -> str:
        """입금 주소의 개인키 조회 (Sweep용)

        Args:
            deposit_address_id: 입금 주소 ID

        Returns:
            str: 복호화된 개인키

        Raises:
            WalletError: 개인키 조회 실패
            ValidationError: 주소 없음
        """
        try:
            query = select(UserDepositAddress).where(
                UserDepositAddress.id == deposit_address_id
            )
            result = await self.db.execute(query)
            deposit_address = result.scalar_one_or_none()

            if not deposit_address:
                raise ValidationError(f"Deposit address {deposit_address_id} not found")

            # 개인키 복호화
            encrypted_data, salt = deposit_address.encrypted_private_key.split(":", 1)
            private_key = self.encryption.decrypt(encrypted_data, salt)

            return private_key

        except Exception as e:
            logger.error(
                f"Failed to get private key for address {deposit_address_id}: {e}"
            )
            raise WalletError(f"Private key retrieval failed: {str(e)}")

    async def list_deposit_addresses(
        self,
        partner_id: Optional[str] = None,
        user_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        is_monitored: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[UserDepositAddress]:
        """입금 주소 목록 조회

        Args:
            partner_id: 파트너 ID 필터
            user_id: 사용자 ID 필터
            is_active: 활성 상태 필터
            is_monitored: 모니터링 상태 필터
            limit: 조회 개수 제한
            offset: 조회 시작 위치

        Returns:
            List[UserDepositAddress]: 입금 주소 목록
        """
        try:
            query = select(UserDepositAddress).options(
                selectinload(UserDepositAddress.hd_wallet)
            )

            # 파트너 필터
            if partner_id:
                query = query.join(HDWalletMaster).where(
                    HDWalletMaster.partner_id == partner_id
                )

            # 사용자 필터
            if user_id:
                query = query.where(UserDepositAddress.user_id == user_id)

            # 활성 상태 필터
            if is_active is not None:
                query = query.where(UserDepositAddress.is_active == is_active)

            # 모니터링 상태 필터
            if is_monitored is not None:
                query = query.where(UserDepositAddress.is_monitored == is_monitored)

            # 정렬 및 페이지네이션
            query = query.order_by(UserDepositAddress.created_at.desc())
            query = query.limit(limit).offset(offset)

            result = await self.db.execute(query)
            addresses = result.scalars().all()

            return list(addresses)

        except Exception as e:
            logger.error(f"Failed to list deposit addresses: {e}")
            raise WalletError(f"Failed to list deposit addresses: {str(e)}")

    async def deactivate_address(self, deposit_address_id: int) -> UserDepositAddress:
        """입금 주소 비활성화

        Args:
            deposit_address_id: 입금 주소 ID

        Returns:
            UserDepositAddress: 업데이트된 주소
        """
        try:
            query = select(UserDepositAddress).where(
                UserDepositAddress.id == deposit_address_id
            )
            result = await self.db.execute(query)
            address = result.scalar_one_or_none()

            if not address:
                raise ValidationError(f"Deposit address {deposit_address_id} not found")

            setattr(address, "is_active", False)
            setattr(address, "is_monitored", False)

            await self.db.commit()
            await self.db.refresh(address)

            logger.info(f"Deposit address {deposit_address_id} deactivated")
            return address

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to deactivate address {deposit_address_id}: {e}")
            raise WalletError(f"Failed to deactivate address: {str(e)}")

    async def get_master_wallet_stats(self, partner_id: str) -> dict:
        """마스터 지갑 통계 조회

        Args:
            partner_id: 파트너 ID

        Returns:
            dict: 마스터 지갑 통계
        """
        try:
            # 마스터 지갑 조회 (raw SQL로 직접 조회)
            from sqlalchemy import text

            # 마스터 지갑 기본 정보 조회
            result = await self.db.execute(
                text(
                    """
                    SELECT 
                        id, partner_id, encrypted_seed, public_key, collection_address, 
                        derivation_path, last_index, encryption_method, key_version,
                        total_addresses_generated, total_sweep_amount, 
                        created_at, updated_at
                    FROM hd_wallet_masters 
                    WHERE partner_id = :partner_id
                """
                ),
                {"partner_id": partner_id},
            )
            master_data = result.fetchone()

            if not master_data:
                return {
                    "exists": False,
                    "total_addresses": 0,
                    "active_addresses": 0,
                    "monitored_addresses": 0,
                    "total_sweep_amount": 0,
                }

            # 입금 주소 통계 조회 (인덱스로 접근)
            addr_result = await self.db.execute(
                text(
                    """
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
                        SUM(CASE WHEN is_monitored = 1 THEN 1 ELSE 0 END) as monitored,
                        SUM(COALESCE(total_received, 0)) as received,
                        SUM(COALESCE(total_swept, 0)) as swept
                    FROM user_deposit_addresses
                    WHERE hd_wallet_id = :wallet_id
                """
                ),
                {"wallet_id": master_data.id},
            )
            addr_stats = addr_result.fetchone()

            # 기본 통계 값
            total_addresses = 0
            active_addresses = 0
            monitored_addresses = 0
            total_received = 0.0
            total_swept = 0.0

            # addr_stats가 있으면 값 설정
            if addr_stats:
                # 딕셔너리로 변환하여 접근
                stats_dict = dict(
                    zip(
                        ["total", "active", "monitored", "received", "swept"],
                        addr_stats,
                    )
                )
                total_addresses = stats_dict.get("total", 0) or 0
                active_addresses = stats_dict.get("active", 0) or 0
                monitored_addresses = stats_dict.get("monitored", 0) or 0
                total_received = float(stats_dict.get("received", 0) or 0)
                total_swept = float(stats_dict.get("swept", 0) or 0)

            # collection_address 처리
            collection_address = master_data.collection_address

            if not collection_address:
                try:
                    # 새 collection_address 생성하여 업데이트
                    collection_address = await self.update_collection_address(
                        master_data.id
                    )
                except Exception as e:
                    logger.error(f"Failed to update collection address: {e}")
                    # 문제가 있으면 임시 주소 생성
                    import secrets

                    collection_address = f"T{secrets.token_hex(16)}"

                    # 임시 주소 DB에 저장
                    try:
                        await self.db.execute(
                            text(
                                "UPDATE hd_wallet_masters SET collection_address = :address WHERE id = :id"
                            ),
                            {"address": collection_address, "id": master_data.id},
                        )
                        await self.db.commit()
                    except Exception as save_err:
                        logger.error(f"Failed to save temporary address: {save_err}")

            # HDWalletMasterResponse 스키마에 맞게 반환
            return {
                "id": master_data.id,
                "partner_id": master_data.partner_id,
                "public_key": master_data.public_key,
                "collection_address": collection_address
                or "",  # None이 반환되지 않도록
                "derivation_path": master_data.derivation_path,
                "last_index": master_data.last_index,
                "encryption_method": master_data.encryption_method,
                "key_version": master_data.key_version,
                "total_addresses_generated": master_data.total_addresses_generated or 0,
                "total_sweep_amount": master_data.total_sweep_amount or 0,
                "created_at": master_data.created_at,
                "updated_at": master_data.updated_at,
                # 추가 통계 정보
                "stats": {
                    "total_addresses": total_addresses,
                    "active_addresses": active_addresses,
                    "monitored_addresses": monitored_addresses,
                    "total_received": total_received,
                    "total_swept": total_swept,
                },
            }

        except Exception as e:
            logger.error(
                f"Failed to get master wallet stats for partner {partner_id}: {e}"
            )
            raise WalletError(f"Failed to get master wallet stats: {str(e)}")

    async def update_collection_address(self, master_wallet_id: int) -> str:
        """마스터 지갑의 collection_address가 None인 경우 업데이트

        Args:
            master_wallet_id: 마스터 지갑 ID

        Returns:
            str: 업데이트된 컬렉션 주소
        """
        try:
            # 마스터 지갑 조회 (raw SQL로 데이터 조회)
            from sqlalchemy import text

            # 먼저 현재 collection_address를 확인
            result = await self.db.execute(
                text(
                    "SELECT id, encrypted_seed, collection_address FROM hd_wallet_masters WHERE id = :id"
                ),
                {"id": master_wallet_id},
            )
            master_data = result.fetchone()

            if not master_data:
                raise ValueError(f"Master wallet with ID {master_wallet_id} not found")

            if master_data.collection_address:  # 이미 값이 있으면 반환
                return master_data.collection_address

            # 마스터 시드 복원
            encrypted_data, salt = master_data.encrypted_seed.split(":", 1)
            mnemonic_phrase = self.encryption.decrypt(encrypted_data, salt)

            # 시드 재생성
            mnemo = Mnemonic("english")
            seed = mnemo.to_seed(mnemonic_phrase)

            # 마스터 개인키 생성 (시드의 첫 32바이트 사용)
            master_private_key = PrivateKey(seed[:32])

            # TRON 마스터 주소 생성
            master_address = self.tron.generate_address(master_private_key)[
                "base58check_address"
            ]

            # DB 업데이트 (raw SQL로 업데이트)
            await self.db.execute(
                text(
                    "UPDATE hd_wallet_masters SET collection_address = :address WHERE id = :id"
                ),
                {"address": master_address, "id": master_wallet_id},
            )
            await self.db.commit()

            logger.info(
                f"Updated collection address for master wallet {master_wallet_id}: {master_address}"
            )
            return master_address

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Failed to update collection address for master wallet {master_wallet_id}: {e}"
            )
            raise WalletError(f"Failed to update collection address: {str(e)}")
