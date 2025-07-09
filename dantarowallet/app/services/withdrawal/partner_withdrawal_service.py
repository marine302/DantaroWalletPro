"""
파트너사 출금 관리 서비스 - Doc #28
파트너사별 유연한 출금 정책 및 자동화를 제공합니다.
"""
import json
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime, timedelta, time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc
from sqlalchemy.orm import selectinload, joinedload

from app.models.withdrawal import Withdrawal, WithdrawalStatus, WithdrawalPriority
from app.models.withdrawal_policy import (
    PartnerWithdrawalPolicy, WithdrawalPolicyType, ApprovalRuleType,
    WithdrawalApprovalRule, WithdrawalWhitelist, WithdrawalBatch
)
from app.models.partner import Partner
from app.models.user import User
from app.core.exceptions import ValidationError, NotFoundError
from app.core.logger import get_logger

logger = get_logger(__name__)


def safe_get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """SQLAlchemy 모델 속성을 안전하게 가져오는 헬퍼 함수"""
    if obj is None:
        return default
    
    value = getattr(obj, attr, default)
    
    # SQLAlchemy Column 타입인 경우 실제 값 추출
    if hasattr(value, 'value'):
        return value.value
    elif hasattr(value, '__getitem__') and hasattr(value, 'keys'):
        # dict-like object
        return value
    else:
        return value


def safe_decimal(value: Any, default: Decimal = Decimal('0')) -> Decimal:
    """안전한 Decimal 변환"""
    if value is None:
        return default
    
    if hasattr(value, 'value'):
        value = value.value
    
    try:
        return Decimal(str(value))
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """안전한 int 변환"""
    if value is None:
        return default
    
    if hasattr(value, 'value'):
        value = value.value
    
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_str(value: Any, default: str = '') -> str:
    """안전한 str 변환"""
    if value is None:
        return default
    
    if hasattr(value, 'value'):
        value = value.value
    
    try:
        return str(value)
    except (TypeError, ValueError):
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    """안전한 bool 변환"""
    if value is None:
        return default
    
    if hasattr(value, 'value'):
        value = value.value
    
    try:
        return bool(value)
    except (TypeError, ValueError):
        return default


