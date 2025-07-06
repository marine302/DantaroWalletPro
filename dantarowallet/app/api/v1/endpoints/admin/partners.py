"""
파트너사 관리 API 엔드포인트
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_admin_user
from app.models.user import User

router = APIRouter(tags=["파트너사 관리"])


@router.get("/")
async def get_partners_list(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    search: Optional[str] = Query(None, description="파트너사명 검색"),
    is_active: Optional[bool] = Query(None, description="활성 상태 필터"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    파트너사 목록을 조회합니다.
    """
    # TODO: 파트너사 목록 조회 로직 구현
    # partner_service = PartnerService(db)
    # return await partner_service.get_partners_list(page, size, search, is_active)
    return {"message": "파트너사 목록 조회 - 구현 필요"}


@router.post("/")
async def create_partner(
    name: str,
    domain: str,
    webhook_url: Optional[str] = None,
    commission_rate: float = 0.0,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    새로운 파트너사를 등록합니다.
    """
    # TODO: 파트너사 등록 로직 구현
    # partner_service = PartnerService(db)
    # return await partner_service.create_partner(name, domain, webhook_url, commission_rate)
    return {"message": "파트너사 등록 - 구현 필요", "name": name}


@router.patch("/{partner_id}")
async def update_partner(
    partner_id: int,
    name: Optional[str] = None,
    domain: Optional[str] = None,
    webhook_url: Optional[str] = None,
    commission_rate: Optional[float] = None,
    is_active: Optional[bool] = None,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    파트너사 정보를 수정합니다.
    """
    # TODO: 파트너사 정보 수정 로직 구현
    # partner_service = PartnerService(db)
    # return await partner_service.update_partner(partner_id, ...)
    return {"message": f"파트너사 {partner_id} 정보 수정 - 구현 필요"}


@router.get("/{partner_id}/users")
async def get_partner_users(
    partner_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    특정 파트너사의 사용자 목록을 조회합니다.
    """
    # TODO: 파트너사 사용자 목록 조회 로직 구현
    # partner_service = PartnerService(db)
    # return await partner_service.get_partner_users(partner_id, page, size)
    return {"message": f"파트너사 {partner_id} 사용자 목록 - 구현 필요"}


@router.get("/{partner_id}/stats")
async def get_partner_stats(
    partner_id: int,
    days: int = Query(30, ge=1, le=365, description="통계 기간 (일)"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    파트너사별 통계를 조회합니다.
    """
    # TODO: 파트너사 통계 조회 로직 구현
    # partner_service = PartnerService(db)
    # return await partner_service.get_partner_stats(partner_id, days)
    return {"message": f"파트너사 {partner_id} 통계 - 구현 필요"}


@router.put("/{partner_id}/fees")
async def set_partner_fee_settings(
    partner_id: int,
    withdrawal_percentage: float,
    withdrawal_min: float,
    withdrawal_max: float,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    파트너사별 수수료 설정을 업데이트합니다.
    """
    # TODO: 파트너별 수수료 설정 로직 구현
    # partner_service = PartnerService(db)
    # return await partner_service.set_fee_settings(partner_id, ...)
    return {"message": f"파트너사 {partner_id} 수수료 설정 - 구현 필요"}


@router.put("/{partner_id}/branding")
async def set_partner_branding(
    partner_id: int,
    logo_url: Optional[str] = None,
    primary_color: Optional[str] = None,
    secondary_color: Optional[str] = None,
    custom_css: Optional[str] = None,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    파트너사별 브랜딩 설정을 업데이트합니다.
    """
    # TODO: 파트너별 브랜딩 설정 로직 구현
    # partner_service = PartnerService(db)
    # return await partner_service.set_branding(partner_id, ...)
    return {"message": f"파트너사 {partner_id} 브랜딩 설정 - 구현 필요"}


@router.post("/{partner_id}/webhook-test")
async def test_partner_webhook(
    partner_id: int,
    test_data: dict,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    파트너사 웹훅을 테스트합니다.
    """
    # TODO: 파트너 웹훅 테스트 로직 구현
    # webhook_service = WebhookService()
    # return await webhook_service.test_webhook(partner_id, test_data)
    return {"message": f"파트너사 {partner_id} 웹훅 테스트 - 구현 필요"}
