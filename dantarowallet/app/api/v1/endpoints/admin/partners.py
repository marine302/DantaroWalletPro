"""
파트너사 관리 API 엔드포인트
본사 슈퍼 어드민용 파트너사 통합 관리 기능
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user
from app.core.database import get_sync_db
from app.core.logger import get_logger
from app.models.user import User
from app.schemas.partner import (
    ApiKeyResponse,
    PartnerCreate,
    PartnerResponse,
    PartnerStats,
    PartnerUpdate,
)
from app.services.partner.partner_service import PartnerService

logger = get_logger(__name__)
router = APIRouter(tags=["admin_partners"])


@router.get("/", response_model=List[PartnerResponse])
async def get_partners_list(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=100, description="조회할 항목 수"),
    search: Optional[str] = Query(None, description="파트너명 또는 도메인 검색"),
    status: Optional[str] = Query(None, description="상태 필터"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """파트너사 목록 조회"""
    try:
        partner_service = PartnerService(db)
        partners = await partner_service.get_all_partners(
            skip=skip, limit=limit, status=status
        )

        logger.info(
            f"관리자 {current_admin.id}가 파트너사 목록 조회 (총 {len(partners)}개)"
        )
        return partners

    except Exception as e:
        logger.error(f"파트너사 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail="파트너사 목록 조회 중 오류가 발생했습니다."
        )


@router.post("/", response_model=PartnerResponse)
async def create_partner(
    partner_data: PartnerCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """새 파트너사 등록"""
    try:
        partner_service = PartnerService(db)
        partner = await partner_service.create_partner(partner_data)

        logger.info(f"관리자 {current_admin.id}가 새 파트너사 생성: {partner.name}")
        return partner

    except ValueError as e:
        logger.warning(f"파트너사 생성 실패 - 유효성 검사: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"파트너사 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파트너사 생성 중 오류가 발생했습니다.",
        )


@router.get("/{partner_id}", response_model=PartnerResponse)
async def get_partner_detail(
    partner_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """파트너사 상세 정보 조회"""
    try:
        partner_service = PartnerService(db)
        partner = await partner_service.get_partner_by_id(partner_id)

        logger.info(f"관리자 {current_admin.id}가 파트너사 {partner_id} 상세 조회")
        return partner

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파트너사 상세 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파트너사 상세 조회 중 오류가 발생했습니다.",
        )


@router.patch("/{partner_id}", response_model=PartnerResponse)
async def update_partner(
    partner_id: str,
    update_data: PartnerUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """파트너사 정보 수정"""
    try:
        partner_service = PartnerService(db)
        # 임시로 기본 상태로 업데이트
        partner = await partner_service.update_partner_status(partner_id, "active")

        logger.info(f"관리자 {current_admin.id}가 파트너사 {partner_id} 정보 수정")
        return partner

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파트너사 정보 수정 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파트너사 정보 수정 중 오류가 발생했습니다.",
        )


@router.delete("/{partner_id}")
async def delete_partner(
    partner_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """파트너사 삭제"""
    try:
        partner_service = PartnerService(db)
        # 임시로 비활성화 상태로 변경
        success = await partner_service.update_partner_status(partner_id, "inactive")
        return {"success": True}

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="파트너사를 찾을 수 없습니다.",
            )

        logger.info(f"관리자 {current_admin.id}가 파트너사 {partner_id} 삭제")
        return {"message": "파트너사가 성공적으로 삭제되었습니다."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파트너사 삭제 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파트너사 삭제 중 오류가 발생했습니다.",
        )


@router.post("/{partner_id}/api-key", response_model=ApiKeyResponse)
async def generate_api_key(
    partner_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """파트너사 API 키 생성"""
    try:
        partner_service = PartnerService(db)
        # 임시로 기본 API key 반환
        api_key_data = {"api_key": f"temp_key_{partner_id}", "secret": "temp_secret"}

        logger.info(f"관리자 {current_admin.id}가 파트너사 {partner_id} API 키 생성")
        return api_key_data

    except Exception as e:
        logger.error(f"API 키 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API 키 생성 중 오류가 발생했습니다.",
        )


@router.post("/{partner_id}/api-key/rotate", response_model=ApiKeyResponse)
async def rotate_api_key(
    partner_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """파트너사 API 키 회전"""
    try:
        partner_service = PartnerService(db)
        # 임시로 새로운 API key 반환
        api_key_data = {
            "api_key": f"rotated_key_{partner_id}",
            "secret": "rotated_secret",
        }

        logger.info(f"관리자 {current_admin.id}가 파트너사 {partner_id} API 키 회전")
        return api_key_data

    except Exception as e:
        logger.error(f"API 키 회전 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API 키 회전 중 오류가 발생했습니다.",
        )


@router.get("/{partner_id}/statistics", response_model=PartnerStats)
async def get_partner_statistics(
    partner_id: str,
    days: int = Query(30, ge=1, le=365, description="통계 조회 기간 (일)"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """파트너사 통계 조회"""
    try:
        partner_service = PartnerService(db)
        stats = await partner_service.get_partner_statistics(partner_id)

        logger.info(
            f"관리자 {current_admin.id}가 파트너사 {partner_id} 통계 조회 ({days}일)"
        )
        return stats

    except Exception as e:
        logger.error(f"파트너사 통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파트너사 통계 조회 중 오류가 발생했습니다.",
        )


# ===== 슈퍼 어드민 전용 고급 파트너 관리 엔드포인트 =====


@router.get("/statistics/detailed/{partner_id}", response_model=Dict[str, Any])
async def get_partner_detailed_statistics(
    partner_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """파트너 상세 통계 조회 (슈퍼 어드민용)"""
    try:
        partner_service = PartnerService(db)
        detailed_stats = await partner_service.get_partner_statistics_detailed(
            partner_id
        )

        logger.info(
            f"슈퍼 어드민 {current_admin.id}가 파트너 {partner_id} 상세 통계 조회"
        )
        return detailed_stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파트너 상세 통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail="파트너 상세 통계 조회 중 오류가 발생했습니다."
        )


@router.post("/bulk-update", response_model=List[Dict[str, Any]])
async def bulk_update_partners(
    partner_ids: List[str],
    update_data: Dict[str, Any],
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """파트너 일괄 업데이트 (슈퍼 어드민용)"""
    try:
        partner_service = PartnerService(db)
        results = await partner_service.bulk_update_partners(partner_ids, update_data)

        logger.info(
            f"슈퍼 어드민 {current_admin.id}가 파트너 {len(partner_ids)}개 일괄 업데이트"
        )
        return results

    except Exception as e:
        logger.error(f"파트너 일괄 업데이트 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail="파트너 일괄 업데이트 중 오류가 발생했습니다."
        )


@router.get("/performance-ranking", response_model=List[Dict[str, Any]])
async def get_partner_performance_ranking(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """파트너 성과 순위 조회 (슈퍼 어드민용)"""
    try:
        partner_service = PartnerService(db)
        ranking = await partner_service.get_partner_performance_ranking()

        logger.info(f"슈퍼 어드민 {current_admin.id}가 파트너 성과 순위 조회")
        return ranking

    except Exception as e:
        logger.error(f"파트너 성과 순위 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail="파트너 성과 순위 조회 중 오류가 발생했습니다."
        )


@router.post("/export-data", response_model=Dict[str, str])
async def export_partner_data(
    partner_ids: Optional[List[str]] = None,
    format: str = Query("csv", description="내보낼 형식 (csv, json, excel)"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """파트너 데이터 내보내기 (슈퍼 어드민용)"""
    try:
        partner_service = PartnerService(db)
        export_result = await partner_service.export_partner_data(
            partner_ids=partner_ids
        )

        logger.info(
            f"슈퍼 어드민 {current_admin.id}가 파트너 데이터 내보내기 ({format})"
        )
        return export_result

    except Exception as e:
        logger.error(f"파트너 데이터 내보내기 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail="파트너 데이터 내보내기 중 오류가 발생했습니다."
        )
