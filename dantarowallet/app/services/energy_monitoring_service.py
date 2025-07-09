"""
Doc #25: 에너지 풀 고급 관리 시스템 - 에너지 모니터링 서비스 (모듈화된 버전)
실시간 모니터링, 예측 분석, 알림 시스템, 패턴 분석

이 파일은 모듈화된 에너지 모니터링 서비스의 메인 진입점입니다.
실제 구현은 energy_monitoring 모듈에서 제공됩니다.
"""

# 모듈화된 서비스 import
from .energy_monitoring.energy_monitoring_service import EnergyMonitoringService
from .energy_monitoring.prediction_service import EnergyPredictionService

# 하위 호환성을 위한 노출
__all__ = [
    "EnergyMonitoringService",
    "EnergyPredictionService"
]
