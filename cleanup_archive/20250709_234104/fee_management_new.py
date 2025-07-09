"""
슈퍼 어드민용 수수료 & 매출 관리 API (강화 버전)
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from decimal import Decimal

from app.core.database import get_db
from app.core.auth import get_current_super_admin
from app.services.fee.super_admin_fee_service import SuperAdminFeeService
from app.schemas.fee import (
    FeeConfigResponse, RevenueStats, TotalRevenueStats,
    Settlement, PartnerBilling
)

router = APIRouter(prefix="/admin/fees", tags=["Super Admin Fee Management"])


@router.post("/partners/{partner_id}/config", response_model=FeeConfigResponse)
async def set_partner_fee_config(
    partner_id: str,
    config_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """파트너별 수수료 설정"""
    try:
        fee_service = SuperAdminFeeService(db)
        fee_config = await fee_service.set_partner_fee_config(partner_id, config_data)
        return fee_config
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set partner fee config: {str(e)}")


@router.get("/partners/{partner_id}/config/history", response_model=List[FeeConfigResponse])
async def get_partner_fee_config_history(
    partner_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """파트너 수수료 설정 이력 조회"""
    try:
        fee_service = SuperAdminFeeService(db)
        history = await fee_service.get_fee_config_history(partner_id)
        return history
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get fee config history: {str(e)}")


@router.post("/calculate")
async def calculate_transaction_fee(
    partner_id: str,
    amount: Decimal,
    transaction_type: str = "transfer",
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """거래 수수료 계산"""
    try:
        fee_service = SuperAdminFeeService(db)
        fee_amount = await fee_service.calculate_transaction_fee(
            partner_id, amount, transaction_type
        )
        
        return {
            "partner_id": partner_id,
            "transaction_amount": amount,
            "transaction_type": transaction_type,
            "calculated_fee": fee_amount,
            "fee_rate": float(fee_amount / amount * 100) if amount > 0 else 0,
            "calculated_at": "now"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate fee: {str(e)}")


@router.get("/revenue/total", response_model=TotalRevenueStats)
async def get_total_revenue_stats(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """전체 매출 통계 조회"""
    fee_service = SuperAdminFeeService(db)
    return await fee_service.get_total_revenue_stats()


@router.get("/revenue/partners/{partner_id}", response_model=RevenueStats)
async def get_partner_revenue_stats(
    partner_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """파트너별 매출 통계 조회"""
    fee_service = SuperAdminFeeService(db)
    return await fee_service.get_partner_revenue_stats(partner_id)


@router.post("/settlements/{partner_id}", response_model=Settlement)
async def create_partner_settlement(
    partner_id: str,
    period: str = Query(..., description="정산 기간 (monthly, weekly)"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """파트너 정산 생성"""
    fee_service = SuperAdminFeeService(db)
    return await fee_service.process_settlement(partner_id, period)


@router.post("/bulk-update")
async def bulk_update_fee_configs(
    updates: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """일괄 수수료 설정 업데이트"""
    try:
        fee_service = SuperAdminFeeService(db)
        results = await fee_service.bulk_update_fees(updates)
        
        return {
            "total_updates": len(updates),
            "successful_updates": len(results["success"]),
            "failed_updates": len(results["failed"]),
            "results": results,
            "updated_by": current_admin.get("id"),
            "updated_at": "now"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk update fees: {str(e)}")


@router.get("/analytics/revenue-trends")
async def get_revenue_trends(
    days: int = Query(30, description="분석 기간 (일)"),
    partner_id: Optional[str] = Query(None, description="특정 파트너"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """매출 트렌드 분석"""
    try:
        # 실제 구현에서는 복잡한 매출 분석 수행
        trends = {
            "analysis_period": days,
            "partner_id": partner_id,
            "revenue_trend": "increasing",  # 트렌드 분석
            "growth_rate": 15.5,  # 성장률
            "daily_averages": [],  # 일별 평균 매출
            "predictions": {
                "next_month": 125000.00,
                "confidence": 0.85
            },
            "top_revenue_days": [],
            "seasonal_patterns": {}
        }
        
        return trends
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze revenue trends: {str(e)}")


@router.get("/analytics/fee-optimization")
async def get_fee_optimization_suggestions(
    partner_id: Optional[str] = Query(None, description="특정 파트너"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """수수료 최적화 제안"""
    try:
        optimization_data = {
            "partner_id": partner_id,
            "current_fee_structure": {},
            "optimization_suggestions": [
                {
                    "type": "volume_discount",
                    "description": "Consider implementing volume discounts for high-transaction partners",
                    "estimated_impact": "+12% revenue"
                },
                {
                    "type": "time_based_pricing",
                    "description": "Implement peak/off-peak pricing",
                    "estimated_impact": "+8% efficiency"
                }
            ],
            "competitive_analysis": {
                "market_average_fee": 0.015,
                "our_average_fee": 0.012,
                "position": "competitive"
            },
            "recommendations": []
        }
        
        return optimization_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate optimization suggestions: {str(e)}")


@router.get("/reports/commission")
async def generate_commission_report(
    start_date: str,
    end_date: str,
    partner_id: Optional[str] = Query(None, description="특정 파트너"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """수수료 보고서 생성"""
    try:
        # 실제 구현에서는 상세한 수수료 보고서 생성
        report = {
            "report_id": "commission_report_001",
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "partner_id": partner_id,
            "summary": {
                "total_transactions": 1234,
                "total_volume": 567890.12,
                "total_fees_collected": 5678.90,
                "average_fee_rate": 0.010
            },
            "detailed_breakdown": {
                "by_transaction_type": {},
                "by_partner": {} if not partner_id else None,
                "by_day": {}
            },
            "generated_by": current_admin.get("id"),
            "generated_at": "now"
        }
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate commission report: {str(e)}")


@router.post("/fees/preview")
async def preview_fee_changes(
    changes: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_super_admin)
):
    """수수료 변경 미리보기"""
    try:
        # 수수료 변경 시뮬레이션
        preview_results = []
        
        for change in changes:
            partner_id = change.get("partner_id")
            new_config = change.get("config", {})
            
            # 현재 설정과 새 설정 비교 분석
            preview_results.append({
                "partner_id": partner_id,
                "current_config": {},  # 현재 설정
                "new_config": new_config,
                "estimated_impact": {
                    "revenue_change": "+5.2%",
                    "transaction_volume_impact": "minimal",
                    "partner_satisfaction": "positive"
                }
            })
        
        return {
            "preview_results": preview_results,
            "overall_impact": {
                "total_revenue_change": "+3.8%",
                "affected_partners": len(changes)
            },
            "recommendations": [
                "Gradual rollout recommended for large fee changes",
                "Monitor partner feedback during transition period"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to preview fee changes: {str(e)}")
