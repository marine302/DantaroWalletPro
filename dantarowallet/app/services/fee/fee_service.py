"""수수료 관리 서비스"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logger import get_logger
from app.models.fee_config import (
    DynamicFeeRule,
    FeeCalculationLog,
    FeeConfig,
    FeeHistory,
    FeeRevenueStats,
)
from app.schemas.fee import (
    DynamicFeeRuleCreate,
    DynamicFeeRuleUpdate,
    FeeCalculationRequest,
    FeeCalculationResult,
    FeeConfigCreate,
    FeeConfigUpdate,
    FeeHistoryCreate,
    PartnerFeeStats,
    TotalRevenueStats,
)

logger = get_logger(__name__)


class FeeService:
    """수수료 관리 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_fee_config(
        self, fee_data: FeeConfigCreate, admin_id: int
    ) -> FeeConfig:
        """새 수수료 설정을 생성합니다."""
        try:
            # 중복 확인
            existing_result = await self.db.execute(
                select(FeeConfig).where(
                    and_(
                        FeeConfig.transaction_type == fee_data.transaction_type,
                        FeeConfig.partner_id == fee_data.partner_id,
                        FeeConfig.is_active == True,
                    )
                )
            )
            existing_config = existing_result.scalar_one_or_none()

            if existing_config:
                raise ValidationError(
                    f"이미 존재하는 수수료 설정입니다: {fee_data.transaction_type}"
                )

            # 새 설정 생성
            fee_config = FeeConfig(
                transaction_type=fee_data.transaction_type,
                base_fee=fee_data.base_fee,
                percentage_fee=fee_data.percentage_fee,
                min_fee=fee_data.min_fee,
                max_fee=fee_data.max_fee,
                partner_id=fee_data.partner_id,
            )

            self.db.add(fee_config)
            await self.db.commit()
            await self.db.refresh(fee_config)

            # 이력 기록
            await self._create_fee_history(
                fee_config_id=fee_config.id,
                old_values={},
                new_values=fee_data.dict(),
                changed_by=admin_id,
                change_reason="새 수수료 설정 생성",
            )

            logger.info(f"새 수수료 설정 생성: {fee_config.id}")
            return fee_config

        except Exception as e:
            await self.db.rollback()
            logger.error(f"수수료 설정 생성 실패: {str(e)}")
            raise

    async def update_fee_config(
        self, config_id: int, update_data: FeeConfigUpdate, admin_id: int
    ) -> FeeConfig:
        """수수료 설정을 업데이트합니다."""
        try:
            # 기존 설정 조회
            result = await self.db.execute(
                select(FeeConfig).where(FeeConfig.id == config_id)
            )
            fee_config = result.scalar_one_or_none()

            if not fee_config:
                raise NotFoundError(f"수수료 설정을 찾을 수 없습니다: {config_id}")

            # 기존 값 저장
            old_values = {
                "base_fee": str(fee_config.base_fee),
                "percentage_fee": str(fee_config.percentage_fee),
                "min_fee": str(fee_config.min_fee),
                "max_fee": str(fee_config.max_fee),
                "is_active": fee_config.is_active,
            }

            # 업데이트 적용
            update_dict = update_data.dict(exclude_unset=True)
            if update_dict:
                await self.db.execute(
                    update(FeeConfig)
                    .where(FeeConfig.id == config_id)
                    .values(**update_dict, updated_at=func.now())
                )

                await self.db.commit()
                await self.db.refresh(fee_config)

                # 이력 기록
                await self._create_fee_history(
                    fee_config_id=config_id,
                    old_values=old_values,
                    new_values=update_dict,
                    changed_by=admin_id,
                    change_reason="수수료 설정 업데이트",
                )

                logger.info(f"수수료 설정 업데이트: {config_id}")

            return fee_config

        except Exception as e:
            await self.db.rollback()
            logger.error(f"수수료 설정 업데이트 실패: {str(e)}")
            raise

    async def calculate_fee(
        self, request: FeeCalculationRequest
    ) -> FeeCalculationResult:
        """거래 수수료를 계산합니다."""
        try:
            # 적용 가능한 수수료 설정 조회
            fee_config = await self._get_applicable_fee_config(
                transaction_type=request.transaction_type, partner_id=request.partner_id
            )

            if not fee_config:
                raise NotFoundError(
                    f"적용 가능한 수수료 설정이 없습니다: {request.transaction_type}"
                )

            # 기본 수수료 계산
            base_fee = fee_config.base_fee
            percentage_fee = request.amount * fee_config.percentage_fee

            # 동적 수수료 규칙 적용
            dynamic_multiplier, applied_rules = await self._apply_dynamic_rules(
                transaction_type=request.transaction_type,
                amount=request.amount,
                partner_id=request.partner_id,
            )

            # 최종 수수료 계산
            calculated_fee = (base_fee + percentage_fee) * dynamic_multiplier

            # 최소/최대 제한 적용
            final_fee = max(fee_config.min_fee, min(calculated_fee, fee_config.max_fee))

            # 계산 세부사항
            calculation_details = {
                "base_fee": str(base_fee),
                "percentage_fee": str(percentage_fee),
                "calculated_fee": str(calculated_fee),
                "min_limit": str(fee_config.min_fee),
                "max_limit": str(fee_config.max_fee),
                "transaction_amount": str(request.amount),
            }

            # 계산 로그 기록
            await self._log_fee_calculation(
                request=request,
                fee_config=fee_config,
                base_fee=base_fee,
                percentage_fee=percentage_fee,
                dynamic_multiplier=dynamic_multiplier,
                final_fee=final_fee,
                applied_rules=applied_rules,
                calculation_details=calculation_details,
            )

            return FeeCalculationResult(
                base_fee=base_fee,
                percentage_fee=percentage_fee,
                dynamic_multiplier=dynamic_multiplier,
                final_fee=final_fee,
                applied_rules=applied_rules,
                calculation_details=calculation_details,
            )

        except Exception as e:
            logger.error(f"수수료 계산 실패: {str(e)}")
            raise

    async def get_partner_revenue_stats(
        self, partner_id: int, start_date: datetime, end_date: datetime
    ) -> PartnerFeeStats:
        """파트너별 매출 통계를 조회합니다."""
        try:
            # 파트너별 수수료 통계 조회
            result = await self.db.execute(
                select(
                    func.count(FeeCalculationLog.id).label("total_transactions"),
                    func.sum(FeeCalculationLog.final_fee).label("total_fee_collected"),
                    func.avg(FeeCalculationLog.final_fee).label("average_fee"),
                ).where(
                    and_(
                        FeeCalculationLog.partner_id == partner_id,
                        FeeCalculationLog.created_at >= start_date,
                        FeeCalculationLog.created_at <= end_date,
                    )
                )
            )
            stats = result.first()

            # 전체 대비 비율 계산
            total_result = await self.db.execute(
                select(func.sum(FeeCalculationLog.final_fee)).where(
                    and_(
                        FeeCalculationLog.created_at >= start_date,
                        FeeCalculationLog.created_at <= end_date,
                    )
                )
            )
            total_fee = total_result.scalar() or Decimal("0")

            fee_percentage = (
                (stats.total_fee_collected / total_fee * 100)
                if total_fee > 0 and stats.total_fee_collected
                else Decimal("0")
            )

            return PartnerFeeStats(
                partner_id=partner_id,
                partner_name=None,  # 실제 구현 시 파트너명 조회
                total_transactions=stats.total_transactions or 0,
                total_fee_collected=stats.total_fee_collected or Decimal("0"),
                average_fee=stats.average_fee or Decimal("0"),
                fee_percentage=fee_percentage,
            )

        except Exception as e:
            logger.error(f"파트너 매출 통계 조회 실패: {str(e)}")
            raise

    async def get_total_revenue_stats(
        self, start_date: datetime, end_date: datetime
    ) -> TotalRevenueStats:
        """전체 매출 통계를 조회합니다."""
        try:
            # 전체 통계
            total_result = await self.db.execute(
                select(
                    func.count(FeeCalculationLog.id).label("total_transactions"),
                    func.sum(FeeCalculationLog.final_fee).label("total_fee_collected"),
                    func.avg(FeeCalculationLog.final_fee).label("average_fee"),
                    func.count(func.distinct(FeeCalculationLog.partner_id)).label(
                        "partners_count"
                    ),
                ).where(
                    and_(
                        FeeCalculationLog.created_at >= start_date,
                        FeeCalculationLog.created_at <= end_date,
                    )
                )
            )
            total_stats = total_result.first()

            # 상위 파트너 조회 (실제 구현 시 파트너 정보 포함)
            top_partners = []  # 임시로 빈 리스트

            # 일별 매출 (실제 구현 시 상세 조회)
            daily_revenue = []  # 임시로 빈 리스트

            return TotalRevenueStats(
                total_transactions=total_stats.total_transactions or 0,
                total_fee_collected=total_stats.total_fee_collected or Decimal("0"),
                average_fee=total_stats.average_fee or Decimal("0"),
                partners_count=total_stats.partners_count or 0,
                top_partners=top_partners,
                daily_revenue=daily_revenue,
            )

        except Exception as e:
            logger.error(f"전체 매출 통계 조회 실패: {str(e)}")
            raise

    async def _get_applicable_fee_config(
        self, transaction_type: str, partner_id: Optional[int] = None
    ) -> Optional[FeeConfig]:
        """적용 가능한 수수료 설정을 조회합니다."""
        # 파트너별 설정 우선 조회
        if partner_id:
            result = await self.db.execute(
                select(FeeConfig).where(
                    and_(
                        FeeConfig.transaction_type == transaction_type,
                        FeeConfig.partner_id == partner_id,
                        FeeConfig.is_active == True,
                    )
                )
            )
            partner_config = result.scalar_one_or_none()
            if partner_config:
                return partner_config

        # 글로벌 설정 조회
        result = await self.db.execute(
            select(FeeConfig).where(
                and_(
                    FeeConfig.transaction_type == transaction_type,
                    FeeConfig.partner_id.is_(None),
                    FeeConfig.is_active == True,
                )
            )
        )
        return result.scalar_one_or_none()

    async def _apply_dynamic_rules(
        self, transaction_type: str, amount: Decimal, partner_id: Optional[int] = None
    ) -> tuple[Decimal, List[str]]:
        """동적 수수료 규칙을 적용합니다."""
        try:
            # 적용 가능한 규칙 조회
            result = await self.db.execute(
                select(DynamicFeeRule)
                .where(
                    and_(
                        DynamicFeeRule.transaction_type == transaction_type,
                        DynamicFeeRule.is_active == True,
                    )
                )
                .order_by(desc(DynamicFeeRule.priority))
            )
            rules = result.scalars().all()

            multiplier = Decimal("1.0")
            applied_rules = []

            for rule in rules:
                if await self._check_rule_condition(rule, amount, partner_id):
                    multiplier *= rule.fee_multiplier
                    applied_rules.append(rule.rule_name)

            return multiplier, applied_rules

        except Exception as e:
            logger.error(f"동적 규칙 적용 실패: {str(e)}")
            return Decimal("1.0"), []

    async def _check_rule_condition(
        self, rule: DynamicFeeRule, amount: Decimal, partner_id: Optional[int]
    ) -> bool:
        """규칙 조건을 확인합니다."""
        try:
            condition = (
                json.loads(rule.condition_value)
                if isinstance(rule.condition_value, str)
                else rule.condition_value
            )

            if rule.condition_type == "volume_based":
                min_amount = Decimal(str(condition.get("min_amount", 0)))
                max_amount = Decimal(str(condition.get("max_amount", float("inf"))))
                return min_amount <= amount <= max_amount

            elif rule.condition_type == "time_based":
                current_hour = datetime.now().hour
                start_hour = condition.get("start_hour", 0)
                end_hour = condition.get("end_hour", 23)
                return start_hour <= current_hour <= end_hour

            elif rule.condition_type == "network_congestion":
                # 실제 구현 시 네트워크 상태 확인
                return False

            return False

        except Exception as e:
            logger.error(f"규칙 조건 확인 실패: {str(e)}")
            return False

    async def _create_fee_history(
        self,
        fee_config_id: int,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        changed_by: int,
        change_reason: str,
    ):
        """수수료 변경 이력을 기록합니다."""
        try:
            history = FeeHistory(
                fee_config_id=fee_config_id,
                old_values=json.dumps(old_values),
                new_values=json.dumps(new_values),
                changed_by=changed_by,
                change_reason=change_reason,
            )

            self.db.add(history)
            await self.db.commit()

        except Exception as e:
            logger.error(f"수수료 이력 기록 실패: {str(e)}")

    async def _log_fee_calculation(
        self,
        request: FeeCalculationRequest,
        fee_config: FeeConfig,
        base_fee: Decimal,
        percentage_fee: Decimal,
        dynamic_multiplier: Decimal,
        final_fee: Decimal,
        applied_rules: List[str],
        calculation_details: Dict[str, Any],
    ):
        """수수료 계산 로그를 기록합니다."""
        try:
            log = FeeCalculationLog(
                user_id=request.user_id,
                partner_id=request.partner_id,
                transaction_type=request.transaction_type,
                transaction_amount=request.amount,
                base_fee=base_fee,
                percentage_fee=percentage_fee,
                dynamic_multiplier=dynamic_multiplier,
                final_fee=final_fee,
                fee_config_id=fee_config.id,
                applied_rules=json.dumps(applied_rules),
                calculation_details=json.dumps(calculation_details),
            )

            self.db.add(log)
            await self.db.commit()

        except Exception as e:
            logger.error(f"수수료 계산 로그 기록 실패: {str(e)}")
