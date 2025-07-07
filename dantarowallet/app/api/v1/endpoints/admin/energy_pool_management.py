"""
에너지 관리 API 엔드포인트 (copilot-doc-24 구현)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_admin, get_redis_client
from app.services.energy.pool_manager import EnergyPoolManager
from app.services.energy.usage_tracker import EnergyUsageTracker
from app.services.energy.price_monitor import EnergyPriceMonitor
from app.schemas.energy import (
    CreateEnergyPoolRequest, EnergyPoolResponse, EnergyPoolStatusResponse,
    EnergyUsageLogResponse, EnergyUsageStatsResponse, EnergySimulationRequest,
    EnergySimulationResponse, AutoManagementSettings, EnergyPriceHistoryResponse,
    MessageResponse
)
from app.models.energy_pool import EnergyPoolModel, EnergyUsageLog, EnergyPriceHistory
from app.models.user import User
from app.core.logger import get_logger
from app.core.tron import get_tron_client

logger = get_logger(__name__)
router = APIRouter()


async def get_energy_pool_manager(
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis_client)
) -> EnergyPoolManager:
    """에너지 풀 매니저 의존성"""
    tron_client = get_tron_client()
    return EnergyPoolManager(db, tron_client, redis_client)


async def get_usage_tracker(
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis_client)
) -> EnergyUsageTracker:
    """사용량 추적기 의존성"""
    return EnergyUsageTracker(db, redis_client)


async def get_price_monitor(
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis_client)
) -> EnergyPriceMonitor:
    """가격 모니터 의존성"""
    return EnergyPriceMonitor(db, redis_client)


@router.get("/admin/energy/status", response_model=EnergyPoolStatusResponse)
async def get_energy_pool_status(
    pool_id: int = Query(1, description="에너지 풀 ID"),
    current_admin: User = Depends(get_current_admin),
    energy_service: EnergyPoolManager = Depends(get_energy_pool_manager)
):
    """에너지 풀 현황 조회"""
    try:
        status = await energy_service.check_pool_status(pool_id)
        
        # 추가 정보 조회
        usage_trend = await energy_service.get_usage_trend(pool_id, days=7)
        depletion_estimate = await energy_service.estimate_depletion_time(pool_id)
        
        return EnergyPoolStatusResponse(
            **status,
            usage_trend=usage_trend,
            estimated_depletion=depletion_estimate,
            recommendations=await energy_service.get_recommendations(status)
        )
    except Exception as e:
        logger.error(f"에너지 풀 상태 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="에너지 풀 상태 조회 실패")


@router.post("/admin/energy/create-pool", response_model=EnergyPoolResponse)
async def create_energy_pool(
    pool_data: CreateEnergyPoolRequest,
    current_admin: User = Depends(get_current_admin),
    energy_service: EnergyPoolManager = Depends(get_energy_pool_manager)
):
    """새 에너지 풀 생성"""
    if not hasattr(current_admin, 'is_super_admin') or not current_admin.is_super_admin:
        raise HTTPException(status_code=403, detail="슈퍼 관리자만 가능합니다")
        
    try:
        pool = await energy_service.create_energy_pool(
            pool_name=pool_data.pool_name,
            owner_private_key=pool_data.owner_private_key,
            initial_trx_amount=pool_data.initial_trx_amount
        )
        
        return EnergyPoolResponse.model_validate(pool)
    except Exception as e:
        logger.error(f"에너지 풀 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/energy/usage-stats", response_model=EnergyUsageStatsResponse)
async def get_energy_usage_statistics(
    pool_id: int = Query(1),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_admin: User = Depends(get_current_admin),
    usage_tracker: EnergyUsageTracker = Depends(get_usage_tracker)
):
    """에너지 사용 통계 조회"""
    stats = await usage_tracker.get_usage_statistics(
        pool_id=pool_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return EnergyUsageStatsResponse(**stats)


@router.get("/admin/energy/usage-logs", response_model=List[EnergyUsageLogResponse])
async def get_energy_usage_logs(
    pool_id: int = Query(1),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    user_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """에너지 사용 로그 조회"""
    from sqlalchemy import select
    
    query = select(EnergyUsageLog).where(EnergyUsageLog.pool_id == pool_id)
    
    if user_id:
        query = query.where(EnergyUsageLog.user_id == user_id)
    if transaction_type:
        query = query.where(EnergyUsageLog.transaction_type == transaction_type)
        
    query = query.order_by(EnergyUsageLog.used_at.desc())
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return [EnergyUsageLogResponse.model_validate(log) for log in logs]


@router.post("/admin/energy/simulate-usage", response_model=EnergySimulationResponse)
async def simulate_energy_usage(
    simulation_data: EnergySimulationRequest,
    current_admin: User = Depends(get_current_admin),
    energy_service: EnergyPoolManager = Depends(get_energy_pool_manager)
):
    """에너지 사용량 시뮬레이션"""
    simulation_result = await energy_service.simulate_usage(
        transaction_count=simulation_data.transaction_count,
        transaction_types=simulation_data.transaction_types,
        time_period_hours=simulation_data.time_period_hours
    )
    
    return EnergySimulationResponse(**simulation_result)


@router.put("/admin/energy/auto-manage", response_model=MessageResponse)
async def update_auto_management_settings(
    pool_id: int,
    settings: AutoManagementSettings,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """자동 에너지 관리 설정"""
    pool = await db.get(EnergyPoolModel, pool_id)
    if not pool:
        raise HTTPException(status_code=404, detail="에너지 풀을 찾을 수 없습니다")
        
    pool.auto_refill = settings.enabled
    pool.auto_refill_amount = settings.refill_amount
    pool.auto_refill_trigger = settings.trigger_percentage
    
    await db.commit()
    
    return MessageResponse(message="자동 관리 설정이 업데이트되었습니다")


@router.get("/admin/energy/price-history", response_model=List[EnergyPriceHistoryResponse])
async def get_energy_price_history(
    days: int = Query(7, le=30),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """에너지 가격 히스토리 조회"""
    since = datetime.utcnow() - timedelta(days=days)
    
    from sqlalchemy import select
    query = select(EnergyPriceHistory).where(
        EnergyPriceHistory.recorded_at >= since
    ).order_by(EnergyPriceHistory.recorded_at.desc())
    
    result = await db.execute(query)
    history = result.scalars().all()
    
    return [EnergyPriceHistoryResponse.model_validate(record) for record in history]


@router.get("/admin/energy/cost-estimate")
async def estimate_transaction_cost(
    transaction_type: str = Query(..., description="거래 유형"),
    token_type: str = Query("TRC20", description="토큰 유형"),
    current_admin: User = Depends(get_current_admin),
    energy_service: EnergyPoolManager = Depends(get_energy_pool_manager)
):
    """트랜잭션 비용 추정"""
    try:
        cost_estimate = await energy_service.estimate_energy_cost(
            transaction_type=transaction_type,
            token_type=token_type
        )
        return cost_estimate
    except Exception as e:
        logger.error(f"비용 추정 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="비용 추정 실패")


@router.get("/admin/energy/top-consumers")
async def get_top_energy_consumers(
    pool_id: int = Query(1),
    days: int = Query(7, le=30),
    limit: int = Query(10, le=50),
    current_admin: User = Depends(get_current_admin),
    usage_tracker: EnergyUsageTracker = Depends(get_usage_tracker)
):
    """상위 에너지 소비자 조회"""
    try:
        consumers = await usage_tracker.get_top_energy_consumers(
            pool_id=pool_id,
            days=days,
            limit=limit
        )
        return {"consumers": consumers}
    except Exception as e:
        logger.error(f"상위 소비자 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="상위 소비자 조회 실패")


@router.get("/admin/energy/efficiency-report")
async def get_energy_efficiency_report(
    pool_id: int = Query(1),
    days: int = Query(30, le=90),
    current_admin: User = Depends(get_current_admin),
    usage_tracker: EnergyUsageTracker = Depends(get_usage_tracker)
):
    """에너지 효율성 리포트"""
    try:
        report = await usage_tracker.get_energy_efficiency_report(
            pool_id=pool_id,
            days=days
        )
        return report
    except Exception as e:
        logger.error(f"효율성 리포트 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="효율성 리포트 생성 실패")


@router.get("/admin/energy/price-trend")
async def get_energy_price_trend(
    days: int = Query(30, le=90),
    current_admin: User = Depends(get_current_admin),
    price_monitor: EnergyPriceMonitor = Depends(get_price_monitor)
):
    """에너지 가격 트렌드 분석"""
    try:
        trend_analysis = await price_monitor.get_price_trend_analysis(days=days)
        return trend_analysis
    except Exception as e:
        logger.error(f"가격 트렌드 분석 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="가격 트렌드 분석 실패")


@router.post("/admin/energy/update-prices", response_model=MessageResponse)
async def update_energy_prices(
    current_admin: User = Depends(get_current_admin),
    price_monitor: EnergyPriceMonitor = Depends(get_price_monitor)
):
    """에너지 가격 수동 업데이트"""
    if not hasattr(current_admin, 'is_super_admin') or not current_admin.is_super_admin:
        raise HTTPException(status_code=403, detail="슈퍼 관리자만 가능합니다")
    
    try:
        updated_prices = await price_monitor.update_energy_price()
        return MessageResponse(
            message=f"에너지 가격 업데이트 완료: TRX ${updated_prices['trx_price_usd']:.4f}"
        )
    except Exception as e:
        logger.error(f"가격 업데이트 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="가격 업데이트 실패")
