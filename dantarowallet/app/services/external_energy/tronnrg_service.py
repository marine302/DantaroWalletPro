"""
TronNRG API 연동 서비스
"""
import httpx
import asyncio
import json
from typing import Dict, List, Optional, Any
from decimal import Decimal
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class TronNRGAPIError(Exception):
    """TronNRG API 오류"""
    pass


class TronNRGService:
    """TronNRG API 연동 서비스"""
    
    def __init__(self):
        self.base_url = "https://api.tronnrg.com/v1"
        self.api_key = getattr(settings, 'TRONNRG_API_KEY', None)
        self.timeout = 30.0
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """HTTP 요청 실행"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "DantaroWallet/1.0"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"TronNRG API error: {response.status_code} - {response.text}")
                    raise TronNRGAPIError(f"API request failed: {response.status_code}")
                        
        except httpx.TimeoutException:
            logger.error("TronNRG API timeout")
            raise TronNRGAPIError("Request timeout")
        except httpx.RequestError as e:
            logger.error(f"TronNRG API connection error: {e}")
            raise TronNRGAPIError(f"Connection error: {e}")
    
    async def get_market_price(self) -> Dict[str, Any]:
        """실시간 시장 가격 조회"""
        return await self._make_request("GET", "/market/price")
    
    async def get_market_data(self) -> Dict[str, Any]:
        """시장 데이터 조회"""
        return await self._make_request("GET", "/market/data")
    
    async def get_providers(self) -> List[Dict[str, Any]]:
        """공급자 목록 조회"""
        response = await self._make_request("GET", "/providers")
        return response.get("data", [])
    
    async def get_provider_detail(self, provider_id: str) -> Dict[str, Any]:
        """특정 공급자 상세 정보 조회"""
        return await self._make_request("GET", f"/providers/{provider_id}")
    
    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """주문 생성"""
        return await self._make_request("POST", "/orders", data=order_data)
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """주문 상태 조회"""
        return await self._make_request("GET", f"/orders/{order_id}")
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """주문 취소"""
        return await self._make_request("DELETE", f"/orders/{order_id}")


# 싱글톤 인스턴스
tronnrg_service = TronNRGService()
