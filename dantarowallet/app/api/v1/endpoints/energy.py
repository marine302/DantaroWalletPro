"""
Doc #25: 에너지 풀 고급 관리 API 엔드포인트
실시간 모니터링, 예측 분석, 알림 시스템
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_partner, get_db
from app.models.energy_pool import EnergyAlert, PartnerEnergyPool
from app.models.partner import Partner
from app.schemas.energy import (
    EnergyAlertListResponse,
    EnergyAnalyticsResponse,
    EnergyDashboardResponse,
    EnergyMonitoringResponse,
    EnergyPatternAnalysisResponse,
    EnergyPoolResponse,
    GlobalEnergyAnalyticsResponse,
    MessageResponse,
)

# EnergyPredictionService를 직접 임포트
from app.services.energy_monitoring_service import (
    EnergyMonitoringService,
    EnergyPredictionService,
)

router = APIRouter()


@router.get("/monitor/{partner_id}", response_model=EnergyMonitoringResponse)
async def monitor_partner_energy(
    partner_id: int,
    db: AsyncSession = Depends(get_db),
    current_partner: Partner = Depends(get_current_partner),
):
    """파트너 에너지 실시간 모니터링 (Doc #25)"""
    # 권한 확인 (자신의 데이터만 조회 가능)
    if str(current_partner.id) != str(partner_id):
        raise HTTPException(
            status_code=403, detail="자신의 에너지 상태만 조회할 수 있습니다"
        )

    try:
        monitoring_service = EnergyMonitoringService(db)
        monitoring_data = await monitoring_service.monitor_partner_energy(partner_id)

        return EnergyMonitoringResponse(
            success=True, data=monitoring_data, timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"에너지 모니터링 실패: {str(e)}")


@router.get("/analytics/{partner_id}", response_model=EnergyAnalyticsResponse)
async def get_energy_analytics(
    partner_id: int,
    days: int = Query(default=30, ge=1, le=90, description="분석 기간 (일)"),
    db: AsyncSession = Depends(get_db),
    current_partner: Partner = Depends(get_current_partner),
):
    """파트너 에너지 사용 분석 (Doc #25)"""
    if str(current_partner.id) != str(partner_id):
        raise HTTPException(
            status_code=403, detail="자신의 에너지 분석만 조회할 수 있습니다"
        )

    try:
        monitoring_service = EnergyMonitoringService(db)
        analytics_data = await monitoring_service.get_energy_analytics(partner_id, days)

        return EnergyAnalyticsResponse(
            success=True, analytics=analytics_data, generated_at=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"에너지 분석 실패: {str(e)}")


@router.get("/alerts/{partner_id}", response_model=EnergyAlertListResponse)
async def get_energy_alerts(
    partner_id: int,
    hours: int = Query(default=24, ge=1, le=168, description="조회 기간 (시간)"),
    db: AsyncSession = Depends(get_db),
    current_partner: Partner = Depends(get_current_partner),
):
    """파트너 에너지 알림 조회 (Doc #25)"""
    if str(current_partner.id) != str(partner_id):
        raise HTTPException(status_code=403, detail="자신의 알림만 조회할 수 있습니다")

    try:
        monitoring_service = EnergyMonitoringService(db)

        # 에너지 풀 조회
        result = await db.execute(
            select(PartnerEnergyPool).where(PartnerEnergyPool.partner_id == partner_id)
        )
        energy_pool = result.scalar_one_or_none()

        if not energy_pool:
            return EnergyAlertListResponse(success=True, alerts=[], total_count=0)

        # 최근 알림 조회
        # alerts = await monitoring_service._get_recent_alerts(getattr(energy_pool, 'id'), hours)
        alerts = []  # 임시 처리

        alert_data = [
            {
                "id": alert.id,
                "type": alert.alert_type,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "threshold_value": float(alert.threshold_value or 0),
                "current_value": float(alert.current_value or 0),
                "estimated_hours_remaining": alert.estimated_hours_remaining,
                "acknowledged": bool(alert.acknowledged),
                "created_at": alert.created_at,
            }
            for alert in alerts
        ]

        return EnergyAlertListResponse(
            success=True, alerts=alert_data, total_count=len(alerts)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 조회 실패: {str(e)}")


@router.get("/global/analytics", response_model=GlobalEnergyAnalyticsResponse)
async def get_global_energy_analytics(
    days: int = Query(default=30, ge=1, le=90, description="분석 기간 (일)"),
    db: AsyncSession = Depends(get_db),
    current_partner: Partner = Depends(get_current_partner),
):
    """전체 에너지 사용 분석 (관리자용)"""
    # 관리자 권한 체크 (실제로는 슈퍼 어드민 권한 확인)
    try:
        monitoring_service = EnergyMonitoringService(db)
        analytics_data = await monitoring_service.get_energy_analytics(
            partner_id=1, days=days
        )  # 임시 처리

        return GlobalEnergyAnalyticsResponse(
            success=True,
            global_analytics=analytics_data,
            generated_at=datetime.utcnow(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"전체 에너지 분석 실패: {str(e)}")


@router.post("/update/{partner_id}", response_model=EnergyMonitoringResponse)
async def update_energy_status(
    partner_id: int,
    wallet_address: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_partner: Partner = Depends(get_current_partner),
):
    """파트너의 에너지 상태 실시간 업데이트"""
    # 권한 확인
    if str(current_partner.id) != str(partner_id):
        raise HTTPException(
            status_code=403, detail="자신의 에너지 상태만 업데이트할 수 있습니다"
        )

    monitoring_service = EnergyMonitoringService(db)

    # 모니터링 데이터 조회
    try:
        monitoring_data = await monitoring_service.monitor_partner_energy(partner_id)

        return EnergyMonitoringResponse(
            success=True, data=monitoring_data, timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"에너지 상태 업데이트 실패: {str(e)}"
        )


@router.get("/dashboard/{partner_id}", response_model=EnergyDashboardResponse)
async def get_energy_dashboard(
    partner_id: int,
    db: AsyncSession = Depends(get_db),
    current_partner: Partner = Depends(get_current_partner),
):
    """에너지 풀 대시보드 데이터 조회"""
    # 권한 확인
    if str(current_partner.id) != str(partner_id):
        raise HTTPException(
            status_code=403, detail="자신의 대시보드만 조회할 수 있습니다"
        )

    monitoring_service = EnergyMonitoringService(db)
    # dashboard_data = await monitoring_service.get_energy_dashboard_data(partner_id)
    dashboard_data = {}  # 임시 처리

    if not dashboard_data["success"]:
        raise HTTPException(
            status_code=400,
            detail=dashboard_data.get("error", "대시보드 데이터 조회 실패"),
        )

    return EnergyDashboardResponse(**dashboard_data)


@router.get("/patterns/{partner_id}", response_model=EnergyPatternAnalysisResponse)
async def analyze_usage_patterns(
    partner_id: int,
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_partner: Partner = Depends(get_current_partner),
):
    """에너지 사용 패턴 분석"""
    # 권한 확인
    if str(current_partner.id) != str(partner_id):
        raise HTTPException(
            status_code=403, detail="자신의 사용 패턴만 분석할 수 있습니다"
        )

    if days < 1 or days > 30:
        raise HTTPException(
            status_code=400, detail="분석 기간은 1-30일 사이여야 합니다"
        )

    prediction_service = EnergyPredictionService(db)
    # analysis_result = await prediction_service.analyze_usage_patterns(partner_id, days)
    analysis_result = {}  # 임시 처리

    if not analysis_result["success"]:
        raise HTTPException(
            status_code=400, detail=analysis_result.get("error", "패턴 분석 실패")
        )

    return EnergyPatternAnalysisResponse(**analysis_result)


@router.post("/alerts/{partner_id}/acknowledge/{alert_id}")
async def acknowledge_alert(
    partner_id: int,
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_partner: Partner = Depends(get_current_partner),
):
    """에너지 알림 확인 처리"""
    # 권한 확인
    if str(current_partner.id) != str(partner_id):
        raise HTTPException(status_code=403, detail="자신의 알림만 확인할 수 있습니다")

    from sqlalchemy import and_, select

    from app.models.energy_pool import EnergyAlert, PartnerEnergyPool

    # 알림 조회 및 권한 확인
    result = await db.execute(
        select(EnergyAlert)
        .join(PartnerEnergyPool)
        .where(
            and_(EnergyAlert.id == alert_id, PartnerEnergyPool.partner_id == partner_id)
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다")

    if getattr(alert, "acknowledged", False):
        raise HTTPException(status_code=400, detail="이미 확인된 알림입니다")

    # 알림 확인 처리 - SQLAlchemy update 사용
    from sqlalchemy import update

    await db.execute(
        update(EnergyAlert)
        .where(EnergyAlert.id == alert_id)
        .values(acknowledged=True, acknowledged_at=datetime.utcnow())
    )

    await db.commit()

    return {"success": True, "message": "알림이 확인되었습니다"}


# 중복된 알림 엔드포인트 제거됨 - 위에서 이미 정의됨


@router.get("/usage-logs/{partner_id}")
async def get_usage_logs(
    partner_id: int,
    limit: int = 50,
    hours: int = 24,
    db: AsyncSession = Depends(get_db),
    current_partner: Partner = Depends(get_current_partner),
):
    """파트너의 에너지 사용 로그 조회"""
    # 권한 확인
    if str(current_partner.id) != str(partner_id):
        raise HTTPException(
            status_code=403, detail="자신의 사용 로그만 조회할 수 있습니다"
        )

    from datetime import timedelta

    from sqlalchemy import and_, desc, select

    from app.models.energy_pool import PartnerEnergyPool, PartnerEnergyUsageLog

    # 시간 제한
    since = datetime.utcnow() - timedelta(hours=hours)

    result = await db.execute(
        select(PartnerEnergyUsageLog)
        .join(PartnerEnergyPool)
        .where(
            and_(
                PartnerEnergyPool.partner_id == partner_id,
                PartnerEnergyUsageLog.created_at >= since,
            )
        )
        .order_by(desc(PartnerEnergyUsageLog.created_at))
        .limit(limit)
    )
    usage_logs = result.scalars().all()

    return {
        "success": True,
        "usage_logs": [
            {
                "id": log.id,
                "transaction_type": log.transaction_type,
                "transaction_hash": log.transaction_hash,
                "energy_consumed": int(getattr(log, "energy_consumed", 0) or 0),
                "bandwidth_consumed": int(getattr(log, "bandwidth_consumed", 0) or 0),
                "energy_unit_price": (
                    float(getattr(log, "energy_unit_price", 0) or 0)
                    if getattr(log, "energy_unit_price", None) is not None
                    else None
                ),
                "total_cost": (
                    float(getattr(log, "total_cost", 0) or 0)
                    if getattr(log, "total_cost", None) is not None
                    else None
                ),
                "created_at": log.created_at,
            }
            for log in usage_logs
        ],
        "total_count": len(usage_logs),
        "period_hours": hours,
    }


# 슈퍼 어드민 전용 엔드포인트
@router.get("/admin/monitor-all", dependencies=[Depends(get_current_partner)])
async def admin_monitor_all_partners(
    background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    """모든 파트너의 에너지 상태 모니터링 (슈퍼 어드민 전용)"""
    # TODO: 슈퍼 어드민 권한 확인 로직 추가

    monitoring_service = EnergyMonitoringService(db)

    # 백그라운드에서 모니터링 실행
    background_tasks.add_task(monitoring_service.monitor_all_partners)

    result = await monitoring_service.monitor_all_partners()

    return {
        "success": True,
        "message": "전체 파트너 모니터링이 시작되었습니다",
        "result": result,
    }


@router.get("/admin/overview")
async def admin_energy_overview(db: AsyncSession = Depends(get_db)):
    """전체 에너지 풀 현황 개요 (슈퍼 어드민 전용)"""
    # TODO: 슈퍼 어드민 권한 확인 로직 추가

    from sqlalchemy import func, select

    from app.models.energy_pool import EnergyStatus, PartnerEnergyPool

    # 전체 통계 조회
    result = await db.execute(
        select(
            func.count(PartnerEnergyPool.id).label("total_pools"),
            func.count(PartnerEnergyPool.id)
            .filter(PartnerEnergyPool.status == "sufficient")
            .label("sufficient"),
            func.count(PartnerEnergyPool.id)
            .filter(PartnerEnergyPool.status == "warning")
            .label("warning"),
            func.count(PartnerEnergyPool.id)
            .filter(PartnerEnergyPool.status == "critical")
            .label("critical"),
            func.count(PartnerEnergyPool.id)
            .filter(PartnerEnergyPool.status == "depleted")
            .label("depleted"),
            func.sum(PartnerEnergyPool.total_energy).label("total_energy_sum"),
            func.sum(PartnerEnergyPool.available_energy).label("available_energy_sum"),
            func.sum(PartnerEnergyPool.frozen_trx_amount).label("frozen_trx_sum"),
        )
    )
    stats = result.first()

    return {
        "success": True,
        "overview": {
            "total_partners": getattr(stats, "total_pools", 0) or 0,
            "status_distribution": {
                "sufficient": getattr(stats, "sufficient", 0) or 0,
                "warning": getattr(stats, "warning", 0) or 0,
                "critical": getattr(stats, "critical", 0) or 0,
                "depleted": getattr(stats, "depleted", 0) or 0,
            },
            "energy_totals": {
                "total_energy": int(getattr(stats, "total_energy_sum", 0) or 0),
                "available_energy": int(getattr(stats, "available_energy_sum", 0) or 0),
                "utilization_rate": round(
                    (
                        (
                            1
                            - (
                                getattr(stats, "available_energy_sum", 0)
                                / getattr(stats, "total_energy_sum", 1)
                            )
                        )
                        * 100
                        if getattr(stats, "total_energy_sum", 0)
                        and getattr(stats, "total_energy_sum", 0) > 0
                        else 0
                    ),
                    2,
                ),
            },
            "frozen_trx_total": float(getattr(stats, "frozen_trx_sum", 0) or 0),
        },
    }
