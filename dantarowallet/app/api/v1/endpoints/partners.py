"""
파트너 관리 API 엔드포인트
파트너 관리자 대시보드에서 파트너 관리 기능을 제공합니다.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_, and_
from decimal import Decimal

from app.core.database import get_sync_db
from app.models.partner import Partner
from app.models.user import User
from app.models.wallet import Wallet
from app.models.transaction import Transaction

router = APIRouter()


@router.get("/partners")
async def get_partners(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(created_at|name|total_volume|last_activity)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_sync_db)
):
    """
    파트너 목록 조회 (페이지네이션, 필터링, 정렬 지원)
    """
    try:
        query = db.query(Partner)
        
        # 검색 필터
        if search:
            query = query.filter(
                or_(
                    Partner.name.ilike(f"%{search}%"),
                    Partner.contact_email.ilike(f"%{search}%"),
                    Partner.api_key.ilike(f"%{search}%")
                )
            )
        
        # 상태 필터
        if status:
            query = query.filter(Partner.status == status)
        
        # 정렬
        if sort_by == "created_at":
            order_column = Partner.created_at
        elif sort_by == "name":
            order_column = Partner.name
        elif sort_by == "total_volume":
            order_column = Partner.total_volume
        else:
            order_column = Partner.last_activity_at
        
        if sort_order == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(order_column)
        
        # 페이지네이션
        partners = query.offset(skip).limit(limit).all()
        
        # 응답 데이터 구성
        result = []
        for partner in partners:
            # 파트너 사용자 수 조회
            user_count = db.query(User).filter(User.partner_id == partner.id).count()
            
            # 파트너 거래 통계 조회
            tx_stats = db.query(
                func.count(Transaction.id),
                func.sum(Transaction.amount)
            ).filter(Transaction.partner_id == partner.id).first()
            
            total_transactions = tx_stats[0] if tx_stats and tx_stats[0] else 0
            total_volume = float(tx_stats[1]) if tx_stats and tx_stats[1] else 0.0
            
            last_activity_value = getattr(partner, 'last_activity_at', None)
            
            result.append({
                "id": partner.id,
                "name": partner.name,
                "contact_email": partner.contact_email,
                "status": partner.status,
                "api_key": partner.api_key,
                "webhook_url": getattr(partner, 'webhook_url', None),
                "fee_rate": float(getattr(partner, 'fee_rate', 0)),
                "total_users": user_count,
                "total_transactions": total_transactions,
                "total_volume": total_volume,
                "last_activity": last_activity_value.isoformat() if last_activity_value is not None else None,
                "created_at": partner.created_at.isoformat(),
                "tier": getattr(partner, 'tier', 'standard')
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/partners/{partner_id}")
async def get_partner_detail(partner_id: int, db: Session = Depends(get_sync_db)):
    """
    파트너 상세 정보 조회
    """
    try:
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="파트너를 찾을 수 없습니다")
        
        # 파트너 사용자 수 조회
        user_count = db.query(User).filter(User.partner_id == partner_id).count()
        
        # 파트너 거래 통계 조회
        tx_stats = db.query(
            func.count(Transaction.id),
            func.sum(Transaction.amount)
        ).filter(Transaction.partner_id == partner_id).first()
        
        total_transactions = tx_stats[0] if tx_stats and tx_stats[0] else 0
        total_volume = float(tx_stats[1]) if tx_stats and tx_stats[1] else 0.0
        
        # 최근 거래 내역
        recent_transactions = db.query(Transaction).filter(
            Transaction.partner_id == partner_id
        ).order_by(desc(Transaction.created_at)).limit(20).all()
        
        # 파트너 사용자 목록
        users = db.query(User).filter(User.partner_id == partner_id).limit(10).all()
        
        return {
            "partner": {
                "id": partner.id,
                "name": partner.name,
                "contact_email": partner.contact_email,
                "status": partner.status,
                "api_key": partner.api_key,
                "webhook_url": getattr(partner, 'webhook_url', None),
                "fee_rate": float(getattr(partner, 'fee_rate', 0)),
                "created_at": partner.created_at.isoformat(),
                "last_activity": (lambda la: la.isoformat() if la else None)(getattr(partner, 'last_activity_at', None)),
                "tier": getattr(partner, 'tier', 'standard'),
                "settings": getattr(partner, 'settings', {})
            },
            "statistics": {
                "total_users": user_count,
                "total_transactions": total_transactions,
                "total_volume": total_volume,
                "average_transaction_size": total_volume / total_transactions if total_transactions > 0 else 0
            },
            "recent_transactions": [
                {
                    "id": tx.id,
                    "type": tx.type,
                    "amount": float(getattr(tx, 'amount', 0)),
                    "currency": tx.currency,
                    "status": tx.status,
                    "created_at": tx.created_at.isoformat(),
                    "from_address": tx.from_address,
                    "to_address": tx.to_address,
                    "tx_hash": getattr(tx, 'tx_hash', None)
                } for tx in recent_transactions
            ],
            "users": [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "status": user.status,
                    "created_at": user.created_at.isoformat(),
                    "last_activity": user.last_activity_at.isoformat() if user.last_activity_at else None
                } for user in users
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/partners/{partner_id}/status")
async def update_partner_status(
    partner_id: int,
    status: str,
    db: Session = Depends(get_sync_db)
):
    """
    파트너 상태 업데이트
    """
    try:
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="파트너를 찾을 수 없습니다")
        
        valid_statuses = ["active", "inactive", "suspended", "pending"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail="유효하지 않은 상태입니다")
        
        if hasattr(partner, 'status'):
            setattr(partner, 'status', status)
        db.commit()
        
        return {
            "message": "파트너 상태가 업데이트되었습니다",
            "partner_id": partner_id,
            "new_status": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/partners/{partner_id}/fee-rate")
async def update_partner_fee_rate(
    partner_id: int,
    fee_rate: float,
    db: Session = Depends(get_sync_db)
):
    """
    파트너 수수료율 업데이트
    """
    try:
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="파트너를 찾을 수 없습니다")
        
        if fee_rate < 0 or fee_rate > 1:
            raise HTTPException(status_code=400, detail="수수료율은 0과 1 사이여야 합니다")
        
        # 수수료율 필드가 있는지 확인
        if hasattr(partner, 'fee_rate'):
            partner.fee_rate = fee_rate
        else:
            # 필드가 없으면 설정 JSON에 저장
            settings = getattr(partner, 'settings', {})
            settings['fee_rate'] = fee_rate
            if hasattr(partner, 'settings'):
                setattr(partner, 'settings', settings)
        
        db.commit()
        
        return {
            "message": "파트너 수수료율이 업데이트되었습니다",
            "partner_id": partner_id,
            "new_fee_rate": fee_rate
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/partners/analytics/revenue")
async def get_partner_revenue_analytics(
    partner_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_sync_db)
):
    """
    파트너 수익 분석 조회
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = db.query(
            func.DATE(Transaction.created_at).label('date'),
            func.count(Transaction.id).label('transaction_count'),
            func.sum(Transaction.amount).label('total_volume'),
            func.sum(Transaction.fee).label('total_fee')
        ).filter(
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        )
        
        if partner_id:
            query = query.filter(Transaction.partner_id == partner_id)
        
        daily_revenue = query.group_by(func.DATE(Transaction.created_at)).all()
        
        result = []
        for row in daily_revenue:
            result.append({
                "date": row.date.strftime("%Y-%m-%d"),
                "transaction_count": row.transaction_count,
                "total_volume": float(row.total_volume) if row.total_volume else 0,
                "total_fee": float(row.total_fee) if row.total_fee else 0
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/partners/top-performers")
async def get_top_performing_partners(
    limit: int = Query(10, ge=1, le=50),
    metric: str = Query("volume", regex="^(volume|transactions|revenue)$"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_sync_db)
):
    """
    상위 성과 파트너 조회
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        if metric == "volume":
            order_column = func.sum(Transaction.amount)
        elif metric == "transactions":
            order_column = func.count(Transaction.id)
        else:  # revenue
            order_column = func.sum(Transaction.fee)
        
        top_partners = db.query(
            Partner.id,
            Partner.name,
            Partner.contact_email,
            Partner.status,
            func.count(Transaction.id).label('transaction_count'),
            func.sum(Transaction.amount).label('total_volume'),
            func.sum(Transaction.fee).label('total_revenue')
        ).join(
            Transaction, Transaction.partner_id == Partner.id
        ).filter(
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        ).group_by(Partner.id).order_by(desc(order_column)).limit(limit).all()
        
        result = []
        for partner in top_partners:
            result.append({
                "id": partner.id,
                "name": partner.name,
                "contact_email": partner.contact_email,
                "status": partner.status,
                "transaction_count": partner.transaction_count,
                "total_volume": float(partner.total_volume) if partner.total_volume else 0,
                "total_revenue": float(partner.total_revenue) if partner.total_revenue else 0
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
