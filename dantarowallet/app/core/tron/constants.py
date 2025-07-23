"""
TRON 블록체인 상수 및 설정.
네트워크 관련 상수들을 중앙 집중화하여 관리합니다.
"""

from enum import Enum
from typing import Dict


class TronNetwork(str, Enum):
    """TRON 네트워크 타입"""

    MAINNET = "mainnet"
    NILE = "nile"  # Testnet
    SHASTA = "shasta"  # Deprecated testnet


class TronConstants:
    """TRON 블록체인 관련 상수"""

    # 기본 수수료 설정
    DEFAULT_FEE_LIMIT = 100_000_000  # 100 TRX
    MIN_FEE_LIMIT = 1_000_000  # 1 TRX
    MAX_FEE_LIMIT = 1_000_000_000  # 1000 TRX

    # 에너지 관련 상수
    ENERGY_PER_TRANSACTION = 65_000  # 일반 트랜잭션 평균 에너지
    BANDWIDTH_PER_TRANSACTION = 268  # 일반 트랜잭션 평균 대역폭

    # 블록 관련
    BLOCK_TIME_SECONDS = 3  # TRON 블록 생성 시간
    CONFIRMATION_BLOCKS = 19  # 권장 확인 블록 수

    # 주소 검증
    ADDRESS_LENGTH = 34
    HEX_ADDRESS_LENGTH = 42

    # 토큰 계약 주소 (네트워크별)
    MAINNET_CONTRACTS = {
        "USDT": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
        "USDC": "TEkxiTehnzSmSe2XqrBj4w32RUN966rdz8",
    }

    NILE_CONTRACTS = {
        "USDT": "TG3XXyExBkPp9nzdajDZsozEu4BkaSJozs",  # Nile testnet USDT
        "USDC": "TEkxiTehnzSmSe2XqrBj4w32RUN966rdz8",  # Placeholder
    }

    @classmethod
    def get_contracts(cls, network: TronNetwork) -> Dict[str, str]:
        """네트워크별 토큰 계약 주소 반환"""
        if network == TronNetwork.MAINNET:
            return cls.MAINNET_CONTRACTS.copy()
        elif network == TronNetwork.NILE:
            return cls.NILE_CONTRACTS.copy()
        else:
            return {}

    @classmethod
    def get_explorer_url(cls, network: TronNetwork) -> str:
        """네트워크별 탐색기 URL 반환"""
        urls = {
            TronNetwork.MAINNET: "https://tronscan.org",
            TronNetwork.NILE: "https://nile.tronscan.org",
            TronNetwork.SHASTA: "https://shasta.tronscan.org",
        }
        return urls.get(network, urls[TronNetwork.NILE])


class TronAddressValidator:
    """TRON 주소 검증 유틸리티"""

    @staticmethod
    def is_valid_base58_address(address: str) -> bool:
        """Base58 주소 형식 검증"""
        if not address or len(address) != TronConstants.ADDRESS_LENGTH:
            return False

        # TRON 주소는 'T'로 시작
        if not address.startswith("T"):
            return False

        # Base58 문자 집합 검증
        base58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        return all(c in base58_chars for c in address)

    @staticmethod
    def is_valid_hex_address(address: str) -> bool:
        """Hex 주소 형식 검증"""
        if not address or len(address) != TronConstants.HEX_ADDRESS_LENGTH:
            return False

        # Hex 주소는 '41'로 시작
        if not address.startswith("41"):
            return False

        # Hex 문자 집합 검증
        try:
            int(address, 16)
            return True
        except ValueError:
            return False
