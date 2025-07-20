"""
TRON 에너지 풀 관리 API 엔드포인트 (copilot-doc-24)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_admin_user
from app.services.energy.pool_manager import EnergyPoolManager
from app.services.energy.usage_tracker import EnergyUsageTracker
from app.services.energy.price_monitor import EnergyPriceMonitor
from app.schemas.energy import (
    CreateEnergyPoolRequest,
    EnergyPoolResponse,
    EnergyPoolStatusResponse,
    EnergyUsageStatsResponse,
    EnergyUsageLogResponse,
    EnergySimulationRequest,
    EnergySimulationResponse,
    AutoManagementSettings,
    EnergyPriceHistoryResponse,
    MessageResponse
)
from app.models.user import User
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["admin_energy"])


# 의존성 함수들
async def get_energy_pool_manager(db: AsyncSession = Depends(get_db)) -> EnergyPoolManager:
    """에너지 풀 매니저 의존성"""
    from tronpy import Tron
    # Redis는 현재 없으므로 Mock 객체 사용
    class MockRedis:
        async def get(self, key): return None
        async def setex(self, key, ttl, value): pass
        async def publish(self, channel, message): pass
    
    # Create a proper Tron client
    tron_client = Tron()  # Uses mainnet by default
    redis_client = MockRedis()
    return EnergyPoolManager(db, tron_client, redis_client)


async def get_usage_tracker(db: AsyncSession = Depends(get_db)) -> EnergyUsageTracker:
    """사용량 추적기 의존성"""
    class MockRedis:
        async def get(self, key): return None
        async def setex(self, key, ttl, value): pass
        async def publish(self, channel, message): pass
    
    redis_client = MockRedis()
    return EnergyUsageTracker(db, redis_client)


async def get_price_monitor(db: AsyncSession = Depends(get_db)) -> EnergyPriceMonitor:
    """가격 모니터 의존성"""
    class MockRedis:
        async def get(self, key): return None
        async def setex(self, key, ttl, value): pass
    
    redis_client = MockRedis()
    return EnergyPriceMonitor(db, redis_client)


@router.get("/status", response_model=EnergyPoolStatusResponse)
async def get_energy_pool_status(
    pool_id: int = Query(1, description="에너지 풀 ID"),
    current_admin: User = Depends(get_current_admin_user),
    energy_service: EnergyPoolManager = Depends(get_energy_pool_manager)
):
    """에너지 풀 현황 조회"""
    try:
        status = await energy_service.check_pool_status(pool_id)
        
        # 추가 정보 조회
        # usage_trend = await energy_service.get_usage_trend(pool_id, days=7)
        # depletion_estimate = await energy_service.estimate_depletion_time(pool_id)
        
        # 임시로 기본값 사용
        usage_trend = {"trend": "stable", "daily_average": 50000}
        depletion_estimate = None if status.get('available_energy', 0) > 100000 else "2 days"
        
        recommendations = []
        if status.get('status') == 'critical':
            recommendations.append("즉시 에너지 충전이 필요합니다")
        elif status.get('status') == 'low':
            recommendations.append("에너지 충전을 권장합니다")
        else:
            recommendations.append("에너지 상태가 양호합니다")
        
        return EnergyPoolStatusResponse(
            **status,
            usage_trend=usage_trend,
            estimated_depletion=depletion_estimate,
            recommendations=recommendations
        )
    except Exception as e:
        logger.error(f"에너지 풀 상태 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="에너지 풀 상태 조회 실패")


@router.post("/create-pool", response_model=EnergyPoolResponse)
async def create_energy_pool(
    pool_data: CreateEnergyPoolRequest,
    current_admin: User = Depends(get_current_admin_user),
    energy_service: EnergyPoolManager = Depends(get_energy_pool_manager)
):
    """새 에너지 풀 생성"""
    # 보안상 실제 프라이빗 키 처리는 제한
    if len(pool_data.owner_private_key) != 64:
        raise HTTPException(status_code=400, detail="올바르지 않은 프라이빗 키 형식")
        
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


@router.get("/usage-stats", response_model=EnergyUsageStatsResponse)
async def get_energy_usage_statistics(
    pool_id: int = Query(1),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_admin: User = Depends(get_current_admin_user),
    usage_tracker: EnergyUsageTracker = Depends(get_usage_tracker)
):
    """에너지 사용 통계 조회"""
    try:
        stats = await usage_tracker.get_usage_statistics(
            pool_id=pool_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return EnergyUsageStatsResponse(**stats)
    except Exception as e:
        logger.error(f"에너지 사용 통계 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="에너지 사용 통계 조회 실패")


@router.get("/usage-logs", response_model=List[EnergyUsageLogResponse])
async def get_energy_usage_logs(
    pool_id: int = Query(1),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    user_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """에너지 사용 로그 조회"""
    try:
        from sqlalchemy import select
        from app.models.energy_pool import EnergyUsageLog
        
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
    except Exception as e:
        logger.error(f"에너지 사용 로그 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="에너지 사용 로그 조회 실패")


@router.post("/simulate-usage", response_model=EnergySimulationResponse)
async def simulate_energy_usage(
    simulation_data: EnergySimulationRequest,
    current_admin: User = Depends(get_current_admin_user),
    energy_service: EnergyPoolManager = Depends(get_energy_pool_manager)
):
    """에너지 사용량 시뮬레이션"""
    try:
        simulation_result = await energy_service.simulate_usage(
            transaction_count=simulation_data.transaction_count,
            transaction_types=simulation_data.transaction_types,
            time_period_hours=simulation_data.time_period_hours
        )
        
        return EnergySimulationResponse(**simulation_result)
    except Exception as e:
        logger.error(f"에너지 시뮬레이션 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="에너지 시뮬레이션 실패")


@router.put("/auto-manage", response_model=MessageResponse)
async def update_auto_management_settings(
    pool_id: int,
    settings: AutoManagementSettings,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """자동 에너지 관리 설정"""
    try:
        from app.models.energy_pool import EnergyPoolModel
        from sqlalchemy import update
        
        # Check if pool exists
        pool = await db.get(EnergyPoolModel, pool_id)
        if not pool:
            raise HTTPException(status_code=404, detail="에너지 풀을 찾을 수 없습니다")
            
        # Update the pool settings
        await db.execute(
            update(EnergyPoolModel)
            .where(EnergyPoolModel.id == pool_id)
            .values(
                auto_refill=settings.enabled,
                auto_refill_amount=settings.refill_amount,
                auto_refill_trigger=settings.trigger_percentage
            )
        )
        
        await db.commit()
        
        return MessageResponse(message="자동 관리 설정이 업데이트되었습니다")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"자동 관리 설정 업데이트 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="자동 관리 설정 업데이트 실패")


@router.get("/price-history", response_model=List[EnergyPriceHistoryResponse])
async def get_energy_price_history(
    days: int = Query(7, le=30),
    current_admin: User = Depends(get_current_admin_user),
    price_monitor: EnergyPriceMonitor = Depends(get_price_monitor)
):
    """에너지 가격 히스토리 조회"""
    try:
        history = await price_monitor.get_price_history(days)
        
        return [
            EnergyPriceHistoryResponse(
                id=i+1,
                trx_price_usd=record['trx_price_usd'],
                energy_price_trx=record['energy_price_trx'],
                energy_price_usd=record['energy_price_usd'],
                market_demand=record['market_demand'],
                network_congestion=record['network_congestion'],
                recorded_at=datetime.fromisoformat(record['recorded_at'])
            )
            for i, record in enumerate(history)
        ]
    except Exception as e:
        logger.error(f"에너지 가격 히스토리 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="에너지 가격 히스토리 조회 실패")


@router.get("/cost-estimate")
async def get_energy_cost_estimate(
    transaction_type: str = Query("transfer", description="거래 유형"),
    token_type: str = Query("TRC20", description="토큰 유형"),
    current_admin: User = Depends(get_current_admin_user),
    energy_service: EnergyPoolManager = Depends(get_energy_pool_manager)
):
    """에너지 비용 추정"""
    try:
        estimate = await energy_service.estimate_energy_cost(
            transaction_type=transaction_type,
            token_type=token_type
        )
        
        return estimate
    except Exception as e:
        logger.error(f"에너지 비용 추정 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="에너지 비용 추정 실패")


@router.post("/update-prices")
async def update_energy_prices(
    current_admin: User = Depends(get_current_admin_user),
    price_monitor: EnergyPriceMonitor = Depends(get_price_monitor)
):
    """에너지 가격 수동 업데이트"""
    try:
        updated_prices = await price_monitor.update_energy_price()
        
        return {
            "message": "에너지 가격이 업데이트되었습니다",
            "prices": updated_prices
        }
    except Exception as e:
        logger.error(f"에너지 가격 업데이트 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="에너지 가격 업데이트 실패")


@router.get("/network-status")
async def get_network_status(
    current_admin: User = Depends(get_current_admin_user),
    energy_service: EnergyPoolManager = Depends(get_energy_pool_manager)
):
    """TRON 네트워크 상태 조회"""
    try:
        congestion = await energy_service.get_network_congestion()
        trx_price = await energy_service.get_trx_price()
        energy_price = await energy_service.get_current_energy_price()
        
        return {
            "network_congestion": congestion,
            "trx_price_usd": trx_price,
            "energy_price_trx": float(energy_price),
            "energy_price_usd": float(energy_price) * trx_price,
            "status": "normal" if congestion < 50 else "congested",
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"네트워크 상태 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="네트워크 상태 조회 실패")


@router.get("/efficiency-report")
async def get_efficiency_report(
    pool_id: int = Query(1),
    days: int = Query(30, le=90),
    current_admin: User = Depends(get_current_admin_user),
    usage_tracker: EnergyUsageTracker = Depends(get_usage_tracker)
):
    """에너지 효율성 리포트"""
    try:
        report = await usage_tracker.get_energy_efficiency_report(pool_id, days)
        
        return report
    except Exception as e:
        logger.error(f"효율성 리포트 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="효율성 리포트 조회 실패")


@router.get("/top-consumers")
async def get_top_energy_consumers(
    pool_id: int = Query(1),
    days: int = Query(7, le=30),
    limit: int = Query(10, le=50),
    current_admin: User = Depends(get_current_admin_user),
    usage_tracker: EnergyUsageTracker = Depends(get_usage_tracker)
):
    """상위 에너지 소비자 조회"""
    try:
        consumers = await usage_tracker.get_top_energy_consumers(pool_id, days, limit)
        
        return {
            "period_days": days,
            "top_consumers": consumers,
            "total_consumers": len(consumers)
        }
    except Exception as e:
        logger.error(f"상위 소비자 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="상위 소비자 조회 실패")
