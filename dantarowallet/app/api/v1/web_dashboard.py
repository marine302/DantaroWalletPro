"""
웹 대시보드 페이지 라우터.
사용자 및 관리자 웹 대시보드를 제공합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.web_auth import optional_auth, require_auth
from app.models.user import User
from app.services.balance_service import BalanceService
from app.services.dashboard_service import DashboardService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth()),
):
    """사용자 대시보드 페이지"""
    try:
        dashboard_service = DashboardService(db)
        balance_service = BalanceService(db)

        # 사용자 정보 및 잔고 조회
        user_overview = await dashboard_service.get_user_overview(current_user.id)
        recent_transactions = await dashboard_service.get_recent_transactions(
            current_user.id
        )
        balance_history = await dashboard_service.get_balance_history(current_user.id)
        wallet_stats = await dashboard_service.get_wallet_stats(current_user.id)

        # 잔고 정보
        trx_balance = await balance_service.get_or_create_balance(
            current_user.id, "TRX"
        )
        usdt_balance = await balance_service.get_or_create_balance(
            current_user.id, "USDT"
        )

        # 차트를 위한 잔고 이력 데이터 처리
        balance_chart_data = {
            "dates": [bh.date.isoformat() if bh.date else "" for bh in balance_history],
            "trx_values": [
                float(bh.balance) if bh.balance else 0.0 for bh in balance_history
            ],
            "usdt_values": [
                float(bh.balance) if bh.balance else 0.0 for bh in balance_history
            ],
        }

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "current_user": current_user,
                "user_overview": user_overview,
                "recent_transactions": recent_transactions,
                "balance_history": balance_chart_data,  # 차트용 데이터로 변경
                "wallet_stats": wallet_stats,
                "user_balance": {
                    "trx_balance": str(trx_balance.amount if trx_balance else 0),
                    "usdt_balance": str(usdt_balance.amount if usdt_balance else 0),
                },
                "wallet_address": getattr(current_user, "tron_address", None) or "",
            },
        )
    except HTTPException as e:
        if e.status_code == 302:
            return RedirectResponse(url="/auth/login")
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logout", response_class=HTMLResponse)
async def logout_page(request: Request):
    """로그아웃 처리"""
    # 쿠키에서 JWT 토큰 제거
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth()),
):
    """사용자 프로필 페이지"""
    try:
        return templates.TemplateResponse(
            "profile.html", {"request": request, "current_user": current_user}
        )
    except HTTPException as e:
        if e.status_code == 302:
            return RedirectResponse(url="/auth/login")
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth()),
):
    """사용자 설정 페이지"""
    try:
        return templates.TemplateResponse(
            "settings.html", {"request": request, "current_user": current_user}
        )
    except HTTPException as e:
        if e.status_code == 302:
            return RedirectResponse(url="/auth/login")
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions", response_class=HTMLResponse)
async def transactions_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth()),
):
    """거래 내역 페이지"""
    try:
        dashboard_service = DashboardService(db)
        transactions = await dashboard_service.get_recent_transactions(
            current_user.id, limit=50
        )

        return templates.TemplateResponse(
            "transactions.html",
            {
                "request": request,
                "current_user": current_user,
                "transactions": transactions,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wallet", response_class=HTMLResponse)
async def wallet_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth()),
):
    """지갑 관리 페이지"""
    try:
        balance_service = BalanceService(db)

        # 잔고 정보
        trx_balance = await balance_service.get_or_create_balance(
            current_user.id, "TRX"
        )
        usdt_balance = await balance_service.get_or_create_balance(
            current_user.id, "USDT"
        )

        return templates.TemplateResponse(
            "wallet.html",
            {
                "request": request,
                "current_user": current_user,
                "trx_balance": trx_balance,
                "usdt_balance": usdt_balance,
                "wallet_address": getattr(current_user, "tron_address", None),
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth()),
):
    """분석 페이지"""
    try:
        dashboard_service = DashboardService(db)
        balance_service = BalanceService(db)

        # 분석 데이터 조회
        user_overview = await dashboard_service.get_user_overview(current_user.id)
        balance_history = await dashboard_service.get_balance_history(
            current_user.id, days=30
        )
        wallet_stats = await dashboard_service.get_wallet_stats(current_user.id)
        recent_transactions = await dashboard_service.get_recent_transactions(
            current_user.id, limit=20
        )

        # 차트를 위한 데이터 처리
        balance_chart_data = {
            "dates": [bh.date.isoformat() if bh.date else "" for bh in balance_history],
            "trx_values": [
                float(bh.balance) if bh.balance else 0.0 for bh in balance_history
            ],
            "usdt_values": [
                float(bh.balance) if bh.balance else 0.0 for bh in balance_history
            ],
        }

        return templates.TemplateResponse(
            "analytics.html",
            {
                "request": request,
                "current_user": current_user,
                "user_overview": user_overview,
                "balance_history": balance_chart_data,
                "wallet_stats": wallet_stats,
                "recent_transactions": recent_transactions,
            },
        )
    except HTTPException as e:
        if e.status_code == 302:
            return RedirectResponse(url="/auth/login")
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
