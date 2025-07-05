"""
웹 UI 라우터 - 사용자 인터페이스 제공
"""
import json
from datetime import datetime, timedelta

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.balance import Balance
from app.models.transaction import Transaction
from app.models.user import User
from app.models.wallet import Wallet
from app.services.balance_service import BalanceService
from app.services.wallet_service import WalletService
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """홈페이지"""
    return templates.TemplateResponse("home.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """로그인 페이지"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """회원가입 페이지"""
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """사용자 대시보드"""
    try:
        # 사용자 잔고 조회
        balance_service = BalanceService(db)
        user_id = current_user.id  # type: ignore
        balance = await balance_service.get_balance(user_id)  # type: ignore

        # 사용자 지갑 조회
        wallet_service = WalletService(db)
        wallet = await wallet_service.get_wallet(user_id)  # type: ignore

        # 최근 거래 내역 조회 (최근 5개)
        recent_transactions = await get_recent_transactions(db, user_id, limit=5)  # type: ignore

        # 잔고 히스토리 (차트용 데이터)
        balance_history = await get_balance_history(db, user_id)  # type: ignore

        # TRX 가격 (임시로 고정값 사용)
        trx_price = 0.1  # 실제로는 외부 API에서 가져와야 함

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "current_user": current_user,
                "balance": balance,
                "wallet_address": wallet.address if wallet else None,
                "recent_transactions": recent_transactions,
                "balance_history": balance_history,
                "trx_price": trx_price,
            },
        )

    except Exception as e:
        # 오류 발생 시 기본값으로 대시보드 표시
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "current_user": current_user,
                "balance": {"trx_balance": 0, "usdt_balance": 0},
                "wallet_address": None,
                "recent_transactions": [],
                "balance_history": {"dates": [], "trx_values": [], "usdt_values": []},
                "trx_price": 0.1,
            },
        )


@router.get("/wallet", response_class=HTMLResponse)
async def wallet_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """지갑 관리 페이지"""
    try:
        wallet_service = WalletService(db)
        wallet = await wallet_service.get_wallet(current_user.id)  # type: ignore

        # 지갑 잔고 조회
        wallet_balance = None
        if wallet:
            from app.core.tron import TronService

            tron_service = TronService()
            wallet_balance = await tron_service.get_balance(wallet.address)  # type: ignore

        return templates.TemplateResponse(
            "wallet.html",
            {
                "request": request,
                "current_user": current_user,
                "wallet": wallet,
                "wallet_balance": wallet_balance,
            },
        )

    except Exception as e:
        return templates.TemplateResponse(
            "wallet.html",
            {
                "request": request,
                "current_user": current_user,
                "wallet": None,
                "wallet_balance": None,
                "error": str(e),
            },
        )


@router.get("/transactions", response_class=HTMLResponse)
async def transactions_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """거래 내역 페이지"""
    try:
        # 거래 내역 조회
        transactions = await get_user_transactions(db, current_user.id)  # type: ignore

        return templates.TemplateResponse(
            "transactions.html",
            {
                "request": request,
                "current_user": current_user,
                "transactions": transactions,
            },
        )

    except Exception as e:
        return templates.TemplateResponse(
            "transactions.html",
            {
                "request": request,
                "current_user": current_user,
                "transactions": [],
                "error": str(e),
            },
        )


@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """분석 페이지"""
    try:
        # 사용자 거래 통계
        analytics_data = await get_user_analytics(db, current_user.id)  # type: ignore

        return templates.TemplateResponse(
            "analytics.html",
            {
                "request": request,
                "current_user": current_user,
                "analytics": analytics_data,
            },
        )

    except Exception as e:
        return templates.TemplateResponse(
            "analytics.html",
            {
                "request": request,
                "current_user": current_user,
                "analytics": {},
                "error": str(e),
            },
        )


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request, current_user: User = Depends(get_current_user)
):
    """설정 페이지"""
    return templates.TemplateResponse(
        "settings.html", {"request": request, "current_user": current_user}
    )


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request, current_user: User = Depends(get_current_user)
):
    """프로필 페이지"""
    return templates.TemplateResponse(
        "profile.html", {"request": request, "current_user": current_user}
    )


# 헬퍼 함수들


async def get_recent_transactions(db: AsyncSession, user_id: int, limit: int = 10):
    """최근 거래 내역 조회"""
    try:
        from sqlalchemy import desc, select

        query = (
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(desc(Transaction.created_at))
            .limit(limit)
        )

        result = await db.execute(query)
        transactions = result.scalars().all()

        return transactions
    except Exception as e:
        print(f"최근 거래 조회 오류: {e}")
        return []


async def get_balance_history(db: AsyncSession, user_id: int, days: int = 7):
    """잔고 히스토리 조회 (차트용)"""
    try:
        # 임시로 더미 데이터 생성
        from datetime import date, timedelta

        dates = []
        trx_values = []
        usdt_values = []

        for i in range(days):
            target_date = date.today() - timedelta(days=days - 1 - i)
            dates.append(target_date.strftime("%m-%d"))
            # 임시 데이터 (실제로는 DB에서 조회)
            trx_values.append(100 + i * 10)
            usdt_values.append(500 + i * 50)

        return {
            "dates": json.dumps(dates),
            "trx_values": json.dumps(trx_values),
            "usdt_values": json.dumps(usdt_values),
        }
    except Exception as e:
        print(f"잔고 히스토리 조회 오류: {e}")
        return {
            "dates": json.dumps([]),
            "trx_values": json.dumps([]),
            "usdt_values": json.dumps([]),
        }


async def get_user_transactions(db: AsyncSession, user_id: int, limit: int = 50):
    """사용자 거래 내역 조회"""
    try:
        from sqlalchemy import desc, select

        query = (
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(desc(Transaction.created_at))
            .limit(limit)
        )

        result = await db.execute(query)
        transactions = result.scalars().all()

        return transactions
    except Exception as e:
        print(f"거래 내역 조회 오류: {e}")
        return []


async def get_user_analytics(db: AsyncSession, user_id: int):
    """사용자 분석 데이터 조회"""
    try:
        from sqlalchemy import func, select

        # 기본 통계
        total_transactions = await db.execute(
            select(func.count(Transaction.id)).where(Transaction.user_id == user_id)
        )
        total_count = total_transactions.scalar() or 0

        # 입금 총액
        total_deposits = await db.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user_id,
                Transaction.transaction_type == "deposit",
            )
        )
        deposit_amount = total_deposits.scalar() or 0

        # 출금 총액
        total_withdrawals = await db.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user_id,
                Transaction.transaction_type == "withdrawal",
            )
        )
        withdrawal_amount = total_withdrawals.scalar() or 0

        return {
            "total_transactions": total_count,
            "total_deposits": float(deposit_amount),
            "total_withdrawals": float(withdrawal_amount),
            "net_amount": float(deposit_amount - withdrawal_amount),
        }
    except Exception as e:
        print(f"분석 데이터 조회 오류: {e}")
        return {
            "total_transactions": 0,
            "total_deposits": 0,
            "total_withdrawals": 0,
            "net_amount": 0,
        }
