"""
슈퍼 어드민 통합 대시보드 API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_super_admin
from app.services.energy.super_admin_energy_service import SuperAdminEnergyService
from app.services.fee.super_admin_fee_service import SuperAdminFeeService
from app.services.monitoring.system_monitor_service import SystemMonitorService
from app.services.partner.partner_service import PartnerService
from app.schemas.energy import EnergyPoolStatus
from app.schemas.fee import TotalRevenueStats
from app.schemas.monitoring import SystemHealth, PartnerRanking, SystemMetrics
from app.schemas.partner import PartnerResponse

router = APIRouter(prefix="/admin/dashboard", tags=["Super Admin Dashboard"])


@router.get("/overview")
async def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """대시보드 개요 조회"""
    try:
        # 서비스 초기화
        energy_service = SuperAdminEnergyService(db)
        fee_service = SuperAdminFeeService(db)
        monitor_service = SystemMonitorService(db)
        partner_service = PartnerService(db)
        
        # 기본 통계 수집
        energy_status = await energy_service.get_total_energy_status()
        revenue_stats = await fee_service.get_total_revenue_stats()
        system_metrics = await monitor_service.collect_system_metrics()
        
        # 파트너 요약
        active_partners = await partner_service.get_all_partners(
            status="active", limit=5
        )
        
        # 알림 개수
        alerts = await monitor_service.get_system_alerts()
        critical_alerts = len([a for a in alerts if a.severity == "critical"])
        warning_alerts = len([a for a in alerts if a.severity == "warning"])
        
        return {
            "energy": {
                "total_energy": energy_status.total_energy,
                "available_energy": energy_status.available_energy,
                "utilization_rate": (
                    (energy_status.total_energy - energy_status.available_energy) / 
                    energy_status.total_energy * 100
                ) if energy_status.total_energy > 0 else 0,
                "is_sufficient": energy_status.is_sufficient
            },
            "revenue": {
                "total_revenue": revenue_stats.get("total_revenue", 0),
                "daily_revenue": revenue_stats.get("daily_revenue", 0),
                "monthly_revenue": revenue_stats.get("monthly_revenue", 0),
                "growth_rate": revenue_stats.get("growth_rate", 0)
            },
            "partners": {
                "total_partners": system_metrics.total_partners,
                "active_partners": system_metrics.active_partners,
                "pending_partners": system_metrics.pending_partners,
                "suspended_partners": system_metrics.suspended_partners
            },
            "system": {
                "api_calls_today": system_metrics.total_api_calls,
                "success_rate": (
                    (system_metrics.successful_api_calls / system_metrics.total_api_calls * 100)
                    if system_metrics.total_api_calls > 0 else 100
                ),
                "avg_response_time": system_metrics.avg_response_time,
                "uptime": 99.9  # 실제 계산 필요
            },
            "alerts": {
                "critical": critical_alerts,
                "warning": warning_alerts,
                "total": len(alerts)
            },
            "recent_partners": [
                {
                    "id": p.id,
                    "name": p.name,
                    "status": p.status,
                    "created_at": p.created_at
                } for p in active_partners[:5]
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard overview: {str(e)}")


@router.get("/energy-status", response_model=EnergyPoolStatus)
async def get_energy_status(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """에너지 풀 상태 조회"""
    energy_service = SuperAdminEnergyService(db)
    return await energy_service.get_total_energy_status()


@router.get("/revenue-stats", response_model=TotalRevenueStats)
async def get_revenue_stats(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """매출 통계 조회"""
    fee_service = SuperAdminFeeService(db)
    return await fee_service.get_total_revenue_stats()


@router.get("/system-health", response_model=SystemHealth)
async def get_system_health(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """시스템 헬스 상태 조회"""
    try:
        monitor_service = SystemMonitorService(db)
        energy_service = SuperAdminEnergyService(db)
        
        # 시스템 메트릭 수집
        metrics = await monitor_service.collect_system_metrics()
        
        # 컴포넌트별 상태 확인
        components = {}
        
        # 데이터베이스 상태
        try:
            from sqlalchemy.sql import text
            result = db.execute(text("SELECT 1"))  # AsyncSession이므로 await 불필요
            components["database"] = "healthy"
        except:
            components["database"] = "unhealthy"
        
        # 에너지 풀 상태
        energy_status = await energy_service.get_total_energy_status()
        if energy_status.is_sufficient:
            components["energy_pool"] = "healthy"
        elif energy_status.available_energy > energy_status.critical_threshold:
            components["energy_pool"] = "warning"
        else:
            components["energy_pool"] = "critical"
        
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
        
        if components["energy_pool"] == "critical":
            health_score -= 30
            issues.append("Critical energy level")
        elif components["energy_pool"] == "warning":
            health_score -= 15
            issues.append("Low energy level")
        
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
            last_check=metrics.timestamp
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")


@router.get("/partner-rankings", response_model=List[PartnerRanking])
async def get_partner_rankings(
    metric: str = Query("performance", description="순위 기준 (performance, volume, revenue)"),
    limit: int = Query(10, description="결과 개수"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """파트너 순위 조회"""
    monitor_service = SystemMonitorService(db)
    rankings = await monitor_service.get_partner_rankings(metric=metric)
    return rankings[:limit]


@router.get("/system-metrics", response_model=SystemMetrics)
async def get_system_metrics(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """시스템 메트릭 조회"""
    monitor_service = SystemMonitorService(db)
    return await monitor_service.collect_system_metrics()


@router.get("/activity-feed")
async def get_activity_feed(
    limit: int = Query(20, description="활동 개수"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """최근 활동 피드 조회"""
    try:
        # 실제 구현에서는 activity_log 테이블에서 조회
        # 현재는 샘플 데이터 반환
        activities = [
            {
                "id": f"activity_{i}",
                "type": "partner_created" if i % 3 == 0 else "energy_allocated" if i % 3 == 1 else "fee_updated",
                "title": f"Activity {i}",
                "description": f"Sample activity description {i}",
                "partner_id": f"partner_{i}" if i % 2 == 0 else None,
                "partner_name": f"Partner {i}" if i % 2 == 0 else None,
                "timestamp": "2024-01-01T10:00:00Z",
                "severity": "info"
            }
            for i in range(limit)
        ]
        
        return {
            "activities": activities,
            "total_count": limit,
            "has_more": False
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get activity feed: {str(e)}")


@router.get("/quick-stats")
async def get_quick_stats(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """빠른 통계 조회"""
    try:
        energy_service = SuperAdminEnergyService(db)
        fee_service = SuperAdminFeeService(db)
        monitor_service = SystemMonitorService(db)
        
        # 에너지 통계
        energy_stats = await energy_service.get_energy_statistics()
        
        # 시스템 메트릭
        system_metrics = await monitor_service.collect_system_metrics()
        
        # 알림 개수
        alerts = await monitor_service.get_system_alerts()
        
        return {
            "energy_utilization": (
                (energy_stats["total_energy"] - energy_stats["available_energy"]) / 
                energy_stats["total_energy"] * 100
            ) if energy_stats["total_energy"] > 0 else 0,
            "active_partners": energy_stats["active_partners"],
            "api_success_rate": (
                (system_metrics.successful_api_calls / system_metrics.total_api_calls * 100)
                if system_metrics.total_api_calls > 0 else 100
            ),
            "pending_alerts": len([a for a in alerts if a.severity in ["warning", "critical"]]),
            "avg_response_time": system_metrics.avg_response_time,
            "total_api_calls": system_metrics.total_api_calls
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get quick stats: {str(e)}")
