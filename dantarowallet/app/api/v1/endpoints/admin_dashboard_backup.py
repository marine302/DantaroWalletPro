import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from app.core.config import settings
from app.core.database import get_db
from app.core.encryption import encrypt_private_key
from app.core.security import create_access_token, verify_password
from app.core.tron import TronService
from app.models.balance import Balance
from app.models.deposit import Deposit
from app.models.energy_pool import EnergyPool, EnergyPriceHistory, EnergyUsageLog
from app.models.fee_config import FeeConfig
from app.models.transaction import Transaction
from app.models.user import User
from app.models.wallet import Wallet
from app.models.withdrawal import Withdrawal
from app.services.energy_pool_service import EnergyPoolService
from app.services.fee_service import FeeService
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# 관리자 인증 헬퍼
async def get_current_admin(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    """현재 관리자 사용자 가져오기"""
    admin_id = getattr(request.state, "admin_id", None)
    if not admin_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(select(User).filter(User.id == int(admin_id)))
    admin = result.scalar_one_or_none()

    if not admin or not admin.is_admin:
        raise HTTPException(status_code=403, detail="Not an admin")

    return admin


@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """관리자 로그인 페이지"""
    return templates.TemplateResponse("admin/login.html", {"request": request})


@router.post("/login")
async def admin_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """관리자 로그인 처리"""
    # 사용자 확인
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "admin/login.html", {"request": request, "error": "Invalid credentials"}
        )

    if not user.is_admin:
        return templates.TemplateResponse(
            "admin/login.html", {"request": request, "error": "Admin access required"}
        )

    # 토큰 생성
    access_token = create_access_token(data={"sub": str(user.id)})

    # 대시보드로 리다이렉트
    response = RedirectResponse(url="/admin/dashboard", status_code=302)
    response.set_cookie(
        key="admin_token",
        value=access_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
    )

    return response


@router.get("/logout")
async def admin_logout():
    """관리자 로그아웃"""
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("admin_token")
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """관리자 대시보드 메인"""
    # 통계 수집
    stats = await get_dashboard_stats(db)

    # 최근 활동
    recent_activities = await get_recent_activities(db)

    # 시스템 상태 (간단한 더미 데이터)
    health_status = {
        "status": "healthy",
        "checks": {
            "database": {"status": "healthy", "message": "Connection OK"},
            "redis": {"status": "healthy", "message": "Connected"},
            "tron": {"status": "healthy", "message": "Network OK"},
        },
    }

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "admin": admin,
            "stats": stats,
            "activities": recent_activities,
            "health": health_status,
        },
    )


@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """사용자 관리 페이지"""
    # 쿼리 생성
    query = select(User)

    if search:
        query = query.filter(User.email.contains(search))

    if status == "active":
        query = query.filter(User.is_active == True)
    elif status == "inactive":
        query = query.filter(User.is_active == False)

    # 페이지네이션
    per_page = 20
    offset = (page - 1) * per_page

    # 전체 개수
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 사용자 목록
    query = query.order_by(User.created_at.desc())
    query = query.limit(per_page).offset(offset)
    result = await db.execute(query)
    users = result.scalars().all()

    # 각 사용자의 잔고 및 지갑 정보 가져오기
    user_data = []
    for user in users:
        # 모든 잔고 조회 (사용자별로 여러 자산 보유 가능)
        balance_result = await db.execute(
            select(Balance).filter(Balance.user_id == user.id)
        )
        balances = balance_result.scalars().all()

        wallet_result = await db.execute(
            select(Wallet).filter(Wallet.user_id == user.id)
        )
        wallet = wallet_result.scalar_one_or_none()

        user_data.append(
            {"user": user, "balances": balances, "wallet": wallet}  # 복수형으로 변경
        )

    # 페이지 정보
    total_pages = max(1, (total + per_page - 1) // per_page)

    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "admin": admin,
            "users": user_data,
            "search": search,
            "status": status,
            "page": page,
            "total_pages": total_pages,
            "total": total,
        },
    )


