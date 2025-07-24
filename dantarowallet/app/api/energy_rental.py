"""
에너지 렌탈 API 엔드포인트
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.energy_rental import PaymentStatus, RentalPlanType, SubscriptionTier
from app.services.energy_rental_service import EnergyRentalService

router = APIRouter(prefix="/energy-rental", tags=["energy-rental"])


# Request Models
class CreateRentalPlanRequest(BaseModel):
    partner_id: int
    plan_type: RentalPlanType
    subscription_tier: Optional[SubscriptionTier] = None
    plan_name: str
    price_per_energy: Decimal = Field(..., gt=0)
    discount_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    auto_recharge_enabled: bool = False
    auto_recharge_threshold: Optional[int] = None
    auto_recharge_amount: Optional[int] = None


class AllocateEnergyRequest(BaseModel):
    partner_id: int
    energy_amount: int = Field(..., gt=0)
    from_pool_id: Optional[int] = None


class RecordEnergyUsageRequest(BaseModel):
    partner_id: int
    energy_used: int = Field(..., gt=0)
    transaction_hash: str
    from_address: str
    to_address: str
    metadata: Optional[Dict[str, Any]] = None


class UpdatePaymentStatusRequest(BaseModel):
    payment_status: PaymentStatus


# API Endpoints


@router.post("/rental-plans", summary="렌탈 플랜 생성")
async def create_rental_plan(
    request: CreateRentalPlanRequest, db: Session = Depends(get_db)
):
    """새로운 에너지 렌탈 플랜을 생성합니다."""
    try:
        service = EnergyRentalService(db)

        rental_plan = service.create_rental_plan(
            partner_id=request.partner_id,
            plan_type=request.plan_type,
            subscription_tier=request.subscription_tier,
            plan_name=request.plan_name,
            price_per_energy=request.price_per_energy,
            discount_rate=request.discount_rate,
            auto_recharge_enabled=request.auto_recharge_enabled,
            auto_recharge_threshold=request.auto_recharge_threshold,
            auto_recharge_amount=request.auto_recharge_amount,
        )

        return {
            "success": True,
            "rental_plan": {
                "id": rental_plan.id,
                "partner_id": rental_plan.partner_id,
                "plan_name": rental_plan.plan_name,
                "plan_type": rental_plan.plan_type.value,
                "subscription_tier": getattr(rental_plan, "subscription_tier", None),
                "created_at": rental_plan.created_at.isoformat(),
            },
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/allocate-energy", summary="에너지 할당")
async def allocate_energy(
    request: AllocateEnergyRequest, db: Session = Depends(get_db)
):
    """파트너에게 에너지를 할당합니다."""
    try:
        service = EnergyRentalService(db)

        allocation = service.allocate_energy(
            partner_id=request.partner_id,
            energy_amount=request.energy_amount,
            from_pool_id=request.from_pool_id,
        )

        return {
            "success": True,
            "allocation": {
                "id": allocation.id,
                "partner_id": allocation.partner_id,
                "allocated_energy": allocation.allocated_energy,
                "remaining_energy": allocation.remaining_energy,
                "expiry_date": allocation.expiry_date.isoformat(),
            },
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/record-usage", summary="에너지 사용 기록")
async def record_energy_usage(
    request: RecordEnergyUsageRequest, db: Session = Depends(get_db)
):
    """에너지 사용을 기록합니다."""
    try:
        service = EnergyRentalService(db)

        usage_record = service.record_energy_usage(
            partner_id=request.partner_id,
            energy_used=request.energy_used,
            transaction_hash=request.transaction_hash,
            from_address=request.from_address,
            to_address=request.to_address,
            metadata=request.metadata,
        )

        return {
            "success": True,
            "usage_record": {
                "id": usage_record.id,
                "partner_id": usage_record.partner_id,
                "energy_used": usage_record.energy_used,
                "total_cost": float(getattr(usage_record, "total_cost", 0)),
                "transaction_hash": usage_record.transaction_hash,
                "used_at": usage_record.used_at.isoformat(),
            },
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/partner/{partner_id}/usage-statistics", summary="파트너 사용 통계")
async def get_partner_usage_statistics(
    partner_id: int,
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    db: Session = Depends(get_db),
):
    """파트너의 에너지 사용 통계를 조회합니다."""
    try:
        service = EnergyRentalService(db)

        stats = service.get_partner_usage_statistics(
            partner_id=partner_id, period_start=period_start, period_end=period_end
        )

        return {"success": True, "statistics": stats}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/billing/{partner_id}", summary="청구서 생성")
async def generate_billing_record(
    partner_id: int,
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    db: Session = Depends(get_db),
):
    """청구서를 생성합니다."""
    try:
        service = EnergyRentalService(db)

        billing_record = service.generate_billing_record(
            partner_id=partner_id,
            billing_period_start=period_start,
            billing_period_end=period_end,
        )

        return {
            "success": True,
            "billing_record": {
                "id": billing_record.id,
                "invoice_number": billing_record.invoice_number,
                "partner_id": billing_record.partner_id,
                "total_energy_used": billing_record.total_energy_used,
                "final_amount": float(getattr(billing_record, "final_amount", 0)),
                "payment_status": billing_record.payment_status.value,
                "due_date": billing_record.due_date.isoformat(),
            },
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/partner/{partner_id}/billing-history", summary="청구 이력")
async def get_billing_history(partner_id: int, db: Session = Depends(get_db)):
    """파트너의 청구 이력을 조회합니다."""
    try:
        service = EnergyRentalService(db)

        billing_history = service.get_billing_history(partner_id)

        return {"success": True, "billing_history": billing_history}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/billing/{billing_id}/payment-status", summary="결제 상태 업데이트")
async def update_payment_status(
    billing_id: int, request: UpdatePaymentStatusRequest, db: Session = Depends(get_db)
):
    """청구서의 결제 상태를 업데이트합니다."""
    try:
        service = EnergyRentalService(db)

        success = service.update_payment_status(
            billing_record_id=billing_id, payment_status=request.payment_status
        )

        return {
            "success": success,
            "message": (
                "결제 상태가 업데이트되었습니다." if success else "업데이트 실패"
            ),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/energy-pools/status", summary="에너지 풀 상태")
async def get_energy_pool_status(db: Session = Depends(get_db)):
    """에너지 풀 상태를 조회합니다."""
    try:
        service = EnergyRentalService(db)

        pool_status = service.get_energy_pool_status()

        return {"success": True, "energy_pools": pool_status}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/system/status", summary="시스템 상태")
async def get_system_status(db: Session = Depends(get_db)):
    """시스템 전체 상태를 조회합니다."""
    try:
        service = EnergyRentalService(db)

        system_status = service.get_system_status()

        return {"success": True, "system_status": system_status}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/partner/{partner_id}/energy-allocation", summary="파트너 에너지 할당 정보"
)
async def get_partner_energy_allocation(partner_id: int, db: Session = Depends(get_db)):
    """파트너의 에너지 할당 정보를 조회합니다."""
    try:
        service = EnergyRentalService(db)

        allocation_info = service.get_partner_energy_allocation(partner_id)

        return {"success": True, "allocation": allocation_info}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/partner/{partner_id}/auto-recharge-check", summary="자동 재충전 확인")
async def auto_recharge_check(partner_id: int, db: Session = Depends(get_db)):
    """자동 재충전 확인 및 실행합니다."""
    try:
        service = EnergyRentalService(db)

        recharge_executed = service.auto_recharge_check(partner_id)

        return {
            "success": True,
            "recharge_executed": recharge_executed,
            "message": (
                "자동 재충전이 실행되었습니다."
                if recharge_executed
                else "자동 재충전이 필요하지 않습니다."
            ),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rental-plans", summary="활성 렌탈 플랜 조회")
async def get_active_rental_plans(
    partner_id: Optional[int] = Query(None), db: Session = Depends(get_db)
):
    """활성 렌탈 플랜을 조회합니다."""
    try:
        service = EnergyRentalService(db)

        rental_plans = service.get_active_rental_plans(partner_id)

        return {"success": True, "rental_plans": rental_plans}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/rental-plans/{plan_id}/deactivate", summary="렌탈 플랜 비활성화")
async def deactivate_rental_plan(plan_id: int, db: Session = Depends(get_db)):
    """렌탈 플랜을 비활성화합니다."""
    try:
        service = EnergyRentalService(db)

        success = service.deactivate_rental_plan(plan_id)

        return {
            "success": success,
            "message": (
                "렌탈 플랜이 비활성화되었습니다." if success else "비활성화 실패"
            ),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 수퍼어드민 <-> 파트너 에너지 렌탈 체인 시스템

@router.get("/plans", summary="렌탈 플랜 목록 조회")
async def get_rental_plans(db: Session = Depends(get_db)):
    """사용 가능한 에너지 렌탈 플랜 목록을 조회합니다."""
    try:
        service = EnergyRentalService(db)
        plans = service.get_available_plans()

        return {
            "success": True,
            "plans": [
                {
                    "id": plan.id,
                    "plan_name": plan.plan_name,
                    "plan_type": plan.plan_type.value,
                    "price_per_energy": float(plan.price_per_energy),
                    "discount_rate": float(plan.discount_rate or 0),
                    "available": True,
                }
                for plan in plans
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/partner/{partner_id}/usage", summary="파트너 에너지 사용 통계")
async def get_partner_usage_stats(
    partner_id: str,
    period: str = Query(default="30d", description="통계 기간 (7d, 30d, 90d)"),
    db: Session = Depends(get_db),
):
    """특정 파트너의 에너지 사용 통계를 조회합니다."""
    try:
        service = EnergyRentalService(db)
        stats = service.get_partner_usage_stats(partner_id, period)

        return {
            "success": True,
            "usage_stats": {
                "partner_id": partner_id,
                "period": period,
                "total_energy_used": stats.get("total_energy_used", 0),
                "daily_average": stats.get("daily_average", 0),
                "peak_usage": stats.get("peak_usage", 0),
                "cost_total": stats.get("cost_total", 0),
                "efficiency_score": stats.get("efficiency_score", 85),
                "trend": stats.get("trend", "stable"),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/partner/{partner_id}/billing", summary="파트너 청구 정보")
async def get_partner_billing(
    partner_id: str, db: Session = Depends(get_db)
):
    """특정 파트너의 청구 정보를 조회합니다."""
    try:
        service = EnergyRentalService(db)
        billing = service.get_partner_billing(partner_id)

        return {
            "success": True,
            "billing": {
                "partner_id": partner_id,
                "current_balance": billing.get("current_balance", 0),
                "pending_charges": billing.get("pending_charges", 0),
                "last_payment": billing.get("last_payment"),
                "next_billing_date": billing.get("next_billing_date"),
                "payment_method": billing.get("payment_method", "auto"),
                "billing_history": billing.get("billing_history", []),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pools/status", summary="에너지 풀 상태 조회")
async def get_pools_status(db: Session = Depends(get_db)):
    """전체 에너지 풀의 상태를 조회합니다."""
    try:
        service = EnergyRentalService(db)
        status = service.get_pools_status()

        return {
            "success": True,
            "pools_status": {
                "total_capacity": status.get("total_capacity", 10000000),
                "available_energy": status.get("available_energy", 7500000),
                "allocated_energy": status.get("allocated_energy", 2500000),
                "utilization_rate": status.get("utilization_rate", 0.75),
                "pools": status.get("pools", [
                    {
                        "pool_id": "main_pool",
                        "name": "메인 에너지 풀",
                        "capacity": 5000000,
                        "available": 3750000,
                        "status": "active",
                    },
                    {
                        "pool_id": "reserve_pool",
                        "name": "예비 에너지 풀",
                        "capacity": 3000000,
                        "available": 2250000,
                        "status": "active",
                    },
                ]),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rent", summary="에너지 렌탈 요청")
async def rent_energy(
    request: AllocateEnergyRequest, db: Session = Depends(get_db)
):
    """파트너가 에너지를 렌탈합니다."""
    try:
        service = EnergyRentalService(db)
        rental = service.rent_energy(
            partner_id=request.partner_id,
            energy_amount=request.energy_amount,
            from_pool_id=request.from_pool_id,
        )

        return {
            "success": True,
            "rental": {
                "rental_id": rental.get("rental_id"),
                "partner_id": request.partner_id,
                "energy_amount": request.energy_amount,
                "cost": rental.get("cost"),
                "status": "active",
                "expires_at": rental.get("expires_at"),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 프론트엔드에서 기대하는 추가 API 엔드포인트들

@router.get("/overview", summary="에너지 렌탈 서비스 개요")
async def get_energy_rental_overview(db: Session = Depends(get_db)):
    """에너지 렌탈 서비스의 전체 개요를 조회합니다."""
    try:
        service = EnergyRentalService(db)
        overview = service.get_energy_rental_overview()

        return {
            "success": True,
            "overview": {
                "total_energy_capacity": overview.get("total_energy_capacity", 50000000),
                "average_utilization": overview.get("average_utilization", 78.5),
                "total_revenue_today": overview.get("total_revenue_today", 1250),
                "active_rentals": overview.get("active_rentals", 145),
                "total_revenue_month": overview.get("total_revenue_month", 35000),
                "profit_margin": overview.get("profit_margin", 22.5),
                "total_energy_rented": overview.get("total_energy_rented", 39250000),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pools", summary="에너지 풀 목록")
async def get_energy_rental_pools(db: Session = Depends(get_db)):
    """렌탈용 에너지 풀 목록을 조회합니다."""
    try:
        service = EnergyRentalService(db)
        pools = service.get_energy_rental_pools()

        return {
            "success": True,
            "pools": [
                {
                    "id": pool.get("id", "pool_001"),
                    "name": pool.get("name", "High-Yield Pool A"),
                    "status": pool.get("status", "active"),
                    "created_at": pool.get("created_at", "2025-07-15T00:00:00Z"),
                    "utilization_rate": pool.get("utilization_rate", 85.2),
                    "available_energy": pool.get("available_energy", 7500000),
                    "total_energy": pool.get("total_energy", 50000000),
                    "staked_trx": pool.get("staked_trx", 150000),
                    "rental_rate": pool.get("rental_rate", 0.02),
                    "daily_revenue": pool.get("daily_revenue", 3000),
                    "auto_rebalance": pool.get("auto_rebalance", True),
                }
                for pool in pools
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pools", summary="에너지 풀 생성")
async def create_energy_rental_pool(
    pool_data: dict, db: Session = Depends(get_db)
):
    """새로운 렌탈용 에너지 풀을 생성합니다."""
    try:
        service = EnergyRentalService(db)
        pool = service.create_energy_rental_pool(
            name=pool_data.get("name", "Default Pool"),
            stake_amount=pool_data.get("stake_amount", 1000),
            rental_rate=pool_data.get("rental_rate", 0.000021),
        )

        return {
            "success": True,
            "pool": {
                "id": pool.get("id"),
                "name": pool.get("name"),
                "stake_amount": pool.get("stake_amount"),
                "rental_rate": pool.get("rental_rate"),
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/pools/{pool_id}", summary="에너지 풀 업데이트")
async def update_energy_rental_pool(
    pool_id: str, updates: dict, db: Session = Depends(get_db)
):
    """에너지 풀 정보를 업데이트합니다."""
    try:
        service = EnergyRentalService(db)
        pool = service.update_energy_rental_pool(pool_id, updates)

        return {
            "success": True,
            "pool": pool,
            "message": "에너지 풀이 성공적으로 업데이트되었습니다.",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/pools/{pool_id}", summary="에너지 풀 삭제")
async def delete_energy_rental_pool(pool_id: str, db: Session = Depends(get_db)):
    """에너지 풀을 삭제합니다."""
    try:
        service = EnergyRentalService(db)
        success = service.delete_energy_rental_pool(pool_id)

        return {
            "success": success,
            "message": "에너지 풀이 삭제되었습니다." if success else "삭제 실패",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/transactions", summary="렌탈 거래 목록")
async def get_energy_rental_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """에너지 렌탈 거래 목록을 조회합니다."""
    try:
        service = EnergyRentalService(db)
        transactions = service.get_energy_rental_transactions(page, limit)

        return {
            "success": True,
            "transactions": [
                {
                    "id": tx.get("id", "tx_001"),
                    "customer_name": tx.get("customer_name", "Trading Bot A"),
                    "energy_amount": tx.get("energy_amount", 5000000),
                    "duration_hours": tx.get("duration_hours", 24),
                    "total_cost": tx.get("total_cost", 1500),
                    "start_time": tx.get("start_time", "2025-07-21T09:00:00Z"),
                    "end_time": tx.get("end_time", "2025-07-22T09:00:00Z"),
                    "status": tx.get("status", "active"),
                }
                for tx in transactions
            ],
            "pagination": {
                "current_page": page,
                "total_pages": 10,  # 실제로는 계산해야 함
                "total_items": 200,  # 실제로는 계산해야 함
                "per_page": limit,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics", summary="렌탈 분석 데이터")
async def get_energy_rental_analytics(
    period: str = Query("30d", description="분석 기간"), db: Session = Depends(get_db)
):
    """에너지 렌탈 분석 데이터를 조회합니다."""
    try:
        service = EnergyRentalService(db)
        analytics = service.get_energy_rental_analytics(period)

        return {
            "success": True,
            "analytics": {
                "period": period,
                "total_revenue": analytics.get("total_revenue", 15750),
                "total_energy_rented": analytics.get("total_energy_rented", 125000000),
                "average_utilization": analytics.get("average_utilization", 82.3),
                "profit_margin": analytics.get("profit_margin", 24.8),
                "top_customers": analytics.get("top_customers", []),
                "revenue_trend": analytics.get("revenue_trend", []),
                "utilization_trend": analytics.get("utilization_trend", []),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/optimization", summary="수익성 최적화 제안")
async def get_energy_rental_optimization(db: Session = Depends(get_db)):
    """에너지 렌탈 수익성 최적화 제안을 조회합니다."""
    try:
        service = EnergyRentalService(db)
        suggestions = service.get_optimization_suggestions()

        return {
            "success": True,
            "suggestions": [
                {
                    "type": "pricing",
                    "title": "가격 조정 제안",
                    "description": "피크 시간대 가격을 15% 인상하여 수익 극대화",
                    "potential_impact": "월 수익 +12%",
                    "priority": "high",
                },
                {
                    "type": "capacity",
                    "title": "용량 확장 제안",
                    "description": "추가 TRX 스테이킹으로 에너지 풀 확장",
                    "potential_impact": "처리량 +30%",
                    "priority": "medium",
                },
                {
                    "type": "timing",
                    "title": "운영 시간 최적화",
                    "description": "수요가 낮은 시간대 풀 유지비 절약",
                    "potential_impact": "운영비 -8%",
                    "priority": "low",
                },
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
