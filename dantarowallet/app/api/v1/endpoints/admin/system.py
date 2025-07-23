"""
슈퍼 어드민용 시스템 관리 API
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user
from app.core.database import get_sync_db
from app.core.logger import get_logger
from app.models.user import User
from app.services.system.system_monitor_service import SystemMonitorService

logger = get_logger(__name__)
router = APIRouter(tags=["시스템 관리"])


@router.get("/health")
async def get_system_health(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """시스템 전반적인 헬스 상태 조회"""
    try:
        monitor_service = SystemMonitorService(db)
        health = await monitor_service.check_system_health()

        logger.info(f"관리자 {str(current_admin.id)}가 시스템 헬스 상태 조회")
        return health

    except Exception as e:
        logger.error(f"시스템 헬스 상태 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail="시스템 헬스 상태 조회 중 오류가 발생했습니다."
        )


@router.get("/metrics")
async def get_system_metrics(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """시스템 메트릭 조회"""
    try:
        monitor_service = SystemMonitorService(db)
        metrics = await monitor_service.collect_system_metrics()

        logger.info(f"관리자 {str(current_admin.id)}가 시스템 메트릭 조회")
        return metrics

    except Exception as e:
        logger.error(f"시스템 메트릭 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail="시스템 메트릭 조회 중 오류가 발생했습니다."
        )


@router.get("/alerts")
async def get_system_alerts(
    severity: Optional[str] = None,
    limit: int = 50,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """시스템 알림 조회"""
    try:
        monitor_service = SystemMonitorService(db)
        alerts = monitor_service.get_system_alerts(severity=severity)

        logger.info(
            f"관리자 {str(current_admin.id)}가 시스템 알림 조회 (심각도: {severity})"
        )
        return alerts

    except Exception as e:
        logger.error(f"시스템 알림 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail="시스템 알림 조회 중 오류가 발생했습니다."
        )


@router.post("/maintenance")
async def enable_maintenance_mode(
    message: str = "시스템 점검 중입니다.",
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """시스템 점검 모드 활성화"""
    try:
        monitor_service = SystemMonitorService(db)
        success = monitor_service.enable_maintenance_mode(
            message, str(str(current_admin.id))
        )

        if success:
            logger.info(f"관리자 {str(current_admin.id)}가 시스템 점검 모드 활성화")
            return {
                "message": "점검 모드가 활성화되었습니다.",
                "enabled_by": str(current_admin.id),
            }
        else:
            raise HTTPException(status_code=400, detail="점검 모드 활성화 실패")

    except Exception as e:
        logger.error(f"점검 모드 활성화 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail="점검 모드 활성화 중 오류가 발생했습니다."
        )


@router.delete("/maintenance")
async def disable_maintenance_mode(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """시스템 점검 모드 비활성화"""
    try:
        monitor_service = SystemMonitorService(db)
        success = await monitor_service.disable_maintenance_mode(str(current_admin.id))

        if success:
            logger.info(f"관리자 {str(current_admin.id)}가 시스템 점검 모드 비활성화")
            return {
                "message": "점검 모드가 비활성화되었습니다.",
                "disabled_by": str(current_admin.id),
            }
        else:
            raise HTTPException(status_code=400, detail="점검 모드 비활성화 실패")

    except Exception as e:
        logger.error(f"점검 모드 비활성화 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail="점검 모드 비활성화 중 오류가 발생했습니다."
        )


@router.get("/logs")
async def get_system_logs(
    level: Optional[str] = None,
    limit: int = 100,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """시스템 로그 조회"""
    try:
        monitor_service = SystemMonitorService(db)
        logs = await monitor_service.get_system_logs(level=level, limit=limit)

        logger.info(
            f"관리자 {str(current_admin.id)}가 시스템 로그 조회 (레벨: {level})"
        )
        return logs

    except Exception as e:
        logger.error(f"시스템 로그 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail="시스템 로그 조회 중 오류가 발생했습니다."
        )


@router.post("/backup")
async def create_system_backup(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """시스템 백업 생성"""
    try:
        monitor_service = SystemMonitorService(db)
        backup_result = await monitor_service.create_system_backup(
            str(current_admin.id)
        )

        logger.info(f"관리자 {str(current_admin.id)}가 시스템 백업 생성")
        return backup_result

    except Exception as e:
        logger.error(f"시스템 백업 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail="시스템 백업 생성 중 오류가 발생했습니다."
        )


@router.get("/performance")
async def get_performance_report(
    days: int = 7,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """시스템 성능 리포트 조회"""
    try:
        monitor_service = SystemMonitorService(db)
        report = await monitor_service.generate_performance_report(days=days)

        logger.info(
            f"관리자 {str(current_admin.id)}가 시스템 성능 리포트 조회 ({days}일)"
        )
        return report

    except Exception as e:
        logger.error(f"성능 리포트 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail="성능 리포트 조회 중 오류가 발생했습니다."
        )
