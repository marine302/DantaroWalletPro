"""
배포 모니터 모듈
배포 상태 모니터링, 템플릿 배포 관리
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import update, desc, and_, or_
from fastapi import HTTPException

from app.models.partner import Partner
from app.schemas.deployment import DeploymentStatus, PartnerTemplate
from .utils import safe_str, safe_dict, safe_int


class DeploymentMonitor:
    """배포 모니터"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def deploy_partner_templates(self, partner_id: str) -> DeploymentStatus:
        """파트너 템플릿 배포"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            # 템플릿 설정
            templates = self._get_template_config()
            deployment_logs = []
            
            # 템플릿별 배포 시뮬레이션
            for template_name, config in templates.items():
                try:
                    # 배포 로그 기록
                    log_entry = {
                        "template": template_name,
                        "status": "success",
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": f"Successfully deployed {template_name}"
                    }
                    deployment_logs.append(log_entry)
                    config["status"] = "deployed"
                    
                except Exception as e:
                    log_entry = {
                        "template": template_name,
                        "status": "error",
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": f"Failed to deploy {template_name}: {str(e)}"
                    }
                    deployment_logs.append(log_entry)
                    config["status"] = "failed"
            
            # 배포 상태 업데이트
            deployment_config = safe_dict(partner.deployment_config)
            deployment_config.update({
                "templates": templates,
                "deployment_logs": deployment_logs,
                "deployed_at": datetime.utcnow().isoformat()
            })
            
            self._update_partner_deployment(partner_id, deployment_config)
            
            return DeploymentStatus(
                partner_id=safe_str(partner.id),
                status="completed",
                templates=templates,
                logs=deployment_logs,
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to deploy templates: {str(e)}")
    
    def _get_template_config(self) -> Dict[str, Dict[str, Any]]:
        """템플릿 설정 반환"""
        return {
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
    
    def _update_partner_deployment(self, partner_id: str, deployment_config: Dict[str, Any]) -> None:
        """파트너 배포 설정 업데이트"""
        update_query = (
            update(Partner)
            .where(Partner.id == partner_id)
            .values(deployment_config=deployment_config)
        )
        self.db.execute(update_query)
        self.db.commit()
    
    async def get_deployment_status(self, partner_id: str) -> DeploymentStatus:
        """배포 상태 조회"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            deployment_config = safe_dict(partner.deployment_config)
            status = self._determine_deployment_status(deployment_config)
            
            return DeploymentStatus(
                partner_id=safe_str(partner.id),
                status=status,
                templates=deployment_config.get("templates", {}),
                logs=deployment_config.get("deployment_logs", []),
                created_at=partner.created_at,
                completed_at=None if status != "completed" else datetime.utcnow()
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get deployment status: {str(e)}")
    
    def _determine_deployment_status(self, deployment_config: Dict[str, Any]) -> str:
        """배포 상태 결정"""
        if not deployment_config:
            return "not_started"
        
        templates = deployment_config.get("templates", {})
        if not templates:
            return "pending"
        
        deployed_count = sum(1 for template in templates.values() 
                           if template.get("status") == "deployed")
        failed_count = sum(1 for template in templates.values() 
                         if template.get("status") == "failed")
        
        if failed_count > 0:
            return "failed"
        elif deployed_count == len(templates):
            return "completed"
        elif deployed_count > 0:
            return "in_progress"
        else:
            return "pending"
    
    async def get_all_deployments(self, 
                                status_filter: Optional[str] = None,
                                limit: int = 100,
                                offset: int = 0) -> List[Dict[str, Any]]:
        """모든 배포 상태 조회"""
        try:
            query = self.db.query(Partner)
            
            if status_filter:
                query = query.filter(Partner.onboarding_status == status_filter)
            
            partners = query.order_by(desc(Partner.created_at)).offset(offset).limit(limit).all()
            
            deployments = []
            for partner in partners:
                deployment_config = safe_dict(partner.deployment_config)
                status = self._determine_deployment_status(deployment_config)
                
                deployment_info = {
                    "partner_id": safe_str(partner.id),
                    "partner_name": safe_str(partner.name),
                    "status": status,
                    "onboarding_status": safe_str(partner.onboarding_status),
                    "created_at": partner.created_at.isoformat() if partner.created_at else None,
                    "templates_count": len(deployment_config.get("templates", {})),
                    "last_updated": deployment_config.get("deployed_at")
                }
                deployments.append(deployment_info)
            
            return deployments
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get deployments: {str(e)}")
    
    async def create_deployment_template(self, template_data: PartnerTemplate) -> str:
        """배포 템플릿 생성"""
        try:
            template_id = f"template_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # 템플릿 데이터 저장 로직 (실제로는 파일 시스템이나 별도 저장소 사용)
            template_config = {
                "template_id": template_id,
                "name": safe_str(template_data.name),
                "version": safe_str(template_data.version),
                "description": safe_str(template_data.description),
                "components": template_data.components or [],
                "created_at": datetime.utcnow().isoformat()
            }
            
            return template_id
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")
    
    async def get_deployment_templates(self) -> List[PartnerTemplate]:
        """배포 템플릿 목록 조회"""
        try:
            # 기본 템플릿들 반환 (실제로는 데이터베이스나 파일 시스템에서 조회)
            templates = [
                PartnerTemplate(
                    template_id="standard_v1",
                    name="Standard Partner Template",
                    version="1.0.0",
                    description="Standard template for new partners",
                    components=["admin_dashboard", "user_wallet", "api_endpoints"]
                ),
                PartnerTemplate(
                    template_id="enterprise_v1",
                    name="Enterprise Partner Template",
                    version="1.0.0",
                    description="Enterprise template with advanced features",
                    components=["admin_dashboard", "user_wallet", "api_endpoints", "analytics", "reporting"]
                )
            ]
            
            return templates
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")
    
    def get_deployment_metrics(self) -> Dict[str, Any]:
        """배포 메트릭 조회"""
        try:
            # 기본 통계 조회
            total_partners = self.db.query(Partner).count()
            active_partners = self.db.query(Partner).filter(Partner.status == "active").count()
            pending_deployments = self.db.query(Partner).filter(
                Partner.onboarding_status.in_(["pending", "deploying"])
            ).count()
            
            return {
                "total_partners": total_partners,
                "active_partners": active_partners,
                "pending_deployments": pending_deployments,
                "success_rate": (active_partners / total_partners * 100) if total_partners > 0 else 0
            }
            
        except Exception:
            return {
                "total_partners": 0,
                "active_partners": 0,
                "pending_deployments": 0,
                "success_rate": 0
            }
