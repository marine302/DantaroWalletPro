"""
관리자용 파트너 관리 API 엔드포인트
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_admin_user
from app.models.user import User
from app.services.partner.partner_service import PartnerService
from app.schemas.partner import (
    Partner, PartnerCreate, PartnerUpdate, PartnerStats,
    ApiKeyResponse
)
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["파트너 관리"])


@router.post("/", response_model=Partner)
async def create_partner(
    partner_data: PartnerCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """새 파트너사를 생성합니다."""
    try:
        partner_service = PartnerService(db)
        partner = await partner_service.create_partner(partner_data)
        
        logger.info(f"관리자 {current_admin.id}가 파트너사 {partner.id} 생성")
        return partner
        
    except Exception as e:
        logger.error(f"파트너사 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파트너사 생성 중 오류가 발생했습니다."
        )


@router.get("/", response_model=List[Partner])
async def list_partners(
    skip: int = Query(0, ge=0, description="건너뛸 개수"),
    limit: int = Query(100, ge=1, le=1000, description="가져올 개수"),
    is_active: Optional[bool] = Query(None, description="활성 상태 필터"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """파트너사 목록을 조회합니다."""
    try:
        partner_service = PartnerService(db)
        partners = await partner_service.get_all_partners(
            skip=skip, 
            limit=limit, 
            is_active=is_active
        )
        
        logger.info(f"관리자 {current_admin.id}가 파트너사 목록 조회")
        return partners
        
    except Exception as e:
        logger.error(f"파트너사 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파트너사 목록 조회 중 오류가 발생했습니다."
        )


@router.get("/{partner_id}", response_model=Partner)
async def get_partner(
    partner_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """특정 파트너사를 조회합니다."""
    try:
        partner_service = PartnerService(db)
        partner = await partner_service.get_partner_by_id(partner_id)
        
        if not partner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="파트너사를 찾을 수 없습니다."
            )
        
        logger.info(f"관리자 {current_admin.id}가 파트너사 {partner_id} 조회")
        return partner
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파트너사 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파트너사 조회 중 오류가 발생했습니다."
        )


@router.patch("/{partner_id}", response_model=Partner)
async def update_partner(
    partner_id: int,
    update_data: PartnerUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """파트너사 정보를 업데이트합니다."""
    try:
        partner_service = PartnerService(db)
        partner = await partner_service.update_partner(partner_id, update_data)
        
        logger.info(f"관리자 {current_admin.id}가 파트너사 {partner_id} 업데이트")
        return partner
        
    except Exception as e:
        logger.error(f"파트너사 업데이트 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파트너사 업데이트 중 오류가 발생했습니다."
        )


@router.delete("/{partner_id}")
async def delete_partner(
    partner_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """파트너사를 삭제(비활성화)합니다."""
    try:
        partner_service = PartnerService(db)
        success = await partner_service.delete_partner(partner_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="삭제할 파트너사를 찾을 수 없습니다."
            )
        
        logger.info(f"관리자 {current_admin.id}가 파트너사 {partner_id} 삭제")
        return {"message": "파트너사가 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파트너사 삭제 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파트너사 삭제 중 오류가 발생했습니다."
        )


@router.post("/{partner_id}/api-key", response_model=ApiKeyResponse)
async def generate_api_key(
    partner_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """파트너사의 새 API 키를 생성합니다."""
    try:
        partner_service = PartnerService(db)
        api_key_response = await partner_service.generate_api_key(partner_id)
        
        logger.info(f"관리자 {current_admin.id}가 파트너사 {partner_id} API 키 생성")
        return api_key_response
        
    except Exception as e:
        logger.error(f"API 키 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API 키 생성 중 오류가 발생했습니다."
        )


@router.post("/{partner_id}/api-key/rotate", response_model=ApiKeyResponse)
async def rotate_api_key(
    partner_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """파트너사의 API 키를 회전시킵니다."""
    try:
        partner_service = PartnerService(db)
        api_key_response = await partner_service.rotate_api_key(partner_id)
        
        logger.info(f"관리자 {current_admin.id}가 파트너사 {partner_id} API 키 회전")
        return api_key_response
        
    except Exception as e:
        logger.error(f"API 키 회전 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API 키 회전 중 오류가 발생했습니다."
        )


@router.get("/{partner_id}/statistics", response_model=PartnerStats)
async def get_partner_statistics(
    partner_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """파트너사 통계를 조회합니다."""
    try:
        partner_service = PartnerService(db)
        stats = await partner_service.get_partner_statistics(partner_id)
        
        logger.info(f"관리자 {current_admin.id}가 파트너사 {partner_id} 통계 조회")
        return stats
        
    except Exception as e:
        logger.error(f"파트너사 통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파트너사 통계 조회 중 오류가 발생했습니다."
        )
