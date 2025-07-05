"""
관리자 패널 통합 서비스.
기존 AdminService와의 호환성을 유지하면서 모듈화된 구조를 제공합니다.
"""
from typing import Any, Dict, List, Optional

from app.schemas.admin import (
    PaginatedTransactionsResponse,
    PaginatedUsersResponse,
    SuspiciousActivityResponse,
    SystemRiskSummaryResponse,
    SystemStatsResponse,
    TransactionMonitorResponse,
    UserDetailResponse,
    UserRiskAnalysisResponse,
)
from app.services.admin.system_monitoring import SystemMonitoringService
from app.services.admin.transaction_monitoring import TransactionMonitoringService
from app.services.admin.user_management import UserManagementService
from sqlalchemy.ext.asyncio import AsyncSession


class AdminService:
    """관리자 패널 통합 서비스 클래스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._system_monitoring = SystemMonitoringService(db)
        self._user_management = UserManagementService(db)
        self._transaction_monitoring = TransactionMonitoringService(db)

    # 시스템 모니터링 관련 메서드들
    async def get_system_stats(self) -> SystemStatsResponse:
        """시스템 전체 통계 조회"""
        return await self._system_monitoring.get_system_stats()

    async def get_system_risk_summary(self) -> SystemRiskSummaryResponse:
        """시스템 전체 위험도 요약"""
        return await self._system_monitoring.get_system_risk_summary()

    # 사용자 관리 관련 메서드들
    async def get_users_list(
        self,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_admin: Optional[bool] = None,
    ) -> PaginatedUsersResponse:
        """사용자 목록 조회 (페이지네이션)"""
        return await self._user_management.get_users_list(
            page, size, search, is_active, is_admin
        )

    async def get_user_detail(self, user_id: int) -> Optional[UserDetailResponse]:
        """사용자 상세 정보 조회"""
        return await self._user_management.get_user_detail(user_id)

    async def update_user(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """사용자 정보 수정"""
        return await self._user_management.update_user(user_id, updates)

    async def get_user_risk_analysis(self, user_id: int) -> UserRiskAnalysisResponse:
        """사용자 위험도 분석"""
        return await self._user_management.get_user_risk_analysis(user_id)

    # 트랜잭션 모니터링 관련 메서드들
    async def get_transaction_monitor(
        self,
        page: int = 1,
        size: int = 50,
        status: Optional[str] = None,
        direction: Optional[str] = None,
        hours: int = 24,
    ) -> TransactionMonitorResponse:
        """트랜잭션 모니터링 데이터 조회"""
        return await self._transaction_monitoring.get_transaction_monitor(
            page, size, status, direction, hours
        )

    async def get_suspicious_activities(
        self,
        page: int = 1,
        size: int = 20,
        severity: Optional[str] = None,
        hours: int = 24,
    ) -> List[SuspiciousActivityResponse]:
        """의심스러운 활동 조회"""
        return await self._transaction_monitoring.get_suspicious_activities(
            page, size, severity, hours
        )
