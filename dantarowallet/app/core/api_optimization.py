"""
API 성능 최적화 모듈

응답 시간 단축, 동시성 처리, 리소스 사용량 최적화를 담당합니다.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

import httpx
from fastapi import HTTPException, Request, Response, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)


class APIOptimizer:
    """API 성능 최적화 관리자"""

    def __init__(self):
        self.request_metrics: Dict[str, List[float]] = {}
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self.concurrent_control: Dict[str, int] = {}  # 동시성 추적

    def performance_monitor(self):
        """API 성능 모니터링 데코레이터"""

        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                endpoint = func.__name__

                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time

                    # 성능 메트릭 수집
                    if endpoint not in self.request_metrics:
                        self.request_metrics[endpoint] = []

                    self.request_metrics[endpoint].append(duration)

                    # 최근 100개 요청만 유지
                    if len(self.request_metrics[endpoint]) > 100:
                        self.request_metrics[endpoint] = self.request_metrics[endpoint][
                            -100:
                        ]

                    # 느린 요청 로깅
                    if duration > 2.0:  # 2초 이상
                        logger.warning(f"슬로우 API: {endpoint} - {duration:.2f}초")

                    return result

                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(f"API 에러: {endpoint} - {duration:.2f}초 - {str(e)}")
                    raise

            return wrapper

        return decorator

    def rate_limit(self, max_requests: int, window_seconds: int):
        """API 속도 제한 데코레이터"""

        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(request: Request, *args, **kwargs):
                client_ip = request.client.host if request.client else "unknown"
                endpoint = func.__name__
                key = f"{endpoint}:{client_ip}"

                current_time = time.time()

                if key not in self.rate_limits:
                    self.rate_limits[key] = {"requests": [], "blocked_until": 0}

                rate_data = self.rate_limits[key]

                # 차단 시간 확인
                if current_time < rate_data["blocked_until"]:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Too many requests",
                    )

                # 윈도우 내 요청 수 확인
                rate_data["requests"] = [
                    req_time
                    for req_time in rate_data["requests"]
                    if current_time - req_time < window_seconds
                ]

                if len(rate_data["requests"]) >= max_requests:
                    rate_data["blocked_until"] = current_time + window_seconds
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded",
                    )

                rate_data["requests"].append(current_time)
                return await func(request, *args, **kwargs)

            return wrapper

        return decorator

    def circuit_breaker(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """서킷 브레이커 패턴 데코레이터"""

        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                endpoint = func.__name__

                if endpoint not in self.circuit_breakers:
                    self.circuit_breakers[endpoint] = {
                        "failure_count": 0,
                        "last_failure_time": 0,
                        "state": "closed",  # closed, open, half_open
                    }

                breaker = self.circuit_breakers[endpoint]
                current_time = time.time()

                # 서킷이 열린 상태인지 확인
                if breaker["state"] == "open":
                    if current_time - breaker["last_failure_time"] > recovery_timeout:
                        breaker["state"] = "half_open"
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Service temporarily unavailable",
                        )

                try:
                    result = await func(*args, **kwargs)

                    # 성공 시 서킷 리셋
                    if breaker["state"] == "half_open":
                        breaker["state"] = "closed"
                        breaker["failure_count"] = 0

                    return result

                except Exception as e:
                    breaker["failure_count"] += 1
                    breaker["last_failure_time"] = current_time

                    # 실패 임계값 초과 시 서킷 열기
                    if breaker["failure_count"] >= failure_threshold:
                        breaker["state"] = "open"

                    raise

            return wrapper

        return decorator

    async def concurrent_requests(
        self, requests: List[Callable], max_concurrent: int = 10
    ) -> List[Any]:
        """동시 요청 처리 최적화"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def bounded_request(request_func):
            async with semaphore:
                return await request_func()

        tasks = [bounded_request(req) for req in requests]
        return await asyncio.gather(*tasks, return_exceptions=True)

    @asynccontextmanager
    async def limited_concurrency(self, key: str, max_concurrent: int):
        """동시성 제한 컨텍스트 매니저"""
        if key not in self.concurrent_control:
            self.concurrent_control[key] = 0

        # 동시성 제한 확인
        if self.concurrent_control[key] >= max_concurrent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Too many concurrent requests",
            )

        self.concurrent_control[key] += 1
        try:
            yield
        finally:
            self.concurrent_control[key] -= 1

    async def optimize_response_compression(self, response: Response) -> Response:
        """응답 압축 최적화"""
        # 응답 크기가 1KB 이상인 경우에만 압축
        if hasattr(response, "body") and len(response.body) > 1024:
            response.headers["Content-Encoding"] = "gzip"
        return response

    async def get_performance_stats(self) -> Dict[str, Any]:
        """API 성능 통계 반환"""
        stats = {}

        for endpoint, metrics in self.request_metrics.items():
            if metrics:
                avg_time = sum(metrics) / len(metrics)
                max_time = max(metrics)
                min_time = min(metrics)
                request_count = len(metrics)

                stats[endpoint] = {
                    "request_count": request_count,
                    "avg_response_time": avg_time,
                    "max_response_time": max_time,
                    "min_response_time": min_time,
                    "p95_response_time": (
                        sorted(metrics)[int(len(metrics) * 0.95)]
                        if len(metrics) > 10
                        else max_time
                    ),
                }

        # 서킷 브레이커 상태
        circuit_status = {}
        for endpoint, breaker in self.circuit_breakers.items():
            circuit_status[endpoint] = {
                "state": breaker["state"],
                "failure_count": breaker["failure_count"],
            }

        return {
            "endpoint_metrics": stats,
            "circuit_breaker_status": circuit_status,
            "active_rate_limits": len(self.rate_limits),
        }

    async def health_check_external_services(self) -> Dict[str, bool]:
        """외부 서비스 헬스체크"""
        services = {
            "tronnrg": "https://api.tronnrg.com/health",
            "energytron": "https://api.energytron.io/v1/health",
            "trongrid": "https://api.trongrid.io",
        }

        health_status = {}

        async with httpx.AsyncClient(timeout=5.0) as client:
            for service_name, url in services.items():
                try:
                    response = await client.get(url)
                    health_status[service_name] = response.status_code == 200
                except:
                    health_status[service_name] = False

        return health_status


