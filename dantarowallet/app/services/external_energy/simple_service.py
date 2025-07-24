"""
간단한 에너지 서비스 - 개인/소규모 프로젝트용
복잡한 기업 계약 없이 즉시 사용 가능한 에너지 공급업체 연동
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class SimpleEnergyService:
    """간단한 에너지 서비스 - 개인/소규모 프로젝트용"""

    def __init__(self):
        self.tronscan_api_key = getattr(settings, "TRONSCAN_API_KEY", "")
        self.trongrid_api_key = getattr(settings, "TRONGRID_API_KEY", "")
        self.use_simple_service = getattr(settings, "USE_SIMPLE_ENERGY_SERVICE", True)
        self.timeout = 10.0

    async def get_trongrid_energy_price(self) -> Dict[str, Any]:
        """TronGrid에서 실시간 에너지 가격 조회 (무료 10K 요청/월)"""
        try:
            url = "https://api.trongrid.io/wallet/getchainparameters"
            headers = {}
            if self.trongrid_api_key:
                headers["TRON-PRO-API-KEY"] = self.trongrid_api_key

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    
                    # ChainParameters에서 에너지 가격 추출
                    energy_fee = 420  # 기본값 (SUN)
                    for param in data.get("chainParameter", []):
                        if param.get("key") == "getEnergyFee":
                            energy_fee = param.get("value", energy_fee)
                            break
                    
                    price_per_energy = energy_fee / 1_000_000  # SUN to TRX
                    
                    return {
                        "success": True,
                        "data": {
                            "price_per_energy": price_per_energy,
                            "price_in_sun": energy_fee,
                            "energy_per_trx": 1_000_000 // energy_fee if energy_fee > 0 else 0,
                            "available_energy": 999999999,  # 정보 제공만
                            "timestamp": datetime.now().isoformat(),
                            "source": "TronGrid Official",
                            "provider": "trongrid"
                        }
                    }

        except Exception as e:
            logger.warning(f"TronGrid API failed: {str(e)}")
            
        # Fallback to TronScan
        return await self.get_tronscan_energy_price()

    async def get_tronscan_energy_price(self) -> Dict[str, Any]:
        """TronScan에서 실시간 에너지 가격 조회 (무료)"""
        try:
            url = "https://apilist.tronscan.org/api/energy/price"
            headers = {}
            if self.tronscan_api_key:
                headers["Authorization"] = f"Bearer {self.tronscan_api_key}"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "data": {
                            "price_per_energy": data.get("energy_price", 0.00002),
                            "price_in_sun": data.get("energy_price_sun", 20),
                            "available_energy": 999999999,  # TronScan은 가격만 제공
                            "timestamp": datetime.now().isoformat(),
                            "source": "TronScan Official",
                            "provider": "tronscan"
                        }
                    }
        except Exception as e:
            logger.error(f"TronScan API 오류: {e}")

        # 실패시 Mock 데이터 반환
        return await self._get_fallback_price_data("TronScan")

    async def get_trongrid_energy_info(self, address: Optional[str] = None) -> Dict[str, Any]:
        """TronGrid에서 에너지 정보 조회"""
        try:
            if not address:
                # 기본 정보만 반환
                return {
                    "success": True,
                    "data": {
                        "energy_limit": 0,
                        "energy_used": 0,
                        "energy_available": 0,
                        "frozen_balance_for_energy": 0,
                        "timestamp": datetime.now().isoformat()
                    }
                }

            url = f"https://api.trongrid.io/v1/accounts/{address}/resources"
            headers = {}
            if self.trongrid_api_key:
                headers["TRON-PRO-API-KEY"] = self.trongrid_api_key

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "data": {
                            "energy_limit": data.get("EnergyLimit", 0),
                            "energy_used": data.get("EnergyUsed", 0),
                            "energy_available": data.get("EnergyLimit", 0) - data.get("EnergyUsed", 0),
                            "frozen_balance_for_energy": data.get("frozBalanceForEnergy", 0),
                            "timestamp": datetime.now().isoformat()
                        }
                    }
        except Exception as e:
            logger.error(f"TronGrid API 오류: {e}")
            
        return {"success": False, "error": "Failed to get energy info"}

    async def get_justlend_energy_price(self) -> Dict[str, Any]:
        """JustLend 에너지 가격 정보 (추정치)"""
        # JustLend는 실시간 API가 없으므로 계산된 추정치 제공
        return {
            "success": True,
            "data": {
                "price_per_energy": 0.000025,  # 일반적인 JustLend 가격
                "min_rent_amount": 1000,
                "max_rent_amount": 100000000,
                "rental_duration_hours": [1, 3, 24, 72],
                "contract_address": "TKkeiboZVvpJSoJJiOKEe63vS5LGmk8mN5",
                "timestamp": datetime.now().isoformat(),
                "source": "JustLend Estimated",
                "provider": "justlend"
            }
        }

    async def get_community_energy_prices(self) -> List[Dict[str, Any]]:
        """커뮤니티 기반 에너지 가격들"""
        prices = []

        # TronScan 가격
        tronscan_price = await self.get_tronscan_energy_price()
        if tronscan_price["success"]:
            prices.append(tronscan_price["data"])

        # JustLend 가격
        justlend_price = await self.get_justlend_energy_price()
        if justlend_price["success"]:
            prices.append(justlend_price["data"])

        # P2P 마켓 추정 가격들
        p2p_prices = [
            {
                "price_per_energy": 0.000018,
                "provider": "energytron_live",
                "source": "Community P2P",
                "timestamp": datetime.now().isoformat(),
                "available_energy": 5000000,
                "note": "커뮤니티 기반 거래"
            },
            {
                "price_per_energy": 0.000022,
                "provider": "tron_energy_market", 
                "source": "P2P Platform",
                "timestamp": datetime.now().isoformat(),
                "available_energy": 8000000,
                "note": "개인간 직거래"
            }
        ]

        prices.extend(p2p_prices)
        return prices

    async def get_best_simple_price(self, energy_amount: int) -> Dict[str, Any]:
        """가장 저렴한 에너지 가격 찾기"""
        all_prices = await self.get_community_energy_prices()
        
        # 가격순으로 정렬
        sorted_prices = sorted(all_prices, key=lambda x: x["price_per_energy"])
        
        if not sorted_prices:
            return {"success": False, "error": "가격 정보를 가져올 수 없습니다"}

        best_price = sorted_prices[0]
        total_cost = energy_amount * best_price["price_per_energy"]

        return {
            "success": True,
            "data": {
                "energy_amount": energy_amount,
                "best_provider": best_price,
                "total_cost": round(total_cost, 6),
                "cost_in_trx": round(total_cost, 6),
                "savings_vs_worst": round(
                    (sorted_prices[-1]["price_per_energy"] - best_price["price_per_energy"]) * energy_amount, 6
                ),
                "price_comparison": [
                    {
                        "provider": p["provider"],
                        "price_per_energy": p["price_per_energy"],
                        "total_cost": round(p["price_per_energy"] * energy_amount, 6),
                        "source": p["source"]
                    }
                    for p in sorted_prices[:3]
                ]
            }
        }

    async def simulate_simple_purchase(self, provider: str, energy_amount: int) -> Dict[str, Any]:
        """간단한 에너지 구매 시뮬레이션"""
        prices = await self.get_community_energy_prices()
        
        # 지정된 공급자 찾기
        provider_data = next((p for p in prices if p["provider"] == provider), None)
        
        if not provider_data:
            return {"success": False, "error": f"공급자 '{provider}'를 찾을 수 없습니다"}

        order_id = f"simple_{provider}_{uuid.uuid4().hex[:8]}"
        total_cost = energy_amount * provider_data["price_per_energy"]

        return {
            "success": True,
            "data": {
                "order_id": order_id,
                "provider": provider,
                "status": "completed",  # 시뮬레이션이므로 즉시 완료
                "energy_amount": energy_amount,
                "price_per_energy": provider_data["price_per_energy"],
                "total_cost": round(total_cost, 6),
                "currency": "TRX",
                "source": provider_data["source"],
                "created_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
                "note": "시뮬레이션 거래 - 실제 에너지는 전송되지 않음"
            }
        }

    async def get_simple_providers(self) -> List[Dict[str, Any]]:
        """사용 가능한 간단한 공급자들"""
        return [
            {
                "id": "tronscan",
                "name": "TronScan",
                "type": "price_info_only",
                "difficulty": "⭐ (매우 쉬움)",
                "signup_time": "즉시",
                "features": ["실시간 가격", "무료 API", "공식 서비스"],
                "limitations": ["가격 정보만", "실제 거래 불가"],
                "api_url": "https://apilist.tronscan.org",
                "website": "https://tronscan.org"
            },
            {
                "id": "justlend",
                "name": "JustLend Energy",
                "type": "direct_purchase",
                "difficulty": "⭐⭐ (쉬움)",
                "signup_time": "지갑 연결만",
                "features": ["DeFi 거래", "개인 사용 가능", "즉시 거래"],
                "limitations": ["가스비 발생", "API 복잡"],
                "contract": "TKkeiboZVvpJSoJJiOKEe63vS5LGmk8mN5",
                "website": "https://justlend.org"
            },
            {
                "id": "energytron_live",
                "name": "EnergyTron.live",
                "type": "community_p2p",
                "difficulty": "⭐⭐⭐ (보통)",
                "signup_time": "10분",
                "features": ["P2P 거래", "저렴한 가격", "커뮤니티 기반"],
                "limitations": ["비공식", "안정성 보장 없음"],
                "website": "https://energytron.live"
            },
            {
                "id": "tron_energy_market",
                "name": "Tron Energy Market",
                "type": "p2p_marketplace",
                "difficulty": "⭐⭐⭐ (보통)",
                "signup_time": "15분",
                "features": ["마켓플레이스", "다양한 판매자", "경쟁 가격"],
                "limitations": ["개인 거래", "사기 위험"],
                "website": "https://tronenergy.market"
            }
        ]

    async def get_available_simple_providers(self) -> List[Dict[str, Any]]:
        """개인/소규모 프로젝트용 쉬운 에너지 공급업체 목록"""
        return [
            {
                "id": "trongrid_official",
                "name": "TronGrid 공식 API",
                "type": "information_only",
                "description": "TRON 재단 공식 API로 실시간 에너지 정보 조회",
                "cost": "무료 (월 10,000 요청)",
                "setup_time": "5분",
                "difficulty": "⭐ (매우 쉬움)",
                "features": ["실시간 데이터", "계정 정보", "가격 조회"],
                "limitations": ["정보 조회만", "실제 거래 불가"],
                "signup_url": "https://www.trongrid.io/register",
                "status": "recommended",
                "api_key_required": True
            },
            {
                "id": "tronscan_api",
                "name": "TronScan API",
                "type": "information_only", 
                "description": "트론 블록체인 익스플로러 API",
                "cost": "무료 (제한 없음)",
                "setup_time": "즉시",
                "difficulty": "⭐ (매우 쉬움)",
                "features": ["가격 조회", "통계 데이터"],
                "limitations": ["기본 정보만", "계정별 정보 제한적"],
                "signup_url": "https://tronscan.org",
                "status": "active",
                "api_key_required": False
            },
            {
                "id": "justlend_dapp",
                "name": "JustLend 에너지 대여",
                "type": "actual_trading",
                "description": "실제 에너지 대여가 가능한 DeFi 플랫폼",
                "cost": "10 TRX 최소 (약 $1.5)",
                "setup_time": "10분",
                "difficulty": "⭐⭐ (쉬움)",
                "features": ["실제 거래", "즉시 사용", "1일~30일 대여"],
                "limitations": ["스마트 컨트랙트 직접 호출", "가스비 별도"],
                "signup_url": "https://justlend.org",
                "status": "active",
                "api_key_required": False
            },
            {
                "id": "shasta_testnet",
                "name": "Shasta 테스트넷",
                "type": "testing",
                "description": "완전 무료로 모든 기능 테스트 가능",
                "cost": "완전 무료",
                "setup_time": "3분",
                "difficulty": "⭐ (매우 쉬움)",
                "features": ["무료 TRX", "실제 거래 시뮬레이션", "모든 기능 테스트"],
                "limitations": ["테스트 환경", "실제 가치 없음"],
                "signup_url": "https://www.trongrid.io/shasta",
                "status": "testing",
                "api_key_required": False
            },
            {
                "id": "community_pools",
                "name": "커뮤니티 에너지 풀",
                "type": "p2p_trading",
                "description": "개인간 소액 에너지 거래",
                "cost": "시장가 (보통 더 저렴)",
                "setup_time": "15분",
                "difficulty": "⭐⭐⭐ (보통)",
                "features": ["P2P 거래", "저렴한 가격", "소액 거래"],
                "limitations": ["비공식", "신뢰성 변동"],
                "signup_url": "https://t.me/TronEnergyShare",
                "status": "community",
                "api_key_required": False
            }
        ]

    async def get_quick_start_guide(self) -> Dict[str, Any]:
        """5분 시작 가이드"""
        return {
            "title": "5분 에너지 서비스 시작 가이드",
            "total_time": "5분",
            "cost": "무료",
            "target": "개인/소규모 프로젝트",
            "steps": [
                {
                    "step": 1,
                    "title": "TronGrid API 키 발급",
                    "time": "3분",
                    "actions": [
                        "https://www.trongrid.io/register 접속",
                        "이메일로 회원가입",
                        "대시보드에서 API 키 생성",
                        "월 10,000 요청 무료 한도 확인"
                    ],
                    "result": "TRON 공식 API 키 획득"
                },
                {
                    "step": 2,
                    "title": "환경 변수 설정",
                    "time": "1분",
                    "actions": [
                        ".env 파일에 TRONGRID_API_KEY=발급받은키 추가",
                        "USE_SIMPLE_ENERGY_SERVICE=true 설정",
                        "서버 재시작"
                    ],
                    "result": "API 연동 준비 완료"
                },
                {
                    "step": 3,
                    "title": "테스트 실행",
                    "time": "1분",
                    "actions": [
                        "GET /api/v1/simple-energy/price 호출",
                        "실시간 에너지 가격 확인", 
                        "GET /api/v1/simple-energy/providers 호출",
                        "사용 가능한 공급업체 목록 확인"
                    ],
                    "result": "실시간 에너지 정보 조회 성공"
                }
            ],
            "next_steps": [
                {
                    "title": "무료 테스트",
                    "description": "Shasta 테스트넷에서 무료로 실제 거래 체험",
                    "url": "https://www.trongrid.io/shasta"
                },
                {
                    "title": "소액 실제 거래",
                    "description": "JustLend에서 $1.5 정도로 실제 에너지 대여",
                    "url": "https://justlend.org"
                },
                {
                    "title": "대용량 서비스",
                    "description": "TronNRG, EnergyTRON 등 기업용 API로 업그레이드",
                    "url": "/docs/api-keys-setup-guide.md"
                }
            ],
            "trouble_shooting": [
                {
                    "problem": "API 키가 작동하지 않음",
                    "solution": "대시보드에서 키 상태 확인, IP 화이트리스트 설정"
                },
                {
                    "problem": "429 Too Many Requests",
                    "solution": "무료 한도 초과, 유료 플랜 업그레이드 또는 요청 빈도 조절"
                },
                {
                    "problem": "실제 거래가 안됨",
                    "solution": "정보 조회용 API이므로 JustLend나 커뮤니티 풀 이용"
                }
            ]
        }

    async def simulate_energy_purchase(
        self, 
        amount: int, 
        user_address: str = "", 
        duration_days: int = 1,
        provider: str = "auto"
    ) -> Dict[str, Any]:
        """에너지 구매 시뮬레이션 (개발/테스트용)"""
        try:
            # 실제 가격 정보 조회
            price_info = await self.get_trongrid_energy_price()
            if not price_info["success"]:
                price_info = await self.get_tronscan_energy_price()
            
            price_data = price_info["data"]
            total_cost_trx = amount * price_data["price_per_energy"]
            total_cost_usd = total_cost_trx * 0.15  # 대략적인 TRX-USD 환율

            # 현실적인 수수료 계산 (제공자별)
            if provider == "justlend":
                service_fee_rate = 0.015  # 1.5%
                min_cost = 10 * 0.15  # 10 TRX 최소
            elif provider == "community":
                service_fee_rate = 0.005  # 0.5%
                min_cost = 1 * 0.15   # 1 TRX 최소
            else:  # auto
                service_fee_rate = 0.02   # 2%
                min_cost = 0
            
            service_fee = max(total_cost_trx * service_fee_rate, min_cost / 0.15)
            final_cost_trx = total_cost_trx + service_fee

            return {
                "order_id": f"simple_{uuid.uuid4().hex[:8]}",
                "status": "simulated_success",
                "simulation": True,
                "energy_amount": amount,
                "provider": provider,
                "pricing": {
                    "price_per_energy_trx": price_data["price_per_energy"],
                    "energy_cost_trx": total_cost_trx,
                    "service_fee_trx": service_fee,
                    "total_cost_trx": final_cost_trx,
                    "total_cost_usd": final_cost_trx * 0.15
                },
                "rental_info": {
                    "duration_days": duration_days,
                    "expires_at": (datetime.now() + timedelta(days=duration_days)).isoformat(),
                    "user_address": user_address
                },
                "timestamp": datetime.now().isoformat(),
                "data_source": price_data["source"],
                "next_steps": [
                    {
                        "option": "무료 테스트",
                        "description": "Shasta 테스트넷에서 실제 거래 체험 (무료)",
                        "cost": "$0",
                        "url": "https://www.trongrid.io/shasta"
                    },
                    {
                        "option": "소액 실제 거래",
                        "description": "JustLend에서 실제 에너지 대여",
                        "cost": f"${final_cost_trx * 0.15:.2f} (최소 $1.5)",
                        "url": "https://justlend.org"
                    },
                    {
                        "option": "커뮤니티 거래",
                        "description": "P2P 에너지 거래 (더 저렴)",
                        "cost": f"${total_cost_trx * 0.15:.2f} (수수료 낮음)",
                        "url": "https://t.me/TronEnergyShare"
                    }
                ],
                "warning": "시뮬레이션 결과입니다. 실제 거래를 위해서는 위의 옵션을 선택하세요."
            }

        except Exception as e:
            logger.error(f"Failed to simulate energy purchase: {str(e)}")
            return {
                "order_id": f"simple_error_{uuid.uuid4().hex[:8]}",
                "status": "simulation_failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def get_timestamp(self) -> str:
        """현재 타임스탬프 반환"""
        return datetime.now().isoformat()

    async def _get_fallback_price_data(self, source: str) -> Dict[str, Any]:
        """API 실패시 대체 데이터"""
        return {
            "success": True,
            "data": {
                "price_per_energy": 0.00002,
                "price_in_sun": 20,
                "available_energy": 999999999,
                "timestamp": datetime.now().isoformat(),
                "source": f"{source} (Fallback)",
                "provider": "fallback",
                "note": "네트워크 오류로 인한 대체 데이터"
            }
        }


# 싱글톤 인스턴스
simple_energy_service = SimpleEnergyService()
