"""
입금 관련 API 엔드포인트.
입금 모니터링, 상태 조회 등의 기능을 제공합니다.
"""
import logging
from typing import Any, Dict

from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import UserResponse
from app.services.deposit_monitoring_service import deposit_monitor
from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/status", response_model=Dict[str, Any])
async def get_deposit_status(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    사용자의 입금 상태 조회

    Returns:
        Dict: 입금 내역 및 상태 정보
    """
    user_id = getattr(current_user, "id", 0)
    status_info = await deposit_monitor.get_deposit_status(db, user_id)
    return status_info


@router.post("/monitor/start")
async def start_monitoring(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_admin_user),
):
    """
    입금 모니터링 시작 (관리자 전용)

    Returns:
        Dict: 모니터링 시작 결과
    """
    if not deposit_monitor.is_monitoring:
        background_tasks.add_task(deposit_monitor.start_monitoring)
        logger.info(f"관리자 {current_user.email}가 입금 모니터링을 시작했습니다")
        return {"message": "입금 모니터링이 시작되었습니다", "status": "started"}
    else:
        return {"message": "입금 모니터링이 이미 실행 중입니다", "status": "already_running"}


@router.post("/monitor/stop")
async def stop_monitoring(current_user: User = Depends(deps.get_current_admin_user)):
    """
    입금 모니터링 중지 (관리자 전용)

    Returns:
        Dict: 모니터링 중지 결과
    """
    if deposit_monitor.is_monitoring:
        deposit_monitor.stop_monitoring()
        logger.info(f"관리자 {current_user.email}가 입금 모니터링을 중지했습니다")
        return {"message": "입금 모니터링이 중지되었습니다", "status": "stopped"}
    else:
        return {"message": "입금 모니터링이 실행되지 않고 있습니다", "status": "not_running"}


@router.get("/monitor/info")
async def get_monitoring_info(
    current_user: User = Depends(deps.get_current_admin_user),
):
    """
    입금 모니터링 상태 정보 조회 (관리자 전용)

    Returns:
        Dict: 모니터링 상태 정보
    """
    return {
        "is_monitoring": deposit_monitor.is_monitoring,
        "monitoring_interval": deposit_monitor.monitoring_interval,
        "last_checked_block": deposit_monitor.last_checked_block,
    }
