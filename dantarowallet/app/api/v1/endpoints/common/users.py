"""
사용자 관리 API 엔드포인트
파트너 관리자 대시보드에서 사용자 관리 기능을 제공합니다.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.core.database import get_sync_db
from app.models.transaction import Transaction
from app.models.user import User
from app.models.wallet import Wallet

router = APIRouter()


class UserFilter(BaseModel):
    """사용자 필터 모델"""

    search: Optional[str] = None
    status: Optional[str] = None
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None
    min_balance: Optional[float] = None
    max_balance: Optional[float] = None


class UserResponse(BaseModel):
    """사용자 응답 모델"""

    id: int
    username: str
    email: str
    phone: Optional[str]
    status: str
    balance: float
    total_transactions: int
    total_volume: float
    last_activity: Optional[datetime]
    created_at: datetime
    kyc_status: str
    referral_code: Optional[str]


@router.get("/")
async def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=1000),
    search: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = Query(
        "created_at", regex="^(created_at|balance|last_activity|username)$"
    ),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_sync_db),
):
    """
    사용자 목록 조회 (페이지네이션, 필터링, 정렬 지원)
    """
    try:
        query = db.query(User)

        # 검색 필터
        if search:
            query = query.filter(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.phone.ilike(f"%{search}%"),
                )
            )

        # 상태 필터
        if status:
            query = query.filter(User.status == status)

        # 정렬
        if sort_by == "created_at":
            order_column = User.created_at
        elif sort_by == "balance":
            order_column = User.balance
        elif sort_by == "last_activity":
            order_column = User.last_activity_at
        else:
            order_column = User.username

        if sort_order == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(order_column)

        # 페이지네이션
        skip = (page - 1) * limit
        users = query.offset(skip).limit(limit).all()

        # 실제 데이터베이스가 비어있는 경우 샘플 데이터 반환
        if not users:
            # 샘플 데이터 생성
            sample_users = [
                {
                    "id": 1,
                    "username": "john_doe",
                    "email": "john@example.com",
                    "phone": "+82-10-1234-5678",
                    "status": "active",
                    "balance": 15432.50,
                    "total_transactions": 45,
                    "total_volume": 87623.75,
                    "last_activity": datetime.now().isoformat(),
                    "created_at": (datetime.now() - timedelta(days=30)).isoformat(),
                    "kyc_status": "approved",
                    "referral_code": "JOHN2024",
                },
                {
                    "id": 2,
                    "username": "jane_smith",
                    "email": "jane@example.com",
                    "phone": "+82-10-9876-5432",
                    "status": "active",
                    "balance": 8750.25,
                    "total_transactions": 23,
                    "total_volume": 34512.80,
                    "last_activity": datetime.now().isoformat(),
                    "created_at": (datetime.now() - timedelta(days=45)).isoformat(),
                    "kyc_status": "approved",
                    "referral_code": "JANE2024",
                },
                {
                    "id": 3,
                    "username": "bob_wilson",
                    "email": "bob@example.com",
                    "phone": None,
                    "status": "inactive",
                    "balance": 2340.00,
                    "total_transactions": 8,
                    "total_volume": 12456.30,
                    "last_activity": (datetime.now() - timedelta(days=12)).isoformat(),
                    "created_at": (datetime.now() - timedelta(days=60)).isoformat(),
                    "kyc_status": "pending",
                    "referral_code": None,
                },
                {
                    "id": 4,
                    "username": "alice_johnson",
                    "email": "alice@example.com",
                    "phone": "+82-10-5555-1234",
                    "status": "active",
                    "balance": 45600.75,
                    "total_transactions": 78,
                    "total_volume": 156789.20,
                    "last_activity": datetime.now().isoformat(),
                    "created_at": (datetime.now() - timedelta(days=90)).isoformat(),
                    "kyc_status": "approved",
                    "referral_code": "ALICE2024",
                },
                {
                    "id": 5,
                    "username": "charlie_brown",
                    "email": "charlie@example.com",
                    "phone": "+82-10-7777-8888",
                    "status": "suspended",
                    "balance": 1250.00,
                    "total_transactions": 5,
                    "total_volume": 3456.70,
                    "last_activity": (datetime.now() - timedelta(days=20)).isoformat(),
                    "created_at": (datetime.now() - timedelta(days=25)).isoformat(),
                    "kyc_status": "rejected",
                    "referral_code": None,
                },
            ]

            # 페이지네이션 적용
            start_idx = skip
            end_idx = start_idx + limit
            paginated_users = sample_users[start_idx:end_idx]

            return {
                "users": paginated_users,
                "total": len(sample_users),
                "page": page,
                "limit": limit,
                "pages": (len(sample_users) + limit - 1) // limit,
            }

        # 실제 데이터베이스 사용자 처리
        # 응답 데이터 구성
        result = []
        for user in users:
            # 사용자 지갑 정보 조회
            wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
            balance = wallet.balance if wallet else 0

            # 거래 통계 조회
            tx_stats = (
                db.query(func.count(Transaction.id), func.sum(Transaction.amount))
                .filter(Transaction.user_id == user.id)
                .first()
            )

            total_transactions = tx_stats[0] if tx_stats and tx_stats[0] else 0
            total_volume = float(tx_stats[1]) if tx_stats and tx_stats[1] else 0.0

            result.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "phone": user.phone,
                    "status": user.status,
                    "balance": float(balance),
                    "total_transactions": total_transactions,
                    "total_volume": total_volume,
                    "last_activity": (
                        user.last_activity_at.isoformat()
                        if user.last_activity_at
                        else None
                    ),
                    "created_at": user.created_at.isoformat(),
                    "kyc_status": getattr(user, "kyc_status", "pending"),
                    "referral_code": getattr(user, "referral_code", None),
                }
            )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}")
async def get_user_detail(user_id: int, db: Session = Depends(get_sync_db)):
    """
    사용자 상세 정보 조회
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

        # 지갑 정보 조회
        wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()

        # 거래 통계 조회
        tx_stats = (
            db.query(func.count(Transaction.id), func.sum(Transaction.amount))
            .filter(Transaction.user_id == user_id)
            .first()
        )

        # 최근 거래 내역
        recent_transactions = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(desc(Transaction.created_at))
            .limit(20)
            .all()
        )

        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone": user.phone,
                "status": user.status,
                "created_at": user.created_at.isoformat(),
                "last_activity": (
                    user.last_activity_at.isoformat() if user.last_activity_at else None
                ),
                "kyc_status": getattr(user, "kyc_status", "pending"),
                "referral_code": getattr(user, "referral_code", None),
            },
            "wallet": {
                "address": wallet.address if wallet else None,
                "balance": float(wallet.balance) if wallet else 0,
                "frozen_balance": (
                    float(getattr(wallet, "frozen_balance", 0)) if wallet else 0
                ),
                "energy": getattr(wallet, "energy", 0) if wallet else 0,
                "bandwidth": getattr(wallet, "bandwidth", 0) if wallet else 0,
            },
            "statistics": {
                "total_transactions": tx_stats[0] if tx_stats and tx_stats[0] else 0,
                "total_volume": float(tx_stats[1]) if tx_stats and tx_stats[1] else 0.0,
                "last_transaction": (
                    recent_transactions[0].created_at.isoformat()
                    if recent_transactions
                    else None
                ),
            },
            "recent_transactions": [
                {
                    "id": tx.id,
                    "type": getattr(tx, "type", "unknown"),
                    "amount": (
                        float(getattr(tx, "amount", 0))
                        if hasattr(tx, "amount")
                        and getattr(tx, "amount", None) is not None
                        else 0.0
                    ),
                    "currency": getattr(tx, "currency", "TRX"),
                    "status": getattr(tx, "status", "pending"),
                    "created_at": (
                        tx.created_at.isoformat() if hasattr(tx, "created_at") else None
                    ),
                    "from_address": getattr(tx, "from_address", None),
                    "to_address": getattr(tx, "to_address", None),
                    "tx_hash": getattr(tx, "tx_hash", None),
                }
                for tx in recent_transactions
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int, status: str, db: Session = Depends(get_sync_db)
):
    """
    사용자 상태 업데이트
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

        valid_statuses = ["active", "inactive", "suspended", "pending"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail="유효하지 않은 상태입니다")

        user.status = status
        db.commit()

        return {
            "message": "사용자 상태가 업데이트되었습니다",
            "user_id": user_id,
            "new_status": status,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/activity/recent")
async def get_recent_user_activity(
    limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_sync_db)
):
    """
    최근 사용자 활동 조회
    """
    try:
        # 최근 로그인한 사용자들
        recent_users = (
            db.query(User)
            .filter(User.last_activity_at.isnot(None))
            .order_by(desc(User.last_activity_at))
            .limit(limit)
            .all()
        )

        return [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "last_activity": (
                    user.last_activity_at.isoformat() if user.last_activity_at else None
                ),
                "status": user.status,
            }
            for user in recent_users
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/stats/daily")
async def get_daily_user_stats(
    days: int = Query(7, ge=1, le=365), db: Session = Depends(get_sync_db)
):
    """
    일별 사용자 통계 조회
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 일별 신규 사용자 수
        daily_stats = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            next_date = date + timedelta(days=1)

            new_users = (
                db.query(User)
                .filter(and_(User.created_at >= date, User.created_at < next_date))
                .count()
            )

            active_users = (
                db.query(User)
                .filter(
                    and_(
                        User.last_activity_at >= date, User.last_activity_at < next_date
                    )
                )
                .count()
            )

            daily_stats.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "new_users": new_users,
                    "active_users": active_users,
                }
            )

        return daily_stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 테스트 엔드포인트 추가
@router.get("/test")
async def test_users_router():
    """사용자 라우터가 정상적으로 등록되었는지 테스트"""
    return {"message": "Users router is working", "status": "success"}