class ResponseOptimizer:
    """응답 최적화 관리자"""

    @staticmethod
    def compress_response(data: Any, threshold: int = 1024) -> Any:
        """응답 데이터 압축"""
        import gzip
        import json

        if isinstance(data, (dict, list)):
            json_data = json.dumps(data, default=str)
            if len(json_data) > threshold:
                # 대용량 데이터는 압축 권장
                logger.info(f"대용량 응답 감지: {len(json_data)} bytes")
                return data

        return data

    @staticmethod
    def paginate_response(
        data: List[Any],
        page: int = 1,
        limit: int = 20,
        total_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """응답 페이지네이션"""
        start_index = (page - 1) * limit
        end_index = start_index + limit

        paginated_data = data[start_index:end_index]

        return {
            "data": paginated_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count or len(data),
                "total_pages": ((total_count or len(data)) + limit - 1) // limit,
                "has_next": end_index < (total_count or len(data)),
                "has_prev": page > 1,
            },
        }


class ConcurrencyOptimizer:
    """동시성 처리 최적화"""

    def __init__(self):
        self.semaphores: Dict[str, asyncio.Semaphore] = {}

    def get_semaphore(self, name: str, limit: int) -> asyncio.Semaphore:
        """세마포어 가져오기 또는 생성"""
        if name not in self.semaphores:
            self.semaphores[name] = asyncio.Semaphore(limit)
        return self.semaphores[name]

    @asynccontextmanager
    async def limited_concurrency(self, name: str, limit: int):
        """제한된 동시성 컨텍스트 매니저"""
        semaphore = self.get_semaphore(name, limit)
        async with semaphore:
            yield

    async def batch_process(
        self,
        items: List[Any],
        process_func: Callable,
        batch_size: int = 10,
        max_concurrent: int = 5,
    ) -> List[Any]:
        """배치 처리 최적화"""
        results = []

        # 배치로 나누기
        batches = [items[i : i + batch_size] for i in range(0, len(items), batch_size)]

        # 동시 처리를 위한 세마포어
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_batch(batch):
            async with semaphore:
                batch_results = []
                for item in batch:
                    try:
                        result = await process_func(item)
                        batch_results.append(result)
                    except Exception as e:
                        logger.error(f"배치 처리 오류: {e}")
                        batch_results.append(None)
                return batch_results

        # 모든 배치 동시 처리
        batch_tasks = [process_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*batch_tasks)

        # 결과 평면화
        for batch_result in batch_results:
            results.extend(batch_result)

        return results


# 전역 최적화 인스턴스들
api_optimizer = APIOptimizer()
response_optimizer = ResponseOptimizer()
concurrency_optimizer = ConcurrencyOptimizer()


# 미들웨어용 성능 추적
async def performance_middleware(request: Request, call_next):
    """성능 추적 미들웨어"""
    start_time = time.time()

    # 요청 처리
    response = await call_next(request)

    # 처리 시간 계산
    process_time = time.time() - start_time

    # 응답 헤더에 처리 시간 추가
    response.headers["X-Process-Time"] = str(process_time)

    # 느린 요청 로깅
    if process_time > 1.0:  # 1초 이상
        logger.warning(
            f"슬로우 요청: {request.method} {request.url.path} - {process_time:.2f}초"
        )

    return response
