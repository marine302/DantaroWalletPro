"""
외부 에너지 공급자 서비스
"""
import asyncio
from typing import List, Dict, Any, Optional, Sequence
from decimal import Decimal
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, update
from sqlalchemy.orm import selectinload

from app.models.external_energy import (
    ExternalEnergyProvider,
    ExternalEnergyPriceHistory,
    ExternalEnergyPurchase,
    EnergyProviderType,
    PurchaseStatus
)
from app.core.logger import get_logger

logger = get_logger(__name__)


def safe_get_value(obj, attr, default=None):
    """SQLAlchemy 객체에서 안전하게 값을 추출"""
    try:
        value = getattr(obj, attr)
        if hasattr(value, '__call__'):
            return default
        return value
    except:
        return default


class ExternalEnergyService:
    """외부 에너지 공급자 관리 서비스"""
    
    def __init__(self):
        pass
    
    async def get_all_providers(self, session: AsyncSession) -> List[ExternalEnergyProvider]:
        """모든 공급자 조회"""
        try:
            logger.info("=== get_all_providers 시작 ===")
            stmt = select(ExternalEnergyProvider).options(
                selectinload(ExternalEnergyProvider.price_history)
            )
            logger.info(f"SQL 쿼리 생성: {stmt}")
            
            result = await session.execute(stmt)
            providers = list(result.scalars().all())
            
            logger.info(f"조회된 공급자 수: {len(providers)}")
            for provider in providers:
                logger.info(f"공급자: id={safe_get_value(provider, 'id')}, name={safe_get_value(provider, 'name')}, active={safe_get_value(provider, 'is_active')}")
                
            return providers
        except Exception as e:
            logger.error(f"공급자 조회 오류: {e}")
            import traceback
            logger.error(f"스택 트레이스: {traceback.format_exc()}")
            return []
    
    async def get_active_providers(self, session: AsyncSession) -> List[ExternalEnergyProvider]:
        """활성 공급자 조회"""
        try:
            logger.info("=== get_active_providers 시작 ===")
            stmt = select(ExternalEnergyProvider).where(
                ExternalEnergyProvider.is_active == True
            ).order_by(ExternalEnergyProvider.priority)
            
            logger.info(f"활성 공급자 쿼리: {stmt}")
            result = await session.execute(stmt)
            providers = list(result.scalars().all())
            
            logger.info(f"활성 공급자 수: {len(providers)}")
            for provider in providers:
                logger.info(f"활성 공급자: id={safe_get_value(provider, 'id')}, name={safe_get_value(provider, 'name')}, priority={safe_get_value(provider, 'priority')}")
                
            return providers
        except Exception as e:
            logger.error(f"활성 공급자 조회 오류: {e}")
            import traceback
            logger.error(f"스택 트레이스: {traceback.format_exc()}")
            return []
    
    async def get_current_prices(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """현재 가격 정보 조회"""
        try:
            print("🚀 === get_current_prices 서비스 시작 ===")  # print 추가
            logger.info("=== get_current_prices 시작 ===")
            prices = []
            providers = await self.get_active_providers(session)
            
            print(f"📊 서비스: 가격 조회 대상 공급자 수: {len(providers)}")  # print 추가
            logger.info(f"가격 조회 대상 공급자 수: {len(providers)}")
            
            for provider in providers:
                print(f"🔍 공급자 {safe_get_value(provider, 'id')} 가격 조회 중...")  # print 추가
                logger.info(f"공급자 {safe_get_value(provider, 'id')} 가격 조회 중...")
                
                # 최신 가격 정보 조회
                stmt = select(ExternalEnergyPriceHistory).where(
                    ExternalEnergyPriceHistory.provider_id == provider.id
                ).order_by(desc(ExternalEnergyPriceHistory.recorded_at)).limit(1)
                
                logger.info(f"가격 히스토리 쿼리: {stmt}")
                result = await session.execute(stmt)
                latest_price = result.scalar_one_or_none()
                
                print(f"💰 공급자 {safe_get_value(provider, 'id')} 최신 가격 정보: {latest_price}")  # print 추가
                logger.info(f"공급자 {safe_get_value(provider, 'id')} 최신 가격 정보: {latest_price}")
                
                if latest_price:
                    # 안전한 값 추출
                    provider_type_value = safe_get_value(provider, 'provider_type', '')
                    logger.info(f"provider_type_value: {provider_type_value}, type: {type(provider_type_value)}")
                    
                    try:
                        # Enum인 경우 .value 속성 사용 (동적 처리)
                        if hasattr(provider_type_value, 'value') and provider_type_value.__class__.__name__ != 'str':
                            provider_type_value = getattr(provider_type_value, 'value')  # type: ignore
                            logger.info(f"Enum value 추출: {provider_type_value}")
                    except Exception as e:
                        logger.warning(f"Enum value 추출 실패: {e}")
                        pass
                    
                    price_value = safe_get_value(latest_price, 'price_per_energy', 0)
                    logger.info(f"price_value: {price_value}, type: {type(price_value)}")
                    
                    try:
                        price_value = float(price_value)
                        logger.info(f"price_value float 변환: {price_value}")
                    except Exception as e:
                        logger.warning(f"가격 float 변환 실패: {e}")
                        price_value = 0.0
                    
                    recorded_at_value = safe_get_value(latest_price, 'recorded_at', None)
                    logger.info(f"recorded_at_value: {recorded_at_value}, type: {type(recorded_at_value)}")
                    
                    try:
                        if recorded_at_value and hasattr(recorded_at_value, 'isoformat'):
                            recorded_at_value = recorded_at_value.isoformat()
                            logger.info(f"recorded_at ISO 변환: {recorded_at_value}")
                    except Exception as e:
                        logger.warning(f"날짜 ISO 변환 실패: {e}")
                        recorded_at_value = None
                    
                    price_data = {
                        'provider_id': safe_get_value(provider, 'id', 0),
                        'provider_name': safe_get_value(provider, 'name', ''),
                        'provider_type': str(provider_type_value),
                        'price_per_energy': price_value,
                        'available_amount': safe_get_value(latest_price, 'available_amount', 0),
                        'min_order': safe_get_value(latest_price, 'min_order', 0),
                        'max_order': safe_get_value(latest_price, 'max_order', 0),
                        'recorded_at': recorded_at_value
                    }
                    
                    print(f"✅ 생성된 가격 데이터: {price_data}")  # print 추가
                    logger.info(f"생성된 가격 데이터: {price_data}")
                    prices.append(price_data)
                else:
                    print(f"⚠️ 공급자 {safe_get_value(provider, 'id')} 가격 정보 없음")  # print 추가
                    logger.warning(f"공급자 {safe_get_value(provider, 'id')} 가격 정보 없음")
            
            print(f"🎯 최종 가격 목록: {prices}")  # print 추가
            print(f"📋 가격 목록 길이: {len(prices)}")  # print 추가
            logger.info(f"최종 가격 목록: {prices}")
            logger.info(f"가격 목록 길이: {len(prices)}")
            return prices
        except Exception as e:
            print(f"❌ 서비스: 가격 정보 조회 오류: {e}")  # print 추가
            logger.error(f"가격 정보 조회 오류: {e}")
            import traceback
            logger.error(f"스택 트레이스: {traceback.format_exc()}")
            print(f"📋 서비스: 스택 트레이스: {traceback.format_exc()}")  # print 추가
            return []
    
    async def execute_purchase(
        self,
        provider_type: EnergyProviderType,
        energy_amount: int,
        session: AsyncSession,
        purchase_type: str = "manual"
    ) -> Optional[ExternalEnergyPurchase]:
        """에너지 구매 실행"""
        try:
            # 공급자 조회
            stmt = select(ExternalEnergyProvider).where(
                and_(
                    ExternalEnergyProvider.provider_type == provider_type,
                    ExternalEnergyProvider.is_active == True
                )
            )
            
            result = await session.execute(stmt)
            provider = result.scalar_one_or_none()
            
            if not provider:
                logger.error(f"공급자를 찾을 수 없습니다: {provider_type}")
                return None
            
            # 구매 기록 생성
            purchase = await self._create_purchase_record(
                provider, energy_amount, purchase_type, session
            )
            
            # 구매 실행 (시뮬레이션)
            await self._simulate_purchase(purchase, session)
            
            return purchase
            
        except Exception as e:
            logger.error(f"구매 실행 오류: {e}")
            return None
    
    async def _create_purchase_record(
        self,
        provider: ExternalEnergyProvider,
        energy_amount: int,
        purchase_type: str,
        session: AsyncSession
    ) -> ExternalEnergyPurchase:
        """구매 기록 생성"""
        try:
            # 현재 가격 조회
            stmt = select(ExternalEnergyPriceHistory).where(
                ExternalEnergyPriceHistory.provider_id == provider.id
            ).order_by(desc(ExternalEnergyPriceHistory.recorded_at)).limit(1)
            
            result = await session.execute(stmt)
            latest_price = result.scalar_one_or_none()
            
            if not latest_price:
                # 기본 가격 사용
                price_per_energy = Decimal("0.001")
            else:
                price_per_energy = latest_price.price_per_energy
            
            total_cost = price_per_energy * energy_amount
            
            # 구매 기록 생성
            purchase = ExternalEnergyPurchase(
                provider_id=provider.id,
                energy_amount=energy_amount,
                price_per_energy=price_per_energy,
                total_cost=total_cost,
                payment_currency="TRX",
                status=PurchaseStatus.PENDING,
                purchase_type=purchase_type,
                trigger_reason=f"auto_purchase_{datetime.utcnow().isoformat()}"
            )
            
            session.add(purchase)
            await session.commit()
            await session.refresh(purchase)
            
            return purchase
            
        except Exception as e:
            logger.error(f"구매 기록 생성 오류: {e}")
            await session.rollback()
            raise
    
    async def _simulate_purchase(self, purchase: ExternalEnergyPurchase, session: AsyncSession):
        """구매 시뮬레이션"""
        try:
            # 구매 실행 시뮬레이션
            await asyncio.sleep(1)
            
            # 구매 완료 업데이트 (안전한 값 추출)
            purchase_id = safe_get_value(purchase, 'id', 0)
            energy_amount = safe_get_value(purchase, 'energy_amount', 0)
            price_per_energy = safe_get_value(purchase, 'price_per_energy', Decimal('0'))
            margin_rate = safe_get_value(purchase, 'margin_rate', Decimal('0.2'))
            
            # 안전한 속성 업데이트
            setattr(purchase, 'status', PurchaseStatus.COMPLETED)
            setattr(purchase, 'transaction_hash', f"mock_tx_{purchase_id}_{datetime.utcnow().timestamp()}")
            setattr(purchase, 'energy_received_at', datetime.utcnow())
            setattr(purchase, 'actual_energy_received', energy_amount)
            setattr(purchase, 'completed_at', datetime.utcnow())
            
            # 마진 계산
            margin = price_per_energy * margin_rate
            setattr(purchase, 'resale_price', price_per_energy + margin)
            
            await session.commit()
            
            logger.info(f"에너지 구매 시뮬레이션 완료: {energy_amount} 에너지")
            
        except Exception as e:
            logger.error(f"구매 시뮬레이션 오류: {e}")
            setattr(purchase, 'status', PurchaseStatus.FAILED)
            await session.commit()
            raise
    
    async def get_purchase_history(
        self,
        session: AsyncSession,
        provider_id: Optional[int] = None,
        limit: int = 100
    ) -> List[ExternalEnergyPurchase]:
        """구매 히스토리 조회"""
        try:
            logger.info(f"=== get_purchase_history 시작 ===")
            logger.info(f"provider_id: {provider_id}, limit: {limit}")
            
            stmt = select(ExternalEnergyPurchase).options(
                selectinload(ExternalEnergyPurchase.provider)
            )
            
            if provider_id:
                stmt = stmt.where(ExternalEnergyPurchase.provider_id == provider_id)
                logger.info(f"특정 공급자 필터링: {provider_id}")
            
            stmt = stmt.order_by(desc(ExternalEnergyPurchase.created_at)).limit(limit)
            logger.info(f"구매 히스토리 쿼리: {stmt}")
            
            result = await session.execute(stmt)
            purchases = list(result.scalars().all())
            
            logger.info(f"조회된 구매 히스토리 수: {len(purchases)}")
            for purchase in purchases:
                logger.info(f"구매 기록: id={safe_get_value(purchase, 'id')}, energy_amount={safe_get_value(purchase, 'energy_amount')}, status={safe_get_value(purchase, 'status')}")
            
            return purchases
            
        except Exception as e:
            logger.error(f"구매 히스토리 조회 오류: {e}")
            import traceback
            logger.error(f"스택 트레이스: {traceback.format_exc()}")
            return []
    
    async def update_provider_stats(self, session: AsyncSession):
        """공급자 통계 업데이트"""
        try:
            providers = await self.get_all_providers(session)
            
            for provider in providers:
                # 성공률 계산
                stmt = select(ExternalEnergyPurchase).where(
                    ExternalEnergyPurchase.provider_id == provider.id
                )
                
                result = await session.execute(stmt)
                all_purchases = result.scalars().all()
                
                if all_purchases:
                    successful_purchases = [
                        p for p in all_purchases 
                        if safe_get_value(p, 'status') == PurchaseStatus.COMPLETED
                    ]
                    
                    success_rate = (len(successful_purchases) / len(all_purchases)) * 100
                    
                    # 안전한 속성 업데이트
                    setattr(provider, 'success_rate', Decimal(str(success_rate)))
                    setattr(provider, 'total_purchases', len(all_purchases))
                    setattr(provider, 'total_energy_purchased', sum(
                        safe_get_value(p, 'energy_amount', 0) for p in successful_purchases
                    ))
            
            await session.commit()
            
        except Exception as e:
            logger.error(f"공급자 통계 업데이트 오류: {e}")
            await session.rollback()


# 전역 서비스 인스턴스
external_energy_service = ExternalEnergyService()
