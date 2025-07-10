"""
파트너사 온보딩 자동화 서비스 - Doc #29 (간소화 버전)
새 파트너사의 온보딩 프로세스를 관리합니다.
"""
from typing import Dict, List, Optional, Any, Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, and_

from app.models.partner import Partner
from app.models.partner_onboarding import (
    PartnerOnboarding, OnboardingStep, OnboardingChecklist, OnboardingLog,
    OnboardingStatus, OnboardingStepStatus, ChecklistCategory
)
from app.core.logger import get_logger

logger = get_logger(__name__)


class SimpleOnboardingService:
    """간소화된 온보딩 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_onboarding(
        self,
        partner_id: str,
        configuration_data: Dict[str, Any]
    ) -> PartnerOnboarding:
        """온보딩 프로세스 생성"""
        try:
            # 기존 온보딩 확인
            existing_result = await self.db.execute(
                select(PartnerOnboarding).where(
                    PartnerOnboarding.partner_id == partner_id
                )
            )
            existing_onboarding = existing_result.scalar_one_or_none()
            
            if existing_onboarding:
                raise ValueError(f"파트너 {partner_id}의 온보딩이 이미 존재합니다.")
            
            # 온보딩 생성
            onboarding = PartnerOnboarding(
                partner_id=partner_id,
                status=OnboardingStatus.PENDING,
                configuration_data=configuration_data,
                auto_proceed=configuration_data.get("auto_proceed", True),
                notification_email=configuration_data.get("notification_email"),
                notification_webhook=configuration_data.get("notification_webhook")
            )
            
            self.db.add(onboarding)
            await self.db.flush()
            
            # 온보딩 단계 생성
            steps = [
                ("파트너 등록", "기본 정보 수집 및 계약 조건 합의", 30),
                ("계정 생성", "파트너 계정 및 API 키 생성", 15),
                ("지갑 설정", "TronLink 연동 및 지갑 등록", 45),
                ("시스템 구성", "에너지 풀 및 수수료 정책 설정", 20),
                ("템플릿 배포", "관리자 대시보드 및 브랜딩 적용", 30),
                ("검증 및 활성화", "시스템 통합 테스트 및 라이브 활성화", 60)
            ]
            
            for idx, (name, description, duration) in enumerate(steps, 1):
                step = OnboardingStep(
                    onboarding_id=onboarding.id,
                    step_number=idx,
                    step_name=name,
                    step_description=description,
                    estimated_duration=duration,
                    is_automated=True
                )
                self.db.add(step)
            
            # 체크리스트 생성
            await self._create_checklist(onboarding.id)
            
            await self.db.commit()
            return onboarding
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"온보딩 생성 실패: {e}")
            raise
    
    async def get_onboarding_status(self, partner_id: str) -> Optional[PartnerOnboarding]:
        """온보딩 상태 조회"""
        result = await self.db.execute(
            select(PartnerOnboarding).where(
                PartnerOnboarding.partner_id == partner_id
            )
        )
        return result.scalar_one_or_none()
    
    async def update_step_status(
        self,
        onboarding_id: int,
        step_number: int,
        status: OnboardingStepStatus,
        result_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """단계 상태 업데이트"""
        try:
            update_values: Dict[str, Any] = {"status": status.value}
            
            if status == OnboardingStepStatus.RUNNING:
                update_values["started_at"] = datetime.utcnow()
            elif status == OnboardingStepStatus.COMPLETED:
                update_values["completed_at"] = datetime.utcnow()
                if result_data:
                    update_values["result_data"] = result_data
            elif status == OnboardingStepStatus.FAILED:
                if error_message:
                    update_values["error_message"] = error_message
            
            await self.db.execute(
                update(OnboardingStep)
                .where(
                    and_(
                        OnboardingStep.onboarding_id == onboarding_id,
                        OnboardingStep.step_number == step_number
                    )
                )
                .values(**update_values)
            )
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"단계 상태 업데이트 실패: {e}")
            return False
    
    async def update_onboarding_progress(
        self,
        onboarding_id: int,
        current_step: int,
        progress_percentage: int,
        status: Optional[OnboardingStatus] = None
    ) -> bool:
        """온보딩 진행률 업데이트"""
        try:
            update_values: Dict[str, Any] = {
                "current_step": current_step,
                "progress_percentage": progress_percentage,
                "updated_at": datetime.utcnow()
            }
            
            if status:
                update_values["status"] = status.value
                if status == OnboardingStatus.COMPLETED:
                    update_values["completed_at"] = datetime.utcnow()
            
            await self.db.execute(
                update(PartnerOnboarding)
                .where(PartnerOnboarding.id == onboarding_id)
                .values(**update_values)
            )
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"온보딩 진행률 업데이트 실패: {e}")
            return False
    
    async def complete_onboarding(self, onboarding_id: int) -> bool:
        """온보딩 완료 처리"""
        try:
            # 온보딩 완료 상태로 업데이트
            await self.db.execute(
                update(PartnerOnboarding)
                .where(PartnerOnboarding.id == onboarding_id)
                .values(
                    status=OnboardingStatus.COMPLETED.value,
                    progress_percentage=100,
                    completed_at=datetime.utcnow(),
                    testing_completed=True
                )
            )
            
            # 파트너 활성화
            onboarding_result = await self.db.execute(
                select(PartnerOnboarding).where(PartnerOnboarding.id == onboarding_id)
            )
            onboarding = onboarding_result.scalar_one_or_none()
            
            if onboarding:
                await self.db.execute(
                    update(Partner)
                    .where(Partner.id == onboarding.partner_id)
                    .values(
                        status="active",
                        activated_at=datetime.utcnow()
                    )
                )
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"온보딩 완료 처리 실패: {e}")
            return False
    
    async def add_onboarding_log(
        self,
        onboarding_id: int,
        level: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        step_number: Optional[int] = None
    ) -> bool:
        """온보딩 로그 추가"""
        try:
            log = OnboardingLog(
                onboarding_id=onboarding_id,
                level=level,
                message=message,
                details=details or {},
                step_number=step_number,
                actor="system"
            )
            
            self.db.add(log)
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"온보딩 로그 추가 실패: {e}")
            return False
    
    async def update_checklist_item(
        self,
        onboarding_id: int,
        item_name: str,
        is_completed: bool,
        completed_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """체크리스트 항목 업데이트"""
        try:
            update_values: Dict[str, Any] = {
                "is_completed": is_completed,
                "updated_at": datetime.utcnow()
            }
            
            if is_completed:
                update_values["completed_at"] = datetime.utcnow()
                if completed_by:
                    update_values["completed_by"] = completed_by
            
            if notes:
                update_values["notes"] = notes
            
            await self.db.execute(
                update(OnboardingChecklist)
                .where(
                    and_(
                        OnboardingChecklist.onboarding_id == onboarding_id,
                        OnboardingChecklist.item_name == item_name
                    )
                )
                .values(**update_values)
            )
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"체크리스트 항목 업데이트 실패: {e}")
            return False
    
    async def get_onboarding_steps(self, onboarding_id: int) -> List[OnboardingStep]:
        """온보딩 단계 목록 조회"""
        result = await self.db.execute(
            select(OnboardingStep)
            .where(OnboardingStep.onboarding_id == onboarding_id)
            .order_by(OnboardingStep.step_number)
        )
        return list(result.scalars().all())
    
    async def get_onboarding_checklist(self, onboarding_id: int) -> List[OnboardingChecklist]:
        """온보딩 체크리스트 조회"""
        result = await self.db.execute(
            select(OnboardingChecklist)
            .where(OnboardingChecklist.onboarding_id == onboarding_id)
            .order_by(OnboardingChecklist.category, OnboardingChecklist.item_name)
        )
        return list(result.scalars().all())
    
    async def get_onboarding_logs(self, onboarding_id: int) -> List[OnboardingLog]:
        """온보딩 로그 조회"""
        result = await self.db.execute(
            select(OnboardingLog)
            .where(OnboardingLog.onboarding_id == onboarding_id)
            .order_by(OnboardingLog.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def _create_checklist(self, onboarding_id):
        """기본 체크리스트 생성"""
        checklist_items = [
            # 보안 체크리스트
            (ChecklistCategory.SECURITY, "API 키 안전하게 저장", "API 키와 시크릿이 안전하게 보관되는지 확인", True),
            (ChecklistCategory.SECURITY, "2FA 설정 완료", "관리자 계정에 2단계 인증이 설정되었는지 확인", True),
            (ChecklistCategory.SECURITY, "IP 화이트리스트 설정", "허용된 IP 주소만 API 접근 가능하도록 설정", False),
            (ChecklistCategory.SECURITY, "웹훅 URL HTTPS 사용", "알림 웹훅이 HTTPS를 사용하는지 확인", True),
            
            # 통합 체크리스트
            (ChecklistCategory.INTEGRATION, "TronLink 지갑 연동", "TronLink 지갑이 올바르게 연동되었는지 확인", True),
            (ChecklistCategory.INTEGRATION, "API 연동 테스트 완료", "모든 API 엔드포인트가 정상 작동하는지 테스트", True),
            (ChecklistCategory.INTEGRATION, "웹훅 수신 테스트", "알림 웹훅이 정상적으로 수신되는지 테스트", True),
            (ChecklistCategory.INTEGRATION, "에러 처리 구현", "API 에러 상황에 대한 적절한 처리가 구현되었는지 확인", True),
            
            # 컴플라이언스 체크리스트
            (ChecklistCategory.COMPLIANCE, "이용약관 동의", "서비스 이용약관에 동의했는지 확인", True),
            (ChecklistCategory.COMPLIANCE, "개인정보처리방침 동의", "개인정보 처리 방침에 동의했는지 확인", True),
            (ChecklistCategory.COMPLIANCE, "AML/KYC 정책 확인", "자금세탁방지 및 고객확인 정책을 이해했는지 확인", True),
            (ChecklistCategory.COMPLIANCE, "데이터 보관 정책 확인", "데이터 보관 및 삭제 정책을 이해했는지 확인", False),
            
            # 기술 체크리스트
            (ChecklistCategory.TECHNICAL, "서버 환경 준비", "운영 서버 환경이 준비되었는지 확인", True),
            (ChecklistCategory.TECHNICAL, "모니터링 시스템 구축", "시스템 모니터링이 구축되었는지 확인", False),
            (ChecklistCategory.TECHNICAL, "백업 시스템 구축", "데이터 백업 시스템이 구축되었는지 확인", False),
        ]
        
        for category, item_name, description, is_required in checklist_items:
            checklist = OnboardingChecklist(
                onboarding_id=onboarding_id,
                category=category,
                item_name=item_name,
                item_description=description,
                is_required=is_required,
                is_automated=True  # 자동으로 완료되는 항목들
            )
            self.db.add(checklist)
