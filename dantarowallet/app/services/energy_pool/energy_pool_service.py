"""에너지 풀 서비스 - 메인 서비스"""

import decimal
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import EnergyInsufficientError, ValidationError
from app.core.logger import get_logger
from app.models.energy_pool import (
    EnergyAlertType,
    EnergyPoolModel,
    EnergyPoolStatus,
    EnergyPriceHistory,
    EnergyStatus,
    EnergyUsageLog,
    PartnerEnergyPool,
    PartnerEnergyUsageLog,
)
from app.models.user import User
from app.schemas.energy import (
    AutoManagementSettings,
    CreateEnergyPoolRequest,
    EnergyAlertResponse,
    EnergyPoolResponse,
    EnergyPoolStatusResponse,
    EnergyPriceHistoryResponse,
    EnergySimulationRequest,
    EnergySimulationResponse,
    EnergyUsageLogResponse,
    EnergyUsageStatsResponse,
    MessageResponse,
)

from .pool_manager import EnergyPoolManager
from .queue_manager import EnergyQueueManager
from .usage_analyzer import EnergyUsageAnalyzer
from .utils import safe_decimal, safe_get_attr, safe_int

logger = get_logger(__name__)


class EnergyPoolService:
    """에너지 풀 관리 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.pool_manager = EnergyPoolManager(db)
        self.usage_analyzer = EnergyUsageAnalyzer(db)
        self.queue_manager = EnergyQueueManager(db)

    async def get_energy_status(self):
        """현재 에너지 풀 상태를 조회합니다."""
        return await self.pool_manager.get_energy_status()

    async def create_energy_pool(self, request: CreateEnergyPoolRequest):
        """새로운 에너지 풀을 생성합니다."""
        return await self.pool_manager.create_energy_pool(request)

    async def recharge_energy(self, amount: int, user_id: int):
        """에너지를 충전합니다."""
        return await self.pool_manager.recharge_energy(amount, user_id)

    async def use_energy(self, amount: int, user_id: int, transaction_hash: str):
        """에너지를 사용합니다."""
        return await self.pool_manager.use_energy(amount, user_id, transaction_hash)

    async def get_usage_stats(self, start_date: datetime, end_date: datetime):
        """사용량 통계를 조회합니다."""
        return await self.usage_analyzer.get_usage_stats(start_date, end_date)

    async def get_usage_logs(self, user_id: Optional[int] = None):
        """사용량 로그를 조회합니다."""
        return await self.usage_analyzer.get_usage_logs(user_id)

    async def add_to_queue(self, user_id: int, energy_amount: int):
        """대기열에 추가합니다."""
        return await self.queue_manager.add_to_queue(user_id, energy_amount)

    async def process_queue(self):
        """대기열을 처리합니다."""
        return await self.queue_manager.process_queue()

    async def optimize_queue(self):
        """대기열을 최적화합니다."""
        return await self.queue_manager.optimize_queue()
