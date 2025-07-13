"""
슈퍼어드민용 에너지 관리 API
Doc #17: 본사 슈퍼 어드민 시스템 구현 기반

전체 에너지 풀 상태 모니터링, 파트너별 에너지 할당,
에너지 충전/소진 관리, 알림 및 통계 제공
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_sync_db
from app.core.auth import get_current_super_admin
from app.models.energy_pool import EnergyPoolModel, EnergyUsageLog, EnergyPriceHistory
from app.models.partner import Partner
from app.models.transaction import Transaction
from app.models.user import User

router = APIRouter(prefix="/admin/energy", tags=["Super Admin Energy"])


# Schema models for responses (inline definitions)
from pydantic import BaseModel

class EnergyPoolStatus(BaseModel):
    """전체 에너지 풀 상태"""
    total_energy: int
    used_energy: int
    available_energy: int
    active_pools: int
    total_partners: int
    energy_utilization_rate: float
    critical_pools: int
    warning_pools: int

class EnergyUsage(BaseModel):
    """파트너별 에너지 사용량"""
    partner_id: int
    partner_name: str
    total_allocated: int
    used_energy: int
    remaining_energy: int
    usage_rate: float
    last_usage: Optional[datetime]

class EnergyAlert(BaseModel):
    """에너지 알림"""
    id: int
    pool_id: int
    partner_name: str
    alert_type: str
    message: str
    severity: str
    created_at: datetime
    acknowledged: bool

class EnergyHistory(BaseModel):
    """에너지 사용 이력"""
    date: datetime
    partner_name: str
    transaction_type: str
    energy_used: int
    remaining_energy: int

class EnergyAllocation(BaseModel):
    """에너지 할당"""
    partner_id: int
    amount: int
    reason: str


@router.get("/status", response_model=EnergyPoolStatus)
async def get_energy_pool_status(
    db: Session = Depends(get_sync_db),
    current_admin = Depends(get_current_super_admin)
):
    """전체 에너지 풀 상태 조회"""
    
    # 전체 에너지 풀 통계 계산
    total_energy = db.query(EnergyPoolModel).with_entities(
        func.sum(EnergyPoolModel.total_energy)
    ).scalar() or 0
    
    used_energy = db.query(EnergyPoolModel).with_entities(
        func.sum(EnergyPoolModel.total_energy - EnergyPoolModel.available_energy)
    ).scalar() or 0
    
    available_energy = total_energy - used_energy
    
    active_pools = db.query(EnergyPoolModel).filter(
        EnergyPoolModel.status == "active"
    ).count()
    
    total_partners = db.query(Partner).count()
    
    # 임계값별 풀 개수
    critical_pools = db.query(EnergyPoolModel).filter(
        EnergyPoolModel.available_energy < (EnergyPoolModel.total_energy * 0.1)
    ).count()
    
    warning_pools = db.query(EnergyPoolModel).filter(
        EnergyPoolModel.available_energy < (EnergyPoolModel.total_energy * 0.2),
        EnergyPoolModel.available_energy >= (EnergyPoolModel.total_energy * 0.1)
    ).count()
    
    energy_utilization_rate = (used_energy / total_energy * 100) if total_energy > 0 else 0
    
    return EnergyPoolStatus(
        total_energy=int(total_energy),
        used_energy=int(used_energy),
        available_energy=int(available_energy),
        active_pools=active_pools,
        total_partners=total_partners,
        energy_utilization_rate=round(energy_utilization_rate, 2),
        critical_pools=critical_pools,
        warning_pools=warning_pools
    )


@router.post("/recharge")
async def recharge_energy_pool(
    pool_id: int,
    amount: int,
    db: Session = Depends(get_sync_db),
    current_admin = Depends(get_current_super_admin)
):
    """에너지 풀 충전"""
    
    pool = db.query(EnergyPoolModel).filter(EnergyPoolModel.id == pool_id).first()
    if not pool:
        raise HTTPException(status_code=404, detail="Energy pool not found")
    
    # 에너지 충전 로직
    old_total = float(getattr(pool, 'total_energy', 0))
    old_available = float(getattr(pool, 'available_energy', 0))
    
    new_total = old_total + amount
    new_available = old_available + amount
    
    # 업데이트
    if hasattr(pool, 'total_energy'):
        setattr(pool, 'total_energy', new_total)
    if hasattr(pool, 'available_energy'):
        setattr(pool, 'available_energy', new_available)
    
    # 사용 로그 기록
    usage_log = EnergyUsageLog(
        pool_id=pool_id,
        energy_amount=amount,
        transaction_type="recharge",
        created_at=datetime.now()
    )
    db.add(usage_log)
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Energy pool recharged with {amount} energy",
        "pool_id": pool_id,
        "new_total": new_total,
        "new_available": new_available
    }


@router.get("/alerts", response_model=List[EnergyAlert])
async def get_energy_alerts(
    acknowledged: Optional[bool] = Query(None, description="확인 여부 필터"),
    limit: int = Query(50, le=100, description="최대 결과 수"),
    db: Session = Depends(get_sync_db),
    current_admin = Depends(get_current_super_admin)
):
    """에너지 관련 알림 조회"""
    
    # Mock 알림 데이터 (실제로는 EnergyAlert 모델에서 조회)
    alerts = []
    
    # 임계값 이하 풀들 조회
    critical_pools = db.query(EnergyPoolModel).join(Partner).filter(
        EnergyPoolModel.available_energy < (EnergyPoolModel.total_energy * 0.1)
    ).all()
    
    for pool in critical_pools:
        partner = db.query(Partner).filter(Partner.id == pool.partner_id).first()
        alert = EnergyAlert(
            id=getattr(pool, 'id', 0),
            pool_id=getattr(pool, 'id', 0),
            partner_name=getattr(partner, 'name', 'Unknown') if partner else "Unknown",
            alert_type="critical_energy",
            message=f"Critical energy level: {getattr(pool, 'available_energy', 0)} remaining",
            severity="critical",
            created_at=datetime.now(),
            acknowledged=False
        )
        alerts.append(alert)
    
    return alerts[:limit]


@router.get("/history", response_model=List[EnergyHistory])
async def get_energy_usage_history(
    partner_id: Optional[int] = Query(None, description="파트너 ID 필터"),
    days: int = Query(7, ge=1, le=90, description="조회 기간 (일)"),
    db: Session = Depends(get_sync_db),
    current_admin = Depends(get_current_super_admin)
):
    """에너지 사용 이력 조회"""
    
    start_date = datetime.now() - timedelta(days=days)
    
    query = db.query(EnergyUsageLog).filter(
        EnergyUsageLog.created_at >= start_date
    )
    
    if partner_id:
        query = query.join(EnergyPoolModel).filter(
            EnergyPoolModel.partner_id == partner_id
        )
    
    usage_logs = query.order_by(EnergyUsageLog.created_at.desc()).limit(100).all()
    
    history = []
    for log in usage_logs:
        pool = db.query(EnergyPoolModel).filter(EnergyPoolModel.id == log.pool_id).first()
        partner = db.query(Partner).filter(Partner.id == pool.partner_id).first() if pool else None
        
        history.append(EnergyHistory(
            date=log.created_at,
            partner_name=getattr(partner, 'name', 'Unknown') if partner else "Unknown",
            transaction_type=getattr(log, 'transaction_type', 'unknown') or "unknown",
            energy_used=log.energy_amount or 0,
            remaining_energy=int(float(getattr(pool, 'available_energy', 0))) if pool else 0
        ))
    
    return history


@router.get("/statistics")
async def get_energy_statistics(
    db: Session = Depends(get_sync_db),
    current_admin = Depends(get_current_super_admin)
):
    """에너지 통계 정보"""
    
    # 파트너별 에너지 사용량
    partner_usage = db.query(
        Partner.id,
        Partner.name,
        EnergyPoolModel.total_energy,
        EnergyPoolModel.available_energy
    ).join(EnergyPoolModel).all()
    
    usage_stats = []
    for partner_id, partner_name, total, available in partner_usage:
        used = float(total or 0) - float(available or 0)
        usage_rate = (used / float(total or 1)) * 100
        
        usage_stats.append({
            "partner_id": partner_id,
            "partner_name": partner_name,
            "total_allocated": float(total or 0),
            "used_energy": used,
            "remaining_energy": float(available or 0),
            "usage_rate": round(usage_rate, 2)
        })
    
    # 전체 통계
    total_pools = db.query(EnergyPoolModel).count()
    active_pools = db.query(EnergyPoolModel).filter(EnergyPoolModel.status == "active").count()
    
    return {
        "partner_usage": usage_stats,
        "summary": {
            "total_pools": total_pools,
            "active_pools": active_pools,
            "inactive_pools": total_pools - active_pools
        }
    }


@router.post("/emergency-rebalance")
async def emergency_rebalance(
    db: Session = Depends(get_sync_db),
    current_admin = Depends(get_current_super_admin)
):
    """긴급 에너지 재분배"""
    
    # 에너지가 부족한 풀들 조회
    low_energy_pools = db.query(EnergyPoolModel).filter(
        EnergyPoolModel.available_energy < (EnergyPoolModel.total_energy * 0.1)
    ).all()
    
    # 에너지가 충분한 풀들 조회
    high_energy_pools = db.query(EnergyPoolModel).filter(
        EnergyPoolModel.available_energy > (EnergyPoolModel.total_energy * 0.8)
    ).all()
    
    rebalanced_pools = []
    
    for low_pool in low_energy_pools:
        if not high_energy_pools:
            break
            
        high_pool = high_energy_pools[0]
        transfer_amount = min(
            float(getattr(high_pool, 'available_energy', 0)) * 0.1,  # 10%만 이전
            float(getattr(low_pool, 'total_energy', 0)) * 0.2  # 필요한 만큼
        )
        
        if transfer_amount > 0:
            # 에너지 이전
            setattr(high_pool, 'available_energy', 
                   float(getattr(high_pool, 'available_energy', 0)) - transfer_amount)
            setattr(low_pool, 'available_energy', 
                   float(getattr(low_pool, 'available_energy', 0)) + transfer_amount)
            
            rebalanced_pools.append({
                "from_pool": high_pool.id,
                "to_pool": low_pool.id,
                "amount": transfer_amount
            })
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Rebalanced {len(rebalanced_pools)} pools",
        "transfers": rebalanced_pools
    }


@router.get("/partners/{partner_id}/usage", response_model=EnergyUsage)
async def get_partner_energy_usage(
    partner_id: int,
    db: Session = Depends(get_sync_db),
    current_admin = Depends(get_current_super_admin)
):
    """특정 파트너의 에너지 사용량 조회"""
    
    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    
    pool = db.query(EnergyPoolModel).filter(EnergyPoolModel.partner_id == partner_id).first()
    if not pool:
        raise HTTPException(status_code=404, detail="Energy pool not found")
    
    total_allocated = float(getattr(pool, 'total_energy', 0))
    remaining_energy = float(getattr(pool, 'available_energy', 0))
    used_energy = total_allocated - remaining_energy
    usage_rate = (used_energy / total_allocated * 100) if total_allocated > 0 else 0
    
    # 마지막 사용 시간 조회
    last_usage_log = db.query(EnergyUsageLog).filter(
        EnergyUsageLog.pool_id == pool.id
    ).order_by(EnergyUsageLog.created_at.desc()).first()
    
    return EnergyUsage(
        partner_id=partner_id,
        partner_name=getattr(partner, 'name', 'Unknown'),
        total_allocated=int(total_allocated),
        used_energy=int(used_energy),
        remaining_energy=int(remaining_energy),
        usage_rate=round(usage_rate, 2),
        last_usage=last_usage_log.created_at if last_usage_log else None
    )


@router.post("/partners/{partner_id}/allocate")
async def allocate_energy_to_partner(
    partner_id: int,
    allocation: EnergyAllocation,
    db: Session = Depends(get_sync_db),
    current_admin = Depends(get_current_super_admin)
):
    """파트너에게 에너지 할당"""
    
    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    
    pool = db.query(EnergyPoolModel).filter(EnergyPoolModel.partner_id == partner_id).first()
    if not pool:
        raise HTTPException(status_code=404, detail="Energy pool not found")
    
    # 에너지 할당
    old_total = float(getattr(pool, 'total_energy', 0))
    old_available = float(getattr(pool, 'available_energy', 0))
    
    new_total = old_total + allocation.amount
    new_available = old_available + allocation.amount
    
    setattr(pool, 'total_energy', new_total)
    setattr(pool, 'available_energy', new_available)
    
    # 할당 로그 기록
    usage_log = EnergyUsageLog(
        pool_id=pool.id,
        energy_amount=allocation.amount,
        transaction_type="allocation",
        created_at=datetime.now()
    )
    db.add(usage_log)
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Allocated {allocation.amount} energy to {partner.name}",
        "partner_id": partner_id,
        "amount": allocation.amount,
        "reason": allocation.reason,
        "new_total": new_total,
        "new_available": new_available
    }


@router.get("/efficiency-report")
async def get_energy_efficiency_report(
    db: Session = Depends(get_sync_db),
    current_admin = Depends(get_current_super_admin)
):
    """에너지 효율성 보고서"""
    
    # 파트너별 효율성 계산
    partners_efficiency = []
    
    partners = db.query(Partner).all()
    for partner in partners:
        pool = db.query(EnergyPoolModel).filter(EnergyPoolModel.partner_id == partner.id).first()
        if not pool:
            continue
            
        total_energy = float(getattr(pool, 'total_energy', 0))
        available_energy = float(getattr(pool, 'available_energy', 0))
        used_energy = total_energy - available_energy
        
        # 최근 30일 거래 수
        recent_transactions = db.query(Transaction).filter(
            Transaction.partner_id == partner.id,
            Transaction.created_at >= datetime.now() - timedelta(days=30)
        ).count()
        
        # 에너지 효율성 = 거래당 평균 에너지 사용량
        efficiency = (used_energy / recent_transactions) if recent_transactions > 0 else 0
        
        partners_efficiency.append({
            "partner_id": partner.id,
            "partner_name": partner.name,
            "total_energy": total_energy,
            "used_energy": used_energy,
            "available_energy": available_energy,
            "recent_transactions": recent_transactions,
            "energy_per_transaction": round(efficiency, 2),
            "utilization_rate": round((used_energy / total_energy * 100) if total_energy > 0 else 0, 2)
        })
    
    # 전체 시스템 효율성
    total_system_energy = sum(p["total_energy"] for p in partners_efficiency)
    total_used_energy = sum(p["used_energy"] for p in partners_efficiency)
    total_transactions = sum(p["recent_transactions"] for p in partners_efficiency)
    
    system_efficiency = {
        "total_energy": total_system_energy,
        "total_used": total_used_energy,
        "total_available": total_system_energy - total_used_energy,
        "total_transactions": total_transactions,
        "average_energy_per_transaction": round((total_used_energy / total_transactions) if total_transactions > 0 else 0, 2),
        "system_utilization_rate": round((total_used_energy / total_system_energy * 100) if total_system_energy > 0 else 0, 2)
    }
    
    return {
        "partners": partners_efficiency,
        "system": system_efficiency,
        "generated_at": datetime.now().isoformat()
    }


@router.post("/threshold/update")
async def update_energy_thresholds(
    pool_id: int,
    warning_threshold: float,
    critical_threshold: float,
    db: Session = Depends(get_sync_db),
    current_admin = Depends(get_current_super_admin)
):
    """에너지 풀 임계값 업데이트"""
    
    pool = db.query(EnergyPoolModel).filter(EnergyPoolModel.id == pool_id).first()
    if not pool:
        raise HTTPException(status_code=404, detail="Energy pool not found")
    
    # 임계값 유효성 검증
    if warning_threshold <= critical_threshold:
        raise HTTPException(status_code=400, detail="Warning threshold must be higher than critical threshold")
    
    if critical_threshold < 0 or warning_threshold > 100:
        raise HTTPException(status_code=400, detail="Thresholds must be between 0 and 100")
    
    # 임계값 업데이트
    if hasattr(pool, 'low_threshold'):
        setattr(pool, 'low_threshold', warning_threshold)
    if hasattr(pool, 'critical_threshold'):
        setattr(pool, 'critical_threshold', critical_threshold)
    
    db.commit()
    
    return {
        "success": True,
        "message": "Energy thresholds updated successfully",
        "pool_id": pool_id,
        "warning_threshold": warning_threshold,
        "critical_threshold": critical_threshold
    }
