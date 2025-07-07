# Copilot 문서 #29: 파트너사 온보딩 자동화

## 목표
새 파트너사의 완전 자동화된 온보딩 프로세스를 구축합니다. 파트너 계정 자동 생성 및 설정, TronLink 지갑 연동 가이드, 초기 에너지 풀 설정 지원, API 키 발급 및 보안 설정, 템플릿 배포 자동화, 온보딩 체크리스트 및 검증을 포함한 통합 시스템을 구현합니다.

## 전제 조건
- Copilot 문서 #24-28이 완료되어 있어야 합니다
- 파트너사 관리 시스템이 구현되어 있어야 합니다
- TronLink 연동 시스템이 작동 중이어야 합니다
- 에너지 풀 및 수수료 관리가 구현되어 있어야 합니다

## 🎯 온보딩 자동화 구조

### 📋 온보딩 프로세스 플로우
```
파트너사 온보딩 자동화
├── 📝 Step 1: 파트너 등록
│   ├── 기본 정보 수집
│   ├── 계약 조건 합의
│   ├── 법적 문서 서명
│   └── 초기 결제 처리
├── 🔐 Step 2: 계정 생성
│   ├── 파트너 계정 생성
│   ├── 관리자 계정 설정
│   ├── API 키/시크릿 발급
│   └── 보안 설정 초기화
├── 💼 Step 3: 지갑 설정
│   ├── TronLink 연동 가이드
│   ├── 메인 지갑 등록
│   ├── 운영 지갑 설정
│   └── 지갑 검증 테스트
├── ⚡ Step 4: 시스템 구성
│   ├── 에너지 풀 정책 설정
│   ├── 수수료 구조 설정
│   ├── 출금 정책 구성
│   └── 알림 설정
├── 🚀 Step 5: 템플릿 배포
│   ├── 관리자 대시보드 생성
│   ├── API 문서 커스터마이징
│   ├── 브랜딩 적용
│   └── 샘플 데이터 생성
└── ✅ Step 6: 검증 및 활성화
    ├── 시스템 통합 테스트
    ├── API 연동 검증
    ├── 보안 체크리스트
    └── 라이브 환경 활성화
```

## 🛠️ 구현 단계

### Phase 1: 온보딩 워크플로우 엔진 (2일)

#### 1.1 온보딩 프로세스 모델
```python
# app/models/partner_onboarding.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

class OnboardingStatus(enum.Enum):
    PENDING = "pending"              # 대기 중
    REGISTRATION = "registration"    # 등록 진행
    ACCOUNT_SETUP = "account_setup" # 계정 설정
    WALLET_SETUP = "wallet_setup"   # 지갑 설정
    SYSTEM_CONFIG = "system_config" # 시스템 구성
    DEPLOYMENT = "deployment"       # 배포 중
    TESTING = "testing"            # 테스트 중
    COMPLETED = "completed"        # 완료
    FAILED = "failed"              # 실패

class PartnerOnboarding(Base):
    """파트너 온보딩 프로세스"""
    __tablename__ = "partner_onboardings"
    
    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey("partners.id"))
    status = Column(Enum(OnboardingStatus), default=OnboardingStatus.PENDING)
    
    # 진행 상태
    current_step = Column(Integer, default=1)
    total_steps = Column(Integer, default=6)
    progress_percentage = Column(Integer, default=0)
    
    # 단계별 완료 상태
    registration_completed = Column(Boolean, default=False)
    account_setup_completed = Column(Boolean, default=False)
    wallet_setup_completed = Column(Boolean, default=False)
    system_config_completed = Column(Boolean, default=False)
    deployment_completed = Column(Boolean, default=False)
    testing_completed = Column(Boolean, default=False)
    
    # 설정 데이터
    configuration_data = Column(JSON, default=dict)
    deployment_info = Column(JSON, default=dict)
    
    # 타임스탬프
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # 관계
    partner = relationship("Partner", back_populates="onboarding")
    steps = relationship("OnboardingStep", back_populates="onboarding")
    checklist = relationship("OnboardingChecklist", back_populates="onboarding")

class OnboardingStep(Base):
    """온보딩 단계 상세"""
    __tablename__ = "onboarding_steps"
    
    id = Column(Integer, primary_key=True)
    onboarding_id = Column(Integer, ForeignKey("partner_onboardings.id"))
    step_number = Column(Integer, nullable=False)
    step_name = Column(String(100), nullable=False)
    status = Column(String(20), default="pending")
    
    # 실행 정보
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    result_data = Column(JSON)
    
    onboarding = relationship("PartnerOnboarding", back_populates="steps")

class OnboardingChecklist(Base):
    """온보딩 체크리스트"""
    __tablename__ = "onboarding_checklists"
    
    id = Column(Integer, primary_key=True)
    onboarding_id = Column(Integer, ForeignKey("partner_onboardings.id"))
    category = Column(String(50))  # "security", "integration", "compliance"
    item_name = Column(String(200))
    is_required = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    notes = Column(Text)
    
    onboarding = relationship("PartnerOnboarding", back_populates="checklist")
```

