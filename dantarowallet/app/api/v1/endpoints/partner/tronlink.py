"""
TronLink 외부 지갑 연동 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_partner
from app.models.partner import Partner
from app.services.external_wallet_service import ExternalWalletService
from app.schemas.external_wallet import (
    ConnectExternalWalletRequest,
    ExternalWalletResponse,
    WalletBalanceResponse,
    TransactionHistoryResponse,
    MessageResponse
)
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["TronLink 연동"])


@router.post("/connect", response_model=ExternalWalletResponse)
async def connect_tronlink_wallet(
    request: ConnectExternalWalletRequest,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """TronLink 지갑 연결"""
    try:
        wallet_service = ExternalWalletService(db)
        wallet = await wallet_service.connect_external_wallet(
            partner_id=int(current_partner.id),
            wallet_type="TRONLINK",
            wallet_address=request.wallet_address,
            public_key=request.public_key,
            signature=request.signature
        )
        
        return ExternalWalletResponse.model_validate(wallet)
        
    except Exception as e:
        logger.error(f"TronLink 지갑 연결 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지갑 연결에 실패했습니다: {str(e)}"
        )


@router.get("/wallets", response_model=List[ExternalWalletResponse])
async def get_connected_wallets(
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """연결된 TronLink 지갑 목록 조회"""
    try:
        wallet_service = ExternalWalletService(db)
        wallets = await wallet_service.get_partner_wallets(int(current_partner.id))
        
        return [ExternalWalletResponse.model_validate(wallet) for wallet in wallets]
        
    except Exception as e:
        logger.error(f"지갑 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="지갑 목록 조회에 실패했습니다"
        )


@router.get("/balance/{wallet_address}", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    wallet_address: str,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """TronLink 지갑 잔액 조회"""
    try:
        wallet_service = ExternalWalletService(db)
        balance_info = await wallet_service.get_wallet_balance(
            partner_id=int(current_partner.id),
            wallet_address=wallet_address
        )
        
        return WalletBalanceResponse(**balance_info)
        
    except Exception as e:
        logger.error(f"지갑 잔액 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="지갑 잔액 조회에 실패했습니다"
        )


@router.get("/transactions/{wallet_address}", response_model=List[TransactionHistoryResponse])
async def get_wallet_transactions(
    wallet_address: str,
    limit: int = 20,
    offset: int = 0,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """TronLink 지갑 거래 내역 조회"""
    try:
        wallet_service = ExternalWalletService(db)
        transactions = await wallet_service.get_wallet_transactions(
            partner_id=int(current_partner.id),
            wallet_address=wallet_address,
            limit=limit,
            offset=offset
        )
        
        return [TransactionHistoryResponse(**tx) for tx in transactions]
        
    except Exception as e:
        logger.error(f"거래 내역 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="거래 내역 조회에 실패했습니다"
        )


@router.delete("/disconnect/{wallet_address}", response_model=MessageResponse)
async def disconnect_wallet(
    wallet_address: str,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """TronLink 지갑 연결 해제"""
    try:
        wallet_service = ExternalWalletService(db)
        success = await wallet_service.disconnect_wallet(
            partner_id=int(current_partner.id),
            wallet_address=wallet_address
        )
        
        if success:
            return MessageResponse(message="지갑 연결이 해제되었습니다")
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="연결된 지갑을 찾을 수 없습니다"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"지갑 연결 해제 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="지갑 연결 해제에 실패했습니다"
        )


@router.post("/verify-signature", response_model=MessageResponse)
async def verify_wallet_signature(
    wallet_address: str,
    message: str,
    signature: str,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """TronLink 지갑 서명 검증"""
    try:
        wallet_service = ExternalWalletService(db)
        is_valid = await wallet_service.verify_wallet_signature(
            wallet_address=wallet_address,
            message=message,
            signature=signature
        )
        
        if is_valid:
            return MessageResponse(message="서명이 유효합니다")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="서명이 유효하지 않습니다"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"서명 검증 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서명 검증에 실패했습니다"
        )
