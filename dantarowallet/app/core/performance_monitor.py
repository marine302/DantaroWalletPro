"""
성능 모니터링 및 최적화 관리자

실시간 성능 메트릭 수집, 분석, 경고 시스템을 제공합니다.
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import psutil
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """성능 메트릭 데이터 클래스"""

    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    database_connections: int
    active_requests: int
    response_time: float
    error_rate: float
    throughput: float


class PerformanceMonitor:
    """성능 모니터링 관리자"""

    def __init__(self):
        self.metrics_history: deque = deque(maxlen=1000)  # 최근 1000개 메트릭
        self.alert_thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
            "response_time": 2.0,  # 2초
            "error_rate": 5.0,  # 5%
            "database_connections": 50,
        }
        self.request_metrics: Dict[str, List[float]] = defaultdict(list)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.total_requests: int = 0
        self.start_time = time.time()

    async def collect_system_metrics(self) -> PerformanceMetrics:
        """시스템 메트릭 수집"""
        try:
            # CPU 사용률
            cpu_usage = psutil.cpu_percent(interval=1)

            # 메모리 사용률
            memory = psutil.virtual_memory()
            memory_usage = memory.percent

            # 디스크 사용률
            disk = psutil.disk_usage("/")
            disk_usage = disk.percent

            # 네트워크 I/O
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
            }

            # 데이터베이스 연결 수
            db_connections = await self._get_database_connections()

            # 현재 활성 요청 수
            active_requests = len(self.request_metrics.get("active", []))

            # 평균 응답 시간
            avg_response_time = await self._calculate_avg_response_time()

            # 에러율
            error_rate = await self._calculate_error_rate()

            # 처리량 (TPS)
            throughput = await self._calculate_throughput()

            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                database_connections=db_connections,
                active_requests=active_requests,
                response_time=avg_response_time,
                error_rate=error_rate,
                throughput=throughput,
            )

            # 메트릭 히스토리에 추가
            self.metrics_history.append(metrics)

            # 임계값 확인 및 경고
            await self._check_alert_thresholds(metrics)

            return metrics

        except Exception as e:
            logger.error(f"시스템 메트릭 수집 실패: {e}")
            raise

    async def _get_database_connections(self) -> int:
        """데이터베이스 연결 수 조회"""
        try:
            from app.core.database import get_db

            db_gen = get_db()
            session = await db_gen.__anext__()
            try:
                if "postgresql" in settings.DATABASE_URL:
                    result = await session.execute(
                        text(
                            "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
                        )
                    )
                    return result.scalar() or 0
                elif "sqlite" in settings.DATABASE_URL:
                    # SQLite는 연결 풀 개념이 다름
                    return 1
                else:
                    return 0
            finally:
                await db_gen.aclose()
        except Exception as e:
            logger.warning(f"DB 연결 수 조회 실패: {e}")
            return 0

    async def _calculate_avg_response_time(self) -> float:
        """평균 응답 시간 계산"""
        all_times = []
        for endpoint_times in self.request_metrics.values():
            all_times.extend(endpoint_times[-100:])  # 최근 100개만

        return sum(all_times) / len(all_times) if all_times else 0.0

    async def _calculate_error_rate(self) -> float:
        """에러율 계산"""
        total_errors = sum(self.error_counts.values())
        if self.total_requests == 0:
            return 0.0
        return (total_errors / self.total_requests) * 100

    async def _calculate_throughput(self) -> float:
        """처리량 계산 (TPS)"""
        uptime = time.time() - self.start_time
        if uptime == 0:
            return 0.0
        return self.total_requests / uptime

    async def _check_alert_thresholds(self, metrics: PerformanceMetrics):
        """경고 임계값 확인"""
        alerts = []

        if metrics.cpu_usage > self.alert_thresholds["cpu_usage"]:
            alerts.append(f"높은 CPU 사용률: {metrics.cpu_usage:.1f}%")

        if metrics.memory_usage > self.alert_thresholds["memory_usage"]:
            alerts.append(f"높은 메모리 사용률: {metrics.memory_usage:.1f}%")

        if metrics.disk_usage > self.alert_thresholds["disk_usage"]:
            alerts.append(f"높은 디스크 사용률: {metrics.disk_usage:.1f}%")

        if metrics.response_time > self.alert_thresholds["response_time"]:
            alerts.append(f"느린 응답 시간: {metrics.response_time:.2f}초")

        if metrics.error_rate > self.alert_thresholds["error_rate"]:
            alerts.append(f"높은 에러율: {metrics.error_rate:.1f}%")

        if metrics.database_connections > self.alert_thresholds["database_connections"]:
            alerts.append(f"많은 DB 연결: {metrics.database_connections}개")

        if alerts:
            logger.warning("성능 경고: " + ", ".join(alerts))

    @asynccontextmanager
    async def track_request(self, endpoint: str):
        """요청 추적 컨텍스트 매니저"""
        start_time = time.time()
        self.total_requests += 1

        # 활성 요청에 추가
        if "active" not in self.request_metrics:
            self.request_metrics["active"] = []
        self.request_metrics["active"].append(start_time)

        try:
            yield
        except Exception as e:
            # 에러 카운트 증가
            self.error_counts[endpoint] += 1
            raise
        finally:
            # 요청 완료 시간 기록
            end_time = time.time()
            duration = end_time - start_time

            if endpoint not in self.request_metrics:
                self.request_metrics[endpoint] = []
            self.request_metrics[endpoint].append(duration)

            # 최근 데이터만 유지 (메모리 절약)
            if len(self.request_metrics[endpoint]) > 1000:
                self.request_metrics[endpoint] = self.request_metrics[endpoint][-500:]

            # 활성 요청에서 제거
            try:
                self.request_metrics["active"].remove(start_time)
            except ValueError:
                pass

    async def get_performance_report(self, minutes: int = 30) -> Dict[str, Any]:
        """성능 보고서 생성"""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            recent_metrics = [
                m for m in self.metrics_history if m.timestamp >= cutoff_time
            ]

            if not recent_metrics:
                return {"message": "데이터 없음"}

            # 통계 계산
            cpu_values = [m.cpu_usage for m in recent_metrics]
            memory_values = [m.memory_usage for m in recent_metrics]
            response_times = [m.response_time for m in recent_metrics]

            report = {
                "period_minutes": minutes,
                "sample_count": len(recent_metrics),
                "cpu_usage": {
                    "avg": sum(cpu_values) / len(cpu_values),
                    "max": max(cpu_values),
                    "min": min(cpu_values),
                },
                "memory_usage": {
                    "avg": sum(memory_values) / len(memory_values),
                    "max": max(memory_values),
                    "min": min(memory_values),
                },
                "response_time": {
                    "avg": sum(response_times) / len(response_times),
                    "max": max(response_times),
                    "min": min(response_times),
                },
                "total_requests": self.total_requests,
                "error_rate": await self._calculate_error_rate(),
                "throughput": await self._calculate_throughput(),
                "top_endpoints": await self._get_top_endpoints(),
                "recommendations": await self._generate_recommendations(recent_metrics),
            }

            return report

        except Exception as e:
            logger.error(f"성능 보고서 생성 실패: {e}")
            return {"error": str(e)}

    async def _get_top_endpoints(self) -> List[Dict[str, Any]]:
        """가장 많이 사용되는 엔드포인트"""
        endpoint_stats = []

        for endpoint, times in self.request_metrics.items():
            if endpoint == "active":
                continue

            endpoint_stats.append(
                {
                    "endpoint": endpoint,
                    "total_requests": len(times),
                    "avg_response_time": sum(times) / len(times) if times else 0,
                    "error_count": self.error_counts.get(endpoint, 0),
                }
            )

        # 요청 수로 정렬
        endpoint_stats.sort(key=lambda x: x["total_requests"], reverse=True)
        return endpoint_stats[:10]

    async def _generate_recommendations(
        self, metrics: List[PerformanceMetrics]
    ) -> List[str]:
        """성능 개선 권장사항 생성"""
        recommendations = []

        if not metrics:
            return recommendations

        avg_cpu = sum(m.cpu_usage for m in metrics) / len(metrics)
        avg_memory = sum(m.memory_usage for m in metrics) / len(metrics)
        avg_response = sum(m.response_time for m in metrics) / len(metrics)

        if avg_cpu > 70:
            recommendations.append(
                "CPU 사용률이 높습니다. 코드 최적화 또는 스케일링을 고려하세요."
            )

        if avg_memory > 80:
            recommendations.append(
                "메모리 사용률이 높습니다. 메모리 누수 확인 또는 캐시 정책 검토가 필요합니다."
            )

        if avg_response > 1.0:
            recommendations.append(
                "응답 시간이 느립니다. 데이터베이스 쿼리 최적화를 검토하세요."
            )

        max_db_connections = max(m.database_connections for m in metrics)
        if max_db_connections > 30:
            recommendations.append(
                "데이터베이스 연결이 많습니다. 연결 풀 설정을 검토하세요."
            )

        if not recommendations:
            recommendations.append("현재 성능이 양호합니다.")

        return recommendations

    async def optimize_database_queries(self, session: AsyncSession) -> Dict[str, Any]:
        """데이터베이스 쿼리 최적화 분석"""
        try:
            optimization_report = {
                "slow_queries": [],
                "table_stats": [],
                "index_suggestions": [],
            }

            # PostgreSQL 슬로우 쿼리 분석
            if "postgresql" in settings.DATABASE_URL:
                slow_queries = await session.execute(
                    text(
                        """
                    SELECT query, mean_time, calls, rows
                    FROM pg_stat_statements 
                    WHERE mean_time > 100
                    ORDER BY mean_time DESC 
                    LIMIT 10
                """
                    )
                )

                for row in slow_queries:
                    optimization_report["slow_queries"].append(
                        {
                            "query": (
                                row.query[:200] + "..."
                                if len(row.query) > 200
                                else row.query
                            ),
                            "avg_time_ms": float(row.mean_time),
                            "call_count": row.calls,
                            "avg_rows": row.rows,
                        }
                    )

            return optimization_report

        except Exception as e:
            logger.warning(f"DB 최적화 분석 실패: {e}")
            return {"error": str(e)}


# 전역 성능 모니터 인스턴스
performance_monitor = PerformanceMonitor()
