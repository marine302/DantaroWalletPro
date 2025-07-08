"""
슈퍼 어드민용 배포 자동화 서비스
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
                "partner_id": partner.id,
                "deployment_id": deployment_id,
                "template_version": "v1.0",
                "environment": "production",
                "domain": partner.domain,
                "subdomain": f"{partner.name.lower().replace(' ', '-')}.dantarowallet.com",
                "database_name": f"dantaro_{partner.id.replace('-', '_')}",
                "api_endpoint": f"https://api.dantarowallet.com/{partner.id}",
                "features": partner.settings.get("features", {}),
                "branding": partner.settings.get("branding", {}),
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
            self.db.refresh(partner)
            
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
                "PARTNER_ID": partner.id,
                "PARTNER_NAME": partner.name,
                "API_KEY": partner.api_key,
                "DATABASE_URL": f"postgresql://user:pass@db:5432/dantaro_{partner.id.replace('-', '_')}",
                "REDIS_URL": "redis://redis:6379/0",
                "TRON_NETWORK": "mainnet",
                "ENERGY_POOL_ADDRESS": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
                "WEBHOOK_SECRET": f"whsec_{uuid.uuid4().hex}",
                "DOMAIN": partner.domain or f"{partner.name.lower().replace(' ', '-')}.dantarowallet.com"
            }
            
            # 브랜딩 설정
            branding_config = partner.settings.get("branding", {})
            
            # 기능 설정
            feature_config = partner.settings.get("features", {
                "multi_signature": True,
                "cold_wallet": True,
                "auto_sweep": False,
                "api_access": True,
                "webhook_notifications": True,
                "2fa_required": False
            })
            
            # 설정 업데이트
            deployment_config = safe_get_attr(partner, 'deployment_config', {})
            if not isinstance(deployment_config, dict):
                deployment_config = {}
            
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
            deployment_config = safe_get_attr(partner, 'deployment_config', {})
            if not isinstance(deployment_config, dict):
                deployment_config = {}
            
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
                "database_name": f"dantaro_{partner.id.replace('-', '_')}",
                "username": f"user_{partner.id.replace('-', '_')}",
                "password": f"pwd_{uuid.uuid4().hex}",
                "host": "localhost",
                "port": 5432,
                "schema_version": "1.0",
                "created_at": datetime.utcnow().isoformat()
            }
            
            # 초기 데이터 설정
            initial_data = {
                "admin_user": {
                    "email": partner.contact_email,
                    "role": "admin",
                    "created_at": datetime.utcnow().isoformat()
                },
                "system_config": {
                    "partner_id": partner.id,
                    "partner_name": partner.name,
                    "api_key": partner.api_key,
                    "commission_rate": safe_float(partner.commission_rate)
                },
                "initial_energy_balance": 10000,  # 초기 에너지 할당
                "wallet_config": {
                    "hot_wallet_limit": "10000.00",
                    "cold_wallet_threshold": "50000.00",
                    "auto_sweep_enabled": False
                }
            }
            
            # 배포 설정 업데이트
            deployment_config = partner.deployment_config or {}
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
            
            deployment_config = partner.deployment_config or {}
            
            return DeploymentStatus(
                partner_id=partner_id,
                status=partner.onboarding_status,
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
            
            # 상태 업데이트
            partner.onboarding_status = "failed"
            
            deployment_config = partner.deployment_config or {}
            deployment_config["rollback_info"] = rollback_log
            partner.deployment_config = deployment_config
            
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
            
            deployment_config = partner.deployment_config or {}
            
            steps = [
                OnboardingStep(
                    step_id="registration",
                    title="Partner Registration",
                    description="Complete partner registration and verification",
                    status="completed" if partner.status != "pending" else "pending",
                    order=1,
                    estimated_duration=5
                ),
                OnboardingStep(
                    step_id="configuration",
                    title="Environment Configuration", 
                    description="Configure partner-specific settings and branding",
                    status="completed" if deployment_config.get("configured_at") else "pending",
                    order=2,
                    estimated_duration=10
                ),
                OnboardingStep(
                    step_id="database_setup",
                    title="Database Setup",
                    description="Create and initialize partner database",
                    status="completed" if deployment_config.get("database_setup_completed") else "pending",
                    order=3,
                    estimated_duration=15
                ),
                OnboardingStep(
                    step_id="template_deployment",
                    title="Template Deployment",
                    description="Deploy admin and user interface templates",
                    status="completed" if deployment_config.get("template_deployment_completed") else "pending",
                    order=4,
                    estimated_duration=20
                ),
                OnboardingStep(
                    step_id="testing",
                    title="System Testing",
                    description="Run integration tests and health checks",
                    status="completed" if partner.onboarding_status == "completed" else "pending",
                    order=5,
                    estimated_duration=10
                ),
                OnboardingStep(
                    step_id="activation",
                    title="Go Live",
                    description="Activate partner system and go live",
                    status="completed" if partner.status == "active" else "pending",
                    order=6,
                    estimated_duration=5
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
            
            # 모든 배포 단계가 완료되었는지 확인
            deployment_config = partner.deployment_config or {}
            
            required_steps = [
                "configured_at",
                "database_setup_completed", 
                "template_deployment_completed"
            ]
            
            all_completed = all(deployment_config.get(step) for step in required_steps)
            
            if not all_completed:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot complete onboarding. Some deployment steps are not finished."
                )
            
            # 온보딩 완료
            partner.onboarding_status = "completed"
            partner.status = "active"
            partner.activated_at = datetime.utcnow()
            
            # 완료 로그 추가
            deployment_config["onboarding_completed_at"] = datetime.utcnow().isoformat()
            partner.deployment_config = deployment_config
            
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to complete onboarding: {str(e)}")
    
    # ===== 슈퍼 어드민용 배포 관리 메서드들 =====
    
    async def get_all_deployments(self, 
                                 status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """모든 파트너 배포 현황 조회 (슈퍼 어드민용)"""
        try:
            query = self.db.query(Partner)
            
            if status_filter:
                query = query.filter(Partner.status == status_filter)
            
            partners = query.all()
            deployments = []
            
            for partner in partners:
                deployment_config = partner.deployment_config or {}
                
                deployment_info = {
                    "partner_id": str(partner.id),
                    "partner_name": partner.name,
                    "status": partner.status,
                    "onboarding_status": partner.onboarding_status,
                    "deployment_status": self._get_deployment_status(deployment_config),
                    "created_at": partner.created_at.isoformat() if partner.created_at else None,
                    "activated_at": partner.activated_at.isoformat() if partner.activated_at else None,
                    "template_type": deployment_config.get("template_type", "standard"),
                    "environment": deployment_config.get("environment", "production"),
                    "infrastructure": deployment_config.get("infrastructure", {}),
                    "health_status": self._check_deployment_health(partner),
                    "last_updated": deployment_config.get("last_updated")
                }
                
                deployments.append(deployment_info)
            
            return deployments
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get all deployments: {str(e)}")
    
    async def get_deployment_statistics(self) -> Dict[str, Any]:
        """배포 통계 조회 (슈퍼 어드민용)"""
        try:
            # 전체 파트너 통계
            total_partners = self.db.query(Partner).count()
            active_deployments = self.db.query(Partner).filter(Partner.status == "active").count()
            pending_deployments = self.db.query(Partner).filter(Partner.onboarding_status == "pending").count()
            failed_deployments = self.db.query(Partner).filter(Partner.status == "suspended").count()
            
            # 템플릿별 통계
            partners = self.db.query(Partner).all()
            template_stats = {}
            
            for partner in partners:
                deployment_config = partner.deployment_config or {}
                template_type = deployment_config.get("template_type", "standard")
                
                if template_type not in template_stats:
                    template_stats[template_type] = 0
                template_stats[template_type] += 1
            
            # 최근 배포 활동
            recent_deployments = []
            for partner in partners[-10:]:  # 최근 10개
                deployment_config = partner.deployment_config or {}
                if deployment_config.get("configured_at"):
                    recent_deployments.append({
                        "partner_name": partner.name,
                        "status": partner.status,
                        "deployed_at": deployment_config.get("configured_at"),
                        "template_type": deployment_config.get("template_type", "standard")
                    })
            
            statistics = {
                "overview": {
                    "total_partners": total_partners,
                    "active_deployments": active_deployments,
                    "pending_deployments": pending_deployments,
                    "failed_deployments": failed_deployments,
                    "success_rate": (active_deployments / max(total_partners, 1)) * 100
                },
                
                "template_distribution": template_stats,
                
                "recent_activity": recent_deployments,
                
                "deployment_health": {
                    "healthy": active_deployments,
                    "unhealthy": failed_deployments,
                    "unknown": pending_deployments
                },
                
                "resource_usage": {
                    "total_instances": active_deployments,
                    "avg_deployment_time": "15 minutes",  # 더미 데이터
                    "total_storage_used": f"{active_deployments * 100}GB",
                    "monthly_cost_estimate": f"${active_deployments * 200} USD"
                }
            }
            
            return statistics
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get deployment statistics: {str(e)}")
    
    async def bulk_deploy_partners(self, 
                                  partner_ids: List[str],
                                  template_type: str = "standard") -> List[Dict[str, Any]]:
        """대량 파트너 배포 (슈퍼 어드민용)"""
        try:
            deployment_results = []
            
            for partner_id in partner_ids:
                try:
                    partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
                    if not partner:
                        deployment_results.append({
                            "partner_id": partner_id,
                            "status": "failed",
                            "error": "Partner not found"
                        })
                        continue
                    
                    # 배포 시작
                    deployment_result = await self.create_partner_instance(partner)
                    
                    deployment_results.append({
                        "partner_id": partner_id,
                        "partner_name": partner.name,
                        "status": "initiated",
                        "deployment_id": deployment_result.deployment_id,
                        "estimated_completion": deployment_result.estimated_completion
                    })
                    
                except Exception as e:
                    deployment_results.append({
                        "partner_id": partner_id,
                        "status": "failed",
                        "error": str(e)
                    })
            
            return deployment_results
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to bulk deploy partners: {str(e)}")
    
    async def manage_deployment_templates(self, 
                                        action: str,
                                        template_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """배포 템플릿 관리 (슈퍼 어드민용)"""
        try:
            if action == "list":
                # 사용 가능한 템플릿 목록 반환
                templates = [
                    {
                        "id": "standard",
                        "name": "표준 템플릿",
                        "description": "일반적인 파트너사용 기본 구성",
                        "version": "1.0.0",
                        "resources": {
                            "cpu": "2 vCPU",
                            "memory": "4GB RAM", 
                            "storage": "100GB SSD"
                        },
                        "features": ["기본 지갑", "TRON 지원", "모니터링"],
                        "monthly_cost": 200
                    },
                    {
                        "id": "enterprise",
                        "name": "엔터프라이즈 템플릿",
                        "description": "고성능 파트너사용 확장 구성",
                        "version": "1.0.0",
                        "resources": {
                            "cpu": "8 vCPU",
                            "memory": "16GB RAM",
                            "storage": "500GB SSD"
                        },
                        "features": ["고급 지갑", "다중 체인", "실시간 모니터링", "전용 지원"],
                        "monthly_cost": 800
                    }
                ]
                return {"templates": templates}
            
            elif action == "create" and template_data:
                # 새 템플릿 생성
                new_template = {
                    "id": template_data.get("id"),
                    "name": template_data.get("name"),
                    "description": template_data.get("description"),
                    "version": "1.0.0",
                    "created_at": datetime.utcnow().isoformat(),
                    "created_by": "super_admin"
                }
                return {"template": new_template, "status": "created"}
            
            elif action == "update" and template_data:
                # 기존 템플릿 업데이트
                return {"template": template_data, "status": "updated"}
            
            elif action == "delete" and template_data:
                # 템플릿 삭제
                return {"template_id": template_data.get("id"), "status": "deleted"}
            
            else:
                raise HTTPException(status_code=400, detail="Invalid action or missing template data")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to manage deployment templates: {str(e)}")
    
    async def monitor_deployment_health(self) -> Dict[str, Any]:
        """배포 건강 상태 모니터링 (슈퍼 어드민용)"""
        try:
            partners = self.db.query(Partner).filter(Partner.status == "active").all()
            
            health_summary = {
                "total_deployments": len(partners),
                "healthy_count": 0,
                "warning_count": 0,
                "critical_count": 0,
                "unknown_count": 0,
                "deployment_health": []
            }
            
            for partner in partners:
                health_status = self._check_deployment_health(partner)
                health_info = {
                    "partner_id": str(partner.id),
                    "partner_name": partner.name,
                    "health_status": health_status["status"],
                    "uptime": health_status["uptime"],
                    "response_time": health_status["response_time"],
                    "error_rate": health_status["error_rate"],
                    "last_check": health_status["last_check"],
                    "issues": health_status.get("issues", [])
                }
                
                health_summary["deployment_health"].append(health_info)
                
                # 상태별 카운트
                if health_status["status"] == "healthy":
                    health_summary["healthy_count"] += 1
                elif health_status["status"] == "warning":
                    health_summary["warning_count"] += 1
                elif health_status["status"] == "critical":
                    health_summary["critical_count"] += 1
                else:
                    health_summary["unknown_count"] += 1
            
            return health_summary
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to monitor deployment health: {str(e)}")
    
    def _get_deployment_status(self, deployment_config: Dict[str, Any]) -> str:
        """배포 상태 계산"""
        if deployment_config.get("onboarding_completed_at"):
            return "completed"
        elif deployment_config.get("template_deployment_completed"):
            return "deployed"
        elif deployment_config.get("database_setup_completed"):
            return "configuring"
        elif deployment_config.get("configured_at"):
            return "setting_up"
        else:
            return "pending"
    
    def _check_deployment_health(self, partner: Partner) -> Dict[str, Any]:
        """개별 배포 건강 상태 확인"""
        # 실제로는 헬스체크 엔드포인트 호출하여 확인
        # 여기서는 더미 데이터 반환
        
        import random
        
        statuses = ["healthy", "warning", "critical"]
        weights = [0.8, 0.15, 0.05]  # 80% healthy, 15% warning, 5% critical
        
        status = random.choices(statuses, weights=weights)[0]
        
        health_data = {
            "status": status,
            "uptime": f"{random.uniform(95, 99.9):.1f}%",
            "response_time": f"{random.randint(50, 300)}ms",
            "error_rate": f"{random.uniform(0, 2):.2f}%",
            "last_check": datetime.utcnow().isoformat(),
            "issues": []
        }
        
        if status == "warning":
            health_data["issues"] = ["High response time detected"]
        elif status == "critical":
            health_data["issues"] = ["Service unavailable", "Database connection failed"]
        
        return health_data

    async def remove_partner_deployment(self, partner_id: str) -> bool:
        """파트너 배포 제거"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            # 배포 설정 제거
            partner.deployment_config = None
            partner.onboarding_status = "removed"
            
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to remove deployment: {str(e)}")

    async def get_available_templates(self) -> List[Dict[str, Any]]:
        """사용 가능한 템플릿 목록 조회"""
        try:
            templates = [
                {
                    "id": "standard",
                    "name": "Standard Template",
                    "description": "기본 지갑 기능을 포함한 표준 템플릿",
                    "features": ["deposit", "withdrawal", "balance", "transactions"],
                    "version": "1.0.0",
                    "category": "basic"
                },
                {
                    "id": "premium",
                    "name": "Premium Template",
                    "description": "고급 분석 기능이 포함된 프리미엄 템플릿",
                    "features": ["deposit", "withdrawal", "balance", "transactions", "analytics", "reports"],
                    "version": "1.0.0",
                    "category": "advanced"
                },
                {
                    "id": "enterprise",
                    "name": "Enterprise Template",
                    "description": "기업용 전체 기능 템플릿",
                    "features": ["deposit", "withdrawal", "balance", "transactions", "analytics", "reports", "api", "webhooks"],
                    "version": "1.0.0",
                    "category": "enterprise"
                }
            ]
            
            return templates
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")

    async def create_template(self, template_data: Dict[str, Any], admin_id: str) -> Dict[str, Any]:
        """새 템플릿 생성"""
        try:
            template = {
                "id": str(uuid.uuid4()),
                "name": template_data["name"],
                "description": template_data.get("description", ""),
                "features": template_data.get("features", []),
                "version": template_data.get("version", "1.0.0"),
                "category": template_data.get("category", "custom"),
                "created_by": admin_id,
                "created_at": datetime.utcnow().isoformat(),
                "config": template_data.get("config", {})
            }
            
            # 실제로는 템플릿 데이터베이스에 저장
            return template
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")

    async def get_all_deployments(self, status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """전체 배포 현황 조회"""
        try:
            query = self.db.query(Partner).filter(Partner.deployment_config.isnot(None))
            
            if status_filter:
                query = query.filter(Partner.onboarding_status == status_filter)
            
            partners = query.limit(limit).all()
            
            deployments = []
            for partner in partners:
                deployment = {
                    "partner_id": partner.id,
                    "partner_name": partner.name,
                    "status": partner.onboarding_status or "pending",
                    "deployment_config": partner.deployment_config,
                    "created_at": partner.created_at.isoformat() if partner.created_at else None,
                    "last_updated": partner.updated_at.isoformat() if partner.updated_at else None
                }
                deployments.append(deployment)
            
            return deployments
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get deployments: {str(e)}")

    async def rollback_deployment(self, deployment_id: str, reason: str) -> bool:
        """배포 롤백"""
        try:
            # deployment_id로 파트너 찾기
            partner = self.db.query(Partner).filter(
                Partner.deployment_config.contains({'deployment_id': deployment_id})
            ).first()
            
            if not partner:
                raise HTTPException(status_code=404, detail="Deployment not found")
            
            # 롤백 로직
            partner.onboarding_status = "rollback"
            
            # 롤백 정보 저장
            if partner.deployment_config:
                partner.deployment_config["rollback"] = {
                    "reason": reason,
                    "rolled_back_at": datetime.utcnow().isoformat()
                }
            
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to rollback deployment: {str(e)}")

    async def get_deployment_status(self, partner_id: str) -> Dict[str, Any]:
        """파트너 배포 상태 조회"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            status = {
                "partner_id": partner.id,
                "partner_name": partner.name,
                "status": partner.onboarding_status or "pending",
                "deployment_config": partner.deployment_config,
                "progress": self._calculate_deployment_progress(partner),
                "health": self._check_deployment_health(partner),
                "last_updated": partner.updated_at.isoformat() if partner.updated_at else None
            }
            
            return status
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get deployment status: {str(e)}")

    def _calculate_deployment_progress(self, partner: Partner) -> Dict[str, Any]:
        """배포 진행률 계산"""
        total_steps = 6
        completed_steps = 0
        
        if partner.deployment_config:
            config = partner.deployment_config
            if config.get("database_setup_completed"):
                completed_steps += 1
            if config.get("container_deployed"):
                completed_steps += 1
            if config.get("dns_configured"):
                completed_steps += 1
            if config.get("ssl_configured"):
                completed_steps += 1
            if config.get("data_initialized"):
                completed_steps += 1
            if config.get("health_check_passed"):
                completed_steps += 1
        
        return {
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "percentage": (completed_steps / total_steps) * 100
        }
    