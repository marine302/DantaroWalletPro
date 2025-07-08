"""
TronLink 지갑 연동 서비스
"""
from typing import Dict, List, Optional, Any
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from tronpy import Tron
from tronpy.keys import PrivateKey

from app.models.partner_wallet import PartnerWallet, WalletType, TransactionStatus
from app.models.partner import Partner
from app.core.logger import get_logger
from app.core.exceptions import ValidationError, AuthenticationError

logger = get_logger(__name__)


def safe_get_attr(obj, attr, default=None):
    """SQLAlchemy 컬럼 속성을 안전하게 가져오는 헬퍼 함수"""
    if obj is None:
        return default
    value = getattr(obj, attr, default)
    if value is not None and hasattr(value, 'value'):
        return value.value
    return value


def safe_bool(value, default=False):
    """안전한 bool 변환"""
    if value is None:
        return default
    if hasattr(value, 'value'):
        value = value.value
    try:
        return bool(value)
    except (TypeError, ValueError):
        return default


class TronLinkService:
    """TronLink 지갑 연동 및 관리 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tron = Tron()
    
    async def initiate_connection(
        self, 
        partner_id: int,
        wallet_address: str,
        signature: str,
        message: str
    ) -> Dict[str, Any]:
        """
        TronLink 지갑 연결 시작
        
        Args:
            partner_id: 파트너 ID
            wallet_address: TronLink 지갑 주소
            signature: 서명
            message: 서명된 메시지
        """
        try:
            # 서명 검증
            is_valid = await self._verify_signature(wallet_address, signature, message)
            if not is_valid:
                raise AuthenticationError("지갑 서명 검증에 실패했습니다")
            
            # 기존 지갑 확인
            existing_wallet = await self._get_partner_wallet(partner_id, wallet_address)
            
            if existing_wallet:
                # 기존 지갑 업데이트
                await self._update_wallet_connection(existing_wallet)
                return {
                    "status": "reconnected",
                    "wallet_id": existing_wallet.id,
                    "address": wallet_address,
                    "message": "기존 지갑이 재연결되었습니다"
                }
            else:
                # 새 지갑 등록
                new_wallet = await self._create_partner_wallet(partner_id, wallet_address)
                return {
                    "status": "connected",
                    "wallet_id": new_wallet.id,
                    "address": wallet_address,
                    "message": "지갑이 성공적으로 연결되었습니다"
                }
                
        except Exception as e:
            logger.error(f"TronLink 연결 실패: {str(e)}")
            raise
    
    async def disconnect_wallet(self, partner_id: int, wallet_id: int) -> bool:
        """지갑 연결 해제"""
        try:
            wallet = await self.db.get(PartnerWallet, wallet_id)
            if not wallet or safe_get_attr(wallet, 'partner_id') != partner_id:
                raise ValidationError("지갑을 찾을 수 없습니다")
            
            # 상태 업데이트
            await self.db.execute(
                update(PartnerWallet)
                .where(PartnerWallet.id == wallet_id)
                .values(
                    is_connected=False,
                    disconnected_at=datetime.utcnow()
                )
            )
            await self.db.commit()
            
            logger.info(f"지갑 연결 해제 완료: {wallet.address}")
            return True
            
        except Exception as e:
            logger.error(f"지갑 연결 해제 실패: {str(e)}")
            raise
    
    async def get_wallet_balance(self, wallet_address: str) -> Dict[str, Any]:
        """지갑 잔액 조회"""
        try:
            # TRX 잔액
            trx_balance = self.tron.get_account_balance(wallet_address)
            
            # USDT 잔액 (TRC20)
            usdt_contract = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # USDT TRC20
            try:
                usdt_balance = self.tron.get_contract(usdt_contract).functions.balanceOf(wallet_address).call()
                usdt_balance = usdt_balance / 1_000_000  # USDT는 6자리 소수점
            except:
                usdt_balance = 0
            
            return {
                "address": wallet_address,
                "trx_balance": float(trx_balance),
                "usdt_balance": float(usdt_balance),
                "updated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"잔액 조회 실패: {str(e)}")
            raise
    
    async def get_partner_wallets(self, partner_id: int) -> List[Dict[str, Any]]:
        """파트너의 연결된 지갑 목록 조회"""
        try:
            query = select(PartnerWallet).where(
                PartnerWallet.partner_id == partner_id,
                PartnerWallet.provider == WalletType.TRONLINK
            ).order_by(PartnerWallet.created_at.desc())
            
            result = await self.db.execute(query)
            wallets = result.scalars().all()
            
            wallet_list = []
            for wallet in wallets:
                # 잔액 정보 조회
                balance_info = await self.get_wallet_balance(wallet.address)
                
                last_connected = safe_get_attr(wallet, 'last_connected_at')
                created_at = safe_get_attr(wallet, 'created_at')
                
                wallet_list.append({
                    "id": safe_get_attr(wallet, 'id'),
                    "address": safe_get_attr(wallet, 'wallet_address'),
                    "wallet_type": safe_get_attr(wallet, 'wallet_type'),
                    "is_connected": safe_get_attr(wallet, 'is_connected'),
                    "balance": balance_info,
                    "last_connected_at": last_connected.isoformat() if last_connected else None,
                    "created_at": created_at.isoformat() if created_at else None
                })
            
            return wallet_list
            
        except Exception as e:
            logger.error(f"지갑 목록 조회 실패: {str(e)}")
            raise
    
    async def _verify_signature(self, address: str, signature: str, message: str) -> bool:
        """TronLink 서명 검증"""
        try:
            # TRON 서명 검증 로직
            # 실제로는 tronpy나 다른 라이브러리를 사용해야 함
            # 여기서는 기본적인 검증만 수행
            
            if len(signature) != 130:  # 65바이트 hex
                return False
                
            # 메시지 해시 생성
            message_hash = hashlib.sha256(message.encode()).hexdigest()
            
            # 실제 구현에서는 TRON 서명 검증 라이브러리 사용
            # 현재는 임시로 True 반환
            logger.info(f"서명 검증 수행: {address}, 메시지: {message[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"서명 검증 실패: {str(e)}")
            return False
    
    async def _get_partner_wallet(self, partner_id: int, address: str) -> Optional[PartnerWallet]:
        """기존 파트너 지갑 조회"""
        query = select(PartnerWallet).where(
            PartnerWallet.partner_id == partner_id,
            PartnerWallet.address == address,
            PartnerWallet.provider == WalletType.TRONLINK
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _create_partner_wallet(self, partner_id: int, address: str) -> PartnerWallet:
        """새 파트너 지갑 생성"""
        wallet = PartnerWallet(
            partner_id=partner_id,
            address=address,
            wallet_type=WalletType.TRONLINK,
            is_connected=True,
            last_connected_at=datetime.utcnow()
        )
        
        self.db.add(wallet)
        await self.db.commit()
        await self.db.refresh(wallet)
        
        logger.info(f"새 지갑 등록 완료: {address}")
        return wallet
    
    async def _update_wallet_connection(self, wallet: PartnerWallet) -> None:
        """지갑 연결 정보 업데이트"""
        await self.db.execute(
            update(PartnerWallet)
            .where(PartnerWallet.id == wallet.id)
            .values(
                is_connected=True,
                last_connected_at=datetime.utcnow()
            )
        )
        await self.db.commit()
        
        logger.info(f"지갑 연결 정보 업데이트 완료: {wallet.address}")
