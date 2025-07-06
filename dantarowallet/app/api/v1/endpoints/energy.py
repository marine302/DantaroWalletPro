"""
사용자용 에너지 관련 API 엔드포인트
"""
from typing import Optional, List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.energy.energy_pool_service import EnergyPoolService
from app.schemas.energy import (
    EnergyPoolStatus, EnergyQueueCreate, EnergyQueue, QueueStatus,
    EnergyUsageStats, EmergencyWithdrawalCreate, EmergencyWithdrawalResponse,
    EnergyAlert
)
from app.core.exceptions import EnergyInsufficientError
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["에너지 상태"])


@router.get("/status", response_model=EnergyPoolStatus)
async def get_energy_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    현재 에너지 풀 상태를 확인합니다.
    사용자가 출금 시 에너지 부족 여부를 알 수 있습니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        status = await energy_service.get_energy_status()
        
        logger.info(f"사용자 {current_user.id}가 에너지 상태 조회")
        return status
        
    except Exception as e:
        logger.error(f"에너지 상태 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="에너지 상태 조회 중 오류가 발생했습니다."
        )


@router.post("/emergency-withdrawal", response_model=EmergencyWithdrawalResponse)
async def create_emergency_withdrawal(
    withdrawal_data: EmergencyWithdrawalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    에너지 부족 시 높은 수수료로 즉시 출금을 처리합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        
        # 에너지 상태 확인
        energy_status = await energy_service.get_energy_status()
        
        if energy_status.energy_sufficient:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="현재 에너지가 충분합니다. 일반 출금을 이용해주세요."
            )
        
        # 긴급 출금 처리
        response = await energy_service.process_emergency_withdrawal(
            user_id=current_user.id,
            withdrawal_data=withdrawal_data
        )
        
        logger.info(f"사용자 {current_user.id}의 긴급 출금 처리: {withdrawal_data.amount}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"긴급 출금 처리 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="긴급 출금 처리 중 오류가 발생했습니다."
        )


@router.post("/queue", response_model=EnergyQueue)
async def add_to_energy_queue(
    queue_data: EnergyQueueCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    에너지 부족 시 거래를 대기열에 추가합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        
        # 대기열에 추가
        queue_item = await energy_service.add_to_queue(
            user_id=current_user.id,
            queue_data=queue_data
        )
        
        logger.info(f"사용자 {current_user.id}가 에너지 대기열에 추가: {queue_data.transaction_type}")
        return queue_item
        
    except Exception as e:
        logger.error(f"에너지 대기열 추가 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대기열 추가 중 오류가 발생했습니다."
        )


@router.get("/queue/{queue_id}/status", response_model=QueueStatus)
async def get_queue_status(
    queue_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    대기열 상태를 조회합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        
        # 대기열 상태 조회
        queue_status = await energy_service.get_queue_status(
            queue_id=queue_id,
            user_id=current_user.id
        )
        
        if not queue_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="대기열 항목을 찾을 수 없습니다."
            )
        
        return queue_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"대기열 상태 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대기열 상태 조회 중 오류가 발생했습니다."
        )


@router.get("/usage-stats", response_model=EnergyUsageStats)
async def get_energy_usage_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    에너지 사용 통계를 조회합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        
        # 사용 통계 조회
        stats = await energy_service.get_usage_stats()
        
        logger.info(f"사용자 {current_user.id}가 에너지 사용 통계 조회")
        return stats
        
    except Exception as e:
        logger.error(f"에너지 사용 통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="에너지 사용 통계 조회 중 오류가 발생했습니다."
        )


@router.get("/alerts", response_model=List[EnergyAlert])
async def get_energy_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    활성 에너지 알림을 조회합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        
        # 활성 알림 조회
        alerts = await energy_service.get_active_alerts()
        
        logger.info(f"사용자 {current_user.id}가 에너지 알림 조회")
        return alerts
        
    except Exception as e:
        logger.error(f"에너지 알림 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="에너지 알림 조회 중 오류가 발생했습니다."
        )


@router.delete("/queue/{queue_id}")
async def cancel_queue_item(
    queue_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    대기열 항목을 취소합니다.
    """
    try:
        energy_service = EnergyPoolService(db)
        
        # 대기열 항목 취소
        success = await energy_service.cancel_queue_item(
            queue_id=queue_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="취소할 대기열 항목을 찾을 수 없습니다."
            )
        
        logger.info(f"사용자 {current_user.id}가 대기열 항목 {queue_id} 취소")
        return {"message": "대기열 항목이 취소되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"대기열 항목 취소 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대기열 항목 취소 중 오류가 발생했습니다."
        )
