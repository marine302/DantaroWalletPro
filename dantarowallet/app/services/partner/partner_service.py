"""
파트너 관리 서비스 - 본사 슈퍼 어드민용 파트너 관리 기능
"""
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from fastapi import HTTPException

from app.models.partner import Partner
from app.schemas.partner import (
    PartnerCreate, PartnerUpdate, PartnerResponse, 
    PartnerStats, ApiKeyResponse
)
from app.core.database import get_db


class PartnerService:
    """본사 슈퍼 어드민용 파트너 관리 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_partner(self, partner_data: PartnerCreate) -> Partner:
        """새 파트너사 등록"""
        try:
            # 중복 확인
            existing = self.db.query(Partner).filter(
                or_(
                    Partner.name == partner_data.name,
                    Partner.domain == partner_data.domain,
                    Partner.contact_email == partner_data.contact_email
                )
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="Partner with this name, domain, or email already exists"
                )
            
            # API 키 생성
            api_key = self._generate_api_key()
            api_secret = self._generate_api_secret()
            
            # 파트너 생성
            partner = Partner(
                id=str(uuid.uuid4()),
                name=partner_data.name,
                display_name=partner_data.display_name,
                domain=partner_data.domain,
                contact_email=partner_data.contact_email,
                contact_phone=partner_data.contact_phone,
                business_type=partner_data.business_type,
                api_key=api_key,
                api_secret_hash=self._hash_secret(api_secret),
                status="pending",
                subscription_plan=partner_data.subscription_plan,
                monthly_limit=partner_data.monthly_limit,
                commission_rate=partner_data.commission_rate,
                settings={
                    "branding": partner_data.settings.get("branding", {}),
                    "features": partner_data.settings.get("features", {}),
                    "security": partner_data.settings.get("security", {})
                },
                onboarding_status="pending",
                deployment_config={
                    "template_version": "v1.0",
                    "customizations": [],
                    "deployment_date": None
                }
            )
            
            self.db.add(partner)
            self.db.commit()
            self.db.refresh(partner)
            
            return partner
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create partner: {str(e)}")
    
    async def get_partner_by_id(self, partner_id: str) -> Optional[Partner]:
        """파트너 ID로 조회"""
        partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        return partner
    
    async def get_all_partners(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        business_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Partner]:
        """모든 파트너 조회 (필터링 및 페이징 지원)"""
        query = self.db.query(Partner)
        
        # 필터 적용
        if status:
            query = query.filter(Partner.status == status)
        
        if business_type:
            query = query.filter(Partner.business_type == business_type)
        
        if search:
            search_filter = or_(
                Partner.name.ilike(f"%{search}%"),
                Partner.display_name.ilike(f"%{search}%"),
                Partner.contact_email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # 페이징
        partners = query.offset(skip).limit(limit).all()
        return partners
    
    async def update_partner(self, partner_id: str, update_data: PartnerUpdate) -> Partner:
        """파트너 정보 업데이트"""
        partner = await self.get_partner_by_id(partner_id)
        
        try:
            # 업데이트 가능한 필드들
            update_fields = update_data.dict(exclude_unset=True)
            
            for field, value in update_fields.items():
                if hasattr(partner, field):
                    setattr(partner, field, value)
            
            partner.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(partner)
            
            return partner
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update partner: {str(e)}")
    
    async def delete_partner(self, partner_id: str) -> bool:
        """파트너 삭제 (소프트 삭제)"""
        partner = await self.get_partner_by_id(partner_id)
        
        try:
            # 활성 상태인 파트너는 먼저 비활성화 필요
            if partner.status == "active":
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete active partner. Please deactivate first."
                )
            
            # 소프트 삭제
            partner.status = "deleted"
            partner.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete partner: {str(e)}")
    
    async def generate_api_key(self, partner_id: str) -> ApiKeyResponse:
        """새 API 키 생성"""
        partner = await self.get_partner_by_id(partner_id)
        
        try:
            api_key = self._generate_api_key()
            api_secret = self._generate_api_secret()
            
            # 기존 키를 백업하고 새 키 설정
            partner.previous_api_key = partner.api_key
            partner.api_key = api_key
            partner.api_secret_hash = self._hash_secret(api_secret)
            partner.api_key_created_at = datetime.utcnow()
            partner.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            return ApiKeyResponse(
                api_key=api_key,
                api_secret=api_secret,
                created_at=partner.api_key_created_at
            )
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to generate API key: {str(e)}")
    
    async def rotate_api_key(self, partner_id: str) -> ApiKeyResponse:
        """API 키 순환 (기존 키 유예기간 제공)"""
        return await self.generate_api_key(partner_id)
    
    async def get_partner_statistics(self, partner_id: str) -> PartnerStats:
        """파트너별 통계 조회"""
        partner = await self.get_partner_by_id(partner_id)
        
        try:
            # 기본 통계 계산 (실제 구현에서는 관련 테이블들과 조인)
            stats = PartnerStats(
                partner_id=partner_id,
                total_users=0,  # user 테이블에서 계산
                total_wallets=0,  # wallet 테이블에서 계산
                total_transactions=0,  # transaction 테이블에서 계산
                total_volume=Decimal("0.00"),  # transaction 테이블에서 계산
                total_fees=Decimal("0.00"),  # fee 테이블에서 계산
                energy_used=0,  # energy_usage_history에서 계산
                energy_remaining=partner.energy_balance or 0,
                success_rate=100.0,  # transaction 성공률 계산
                last_active=partner.last_activity_at,
                status=partner.status
            )
            
            return stats
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get partner statistics: {str(e)}")
    
    async def update_partner_status(self, partner_id: str, status: str) -> Partner:
        """파트너 상태 변경"""
        partner = await self.get_partner_by_id(partner_id)
        
        valid_statuses = ["pending", "active", "suspended", "deleted"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {valid_statuses}"
            )
        
        try:
            partner.status = status
            partner.updated_at = datetime.utcnow()
            
            # 상태별 추가 처리
            if status == "active":
                partner.activated_at = datetime.utcnow()
            elif status == "suspended":
                partner.suspended_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(partner)
            
            return partner
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update partner status: {str(e)}")
    
    async def get_partner_activity_log(
        self, 
        partner_id: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """파트너 활동 로그 조회"""
        # 실제 구현에서는 activity_log 테이블에서 조회
        # 현재는 기본 구조만 반환
        return [
            {
                "id": str(uuid.uuid4()),
                "partner_id": partner_id,
                "activity_type": "api_call",
                "description": "API key generated",
                "metadata": {},
                "created_at": datetime.utcnow()
            }
        ]
    
    def _generate_api_key(self) -> str:
        """API 키 생성"""
        prefix = "pk_"
        random_part = secrets.token_urlsafe(32)
        return f"{prefix}{random_part}"
    
    def _generate_api_secret(self) -> str:
        """API 시크릿 생성"""
        prefix = "sk_"
        random_part = secrets.token_urlsafe(64)
        return f"{prefix}{random_part}"
    
    def _hash_secret(self, secret: str) -> str:
        """시크릿 해시 생성"""
        return hashlib.sha256(secret.encode()).hexdigest()
