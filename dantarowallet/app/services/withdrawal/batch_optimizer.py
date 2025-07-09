"""
출금 요청 그룹핑 및 배치 최적화 모듈
수수료 절약을 위한 최적화된 배치를 생성합니다.
"""
from typing import List, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.withdrawal import Withdrawal, WithdrawalStatus, WithdrawalPriority
from app.core.logger import get_logger
from .utils import safe_str, safe_decimal, safe_int

logger = get_logger(__name__)


class BatchOptimizer:
    """출금 배치 최적화기"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def optimize_withdrawal_batches(
        self,
        partner_id: str,
        max_batches: int = 10
    ) -> List[Dict[str, Any]]:
        """파트너사의 대기 중인 출금 요청들을 최적화된 배치로 그룹핑합니다."""
        try:
            # 대기 중인 출금 요청들 조회
            pending_result = await self.db.execute(
                select(Withdrawal).where(
                    and_(
                        Withdrawal.partner_id == partner_id,
                        Withdrawal.status == WithdrawalStatus.PENDING
                    )
                ).order_by(Withdrawal.created_at.asc())
            )
            pending_withdrawals = list(pending_result.scalars().all())
            
            if not pending_withdrawals:
                return []
            
            # 우선순위별로 그룹핑
            priority_groups = self._group_by_priority(pending_withdrawals)
            
            optimized_batches = []
            
            for priority, withdrawals in priority_groups.items():
                # 각 우선순위 그룹을 최적 크기로 분할
                batches = self._create_optimal_batches(withdrawals, max_batch_size=20)
                
                for batch_withdrawals in batches:
                    if len(batch_withdrawals) == 0:
                        continue
                    
                    batch_info = self._calculate_batch_info(batch_withdrawals, priority)
                    optimized_batches.append(batch_info)
            
            # 우선순위와 효율성 순으로 정렬
            optimized_batches.sort(
                key=lambda x: (-x['priority_score'], -x['efficiency_score'])
            )
            
            return optimized_batches[:max_batches]
            
        except Exception as e:
            logger.error(f"배치 최적화 실패: {str(e)}")
            raise
    
    def _group_by_priority(
        self, 
        withdrawals: List[Withdrawal]
    ) -> Dict[str, List[Withdrawal]]:
        """출금 요청들을 우선순위별로 그룹핑합니다."""
        groups = {
            'urgent': [],
            'high': [],
            'normal': [],
            'low': []
        }
        
        for withdrawal in withdrawals:
            priority = safe_str(withdrawal.priority).lower()
            if priority in groups:
                groups[priority].append(withdrawal)
            else:
                groups['normal'].append(withdrawal)
        
        # 빈 그룹 제거
        return {k: v for k, v in groups.items() if v}
    
    def _create_optimal_batches(
        self, 
        withdrawals: List[Withdrawal],
        max_batch_size: int = 20
    ) -> List[List[Withdrawal]]:
        """최적 크기의 배치들을 생성합니다."""
        if not withdrawals:
            return []
        
        batches = []
        current_batch = []
        current_batch_amount = Decimal('0')
        
        # 금액별로 정렬 (비슷한 금액끼리 묶기)
        sorted_withdrawals = sorted(
            withdrawals, 
            key=lambda w: safe_decimal(w.amount)
        )
        
        for withdrawal in sorted_withdrawals:
            amount = safe_decimal(withdrawal.amount)
            
            # 배치 크기나 금액 제한 확인
            if (len(current_batch) >= max_batch_size or 
                current_batch_amount + amount > Decimal('50000')):
                
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                    current_batch_amount = Decimal('0')
            
            current_batch.append(withdrawal)
            current_batch_amount += amount
        
        # 마지막 배치 추가
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def _calculate_batch_info(
        self, 
        withdrawals: List[Withdrawal],
        priority: str
    ) -> Dict[str, Any]:
        """배치 정보를 계산합니다."""
        total_amount = sum(safe_decimal(w.amount) for w in withdrawals)
        withdrawal_ids = [safe_int(w.id) for w in withdrawals]
        
        # 에너지 비용 추정
        estimated_energy = self._estimate_energy_cost(Decimal(str(total_amount)))
        
        # 우선순위 점수 계산
        priority_score = self._calculate_batch_priority(withdrawals)
        
        # 효율성 점수 (배치 크기 대비 수수료 절약)
        efficiency_score = len(withdrawals) * 10 - float(estimated_energy)
        
        return {
            'withdrawal_ids': withdrawal_ids,
            'total_amount': float(total_amount),
            'total_count': len(withdrawals),
            'estimated_energy_cost': float(estimated_energy),
            'priority_score': priority_score,
            'efficiency_score': max(0, int(efficiency_score)),
            'estimated_completion_time': datetime.utcnow(),
            'priority_level': priority
        }
    
    def _estimate_energy_cost(self, amount: Decimal) -> Decimal:
        """배치의 예상 에너지 비용을 계산합니다."""
        base_cost = Decimal('13.85')  # 기본 TRC20 전송 에너지
        
        if amount > Decimal('1000'):
            base_cost += Decimal('1.0')  # 대액 전송 추가 비용
        
        return base_cost
    
    def _calculate_batch_priority(self, withdrawals: List[Withdrawal]) -> int:
        """배치의 우선순위 점수를 계산합니다."""
        priority_score = 0
        
        for withdrawal in withdrawals:
            # 우선순위별 점수
            priority = safe_str(withdrawal.priority)
            if priority == WithdrawalPriority.URGENT:
                priority_score += 10
            elif priority == WithdrawalPriority.HIGH:
                priority_score += 5
            elif priority == WithdrawalPriority.NORMAL:
                priority_score += 2
            
            # 대기 시간 보너스
            try:
                created_at_value = getattr(withdrawal, 'created_at', None)
                if created_at_value and hasattr(created_at_value, 'total_seconds'):
                    wait_hours = (datetime.utcnow() - created_at_value).total_seconds() / 3600
                    priority_score += min(int(wait_hours), 24)  # 최대 24시간 보너스
                elif created_at_value:
                    # Column 타입인 경우 실제 값 시도
                    actual_value = getattr(created_at_value, 'value', created_at_value)
                    if actual_value and hasattr(actual_value, 'total_seconds'):
                        wait_hours = (datetime.utcnow() - actual_value).total_seconds() / 3600
                        priority_score += min(int(wait_hours), 24)
            except (AttributeError, TypeError, ValueError):
                pass  # 오류가 발생하면 무시
        
        return priority_score
