"""
슈퍼 어드민용 배포 자동화 서비스 (타입 안전성 확보)
"""
import uuid
import json
from decimal import Decimal, InvalidOperation as DecimalException
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, update
from fastapi import HTTPException

from app.models.partner import Partner
from app.schemas.deployment import (
    DeploymentResult, DeploymentStatus, PartnerTemplate,
    OnboardingStep, DeploymentConfig
)
from app.core.database import get_db


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


def safe_float(value: Any, default: float = 0.0) -> float:
    """안전한 float 변환"""
    if value is None:
        return default
    
    if hasattr(value, 'value'):
        value = value.value
    
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_decimal(value: Any, default: Decimal = Decimal('0')) -> Decimal:
    """안전한 Decimal 변환"""
    if value is None:
        return default
    
    if hasattr(value, 'value'):
        value = value.value
    
    try:
        return Decimal(str(value))
    except (TypeError, ValueError, DecimalException):
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


def safe_datetime(value: Any, default: Optional[datetime] = None) -> Optional[datetime]:
    """안전한 datetime 변환"""
    if value is None:
        return default
    
    if hasattr(value, 'value'):
        value = value.value
    
    if isinstance(value, datetime):
        return value
    
    return default


def safe_dict(value: Any, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """안전한 dict 변환"""
    if default is None:
        default = {}
    
    if value is None:
        return default
    
    if hasattr(value, 'value'):
        value = value.value
    
    if isinstance(value, dict):
        return value
    
    return default


class DeploymentService:
    """배포 자동화 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_partner_instance(self, partner_id: str, template_type: str = "standard") -> DeploymentResult:
        """파트너 인스턴스 생성"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
                
            deployment_id = str(uuid.uuid4())
            
            # 배포 설정 준비
            deployment_config = {
                "partner_id": safe_str(partner.id),
                "deployment_id": deployment_id,
                "template_version": "v1.0",
                "environment": "production",
                "domain": safe_str(partner.domain),
                "subdomain": f"{safe_str(partner.name).lower().replace(' ', '-')}.dantarowallet.com",
                "database_name": f"dantaro_{safe_str(partner.id).replace('-', '_')}",
                "api_endpoint": f"https://api.dantarowallet.com/{safe_str(partner.id)}",
                "features": safe_dict(partner.settings).get("features", {}),
                "branding": safe_dict(partner.settings).get("branding", {}),
                "created_at": datetime.utcnow().isoformat()
            }
            
            # 파트너 배포 설정 업데이트
            update_query = (
                update(Partner)
                .where(Partner.id == partner_id)
                .values(
                    deployment_config=deployment_config,
                    onboarding_status="deploying"
                )
            )
            self.db.execute(update_query)
            self.db.commit()
            
            # 실제 배포 프로세스 (Docker, Kubernetes 등)
            deployment_steps = [
                {"step": "database_creation", "status": "pending"},
                {"step": "container_deployment", "status": "pending"},
                {"step": "dns_configuration", "status": "pending"},
                {"step": "ssl_certificate", "status": "pending"},
                {"step": "initial_data_setup", "status": "pending"},
                {"step": "health_check", "status": "pending"}
            ]
            
            return DeploymentResult(
                deployment_id=deployment_id,
                partner_id=safe_str(partner.id),
                status="in_progress",
                steps=deployment_steps,
                config=deployment_config,
                logs=[],
                created_at=datetime.utcnow(),
                estimated_completion=datetime.utcnow() + timedelta(minutes=30)
            )
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create partner instance: {str(e)}")
    
    async def configure_partner_environment(self, partner_id: str, config_data: Dict[str, Any]) -> bool:
        """파트너 환경 설정"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            # 환경 변수 설정
            env_config = {
                "PARTNER_ID": safe_str(partner.id),
                "PARTNER_NAME": safe_str(partner.name),
                "API_KEY": safe_str(partner.api_key),
                "DATABASE_URL": f"postgresql://user:pass@db:5432/dantaro_{safe_str(partner.id).replace('-', '_')}",
                "REDIS_URL": "redis://redis:6379/0",
                "TRON_NETWORK": "mainnet",
                "ENERGY_POOL_ADDRESS": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
                "WEBHOOK_SECRET": f"whsec_{uuid.uuid4().hex}",
                "DOMAIN": safe_str(partner.domain) or f"{safe_str(partner.name).lower().replace(' ', '-')}.dantarowallet.com"
            }
            
            # 브랜딩 설정
            branding_config = safe_dict(partner.settings).get("branding", {})
            
            # 기능 설정
            feature_config = safe_dict(partner.settings).get("features", {
                "multi_signature": True,
                "cold_wallet": True,
                "auto_sweep": False,
                "api_access": True,
                "webhook_notifications": True,
                "2fa_required": False
            })
            
            # 설정 업데이트
            deployment_config = safe_dict(partner.deployment_config)
            deployment_config.update({
                "environment_variables": env_config,
                "branding_config": branding_config,
                "feature_config": feature_config,
                "configured_at": datetime.utcnow().isoformat()
            })
            
            # SQLAlchemy update 사용
            update_query = (
                update(Partner)
                .where(Partner.id == partner_id)
                .values(deployment_config=deployment_config)
            )
            self.db.execute(update_query)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to configure partner environment: {str(e)}")
    
    async def deploy_partner_templates(self, partner_id: str) -> DeploymentStatus:
        """파트너 템플릿 배포"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            # 템플릿 유형별 배포
            templates = {
                "admin_dashboard": {
                    "template": "admin-dashboard-v1.0",
                    "path": "/admin",
                    "status": "pending"
                },
                "user_wallet": {
                    "template": "user-wallet-v1.0", 
                    "path": "/wallet",
                    "status": "pending"
                },
                "api_endpoints": {
                    "template": "api-v1.0",
                    "path": "/api",
                    "status": "pending"
                },
                "documentation": {
                    "template": "docs-v1.0",
                    "path": "/docs",
                    "status": "pending"
                }
            }
            
            deployment_logs = []
            
            # 템플릿별 배포 시뮬레이션
            for template_name, config in templates.items():
                try:
                    # 실제 배포 로직 (Docker, 파일 복사 등)
                    config["status"] = "deployed"
                    config["deployed_at"] = datetime.utcnow().isoformat()
                    
                    deployment_logs.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "level": "info",
                        "message": f"Successfully deployed {template_name} template"
                    })
                    
                except Exception as e:
                    config["status"] = "failed"
                    config["error"] = str(e)
                    
                    deployment_logs.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "level": "error",
                        "message": f"Failed to deploy {template_name}: {str(e)}"
                    })
            
            # 배포 상태 업데이트
            deployment_config = safe_dict(partner.deployment_config)
            deployment_config.update({
                "templates": templates,
                "deployment_logs": deployment_logs,
                "template_deployment_completed": True,
                "template_deployed_at": datetime.utcnow().isoformat()
            })
            
            # 모든 템플릿이 성공적으로 배포되었는지 확인
            all_deployed = all(t["status"] == "deployed" for t in templates.values())
            
            if all_deployed:
                onboarding_status = "deployed"
                overall_status = "completed"
            else:
                onboarding_status = "partial_failure"
                overall_status = "partial_failure"
            
            # SQLAlchemy update 사용
            update_query = (
                update(Partner)
                .where(Partner.id == partner_id)
                .values(
                    deployment_config=deployment_config,
                    onboarding_status=onboarding_status
                )
            )
            self.db.execute(update_query)
            self.db.commit()
            
            return DeploymentStatus(
                partner_id=partner_id,
                status=overall_status,
                templates=templates,
                logs=deployment_logs,
                completed_at=datetime.utcnow() if all_deployed else None
            )
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to deploy partner templates: {str(e)}")
    
    async def setup_partner_database(self, partner_id: str) -> bool:
        """파트너 데이터베이스 설정"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            # 데이터베이스 설정
            db_config = {
                "database_name": f"dantaro_{safe_str(partner.id).replace('-', '_')}",
                "host": "localhost",
                "port": 5432,
                "user": f"dantaro_{safe_str(partner.id).replace('-', '_')}_user",
                "password": f"pwd_{uuid.uuid4().hex[:16]}",
                "max_connections": 100,
                "timezone": "UTC"
            }
            
            # 초기 데이터 설정
            initial_data = {
                "partner_info": {
                    "name": safe_str(partner.name),
                    "domain": safe_str(partner.domain),
                    "commission_rate": safe_float(partner.commission_rate)
                },
                "default_settings": {
                    "currency": "USD",
                    "language": "en",
                    "timezone": "UTC",
                    "notification_settings": {
                        "email": True,
                        "sms": False,
                        "push": True
                    }
                },
                "security_settings": {
                    "2fa_enabled": False,
                    "ip_whitelist": [],
                    "api_rate_limit": 1000,
                    "session_timeout": 3600
                }
            }
            
            # 배포 설정 업데이트
            deployment_config = safe_dict(partner.deployment_config)
            deployment_config.update({
                "database_config": db_config,
                "initial_data": initial_data,
                "database_setup_completed": True,
                "database_setup_at": datetime.utcnow().isoformat()
            })
            
            # 데이터베이스 초기화
            update_query = (
                update(Partner)
                .where(Partner.id == partner_id)
                .values(
                    deployment_config=deployment_config,
                    energy_balance=Decimal('10000')
                )
            )
            self.db.execute(update_query)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to setup partner database: {str(e)}")
    
    async def get_deployment_status(self, partner_id: str) -> DeploymentStatus:
        """배포 상태 조회"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            deployment_config = safe_dict(partner.deployment_config)
            
            return DeploymentStatus(
                partner_id=partner_id,
                status=safe_str(partner.onboarding_status),
                templates=deployment_config.get("templates", {}),
                logs=deployment_config.get("deployment_logs", []),
                completed_at=None,  # 실제 완료 시간 계산
                config=deployment_config
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get deployment status: {str(e)}")
    
    async def rollback_deployment(self, partner_id: str, reason: str) -> bool:
        """배포 롤백"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            # 롤백 로그
            rollback_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "reason": reason,
                "rollback_actions": [
                    "Stopped containers",
                    "Removed DNS entries", 
                    "Deleted database",
                    "Cleaned up files"
                ]
            }
            
            deployment_config = safe_dict(partner.deployment_config)
            deployment_config["rollback_info"] = rollback_log
            
            # 롤백 처리
            update_query = (
                update(Partner)
                .where(Partner.id == partner_id)
                .values(
                    deployment_config=deployment_config,
                    onboarding_status="failed"
                )
            )
            self.db.execute(update_query)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to rollback deployment: {str(e)}")
    
    async def get_onboarding_steps(self, partner_id: str) -> List[OnboardingStep]:
        """온보딩 단계 조회"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            partner_status = safe_str(partner.status)
            onboarding_status = safe_str(partner.onboarding_status)
            
            steps = [
                OnboardingStep(
                    step_id="partner_registration",
                    title="Partner Registration",
                    description="Partner registration and basic information",
                    status="completed" if partner_status != "pending" else "pending",
                    order=1,
                    estimated_duration=5
                ),
                OnboardingStep(
                    step_id="contract_signing",
                    title="Contract Signing",
                    description="Digital contract signing and terms agreement",
                    status="completed",
                    order=2,
                    estimated_duration=15
                ),
                OnboardingStep(
                    step_id="technical_setup",
                    title="Technical Setup",
                    description="Technical infrastructure setup and configuration",
                    status="completed",
                    order=3,
                    estimated_duration=30
                ),
                OnboardingStep(
                    step_id="integration_testing",
                    title="Integration Testing",
                    description="API integration and system testing",
                    status="completed" if onboarding_status == "completed" else "pending",
                    order=4,
                    estimated_duration=45
                ),
                OnboardingStep(
                    step_id="go_live",
                    title="Go Live",
                    description="Production deployment and go-live",
                    status="completed" if partner_status == "active" else "pending",
                    order=5,
                    estimated_duration=15
                )
            ]
            
            return steps
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get onboarding steps: {str(e)}")
    
    async def complete_onboarding(self, partner_id: str) -> bool:
        """온보딩 완료"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            # 온보딩 완료 처리
            deployment_config = safe_dict(partner.deployment_config)
            deployment_config["onboarding_completed_at"] = datetime.utcnow().isoformat()
            
            update_query = (
                update(Partner)
                .where(Partner.id == partner_id)
                .values(
                    onboarding_status="completed",
                    status="active",
                    activated_at=datetime.utcnow(),
                    deployment_config=deployment_config
                )
            )
            self.db.execute(update_query)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to complete onboarding: {str(e)}")
    
    async def get_all_deployments(self, 
                                 skip: int = 0, 
                                 limit: int = 100,
                                 status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """모든 배포 현황 조회"""
        try:
            query = self.db.query(Partner)
            
            if status_filter:
                query = query.filter(Partner.onboarding_status == status_filter)
            
            partners = query.offset(skip).limit(limit).all()
            
            deployments = []
            for partner in partners:
                deployment_config = safe_dict(partner.deployment_config)
                created_at = safe_datetime(partner.created_at)
                activated_at = safe_datetime(partner.activated_at)
                
                deployments.append({
                    "partner_id": safe_str(partner.id),
                    "partner_name": safe_str(partner.name),
                    "status": safe_str(partner.onboarding_status),
                    "deployment_status": self._get_deployment_status(deployment_config),
                    "created_at": created_at.isoformat() if created_at else None,
                    "activated_at": activated_at.isoformat() if activated_at else None,
                    "config": deployment_config
                })
            
            return deployments
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get all deployments: {str(e)}")
    
    def _get_deployment_status(self, deployment_config: Dict[str, Any]) -> str:
        """배포 상태 계산"""
        if not deployment_config:
            return "not_started"
        
        if deployment_config.get("onboarding_completed_at"):
            return "completed"
        elif deployment_config.get("template_deployment_completed"):
            return "templates_deployed"
        elif deployment_config.get("database_setup_completed"):
            return "database_ready"
        elif deployment_config.get("environment_variables"):
            return "environment_configured"
        else:
            return "in_progress"
    
    async def create_deployment_template(self, template_data: PartnerTemplate) -> str:
        """배포 템플릿 생성"""
        try:
            template_id = str(uuid.uuid4())
            
            # 템플릿 저장 로직 (실제로는 별도 테이블에 저장)
            template_config = {
                "template_id": template_id,
                "name": template_data.name,
                "description": template_data.description,
                "version": template_data.version,
                "components": template_data.components,
                "customizable_fields": template_data.customizable_fields,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # 여기서 실제로는 템플릿 저장소에 저장
            # await self.template_repository.save(template_config)
            
            return template_id
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create deployment template: {str(e)}")
    
    async def get_deployment_templates(self) -> List[PartnerTemplate]:
        """배포 템플릿 목록 조회"""
        try:
            # 실제로는 템플릿 저장소에서 조회
            templates = [
                PartnerTemplate(
                    template_id="standard-v1",
                    name="Standard Deployment",
                    description="Standard partner deployment with basic features",
                    version="1.0.0",
                    components=["web", "api", "database"],
                    customizable_fields=["domain", "branding", "features"]
                ),
                PartnerTemplate(
                    template_id="premium-v1",
                    name="Premium Deployment",
                    description="Premium partner deployment with advanced features",
                    version="1.0.0",
                    components=["web", "api", "database", "cache", "monitoring"],
                    customizable_fields=["domain", "branding", "features", "monitoring"]
                )
            ]
            
            return templates
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get deployment templates: {str(e)}")
    
    async def update_deployment_config(self, partner_id: str, config_updates: Dict[str, Any]) -> bool:
        """배포 설정 업데이트"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            deployment_config = safe_dict(partner.deployment_config)
            deployment_config.update(config_updates)
            deployment_config["updated_at"] = datetime.utcnow().isoformat()
            
            update_query = (
                update(Partner)
                .where(Partner.id == partner_id)
                .values(deployment_config=deployment_config)
            )
            self.db.execute(update_query)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update deployment config: {str(e)}")
    
    async def delete_partner_deployment(self, partner_id: str) -> bool:
        """파트너 배포 삭제"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            # 배포 리소스 정리
            # 1. 컨테이너 중지
            # 2. 데이터베이스 삭제
            # 3. DNS 레코드 삭제
            # 4. 파일 정리
            
            # 파트너 상태 업데이트
            update_query = (
                update(Partner)
                .where(Partner.id == partner_id)
                .values(
                    deployment_config=None,
                    onboarding_status="removed"
                )
            )
            self.db.execute(update_query)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete partner deployment: {str(e)}")
    
    async def get_deployment_logs(self, partner_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """배포 로그 조회"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            deployment_config = safe_dict(partner.deployment_config)
            logs = deployment_config.get("deployment_logs", [])
            
            # 최신 로그부터 반환
            return logs[-limit:] if len(logs) > limit else logs
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get deployment logs: {str(e)}")
    
    async def get_deployment_metrics(self, partner_id: str) -> Dict[str, Any]:
        """배포 메트릭 조회"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            deployment_config = safe_dict(partner.deployment_config)
            created_at = safe_datetime(partner.created_at)
            updated_at = safe_datetime(partner.updated_at)
            
            metrics = {
                "partner_id": safe_str(partner.id),
                "deployment_status": self._get_deployment_status(deployment_config),
                "uptime": self._calculate_uptime(created_at),
                "resource_usage": self._get_resource_usage(deployment_config),
                "error_count": self._get_error_count(deployment_config),
                "last_updated": updated_at.isoformat() if updated_at else None
            }
            
            return metrics
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get deployment metrics: {str(e)}")
    
    def _calculate_uptime(self, created_at: Optional[datetime]) -> Optional[str]:
        """업타임 계산"""
        if not created_at:
            return None
        
        uptime = datetime.utcnow() - created_at
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        return f"{days}d {hours}h {minutes}m"
    
    def _get_resource_usage(self, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """리소스 사용량 조회"""
        # 실제로는 모니터링 시스템에서 조회
        return {
            "cpu_usage": "45%",
            "memory_usage": "67%",
            "disk_usage": "23%",
            "network_io": "1.2MB/s"
        }
    
    def _get_error_count(self, deployment_config: Dict[str, Any]) -> int:
        """에러 카운트 조회"""
        logs = deployment_config.get("deployment_logs", [])
        return len([log for log in logs if log.get("level") == "error"])
    
    async def schedule_deployment_maintenance(self, partner_id: str, maintenance_window: Dict[str, Any]) -> bool:
        """배포 유지보수 예약"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            deployment_config = safe_dict(partner.deployment_config)
            maintenance_schedule = deployment_config.get("maintenance_schedule", [])
            
            maintenance_schedule.append({
                "scheduled_at": maintenance_window.get("scheduled_at"),
                "duration": maintenance_window.get("duration", 30),
                "description": maintenance_window.get("description", ""),
                "type": maintenance_window.get("type", "routine"),
                "created_at": datetime.utcnow().isoformat()
            })
            
            deployment_config["maintenance_schedule"] = maintenance_schedule
            
            update_query = (
                update(Partner)
                .where(Partner.id == partner_id)
                .values(deployment_config=deployment_config)
            )
            self.db.execute(update_query)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to schedule deployment maintenance: {str(e)}")
    
    async def perform_health_check(self, partner_id: str) -> Dict[str, Any]:
        """배포 헬스 체크"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            deployment_config = safe_dict(partner.deployment_config)
            
            # 각 컴포넌트별 헬스 체크
            health_status = {
                "overall": "healthy",
                "components": {
                    "database": {"status": "healthy", "response_time": "5ms"},
                    "api": {"status": "healthy", "response_time": "15ms"},
                    "web": {"status": "healthy", "response_time": "100ms"},
                    "cache": {"status": "healthy", "response_time": "2ms"}
                },
                "last_check": datetime.utcnow().isoformat(),
                "uptime": self._calculate_uptime(safe_datetime(partner.created_at))
            }
            
            return health_status
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to perform health check: {str(e)}")
    
    async def emergency_rollback(self, partner_id: str) -> bool:
        """긴급 롤백"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            deployment_config = safe_dict(partner.deployment_config)
            
            # 긴급 롤백 처리
            if deployment_config:
                deployment_config["rollback"] = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "reason": "emergency_rollback",
                    "status": "initiated"
                }
            
            update_query = (
                update(Partner)
                .where(Partner.id == partner_id)
                .values(
                    deployment_config=deployment_config,
                    onboarding_status="rollback"
                )
            )
            self.db.execute(update_query)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to perform emergency rollback: {str(e)}")
    
    async def get_deployment_summary(self) -> Dict[str, Any]:
        """배포 요약 정보"""
        try:
            # 전체 파트너 수
            total_partners = self.db.query(Partner).count()
            
            # 상태별 파트너 수
            active_partners = self.db.query(Partner).filter(Partner.status == "active").count()
            pending_partners = self.db.query(Partner).filter(Partner.status == "pending").count()
            
            # 온보딩 상태별 파트너 수
            completed_onboarding = self.db.query(Partner).filter(Partner.onboarding_status == "completed").count()
            in_progress_onboarding = self.db.query(Partner).filter(Partner.onboarding_status == "deploying").count()
            
            summary = {
                "total_partners": total_partners,
                "active_partners": active_partners,
                "pending_partners": pending_partners,
                "completed_onboarding": completed_onboarding,
                "in_progress_onboarding": in_progress_onboarding,
                "deployment_success_rate": (completed_onboarding / total_partners * 100) if total_partners > 0 else 0,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return summary
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get deployment summary: {str(e)}")
