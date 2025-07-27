"""
TronNRG API 서비스 - 문서 #40 기반
"""

import aiohttp
from typing import Dict, Optional
from decimal import Decimal
from app.core.logging import get_logger

logger = get_logger(__name__)


class TronNRGAPI:
    """TronNRG 외부 에너지 공급사 API"""

    def __init__(self):
        self.base_url = "https://api.tronnrg.com/v2"
        self.api_key = "test_api_key"  # 실제로는 환경변수에서 가져옴

    async def get_energy_price(self) -> Decimal:
        """현재 에너지 가격 조회"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/price"
                headers = {"X-API-Key": self.api_key}
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return Decimal(str(data.get("energy_price", "0.00015")))
                    else:
                        logger.error(f"TronNRG 가격 조회 실패: {response.status}")
                        return Decimal("0.00015")  # 기본값
        except Exception as e:
            logger.error(f"TronNRG API 오류: {e}")
            return Decimal("0.00015")  # 기본값

    async def purchase_energy(
        self, 
        target_address: str, 
        energy_amount: int, 
        duration_hours: int = 24
    ) -> Dict:
        """에너지 구매"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/delegate"
                headers = {"X-API-Key": self.api_key}
                payload = {
                    "receiver": target_address,
                    "amount": energy_amount,
                    "lock_period": duration_hours
                }
                
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "transaction_id": data.get("txid"),
                            "cost_trx": data.get("fee_trx"),
                            "delegation_id": data.get("delegation_id")
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"TronNRG 에너지 구매 실패: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"API 오류: {response.status}"
                        }
        except Exception as e:
            logger.error(f"TronNRG 에너지 구매 오류: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def check_delegation_status(self, delegation_id: str) -> Dict:
        """위임 상태 확인"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/delegation/{delegation_id}"
                headers = {"X-API-Key": self.api_key}
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "status": data.get("status"),
                            "energy_delegated": data.get("energy_amount"),
                            "expires_at": data.get("expires_at")
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"API 오류: {response.status}"
                        }
        except Exception as e:
            logger.error(f"TronNRG 위임 상태 확인 오류: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_account_info(self) -> Dict:
        """계정 정보 조회"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/account"
                headers = {"X-API-Key": self.api_key}
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "available_energy": data.get("available_energy", 0),
                            "total_energy": data.get("total_energy", 0),
                            "balance_trx": data.get("balance_trx", 0)
                        }
                    else:
                        logger.error(f"TronNRG 계정 정보 조회 실패: {response.status}")
                        return {
                            "success": False,
                            "error": f"API 오류: {response.status}"
                        }
        except Exception as e:
            logger.error(f"TronNRG 계정 정보 조회 오류: {e}")
            return {
                "success": False,
                "error": str(e)
            }
