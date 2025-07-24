"""
파트너 에너지 렌탈 관리 API

수퍼어드민이 파트너사에게 에너지를 할당하고 마진을 관리하는 API
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_db
from app.models.partner_energy_allocation import (
    AllocationStatus,
    BillingCycle,
    BillingStatus,
    EnergyMarginConfig,
    EnergyPurchaseRecord,
    PartnerEnergyAllocation,
    PartnerEnergyBilling,
    PartnerEnergyUsage,
    PartnerTier,
)
from app.models.user import User

router = APIRouter()


from typing import Any, Dict

# 파트너 에너지 할당 관련 스키마
from pydantic import BaseModel, Field


class PartnerEnergyAllocationCreate(BaseModel):
    partner_id: str = Field(..., description="파트너 ID")
    partner_name: str = Field(..., description="파트너 이름")
    partner_tier: PartnerTier = Field(PartnerTier.BUSINESS, description="파트너 등급")
    allocated_amount: int = Field(..., gt=0, description="할당할 에너지량")
    purchase_price: float = Field(..., gt=0, description="구매 단가")
    markup_percentage: float = Field(..., ge=0, le=100, description="마진율 (%)")
    billing_cycle: BillingCycle = Field(BillingCycle.MONTHLY, description="정산 주기")
    expiry_date: Optional[datetime] = Field(None, description="만료일")
    notes: Optional[str] = Field(None, description="메모")


class PartnerEnergyAllocationUpdate(BaseModel):
    allocated_amount: Optional[int] = Field(None, gt=0)
    markup_percentage: Optional[float] = Field(None, ge=0, le=100)
    billing_cycle: Optional[BillingCycle] = None
    status: Optional[AllocationStatus] = None
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = None


class PartnerEnergyUsageCreate(BaseModel):
    allocation_id: int = Field(..., description="할당 ID")
    used_amount: int = Field(..., gt=0, description="사용량")
    transaction_hash: Optional[str] = Field(None, description="트랜잭션 해시")
    description: Optional[str] = Field(None, description="설명")


class PartnerEnergyAllocationResponse(BaseModel):
    id: int
    partner_id: str
    partner_name: str
    partner_tier: PartnerTier
    allocated_amount: int
    remaining_amount: int
    used_amount: int
    purchase_price: float
    markup_percentage: float
    rental_price: float
    billing_cycle: BillingCycle
    status: AllocationStatus
    allocation_date: datetime
    expiry_date: Optional[datetime]
    last_usage_date: Optional[datetime]
    utilization_rate: float
    total_revenue: float
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PartnerEnergyUsageResponse(BaseModel):
    id: int
    allocation_id: int
    partner_id: str
    used_amount: int
    unit_price: float
    total_cost: float
    usage_date: datetime
    transaction_hash: Optional[str]
    billing_status: BillingStatus
    description: Optional[str]

    class Config:
        from_attributes = True


class RevenueAnalyticsResponse(BaseModel):
    total_revenue: float
    total_margin: float
    total_usage: int
    partner_count: int
    avg_margin_rate: float
    top_partners: List[Dict[str, Any]]
    revenue_by_tier: Dict[str, float]
    monthly_trend: List[Dict[str, Any]]


@router.post(
    "/partners/{partner_id}/energy/allocate",
    response_model=PartnerEnergyAllocationResponse,
    summary="파트너에게 에너지 할당",
)
async def allocate_energy_to_partner(
    partner_id: str,
    allocation_data: PartnerEnergyAllocationCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """파트너에게 에너지를 할당합니다."""

    # 마진 설정에서 기본 마진율 가져오기
    margin_config = (
        db.query(EnergyMarginConfig)
        .filter(
            EnergyMarginConfig.partner_tier == allocation_data.partner_tier,
            EnergyMarginConfig.is_active == True,
        )
        .first()
    )

    # 렌탈 가격 계산
    rental_price = allocation_data.purchase_price * (
        1 + allocation_data.markup_percentage / 100
    )

    # 할당 생성
    allocation = PartnerEnergyAllocation(
        partner_id=partner_id,
        partner_name=allocation_data.partner_name,
        partner_tier=allocation_data.partner_tier,
        allocated_amount=allocation_data.allocated_amount,
        remaining_amount=allocation_data.allocated_amount,
        purchase_price=allocation_data.purchase_price,
        markup_percentage=allocation_data.markup_percentage,
        rental_price=rental_price,
        billing_cycle=allocation_data.billing_cycle,
        expiry_date=allocation_data.expiry_date,
        notes=allocation_data.notes,
        created_by=current_admin.id,
    )

    db.add(allocation)
    db.commit()
    db.refresh(allocation)

    return allocation


@router.get(
    "/partners/{partner_id}/energy/allocations",
    response_model=List[PartnerEnergyAllocationResponse],
    summary="파트너 에너지 할당 목록",
)
async def get_partner_energy_allocations(
    partner_id: str,
    status: Optional[AllocationStatus] = Query(None, description="상태 필터"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """파트너의 에너지 할당 목록을 조회합니다."""

    query = db.query(PartnerEnergyAllocation).filter(
        PartnerEnergyAllocation.partner_id == partner_id
    )

    if status:
        query = query.filter(PartnerEnergyAllocation.status == status)

    allocations = query.offset(skip).limit(limit).all()
    return allocations


@router.put(
    "/partners/{partner_id}/energy/allocations/{allocation_id}",
    response_model=PartnerEnergyAllocationResponse,
    summary="에너지 할당 수정",
)
async def update_energy_allocation(
    partner_id: str,
    allocation_id: int,
    update_data: PartnerEnergyAllocationUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """에너지 할당을 수정합니다."""

    allocation = (
        db.query(PartnerEnergyAllocation)
        .filter(
            PartnerEnergyAllocation.id == allocation_id,
            PartnerEnergyAllocation.partner_id == partner_id,
        )
        .first()
    )

    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="에너지 할당을 찾을 수 없습니다.",
        )

    # 업데이트할 필드들
    update_dict = update_data.dict(exclude_unset=True)

    for field, value in update_dict.items():
        setattr(allocation, field, value)

    # 마진율이 변경된 경우 렌탈 가격 재계산
    if "markup_percentage" in update_dict:
        allocation.rental_price = allocation.purchase_price * (
            1 + allocation.markup_percentage / 100
        )

    allocation.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(allocation)

    return allocation


@router.post(
    "/partners/{partner_id}/energy/usage",
    response_model=PartnerEnergyUsageResponse,
    summary="에너지 사용량 기록",
)
async def record_energy_usage(
    partner_id: str,
    usage_data: PartnerEnergyUsageCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """파트너의 에너지 사용량을 기록합니다."""

    # 할당 확인
    allocation = (
        db.query(PartnerEnergyAllocation)
        .filter(
            PartnerEnergyAllocation.id == usage_data.allocation_id,
            PartnerEnergyAllocation.partner_id == partner_id,
            PartnerEnergyAllocation.status == AllocationStatus.ACTIVE,
        )
        .first()
    )

    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="활성화된 에너지 할당을 찾을 수 없습니다.",
        )

    # 사용 가능한 에너지량 확인
    if usage_data.used_amount > allocation.remaining_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"사용 가능한 에너지량({allocation.remaining_amount})을 초과했습니다.",
        )

    # 사용량 기록 생성
    usage = PartnerEnergyUsage(
        allocation_id=allocation.id,
        partner_id=partner_id,
        used_amount=usage_data.used_amount,
        unit_price=allocation.rental_price,
        total_cost=usage_data.used_amount * allocation.rental_price,
        transaction_hash=usage_data.transaction_hash,
        description=usage_data.description,
    )

    # 할당에서 사용량 차감
    allocation.remaining_amount -= usage_data.used_amount
    allocation.last_usage_date = datetime.now(timezone.utc)

    db.add(usage)
    db.commit()
    db.refresh(usage)

    return usage


@router.get(
    "/partners/{partner_id}/energy/usage",
    response_model=List[PartnerEnergyUsageResponse],
    summary="파트너 에너지 사용량 조회",
)
async def get_partner_energy_usage(
    partner_id: str,
    allocation_id: Optional[int] = Query(None, description="할당 ID"),
    start_date: Optional[datetime] = Query(None, description="시작일"),
    end_date: Optional[datetime] = Query(None, description="종료일"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """파트너의 에너지 사용량을 조회합니다."""

    query = db.query(PartnerEnergyUsage).filter(
        PartnerEnergyUsage.partner_id == partner_id
    )

    if allocation_id:
        query = query.filter(PartnerEnergyUsage.allocation_id == allocation_id)

    if start_date:
        query = query.filter(PartnerEnergyUsage.usage_date >= start_date)

    if end_date:
        query = query.filter(PartnerEnergyUsage.usage_date <= end_date)

    usage_records = (
        query.order_by(PartnerEnergyUsage.usage_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return usage_records


@router.get(
    "/admin/energy/revenue-analytics",
    response_model=RevenueAnalyticsResponse,
    summary="에너지 수익 분석",
)
async def get_revenue_analytics(
    start_date: Optional[datetime] = Query(None, description="시작일"),
    end_date: Optional[datetime] = Query(None, description="종료일"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """에너지 렌탈 수익을 분석합니다."""

    # 기본 기간 설정 (최근 30일)
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        start_date = end_date - timedelta(days=30)

    # 전체 할당 조회
    allocations_query = db.query(PartnerEnergyAllocation)

    if start_date or end_date:
        allocations_query = allocations_query.filter(
            PartnerEnergyAllocation.allocation_date >= start_date,
            PartnerEnergyAllocation.allocation_date <= end_date,
        )

    allocations = allocations_query.all()

    # 수익 계산
    total_revenue = sum(allocation.total_revenue for allocation in allocations)
    total_usage = sum(allocation.used_amount for allocation in allocations)
    partner_count = len(set(allocation.partner_id for allocation in allocations))

    # 파트너 등급별 수익
    revenue_by_tier = {}
    for tier in PartnerTier:
        tier_allocations = [a for a in allocations if a.partner_tier == tier]
        revenue_by_tier[tier.value] = sum(a.total_revenue for a in tier_allocations)

    # 상위 파트너 (수익 기준)
    partner_revenue = {}
    for allocation in allocations:
        if allocation.partner_id not in partner_revenue:
            partner_revenue[allocation.partner_id] = {
                "partner_name": allocation.partner_name,
                "revenue": 0,
                "usage": 0,
            }
        partner_revenue[allocation.partner_id]["revenue"] += allocation.total_revenue
        partner_revenue[allocation.partner_id]["usage"] += allocation.used_amount

    top_partners = sorted(
        [{"partner_id": k, **v} for k, v in partner_revenue.items()],
        key=lambda x: x["revenue"],
        reverse=True,
    )[:10]

    # 평균 마진율
    if allocations:
        avg_margin_rate = sum(a.markup_percentage for a in allocations) / len(
            allocations
        )
    else:
        avg_margin_rate = 0.0

    return RevenueAnalyticsResponse(
        total_revenue=total_revenue,
        total_margin=total_revenue,  # 실제로는 총 마진만 계산해야 함
        total_usage=total_usage,
        partner_count=partner_count,
        avg_margin_rate=avg_margin_rate,
        top_partners=top_partners,
        revenue_by_tier=revenue_by_tier,
        monthly_trend=[],  # 구현 필요
    )


# 마진 설정 관리
class EnergyMarginConfigCreate(BaseModel):
    partner_tier: PartnerTier
    default_margin_percentage: float = Field(..., ge=0, le=100)
    min_margin_percentage: float = Field(..., ge=0, le=100)
    max_margin_percentage: float = Field(..., ge=0, le=100)
    volume_threshold_1: int = Field(1000000, gt=0)
    volume_margin_1: float = Field(0.0, ge=0)
    volume_threshold_2: int = Field(10000000, gt=0)
    volume_margin_2: float = Field(0.0, ge=0)


class EnergyMarginConfigResponse(BaseModel):
    id: int
    partner_tier: PartnerTier
    default_margin_percentage: float
    min_margin_percentage: float
    max_margin_percentage: float
    volume_threshold_1: int
    volume_margin_1: float
    volume_threshold_2: int
    volume_margin_2: float
    effective_date: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get(
    "/admin/energy/margin-config",
    response_model=List[EnergyMarginConfigResponse],
    summary="마진 설정 조회",
)
async def get_margin_config(
    db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin_user)
):
    """에너지 마진 설정을 조회합니다."""
    configs = (
        db.query(EnergyMarginConfig).filter(EnergyMarginConfig.is_active == True).all()
    )
    return configs


@router.post(
    "/admin/energy/margin-config",
    response_model=EnergyMarginConfigResponse,
    summary="마진 설정 생성/수정",
)
async def set_margin_config(
    config_data: EnergyMarginConfigCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    """에너지 마진 설정을 생성하거나 수정합니다."""

    # 기존 설정 비활성화
    existing_config = (
        db.query(EnergyMarginConfig)
        .filter(
            EnergyMarginConfig.partner_tier == config_data.partner_tier,
            EnergyMarginConfig.is_active == True,
        )
        .first()
    )

    if existing_config:
        existing_config.is_active = False

    # 새 설정 생성
    new_config = EnergyMarginConfig(
        partner_tier=config_data.partner_tier,
        default_margin_percentage=config_data.default_margin_percentage,
        min_margin_percentage=config_data.min_margin_percentage,
        max_margin_percentage=config_data.max_margin_percentage,
        volume_threshold_1=config_data.volume_threshold_1,
        volume_margin_1=config_data.volume_margin_1,
        volume_threshold_2=config_data.volume_threshold_2,
        volume_margin_2=config_data.volume_margin_2,
        created_by=current_admin.id,
    )

    db.add(new_config)
    db.commit()
    db.refresh(new_config)

    return new_config
