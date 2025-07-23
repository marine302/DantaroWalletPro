"""
외부 에너지 관리 서비스
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, desc, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_optimization import api_optimizer, concurrency_optimizer
from app.core.database_optimization import OptimizedServiceBase, db_optimizer
from app.core.exceptions import DantaroException
from app.models.energy_order import EnergyOrder, OrderStatus, OrderType
from app.models.energy_price import EnergyPrice
from app.models.energy_provider import EnergyProvider, ProviderStatus
from app.schemas.external_energy import (
    CreateOrderRequest,
    CreateOrderResponse,
    EnergyOrderResponse,
    EnergyProviderResponse,
    MarketSummary,
    ProviderFees,
    ProviderStatus,
)
from app.services.external_energy.energytron_service import energytron_service
from app.services.external_energy.tronnrg_service import (
    TronNRGAPIError,
    tronnrg_service,
)

logger = logging.getLogger(__name__)


class ExternalEnergyError(DantaroException):
    """외부 에너지 관련 오류"""

    def __init__(self, message: str, error_code: str = "EXTERNAL_ENERGY_ERROR"):
        super().__init__(message, error_code)


# 기존 서비스 최적화
class OptimizedExternalEnergyService(OptimizedServiceBase):
    """최적화된 외부 에너지 서비스"""

    def __init__(self, db: AsyncSession):
        super().__init__(db)
        # 지원하는 공급업체 서비스 매핑
        self.provider_services = {
            "tronnrg": tronnrg_service,
            "energytron": energytron_service,
        }

    @api_optimizer.performance_monitor()
    @api_optimizer.circuit_breaker(failure_threshold=3, recovery_timeout=30)
    async def get_optimized_suppliers(self) -> List[EnergyProviderResponse]:
        """최적화된 공급업체 목록 조회"""
        try:
            # 캐싱된 공급업체 조회
            cached_suppliers = await self._get_cached_suppliers()
            if cached_suppliers:
                return cached_suppliers

            # 병렬로 모든 공급업체 상태 확인
            async with concurrency_optimizer.limited_concurrency("supplier_check", 5):
                supplier_tasks = []
                for provider_name, service in self.provider_services.items():
                    task = self._check_provider_status(provider_name, service)
                    supplier_tasks.append(task)

                results = await asyncio.gather(*supplier_tasks, return_exceptions=True)

            # 결과 필터링 및 정렬
            active_suppliers = []
            for result in results:
                if isinstance(result, EnergyProviderResponse):
                    active_suppliers.append(result)

            # 신뢰도 순으로 정렬
            active_suppliers.sort(key=lambda x: x.reliability_score, reverse=True)

            # 결과 캐싱 (5분)
            await self._cache_suppliers(active_suppliers, 300)

            return active_suppliers

        except Exception as e:
            logger.error(f"최적화된 공급업체 조회 실패: {e}")
            raise ExternalEnergyError("Failed to retrieve optimized suppliers")

    @db_optimizer.cache_query(expire_seconds=180)  # 3분 캐싱
    async def get_price_comparison(self, amount: int) -> Dict[str, Any]:
        """가격 비교 최적화"""
        try:
            # 동시에 모든 공급업체 가격 조회
            price_tasks = []
            for provider_name, service in self.provider_services.items():
                task = self._get_provider_price(provider_name, service, amount)
                price_tasks.append(task)

            prices = await asyncio.gather(*price_tasks, return_exceptions=True)

            # 유효한 가격만 필터링
            valid_prices = []
            for price in prices:
                if isinstance(price, dict) and "provider" in price:
                    valid_prices.append(price)

            if not valid_prices:
                raise ExternalEnergyError("No valid prices available")

            # 최적 가격 계산
            best_price = min(valid_prices, key=lambda x: x["total_cost"])
            savings = (
                max(valid_prices, key=lambda x: x["total_cost"])["total_cost"]
                - best_price["total_cost"]
            )

            return {
                "prices": valid_prices,
                "best_option": best_price,
                "potential_savings": savings,
                "comparison_time": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"가격 비교 최적화 실패: {e}")
            raise

    async def _check_provider_status(
        self, provider_name: str, service
    ) -> Optional[EnergyProviderResponse]:
        """공급업체 상태 확인"""
        try:
            # 헬스체크
            is_healthy = await service.health_check()
            if not is_healthy:
                return None

            # 기본 정보 조회
            return EnergyProviderResponse(
                id=provider_name,
                name=provider_name.title(),
                status=ProviderStatus.ONLINE,
                pricePerEnergy=0.001,
                availableEnergy=1000000,
                reliability=95.0,
                avgResponseTime=150.0,
                minOrderSize=1000,
                maxOrderSize=1000000,
                fees=ProviderFees(tradingFee=0.001, withdrawalFee=0.0005),
                lastUpdated=datetime.now().isoformat(),  # 문자열로 변환
            )

        except Exception as e:
            logger.warning(f"공급업체 {provider_name} 상태 확인 실패: {e}")
            return None

    async def _get_provider_price(
        self, provider_name: str, service, amount: int
    ) -> Optional[Dict[str, Any]]:
        """공급업체별 가격 조회"""
        try:
            price_response = await service.get_current_prices()
            if not price_response or not price_response.prices:
                return None

            # 요청 금액에 맞는 가격 찾기
            suitable_price = None
            for price_tier in price_response.prices:
                if price_tier.amount >= amount:
                    suitable_price = price_tier
                    break

            if not suitable_price:
                suitable_price = price_response.prices[-1]  # 최대 tier 사용

            return {
                "provider": provider_name,
                "amount": amount,
                "price_per_unit": suitable_price.price_per_unit,
                "total_cost": amount * suitable_price.price_per_unit,
                "estimated_delivery": "5-10 minutes",
                "features": ["Instant", "Reliable"],
            }

        except Exception as e:
            logger.warning(f"공급업체 {provider_name} 가격 조회 실패: {e}")
            return None

    async def _get_cached_suppliers(self) -> Optional[List[EnergyProviderResponse]]:
        """캐싱된 공급업체 조회"""
        # 구현 필요
        return None

    async def _cache_suppliers(self, suppliers: List[EnergyProviderResponse], ttl: int):
        """공급업체 캐싱"""
        # 구현 필요
        pass


class ExternalEnergyService:
    """외부 에너지 관리 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        # 지원하는 공급업체 서비스 매핑
        self.provider_services = {
            "tronnrg": tronnrg_service,
            "energytron": energytron_service,
        }

    def _get_provider_service(self, provider_name: str):
        """공급업체별 서비스 인스턴스 반환"""
        service = self.provider_services.get(provider_name.lower())
        if not service:
            raise ExternalEnergyError(f"Unsupported provider: {provider_name}")
        return service

    async def get_providers(self) -> List[EnergyProviderResponse]:
        """모든 활성 공급자 목록 조회"""
        try:
            # 데이터베이스에서 공급자 조회
            result = await self.db.execute(
                select(EnergyProvider)
                .where(EnergyProvider.status == ProviderStatus.ONLINE)
                .order_by(EnergyProvider.name)
            )
            providers = result.scalars().all()

            # 최신 가격 정보와 함께 응답 생성
            provider_responses = []
            for provider in providers:
                # 최신 가격 조회
                price_result = await self.db.execute(
                    select(EnergyPrice)
                    .where(EnergyPrice.provider_id == provider.id)
                    .order_by(desc(EnergyPrice.timestamp))
                    .limit(1)
                )
                latest_price = price_result.scalar_one_or_none()

                provider_data = provider.to_dict()
                if latest_price:
                    provider_data.update(
                        {
                            "pricePerEnergy": float(str(latest_price.price)),
                            "availableEnergy": latest_price.available_energy,
                        }
                    )
                else:
                    provider_data.update({"pricePerEnergy": 0.0, "availableEnergy": 0})

                provider_responses.append(EnergyProviderResponse(**provider_data))

            return provider_responses

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_providers: {e}")
            raise ExternalEnergyError("Failed to fetch providers")

    async def get_provider_detail(
        self, provider_id: str
    ) -> Optional[EnergyProviderResponse]:
        """특정 공급자 상세 정보 조회"""
        try:
            # 공급자 기본 정보 조회
            result = await self.db.execute(
                select(EnergyProvider).where(EnergyProvider.id == provider_id)
            )
            provider = result.scalar_one_or_none()

            if not provider:
                return None

            # 최신 가격 정보 조회
            price_result = await self.db.execute(
                select(EnergyPrice)
                .where(EnergyPrice.provider_id == provider_id)
                .order_by(desc(EnergyPrice.timestamp))
                .limit(1)
            )
            latest_price = price_result.scalar_one_or_none()

            provider_data = provider.to_dict()
            if latest_price:
                provider_data.update(
                    {
                        "pricePerEnergy": float(latest_price.price) if latest_price.price else 0.0,  # type: ignore
                        "availableEnergy": latest_price.available_energy,
                    }
                )
            else:
                provider_data.update({"pricePerEnergy": 0.0, "availableEnergy": 0})

            return EnergyProviderResponse(**provider_data)

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_provider_detail: {e}")
            raise ExternalEnergyError("Failed to fetch provider details")

    async def get_market_summary(self) -> MarketSummary:
        """시장 요약 정보 조회"""
        try:
            # 활성 공급자 수 조회
            provider_result = await self.db.execute(
                select(EnergyProvider).where(
                    EnergyProvider.status == ProviderStatus.ONLINE
                )
            )
            active_providers = provider_result.scalars().all()

            # 최신 가격들 조회
            prices = []
            for provider in active_providers:
                price_result = await self.db.execute(
                    select(EnergyPrice)
                    .where(EnergyPrice.provider_id == provider.id)
                    .order_by(desc(EnergyPrice.timestamp))
                    .limit(1)
                )
                latest_price = price_result.scalar_one_or_none()
                if latest_price:
                    prices.append(
                        {
                            "provider_id": provider.id,
                            "provider_name": provider.name,
                            "price": float(latest_price.price) if latest_price.price else 0.0,  # type: ignore
                        }
                    )

            # 최저 가격 찾기
            best_price_data = min(prices, key=lambda x: x["price"]) if prices else None

            # 평균 가격 계산
            avg_price = sum(p["price"] for p in prices) / len(prices) if prices else 0.0

            # 총 거래량 계산 (임시)
            total_volume = sum(
                p.get("volume_24h", 0)
                for p in [
                    p.to_dict()
                    for provider in active_providers
                    for p in provider.prices
                ]
                if p.get("volume_24h")
            )

            return MarketSummary(
                bestPrice=best_price_data["price"] if best_price_data else 0.0,
                bestProvider=(
                    best_price_data["provider_name"] if best_price_data else ""
                ),
                totalProviders=len(active_providers),
                activeProviders=len(active_providers),
                avgPrice=avg_price,
                priceChange24h=0.0,  # TODO: 24시간 변동률 계산
                totalVolume=total_volume,
                lastUpdated=datetime.now().isoformat(),
            )

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_market_summary: {e}")
            raise ExternalEnergyError("Failed to fetch market summary")

    async def get_realtime_prices(self) -> List[Dict[str, Any]]:
        """실시간 가격 정보 조회"""
        try:
            # 모든 활성 공급자의 최신 가격 조회
            providers = await self.get_providers()

            prices = []
            for provider in providers:
                price_result = await self.db.execute(
                    select(EnergyPrice)
                    .where(EnergyPrice.provider_id == provider.id)
                    .order_by(desc(EnergyPrice.timestamp))
                    .limit(1)
                )
                latest_price = price_result.scalar_one_or_none()

                if latest_price:
                    change_24h_val = latest_price.change_24h
                    change_24h = float(change_24h_val) if change_24h_val is not None else 0.0  # type: ignore

                    prices.append(
                        {
                            "providerId": provider.id,
                            "providerName": provider.name,
                            "price": provider.pricePerEnergy,
                            "availableEnergy": provider.availableEnergy,
                            "change24h": change_24h,
                            "timestamp": latest_price.timestamp.isoformat(),
                        }
                    )

            return prices

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_realtime_prices: {e}")
            raise ExternalEnergyError("Failed to fetch realtime prices")

    async def create_order(
        self, order_request: CreateOrderRequest, user_id: str
    ) -> EnergyOrderResponse:
        """새로운 주문 생성"""
        try:
            # 공급자 확인
            provider_result = await self.db.execute(
                select(EnergyProvider).where(
                    EnergyProvider.id == order_request.providerId
                )
            )
            provider = provider_result.scalar_one_or_none()

            if not provider:
                raise ExternalEnergyError("Provider not found", "PROVIDER_NOT_FOUND")

            # 주문 ID 생성
            order_id = str(uuid.uuid4())

            # 총 비용 계산
            price_limit = (
                Decimal(str(order_request.priceLimit))
                if order_request.priceLimit
                else Decimal("0")
            )
            total_cost = Decimal(str(order_request.amount)) * price_limit

            # 주문 생성
            order = EnergyOrder(
                id=order_id,
                provider_id=order_request.providerId,
                user_id=user_id,
                amount=order_request.amount,
                price=order_request.priceLimit or Decimal("0"),
                total_cost=total_cost,
                order_type=OrderType(order_request.orderType),
                duration=order_request.duration or 1,
                trading_fee=provider.trading_fee,
                withdrawal_fee=provider.withdrawal_fee,
            )

            self.db.add(order)
            await self.db.commit()
            await self.db.refresh(order)

            return EnergyOrderResponse(**order.to_dict())

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error in create_order: {e}")
            raise ExternalEnergyError("Failed to create order")

    async def get_user_orders(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        status_filter: Optional[OrderStatus] = None,
    ) -> List[EnergyOrderResponse]:
        """사용자 주문 목록 조회"""
        try:
            query = select(EnergyOrder).where(EnergyOrder.user_id == user_id)

            if status_filter:
                query = query.where(EnergyOrder.status == status_filter)

            query = query.order_by(desc(EnergyOrder.created_at))
            query = query.offset((page - 1) * limit).limit(limit)

            result = await self.db.execute(query)
            orders = result.scalars().all()

            return [EnergyOrderResponse(**order.to_dict()) for order in orders]

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_user_orders: {e}")
            raise ExternalEnergyError("Failed to fetch user orders")

    async def get_order_detail(
        self, order_id: str, user_id: str
    ) -> Optional[EnergyOrderResponse]:
        """특정 주문 상세 정보 조회"""
        try:
            result = await self.db.execute(
                select(EnergyOrder).where(
                    and_(EnergyOrder.id == order_id, EnergyOrder.user_id == user_id)
                )
            )
            order = result.scalar_one_or_none()

            if not order:
                return None

            return EnergyOrderResponse(**order.to_dict())

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_order_detail: {e}")
            raise ExternalEnergyError("Failed to fetch order details")

    async def update_provider_data(self, provider_id: str):
        """공급자 데이터 업데이트 (백그라운드 작업)"""
        try:
            # 외부 API에서 최신 데이터 가져오기
            if provider_id.startswith("tronnrg"):
                market_data = await tronnrg_service.get_market_data()

                # 가격 정보 업데이트
                price_data = EnergyPrice(
                    provider_id=provider_id,
                    price=Decimal(str(market_data.get("price", 0.0))),
                    available_energy=market_data.get("availableEnergy", 0),
                    volume_24h=market_data.get("volume24h", 0),
                    change_24h=Decimal(str(market_data.get("change24h", 0.0))),
                )

                self.db.add(price_data)
                await self.db.commit()

                return True

            return False

        except (SQLAlchemyError, TronNRGAPIError) as e:
            await self.db.rollback()
            logger.error(f"Error updating provider data: {e}")
            return False

    async def get_all_provider_prices(self) -> Dict[str, Any]:
        """모든 공급업체의 현재 가격 조회"""
        try:
            all_prices = {}

            for provider_name, service in self.provider_services.items():
                try:
                    prices = await service.get_current_prices()
                    all_prices[provider_name] = prices
                except Exception as e:
                    logger.warning(f"Failed to get prices from {provider_name}: {e}")
                    all_prices[provider_name] = None

            return all_prices
        except Exception as e:
            logger.error(f"Error getting all provider prices: {e}")
            raise ExternalEnergyError("Failed to fetch provider prices")

    async def find_best_price(self, energy_amount: int) -> Optional[Dict[str, Any]]:
        """최적 가격 공급업체 찾기"""
        try:
            all_prices = await self.get_all_provider_prices()
            best_option = None
            best_price = float("inf")

            for provider_name, price_data in all_prices.items():
                if not price_data:
                    continue

                # 해당 에너지 양에 맞는 가격 찾기
                for tier in price_data.prices:
                    if tier.amount >= energy_amount:
                        total_cost = tier.price_per_unit * energy_amount
                        if total_cost < best_price:
                            best_price = total_cost
                            best_option = {
                                "provider": provider_name,
                                "price_per_unit": tier.price_per_unit,
                                "total_cost": total_cost,
                                "tier_info": tier,
                            }
                        break

            return best_option
        except Exception as e:
            logger.error(f"Error finding best price: {e}")
            raise ExternalEnergyError("Failed to find best price")

    async def purchase_energy_multi_provider(
        self,
        energy_amount: int,
        target_address: str,
        preferred_provider: Optional[str] = None,
        auto_distribute: bool = False,
        partner_allocation: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """다중 공급업체를 고려한 에너지 구매"""
        try:
            if preferred_provider:
                # 선호 공급업체 지정된 경우
                service = self._get_provider_service(preferred_provider)
                from app.schemas.external_energy import EnergyPurchaseRequest

                request = EnergyPurchaseRequest(
                    amount=energy_amount,
                    target_address=target_address,
                    auto_distribute=auto_distribute,
                    partner_allocation=partner_allocation,
                )

                result = await service.purchase_energy(request)
                return {
                    "provider_used": preferred_provider,
                    "purchase_result": result,
                    "strategy": "preferred_provider",
                }
            else:
                # 최적 가격 공급업체 자동 선택
                best_option = await self.find_best_price(energy_amount)
                if not best_option:
                    raise ExternalEnergyError(
                        "No available providers for the requested amount"
                    )

                service = self._get_provider_service(best_option["provider"])
                from app.schemas.external_energy import EnergyPurchaseRequest

                request = EnergyPurchaseRequest(
                    amount=energy_amount,
                    target_address=target_address,
                    auto_distribute=auto_distribute,
                    partner_allocation=partner_allocation,
                )

                result = await service.purchase_energy(request)
                return {
                    "provider_used": best_option["provider"],
                    "purchase_result": result,
                    "best_price_info": best_option,
                    "strategy": "best_price",
                }

        except Exception as e:
            logger.error(f"Error in multi-provider purchase: {e}")
            raise ExternalEnergyError(f"Failed to purchase energy: {str(e)}")

    async def update_all_provider_prices(self) -> Dict[str, Any]:
        """모든 공급업체 가격 정보 업데이트"""
        try:
            update_results = {}

            for provider_name, service in self.provider_services.items():
                try:
                    # 각 공급업체별로 가격 업데이트
                    if hasattr(service, "get_energy_price"):
                        # 표준 수량들에 대한 가격 조회 (1M, 10M, 100M)
                        standard_amounts = [1000000, 10000000, 100000000]

                        for amount in standard_amounts:
                            price_info = await service.get_energy_price(amount)
                            if price_info:
                                # DB에 가격 정보 저장
                                await self._update_price_in_db(
                                    provider_name, amount, price_info
                                )

                        update_results[provider_name] = {
                            "success": True,
                            "updated_at": datetime.now(),
                            "price_points": len(standard_amounts),
                        }
                    else:
                        update_results[provider_name] = {
                            "success": False,
                            "error": "Service does not support price updates",
                        }

                except Exception as e:
                    logger.error(f"Failed to update prices for {provider_name}: {e}")
                    update_results[provider_name] = {"success": False, "error": str(e)}

            return update_results

        except Exception as e:
            logger.error(f"Error updating all provider prices: {e}")
            raise ExternalEnergyError("Failed to update provider prices")

    async def _update_price_in_db(
        self, provider_name: str, amount: int, price_info: Dict[str, Any]
    ) -> None:
        """DB에 가격 정보 업데이트"""
        try:
            # 기존 가격 정보 조회
            existing_price = await self.db.execute(
                select(EnergyPrice).where(
                    and_(
                        EnergyPrice.provider_name == provider_name,
                        EnergyPrice.amount == amount,
                    )
                )
            )
            existing_price = existing_price.scalar_one_or_none()

            if existing_price:
                # 기존 정보 업데이트
                existing_price.price_sun = int(price_info.get("price_sun", 0))
                existing_price.price_trx = float(price_info.get("price_trx", 0.0))
                existing_price.updated_at = datetime.now()
            else:
                # 새로운 가격 정보 생성
                new_price = EnergyPrice(
                    provider_name=provider_name,
                    amount=amount,
                    price_sun=int(price_info.get("price_sun", 0)),
                    price_trx=float(price_info.get("price_trx", 0.0)),
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                self.db.add(new_price)

            await self.db.commit()

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update price in DB: {e}")
            raise

    async def check_all_provider_health(self) -> Dict[str, Any]:
        """모든 공급업체 상태 확인"""
        try:
            health_status = {}

            for provider_name, service in self.provider_services.items():
                try:
                    start_time = datetime.now()
                    is_healthy = await service.health_check()
                    response_time = (datetime.now() - start_time).total_seconds()

                    health_status[provider_name] = {
                        "is_healthy": is_healthy,
                        "response_time": response_time,
                        "last_check": datetime.now(),
                        "error_message": None,
                    }
                except Exception as e:
                    health_status[provider_name] = {
                        "is_healthy": False,
                        "response_time": 0.0,
                        "last_check": datetime.now(),
                        "error_message": str(e),
                    }

            return health_status
        except Exception as e:
            logger.error(f"Error checking provider health: {e}")
            raise ExternalEnergyError("Failed to check provider health")


# 서비스 팩토리 함수
def get_external_energy_service(db: AsyncSession) -> ExternalEnergyService:
    """외부 에너지 서비스 인스턴스 생성"""
    return ExternalEnergyService(db)
