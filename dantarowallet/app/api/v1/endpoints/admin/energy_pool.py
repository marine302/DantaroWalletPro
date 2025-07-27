"""
에너지 풀 관리 API 엔드포인트
문서 40번 4.5절 멀티 에너지 공급원 관리 API
"""

from decimal import Decimal
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_admin_user
from app.services.energy_pool_service import EnergyPoolService
from app.models.energy_pool import EnergySourceType, EnergySourceStatus
from app.models.user import User
from app.schemas.energy_pool import (
    EnergyPoolCreate,
    EnergyPoolUpdate,
    EnergyPoolResponse,
    EnergyAllocationRequest,
    EnergyAllocationResponse,
    EnergyCostCalculation,
)

router = APIRouter()


@router.get("/summary", response_model=Dict[str, Any])
async def get_energy_pool_summary(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """
    에너지 풀 현황 요약
    본사 관리자만 접근 가능
    """
    service = EnergyPoolService(db)
    summary = await service.get_energy_pool_summary()
    return summary


@router.get("/optimal-source/{required_energy}")
async def get_optimal_energy_source(
    required_energy: Decimal,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """
    최적 에너지 공급원 조회
    우선순위 기반 자동 선택
    """
    service = EnergyPoolService(db)
    source = await service.get_optimal_energy_source(required_energy)
    
    if not source:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="사용 가능한 에너지 공급원이 없습니다"
        )
    
    return {
        "source_id": source.id,
        "source_type": source.source_type.value,
        "available_energy": source.available_energy,
        "wallet_address": source.wallet_address,
    }


@router.post("/allocate", response_model=EnergyAllocationResponse)
async def allocate_energy(
    request: EnergyAllocationRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """
    에너지 할당 처리
    파트너사 지갑에 에너지 위임
    """
    service = EnergyPoolService(db)
    success = await service.allocate_energy(
        source_id=request.source_id,
        amount=request.amount,
        partner_wallet=request.partner_wallet
    )
    
    if not success:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="에너지 할당에 실패했습니다"
        )
    
    return EnergyAllocationResponse(
        success=True,
        message=f"{request.amount} 에너지가 {request.partner_wallet}에 할당되었습니다"
    )


@router.post("/calculate-cost", response_model=EnergyCostCalculation)
async def calculate_energy_cost(
    energy_amount: Decimal,
    source_type: EnergySourceType,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """
    에너지 비용 계산
    마진 및 SaaS 수수료 포함
    """
    service = EnergyPoolService(db)
    cost = await service.calculate_energy_cost(energy_amount, source_type)
    
    # SaaS 수수료 (건당 1 TRX)
    saas_fee = Decimal("1.0")
    total_cost = cost + saas_fee
    
    return EnergyCostCalculation(
        energy_amount=energy_amount,
        source_type=source_type.value,
        base_cost=cost,
        saas_fee=saas_fee,
        total_cost=total_cost,
        margin_rate=Decimal("0.175")  # 17.5%
    )


@router.put("/status/{source_id}")
async def update_energy_source_status(
    source_id: int,
    status: EnergySourceStatus,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """
    에너지 공급원 상태 업데이트
    """
    service = EnergyPoolService(db)
    success = await service.update_energy_status(source_id, status)
    
    if not success:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="에너지 공급원을 찾을 수 없습니다"
        )
    
    return {"message": f"에너지 공급원 {source_id} 상태가 {status.value}로 업데이트되었습니다"}


@router.get("/health-check")
async def energy_sources_health_check(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """
    모든 에너지 공급원 상태 확인
    실시간 모니터링용
    """
    from app.models.energy_pool import EnergyPool
    
    pools = db.query(EnergyPool).filter(EnergyPool.is_active == True).all()
    
    health_status = []
    for pool in pools:
        status_info = {
            "source_id": pool.id,
            "source_type": pool.source_type.value,
            "status": pool.status.value,
            "available_energy": pool.available_energy,
            "utilization_rate": (pool.total_energy - pool.available_energy) / pool.total_energy * 100 if pool.total_energy > 0 else 0,
            "last_updated": pool.last_updated,
        }
        health_status.append(status_info)
    
    return {
        "total_sources": len(health_status),
        "healthy_sources": len([s for s in health_status if s["status"] == "active"]),
        "sources": health_status
    }
