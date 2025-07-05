"""
입금 모니터링 서비스 기본 클래스
"""
import asyncio
import logging
from typing import Optional

from app.core.tron import TronService

logger = logging.getLogger(__name__)


class BaseMonitorService:
    """입금 모니터링 서비스의 기본 클래스"""

    def __init__(self):
        self.tron = TronService()
        self.is_monitoring = False
        self.monitoring_interval = 30  # 30초마다 확인
        self.last_checked_block = None

    async def start_monitoring(self):
        """모니터링 시작"""
        if self.is_monitoring:
            logger.warning("모니터링이 이미 실행 중입니다")
            return

        self.is_monitoring = True
        logger.info("🔍 입금 모니터링 시작")

        try:
            while self.is_monitoring:
                await self._monitor_deposits()
                await asyncio.sleep(self.monitoring_interval)
        except Exception as e:
            logger.error(f"모니터링 중 오류 발생: {e}")
        finally:
            self.is_monitoring = False

    async def stop_monitoring(self):
        """모니터링 중지"""
        logger.info("입금 모니터링 중지")
        self.is_monitoring = False

    async def _monitor_deposits(self):
        """실제 모니터링 로직 - 자식 클래스에서 구현"""
        raise NotImplementedError("자식 클래스에서 구현해야 합니다")
