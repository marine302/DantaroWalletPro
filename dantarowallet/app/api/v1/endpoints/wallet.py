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
    
    # 실제 모니터링 설정 업데이트
    wallet = await service.get_wallet(user_id)
    if not wallet:
        raise NotFoundError("Wallet not found")
    
    # 모니터링 상태 업데이트
    try:
        # 직접 지갑 모델 업데이트
        from app.models.wallet import Wallet
        from sqlalchemy import select
        
        # async 세션에서 조회
        result = await db.execute(select(Wallet).filter(Wallet.user_id == user_id))
        wallet_record = result.scalar_one_or_none()
        
        if wallet_record:
            # SQLAlchemy 2.0 스타일로 속성 업데이트
            setattr(wallet_record, 'is_monitored', request.enable)
            await db.commit()
        
        # 응답용 wallet 객체 업데이트
        setattr(wallet, "is_monitored", request.enable)
        
    except Exception as e:
        logger.error(f"Error updating monitoring status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update monitoring status")

    return wallet


@router.get("/network-info")
async def get_network_info(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """네트워크 정보 조회"""
    from datetime import datetime
    
    try:
        # 실제 TRON 네트워크 정보 조회
        # TODO: service.tron.get_block_number() 메서드 구현 후 활성화
        
        # 현재는 기본값 반환 (실제 TRON API 연동 필요)
        block_number = 12345678  # service.tron.get_block_number()
        
        # 네트워크 상태 정보
        network_status = {
            "network": "TRON Mainnet",
            "block_number": block_number,
            "tps": 2000,  # 초당 거래 처리량
            "energy_price": 280,  # sun per energy unit
            "bandwidth_price": 1000,  # sun per bandwidth unit
            "status": "healthy",
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return network_status
        
    except Exception as e:
        logger.error(f"Error fetching network info: {e}")
        # 에러 발생 시 기본값 반환
        return {
            "network": "TRON Mainnet", 
            "block_number": 0,
            "status": "unavailable",
            "error": "Network information temporarily unavailable"
        }
