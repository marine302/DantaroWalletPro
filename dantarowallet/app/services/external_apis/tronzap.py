"""
TronZap API 서비스 - 문서 #40 기반
"""

import aiohttp
from typing import Dict, Optional
from decimal import Decimal
from app.core.logging import get_logger

logger = get_logger(__name__)


class TronZapAPI:
    """TronZap 외부 에너지 공급사 API"""

    def __init__(self):
        self.base_url = "https://api.tronzap.com/v1"
        self.api_key = "test_api_key"  # 실제로는 환경변수에서 가져옴

    async def get_energy_price(self) -> Decimal:
        """현재 에너지 가격 조회"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/energy/price"
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return Decimal(str(data.get("price_per_energy", "0.00012")))
                    else:
                        logger.error(f"TronZap 가격 조회 실패: {response.status}")
                        return Decimal("0.00012")  # 기본값
        except Exception as e:
            logger.error(f"TronZap API 오류: {e}")
            return Decimal("0.00012")  # 기본값

    async def purchase_energy(
        self, 
        target_address: str, 
        energy_amount: int, 
        duration_days: int = 1
    ) -> Dict:
        """에너지 구매"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/energy/purchase"
                headers = {"Authorization": f"Bearer {self.api_key}"}
                payload = {
                    "target_address": target_address,
                    "energy_amount": energy_amount,
                    "duration_days": duration_days
                }
                
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "order_id": data.get("order_id"),
                            "tx_hash": data.get("tx_hash"),
                            "cost_trx": data.get("cost_trx")
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"TronZap 에너지 구매 실패: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"API 오류: {response.status}"
                        }
        except Exception as e:
            logger.error(f"TronZap 에너지 구매 오류: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def check_order_status(self, order_id: str) -> Dict:
        """주문 상태 확인"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/orders/{order_id}"
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "status": data.get("status"),
                            "tx_hash": data.get("tx_hash")
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"API 오류: {response.status}"
                        }
        except Exception as e:
            logger.error(f"TronZap 주문 상태 확인 오류: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_available_energy(self) -> int:
        """사용 가능한 에너지량 조회"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/energy/available"
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("available_energy", 0)
                    else:
                        logger.error(f"TronZap 가용 에너지 조회 실패: {response.status}")
                        return 0
        except Exception as e:
            logger.error(f"TronZap 가용 에너지 조회 오류: {e}")
            return 0
