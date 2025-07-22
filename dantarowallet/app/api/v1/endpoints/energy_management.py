"""
파트너용 에너지 풀 관리 API
Doc #25: 에너지 풀 고급 관리 시스템 구현

파트너사별 에너지 풀 CRUD 관리, 에너지 할당, 
임계값 설정, 자동 충전 설정 등 에너지 풀 관리 기능
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from pydantic import BaseModel

from app.core.database import get_sync_db
from app.api.deps import get_current_partner  # 실제 JWT 기반 파트너 인증 사용
from app.models.energy_pool import EnergyPoolModel, EnergyUsageLog, EnergyPriceHistory
from app.models.partner import Partner
from app.models.user import User

router = APIRouter(prefix="/energy-management", tags=["energy_management"])

# ============== Pydantic 스키마 ===============

class EnergyPoolCreate(BaseModel):
    """에너지 풀 생성 요청"""
    pool_name: str
    initial_energy: int
    max_energy_limit: int
    warning_threshold: int = 20  # 경고 임계값 (%)
    critical_threshold: int = 10  # 위험 임계값 (%)
    auto_recharge_enabled: bool = False
    auto_recharge_amount: Optional[int] = None
    priority: int = 1  # 우선순위 (1=높음, 5=낮음)

class EnergyPoolUpdate(BaseModel):
    """에너지 풀 수정 요청"""
    pool_name: Optional[str] = None
    max_energy_limit: Optional[int] = None
    warning_threshold: Optional[int] = None
    critical_threshold: Optional[int] = None
    auto_recharge_enabled: Optional[bool] = None
    auto_recharge_amount: Optional[int] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None

class EnergyAllocation(BaseModel):
    """에너지 할당 요청"""
    user_id: int
    allocated_energy: int
    valid_until: Optional[datetime] = None
    notes: Optional[str] = None

class EnergyThresholdSettings(BaseModel):
    """임계값 설정"""
    warning_threshold: int  # 20% 등
    critical_threshold: int  # 10% 등
    emergency_threshold: int  # 5% 등
    auto_recharge_threshold: int  # 15% 등
    notification_enabled: bool = True

class AutoRechargeSettings(BaseModel):
    """자동 충전 설정"""
    enabled: bool
    trigger_threshold: int  # 임계값 (%)
    recharge_amount: int  # 충전량
    max_daily_recharge: int  # 일일 최대 충전량
    recharge_interval_hours: int = 1  # 충전 간격 (시간)

class EnergyPoolInfo(BaseModel):
    """에너지 풀 정보 응답"""
    id: int
    pool_name: str
    partner_id: int
    total_energy: int
    available_energy: int
    allocated_energy: int
    reserved_energy: int
    energy_usage_rate: float
    warning_threshold: int
    critical_threshold: int
    status: str  # active, warning, critical, depleted
    auto_recharge_enabled: bool
    priority: int
    created_at: datetime
    last_charged_at: Optional[datetime]
    estimated_depletion_time: Optional[datetime]

class EnergyAllocationInfo(BaseModel):
    """에너지 할당 정보"""
    id: int
    user_id: int
    username: str
    allocated_energy: int
    used_energy: int
    remaining_energy: int
    allocation_date: datetime
    valid_until: Optional[datetime]
    status: str  # active, expired, revoked

class EnergyUsageStats(BaseModel):
    """에너지 사용 통계"""
    total_pools: int
    total_energy: int
    available_energy: int
    allocated_energy: int
    daily_usage: int
    weekly_usage: int
    monthly_usage: int
    peak_usage_hour: int
    average_usage_rate: float
    cost_per_energy: float

# ============== API 엔드포인트 ===============

@router.get("/pools", response_model=List[EnergyPoolInfo])
async def get_energy_pools(
    db: Session = Depends(get_sync_db),
    current_partner: Partner = Depends(get_current_partner),
    status: Optional[str] = Query(None, description="상태 필터 (active, warning, critical)"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """파트너의 모든 에너지 풀 목록 조회"""
    
    query = db.query(EnergyPoolModel).filter(
        EnergyPoolModel.partner_id == current_partner.id
    )
    
    # 상태 필터링
    if status:
        if status == "warning":
            query = query.filter(
                (EnergyPoolModel.available_energy / EnergyPoolModel.total_energy * 100) <= EnergyPoolModel.warning_threshold
            )
        elif status == "critical":
            query = query.filter(
                (EnergyPoolModel.available_energy / EnergyPoolModel.total_energy * 100) <= EnergyPoolModel.critical_threshold
            )
        elif status == "active":
            query = query.filter(EnergyPoolModel.is_active == True)
    
    # 페이징
    offset = (page - 1) * limit
    pools = query.order_by(EnergyPoolModel.priority, desc(EnergyPoolModel.created_at)).offset(offset).limit(limit).all()
    
    result = []
    for pool in pools:
        total_energy = float(getattr(pool, 'total_energy', 0))
        available_energy = float(getattr(pool, 'available_energy', 0))
        allocated_energy = float(getattr(pool, 'allocated_energy', 0))
        
        # 상태 계산
        if total_energy > 0:
            usage_rate = ((total_energy - available_energy) / total_energy) * 100
            available_percentage = (available_energy / total_energy) * 100
            
            if available_percentage <= getattr(pool, 'critical_threshold', 10):
                status_str = "critical"
            elif available_percentage <= getattr(pool, 'warning_threshold', 20):
                status_str = "warning"
            elif getattr(pool, 'is_active', True):
                status_str = "active"
            else:
                status_str = "inactive"
        else:
            usage_rate = 0
            status_str = "depleted"
        
        # 예상 고갈 시간 계산
        estimated_depletion = None
        if available_energy > 0 and usage_rate > 0:
            hours_remaining = available_energy / (usage_rate / 24)  # 시간당 사용량 기준
            estimated_depletion = datetime.now() + timedelta(hours=hours_remaining)
        
        result.append(EnergyPoolInfo(
            id=getattr(pool, 'id', 0),
            pool_name=getattr(pool, 'pool_name', ''),
            partner_id=getattr(pool, 'partner_id', 0),
            total_energy=int(total_energy),
            available_energy=int(available_energy),
            allocated_energy=int(allocated_energy),
            reserved_energy=int(getattr(pool, 'reserved_energy', 0)),
            energy_usage_rate=round(usage_rate, 2),
            warning_threshold=getattr(pool, 'warning_threshold', 20),
            critical_threshold=getattr(pool, 'critical_threshold', 10),
            status=status_str,
            auto_recharge_enabled=getattr(pool, 'auto_recharge_enabled', False),
            priority=getattr(pool, 'priority', 1),
            created_at=getattr(pool, 'created_at', datetime.now()),
            last_charged_at=getattr(pool, 'last_charged_at', None),
            estimated_depletion_time=estimated_depletion
        ))
    
    return result

@router.post("/pools", response_model=EnergyPoolInfo)
async def create_energy_pool(
    pool_data: EnergyPoolCreate,
    db: Session = Depends(get_sync_db),
    current_partner: Partner = Depends(get_current_partner)
):
    """새 에너지 풀 생성"""
    
    # 풀 이름 중복 확인
    existing_pool = db.query(EnergyPoolModel).filter(
        EnergyPoolModel.partner_id == current_partner.id,
        EnergyPoolModel.pool_name == pool_data.pool_name
    ).first()
    
    if existing_pool:
        raise HTTPException(status_code=400, detail="Pool name already exists")
    
    # 새 에너지 풀 생성
    new_pool = EnergyPoolModel(
        partner_id=current_partner.id,
        pool_name=pool_data.pool_name,
        total_energy=pool_data.initial_energy,
        available_energy=pool_data.initial_energy,
        allocated_energy=0,
        max_energy_limit=pool_data.max_energy_limit,
        warning_threshold=pool_data.warning_threshold,
        critical_threshold=pool_data.critical_threshold,
        auto_recharge_enabled=pool_data.auto_recharge_enabled,
        auto_recharge_amount=pool_data.auto_recharge_amount,
        priority=pool_data.priority,
        is_active=True,
        created_at=datetime.now()
    )
    
    db.add(new_pool)
    db.commit()
    db.refresh(new_pool)
    
    # 사용 로그 기록
    usage_log = EnergyUsageLog(
        pool_id=new_pool.id,
        partner_id=current_partner.id,
        transaction_type="pool_created",
        energy_amount=pool_data.initial_energy,
        description=f"Energy pool '{pool_data.pool_name}' created",
        created_at=datetime.now()
    )
    db.add(usage_log)
    db.commit()
    
    return EnergyPoolInfo(
        id=getattr(new_pool, 'id', 0),
        pool_name=getattr(new_pool, 'pool_name', ''),
        partner_id=getattr(new_pool, 'partner_id', 0),
        total_energy=int(getattr(new_pool, 'total_energy', 0)),
        available_energy=int(getattr(new_pool, 'available_energy', 0)),
        allocated_energy=int(getattr(new_pool, 'allocated_energy', 0)),
        reserved_energy=0,
        energy_usage_rate=0.0,
        warning_threshold=getattr(new_pool, 'warning_threshold', 20),
        critical_threshold=getattr(new_pool, 'critical_threshold', 10),
        status="active",
        auto_recharge_enabled=getattr(new_pool, 'auto_recharge_enabled', False),
        priority=getattr(new_pool, 'priority', 1),
        created_at=getattr(new_pool, 'created_at', datetime.now()),
        last_charged_at=None,
        estimated_depletion_time=None
    )

@router.get("/pools/{pool_id}", response_model=EnergyPoolInfo)
async def get_energy_pool(
    pool_id: int,
    db: Session = Depends(get_sync_db),
    current_partner: Partner = Depends(get_current_partner)
):
    """특정 에너지 풀 상세 정보 조회"""
    
    pool = db.query(EnergyPoolModel).filter(
        EnergyPoolModel.id == pool_id,
        EnergyPoolModel.partner_id == current_partner.id
    ).first()
    
    if not pool:
        raise HTTPException(status_code=404, detail="Energy pool not found")
    
    # 상세 정보 계산
    total_energy = float(getattr(pool, 'total_energy', 0))
    available_energy = float(getattr(pool, 'available_energy', 0))
    allocated_energy = float(getattr(pool, 'allocated_energy', 0))
    
    usage_rate = ((total_energy - available_energy) / total_energy * 100) if total_energy > 0 else 0
    available_percentage = (available_energy / total_energy * 100) if total_energy > 0 else 0
    
    # 상태 결정
    if available_percentage <= getattr(pool, 'critical_threshold', 10):
        status_str = "critical"
    elif available_percentage <= getattr(pool, 'warning_threshold', 20):
        status_str = "warning"
    elif getattr(pool, 'is_active', True):
        status_str = "active"
    else:
        status_str = "inactive"
    
    return EnergyPoolInfo(
        id=getattr(pool, 'id', 0),
        pool_name=getattr(pool, 'pool_name', ''),
        partner_id=getattr(pool, 'partner_id', 0),
        total_energy=int(total_energy),
        available_energy=int(available_energy),
        allocated_energy=int(allocated_energy),
        reserved_energy=int(getattr(pool, 'reserved_energy', 0)),
        energy_usage_rate=round(usage_rate, 2),
        warning_threshold=getattr(pool, 'warning_threshold', 20),
        critical_threshold=getattr(pool, 'critical_threshold', 10),
        status=status_str,
        auto_recharge_enabled=getattr(pool, 'auto_recharge_enabled', False),
        priority=getattr(pool, 'priority', 1),
        created_at=getattr(pool, 'created_at', datetime.now()),
        last_charged_at=getattr(pool, 'last_charged_at', None),
        estimated_depletion_time=None
    )

@router.put("/pools/{pool_id}", response_model=EnergyPoolInfo)
async def update_energy_pool(
    pool_id: int,
    pool_data: EnergyPoolUpdate,
    db: Session = Depends(get_sync_db),
    current_partner: Partner = Depends(get_current_partner)
):
    """에너지 풀 설정 업데이트"""
    
    pool = db.query(EnergyPoolModel).filter(
        EnergyPoolModel.id == pool_id,
        EnergyPoolModel.partner_id == current_partner.id
    ).first()
    
    if not pool:
        raise HTTPException(status_code=404, detail="Energy pool not found")
    
    # 업데이트할 필드들 적용
    update_data = pool_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(pool, field):
            setattr(pool, field, value)
    
    pool.updated_at = datetime.now()
    db.commit()
    db.refresh(pool)
    
    # 변경 로그 기록
    usage_log = EnergyUsageLog(
        pool_id=pool.id,
        partner_id=current_partner.id,
        transaction_type="pool_updated",
        energy_amount=0,
        description=f"Energy pool settings updated: {', '.join(update_data.keys())}",
        created_at=datetime.now()
    )
    db.add(usage_log)
    db.commit()
    
    return await get_energy_pool(pool_id, db, current_partner)

@router.delete("/pools/{pool_id}")
async def delete_energy_pool(
    pool_id: int,
    db: Session = Depends(get_sync_db),
    current_partner: Partner = Depends(get_current_partner)
):
    """에너지 풀 삭제"""
    
    pool = db.query(EnergyPoolModel).filter(
        EnergyPoolModel.id == pool_id,
        EnergyPoolModel.partner_id == current_partner.id
    ).first()
    
    if not pool:
        raise HTTPException(status_code=404, detail="Energy pool not found")
    
    # 할당된 에너지가 있는지 확인
    if getattr(pool, 'allocated_energy', 0) > 0:
        raise HTTPException(status_code=400, detail="Cannot delete pool with allocated energy")
    
    # 삭제 로그 기록
    usage_log = EnergyUsageLog(
        pool_id=pool.id,
        partner_id=current_partner.id,
        transaction_type="pool_deleted",
        energy_amount=0,
        description=f"Energy pool '{getattr(pool, 'pool_name', '')}' deleted",
        created_at=datetime.now()
    )
    db.add(usage_log)
    
    # 풀 삭제
    db.delete(pool)
    db.commit()
    
    return {"message": "Energy pool deleted successfully"}

@router.post("/pools/{pool_id}/recharge")
async def recharge_energy_pool(
    pool_id: int,
    recharge_amount: int = Body(..., embed=True),
    db: Session = Depends(get_sync_db),
    current_partner: Partner = Depends(get_current_partner)
):
    """에너지 풀 수동 충전"""
    
    pool = db.query(EnergyPoolModel).filter(
        EnergyPoolModel.id == pool_id,
        EnergyPoolModel.partner_id == current_partner.id
    ).first()
    
    if not pool:
        raise HTTPException(status_code=404, detail="Energy pool not found")
    
    if recharge_amount <= 0:
        raise HTTPException(status_code=400, detail="Recharge amount must be positive")
    
    # 최대 한도 확인
    max_limit = getattr(pool, 'max_energy_limit', 0)
    current_total = getattr(pool, 'total_energy', 0)
    
    if current_total + recharge_amount > max_limit:
        raise HTTPException(
            status_code=400, 
            detail=f"Recharge would exceed maximum limit ({max_limit})"
        )
    
    # 에너지 충전
    setattr(pool, 'total_energy', current_total + recharge_amount)
    setattr(pool, 'available_energy', getattr(pool, 'available_energy', 0) + recharge_amount)
    setattr(pool, 'last_charged_at', datetime.now())
    
    db.commit()
    
    # 충전 로그 기록
    usage_log = EnergyUsageLog(
        pool_id=pool.id,
        partner_id=current_partner.id,
        transaction_type="manual_recharge",
        energy_amount=recharge_amount,
        description=f"Manual recharge of {recharge_amount} energy",
        created_at=datetime.now()
    )
    db.add(usage_log)
    db.commit()
    
    return {
        "message": "Energy pool recharged successfully",
        "pool_id": pool_id,
        "recharged_amount": recharge_amount,
        "new_total": int(getattr(pool, 'total_energy', 0)),
        "new_available": int(getattr(pool, 'available_energy', 0))
    }

@router.get("/pools/{pool_id}/allocations", response_model=List[EnergyAllocationInfo])
async def get_energy_allocations(
    pool_id: int,
    db: Session = Depends(get_sync_db),
    current_partner: Partner = Depends(get_current_partner)
):
    """에너지 풀의 사용자별 할당 현황 조회"""
    
    pool = db.query(EnergyPoolModel).filter(
        EnergyPoolModel.id == pool_id,
        EnergyPoolModel.partner_id == current_partner.id
    ).first()
    
    if not pool:
        raise HTTPException(status_code=404, detail="Energy pool not found")
    
    # 할당 정보 조회 (실제 구현에서는 별도 allocation 테이블 필요)
    # 여기서는 샘플 데이터로 대체
    return [
        EnergyAllocationInfo(
            id=1,
            user_id=1,
            username="user1",
            allocated_energy=1000,
            used_energy=200,
            remaining_energy=800,
            allocation_date=datetime.now() - timedelta(days=1),
            valid_until=datetime.now() + timedelta(days=30),
            status="active"
        )
    ]

@router.post("/pools/{pool_id}/allocate")
async def allocate_energy(
    pool_id: int,
    allocation_data: EnergyAllocation,
    db: Session = Depends(get_sync_db),
    current_partner: Partner = Depends(get_current_partner)
):
    """사용자에게 에너지 할당"""
    
    pool = db.query(EnergyPoolModel).filter(
        EnergyPoolModel.id == pool_id,
        EnergyPoolModel.partner_id == current_partner.id
    ).first()
    
    if not pool:
        raise HTTPException(status_code=404, detail="Energy pool not found")
    
    # 사용자 존재 확인
    user = db.query(User).filter(User.id == allocation_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 사용 가능 에너지 확인
    available_energy = getattr(pool, 'available_energy', 0)
    if allocation_data.allocated_energy > available_energy:
        raise HTTPException(status_code=400, detail="Insufficient available energy")
    
    # 에너지 할당 (실제 구현에서는 별도 테이블 필요)
    setattr(pool, 'available_energy', available_energy - allocation_data.allocated_energy)
    setattr(pool, 'allocated_energy', getattr(pool, 'allocated_energy', 0) + allocation_data.allocated_energy)
    
    db.commit()
    
    # 할당 로그 기록
    usage_log = EnergyUsageLog(
        pool_id=pool.id,
        partner_id=current_partner.id,
        user_id=allocation_data.user_id,
        transaction_type="energy_allocated",
        energy_amount=allocation_data.allocated_energy,
        description=f"Energy allocated to user {allocation_data.user_id}",
        created_at=datetime.now()
    )
    db.add(usage_log)
    db.commit()
    
    return {
        "message": "Energy allocated successfully",
        "pool_id": pool_id,
        "user_id": allocation_data.user_id,
        "allocated_amount": allocation_data.allocated_energy,
        "remaining_available": int(getattr(pool, 'available_energy', 0))
    }

@router.put("/pools/{pool_id}/thresholds")
async def update_energy_thresholds(
    pool_id: int,
    threshold_settings: EnergyThresholdSettings,
    db: Session = Depends(get_sync_db),
    current_partner: Partner = Depends(get_current_partner)
):
    """에너지 풀 임계값 설정 업데이트"""
    
    pool = db.query(EnergyPoolModel).filter(
        EnergyPoolModel.id == pool_id,
        EnergyPoolModel.partner_id == current_partner.id
    ).first()
    
    if not pool:
        raise HTTPException(status_code=404, detail="Energy pool not found")
    
    # 임계값 검증
    if threshold_settings.critical_threshold >= threshold_settings.warning_threshold:
        raise HTTPException(status_code=400, detail="Critical threshold must be lower than warning threshold")
    
    # 임계값 업데이트
    setattr(pool, 'warning_threshold', threshold_settings.warning_threshold)
    setattr(pool, 'critical_threshold', threshold_settings.critical_threshold)
    # 추가 임계값 필드들도 모델에 있다면 업데이트
    
    db.commit()
    
    return {"message": "Threshold settings updated successfully"}

@router.put("/pools/{pool_id}/auto-recharge")
async def update_auto_recharge_settings(
    pool_id: int,
    auto_recharge_settings: AutoRechargeSettings,
    db: Session = Depends(get_sync_db),
    current_partner: Partner = Depends(get_current_partner)
):
    """자동 충전 설정 업데이트"""
    
    pool = db.query(EnergyPoolModel).filter(
        EnergyPoolModel.id == pool_id,
        EnergyPoolModel.partner_id == current_partner.id
    ).first()
    
    if not pool:
        raise HTTPException(status_code=404, detail="Energy pool not found")
    
    # 자동 충전 설정 업데이트
    setattr(pool, 'auto_recharge_enabled', auto_recharge_settings.enabled)
    setattr(pool, 'auto_recharge_amount', auto_recharge_settings.recharge_amount)
    # 추가 자동 충전 필드들도 모델에 있다면 업데이트
    
    db.commit()
    
    return {"message": "Auto-recharge settings updated successfully"}

@router.get("/statistics", response_model=EnergyUsageStats)
async def get_energy_usage_statistics(
    db: Session = Depends(get_sync_db),
    current_partner: Partner = Depends(get_current_partner),
    days: int = Query(30, ge=1, le=365, description="통계 기간 (일)")
):
    """파트너의 에너지 사용 통계"""
    
    # 기본 통계 계산
    pools = db.query(EnergyPoolModel).filter(
        EnergyPoolModel.partner_id == current_partner.id
    ).all()
    
    total_pools = len(pools)
    total_energy = sum(float(getattr(pool, 'total_energy', 0)) for pool in pools)
    available_energy = sum(float(getattr(pool, 'available_energy', 0)) for pool in pools)
    allocated_energy = sum(float(getattr(pool, 'allocated_energy', 0)) for pool in pools)
    
    # 사용량 통계 (간단한 계산)
    daily_usage = int((total_energy - available_energy) / max(days, 1))
    weekly_usage = daily_usage * 7
    monthly_usage = daily_usage * 30
    
    # 평균 사용률
    average_usage_rate = ((total_energy - available_energy) / total_energy * 100) if total_energy > 0 else 0
    
    # 피크 시간 계산 (임시로 오후 2시)
    peak_hour = 14  # TODO: 실제 통계에서 피크 시간 계산
    
    # 현재 에너지 가격 조회 (임시값)
    current_price = 0.001  # TODO: 실제 에너지 가격 테이블에서 조회
    
    return EnergyUsageStats(
        total_pools=total_pools,
        total_energy=int(total_energy),
        available_energy=int(available_energy),
        allocated_energy=int(allocated_energy),
        daily_usage=daily_usage,
        weekly_usage=weekly_usage,
        monthly_usage=monthly_usage,
        peak_usage_hour=peak_hour or 14,  # 피크 시간 계산 결과 또는 기본값
        average_usage_rate=round(average_usage_rate, 2),
        cost_per_energy=current_price or 0.001  # 실제 에너지 가격 또는 기본값
    )
