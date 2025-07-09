"""
에너지 풀 서비스 - 데이터 클래스 및 모델 정의
"""
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal


class EnergyPoolStatusInfo:
    """에너지 풀 상태 정보"""
    def __init__(self, total_energy: int, available_energy: int, reserved_energy: int, 
                 daily_consumption: int, usage_rate: float, efficiency: float,
                 alert_threshold: int, critical_threshold: int):
        self.total_energy = total_energy
        self.available_energy = available_energy
        self.reserved_energy = reserved_energy
        self.daily_consumption = daily_consumption
        self.usage_rate = usage_rate
        self.efficiency = efficiency
        self.alert_threshold = alert_threshold
        self.critical_threshold = critical_threshold


class EnergyTransaction:
    """에너지 트랜잭션 클래스"""
    def __init__(self, user_id: int, energy_amount: int, transaction_type: str, 
                 transaction_id: str, created_at: Optional[datetime] = None):
        self.id: Optional[int] = None
        self.user_id = user_id
        self.energy_amount = energy_amount
        self.transaction_type = transaction_type
        self.transaction_id = transaction_id
        self.created_at = created_at or datetime.utcnow()


class EnergyQueue:
    """에너지 대기열 클래스"""
    def __init__(self, user_id: int, estimated_energy: int, transaction_type: str, 
                 priority: int = 1, status: str = "pending", created_at: Optional[datetime] = None):
        self.id: Optional[int] = None
        self.user_id = user_id
        self.estimated_energy = estimated_energy
        self.transaction_type = transaction_type
        self.priority = priority
        self.status = status
        self.created_at = created_at or datetime.utcnow()


class EnergyAlert:
    """에너지 알림 클래스"""
    def __init__(self, alert_type: str, message: str, is_active: bool = True, 
                 created_at: Optional[datetime] = None):
        self.id: Optional[int] = None
        self.alert_type = alert_type
        self.message = message
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()


class QueueStatus:
    """대기열 상태 클래스"""
    def __init__(self, position: int, estimated_wait_time: int, queue_size: int):
        self.position = position
        self.estimated_wait_time = estimated_wait_time
        self.queue_size = queue_size


class EnergyUsageStats:
    """에너지 사용 통계 클래스"""
    def __init__(self, daily_usage: int, transaction_count: int, efficiency_score: float, 
                 peak_hour: int, cost_breakdown: Dict[str, float]):
        self.daily_usage = daily_usage
        self.transaction_count = transaction_count
        self.efficiency_score = efficiency_score
        self.peak_hour = peak_hour
        self.cost_breakdown = cost_breakdown


class EnergyRechargeRequest:
    """에너지 충전 요청 클래스"""
    def __init__(self, amount: int, payment_method: str = "trx", reason: str = ""):
        self.amount = amount
        self.payment_method = payment_method
        self.reason = reason


class EnergyQueueCreate:
    """에너지 대기열 생성 클래스"""
    def __init__(self, estimated_energy: int, transaction_type: str, priority: int = 1):
        self.estimated_energy = estimated_energy
        self.transaction_type = transaction_type
        self.priority = priority


class EmergencyWithdrawalCreate:
    """긴급 출금 생성 클래스"""
    def __init__(self, amount: Decimal, reason: str):
        self.amount = amount
        self.reason = reason


class EmergencyWithdrawalResponse:
    """긴급 출금 응답 클래스"""
    def __init__(self, success: bool, transaction_id: str, message: str):
        self.success = success
        self.transaction_id = transaction_id
        self.message = message
