"""
지갑 관련 API 엔드포인트.
지갑 생성, 조회, 잔고 확인, 주소 검증 등의 기능을 제공합니다.
"""
import logging
from datetime import datetime

from app.api import deps
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.schemas.wallet import (
    AddressValidationRequest,
    AddressValidationResponse,
    WalletBalanceResponse,
    WalletCreateResponse,
    WalletMonitoringRequest,
    WalletResponse,
)
from app.services.wallet_service import WalletService
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/create", response_model=WalletCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_wallet(
    current_user: User = Depends(deps.get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """사용자 지갑 생성"""
    service = WalletService(db)
    wallet = await service.create_wallet(current_user.id)
    await db.commit()

    return WalletCreateResponse(
        address=wallet.address,
        hex_address=wallet.hex_address,
        network=settings.TRON_NETWORK,
    )


@router.get("/", response_model=WalletResponse)
async def get_wallet(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """현재 사용자 지갑 정보 조회"""
    service = WalletService(db)
    wallet = await service.get_wallet(current_user.id)

    if not wallet:
        raise NotFoundError("Wallet not found. Please create a wallet first.")

    return wallet


@router.get("/balance", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """지갑 온체인 잔고 조회"""
    service = WalletService(db)
    wallet = await service.get_wallet(current_user.id)

    if not wallet:
        raise NotFoundError("Wallet not found")

    balance_info = await service.get_wallet_balance(wallet)
    return balance_info


@router.post("/validate-address", response_model=AddressValidationResponse)
async def validate_address(
    request: AddressValidationRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """TRON 주소 유효성 검증"""
    service = WalletService(db)

    # 기본 유효성 검증
    is_valid = await service.tron.validate_address(request.address)

    if not is_valid:
        return AddressValidationResponse(
            address=request.address,
            is_valid=False,
            message="Invalid TRON address format",
        )

    # 내부 주소인지 확인
    internal_wallet = await service.get_wallet_by_address(request.address)
    is_internal = internal_wallet is not None

    return AddressValidationResponse(
        address=request.address,
        is_valid=True,
        is_internal=is_internal,
        message="Internal wallet address" if is_internal else "Valid external address",
    )


@router.post("/monitoring", response_model=WalletResponse)
async def update_monitoring(
    request: WalletMonitoringRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """지갑 모니터링 설정 업데이트"""
    service = WalletService(db)
    wallet = await service.get_wallet(current_user.id)

    if not wallet:
        raise NotFoundError("Wallet not found")

    setattr(wallet, "is_monitored", request.enable)
    await db.commit()

    return wallet


async def toggle_monitoring(
    request: WalletMonitoringRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """지갑 모니터링 설정 변경"""
    service = WalletService(db)
    wallet = await service.toggle_monitoring(current_user.id, request.enable)
    await db.commit()

    return wallet


@router.get("/network-info")
async def get_network_info(current_user: User = Depends(deps.get_current_active_user)):
    """네트워크 정보 조회"""
    service = WalletService(None)  # DB 불필요

    block_number = service.tron.get_block_number()

    return {
        "network": settings.TRON_NETWORK,
        "current_block": block_number,
        "usdt_contract": "TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf"
        if settings.TRON_NETWORK == "nile"
        else "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
        "explorer_url": "https://nile.tronscan.org"
        if settings.TRON_NETWORK == "nile"
        else "https://tronscan.org",
    }
