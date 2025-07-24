"""
파트너어드민 전용 에너지 렌탈 API
- 수퍼어드민에서 에너지 렌탈
- 사용자별 에너지 사용 관리
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_partner_admin
from app.core.database import get_db
from app.models.user import User
from app.services.energy_rental_service import EnergyRentalService

router = APIRouter(prefix="/partner/energy-rental", tags=["Partner Energy Rental"])


class EnergyRentalRequest(BaseModel):
    energy_amount: int
    duration_hours: Optional[int] = 24  # 기본 24시간


class UserEnergyAllocationRequest(BaseModel):
    user_id: int
    energy_amount: int
    transaction_id: str  # 출금 트랜잭션 ID


@router.post("/rent-from-super-admin")
async def rent_energy_from_super_admin(
    request: EnergyRentalRequest,
    current_user: User = Depends(get_current_partner_admin),
    db: Session = Depends(get_db),
):
    """수퍼어드민에서 에너지 렌탈"""
    try:
        service = EnergyRentalService(db)
        
        # 파트너 ID 추출
        partner_id = getattr(current_user, "partner_id", None)
        if not partner_id:
            raise HTTPException(status_code=403, detail="파트너 권한이 필요합니다")
        
        rental_result = service.rent_energy_from_super_admin(
            partner_id=partner_id,
            energy_amount=request.energy_amount,
            duration_hours=request.duration_hours or 24,
        )
        
        return {
            "success": True,
            "rental": {
                "partner_id": partner_id,
                "energy_amount": request.energy_amount,
                "duration_hours": request.duration_hours,
                "total_cost": rental_result.get("total_cost"),
                "rental_id": rental_result.get("rental_id"),
                "expires_at": rental_result.get("expires_at"),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/allocate-energy-for-withdrawal")
async def allocate_energy_for_user_withdrawal(
    request: UserEnergyAllocationRequest,
    current_user: User = Depends(get_current_partner_admin),
    db: Session = Depends(get_db),
):
    """사용자 출금을 위한 에너지 할당"""
    try:
        service = EnergyRentalService(db)
        
        partner_id = getattr(current_user, "partner_id", None)
        if not partner_id:
            raise HTTPException(status_code=403, detail="파트너 권한이 필요합니다")
        
        allocation_result = service.allocate_energy_for_withdrawal(
            partner_id=partner_id,
            user_id=request.user_id,
            energy_amount=request.energy_amount,
            transaction_id=request.transaction_id,
        )
        
        return {
            "success": True,
            "allocation": {
                "user_id": request.user_id,
                "energy_amount": request.energy_amount,
                "transaction_id": request.transaction_id,
                "allocation_id": allocation_result.get("allocation_id"),
                "remaining_partner_energy": allocation_result.get("remaining_energy"),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my-energy-balance")
async def get_partner_energy_balance(
    current_user: User = Depends(get_current_partner_admin),
    db: Session = Depends(get_db),
):
    """파트너의 현재 에너지 잔액 조회"""
    try:
        service = EnergyRentalService(db)
        
        partner_id = getattr(current_user, "partner_id", None)
        if not partner_id:
            raise HTTPException(status_code=403, detail="파트너 권한이 필요합니다")
        
        balance_info = service.get_partner_energy_balance(partner_id=partner_id)
        
        return {
            "success": True,
            "partner_id": partner_id,
            "energy_balance": balance_info,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users-energy-usage")
async def get_users_energy_usage(
    period_days: int = Query(7, description="조회 기간 (일)"),
    current_user: User = Depends(get_current_partner_admin),
    db: Session = Depends(get_db),
):
    """파트너 사용자들의 에너지 사용 현황"""
    try:
        service = EnergyRentalService(db)
        
        partner_id = getattr(current_user, "partner_id", None)
        if not partner_id:
            raise HTTPException(status_code=403, detail="파트너 권한이 필요합니다")
        
        usage_data = service.get_partner_users_energy_usage(
            partner_id=partner_id, period_days=period_days
        )
        
        return {
            "success": True,
            "partner_id": partner_id,
            "period_days": period_days,
            "users_usage": usage_data,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/billing-summary")
async def get_energy_billing_summary(
    month: Optional[int] = Query(None, description="월 (1-12)"),
    year: Optional[int] = Query(None, description="년도"),
    current_user: User = Depends(get_current_partner_admin),
    db: Session = Depends(get_db),
):
    """에너지 사용 청구 요약"""
    try:
        service = EnergyRentalService(db)
        
        partner_id = getattr(current_user, "partner_id", None)
        if not partner_id:
            raise HTTPException(status_code=403, detail="파트너 권한이 필요합니다")
        
        # 기본값: 현재 월/년
        if not month or not year:
            now = datetime.now()
            month = month or now.month
            year = year or now.year
        
        billing_summary = service.get_partner_energy_billing_summary(
            partner_id=partner_id, month=month, year=year
        )
        
        return {
            "success": True,
            "partner_id": partner_id,
            "billing_period": f"{year}-{month:02d}",
            "billing_summary": billing_summary,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
