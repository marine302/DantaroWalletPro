"""
외부 에너지 공급자 API 엔드포인트
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.external_energy import EnergyProviderType, PurchaseStatus
from app.services.external_energy_service import external_energy_service, safe_get_value
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


class PurchaseRequest(BaseModel):
    """구매 요청 모델"""
    provider_type: EnergyProviderType = Field(..., description="공급자 유형")
    energy_amount: int = Field(..., ge=1, description="구매할 에너지량")
    max_price: Optional[Decimal] = Field(None, description="최대 허용 가격")
    purchase_type: str = Field("manual", description="구매 유형")


class PurchaseResponse(BaseModel):
    """구매 응답 모델"""
    purchase_id: int
    provider_type: EnergyProviderType
    energy_amount: int
    price_per_energy: Decimal
    total_cost: Decimal
    status: PurchaseStatus
    created_at: datetime


@router.get("/providers")
async def get_providers(
    active_only: bool = Query(True, description="활성 공급자만 조회"),
    session: AsyncSession = Depends(get_db)
):
    """공급자 목록 조회"""
    try:
        if active_only:
            providers = await external_energy_service.get_active_providers(session)
        else:
            providers = await external_energy_service.get_all_providers(session)
        
        result = []
        for provider in providers:
            price_updated_at = safe_get_value(provider, 'price_updated_at')
            result.append({
                "id": safe_get_value(provider, 'id'),
                "provider_type": safe_get_value(provider, 'provider_type'),
                "name": safe_get_value(provider, 'name'),
                "is_active": safe_get_value(provider, 'is_active'),
                "priority": safe_get_value(provider, 'priority'),
                "success_rate": float(safe_get_value(provider, 'success_rate', 0)),
                "last_price": float(safe_get_value(provider, 'last_price', 0)) if safe_get_value(provider, 'last_price') else None,
                "price_updated_at": price_updated_at.isoformat() if price_updated_at else None
            })
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"공급자 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="공급자 조회 중 오류가 발생했습니다")


@router.get("/prices")
async def get_current_prices(
    force_refresh: bool = Query(False, description="강제 새로고침"),
    session: AsyncSession = Depends(get_db)
):
    """현재 에너지 가격 조회"""
    try:
        # 가격 조회
        prices = await external_energy_service.get_current_prices(session)
        
        if not prices:
            raise HTTPException(status_code=503, detail="가격 정보를 조회할 수 없습니다")
        
        # 최적 가격 찾기
        best_price = None
        if prices:
            best_price = min(prices, key=lambda x: x['price_per_energy'])
        
        # 응답 구성
        response = {
            "prices": prices,
            "updated_at": datetime.utcnow().isoformat(),
            "best_price": best_price
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"가격 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="가격 조회 중 오류가 발생했습니다")


@router.post("/purchase")
async def execute_purchase(
    request: PurchaseRequest,
    session: AsyncSession = Depends(get_db)
):
    """에너지 구매 실행"""
    try:
        # 구매 실행
        purchase = await external_energy_service.execute_purchase(
            provider_type=request.provider_type,
            energy_amount=request.energy_amount,
            session=session,
            purchase_type=request.purchase_type
        )
        
        if not purchase:
            raise HTTPException(status_code=400, detail="구매 실행에 실패했습니다")
        
        # 응답 구성
        response = PurchaseResponse(
            purchase_id=safe_get_value(purchase, 'id', 0),
            provider_type=safe_get_value(purchase.provider, 'provider_type', EnergyProviderType.JUSTLEND),
            energy_amount=safe_get_value(purchase, 'energy_amount', 0),
            price_per_energy=safe_get_value(purchase, 'price_per_energy', Decimal('0')),
            total_cost=safe_get_value(purchase, 'total_cost', Decimal('0')),
            status=PurchaseStatus(safe_get_value(purchase, 'status', 'pending')),
            created_at=safe_get_value(purchase, 'created_at', datetime.utcnow())
        )
        
        return response
        
    except Exception as e:
        logger.error(f"구매 실행 오류: {e}")
        raise HTTPException(status_code=500, detail="구매 실행 중 오류가 발생했습니다")


@router.get("/purchase/{purchase_id}")
async def get_purchase_details(
    purchase_id: int = Path(..., description="구매 ID"),
    session: AsyncSession = Depends(get_db)
):
    """구매 상세 정보 조회"""
    try:
        # 구매 기록 조회
        purchases = await external_energy_service.get_purchase_history(
            session=session,
            limit=1000
        )
        
        purchase = next((p for p in purchases if safe_get_value(p, 'id') == purchase_id), None)
        
        if not purchase:
            raise HTTPException(status_code=404, detail="구매 기록을 찾을 수 없습니다")
        
        # 응답 구성
        created_at = safe_get_value(purchase, 'created_at')
        completed_at = safe_get_value(purchase, 'completed_at')
        
        response = {
            "purchase_id": safe_get_value(purchase, 'id'),
            "provider": {
                "id": safe_get_value(purchase.provider, 'id'),
                "name": safe_get_value(purchase.provider, 'name'),
                "provider_type": safe_get_value(purchase.provider, 'provider_type')
            },
            "energy_amount": safe_get_value(purchase, 'energy_amount'),
            "price_per_energy": float(safe_get_value(purchase, 'price_per_energy', 0)),
            "total_cost": float(safe_get_value(purchase, 'total_cost', 0)),
            "status": safe_get_value(purchase, 'status'),
            "purchase_type": safe_get_value(purchase, 'purchase_type'),
            "transaction_hash": safe_get_value(purchase, 'transaction_hash'),
            "created_at": created_at.isoformat() if created_at else None,
            "completed_at": completed_at.isoformat() if completed_at else None
        }
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"구매 상세 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="구매 상세 조회 중 오류가 발생했습니다")


@router.get("/purchase")
async def get_purchase_history(
    provider_id: Optional[int] = Query(None, description="공급자 ID"),
    limit: int = Query(100, ge=1, le=1000, description="조회 개수"),
    session: AsyncSession = Depends(get_db)
):
    """구매 히스토리 조회"""
    try:
        # 구매 히스토리 조회
        purchases = await external_energy_service.get_purchase_history(
            session=session,
            provider_id=provider_id,
            limit=limit
        )
        
        result = []
        for purchase in purchases:
            created_at = safe_get_value(purchase, 'created_at')
            completed_at = safe_get_value(purchase, 'completed_at')
            
            result.append({
                "purchase_id": safe_get_value(purchase, 'id'),
                "provider": {
                    "id": safe_get_value(purchase.provider, 'id'),
                    "name": safe_get_value(purchase.provider, 'name'),
                    "provider_type": safe_get_value(purchase.provider, 'provider_type')
                },
                "energy_amount": safe_get_value(purchase, 'energy_amount'),
                "price_per_energy": float(safe_get_value(purchase, 'price_per_energy', 0)),
                "total_cost": float(safe_get_value(purchase, 'total_cost', 0)),
                "status": safe_get_value(purchase, 'status'),
                "purchase_type": safe_get_value(purchase, 'purchase_type'),
                "created_at": created_at.isoformat() if created_at else None,
                "completed_at": completed_at.isoformat() if completed_at else None
            })
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"구매 히스토리 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="구매 히스토리 조회 중 오류가 발생했습니다")


@router.post("/stats/update")
async def update_provider_stats(
    session: AsyncSession = Depends(get_db)
):
    """공급자 통계 업데이트"""
    try:
        await external_energy_service.update_provider_stats(session)
        
        return JSONResponse(content={"message": "공급자 통계가 업데이트되었습니다"})
        
    except Exception as e:
        logger.error(f"공급자 통계 업데이트 오류: {e}")
        raise HTTPException(status_code=500, detail="공급자 통계 업데이트 중 오류가 발생했습니다")


@router.get("/stats")
async def get_provider_stats(
    session: AsyncSession = Depends(get_db)
):
    """공급자 통계 조회"""
    try:
        providers = await external_energy_service.get_all_providers(session)
        
        stats = []
        for provider in providers:
            stats.append({
                "provider_id": safe_get_value(provider, 'id'),
                "provider_name": safe_get_value(provider, 'name'),
                "provider_type": safe_get_value(provider, 'provider_type'),
                "success_rate": float(safe_get_value(provider, 'success_rate', 0)),
                "total_purchases": safe_get_value(provider, 'total_purchases', 0),
                "total_energy_purchased": float(safe_get_value(provider, 'total_energy_purchased', 0)),
                "average_response_time": safe_get_value(provider, 'average_response_time', 0),
                "is_active": safe_get_value(provider, 'is_active')
            })
        
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.error(f"공급자 통계 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="공급자 통계 조회 중 오류가 발생했습니다")
