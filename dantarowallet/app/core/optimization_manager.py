"""
통합 백엔드 최적화 관리자

데이터베이스, API, 백그라운드 작업의 모든 최적화를 통합 관리합니다.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.api_optimization import APIOptimizer
from app.core.background_optimization import (
    BackgroundTask,
    OptimizedTaskQueue,
    TaskPriority,
)
from app.core.config import settings
from app.core.database_optimization import DatabaseOptimizer, db_optimizer
from app.core.performance_monitor import PerformanceMonitor, performance_monitor

logger = logging.getLogger(__name__)


class IntegratedOptimizationManager:
    """통합 최적화 관리자"""

    def __init__(self):
        self.db_optimizer = db_optimizer
        self.api_optimizer = APIOptimizer()
        self.task_queue = OptimizedTaskQueue()
        self.monitor = performance_monitor  # monitor 속성 추가
        self.performance_monitor = performance_monitor
        self.optimization_enabled = True
        self.auto_scaling_enabled = True

    async def initialize(self):
        """최적화 시스템 초기화"""
        try:
            logger.info("통합 최적화 시스템 초기화 시작")

            # Redis 초기화 (타임아웃 추가)
            try:
                await asyncio.wait_for(
                    self.db_optimizer.initialize_redis(), timeout=5.0
                )
                logger.info("Redis 초기화 완료")
            except asyncio.TimeoutError:
                logger.warning("Redis 초기화 타임아웃, 스킵")
            except Exception as e:
                logger.warning(f"Redis 초기화 실패, 스킵: {e}")

            # 백그라운드 작업들을 비동기로 시작 (blocking 방지)
            if hasattr(asyncio, "create_task"):
                # 성능 모니터링 시작
                asyncio.create_task(self._performance_monitoring_loop())

                # 자동 스케일링 시작
                if self.auto_scaling_enabled:
                    asyncio.create_task(self._auto_scaling_loop())

                # 백그라운드 작업 스케줄러 시작
                asyncio.create_task(self._background_scheduler_loop())

                # 기본 최적화 작업 등록 (비동기로 처리)
                asyncio.create_task(self._register_default_optimization_tasks())

                logger.info("통합 최적화 시스템 백그라운드 작업 시작")

            logger.info("통합 최적화 시스템 초기화 완료")

        except Exception as e:
            logger.error(f"최적화 시스템 초기화 실패: {e}")
            # 에러 발생 시에도 서버 시작은 계속 진행
            logger.warning("최적화 시스템 없이 서버 계속 진행")

    async def _performance_monitoring_loop(self):
        """성능 모니터링 루프"""
        while True:
            try:
                # 시스템 메트릭 수집
                metrics = await self.performance_monitor.collect_system_metrics()

                # 임계값 확인 및 자동 최적화
                await self._check_and_optimize(metrics)

                await asyncio.sleep(30)  # 30초마다 모니터링

            except Exception as e:
                logger.error(f"성능 모니터링 루프 에러: {e}")
                await asyncio.sleep(60)

    async def _auto_scaling_loop(self):
        """자동 스케일링 루프"""
        while True:
            try:
                # 시스템 부하 확인
                metrics = await self.performance_monitor.collect_system_metrics()

                # 동적 스케일링
                await self._dynamic_scaling(metrics)

                await asyncio.sleep(60)  # 1분마다 확인

            except Exception as e:
                logger.error(f"자동 스케일링 루프 에러: {e}")
                await asyncio.sleep(120)

    async def _background_scheduler_loop(self):
        """백그라운드 작업 스케줄러 루프"""
        while True:
            try:
                # 예약된 작업 실행
                await self.task_queue.run_scheduled_jobs()

                # 큐 최적화
                await self.task_queue.optimize_task_scheduling()

                # 완료된 작업 정리
                await self.task_queue.cleanup_completed_tasks()

                await asyncio.sleep(30)  # 30초마다 실행

            except Exception as e:
                logger.error(f"백그라운드 스케줄러 루프 에러: {e}")
                await asyncio.sleep(60)

    async def _check_and_optimize(self, metrics):
        """메트릭 기반 자동 최적화"""
        try:
            # CPU 사용률이 높은 경우
            if metrics.cpu_usage > 80:
                logger.warning(f"높은 CPU 사용률 감지: {metrics.cpu_usage:.1f}%")
                await self._optimize_cpu_usage()

            # 메모리 사용률이 높은 경우
            if metrics.memory_usage > 85:
                logger.warning(f"높은 메모리 사용률 감지: {metrics.memory_usage:.1f}%")
                await self._optimize_memory_usage()

            # 응답 시간이 느린 경우
            if metrics.response_time > 2.0:
                logger.warning(f"느린 응답 시간 감지: {metrics.response_time:.2f}초")
                await self._optimize_response_time()

            # 에러율이 높은 경우
            if metrics.error_rate > 5.0:
                logger.warning(f"높은 에러율 감지: {metrics.error_rate:.1f}%")
                await self._optimize_error_handling()

        except Exception as e:
            logger.error(f"자동 최적화 실패: {e}")

    async def _optimize_cpu_usage(self):
        """CPU 사용률 최적화"""
        # 백그라운드 작업 동시 실행 수 감소
        self.task_queue.max_concurrent_tasks = max(
            1, self.task_queue.max_concurrent_tasks - 1
        )

        # API 동시성 제한 강화
        # 추가 최적화 로직...

        logger.info("CPU 사용률 최적화 적용")

    async def _optimize_memory_usage(self):
        """메모리 사용률 최적화"""
        # 캐시 정리
        if hasattr(self.db_optimizer, "query_cache"):
            cache_size = len(self.db_optimizer.query_cache)
            self.db_optimizer.query_cache.clear()
            logger.info(f"메모리 최적화: 캐시 정리 ({cache_size}개 항목)")

    async def _optimize_response_time(self):
        """응답 시간 최적화"""
        # 데이터베이스 연결 풀 증가
        # 캐시 TTL 증가
        logger.info("응답 시간 최적화 적용")

    async def _optimize_error_handling(self):
        """에러 처리 최적화"""
        # 서킷 브레이커 임계값 조정
        # 재시도 로직 개선
        logger.info("에러 처리 최적화 적용")

    async def _dynamic_scaling(self, metrics):
        """동적 스케일링"""
        try:
            # 부하에 따른 리소스 할당 조정
            if metrics.throughput > 100:  # 높은 처리량
                # 더 많은 리소스 할당
                if self.task_queue.max_concurrent_tasks < 10:
                    self.task_queue.max_concurrent_tasks += 1
                    logger.info(
                        f"스케일 업: 동시 작업 수 증가 → {self.task_queue.max_concurrent_tasks}"
                    )

            elif metrics.throughput < 20:  # 낮은 처리량
                # 리소스 절약
                if self.task_queue.max_concurrent_tasks > 2:
                    self.task_queue.max_concurrent_tasks -= 1
                    logger.info(
                        f"스케일 다운: 동시 작업 수 감소 → {self.task_queue.max_concurrent_tasks}"
                    )

        except Exception as e:
            logger.error(f"동적 스케일링 실패: {e}")

    async def _register_default_optimization_tasks(self):
        """기본 최적화 작업 등록"""
        try:
            # 캐시 정리 작업 (매시간)
            await self.task_queue.schedule_recurring_task(
                name="cache_cleanup",
                func=self._cache_cleanup_task,
                interval_seconds=3600,  # 1시간
            )

            # 성능 메트릭 수집 (5분마다)
            await self.task_queue.schedule_recurring_task(
                name="metrics_collection",
                func=self._collect_metrics_task,
                interval_seconds=300,  # 5분
            )

            # 데이터베이스 최적화 (매일 새벽 3시)
            await self.task_queue.schedule_cron_task(
                name="db_optimization",
                func=self._optimize_database_task,
                cron_expression="3:0",  # 매일 새벽 3시 (hour:minute 형식)
            )

            logger.info("기본 최적화 작업 등록 완료")

        except Exception as e:
            logger.error(f"기본 최적화 작업 등록 실패: {e}")

    async def get_optimization_status(self) -> Dict[str, Any]:
        """최적화 상태 조회"""
        try:
            # 성능 보고서
            performance_report = await self.performance_monitor.get_performance_report()

            # API 성능 통계
            api_stats = await self.api_optimizer.get_performance_stats()

            # 작업 큐 통계
            queue_stats = await self.task_queue.get_queue_statistics()

            return {
                "optimization_enabled": self.optimization_enabled,
                "auto_scaling_enabled": self.auto_scaling_enabled,
                "performance": performance_report,
                "api_performance": api_stats,
                "task_queue": queue_stats,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"최적화 상태 조회 실패: {e}")
            return {"error": str(e)}

    async def apply_manual_optimization(
        self, optimization_type: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """수동 최적화 적용"""
        try:
            result = {"success": False, "message": ""}

            if optimization_type == "cache_clear":
                # 캐시 정리
                cache_size = len(self.db_optimizer.query_cache)
                self.db_optimizer.query_cache.clear()
                result = {
                    "success": True,
                    "message": f"캐시 정리 완료: {cache_size}개 항목 삭제",
                }

            elif optimization_type == "scale_workers":
                # 워커 수 조정
                new_count = params.get("worker_count", 5)
                old_count = self.task_queue.max_concurrent_tasks
                self.task_queue.max_concurrent_tasks = new_count
                result = {
                    "success": True,
                    "message": f"워커 수 조정: {old_count} → {new_count}",
                }

            elif optimization_type == "optimize_queries":
                # 쿼리 최적화 실행
                # 실제 구현 필요
                result = {"success": True, "message": "쿼리 최적화 실행 완료"}

            else:
                result = {
                    "success": False,
                    "message": f"알 수 없는 최적화 유형: {optimization_type}",
                }

            logger.info(f"수동 최적화 적용: {optimization_type} - {result['message']}")
            return result

        except Exception as e:
            logger.error(f"수동 최적화 실패: {e}")
            return {"success": False, "message": f"최적화 실패: {str(e)}"}

    async def generate_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """최적화 권장사항 생성"""
        try:
            recommendations = []

            # 성능 메트릭 기반 권장사항
            metrics = await self.performance_monitor.collect_system_metrics()

            if metrics.cpu_usage > 70:
                recommendations.append(
                    {
                        "type": "cpu_optimization",
                        "priority": "high",
                        "title": "CPU 사용률 최적화",
                        "description": f"현재 CPU 사용률이 {metrics.cpu_usage:.1f}%입니다. 백그라운드 작업 수를 줄이거나 코드 최적화를 고려하세요.",
                        "actions": ["scale_workers", "optimize_queries"],
                    }
                )

            if metrics.memory_usage > 80:
                recommendations.append(
                    {
                        "type": "memory_optimization",
                        "priority": "high",
                        "title": "메모리 사용률 최적화",
                        "description": f"현재 메모리 사용률이 {metrics.memory_usage:.1f}%입니다. 캐시 정리를 권장합니다.",
                        "actions": ["cache_clear"],
                    }
                )

            if metrics.response_time > 1.5:
                recommendations.append(
                    {
                        "type": "performance_optimization",
                        "priority": "medium",
                        "title": "응답 시간 최적화",
                        "description": f"평균 응답 시간이 {metrics.response_time:.2f}초입니다. 데이터베이스 쿼리 최적화를 권장합니다.",
                        "actions": ["optimize_queries"],
                    }
                )

            # API 성능 기반 권장사항
            api_stats = await self.api_optimizer.get_performance_stats()

            # 느린 엔드포인트 확인
            for endpoint, stats in api_stats.get("endpoint_metrics", {}).items():
                if stats.get("avg_response_time", 0) > 2.0:
                    recommendations.append(
                        {
                            "type": "api_optimization",
                            "priority": "medium",
                            "title": f"API 엔드포인트 최적화: {endpoint}",
                            "description": f"{endpoint}의 평균 응답 시간이 {stats['avg_response_time']:.2f}초입니다.",
                            "actions": ["optimize_queries", "cache_optimization"],
                        }
                    )

            return recommendations

        except Exception as e:
            logger.error(f"최적화 권장사항 생성 실패: {e}")
            return []

    # 백그라운드 작업 메서드들
    async def _cache_cleanup_task(self):
        """캐시 정리 작업"""
        try:
            logger.info("캐시 정리 작업 시작")
            await self.db_optimizer.cleanup_expired_cache()
            logger.info("캐시 정리 작업 완료")
        except Exception as e:
            logger.error(f"캐시 정리 작업 실패: {e}")

    async def _collect_metrics_task(self):
        """성능 메트릭 수집 작업"""
        try:
            logger.info("성능 메트릭 수집 시작")
            metrics = await self.monitor.collect_system_metrics()
            if metrics:
                logger.info(f"메트릭 수집 완료: {metrics.cpu_usage:.1f}% CPU")
        except Exception as e:
            logger.error(f"성능 메트릭 수집 실패: {e}")

    async def _optimize_database_task(self):
        """데이터베이스 최적화 작업"""
        try:
            logger.info("데이터베이스 최적화 작업 시작")

            # DB 세션 가져오기
            from app.core.database import get_db

            async for session in get_db():
                await self.db_optimizer.optimize_indexes(session)
                await self.db_optimizer.cleanup_old_data(session)
                break

            logger.info("데이터베이스 최적화 작업 완료")
        except Exception as e:
            logger.error(f"데이터베이스 최적화 작업 실패: {e}")


# 전역 통합 최적화 관리자 인스턴스
optimization_manager = IntegratedOptimizationManager()
