"""
에너지 풀 관리 API 엔드포인트
"""
from decimal import Decimal

from app.core.database import get_db
from app.models.energy_pool import EnergyPool, EnergyPriceHistory, EnergyUsageLog
from app.models.user import User
from app.services.energy_pool_service import EnergyPoolService
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_current_admin

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/energy", response_class=HTMLResponse)
async def energy_pool_page(
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """에너지 풀 관리 페이지"""
    # 활성화된 에너지 풀 조회
    result = await db.execute(
        select(EnergyPool).filter(EnergyPool.is_active == True)
    )
    energy_pools = result.scalars().all()

    return templates.TemplateResponse(
        "admin/energy.html",
        {
            "request": request,
            "admin": admin,
            "energy_pools": energy_pools,
        },
    )


@router.get("/api/energy/status")
async def get_energy_pool_status(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """에너지 풀 상태 조회"""
    service = EnergyPoolService(db)
    pool = await service.get_default_energy_pool()
    
    if not pool:
        return JSONResponse({"status": "no_pool", "message": "No active energy pool"})
    
    return JSONResponse({
        "status": "active",
        "pool_name": pool.pool_name,
        "available_energy": pool.available_energy,
        "available_bandwidth": pool.available_bandwidth,
        "total_frozen_trx": float(pool.total_frozen_trx),
    })


@router.get("/api/energy/statistics")
async def get_energy_statistics(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """에너지 사용 통계"""
    # 최근 사용량 로그 조회
    result = await db.execute(
        select(EnergyUsageLog)
        .order_by(desc(EnergyUsageLog.created_at))
        .limit(10)
    )
    recent_usage = result.scalars().all()
    
    usage_data = [
        {
            "timestamp": log.created_at.isoformat(),
            "energy_used": log.energy_consumed,
            "tx_hash": log.transaction_hash,
        }
        for log in recent_usage
    ]
    
    return JSONResponse({"recent_usage": usage_data})


@router.get("/api/energy/refreeze-check")
async def check_refreeze_needed(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """재동결 필요 여부 확인"""
    service = EnergyPoolService(db)
    needs_refreeze = await service.check_refreeze_needed()
    
    return JSONResponse({"needs_refreeze": needs_refreeze})


@router.post("/api/energy/create-pool")
async def create_energy_pool(
    pool_name: str = Form(...),
    wallet_address: str = Form(...),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """새 에너지 풀 생성"""
    try:
        service = EnergyPoolService(db)
        pool = await service.create_energy_pool(
            pool_name=pool_name,
            wallet_address=wallet_address,
        )
        
        return JSONResponse({
            "status": "success",
            "pool_id": pool.id,
            "message": "Energy pool created successfully"
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=400)


@router.post("/api/energy/record-price")
async def record_energy_price(
    price_per_energy: Decimal = Form(...),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """에너지 가격 기록"""
    try:
        price_history = EnergyPriceHistory(
            price_per_energy=price_per_energy,
            source="admin_manual",
        )
        
        db.add(price_history)
        await db.commit()
        
        return JSONResponse({
            "status": "success",
            "message": "Energy price recorded"
        })
    except Exception as e:
        await db.rollback()
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=400)


@router.post("/api/energy/simulate-usage")
async def simulate_usage(
    energy_amount: int = Form(...),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """에너지 사용 시뮬레이션"""
    try:
        # 시뮬레이션 로그 생성
        usage_log = EnergyUsageLog(
            energy_pool_id=1,  # 기본 풀 ID (실제로는 동적으로 조회)
            transaction_hash=f"SIMULATION_{int(Decimal('1234567890'))}",
            energy_consumed=energy_amount,
            bandwidth_consumed=0,
            fee_paid=Decimal("0"),
            simulation=True,
        )
        
        db.add(usage_log)
        await db.commit()
        
        return JSONResponse({
            "status": "success",
            "energy_used": energy_amount,
            "message": "Usage simulation completed"
        })
    except Exception as e:
        await db.rollback()
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=400)


@router.get("/api/energy/recent-usage")
async def get_recent_usage(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """최근 에너지 사용 내역"""
    result = await db.execute(
        select(EnergyUsageLog)
        .order_by(desc(EnergyUsageLog.created_at))
        .limit(20)
    )
    usage_logs = result.scalars().all()
    
    data = [
        {
            "id": log.id,
            "transaction_hash": log.transaction_hash,
            "energy_consumed": log.energy_consumed,
            "bandwidth_consumed": log.bandwidth_consumed,
            "fee_paid": float(log.fee_paid),
            "created_at": log.created_at.isoformat(),
            "is_simulation": log.simulation,
        }
        for log in usage_logs
    ]
    
    return JSONResponse({"usage_logs": data})
