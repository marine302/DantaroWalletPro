"""
에너지 관리 API 엔드포인트
파트너 관리자 대시보드에서 에너지 풀 관리 기능을 제공합니다.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_, and_
from pydantic import BaseModel

from app.core.database import get_sync_db
from app.models.energy_pool import EnergyPoolModel, EnergyUsageLog, EnergyPriceHistory
from app.models.partner import Partner
from app.models.transaction import Transaction

router = APIRouter()


class EnergyPoolCreateRequest(BaseModel):
    """에너지 풀 생성 요청 모델"""
    pool_name: str
    owner_address: str
    frozen_trx: float
    total_energy: int
    low_threshold: Optional[float] = 20.0
    critical_threshold: Optional[float] = 10.0


class EnergyPoolUpdateRequest(BaseModel):
    """에너지 풀 업데이트 요청 모델"""
    pool_name: Optional[str] = None
    frozen_trx: Optional[float] = None
    total_energy: Optional[int] = None
    low_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    status: Optional[str] = None


@router.get("/energy/pools")
async def get_energy_pools(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(created_at|total_energy|available_energy|usage_rate)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_sync_db)
):
    """
    에너지 풀 목록 조회
    """
    try:
        query = db.query(EnergyPoolModel)
        
        # 상태 필터
        if status:
            query = query.filter(EnergyPoolModel.status == status)
        
        # 정렬
        if sort_by == "created_at":
            order_column = EnergyPoolModel.created_at
        elif sort_by == "total_energy":
            order_column = EnergyPoolModel.total_energy
        elif sort_by == "available_energy":
            order_column = EnergyPoolModel.available_energy
        else:
            order_column = EnergyPoolModel.created_at
        
        if sort_order == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(order_column)
        
        # 페이지네이션
        pools = query.offset(skip).limit(limit).all()
        
        # 응답 데이터 구성
        result = []
        for pool in pools:
            # 사용률 계산
            usage_rate = 0.0
            total_energy = getattr(pool, 'total_energy', 0) or 0
            available_energy = getattr(pool, 'available_energy', 0) or 0
            if total_energy > 0:
                usage_rate = round(((total_energy - available_energy) / total_energy) * 100, 2)
            
            # 최근 사용 로그
            recent_usage = db.query(EnergyUsageLog).filter(
                EnergyUsageLog.pool_id == pool.id
            ).order_by(desc(EnergyUsageLog.used_at)).limit(5).all()
            
            frozen_trx_value = getattr(pool, 'frozen_trx', 0)
            frozen_trx = float(frozen_trx_value) if frozen_trx_value is not None else 0.0
            
            result.append({
                "id": pool.id,
                "pool_name": pool.pool_name,
                "owner_address": pool.owner_address,
                "frozen_trx": frozen_trx,
                "total_energy": total_energy,
                "available_energy": available_energy,
                "used_energy": getattr(pool, 'used_energy', 0) or 0,
                "usage_rate": usage_rate,
                "status": pool.status,
                "low_threshold": float(getattr(pool, 'low_threshold', 20.0)),
                "critical_threshold": float(getattr(pool, 'critical_threshold', 10.0)),
                "created_at": pool.created_at.isoformat(),
                "last_updated": pool.updated_at.isoformat() if pool.updated_at else None,
                "recent_usage_count": len(recent_usage)
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/energy/pools/{pool_id}")
async def get_energy_pool_detail(pool_id: int, db: Session = Depends(get_sync_db)):
    """
    에너지 풀 상세 정보 조회
    """
    try:
        pool = db.query(EnergyPoolModel).filter(EnergyPoolModel.id == pool_id).first()
        if not pool:
            raise HTTPException(status_code=404, detail="에너지 풀을 찾을 수 없습니다")
        
        # 사용률 계산
        usage_rate = 0
        if pool.total_energy > 0:
            usage_rate = round(((pool.total_energy - pool.available_energy) / pool.total_energy) * 100, 2)
        
        # 최근 사용 로그 (최근 50개)
        usage_logs = db.query(EnergyUsageLog).filter(
            EnergyUsageLog.pool_id == pool_id
        ).order_by(desc(EnergyUsageLog.created_at)).limit(50).all()
        
        # 일별 사용량 통계 (최근 30일)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        daily_usage = []
        for i in range(30):
            date = start_date + timedelta(days=i)
            next_date = date + timedelta(days=1)
            
            day_usage = db.query(
                func.sum(EnergyUsageLog.energy_used),
                func.count(EnergyUsageLog.id)
            ).filter(
                EnergyUsageLog.pool_id == pool_id,
                EnergyUsageLog.created_at >= date,
                EnergyUsageLog.created_at < next_date
            ).first()
            
            daily_usage.append({
                "date": date.strftime("%Y-%m-%d"),
                "energy_used": int(day_usage[0]) if day_usage and day_usage[0] else 0,
                "transaction_count": day_usage[1] if day_usage and day_usage[1] else 0
            })
        
        # 가격 히스토리 (최근 20개)
        price_history = db.query(EnergyPriceHistory).filter(
            EnergyPriceHistory.pool_id == pool_id
        ).order_by(desc(EnergyPriceHistory.recorded_at)).limit(20).all()
        
        return {
            "pool": {
                "id": pool.id,
                "pool_name": pool.pool_name,
                "owner_address": pool.owner_address,
                "frozen_trx": float(pool.frozen_trx),
                "total_energy": pool.total_energy,
                "available_energy": pool.available_energy,
                "used_energy": pool.used_energy,
                "usage_rate": usage_rate,
                "status": pool.status,
                "low_threshold": float(getattr(pool, 'low_threshold', 20.0)),
                "critical_threshold": float(getattr(pool, 'critical_threshold', 10.0)),
                "created_at": pool.created_at.isoformat(),
                "last_updated": pool.updated_at.isoformat() if pool.updated_at else None
            },
            "daily_usage": daily_usage,
            "recent_usage_logs": [
                {
                    "id": log.id,
                    "transaction_hash": getattr(log, 'transaction_hash', None),
                    "energy_used": log.energy_used,
                    "partner_id": getattr(log, 'partner_id', None),
                    "created_at": log.created_at.isoformat(),
                    "operation_type": getattr(log, 'operation_type', 'transfer')
                } for log in usage_logs
            ],
            "price_history": [
                {
                    "price_per_energy": float(price.price_per_energy),
                    "recorded_at": price.recorded_at.isoformat(),
                    "market_rate": float(getattr(price, 'market_rate', 0))
                } for price in price_history
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/energy/pools")
async def create_energy_pool(
    pool_data: EnergyPoolCreateRequest,
    db: Session = Depends(get_sync_db)
):
    """
    새 에너지 풀 생성
    """
    try:
        # 풀 이름 중복 확인
        existing_pool = db.query(EnergyPoolModel).filter(
            EnergyPoolModel.pool_name == pool_data.pool_name
        ).first()
        if existing_pool:
            raise HTTPException(status_code=400, detail="이미 존재하는 풀 이름입니다")
        
        # 새 에너지 풀 생성
        new_pool = EnergyPoolModel(
            pool_name=pool_data.pool_name,
            owner_address=pool_data.owner_address,
            frozen_trx=pool_data.frozen_trx,
            total_energy=pool_data.total_energy,
            available_energy=pool_data.total_energy,  # 초기에는 모든 에너지가 사용 가능
            used_energy=0,
            status="active"
        )
        
        # 선택적 필드 설정
        if hasattr(new_pool, 'low_threshold'):
            setattr(new_pool, 'low_threshold', pool_data.low_threshold)
        if hasattr(new_pool, 'critical_threshold'):
            setattr(new_pool, 'critical_threshold', pool_data.critical_threshold)
        
        db.add(new_pool)
        db.commit()
        db.refresh(new_pool)
        
        return {
            "message": "에너지 풀이 성공적으로 생성되었습니다",
            "pool_id": new_pool.id,
            "pool_name": new_pool.pool_name,
            "total_energy": new_pool.total_energy
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/energy/pools/{pool_id}")
async def update_energy_pool(
    pool_id: int,
    pool_data: EnergyPoolUpdateRequest,
    db: Session = Depends(get_sync_db)
):
    """
    에너지 풀 정보 업데이트
    """
    try:
        pool = db.query(EnergyPoolModel).filter(EnergyPoolModel.id == pool_id).first()
        if not pool:
            raise HTTPException(status_code=404, detail="에너지 풀을 찾을 수 없습니다")
        
        # 업데이트할 필드들
        update_fields = {}
        if pool_data.pool_name:
            update_fields['pool_name'] = pool_data.pool_name
        if pool_data.frozen_trx is not None:
            update_fields['frozen_trx'] = pool_data.frozen_trx
        if pool_data.total_energy is not None:
            # 총 에너지 변경 시 사용 가능 에너지도 비례하여 조정
            old_total = pool.total_energy
            new_total = pool_data.total_energy
            if old_total > 0:
                ratio = new_total / old_total
                update_fields['total_energy'] = new_total
                update_fields['available_energy'] = int(pool.available_energy * ratio)
        if pool_data.low_threshold is not None:
            update_fields['low_threshold'] = pool_data.low_threshold
        if pool_data.critical_threshold is not None:
            update_fields['critical_threshold'] = pool_data.critical_threshold
        if pool_data.status:
            valid_statuses = ["active", "low", "critical", "depleted", "maintenance"]
            if pool_data.status not in valid_statuses:
                raise HTTPException(status_code=400, detail="유효하지 않은 상태입니다")
            update_fields['status'] = pool_data.status
        
        # 필드 업데이트
        for field, value in update_fields.items():
            if hasattr(pool, field):
                setattr(pool, field, value)
        
        db.commit()
        
        return {
            "message": "에너지 풀 정보가 업데이트되었습니다",
            "pool_id": pool_id,
            "updated_fields": list(update_fields.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/energy/pools/{pool_id}")
async def delete_energy_pool(pool_id: int, db: Session = Depends(get_sync_db)):
    """
    에너지 풀 삭제 (소프트 삭제)
    """
    try:
        pool = db.query(EnergyPoolModel).filter(EnergyPoolModel.id == pool_id).first()
        if not pool:
            raise HTTPException(status_code=404, detail="에너지 풀을 찾을 수 없습니다")
        
        # 활성 상태인지 확인
        if pool.status == "active" and pool.available_energy > 0:
            raise HTTPException(
                status_code=400, 
                detail="활성 상태이고 사용 가능한 에너지가 있어 삭제할 수 없습니다"
            )
        
        # 소프트 삭제
        pool.status = "deleted"
        if hasattr(pool, 'deleted_at'):
            setattr(pool, 'deleted_at', datetime.now())
        
        db.commit()
        
        return {
            "message": "에너지 풀이 삭제되었습니다",
            "pool_id": pool_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/energy/stats")
async def get_energy_stats(db: Session = Depends(get_sync_db)):
    """
    전체 에너지 통계 조회
    """
    try:
        # 전체 에너지 풀 통계
        pool_stats = db.query(
            func.count(EnergyPoolModel.id),
            func.sum(EnergyPoolModel.total_energy),
            func.sum(EnergyPoolModel.available_energy),
            func.sum(EnergyPoolModel.used_energy),
            func.sum(EnergyPoolModel.frozen_trx)
        ).filter(EnergyPoolModel.status != "deleted").first()
        
        total_pools = pool_stats[0] if pool_stats and pool_stats[0] else 0
        total_energy = int(pool_stats[1]) if pool_stats and pool_stats[1] else 0
        available_energy = int(pool_stats[2]) if pool_stats and pool_stats[2] else 0
        used_energy = int(pool_stats[3]) if pool_stats and pool_stats[3] else 0
        total_frozen_trx = float(pool_stats[4]) if pool_stats and pool_stats[4] else 0.0
        
        # 전체 사용률
        usage_rate = 0
        if total_energy > 0:
            usage_rate = round((used_energy / total_energy) * 100, 2)
        
        # 상태별 풀 개수
        status_counts = db.query(
            EnergyPoolModel.status,
            func.count(EnergyPoolModel.id)
        ).filter(EnergyPoolModel.status != "deleted").group_by(EnergyPoolModel.status).all()
        
        status_summary = {status: count for status, count in status_counts}
        
        # 최근 24시간 사용량
        yesterday = datetime.now() - timedelta(hours=24)
        recent_usage = db.query(
            func.sum(EnergyUsageLog.energy_used),
            func.count(EnergyUsageLog.id)
        ).filter(EnergyUsageLog.created_at >= yesterday).first()
        
        daily_usage = int(recent_usage[0]) if recent_usage and recent_usage[0] else 0
        daily_transactions = recent_usage[1] if recent_usage and recent_usage[1] else 0
        
        return {
            "overview": {
                "total_pools": total_pools,
                "total_energy": total_energy,
                "available_energy": available_energy,
                "used_energy": used_energy,
                "usage_rate": usage_rate,
                "total_frozen_trx": total_frozen_trx
            },
            "status_summary": status_summary,
            "daily_metrics": {
                "energy_used_24h": daily_usage,
                "transactions_24h": daily_transactions,
                "avg_energy_per_tx": round(daily_usage / daily_transactions, 2) if daily_transactions > 0 else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/energy/usage/analytics")
async def get_energy_usage_analytics(
    days: int = Query(30, ge=1, le=365),
    pool_id: Optional[int] = None,
    partner_id: Optional[int] = None,
    db: Session = Depends(get_sync_db)
):
    """
    에너지 사용량 분석 데이터 조회
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = db.query(EnergyUsageLog).filter(
            EnergyUsageLog.created_at >= start_date,
            EnergyUsageLog.created_at <= end_date
        )
        
        if pool_id:
            query = query.filter(EnergyUsageLog.pool_id == pool_id)
        if partner_id:
            query = query.filter(getattr(EnergyUsageLog, 'partner_id', None) == partner_id)
        
        # 일별 사용량 통계
        daily_analytics = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            next_date = date + timedelta(days=1)
            
            day_stats = query.filter(
                EnergyUsageLog.created_at >= date,
                EnergyUsageLog.created_at < next_date
            ).with_entities(
                func.sum(EnergyUsageLog.energy_used),
                func.count(EnergyUsageLog.id),
                func.avg(EnergyUsageLog.energy_used)
            ).first()
            
            daily_analytics.append({
                "date": date.strftime("%Y-%m-%d"),
                "total_energy_used": int(day_stats[0]) if day_stats and day_stats[0] else 0,
                "transaction_count": day_stats[1] if day_stats and day_stats[1] else 0,
                "avg_energy_per_tx": round(float(day_stats[2]), 2) if day_stats and day_stats[2] else 0
            })
        
        # 풀별 사용량 (상위 10개)
        pool_usage = db.query(
            EnergyUsageLog.pool_id,
            EnergyPoolModel.pool_name,
            func.sum(EnergyUsageLog.energy_used).label('total_used'),
            func.count(EnergyUsageLog.id).label('transaction_count')
        ).join(
            EnergyPoolModel, EnergyUsageLog.pool_id == EnergyPoolModel.id
        ).filter(
            EnergyUsageLog.created_at >= start_date
        ).group_by(
            EnergyUsageLog.pool_id, EnergyPoolModel.pool_name
        ).order_by(
            desc('total_used')
        ).limit(10).all()
        
        top_pools = [
            {
                "pool_id": row.pool_id,
                "pool_name": row.pool_name,
                "total_energy_used": int(row.total_used),
                "transaction_count": row.transaction_count
            } for row in pool_usage
        ]
        
        return {
            "period": {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "days": days
            },
            "daily_analytics": daily_analytics,
            "top_pools": top_pools
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
