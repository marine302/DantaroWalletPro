"""
에너지 풀 서비스 - 에너지 큐 매니저
"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from .models import EnergyQueue, EnergyQueueCreate, QueueStatus
from .utils import safe_int

logger = logging.getLogger(__name__)


class EnergyQueueManager:
    """에너지 큐 관리 클래스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._queue: List[EnergyQueue] = []
        self._next_id = 1
    
    async def add_to_queue(self, user_id: int, queue_data: EnergyQueueCreate) -> EnergyQueue:
        """대기열에 추가"""
        try:
            queue_item = EnergyQueue(
                user_id=user_id,
                estimated_energy=queue_data.estimated_energy,
                transaction_type=queue_data.transaction_type,
                priority=queue_data.priority,
                status="pending",
                created_at=datetime.utcnow()
            )
            queue_item.id = self._next_id
            self._next_id += 1
            
            # 우선순위에 따라 정렬하여 삽입
            insert_pos = 0
            for i, item in enumerate(self._queue):
                if item.priority < queue_item.priority:
                    insert_pos = i
                    break
                insert_pos = i + 1
            
            self._queue.insert(insert_pos, queue_item)
            
            logger.info(f"사용자 {user_id}를 대기열에 추가: 위치 {insert_pos + 1}")
            return queue_item
            
        except Exception as e:
            logger.error(f"대기열 추가 실패: {e}")
            raise
    
    async def get_queue_status(self, user_id: int) -> Optional[QueueStatus]:
        """사용자의 대기열 상태 조회"""
        try:
            for i, item in enumerate(self._queue):
                if item.user_id == user_id and item.status == "pending":
                    position = i + 1
                    estimated_wait_time = self._calculate_wait_time(position)
                    queue_size = len(self._queue)
                    
                    return QueueStatus(
                        position=position,
                        estimated_wait_time=estimated_wait_time,
                        queue_size=queue_size
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"대기열 상태 조회 실패: {e}")
            return None
    
    def _calculate_wait_time(self, position: int) -> int:
        """대기 시간 계산 (분 단위)"""
        # 평균 처리 시간: 2분/건
        avg_processing_time = 2
        return position * avg_processing_time
    
    async def process_next_in_queue(self) -> Optional[EnergyQueue]:
        """대기열에서 다음 항목 처리"""
        try:
            if not self._queue:
                return None
            
            # 우선순위가 가장 높은 항목 선택
            next_item = self._queue.pop(0)
            next_item.status = "processing"
            
            logger.info(f"대기열에서 처리 시작: 사용자 {next_item.user_id}")
            return next_item
            
        except Exception as e:
            logger.error(f"대기열 처리 실패: {e}")
            return None
    
    async def complete_queue_item(self, item_id: int, success: bool = True) -> bool:
        """대기열 항목 완료 처리"""
        try:
            # 완료된 항목은 별도 로그로 관리 (여기서는 간단히 상태만 변경)
            # 실제로는 데이터베이스에 완료 기록을 저장해야 함
            
            logger.info(f"대기열 항목 {item_id} 완료: 성공={success}")
            return True
            
        except Exception as e:
            logger.error(f"대기열 항목 완료 처리 실패: {e}")
            return False
    
    async def remove_from_queue(self, user_id: int) -> bool:
        """대기열에서 제거"""
        try:
            for i, item in enumerate(self._queue):
                if item.user_id == user_id:
                    removed_item = self._queue.pop(i)
                    removed_item.status = "cancelled"
                    logger.info(f"사용자 {user_id}를 대기열에서 제거")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"대기열 제거 실패: {e}")
            return False
    
    async def get_queue_list(self, limit: int = 10) -> List[EnergyQueue]:
        """대기열 목록 조회"""
        try:
            return self._queue[:limit]
        except Exception as e:
            logger.error(f"대기열 목록 조회 실패: {e}")
            return []
    
    async def get_queue_statistics(self) -> dict:
        """대기열 통계"""
        try:
            total_pending = len([item for item in self._queue if item.status == "pending"])
            avg_wait_time = self._calculate_wait_time(total_pending // 2) if total_pending > 0 else 0
            
            # 트랜잭션 타입별 통계
            type_stats = {}
            for item in self._queue:
                tx_type = item.transaction_type
                if tx_type not in type_stats:
                    type_stats[tx_type] = {"count": 0, "total_energy": 0}
                type_stats[tx_type]["count"] += 1
                type_stats[tx_type]["total_energy"] += item.estimated_energy
            
            return {
                "total_pending": total_pending,
                "average_wait_time": avg_wait_time,
                "type_statistics": type_stats,
                "queue_size": len(self._queue)
            }
            
        except Exception as e:
            logger.error(f"대기열 통계 조회 실패: {e}")
            return {
                "total_pending": 0,
                "average_wait_time": 0,
                "type_statistics": {},
                "queue_size": 0
            }
    
    async def cleanup_old_queue_items(self, hours: int = 24) -> int:
        """오래된 대기열 항목 정리"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            removed_count = 0
            
            # 오래된 항목 제거
            self._queue = [
                item for item in self._queue
                if item.created_at > cutoff_time
            ]
            
            logger.info(f"오래된 대기열 항목 {removed_count}개 제거")
            return removed_count
            
        except Exception as e:
            logger.error(f"대기열 정리 실패: {e}")
            return 0
