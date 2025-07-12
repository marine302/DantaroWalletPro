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
    EnergyPriceHistory,
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
            stmt = select(ExternalEnergyProvider).options(
                selectinload(ExternalEnergyProvider.price_history)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"공급자 조회 오류: {e}")
            return []
    
    async def get_active_providers(self, session: AsyncSession) -> List[ExternalEnergyProvider]:
        """활성 공급자 조회"""
        try:
            stmt = select(ExternalEnergyProvider).where(
                ExternalEnergyProvider.is_active == True
            ).order_by(ExternalEnergyProvider.priority)
            
            result = await session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"활성 공급자 조회 오류: {e}")
            return []
    
    async def get_current_prices(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """현재 가격 정보 조회"""
        try:
            prices = []
            providers = await self.get_active_providers(session)
            
            for provider in providers:
                # 최신 가격 정보 조회
                stmt = select(EnergyPriceHistory).where(
                    EnergyPriceHistory.provider_id == provider.id
                ).order_by(desc(EnergyPriceHistory.recorded_at)).limit(1)
                
                result = await session.execute(stmt)
                latest_price = result.scalar_one_or_none()
                
                if latest_price:
                    prices.append({
                        'provider_id': provider.id,
                        'provider_name': provider.name,
                        'provider_type': provider.provider_type,
                        'price_per_energy': latest_price.price_per_energy,
                        'available_amount': latest_price.available_amount,
                        'min_order': latest_price.min_order,
                        'max_order': latest_price.max_order,
                        'recorded_at': latest_price.recorded_at
                    })
            
            return prices
        except Exception as e:
            logger.error(f"가격 정보 조회 오류: {e}")
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
            stmt = select(EnergyPriceHistory).where(
                EnergyPriceHistory.provider_id == provider.id
            ).order_by(desc(EnergyPriceHistory.recorded_at)).limit(1)
            
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
            stmt = select(ExternalEnergyPurchase).options(
                selectinload(ExternalEnergyPurchase.provider)
            )
            
            if provider_id:
                stmt = stmt.where(ExternalEnergyPurchase.provider_id == provider_id)
            
            stmt = stmt.order_by(desc(ExternalEnergyPurchase.created_at)).limit(limit)
            
            result = await session.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"구매 히스토리 조회 오류: {e}")
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
