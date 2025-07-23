"""
백그라운드 작업 최적화 모듈

비동기 작업, 스케줄링, 큐 관리를 최적화합니다.
"""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from app.core.config import settings

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """작업 우선순위"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class TaskStatus(Enum):
    """작업 상태"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class BackgroundTask:
    """백그라운드 작업 정의"""

    id: str
    name: str
    func: str  # 함수명
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 3
    retry_delay: int = 60  # 초
    timeout: int = 300  # 초
    retry_count: int = 0
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.created_at, type(datetime.now)):
            self.created_at = datetime.now()
        if isinstance(self.scheduled_at, type(datetime.now)):
            self.scheduled_at = datetime.now()


class OptimizedTaskQueue:
    """최적화된 작업 큐"""

    def __init__(self):
        self.local_queue: Dict[TaskPriority, List[BackgroundTask]] = {
            priority: [] for priority in TaskPriority
        }
        self.running_tasks: Dict[str, BackgroundTask] = {}
        self.completed_tasks: Dict[str, BackgroundTask] = {}
        self.failed_tasks: Dict[str, BackgroundTask] = {}
        self.max_concurrent_tasks = 10
        self.worker_pool = ThreadPoolExecutor(max_workers=5)

        # 스케줄링 관련 속성들 추가
        self.recurring_tasks: Dict[str, Dict[str, Any]] = {}
        self.cron_tasks: Dict[str, Dict[str, Any]] = {}

        # Redis 관련 속성 추가
        self._redis_client = None  # 기본값은 None, 나중에 설정 가능

    async def initialize(self):
        """큐 초기화"""
        logger.info("로컬 작업 큐 초기화 완료")

    async def add_task(
        self,
        task_name: str,
        func_name: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        delay: int = 0,
        **task_options,
    ) -> str:
        """작업 추가"""
        task_id = f"{task_name}_{datetime.now().timestamp()}"

        task = BackgroundTask(
            id=task_id,
            name=task_name,
            func=func_name,
            args=args or [],
            kwargs=kwargs or {},
            priority=priority,
            scheduled_at=datetime.now() + timedelta(seconds=delay),
            **task_options,
        )

        self.local_queue[priority].append(task)

        logger.info(f"작업 추가: {task_id} (우선순위: {priority.name})")
        return task_id

    async def get_next_task(self) -> Optional[BackgroundTask]:
        """다음 실행할 작업 조회"""
        return self._get_next_task_from_local()

    def _get_next_task_from_local(self) -> Optional[BackgroundTask]:
        """로컬 큐에서 다음 작업 조회"""
        # 우선순위 순으로 확인
        for priority in [
            TaskPriority.URGENT,
            TaskPriority.HIGH,
            TaskPriority.NORMAL,
            TaskPriority.LOW,
        ]:
            queue = self.local_queue[priority]

            # 실행 시간이 된 작업 찾기
            for i, task in enumerate(queue):
                scheduled_time = task.scheduled_at or datetime.now()
                if scheduled_time <= datetime.now():
                    return queue.pop(i)

        return None

    async def execute_task(self, task: BackgroundTask) -> bool:
        """작업 실행"""
        if len(self.running_tasks) >= self.max_concurrent_tasks:
            logger.warning("최대 동시 실행 작업 수 초과")
            return False

        task.status = TaskStatus.RUNNING
        self.running_tasks[task.id] = task

        try:
            logger.info(f"작업 실행 시작: {task.id}")

            # 타임아웃과 함께 작업 실행
            result = await asyncio.wait_for(
                self._run_task_function(task), timeout=task.timeout
            )

            task.status = TaskStatus.COMPLETED
            self.completed_tasks[task.id] = task
            logger.info(f"작업 완료: {task.id}")

            return True

        except asyncio.TimeoutError:
            logger.error(f"작업 타임아웃: {task.id}")
            task.status = TaskStatus.FAILED
            await self._handle_task_failure(task, "Timeout")
            return False

        except Exception as e:
            logger.error(f"작업 실행 실패: {task.id} - {e}")
            task.status = TaskStatus.FAILED
            await self._handle_task_failure(task, str(e))
            return False

        finally:
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]

    async def _run_task_function(self, task: BackgroundTask):
        """작업 함수 실행"""
        # 동적으로 함수 호출
        module_path, func_name = task.func.rsplit(".", 1)

        # 모듈 임포트
        import importlib

        module = importlib.import_module(module_path)
        func = getattr(module, func_name)

        # 함수 실행
        if asyncio.iscoroutinefunction(func):
            return await func(*task.args, **task.kwargs)
        else:
            # CPU 집약적 작업은 별도 스레드에서 실행
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.worker_pool, lambda: func(*task.args, **task.kwargs)
            )

    async def _handle_task_failure(self, task: BackgroundTask, error_message: str):
        """작업 실패 처리"""
        task.retry_count = getattr(task, "retry_count", 0) + 1

        if task.retry_count < task.max_retries:
            # 재시도 스케줄링
            task.status = TaskStatus.RETRYING
            task.scheduled_at = datetime.now() + timedelta(
                seconds=task.retry_delay * task.retry_count
            )

            logger.info(
                f"작업 재시도 스케줄링: {task.id} ({task.retry_count}/{task.max_retries})"
            )

            if self.redis_client:
                await self._add_task_to_redis(task)
            else:
                self.local_queue[task.priority].append(task)
        else:
            # 최대 재시도 횟수 초과
            self.failed_tasks[task.id] = task
            logger.error(f"작업 최종 실패: {task.id} - {error_message}")

    async def start_worker(self):
        """작업 워커 시작"""
        logger.info("백그라운드 작업 워커 시작")

        while True:
            try:
                task = await self.get_next_task()

                if task:
                    asyncio.create_task(self.execute_task(task))
                else:
                    # 작업이 없으면 잠시 대기
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"워커 오류: {e}")
                await asyncio.sleep(5)

    def get_queue_status(self) -> Dict[str, Any]:
        """큐 상태 조회"""
        return {
            "pending_tasks": {
                priority.name: len(queue)
                for priority, queue in self.local_queue.items()
            },
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "max_concurrent": self.max_concurrent_tasks,
        }

    async def optimize_task_scheduling(self):
        """작업 스케줄링 최적화"""
        try:
            # CPU 및 메모리 사용률 확인
            cpu_usage = await self._get_cpu_usage()
            memory_usage = await self._get_memory_usage()

            # 시스템 부하에 따른 동시 실행 작업 수 조정
            if cpu_usage > 80 or memory_usage > 85:
                # 고부하 시 동시 실행 작업 수 감소
                self.max_concurrent_tasks = max(1, self.max_concurrent_tasks - 1)
                logger.info(
                    f"시스템 부하로 인한 동시 실행 작업 수 감소: {self.max_concurrent_tasks}"
                )
            elif cpu_usage < 50 and memory_usage < 60:
                # 저부하 시 동시 실행 작업 수 증가
                self.max_concurrent_tasks = min(10, self.max_concurrent_tasks + 1)
                logger.info(
                    f"시스템 여유로 인한 동시 실행 작업 수 증가: {self.max_concurrent_tasks}"
                )

            # 우선순위 큐 재정렬
            await self._reorder_queues_by_priority()

        except Exception as e:
            logger.error(f"작업 스케줄링 최적화 실패: {e}")

    async def _get_cpu_usage(self) -> float:
        """CPU 사용률 조회"""
        try:
            import psutil

            return psutil.cpu_percent(interval=1)
        except ImportError:
            return 50.0  # 기본값

    async def _get_memory_usage(self) -> float:
        """메모리 사용률 조회"""
        try:
            import psutil

            return psutil.virtual_memory().percent
        except ImportError:
            return 50.0  # 기본값

    async def _reorder_queues_by_priority(self):
        """우선순위별 큐 재정렬"""
        for priority in TaskPriority:
            queue = self.local_queue[priority]
            # 예정 시간순으로 정렬
            queue.sort(key=lambda task: task.scheduled_at or datetime.now())

    async def get_queue_statistics(self) -> Dict[str, Any]:
        """큐 통계 정보 반환"""
        stats = {
            "queue_lengths": {},
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_distribution": {},
        }

        # 우선순위별 큐 길이
        for priority in TaskPriority:
            stats["queue_lengths"][priority.name] = len(self.local_queue[priority])

        # 작업 유형별 분포
        task_types = {}
        for queue in self.local_queue.values():
            for task in queue:
                task_type = task.func
                task_types[task_type] = task_types.get(task_type, 0) + 1

        stats["task_distribution"] = task_types

        return stats

    async def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """완료된 작업 정리"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        # 완료된 작업 정리
        to_remove = []
        for task_id, task in self.completed_tasks.items():
            if task.completed_at and task.completed_at < cutoff_time:
                to_remove.append(task_id)

        for task_id in to_remove:
            del self.completed_tasks[task_id]

        # 실패한 작업 정리
        to_remove = []
        for task_id, task in self.failed_tasks.items():
            if task.failed_at and task.failed_at < cutoff_time:
                to_remove.append(task_id)

        for task_id in to_remove:
            del self.failed_tasks[task_id]

        logger.info(f"정리된 작업: 완료 {len(to_remove)}개")

    async def _add_task_to_redis(self, task: BackgroundTask) -> None:
        """Redis에 작업 추가"""
        if not self.redis_client:
            return

        try:
            task_data = {
                "id": task.id,
                "name": task.name,
                "func": task.func,
                "args": task.args,
                "kwargs": task.kwargs,
                "priority": task.priority.value,
                "scheduled_at": task.scheduled_at.isoformat(),
                "retry_count": task.retry_count,
                "max_retries": task.max_retries,
                "retry_delay": task.retry_delay,
                "status": task.status.value,
            }

            # Redis 리스트에 작업 추가
            queue_name = f"task_queue_{task.priority.name.lower()}"
            await self.redis_client.lpush(queue_name, json.dumps(task_data))

            # 스케줄된 시간이 있으면 스케줄된 작업 세트에도 추가
            if task.scheduled_at > datetime.now():
                score = task.scheduled_at.timestamp()
                await self.redis_client.zadd("scheduled_tasks", {task.id: score})

        except Exception as e:
            logger.error(f"Redis에 작업 추가 실패: {e}")
            # Redis 실패 시 로컬 큐에 추가
            self.local_queue[task.priority].append(task)

    async def schedule_recurring_task(
        self, name: str, func: Callable, interval_seconds: int, *args, **kwargs
    ) -> str:
        """반복 작업 스케줄링"""
        task_id = f"recurring_{name}_{datetime.now().timestamp()}"

        # 반복 작업 정보 저장
        recurring_task = {
            "id": task_id,
            "name": name,
            "func": func.__name__ if hasattr(func, "__name__") else str(func),
            "args": args,
            "kwargs": kwargs,
            "interval_seconds": interval_seconds,
            "next_run": datetime.now() + timedelta(seconds=interval_seconds),
            "is_active": True,
        }

        self.recurring_tasks[task_id] = recurring_task

        # 첫 번째 실행 스케줄링
        await self.add_task(
            task_name=f"{name}_initial",
            func_name=func.__name__ if hasattr(func, "__name__") else str(func),
            args=list(args),
            kwargs=dict(kwargs),
            priority=TaskPriority.NORMAL,
            delay=int((recurring_task["next_run"] - datetime.now()).total_seconds()),
        )

        logger.info(f"반복 작업 스케줄링: {name} (간격: {interval_seconds}초)")
        return task_id

    async def schedule_cron_task(
        self, name: str, func: Callable, cron_expression: str, *args, **kwargs
    ) -> str:
        """Cron 표현식으로 작업 스케줄링"""
        task_id = f"cron_{name}_{datetime.now().timestamp()}"

        # 간단한 cron 파싱 (시간:분 형식만 지원)
        try:
            if ":" in cron_expression:
                hour, minute = map(int, cron_expression.split(":"))
                next_run = self._get_next_daily_run_time(hour, minute)
            else:
                # 간격(초) 형식
                interval = int(cron_expression)
                next_run = datetime.now() + timedelta(seconds=interval)

            cron_task = {
                "id": task_id,
                "name": name,
                "func": func.__name__ if hasattr(func, "__name__") else str(func),
                "args": args,
                "kwargs": kwargs,
                "cron_expression": cron_expression,
                "next_run": next_run,
                "is_active": True,
            }

            self.cron_tasks[task_id] = cron_task

            # 첫 번째 실행 스케줄링
            await self.add_task(
                task_name=f"{name}_cron",
                func_name=func.__name__ if hasattr(func, "__name__") else str(func),
                args=list(args),
                kwargs=dict(kwargs),
                priority=TaskPriority.NORMAL,
                delay=int((next_run - datetime.now()).total_seconds()),
            )

            logger.info(f"Cron 작업 스케줄링: {name} ({cron_expression})")
            return task_id

        except ValueError as e:
            logger.error(f"잘못된 cron 표현식: {cron_expression} - {e}")
            raise ValueError(f"Invalid cron expression: {cron_expression}")

    def _get_next_daily_run_time(self, hour: int, minute: int) -> datetime:
        """다음 일일 실행 시간 계산"""
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # 오늘 시간이 이미 지났으면 내일로 설정
        if next_run <= now:
            next_run += timedelta(days=1)

        return next_run

    async def run_scheduled_jobs(self) -> None:
        """스케줄된 작업들 실행"""
        current_time = datetime.now()

        # 반복 작업 확인
        for task_id, task_info in list(self.recurring_tasks.items()):
            if task_info["is_active"] and task_info["next_run"] <= current_time:
                # 작업 실행
                await self.add_task(
                    task_name=f"{task_info['name']}_recurring",
                    func_name=task_info["func"],
                    args=task_info["args"],
                    kwargs=task_info["kwargs"],
                    priority=TaskPriority.NORMAL,
                )

                # 다음 실행 시간 업데이트
                task_info["next_run"] = current_time + timedelta(
                    seconds=task_info["interval_seconds"]
                )

        # Cron 작업 확인
        for task_id, task_info in list(self.cron_tasks.items()):
            if task_info["is_active"] and task_info["next_run"] <= current_time:
                # 작업 실행
                await self.add_task(
                    task_name=f"{task_info['name']}_cron",
                    func_name=task_info["func"],
                    args=task_info["args"],
                    kwargs=task_info["kwargs"],
                    priority=TaskPriority.NORMAL,
                )

                # 다음 실행 시간 업데이트 (일일 반복)
                cron_expr = task_info["cron_expression"]
                if ":" in cron_expr:
                    hour, minute = map(int, cron_expr.split(":"))
                    task_info["next_run"] = self._get_next_daily_run_time(hour, minute)
                else:
                    interval = int(cron_expr)
                    task_info["next_run"] = current_time + timedelta(seconds=interval)

    # Redis 클라이언트 속성 추가
    @property
    def redis_client(self):
        """Redis 클라이언트 반환"""
        return getattr(self, "_redis_client", None)

    @redis_client.setter
    def redis_client(self, value):
        """Redis 클라이언트 설정"""
        self._redis_client = value

    # ...existing code...


class TaskScheduler:
    """작업 스케줄러"""

    def __init__(self, task_queue: OptimizedTaskQueue):
        self.task_queue = task_queue
        self.scheduled_jobs: Dict[str, Dict[str, Any]] = {}

    async def schedule_recurring_task(
        self,
        name: str,
        func_name: str,
        interval_seconds: int,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> str:
        """반복 작업 스케줄링"""
        job_id = f"recurring_{name}_{datetime.now().timestamp()}"

        self.scheduled_jobs[job_id] = {
            "name": name,
            "func_name": func_name,
            "interval": interval_seconds,
            "args": args or [],
            "kwargs": kwargs or {},
            "priority": priority,
            "next_run": datetime.now(),
            "active": True,
        }

        logger.info(f"반복 작업 등록: {job_id} (간격: {interval_seconds}초)")
        return job_id

    async def schedule_cron_task(
        self,
        name: str,
        func_name: str,
        cron_expression: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> str:
        """크론 작업 스케줄링"""
        # 간단한 크론 파싱 (실제로는 croniter 라이브러리 사용 권장)
        job_id = f"cron_{name}_{datetime.now().timestamp()}"

        self.scheduled_jobs[job_id] = {
            "name": name,
            "func_name": func_name,
            "cron": cron_expression,
            "args": args or [],
            "kwargs": kwargs or {},
            "priority": priority,
            "next_run": self._parse_cron_next_run(cron_expression),
            "active": True,
        }

        logger.info(f"크론 작업 등록: {job_id} ({cron_expression})")
        return job_id

    def _parse_cron_next_run(self, cron_expression: str) -> datetime:
        """크론 표현식 파싱 (간단한 버전)"""
        # 실제로는 croniter 라이브러리 사용
        # 여기서는 간단히 1시간 후로 설정
        return datetime.now() + timedelta(hours=1)

    async def start_scheduler(self):
        """스케줄러 시작"""
        logger.info("작업 스케줄러 시작")

        while True:
            try:
                current_time = datetime.now()

                for job_id, job in self.scheduled_jobs.items():
                    if not job["active"]:
                        continue

                    if current_time >= job["next_run"]:
                        # 작업을 큐에 추가
                        await self.task_queue.add_task(
                            task_name=job["name"],
                            func_name=job["func_name"],
                            args=job["args"],
                            kwargs=job["kwargs"],
                            priority=job["priority"],
                        )

                        # 다음 실행 시간 계산
                        if "interval" in job:
                            job["next_run"] = current_time + timedelta(
                                seconds=job["interval"]
                            )
                        elif "cron" in job:
                            job["next_run"] = self._parse_cron_next_run(job["cron"])

                await asyncio.sleep(10)  # 10초마다 스케줄 확인

            except Exception as e:
                logger.error(f"스케줄러 오류: {e}")
                await asyncio.sleep(60)


# 최적화된 백그라운드 작업 함수들
async def optimized_price_update():
    """최적화된 가격 업데이트"""
    logger.info("가격 업데이트 작업 시작")

    try:
        # 외부 API 병렬 호출로 최적화
        from app.core.database import get_db
        from app.services.external_energy.external_energy_service import (
            get_external_energy_service,
        )

        async for db in get_db():
            service = get_external_energy_service(db)

            # 병렬로 모든 공급업체 가격 업데이트
            await service.update_all_provider_prices()
            break

        logger.info("가격 업데이트 완료")

    except Exception as e:
        logger.error(f"가격 업데이트 실패: {e}")
        raise


async def optimized_withdrawal_processing():
    """최적화된 출금 처리"""
    logger.info("출금 처리 작업 시작")

    try:
        from app.core.database import get_db
        from app.services.withdrawal.batch_optimizer import AdvancedBatchOptimizer

        async for db in get_db():
            optimizer = AdvancedBatchOptimizer(db)

            # 모든 파트너의 출금 최적화 처리
            # 실제로는 파트너 목록을 조회해야 함
            partner_ids = ["partner_1", "partner_2"]  # 예시

            for partner_id in partner_ids:
                batches = await optimizer.get_optimized_batches_with_ai(partner_id)
                logger.info(f"파트너 {partner_id}: {len(batches)}개 배치 최적화 완료")

            break

        logger.info("출금 처리 최적화 완료")

    except Exception as e:
        logger.error(f"출금 처리 최적화 실패: {e}")
        raise


# 전역 인스턴스
task_queue = OptimizedTaskQueue()
task_scheduler = TaskScheduler(task_queue)


# 시스템 시작 시 호출
async def start_background_services():
    """백그라운드 서비스 시작"""
    await task_queue.initialize()

    # 기본 스케줄링 작업 등록
    await task_scheduler.schedule_recurring_task(
        name="price_update",
        func_name="app.core.background_optimization.optimized_price_update",
        interval_seconds=300,  # 5분마다
        priority=TaskPriority.HIGH,
    )

    await task_scheduler.schedule_recurring_task(
        name="withdrawal_processing",
        func_name="app.core.background_optimization.optimized_withdrawal_processing",
        interval_seconds=600,  # 10분마다
        priority=TaskPriority.NORMAL,
    )

    # 워커와 스케줄러 시작
    asyncio.create_task(task_queue.start_worker())
    asyncio.create_task(task_scheduler.start_scheduler())

    logger.info("백그라운드 최적화 서비스 시작 완료")
