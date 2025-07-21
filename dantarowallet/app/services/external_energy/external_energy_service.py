"""
외부 에너지 관리 서비스
"""
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, desc
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.models.energy_provider import EnergyProvider, ProviderStatus
from app.models.energy_price import EnergyPrice
from app.models.energy_order import EnergyOrder, OrderType, OrderStatus
from app.schemas.external_energy import (
    EnergyProviderResponse, MarketSummary, CreateOrderRequest, 
    EnergyOrderResponse, CreateOrderResponse
)
from app.services.external_energy.tronnrg_service import tronnrg_service, TronNRGAPIError
from app.services.external_energy.energytron_service import energytron_service
from app.core.exceptions import DantaroException

logger = logging.getLogger(__name__)


class ExternalEnergyError(DantaroException):
    """외부 에너지 관련 오류"""
    def __init__(self, message: str, error_code: str = "EXTERNAL_ENERGY_ERROR"):
        super().__init__(message, error_code)


class ExternalEnergyService:
    """외부 에너지 관리 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # 지원하는 공급업체 서비스 매핑
        self.provider_services = {
            'tronnrg': tronnrg_service,
            'energytron': energytron_service
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
                    provider_data.update({
                        "pricePerEnergy": float(str(latest_price.price)),
                        "availableEnergy": latest_price.available_energy
                    })
                else:
                    provider_data.update({
                        "pricePerEnergy": 0.0,
                        "availableEnergy": 0
                    })
                
                provider_responses.append(EnergyProviderResponse(**provider_data))
            
            return provider_responses
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_providers: {e}")
            raise ExternalEnergyError("Failed to fetch providers")
    
    async def get_provider_detail(self, provider_id: str) -> Optional[EnergyProviderResponse]:
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
                provider_data.update({
                    "pricePerEnergy": float(latest_price.price) if latest_price.price else 0.0,  # type: ignore
                    "availableEnergy": latest_price.available_energy
                })
            else:
                provider_data.update({
                    "pricePerEnergy": 0.0,
                    "availableEnergy": 0
                })
            
            return EnergyProviderResponse(**provider_data)
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_provider_detail: {e}")
            raise ExternalEnergyError("Failed to fetch provider details")
    
    async def get_market_summary(self) -> MarketSummary:
        """시장 요약 정보 조회"""
        try:
            # 활성 공급자 수 조회
            provider_result = await self.db.execute(
                select(EnergyProvider)
                .where(EnergyProvider.status == ProviderStatus.ONLINE)
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
                    prices.append({
                        "provider_id": provider.id,
                        "provider_name": provider.name,
                        "price": float(latest_price.price) if latest_price.price else 0.0  # type: ignore
                    })
            
            # 최저 가격 찾기
            best_price_data = min(prices, key=lambda x: x["price"]) if prices else None
            
            # 평균 가격 계산
            avg_price = sum(p["price"] for p in prices) / len(prices) if prices else 0.0
            
            # 총 거래량 계산 (임시)
            total_volume = sum(p.get("volume_24h", 0) for p in [p.to_dict() for provider in active_providers 
                              for p in provider.prices] if p.get("volume_24h"))
            
            return MarketSummary(
                bestPrice=best_price_data["price"] if best_price_data else 0.0,
                bestProvider=best_price_data["provider_name"] if best_price_data else "",
                totalProviders=len(active_providers),
                activeProviders=len(active_providers),
                avgPrice=avg_price,
                priceChange24h=0.0,  # TODO: 24시간 변동률 계산
                totalVolume=total_volume,
                lastUpdated=datetime.now().isoformat()
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
                    
                    prices.append({
                        "providerId": provider.id,
                        "providerName": provider.name,
                        "price": provider.pricePerEnergy,
                        "availableEnergy": provider.availableEnergy,
                        "change24h": change_24h,
                        "timestamp": latest_price.timestamp.isoformat()
                    })
            
            return prices
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_realtime_prices: {e}")
            raise ExternalEnergyError("Failed to fetch realtime prices")
    
    async def create_order(self, order_request: CreateOrderRequest, user_id: str) -> EnergyOrderResponse:
        """새로운 주문 생성"""
        try:
            # 공급자 확인
            provider_result = await self.db.execute(
                select(EnergyProvider).where(EnergyProvider.id == order_request.providerId)
            )
            provider = provider_result.scalar_one_or_none()
            
            if not provider:
                raise ExternalEnergyError("Provider not found", "PROVIDER_NOT_FOUND")
            
            # 주문 ID 생성
            order_id = str(uuid.uuid4())
            
            # 총 비용 계산
            price_limit = Decimal(str(order_request.priceLimit)) if order_request.priceLimit else Decimal('0')
            total_cost = Decimal(str(order_request.amount)) * price_limit
            
            # 주문 생성
            order = EnergyOrder(
                id=order_id,
                provider_id=order_request.providerId,
                user_id=user_id,
                amount=order_request.amount,
                price=order_request.priceLimit or Decimal('0'),
                total_cost=total_cost,
                order_type=OrderType(order_request.orderType),
                duration=order_request.duration or 1,
                trading_fee=provider.trading_fee,
                withdrawal_fee=provider.withdrawal_fee
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
        status_filter: Optional[OrderStatus] = None
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
    
    async def get_order_detail(self, order_id: str, user_id: str) -> Optional[EnergyOrderResponse]:
        """특정 주문 상세 정보 조회"""
        try:
            result = await self.db.execute(
                select(EnergyOrder).where(
                    and_(
                        EnergyOrder.id == order_id,
                        EnergyOrder.user_id == user_id
                    )
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
                    change_24h=Decimal(str(market_data.get("change24h", 0.0)))
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
            best_price = float('inf')
            
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
                                'provider': provider_name,
                                'price_per_unit': tier.price_per_unit,
                                'total_cost': total_cost,
                                'tier_info': tier
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
        partner_allocation: Optional[Dict[str, int]] = None
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
                    partner_allocation=partner_allocation
                )
                
                result = await service.purchase_energy(request)
                return {
                    'provider_used': preferred_provider,
                    'purchase_result': result,
                    'strategy': 'preferred_provider'
                }
            else:
                # 최적 가격 공급업체 자동 선택
                best_option = await self.find_best_price(energy_amount)
                if not best_option:
                    raise ExternalEnergyError("No available providers for the requested amount")
                
                service = self._get_provider_service(best_option['provider'])
                from app.schemas.external_energy import EnergyPurchaseRequest
                
                request = EnergyPurchaseRequest(
                    amount=energy_amount,
                    target_address=target_address,
                    auto_distribute=auto_distribute,
                    partner_allocation=partner_allocation
                )
                
                result = await service.purchase_energy(request)
                return {
                    'provider_used': best_option['provider'],
                    'purchase_result': result,
                    'best_price_info': best_option,
                    'strategy': 'best_price'
                }
                
        except Exception as e:
            logger.error(f"Error in multi-provider purchase: {e}")
            raise ExternalEnergyError(f"Failed to purchase energy: {str(e)}")
    
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
                        'is_healthy': is_healthy,
                        'response_time': response_time,
                        'last_check': datetime.now(),
                        'error_message': None
                    }
                except Exception as e:
                    health_status[provider_name] = {
                        'is_healthy': False,
                        'response_time': 0.0,
                        'last_check': datetime.now(),
                        'error_message': str(e)
                    }
            
            return health_status
        except Exception as e:
            logger.error(f"Error checking provider health: {e}")
            raise ExternalEnergyError("Failed to check provider health")
