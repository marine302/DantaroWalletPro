"""
TRON 에너지 풀 관리 API 엔드포인트
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_admin_user
from app.models.user import User
from app.services.energy_pool_service import EnergyPoolService
from app.schemas.energy import (
    EnergyPoolStatus, EnergyRechargeRequest, EnergyUsageStats,
    EnergyQueueCreate, QueueStatus, CreateEnergyAlert,
    EmergencyWithdrawalCreate, EmergencyWithdrawalResponse
)
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["에너지 풀 관리"])


@router.get("/status", response_model=EnergyPoolStatus)
async def get_energy_pool_status(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    현재 에너지 풀 상태를 조회합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        status = await energy_service.get_energy_status()
        
        logger.info(f"관리자 {current_admin.id}가 에너지 풀 상태 조회")
        return status
        
    except Exception as e:
        logger.error(f"에너지 풀 상태 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="에너지 풀 상태 조회 중 오류가 발생했습니다."
        )


@router.post("/recharge")
async def recharge_energy_pool(
    recharge_data: EnergyRechargeRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    에너지 풀을 충전합니다.
    TRX를 freeze하여 에너지를 확보합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        result = await energy_service.recharge_energy(recharge_data)
        
        logger.info(f"관리자 {current_admin.id}가 에너지 풀 충전: {recharge_data.trx_amount} TRX")
        return result
        
    except Exception as e:
        logger.error(f"에너지 풀 충전 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="에너지 풀 충전 중 오류가 발생했습니다."
        )


@router.get("/usage-stats", response_model=EnergyUsageStats)
async def get_energy_usage_stats(
    days: int = Query(7, ge=1, le=30, description="통계 기간 (일)"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    에너지 사용 통계를 조회합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        stats = await energy_service.get_usage_statistics(days)
        
        logger.info(f"관리자 {current_admin.id}가 에너지 사용 통계 조회 ({days}일)")
        return stats
        
    except Exception as e:
        logger.error(f"에너지 사용 통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="에너지 사용 통계 조회 중 오류가 발생했습니다."
        )


@router.get("/queue", response_model=List[Dict[str, Any]])
async def get_energy_queue(
    status_filter: Optional[str] = Query(None, description="상태 필터"),
    limit: int = Query(100, ge=1, le=1000, description="조회 개수"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    에너지 대기 큐를 조회합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        queue = await energy_service.get_energy_queue(status_filter, limit)
        
        logger.info(f"관리자 {current_admin.id}가 에너지 대기 큐 조회")
        return queue
        
    except Exception as e:
        logger.error(f"에너지 대기 큐 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="에너지 대기 큐 조회 중 오류가 발생했습니다."
        )


@router.post("/queue")
async def add_to_energy_queue(
    queue_data: EnergyQueueCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    에너지 대기 큐에 새 항목을 추가합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        queue_item = await energy_service.add_to_queue(queue_data, current_admin.id)
        
        logger.info(f"관리자 {current_admin.id}가 에너지 대기 큐에 항목 추가")
        return queue_item
        
    except Exception as e:
        logger.error(f"에너지 대기 큐 추가 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="에너지 대기 큐 추가 중 오류가 발생했습니다."
        )


@router.post("/alerts")
async def create_energy_alert(
    alert_data: CreateEnergyAlert,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    에너지 알림을 생성합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        alert = await energy_service.create_alert(alert_data, current_admin.id)
        
        logger.info(f"관리자 {current_admin.id}가 에너지 알림 생성")
        return alert
        
    except Exception as e:
        logger.error(f"에너지 알림 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="에너지 알림 생성 중 오류가 발생했습니다."
        )


@router.post("/emergency-withdrawal", response_model=EmergencyWithdrawalResponse)
async def create_emergency_withdrawal(
    withdrawal_data: EmergencyWithdrawalCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    긴급 출금을 생성합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        withdrawal = await energy_service.create_emergency_withdrawal(
            withdrawal_data, current_admin.id
        )
        
        logger.info(f"관리자 {current_admin.id}가 긴급 출금 생성: {withdrawal_data.amount} TRX")
        return withdrawal
        
    except Exception as e:
        logger.error(f"긴급 출금 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="긴급 출금 생성 중 오류가 발생했습니다."
        )


@router.get("/optimize")
async def optimize_energy_distribution(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    에너지 분배를 최적화합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        result = await energy_service.optimize_energy_distribution()
        
        logger.info(f"관리자 {current_admin.id}가 에너지 분배 최적화 실행")
        return result
        
    except Exception as e:
        logger.error(f"에너지 분배 최적화 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="에너지 분배 최적화 중 오류가 발생했습니다."
        )
