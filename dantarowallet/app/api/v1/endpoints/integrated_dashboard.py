"""파트너사 종합 대시보드 API 엔드포인트"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.dashboard.integrated_dashboard import IntegratedDashboard
from app.services.external_energy_service import safe_get_value
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

@router.get("/dashboard/{partner_id}", response_model=Dict[str, Any])
async def get_dashboard_data(
    partner_id: int,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    파트너사 종합 대시보드 데이터 조회
    """
    try:
        dashboard = IntegratedDashboard(db, partner_id)
        data = await dashboard.get_dashboard_data()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"대시보드 데이터 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="대시보드 데이터 조회 실패")

@router.get("/dashboard/{partner_id}/wallet-overview", response_model=Dict[str, Any])
async def get_wallet_overview(
    partner_id: int,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    멀티 지갑 통합 현황 조회
    """
    try:
        dashboard = IntegratedDashboard(db, partner_id)
        data = await dashboard.get_wallet_overview()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"지갑 현황 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="지갑 현황 조회 실패")

@router.get("/dashboard/{partner_id}/transaction-flow", response_model=Dict[str, Any])
async def get_transaction_flow(
    partner_id: int,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    실시간 거래 흐름 분석 조회
    """
    try:
        dashboard = IntegratedDashboard(db, partner_id)
        data = await dashboard.get_transaction_flow()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"거래 흐름 분석 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="거래 흐름 분석 조회 실패")

@router.get("/dashboard/{partner_id}/energy-status", response_model=Dict[str, Any])
async def get_energy_status(
    partner_id: int,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    에너지 풀 현황 조회
    """
    try:
        dashboard = IntegratedDashboard(db, partner_id)
        data = await dashboard.get_energy_status()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"에너지 상태 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="에너지 상태 조회 실패")

@router.get("/dashboard/{partner_id}/user-analytics", response_model=Dict[str, Any])
async def get_user_analytics(
    partner_id: int,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    사용자 분석 정보 조회
    """
    try:
        dashboard = IntegratedDashboard(db, partner_id)
        data = await dashboard.get_user_analytics()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"사용자 분석 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="사용자 분석 조회 실패")

@router.get("/dashboard/{partner_id}/revenue-metrics", response_model=Dict[str, Any])
async def get_revenue_metrics(
    partner_id: int,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    수익 지표 조회
    """
    try:
        dashboard = IntegratedDashboard(db, partner_id)
        data = await dashboard.get_revenue_metrics()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"수익 지표 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="수익 지표 조회 실패")

@router.get("/dashboard/{partner_id}/risk-alerts", response_model=Dict[str, Any])
async def get_risk_alerts(
    partner_id: int,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    리스크 알림 조회
    """
    try:
        dashboard = IntegratedDashboard(db, partner_id)
        data = await dashboard.get_risk_alerts()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"리스크 알림 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="리스크 알림 조회 실패")

@router.get("/dashboard/{partner_id}/predictions", response_model=Dict[str, Any])
async def get_predictions(
    partner_id: int,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    예측 정보 조회
    """
    try:
        dashboard = IntegratedDashboard(db, partner_id)
        data = await dashboard.get_predictions()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"예측 정보 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="예측 정보 조회 실패")

@router.get("/dashboard/{partner_id}/system-health", response_model=Dict[str, Any])
async def get_system_health(
    partner_id: int,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    시스템 상태 조회
    """
    try:
        dashboard = IntegratedDashboard(db, partner_id)
        data = await dashboard.get_system_health()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"시스템 상태 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="시스템 상태 조회 실패")
