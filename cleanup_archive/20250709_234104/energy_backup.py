"""
TRON 에너지 풀 관리 API 엔드포인트
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_admin_user
from app.models.user import User
from app.services.energy.energy_pool_service import EnergyPoolService
from app.schemas.energy import (
    EnergyPoolStatus, EnergyRechargeRequest, EnergyUsageStats,
    EnergyQueueCreate, QueueStatus
)
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["에너지 풀 관리"])


@router.get("/status", response_model=EnergyPoolStatus)
async def get_energy_pool_status(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
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
            status_code=500,
            detail="에너지 풀 상태 조회 중 오류가 발생했습니다."
        )


@router.post("/recharge")
async def recharge_energy_pool(
    recharge_data: EnergyRechargeRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    에너지 풀을 충전합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        result = await energy_service.recharge_energy(recharge_data)
        
        logger.info(f"관리자 {current_admin.id}가 에너지 풀 충전: {recharge_data.amount}")
        return {"success": result, "message": "에너지 풀 충전이 완료되었습니다."}
        
    except Exception as e:
        logger.error(f"에너지 풀 충전 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="에너지 풀 충전 중 오류가 발생했습니다."
        )


@router.get("/usage-stats", response_model=EnergyUsageStats)
async def get_energy_usage_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    에너지 사용 통계를 조회합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        stats = await energy_service.get_usage_stats()
        
        logger.info(f"관리자 {current_admin.id}가 에너지 사용 통계 조회")
        return stats
        
    except Exception as e:
        logger.error(f"에너지 사용 통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="에너지 사용 통계 조회 중 오류가 발생했습니다."
        )


@router.post("/queue")
async def add_to_energy_queue(
    queue_data: EnergyQueueCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    에너지 대기 큐에 새 항목을 추가합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        # type: ignore을 사용하여 타입 체커 우회
        admin_id: int = current_admin.id  # type: ignore
        queue_id = await energy_service.add_to_queue(admin_id, queue_data)
        
        logger.info(f"관리자 {current_admin.id}가 에너지 대기 큐에 항목 추가")
        return {"queue_id": queue_id, "message": "대기 큐에 추가되었습니다."}
        
    except Exception as e:
        logger.error(f"에너지 대기 큐 추가 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="에너지 대기 큐 추가 중 오류가 발생했습니다."
        )


@router.get("/queue-status")
async def get_queue_status(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    에너지 대기 큐 상태를 조회합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        admin_id: int = current_admin.id  # type: ignore
        status = await energy_service.get_queue_status(admin_id)
        
        logger.info(f"관리자 {current_admin.id}가 에너지 대기 큐 상태 조회")
        return status
        
    except Exception as e:
        logger.error(f"에너지 대기 큐 상태 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="에너지 대기 큐 상태 조회 중 오류가 발생했습니다."
        )


@router.post("/process-queue")
async def process_energy_queue(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    에너지 대기 큐를 처리합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        processed_ids = await energy_service.process_queue()
        
        logger.info(f"관리자 {current_admin.id}가 에너지 대기 큐 처리: {len(processed_ids)}개 항목")
        return {
            "processed_count": len(processed_ids),
            "processed_ids": processed_ids,
            "message": "대기 큐 처리가 완료되었습니다."
        }
        
    except Exception as e:
        logger.error(f"에너지 대기 큐 처리 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="에너지 대기 큐 처리 중 오류가 발생했습니다."
        )


@router.get("/alerts")
async def get_active_alerts(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    활성 에너지 알림을 조회합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        alerts = await energy_service.get_active_alerts()
        
        logger.info(f"관리자 {current_admin.id}가 활성 에너지 알림 조회")
        return alerts
        
    except Exception as e:
        logger.error(f"활성 에너지 알림 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="활성 에너지 알림 조회 중 오류가 발생했습니다."
        )


@router.delete("/queue/{queue_id}")
async def cancel_queue_item(
    queue_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    에너지 대기 큐 항목을 취소합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        admin_id: int = current_admin.id  # type: ignore
        success = await energy_service.cancel_queue_item(queue_id, admin_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="대기 큐 항목을 찾을 수 없습니다."
            )
        
        logger.info(f"관리자 {current_admin.id}가 에너지 대기 큐 항목 {queue_id} 취소")
        return {"message": "대기 큐 항목이 취소되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"에너지 대기 큐 항목 취소 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="에너지 대기 큐 항목 취소 중 오류가 발생했습니다."
        )
