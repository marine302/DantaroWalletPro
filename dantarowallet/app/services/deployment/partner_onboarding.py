"""
파트너 온보딩 모듈
온보딩 단계 관리, 진행 상황 추적
"""
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import update
from fastapi import HTTPException

from app.models.partner import Partner
from app.schemas.deployment import OnboardingStep
from .utils import safe_str, safe_dict


class PartnerOnboarding:
    """파트너 온보딩 관리"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_onboarding_steps(self, partner_id: str) -> List[OnboardingStep]:
        """온보딩 단계 조회"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            partner_status = safe_str(partner.status)
            onboarding_status = safe_str(partner.onboarding_status)
            
            steps = self._create_onboarding_steps(partner_status, onboarding_status)
            return steps
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get onboarding steps: {str(e)}")
    
    def _create_onboarding_steps(self, partner_status: str, onboarding_status: str) -> List[OnboardingStep]:
        """온보딩 단계 생성"""
        return [
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
    
    async def update_onboarding_step(self, partner_id: str, step_id: str, status: str) -> bool:
        """온보딩 단계 상태 업데이트"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                return False
            
            deployment_config = safe_dict(partner.deployment_config)
            if "onboarding_steps" not in deployment_config:
                deployment_config["onboarding_steps"] = {}
            
            deployment_config["onboarding_steps"][step_id] = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            update_query = (
                update(Partner)
                .where(Partner.id == partner_id)
                .values(deployment_config=deployment_config)
            )
            self.db.execute(update_query)
            self.db.commit()
            
            return True
            
        except Exception:
            self.db.rollback()
            return False
    
    def get_onboarding_progress(self, partner_id: str) -> dict:
        """온보딩 진행 상황 조회"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                return {"progress": 0, "current_step": None}
            
            deployment_config = safe_dict(partner.deployment_config)
            onboarding_steps = deployment_config.get("onboarding_steps", {})
            
            total_steps = 5
            completed_steps = len([step for step in onboarding_steps.values() 
                                 if step.get("status") == "completed"])
            
            progress = int((completed_steps / total_steps) * 100)
            
            # 현재 단계 찾기
            step_order = ["partner_registration", "contract_signing", "technical_setup", 
                         "integration_testing", "go_live"]
            current_step = None
            
            for step_id in step_order:
                if step_id not in onboarding_steps or onboarding_steps[step_id].get("status") != "completed":
                    current_step = step_id
                    break
            
            return {
                "progress": progress,
                "current_step": current_step,
                "completed_steps": completed_steps,
                "total_steps": total_steps
            }
            
        except Exception:
            return {"progress": 0, "current_step": None}