class PartnerWithdrawalService:
    """파트너사 출금 관리 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # === 출금 정책 관리 ===
    
    async def create_withdrawal_policy(
        self, 
        partner_id: str,
        policy_data: Dict[str, Any],
        admin_id: int
    ) -> PartnerWithdrawalPolicy:
        """파트너사 출금 정책을 생성합니다."""
        try:
            # 파트너 존재 확인
            partner_result = await self.db.execute(
                select(Partner).where(Partner.id == partner_id)
            )
            partner = partner_result.scalar_one_or_none()
            if not partner:
                raise NotFoundError(f"파트너를 찾을 수 없습니다: {partner_id}")
            
            # 기존 정책 확인
            existing_result = await self.db.execute(
                select(PartnerWithdrawalPolicy).where(
                    PartnerWithdrawalPolicy.partner_id == partner_id
                )
            )
            existing_policy = existing_result.scalar_one_or_none()
            
            if existing_policy:
                raise ValidationError(f"이미 출금 정책이 존재합니다: {partner_id}")
            
            # 새 정책 생성
            policy = PartnerWithdrawalPolicy(
                partner_id=partner_id,
                **policy_data
            )
            
            self.db.add(policy)
            await self.db.commit()
            await self.db.refresh(policy)
            
            logger.info(f"파트너 출금 정책 생성: {partner_id} -> {policy.id}")
            return policy
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"파트너 출금 정책 생성 실패: {str(e)}")
            raise
    
    async def get_withdrawal_policy(
        self, 
        partner_id: str
    ) -> Optional[PartnerWithdrawalPolicy]:
        """파트너사 출금 정책을 조회합니다."""
        result = await self.db.execute(
            select(PartnerWithdrawalPolicy)
            .options(
                selectinload(PartnerWithdrawalPolicy.approval_rules),
                selectinload(PartnerWithdrawalPolicy.whitelist_addresses)
            )
            .where(PartnerWithdrawalPolicy.partner_id == partner_id)
        )
        return result.scalar_one_or_none()
    
    async def update_withdrawal_policy(
        self,
        partner_id: str,
        update_data: Dict[str, Any],
        admin_id: int
    ) -> PartnerWithdrawalPolicy:
        """파트너사 출금 정책을 업데이트합니다."""
        try:
            # 기존 정책 조회
            policy = await self.get_withdrawal_policy(partner_id)
            if not policy:
                raise NotFoundError(f"출금 정책을 찾을 수 없습니다: {partner_id}")
            
            # 업데이트 적용
            for field, value in update_data.items():
                if hasattr(policy, field):
                    setattr(policy, field, value)
            
            # 수동으로 updated_at 설정
            current_time = datetime.utcnow()
            query = (
                update(PartnerWithdrawalPolicy)
                .where(PartnerWithdrawalPolicy.id == policy.id)
                .values(updated_at=current_time)
            )
            await self.db.execute(query)
            await self.db.commit()
            await self.db.refresh(policy)
            
            logger.info(f"파트너 출금 정책 업데이트: {partner_id}")
            return policy
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"파트너 출금 정책 업데이트 실패: {str(e)}")
            raise
    
    # === 실시간 출금 자동 승인 규칙 엔진 ===
    
    async def evaluate_withdrawal_request(
        self,
        withdrawal_id: int,
        partner_id: str
    ) -> Dict[str, Any]:
        """출금 요청을 평가하고 자동 승인 여부를 결정합니다."""
        try:
            # 출금 요청 조회
            withdrawal_result = await self.db.execute(
                select(Withdrawal)
                .options(joinedload(Withdrawal.user))
                .where(Withdrawal.id == withdrawal_id)
            )
            withdrawal = withdrawal_result.scalar_one_or_none()
            if not withdrawal:
                raise NotFoundError(f"출금 요청을 찾을 수 없습니다: {withdrawal_id}")
            
            # 파트너 정책 조회
            policy = await self.get_withdrawal_policy(partner_id)
            if not policy:
                raise NotFoundError(f"출금 정책을 찾을 수 없습니다: {partner_id}")
            
            evaluation_result = {
                'can_auto_approve': False,
                'approval_reason': '',
                'risk_score': 0,
                'required_actions': [],
                'policy_applied': 'none'
            }
            
            # 1. 정책 활성화 확인
            if not safe_bool(policy.is_active):
                evaluation_result['approval_reason'] = '정책이 비활성화됨'
                return evaluation_result
            
            # 2. 자동 승인 활성화 확인
            if not safe_bool(policy.auto_approve_enabled):
                evaluation_result['approval_reason'] = '자동 승인이 비활성화됨'
                evaluation_result['required_actions'].append('manual_review')
                return evaluation_result
            
            # 3. 금액 제한 확인
            amount = safe_decimal(withdrawal.amount)
            max_auto_amount = safe_decimal(policy.auto_approve_max_amount)
            
            if max_auto_amount > 0 and amount > max_auto_amount:
                evaluation_result['approval_reason'] = f'금액이 자동 승인 한도 초과: {amount} > {max_auto_amount}'
                evaluation_result['required_actions'].append('manual_review')
                return evaluation_result
            
            # 4. 일일 한도 확인
            daily_limit = safe_decimal(policy.auto_approve_daily_limit)
            if daily_limit > 0:
                today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                today_total_result = await self.db.execute(
                    select(func.sum(Withdrawal.amount))
                    .where(
                        and_(
                            Withdrawal.partner_id == partner_id,
                            Withdrawal.user_id == safe_int(withdrawal.user_id),
                            Withdrawal.status.in_([
                                WithdrawalStatus.APPROVED,
                                WithdrawalStatus.PROCESSING,
                                WithdrawalStatus.COMPLETED
                            ]),
                            Withdrawal.created_at >= today_start
                        )
                    )
                )
                today_total = safe_decimal(today_total_result.scalar() or 0)
                
                if today_total + amount > daily_limit:
                    evaluation_result['approval_reason'] = f'일일 한도 초과: {today_total + amount} > {daily_limit}'
                    evaluation_result['required_actions'].append('daily_limit_exceeded')
                    return evaluation_result
            
            # 5. 화이트리스트 확인
            if safe_bool(policy.whitelist_enabled):
                whitelist_result = await self.db.execute(
                    select(WithdrawalWhitelist).where(
                        and_(
                            WithdrawalWhitelist.partner_id == partner_id,
                            WithdrawalWhitelist.address == safe_str(withdrawal.to_address),
                            WithdrawalWhitelist.is_active == True
                        )
                    )
                )
                whitelist_entry = whitelist_result.scalar_one_or_none()
                
                if safe_bool(policy.whitelist_only) and not whitelist_entry:
                    evaluation_result['approval_reason'] = '화이트리스트에 없는 주소'
                    evaluation_result['required_actions'].append('address_verification')
                    return evaluation_result
                
                if whitelist_entry:
                    evaluation_result['risk_score'] -= 20  # 화이트리스트 주소는 위험도 감소
            
            # 6. 위험 점수 계산
            risk_score = await self._calculate_risk_score(withdrawal, policy)
            evaluation_result['risk_score'] = risk_score
            
            risk_threshold = safe_int(policy.risk_score_threshold, 50)
            if risk_score > risk_threshold:
                evaluation_result['approval_reason'] = f'위험 점수 초과: {risk_score} > {risk_threshold}'
                evaluation_result['required_actions'].append('risk_assessment')
                return evaluation_result
            
            # 7. 모든 조건 통과 - 자동 승인 가능
            evaluation_result['can_auto_approve'] = True
            evaluation_result['approval_reason'] = '모든 자동 승인 조건 충족'
            evaluation_result['policy_applied'] = safe_str(policy.policy_type)
            
            return evaluation_result
            
        except Exception as e:
            logger.error(f"출금 요청 평가 실패: {str(e)}")
            raise
    
    async def _calculate_risk_score(
        self,
        withdrawal: Withdrawal,
        policy: PartnerWithdrawalPolicy
    ) -> int:
        """출금 요청의 위험 점수를 계산합니다."""
        risk_score = 0
        
        try:
            # 1. 금액 기반 위험도
            amount = safe_decimal(withdrawal.amount)
            if amount > Decimal('1000'):
                risk_score += 10
            if amount > Decimal('10000'):
                risk_score += 20
            
            # 2. 신규 주소 위험도
            address_history_result = await self.db.execute(
                select(func.count(Withdrawal.id))
                .where(
                    and_(
                        Withdrawal.to_address == safe_str(withdrawal.to_address),
                        Withdrawal.status == WithdrawalStatus.COMPLETED
                    )
                )
            )
            address_count = safe_int(address_history_result.scalar() or 0)
            
            if address_count == 0:
                risk_score += 15  # 신규 주소
            elif address_count < 5:
                risk_score += 5   # 사용 빈도 낮음
            
            # 3. 사용자 활동 패턴
            user_id = safe_int(withdrawal.user_id)
            recent_activity_result = await self.db.execute(
                select(func.count(Withdrawal.id))
                .where(
                    and_(
                        Withdrawal.user_id == user_id,
                        Withdrawal.created_at >= datetime.utcnow() - timedelta(days=7),
                        Withdrawal.status.in_([
                            WithdrawalStatus.COMPLETED,
                            WithdrawalStatus.PROCESSING
                        ])
                    )
                )
            )
            recent_count = safe_int(recent_activity_result.scalar() or 0)
            
            if recent_count > 10:
                risk_score += 25  # 과도한 출금 활동
            elif recent_count > 5:
                risk_score += 10
            
            # 4. 시간대 기반 위험도
            current_hour = datetime.utcnow().hour
            if current_hour < 6 or current_hour > 22:
                risk_score += 5  # 야간 시간대
            
            return min(risk_score, 100)  # 최대 100점
            
        except Exception as e:
            logger.error(f"위험 점수 계산 실패: {str(e)}")
            return 50  # 기본값
    
    # === 일괄 출금 스케줄 관리 ===
    
    async def create_withdrawal_batch(
        self,
        partner_id: str,
        withdrawal_ids: List[int],
        scheduled_time: Optional[datetime] = None
    ) -> WithdrawalBatch:
        """출금 배치를 생성합니다."""
        try:
            # 파트너 정책 조회
            policy = await self.get_withdrawal_policy(partner_id)
            if not policy:
                raise NotFoundError(f"출금 정책을 찾을 수 없습니다: {partner_id}")
            
            # 출금 요청들 검증
            withdrawals_result = await self.db.execute(
                select(Withdrawal).where(
                    and_(
                        Withdrawal.id.in_(withdrawal_ids),
                        Withdrawal.partner_id == partner_id,
                        Withdrawal.status == WithdrawalStatus.APPROVED
                    )
                )
            )
            withdrawals = withdrawals_result.scalars().all()
            
            if len(withdrawals) != len(withdrawal_ids):
                raise ValidationError("일부 출금 요청이 배치 처리에 적합하지 않습니다")
            
            # 배치 크기 확인
            batch_min = safe_int(policy.batch_min_count, 1)
            batch_max = safe_int(policy.batch_max_count, 100)
            
            if len(withdrawals) < batch_min:
                raise ValidationError(f"배치 최소 개수 미달: {len(withdrawals)} < {batch_min}")
            
            if len(withdrawals) > batch_max:
                raise ValidationError(f"배치 최대 개수 초과: {len(withdrawals)} > {batch_max}")
            
            # 총 금액 계산
            total_amount = sum(safe_decimal(w.amount) for w in withdrawals)
            total_fee = sum(safe_decimal(w.fee) for w in withdrawals)
            
            # 배치 생성
            batch = WithdrawalBatch(
                partner_id=partner_id,
                batch_type='manual' if scheduled_time else 'scheduled',
                total_count=len(withdrawals),
                total_amount=total_amount,
                total_fee=total_fee,
                scheduled_time=scheduled_time or datetime.utcnow(),
                withdrawal_ids=json.dumps(withdrawal_ids),
                status='pending'
            )
            
            self.db.add(batch)
            await self.db.commit()
            await self.db.refresh(batch)
            
            # 출금 요청들에 배치 ID 업데이트
            for withdrawal in withdrawals:
                # SQLAlchemy 모델 속성 안전하게 업데이트
                await self.db.execute(
                    update(Withdrawal)
                    .where(Withdrawal.id == withdrawal.id)
                    .values(
                        batch_id=str(batch.id),
                        status=WithdrawalStatus.PROCESSING
                    )
                )
            
            await self.db.commit()
            
            logger.info(f"출금 배치 생성: {partner_id} -> {batch.id} ({len(withdrawals)}건)")
            return batch
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"출금 배치 생성 실패: {str(e)}")
            raise
    
    async def get_pending_batches(
        self,
        partner_id: str,
        limit: int = 10
    ) -> List[WithdrawalBatch]:
        """대기 중인 출금 배치들을 조회합니다."""
        result = await self.db.execute(
            select(WithdrawalBatch)
            .where(
                and_(
                    WithdrawalBatch.partner_id == partner_id,
                    WithdrawalBatch.status.in_(['pending', 'scheduled'])
                )
            )
            .order_by(WithdrawalBatch.scheduled_time)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    # === 출금 요청 그룹핑 및 배치 최적화 ===
    
    async def optimize_withdrawal_batches(
        self,
        partner_id: str
    ) -> List[Dict[str, Any]]:
        """출금 요청들을 최적화된 배치로 그룹핑합니다."""
        try:
            # 파트너 정책 조회
            policy = await self.get_withdrawal_policy(partner_id)
            if not policy:
                raise NotFoundError(f"출금 정책을 찾을 수 없습니다: {partner_id}")
            
            # 승인된 출금 요청들 조회
            pending_result = await self.db.execute(
                select(Withdrawal)
                .where(
                    and_(
                        Withdrawal.partner_id == partner_id,
                        Withdrawal.status == WithdrawalStatus.APPROVED,
                        Withdrawal.batch_id.is_(None)
                    )
                )
                .order_by(Withdrawal.priority.desc(), Withdrawal.amount.desc())
            )
            pending_withdrawals = pending_result.scalars().all()
            
            if not pending_withdrawals:
                return []
            
            # 최적화 설정
            optimal_batch_size = safe_int(policy.optimal_batch_size, 20)
            energy_threshold = safe_decimal(policy.energy_cost_threshold, Decimal('10'))
            
            # 배치 그룹핑 알고리즘
            optimized_batches = []
            current_batch = []
            current_total = Decimal('0')
            current_energy_cost = Decimal('0')
            
            for withdrawal in pending_withdrawals:
                amount = safe_decimal(withdrawal.amount)
                estimated_energy = self._estimate_energy_cost(amount)
                
                # 배치 크기나 에너지 비용 초과 시 새 배치 시작
                if (len(current_batch) >= optimal_batch_size or 
                    current_energy_cost + estimated_energy > energy_threshold):
                    
                    if current_batch:
                        optimized_batches.append({
                            'withdrawal_ids': [safe_int(w.id) for w in current_batch],
                            'total_amount': current_total,
                            'total_count': len(current_batch),
                            'estimated_energy_cost': current_energy_cost,
                            'priority_score': self._calculate_batch_priority(current_batch)
                        })
                    
                    current_batch = []
                    current_total = Decimal('0')
                    current_energy_cost = Decimal('0')
                
                current_batch.append(withdrawal)
                current_total += amount
                current_energy_cost += estimated_energy
            
            # 마지막 배치 추가
            if current_batch:
                optimized_batches.append({
                    'withdrawal_ids': [safe_int(w.id) for w in current_batch],
                    'total_amount': current_total,
                    'total_count': len(current_batch),
                    'estimated_energy_cost': current_energy_cost,
                    'priority_score': self._calculate_batch_priority(current_batch)
                })
            
            # 우선순위순으로 정렬
            optimized_batches.sort(key=lambda x: x['priority_score'], reverse=True)
            
            logger.info(f"출금 배치 최적화 완료: {partner_id} -> {len(optimized_batches)}개 배치")
            return optimized_batches
            
        except Exception as e:
            logger.error(f"출금 배치 최적화 실패: {str(e)}")
            raise
    
    def _estimate_energy_cost(self, amount: Decimal) -> Decimal:
        """출금 금액에 따른 예상 에너지 비용을 계산합니다."""
        # 기본 TRC20 전송 비용 + 금액 비례 추가 비용
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
            wait_hours = (datetime.utcnow() - withdrawal.created_at).total_seconds() / 3600
            priority_score += min(int(wait_hours), 24)  # 최대 24시간 보너스
        
        return priority_score
    
    # === 화이트리스트 관리 ===
    
    async def create_whitelist_entry(
        self,
        policy_id: int,
        whitelist_data: Dict[str, Any],
        admin_id: int
    ) -> WithdrawalWhitelist:
        """화이트리스트 항목을 생성합니다."""
        try:
            # 중복 주소 확인
            existing_result = await self.db.execute(
                select(WithdrawalWhitelist).where(
                    and_(
                        WithdrawalWhitelist.policy_id == policy_id,
                        WithdrawalWhitelist.address == whitelist_data['address']
                    )
                )
            )
            existing_entry = existing_result.scalar_one_or_none()
            
            if existing_entry:
                raise ValidationError(f"이미 등록된 주소입니다: {whitelist_data['address']}")
            
            # 화이트리스트 항목 생성
            whitelist_entry = WithdrawalWhitelist(
                policy_id=policy_id,
                address=whitelist_data['address'],
                address_label=whitelist_data.get('label'),
                max_daily_amount=whitelist_data.get('max_daily_amount'),
                max_monthly_amount=whitelist_data.get('max_monthly_amount'),
                is_active=whitelist_data.get('is_active', True),
                verified_at=datetime.utcnow(),
                verified_by=admin_id
            )
            
            self.db.add(whitelist_entry)
            await self.db.commit()
            await self.db.refresh(whitelist_entry)
            
            logger.info(f"화이트리스트 항목 생성: {whitelist_entry.id} -> {whitelist_entry.address}")
            return whitelist_entry
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"화이트리스트 항목 생성 실패: {str(e)}")
            raise
    
    async def get_whitelist_entries(
        self,
        policy_id: int,
        active_only: bool = False
    ) -> List[WithdrawalWhitelist]:
        """화이트리스트 항목들을 조회합니다."""
        query = select(WithdrawalWhitelist).where(
            WithdrawalWhitelist.policy_id == policy_id
        )
        
        if active_only:
            query = query.where(WithdrawalWhitelist.is_active == True)
        
        result = await self.db.execute(query.order_by(WithdrawalWhitelist.created_at.desc()))
        return list(result.scalars().all())
    
    async def delete_whitelist_entry(
        self,
        whitelist_id: int,
        partner_id: str,
        admin_id: int
    ) -> bool:
        """화이트리스트 항목을 삭제합니다."""
        try:
            # 권한 확인을 위해 정책과 함께 조회
            result = await self.db.execute(
                select(WithdrawalWhitelist)
                .join(PartnerWithdrawalPolicy)
                .where(
                    and_(
                        WithdrawalWhitelist.id == whitelist_id,
                        PartnerWithdrawalPolicy.partner_id == partner_id
                    )
                )
            )
            whitelist_entry = result.scalar_one_or_none()
            
            if not whitelist_entry:
                return False
            
            await self.db.delete(whitelist_entry)
            await self.db.commit()
            
            logger.info(f"화이트리스트 항목 삭제: {whitelist_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"화이트리스트 항목 삭제 실패: {str(e)}")
            raise

    # === 승인 규칙 관리 ===
    
    # === 승인 규칙 관리 ===
    
    async def create_approval_rule(
        self,
        policy_id: int,
        rule_data: Dict[str, Any],
        admin_id: int
    ) -> WithdrawalApprovalRule:
        """승인 규칙을 생성합니다."""
        try:
            # 승인 규칙 생성
            approval_rule = WithdrawalApprovalRule(
                policy_id=policy_id,
                rule_type=rule_data['rule_type'],
                rule_name=rule_data['rule_name'],
                conditions=rule_data.get('conditions', {}),
                actions=rule_data.get('actions', {}),
                priority=rule_data.get('priority', 1),
                is_active=rule_data.get('is_active', True),
                created_by=admin_id
            )
            
            self.db.add(approval_rule)
            await self.db.commit()
            await self.db.refresh(approval_rule)
            
            logger.info(f"승인 규칙 생성: {approval_rule.id} -> {approval_rule.rule_name}")
            return approval_rule
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"승인 규칙 생성 실패: {str(e)}")
            raise
    
    async def get_approval_rules(
        self,
        policy_id: int,
        active_only: bool = False
    ) -> List[WithdrawalApprovalRule]:
        """승인 규칙들을 조회합니다."""
        query = select(WithdrawalApprovalRule).where(
            WithdrawalApprovalRule.policy_id == policy_id
        )
        
        if active_only:
            query = query.where(WithdrawalApprovalRule.is_active == True)
        
        result = await self.db.execute(query.order_by(WithdrawalApprovalRule.priority.desc()))
        return list(result.scalars().all())
    
    async def get_pending_batches(
        self,
        partner_id: str,
        limit: int = 10
    ) -> List[WithdrawalBatch]:
        """대기 중인 배치들을 조회합니다."""
        result = await self.db.execute(
            select(WithdrawalBatch)
            .where(
                and_(
                    WithdrawalBatch.partner_id == partner_id,
                    WithdrawalBatch.status == "pending"
                )
            )
            .order_by(WithdrawalBatch.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def execute_batch_with_tronlink(
        self,
        batch_id: str,
        partner_id: str
    ) -> Dict[str, Any]:
        """TronLink를 사용하여 배치를 실행합니다."""
        try:
            # 배치 조회
            batch_result = await self.db.execute(
                select(WithdrawalBatch).where(
                    and_(
                        WithdrawalBatch.id == batch_id,
                        WithdrawalBatch.partner_id == partner_id
                    )
                )
            )
            batch = batch_result.scalar_one_or_none()
            
            if not batch:
                raise NotFoundError(f"배치를 찾을 수 없습니다: {batch_id}")
            
            # 배치 상태 업데이트
            batch.status = "processing"
            batch.started_at = datetime.utcnow()
            
            # 여기서 실제 TronLink 자동 서명 로직 구현
            # 임시로 성공 응답 반환
            
            await self.db.commit()
            
            return {
                "batch_id": batch_id,
                "status": "processing",
                "started_at": batch.started_at.isoformat(),
                "message": "배치 실행이 시작되었습니다"
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"배치 실행 실패: {str(e)}")
            raise
