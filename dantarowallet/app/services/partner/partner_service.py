"""
파트너 관리 서비스.
파트너사 CRUD, API 키 관리, 통계 조회 등 파트너 관련 모든 비즈니스 로직을 담당합니다.
"""

from typing import List, Optional
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timedelta
import secrets
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import selectinload

from app.models.partner import Partner
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.schemas.partner import PartnerCreate, PartnerUpdate, PartnerStats
from app.core.exceptions import PartnerNotFoundError, DuplicatePartnerError
from app.core.logger import get_logger

logger = get_logger(__name__)


class PartnerService:
    """파트너 관리 서비스 클래스."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_partner(self, partner_data: PartnerCreate) -> Partner:
        """새 파트너사를 생성합니다."""
        try:
            # 중복 체크 (company_name, contact_email)
            existing = await self._check_duplicate_partner(
                partner_data.company_name, 
                partner_data.contact_email
            )
            if existing:
                raise DuplicatePartnerError(
                    f"Partner already exists: {partner_data.company_name}"
                )
            
            # API 키 생성
            api_key = self._generate_api_key()
            api_secret = self._generate_api_secret()
            
            # 파트너 객체 생성
            partner = Partner(
                id=uuid4(),
                company_name=partner_data.company_name,
                contact_email=partner_data.contact_email,
                contact_phone=partner_data.contact_phone,
                business_type=partner_data.business_type,
                api_key=api_key,
                api_secret_hash=self._hash_secret(api_secret),
                is_active=True,
                onboarding_status="pending",
                fee_config={
                    "transaction_fee_rate": "0.001",  # 0.1%
                    "min_fee": "1.0",
                    "max_fee": "100.0"
                },
                energy_allocation=1000,  # 기본 에너지 할당량
                custom_branding={},
                deployment_config={},
                created_at=datetime.utcnow()
            )
            
            self.db.add(partner)
            await self.db.commit()
            await self.db.refresh(partner)
            
            logger.info(f"Created new partner: {partner.company_name} (ID: {partner.id})")
            
            # API 시크릿은 생성 시에만 반환 (보안)
            partner.api_secret = api_secret
            return partner
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create partner: {str(e)}")
            raise
    
    async def get_partner_by_id(self, partner_id: UUID) -> Partner:
        """ID로 파트너를 조회합니다."""
        result = await self.db.execute(
            select(Partner).where(Partner.id == partner_id)
        )
        partner = result.scalar_one_or_none()
        
        if not partner:
            raise PartnerNotFoundError(f"Partner not found: {partner_id}")
        
        return partner
    
    async def get_partner_by_api_key(self, api_key: str) -> Optional[Partner]:
        """API 키로 파트너를 조회합니다."""
        result = await self.db.execute(
            select(Partner).where(
                and_(Partner.api_key == api_key, Partner.is_active == True)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all_partners(
        self, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Partner]:
        """모든 파트너를 조회합니다."""
        query = select(Partner).offset(skip).limit(limit)
        
        if is_active is not None:
            query = query.where(Partner.is_active == is_active)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_partner(
        self, 
        partner_id: UUID, 
        update_data: PartnerUpdate
    ) -> Partner:
        """파트너 정보를 업데이트합니다."""
        partner = await self.get_partner_by_id(partner_id)
        
        # 업데이트 가능한 필드들만 적용
        update_fields = update_data.dict(exclude_unset=True)
        
        # 특별 처리가 필요한 필드들
        if "fee_config" in update_fields:
            # 기존 설정과 병합
            current_config = partner.fee_config or {}
            current_config.update(update_fields["fee_config"])
            update_fields["fee_config"] = current_config
        
        if "custom_branding" in update_fields:
            # 기존 브랜딩과 병합
            current_branding = partner.custom_branding or {}
            current_branding.update(update_fields["custom_branding"])
            update_fields["custom_branding"] = current_branding
        
        # 업데이트 실행
        await self.db.execute(
            update(Partner)
            .where(Partner.id == partner_id)
            .values(**update_fields)
        )
        await self.db.commit()
        
        # 업데이트된 파트너 반환
        updated_partner = await self.get_partner_by_id(partner_id)
        logger.info(f"Updated partner: {partner_id}")
        
        return updated_partner
    
    async def delete_partner(self, partner_id: UUID) -> bool:
        """파트너를 삭제합니다 (soft delete)."""
        partner = await self.get_partner_by_id(partner_id)
        
        # Soft delete - is_active를 False로 설정
        await self.db.execute(
            update(Partner)
            .where(Partner.id == partner_id)
            .values(is_active=False, deleted_at=datetime.utcnow())
        )
        await self.db.commit()
        
        logger.info(f"Deleted partner: {partner_id}")
        return True
    
    async def generate_api_key(self, partner_id: UUID) -> str:
        """새 API 키를 생성합니다."""
        partner = await self.get_partner_by_id(partner_id)
        
        new_api_key = self._generate_api_key()
        
        await self.db.execute(
            update(Partner)
            .where(Partner.id == partner_id)
            .values(api_key=new_api_key)
        )
        await self.db.commit()
        
        logger.info(f"Generated new API key for partner: {partner_id}")
        return new_api_key
    
    async def rotate_api_key(self, partner_id: UUID) -> dict:
        """API 키와 시크릿을 모두 회전시킵니다."""
        partner = await self.get_partner_by_id(partner_id)
        
        new_api_key = self._generate_api_key()
        new_api_secret = self._generate_api_secret()
        new_secret_hash = self._hash_secret(new_api_secret)
        
        await self.db.execute(
            update(Partner)
            .where(Partner.id == partner_id)
            .values(
                api_key=new_api_key,
                api_secret_hash=new_secret_hash
            )
        )
        await self.db.commit()
        
        logger.info(f"Rotated API credentials for partner: {partner_id}")
        
        return {
            "api_key": new_api_key,
            "api_secret": new_api_secret  # 이때만 반환
        }
    
    async def verify_api_credentials(
        self, 
        api_key: str, 
        api_secret: str
    ) -> Optional[Partner]:
        """API 자격증명을 검증합니다."""
        partner = await self.get_partner_by_api_key(api_key)
        
        if not partner:
            return None
        
        if not self._verify_secret(api_secret, partner.api_secret_hash):
            return None
        
        return partner
    
    async def get_partner_statistics(self, partner_id: UUID) -> PartnerStats:
        """파트너의 통계 정보를 조회합니다."""
        partner = await self.get_partner_by_id(partner_id)
        
        # 거래 통계 계산
        today = datetime.utcnow().date()
        month_start = today.replace(day=1)
        
        # 전체 거래량
        total_transactions = await self.db.execute(
            select(func.count(Transaction.id))
            .join(Wallet, Transaction.wallet_id == Wallet.id)
            .where(Wallet.partner_id == partner_id)
        )
        total_tx_count = total_transactions.scalar() or 0
        
        # 이번 달 거래량
        monthly_transactions = await self.db.execute(
            select(
                func.count(Transaction.id),
                func.sum(Transaction.amount)
            )
            .join(Wallet, Transaction.wallet_id == Wallet.id)
            .where(
                and_(
                    Wallet.partner_id == partner_id,
                    Transaction.created_at >= month_start
                )
            )
        )
        monthly_result = monthly_transactions.first()
        monthly_tx_count = monthly_result[0] or 0
        monthly_volume = monthly_result[1] or Decimal('0')
        
        # 지갑 수
        wallet_count = await self.db.execute(
            select(func.count(Wallet.id))
            .where(Wallet.partner_id == partner_id)
        )
        total_wallets = wallet_count.scalar() or 0
        
        # 에너지 사용량 (임시 - 나중에 별도 테이블에서 조회)
        energy_used = partner.energy_allocation * 0.3  # 임시 계산
        
        return PartnerStats(
            partner_id=partner_id,
            total_transactions=total_tx_count,
            monthly_transactions=monthly_tx_count,
            monthly_volume=monthly_volume,
            total_wallets=total_wallets,
            energy_allocated=partner.energy_allocation,
            energy_used=int(energy_used),
            revenue_generated=monthly_volume * Decimal(partner.fee_config.get("transaction_fee_rate", "0.001")),
            last_activity=partner.updated_at or partner.created_at
        )
    
    # Private helper methods
    
    async def _check_duplicate_partner(
        self, 
        company_name: str, 
        contact_email: str
    ) -> Optional[Partner]:
        """중복 파트너 체크."""
        result = await self.db.execute(
            select(Partner).where(
                and_(
                    Partner.company_name == company_name,
                    Partner.contact_email == contact_email,
                    Partner.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    def _generate_api_key(self) -> str:
        """API 키 생성."""
        return f"dk_{secrets.token_urlsafe(32)}"
    
    def _generate_api_secret(self) -> str:
        """API 시크릿 생성."""
        return secrets.token_urlsafe(64)
    
    def _hash_secret(self, secret: str) -> str:
        """시크릿 해시 생성."""
        return hashlib.sha256(secret.encode()).hexdigest()
    
    def _verify_secret(self, secret: str, secret_hash: str) -> bool:
        """시크릿 검증."""
        return hashlib.sha256(secret.encode()).hexdigest() == secret_hash
