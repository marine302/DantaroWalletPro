"""파트너사 출금 및 에너지 정책 관리 서비스 - Doc #26"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logger import get_logger
from app.models.fee_policy import (
    EnergyPolicy,
    PartnerEnergyPolicy,
    UserTier,
    WithdrawalPolicy,
)
from app.models.partner import Partner
from app.models.withdrawal_policy import PartnerWithdrawalPolicy
from app.schemas.fee_policy import (
    PartnerEnergyPolicyCreate,
    PartnerEnergyPolicyResponse,
    PartnerEnergyPolicyUpdate,
    PartnerWithdrawalPolicyCreate,
    PartnerWithdrawalPolicyResponse,
    PartnerWithdrawalPolicyUpdate,
    UserTierCreate,
    UserTierResponse,
    UserTierUpdate,
)

logger = get_logger(__name__)


def safe_get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """SQLAlchemy 객체의 속성을 안전하게 가져옵니다."""
    try:
        value = getattr(obj, attr, default)
        # SQLAlchemy Column이면 실제 값으로 변환
        if hasattr(value, "__class__") and "Column" in str(type(value)):
            return default
        return value
    except Exception:
        return default


class PartnerPolicyService:
    """파트너사 출금 및 에너지 정책 관리 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # === 출금 정책 관리 ===

    async def create_withdrawal_policy(
        self, partner_id: str, policy_data: PartnerWithdrawalPolicyCreate, admin_id: int
    ) -> PartnerWithdrawalPolicyResponse:
        """파트너사 출금 정책을 생성합니다."""
        try:
            # 파트너 존재 확인
            await self._validate_partner_exists(partner_id)

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
            policy = PartnerWithdrawalPolicy(
                partner_id=partner_id, **policy_data.dict()
            )

            self.db.add(policy)
            await self.db.commit()
            await self.db.refresh(policy)

            logger.info(f"파트너 출금 정책 생성: {partner_id} -> {policy.id}")
            return self._format_withdrawal_policy_response(policy)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"파트너 출금 정책 생성 실패: {str(e)}")
            raise

    async def get_withdrawal_policy(
        self, partner_id: str
    ) -> Optional[PartnerWithdrawalPolicyResponse]:
        """파트너사 출금 정책을 조회합니다."""
        result = await self.db.execute(
            select(PartnerWithdrawalPolicy).where(
                PartnerWithdrawalPolicy.partner_id == partner_id
            )
        )
        policy = result.scalar_one_or_none()

        if not policy:
            return None

        return self._format_withdrawal_policy_response(policy)

    async def update_withdrawal_policy(
        self, partner_id: str, update_data: PartnerWithdrawalPolicyUpdate, admin_id: int
    ) -> PartnerWithdrawalPolicyResponse:
        """파트너사 출금 정책을 업데이트합니다."""
        try:
            # 기존 정책 조회
            result = await self.db.execute(
                select(PartnerWithdrawalPolicy).where(
                    PartnerWithdrawalPolicy.partner_id == partner_id
                )
            )
            policy = result.scalar_one_or_none()

            if not policy:
                raise NotFoundError(f"출금 정책을 찾을 수 없습니다: {partner_id}")

            # 업데이트 적용
            update_dict = update_data.dict(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()

            for field, value in update_dict.items():
                setattr(policy, field, value)

            await self.db.commit()
            await self.db.refresh(policy)

            logger.info(f"파트너 출금 정책 업데이트: {partner_id}")
            return self._format_withdrawal_policy_response(policy)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"파트너 출금 정책 업데이트 실패: {str(e)}")
            raise

    # === 에너지 정책 관리 ===

    async def create_energy_policy(
        self, partner_id: str, policy_data: PartnerEnergyPolicyCreate, admin_id: int
    ) -> PartnerEnergyPolicyResponse:
        """파트너사 에너지 정책을 생성합니다."""
        try:
            # 파트너 존재 확인
            await self._validate_partner_exists(partner_id)

            # 기존 정책 확인
            existing_result = await self.db.execute(
                select(PartnerEnergyPolicy).where(
                    PartnerEnergyPolicy.partner_id == partner_id
                )
            )
            existing_policy = existing_result.scalar_one_or_none()

            if existing_policy:
                raise ValidationError(f"이미 에너지 정책이 존재합니다: {partner_id}")

            # 새 정책 생성
            policy = PartnerEnergyPolicy(partner_id=partner_id, **policy_data.dict())

            self.db.add(policy)
            await self.db.commit()
            await self.db.refresh(policy)

            logger.info(f"파트너 에너지 정책 생성: {partner_id} -> {policy.id}")
            return self._format_energy_policy_response(policy)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"파트너 에너지 정책 생성 실패: {str(e)}")
            raise

    async def get_energy_policy(
        self, partner_id: str
    ) -> Optional[PartnerEnergyPolicyResponse]:
        """파트너사 에너지 정책을 조회합니다."""
        result = await self.db.execute(
            select(PartnerEnergyPolicy).where(
                PartnerEnergyPolicy.partner_id == partner_id
            )
        )
        policy = result.scalar_one_or_none()

        if not policy:
            return None

        return self._format_energy_policy_response(policy)

    async def update_energy_policy(
        self, partner_id: str, update_data: PartnerEnergyPolicyUpdate, admin_id: int
    ) -> PartnerEnergyPolicyResponse:
        """파트너사 에너지 정책을 업데이트합니다."""
        try:
            # 기존 정책 조회
            result = await self.db.execute(
                select(PartnerEnergyPolicy).where(
                    PartnerEnergyPolicy.partner_id == partner_id
                )
            )
            policy = result.scalar_one_or_none()

            if not policy:
                raise NotFoundError(f"에너지 정책을 찾을 수 없습니다: {partner_id}")

            # 업데이트 적용
            update_dict = update_data.dict(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()

            for field, value in update_dict.items():
                setattr(policy, field, value)

            await self.db.commit()
            await self.db.refresh(policy)

            logger.info(f"파트너 에너지 정책 업데이트: {partner_id}")
            return self._format_energy_policy_response(policy)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"파트너 에너지 정책 업데이트 실패: {str(e)}")
            raise

    # === 사용자 등급 관리 ===

    async def create_user_tier(
        self, partner_id: str, user_id: int, tier_data: UserTierCreate, admin_id: int
    ) -> UserTierResponse:
        """사용자 등급을 생성합니다."""
        try:
            # 파트너 존재 확인
            await self._validate_partner_exists(partner_id)

            # 기존 활성 등급 확인
            existing_result = await self.db.execute(
                select(UserTier).where(
                    and_(
                        UserTier.partner_id == partner_id,
                        UserTier.user_id == user_id,
                        UserTier.is_active == True,
                    )
                )
            )
            existing_tier = existing_result.scalar_one_or_none()

            # 기존 등급이 있으면 비활성화
            if existing_tier:
                existing_tier.is_active = False
                setattr(existing_tier, "updated_at", datetime.utcnow())

            # 새 등급 생성
            tier = UserTier(partner_id=partner_id, user_id=user_id, **tier_data.dict())

            self.db.add(tier)
            await self.db.commit()
            await self.db.refresh(tier)

            logger.info(f"사용자 등급 생성: {partner_id}/{user_id} -> {tier.tier_name}")
            return self._format_user_tier_response(tier)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"사용자 등급 생성 실패: {str(e)}")
            raise

    async def get_user_tier(
        self, partner_id: str, user_id: int
    ) -> Optional[UserTierResponse]:
        """활성 사용자 등급을 조회합니다."""
        result = await self.db.execute(
            select(UserTier).where(
                and_(
                    UserTier.partner_id == partner_id,
                    UserTier.user_id == user_id,
                    UserTier.is_active == True,
                )
            )
        )
        tier = result.scalar_one_or_none()

        if not tier:
            return None

        return self._format_user_tier_response(tier)

    async def get_partner_user_tiers(
        self,
        partner_id: str,
        is_active: Optional[bool] = True,
        limit: int = 100,
        offset: int = 0,
    ) -> List[UserTierResponse]:
        """파트너의 모든 사용자 등급을 조회합니다."""
        query = select(UserTier).where(UserTier.partner_id == partner_id)

        if is_active is not None:
            query = query.where(UserTier.is_active == is_active)

        query = query.order_by(desc(UserTier.created_at))
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        tiers = result.scalars().all()

        return [self._format_user_tier_response(tier) for tier in tiers]

    async def update_user_tier(
        self, partner_id: str, user_id: int, update_data: UserTierUpdate, admin_id: int
    ) -> UserTierResponse:
        """사용자 등급을 업데이트합니다."""
        try:
            # 활성 등급 조회
            result = await self.db.execute(
                select(UserTier).where(
                    and_(
                        UserTier.partner_id == partner_id,
                        UserTier.user_id == user_id,
                        UserTier.is_active == True,
                    )
                )
            )
            tier = result.scalar_one_or_none()

            if not tier:
                raise NotFoundError(
                    f"활성 사용자 등급을 찾을 수 없습니다: {partner_id}/{user_id}"
                )

            # 업데이트 적용
            update_dict = update_data.dict(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()

            for field, value in update_dict.items():
                setattr(tier, field, value)

            await self.db.commit()
            await self.db.refresh(tier)

            logger.info(f"사용자 등급 업데이트: {partner_id}/{user_id}")
            return self._format_user_tier_response(tier)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"사용자 등급 업데이트 실패: {str(e)}")
            raise

    async def deactivate_user_tier(
        self, partner_id: str, user_id: int, admin_id: int
    ) -> bool:
        """사용자 등급을 비활성화합니다."""
        try:
            # 활성 등급 조회
            result = await self.db.execute(
                select(UserTier).where(
                    and_(
                        UserTier.partner_id == partner_id,
                        UserTier.user_id == user_id,
                        UserTier.is_active == True,
                    )
                )
            )
            tier = result.scalar_one_or_none()

            if not tier:
                raise NotFoundError(
                    f"활성 사용자 등급을 찾을 수 없습니다: {partner_id}/{user_id}"
                )

            # 비활성화
            tier.is_active = False
            setattr(tier, "updated_at", datetime.utcnow())

            await self.db.commit()

            logger.info(f"사용자 등급 비활성화: {partner_id}/{user_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"사용자 등급 비활성화 실패: {str(e)}")
            raise

    # === 정책 검증 및 적용 ===

    async def validate_withdrawal_request(
        self,
        partner_id: str,
        amount: float,
        user_id: int,
        request_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """출금 요청을 정책에 따라 검증합니다."""
        if request_time is None:
            request_time = datetime.utcnow()

        # 출금 정책 조회
        policy = await self.get_withdrawal_policy(partner_id)
        if not policy:
            return {
                "allowed": True,
                "processing_type": "realtime",
                "message": "기본 출금 정책 적용",
            }

        # 최소/최대 금액 확인
        if policy.min_amount and amount < policy.min_amount:
            return {
                "allowed": False,
                "reason": "minimum_amount",
                "message": f"최소 출금 금액: {policy.min_amount}",
                "min_amount": policy.min_amount,
            }

        if policy.max_amount and amount > policy.max_amount:
            return {
                "allowed": False,
                "reason": "maximum_amount",
                "message": f"최대 출금 금액: {policy.max_amount}",
                "max_amount": policy.max_amount,
            }

        # 시간 제한 확인
        if policy.allowed_hours:
            current_hour = request_time.hour
            allowed_hours = policy.allowed_hours
            if current_hour not in allowed_hours:
                return {
                    "allowed": False,
                    "reason": "time_restriction",
                    "message": f"허용된 출금 시간: {allowed_hours}",
                    "allowed_hours": allowed_hours,
                }

        # 일일 한도 확인
        if policy.daily_limit:
            daily_total = await self._get_daily_withdrawal_total(
                partner_id, user_id, request_time
            )
            if daily_total + amount > policy.daily_limit:
                return {
                    "allowed": False,
                    "reason": "daily_limit",
                    "message": f"일일 출금 한도 초과: {policy.daily_limit}",
                    "daily_limit": policy.daily_limit,
                    "current_total": daily_total,
                }

        # 처리 방식 결정
        processing_type = self._determine_processing_type(policy, amount)

        return {
            "allowed": True,
            "processing_type": processing_type,
            "policy": policy.processing_policy.value,
            "estimated_delay": (
                policy.batch_delay_minutes if processing_type == "batch" else 0
            ),
        }

    async def validate_energy_usage(
        self, partner_id: str, required_energy: int, current_available: int
    ) -> Dict[str, Any]:
        """에너지 사용 요청을 정책에 따라 검증합니다."""
        # 에너지 정책 조회
        policy = await self.get_energy_policy(partner_id)
        if not policy:
            return {
                "allowed": current_available >= required_energy,
                "action": (
                    "reject" if current_available < required_energy else "proceed"
                ),
                "message": "기본 에너지 정책 적용",
            }

        # 충분한 에너지가 있는 경우
        if current_available >= required_energy:
            return {
                "allowed": True,
                "action": "proceed",
                "energy_used": required_energy,
            }

        # 에너지 부족 시 정책에 따른 처리
        shortage = required_energy - current_available

        if policy.default_policy == EnergyPolicy.WAIT_QUEUE:
            return {
                "allowed": False,
                "action": "wait_queue",
                "message": "에너지 부족으로 대기열 등록",
                "shortage_amount": shortage,
                "estimated_wait": policy.queue_max_wait_hours
                * 60,  # 시간을 분으로 변환
            }

        elif policy.default_policy == EnergyPolicy.TRX_PAYMENT:
            # TRX 결제 비용 계산 (간단한 예시)
            trx_cost = shortage * 0.01  # 예시 비율
            return {
                "allowed": True,
                "action": "trx_payment",
                "message": "TRX 직접 결제로 처리",
                "shortage_amount": shortage,
                "trx_cost": trx_cost,
            }

        elif policy.default_policy == EnergyPolicy.PRIORITY_QUEUE:
            return {
                "allowed": False,
                "action": "priority_queue",
                "message": "우선순위 큐에 등록",
                "shortage_amount": shortage,
                "priority_timeout": policy.queue_max_wait_hours
                * 60,  # 시간을 분으로 변환
            }

        else:  # REJECT
            return {
                "allowed": False,
                "action": "reject",
                "message": "에너지 부족으로 거부",
                "shortage_amount": shortage,
            }

    # === 유틸리티 메서드 ===

    async def _validate_partner_exists(self, partner_id: str):
        """파트너 존재 확인"""
        result = await self.db.execute(select(Partner).where(Partner.id == partner_id))
        partner = result.scalar_one_or_none()
        if not partner:
            raise NotFoundError(f"파트너를 찾을 수 없습니다: {partner_id}")

    async def _get_daily_withdrawal_total(
        self, partner_id: str, user_id: int, request_time: datetime
    ) -> float:
        """일일 출금 총액 조회 (실제로는 transaction 테이블에서 조회)"""
        # TODO: 실제 transaction 테이블과 연동
        return 0.0

    def _determine_processing_type(
        self, policy: PartnerWithdrawalPolicyResponse, amount: float
    ) -> str:
        """출금 처리 방식 결정"""
        if policy.processing_policy == WithdrawalPolicy.REALTIME:
            return "realtime"
        elif policy.processing_policy == WithdrawalPolicy.BATCH:
            return "batch"
        elif policy.processing_policy == WithdrawalPolicy.HYBRID:
            # 금액에 따라 결정 (예: 대량은 배치, 소량은 실시간)
            threshold = float(policy.max_amount) * 0.8 if policy.max_amount else 1000
            return "batch" if amount > threshold else "realtime"
        else:  # MANUAL
            return "manual"

    def _format_withdrawal_policy_response(
        self, policy: PartnerWithdrawalPolicy
    ) -> PartnerWithdrawalPolicyResponse:
        """출금 정책 응답 포맷팅"""
        return PartnerWithdrawalPolicyResponse(
            id=safe_get_attr(policy, "id", 0),
            partner_id=safe_get_attr(policy, "partner_id", ""),
            processing_policy=safe_get_attr(
                policy, "processing_policy", WithdrawalPolicy.HYBRID
            ),
            min_amount=safe_get_attr(policy, "min_amount"),
            max_amount=safe_get_attr(policy, "max_amount"),
            daily_limit=safe_get_attr(policy, "daily_limit"),
            allowed_hours=safe_get_attr(policy, "allowed_hours"),
            batch_delay_minutes=safe_get_attr(policy, "batch_delay_minutes"),
            auto_approval_threshold=safe_get_attr(policy, "auto_approval_threshold"),
            require_admin_approval=safe_get_attr(
                policy, "require_admin_approval", True
            ),
            is_active=safe_get_attr(policy, "is_active", True),
            created_at=safe_get_attr(policy, "created_at", datetime.utcnow()),
            updated_at=safe_get_attr(policy, "updated_at"),
        )

    def _format_energy_policy_response(
        self, policy: PartnerEnergyPolicy
    ) -> PartnerEnergyPolicyResponse:
        """에너지 정책 응답 포맷팅"""
        return PartnerEnergyPolicyResponse(
            id=safe_get_attr(policy, "id", 0),
            partner_id=safe_get_attr(policy, "partner_id", ""),
            default_policy=safe_get_attr(
                policy, "default_policy", EnergyPolicy.WAIT_QUEUE
            ),
            trx_payment_enabled=safe_get_attr(policy, "trx_payment_enabled", True),
            trx_payment_markup=safe_get_attr(
                policy, "trx_payment_markup", Decimal("0.1")
            ),
            trx_payment_max_fee=safe_get_attr(
                policy, "trx_payment_max_fee", Decimal("20")
            ),
            queue_enabled=safe_get_attr(policy, "queue_enabled", True),
            queue_max_wait_hours=safe_get_attr(policy, "queue_max_wait_hours", 24),
            queue_notification_enabled=safe_get_attr(
                policy, "queue_notification_enabled", True
            ),
            priority_queue_enabled=safe_get_attr(
                policy, "priority_queue_enabled", True
            ),
            vip_priority_levels=safe_get_attr(policy, "vip_priority_levels"),
            energy_saving_enabled=safe_get_attr(policy, "energy_saving_enabled", False),
            energy_saving_threshold=safe_get_attr(
                policy, "energy_saving_threshold", 20
            ),
            created_at=safe_get_attr(policy, "created_at", datetime.utcnow()),
            updated_at=safe_get_attr(policy, "updated_at"),
        )

    def _format_user_tier_response(self, tier: UserTier) -> UserTierResponse:
        """사용자 등급 응답 포맷팅"""
        return UserTierResponse(
            id=safe_get_attr(tier, "id", 0),
            partner_id=safe_get_attr(tier, "partner_id", ""),
            tier_name=safe_get_attr(tier, "tier_name", ""),
            tier_level=safe_get_attr(tier, "tier_level", 1),
            min_volume=safe_get_attr(tier, "min_volume", Decimal("0")),
            fee_discount_rate=safe_get_attr(tier, "fee_discount_rate", Decimal("0")),
            withdrawal_limit_multiplier=safe_get_attr(
                tier, "withdrawal_limit_multiplier", Decimal("1.0")
            ),
            benefits=safe_get_attr(tier, "benefits"),
            upgrade_conditions=safe_get_attr(tier, "upgrade_conditions"),
            created_at=safe_get_attr(tier, "created_at", datetime.utcnow()),
            updated_at=safe_get_attr(tier, "updated_at"),
        )
