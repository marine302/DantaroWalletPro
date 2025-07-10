"""
에너지 풀 관리자 모듈
"""
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.energy_pool import EnergyPoolModel, EnergyPoolStatus
from app.core.logging import setup_logging

logger = setup_logging()


class EnergyPoolManager:
    """에너지 풀 관리자 클래스"""
    
    def __init__(self, db: AsyncSession, tron_client=None, redis_client=None):
        self.db = db
        self.tron_client = tron_client
        self.redis_client = redis_client
    
    async def create_energy_pool(
        self,
        pool_name: str,
        owner_private_key: str,
        initial_trx_amount: int = 1000
    ) -> EnergyPoolModel:
        """새로운 에너지 풀 생성"""
        try:
            # 테스트용 더미 주소 생성
            test_address = f"T{pool_name.replace(' ', '')[:20]}TestAddress"
            
            energy_pool = EnergyPoolModel(
                pool_name=pool_name,
                owner_address=test_address,
                total_energy=initial_trx_amount * 1000,  # 1 TRX = 1000 Energy 가정
                available_energy=initial_trx_amount * 1000,
                used_energy=0,
                frozen_trx=Decimal(str(initial_trx_amount)),
                status=EnergyPoolStatus.ACTIVE,
                warning_threshold=20,
                critical_threshold=10
            )
            
            self.db.add(energy_pool)
            await self.db.commit()
            await self.db.refresh(energy_pool)
            
            logger.info(f"✅ 에너지 풀 생성 완료: {pool_name}")
            return energy_pool
            
        except Exception as e:
            logger.error(f"❌ 에너지 풀 생성 실패: {e}")
            await self.db.rollback()
            raise
    
    async def check_pool_status(self, pool_id: int) -> Dict[str, Any]:
        """에너지 풀 상태 확인"""
        try:
            result = await self.db.execute(
                select(EnergyPoolModel).where(EnergyPoolModel.id == pool_id)
            )
            pool = result.scalar_one_or_none()
            
            if not pool:
                return {
                    "status": "not_found",
                    "message": "에너지 풀을 찾을 수 없습니다"
                }
            
            # 안전한 타입 변환
            total_energy = getattr(pool, 'total_energy', 0) or 0
            used_energy = getattr(pool, 'used_energy', 0) or 0
            available_energy = getattr(pool, 'available_energy', 0) or 0
            frozen_trx = float(getattr(pool, 'frozen_trx', 0) or 0)
            
            usage_percentage = (used_energy / total_energy * 100) if total_energy > 0 else 0
            
            status = "sufficient"
            if usage_percentage >= 90:
                status = "critical"
            elif usage_percentage >= 70:
                status = "warning"
            
            return {
                "id": pool.id,
                "name": pool.pool_name,
                "status": status,
                "total_energy": total_energy,
                "available_energy": available_energy,
                "used_energy": used_energy,
                "usage_percentage": usage_percentage,
                "frozen_trx": frozen_trx,
                "last_updated": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"❌ 에너지 풀 상태 확인 실패: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def get_pool_info(self, pool_id: int) -> Optional[EnergyPoolModel]:
        """에너지 풀 정보 조회"""
        try:
            result = await self.db.execute(
                select(EnergyPoolModel).where(EnergyPoolModel.id == pool_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ 에너지 풀 정보 조회 실패: {e}")
            return None