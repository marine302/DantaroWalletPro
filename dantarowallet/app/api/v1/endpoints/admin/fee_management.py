"""
관리자용 수수료 관리 API 엔드포인트
"""
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_admin_user
from app.models.user import User
from app.services.fee.fee_service import FeeService
from app.schemas.fee import (
    FeeConfig, FeeConfigCreate, FeeConfigUpdate,
    FeeCalculationRequest, FeeCalculationResult,
    PartnerFeeStats, TotalRevenueStats
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
    """새 수수료 설정을 생성합니다."""
    try:
        fee_service = FeeService(db)
        config = await fee_service.create_fee_config(
            fee_data=fee_data,
            admin_id=current_admin.id
        )
        
        logger.info(f"관리자 {current_admin.id}가 수수료 설정 생성: {config.id}")
        return config
        
    except Exception as e:
        logger.error(f"수수료 설정 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="수수료 설정 생성 중 오류가 발생했습니다."
        )


@router.patch("/configs/{config_id}", response_model=FeeConfig)
async def update_fee_config(
    config_id: int,
    update_data: FeeConfigUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """수수료 설정을 업데이트합니다."""
    try:
        fee_service = FeeService(db)
        config = await fee_service.update_fee_config(
            config_id=config_id,
            update_data=update_data,
            admin_id=current_admin.id
        )
        
        logger.info(f"관리자 {current_admin.id}가 수수료 설정 {config_id} 업데이트")
        return config
        
    except Exception as e:
        logger.error(f"수수료 설정 업데이트 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="수수료 설정 업데이트 중 오류가 발생했습니다."
        )


@router.post("/calculate", response_model=FeeCalculationResult)
async def calculate_fee(
    calculation_request: FeeCalculationRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """수수료를 계산합니다."""
    try:
        fee_service = FeeService(db)
        result = await fee_service.calculate_fee(calculation_request)
        
        logger.info(f"관리자 {current_admin.id}가 수수료 계산 실행")
        return result
        
    except Exception as e:
        logger.error(f"수수료 계산 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="수수료 계산 중 오류가 발생했습니다."
        )


@router.get("/revenue/partner/{partner_id}", response_model=PartnerFeeStats)
async def get_partner_revenue_stats(
    partner_id: int,
    start_date: datetime = Query(..., description="시작 날짜"),
    end_date: datetime = Query(..., description="종료 날짜"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """파트너별 매출 통계를 조회합니다."""
    try:
        fee_service = FeeService(db)
        stats = await fee_service.get_partner_revenue_stats(
            partner_id=partner_id,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"관리자 {current_admin.id}가 파트너 {partner_id} 매출 통계 조회")
        return stats
        
    except Exception as e:
        logger.error(f"파트너 매출 통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파트너 매출 통계 조회 중 오류가 발생했습니다."
        )


@router.get("/revenue/total", response_model=TotalRevenueStats)
async def get_total_revenue_stats(
    start_date: datetime = Query(..., description="시작 날짜"),
    end_date: datetime = Query(..., description="종료 날짜"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """전체 매출 통계를 조회합니다."""
    try:
        fee_service = FeeService(db)
        stats = await fee_service.get_total_revenue_stats(
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"관리자 {current_admin.id}가 전체 매출 통계 조회")
        return stats
        
    except Exception as e:
        logger.error(f"전체 매출 통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="전체 매출 통계 조회 중 오류가 발생했습니다."
        )
