"""
수퍼어드민 전용 에너지 렌탈 관리 API
- 에너지 공급업체에서 구매
- 파트너별 할당 및 마진 관리
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_super_admin
from app.core.database import get_db
from app.models.user import User
from app.services.energy_rental_service import EnergyRentalService

router = APIRouter(prefix="/admin/energy-rental", tags=["Super Admin Energy Rental"])


class EnergyPurchaseRequest(BaseModel):
    provider_id: str
    energy_amount: int
    max_price_per_energy: Optional[Decimal] = None


class PartnerAllocationRequest(BaseModel):
    partner_id: int
    energy_amount: int
    margin_rate: Decimal  # 마진율 (예: 0.15 = 15%)
    price_per_energy: Decimal


@router.post("/purchase-from-provider")
async def purchase_energy_from_provider(
    request: EnergyPurchaseRequest,
    current_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """외부 에너지 공급업체에서 에너지 구매"""
    try:
        service = EnergyRentalService(db)
        
        # 에너지 공급업체에서 구매 로직
        purchase_result = service.purchase_from_external_provider(
            provider_id=request.provider_id,
            energy_amount=request.energy_amount,
            max_price=request.max_price_per_energy,
        )
        
        return {
            "success": True,
            "purchase": {
                "provider_id": request.provider_id,
                "energy_amount": request.energy_amount,
                "total_cost": purchase_result.get("total_cost"),
                "average_price": purchase_result.get("average_price"),
                "transaction_id": purchase_result.get("transaction_id"),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/allocate-to-partner")
async def allocate_energy_to_partner(
    request: PartnerAllocationRequest,
    current_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """파트너에게 에너지 할당 (마진 포함)"""
    try:
        service = EnergyRentalService(db)
        
        allocation = service.allocate_energy_to_partner(
            partner_id=request.partner_id,
            energy_amount=request.energy_amount,
            margin_rate=request.margin_rate,
            price_per_energy=request.price_per_energy,
        )
        
        return {
            "success": True,
            "allocation": {
                "partner_id": request.partner_id,
                "energy_amount": request.energy_amount,
                "price_with_margin": allocation.get("final_price"),
                "margin_amount": allocation.get("margin_amount"),
                "allocation_id": allocation.get("allocation_id"),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/partners/{partner_id}/energy-usage")
async def get_partner_energy_usage(
    partner_id: int,
    period_days: int = Query(30, description="조회 기간 (일)"),
    current_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """파트너별 에너지 사용 현황 조회"""
    try:
        service = EnergyRentalService(db)
        
        usage_stats = service.get_partner_energy_usage_for_admin(
            partner_id=partner_id, period_days=period_days
        )
        
        return {
            "success": True,
            "partner_id": partner_id,
            "period_days": period_days,
            "usage_stats": usage_stats,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/revenue-analytics")
async def get_energy_rental_revenue(
    period_days: int = Query(30, description="조회 기간 (일)"),
    current_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """에너지 렌탈 수익 분석"""
    try:
        service = EnergyRentalService(db)
        
        revenue_data = service.get_energy_rental_revenue_analytics(
            period_days=period_days
        )
        
        return {
            "success": True,
            "revenue_analytics": revenue_data,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/providers/status")
async def get_energy_providers_status(
    current_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    """외부 에너지 공급업체 상태 조회"""
    try:
        service = EnergyRentalService(db)
        
        providers_status = service.get_external_providers_status()
        
        return {
            "success": True,
            "providers": providers_status,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