@router.post("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """사용자 상태 토글"""
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 사용자 상태 토글 (SQLAlchemy update 방식)
    await db.execute(
        User.__table__.update()
        .where(User.id == user_id)
        .values(is_active=~User.is_active)
    )
    await db.commit()

    return RedirectResponse(url="/admin/users", status_code=302)


@router.get("/withdrawals", response_class=HTMLResponse)
async def admin_withdrawals(
    request: Request,
    status: str = Query("pending"),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """출금 관리 페이지"""
    query = select(Withdrawal)

    if status and status != "all":
        query = query.filter(Withdrawal.status == status)

    # 우선순위 및 요청 시간 순서로 정렬
    query = query.order_by(Withdrawal.created_at.desc())

    result = await db.execute(query)
    withdrawals = result.scalars().all()

    # 사용자 정보 포함
    withdrawal_data = []
    for w in withdrawals:
        user_result = await db.execute(select(User).filter(User.id == w.user_id))
        user = user_result.scalar_one()

        withdrawal_data.append({"withdrawal": w, "user": user})

    return templates.TemplateResponse(
        "admin/withdrawals.html",
        {
            "request": request,
            "admin": admin,
            "withdrawals": withdrawal_data,
            "current_status": status,
        },
    )


@router.get("/system", response_class=HTMLResponse)
async def admin_system(
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """시스템 관리 페이지"""
    # 시스템 메트릭 (더미 데이터)
    metrics = {
        "cpu_percent": 45.2,
        "memory_percent": 67.8,
        "disk_percent": 23.4,
        "active_requests": 15,
        "total_requests": 15420,
        "error_rate": 0.2,
        "avg_response_time_ms": 125,
        "p95_response_time_ms": 250,
        "p99_response_time_ms": 500,
        "uptime_seconds": 345600,
    }

    # 백그라운드 태스크 상태 (더미 데이터)
    task_status = [
        {"name": "wallet_sync", "done": False, "cancelled": False},
        {"name": "balance_update", "done": False, "cancelled": False},
        {"name": "tx_monitor", "done": False, "cancelled": False},
    ]

    return templates.TemplateResponse(
        "admin/system.html",
        {
            "request": request,
            "admin": admin,
            "metrics": metrics,
            "task_status": task_status,
            "emergency_stop_enabled": getattr(settings, "EMERGENCY_STOP", False),
        },
    )


@router.post("/emergency-stop")
async def emergency_stop(
    action: str = Form(...),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """긴급 정지/해제"""
    if action == "enable":
        settings.EMERGENCY_STOP = True
        message = "Emergency stop ENABLED"
    else:
        settings.EMERGENCY_STOP = False
        message = "Emergency stop DISABLED"

    return RedirectResponse(url="/admin/system", status_code=302)


@router.post("/users/{user_id}/create-wallet")
async def create_user_wallet(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """사용자를 위한 Tron 지갑 생성"""
    # 사용자 확인
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 이미 지갑이 있는지 확인
    wallet_result = await db.execute(select(Wallet).filter(Wallet.user_id == user_id))
    existing_wallet = wallet_result.scalar_one_or_none()

    if existing_wallet:
        raise HTTPException(status_code=400, detail="User already has a wallet")

    try:
        # Tron 지갑 생성
        tron_service = TronService()
        wallet_data = tron_service.generate_wallet()

        # 개인키 암호화
        encrypted_key, salt = encrypt_private_key(wallet_data["private_key"])

        # 데이터베이스에 저장
        new_wallet = Wallet(
            user_id=user_id,
            address=wallet_data["address"],
            hex_address=wallet_data["hex_address"],
            encrypted_private_key=encrypted_key,
            encryption_salt=salt,
            is_active=True,
            is_monitored=True,
        )

        db.add(new_wallet)

        # 사용자 tron_address 업데이트 (SQLAlchemy update 방식 사용)
        await db.execute(
            User.__table__.update()
            .where(User.id == user_id)
            .values(tron_address=wallet_data["address"])
        )

        await db.commit()

        return RedirectResponse(url="/admin/users", status_code=302)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create wallet: {str(e)}"
        )


@router.post("/users/{user_id}/create-balance")
async def create_user_balance(
    user_id: int,
    asset: str = Form(...),
    amount: float = Form(0.0),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """사용자에게 초기 잔고 생성/추가"""
    # 사용자 확인
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 기존 잔고 확인
    balance_result = await db.execute(
        select(Balance).filter(and_(Balance.user_id == user_id, Balance.asset == asset))
    )
    existing_balance = balance_result.scalar_one_or_none()

    if existing_balance:
        # 기존 잔고에 추가 (SQLAlchemy update 방식)
        await db.execute(
            Balance.__table__.update()
            .where(and_(Balance.user_id == user_id, Balance.asset == asset))
            .values(amount=Balance.amount + amount)
        )
    else:
        # 새 잔고 생성
        new_balance = Balance(
            user_id=user_id, asset=asset, amount=amount, locked_amount=0.0
        )
        db.add(new_balance)

    await db.commit()

    return RedirectResponse(url="/admin/users", status_code=302)


@router.get("/fees", response_class=HTMLResponse)
async def admin_fees(
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """수수료 관리 페이지"""
    fee_service = FeeService(db)
    fee_configs = await fee_service.get_all_fee_configs()

    # SQLAlchemy 객체를 딕셔너리로 변환
    fee_configs_dict = []
    for config in fee_configs:
        config_dict = {
            "id": config.id,
            "fee_type": config.fee_type,
            "asset": config.asset,
            "fee_amount": str(config.fee_amount),
            "description": config.description,
            "is_active": config.is_active,
        }

        # datetime 필드 안전하게 처리
        if hasattr(config, "created_at"):
            try:
                config_dict["created_at"] = (
                    config.created_at.isoformat()
                    if config.created_at is not None
                    else None
                )
            except:
                config_dict["created_at"] = None
        else:
            config_dict["created_at"] = None

        if hasattr(config, "updated_at"):
            try:
                config_dict["updated_at"] = (
                    config.updated_at.isoformat()
                    if config.updated_at is not None
                    else None
                )
            except:
                config_dict["updated_at"] = None
        else:
            config_dict["updated_at"] = None

        fee_configs_dict.append(config_dict)

    return templates.TemplateResponse(
        "admin/fees.html",
        {
            "request": request,
            "admin": admin,
            "fee_configs": fee_configs,
            "fee_configs_json": fee_configs_dict,
        },
    )


@router.post("/fees/create")
async def create_fee_config(
    fee_type: str = Form(...),
    asset: str = Form(...),
    fee_amount: str = Form(...),
    description: str = Form(""),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """수수료 설정 생성"""
    fee_service = FeeService(db)

    try:
        amount = Decimal(fee_amount)
        await fee_service.create_fee_config(
            fee_type=fee_type,
            asset=asset,
            fee_amount=amount,
            description=description if description else None,
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Failed to create fee config: {str(e)}"
        )

    return RedirectResponse(url="/admin/fees", status_code=302)


# === Energy Pool Management Endpoints ===


@router.get("/energy", response_class=HTMLResponse)
async def energy_pool_page(
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """에너지 풀 관리 페이지"""
    energy_service = EnergyPoolService(db)

    # 에너지 풀 현황 조회
    pool_status = await energy_service.get_energy_pool_status()

    # 에너지 사용 통계 (최근 7일)
    usage_stats = await energy_service.get_energy_usage_statistics(days=7)

    # Refreeze 필요 여부 확인
    refreeze_check = await energy_service.check_refreeze_needed()

    return templates.TemplateResponse(
        "admin/energy.html",
        {
            "request": request,
            "admin": admin,
            "pool_status": pool_status,
            "usage_stats": usage_stats,
            "refreeze_check": refreeze_check,
            "page_title": "에너지 풀 관리",
        },
    )


@router.get("/api/energy/status")
async def get_energy_pool_status(
    admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    """에너지 풀 현황 API"""
    energy_service = EnergyPoolService(db)
    return await energy_service.get_energy_pool_status()


@router.get("/api/energy/statistics")
async def get_energy_statistics(
    days: int = Query(7, ge=1, le=30),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """에너지 사용 통계 API"""
    energy_service = EnergyPoolService(db)
    return await energy_service.get_energy_usage_statistics(days=days)


@router.get("/api/energy/refreeze-check")
async def check_refreeze_needed(
    admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
):
    """Refreeze 필요 여부 확인 API"""
    energy_service = EnergyPoolService(db)
    return await energy_service.check_refreeze_needed()


@router.post("/api/energy/create-pool")
async def create_energy_pool(
    wallet_address: str = Form(...),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """에너지 풀 생성 API"""
    energy_service = EnergyPoolService(db)

    try:
        # 기존 풀이 있는지 확인
        existing_pool = await energy_service.get_default_energy_pool()
        if existing_pool:
            return {
                "error": "Default energy pool already exists",
                "pool_id": existing_pool.id,
            }

        # 새 풀 생성
        new_pool = await energy_service.create_default_energy_pool(wallet_address)
        return {
            "success": True,
            "message": "Energy pool created successfully",
            "pool_id": new_pool.id,
            "wallet_address": new_pool.wallet_address,
        }
    except Exception as e:
        return {"error": f"Failed to create energy pool: {str(e)}"}


@router.post("/api/energy/record-price")
async def record_energy_price(
    trx_price_usd: float = Form(...),
    energy_per_trx: int = Form(...),
    bandwidth_per_trx: int = Form(...),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """에너지 가격 정보 기록 API"""
    energy_service = EnergyPoolService(db)

    try:
        price_record = await energy_service.record_energy_price(
            trx_price_usd=Decimal(str(trx_price_usd)),
            energy_per_trx=energy_per_trx,
            bandwidth_per_trx=bandwidth_per_trx,
            source="Manual",
        )

        return {
            "success": True,
            "message": "Energy price recorded successfully",
            "record_id": price_record.id,
            "recorded_at": price_record.recorded_at.isoformat(),
        }
    except Exception as e:
        return {"error": f"Failed to record price: {str(e)}"}


@router.post("/api/energy/simulate-usage")
async def simulate_energy_usage(
    transaction_type: str = Form(...),
    energy_amount: int = Form(...),
    bandwidth_amount: int = Form(0),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """에너지 사용 시뮬레이션 API (테스트용)"""
    energy_service = EnergyPoolService(db)

    try:
        # 기본 풀 조회
        pool = await energy_service.get_default_energy_pool()
        if not pool:
            return {"error": "No energy pool found"}

        # 시뮬레이션 로그 기록
        usage_log = await energy_service.log_energy_usage(
            energy_pool_id=pool.id,
            transaction_hash=f"SIM_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            transaction_type=transaction_type,
            energy_consumed=energy_amount,
            bandwidth_consumed=bandwidth_amount,
            from_address="SIMULATION",
            to_address="SIMULATION",
        )

        return {
            "success": True,
            "message": "Energy usage simulated successfully",
            "log_id": usage_log.id,
            "energy_consumed": energy_amount,
            "bandwidth_consumed": bandwidth_amount,
        }
    except Exception as e:
        return {"error": f"Simulation failed: {str(e)}"}


@router.get("/api/energy/recent-usage")
async def get_recent_energy_usage(
    limit: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """최근 에너지 사용 내역 API"""
    try:
        energy_service = EnergyPoolService(db)
        pool = await energy_service.get_default_energy_pool()

        if not pool:
            return {"error": "No energy pool found"}

        # 최근 사용 내역 조회
        recent_logs = await db.execute(
            select(EnergyUsageLog)
            .filter(EnergyUsageLog.energy_pool_id == pool.id)
            .order_by(EnergyUsageLog.created_at.desc())
            .limit(limit)
        )

        usage_data = []
        for log in recent_logs.scalars():
            usage_data.append(
                {
                    "id": log.id,
                    "transaction_hash": log.transaction_hash,
                    "transaction_type": log.transaction_type,
                    "energy_consumed": log.energy_consumed,
                    "bandwidth_consumed": log.bandwidth_consumed,
                    "trx_cost_equivalent": str(log.trx_cost_equivalent)
                    if log.trx_cost_equivalent is not None
                    else "0",
                    "user_id": log.user_id,
                    "from_address": log.from_address,
                    "to_address": log.to_address,
                    "amount": str(log.amount) if log.amount is not None else None,
                    "asset": log.asset,
                    "timestamp": log.timestamp.isoformat(),
                    "created_at": log.created_at.isoformat(),
                }
            )

        return {
            "pool_id": pool.id,
            "total_logs": len(usage_data),
            "usage_logs": usage_data,
        }

    except Exception as e:
        return {"error": f"Failed to fetch recent usage: {str(e)}"}


# 헬퍼 함수들


async def get_dashboard_stats(db: AsyncSession) -> dict:
    """대시보드 통계 수집"""
    # 사용자 통계
    total_users = await db.execute(select(func.count(User.id)))
    total_users = total_users.scalar()

    active_users = await db.execute(
        select(func.count(User.id)).filter(User.is_active == True)
    )
    active_users = active_users.scalar()

    # 잔고 통계
    total_balance = await db.execute(select(func.sum(Balance.amount)))
    total_balance = total_balance.scalar() or 0

    # 오늘 통계
    today = datetime.utcnow().date()

    today_deposits = await db.execute(
        select(
            func.count(Deposit.id), func.coalesce(func.sum(Deposit.amount), 0)
        ).filter(Deposit.created_at >= today)
    )
    deposit_count, deposit_amount = today_deposits.one()

    today_withdrawals = await db.execute(
        select(
            func.count(Withdrawal.id), func.coalesce(func.sum(Withdrawal.amount), 0)
        ).filter(Withdrawal.created_at >= today)
    )
    withdrawal_count, withdrawal_amount = today_withdrawals.one()

    # 대기 중인 출금
    pending_withdrawals = await db.execute(
        select(func.count(Withdrawal.id)).filter(Withdrawal.status == "pending")
    )
    pending_count = pending_withdrawals.scalar()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_balance": float(total_balance),
        "today_deposits": {
            "count": deposit_count or 0,
            "amount": float(deposit_amount or 0),
        },
        "today_withdrawals": {
            "count": withdrawal_count or 0,
            "amount": float(withdrawal_amount or 0),
        },
        "pending_withdrawals": pending_count or 0,
    }


async def get_recent_activities(db: AsyncSession, limit: int = 10) -> list:
    """최근 활동 조회"""
    activities = []

    # 최근 입금
    recent_deposits = await db.execute(
        select(Deposit)
        .filter(Deposit.is_confirmed == True)
        .order_by(Deposit.created_at.desc())
        .limit(5)
    )
    for deposit in recent_deposits.scalars():
        activities.append(
            {
                "type": "deposit",
                "amount": str(deposit.amount),
                "time": deposit.created_at,
                "details": f"Deposit confirmed",
            }
        )

    # 최근 출금
    recent_withdrawals = await db.execute(
        select(Withdrawal)
        .filter(Withdrawal.status == "completed")
        .order_by(Withdrawal.created_at.desc())
        .limit(5)
    )
    for withdrawal in recent_withdrawals.scalars():
        activities.append(
            {
                "type": "withdrawal",
                "amount": str(withdrawal.amount),
                "time": withdrawal.created_at,
                "details": f"Withdrawal completed",
            }
        )

    # 시간순 정렬
    activities.sort(key=lambda x: x["time"], reverse=True)
    return activities[:limit]
