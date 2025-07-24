"""
최적화 관리 API 엔드포인트

백엔드 성능 최적화 상태 모니터링 및 관리를 위한 API를 제공합니다.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_super_admin
from app.core.database import get_db
from app.core.optimization_manager import optimization_manager
from app.core.performance_monitor import performance_monitor
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/optimization", tags=["optimization"])


@router.get("/status", response_model=Dict[str, Any])
async def get_optimization_status(
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    최적화 시스템 전체 상태 조회
    슈퍼 어드민만 접근 가능
    """
    try:
        status_data = await optimization_manager.get_optimization_status()
        return {"success": True, "data": status_data}
    except Exception as e:
        logger.error(f"최적화 상태 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="최적화 상태 조회 실패",
        )


@router.get("/performance/metrics", response_model=Dict[str, Any])
async def get_performance_metrics(
    minutes: int = Query(30, ge=1, le=1440, description="조회 기간 (분)"),
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    성능 메트릭 조회
    """
    try:
        # 현재 메트릭 수집
        current_metrics = await performance_monitor.collect_system_metrics()

        # 기간별 성능 보고서
        performance_report = await performance_monitor.get_performance_report(minutes)

        return {
            "success": True,
            "data": {
                "current_metrics": {
                    "cpu_usage": current_metrics.cpu_usage,
                    "memory_usage": current_metrics.memory_usage,
                    "disk_usage": current_metrics.disk_usage,
                    "response_time": current_metrics.response_time,
                    "error_rate": current_metrics.error_rate,
                    "throughput": current_metrics.throughput,
                    "database_connections": current_metrics.database_connections,
                    "active_requests": current_metrics.active_requests,
                    "timestamp": current_metrics.timestamp.isoformat(),
                },
                "performance_report": performance_report,
            },
        }
    except Exception as e:
        logger.error(f"성능 메트릭 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="성능 메트릭 조회 실패",
        )


@router.get("/recommendations", response_model=Dict[str, Any])
async def get_optimization_recommendations(
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    최적화 권장사항 조회
    """
    try:
        recommendations = (
            await optimization_manager.generate_optimization_recommendations()
        )

        return {
            "success": True,
            "data": {"recommendations": recommendations, "count": len(recommendations)},
        }
    except Exception as e:
        logger.error(f"최적화 권장사항 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="최적화 권장사항 조회 실패",
        )


@router.post("/actions/{action_type}", response_model=Dict[str, Any])
async def execute_optimization_action(
    action_type: str,
    params: Optional[Dict[str, Any]] = None,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    최적화 작업 실행

    지원되는 action_type:
    - cache_clear: 캐시 정리
    - scale_workers: 워커 수 조정
    - optimize_queries: 쿼리 최적화
    """
    try:
        if params is None:
            params = {}

        # 허용된 액션 타입 확인
        allowed_actions = ["cache_clear", "scale_workers", "optimize_queries"]
        if action_type not in allowed_actions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원되지 않는 액션 타입입니다. 허용된 타입: {allowed_actions}",
            )

        # 최적화 작업 실행
        result = await optimization_manager.apply_manual_optimization(
            action_type, params
        )

        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "action_type": action_type,
                "params": params,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"]
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"최적화 작업 실행 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="최적화 작업 실행 실패",
        )


@router.get("/api-performance", response_model=Dict[str, Any])
async def get_api_performance_stats(
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    API 성능 통계 조회
    """
    try:
        api_stats = await optimization_manager.api_optimizer.get_performance_stats()

        return {"success": True, "data": api_stats}
    except Exception as e:
        logger.error(f"API 성능 통계 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API 성능 통계 조회 실패",
        )


@router.get("/database/optimization", response_model=Dict[str, Any])
async def get_database_optimization_info(
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    데이터베이스 최적화 정보 조회
    """
    try:
        # 슬로우 쿼리 분석
        optimization_report = await performance_monitor.optimize_database_queries(db)

        return {"success": True, "data": optimization_report}
    except Exception as e:
        logger.error(f"데이터베이스 최적화 정보 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터베이스 최적화 정보 조회 실패",
        )


@router.post("/cache/clear", response_model=Dict[str, Any])
async def clear_cache(
    cache_type: str = Query("all", description="캐시 타입 (all, query, api)"),
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    캐시 정리
    """
    try:
        cleared_items = 0

        if cache_type in ["all", "query"]:
            # 쿼리 캐시 정리
            query_cache_size = len(optimization_manager.db_optimizer.query_cache)
            optimization_manager.db_optimizer.query_cache.clear()
            cleared_items += query_cache_size
            logger.info(f"쿼리 캐시 정리: {query_cache_size}개 항목")

        if cache_type in ["all", "api"]:
            # API 캐시 정리 (Redis 연결되어 있는 경우)
            if optimization_manager.db_optimizer.redis_client:
                # Redis 캐시 정리 로직
                pass

        return {
            "success": True,
            "message": f"캐시 정리 완료: {cleared_items}개 항목 삭제",
            "cache_type": cache_type,
            "cleared_items": cleared_items,
        }

    except Exception as e:
        logger.error(f"캐시 정리 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="캐시 정리 실패"
        )


@router.post("/scaling/adjust", response_model=Dict[str, Any])
async def adjust_scaling(
    worker_count: int = Query(..., ge=1, le=20, description="워커 수"),
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    워커 수 조정 (수동 스케일링)
    """
    try:
        old_count = optimization_manager.task_queue.max_concurrent_tasks
        optimization_manager.task_queue.max_concurrent_tasks = worker_count

        return {
            "success": True,
            "message": f"워커 수 조정 완료: {old_count} → {worker_count}",
            "old_worker_count": old_count,
            "new_worker_count": worker_count,
        }

    except Exception as e:
        logger.error(f"워커 수 조정 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="워커 수 조정 실패",
        )


@router.get("/health-check", response_model=Dict[str, Any])
async def optimization_health_check(
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    최적화 시스템 헬스 체크
    """
    try:
        health_status = {
            "optimization_manager": optimization_manager.optimization_enabled,
            "auto_scaling": optimization_manager.auto_scaling_enabled,
            "database_optimizer": optimization_manager.db_optimizer is not None,
            "api_optimizer": optimization_manager.api_optimizer is not None,
            "task_queue": optimization_manager.task_queue is not None,
            "performance_monitor": optimization_manager.performance_monitor is not None,
            "redis_connection": optimization_manager.db_optimizer.redis_client
            is not None,
        }

        # 전체 헬스 상태
        overall_health = all(health_status.values())

        return {
            "success": True,
            "data": {
                "overall_health": overall_health,
                "components": health_status,
                "timestamp": performance_monitor.start_time,
            },
        }

    except Exception as e:
        logger.error(f"헬스 체크 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="헬스 체크 실패"
        )
