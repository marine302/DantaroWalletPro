"""
파트너사 출금 관리 서비스 - Doc #28
파트너사별 유연한 출금 정책 및 자동화를 제공합니다.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.models.withdrawal import WithdrawalBatch
from app.models.withdrawal_policy import (
    PartnerWithdrawalPolicy,
    WithdrawalApprovalRule,
    WithdrawalWhitelist,
)

from .approval_engine import ApprovalEngine
from .batch_manager import BatchManager
from .batch_optimizer import BatchOptimizer

# 모듈화된 컴포넌트들 import
from .policy_manager import PolicyManager

logger = get_logger(__name__)


class PartnerWithdrawalService:
    """파트너사 출금 관리 서비스 - 모든 로직을 모듈화된 컴포넌트에 위임"""

    def __init__(self, db: AsyncSession):
        self.db = db

        # 모듈화된 컴포넌트들 초기화
        self.policy_manager = PolicyManager(db)
        self.approval_engine = ApprovalEngine(db)
        self.batch_manager = BatchManager(db)
        self.batch_optimizer = BatchOptimizer(db)

    # === 출금 정책 관리 ===

    async def create_withdrawal_policy(
        self, partner_id: str, policy_data: Dict[str, Any], admin_id: int
    ) -> PartnerWithdrawalPolicy:
        """파트너사 출금 정책을 생성합니다."""
        return await self.policy_manager.create_withdrawal_policy(
            partner_id, policy_data, admin_id
        )

    async def get_withdrawal_policy(
        self, partner_id: str
    ) -> Optional[PartnerWithdrawalPolicy]:
        """파트너사 출금 정책을 조회합니다."""
        return await self.policy_manager.get_withdrawal_policy(partner_id)

    async def update_withdrawal_policy(
        self, partner_id: str, update_data: Dict[str, Any], admin_id: int
    ) -> PartnerWithdrawalPolicy:
        """파트너사 출금 정책을 업데이트합니다."""
        return await self.policy_manager.update_withdrawal_policy(
            partner_id, update_data, admin_id
        )

    # === 실시간 출금 자동 승인 규칙 엔진 ===

    async def evaluate_withdrawal_request(
        self, withdrawal_id: int, partner_id: str
    ) -> Dict[str, Any]:
        """출금 요청을 평가하고 자동 승인 여부를 결정합니다."""
        return await self.approval_engine.evaluate_withdrawal_request(
            withdrawal_id, partner_id
        )

    async def create_approval_rule(
        self, policy_id: int, rule_data: Dict[str, Any], admin_id: int
    ) -> WithdrawalApprovalRule:
        """승인 규칙을 생성합니다."""
        return await self.approval_engine.create_approval_rule(
            policy_id, rule_data, admin_id
        )

    async def get_approval_rules(
        self, policy_id: int, active_only: bool = False
    ) -> List[WithdrawalApprovalRule]:
        """승인 규칙들을 조회합니다."""
        return await self.approval_engine.get_approval_rules(policy_id, active_only)

    # === 일괄 출금 스케줄 관리 ===

    async def create_withdrawal_batch(
        self,
        partner_id: str,
        withdrawal_ids: List[int],
        scheduled_time: Optional[datetime] = None,
    ) -> WithdrawalBatch:
        """출금 배치를 생성합니다."""
        return await self.batch_manager.create_withdrawal_batch(
            partner_id, withdrawal_ids, scheduled_time
        )

    async def get_pending_batches(
        self, partner_id: str, limit: int = 10
    ) -> List[WithdrawalBatch]:
        """대기 중인 배치들을 조회합니다."""
        return await self.batch_manager.get_pending_batches(partner_id, limit)

    async def execute_batch_with_tronlink(
        self, batch_id: str, partner_id: str
    ) -> Dict[str, Any]:
        """TronLink를 사용하여 배치를 실행합니다."""
        return await self.batch_manager.execute_batch_with_tronlink(
            batch_id, partner_id
        )

    # === 출금 요청 그룹핑 및 배치 최적화 ===

    async def optimize_withdrawal_batches(
        self, partner_id: str, max_batches: int = 10
    ) -> List[Dict[str, Any]]:
        """파트너사의 대기 중인 출금 요청들을 최적화된 배치로 그룹핑합니다."""
        return await self.batch_optimizer.optimize_withdrawal_batches(
            partner_id, max_batches
        )

    # === 화이트리스트 관리 ===

    async def create_whitelist_entry(
        self, policy_id: int, whitelist_data: Dict[str, Any], admin_id: int
    ) -> WithdrawalWhitelist:
        """화이트리스트 항목을 생성합니다."""
        return await self.policy_manager.create_whitelist_entry(
            policy_id, whitelist_data, admin_id
        )

    async def get_whitelist_entries(
        self, policy_id: int, active_only: bool = False
    ) -> List[WithdrawalWhitelist]:
        """화이트리스트 항목들을 조회합니다."""
        return await self.policy_manager.get_whitelist_entries(policy_id, active_only)

    async def delete_whitelist_entry(
        self, whitelist_id: int, partner_id: str, admin_id: int
    ) -> bool:
        """화이트리스트 항목을 삭제합니다."""
        return await self.policy_manager.delete_whitelist_entry(
            whitelist_id, partner_id, admin_id
        )
