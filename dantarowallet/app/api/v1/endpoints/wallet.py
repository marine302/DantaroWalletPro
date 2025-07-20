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
from fastapi import APIRouter, Depends, status, HTTPException
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
    """Create New User Wallet
    
    Creates a new TRON wallet for the verified user.
    Returns the wallet address, hex address, and network information.
    """
    service = WalletService(db)
    wallet = await service.create_wallet(getattr(current_user, 'id'))
    await db.commit()

    return WalletCreateResponse(
        address=getattr(wallet, 'address'),
        hex_address=getattr(wallet, 'hex_address'),
        network=settings.TRON_NETWORK,
    )


@router.get("/", response_model=WalletResponse)
async def get_wallet(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get User Wallet Information
    
    Retrieves the user's wallet details including address, hex address,
    and network information. This is for wallet management purposes.
    """
    service = WalletService(db)
    user_id = getattr(current_user, 'id', None)
    if user_id is None:
        raise HTTPException(status_code=400, detail="Invalid user")
    wallet = await service.get_wallet(user_id)

    if not wallet:
        raise NotFoundError("Wallet not found. Please create a wallet first.")

    return wallet


@router.get("/balance", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get On-Chain Wallet Balance
    
    Retrieves the actual on-chain balance from the TRON blockchain.
    This shows the real-time balance directly from the blockchain,
    different from internal system balance (/api/v1/balance/).
    """
    service = WalletService(db)
    user_id = getattr(current_user, 'id', None)
    if user_id is None:
        raise HTTPException(status_code=400, detail="Invalid user")
    wallet = await service.get_wallet(user_id)

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
    """Validate TRON Address
    
    Validates if the provided address is a valid TRON address format
    and checks additional properties if needed.
    """
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
    user_id = getattr(current_user, 'id', None)
    if user_id is None:
        raise HTTPException(status_code=400, detail="Invalid user")
    wallet = await service.get_wallet(user_id)

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
    user_id = getattr(current_user, 'id', None)
    if user_id is None:
        raise HTTPException(status_code=400, detail="Invalid user")
    
    # toggle_monitoring 메서드가 없으므로 임시 구현
    wallet = await service.get_wallet(user_id)
    if not wallet:
        raise NotFoundError("Wallet not found")
    
    # 모니터링 상태 업데이트 (임시)
    setattr(wallet, "is_monitored", request.enable)
    await db.commit()

    return wallet


@router.get("/network-info")
async def get_network_info(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """네트워크 정보 조회"""
    # DB 세션이 필요하므로 전달
    service = WalletService(db)

    # 임시 네트워크 정보 반환
    block_number = 12345678  # service.tron.get_block_number()

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
