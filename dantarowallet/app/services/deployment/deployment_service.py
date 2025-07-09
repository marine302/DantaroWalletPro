"""
슈퍼 어드민용 배포 자동화 서비스 (모듈화된 버전)
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.schemas.deployment import (
    DeploymentResult, DeploymentStatus, PartnerTemplate,
    OnboardingStep, DeploymentConfig
)

# 모듈화된 컴포넌트들 import
from .deployment_manager import DeploymentManager
from .partner_onboarding import PartnerOnboarding
from .config_validator import ConfigValidator
from .deployment_monitor import DeploymentMonitor


class DeploymentService:
    """배포 자동화 서비스 (모듈화된 버전)"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # 모듈화된 컴포넌트들 초기화
        self.deployment_manager = DeploymentManager(db)
        self.partner_onboarding = PartnerOnboarding(db)
        self.config_validator = ConfigValidator(db)
        self.deployment_monitor = DeploymentMonitor(db)
    
    # === 배포 관리 ===
    
    async def create_partner_instance(self, partner_id: str, template_type: str = "standard") -> DeploymentResult:
        """파트너 인스턴스 생성"""
        return await self.deployment_manager.create_partner_instance(partner_id, template_type)
    
    async def rollback_deployment(self, partner_id: str, reason: str) -> bool:
        """배포 롤백"""
        return await self.deployment_manager.rollback_deployment(partner_id, reason)
    
    def _get_deployment_status(self, deployment_config: Dict[str, Any]) -> str:
        """배포 상태 정보 반환 (호환성을 위한 메서드)"""
        return self.deployment_manager.get_deployment_status_info(deployment_config)
    
    # === 파트너 온보딩 ===
    
    async def get_onboarding_steps(self, partner_id: str) -> List[OnboardingStep]:
        """온보딩 단계 조회"""
        return await self.partner_onboarding.get_onboarding_steps(partner_id)
    
    async def complete_onboarding(self, partner_id: str) -> bool:
        """온보딩 완료"""
        return await self.partner_onboarding.complete_onboarding(partner_id)
    
    async def update_onboarding_step(self, partner_id: str, step_id: str, status: str) -> bool:
        """온보딩 단계 상태 업데이트"""
        return await self.partner_onboarding.update_onboarding_step(partner_id, step_id, status)
    
    def get_onboarding_progress(self, partner_id: str) -> dict:
        """온보딩 진행 상황 조회"""
        return self.partner_onboarding.get_onboarding_progress(partner_id)
    
    # === 설정 검증 ===
    
    async def configure_partner_environment(self, partner_id: str, config_data: Dict[str, Any]) -> bool:
        """파트너 환경 설정"""
        return await self.config_validator.configure_partner_environment(partner_id, config_data)
    
    async def setup_partner_database(self, partner_id: str) -> bool:
        """파트너 데이터베이스 설정"""
        return await self.config_validator.setup_partner_database(partner_id)
    
    def validate_configuration(self, config_data: Dict[str, Any]) -> List[str]:
        """설정 유효성 검증"""
        return self.config_validator.validate_configuration(config_data)
    
    def get_configuration_status(self, partner_id: str) -> Dict[str, Any]:
        """설정 상태 조회"""
        return self.config_validator.get_configuration_status(partner_id)
    
    # === 배포 모니터링 ===
    
    async def deploy_partner_templates(self, partner_id: str) -> DeploymentStatus:
        """파트너 템플릿 배포"""
        return await self.deployment_monitor.deploy_partner_templates(partner_id)
    
    async def get_deployment_status(self, partner_id: str) -> DeploymentStatus:
        """배포 상태 조회"""
        return await self.deployment_monitor.get_deployment_status(partner_id)
    
    async def get_all_deployments(self, 
                                status_filter: Optional[str] = None,
                                limit: int = 100,
                                offset: int = 0) -> List[Dict[str, Any]]:
        """모든 배포 상태 조회"""
        return await self.deployment_monitor.get_all_deployments(status_filter, limit, offset)
    
    async def create_deployment_template(self, template_data: PartnerTemplate) -> str:
        """배포 템플릿 생성"""
        return await self.deployment_monitor.create_deployment_template(template_data)
    
    async def get_deployment_templates(self) -> List[PartnerTemplate]:
        """배포 템플릿 목록 조회"""
        return await self.deployment_monitor.get_deployment_templates()
    
    def get_deployment_metrics(self) -> Dict[str, Any]:
        """배포 메트릭 조회"""
        return self.deployment_monitor.get_deployment_metrics()
    
    # === 통합 메서드들 ===
    
    async def full_partner_deployment(self, partner_id: str, config_data: Dict[str, Any]) -> DeploymentResult:
        """전체 파트너 배포 프로세스"""
        try:
            # 1. 설정 검증
            validation_errors = self.validate_configuration(config_data)
            if validation_errors:
                raise ValueError(f"Configuration validation failed: {validation_errors}")
            
            # 2. 환경 설정
            await self.configure_partner_environment(partner_id, config_data)
            
            # 3. 데이터베이스 설정
            await self.setup_partner_database(partner_id)
            
            # 4. 파트너 인스턴스 생성
            deployment_result = await self.create_partner_instance(partner_id, config_data.get("template_type", "standard"))
            
            # 5. 템플릿 배포
            await self.deploy_partner_templates(partner_id)
            
            return deployment_result
            
        except Exception as e:
            # 실패 시 롤백
            await self.rollback_deployment(partner_id, str(e))
            raise
    
    def get_service_health(self) -> Dict[str, Any]:
        """서비스 상태 확인"""
        try:
            metrics = self.get_deployment_metrics()
            return {
                "status": "healthy",
                "modules": {
                    "deployment_manager": "active",
                    "partner_onboarding": "active", 
                    "config_validator": "active",
                    "deployment_monitor": "active"
                },
                "metrics": metrics,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"
            }
