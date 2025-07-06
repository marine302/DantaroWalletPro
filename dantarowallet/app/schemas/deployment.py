"""
배포 관련 스키마
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DeploymentResult(BaseModel):
    """배포 결과"""
    deployment_id: str
    partner_id: str
    status: str  # in_progress, completed, failed
    steps: List[Dict[str, str]]
    config: Dict[str, Any]
    logs: List[str]
    created_at: datetime
    estimated_completion: Optional[datetime] = None


class DeploymentStatus(BaseModel):
    """배포 상태"""
    partner_id: str
    status: str
    templates: Dict[str, Any]
    logs: List[Dict[str, str]]
    completed_at: Optional[datetime] = None
    config: Optional[Dict[str, Any]] = None


class PartnerTemplate(BaseModel):
    """파트너 템플릿"""
    template_id: str
    name: str
    version: str
    description: str
    components: List[str]
    customizable_fields: List[str]


class OnboardingStep(BaseModel):
    """온보딩 단계"""
    step_id: str
    title: str
    description: str
    status: str  # pending, in_progress, completed, failed
    order: int
    estimated_duration: int  # minutes
    completed_at: Optional[datetime] = None


class DeploymentConfig(BaseModel):
    """배포 설정"""
    partner_id: str
    template_version: str
    environment: str
    domain: str
    features: Dict[str, bool]
    branding: Dict[str, Any]
    database_config: Dict[str, str]
