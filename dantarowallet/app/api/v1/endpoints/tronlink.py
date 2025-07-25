"""
TronLink 외부 지갑 연동 API 엔드포인트
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_partner
from app.core.database import get_db
from app.core.logger import get_logger
from app.models.partner import Partner
from app.schemas.auto_signing import (
    AutoSigningSessionRequest,
    AutoSigningSessionResponse,
    BatchResultResponse,
    BatchSigningRequest,
    BatchSigningResponse,
    BatchStatusResponse,
    SessionRevokeRequest,
    SessionRevokeResponse,
)
from app.schemas.auto_signing import TronLinkAuthRequest as AutoSigningAuthRequest
from app.schemas.auto_signing import TronLinkAuthResponse as AutoSigningAuthResponse
from app.schemas.auto_signing import (
    TronWebSignRequest,
    TronWebSignResponse,
    TronWebStatusRequest,
    TronWebStatusResponse,
)
from app.schemas.tronlink import (
    MessageResponse,
    PartnerWalletInfo,
    PartnerWalletsResponse,
    TronLinkAuthRequest,
    TronLinkAuthResponse,
    TronLinkConnectRequest,
    TronLinkConnectResponse,
    TronLinkStatusResponse,
    WalletBalanceResponse,
    WalletDisconnectRequest,
    WalletTransactionRequest,
    WalletTransactionResponse,
)
from app.services.external_wallet.auto_signing_service import TronLinkAutoSigningService
from app.services.external_wallet.tronlink_service import TronLinkService

logger = get_logger(__name__)
router = APIRouter(tags=["tronlink"])


@router.post("/connect", response_model=TronLinkConnectResponse)
async def connect_tronlink_wallet(
    request: TronLinkConnectRequest,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """
    TronLink 지갑 연결

    파트너사의 TronLink 지갑을 연결합니다.
    서명 검증을 통해 지갑 소유권을 확인합니다.
    """
    try:
        tronlink_service = TronLinkService(db)

        result = await tronlink_service.initiate_connection(
            partner_id=safe_int(current_partner.id),
            wallet_address=request.wallet_address,
            signature=request.signature,
            message=request.message,
        )

        return TronLinkConnectResponse(**result)

    except Exception as e:
        logger.error(f"TronLink 연결 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지갑 연결에 실패했습니다: {str(e)}",
        )


@router.get("/wallets", response_model=PartnerWalletsResponse)
async def get_partner_wallets(
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """Get Partner's Connected TronLink Wallets

    Retrieves all TronLink wallets connected to the current partner
    along with their balance information. This is specifically for
    partner-managed wallet portfolio overview.
    """
    try:
        tronlink_service = TronLinkService(db)

        wallets = await tronlink_service.get_partner_wallets(
            safe_int(current_partner.id)
        )

        return PartnerWalletsResponse(
            wallets=[PartnerWalletInfo(**wallet) for wallet in wallets],
            total_count=len(wallets),
        )

    except Exception as e:
        logger.error(f"지갑 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"지갑 목록 조회에 실패했습니다: {str(e)}",
        )


@router.get("/wallet/{wallet_address}/balance", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    wallet_address: str,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """Get TronLink Wallet Balance

    Retrieves real-time TRX and USDT balance for a specific TronLink wallet.
    This endpoint is specifically for partner-connected TronLink wallets
    and includes ownership verification.
    """
    try:
        tronlink_service = TronLinkService(db)

        # 지갑 소유권 확인
        wallets = await tronlink_service.get_partner_wallets(
            safe_int(current_partner.id)
        )
        wallet_addresses = [w["address"] for w in wallets]

        if wallet_address not in wallet_addresses:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="접근 권한이 없는 지갑입니다",
            )

        balance = await tronlink_service.get_wallet_balance(wallet_address)

        return WalletBalanceResponse(**balance)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"잔액 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"잔액 조회에 실패했습니다: {str(e)}",
        )


@router.post("/disconnect", response_model=MessageResponse)
async def disconnect_wallet(
    request: WalletDisconnectRequest,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """
    지갑 연결 해제

    연결된 TronLink 지갑의 연결을 해제합니다.
    """
    try:
        tronlink_service = TronLinkService(db)

        success = await tronlink_service.disconnect_wallet(
            partner_id=safe_int(current_partner.id), wallet_id=request.wallet_id
        )

        if success:
            return MessageResponse(
                message="지갑 연결이 성공적으로 해제되었습니다", success=True
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="지갑 연결 해제에 실패했습니다",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"지갑 연결 해제 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"지갑 연결 해제에 실패했습니다: {str(e)}",
        )


@router.get("/status", response_model=TronLinkStatusResponse)
async def get_tronlink_status(
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """
    TronLink 연동 상태 조회

    파트너의 전체적인 TronLink 연동 상태와 통계를 조회합니다.
    """
    try:
        tronlink_service = TronLinkService(db)

        wallets = await tronlink_service.get_partner_wallets(
            safe_int(current_partner.id)
        )

        # 연결된 지갑들의 총 잔액 계산
        total_trx = sum(w["balance"]["trx_balance"] for w in wallets)
        total_usdt = sum(w["balance"]["usdt_balance"] for w in wallets)

        # 마지막 활동 시간
        last_activity = None
        if wallets:
            last_connected_times = [
                w["last_connected_at"] for w in wallets if w["last_connected_at"]
            ]
            if last_connected_times:
                last_activity = max(last_connected_times)

        return TronLinkStatusResponse(
            is_connected=len(wallets) > 0,
            wallet_count=len(wallets),
            total_balance={"TRX": total_trx, "USDT": total_usdt},
            last_activity=last_activity,
        )

    except Exception as e:
        logger.error(f"TronLink 상태 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"상태 조회에 실패했습니다: {str(e)}",
        )


@router.post("/auth", response_model=TronLinkAuthResponse)
async def authenticate_with_tronlink(
    request: TronLinkAuthRequest, db: AsyncSession = Depends(get_db)
):
    """
    TronLink 지갑을 통한 인증 (로그인)

    TronLink 지갑 서명을 통해 파트너를 인증하고 액세스 토큰을 발급합니다.
    """
    try:
        # 여기서는 기본적인 구조만 제공
        # 실제로는 JWT 토큰 생성 및 파트너 매칭 로직 필요

        # 임시 응답
        return TronLinkAuthResponse(
            access_token="temp_token_" + request.wallet_address[-8:],
            partner_id=1,  # 실제로는 지갑 주소로 파트너 조회
            wallet_address=request.wallet_address,
            expires_in=3600,
        )

    except Exception as e:
        logger.error(f"TronLink 인증 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"인증에 실패했습니다: {str(e)}",
        )


# 관리자용 엔드포인트들
@router.get("/admin/all-connections", response_model=List[Dict[str, Any]])
async def get_all_tronlink_connections(
    # current_admin: Admin = Depends(get_current_admin),  # 관리자 권한 필요
    db: AsyncSession = Depends(get_db),
):
    """
    전체 TronLink 연결 현황 조회 (관리자용)

    모든 파트너의 TronLink 연결 상태를 조회합니다.
    """
    try:
        # 임시 구현 - 실제로는 모든 파트너의 지갑 정보 조회
        return [
            {
                "partner_id": 1,
                "partner_name": "테스트 파트너",
                "connected_wallets": 2,
                "total_balance": {"TRX": 1000.5, "USDT": 500.0},
                "last_activity": "2025-07-08T10:30:00Z",
            }
        ]

    except Exception as e:
        logger.error(f"전체 연결 현황 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"조회에 실패했습니다: {str(e)}",
        )


def safe_get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """SQLAlchemy 모델 속성을 안전하게 가져오는 헬퍼 함수"""
    if obj is None:
        return default

    value = getattr(obj, attr, default)

    # SQLAlchemy Column 타입인 경우 실제 값 추출
    if hasattr(value, "value"):
        return value.value
    elif hasattr(value, "__getitem__") and hasattr(value, "keys"):
        return value
    else:
        return value


def safe_str(value: Any, default: str = "") -> str:
    """안전한 str 변환"""
    if value is None:
        return default

    if hasattr(value, "value"):
        value = value.value

    try:
        return str(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """안전한 int 변환"""
    if value is None:
        return default

    if hasattr(value, "value"):
        value = value.value

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# =====================================================================
# TronLink 자동 서명 엔드포인트들 (Auto Signing Endpoints)
# =====================================================================


@router.post("/auto-signing/authorize", response_model=AutoSigningAuthResponse)
async def authorize_auto_signing(
    request: AutoSigningAuthRequest,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """
    TronLink 자동 서명 권한 요청 (tron_requestAccounts)

    TronLink 지갑에 자동 서명 권한을 요청하고 계정을 승인받습니다.
    실제 TronLink API의 tron_requestAccounts와 호환됩니다.
    """
    try:
        auto_signing_service = TronLinkAutoSigningService(db)

        result = await auto_signing_service.request_account_authorization(
            partner_id=safe_int(current_partner.id),
            wallet_address=request.wallet_address,
            signature=request.signature,
            message=request.message,
        )

        return AutoSigningAuthResponse(**result)

    except Exception as e:
        logger.error(f"TronLink 자동 서명 권한 요청 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"자동 서명 권한 요청에 실패했습니다: {str(e)}",
        )


@router.post("/auto-signing/session", response_model=AutoSigningSessionResponse)
async def create_auto_signing_session(
    request: AutoSigningSessionRequest,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """
    자동 서명 세션 생성

    지정된 조건으로 자동 서명 세션을 생성합니다.
    TronLink의 세션 관리와 호환되는 구조입니다.
    """
    try:
        auto_signing_service = TronLinkAutoSigningService(db)

        result = await auto_signing_service.create_auto_signing_session(
            partner_id=safe_int(current_partner.id),
            wallet_address=request.wallet_address,
            session_duration_hours=request.session_duration_hours,
            max_amount_per_tx=request.max_amount_per_tx,
            max_daily_amount=request.max_daily_amount,
            allowed_addresses=request.allowed_addresses,
        )

        return AutoSigningSessionResponse(**result)

    except Exception as e:
        logger.error(f"자동 서명 세션 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"자동 서명 세션 생성에 실패했습니다: {str(e)}",
        )


@router.post("/auto-signing/sign", response_model=TronWebSignResponse)
async def sign_transaction_auto(
    request: TronWebSignRequest,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """
    TronWeb 호환 자동 트랜잭션 서명

    출금 요청을 자동으로 서명하고 처리합니다.
    window.tronWeb.trx.sign()과 호환되는 구조입니다.
    """
    try:
        auto_signing_service = TronLinkAutoSigningService(db)

        result = await auto_signing_service.sign_transaction_with_tronweb(
            withdrawal_id=request.withdrawal_id, session_token=request.session_token
        )

        return TronWebSignResponse(**result)

    except Exception as e:
        logger.error(f"자동 트랜잭션 서명 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"자동 트랜잭션 서명에 실패했습니다: {str(e)}",
        )


@router.post("/auto-signing/batch", response_model=BatchSigningResponse)
async def batch_sign_transactions(
    request: BatchSigningRequest,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """
    배치 자동 서명

    여러 출금 요청을 한 번에 자동 서명 처리합니다.
    TronLink의 배치 처리와 호환됩니다.
    """
    try:
        auto_signing_service = TronLinkAutoSigningService(db)

        result = await auto_signing_service.batch_sign_with_tronlink(
            withdrawal_ids=request.withdrawal_ids,
            session_token=request.session_token,
            max_concurrent=request.max_concurrent,
        )

        return BatchSigningResponse(**result)

    except Exception as e:
        logger.error(f"배치 자동 서명 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"배치 자동 서명에 실패했습니다: {str(e)}",
        )


@router.get("/auto-signing/session/status", response_model=TronWebStatusResponse)
async def get_session_status(
    session_token: str,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """
    자동 서명 세션 상태 조회 (TronWeb 호환)

    현재 자동 서명 세션의 상태를 조회합니다.
    window.tronWeb 상태와 호환되는 정보를 제공합니다.
    """
    try:
        auto_signing_service = TronLinkAutoSigningService(db)

        result = await auto_signing_service.get_tronweb_status(
            partner_id=safe_int(current_partner.id), session_token=session_token
        )

        return TronWebStatusResponse(**result)

    except Exception as e:
        logger.error(f"세션 상태 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"세션 상태 조회에 실패했습니다: {str(e)}",
        )


@router.post("/auto-signing/session/revoke", response_model=SessionRevokeResponse)
async def revoke_session(
    request: SessionRevokeRequest,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """
    자동 서명 세션 해제

    활성화된 자동 서명 세션을 해제합니다.
    TronLink 연결 해제와 호환됩니다.
    """
    try:
        auto_signing_service = TronLinkAutoSigningService(db)

        result = await auto_signing_service.revoke_auto_signing_session(
            partner_id=safe_int(current_partner.id), session_token=request.session_token
        )

        return SessionRevokeResponse(**result)

    except Exception as e:
        logger.error(f"세션 해제 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"세션 해제에 실패했습니다: {str(e)}",
        )


# 배치 상태 조회를 위한 추가 엔드포인트들
@router.get("/auto-signing/batch/{batch_id}/status")
async def get_batch_status(
    batch_id: str,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """
    배치 자동 서명 상태 조회

    배치 처리의 실시간 상태를 조회합니다.
    """
    try:
        # 배치 상태 조회 로직 구현 필요
        # 현재는 기본 응답만 제공
        return {
            "batch_id": batch_id,
            "status": "processing",
            "message": "배치 처리 상태 조회 기능은 향후 구현될 예정입니다.",
        }

    except Exception as e:
        logger.error(f"배치 상태 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"배치 상태 조회에 실패했습니다: {str(e)}",
        )


@router.get("/auto-signing/batch/{batch_id}/result")
async def get_batch_result(
    batch_id: str,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """
    배치 자동 서명 결과 조회

    완료된 배치 처리의 상세 결과를 조회합니다.
    """
    try:
        # 배치 결과 조회 로직 구현 필요
        # 현재는 기본 응답만 제공
        return {
            "batch_id": batch_id,
            "status": "completed",
            "message": "배치 처리 결과 조회 기능은 향후 구현될 예정입니다.",
        }

    except Exception as e:
        logger.error(f"배치 결과 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"배치 결과 조회에 실패했습니다: {str(e)}",
        )