#### 1.2 온보딩 워크플로우 서비스
```python
# app/services/onboarding_workflow_service.py
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models import (
    Partner, PartnerOnboarding, OnboardingStep,
    OnboardingChecklist, OnboardingStatus
)
from app.services.partner_service import PartnerService
from app.services.wallet_service import WalletService
from app.services.deployment_service import DeploymentService
from app.core.logging import get_logger
import asyncio

logger = get_logger(__name__)

class OnboardingWorkflowService:
    """온보딩 워크플로우 관리 서비스"""
    
    def __init__(
        self,
        db: Session,
        partner_service: PartnerService,
        wallet_service: WalletService,
        deployment_service: DeploymentService
    ):
        self.db = db
        self.partner_service = partner_service
        self.wallet_service = wallet_service
        self.deployment_service = deployment_service
        
        # 온보딩 단계 정의
        self.steps = [
            {
                "number": 1,
                "name": "파트너 등록",
                "handler": self._handle_registration
            },
            {
                "number": 2,
                "name": "계정 생성",
                "handler": self._handle_account_setup
            },
            {
                "number": 3,
                "name": "지갑 설정",
                "handler": self._handle_wallet_setup
            },
            {
                "number": 4,
                "name": "시스템 구성",
                "handler": self._handle_system_config
            },
            {
                "number": 5,
                "name": "템플릿 배포",
                "handler": self._handle_deployment
            },
            {
                "number": 6,
                "name": "검증 및 활성화",
                "handler": self._handle_testing
            }
        ]
    
    async def start_onboarding(
        self,
        partner_data: Dict
    ) -> PartnerOnboarding:
        """온보딩 프로세스 시작"""
        try:
            # 파트너 생성
            partner = await self.partner_service.create_partner(partner_data)
            
            # 온보딩 프로세스 생성
            onboarding = PartnerOnboarding(
                partner_id=partner.id,
                status=OnboardingStatus.REGISTRATION,
                configuration_data=partner_data
            )
            
            self.db.add(onboarding)
            self.db.flush()
            
            # 온보딩 단계 생성
            for step in self.steps:
                step_record = OnboardingStep(
                    onboarding_id=onboarding.id,
                    step_number=step["number"],
                    step_name=step["name"]
                )
                self.db.add(step_record)
            
            # 체크리스트 생성
            await self._create_checklist(onboarding.id)
            
            self.db.commit()
            
            # 첫 번째 단계 실행
            await self._execute_next_step(onboarding)
            
            return onboarding
            
        except Exception as e:
            logger.error(f"온보딩 시작 실패: {e}")
            self.db.rollback()
            raise
    
    async def _execute_next_step(
        self,
        onboarding: PartnerOnboarding
    ):
        """다음 단계 실행"""
        try:
            current_step = self.steps[onboarding.current_step - 1]
            step_record = self.db.query(OnboardingStep).filter(
                OnboardingStep.onboarding_id == onboarding.id,
                OnboardingStep.step_number == onboarding.current_step
            ).first()
            
            # 단계 시작
            step_record.status = "running"
            step_record.started_at = datetime.utcnow()
            self.db.commit()
            
            # 핸들러 실행
            result = await current_step["handler"](onboarding)
            
            # 단계 완료
            step_record.status = "completed"
            step_record.completed_at = datetime.utcnow()
            step_record.result_data = result
            
            # 진행률 업데이트
            onboarding.progress_percentage = int(
                (onboarding.current_step / onboarding.total_steps) * 100
            )
            
            # 다음 단계로 이동
            if onboarding.current_step < onboarding.total_steps:
                onboarding.current_step += 1
                await self._execute_next_step(onboarding)
            else:
                onboarding.status = OnboardingStatus.COMPLETED
                onboarding.completed_at = datetime.utcnow()
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"단계 실행 실패: {e}")
            step_record.status = "failed"
            step_record.error_message = str(e)
            onboarding.status = OnboardingStatus.FAILED
            self.db.commit()
            raise
    
    async def _handle_registration(
        self,
        onboarding: PartnerOnboarding
    ) -> Dict:
        """Step 1: 파트너 등록 처리"""
        partner = onboarding.partner
        
        # 계약 문서 생성
        contract_id = await self._generate_contract(partner)
        
        # 결제 정보 설정
        payment_info = await self._setup_payment(partner)
        
        onboarding.registration_completed = True
        
        return {
            "contract_id": contract_id,
            "payment_info": payment_info
        }
    
    async def _handle_account_setup(
        self,
        onboarding: PartnerOnboarding
    ) -> Dict:
        """Step 2: 계정 생성"""
        partner = onboarding.partner
        
        # API 키 생성
        api_credentials = await self.partner_service.generate_api_credentials(
            partner.id
        )
        
        # 관리자 계정 생성
        admin_account = await self._create_admin_account(partner)
        
        # 보안 설정
        security_config = await self._setup_security(partner)
        
        onboarding.account_setup_completed = True
        
        return {
            "api_key": api_credentials["api_key"],
            "admin_account": admin_account,
            "security_config": security_config
        }
    
    async def _handle_wallet_setup(
        self,
        onboarding: PartnerOnboarding
    ) -> Dict:
        """Step 3: 지갑 설정"""
        partner = onboarding.partner
        
        # TronLink 연동 가이드 URL 생성
        guide_url = await self._generate_wallet_guide(partner)
        
        # 지갑 등록 대기
        wallet_info = await self._wait_for_wallet_registration(partner)
        
        # 지갑 검증
        validation_result = await self.wallet_service.validate_partner_wallet(
            partner.id,
            wallet_info["address"]
        )
        
        onboarding.wallet_setup_completed = True
        
        return {
            "guide_url": guide_url,
            "wallet_address": wallet_info["address"],
            "validation": validation_result
        }
    
    async def _handle_system_config(
        self,
        onboarding: PartnerOnboarding
    ) -> Dict:
        """Step 4: 시스템 구성"""
        partner = onboarding.partner
        
        # 에너지 풀 정책 설정
        energy_policy = await self._setup_energy_policy(partner)
        
        # 수수료 구조 설정
        fee_structure = await self._setup_fee_structure(partner)
        
        # 출금 정책 설정
        withdrawal_policy = await self._setup_withdrawal_policy(partner)
        
        # 알림 설정
        notification_config = await self._setup_notifications(partner)
        
        onboarding.system_config_completed = True
        
        return {
            "energy_policy": energy_policy,
            "fee_structure": fee_structure,
            "withdrawal_policy": withdrawal_policy,
            "notifications": notification_config
        }
    
    async def _handle_deployment(
        self,
        onboarding: PartnerOnboarding
    ) -> Dict:
        """Step 5: 템플릿 배포"""
        partner = onboarding.partner
        
        # 관리자 대시보드 배포
        dashboard_url = await self.deployment_service.deploy_admin_dashboard(
            partner.id
        )
        
        # API 문서 커스터마이징
        api_docs_url = await self.deployment_service.customize_api_docs(
            partner.id
        )
        
        # 브랜딩 적용
        branding_result = await self._apply_branding(partner)
        
        # 샘플 데이터 생성
        sample_data = await self._create_sample_data(partner)
        
        onboarding.deployment_completed = True
        onboarding.deployment_info = {
            "dashboard_url": dashboard_url,
            "api_docs_url": api_docs_url,
            "branding": branding_result,
            "sample_data": sample_data
        }
        
        return onboarding.deployment_info
    
    async def _handle_testing(
        self,
        onboarding: PartnerOnboarding
    ) -> Dict:
        """Step 6: 검증 및 활성화"""
        partner = onboarding.partner
        
        # 통합 테스트 실행
        test_results = await self._run_integration_tests(partner)
        
        # 보안 체크리스트 검증
        security_check = await self._verify_security_checklist(onboarding)
        
        # 성능 테스트
        performance_test = await self._run_performance_test(partner)
        
        # 최종 활성화
        if all([
            test_results["passed"],
            security_check["passed"],
            performance_test["passed"]
        ]):
            await self.partner_service.activate_partner(partner.id)
            onboarding.testing_completed = True
        
        return {
            "integration_tests": test_results,
            "security_check": security_check,
            "performance_test": performance_test,
            "activated": onboarding.testing_completed
        }
    
    async def _create_checklist(self, onboarding_id: int):
        """온보딩 체크리스트 생성"""
        checklist_items = [
            # 보안 체크리스트
            ("security", "API 키 안전하게 저장", True),
            ("security", "2FA 설정 완료", True),
            ("security", "IP 화이트리스트 설정", False),
            ("security", "웹훅 URL HTTPS 사용", True),
            
            # 통합 체크리스트
            ("integration", "TronLink 지갑 연동", True),
            ("integration", "API 연동 테스트 완료", True),
            ("integration", "웹훅 수신 테스트", True),
            ("integration", "에러 처리 구현", True),
            
            # 컴플라이언스 체크리스트
            ("compliance", "이용약관 동의", True),
            ("compliance", "개인정보처리방침 동의", True),
            ("compliance", "AML/KYC 정책 확인", True),
            ("compliance", "데이터 보관 정책 확인", False)
        ]
        
        for category, item_name, is_required in checklist_items:
            checklist = OnboardingChecklist(
                onboarding_id=onboarding_id,
                category=category,
                item_name=item_name,
                is_required=is_required
            )
            self.db.add(checklist)