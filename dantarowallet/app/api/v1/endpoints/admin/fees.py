"""
관리자용 수수료 관리 API 엔드포인트
"""
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_admin_user
from app.models.user import User
from app.services.fee.fee_service import FeeService
from app.schemas.fee import (
    FeeConfig, FeeConfigCreate, FeeConfigUpdate,
    FeeCalculationRequest, FeeCalculationResult
)
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["수수료 관리"])


@router.post("/configs", response_model=FeeConfig)
async def create_fee_config(
    fee_data: FeeConfigCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    새 수수료 설정을 생성합니다.
    """
    try:
        fee_service = FeeService(db)
        admin_id: int = current_admin.id  # type: ignore
        config = await fee_service.create_fee_config(
            fee_data=fee_data,
            admin_id=admin_id
        )
        
        logger.info(f"관리자 {current_admin.id}가 수수료 설정 생성: {config.id}")
        return config
        
    except Exception as e:
        logger.error(f"수수료 설정 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="수수료 설정 생성 중 오류가 발생했습니다."
        )


@router.patch("/configs/{config_id}", response_model=FeeConfig)
async def update_fee_config(
    config_id: int,
    update_data: FeeConfigUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    기존 수수료 설정을 수정합니다.
    """
    try:
        fee_service = FeeService(db)
        admin_id: int = current_admin.id  # type: ignore
        config = await fee_service.update_fee_config(
            config_id=config_id,
            update_data=update_data,
            admin_id=admin_id
        )
        
        logger.info(f"관리자 {current_admin.id}가 수수료 설정 {config_id} 수정")
        return config
        
    except Exception as e:
        logger.error(f"수수료 설정 수정 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="수수료 설정 수정 중 오류가 발생했습니다."
        )


@router.post("/calculate", response_model=FeeCalculationResult)
async def calculate_fee(
    calculation_request: FeeCalculationRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    특정 거래에 대한 수수료를 미리 계산합니다.
    """
    try:
        fee_service = FeeService(db)
        result = await fee_service.calculate_fee(calculation_request)
        
        logger.info(f"관리자 {current_admin.id}가 수수료 계산: {calculation_request.amount}")
        return result
        
    except Exception as e:
        logger.error(f"수수료 계산 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="수수료 계산 중 오류가 발생했습니다."
        )


@router.get("/partner/{partner_id}/revenue-stats")
async def get_partner_revenue_stats(
    partner_id: int,
    days: int = Query(30, ge=1, le=365, description="통계 기간 (일)"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    파트너별 수수료 수익 통계를 조회합니다.
    """
    try:
        fee_service = FeeService(db)
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
        
        stats = await fee_service.get_partner_revenue_stats(
            partner_id=partner_id,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"관리자 {current_admin.id}가 파트너 {partner_id} 수수료 통계 조회")
        return stats
        
    except Exception as e:
        logger.error(f"파트너 수수료 통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="파트너 수수료 통계 조회 중 오류가 발생했습니다."
        )


@router.get("/total-revenue-stats")
async def get_total_revenue_stats(
    days: int = Query(30, ge=1, le=365, description="통계 기간 (일)"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    전체 수수료 수익 통계를 조회합니다.
    """
    try:
        fee_service = FeeService(db)
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
        
        stats = await fee_service.get_total_revenue_stats(
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"관리자 {current_admin.id}가 전체 수수료 수익 통계 조회")
        return stats
        
    except Exception as e:
        logger.error(f"전체 수수료 수익 통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="전체 수수료 수익 통계 조회 중 오류가 발생했습니다."
        )
