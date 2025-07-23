"""
슈퍼 어드민용 시스템 모니터링 API
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_super_admin
from app.core.database import get_db
from app.schemas.monitoring import (
    Alert,
    PartnerRanking,
    PerformanceReport,
    SystemHealth,
    SystemMetrics,
)
from app.services.monitoring.system_monitor_service import SystemMonitorService

router = APIRouter(prefix="/admin/monitoring", tags=["Super Admin Monitoring"])


@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics(
    db: Session = Depends(get_db), current_admin=Depends(get_current_super_admin)
):
    """시스템 메트릭 조회"""
    monitor_service = SystemMonitorService(db)
    return await monitor_service.collect_system_metrics()


@router.get("/health", response_model=SystemHealth)
async def get_system_health(
    db: Session = Depends(get_db), current_admin=Depends(get_current_super_admin)
):
    """시스템 헬스 상태 조회"""
    try:
        monitor_service = SystemMonitorService(db)

        # 시스템 메트릭 수집
        metrics = await monitor_service.collect_system_metrics()

        # 컴포넌트별 상태 확인
        components = {}

        # 데이터베이스 상태
        try:
            db.execute("SELECT 1")
            components["database"] = "healthy"
        except:
            components["database"] = "unhealthy"

        # API 상태
        if metrics.api_error_rate < 5:
            components["api"] = "healthy"
        elif metrics.api_error_rate < 15:
            components["api"] = "warning"
        else:
            components["api"] = "critical"

        # 전체 헬스 점수 계산
        health_score = 100
        issues = []

        if components["database"] == "unhealthy":
            health_score -= 40
            issues.append("Database connection issues")

        if components["api"] == "critical":
            health_score -= 25
            issues.append("High API error rate")
        elif components["api"] == "warning":
            health_score -= 10
            issues.append("Elevated API error rate")

        # 상태 판정
        if health_score >= 90:
            status = "healthy"
        elif health_score >= 70:
            status = "warning"
        else:
            status = "critical"

        return SystemHealth(
            status=status,
            health_score=max(0, health_score),
            components=components,
            issues=issues,
            last_check=metrics.timestamp,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get system health: {str(e)}"
        )


@router.get("/alerts", response_model=List[Alert])
async def get_system_alerts(
    severity: Optional[str] = Query(None, description="알림 심각도"),
    limit: int = Query(50, description="조회 개수"),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_super_admin),
):
    """시스템 알림 조회"""
    monitor_service = SystemMonitorService(db)
    alerts = await monitor_service.get_system_alerts(severity=severity)
    return alerts[:limit]


@router.get("/partners/rankings", response_model=List[PartnerRanking])
async def get_partner_rankings(
    metric: str = Query("performance", description="순위 기준"),
    limit: int = Query(10, description="결과 개수"),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_super_admin),
):
    """파트너 순위 조회"""
    monitor_service = SystemMonitorService(db)
    rankings = await monitor_service.get_partner_rankings(metric=metric)
    return rankings[:limit]


@router.get("/partners/{partner_id}/health")
async def get_partner_health(
    partner_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_super_admin),
):
    """파트너 헬스 체크"""
    monitor_service = SystemMonitorService(db)
    return await monitor_service.check_partner_health(partner_id)


@router.post("/reports/performance", response_model=PerformanceReport)
async def generate_performance_report(
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_super_admin),
):
    """성능 보고서 생성"""
    monitor_service = SystemMonitorService(db)
    return await monitor_service.generate_performance_report(start_date, end_date)


@router.get("/analytics/api-usage")
async def get_api_usage_analytics(
    days: int = Query(7, description="분석 기간 (일)"),
    partner_id: Optional[str] = Query(None, description="특정 파트너"),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_super_admin),
):
    """API 사용량 분석"""
    try:
        # 실제 구현에서는 API 로그 테이블에서 상세 분석
        analytics = {
            "analysis_period": days,
            "partner_id": partner_id,
            "total_api_calls": 15234,
            "successful_calls": 14876,
            "failed_calls": 358,
            "success_rate": 97.65,
            "average_response_time": 245.6,
            "peak_usage_hours": [9, 10, 11, 14, 15, 16],
            "endpoint_popularity": [
                {"endpoint": "/api/v1/wallets", "calls": 5432, "success_rate": 98.2},
                {
                    "endpoint": "/api/v1/transactions",
                    "calls": 4321,
                    "success_rate": 97.8,
                },
                {"endpoint": "/api/v1/balance", "calls": 3210, "success_rate": 99.1},
            ],
            "error_analysis": {
                "most_common_errors": [
                    {"code": 400, "count": 156, "description": "Bad Request"},
                    {"code": 429, "count": 98, "description": "Rate Limit Exceeded"},
                    {"code": 500, "count": 67, "description": "Internal Server Error"},
                ]
            },
            "geographic_distribution": {
                "KR": 65.2,
                "US": 15.8,
                "JP": 12.3,
                "others": 6.7,
            },
        }

        return analytics

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get API usage analytics: {str(e)}"
        )


@router.get("/analytics/uptime")
async def get_uptime_analytics(
    days: int = Query(30, description="분석 기간 (일)"),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_super_admin),
):
    """시스템 가동률 분석"""
    try:
        uptime_data = {
            "analysis_period": days,
            "overall_uptime": 99.94,
            "target_uptime": 99.9,
            "downtime_incidents": [
                {
                    "date": "2024-01-15",
                    "duration_minutes": 12,
                    "reason": "Database maintenance",
                    "impact": "low",
                },
                {
                    "date": "2024-01-08",
                    "duration_minutes": 5,
                    "reason": "API rate limiting",
                    "impact": "medium",
                },
            ],
            "daily_uptime": [],  # 일별 가동률 데이터
            "service_level_compliance": {
                "sla_target": 99.9,
                "actual": 99.94,
                "status": "compliant",
            },
            "recommendations": [
                "Continue current maintenance schedule",
                "Consider redundant database setup",
                "Implement graceful degradation for rate limiting",
            ],
        }

        return uptime_data

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get uptime analytics: {str(e)}"
        )


@router.post("/alerts/send")
async def send_custom_alert(
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    partner_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_super_admin),
):
    """커스텀 알림 전송"""
    try:
        monitor_service = SystemMonitorService(db)

        alert = Alert(
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            partner_id=partner_id,
            created_at=datetime.utcnow(),
        )

        success = await monitor_service.send_alert_notifications(alert)

        if success:
            return {
                "message": "Alert sent successfully",
                "alert_type": alert_type,
                "severity": severity,
                "sent_by": current_admin.get("id"),
                "sent_at": "now",
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to send alert")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send alert: {str(e)}")


@router.get("/logs/system")
async def get_system_logs(
    level: Optional[str] = Query(None, description="로그 레벨"),
    limit: int = Query(100, description="조회 개수"),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_super_admin),
):
    """시스템 로그 조회"""
    try:
        # 실제 구현에서는 로그 파일 또는 로그 테이블에서 조회
        logs = [
            {
                "timestamp": "2024-01-01T10:00:00Z",
                "level": "INFO",
                "component": "API",
                "message": "System started successfully",
                "details": {},
            },
            {
                "timestamp": "2024-01-01T10:01:00Z",
                "level": "WARNING",
                "component": "Energy",
                "message": "Energy pool below alert threshold",
                "details": {"current_energy": 95000, "threshold": 100000},
            },
        ]

        # 레벨 필터 적용
        if level:
            logs = [log for log in logs if log["level"] == level.upper()]

        return {
            "logs": logs[:limit],
            "total_count": len(logs),
            "filters": {"level": level},
            "retrieved_at": "now",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get system logs: {str(e)}"
        )
