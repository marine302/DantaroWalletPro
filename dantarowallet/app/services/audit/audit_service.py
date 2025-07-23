"""
감사 서비스 - 트랜잭션 감사 및 로깅
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.logging import get_logger
from app.models.audit import AuditEventType, AuditLog

logger = get_logger(__name__)


def safe_str_extract(value) -> str:
    """SQLAlchemy 컬럼 값을 안전하게 str로 변환"""
    try:
        return str(value) if value is not None else ""
    except (ValueError, TypeError):
        return ""


class AuditService:
    """감사 로깅 서비스"""

    def __init__(self, db: Optional[Session] = None):
        self.db = db or get_db_session()

    async def log_event(
        self,
        event_type: AuditEventType,
        entity_type: str,
        entity_id: str,
        event_data: Dict[str, Any],
        user_id: Optional[int] = None,
        partner_id: Optional[int] = None,
        severity: str = "info",
        compliance_flags: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """감사 이벤트 로깅"""
        try:
            # 이전 로그의 해시 가져오기
            last_log = self.db.query(AuditLog).order_by(desc(AuditLog.id)).first()
            previous_hash = last_log.log_hash if last_log else "0"

            # 현재 로그 해시 생성
            log_content = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type.value,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "event_data": event_data,
                "previous_hash": previous_hash,
            }

            current_hash = hashlib.sha256(
                json.dumps(log_content, sort_keys=True).encode()
            ).hexdigest()

            # 감사 로그 생성
            audit_log = AuditLog(
                event_type=event_type,
                event_category=self._get_event_category(event_type),
                severity=severity,
                entity_type=entity_type,
                entity_id=entity_id,
                partner_id=partner_id,
                user_id=user_id,
                event_data=event_data,
                ip_address=ip_address,
                user_agent=user_agent,
                block_hash=previous_hash,
                log_hash=current_hash,
                compliance_flags=compliance_flags or {},
                risk_score=self._calculate_risk_score(event_type, event_data),
                requires_review=self._requires_review(event_type, event_data),
            )

            self.db.add(audit_log)
            self.db.commit()

            logger.info(
                f"감사 로그 생성: {event_type.value} - {entity_type}:{entity_id}"
            )
            return audit_log

        except Exception as e:
            logger.error(f"감사 로그 생성 실패: {str(e)}")
            self.db.rollback()
            raise

    def _get_event_category(self, event_type: AuditEventType) -> str:
        """이벤트 카테고리 결정"""
        transaction_events = {
            AuditEventType.TRANSACTION_CREATED,
            AuditEventType.TRANSACTION_COMPLETED,
            AuditEventType.TRANSACTION_FAILED,
            AuditEventType.WITHDRAWAL_REQUESTED,
            AuditEventType.WITHDRAWAL_APPROVED,
            AuditEventType.DEPOSIT_DETECTED,
        }

        compliance_events = {
            AuditEventType.COMPLIANCE_CHECK,
            AuditEventType.SUSPICIOUS_ACTIVITY,
        }

        if event_type in transaction_events:
            return "transaction"
        elif event_type in compliance_events:
            return "compliance"
        else:
            return "system"

    def _calculate_risk_score(
        self, event_type: AuditEventType, event_data: Dict
    ) -> int:
        """위험 점수 계산"""
        base_scores = {
            AuditEventType.TRANSACTION_CREATED: 1,
            AuditEventType.TRANSACTION_COMPLETED: 1,
            AuditEventType.TRANSACTION_FAILED: 3,
            AuditEventType.WITHDRAWAL_REQUESTED: 5,
            AuditEventType.WITHDRAWAL_APPROVED: 3,
            AuditEventType.DEPOSIT_DETECTED: 1,
            AuditEventType.SUSPICIOUS_ACTIVITY: 8,
            AuditEventType.COMPLIANCE_CHECK: 2,
            AuditEventType.USER_ACTION: 1,
            AuditEventType.SYSTEM_ACTION: 1,
        }

        score = base_scores.get(event_type, 1)

        # 추가 위험 요소 고려
        if event_data.get("amount", 0) > 10000:  # 고액 거래
            score += 2

        if event_data.get("is_international", False):  # 국제 거래
            score += 1

        return min(score, 10)  # 최대 10점

    def _requires_review(self, event_type: AuditEventType, event_data: Dict) -> bool:
        """수동 검토 필요 여부"""
        high_risk_events = {
            AuditEventType.SUSPICIOUS_ACTIVITY,
            AuditEventType.TRANSACTION_FAILED,
        }

        if event_type in high_risk_events:
            return True

        # 고액 거래는 검토 필요
        if event_data.get("amount", 0) > 50000:
            return True

        return False

    async def get_audit_logs(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[int] = None,
        partner_id: Optional[int] = None,
        event_types: Optional[List[AuditEventType]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        """감사 로그 조회"""
        query = self.db.query(AuditLog)

        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if partner_id:
            query = query.filter(AuditLog.partner_id == partner_id)
        if event_types:
            query = query.filter(AuditLog.event_type.in_(event_types))
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)

        return (
            query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()
        )

    async def verify_audit_chain(
        self, start_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """감사 체인 무결성 검증"""
        query = self.db.query(AuditLog)
        if start_id:
            query = query.filter(AuditLog.id >= start_id)

        logs = query.order_by(AuditLog.id).all()

        verified_count = 0
        error_count = 0
        errors = []

        previous_hash = "0"

        for log in logs:
            # 해시 검증
            log_content = {
                "timestamp": log.timestamp.isoformat(),
                "event_type": log.event_type.value,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "event_data": log.event_data,
                "previous_hash": previous_hash,
            }

            expected_hash = hashlib.sha256(
                json.dumps(log_content, sort_keys=True).encode()
            ).hexdigest()

            # SQLAlchemy 컬럼 값을 안전하게 추출하여 비교
            actual_log_hash = safe_str_extract(log.log_hash)
            actual_block_hash = safe_str_extract(log.block_hash)

            if actual_log_hash == expected_hash and actual_block_hash == previous_hash:
                verified_count += 1
            else:
                error_count += 1
                errors.append(
                    {
                        "log_id": log.id,
                        "expected_hash": expected_hash,
                        "actual_hash": actual_log_hash,
                        "expected_block_hash": previous_hash,
                        "actual_block_hash": actual_block_hash,
                    }
                )

            previous_hash = actual_log_hash

        return {
            "total_logs": len(logs),
            "verified_count": verified_count,
            "error_count": error_count,
            "errors": errors,
            "chain_valid": error_count == 0,
        }

    def close(self):
        """세션 종료"""
        if self.db:
            self.db.close()
