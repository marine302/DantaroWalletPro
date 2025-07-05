"""
사용자 관리 관련 API 엔드포인트
"""
from decimal import Decimal
from typing import Optional

from app.core.database import get_db
from app.core.encryption import encrypt_private_key
from app.core.tron import TronService
from app.models.balance import Balance
from app.models.user import User
from app.models.wallet import Wallet
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_current_admin

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


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
            {"user": user, "balances": balances, "wallet": wallet}
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


@router.post("/users/{user_id}/create-wallet")
async def create_user_wallet(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """사용자 지갑 생성"""
    # 사용자 확인
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 기존 지갑 확인
    existing_wallet = await db.execute(
        select(Wallet).filter(Wallet.user_id == user_id)
    )
    if existing_wallet.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Wallet already exists")

    try:
        # TRON 지갑 생성
        tron_service = TronService()
        wallet_data = tron_service.create_wallet()

        # 개인키 암호화
        encrypted_private_key = encrypt_private_key(wallet_data["private_key"])

        # 지갑 정보 저장
        wallet = Wallet(
            user_id=user_id,
            address=wallet_data["address"],
            encrypted_private_key=encrypted_private_key,
            is_active=True,
        )

        db.add(wallet)
        await db.commit()

        return RedirectResponse(url="/admin/users", status_code=302)

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Wallet creation failed: {str(e)}")


@router.post("/users/{user_id}/create-balance")
async def create_user_balance(
    user_id: int,
    asset_symbol: str = Form(...),
    amount: Decimal = Form(...),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """사용자 잔고 생성"""
    # 사용자 확인
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 기존 잔고 확인 (동일한 자산)
    existing_balance = await db.execute(
        select(Balance).filter(
            Balance.user_id == user_id,
            Balance.asset_symbol == asset_symbol
        )
    )
    if existing_balance.scalar_one_or_none():
        raise HTTPException(
            status_code=400, 
            detail=f"Balance for {asset_symbol} already exists"
        )

    try:
        # 잔고 생성
        balance = Balance(
            user_id=user_id,
            asset_symbol=asset_symbol,
            available_balance=amount,
            locked_balance=Decimal("0"),
        )

        db.add(balance)
        await db.commit()

        return RedirectResponse(url="/admin/users", status_code=302)

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Balance creation failed: {str(e)}")
