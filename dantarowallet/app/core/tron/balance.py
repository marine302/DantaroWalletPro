"""
TRON 잔고 조회 서비스.
TRX 및 TRC20 토큰 잔고 조회를 담당합니다.
"""
import logging
from typing import Any, Dict, List, Optional

from app.core.tron.constants import TronConstants, TronNetwork
from app.core.tron.network import TronNetworkService

logger = logging.getLogger(__name__)


class TronBalanceService(TronNetworkService):
    """TRON 잔고 조회 서비스"""
    
    async def get_trx_balance(self, address: str) -> Dict[str, Any]:
        """TRX 잔고 조회"""
        try:
            self.ensure_connection()
            balance = self.client.get_account_balance(address)
            
            return {
                "token": "TRX",
                "balance": balance,
                "decimals": 6,
                "formatted": balance / 1_000_000,  # SUN to TRX
                "address": address
            }
            
        except Exception as e:
            logger.error(f"Error getting TRX balance for {address}: {e}")
            return {
                "token": "TRX",
                "balance": 0,
                "decimals": 6,
                "formatted": 0.0,
                "address": address,
                "error": str(e)
            }
    
    async def get_trc20_balance(self, address: str, token: str = "USDT") -> Dict[str, Any]:
        """TRC20 토큰 잔고 조회"""
        try:
            self.ensure_connection()
            
            # 토큰 계약 주소 가져오기
            contracts = TronConstants.get_contracts(self.network)
            contract_address = contracts.get(token.upper())
            
            if not contract_address:
                raise ValueError(f"Unsupported token: {token}")
            
            # 스마트 컨트랙트 인스턴스 생성
            contract = self.client.get_contract(contract_address)
            
            # 잔고 및 소수점 조회
            balance = contract.functions.balanceOf(address)
            decimals = contract.functions.decimals()
            
            return {
                "token": token.upper(),
                "balance": balance,
                "decimals": decimals,
                "formatted": balance / (10 ** decimals),
                "contract_address": contract_address,
                "address": address
            }
            
        except Exception as e:
            logger.error(f"Error getting {token} balance for {address}: {e}")
            return {
                "token": token.upper(),
                "balance": 0,
                "decimals": 6,
                "formatted": 0.0,
                "address": address,
                "error": str(e)
            }
    
    async def get_balance(self, address: str, token: str = "USDT") -> Dict[str, Any]:
        """통합 잔고 조회 (TRX 또는 TRC20)"""
        if token.upper() == "TRX":
            return await self.get_trx_balance(address)
        else:
            return await self.get_trc20_balance(address, token)
    
    async def get_multiple_balances(self, address: str, tokens: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """여러 토큰 잔고 한번에 조회"""
        if tokens is None:
            tokens = ["TRX", "USDT"]
        
        results = {}
        for token in tokens:
            try:
                balance_info = await self.get_balance(address, token)
                results[token] = balance_info
            except Exception as e:
                logger.error(f"Error getting balance for {token}: {e}")
                results[token] = {
                    "token": token,
                    "balance": 0,
                    "error": str(e)
                }
        
        return results
