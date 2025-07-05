"""
지갑 관리 서비스 모듈.
지갑 생성, 조회, 온체인 잔고 확인 등의 기능을 모듈화하여 관리합니다.
"""

from app.services.wallet.wallet_service import WalletService

__all__ = [
    "WalletService",
]
