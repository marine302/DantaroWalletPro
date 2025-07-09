"""
관리자용 수수료 관리 API 엔드포인트
"""
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_admin_user
from app.models.user import User
from app.services.fee.fee_service import FeeService
from app.schemas.fee import (
    FeeConfig, FeeConfigCreate, FeeConfigUpdate,
    DynamicFeeRule, DynamicFeeRuleCreate, DynamicFeeRuleUpdate,
    FeeCalculationRequest, FeeCalculationResult,
    PartnerFeeStats, TotalRevenueStats, FeeHistory
)
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["수수료 관리"])


@router.post("/configs", response_model=FeeConfig)
async def create_fee_config(
    fee_data: FeeConfigCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    새 수수료 설정을 생성합니다.
    """
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


@router.get("/configs", response_model=List[FeeConfig])
async def get_fee_configs(
    transaction_type: Optional[str] = Query(None, description="거래 유형 필터"),
    partner_id: Optional[int] = Query(None, description="파트너 ID 필터"),
    is_active: Optional[bool] = Query(None, description="활성 상태 필터"),
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=100, description="조회할 항목 수"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    수수료 설정 목록을 조회합니다.
    """
    try:
        fee_service = FeeService(db)
        configs = await fee_service.get_fee_configs(
            transaction_type=transaction_type,
            partner_id=partner_id,
            is_active=is_active,
            skip=skip,
            limit=limit
        )
        
        logger.info(f"관리자 {current_admin.id}가 수수료 설정 목록 조회")
        return configs
        
    except Exception as e:
        logger.error(f"수수료 설정 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="수수료 설정 목록 조회 중 오류가 발생했습니다."
        )


@router.get("/configs/{config_id}", response_model=FeeConfig)
async def get_fee_config(
    config_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    특정 수수료 설정을 조회합니다.
    """
    try:
        fee_service = FeeService(db)
        config = await fee_service.get_fee_config_by_id(config_id)
        
        logger.info(f"관리자 {current_admin.id}가 수수료 설정 {config_id} 조회")
        return config
        
    except Exception as e:
        logger.error(f"수수료 설정 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="수수료 설정 조회 중 오류가 발생했습니다."
        )


@router.patch("/configs/{config_id}", response_model=FeeConfig)
async def update_fee_config(
    config_id: int,
    update_data: FeeConfigUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    기존 수수료 설정을 수정합니다.
    """
    try:
        fee_service = FeeService(db)
        config = await fee_service.update_fee_config(
            config_id=config_id,
            update_data=update_data,
            admin_id=current_admin.id
        )
        
        logger.info(f"관리자 {current_admin.id}가 수수료 설정 {config_id} 수정")
        return config
        
    except Exception as e:
        logger.error(f"수수료 설정 수정 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="수수료 설정 수정 중 오류가 발생했습니다."
        )


@router.delete("/configs/{config_id}")
async def delete_fee_config(
    config_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    수수료 설정을 삭제합니다.
    """
    try:
        fee_service = FeeService(db)
        success = await fee_service.delete_fee_config(config_id, current_admin.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="수수료 설정을 찾을 수 없습니다."
            )
        
        logger.info(f"관리자 {current_admin.id}가 수수료 설정 {config_id} 삭제")
        return {"message": "수수료 설정이 성공적으로 삭제되었습니다."}
        
    except Exception as e:
        logger.error(f"수수료 설정 삭제 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="수수료 설정 삭제 중 오류가 발생했습니다."
        )


@router.post("/calculate", response_model=FeeCalculationResult)
async def calculate_fee(
    calculation_request: FeeCalculationRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="수수료 계산 중 오류가 발생했습니다."
        )


@router.get("/history", response_model=List[FeeHistory])
async def get_fee_history(
    config_id: Optional[int] = Query(None, description="특정 설정 ID"),
    start_date: Optional[datetime] = Query(None, description="시작 날짜"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜"),
    limit: int = Query(50, ge=1, le=200, description="조회할 항목 수"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    수수료 변경 이력을 조회합니다.
    """
    try:
        fee_service = FeeService(db)
        history = await fee_service.get_fee_history(
            config_id=config_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        logger.info(f"관리자 {current_admin.id}가 수수료 변경 이력 조회")
        return history
        
    except Exception as e:
        logger.error(f"수수료 변경 이력 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="수수료 변경 이력 조회 중 오류가 발생했습니다."
        )


@router.get("/stats/partner/{partner_id}", response_model=PartnerFeeStats)
async def get_partner_fee_stats(
    partner_id: int,
    days: int = Query(30, ge=1, le=365, description="통계 기간 (일)"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    파트너별 수수료 통계를 조회합니다.
    """
    try:
        fee_service = FeeService(db)
        stats = await fee_service.get_partner_fee_stats(partner_id, days)
        
        logger.info(f"관리자 {current_admin.id}가 파트너 {partner_id} 수수료 통계 조회")
        return stats
        
    except Exception as e:
        logger.error(f"파트너 수수료 통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파트너 수수료 통계 조회 중 오류가 발생했습니다."
        )


@router.get("/stats/total", response_model=TotalRevenueStats)
async def get_total_revenue_stats(
    days: int = Query(30, ge=1, le=365, description="통계 기간 (일)"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    전체 수수료 수익 통계를 조회합니다.
    """
    try:
        fee_service = FeeService(db)
        stats = await fee_service.get_total_revenue_stats(days)
        
        logger.info(f"관리자 {current_admin.id}가 전체 수수료 수익 통계 조회")
        return stats
        
    except Exception as e:
        logger.error(f"전체 수수료 수익 통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="전체 수수료 수익 통계 조회 중 오류가 발생했습니다."
        )


@router.post("/rules", response_model=DynamicFeeRule)
async def create_dynamic_fee_rule(
    rule_data: DynamicFeeRuleCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    동적 수수료 규칙을 생성합니다.
    """
    try:
        fee_service = FeeService(db)
        rule = await fee_service.create_dynamic_fee_rule(rule_data, current_admin.id)
        
        logger.info(f"관리자 {current_admin.id}가 동적 수수료 규칙 생성: {rule.id}")
        return rule
        
    except Exception as e:
        logger.error(f"동적 수수료 규칙 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="동적 수수료 규칙 생성 중 오류가 발생했습니다."
        )


@router.get("/rules", response_model=List[DynamicFeeRule])
async def get_dynamic_fee_rules(
    is_active: Optional[bool] = Query(None, description="활성 상태 필터"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    동적 수수료 규칙 목록을 조회합니다.
    """
    try:
        fee_service = FeeService(db)
        rules = await fee_service.get_dynamic_fee_rules(is_active)
        
        logger.info(f"관리자 {current_admin.id}가 동적 수수료 규칙 목록 조회")
        return rules
        
    except Exception as e:
        logger.error(f"동적 수수료 규칙 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="동적 수수료 규칙 목록 조회 중 오류가 발생했습니다."
        )
