"""
입금 모니터링 서비스.
TRON 블록체인에서 입금 트랜잭션을 감지하고 처리합니다.
"""
from .deposit_monitoring.monitor_service import DepositMonitoringService

__all__ = ["DepositMonitoringService", "deposit_monitor"]

# 이 파일은 하위 모듈을 가져오는 역할만 합니다.
# 모든 구현은 deposit_monitoring/ 패키지 내부에 있습니다.

# 전역 모니터링 인스턴스
deposit_monitor = DepositMonitoringService()
