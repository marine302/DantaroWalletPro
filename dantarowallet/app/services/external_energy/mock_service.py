"""
Mock 에너지 서비스 - 개발/테스트용
실제 API 키 없이도 외부 에너지 공급업체 기능을 시뮬레이션
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.core.config import settings


class MockEnergyService:
    """개발용 Mock 에너지 서비스"""

    def __init__(self):
        self.use_mock = getattr(settings, "USE_MOCK_ENERGY_SERVICE", True)

    async def get_tronnrg_market_price(self) -> Dict[str, Any]:
        """TronNRG 시장 가격 Mock 데이터"""
        return {
            "success": True,
            "data": {
                "price_per_energy": round(random.uniform(0.000015, 0.000025), 8),
                "available_energy": random.randint(5000000, 15000000),
                "min_order": 1000,
                "max_order": 1000000,
                "timestamp": datetime.now().isoformat(),
                "provider": "TronNRG",
                "market_status": "active"
            }
        }

    async def get_energytron_market_price(self) -> Dict[str, Any]:
        """EnergyTRON 시장 가격 Mock 데이터"""
        return {
            "success": True,
            "data": {
                "price_per_energy": round(random.uniform(0.000018, 0.000028), 8),
                "available_energy": random.randint(8000000, 20000000),
                "min_order": 500,
                "max_order": 2000000,
                "timestamp": datetime.now().isoformat(),
                "provider": "EnergyTRON",
                "market_status": "active",
                "partner_discount": 0.05  # 5% 파트너 할인
            }
        }

    async def get_all_providers(self) -> List[Dict[str, Any]]:
        """모든 공급자 목록 Mock 데이터"""
        return [
            {
                "id": "tronnrg_001",
                "name": "TronNRG",
                "status": "active",
                "reliability": 0.98,
                "avg_response_time": 150,  # ms
                "current_price": round(random.uniform(0.000015, 0.000025), 8),
                "available_energy": random.randint(5000000, 15000000),
                "features": ["instant_delivery", "bulk_orders", "api_integration"],
                "supported_networks": ["tron_mainnet", "tron_nile"]
            },
            {
                "id": "energytron_001", 
                "name": "EnergyTRON",
                "status": "active",
                "reliability": 0.96,
                "avg_response_time": 200,  # ms
                "current_price": round(random.uniform(0.000018, 0.000028), 8),
                "available_energy": random.randint(8000000, 20000000),
                "features": ["partner_program", "white_label", "custom_api"],
                "supported_networks": ["tron_mainnet", "tron_nile"],
                "partner_benefits": {
                    "discount_rate": 0.05,
                    "priority_support": True,
                    "custom_integration": True
                }
            },
            {
                "id": "justlend_001",
                "name": "JustLend Energy",
                "status": "active", 
                "reliability": 0.94,
                "avg_response_time": 300,  # ms
                "current_price": round(random.uniform(0.000020, 0.000030), 8),
                "available_energy": random.randint(3000000, 10000000),
                "features": ["defi_integration", "staking_rewards"],
                "supported_networks": ["tron_mainnet"]
            }
        ]

    async def create_mock_order(self, provider_id: str, amount: int) -> Dict[str, Any]:
        """Mock 주문 생성"""
        order_id = f"mock_{provider_id}_{uuid.uuid4().hex[:8]}"
        
        # 공급자별 다른 가격 적용
        if provider_id == "tronnrg_001":
            price_per_energy = round(random.uniform(0.000015, 0.000025), 8)
        elif provider_id == "energytron_001":
            price_per_energy = round(random.uniform(0.000018, 0.000028), 8)
        else:
            price_per_energy = round(random.uniform(0.000020, 0.000030), 8)
        
        total_cost = amount * price_per_energy
        
        return {
            "success": True,
            "data": {
                "order_id": order_id,
                "provider_id": provider_id,
                "status": "pending",
                "energy_amount": amount,
                "price_per_energy": price_per_energy,
                "total_cost": round(total_cost, 6),
                "currency": "TRX",
                "created_at": datetime.now().isoformat(),
                "estimated_completion": (datetime.now() + timedelta(minutes=5)).isoformat(),
                "transaction_hash": None  # 완료 시 업데이트
            }
        }

    async def get_mock_order_status(self, order_id: str) -> Dict[str, Any]:
        """Mock 주문 상태 조회"""
        # 실제로는 DB에서 조회하겠지만, Mock에서는 랜덤하게 상태 생성
        statuses = ["pending", "processing", "completed", "failed"]
        status = random.choice(statuses)
        
        result = {
            "success": True,
            "data": {
                "order_id": order_id,
                "status": status,
                "created_at": (datetime.now() - timedelta(minutes=10)).isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        }
        
        if status == "completed":
            result["data"].update({
                "transaction_hash": f"0x{uuid.uuid4().hex}",
                "energy_delivered": random.randint(900, 1000),  # 약간의 손실 시뮬레이션
                "completion_time": datetime.now().isoformat()
            })
        elif status == "failed":
            result["data"].update({
                "error_code": "INSUFFICIENT_BALANCE",
                "error_message": "공급자 잔액 부족"
            })
        
        return result

    async def get_mock_best_price(self, energy_amount: int) -> Dict[str, Any]:
        """최적 가격 공급자 추천 Mock"""
        providers = await self.get_all_providers()
        
        # 가격순으로 정렬
        sorted_providers = sorted(providers, key=lambda x: x["current_price"])
        
        best_provider = sorted_providers[0]
        best_price = best_provider["current_price"] * energy_amount
        
        return {
            "success": True,
            "data": {
                "energy_amount": energy_amount,
                "best_provider": best_provider,
                "best_price": round(best_price, 6),
                "price_comparison": [
                    {
                        "provider": p["name"],
                        "price": round(p["current_price"] * energy_amount, 6),
                        "available": p["available_energy"] >= energy_amount
                    }
                    for p in sorted_providers[:3]
                ]
            }
        }

    async def get_mock_system_status(self) -> Dict[str, Any]:
        """시스템 상태 Mock 데이터"""
        return {
            "success": True,
            "data": {
                "overall_status": "healthy",
                "total_providers": 3,
                "active_providers": 3,
                "total_orders_today": random.randint(150, 300),
                "success_rate": round(random.uniform(0.95, 0.99), 3),
                "avg_response_time": random.randint(180, 250),
                "system_load": round(random.uniform(0.3, 0.7), 2),
                "last_updated": datetime.now().isoformat(),
                "providers_health": [
                    {
                        "name": "TronNRG",
                        "status": "online",
                        "response_time": random.randint(100, 200),
                        "success_rate": round(random.uniform(0.96, 0.99), 3)
                    },
                    {
                        "name": "EnergyTRON", 
                        "status": "online",
                        "response_time": random.randint(150, 250),
                        "success_rate": round(random.uniform(0.94, 0.98), 3)
                    },
                    {
                        "name": "JustLend Energy",
                        "status": "online", 
                        "response_time": random.randint(200, 350),
                        "success_rate": round(random.uniform(0.92, 0.96), 3)
                    }
                ]
            }
        }


# 싱글톤 인스턴스
mock_energy_service = MockEnergyService()
