"""파트너사 수수료 및 정책 관리 서비스 - Doc #26"""
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload

from app.models.fee_policy import (
    PartnerFeePolicy, FeeTier,
    PartnerEnergyPolicy, UserTier, PartnerPolicyCalculationLog,
    FeeType, WithdrawalPolicy, EnergyPolicy
)
from app.models.withdrawal_policy import PartnerWithdrawalPolicy
from app.models.partner import Partner
from app.models.user import User
from app.schemas.fee_policy import (
    PartnerFeePolicyCreate, PartnerFeePolicyUpdate, PartnerFeePolicyResponse,
    FeeTierCreate, FeeTierResponse,
    FeeCalculationRequest, FeeCalculationResponse,
    PartnerPolicyCalculationLogResponse
)
from app.core.exceptions import ValidationError, NotFoundError
from app.core.logger import get_logger

logger = get_logger(__name__)


def safe_get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """SQLAlchemy 모델 속성을 안전하게 가져오는 헬퍼 함수"""
    if obj is None:
        return default
    
    value = getattr(obj, attr, default)
    
    # SQLAlchemy Column 타입인 경우 실제 값 추출
    if hasattr(value, 'value'):
        return value.value
    elif hasattr(value, '__getitem__') and hasattr(value, 'keys'):
        # dict-like object
        return value
    else:
        return value


def safe_decimal(value: Any, default: Decimal = Decimal('0')) -> Decimal:
    """안전한 Decimal 변환"""
    if value is None:
        return default
    
    if hasattr(value, 'value'):
        value = value.value
    
    try:
        return Decimal(str(value))
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """안전한 int 변환"""
    if value is None:
        return default
    
    if hasattr(value, 'value'):
        value = value.value
    
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_str(value: Any, default: str = '') -> str:
    """안전한 str 변환"""
    if value is None:
        return default
    
    if hasattr(value, 'value'):
        value = value.value
    
    try:
        return str(value)
    except (TypeError, ValueError):
        return default


def safe_datetime(value: Any, default: Optional[datetime] = None) -> datetime:
    """안전한 datetime 변환"""
    if value is None:
        return default or datetime.utcnow()
    
    if hasattr(value, 'value'):
        value = value.value
    
    if isinstance(value, datetime):
        return value
    
    return default or datetime.utcnow()


def safe_bool(value: Any, default: bool = False) -> bool:
    """안전한 bool 변환"""
    if value is None:
        return default
    
    if hasattr(value, 'value'):
        value = value.value
    
    try:
        return bool(value)
    except (TypeError, ValueError):
        return default


