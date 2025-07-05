"""
알림 관리 서비스
"""
import json
import logging
from datetime import datetime
from typing import List, Optional

from app.core.exceptions import NotFoundError, ValidationError
from app.models.transaction_analytics import TransactionAlert
from app.schemas.transaction_analytics import AlertRequest, AlertResponse
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from .utils import BaseAnalyticsService

logger = logging.getLogger(__name__)


class AlertService(BaseAnalyticsService):
    """알림 관리 전용 서비스"""

    async def create_alert(
        self, db: AsyncSession, alert_request: AlertRequest
    ) -> AlertResponse:
        """새로운 알림 생성"""
        try:
            # 알림 데이터 JSON 변환
            alert_data_json = None
            if alert_request.alert_data:
                alert_data_json = json.dumps(alert_request.alert_data)

            alert = TransactionAlert(
                user_id=alert_request.user_id,
                transaction_id=alert_request.transaction_id,
                alert_type=alert_request.alert_type,
                level=alert_request.level.value,
                title=alert_request.title,
                description=alert_request.description,
                alert_data=alert_data_json,
            )

            db.add(alert)
            await db.commit()
            await db.refresh(alert)

            logger.info(
                f"알림 생성됨: {alert.id} (타입: {alert.alert_type}, 레벨: {alert.level})"
            )

            return AlertResponse(
                id=alert.id,  # type: ignore
                user_id=alert.user_id,  # type: ignore
                transaction_id=alert.transaction_id,  # type: ignore
                alert_type=alert.alert_type,  # type: ignore
                level=alert.level,  # type: ignore
                title=alert.title,  # type: ignore
                description=alert.description,  # type: ignore
                is_resolved=alert.is_resolved,  # type: ignore
                resolved_by=alert.resolved_by,  # type: ignore
                resolved_at=alert.resolved_at,  # type: ignore
                created_at=alert.created_at,  # type: ignore
                alert_data=json.loads(alert.alert_data) if alert.alert_data else None,  # type: ignore
            )

        except Exception as e:
            await db.rollback()
            logger.error(f"알림 생성 중 오류: {str(e)}")
            raise ValidationError(f"알림을 생성할 수 없습니다: {str(e)}")

    async def get_alerts(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        alert_type: Optional[str] = None,
        level: Optional[str] = None,
        is_resolved: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AlertResponse]:
        """알림 목록 조회"""
        try:
            query = select(TransactionAlert)

            if user_id:
                query = query.where(TransactionAlert.user_id == user_id)
            if alert_type:
                query = query.where(TransactionAlert.alert_type == alert_type)
            if level:
                query = query.where(TransactionAlert.level == level)
            if is_resolved is not None:
                query = query.where(TransactionAlert.is_resolved == is_resolved)

            query = query.order_by(desc(TransactionAlert.created_at))
            query = query.offset(offset).limit(limit)

            result = await db.execute(query)
            alerts = result.scalars().all()

            return [self._convert_to_response(alert) for alert in alerts]

        except Exception as e:
            logger.error(f"알림 목록 조회 중 오류: {str(e)}")
            raise ValidationError(f"알림 목록을 조회할 수 없습니다: {str(e)}")

    async def get_alert_by_id(self, db: AsyncSession, alert_id: int) -> AlertResponse:
        """알림 상세 조회"""
        try:
            result = await db.execute(
                select(TransactionAlert).where(TransactionAlert.id == alert_id)
            )
            alert = result.scalar_one_or_none()

            if not alert:
                raise NotFoundError("알림을 찾을 수 없습니다")

            return self._convert_to_response(alert)

        except Exception as e:
            logger.error(f"알림 조회 중 오류: {str(e)}")
            raise ValidationError(f"알림을 조회할 수 없습니다: {str(e)}")

    async def resolve_alert(self, db: AsyncSession, alert_id: int, admin_id: int):
        """알림 해결 처리"""
        try:
            result = await db.execute(
                select(TransactionAlert).where(TransactionAlert.id == alert_id)
            )
            alert = result.scalar_one_or_none()

            if not alert:
                raise NotFoundError("알림을 찾을 수 없습니다")

            if alert.is_resolved:  # type: ignore
                raise ValidationError("이미 해결된 알림입니다")

            alert.is_resolved = True  # type: ignore
            alert.resolved_by = admin_id  # type: ignore
            alert.resolved_at = datetime.utcnow()  # type: ignore

            await db.commit()

        except Exception as e:
            await db.rollback()
            logger.error(f"알림 해결 중 오류: {str(e)}")
            raise ValidationError(f"알림을 해결할 수 없습니다: {str(e)}")

    def _convert_to_response(self, alert: TransactionAlert) -> AlertResponse:
        """모델을 응답 객체로 변환"""
        return AlertResponse(
            id=alert.id,  # type: ignore
            user_id=alert.user_id,  # type: ignore
            transaction_id=alert.transaction_id,  # type: ignore
            alert_type=alert.alert_type,  # type: ignore
            level=alert.level,  # type: ignore
            title=alert.title,  # type: ignore
            description=alert.description,  # type: ignore
            is_resolved=alert.is_resolved,  # type: ignore
            resolved_by=alert.resolved_by,  # type: ignore
            resolved_at=alert.resolved_at,  # type: ignore
            created_at=alert.created_at,  # type: ignore
            alert_data=json.loads(alert.alert_data) if alert.alert_data else None,  # type: ignore
        )
