"""
슈퍼 어드민용 시스템 모니터링 서비스
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import PartnerApiLog
from app.models.fee_config import FeeConfig
from app.models.partner import Partner
from app.schemas.monitoring import (
    Alert,
    PartnerRanking,
    PerformanceReport,
    SystemHealth,
    SystemMetrics,
)


class SystemMonitorService:
    """시스템 모니터링 서비스"""

    def __init__(self, db: Session):
        self.db = db

    async def collect_system_metrics(self) -> SystemMetrics:
        """시스템 메트릭 수집"""
        try:
            # 파트너 통계
            total_partners = self.db.query(Partner).count()
            active_partners = (
                self.db.query(Partner).filter(Partner.status == "active").count()
            )
            pending_partners = (
                self.db.query(Partner).filter(Partner.status == "pending").count()
            )
            suspended_partners = (
                self.db.query(Partner).filter(Partner.status == "suspended").count()
            )

            # API 호출 통계 (최근 24시간)
            yesterday = datetime.utcnow() - timedelta(hours=24)
            total_api_calls = (
                self.db.query(PartnerApiLog)
                .filter(PartnerApiLog.created_at >= yesterday)
                .count()
            )

            successful_calls = (
                self.db.query(PartnerApiLog)
                .filter(
                    and_(
                        PartnerApiLog.created_at >= yesterday,
                        PartnerApiLog.status_code.between(200, 299),
                    )
                )
                .count()
            )

            error_rate = (
                ((total_api_calls - successful_calls) / total_api_calls * 100)
                if total_api_calls > 0
                else 0
            )

            # 평균 응답시간
            avg_response_time = (
                self.db.query(func.avg(PartnerApiLog.response_time_ms))
                .filter(PartnerApiLog.created_at >= yesterday)
                .scalar()
                or 0
            )

            return SystemMetrics(
                timestamp=datetime.utcnow(),
                total_partners=total_partners,
                active_partners=active_partners,
                pending_partners=pending_partners,
                suspended_partners=suspended_partners,
                total_api_calls=total_api_calls,
                successful_api_calls=successful_calls,
                api_error_rate=error_rate,
                avg_response_time=avg_response_time,
                system_load=0.0,  # 실제 시스템 로드 측정 필요
                memory_usage=0.0,  # 실제 메모리 사용량 측정 필요
                disk_usage=0.0,  # 실제 디스크 사용량 측정 필요
            )

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to collect system metrics: {str(e)}"
            )

    async def check_partner_health(self, partner_id: str) -> Dict[str, Any]:
        """파트너 헬스 체크"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")

            # 최근 24시간 API 호출 통계
            yesterday = datetime.utcnow() - timedelta(hours=24)

            total_calls = (
                self.db.query(PartnerApiLog)
                .filter(
                    and_(
                        PartnerApiLog.partner_id == partner_id,
                        PartnerApiLog.created_at >= yesterday,
                    )
                )
                .count()
            )

            successful_calls = (
                self.db.query(PartnerApiLog)
                .filter(
                    and_(
                        PartnerApiLog.partner_id == partner_id,
                        PartnerApiLog.created_at >= yesterday,
                        PartnerApiLog.status_code.between(200, 299),
                    )
                )
                .count()
            )

            error_calls = total_calls - successful_calls
            error_rate = (error_calls / total_calls * 100) if total_calls > 0 else 0

            # 평균 응답시간
            avg_response_time = (
                self.db.query(func.avg(PartnerApiLog.response_time_ms))
                .filter(
                    and_(
                        PartnerApiLog.partner_id == partner_id,
                        PartnerApiLog.created_at >= yesterday,
                    )
                )
                .scalar()
                or 0
            )

            # 전체 헬스 점수 계산
            health_score = 100

            # 에러율 패널티
            if error_rate > 10:
                health_score -= 30
            elif error_rate > 5:
                health_score -= 15

            # 응답시간 패널티
            if avg_response_time > 5000:  # 5초 이상
                health_score -= 20
            elif avg_response_time > 2000:  # 2초 이상
                health_score -= 10

            # 에너지 상태 패널티
                health_score -= 25
                health_score -= 10

            # 상태 판정
            if health_score >= 90:
                status = "excellent"
            elif health_score >= 70:
                status = "good"
            elif health_score >= 50:
                status = "warning"
            else:
                status = "critical"

            return {
                "partner_id": partner_id,
                "partner_name": partner.name,
                "status": status,
                "health_score": max(0, health_score),
                "api_stats": {
                    "total_calls": total_calls,
                    "successful_calls": successful_calls,
                    "error_calls": error_calls,
                    "error_rate": error_rate,
                    "avg_response_time": avg_response_time,
                },
                "last_activity": partner.last_activity_at,
                "checked_at": datetime.utcnow(),
            }

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to check partner health: {str(e)}"
            )

    async def send_alert_notifications(self, alert: Alert) -> bool:
        """알림 전송"""
        try:
            # 실제 구현에서는 이메일, 슬랙, SMS 등으로 알림 전송
            # 여기서는 로깅만 구현

            alert_data = {
                "id": str(uuid.uuid4()),
                "type": alert.alert_type,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "partner_id": getattr(alert, "partner_id", None),
                "created_at": datetime.utcnow(),
                "sent_at": datetime.utcnow(),
            }

            # 알림 로그 저장 (실제 구현에서는 alert 테이블에 저장)
            print(f"Alert sent: {alert_data}")

            return True

        except Exception as e:
            print(f"Failed to send alert: {str(e)}")
            return False

    async def generate_performance_report(
        self, start_date: datetime, end_date: datetime
    ) -> PerformanceReport:
        """성능 보고서 생성"""
        try:
            # 기간 내 파트너 성능 통계
            partner_stats = (
                self.db.query(
                    Partner.id,
                    Partner.name,
                    func.count(PartnerApiLog.id).label("total_calls"),
                    func.avg(PartnerApiLog.response_time_ms).label("avg_response_time"),
                    func.sum(
                        func.case(
                            (PartnerApiLog.status_code.between(200, 299), 1), else_=0
                        )
                    ).label("successful_calls"),
                )
                .outerjoin(
                    PartnerApiLog,
                    and_(
                        Partner.id == PartnerApiLog.partner_id,
                        PartnerApiLog.created_at.between(start_date, end_date),
                    ),
                )
                .group_by(Partner.id, Partner.name)
                .all()
            )

            # 전체 시스템 통계
            total_api_calls = sum(stat.total_calls or 0 for stat in partner_stats)
            total_successful = sum(stat.successful_calls or 0 for stat in partner_stats)
            overall_success_rate = (
                (total_successful / total_api_calls * 100) if total_api_calls > 0 else 0
            )

            # 평균 응답시간
            avg_response_times = [
                stat.avg_response_time
                for stat in partner_stats
                if stat.avg_response_time
            ]
            overall_avg_response_time = (
                sum(avg_response_times) / len(avg_response_times)
                if avg_response_times
                else 0
            )

            # 파트너별 순위
            partner_performance = []
            for stat in partner_stats:
                error_rate = 0
                if stat.total_calls and stat.total_calls > 0:
                    error_rate = (
                        (stat.total_calls - (stat.successful_calls or 0))
                        / stat.total_calls
                    ) * 100

                partner_performance.append(
                    {
                        "partner_id": stat.id,
                        "partner_name": stat.name,
                        "total_calls": stat.total_calls or 0,
                        "success_rate": 100 - error_rate,
                        "avg_response_time": stat.avg_response_time or 0,
                        "performance_score": max(
                            0, 100 - error_rate - (stat.avg_response_time or 0) / 100
                        ),
                    }
                )

            # 성능 점수로 정렬
            partner_performance.sort(key=lambda x: x["performance_score"], reverse=True)

            return PerformanceReport(
                report_id=str(uuid.uuid4()),
                period_start=start_date,
                period_end=end_date,
                total_api_calls=total_api_calls,
                overall_success_rate=overall_success_rate,
                overall_avg_response_time=overall_avg_response_time,
                total_partners=len(partner_stats),
                partner_performance=partner_performance,
                system_uptime=99.9,  # 실제 계산 필요
                generated_at=datetime.utcnow(),
            )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate performance report: {str(e)}",
            )

    async def get_system_alerts(self, severity: Optional[str] = None) -> List[Alert]:
        """시스템 알림 조회"""
        try:
            alerts = []

            # API 오류율 높은 파트너
            yesterday = datetime.utcnow() - timedelta(hours=24)
            high_error_partners = (
                self.db.query(
                    PartnerApiLog.partner_id,
                    func.count(PartnerApiLog.id).label("total_calls"),
                    func.sum(
                        func.case((PartnerApiLog.status_code >= 400, 1), else_=0)
                    ).label("error_calls"),
                )
                .filter(PartnerApiLog.created_at >= yesterday)
                .group_by(PartnerApiLog.partner_id)
                .having(
                    and_(
                        func.count(PartnerApiLog.id) > 10,  # 최소 호출 수
                        (
                            func.sum(
                                func.case(
                                    (PartnerApiLog.status_code >= 400, 1), else_=0
                                )
                            )
                            / func.count(PartnerApiLog.id)
                        )
                        > 0.1,  # 10% 이상 에러율
                    )
                )
                .all()
            )

            for partner_stat in high_error_partners:
                error_rate = (partner_stat.error_calls / partner_stat.total_calls) * 100
                partner = (
                    self.db.query(Partner)
                    .filter(Partner.id == partner_stat.partner_id)
                    .first()
                )

                if partner:
                    severity_level = "critical" if error_rate > 50 else "warning"
                    alerts.append(
                        Alert(
                            alert_type="high_error_rate",
                            severity=severity_level,
                            title=f"High Error Rate - {partner.name}",
                            message=f"Partner {partner.name} has {error_rate:.1f}% error rate",
                            partner_id=str(partner.id),
                            created_at=datetime.utcnow(),
                        )
                    )

            # 필터 적용
            if severity:
                alerts = [alert for alert in alerts if alert.severity == severity]

            return alerts

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to get system alerts: {str(e)}"
            )

    async def get_partner_rankings(
        self, metric: str = "performance"
    ) -> List[PartnerRanking]:
        """파트너 순위 조회"""
        try:
            # 최근 30일 기준
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)

            if metric == "performance":
                # 성능 기준 순위
                partner_stats = (
                    self.db.query(
                        Partner.id,
                        Partner.name,
                        func.count(PartnerApiLog.id).label("total_calls"),
                        func.avg(PartnerApiLog.response_time_ms).label(
                            "avg_response_time"
                        ),
                        func.sum(
                            func.case(
                                (PartnerApiLog.status_code.between(200, 299), 1),
                                else_=0,
                            )
                        ).label("successful_calls"),
                    )
                    .outerjoin(
                        PartnerApiLog,
                        and_(
                            Partner.id == PartnerApiLog.partner_id,
                            PartnerApiLog.created_at >= thirty_days_ago,
                        ),
                    )
                    .filter(Partner.status == "active")
                    .group_by(Partner.id, Partner.name)
                    .all()
                )

                rankings = []
                for i, stat in enumerate(partner_stats):
                    error_rate = 0
                    if stat.total_calls and stat.total_calls > 0:
                        error_rate = (
                            (stat.total_calls - (stat.successful_calls or 0))
                            / stat.total_calls
                        ) * 100

                    performance_score = max(
                        0, 100 - error_rate - (stat.avg_response_time or 0) / 100
                    )

                    rankings.append(
                        PartnerRanking(
                            rank=i + 1,
                            partner_id=stat.id,
                            partner_name=stat.name,
                            score=performance_score,
                            metric_value=performance_score,
                            metric_type="performance_score",
                            change_from_last_period=0.0,  # 실제 계산 필요
                        )
                    )

                # 성능 점수로 정렬
                rankings.sort(key=lambda x: x.score, reverse=True)

                # 순위 재설정
                for i, ranking in enumerate(rankings):
                    ranking.rank = i + 1

                return rankings

            elif metric == "volume":
                # 거래량 기준 순위 (실제 구현에서는 transaction 테이블 활용)
                return []

            else:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid metric. Use 'performance' or 'volume'",
                )

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to get partner rankings: {str(e)}"
            )
