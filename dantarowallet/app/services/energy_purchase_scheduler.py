"""
외부 에너지 공급자 자동 구매 스케줄러
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.models.energy_rental import EnergyPool
from app.models.external_energy import (
    EnergyProviderType,
    EnergyPurchaseRule,
    ExternalEnergyProvider,
    ExternalEnergyPurchase,
    PurchaseStatus,
)
from app.services.external_energy_service import ExternalEnergyService, safe_get_value

logger = get_logger(__name__)


class EnergyPurchaseScheduler:
    """에너지 자동 구매 스케줄러"""

    def __init__(self):
        self.is_running = False
        self.task = None
        self.external_energy_service = ExternalEnergyService()

    async def start(self):
        """스케줄러 시작"""
        if self.is_running:
            logger.warning("스케줄러가 이미 실행 중입니다")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._run_scheduler())
        logger.info("에너지 자동 구매 스케줄러 시작")

    async def stop(self):
        """스케줄러 중지"""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("에너지 자동 구매 스케줄러 중지")

    async def _run_scheduler(self):
        """스케줄러 메인 루프"""
        while self.is_running:
            try:
                await self._run_scheduler_cycle()
                await asyncio.sleep(60)  # 1분마다 실행
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"스케줄러 실행 오류: {e}")
                await asyncio.sleep(60)

    async def _run_scheduler_cycle(self):
        """스케줄러 실행 주기"""
        try:
            async with AsyncSessionLocal() as session:
                # 활성 구매 규칙 조회
                rules = await self._get_active_rules(session)

                # 각 규칙에 대해 조건 확인 및 실행
                for rule in rules:
                    try:
                        await self._process_rule(rule, session)
                    except Exception as e:
                        logger.error(
                            f"규칙 {safe_get_value(rule, 'id', 'unknown')} 처리 오류: {e}"
                        )

        except Exception as e:
            logger.error(f"스케줄러 주기 실행 오류: {e}")

    async def _get_active_rules(
        self, session: AsyncSession
    ) -> List[EnergyPurchaseRule]:
        """활성 구매 규칙 조회"""
        try:
            stmt = (
                select(EnergyPurchaseRule)
                .where(EnergyPurchaseRule.is_active == True)
                .order_by(EnergyPurchaseRule.priority)
            )

            result = await session.execute(stmt)
            rules = result.scalars().all()
            return list(rules)

        except Exception as e:
            logger.error(f"활성 규칙 조회 오류: {e}")
            return []

    async def _process_rule(self, rule: EnergyPurchaseRule, session: AsyncSession):
        """규칙 처리"""
        try:
            rule_id = safe_get_value(rule, "id", "unknown")

            # 일일 실행 한도 확인
            if not await self._check_daily_limit(rule, session):
                logger.info(f"규칙 {rule_id}: 일일 실행 한도 초과")
                return

            # 쿨다운 시간 확인
            if not await self._check_cooldown(rule):
                logger.info(f"규칙 {rule_id}: 쿨다운 시간 내")
                return

            # 트리거 조건 확인
            if not await self._check_trigger_conditions(rule, session):
                logger.debug(f"규칙 {rule_id}: 트리거 조건 미충족")
                return

            # 자동 구매 실행
            await self._execute_auto_purchase(rule, session)

        except Exception as e:
            logger.error(f"규칙 처리 오류: {e}")

    async def _check_daily_limit(
        self, rule: EnergyPurchaseRule, session: AsyncSession
    ) -> bool:
        """일일 실행 한도 확인"""
        try:
            rule_id = safe_get_value(rule, "id", 0)
            max_daily = safe_get_value(rule, "max_daily_executions", 10)

            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            stmt = select(ExternalEnergyPurchase).where(
                and_(
                    ExternalEnergyPurchase.trigger_reason.like(f"%rule_{rule_id}%"),
                    ExternalEnergyPurchase.created_at >= today,
                )
            )

            result = await session.execute(stmt)
            daily_count = len(result.scalars().all())

            return daily_count < max_daily

        except Exception as e:
            logger.error(f"일일 한도 확인 오류: {e}")
            return False

    async def _check_cooldown(self, rule: EnergyPurchaseRule) -> bool:
        """쿨다운 시간 확인"""
        try:
            last_executed = safe_get_value(rule, "last_executed_at")
            if not last_executed:
                return True

            cooldown_minutes = safe_get_value(rule, "cooldown_minutes", 30)
            next_execution = last_executed + timedelta(minutes=cooldown_minutes)

            return datetime.utcnow() >= next_execution
        except Exception as e:
            logger.error(f"쿨다운 확인 오류: {e}")
            return True

    async def _check_trigger_conditions(
        self, rule: EnergyPurchaseRule, session: AsyncSession
    ) -> bool:
        """트리거 조건 확인"""
        try:
            trigger_type = safe_get_value(rule, "trigger_type", "")

            if trigger_type == "threshold":
                return await self._check_threshold_trigger(rule, session)
            elif trigger_type == "schedule":
                return await self._check_schedule_trigger(rule)
            elif trigger_type == "prediction":
                return await self._check_prediction_trigger(rule, session)
            else:
                return False
        except Exception as e:
            logger.error(f"트리거 조건 확인 오류: {e}")
            return False

    async def _check_threshold_trigger(
        self, rule: EnergyPurchaseRule, session: AsyncSession
    ) -> bool:
        """임계값 트리거 확인"""
        try:
            # 현재 에너지 풀 상태 조회
            stmt = select(EnergyPool).where(EnergyPool.is_active == True)
            result = await session.execute(stmt)
            energy_pools = result.scalars().all()

            if not energy_pools:
                return False

            # 전체 에너지 계산
            total_energy = sum(
                safe_get_value(pool, "available_energy", 0) for pool in energy_pools
            )
            total_capacity = sum(
                safe_get_value(pool, "total_capacity", 0) for pool in energy_pools
            )

            # 임계값 체크
            energy_threshold = safe_get_value(rule, "energy_threshold")
            if energy_threshold and total_energy < energy_threshold:
                return True

            threshold_percentage = safe_get_value(rule, "threshold_percentage")
            if threshold_percentage and total_capacity > 0:
                current_percentage = (total_energy / total_capacity) * 100
                if current_percentage < float(threshold_percentage):
                    return True

            return False

        except Exception as e:
            logger.error(f"임계값 트리거 확인 오류: {e}")
            return False

    async def _check_schedule_trigger(self, rule: EnergyPurchaseRule) -> bool:
        """스케줄 트리거 확인"""
        try:
            schedule_cron = safe_get_value(rule, "schedule_cron")
            if not schedule_cron:
                return False

            # 매시간 실행 예시
            if schedule_cron == "0 * * * *":
                now = datetime.utcnow()
                return now.minute == 0

            # 추가 스케줄 로직 구현 필요
            return False

        except Exception as e:
            logger.error(f"스케줄 트리거 확인 오류: {e}")
            return False

    async def _check_prediction_trigger(
        self, rule: EnergyPurchaseRule, session: AsyncSession
    ) -> bool:
        """예측 트리거 확인"""
        try:
            # 예측 모델을 통한 에너지 수요 예측
            # 현재는 간단한 트렌드 분석
            stmt = select(EnergyPool).where(EnergyPool.is_active == True)
            result = await session.execute(stmt)
            energy_pools = result.scalars().all()

            if not energy_pools:
                return False

            # 에너지 감소율 계산
            total_energy = sum(
                safe_get_value(pool, "available_energy", 0) for pool in energy_pools
            )
            energy_threshold = safe_get_value(rule, "energy_threshold")

            # 임계값 기반 예측
            if energy_threshold and total_energy < energy_threshold * 1.2:
                return True

            return False

        except Exception as e:
            logger.error(f"예측 트리거 확인 오류: {e}")
            return False

    async def _execute_auto_purchase(
        self, rule: EnergyPurchaseRule, session: AsyncSession
    ):
        """자동 구매 실행"""
        try:
            # 구매량 계산
            purchase_amount = await self._calculate_purchase_amount(rule, session)

            # 최적 공급자 선택
            best_provider = await self._select_best_provider(rule, session)

            if not best_provider:
                logger.warning("사용 가능한 공급자가 없습니다")
                return

            # 가격 확인
            provider_prices = await self.external_energy_service.get_current_prices(
                session
            )
            provider_price = next(
                (
                    p
                    for p in provider_prices
                    if p["provider_id"] == safe_get_value(best_provider, "id")
                ),
                None,
            )

            if not provider_price:
                logger.warning(
                    f"공급자 {safe_get_value(best_provider, 'name')}의 가격 정보를 찾을 수 없습니다"
                )
                return

            # 최대 허용 가격 확인
            max_price = safe_get_value(rule, "max_price")
            if max_price and provider_price["price_per_energy"] > max_price:
                logger.warning(
                    f"가격이 최대 허용 가격을 초과합니다: {provider_price['price_per_energy']} > {max_price}"
                )
                return

            # 구매 실행
            provider_type_value = safe_get_value(best_provider, "provider_type")
            if isinstance(provider_type_value, EnergyProviderType):
                provider_type_enum = provider_type_value
            else:
                # 문자열인 경우 enum으로 변환
                provider_type_enum = EnergyProviderType(str(provider_type_value))

            purchase = await self.external_energy_service.execute_purchase(
                provider_type=provider_type_enum,
                energy_amount=purchase_amount,
                session=session,
                purchase_type="auto",
            )

            if purchase:
                # 구매 성공 시 규칙 업데이트
                setattr(rule, "last_executed_at", datetime.utcnow())
                await session.commit()

                logger.info(
                    f"자동 구매 완료: {purchase_amount} 에너지, 공급자: {safe_get_value(best_provider, 'name')}"
                )

        except Exception as e:
            logger.error(f"자동 구매 실행 오류: {e}")
            await session.rollback()

    async def _calculate_purchase_amount(
        self, rule: EnergyPurchaseRule, session: AsyncSession
    ) -> int:
        """구매량 계산"""
        try:
            purchase_amount = safe_get_value(rule, "purchase_amount")
            if purchase_amount:
                return int(purchase_amount)

            purchase_percentage = safe_get_value(rule, "purchase_percentage")
            if purchase_percentage:
                # 전체 용량 기준 퍼센트 계산
                stmt = select(EnergyPool).where(EnergyPool.is_active == True)
                result = await session.execute(stmt)
                energy_pools = result.scalars().all()

                total_capacity = sum(
                    safe_get_value(pool, "total_capacity", 0) for pool in energy_pools
                )
                return int(total_capacity * float(purchase_percentage) / 100)

            # 기본값: 10,000 에너지
            return 10000

        except Exception as e:
            logger.error(f"구매량 계산 오류: {e}")
            return 10000

    async def _select_best_provider(
        self, rule: EnergyPurchaseRule, session: AsyncSession
    ) -> Optional[ExternalEnergyProvider]:
        """최적 공급자 선택"""
        try:
            # 기본 조건: 활성 상태
            stmt = select(ExternalEnergyProvider).where(
                ExternalEnergyProvider.is_active == True
            )

            # 선호 공급자 필터
            preferred_providers = safe_get_value(rule, "preferred_providers")
            if preferred_providers:
                preferred_types = [EnergyProviderType(pt) for pt in preferred_providers]
                stmt = stmt.where(
                    ExternalEnergyProvider.provider_type.in_(preferred_types)
                )

            # 우선순위 정렬
            stmt = stmt.order_by(
                ExternalEnergyProvider.priority,
                ExternalEnergyProvider.success_rate.desc(),
            )

            result = await session.execute(stmt)
            providers = result.scalars().all()

            if not providers:
                # 선호 공급자가 없으면 모든 활성 공급자 중 선택
                stmt = (
                    select(ExternalEnergyProvider)
                    .where(ExternalEnergyProvider.is_active == True)
                    .order_by(
                        ExternalEnergyProvider.priority,
                        ExternalEnergyProvider.success_rate.desc(),
                    )
                )

                result = await session.execute(stmt)
                return result.scalar_one_or_none()

            return providers[0] if providers else None

        except Exception as e:
            logger.error(f"최적 공급자 선택 오류: {e}")
            return None


# 전역 스케줄러 인스턴스
energy_purchase_scheduler = EnergyPurchaseScheduler()
