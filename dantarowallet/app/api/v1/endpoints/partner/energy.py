"""
파트너사 에너지 계산 및 요청 API
문서 41번 4.1절 에너지 계산 API 구현
"""

from decimal import Decimal
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_partner
from app.services.energy_pool_service import EnergyPoolService
from app.services.partner_energy_service import PartnerEnergyService
from app.models.partner import Partner
from app.schemas.partner_energy import (
    EnergyCalculationRequest,
    EnergyCalculationResponse,
    EnergyChargeRequest,
    EnergyChargeResponse,
    WithdrawalBatchRequest,
    EnergyMonitoringResponse,
)

router = APIRouter()


@router.post("/calculate", response_model=EnergyCalculationResponse)
async def calculate_energy_cost(
    request: EnergyCalculationRequest,
    db: Session = Depends(get_db),
    current_partner: Partner = Depends(get_current_partner),
):
    """
    에너지 비용 계산 API
    파트너사가 출금 요청에 필요한 에너지 비용을 조회
    """
    service = PartnerEnergyService(db)
    
    # 총 에너지 요구량 계산
    withdrawal_requests_dict = [req.dict() for req in request.withdrawal_requests]
    total_energy = await service.calculate_withdrawal_energy(
        withdrawal_requests=withdrawal_requests_dict,
        batch_mode=request.batch_mode
    )
    
    # 비용 계산
    partner_id_str = str(str(current_partner.id))
    cost_calculation = await service.calculate_energy_cost(
        partner_id=partner_id_str,
        energy_amount=total_energy,
        batch_mode=request.batch_mode
    )
    
    # 폴백 TRX 소각량 계산
    fallback_burn = await service.calculate_fallback_burn_cost(
        withdrawal_requests=withdrawal_requests_dict
    )
    
    # 응답 유효기간 (30분)
    valid_until = datetime.utcnow() + timedelta(minutes=30)
    
    return EnergyCalculationResponse(
        total_energy_required=total_energy,
        base_cost_trx=cost_calculation["base_cost"],
        margin_trx=cost_calculation["margin"],
        saas_fee_trx=cost_calculation["saas_fee"],
        total_cost_trx=cost_calculation["total_cost"],
        energy_price=cost_calculation["energy_price"],
        fallback_burn_trx=fallback_burn,
        valid_until=valid_until.isoformat() + "Z"
    )


@router.post("/charge", response_model=EnergyChargeResponse)
async def request_energy_charge(
    request: EnergyChargeRequest,
    db: Session = Depends(get_db),
    current_partner: Partner = Depends(get_current_partner),
):
    """
    에너지 충전 요청 API
    1단계: TRX 송금 확인
    2단계: 에너지 위임 요청
    3단계: 위임 완료 확인
    """
    service = PartnerEnergyService(db)
    
    # TRX 송금 확인
    payment_verified = await service.verify_trx_payment(
        partner_id=str(current_partner.id),
        trx_amount=request.trx_amount,
        tx_hash=request.tx_hash,
        reference_id=request.reference_id
    )
    
    if not payment_verified:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="TRX 송금을 확인할 수 없습니다"
        )
    
    # 에너지 위임 처리
    delegation_result = await service.delegate_energy(
        partner_id=str(current_partner.id),
        target_address=request.target_address,
        energy_amount=request.energy_amount,
        duration_days=request.duration_days
    )
    
    if not delegation_result["success"]:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"에너지 위임 실패: {delegation_result['error']}"
        )
    
    return EnergyChargeResponse(
        delegation_tx_hash=delegation_result["tx_hash"],
        delegated_energy=delegation_result["energy_amount"],
        expires_at=delegation_result["expires_at"],
        status="completed"
    )


@router.post("/batch-process", response_model=Dict[str, Any])
async def process_withdrawal_batch(
    request: WithdrawalBatchRequest,
    db: Session = Depends(get_db),
    current_partner: Partner = Depends(get_current_partner),
):
    """
    출금 배치 처리 API
    배치 그룹핑 로직 및 SaaS 수수료 최적화
    """
    service = PartnerEnergyService(db)
    
    # 배치 그룹핑 로직 적용
    withdrawal_requests_dict = [req.dict() for req in request.withdrawal_requests]
    batch_groups = await service.optimize_withdrawal_batch(
        partner_id=str(current_partner.id),
        withdrawal_requests=withdrawal_requests_dict
    )
    
    # SaaS 수수료 계산
    saas_fee = await service.calculate_batch_saas_fee(
        withdrawal_count=len(request.withdrawal_requests),
        has_urgent=any(req.type == "immediate" for req in request.withdrawal_requests)
    )
    
    return {
        "batch_groups": batch_groups,
        "total_requests": len(request.withdrawal_requests),
        "optimized_groups": len(batch_groups),
        "estimated_saas_fee": saas_fee,
        "processing_time_estimate": f"{len(batch_groups) * 5} minutes"
    }


@router.get("/monitoring", response_model=EnergyMonitoringResponse)
async def get_energy_monitoring(
    db: Session = Depends(get_db),
    current_partner: Partner = Depends(get_current_partner),
):
    """
    파트너사 지갑 에너지 모니터링
    자동 충전 트리거 조건 확인
    """
    service = PartnerEnergyService(db)
    
    monitoring_data = await service.get_wallet_energy_status(
        partner_id=str(current_partner.id)
    )
    
    # 자동 충전 필요 여부 확인
    auto_recharge_needed = monitoring_data["current_energy"] < monitoring_data["auto_recharge_threshold"]
    
    return EnergyMonitoringResponse(
        hot_wallet_address=monitoring_data["hot_wallet_address"],
        cold_wallet_address=monitoring_data["cold_wallet_address"],
        hot_wallet_usdt_balance=monitoring_data["hot_wallet_usdt_balance"],
        hot_wallet_trx_balance=monitoring_data["hot_wallet_trx_balance"],
        current_energy=monitoring_data["current_energy"],
        daily_average_usage=monitoring_data["daily_average_usage"],
        estimated_depletion=monitoring_data["estimated_depletion"],
        auto_recharge_threshold=monitoring_data["auto_recharge_threshold"],
        auto_recharge_needed=auto_recharge_needed
    )


@router.get("/fee-settings", response_model=Dict[str, Any])
async def get_partner_fee_settings(
    db: Session = Depends(get_db),
    current_partner: Partner = Depends(get_current_partner),
):
    """
    파트너사 SaaS 수수료 설정 조회
    """
    service = PartnerEnergyService(db)
    
    fee_settings = await service.get_partner_fee_settings(str(current_partner.id))
    
    return {
        "partner_id": str(current_partner.id),
        "fee_settings": fee_settings,
        "last_updated": fee_settings.get("last_updated"),
        "effective_from": fee_settings.get("effective_from")
    }


@router.get("/usage-history", response_model=List[Dict[str, Any]])
async def get_energy_usage_history(
    days: int = 30,
    db: Session = Depends(get_db),
    current_partner: Partner = Depends(get_current_partner),
):
    """
    파트너사 에너지 사용 이력 조회
    """
    service = PartnerEnergyService(db)
    
    usage_history = await service.get_energy_usage_history(
        partner_id=str(current_partner.id),
        days=days
    )
    
    return usage_history
