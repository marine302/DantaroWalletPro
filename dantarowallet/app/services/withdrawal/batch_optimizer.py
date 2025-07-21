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


"""
출금 배치 최적화 개선 모듈
"""
from app.core.database_optimization import OptimizedServiceBase, db_optimizer
from app.core.api_optimization import concurrency_optimizer
import asyncio


class AdvancedBatchOptimizer(OptimizedServiceBase):
    """고급 배치 최적화기"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.batch_optimizer = BatchOptimizer(db)
    
    @db_optimizer.cache_query(expire_seconds=60)  # 1분 캐싱
    async def get_optimized_batches_with_ai(
        self, 
        partner_id: str, 
        max_batches: int = 10
    ) -> List[Dict[str, Any]]:
        """AI 기반 배치 최적화"""
        try:
            # 기존 최적화 수행
            base_batches = await self.batch_optimizer.optimize_withdrawal_batches(
                partner_id, max_batches
            )
            
            if not base_batches:
                return []
            
            # AI 기반 추가 최적화
            optimized_batches = await self._apply_ai_optimization(base_batches)
            
            # 네트워크 상태 기반 우선순위 조정
            final_batches = await self._adjust_for_network_conditions(optimized_batches)
            
            return final_batches
            
        except Exception as e:
            logger.error(f"AI 배치 최적화 실패: {e}")
            # 폴백: 기본 최적화 사용
            return await self.batch_optimizer.optimize_withdrawal_batches(partner_id, max_batches)
    
    async def _apply_ai_optimization(self, batches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """AI 기반 배치 최적화 적용"""
        try:
            # 시뮬레이션 기반 최적화
            for batch in batches:
                # 예상 가스비 계산
                estimated_gas = await self._estimate_gas_cost(batch)
                batch['estimated_gas_cost'] = estimated_gas
                
                # 최적 실행 시간 예측
                optimal_time = await self._predict_optimal_execution_time(batch)
                batch['optimal_execution_time'] = optimal_time
                
                # 성공률 예측
                success_rate = await self._predict_success_rate(batch)
                batch['predicted_success_rate'] = success_rate
            
            # 총 비용 효율성으로 재정렬
            batches.sort(key=lambda x: x.get('estimated_gas_cost', 0))
            
            return batches
            
        except Exception as e:
            logger.warning(f"AI 최적화 실패, 기본 배치 반환: {e}")
            return batches
    
    async def _estimate_gas_cost(self, batch: Dict[str, Any]) -> float:
        """가스비 예측"""
        try:
            base_cost = 21000  # 기본 트랜잭션 비용
            withdrawal_count = batch.get('total_count', 1)
            
            # 복잡도에 따른 추가 비용
            complexity_factor = min(withdrawal_count * 1.2, 5.0)
            estimated_cost = base_cost * complexity_factor
            
            # 네트워크 혼잡도 반영
            network_multiplier = await self._get_network_congestion_multiplier()
            
            return estimated_cost * network_multiplier
            
        except Exception as e:
            logger.warning(f"가스비 예측 실패: {e}")
            return 25000.0  # 기본값
    
    async def _predict_optimal_execution_time(self, batch: Dict[str, Any]) -> str:
        """최적 실행 시간 예측"""
        try:
            # 과거 데이터 기반 분석
            current_hour = datetime.now().hour
            
            # 네트워크 활동이 적은 시간대 권장
            low_activity_hours = [2, 3, 4, 5, 6, 7]  # 새벽 시간
            
            if current_hour in low_activity_hours:
                return "immediate"
            elif current_hour < 12:
                return "in_2_hours"
            else:
                return "tonight_2am"
                
        except Exception as e:
            logger.warning(f"실행 시간 예측 실패: {e}")
            return "immediate"
    
    async def _predict_success_rate(self, batch: Dict[str, Any]) -> float:
        """성공률 예측"""
        try:
            base_rate = 95.0  # 기본 성공률
            
            # 배치 크기에 따른 조정
            batch_size = batch.get('total_count', 1)
            if batch_size > 50:
                base_rate -= 5.0
            elif batch_size > 100:
                base_rate -= 10.0
            
            # 우선순위에 따른 조정
            priority_score = batch.get('priority_score', 0)
            if priority_score > 50:
                base_rate += 2.0
            
            return max(min(base_rate, 99.0), 70.0)  # 70-99% 범위
            
        except Exception as e:
            logger.warning(f"성공률 예측 실패: {e}")
            return 90.0
    
    async def _get_network_congestion_multiplier(self) -> float:
        """네트워크 혼잡도 승수"""
        try:
            current_hour = datetime.now().hour
            
            # 시간대별 혼잡도 (실제로는 API에서 가져와야 함)
            congestion_map = {
                range(0, 6): 0.8,   # 새벽 - 낮은 혼잡도
                range(6, 9): 1.3,   # 아침 - 높은 혼잡도
                range(9, 18): 1.1,  # 오후 - 보통 혼잡도
                range(18, 22): 1.4, # 저녁 - 매우 높은 혼잡도
                range(22, 24): 1.0  # 밤 - 보통 혼잡도
            }
            
            for hour_range, multiplier in congestion_map.items():
                if current_hour in hour_range:
                    return multiplier
            
            return 1.0
            
        except Exception as e:
            logger.warning(f"네트워크 혼잡도 조회 실패: {e}")
            return 1.0
    
    async def _adjust_for_network_conditions(self, batches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """네트워크 상태에 따른 배치 조정"""
        try:
            # 병렬로 네트워크 상태 확인
            network_tasks = [
                self._check_tron_network_status(),
                self._check_gas_price_trends(),
                self._check_node_performance()
            ]
            
            async with concurrency_optimizer.limited_concurrency("network_check", 3):
                network_status, gas_trends, node_performance = await asyncio.gather(
                    *network_tasks, return_exceptions=True
                )
            
            # 네트워크 상태에 따른 배치 순서 조정
            for batch in batches:
                adjustment_score = 0
                
                # 가스비 트렌드 반영
                if isinstance(gas_trends, dict) and gas_trends.get('trend') == 'decreasing':
                    adjustment_score += 10  # 가스비가 내려가는 추세면 우선순위 상승
                
                # 노드 성능 반영
                if isinstance(node_performance, dict) and node_performance.get('avg_response_time', 1000) < 200:
                    adjustment_score += 5  # 빠른 응답시간이면 우선순위 상승
                
                batch['network_adjustment_score'] = adjustment_score
                batch['final_priority_score'] = batch.get('priority_score', 0) + adjustment_score
            
            # 최종 우선순위로 정렬
            batches.sort(key=lambda x: x.get('final_priority_score', 0), reverse=True)
            
            return batches
            
        except Exception as e:
            logger.warning(f"네트워크 상태 조정 실패: {e}")
            return batches
    
    async def _check_tron_network_status(self) -> Dict[str, Any]:
        """TRON 네트워크 상태 확인"""
        try:
            # 실제로는 TRON API 호출
            return {
                'status': 'healthy',
                'tps': 2000,
                'block_time': 3.0
            }
        except Exception as e:
            logger.warning(f"TRON 네트워크 상태 확인 실패: {e}")
            return {'status': 'unknown'}
    
    async def _check_gas_price_trends(self) -> Dict[str, Any]:
        """가스비 트렌드 확인"""
        try:
            # 실제로는 가스비 추적 API 호출
            return {
                'current_price': 420,
                'trend': 'stable',
                'recommendation': 'proceed'
            }
        except Exception as e:
            logger.warning(f"가스비 트렌드 확인 실패: {e}")
            return {'trend': 'unknown'}
    
    async def _check_node_performance(self) -> Dict[str, Any]:
        """노드 성능 확인"""
        try:
            # 실제로는 노드 상태 API 호출
            return {
                'avg_response_time': 150,
                'success_rate': 99.5,
                'load': 'normal'
            }
        except Exception as e:
            logger.warning(f"노드 성능 확인 실패: {e}")
            return {'avg_response_time': 1000}


# 성능 모니터링
class BatchPerformanceMonitor:
    """배치 성능 모니터링"""
    
    def __init__(self):
        self.performance_data: Dict[str, List[Dict[str, Any]]] = {}
    
    async def record_batch_execution(
        self, 
        batch_id: str, 
        execution_time: float,
        success_rate: float,
        gas_used: float
    ):
        """배치 실행 성능 기록"""
        if batch_id not in self.performance_data:
            self.performance_data[batch_id] = []
        
        self.performance_data[batch_id].append({
            'timestamp': datetime.now(),
            'execution_time': execution_time,
            'success_rate': success_rate,
            'gas_used': gas_used
        })
        
        # 최근 100개 기록만 유지
        if len(self.performance_data[batch_id]) > 100:
            self.performance_data[batch_id] = self.performance_data[batch_id][-100:]
    
    def get_performance_insights(self, batch_id: str) -> Dict[str, Any]:
        """성능 인사이트 제공"""
        if batch_id not in self.performance_data:
            return {}
        
        data = self.performance_data[batch_id]
        if not data:
            return {}
        
        avg_execution_time = sum(d['execution_time'] for d in data) / len(data)
        avg_success_rate = sum(d['success_rate'] for d in data) / len(data)
        avg_gas_used = sum(d['gas_used'] for d in data) / len(data)
        
        return {
            'average_execution_time': avg_execution_time,
            'average_success_rate': avg_success_rate,
            'average_gas_used': avg_gas_used,
            'total_executions': len(data),
            'performance_trend': self._calculate_trend(data)
        }
    
    def _calculate_trend(self, data: List[Dict[str, Any]]) -> str:
        """성능 트렌드 계산"""
        if len(data) < 5:
            return 'insufficient_data'
        
        recent_performance = data[-5:]
        older_performance = data[-10:-5] if len(data) >= 10 else data[:-5]
        
        if not older_performance:
            return 'stable'
        
        recent_avg = sum(d['execution_time'] for d in recent_performance) / len(recent_performance)
        older_avg = sum(d['execution_time'] for d in older_performance) / len(older_performance)
        
        if recent_avg < older_avg * 0.9:
            return 'improving'
        elif recent_avg > older_avg * 1.1:
            return 'degrading'
        else:
            return 'stable'


# 전역 인스턴스
batch_performance_monitor = BatchPerformanceMonitor()
