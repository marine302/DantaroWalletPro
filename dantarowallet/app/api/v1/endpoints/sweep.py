"""
Sweep 자동화 API 엔드포인트
입금 Sweep 자동화 시스템 관리를 위한 RESTful API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_partner
from app.models.partner import Partner
from app.services.sweep.sweep_service import SweepService
from app.services.sweep.hd_wallet_service import HDWalletService
from app.schemas.sweep import (
    # Configuration schemas
    SweepConfigurationCreate,
    SweepConfigurationUpdate,
    SweepConfigurationResponse,
    
    # HD Wallet schemas
    HDWalletMasterResponse,
    UserDepositAddressCreate,
    UserDepositAddressUpdate,
    UserDepositAddressResponse,
    
    # Sweep operation schemas
    ManualSweepRequest,
    ManualSweepResponse,
    EmergencySweepRequest,
    EmergencySweepResponse,
    BatchSweepRequest,
    BatchSweepResponse,
    
    # Log and queue schemas
    SweepLogResponse,
    SweepQueueResponse,
    
    # Analytics schemas
    SweepStatistics,
    SweepAnalytics,
    
    # Enums
    SweepStatus,
    QueueStatus,
    QueueType
)

router = APIRouter()


# ===== HD Wallet Management =====

@router.post("/wallets/master", response_model=HDWalletMasterResponse)
async def create_master_wallet(
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """파트너용 마스터 HD 지갑 생성"""
    try:
        hd_service = HDWalletService(db)
        master_wallet = await hd_service.create_master_wallet(str(partner.id))
        return master_wallet
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create master wallet: {str(e)}"
        )


@router.get("/wallets/master", response_model=HDWalletMasterResponse)
async def get_master_wallet(
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """마스터 HD 지갑 조회"""
    try:
        hd_service = HDWalletService(db)
        wallet_data = await hd_service.get_master_wallet_stats(str(partner.id))
        
        # wallet_data에 exists가 있다면 이전 버전 형식이므로 처리
        if isinstance(wallet_data, dict) and wallet_data.get("exists") is False:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Master wallet not found"
            )
            
        return wallet_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get master wallet: {str(e)}"
        )


@router.post("/addresses", response_model=UserDepositAddressResponse)
async def create_deposit_address(
    request: UserDepositAddressCreate,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """사용자 입금 주소 생성"""
    try:
        hd_service = HDWalletService(db)
        address = await hd_service.generate_deposit_address(
            partner_id=str(partner.id),
            user_id=request.user_id,
            force_new=False
        )
        return address
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create deposit address: {str(e)}"
        )


@router.get("/addresses", response_model=List[UserDepositAddressResponse])
async def list_deposit_addresses(
    user_id: Optional[int] = Query(None, description="사용자 ID 필터"),
    is_active: Optional[bool] = Query(None, description="활성 상태 필터"),
    is_monitored: Optional[bool] = Query(None, description="모니터링 상태 필터"),
    limit: int = Query(100, ge=1, le=1000, description="조회 개수 제한"),
    offset: int = Query(0, ge=0, description="조회 시작 위치"),
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """입금 주소 목록 조회"""
    try:
        hd_service = HDWalletService(db)
        addresses = await hd_service.list_deposit_addresses(
            partner_id=str(partner.id),
            user_id=user_id,
            is_active=is_active,
            is_monitored=is_monitored,
            limit=limit,
            offset=offset
        )
        return addresses
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list deposit addresses: {str(e)}"
        )


@router.put("/addresses/{address_id}", response_model=UserDepositAddressResponse)
async def update_deposit_address(
    address_id: int,
    request: UserDepositAddressUpdate,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """입금 주소 업데이트"""
    try:
        # TODO: 권한 검증 로직 추가
        # 현재는 간단하게 구현
        raise HTTPException(
            status_code=http_status.HTTP_501_NOT_IMPLEMENTED,
            detail="Address update not implemented yet"
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update deposit address: {str(e)}"
        )


@router.delete("/addresses/{address_id}")
async def deactivate_deposit_address(
    address_id: int,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """입금 주소 비활성화"""
    try:
        hd_service = HDWalletService(db)
        await hd_service.deactivate_address(address_id)
        return {"message": "Address deactivated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to deactivate address: {str(e)}"
        )


# ===== Sweep Configuration =====

@router.post("/config", response_model=SweepConfigurationResponse)
async def create_sweep_configuration(
    request: SweepConfigurationCreate,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """Sweep 설정 생성"""
    try:
        sweep_service = SweepService(db)
        config = await sweep_service.create_sweep_configuration(
            partner_id=str(partner.id),
            destination_wallet_id=request.destination_wallet_id,
            **request.dict(exclude={"partner_id", "destination_wallet_id"})
        )
        return config
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create sweep configuration: {str(e)}"
        )


@router.get("/config", response_model=SweepConfigurationResponse)
async def get_sweep_configuration(
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """Sweep 설정 조회"""
    try:
        sweep_service = SweepService(db)
        config = await sweep_service.get_sweep_configuration(str(partner.id))
        if not config:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Sweep configuration not found"
            )
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sweep configuration: {str(e)}"
        )


@router.put("/config", response_model=SweepConfigurationResponse)
async def update_sweep_configuration(
    request: SweepConfigurationUpdate,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """Sweep 설정 업데이트"""
    try:
        sweep_service = SweepService(db)
        config = await sweep_service.update_sweep_configuration(
            partner_id=str(partner.id),
            **request.dict(exclude_unset=True)
        )
        return config
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update sweep configuration: {str(e)}"
        )


# ===== Manual Sweep Operations =====

@router.post("/manual", response_model=ManualSweepResponse)
async def manual_sweep(
    request: ManualSweepRequest,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """단일 주소 수동 Sweep"""
    try:
        sweep_service = SweepService(db)
        result = await sweep_service.manual_sweep(
            partner_id=str(partner.id),
            address=request.address,
            amount=request.amount,
            force=request.force
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to execute manual sweep: {str(e)}"
        )


@router.post("/manual/batch", response_model=BatchSweepResponse)
async def batch_manual_sweep(
    request: BatchSweepRequest,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """배치 수동 Sweep"""
    try:
        sweep_service = SweepService(db)
        result = await sweep_service.batch_sweep(
            partner_id=str(partner.id),
            addresses=request.addresses,
            force=request.force,
            priority=request.priority
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to execute batch manual sweep: {str(e)}"
        )


@router.post("/emergency", response_model=EmergencySweepResponse)
async def emergency_sweep(
    request: EmergencySweepRequest,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """긴급 Sweep"""
    try:
        sweep_service = SweepService(db)
        result = await sweep_service.emergency_sweep(
            partner_id=str(partner.id),
            addresses=request.addresses,
            reason=request.reason
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to execute emergency sweep: {str(e)}"
        )