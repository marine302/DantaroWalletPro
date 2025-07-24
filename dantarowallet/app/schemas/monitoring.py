"""
모니터링 관련 스키마
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SystemMetrics(BaseModel):
    """시스템 메트릭스"""

    timestamp: datetime
    total_partners: int
    active_partners: int
    pending_partners: int
    suspended_partners: int
    total_api_calls: int
    successful_api_calls: int
    api_error_rate: float  # 퍼센트
    avg_response_time: float  # 밀리초
    system_load: float
    memory_usage: float  # 퍼센트
    disk_usage: float  # 퍼센트


class SystemHealth(BaseModel):
    """시스템 헬스"""

    status: str = Field(..., description="시스템 상태")
    health_score: float = Field(..., description="헬스 점수")
    components: Dict[str, str] = Field(..., description="컴포넌트 상태")
    issues: List[str] = Field(default_factory=list, description="발견된 문제들")
    last_check: datetime


class PartnerRanking(BaseModel):
    """파트너 순위"""

    rank: int
    partner_id: str
    partner_name: str
    score: float
    metric_value: float
    metric_type: str
    change_from_last_period: float


class PerformanceReport(BaseModel):
    """성능 보고서"""

    report_id: str
    period_start: datetime
    period_end: datetime
    total_api_calls: int
    overall_success_rate: float
    overall_avg_response_time: float
    total_partners: int
    partner_performance: List[Dict[str, Any]]
    system_uptime: float
    generated_at: datetime


class Alert(BaseModel):
    """알림"""

    alert_type: str
    severity: str  # info, warning, critical
    title: str
    message: str
    partner_id: Optional[str] = None
    created_at: datetime
