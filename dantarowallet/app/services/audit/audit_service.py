"""
감사 로깅 서비스 - Doc #30
트랜잭션 감사 및 컴플라이언스를 위한 핵심 서비스
"""
import hashlib
import json
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, desc, func

from app.models.audit import (
    AuditLog, AuditEventType, ComplianceCheck, ComplianceCheckType,
    ComplianceStatus, RiskLevel, SuspiciousActivity, AuditReport
)
from app.models.user import User
from app.models.partner import Partner
from app.core.logger import get_logger

logger = get_logger(__name__)


def safe_int(value: Any, default: int = 0) -> int:
    """안전한 int 변환"""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """안전한 str 변환"""
    if value is None:
        return default
    try:
        return str(value)
    except (ValueError, TypeError):
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    """안전한 bool 변환"""
    if value is None:
        return default
    try:
        return bool(value)
    except (ValueError, TypeError):
        return default


class AuditService:
    """감사 로깅 서비스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _calculate_log_hash(self, log_data: Dict[str, Any], previous_hash: str = "") -> str:
        """로그 데이터의 해시 계산"""
        try:
            # 해시 계산용 데이터 준비
            hash_data = {
                "timestamp": log_data.get("timestamp", "").isoformat() if isinstance(log_data.get("timestamp"), datetime) else str(log_data.get("timestamp", "")),
                "event_type": str(log_data.get("event_type", "")),
                "entity_type": str(log_data.get("entity_type", "")),
                "entity_id": str(log_data.get("entity_id", "")),
                "event_data": json.dumps(log_data.get("event_data", {}), sort_keys=True),
                "previous_hash": previous_hash
            }
            
            # JSON 문자열로 변환
            hash_string = json.dumps(hash_data, sort_keys=True)
            
            # SHA-256 해시 계산
            return hashlib.sha256(hash_string.encode()).hexdigest()
        except Exception as e:
            logger.error(f"해시 계산 오류: {e}")
            return ""
    
    async def _get_last_log_hash(self) -> str:
        """마지막 로그의 해시 가져오기"""
        try:
            result = await self.db.execute(
                select(AuditLog.log_hash)
                .order_by(desc(AuditLog.id))
                .limit(1)
            )
            last_hash = result.scalar_one_or_none()
            return last_hash or ""
        except Exception as e:
            logger.error(f"마지막 로그 해시 조회 오류: {e}")
            return ""
    
    async def log_event(
        self,
        event_type: AuditEventType,
        entity_type: str,
        entity_id: str,
        event_data: Dict[str, Any],
        user_id: Optional[int] = None,
        partner_id: Optional[int] = None,
        severity: str = "info",
        event_category: str = "system",
        compliance_flags: Optional[Dict[str, Any]] = None,
        risk_score: int = 0,
        requires_review: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """감사 이벤트 로깅"""
        try:
            # 이전 로그의 해시 가져오기
            previous_hash = await self._get_last_log_hash()
            
            # 현재 시간
            timestamp = datetime.utcnow()
            
            # 로그 데이터 준비
            log_data = {
                "timestamp": timestamp,
                "event_type": event_type.value,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "event_data": event_data,
                "user_id": user_id,
                "partner_id": partner_id,
                "severity": severity,
                "event_category": event_category
            }
            
            # 현재 로그의 해시 계산
            log_hash = self._calculate_log_hash(log_data, previous_hash)
            
            # 감사 로그 생성
            audit_log = AuditLog(
                timestamp=timestamp,
                event_type=event_type,
                event_category=event_category,
                severity=severity,
                entity_type=entity_type,
                entity_id=entity_id,
                partner_id=partner_id,
                user_id=user_id,
                event_data=event_data,
                ip_address=ip_address,
                user_agent=user_agent,
                previous_hash=previous_hash,
                log_hash=log_hash,
                compliance_flags=compliance_flags or {},
                risk_score=risk_score,
                requires_review=requires_review
            )
            
            self.db.add(audit_log)
            await self.db.commit()
            
            # 객체를 새로고침하여 lazy loading 문제 방지
            await self.db.refresh(audit_log)
            
            logger.info(f"감사 로그 생성 완료: {event_type.value} - {entity_type}:{entity_id}")
            return audit_log
            
        except Exception as e:
            logger.error(f"감사 로그 생성 오류: {e}")
            await self.db.rollback()
            return None
    
    async def log_transaction_event(
        self,
        transaction_id: str,
        event_type: AuditEventType,
        transaction_data: Dict[str, Any],
        user_id: Optional[int] = None,
        partner_id: Optional[int] = None,
        **kwargs
    ) -> Optional[AuditLog]:
        """트랜잭션 이벤트 로깅"""
        return await self.log_event(
            event_type=event_type,
            entity_type="transaction",
            entity_id=transaction_id,
            event_data=transaction_data,
            user_id=user_id,
            partner_id=partner_id,
            event_category="transaction",
            **kwargs
        )
    
    async def log_user_action(
        self,
        user_id: int,
        action: str,
        action_data: Dict[str, Any],
        severity: str = "info",
        **kwargs
    ) -> Optional[AuditLog]:
        """사용자 액션 로깅"""
        return await self.log_event(
            event_type=AuditEventType.USER_ACTION,
            entity_type="user",
            entity_id=str(user_id),
            event_data={"action": action, **action_data},
            user_id=user_id,
            severity=severity,
            event_category="user",
            **kwargs
        )
    
    async def log_admin_action(
        self,
        admin_user_id: int,
        action: str,
        action_data: Dict[str, Any],
        target_entity_type: str = "system",
        target_entity_id: str = "",
        severity: str = "info",
        **kwargs
    ) -> Optional[AuditLog]:
        """관리자 액션 로깅"""
        return await self.log_event(
            event_type=AuditEventType.ADMIN_ACTION,
            entity_type=target_entity_type,
            entity_id=target_entity_id,
            event_data={"action": action, "admin_user_id": admin_user_id, **action_data},
            user_id=admin_user_id,
            severity=severity,
            event_category="admin",
            **kwargs
        )
    
    async def log_suspicious_activity(
        self,
        user_id: int,
        activity_type: str,
        activity_data: Dict[str, Any],
        severity: RiskLevel = RiskLevel.MEDIUM,
        **kwargs
    ) -> Optional[AuditLog]:
        """의심스러운 활동 로깅"""
        return await self.log_event(
            event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
            entity_type="user",
            entity_id=str(user_id),
            event_data={"activity_type": activity_type, **activity_data},
            user_id=user_id,
            severity=severity.value,
            event_category="security",
            requires_review=True,
            risk_score=self._calculate_risk_score(severity),
            **kwargs
        )
    
    def _calculate_risk_score(self, risk_level: RiskLevel) -> int:
        """위험도 레벨에 따른 점수 계산"""
        risk_scores = {
            RiskLevel.LOW: 25,
            RiskLevel.MEDIUM: 50,
            RiskLevel.HIGH: 75,
            RiskLevel.CRITICAL: 100
        }
        return risk_scores.get(risk_level, 0)
    
    async def get_audit_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        event_type: Optional[AuditEventType] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[int] = None,
        partner_id: Optional[int] = None,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        requires_review: Optional[bool] = None
    ) -> List[AuditLog]:
        """감사 로그 조회"""
        try:
            query = select(AuditLog)
            
            # 필터 조건 적용
            conditions = []
            
            if event_type:
                conditions.append(AuditLog.event_type == event_type)
            
            if entity_type:
                conditions.append(AuditLog.entity_type == entity_type)
            
            if entity_id:
                conditions.append(AuditLog.entity_id == entity_id)
            
            if user_id:
                conditions.append(AuditLog.user_id == user_id)
            
            if partner_id:
                conditions.append(AuditLog.partner_id == partner_id)
            
            if severity:
                conditions.append(AuditLog.severity == severity)
            
            if start_date:
                conditions.append(AuditLog.timestamp >= start_date)
            
            if end_date:
                conditions.append(AuditLog.timestamp <= end_date)
            
            if requires_review is not None:
                conditions.append(AuditLog.requires_review == requires_review)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # 정렬 및 페이지네이션
            query = query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"감사 로그 조회 오류: {e}")
            return []
    
    async def get_audit_log_count(
        self,
        event_type: Optional[AuditEventType] = None,
        entity_type: Optional[str] = None,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        requires_review: Optional[bool] = None
    ) -> int:
        """감사 로그 개수 조회"""
        try:
            query = select(func.count(AuditLog.id))
            
            # 필터 조건 적용
            conditions = []
            
            if event_type:
                conditions.append(AuditLog.event_type == event_type)
            
            if entity_type:
                conditions.append(AuditLog.entity_type == entity_type)
            
            if severity:
                conditions.append(AuditLog.severity == severity)
            
            if start_date:
                conditions.append(AuditLog.timestamp >= start_date)
            
            if end_date:
                conditions.append(AuditLog.timestamp <= end_date)
            
            if requires_review is not None:
                conditions.append(AuditLog.requires_review == requires_review)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none() or 0
            
        except Exception as e:
            logger.error(f"감사 로그 개수 조회 오류: {e}")
            return 0
    
    async def verify_log_integrity(self, log_id: int) -> bool:
        """로그 무결성 검증"""
        try:
            # 현재 로그 조회
            result = await self.db.execute(
                select(AuditLog).where(AuditLog.id == log_id)
            )
            current_log = result.scalar_one_or_none()
            
            if not current_log:
                return False
            
            # 로그 데이터 재구성
            log_data = {
                "timestamp": current_log.timestamp,
                "event_type": current_log.event_type.value,
                "entity_type": current_log.entity_type,
                "entity_id": current_log.entity_id,
                "event_data": current_log.event_data,
                "user_id": current_log.user_id,
                "partner_id": current_log.partner_id,
                "severity": current_log.severity,
                "event_category": current_log.event_category
            }
            
            # 해시 재계산
            previous_hash_value = safe_str(current_log.previous_hash, "")
            calculated_hash = self._calculate_log_hash(log_data, previous_hash_value)
            
            # 저장된 해시와 비교
            return calculated_hash == current_log.log_hash
            
        except Exception as e:
            logger.error(f"로그 무결성 검증 오류: {e}")
            return False
    
    async def get_audit_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """감사 통계 조회"""
        try:
            # 기본 기간 설정 (최근 30일)
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # 총 로그 수
            total_logs = await self.get_audit_log_count(
                start_date=start_date,
                end_date=end_date
            )
            
            # 이벤트 타입별 통계
            event_type_stats = {}
            for event_type in AuditEventType:
                count = await self.get_audit_log_count(
                    event_type=event_type,
                    start_date=start_date,
                    end_date=end_date
                )
                event_type_stats[event_type.value] = count
            
            # 심각도별 통계
            severity_stats = {}
            for severity in ["info", "warning", "error", "critical"]:
                count = await self.get_audit_log_count(
                    severity=severity,
                    start_date=start_date,
                    end_date=end_date
                )
                severity_stats[severity] = count
            
            # 검토 필요 로그 수
            review_required = await self.get_audit_log_count(
                requires_review=True,
                start_date=start_date,
                end_date=end_date
            )
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_logs": total_logs,
                "event_type_stats": event_type_stats,
                "severity_stats": severity_stats,
                "review_required": review_required
            }
            
        except Exception as e:
            logger.error(f"감사 통계 조회 오류: {e}")
            return {}
