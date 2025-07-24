"""
파트너사 온보딩 자동화 API 엔드포인트 - Doc #29
새 파트너사의 완전 자동화된 온보딩 API를 제공합니다.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import get_current_admin_user, get_current_user, get_db
from app.core.logger import get_logger
from app.models.partner import Partner
from app.models.partner_onboarding import (
    OnboardingChecklist,
    OnboardingLog,
    OnboardingStatus,
    OnboardingStep,
    OnboardingStepStatus,
    PartnerOnboarding,
)
from app.models.user import User
from app.schemas.onboarding import (
    ChecklistUpdateRequest,
    OnboardingChecklistResponse,
    OnboardingCreateRequest,
    OnboardingDetailResponse,
    OnboardingErrorResponse,
    OnboardingFilterRequest,
    OnboardingListResponse,
    OnboardingLogRequest,
    OnboardingLogResponse,
    OnboardingProgressResponse,
    OnboardingResponse,
    OnboardingStatsResponse,
    OnboardingStepResponse,
    OnboardingSuccessResponse,
    ProgressUpdateRequest,
    StepStatusUpdateRequest,
)
from app.services.onboarding.simple_onboarding_service import SimpleOnboardingService

logger = get_logger(__name__)


# Helper functions for safely extracting values from SQLAlchemy columns
def safe_int(value) -> int:
    """Safely extract integer value from SQLAlchemy column or return actual value."""
    if hasattr(value, "__class__") and hasattr(value.__class__, "__name__"):
        if "Column" in value.__class__.__name__:
            return int(value)
    return value


def safe_str(value) -> str:
    """Safely extract string value from SQLAlchemy column or return actual value."""
    if hasattr(value, "__class__") and hasattr(value.__class__, "__name__"):
        if "Column" in value.__class__.__name__:
            return str(value)
    return value


def safe_optional_str(value) -> Optional[str]:
    """Safely extract optional string value from SQLAlchemy column or return actual value."""
    if value is None:
        return None
    if hasattr(value, "__class__") and hasattr(value.__class__, "__name__"):
        if "Column" in value.__class__.__name__:
            return str(value)
    return value


def safe_optional_int(value) -> Optional[int]:
    """Safely extract optional integer value from SQLAlchemy column or return actual value."""
    if value is None:
        return None
    if hasattr(value, "__class__") and hasattr(value.__class__, "__name__"):
        if "Column" in value.__class__.__name__:
            return int(value)
    return value


def safe_bool(value) -> bool:
    """Safely extract boolean value from SQLAlchemy column or return actual value."""
    if hasattr(value, "__class__") and hasattr(value.__class__, "__name__"):
        if "Column" in value.__class__.__name__:
            return bool(value)
    return value


def safe_enum(value, enum_class: type):
    """Safely extract enum value from SQLAlchemy column or return actual value."""
    if hasattr(value, "__class__") and hasattr(value.__class__, "__name__"):
        if "Column" in value.__class__.__name__:
            return enum_class(str(value))
    if isinstance(value, enum_class):
        return value
    return enum_class(value)


router = APIRouter()


# === 온보딩 생성 및 조회 ===


@router.post("/", response_model=OnboardingSuccessResponse)
async def create_onboarding(
    request: OnboardingCreateRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """새 파트너사 온보딩 프로세스를 시작합니다."""
    try:
        service = SimpleOnboardingService(db)

        # 설정 데이터 구성
        configuration_data = {
            "partner_id": request.partner_id,
            "company_name": request.company_name,
            "contact_email": request.contact_email,
            "business_type": request.business_type,
            "auto_proceed": request.auto_proceed,
            "notification_email": request.notification_email,
            "notification_webhook": request.notification_webhook,
            "main_wallet_address": request.main_wallet_address,
            "brand_color": request.brand_color,
            "logo_url": request.logo_url,
        }

        # additional_config가 있으면 추가
        if hasattr(request, "additional_config") and request.additional_config:
            configuration_data.update(request.additional_config)

        onboarding = await service.create_onboarding(
            request.partner_id, configuration_data
        )

        # 시작 로그 추가
        await service.add_onboarding_log(
            safe_int(safe_int(onboarding.id)),
            "info",
            f"온보딩 프로세스가 관리자 {current_user.email}에 의해 시작되었습니다.",
            {"admin_id": current_user.id, "admin_email": current_user.email},
        )

        return OnboardingSuccessResponse(
            message="온보딩 프로세스가 성공적으로 시작되었습니다.",
            onboarding_id=safe_int(safe_int(onboarding.id)),
            partner_id=request.partner_id,
            data={"auto_proceed": request.auto_proceed},
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"온보딩 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="온보딩 생성 중 오류가 발생했습니다.",
        )


@router.get("/{partner_id}", response_model=OnboardingDetailResponse)
async def get_onboarding_detail(
    partner_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """파트너사 온보딩 상세 정보를 조회합니다."""
    try:
        service = SimpleOnboardingService(db)

        # 온보딩 기본 정보 조회
        onboarding = await service.get_onboarding_status(partner_id)
        if not onboarding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"파트너 {partner_id}의 온보딩 정보를 찾을 수 없습니다.",
            )

        # 상세 정보 조회
        steps = await service.get_onboarding_steps(safe_int(safe_int(onboarding.id)))
        checklist = await service.get_onboarding_checklist(
            safe_int(safe_int(onboarding.id))
        )
        logs = await service.get_onboarding_logs(safe_int(safe_int(onboarding.id)))

        # 응답 구성
        return OnboardingDetailResponse(
            **onboarding.__dict__,
            steps=[OnboardingStepResponse(**step.__dict__) for step in steps],
            checklist=[
                OnboardingChecklistResponse(**item.__dict__) for item in checklist
            ],
            logs=[OnboardingLogResponse(**log.__dict__) for log in logs],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"온보딩 상세 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="온보딩 정보 조회 중 오류가 발생했습니다.",
        )


@router.get("/{partner_id}/progress", response_model=OnboardingProgressResponse)
async def get_onboarding_progress(
    partner_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """파트너사 온보딩 진행 상황을 조회합니다."""
    try:
        service = SimpleOnboardingService(db)

        onboarding = await service.get_onboarding_status(partner_id)
        if not onboarding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"파트너 {partner_id}의 온보딩 정보를 찾을 수 없습니다.",
            )

        steps = await service.get_onboarding_steps(safe_int(safe_int(onboarding.id)))

        # 현재 단계 정보
        current_step_name = None
        next_step_name = None

        current_step_num = safe_int(onboarding.current_step)

        for step in steps:
            step_num = safe_int(step.step_number)
            if step_num == current_step_num:
                current_step_name = safe_str(step.step_name)
            elif step_num == current_step_num + 1:
                next_step_name = safe_str(step.step_name)

        return OnboardingProgressResponse(
            partner_id=partner_id,
            status=safe_enum(onboarding.status, OnboardingStatus),
            current_step=safe_int(onboarding.current_step),
            total_steps=safe_int(onboarding.total_steps),
            progress_percentage=safe_int(onboarding.progress_percentage),
            current_step_name=current_step_name,
            next_step_name=next_step_name,
            estimated_completion_time=None,  # 계산 로직 필요
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"온보딩 진행 상황 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="온보딩 진행 상황 조회 중 오류가 발생했습니다.",
        )


# === 온보딩 관리 ===


@router.put(
    "/{partner_id}/steps/{step_number}/status", response_model=OnboardingSuccessResponse
)
async def update_step_status(
    partner_id: str,
    step_number: int,
    request: StepStatusUpdateRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """온보딩 단계 상태를 업데이트합니다."""
    try:
        service = SimpleOnboardingService(db)

        # 온보딩 확인
        onboarding = await service.get_onboarding_status(partner_id)
        if not onboarding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"파트너 {partner_id}의 온보딩 정보를 찾을 수 없습니다.",
            )

        # 단계 상태 업데이트
        success = await service.update_step_status(
            safe_int(safe_int(onboarding.id)),
            step_number,
            request.status,
            request.result_data,
            request.error_message,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="단계 상태 업데이트에 실패했습니다.",
            )

        # 로그 추가
        await service.add_onboarding_log(
            safe_int(safe_int(onboarding.id)),
            "info",
            f"단계 {step_number} 상태가 {request.status.value}로 업데이트되었습니다.",
            {
                "step_number": step_number,
                "new_status": request.status.value,
                "admin_id": current_user.id,
            },
            step_number,
        )

        return OnboardingSuccessResponse(
            message=f"단계 {step_number} 상태가 성공적으로 업데이트되었습니다.",
            partner_id=partner_id,
            data={"step_number": step_number, "status": request.status.value},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"단계 상태 업데이트 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="단계 상태 업데이트 중 오류가 발생했습니다.",
        )


@router.put("/{partner_id}/progress", response_model=OnboardingSuccessResponse)
async def update_onboarding_progress(
    partner_id: str,
    request: ProgressUpdateRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """온보딩 진행률을 업데이트합니다."""
    try:
        service = SimpleOnboardingService(db)

        # 온보딩 확인
        onboarding = await service.get_onboarding_status(partner_id)
        if not onboarding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"파트너 {partner_id}의 온보딩 정보를 찾을 수 없습니다.",
            )

        # 진행률 업데이트
        success = await service.update_onboarding_progress(
            safe_int(safe_int(onboarding.id)),
            request.current_step,
            request.progress_percentage,
            request.status,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="온보딩 진행률 업데이트에 실패했습니다.",
            )

        # 로그 추가
        await service.add_onboarding_log(
            safe_int(safe_int(onboarding.id)),
            "info",
            f"온보딩 진행률이 {request.progress_percentage}%로 업데이트되었습니다.",
            {
                "current_step": request.current_step,
                "progress_percentage": request.progress_percentage,
                "status": request.status.value if request.status else None,
                "admin_id": current_user.id,
            },
        )

        return OnboardingSuccessResponse(
            message="온보딩 진행률이 성공적으로 업데이트되었습니다.",
            partner_id=partner_id,
            data={
                "current_step": request.current_step,
                "progress_percentage": request.progress_percentage,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"온보딩 진행률 업데이트 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="온보딩 진행률 업데이트 중 오류가 발생했습니다.",
        )


@router.post("/{partner_id}/complete", response_model=OnboardingSuccessResponse)
async def complete_onboarding(
    partner_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """온보딩을 완료 처리합니다."""
    try:
        service = SimpleOnboardingService(db)

        # 온보딩 확인
        onboarding = await service.get_onboarding_status(partner_id)
        if not onboarding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"파트너 {partner_id}의 온보딩 정보를 찾을 수 없습니다.",
            )

        # 온보딩 완료
        success = await service.complete_onboarding(safe_int(onboarding.id))

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="온보딩 완료 처리에 실패했습니다.",
            )

        # 완료 로그 추가
        await service.add_onboarding_log(
            safe_int(safe_int(onboarding.id)),
            "info",
            f"온보딩이 관리자 {current_user.email}에 의해 완료되었습니다.",
            {
                "admin_id": current_user.id,
                "admin_email": current_user.email,
                "completion_time": datetime.utcnow().isoformat(),
            },
        )

        return OnboardingSuccessResponse(
            message="온보딩이 성공적으로 완료되었습니다.",
            partner_id=partner_id,
            data={"completed_by": current_user.email},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"온보딩 완료 처리 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="온보딩 완료 처리 중 오류가 발생했습니다.",
        )


# === 체크리스트 관리 ===


@router.put("/{partner_id}/checklist", response_model=OnboardingSuccessResponse)
async def update_checklist_item(
    partner_id: str,
    request: ChecklistUpdateRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """체크리스트 항목을 업데이트합니다."""
    try:
        service = SimpleOnboardingService(db)

        # 온보딩 확인
        onboarding = await service.get_onboarding_status(partner_id)
        if not onboarding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"파트너 {partner_id}의 온보딩 정보를 찾을 수 없습니다.",
            )

        # 체크리스트 항목 업데이트
        completed_by = (
            request.completed_by
            if request.completed_by
            else safe_str(current_user.email)
        )
        success = await service.update_checklist_item(
            safe_int(onboarding.id),
            request.item_name,
            request.is_completed,
            completed_by,
            request.notes,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="체크리스트 항목 업데이트에 실패했습니다.",
            )

        # 로그 추가
        await service.add_onboarding_log(
            safe_int(safe_int(onboarding.id)),
            "info",
            f"체크리스트 항목 '{request.item_name}'이 {'완료' if request.is_completed else '미완료'}로 업데이트되었습니다.",
            {
                "item_name": request.item_name,
                "is_completed": request.is_completed,
                "completed_by": request.completed_by or current_user.email,
                "notes": request.notes,
            },
        )

        return OnboardingSuccessResponse(
            message=f"체크리스트 항목이 성공적으로 업데이트되었습니다.",
            partner_id=partner_id,
            data={"item_name": request.item_name, "is_completed": request.is_completed},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"체크리스트 항목 업데이트 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="체크리스트 항목 업데이트 중 오류가 발생했습니다.",
        )


@router.get("/{partner_id}/checklist", response_model=List[OnboardingChecklistResponse])
async def get_onboarding_checklist(
    partner_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """온보딩 체크리스트를 조회합니다."""
    try:
        service = SimpleOnboardingService(db)

        # 온보딩 확인
        onboarding = await service.get_onboarding_status(partner_id)
        if not onboarding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"파트너 {partner_id}의 온보딩 정보를 찾을 수 없습니다.",
            )

        # 체크리스트 조회
        checklist = await service.get_onboarding_checklist(safe_int(onboarding.id))

        return [OnboardingChecklistResponse(**item.__dict__) for item in checklist]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"온보딩 체크리스트 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="온보딩 체크리스트 조회 중 오류가 발생했습니다.",
        )


# === 로그 관리 ===


@router.post("/{partner_id}/logs", response_model=OnboardingSuccessResponse)
async def add_onboarding_log(
    partner_id: str,
    request: OnboardingLogRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """온보딩 로그를 추가합니다."""
    try:
        service = SimpleOnboardingService(db)

        # 온보딩 확인
        onboarding = await service.get_onboarding_status(partner_id)
        if not onboarding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"파트너 {partner_id}의 온보딩 정보를 찾을 수 없습니다.",
            )

        # 로그 추가
        success = await service.add_onboarding_log(
            safe_int(safe_int(onboarding.id)),
            request.level,
            request.message,
            request.details,
            request.step_number,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="온보딩 로그 추가에 실패했습니다.",
            )

        return OnboardingSuccessResponse(
            message="온보딩 로그가 성공적으로 추가되었습니다.",
            partner_id=partner_id,
            data={"level": request.level, "message": request.message},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"온보딩 로그 추가 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="온보딩 로그 추가 중 오류가 발생했습니다.",
        )


@router.get("/{partner_id}/logs", response_model=List[OnboardingLogResponse])
async def get_onboarding_logs(
    partner_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """온보딩 로그를 조회합니다."""
    try:
        service = SimpleOnboardingService(db)

        # 온보딩 확인
        onboarding = await service.get_onboarding_status(partner_id)
        if not onboarding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"파트너 {partner_id}의 온보딩 정보를 찾을 수 없습니다.",
            )

        # 로그 조회
        logs = await service.get_onboarding_logs(safe_int(onboarding.id))

        # 제한 적용
        limited_logs = logs[:limit] if limit > 0 else logs

        return [OnboardingLogResponse(**log.__dict__) for log in limited_logs]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"온보딩 로그 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="온보딩 로그 조회 중 오류가 발생했습니다.",
        )


@router.get("/admin/all")
async def get_onboarding_list(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """파트너 온보딩 목록을 조회합니다."""
    try:
        # 기본 쿼리
        query = select(PartnerOnboarding)

        # 상태 필터
        if status:
            query = query.where(PartnerOnboarding.status == status)

        # 정렬 및 페이징
        query = (
            query.order_by(PartnerOnboarding.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await db.execute(query)
        onboardings = result.scalars().all()

        # 응답 데이터 구성
        items = []
        for onboarding in onboardings:
            created_at = getattr(onboarding, "created_at", None)
            updated_at = getattr(onboarding, "updated_at", None)
            items.append(
                {
                    "id": onboarding.id,
                    "partner_id": onboarding.partner_id,
                    "status": (
                        onboarding.status.value
                        if hasattr(onboarding.status, "value")
                        else str(onboarding.status)
                    ),
                    "current_step": onboarding.current_step,
                    "total_steps": onboarding.total_steps,
                    "progress_percentage": onboarding.progress_percentage,
                    "created_at": created_at.isoformat() if created_at else None,
                    "updated_at": updated_at.isoformat() if updated_at else None,
                }
            )

        return {"items": items, "total": len(items), "limit": limit, "offset": offset}

    except Exception as e:
        logger.error(f"온보딩 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=500, detail=f"온보딩 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


# === 온보딩 생성 및 조회 ===
