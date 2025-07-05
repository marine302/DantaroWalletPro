"""
트랜잭션 분석 및 모니터링 서비스 (리팩토링된 버전)
기존 대용량 서비스를 모듈화된 구조로 재구성
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.exceptions import NotFoundError, ValidationError
from app.models.transaction_analytics import (
    AlertLevel,
    AlertType,
    SystemAlert,
    TransactionAlert,
    TransactionSummary,
)
from app.schemas.transaction_analytics import (
    AlertRequest,
    AlertResponse,
    RealTimeTransactionMetrics,
    SuspiciousPatternAlert,
    TransactionAnalyticsFilter,
    TransactionAnalyticsResponse,
    TransactionMonitoringConfig,
    TransactionTrendAnalysis,
    UserTransactionProfile,
)
from app.services.transaction_analytics.alert_service import AlertService
from app.services.transaction_analytics.metrics_service import MetricsService
from app.services.transaction_analytics.pattern_service import (
    PatternDetectionService,
    VelocityCheckService,
)
from app.services.transaction_analytics.reporting_service import ReportingService

# 새로 분리된 서비스 모듈들 import
from app.services.transaction_analytics.statistics_service import StatisticsService
from app.services.transaction_analytics.utils import TransactionUtils
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class TransactionAnalyticsService:
    """
    트랜잭션 분석 서비스 (리팩토링된 메인 서비스)
    각 기능별로 분리된 서비스들을 조합하여 사용
    """

    def __init__(self):
        self.monitoring_config = TransactionMonitoringConfig()

        # 분리된 서비스들 초기화
        self.statistics_service = StatisticsService()
        self.metrics_service = MetricsService()
        self.alert_service = AlertService()
        self.pattern_service = PatternDetectionService(self.monitoring_config)
        self.velocity_service = VelocityCheckService(self.monitoring_config)
        self.reporting_service = ReportingService()
        self.utils = TransactionUtils()

    # ====================
    # 메인 분석 API
    # ====================

    async def get_transaction_analytics(
        self, db: AsyncSession, filters: TransactionAnalyticsFilter
    ) -> TransactionAnalyticsResponse:
        """트랜잭션 분석 데이터 조회 (통계 서비스 위임)"""
        try:
            return await self.statistics_service.get_comprehensive_analytics(
                db, filters
            )
        except Exception as e:
            logger.error(f"트랜잭션 분석 조회 중 오류: {str(e)}")
            raise ValidationError(f"트랜잭션 분석을 조회할 수 없습니다: {str(e)}")

    async def get_real_time_metrics(
        self, db: AsyncSession, time_window_minutes: int = 60
    ) -> RealTimeTransactionMetrics:
        """실시간 메트릭 조회 (메트릭 서비스 위임)"""
        try:
            return await self.metrics_service.get_real_time_metrics(
                db, time_window_minutes
            )
        except Exception as e:
            logger.error(f"실시간 메트릭 조회 중 오류: {str(e)}")
            raise ValidationError(f"실시간 메트릭을 조회할 수 없습니다: {str(e)}")

    # ====================
    # 패턴 감지 및 보안
    # ====================

    async def detect_suspicious_patterns(
        self, db: AsyncSession, user_id: Optional[int] = None, hours_back: int = 24
    ) -> List[SuspiciousPatternAlert]:
        """의심스러운 패턴 감지 (패턴 서비스 위임)"""
        return await self.pattern_service.detect_suspicious_patterns(
            db, user_id, hours_back
        )

    async def check_transaction_velocity(
        self, db: AsyncSession, user_id: int, amount: float, asset: str
    ) -> dict:
        """거래 속도 체크 (속도 체크 서비스 위임)"""
        return await self.velocity_service.check_transaction_velocity(
            db, user_id, amount, asset
        )

    # ====================
    # 알림 관리
    # ====================

    async def create_alert(
        self, db: AsyncSession, alert_data: AlertRequest
    ) -> AlertResponse:
        """알림 생성 (알림 서비스 위임)"""
        try:
            return await self.alert_service.create_alert(db, alert_data)
        except Exception as e:
            logger.error(f"알림 생성 중 오류: {str(e)}")
            raise ValidationError(f"알림을 생성할 수 없습니다: {str(e)}")

    async def get_alerts(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        level: Optional[AlertLevel] = None,
        alert_type: Optional[AlertType] = None,
        is_resolved: Optional[bool] = None,
        limit: int = 50,
    ) -> List[AlertResponse]:
        """알림 목록 조회 (알림 서비스 위임)"""
        try:
            return await self.alert_service.get_alerts(
                db, user_id, level, alert_type, is_resolved, limit
            )
        except Exception as e:
            logger.error(f"알림 조회 중 오류: {str(e)}")
            raise ValidationError(f"알림을 조회할 수 없습니다: {str(e)}")

    async def resolve_alert(
        self,
        db: AsyncSession,
        alert_id: int,
        resolved_by: int,
        resolution_note: Optional[str] = None,
    ) -> AlertResponse:
        """알림 해결 처리 (알림 서비스 위임)"""
        try:
            return await self.alert_service.resolve_alert(
                db, alert_id, resolved_by, resolution_note
            )
        except Exception as e:
            logger.error(f"알림 해결 처리 중 오류: {str(e)}")
            raise ValidationError(f"알림을 해결할 수 없습니다: {str(e)}")

    # ====================
    # 보고서 생성
    # ====================

    async def generate_trend_analysis(
        self, db: AsyncSession, filters: TransactionAnalyticsFilter, days_back: int = 30
    ) -> TransactionTrendAnalysis:
        """트랜드 분석 보고서 생성 (보고서 서비스 위임)"""
        try:
            return await self.reporting_service.generate_trend_analysis(
                db, filters, days_back
            )
        except Exception as e:
            logger.error(f"트랜드 분석 생성 중 오류: {str(e)}")
            raise ValidationError(f"트랜드 분석을 생성할 수 없습니다: {str(e)}")

    async def get_user_transaction_profile(
        self, db: AsyncSession, user_id: int, days_back: int = 90
    ) -> UserTransactionProfile:
        """사용자 거래 프로필 조회 (보고서 서비스 위임)"""
        try:
            return await self.reporting_service.generate_user_profile(
                db, user_id, days_back
            )
        except Exception as e:
            logger.error(f"사용자 프로필 생성 중 오류: {str(e)}")
            raise ValidationError(f"사용자 프로필을 생성할 수 없습니다: {str(e)}")

    # ====================
    # 시스템 모니터링
    # ====================

    async def monitor_system_health(self, db: AsyncSession) -> Dict[str, Any]:
        """시스템 건강성 모니터링"""
        try:
            # 여러 서비스의 건강성 체크 결과 통합
            health_data = {}

            # 메트릭 서비스 건강성
            health_data["metrics"] = await self.metrics_service.get_health_check(db)

            # 알림 서비스 건강성
            health_data["alerts"] = await self.alert_service.get_health_check(db)

            # 전체 시스템 상태 계산
            all_healthy = all(
                service_health.get("status") == "healthy"
                for service_health in health_data.values()
            )

            health_data["overall_status"] = "healthy" if all_healthy else "degraded"
            health_data["checked_at"] = datetime.utcnow()

            return health_data

        except Exception as e:
            logger.error(f"시스템 건강성 체크 중 오류: {str(e)}")
            return {
                "overall_status": "error",
                "error": str(e),
                "checked_at": datetime.utcnow(),
            }

    # ====================
    # 자동화된 모니터링
    # ====================

    async def run_automated_monitoring(self, db: AsyncSession) -> Dict[str, Any]:
        """자동화된 모니터링 실행"""
        try:
            results = {
                "timestamp": datetime.utcnow(),
                "checks_performed": [],
                "alerts_generated": [],
                "errors": [],
            }

            # 1. 의심스러운 패턴 감지
            try:
                suspicious_patterns = await self.detect_suspicious_patterns(
                    db, hours_back=1
                )
                results["checks_performed"].append("suspicious_pattern_detection")

                # 심각한 패턴에 대해 알림 생성
                for pattern in suspicious_patterns:
                    if pattern.confidence_score > 0.8:
                        alert_request = AlertRequest(
                            level=AlertLevel.HIGH,
                            type=AlertType.SECURITY,
                            title=f"의심스러운 패턴 감지: {pattern.pattern_type}",
                            message=f"신뢰도: {pattern.confidence_score:.2f}",
                            metadata=pattern.details,
                        )
                        alert = await self.create_alert(db, alert_request)
                        results["alerts_generated"].append(alert.id)

            except Exception as e:
                results["errors"].append(f"패턴 감지 오류: {str(e)}")

            # 2. 시스템 건강성 체크
            try:
                health = await self.monitor_system_health(db)
                results["checks_performed"].append("system_health_check")

                if health["overall_status"] != "healthy":
                    alert_request = AlertRequest(
                        level=AlertLevel.MEDIUM,
                        type=AlertType.SYSTEM,
                        title="시스템 건강성 경고",
                        message=f"상태: {health['overall_status']}",
                        metadata=health,
                    )
                    alert = await self.create_alert(db, alert_request)
                    results["alerts_generated"].append(alert.id)

            except Exception as e:
                results["errors"].append(f"건강성 체크 오류: {str(e)}")

            # 3. 실시간 메트릭 임계값 체크
            try:
                metrics = await self.get_real_time_metrics(db, 60)
                results["checks_performed"].append("metrics_threshold_check")

                # 트랜잭션 볼륨 급증 체크
                if hasattr(metrics, "current_tps") and metrics.current_tps > 100:
                    alert_request = AlertRequest(
                        level=AlertLevel.MEDIUM,
                        type=AlertType.PERFORMANCE,
                        title="높은 TPS 감지",
                        message=f"현재 TPS: {metrics.current_tps}",
                        metadata={"current_tps": metrics.current_tps},
                    )
                    alert = await self.create_alert(db, alert_request)
                    results["alerts_generated"].append(alert.id)

            except Exception as e:
                results["errors"].append(f"메트릭 체크 오류: {str(e)}")

            return results

        except Exception as e:
            logger.error(f"자동화된 모니터링 실행 중 오류: {str(e)}")
            return {"timestamp": datetime.utcnow(), "status": "error", "error": str(e)}

    # ====================
    # 설정 관리
    # ====================

    def update_monitoring_config(
        self, config_updates: Dict[str, Any]
    ) -> TransactionMonitoringConfig:
        """모니터링 설정 업데이트"""
        for key, value in config_updates.items():
            if hasattr(self.monitoring_config, key):
                setattr(self.monitoring_config, key, value)

        return self.monitoring_config

    def get_monitoring_config(self) -> TransactionMonitoringConfig:
        """현재 모니터링 설정 조회"""
        return self.monitoring_config


# ====================
# 백워드 호환성을 위한 래퍼 함수들
# ====================


# 기존 코드가 직접 호출하던 메서드들의 호환성 보장
async def get_transaction_analytics_legacy(
    db: AsyncSession, filters: TransactionAnalyticsFilter
) -> TransactionAnalyticsResponse:
    """레거시 호환용 래퍼 함수"""
    service = TransactionAnalyticsService()
    return await service.get_transaction_analytics(db, filters)


async def detect_suspicious_patterns_legacy(
    db: AsyncSession, user_id: Optional[int] = None, hours_back: int = 24
) -> List[SuspiciousPatternAlert]:
    """레거시 호환용 래퍼 함수"""
    service = TransactionAnalyticsService()
    return await service.detect_suspicious_patterns(db, user_id, hours_back)
