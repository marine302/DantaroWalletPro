"""
실시간 출금 자동 승인 규칙 엔진
출금 요청을 평가하고 자동 승인 여부를 결정합니다.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload

from app.models.withdrawal import Withdrawal, WithdrawalStatus
from app.models.withdrawal_policy import PartnerWithdrawalPolicy, WithdrawalWhitelist, WithdrawalApprovalRule
from app.core.exceptions import NotFoundError
from app.core.logger import get_logger
from .utils import safe_bool, safe_decimal, safe_int, safe_str

logger = get_logger(__name__)


class ApprovalEngine:
    """출금 자동 승인 엔진"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
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
            policy_result = await self.db.execute(
                select(PartnerWithdrawalPolicy).where(
                    PartnerWithdrawalPolicy.partner_id == partner_id
                )
            )
            policy = policy_result.scalar_one_or_none()
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
            
            # 6. 위험 점수 계산
            risk_score = await self._calculate_risk_score(withdrawal, policy)
            risk_threshold = safe_int(policy.risk_score_threshold, 50)
            
            if risk_score > risk_threshold:
                evaluation_result['approval_reason'] = f'위험 점수 초과: {risk_score} > {risk_threshold}'
                evaluation_result['required_actions'].append('risk_review')
                evaluation_result['risk_score'] = risk_score
                return evaluation_result
            
            # 모든 조건을 통과한 경우 자동 승인
            evaluation_result.update({
                'can_auto_approve': True,
                'approval_reason': '모든 자동 승인 조건 충족',
                'risk_score': risk_score,
                'policy_applied': safe_str(policy.policy_type)
            })
            
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
            # 1. 금액 기반 위험 점수
            amount = safe_decimal(withdrawal.amount)
            if amount > Decimal('10000'):
                risk_score += 30
            elif amount > Decimal('5000'):
                risk_score += 20
            elif amount > Decimal('1000'):
                risk_score += 10
            
            # 2. 주소 기반 위험 점수 (새로운 주소일수록 높음)
            address_history_result = await self.db.execute(
                select(func.count(Withdrawal.id))
                .where(
                    and_(
                        Withdrawal.user_id == safe_int(withdrawal.user_id),
                        Withdrawal.to_address == safe_str(withdrawal.to_address),
                        Withdrawal.status == WithdrawalStatus.COMPLETED
                    )
                )
            )
            address_usage_count = address_history_result.scalar() or 0
            
            if address_usage_count == 0:
                risk_score += 25  # 완전히 새로운 주소
            elif address_usage_count < 3:
                risk_score += 15  # 거의 사용하지 않은 주소
            elif address_usage_count < 10:
                risk_score += 5   # 가끔 사용하는 주소
            # 자주 사용하는 주소는 위험 점수 추가 없음
            
            # 3. 시간 기반 위험 점수 (업무 시간 외에는 위험도 증가)
            current_hour = datetime.utcnow().hour
            if current_hour < 6 or current_hour > 22:  # 새벽/밤 시간대
                risk_score += 10
            elif current_hour < 9 or current_hour > 18:  # 업무 시간 외
                risk_score += 5
            
            # 4. 빈도 기반 위험 점수 (최근 출금이 많으면 위험도 증가)
            recent_count_result = await self.db.execute(
                select(func.count(Withdrawal.id))
                .where(
                    and_(
                        Withdrawal.user_id == safe_int(withdrawal.user_id),
                        Withdrawal.created_at >= datetime.utcnow() - timedelta(hours=24),
                        Withdrawal.status.in_([
                            WithdrawalStatus.COMPLETED,
                            WithdrawalStatus.PROCESSING,
                            WithdrawalStatus.APPROVED
                        ])
                    )
                )
            )
            recent_withdrawals = recent_count_result.scalar() or 0
            
            if recent_withdrawals > 5:
                risk_score += 20
            elif recent_withdrawals > 3:
                risk_score += 10
            elif recent_withdrawals > 1:
                risk_score += 5
            
            return min(risk_score, 100)  # 최대 100점으로 제한
            
        except Exception as e:
            logger.error(f"위험 점수 계산 실패: {str(e)}")
            return 50  # 오류 시 중간 위험도로 설정
    
    async def create_approval_rule(
        self,
        policy_id: int,
        rule_data: Dict[str, Any],
        admin_id: int
    ) -> 'WithdrawalApprovalRule':
        """승인 규칙을 생성합니다."""
        from app.models.withdrawal_policy import WithdrawalApprovalRule
        
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
    ) -> List['WithdrawalApprovalRule']:
        """승인 규칙들을 조회합니다."""
        from app.models.withdrawal_policy import WithdrawalApprovalRule
        
        query = select(WithdrawalApprovalRule).where(
            WithdrawalApprovalRule.policy_id == policy_id
        )
        
        if active_only:
            query = query.where(WithdrawalApprovalRule.is_active == True)
        
        result = await self.db.execute(query.order_by(WithdrawalApprovalRule.priority.desc()))
        return list(result.scalars().all())
