"""
EnergyTRON API 통합 서비스

EnergyTRON은 B2B/B2C 하이브리드 모델로 파트너십 프로그램을 운영하며
화이트라벨 솔루션과 커스텀 API 개발을 지원합니다.
"""

import httpx
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from app.core.config import settings
from app.schemas.external_energy import (
    EnergyPriceResponse,
    EnergyPurchaseRequest,
    EnergyPurchaseResponse,
    EnergyBalanceResponse
)

logger = logging.getLogger(__name__)


class EnergyTRONService:
    """EnergyTRON API 서비스 클래스"""
    
    def __init__(self):
        self.base_url = "https://api.energytron.io/v1"
        self.api_key = getattr(settings, 'ENERGYTRON_API_KEY', 'demo_key_energytron')
        self.partner_id = getattr(settings, 'ENERGYTRON_PARTNER_ID', 'partner_demo')
        self.timeout = 30.0
        
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """EnergyTRON API 요청 실행"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Partner-ID": self.partner_id,
            "Content-Type": "application/json",
            "User-Agent": "DantaroWallet-B2B/1.0"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            logger.error(f"EnergyTRON API timeout: {endpoint}")
            raise Exception("EnergyTRON API 요청 시간 초과")
        except httpx.HTTPStatusError as e:
            logger.error(f"EnergyTRON API HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"EnergyTRON API 오류: {e.response.status_code}")
        except Exception as e:
            logger.error(f"EnergyTRON API 요청 실패: {str(e)}")
            raise Exception(f"EnergyTRON API 연결 실패: {str(e)}")

    async def get_current_prices(self) -> EnergyPriceResponse:
        """현재 에너지 가격 조회 (파트너 할인가 포함)"""
        try:
            data = await self._make_request("GET", "/partner/prices")
            
            # EnergyTRON 응답 형식에 맞춰 변환
            return EnergyPriceResponse(
                provider="energytron",
                prices=[
                    {
                        "amount": tier["amount"],
                        "price_per_unit": tier["partner_price"],  # 파트너 할인가
                        "total_price": tier["amount"] * tier["partner_price"],
                        "discount_rate": tier.get("discount_percent", 0.0),
                        "tier_name": tier.get("tier_name", f"{tier['amount']} 에너지")
                    }
                    for tier in data.get("pricing_tiers", [])
                ],
                currency="TRX",
                last_updated=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
                valid_until=datetime.fromisoformat(data.get("valid_until", (datetime.now() + timedelta(hours=1)).isoformat())),
                minimum_order=data.get("minimum_order", 1000),
                maximum_order=data.get("maximum_order", 10000000)
            )
            
        except Exception as e:
            logger.error(f"EnergyTRON 가격 조회 실패: {str(e)}")
            raise Exception(f"EnergyTRON 가격 정보를 가져올 수 없습니다: {str(e)}")

    async def purchase_energy(self, request: EnergyPurchaseRequest) -> EnergyPurchaseResponse:
        """에너지 구매 (파트너 API 사용)"""
        try:
            purchase_data = {
                "partner_id": self.partner_id,
                "energy_amount": request.amount,
                "target_address": request.target_address,
                "distribution_plan": {
                    "auto_distribute": request.auto_distribute,
                    "partner_allocation": request.partner_allocation or {}
                },
                "payment_method": "TRX",
                "callback_url": getattr(settings, 'ENERGYTRON_CALLBACK_URL', None)
            }
            
            data = await self._make_request("POST", "/partner/buy", purchase_data)
            
            return EnergyPurchaseResponse(
                transaction_id=data["transaction_id"],
                provider="energytron",
                amount=data["energy_amount"],
                total_cost=data["total_cost"],
                status=data["status"],
                estimated_delivery=datetime.fromisoformat(data.get("estimated_delivery", datetime.now().isoformat())),
                tx_hash=data.get("blockchain_tx", ""),
                partner_benefits={
                    "discount_applied": data.get("discount_applied", 0.0),
                    "loyalty_points": data.get("loyalty_points_earned", 0),
                    "next_tier_progress": data.get("tier_progress", 0.0)
                }
            )
            
        except Exception as e:
            logger.error(f"EnergyTRON 에너지 구매 실패: {str(e)}")
            raise Exception(f"EnergyTRON 에너지 구매 실패: {str(e)}")

    async def check_balance(self, address: str) -> EnergyBalanceResponse:
        """에너지 잔액 조회"""
        try:
            params = {"address": address}
            data = await self._make_request("GET", "/partner/balance", params=params)
            
            return EnergyBalanceResponse(
                address=address,
                available_energy=data["available_energy"],
                reserved_energy=data.get("reserved_energy", 0),
                total_purchased=data.get("total_purchased", 0),
                last_updated=datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat())),
                provider="energytron",
                partner_tier=data.get("partner_tier", "standard"),
                next_refill_discount=data.get("next_discount", 0.0)
            )
            
        except Exception as e:
            logger.error(f"EnergyTRON 잔액 조회 실패: {str(e)}")
            raise Exception(f"EnergyTRON 잔액 조회 실패: {str(e)}")

    async def distribute_energy(
        self, 
        source_address: str, 
        allocations: Dict[str, int]
    ) -> Dict[str, Any]:
        """파트너들에게 에너지 분배"""
        try:
            distribution_data = {
                "source_address": source_address,
                "allocations": [
                    {
                        "partner_address": address,
                        "energy_amount": amount,
                        "priority": "normal"
                    }
                    for address, amount in allocations.items()
                ]
            }
            
            data = await self._make_request("POST", "/partner/distribute", distribution_data)
            
            return {
                "distribution_id": data["distribution_id"],
                "status": data["status"],
                "total_distributed": data["total_distributed"],
                "successful_allocations": data["successful_allocations"],
                "failed_allocations": data.get("failed_allocations", []),
                "estimated_completion": data.get("estimated_completion")
            }
            
        except Exception as e:
            logger.error(f"EnergyTRON 에너지 분배 실패: {str(e)}")
            raise Exception(f"EnergyTRON 에너지 분배 실패: {str(e)}")

    async def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """거래 상태 조회"""
        try:
            params = {"transaction_id": transaction_id}
            data = await self._make_request("GET", "/partner/transaction/status", params=params)
            
            return {
                "transaction_id": transaction_id,
                "status": data["status"],
                "progress": data.get("progress", 0),
                "blockchain_confirmations": data.get("confirmations", 0),
                "energy_delivered": data.get("energy_delivered", 0),
                "last_updated": data.get("last_updated"),
                "error_message": data.get("error_message")
            }
            
        except Exception as e:
            logger.error(f"EnergyTRON 거래 상태 조회 실패: {str(e)}")
            raise Exception(f"EnergyTRON 거래 상태 조회 실패: {str(e)}")

    async def get_partner_statistics(self) -> Dict[str, Any]:
        """파트너 통계 정보 조회"""
        try:
            data = await self._make_request("GET", "/partner/statistics")
            
            return {
                "partner_id": self.partner_id,
                "tier": data["tier"],
                "total_purchased": data["total_purchased"],
                "total_distributed": data["total_distributed"],
                "active_addresses": data["active_addresses"],
                "monthly_volume": data["monthly_volume"],
                "available_discounts": data.get("available_discounts", []),
                "performance_metrics": data.get("performance_metrics", {}),
                "next_tier_requirements": data.get("next_tier_requirements", {})
            }
            
        except Exception as e:
            logger.error(f"EnergyTRON 파트너 통계 조회 실패: {str(e)}")
            raise Exception(f"EnergyTRON 파트너 통계 조회 실패: {str(e)}")

    async def health_check(self) -> bool:
        """API 상태 확인"""
        try:
            data = await self._make_request("GET", "/partner/health")
            return data.get("status") == "healthy"
        except:
            return False


# 싱글톤 인스턴스
energytron_service = EnergyTRONService()
