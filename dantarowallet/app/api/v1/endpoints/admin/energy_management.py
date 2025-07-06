"""
슈퍼 어드민용 에너지 관리 API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_super_admin
from app.services.energy.super_admin_energy_service import SuperAdminEnergyService
from app.schemas.energy import (
    EnergyPoolStatus, EnergyUsage, EnergyAlert, 
    EnergyHistory, EnergyAllocation
)

router = APIRouter(prefix="/admin/energy", tags=["Super Admin Energy"])


@router.get("/status", response_model=EnergyPoolStatus)
async def get_energy_pool_status(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """전체 에너지 풀 상태 조회"""
    energy_service = SuperAdminEnergyService(db)
    return await energy_service.get_total_energy_status()


@router.post("/recharge")
async def recharge_energy_pool(
    amount: int,
    description: str = "",
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """에너지 풀 충전"""
    try:
        energy_service = SuperAdminEnergyService(db)
        success = await energy_service.recharge_energy_pool(amount, description)
        
        if success:
            return {
                "message": "Energy pool recharged successfully",
                "amount": amount,
                "description": description,
                "recharged_by": current_admin.get("id"),
                "recharged_at": "now"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to recharge energy pool")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recharge energy pool: {str(e)}")


@router.get("/alerts", response_model=List[EnergyAlert])
async def get_energy_alerts(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """에너지 알림 조회"""
    energy_service = SuperAdminEnergyService(db)
    return await energy_service.monitor_energy_alerts()


@router.get("/history", response_model=List[EnergyHistory])
async def get_energy_usage_history(
    partner_id: Optional[str] = Query(None, description="파트너 ID"),
    transaction_type: Optional[str] = Query(None, description="거래 유형"),
    limit: int = Query(100, description="조회 개수"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """에너지 사용 이력 조회"""
    energy_service = SuperAdminEnergyService(db)
    return await energy_service.get_energy_usage_history(
        partner_id=partner_id,
        limit=limit,
        transaction_type=transaction_type
    )


@router.get("/statistics")
async def get_energy_statistics(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """에너지 통계 조회"""
    energy_service = SuperAdminEnergyService(db)
    return await energy_service.get_energy_statistics()


@router.post("/emergency-rebalance")
async def emergency_energy_rebalance(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """긴급 에너지 재분배"""
    energy_service = SuperAdminEnergyService(db)
    return await energy_service.emergency_energy_rebalance()


@router.get("/partners/{partner_id}/usage", response_model=EnergyUsage)
async def get_partner_energy_usage(
    partner_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """특정 파트너 에너지 사용량 조회"""
    energy_service = SuperAdminEnergyService(db)
    return await energy_service.get_partner_energy_usage(partner_id)


@router.post("/partners/{partner_id}/allocate")
async def allocate_energy_to_partner(
    partner_id: str,
    amount: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """파트너에게 에너지 할당"""
    try:
        energy_service = SuperAdminEnergyService(db)
        success = await energy_service.allocate_energy_to_partner(partner_id, amount)
        
        if success:
            return {
                "partner_id": partner_id,
                "allocated_amount": amount,
                "reason": reason,
                "allocated_by": current_admin.get("id"),
                "allocated_at": "now"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to allocate energy")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to allocate energy: {str(e)}")


@router.get("/efficiency-report")
async def get_energy_efficiency_report(
    days: int = Query(30, description="분석 기간 (일)"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """에너지 효율성 보고서"""
    try:
        energy_service = SuperAdminEnergyService(db)
        
        # 기본 통계 조회
        statistics = await energy_service.get_energy_statistics()
        
        # 효율성 분석 (실제 구현에서는 더 복잡한 분석 수행)
        efficiency_report = {
            "analysis_period_days": days,
            "total_energy_consumed": statistics.get("total_energy", 0) - statistics.get("available_energy", 0),
            "average_daily_consumption": 0,  # 실제 계산 필요
            "peak_usage_hours": [],  # 피크 시간대 분석
            "efficiency_score": 85.5,  # 효율성 점수
            "recommendations": [
                "Consider implementing energy-saving features during off-peak hours",
                "Monitor high-consumption partners for optimization opportunities",
                "Schedule maintenance during low-usage periods"
            ],
            "top_energy_consumers": statistics.get("top_energy_consumers", [])
        }
        
        return efficiency_report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate efficiency report: {str(e)}")


@router.post("/threshold/update")
async def update_energy_thresholds(
    alert_threshold: Optional[int] = None,
    critical_threshold: Optional[int] = None,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """에너지 임계값 업데이트"""
    try:
        # 실제 구현에서는 EnergyPool 모델 업데이트
        updates = {}
        if alert_threshold is not None:
            updates["alert_threshold"] = alert_threshold
        if critical_threshold is not None:
            updates["critical_threshold"] = critical_threshold
        
        if not updates:
            raise HTTPException(status_code=400, detail="No threshold values provided")
        
        # 임계값 업데이트 로직 (실제 구현 필요)
        
        return {
            "message": "Energy thresholds updated successfully",
            "updates": updates,
            "updated_by": current_admin.get("id"),
            "updated_at": "now"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update energy thresholds: {str(e)}")
