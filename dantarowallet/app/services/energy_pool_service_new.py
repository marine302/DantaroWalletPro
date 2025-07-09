"""
에너지 풀 관리 서비스 - 모듈화된 버전

이 파일은 모듈화된 에너지 풀 서비스의 메인 진입점입니다.
실제 구현은 energy_pool 모듈에서 제공됩니다.
"""

# 모듈화된 서비스 import
from .energy_pool.energy_pool_service import EnergyPoolModelService
from .energy_pool.models import (
    EnergyPoolStatusInfo, EnergyTransaction, EnergyQueue, EnergyAlert,
    EnergyUsageStats, EnergyRechargeRequest, EnergyQueueCreate,
    EmergencyWithdrawalCreate, EmergencyWithdrawalResponse, QueueStatus
)

# 하위 호환성을 위한 노출
__all__ = [
    "EnergyPoolModelService",
    "EnergyPoolStatusInfo",
    "EnergyTransaction", 
    "EnergyQueue",
    "EnergyAlert",
    "EnergyUsageStats",
    "EnergyRechargeRequest",
    "EnergyQueueCreate",
    "EmergencyWithdrawalCreate",
    "EmergencyWithdrawalResponse",
    "QueueStatus"
]
