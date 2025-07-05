"""
TRON 지갑 관리 서비스.
지갑 생성, 주소 검증 등의 기능을 담당합니다.
"""
import logging
from typing import Dict

from app.core.tron.constants import TronAddressValidator, TronConstants
from app.core.tron.network import TronNetworkService
from tronpy.keys import PrivateKey

logger = logging.getLogger(__name__)


class TronWalletManager(TronNetworkService):
    """TRON 지갑 관리 클래스"""
    
    def generate_wallet(self) -> Dict[str, str]:
        """새 지갑 생성"""
        try:
            # 프라이빗 키 생성
            private_key = PrivateKey.random()
            public_key = private_key.public_key
            
            # 주소 생성
            address = public_key.to_base58check_address()
            hex_address = public_key.to_hex_address()
            
            wallet_info = {
                "address": address,
                "hex_address": hex_address,
                "private_key": private_key.hex(),
                "public_key": public_key.hex(),
            }
            
            logger.info(f"New wallet generated: {address}")
            return wallet_info
            
        except Exception as e:
            logger.error(f"Failed to generate wallet: {e}")
            raise
    
    async def validate_address(self, address: str) -> bool:
        """지갑 주소 검증"""
        try:
            # 형식 검증
            if not TronAddressValidator.is_valid_base58_address(address):
                return False
            
            # Base58 디코딩 검증
            try:
                import base58
                base58.b58decode_check(address)
                return True
            except Exception:
                return False
                
        except Exception as e:
            logger.error(f"Address validation failed for {address}: {e}")
            return False
    
    def hex_to_base58(self, hex_address: str) -> str:
        """Hex 주소를 Base58 주소로 변환"""
        try:
            self.ensure_connection()
            return self.client.to_base58check_address(hex_address)
        except Exception as e:
            logger.error(f"Failed to convert hex to base58: {e}")
            raise
    
    def base58_to_hex(self, base58_address: str) -> str:
        """Base58 주소를 Hex 주소로 변환"""
        try:
            self.ensure_connection()
            return self.client.to_hex_address(base58_address)
        except Exception as e:
            logger.error(f"Failed to convert base58 to hex: {e}")
            raise
    
    def get_private_key_from_hex(self, hex_key: str) -> PrivateKey:
        """16진수 문자열로부터 PrivateKey 객체 생성"""
        try:
            return PrivateKey(bytes.fromhex(hex_key))
        except Exception as e:
            logger.error(f"Failed to create private key from hex: {e}")
            raise ValueError("Invalid private key format")
    
    def address_to_hex(self, address: str) -> str:
        """Base58 주소를 Hex 주소로 변환"""
        try:
            if not TronAddressValidator.is_valid_base58_address(address):
                raise ValueError("Invalid base58 address")
            
            # tronpy를 사용한 주소 변환
            from tronpy.keys import to_hex_address
            return to_hex_address(address)
            
        except Exception as e:
            logger.error(f"Failed to convert address to hex: {e}")
            raise
    
    def hex_to_address(self, hex_address: str) -> str:
        """Hex 주소를 Base58 주소로 변환"""
        try:
            if not TronAddressValidator.is_valid_hex_address(hex_address):
                raise ValueError("Invalid hex address")
            
            # tronpy를 사용한 주소 변환
            from tronpy.keys import to_base58check_address
            return to_base58check_address(hex_address)
            
        except Exception as e:
            logger.error(f"Failed to convert hex to address: {e}")
            raise
