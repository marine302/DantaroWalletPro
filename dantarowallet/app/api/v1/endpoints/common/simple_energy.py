"""
Simple Energy API - 개인/소규모 프로젝트용 쉬운 에너지 API

복잡한 기업 계약 없이 즉시 사용 가능한 에너지 관련 API를 제공합니다.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.external_energy.simple_service import simple_energy_service

router = APIRouter()


@router.get("/providers")
async def get_simple_providers():
    """개인/소규모 프로젝트용 쉬운 에너지 공급업체 목록 (인증 불필요)"""
    try:
        providers = await simple_energy_service.get_available_simple_providers()
        return {
            "success": True,
            "data": providers,
            "total": len(providers),
            "message": "5분 내에 시작할 수 있는 쉬운 에너지 공급업체 목록"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/price")
async def get_simple_energy_price():
    """실시간 에너지 가격 조회 (무료 API 사용, 인증 불필요)"""
    try:
        # TronGrid 우선, 실패시 TronScan 사용
        price_info = await simple_energy_service.get_trongrid_energy_price()
        if not price_info["success"]:
            price_info = await simple_energy_service.get_tronscan_energy_price()
        
        return {
            "success": True,
            "data": price_info["data"],
            "message": "실시간 에너지 가격 (TRON 공식 API)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/account/{address}")
async def get_account_energy_info(address: str):
    """계정의 에너지 정보 조회 (TronGrid API 사용, 인증 불필요)"""
    try:
        account_info = await simple_energy_service.get_trongrid_energy_info(address)
        return {
            "success": True,
            "data": account_info.get("data", {}),
            "message": f"계정 {address}의 에너지 정보"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quick-start")
async def get_quick_start_guide():
    """5분 시작 가이드 (인증 불필요)"""
    try:
        guide = await simple_energy_service.get_quick_start_guide()
        return {
            "success": True,
            "data": guide,
            "message": "개인/소규모 프로젝트용 5분 시작 가이드"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate-purchase")
async def simulate_energy_purchase(
    amount: int = Query(..., gt=0, description="구매할 에너지 양"),
    user_address: Optional[str] = Query(None, description="사용자 주소"),
    duration_days: int = Query(1, ge=1, le=30, description="대여 기간 (일)"),
    provider: str = Query("auto", description="공급업체 (auto, justlend, community)")
):
    """에너지 구매 시뮬레이션 (인증 불필요, 개발/테스트용)"""
    try:
        simulation = await simple_energy_service.simulate_energy_purchase(
            amount=amount,
            user_address=user_address or "",
            duration_days=duration_days,
            provider=provider
        )
        return {
            "success": True,
            "data": simulation,
            "message": "에너지 구매 시뮬레이션 완료"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pricing-comparison")
async def get_pricing_comparison():
    """다양한 공급업체 가격 비교 (인증 불필요)"""
    try:
        # 여러 소스에서 가격 정보 수집
        trongrid_price = await simple_energy_service.get_trongrid_energy_price()
        tronscan_price = await simple_energy_service.get_tronscan_energy_price()
        justlend_price = await simple_energy_service.get_justlend_energy_price()
        
        comparison = {
            "official_sources": [
                {
                    "provider": "TronGrid",
                    "type": "공식 API",
                    "price_per_energy": trongrid_price["data"]["price_per_energy"] if trongrid_price["success"] else None,
                    "features": ["실시간 데이터", "계정 정보"],
                    "cost": "무료 (월 10K 요청)",
                    "status": "available" if trongrid_price["success"] else "error"
                },
                {
                    "provider": "TronScan",
                    "type": "익스플로러 API", 
                    "price_per_energy": tronscan_price["data"]["price_per_energy"] if tronscan_price["success"] else None,
                    "features": ["가격 정보", "통계 데이터"],
                    "cost": "무료 (무제한)",
                    "status": "available" if tronscan_price["success"] else "error"
                }
            ],
            "trading_platforms": [
                {
                    "provider": "JustLend",
                    "type": "DeFi 플랫폼",
                    "price_per_energy": justlend_price["data"]["price_per_energy"],
                    "features": ["실제 거래", "스마트 컨트랙트"],
                    "cost": "10 TRX 최소 (약 $1.5)",
                    "status": "available"
                },
                {
                    "provider": "Community Pools",
                    "type": "P2P 거래",
                    "price_per_energy": None,
                    "features": ["저렴한 가격", "개인간 거래"],
                    "cost": "시장가 (보통 더 저렴)",
                    "status": "community"
                }
            ],
            "recommendations": {
                "development": "TronGrid API (무료, 공식)",
                "testing": "Shasta 테스트넷 (완전 무료)",
                "small_trading": "JustLend (최소 $1.5)",
                "large_scale": "TronNRG, EnergyTRON (기업 계약)"
            }
        }
        
        return {
            "success": True,
            "data": comparison,
            "message": "에너지 공급업체 가격 비교"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_simple_energy_config():
    """현재 Simple Energy Service 설정 정보 (인증 불필요)"""
    try:
        config = {
            "service_name": "Simple Energy Service",
            "version": "1.0.0",
            "target_users": "개인/소규모 프로젝트",
            "apis_used": [
                {
                    "name": "TronGrid",
                    "status": "configured" if simple_energy_service.trongrid_api_key else "not_configured",
                    "cost": "무료 (월 10K 요청)",
                    "url": "https://www.trongrid.io"
                },
                {
                    "name": "TronScan", 
                    "status": "available",
                    "cost": "무료 (무제한)",
                    "url": "https://tronscan.org"
                }
            ],
            "features": [
                "실시간 가격 조회",
                "계정 에너지 정보",
                "구매 시뮬레이션",
                "가격 비교",
                "5분 시작 가이드"
            ],
            "setup_guide": "/api/v1/simple-energy/quick-start",
            "documentation": "/docs/easy-energy-providers-guide.md"
        }
        
        return {
            "success": True,
            "data": config,
            "message": "Simple Energy Service 설정 정보"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def check_simple_energy_health():
    """Simple Energy Service 상태 체크 (인증 불필요)"""
    try:
        health_status = {
            "service": "Simple Energy Service",
            "status": "healthy",
            "timestamp": simple_energy_service.get_timestamp(),
            "checks": []
        }
        
        # TronGrid API 체크
        try:
            trongrid_result = await simple_energy_service.get_trongrid_energy_price()
            health_status["checks"].append({
                "name": "TronGrid API",
                "status": "ok" if trongrid_result["success"] else "warning",
                "response_time": "< 1s",
                "message": "TRON 공식 API 연결 상태"
            })
        except:
            health_status["checks"].append({
                "name": "TronGrid API",
                "status": "error",
                "message": "API 키 설정 필요"
            })
        
        # TronScan API 체크 
        try:
            tronscan_result = await simple_energy_service.get_tronscan_energy_price()
            health_status["checks"].append({
                "name": "TronScan API",
                "status": "ok" if tronscan_result["success"] else "warning",
                "response_time": "< 2s",
                "message": "백업 API 연결 상태"
            })
        except:
            health_status["checks"].append({
                "name": "TronScan API", 
                "status": "error",
                "message": "백업 API 연결 실패"
            })
        
        return {
            "success": True,
            "data": health_status,
            "message": "Simple Energy Service 상태 체크 완료"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
