"""
관리자 패널 API 라우터.
관리자 전용 엔드포인트들을 제공합니다.
"""
from typing import Any, Dict, List, Optional

from app.core.auth import get_current_super_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.admin import (
    BackupCreateRequest,
    BackupInfoResponse,
    PaginatedTransactionsResponse,
    PaginatedUsersResponse,
    SuspiciousActivityResponse,
    SystemRiskSummaryResponse,
    SystemStatsResponse,
    UserDetailResponse,
    UserRiskAnalysisResponse,
    UserUpdateRequest,
)
from app.services.admin_service import AdminService
from app.services.backup_service import BackupService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["admin"])


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    current_admin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    시스템 전체 통계 조회

    관리자만 접근 가능한 시스템 통계 정보를 반환합니다.
    """
    admin_service = AdminService(db)
    return await admin_service.get_system_stats()


@router.get("/users", response_model=PaginatedUsersResponse)
async def get_users_list(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    search: Optional[str] = Query(None, description="이메일 검색"),
    is_active: Optional[bool] = Query(None, description="활성 상태 필터"),
    is_admin: Optional[bool] = Query(None, description="관리자 필터"),
    current_admin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    사용자 목록 조회

    페이지네이션과 필터링을 지원하는 사용자 목록을 반환합니다.
    """
    admin_service = AdminService(db)
    return await admin_service.get_users_list(
        page=page, size=size, search=search, is_active=is_active, is_admin=is_admin
    )


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: int,
    current_admin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    사용자 상세 정보 조회

    특정 사용자의 상세 정보와 통계를 반환합니다.
    """
    admin_service = AdminService(db)
    user_detail = await admin_service.get_user_detail(user_id)

    if not user_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다"
        )

    return user_detail


@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdateRequest,
    current_admin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    사용자 정보 수정

    관리자가 사용자의 상태를 변경할 수 있습니다.
    """
    admin_service = AdminService(db)

    # 업데이트할 필드만 추출
    updates = {}
    if user_update.is_active is not None:
        updates["is_active"] = user_update.is_active
    if user_update.is_verified is not None:
        updates["is_verified"] = user_update.is_verified
    if user_update.is_admin is not None:
        updates["is_admin"] = user_update.is_admin

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="수정할 필드가 없습니다"
        )

    success = await admin_service.update_user(user_id, updates)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없거나 수정에 실패했습니다"
        )

    return {"message": "사용자 정보가 수정되었습니다"}


@router.get("/transactions", response_model=PaginatedTransactionsResponse)
async def get_transaction_monitor(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(50, ge=1, le=100, description="페이지 크기"),
    status: Optional[str] = Query(None, description="거래 상태 필터"),
    user_id: Optional[int] = Query(None, description="사용자 ID 필터"),
    hours: int = Query(24, ge=1, le=168, description="조회 시간 범위(시간)"),
    current_admin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    거래 모니터링

    최근 거래 내역을 모니터링할 수 있습니다.
    """
    admin_service = AdminService(db)
    return await admin_service.get_transaction_monitor(
        page=page, size=size, status=status, user_id=user_id, hours=hours
    )


@router.get("/suspicious-activities")
async def get_suspicious_activities(
    limit: int = Query(20, ge=1, le=100, description="조회 개수"),
    current_admin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    의심스러운 활동 탐지

    시스템에서 탐지된 의심스러운 활동들을 반환합니다.
    """
    admin_service = AdminService(db)
    return await admin_service.get_suspicious_activities(limit=limit)


@router.post("/users/{user_id}/disable")
async def disable_user(
    user_id: int,
    current_admin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    사용자 비활성화

    특정 사용자를 비활성화합니다.
    """
    admin_service = AdminService(db)
    success = await admin_service.update_user(user_id, {"is_active": False})

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다"
        )

    return {"message": "사용자가 비활성화되었습니다"}


@router.post("/users/{user_id}/enable")
async def enable_user(
    user_id: int,
    current_admin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    사용자 활성화

    비활성화된 사용자를 다시 활성화합니다.
    """
    admin_service = AdminService(db)
    success = await admin_service.update_user(user_id, {"is_active": True})

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다"
        )

    return {"message": "사용자가 활성화되었습니다"}


@router.post("/users/{user_id}/verify")
async def verify_user(
    user_id: int,
    current_admin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    사용자 이메일 인증

    관리자가 사용자의 이메일을 인증 처리합니다.
    """
    admin_service = AdminService(db)
    success = await admin_service.update_user(user_id, {"is_verified": True})

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다"
        )

    return {"message": "사용자 이메일이 인증되었습니다"}


@router.post("/backup", response_model=BackupInfoResponse)
async def create_backup(
    req: BackupCreateRequest,
    current_admin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """DB 백업 생성"""
    backup_service = BackupService(db)
    return await backup_service.create_backup(req.backup_type, req.description)


@router.get("/backups", response_model=List[BackupInfoResponse])
async def list_backups(
    current_admin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """백업 목록 조회"""
    backup_service = BackupService(db)
    return await backup_service.list_backups()


@router.post("/restore")
async def restore_backup(
    file_path: str,
    current_admin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """지정된 백업 파일로 복구"""
    backup_service = BackupService(db)
    success = await backup_service.restore_backup(file_path)
    if not success:
        raise HTTPException(status_code=404, detail="백업 파일을 찾을 수 없습니다")
    return {"message": "복구가 완료되었습니다"}


@router.get("/users/{user_id}/risk", response_model=UserRiskAnalysisResponse)
async def get_user_risk_analysis(
    user_id: int,
    current_admin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """특정 사용자 리스크 분석"""
    admin_service = AdminService(db)
    return await admin_service.get_user_risk_analysis(user_id)


@router.get("/risk-summary", response_model=SystemRiskSummaryResponse)
async def get_system_risk_summary(
    current_admin = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """시스템 전체 리스크 요약"""
    admin_service = AdminService(db)
    return await admin_service.get_system_risk_summary()


# 새로 추가된 관리자 기능들 import
from app.api.v1.endpoints.admin import energy, fees, partners

# 하위 라우터 등록
router.include_router(energy.router, prefix="/energy")  # Uses admin_energy tag from router
router.include_router(fees.router, prefix="/fees")  # Uses admin_fees tag from router
router.include_router(partners.router, prefix="/partners")  # Uses admin_partners tag from router
