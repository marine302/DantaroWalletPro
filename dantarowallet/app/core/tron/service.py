"""
TRON 통합 서비스.
기존 TronService와의 호환성을 유지하면서 모듈화된 구조를 제공합니다.
"""
import logging
from typing import Any, Dict, List, Optional

from app.core.tron.balance import TronBalanceService
from app.core.tron.energy import TronEnergyService
from app.core.tron.network import TronNetworkService
from app.core.tron.stats import TronNetworkStatsService
from app.core.tron.transaction import TronTransactionService
from app.core.tron.wallet import TronWalletManager

logger = logging.getLogger(__name__)


class TronService:
    """
    TRON 통합 서비스 클래스
    
    기존 코드와의 호환성을 유지하면서 모듈화된 TRON 서비스들을 통합합니다.
    각 기능별로 전문화된 서비스 클래스들을 활용합니다.
    """
    
    def __init__(self):
        # 임시로 TRON 서비스 초기화를 비활성화 (무한루프 방지)
        logger.info("TronService initialization disabled to prevent infinite loops")
        self._initialized = False
    
    @property
    def client(self):
        """TRON 클라이언트 인스턴스 반환 (기존 호환성)"""
        return self._network_service.client
    
    # =============================================================================
    # 지갑 관련 메서드
    # =============================================================================
    
    def generate_wallet(self) -> Dict[str, str]:
        """새 지갑 생성 (임시 비활성화)"""
        return {"address": "TEMP_ADDRESS", "private_key": "TEMP_KEY"}
    
    async def validate_address(self, address: str) -> bool:
        """주소 검증 (임시 비활성화)"""
        return True
        """주소 유효성 검증"""
        return await self._wallet_manager.validate_address(address)
    
    def hex_to_base58(self, hex_address: str) -> str:
        """Hex 주소를 Base58 주소로 변환"""
        return self._wallet_manager.hex_to_base58(hex_address)
    
    def base58_to_hex(self, base58_address: str) -> str:
        """Base58 주소를 Hex 주소로 변환"""
        return self._wallet_manager.base58_to_hex(base58_address)
    
    # =============================================================================
    # 잔고 관련 메서드
    # =============================================================================
    
    async def get_balance(self, address: str, token: str = "USDT") -> Dict[str, Any]:
        """지갑 잔고 조회 (기존 호환성 유지)"""
        return await self._balance_service.get_balance(address, token)
    
    async def get_trx_balance(self, address: str) -> Dict[str, Any]:
        """TRX 잔고 조회"""
        return await self._balance_service.get_trx_balance(address)
    
    async def get_trc20_balance(self, address: str, token: str = "USDT") -> Dict[str, Any]:
        """TRC20 토큰 잔고 조회"""
        return await self._balance_service.get_trc20_balance(address, token)
    
    async def get_multiple_balances(self, address: str, tokens: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """여러 토큰 잔고 한번에 조회"""
        return await self._balance_service.get_multiple_balances(address, tokens)
    
    # =============================================================================
    # 트랜잭션 관련 메서드
    # =============================================================================
    
    async def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """트랜잭션 정보 조회"""
        return await self._transaction_service.get_transaction(tx_hash)
    
    async def get_transaction_by_hash(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """트랜잭션 정보 조회 (별칭 메서드)"""
        return await self.get_transaction(tx_hash)
    
    async def get_transactions_for_address(
        self, address: str, token: str = "USDT", start_block: Optional[int] = None, 
        end_block: Optional[int] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """주소별 트랜잭션 조회"""
        try:
            # 블록 범위 설정
            if end_block is None:
                end_block = self.get_block_number()
            if start_block is None:
                start_block = max(0, end_block - 1000)  # 최근 1000블록
            
            if token.upper() == "TRX":
                return self.get_trx_transactions(address, start_block, end_block)
            else:
                # TRC20 토큰의 경우 컨트랙트 주소 필요
                from app.core.tron.constants import TronConstants
                contracts = TronConstants.get_contracts(self.network)
                contract_address = contracts.get(token.upper())
                
                if not contract_address:
                    logger.warning(f"Unsupported token: {token}")
                    return []
                
                return self.get_trc20_transactions(address, contract_address, start_block, end_block)
                
        except Exception as e:
            logger.error(f"Error getting transactions for address {address}: {e}")
            return []
    
    def get_block_number(self) -> int:
        """현재 블록 번호 조회"""
        return self._transaction_service.get_block_number()
    
    def get_trx_transactions(
        self, address: str, start_block: int, end_block: int
    ) -> List[Dict[str, Any]]:
        """TRX 트랜잭션 조회"""
        return self._transaction_service.get_trx_transactions(address, start_block, end_block)
    
    def get_trc20_transactions(
        self, address: str, contract_address: str, start_block: int, end_block: int
    ) -> List[Dict[str, Any]]:
        """TRC20 토큰 트랜잭션 조회"""
        return self._transaction_service.get_trc20_transactions(address, contract_address, start_block, end_block)
    
    # =============================================================================
    # 에너지 및 리소스 관련 메서드
    # =============================================================================
    
    async def get_account_resources(self, address: str) -> Dict[str, Any]:
        """계정의 에너지 및 대역폭 정보 조회"""
        return await self._energy_service.get_account_resources(address)
    
    async def get_energy_price_info(self) -> Dict[str, Any]:
        """현재 에너지 가격 정보 조회"""
        return await self._energy_service.get_energy_price_info()
    
    async def estimate_transaction_cost(
        self, transaction_type: str = "USDT_TRANSFER"
    ) -> Dict[str, Any]:
        """트랜잭션 타입별 예상 비용 계산"""
        return await self._energy_service.estimate_transaction_cost(transaction_type)
    
    async def get_energy_info(self, address: Optional[str] = None) -> Dict[str, Any]:
        """계정의 에너지 정보 조회"""
        return await self._energy_service.get_energy_info(address)
    
    async def get_energy_price(self) -> Dict[str, Any]:
        """현재 에너지 가격 정보 조회"""
        return await self._energy_service.get_energy_price()
    
    async def estimate_transaction_energy(
        self, contract_address: str, function_selector: str, 
        parameter: str = "", caller_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """트랜잭션에 필요한 에너지 추정"""
        return await self._energy_service.estimate_transaction_energy(
            contract_address, function_selector, parameter, caller_address
        )
    
    # =============================================================================
    # 네트워크 통계 관련 메서드
    # =============================================================================
    
    async def get_network_stats(self) -> Dict[str, Any]:
        """TRON 네트워크 전체 통계 정보"""
        return await self._stats_service.get_network_stats()
    
    async def get_chain_parameters(self) -> Dict[str, Any]:
        """TRON 체인 파라미터 조회"""
        return await self._stats_service.get_chain_parameters()
    
    async def get_node_info(self) -> Dict[str, Any]:
        """노드 정보 조회"""
        return await self._stats_service.get_node_info()
    
    # =============================================================================
    # 네트워크 연결 관련 메서드
    # =============================================================================
    
    def ensure_connection(self) -> None:
        """연결 상태 확인 및 재연결"""
        self._network_service.ensure_connection()
    
    async def get_latest_block_number(self) -> int:
        """최신 블록 번호 조회"""
        return await self._network_service.get_latest_block_number()
    
    async def get_latest_block(self) -> dict:
        """최신 블록 정보 조회"""
        return await self._network_service.get_latest_block()
    
    # =============================================================================
    # 유틸리티 메서드
    # =============================================================================
    
    def is_connected(self) -> bool:
        """네트워크 연결 상태 확인"""
        return self._network_service._network_client.is_connected()
    
    def reconnect(self) -> None:
        """네트워크 재연결"""
        self._network_service._network_client.reconnect()
    
    @property
    def network(self):
        """현재 네트워크 반환"""
        return self._network_service.network
