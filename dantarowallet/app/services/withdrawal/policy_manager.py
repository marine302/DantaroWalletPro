"""
출금 정책 관리 모듈
파트너사 출금 정책의 생성, 조회, 업데이트를 담당합니다.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logger import get_logger
from app.models.partner import Partner
from app.models.withdrawal_policy import (
    PartnerWithdrawalPolicy,
    WithdrawalApprovalRule,
    WithdrawalWhitelist,
)

logger = get_logger(__name__)


class PolicyManager:
    """출금 정책 관리자"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_withdrawal_policy(
        self, partner_id: str, policy_data: Dict[str, Any], admin_id: int
    ) -> PartnerWithdrawalPolicy:
        """파트너사 출금 정책을 생성합니다."""
        try:
            # 파트너 존재 확인
            partner_result = await self.db.execute(
                select(Partner).where(Partner.id == partner_id)
            )
            partner = partner_result.scalar_one_or_none()
            if not partner:
                raise NotFoundError(f"파트너를 찾을 수 없습니다: {partner_id}")

            # 기존 정책 확인
            existing_result = await self.db.execute(
                select(PartnerWithdrawalPolicy).where(
                    PartnerWithdrawalPolicy.partner_id == partner_id
                )
            )
            existing_policy = existing_result.scalar_one_or_none()

            if existing_policy:
                raise ValidationError(f"이미 출금 정책이 존재합니다: {partner_id}")

            # 새 정책 생성
            policy = PartnerWithdrawalPolicy(partner_id=partner_id, **policy_data)

            self.db.add(policy)
            await self.db.commit()
            await self.db.refresh(policy)

            logger.info(f"파트너 출금 정책 생성: {partner_id} -> {policy.id}")
            return policy

        except Exception as e:
            await self.db.rollback()
            logger.error(f"파트너 출금 정책 생성 실패: {str(e)}")
            raise

    async def get_withdrawal_policy(
        self, partner_id: str
    ) -> Optional[PartnerWithdrawalPolicy]:
        """파트너사 출금 정책을 조회합니다."""
        result = await self.db.execute(
            select(PartnerWithdrawalPolicy)
            .options(
                selectinload(PartnerWithdrawalPolicy.approval_rules),
                selectinload(PartnerWithdrawalPolicy.whitelist_entries),
            )
            .where(PartnerWithdrawalPolicy.partner_id == partner_id)
        )
        return result.scalar_one_or_none()

    async def update_withdrawal_policy(
        self, partner_id: str, update_data: Dict[str, Any], admin_id: int
    ) -> PartnerWithdrawalPolicy:
        """파트너사 출금 정책을 업데이트합니다."""
        try:
            # 기존 정책 조회
            policy = await self.get_withdrawal_policy(partner_id)
            if not policy:
                raise NotFoundError(f"출금 정책을 찾을 수 없습니다: {partner_id}")

            # 업데이트 적용
            for field, value in update_data.items():
                if hasattr(policy, field):
                    setattr(policy, field, value)

            # 수동으로 updated_at 설정
            current_time = datetime.utcnow()
            query = (
                update(PartnerWithdrawalPolicy)
                .where(PartnerWithdrawalPolicy.id == policy.id)
                .values(updated_at=current_time)
            )
            await self.db.execute(query)
            await self.db.commit()
            await self.db.refresh(policy)

            logger.info(f"파트너 출금 정책 업데이트: {partner_id}")
            return policy

        except Exception as e:
            await self.db.rollback()
            logger.error(f"파트너 출금 정책 업데이트 실패: {str(e)}")
            raise

    # === 화이트리스트 관리 ===

    async def create_whitelist_entry(
        self, policy_id: int, whitelist_data: Dict[str, Any], admin_id: int
    ) -> WithdrawalWhitelist:
        """화이트리스트 항목을 생성합니다."""
        try:
            # 중복 주소 확인
            existing_result = await self.db.execute(
                select(WithdrawalWhitelist).where(
                    and_(
                        WithdrawalWhitelist.policy_id == policy_id,
                        WithdrawalWhitelist.address == whitelist_data["address"],
                    )
                )
            )
            existing_entry = existing_result.scalar_one_or_none()

            if existing_entry:
                raise ValidationError(
                    f"이미 등록된 주소입니다: {whitelist_data['address']}"
                )

            # 화이트리스트 항목 생성
            whitelist_entry = WithdrawalWhitelist(
                policy_id=policy_id,
                address=whitelist_data["address"],
                address_label=whitelist_data.get("label"),
                max_daily_amount=whitelist_data.get("max_daily_amount"),
                max_monthly_amount=whitelist_data.get("max_monthly_amount"),
                is_active=whitelist_data.get("is_active", True),
                verified_at=datetime.utcnow(),
                verified_by=admin_id,
            )

            self.db.add(whitelist_entry)
            await self.db.commit()
            await self.db.refresh(whitelist_entry)

            logger.info(
                f"화이트리스트 항목 생성: {whitelist_entry.id} -> {whitelist_entry.address}"
            )
            return whitelist_entry

        except Exception as e:
            await self.db.rollback()
            logger.error(f"화이트리스트 항목 생성 실패: {str(e)}")
            raise

    async def get_whitelist_entries(
        self, policy_id: int, active_only: bool = False
    ) -> List[WithdrawalWhitelist]:
        """화이트리스트 항목들을 조회합니다."""
        query = select(WithdrawalWhitelist).where(
            WithdrawalWhitelist.policy_id == policy_id
        )

        if active_only:
            query = query.where(WithdrawalWhitelist.is_active == True)

        result = await self.db.execute(
            query.order_by(WithdrawalWhitelist.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_whitelist_entry(
        self, whitelist_id: int, partner_id: str, admin_id: int
    ) -> bool:
        """화이트리스트 항목을 삭제합니다."""
        try:
            # 권한 확인을 위해 정책과 함께 조회
            result = await self.db.execute(
                select(WithdrawalWhitelist)
                .join(PartnerWithdrawalPolicy)
                .where(
                    and_(
                        WithdrawalWhitelist.id == whitelist_id,
                        PartnerWithdrawalPolicy.partner_id == partner_id,
                    )
                )
            )
            whitelist_entry = result.scalar_one_or_none()

            if not whitelist_entry:
                return False

            await self.db.delete(whitelist_entry)
            await self.db.commit()

            logger.info(f"화이트리스트 항목 삭제: {whitelist_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"화이트리스트 항목 삭제 실패: {str(e)}")
            raise
