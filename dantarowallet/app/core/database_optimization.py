"""
데이터베이스 최적화 모듈

성능 향상을 위한 데이터베이스 연결 최적화, 캐싱, 배치 처리 등을 관리합니다.
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from sqlalchemy import Table, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.pool import QueuePool

# Redis는 선택적 의존성으로 처리
redis = None
REDIS_AVAILABLE = False

from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DatabaseOptimizer:
    """데이터베이스 성능 최적화 관리자"""

    def __init__(self):
        self.redis_client: Optional[Any] = None
        self.query_cache: Dict[str, Any] = {}
        self.batch_operations: Dict[str, List[Any]] = {}

    async def initialize_redis(self):
        """Redis 연결 초기화"""
        try:
            if not REDIS_AVAILABLE or redis is None:
                logger.warning(
                    "Redis 패키지가 설치되지 않았습니다. 캐싱 기능이 제한됩니다."
                )
                return

            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30,
            )
            if self.redis_client:
                await self.redis_client.ping()
            logger.info("Redis 연결 성공")
        except Exception as e:
            logger.warning(f"Redis 연결 실패, 메모리 캐시 사용: {e}")
            self.redis_client = None

    def cache_key_generator(self, *args, **kwargs) -> str:
        """캐시 키 생성"""
        key_data = f"{args}_{kwargs}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def cache_query(self, expire_seconds: int = 300):
        """쿼리 결과 캐싱 데코레이터"""

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                cache_key = (
                    f"query:{func.__name__}:{self.cache_key_generator(*args, **kwargs)}"
                )

                # 캐시에서 조회
                cached_result = await self._get_cache(cache_key)
                if cached_result is not None:
                    return cached_result

                # 함수 실행
                result = await func(*args, **kwargs)

                # 결과 캐싱
                await self._set_cache(cache_key, result, expire_seconds)
                return result

            return wrapper

        return decorator

    async def _get_cache(self, key: str) -> Any:
        """캐시에서 데이터 조회"""
        try:
            if self.redis_client:
                data = await self.redis_client.get(key)
                if data:
                    return json.loads(data)
            else:
                # 메모리 캐시 폴백
                if key in self.query_cache:
                    item = self.query_cache[key]
                    if item["expire_time"] > time.time():
                        return item["data"]
                    else:
                        del self.query_cache[key]
        except Exception as e:
            logger.warning(f"캐시 조회 실패: {e}")
        return None

    async def _set_cache(self, key: str, data: Any, expire_seconds: int):
        """캐시에 데이터 저장"""
        try:
            if self.redis_client:
                await self.redis_client.setex(
                    key, expire_seconds, json.dumps(data, default=str)
                )
            else:
                # 메모리 캐시 폴백
                self.query_cache[key] = {
                    "data": data,
                    "expire_time": time.time() + expire_seconds,
                }
        except Exception as e:
            logger.warning(f"캐시 저장 실패: {e}")

    async def batch_insert(self, session: AsyncSession, objects: List[Any]):
        """배치 삽입 최적화"""
        try:
            if not objects:
                return

            # 배치 크기 제한
            batch_size = 1000
            for i in range(0, len(objects), batch_size):
                batch = objects[i : i + batch_size]
                session.add_all(batch)
                await session.flush()

            await session.commit()
            logger.info(f"배치 삽입 완료: {len(objects)}개 객체")

        except Exception as e:
            await session.rollback()
            logger.error(f"배치 삽입 실패: {e}")
            raise

    async def execute_bulk_update(
        self, session: AsyncSession, model: Type[T], updates: List[Dict[str, Any]]
    ):
        """대량 업데이트 최적화"""
        try:
            if not updates:
                return

            # 모델에서 테이블 정보 가져오기
            if not hasattr(model, "__table__"):
                logger.error(f"모델 {model}에서 __table__ 속성을 찾을 수 없습니다")
                return

            table = getattr(model, "__table__")

            # 배치 크기별로 나누어 처리
            batch_size = 500
            for i in range(0, len(updates), batch_size):
                batch = updates[i : i + batch_size]

                # bulk_update_mappings 사용
                await session.execute(table.update(), batch)
                await session.flush()

            await session.commit()
            logger.info(f"대량 업데이트 완료: {len(updates)}개 레코드")

        except Exception as e:
            await session.rollback()
            logger.error(f"대량 업데이트 실패: {e}")
            raise

    async def optimize_query_with_loading(
        self, session: AsyncSession, query, *relationships
    ):
        """관계형 데이터 로딩 최적화"""
        try:
            # selectinload 또는 joinedload 적용
            optimized_query = query
            for relationship in relationships:
                if (
                    hasattr(relationship, "_is_collection")
                    and relationship._is_collection
                ):
                    optimized_query = optimized_query.options(
                        selectinload(relationship)
                    )
                else:
                    optimized_query = optimized_query.options(joinedload(relationship))

            result = await session.execute(optimized_query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"쿼리 최적화 실패: {e}")
            raise

    async def analyze_slow_queries(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """슬로우 쿼리 분석"""
        try:
            # PostgreSQL의 경우
            if "postgresql" in settings.DATABASE_URL:
                result = await session.execute(
                    text(
                        """
                    SELECT query, mean_time, calls, rows, 100.0 * shared_blks_hit / 
                           nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                    FROM pg_stat_statements 
                    ORDER BY mean_time DESC 
                    LIMIT 10
                """
                    )
                )

                slow_queries = []
                for row in result:
                    slow_queries.append(
                        {
                            "query": row.query,
                            "mean_time": float(row.mean_time),
                            "calls": row.calls,
                            "rows": row.rows,
                            "hit_percent": float(row.hit_percent or 0),
                        }
                    )

                return slow_queries
            else:
                # PostgreSQL이 아닌 경우 빈 리스트 반환
                logger.warning(
                    "PostgreSQL이 아닌 데이터베이스에서는 슬로우 쿼리 분석이 지원되지 않습니다"
                )
                return []

        except Exception as e:
            logger.warning(f"슬로우 쿼리 분석 실패: {e}")
            return []

    async def optimize_indexes(self, session: AsyncSession) -> Dict[str, Any]:
        """인덱스 최적화 제안"""
        try:
            optimization_suggestions = {
                "missing_indexes": [],
                "unused_indexes": [],
                "duplicate_indexes": [],
            }

            # 자주 사용되는 WHERE 절에 대한 인덱스 확인
            common_queries = [
                "SELECT * FROM withdrawals WHERE status = 'pending'",
                "SELECT * FROM energy_orders WHERE provider_id = ?",
                "SELECT * FROM users WHERE created_at > ?",
                "SELECT * FROM transactions WHERE user_id = ? AND created_at BETWEEN ? AND ?",
            ]

            for query in common_queries:
                # EXPLAIN ANALYZE로 실행 계획 분석
                try:
                    plan = await session.execute(text(f"EXPLAIN ANALYZE {query}"))
                    # 실행 계획에서 Seq Scan이 있으면 인덱스 추천
                    plan_text = str(plan.fetchall())
                    if "Seq Scan" in plan_text:
                        optimization_suggestions["missing_indexes"].append(
                            {"query": query, "suggestion": "인덱스 추가 권장"}
                        )
                except:
                    pass

            return optimization_suggestions

        except Exception as e:
            logger.error(f"인덱스 최적화 분석 실패: {e}")
            return {}

    async def cleanup_expired_cache(self):
        """만료된 캐시 정리"""
        try:
            if not self.redis_client:
                await self.initialize_redis()

            if not self.redis_client:
                logger.warning("Redis 클라이언트를 사용할 수 없습니다")
                return

            # Redis 메모리 사용량 체크
            info = await self.redis_client.info("memory")
            used_memory = info.get("used_memory", 0)

            if used_memory > 100 * 1024 * 1024:  # 100MB 이상
                # 만료시간이 설정된 키들의 TTL 단축
                async for key in self.redis_client.scan_iter(match="*"):
                    ttl = await self.redis_client.ttl(key)
                    if ttl > 3600:  # 1시간 이상 남은 경우
                        await self.redis_client.expire(key, 1800)  # 30분으로 단축

            logger.info("만료된 캐시 정리 완료")

        except Exception as e:
            logger.error(f"캐시 정리 중 오류: {e}")

    async def cleanup_old_data(self, session: Optional[AsyncSession] = None):
        """오래된 데이터 정리"""
        try:
            if not session:
                # 새로운 세션 생성
                from app.core.database import get_db

                async for db in get_db():
                    session = db
                    break

            if not session:
                logger.error("데이터베이스 세션을 가져올 수 없습니다")
                return

            logger.info("오래된 데이터 정리 시작")

            # 30일 이상 된 로그 데이터 삭제
            cutoff_date = datetime.now() - timedelta(days=30)

            # 오래된 트랜잭션 분석 데이터 삭제
            delete_query = text(
                """
                DELETE FROM transaction_analytics 
                WHERE created_at < :cutoff_date
            """
            )
            result = await session.execute(delete_query, {"cutoff_date": cutoff_date})
            deleted_count = getattr(result, "rowcount", 0)

            # 완료된 오래된 작업 정리
            cleanup_tasks_query = text(
                """
                DELETE FROM background_tasks 
                WHERE status = 'completed' AND updated_at < :cutoff_date
            """
            )
            await session.execute(cleanup_tasks_query, {"cutoff_date": cutoff_date})

            await session.commit()
            logger.info(f"오래된 데이터 정리 완료: {deleted_count}개 레코드 삭제")

        except Exception as e:
            logger.error(f"오래된 데이터 정리 중 오류: {e}")
            if session:
                await session.rollback()


# 전역 최적화 인스턴스
db_optimizer = DatabaseOptimizer()


# 최적화된 서비스 베이스 클래스
class OptimizedServiceBase:
    """성능 최적화가 적용된 서비스 베이스 클래스"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.optimizer = db_optimizer

    @db_optimizer.cache_query(expire_seconds=600)  # 10분 캐싱
    async def get_cached_count(self, model: Type[T], **filters) -> int:
        """캐싱된 카운트 조회"""
        query = select(func.count()).select_from(model)
        for key, value in filters.items():
            if hasattr(model, key):
                query = query.where(getattr(model, key) == value)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def batch_create(self, objects: List[Any]):
        """배치 생성"""
        await self.optimizer.batch_insert(self.db, objects)

    async def batch_update(self, model: Type[T], updates: List[Dict[str, Any]]):
        """배치 업데이트"""
        await self.optimizer.execute_bulk_update(self.db, model, updates)
