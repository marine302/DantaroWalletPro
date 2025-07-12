"""
에너지 렌탈 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from decimal import Decimal
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.energy_rental_service import EnergyRentalService
from app.models.energy_rental import (
    RentalPlanType, SubscriptionTier, PaymentStatus
)

router = APIRouter(prefix="/energy-rental", tags=["energy-rental"])

# Request Models
class CreateRentalPlanRequest(BaseModel):
    partner_id: int
    plan_type: RentalPlanType
    subscription_tier: Optional[SubscriptionTier] = None
    plan_name: str
    price_per_energy: Decimal = Field(..., gt=0)
    discount_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    auto_recharge_enabled: bool = False
    auto_recharge_threshold: Optional[int] = None
    auto_recharge_amount: Optional[int] = None

class AllocateEnergyRequest(BaseModel):
    partner_id: int
    energy_amount: int = Field(..., gt=0)
    from_pool_id: Optional[int] = None

class RecordEnergyUsageRequest(BaseModel):
    partner_id: int
    energy_used: int = Field(..., gt=0)
    transaction_hash: str
    from_address: str
    to_address: str
    metadata: Optional[Dict[str, Any]] = None

class UpdatePaymentStatusRequest(BaseModel):
    payment_status: PaymentStatus

# API Endpoints

@router.post("/rental-plans", summary="렌탈 플랜 생성")
async def create_rental_plan(
    request: CreateRentalPlanRequest,
    db: Session = Depends(get_db)
):
    """새로운 에너지 렌탈 플랜을 생성합니다."""
    try:
        service = EnergyRentalService(db)
        
        rental_plan = service.create_rental_plan(
            partner_id=request.partner_id,
            plan_type=request.plan_type,
            subscription_tier=request.subscription_tier,
            plan_name=request.plan_name,
            price_per_energy=request.price_per_energy,
            discount_rate=request.discount_rate,
            auto_recharge_enabled=request.auto_recharge_enabled,
            auto_recharge_threshold=request.auto_recharge_threshold,
            auto_recharge_amount=request.auto_recharge_amount
        )
        
        return {
            "success": True,
            "rental_plan": {
                "id": rental_plan.id,
                "partner_id": rental_plan.partner_id,
                "plan_name": rental_plan.plan_name,
                "plan_type": rental_plan.plan_type.value,
                "subscription_tier": getattr(rental_plan, 'subscription_tier', None),
                "created_at": rental_plan.created_at.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/allocate-energy", summary="에너지 할당")
async def allocate_energy(
    request: AllocateEnergyRequest,
    db: Session = Depends(get_db)
):
    """파트너에게 에너지를 할당합니다."""
    try:
        service = EnergyRentalService(db)
        
        allocation = service.allocate_energy(
            partner_id=request.partner_id,
            energy_amount=request.energy_amount,
            from_pool_id=request.from_pool_id
        )
        
        return {
            "success": True,
            "allocation": {
                "id": allocation.id,
                "partner_id": allocation.partner_id,
                "allocated_energy": allocation.allocated_energy,
                "remaining_energy": allocation.remaining_energy,
                "expiry_date": allocation.expiry_date.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/record-usage", summary="에너지 사용 기록")
async def record_energy_usage(
    request: RecordEnergyUsageRequest,
    db: Session = Depends(get_db)
):
    """에너지 사용을 기록합니다."""
    try:
        service = EnergyRentalService(db)
        
        usage_record = service.record_energy_usage(
            partner_id=request.partner_id,
            energy_used=request.energy_used,
            transaction_hash=request.transaction_hash,
            from_address=request.from_address,
            to_address=request.to_address,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "usage_record": {
                "id": usage_record.id,
                "partner_id": usage_record.partner_id,
                "energy_used": usage_record.energy_used,
                "total_cost": float(getattr(usage_record, 'total_cost', 0)),
                "transaction_hash": usage_record.transaction_hash,
                "used_at": usage_record.used_at.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/partner/{partner_id}/usage-statistics", summary="파트너 사용 통계")
async def get_partner_usage_statistics(
    partner_id: int,
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    db: Session = Depends(get_db)
):
    """파트너의 에너지 사용 통계를 조회합니다."""
    try:
        service = EnergyRentalService(db)
        
        stats = service.get_partner_usage_statistics(
            partner_id=partner_id,
            period_start=period_start,
            period_end=period_end
        )
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/billing/{partner_id}", summary="청구서 생성")
async def generate_billing_record(
    partner_id: int,
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    db: Session = Depends(get_db)
):
    """청구서를 생성합니다."""
    try:
        service = EnergyRentalService(db)
        
        billing_record = service.generate_billing_record(
            partner_id=partner_id,
            billing_period_start=period_start,
            billing_period_end=period_end
        )
        
        return {
            "success": True,
            "billing_record": {
                "id": billing_record.id,
                "invoice_number": billing_record.invoice_number,
                "partner_id": billing_record.partner_id,
                "total_energy_used": billing_record.total_energy_used,
                "final_amount": float(getattr(billing_record, 'final_amount', 0)),
                "payment_status": billing_record.payment_status.value,
                "due_date": billing_record.due_date.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/partner/{partner_id}/billing-history", summary="청구 이력")
async def get_billing_history(
    partner_id: int,
    db: Session = Depends(get_db)
):
    """파트너의 청구 이력을 조회합니다."""
    try:
        service = EnergyRentalService(db)
        
        billing_history = service.get_billing_history(partner_id)
        
        return {
            "success": True,
            "billing_history": billing_history
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/billing/{billing_id}/payment-status", summary="결제 상태 업데이트")
async def update_payment_status(
    billing_id: int,
    request: UpdatePaymentStatusRequest,
    db: Session = Depends(get_db)
):
    """청구서의 결제 상태를 업데이트합니다."""
    try:
        service = EnergyRentalService(db)
        
        success = service.update_payment_status(
            billing_record_id=billing_id,
            payment_status=request.payment_status
        )
        
        return {
            "success": success,
            "message": "결제 상태가 업데이트되었습니다." if success else "업데이트 실패"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/energy-pools/status", summary="에너지 풀 상태")
async def get_energy_pool_status(
    db: Session = Depends(get_db)
):
    """에너지 풀 상태를 조회합니다."""
    try:
        service = EnergyRentalService(db)
        
        pool_status = service.get_energy_pool_status()
        
        return {
            "success": True,
            "energy_pools": pool_status
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/system/status", summary="시스템 상태")
async def get_system_status(
    db: Session = Depends(get_db)
):
    """시스템 전체 상태를 조회합니다."""
    try:
        service = EnergyRentalService(db)
        
        system_status = service.get_system_status()
        
        return {
            "success": True,
            "system_status": system_status
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/partner/{partner_id}/energy-allocation", summary="파트너 에너지 할당 정보")
async def get_partner_energy_allocation(
    partner_id: int,
    db: Session = Depends(get_db)
):
    """파트너의 에너지 할당 정보를 조회합니다."""
    try:
        service = EnergyRentalService(db)
        
        allocation_info = service.get_partner_energy_allocation(partner_id)
        
        return {
            "success": True,
            "allocation": allocation_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/partner/{partner_id}/auto-recharge-check", summary="자동 재충전 확인")
async def auto_recharge_check(
    partner_id: int,
    db: Session = Depends(get_db)
):
    """자동 재충전 확인 및 실행합니다."""
    try:
        service = EnergyRentalService(db)
        
        recharge_executed = service.auto_recharge_check(partner_id)
        
        return {
            "success": True,
            "recharge_executed": recharge_executed,
            "message": "자동 재충전이 실행되었습니다." if recharge_executed else "자동 재충전이 필요하지 않습니다."
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/rental-plans", summary="활성 렌탈 플랜 조회")
async def get_active_rental_plans(
    partner_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """활성 렌탈 플랜을 조회합니다."""
    try:
        service = EnergyRentalService(db)
        
        rental_plans = service.get_active_rental_plans(partner_id)
        
        return {
            "success": True,
            "rental_plans": rental_plans
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/rental-plans/{plan_id}/deactivate", summary="렌탈 플랜 비활성화")
async def deactivate_rental_plan(
    plan_id: int,
    db: Session = Depends(get_db)
):
    """렌탈 플랜을 비활성화합니다."""
    try:
        service = EnergyRentalService(db)
        
        success = service.deactivate_rental_plan(plan_id)
        
        return {
            "success": success,
            "message": "렌탈 플랜이 비활성화되었습니다." if success else "비활성화 실패"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