class PartnerFeePolicyService:
    """파트너사 수수료 및 정책 관리 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # === 파트너 수수료 정책 관리 ===
    
    async def create_partner_fee_policy(
        self, 
        partner_id: str,
        policy_data: PartnerFeePolicyCreate,
        admin_id: int
    ) -> PartnerFeePolicyResponse:
        """파트너사 수수료 정책을 생성합니다."""
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
                select(PartnerFeePolicy).where(
                    PartnerFeePolicy.partner_id == partner_id
                )
            )
            existing_policy = existing_result.scalar_one_or_none()
            
            if existing_policy:
                raise ValidationError(f"이미 수수료 정책이 존재합니다: {partner_id}")
            
            # 새 정책 생성
            policy = PartnerFeePolicy(
                partner_id=partner_id,
                **policy_data.dict()
            )
            
            self.db.add(policy)
            await self.db.commit()
            await self.db.refresh(policy)
            
            # 계산 로그 기록
            await self._create_calculation_log(
                partner_id=partner_id,
                calculation_type="policy_create",
                request_data=policy_data.dict(),
                result_data={"policy_id": policy.id},
                admin_id=admin_id
            )
            
            logger.info(f"파트너 수수료 정책 생성: {partner_id} -> {policy.id}")
            return await self._format_policy_response(policy)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"파트너 수수료 정책 생성 실패: {str(e)}")
            raise
    
    async def get_partner_fee_policy(
        self, 
        partner_id: str
    ) -> Optional[PartnerFeePolicyResponse]:
        """파트너사 수수료 정책을 조회합니다."""
        result = await self.db.execute(
            select(PartnerFeePolicy)
            .options(
                selectinload(PartnerFeePolicy.fee_tiers),
                selectinload(PartnerFeePolicy.user_tiers)
            )
            .where(PartnerFeePolicy.partner_id == partner_id)
        )
        policy = result.scalar_one_or_none()
        
        if not policy:
            return None
        
        return await self._format_policy_response(policy)
    
    async def update_partner_fee_policy(
        self,
        partner_id: str,
        update_data: PartnerFeePolicyUpdate,
        admin_id: int
    ) -> PartnerFeePolicyResponse:
        """파트너사 수수료 정책을 업데이트합니다."""
        try:
            # 기존 정책 조회
            result = await self.db.execute(
                select(PartnerFeePolicy).where(
                    PartnerFeePolicy.partner_id == partner_id
                )
            )
            policy = result.scalar_one_or_none()
            
            if not policy:
                raise NotFoundError(f"수수료 정책을 찾을 수 없습니다: {partner_id}")
            
            # 기존 값 저장 (로깅용)
            old_values = {
                "fee_type": safe_str(policy.fee_type),
                "base_fee_rate": safe_str(policy.base_fee_rate),
                "min_fee_amount": safe_str(policy.min_fee_amount),
                "max_fee_amount": safe_str(policy.max_fee_amount) if safe_get_attr(policy, 'max_fee_amount') else None
            }
            
            # 업데이트 적용
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(policy, field, value)
            
            # 수동으로 updated_at 설정
            current_time = datetime.utcnow()
            query = (
                update(PartnerFeePolicy)
                .where(PartnerFeePolicy.id == policy.id)
                .values(updated_at=current_time)
            )
            await self.db.execute(query)
            await self.db.commit()
            await self.db.refresh(policy)
            
            # 계산 로그 기록
            await self._create_calculation_log(
                partner_id=partner_id,
                calculation_type="policy_update",
                request_data=update_dict,
                result_data={"old_values": old_values, "new_values": update_dict},
                admin_id=admin_id
            )
            
            logger.info(f"파트너 수수료 정책 업데이트: {partner_id}")
            return await self._format_policy_response(policy)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"파트너 수수료 정책 업데이트 실패: {str(e)}")
            raise
    
    # === 구간별 수수료 관리 ===
    
    async def create_fee_tier(
        self,
        partner_id: str,
        tier_data: FeeTierCreate,
        admin_id: int
    ) -> FeeTierResponse:
        """구간별 수수료를 생성합니다."""
        try:
            # 파트너 정책 확인
            policy = await self._get_partner_policy(partner_id)
            
            # 구간 겹침 검사
            await self._validate_tier_overlap(partner_id, tier_data.min_amount, tier_data.max_amount)
            
            # 구간 생성
            tier = FeeTier(
                partner_fee_policy_id=policy.id,
                **tier_data.dict()
            )
            
            self.db.add(tier)
            await self.db.commit()
            await self.db.refresh(tier)
            
            logger.info(f"구간별 수수료 생성: {partner_id} -> {tier.id}")
            return FeeTierResponse(
                id=safe_int(tier.id),
                fee_policy_id=safe_int(policy.id),
                min_amount=safe_decimal(tier.min_amount),
                max_amount=safe_decimal(tier.max_amount) if safe_get_attr(tier, 'max_amount') else None,
                fee_rate=safe_decimal(tier.fee_rate),
                fixed_fee=safe_decimal(tier.fixed_fee),
                created_at=safe_datetime(tier.created_at)
            )
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"구간별 수수료 생성 실패: {str(e)}")
            raise
    
    async def get_fee_tiers(self, partner_id: str) -> List[FeeTierResponse]:
        """파트너의 모든 구간별 수수료를 조회합니다."""
        policy = await self._get_partner_policy(partner_id)
        
        result = await self.db.execute(
            select(FeeTier)
            .where(FeeTier.partner_fee_policy_id == policy.id)
            .order_by(FeeTier.min_amount)
        )
        tiers = result.scalars().all()
        
        return [
            FeeTierResponse(
                id=safe_int(tier.id),
                fee_policy_id=safe_int(policy.id),
                min_amount=safe_decimal(tier.min_amount),
                max_amount=safe_decimal(tier.max_amount) if safe_get_attr(tier, 'max_amount') else None,
                fee_rate=safe_decimal(tier.fee_rate),
                fixed_fee=safe_decimal(tier.fixed_fee),
                created_at=safe_datetime(tier.created_at)
            )
            for tier in tiers
        ]
    
    # === 수수료 계산 엔진 ===
    
    async def calculate_fee(
        self,
        partner_id: str,
        calculation_request: FeeCalculationRequest,
        user_id: Optional[int] = None
    ) -> FeeCalculationResponse:
        """수수료를 계산합니다."""
        try:
            # 파트너 정책 조회
            policy = await self._get_partner_policy(partner_id)
            
            # 사용자 등급 조회 (할인 적용용)
            user_tier = None
            if user_id:
                user_tier = await self._get_user_tier(partner_id, user_id)
            
            # 수수료 계산
            fee_result = await self._calculate_fee_by_type(
                policy, calculation_request, user_tier
            )
            
            # 계산 로그 기록
            await self._create_calculation_log(
                partner_id=partner_id,
                calculation_type="fee_calculation",
                request_data=calculation_request.dict(),
                result_data=fee_result,
                user_id=user_id
            )
            
            return FeeCalculationResponse(**fee_result)
            
        except Exception as e:
            logger.error(f"수수료 계산 실패: {str(e)}")
            raise
    
    async def _calculate_fee_by_type(
        self,
        policy: PartnerFeePolicy,
        request: FeeCalculationRequest,
        user_tier: Optional[UserTier] = None
    ) -> Dict[str, Any]:
        """수수료 유형에 따른 계산 로직"""
        
        base_amount = request.amount
        transaction_type = request.transaction_type
        
        # 거래 유형별 기본 수수료율 선택
        if transaction_type == "withdrawal":
            base_rate = safe_decimal(policy.withdrawal_fee_rate)
        elif transaction_type == "internal_transfer":
            base_rate = safe_decimal(policy.internal_transfer_fee_rate)
        else:
            base_rate = safe_decimal(policy.base_fee_rate)
        
        # 수수료 유형별 계산
        fee_type = safe_get_attr(policy, 'fee_type')
        if fee_type == FeeType.FLAT:
            calculated_fee = await self._calculate_flat_fee(policy, base_amount, base_rate)
        elif fee_type == FeeType.PERCENTAGE:
            calculated_fee = await self._calculate_percentage_fee(policy, base_amount, base_rate)
        elif fee_type == FeeType.TIERED:
            calculated_fee = await self._calculate_tiered_fee(policy, base_amount)
        elif fee_type == FeeType.DYNAMIC:
            calculated_fee = await self._calculate_dynamic_fee(policy, request)
        else:
            raise ValidationError(f"지원하지 않는 수수료 유형: {fee_type}")
        
        # 사용자 등급 할인 적용
        if user_tier and safe_decimal(user_tier.discount_rate) > 0:
            discount_amount = calculated_fee * safe_decimal(user_tier.discount_rate)
            calculated_fee = max(calculated_fee - discount_amount, Decimal('0'))
        else:
            discount_amount = Decimal('0')
        
        # 최소/최대 수수료 적용
        min_fee = safe_decimal(policy.min_fee_amount)
        max_fee = safe_decimal(policy.max_fee_amount)
        
        if min_fee and calculated_fee < min_fee:
            calculated_fee = min_fee
        
        if max_fee and calculated_fee > max_fee:
            calculated_fee = policy.max_fee_amount
        
        return {
            "original_amount": base_amount,
            "calculated_fee": calculated_fee,
            "discount_amount": discount_amount,
            "final_fee": calculated_fee,
            "effective_rate": calculated_fee / base_amount if base_amount > 0 else Decimal('0'),
            "calculation_method": policy.fee_type.value,
            "user_tier_applied": user_tier.tier_name if user_tier else None,
            "metadata": {
                "min_fee_applied": policy.min_fee_amount and calculated_fee == policy.min_fee_amount,
                "max_fee_applied": policy.max_fee_amount and calculated_fee == policy.max_fee_amount,
                "base_rate_used": str(base_rate)
            }
        }
    
    async def _calculate_flat_fee(
        self, policy: PartnerFeePolicy, amount: Decimal, base_rate: Decimal
    ) -> Decimal:
        """고정 수수료 계산"""
        return base_rate  # 고정 수수료는 금액에 관계없이 동일
    
    async def _calculate_percentage_fee(
        self, policy: PartnerFeePolicy, amount: Decimal, base_rate: Decimal
    ) -> Decimal:
        """비율 수수료 계산"""
        return amount * base_rate
    
    async def _calculate_tiered_fee(
        self, policy: PartnerFeePolicy, amount: Decimal
    ) -> Decimal:
        """구간별 수수료 계산"""
        # 해당 금액에 맞는 구간 찾기
        result = await self.db.execute(
            select(FeeTier)
            .where(
                and_(
                    FeeTier.partner_fee_policy_id == policy.id,
                    FeeTier.min_amount <= amount,
                    or_(
                        FeeTier.max_amount.is_(None),
                        FeeTier.max_amount >= amount
                    )
                )
            )
            .order_by(FeeTier.min_amount)
            .limit(1)
        )
        tier = result.scalar_one_or_none()
        
        if not tier:
            # 해당 구간이 없으면 기본 비율 사용
            base_rate = safe_decimal(policy.base_fee_rate)
            return amount * base_rate
        
        fixed_fee = safe_decimal(tier.fixed_fee)
        rate_fee = safe_decimal(tier.fee_rate)
        return fixed_fee + (amount * rate_fee)
    
    async def _calculate_dynamic_fee(
        self, policy: PartnerFeePolicy, request: FeeCalculationRequest
    ) -> Decimal:
        """동적 수수료 계산 (시간대, 네트워크 상황 등 고려)"""
        base_rate = safe_decimal(policy.base_fee_rate)
        base_fee = request.amount * base_rate
        
        # 시간대별 조정 (예: 피크 시간 할증)
        current_hour = datetime.utcnow().hour
        if 9 <= current_hour <= 18:  # 업무시간
            base_fee *= Decimal('1.2')  # 20% 할증
        
        # 네트워크 상황 조정 (예: TRX 네트워크 혼잡도)
        # 실제로는 외부 API에서 가져온 데이터를 활용
        network_multiplier = Decimal('1.0')  # 기본값
        
        return base_fee * network_multiplier
    
    # === 유틸리티 메서드 ===
    
    async def _get_partner_policy(self, partner_id: str) -> PartnerFeePolicy:
        """파트너 정책을 조회하고 없으면 예외 발생"""
        result = await self.db.execute(
            select(PartnerFeePolicy).where(
                PartnerFeePolicy.partner_id == partner_id
            )
        )
        policy = result.scalar_one_or_none()
        
        if not policy:
            raise NotFoundError(f"파트너 수수료 정책을 찾을 수 없습니다: {partner_id}")
        
        return policy
    
    async def _get_user_tier(self, partner_id: str, user_id: int) -> Optional[UserTier]:
        """사용자 등급 조회"""
        result = await self.db.execute(
            select(UserTier).where(
                and_(
                    UserTier.partner_id == partner_id,
                    UserTier.user_id == user_id,
                    UserTier.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def _validate_tier_overlap(
        self, partner_id: str, min_amount: Decimal, max_amount: Optional[Decimal]
    ):
        """구간 겹침 검사"""
        policy = await self._get_partner_policy(partner_id)
        
        # 기존 구간들과 겹치는지 확인
        query = select(FeeTier).where(
            FeeTier.partner_fee_policy_id == policy.id
        )
        
        if max_amount is not None:
            # 새 구간이 유한한 경우
            query = query.where(
                or_(
                    and_(
                        FeeTier.min_amount <= min_amount,
                        or_(
                            FeeTier.max_amount.is_(None),
                            FeeTier.max_amount > min_amount
                        )
                    ),
                    and_(
                        FeeTier.min_amount < max_amount,
                        or_(
                            FeeTier.max_amount.is_(None),
                            FeeTier.max_amount >= max_amount
                        )
                    )
                )
            )
        else:
            # 새 구간이 무한한 경우
            query = query.where(
                or_(
                    FeeTier.min_amount >= min_amount,
                    FeeTier.max_amount.is_(None),
                    FeeTier.max_amount > min_amount
                )
            )
        
        result = await self.db.execute(query)
        overlapping_tier = result.scalar_one_or_none()
        
        if overlapping_tier:
            raise ValidationError("기존 수수료 구간과 겹칩니다")
    
    async def _format_policy_response(self, policy: PartnerFeePolicy) -> PartnerFeePolicyResponse:
        """정책 응답 포맷팅"""
        return PartnerFeePolicyResponse(
            id=safe_int(policy.id),
            partner_id=safe_str(policy.partner_id),
            fee_type=safe_get_attr(policy, 'fee_type'),
            base_fee_rate=safe_decimal(policy.base_fee_rate),
            min_fee_amount=safe_decimal(policy.min_fee_amount),
            max_fee_amount=safe_decimal(policy.max_fee_amount) if safe_get_attr(policy, 'max_fee_amount') else None,
            withdrawal_fee_rate=safe_decimal(policy.withdrawal_fee_rate),
            internal_transfer_fee_rate=safe_decimal(policy.internal_transfer_fee_rate),
            vip_discount_rates=safe_get_attr(policy, 'vip_discount_rates', {}),
            promotion_active=safe_bool(policy.promotion_active),
            promotion_fee_rate=safe_decimal(policy.promotion_fee_rate) if safe_get_attr(policy, 'promotion_fee_rate') else None,
            promotion_end_date=safe_get_attr(policy, 'promotion_end_date'),
            platform_share_rate=safe_decimal(policy.platform_share_rate),
            created_at=safe_get_attr(policy, 'created_at'),
            updated_at=safe_get_attr(policy, 'updated_at')
        )
    
    async def _create_calculation_log(
        self,
        partner_id: str,
        calculation_type: str,
        request_data: Dict[str, Any],
        result_data: Dict[str, Any],
        user_id: Optional[int] = None,
        admin_id: Optional[int] = None
    ):
        """수수료 계산 로그 생성"""
        try:
            log = PartnerPolicyCalculationLog(
                partner_id=partner_id,
                user_id=user_id,
                calculation_type=calculation_type,
                request_data=request_data,
                result_data=result_data,
                admin_id=admin_id,
                calculated_at=datetime.utcnow()
            )
            
            self.db.add(log)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"수수료 계산 로그 생성 실패: {str(e)}")
            # 로그 실패는 메인 프로세스에 영향 주지 않음
            pass
    
    # === 정책 조회 및 관리 ===
    
    async def get_calculation_logs(
        self,
        partner_id: str,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[int] = None,
        calculation_type: Optional[str] = None
    ) -> List[PartnerPolicyCalculationLogResponse]:
        """수수료 계산 로그 조회"""
        query = select(PartnerPolicyCalculationLog).where(
            PartnerPolicyCalculationLog.partner_id == partner_id
        )
        
        if user_id:
            query = query.where(PartnerPolicyCalculationLog.user_id == user_id)
        
        if calculation_type:
            query = query.where(PartnerPolicyCalculationLog.calculation_type == calculation_type)
        
        query = query.order_by(desc(PartnerPolicyCalculationLog.calculated_at))
        query = query.offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        return [
            PartnerPolicyCalculationLogResponse(
                id=safe_int(log.id),
                partner_id=safe_str(log.partner_id),
                user_id=safe_int(log.user_id) if safe_get_attr(log, 'user_id') else None,
                calculation_type=safe_str(log.calculation_type),
                request_data=safe_get_attr(log, 'request_data', {}),
                result_data=safe_get_attr(log, 'result_data', {}),
                calculated_at=safe_get_attr(log, 'calculated_at'),
                admin_id=safe_int(log.admin_id) if safe_get_attr(log, 'admin_id') else None
            )
            for log in logs
        ]
    
    async def delete_partner_fee_policy(self, partner_id: str, admin_id: int) -> bool:
        """파트너사 수수료 정책 삭제"""
        try:
            policy = await self._get_partner_policy(partner_id)
            
            # 관련된 구간들도 함께 삭제
            await self.db.execute(
                select(FeeTier).where(
                    FeeTier.partner_fee_policy_id == policy.id
                )
            )
            
            # 정책 삭제
            await self.db.delete(policy)
            await self.db.commit()
            
            # 삭제 로그 기록
            await self._create_calculation_log(
                partner_id=partner_id,
                calculation_type="policy_delete",
                request_data={"deleted_by": admin_id},
                result_data={"policy_id": policy.id},
                admin_id=admin_id
            )
            
            logger.info(f"파트너 수수료 정책 삭제: {partner_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"파트너 수수료 정책 삭제 실패: {str(e)}")
            raise
