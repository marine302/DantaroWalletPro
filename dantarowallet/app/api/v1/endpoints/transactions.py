"""
거래 관리 API 엔드포인트
파트너 관리자 대시보드에서 거래 관리 기능을 제공합니다.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_, and_

from app.core.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.models.partner import Partner
from app.models.wallet import Wallet

router = APIRouter()


@router.get("/transactions")
async def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
    partner_id: Optional[int] = None,
    user_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort_by: str = Query("created_at", regex="^(created_at|amount|status)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """
    거래 목록 조회 (페이지네이션, 필터링, 정렬 지원)
    """
    try:
        query = db.query(Transaction)
        
        # 검색 필터
        if search:
            query = query.filter(
                or_(
                    Transaction.tx_hash.ilike(f"%{search}%"),
                    Transaction.from_address.ilike(f"%{search}%"),
                    Transaction.to_address.ilike(f"%{search}%")
                )
            )
        
        # 상태 필터
        if status:
            query = query.filter(Transaction.status == status)
        
        # 타입 필터
        if type:
            query = query.filter(Transaction.type == type)
        
        # 파트너 필터
        if partner_id:
            query = query.filter(Transaction.partner_id == partner_id)
        
        # 사용자 필터
        if user_id:
            query = query.filter(Transaction.user_id == user_id)
        
        # 날짜 범위 필터
        if date_from:
            query = query.filter(Transaction.created_at >= date_from)
        if date_to:
            query = query.filter(Transaction.created_at <= date_to)
        
        # 정렬
        if sort_by == "created_at":
            order_column = Transaction.created_at
        elif sort_by == "amount":
            order_column = Transaction.amount
        else:
            order_column = Transaction.status
        
        if sort_order == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(order_column)
        
        # 페이지네이션
        transactions = query.offset(skip).limit(limit).all()
        
        # 응답 데이터 구성
        result = []
        for tx in transactions:
            # 사용자 정보 조회
            user_id = getattr(tx, 'user_id', None)
            user = db.query(User).filter(User.id == user_id).first() if user_id else None
            
            # 파트너 정보 조회
            partner = db.query(Partner).filter(Partner.id == tx.partner_id).first() if tx.partner_id else None
            
            result.append({
                "id": tx.id,
                "tx_hash": getattr(tx, 'tx_hash', None),
                "type": tx.type,
                "amount": float(getattr(tx, 'amount', 0)),
                "currency": tx.currency,
                "status": tx.status,
                "from_address": tx.from_address,
                "to_address": tx.to_address,
                "fee": float(getattr(tx, 'fee', 0)),
                "energy_used": getattr(tx, 'energy_used', 0),
                "bandwidth_used": getattr(tx, 'bandwidth_used', 0),
                "created_at": tx.created_at.isoformat(),
                "updated_at": (lambda ua: ua.isoformat() if ua else None)(getattr(tx, 'updated_at', None)),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                } if user else None,
                "partner": {
                    "id": partner.id,
                    "name": partner.name,
                    "contact_email": partner.contact_email
                } if partner else None
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/{transaction_id}")
async def get_transaction_detail(transaction_id: int, db: Session = Depends(get_db)):
    """
    거래 상세 정보 조회
    """
    try:
        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not tx:
            raise HTTPException(status_code=404, detail="거래를 찾을 수 없습니다")
        
        # 사용자 정보 조회
        user_id = getattr(tx, 'user_id', None)
        user = db.query(User).filter(User.id == user_id).first() if user_id else None
        
        # 파트너 정보 조회
        partner = db.query(Partner).filter(Partner.id == tx.partner_id).first() if tx.partner_id else None
        
        return {
            "transaction": {
                "id": tx.id,
                "tx_hash": getattr(tx, 'tx_hash', None),
                "type": tx.type,
                "amount": float(getattr(tx, 'amount', 0)),
                "currency": tx.currency,
                "status": tx.status,
                "from_address": tx.from_address,
                "to_address": tx.to_address,
                "fee": float(getattr(tx, 'fee', 0)),
                "energy_used": getattr(tx, 'energy_used', 0),
                "bandwidth_used": getattr(tx, 'bandwidth_used', 0),
                "created_at": tx.created_at.isoformat(),
                "updated_at": (lambda ua: ua.isoformat() if ua else None)(getattr(tx, 'updated_at', None)),
                "confirmation_count": getattr(tx, 'confirmation_count', 0),
                "block_number": getattr(tx, 'block_number', None),
                "gas_limit": getattr(tx, 'gas_limit', None),
                "gas_used": getattr(tx, 'gas_used', None)
            },
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "status": user.status,
                "created_at": user.created_at.isoformat()
            } if user else None,
            "partner": {
                "id": partner.id,
                "name": partner.name,
                "contact_email": partner.contact_email,
                "status": partner.status,
                "created_at": partner.created_at.isoformat()
            } if partner else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/analytics/daily")
async def get_daily_transaction_analytics(
    days: int = Query(30, ge=1, le=365),
    partner_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    일별 거래 분석 데이터 조회
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = db.query(
            func.DATE(Transaction.created_at).label('date'),
            func.count(Transaction.id).label('transaction_count'),
            func.sum(Transaction.amount).label('total_volume'),
            func.sum(Transaction.fee).label('total_fee'),
            func.avg(Transaction.amount).label('avg_amount')
        ).filter(
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        )
        
        if partner_id:
            query = query.filter(Transaction.partner_id == partner_id)
        
        daily_analytics = query.group_by(func.DATE(Transaction.created_at)).all()
        
        result = []
        for row in daily_analytics:
            result.append({
                "date": row.date.strftime("%Y-%m-%d"),
                "transaction_count": row.transaction_count,
                "total_volume": float(row.total_volume) if row.total_volume else 0,
                "total_fee": float(row.total_fee) if row.total_fee else 0,
                "avg_amount": float(row.avg_amount) if row.avg_amount else 0
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/analytics/hourly")
async def get_hourly_transaction_analytics(
    hours: int = Query(24, ge=1, le=168),  # 최대 1주일
    partner_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    시간별 거래 분석 데이터 조회
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours)
        
        query = db.query(
            func.DATE_FORMAT(Transaction.created_at, '%Y-%m-%d %H:00:00').label('hour'),
            func.count(Transaction.id).label('transaction_count'),
            func.sum(Transaction.amount).label('total_volume'),
            func.sum(Transaction.fee).label('total_fee')
        ).filter(
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        )
        
        if partner_id:
            query = query.filter(Transaction.partner_id == partner_id)
        
        hourly_analytics = query.group_by(
            func.DATE_FORMAT(Transaction.created_at, '%Y-%m-%d %H:00:00')
        ).all()
        
        result = []
        for row in hourly_analytics:
            result.append({
                "hour": row.hour,
                "transaction_count": row.transaction_count,
                "total_volume": float(row.total_volume) if row.total_volume else 0,
                "total_fee": float(row.total_fee) if row.total_fee else 0
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/status/summary")
async def get_transaction_status_summary(
    days: int = Query(7, ge=1, le=365),
    partner_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    거래 상태별 요약 통계 조회
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = db.query(
            Transaction.status,
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total_amount'),
            func.avg(Transaction.amount).label('avg_amount')
        ).filter(
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        )
        
        if partner_id:
            query = query.filter(Transaction.partner_id == partner_id)
        
        status_summary = query.group_by(Transaction.status).all()
        
        result = []
        for row in status_summary:
            result.append({
                "status": row.status,
                "count": row.count,
                "total_amount": float(row.total_amount) if row.total_amount else 0,
                "avg_amount": float(row.avg_amount) if row.avg_amount else 0
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/failed")
async def get_failed_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    실패한 거래 목록 조회
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        failed_transactions = db.query(Transaction).filter(
            Transaction.status == "failed",
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        ).order_by(desc(Transaction.created_at)).offset(skip).limit(limit).all()
        
        result = []
        for tx in failed_transactions:
            # 사용자 정보 조회
            user_id = getattr(tx, 'user_id', None)
            user = db.query(User).filter(User.id == user_id).first() if user_id else None
            
            # 파트너 정보 조회
            partner = db.query(Partner).filter(Partner.id == tx.partner_id).first() if tx.partner_id else None
            
            result.append({
                "id": tx.id,
                "tx_hash": getattr(tx, 'tx_hash', None),
                "type": tx.type,
                "amount": float(getattr(tx, 'amount', 0)),
                "currency": tx.currency,
                "from_address": tx.from_address,
                "to_address": tx.to_address,
                "created_at": tx.created_at.isoformat(),
                "error_message": getattr(tx, 'error_message', None),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                } if user else None,
                "partner": {
                    "id": partner.id,
                    "name": partner.name
                } if partner else None
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/transactions/{transaction_id}/retry")
async def retry_failed_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """
    실패한 거래 재시도
    """
    try:
        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not tx:
            raise HTTPException(status_code=404, detail="거래를 찾을 수 없습니다")
        
        tx_status = getattr(tx, 'status', '')
        if tx_status != "failed":
            raise HTTPException(status_code=400, detail="실패한 거래만 재시도할 수 있습니다")
        
        # 거래 상태를 pending으로 변경
        if hasattr(tx, 'status'):
            setattr(tx, 'status', "pending")
        if hasattr(tx, 'updated_at'):
            setattr(tx, 'updated_at', datetime.now())
        db.commit()
        
        # 여기서 실제 거래 재시도 로직을 구현해야 함
        # 예: 백그라운드 작업 큐에 추가
        
        return {
            "message": "거래 재시도가 요청되었습니다",
            "transaction_id": transaction_id,
            "new_status": "pending"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
