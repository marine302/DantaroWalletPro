"""파트너사 수수료 및 정책 관리 API 엔드포인트 - Doc #26"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_current_admin_user, get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.models.user import User
from app.schemas.fee_policy import (  # 수수료 정책 스키마; 출금 정책 스키마; 에너지 정책 스키마; 사용자 등급 스키마
    FeeCalculationRequest,
    FeeCalculationResponse,
    FeeTierCreate,
    FeeTierResponse,
    PartnerEnergyPolicyCreate,
    PartnerEnergyPolicyResponse,
    PartnerEnergyPolicyUpdate,
    PartnerFeePolicyCreate,
    PartnerFeePolicyResponse,
    PartnerFeePolicyUpdate,
    PartnerPolicyCalculationLogResponse,
    PartnerWithdrawalPolicyCreate,
    PartnerWithdrawalPolicyResponse,
    PartnerWithdrawalPolicyUpdate,
    UserTierCreate,
    UserTierResponse,
    UserTierUpdate,
)
from app.services.fee.partner_fee_policy_service import PartnerFeePolicyService
from app.services.fee.partner_policy_service import PartnerPolicyService

router = APIRouter()


# 헬퍼 함수
def safe_get_user_id(user: User) -> int:
    """User 객체에서 안전하게 ID를 가져옵니다."""
    try:
        if hasattr(user, "id"):
            user_id = getattr(user, "id")
            if hasattr(user_id, "__class__") and "Column" in str(user_id.__class__):
                # SQLAlchemy Column인 경우 기본값 반환
                return 1  # 기본 admin ID
            return int(user_id)
        return 1  # 기본 admin ID
    except (AttributeError, TypeError, ValueError):
        return 1  # 기본 admin ID


# === 파트너 수수료 정책 관리 ===


@router.post(
    "/partners/{partner_id}/fee-policy", response_model=PartnerFeePolicyResponse
)
async def create_partner_fee_policy(
    partner_id: str,
    policy_data: PartnerFeePolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """파트너사 수수료 정책을 생성합니다."""
    service = PartnerFeePolicyService(db)
    return await service.create_partner_fee_policy(
        partner_id=partner_id,
        policy_data=policy_data,
        admin_id=safe_get_user_id(current_user),
    )


@router.get(
    "/partners/{partner_id}/fee-policy",
    response_model=Optional[PartnerFeePolicyResponse],
)
async def get_partner_fee_policy(
    partner_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """파트너사 수수료 정책을 조회합니다."""
    service = PartnerFeePolicyService(db)
    policy = await service.get_partner_fee_policy(partner_id)

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"수수료 정책을 찾을 수 없습니다: {partner_id}",
        )

    return policy


@router.put(
    "/partners/{partner_id}/fee-policy", response_model=PartnerFeePolicyResponse
)
async def update_partner_fee_policy(
    partner_id: str,
    update_data: PartnerFeePolicyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """파트너사 수수료 정책을 업데이트합니다."""
    service = PartnerFeePolicyService(db)
    return await service.update_partner_fee_policy(
        partner_id=partner_id,
        update_data=update_data,
        admin_id=safe_get_user_id(current_user),
    )


@router.delete("/partners/{partner_id}/fee-policy")
async def delete_partner_fee_policy(
    partner_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """파트너사 수수료 정책을 삭제합니다."""
    service = PartnerFeePolicyService(db)
    success = await service.delete_partner_fee_policy(
        partner_id=partner_id, admin_id=safe_get_user_id(current_user)
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"수수료 정책을 찾을 수 없습니다: {partner_id}",
        )

    return {"message": "수수료 정책이 삭제되었습니다"}


# === 구간별 수수료 관리 ===


@router.post("/partners/{partner_id}/fee-tiers", response_model=FeeTierResponse)
async def create_fee_tier(
    partner_id: str,
    tier_data: FeeTierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """구간별 수수료를 생성합니다."""
    service = PartnerFeePolicyService(db)
    return await service.create_fee_tier(
        partner_id=partner_id,
        tier_data=tier_data,
        admin_id=safe_get_user_id(current_user),
    )


@router.get("/partners/{partner_id}/fee-tiers", response_model=List[FeeTierResponse])
async def get_fee_tiers(
    partner_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """파트너의 모든 구간별 수수료를 조회합니다."""
    service = PartnerFeePolicyService(db)
    return await service.get_fee_tiers(partner_id)


# === 수수료 계산 ===


@router.post(
    "/partners/{partner_id}/calculate-fee", response_model=FeeCalculationResponse
)
async def calculate_fee(
    partner_id: str,
    calculation_request: FeeCalculationRequest,
    user_id: Optional[int] = Query(None, description="사용자 ID (등급 할인 적용용)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """수수료를 계산합니다."""
    service = PartnerFeePolicyService(db)
    return await service.calculate_fee(
        partner_id=partner_id, calculation_request=calculation_request, user_id=user_id
    )


@router.get(
    "/partners/{partner_id}/calculation-logs",
    response_model=List[PartnerPolicyCalculationLogResponse],
)
async def get_calculation_logs(
    partner_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user_id: Optional[int] = Query(None),
    calculation_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """수수료 계산 로그를 조회합니다."""
    service = PartnerFeePolicyService(db)
    return await service.get_calculation_logs(
        partner_id=partner_id,
        limit=limit,
        offset=offset,
        user_id=user_id,
        calculation_type=calculation_type,
    )


# === 출금 정책 관리 ===


@router.post(
    "/partners/{partner_id}/withdrawal-policy",
    response_model=PartnerWithdrawalPolicyResponse,
)
async def create_withdrawal_policy(
    partner_id: str,
    policy_data: PartnerWithdrawalPolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """파트너사 출금 정책을 생성합니다."""
    service = PartnerPolicyService(db)
    return await service.create_withdrawal_policy(
        partner_id=partner_id,
        policy_data=policy_data,
        admin_id=safe_get_user_id(current_user),
    )


@router.get(
    "/partners/{partner_id}/withdrawal-policy",
    response_model=Optional[PartnerWithdrawalPolicyResponse],
)
async def get_withdrawal_policy(
    partner_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """파트너사 출금 정책을 조회합니다."""
    service = PartnerPolicyService(db)
    policy = await service.get_withdrawal_policy(partner_id)

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"출금 정책을 찾을 수 없습니다: {partner_id}",
        )

    return policy


@router.put(
    "/partners/{partner_id}/withdrawal-policy",
    response_model=PartnerWithdrawalPolicyResponse,
)
async def update_withdrawal_policy(
    partner_id: str,
    update_data: PartnerWithdrawalPolicyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """파트너사 출금 정책을 업데이트합니다."""
    service = PartnerPolicyService(db)
    return await service.update_withdrawal_policy(
        partner_id=partner_id,
        update_data=update_data,
        admin_id=safe_get_user_id(current_user),
    )


@router.post("/partners/{partner_id}/validate-withdrawal")
async def validate_withdrawal_request(
    partner_id: str,
    amount: float = Query(..., gt=0),
    user_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """출금 요청을 정책에 따라 검증합니다."""
    service = PartnerPolicyService(db)
    return await service.validate_withdrawal_request(
        partner_id=partner_id, amount=amount, user_id=user_id
    )


# === 에너지 정책 관리 ===


@router.post(
    "/partners/{partner_id}/energy-policy", response_model=PartnerEnergyPolicyResponse
)
async def create_energy_policy(
    partner_id: str,
    policy_data: PartnerEnergyPolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """파트너사 에너지 정책을 생성합니다."""
    service = PartnerPolicyService(db)
    return await service.create_energy_policy(
        partner_id=partner_id,
        policy_data=policy_data,
        admin_id=safe_get_user_id(current_user),
    )


@router.get(
    "/partners/{partner_id}/energy-policy",
    response_model=Optional[PartnerEnergyPolicyResponse],
)
async def get_energy_policy(
    partner_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """파트너사 에너지 정책을 조회합니다."""
    service = PartnerPolicyService(db)
    policy = await service.get_energy_policy(partner_id)

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"에너지 정책을 찾을 수 없습니다: {partner_id}",
        )

    return policy


@router.put(
    "/partners/{partner_id}/energy-policy", response_model=PartnerEnergyPolicyResponse
)
async def update_energy_policy(
    partner_id: str,
    update_data: PartnerEnergyPolicyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """파트너사 에너지 정책을 업데이트합니다."""
    service = PartnerPolicyService(db)
    return await service.update_energy_policy(
        partner_id=partner_id,
        update_data=update_data,
        admin_id=safe_get_user_id(current_user),
    )


@router.post("/partners/{partner_id}/validate-energy")
async def validate_energy_usage(
    partner_id: str,
    required_energy: int = Query(..., gt=0),
    current_available: int = Query(..., ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """에너지 사용 요청을 정책에 따라 검증합니다."""
    service = PartnerPolicyService(db)
    return await service.validate_energy_usage(
        partner_id=partner_id,
        required_energy=required_energy,
        current_available=current_available,
    )


# === 사용자 등급 관리 ===


@router.post(
    "/partners/{partner_id}/users/{user_id}/tier", response_model=UserTierResponse
)
async def create_user_tier(
    partner_id: str,
    user_id: int,
    tier_data: UserTierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """사용자 등급을 생성합니다."""
    service = PartnerPolicyService(db)
    return await service.create_user_tier(
        partner_id=partner_id,
        user_id=user_id,
        tier_data=tier_data,
        admin_id=safe_get_user_id(current_user),
    )


@router.get(
    "/partners/{partner_id}/users/{user_id}/tier",
    response_model=Optional[UserTierResponse],
)
async def get_user_tier(
    partner_id: str,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """활성 사용자 등급을 조회합니다."""
    service = PartnerPolicyService(db)
    tier = await service.get_user_tier(partner_id, user_id)

    if not tier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"활성 사용자 등급을 찾을 수 없습니다: {partner_id}/{user_id}",
        )

    return tier


@router.get("/partners/{partner_id}/user-tiers", response_model=List[UserTierResponse])
async def get_partner_user_tiers(
    partner_id: str,
    is_active: Optional[bool] = Query(True),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """파트너의 모든 사용자 등급을 조회합니다."""
    service = PartnerPolicyService(db)
    return await service.get_partner_user_tiers(
        partner_id=partner_id, is_active=is_active, limit=limit, offset=offset
    )


@router.put(
    "/partners/{partner_id}/users/{user_id}/tier", response_model=UserTierResponse
)
async def update_user_tier(
    partner_id: str,
    user_id: int,
    update_data: UserTierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """사용자 등급을 업데이트합니다."""
    service = PartnerPolicyService(db)
    return await service.update_user_tier(
        partner_id=partner_id,
        user_id=user_id,
        update_data=update_data,
        admin_id=safe_get_user_id(current_user),
    )


@router.delete("/partners/{partner_id}/users/{user_id}/tier")
async def deactivate_user_tier(
    partner_id: str,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """사용자 등급을 비활성화합니다."""
    service = PartnerPolicyService(db)
    success = await service.deactivate_user_tier(
        partner_id=partner_id, user_id=user_id, admin_id=safe_get_user_id(current_user)
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"활성 사용자 등급을 찾을 수 없습니다: {partner_id}/{user_id}",
        )

    return {"message": "사용자 등급이 비활성화되었습니다"}
