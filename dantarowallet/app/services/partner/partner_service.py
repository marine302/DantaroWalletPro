"""
파트너 관리 서비스 - 본사 슈퍼 어드민용 파트너 관리 기능
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, update
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.partner import Partner
from app.schemas.partner import (
    ApiKeyResponse,
    PartnerCreate,
    PartnerResponse,
    PartnerStats,
    PartnerUpdate,
)


# 헬퍼 함수
def safe_get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """SQLAlchemy 객체에서 안전하게 속성을 가져옵니다."""
    if obj is None:
        return default
    try:
        value = getattr(obj, attr, default)
        # SQLAlchemy Column 타입인지 확인
        if hasattr(value, "__class__") and "Column" in str(value.__class__):
            return default
        return value
    except (AttributeError, TypeError):
        return default


def safe_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    """안전하게 Decimal로 변환합니다."""
    try:
        if value is None:
            return default
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """안전하게 float로 변환합니다."""
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


class PartnerService:
    """본사 슈퍼 어드민용 파트너 관리 서비스"""

    def __init__(self, db: Session):
        self.db = db

    async def create_partner(self, partner_data: PartnerCreate) -> Partner:
        """새 파트너사 등록"""
        try:
            # 중복 확인
            existing = (
                self.db.query(Partner)
                .filter(
                    or_(
                        Partner.name == partner_data.name,
                        Partner.domain == partner_data.domain,
                        Partner.contact_email == partner_data.contact_email,
                    )
                )
                .first()
            )

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="Partner with this name, domain, or email already exists",
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
                    "security": partner_data.settings.get("security", {}),
                },
                onboarding_status="pending",
                deployment_config={
                    "template_version": "v1.0",
                    "customizations": [],
                    "deployment_date": None,
                },
            )

            self.db.add(partner)
            self.db.commit()
            self.db.refresh(partner)

            return partner

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to create partner: {str(e)}"
            )

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
        search: Optional[str] = None,
    ) -> List[Partner]:
        """모든 파트너 목록 조회 (슈퍼 어드민용)"""
        try:
            query = self.db.query(Partner)

            # 상태 필터링
            if status:
                query = query.filter(Partner.status == status)

            # 검색 필터링
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Partner.name.ilike(search_term),
                        Partner.domain.ilike(search_term),
                        Partner.contact_email.ilike(search_term),
                    )
                )

            return query.offset(skip).limit(limit).all()

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch partners: {str(e)}"
            )

    async def get_partner_count(self) -> int:
        """총 파트너 수 조회"""
        try:
            return self.db.query(Partner).count()
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to count partners: {str(e)}"
            )

    async def get_partners_by_status(self, status: str) -> List[Partner]:
        """상태별 파트너 조회"""
        try:
            return self.db.query(Partner).filter(Partner.status == status).all()
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch partners by status: {str(e)}"
            )

    async def get_partner_statistics_detailed(self, partner_id: str) -> Dict[str, Any]:
        """파트너 상세 통계 조회 (슈퍼 어드민용)"""
        try:
            partner = await self.get_partner_by_id(partner_id)
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")

            # 기본 통계 계산
            basic_stats = await self.get_partner_statistics(partner_id)

            # 추가 상세 통계
            current_month = datetime.utcnow().replace(day=1)
            last_month = (current_month - timedelta(days=1)).replace(day=1)

            # 월별 성장률 계산 (실제 구현에서는 transaction 테이블 조회)
            monthly_growth = {
                "transaction_count_growth": 15.5,  # %
                "revenue_growth": 23.2,  # %
                "user_growth": 8.7,  # %
            }

            # 성능 지표
            performance_metrics = {
                "avg_response_time": 180,  # ms
                "success_rate": 99.2,  # %
                "error_rate": 0.8,  # %
                "uptime": 99.9,  # %
            }

            # 비즈니스 지표
            business_metrics = {
                "ltv": 1250.0,  # Customer Lifetime Value
                "churn_rate": 2.3,  # %
                "satisfaction_score": 4.6,  # /5.0
                "support_tickets": 3,
            }

            # 기본 통계를 dict로 변환
            basic_stats_dict = (
                basic_stats.dict()
                if hasattr(basic_stats, "dict")
                else vars(basic_stats)
            )

            return {
                "partner_id": partner_id,
                "basic_stats": basic_stats_dict,
                "monthly_growth": monthly_growth,
                "performance_metrics": performance_metrics,
                "business_metrics": business_metrics,
                "last_activity": partner.updated_at,
                "onboarding_completion": 95.0,  # %
            }

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to get detailed statistics: {str(e)}"
            )

    async def bulk_update_partners(
        self, partner_ids: List[str], update_data: Dict[str, Any]
    ) -> List[Partner]:
        """파트너 일괄 업데이트"""
        try:
            updated_partners = []

            for partner_id in partner_ids:
                partner = (
                    self.db.query(Partner).filter(Partner.id == partner_id).first()
                )
                if partner:
                    for key, value in update_data.items():
                        if hasattr(partner, key) and key not in ["id", "created_at"]:
                            setattr(partner, key, value)

                    updated_partners.append(partner)

            self.db.commit()

            for partner in updated_partners:
                self.db.refresh(partner)

            return updated_partners

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to bulk update partners: {str(e)}"
            )

    async def get_partner_performance_ranking(self) -> List[Dict[str, Any]]:
        """파트너 성과 순위 조회"""
        try:
            partners = self.db.query(Partner).filter(Partner.status == "active").all()

            # 성과 지표 계산 (실제 구현에서는 transaction, revenue 데이터 기반)
            performance_data = []

            for partner in partners:
                stats = await self.get_partner_statistics(str(partner.id))

                performance_score = (
                    stats.total_transactions * 0.3
                    + float(stats.total_volume) * 0.4
                    + 100 * 0.3  # active_users 임시값
                )

                performance_data.append(
                    {
                        "partner_id": str(partner.id),
                        "partner_name": partner.name,
                        "performance_score": performance_score,
                        "total_revenue": float(stats.total_volume),
                        "total_transactions": stats.total_transactions,
                        "active_users": 100,  # 임시값
                        "growth_rate": 15.5,  # 임시 값
                    }
                )

            # 성과 점수 기준 정렬
            performance_data.sort(key=lambda x: x["performance_score"], reverse=True)

            # 순위 추가
            for i, data in enumerate(performance_data):
                data["rank"] = i + 1

            return performance_data

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to get performance ranking: {str(e)}"
            )

    async def export_partner_data(
        self, partner_ids: Optional[List[str]] = None, format_type: str = "json"
    ) -> Dict[str, Any]:
        """파트너 데이터 내보내기"""
        try:
            query = self.db.query(Partner)

            if partner_ids:
                query = query.filter(Partner.id.in_(partner_ids))

            partners = query.all()

            export_data = []
            for partner in partners:
                partner_data = {
                    "id": str(partner.id),
                    "name": safe_get_attr(partner, "name", ""),
                    "domain": safe_get_attr(partner, "domain", ""),
                    "contact_email": safe_get_attr(partner, "contact_email", ""),
                    "status": safe_get_attr(partner, "status", "pending"),
                    "commission_rate": safe_float(
                        safe_get_attr(partner, "commission_rate"), 0.0
                    ),
                    "created_at": (
                        safe_get_attr(partner, "created_at").isoformat()
                        if safe_get_attr(partner, "created_at")
                        else None
                    ),
                    "updated_at": (
                        safe_get_attr(partner, "updated_at").isoformat()
                        if safe_get_attr(partner, "updated_at")
                        else None
                    ),
                }

                # 통계 데이터 추가
                stats = await self.get_partner_statistics(str(partner.id))
                partner_data["statistics"] = stats

                export_data.append(partner_data)

            return {
                "export_date": datetime.utcnow().isoformat(),
                "format": format_type,
                "total_records": len(export_data),
                "data": export_data,
            }

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to export partner data: {str(e)}"
            )

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
                energy_remaining=int(
                    safe_decimal(safe_get_attr(partner, "energy_balance", 0))
                ),
                success_rate=100.0,  # transaction 성공률 계산
                last_active=safe_get_attr(partner, "last_activity_at"),
                status=safe_get_attr(partner, "status", "pending"),
            )

            return stats

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to get partner statistics: {str(e)}"
            )

    async def update_partner_status(self, partner_id: str, status: str) -> Partner:
        """파트너 상태 변경"""
        partner = await self.get_partner_by_id(partner_id)

        valid_statuses = ["pending", "active", "suspended", "deleted"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {valid_statuses}",
            )

        try:
            # 기존 partner 객체를 새로 고침하여 최신 상태로 가져오기
            self.db.refresh(partner)
            partner_id = safe_get_attr(partner, "id")

            # SQLAlchemy update 사용하여 안전하게 업데이트
            self.db.execute(
                update(Partner)
                .where(Partner.id == partner_id)
                .values(
                    status=status,
                    updated_at=datetime.utcnow(),
                    activated_at=datetime.utcnow() if status == "active" else None,
                    suspended_at=datetime.utcnow() if status == "suspended" else None,
                )
            )

            self.db.commit()
            self.db.refresh(partner)

            return partner

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to update partner status: {str(e)}"
            )

    async def get_partner_activity_log(
        self, partner_id: str, limit: int = 50
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
                "created_at": datetime.utcnow(),
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
