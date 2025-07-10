"""
ML 기반 이상 탐지 서비스 - Doc #30
머신러닝을 활용한 의심스러운 거래 패턴 탐지
"""
import json
import decimal
from typing import Dict, Optional, List, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, desc, func

from app.models.audit import (
    SuspiciousActivity, RiskLevel, AuditEventType
)
from app.models.user import User
from app.models.transaction import Transaction
from app.services.audit.audit_service import AuditService
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


def safe_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    """안전한 Decimal 변환"""
    if value is None:
        return default
    try:
        return Decimal(str(value))
    except (ValueError, TypeError, decimal.InvalidOperation):
        return default


class MLAnomalyDetectionService:
    """ML 기반 이상 탐지 서비스"""
    
    def __init__(self, db: AsyncSession, audit_service: AuditService):
        self.db = db
        self.audit_service = audit_service
        
        # 탐지 임계값 설정
        self.thresholds = {
            "high_frequency": {"count": 50, "period_hours": 24},
            "high_amount": {"amount": Decimal("10000")},
            "velocity_check": {"amount": Decimal("50000"), "period_hours": 24},
            "round_amount": {"threshold": 0.9},  # 반올림된 금액 비율
            "unusual_time": {"start_hour": 2, "end_hour": 6},  # 새벽 시간대
            "structuring": {"amount_threshold": Decimal("9000"), "count": 3, "period_hours": 24}
        }
    
    async def analyze_transaction_patterns(
        self,
        user_id: int,
        transaction_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """트랜잭션 패턴 분석"""
        try:
            anomalies = []
            
            # 1. 고빈도 거래 탐지
            high_freq_anomaly = await self._detect_high_frequency_transactions(user_id)
            if high_freq_anomaly:
                anomalies.append(high_freq_anomaly)
            
            # 2. 고액 거래 탐지
            high_amount_anomaly = self._detect_high_amount_transaction(transaction_data)
            if high_amount_anomaly:
                anomalies.append(high_amount_anomaly)
            
            # 3. 거래 속도 분석
            velocity_anomaly = await self._detect_transaction_velocity(user_id, transaction_data)
            if velocity_anomaly:
                anomalies.append(velocity_anomaly)
            
            # 4. 반올림 금액 패턴 탐지
            round_amount_anomaly = await self._detect_round_amount_pattern(user_id)
            if round_amount_anomaly:
                anomalies.append(round_amount_anomaly)
            
            # 5. 비정상 시간대 거래 탐지
            unusual_time_anomaly = self._detect_unusual_time_transaction(transaction_data)
            if unusual_time_anomaly:
                anomalies.append(unusual_time_anomaly)
            
            # 6. 분할 거래 탐지 (구조화)
            structuring_anomaly = await self._detect_structuring_pattern(user_id, transaction_data)
            if structuring_anomaly:
                anomalies.append(structuring_anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"트랜잭션 패턴 분석 오류: {e}")
            return []
    
    async def _detect_high_frequency_transactions(self, user_id: int) -> Optional[Dict[str, Any]]:
        """고빈도 거래 탐지"""
        try:
            # 최근 24시간 거래 수 확인
            threshold_time = datetime.utcnow() - timedelta(hours=self.thresholds["high_frequency"]["period_hours"])
            
            # 실제 Transaction 모델을 사용한다면:
            # result = await self.db.execute(
            #     select(func.count(Transaction.id))
            #     .where(and_(
            #         Transaction.user_id == user_id,
            #         Transaction.created_at >= threshold_time
            #     ))
            # )
            # transaction_count = result.scalar_one_or_none() or 0
            
            # 임시로 모의 데이터 사용
            transaction_count = 75  # 예시
            
            threshold_count = self.thresholds["high_frequency"]["count"]
            
            if transaction_count > threshold_count:
                return {
                    "type": "high_frequency",
                    "severity": RiskLevel.HIGH,
                    "confidence": min(transaction_count / threshold_count, 2.0),
                    "details": {
                        "transaction_count": transaction_count,
                        "threshold": threshold_count,
                        "period_hours": self.thresholds["high_frequency"]["period_hours"]
                    },
                    "description": f"최근 24시간 내 {transaction_count}회 거래 (임계값: {threshold_count}회)"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"고빈도 거래 탐지 오류: {e}")
            return None
    
    def _detect_high_amount_transaction(self, transaction_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """고액 거래 탐지"""
        try:
            amount = safe_decimal(transaction_data.get("amount", 0))
            threshold = self.thresholds["high_amount"]["amount"]
            
            if amount > threshold:
                confidence = min(float(amount / threshold), 3.0)
                severity = RiskLevel.CRITICAL if amount > threshold * 5 else RiskLevel.HIGH
                
                return {
                    "type": "high_amount",
                    "severity": severity,
                    "confidence": confidence,
                    "details": {
                        "amount": str(amount),
                        "threshold": str(threshold),
                        "currency": transaction_data.get("currency", "USDT")
                    },
                    "description": f"고액 거래 탐지: {amount} (임계값: {threshold})"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"고액 거래 탐지 오류: {e}")
            return None
    
    async def _detect_transaction_velocity(
        self, 
        user_id: int, 
        transaction_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """거래 속도 분석"""
        try:
            # 최근 24시간 거래 총액 확인
            threshold_time = datetime.utcnow() - timedelta(hours=self.thresholds["velocity_check"]["period_hours"])
            
            # 임시로 모의 데이터 사용
            total_amount = Decimal("75000")  # 예시
            threshold_amount = self.thresholds["velocity_check"]["amount"]
            
            if total_amount > threshold_amount:
                confidence = min(float(total_amount / threshold_amount), 3.0)
                
                return {
                    "type": "high_velocity",
                    "severity": RiskLevel.HIGH,
                    "confidence": confidence,
                    "details": {
                        "total_amount": str(total_amount),
                        "threshold": str(threshold_amount),
                        "period_hours": self.thresholds["velocity_check"]["period_hours"]
                    },
                    "description": f"고속 거래 탐지: 24시간 내 {total_amount} (임계값: {threshold_amount})"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"거래 속도 분석 오류: {e}")
            return None
    
    async def _detect_round_amount_pattern(self, user_id: int) -> Optional[Dict[str, Any]]:
        """반올림 금액 패턴 탐지"""
        try:
            # 최근 거래들의 반올림 비율 분석
            # 임시로 모의 데이터 사용
            round_amounts = [1000, 5000, 10000, 2500, 7500]  # 예시 거래 금액들
            total_transactions = len(round_amounts)
            
            # 반올림된 금액 (끝자리가 00인 경우) 개수 계산
            round_count = sum(1 for amount in round_amounts if amount % 100 == 0 or amount % 1000 == 0)
            round_ratio = round_count / total_transactions if total_transactions > 0 else 0
            
            threshold = self.thresholds["round_amount"]["threshold"]
            
            if round_ratio > threshold and total_transactions >= 5:
                return {
                    "type": "round_amount_pattern",
                    "severity": RiskLevel.MEDIUM,
                    "confidence": round_ratio,
                    "details": {
                        "round_count": round_count,
                        "total_transactions": total_transactions,
                        "round_ratio": round_ratio,
                        "threshold": threshold
                    },
                    "description": f"반올림 금액 패턴: {round_count}/{total_transactions} 거래가 반올림된 금액"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"반올림 금액 패턴 탐지 오류: {e}")
            return None
    
    def _detect_unusual_time_transaction(self, transaction_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """비정상 시간대 거래 탐지"""
        try:
            # 거래 시간 확인
            transaction_time = datetime.utcnow()  # 실제로는 transaction_data에서 가져와야 함
            hour = transaction_time.hour
            
            start_hour = self.thresholds["unusual_time"]["start_hour"]
            end_hour = self.thresholds["unusual_time"]["end_hour"]
            
            # 새벽 2시-6시 거래 탐지
            if start_hour <= hour <= end_hour:
                return {
                    "type": "unusual_time",
                    "severity": RiskLevel.MEDIUM,
                    "confidence": 0.7,
                    "details": {
                        "transaction_hour": hour,
                        "unusual_period": f"{start_hour}:00-{end_hour}:00"
                    },
                    "description": f"비정상 시간대 거래: {hour}시 (새벽 시간대)"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"비정상 시간대 거래 탐지 오류: {e}")
            return None
    
    async def _detect_structuring_pattern(
        self, 
        user_id: int, 
        transaction_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """분할 거래 탐지 (구조화)"""
        try:
            # 최근 24시간 내 9000달러 미만의 거래들 확인
            threshold_time = datetime.utcnow() - timedelta(hours=self.thresholds["structuring"]["period_hours"])
            threshold_amount = self.thresholds["structuring"]["amount_threshold"]
            threshold_count = self.thresholds["structuring"]["count"]
            
            # 임시로 모의 데이터 사용
            small_transactions = [8500, 8900, 8700, 8800]  # 예시 거래들
            small_transaction_count = len(small_transactions)
            
            if small_transaction_count >= threshold_count:
                total_amount = sum(small_transactions)
                avg_amount = total_amount / small_transaction_count
                
                return {
                    "type": "structuring",
                    "severity": RiskLevel.HIGH,
                    "confidence": min(small_transaction_count / threshold_count, 2.0),
                    "details": {
                        "small_transaction_count": small_transaction_count,
                        "threshold_count": threshold_count,
                        "threshold_amount": str(threshold_amount),
                        "total_amount": total_amount,
                        "average_amount": avg_amount
                    },
                    "description": f"분할 거래 패턴: {small_transaction_count}회의 {threshold_amount} 미만 거래"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"분할 거래 탐지 오류: {e}")
            return None
    
    async def create_suspicious_activity(
        self,
        user_id: int,
        detection_type: str,
        anomaly_data: Dict[str, Any],
        transaction_ids: Optional[List[str]] = None
    ) -> Optional[SuspiciousActivity]:
        """의심스러운 활동 기록 생성"""
        try:
            # 위험도 및 점수 계산
            severity_value = anomaly_data.get("severity", RiskLevel.MEDIUM)
            
            # severity를 RiskLevel enum으로 변환
            if isinstance(severity_value, RiskLevel):
                severity = severity_value
            elif isinstance(severity_value, str):
                # 문자열을 RiskLevel로 변환
                severity_map = {
                    "low": RiskLevel.LOW,
                    "medium": RiskLevel.MEDIUM,
                    "high": RiskLevel.HIGH,
                    "critical": RiskLevel.CRITICAL
                }
                severity = severity_map.get(severity_value.lower(), RiskLevel.MEDIUM)
            else:
                severity = RiskLevel.MEDIUM
            
            confidence = anomaly_data.get("confidence", 0.5)
            
            # JSON 직렬화 가능한 데이터로 변환
            clean_anomaly_data = {}
            for key, value in anomaly_data.items():
                if hasattr(value, 'value'):  # Enum인 경우
                    clean_anomaly_data[key] = value.value
                else:
                    clean_anomaly_data[key] = value
            
            # 의심스러운 활동 생성
            suspicious_activity = SuspiciousActivity(
                detection_type=detection_type,
                severity=severity,
                user_id=user_id,
                transaction_ids=transaction_ids or [],
                pattern_name=anomaly_data.get("type", detection_type),
                pattern_data=anomaly_data.get("details", {}),
                ml_model_name="anomaly_detection_v1",
                ml_model_version="1.0.0",
                confidence_score=Decimal(str(confidence)),
                description=anomaly_data.get("description", ""),
                additional_data=clean_anomaly_data,
                action_taken="flagged",
                detected_at=datetime.utcnow()
            )
            
            self.db.add(suspicious_activity)
            await self.db.commit()
            
            # 객체를 새로고침하여 lazy loading 문제 방지
            await self.db.refresh(suspicious_activity)
            
            # 감사 로그 생성
            await self.audit_service.log_suspicious_activity(
                user_id=user_id,
                activity_type=detection_type,
                activity_data={
                    "pattern_name": anomaly_data.get("type", detection_type),
                    "confidence": confidence,
                    "details": anomaly_data.get("details", {}),
                    "action_taken": "flagged"
                },
                severity=RiskLevel.MEDIUM  # 기본값 사용
            )
            
            logger.info(f"의심스러운 활동 기록 생성: {detection_type} - 사용자 {user_id}")
            return suspicious_activity
            
        except Exception as e:
            logger.error(f"의심스러운 활동 기록 생성 오류: {e}")
            await self.db.rollback()
            return None
    
    async def process_transaction_for_anomalies(
        self,
        user_id: int,
        transaction_data: Dict[str, Any]
    ) -> List[SuspiciousActivity]:
        """트랜잭션의 이상 탐지 처리"""
        try:
            created_activities = []
            
            # 패턴 분석 수행
            anomalies = await self.analyze_transaction_patterns(user_id, transaction_data)
            
            # 각 이상 패턴에 대해 의심스러운 활동 기록 생성
            for anomaly in anomalies:
                activity = await self.create_suspicious_activity(
                    user_id=user_id,
                    detection_type=anomaly.get("type", "unknown"),
                    anomaly_data=anomaly,
                    transaction_ids=[transaction_data.get("transaction_id", "")]
                )
                if activity:
                    created_activities.append(activity)
            
            return created_activities
            
        except Exception as e:
            logger.error(f"트랜잭션 이상 탐지 처리 오류: {e}")
            return []
    
    async def get_suspicious_activities(
        self,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[int] = None,
        detection_type: Optional[str] = None,
        severity: Optional[RiskLevel] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        resolved: Optional[bool] = None
    ) -> List[SuspiciousActivity]:
        """의심스러운 활동 조회"""
        try:
            query = select(SuspiciousActivity)
            
            # 필터 조건 적용
            conditions = []
            
            if user_id:
                conditions.append(SuspiciousActivity.user_id == user_id)
            
            if detection_type:
                conditions.append(SuspiciousActivity.detection_type == detection_type)
            
            if severity:
                conditions.append(SuspiciousActivity.severity == severity)
            
            if start_date:
                conditions.append(SuspiciousActivity.detected_at >= start_date)
            
            if end_date:
                conditions.append(SuspiciousActivity.detected_at <= end_date)
            
            if resolved is not None:
                if resolved:
                    conditions.append(SuspiciousActivity.resolved_at.isnot(None))
                else:
                    conditions.append(SuspiciousActivity.resolved_at.is_(None))
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # 정렬 및 페이지네이션
            query = query.order_by(desc(SuspiciousActivity.detected_at)).offset(offset).limit(limit)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"의심스러운 활동 조회 오류: {e}")
            return []
    
    async def resolve_suspicious_activity(
        self,
        activity_id: int,
        resolver_user_id: int,
        resolution_notes: str,
        action_taken: str = "reviewed"
    ) -> bool:
        """의심스러운 활동 해결"""
        try:
            # 활동 조회
            result = await self.db.execute(
                select(SuspiciousActivity).where(SuspiciousActivity.id == activity_id)
            )
            activity = result.scalar_one_or_none()
            
            if not activity:
                logger.error(f"의심스러운 활동을 찾을 수 없음: {activity_id}")
                return False
            
            # 해결 정보 업데이트
            setattr(activity, 'resolved_at', datetime.utcnow())
            setattr(activity, 'resolved_by', resolver_user_id)
            setattr(activity, 'resolution_notes', resolution_notes)
            setattr(activity, 'action_taken', action_taken)
            
            await self.db.commit()
            
            # 객체를 새로고침하여 lazy loading 문제 방지
            await self.db.refresh(activity)
            
            # 감사 로그 생성
            await self.audit_service.log_admin_action(
                admin_user_id=resolver_user_id,
                action="resolve_suspicious_activity",
                action_data={
                    "activity_id": activity_id,
                    "detection_type": safe_str(activity.detection_type),
                    "action_taken": action_taken,
                    "resolution_notes": resolution_notes
                },
                target_entity_type="suspicious_activity",
                target_entity_id=str(activity_id),
                severity="info"
            )
            
            logger.info(f"의심스러운 활동 해결: {activity_id}")
            return True
            
        except Exception as e:
            logger.error(f"의심스러운 활동 해결 오류: {e}")
            await self.db.rollback()
            return False
    
    async def get_detection_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """탐지 통계 조회"""
        try:
            # 기본 기간 설정 (최근 30일)
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # 총 탐지 수
            total_query = select(func.count(SuspiciousActivity.id)).where(
                and_(
                    SuspiciousActivity.detected_at >= start_date,
                    SuspiciousActivity.detected_at <= end_date
                )
            )
            result = await self.db.execute(total_query)
            total_detections = result.scalar_one_or_none() or 0
            
            # 탐지 타입별 통계
            detection_types = ["high_frequency", "high_amount", "high_velocity", "round_amount_pattern", "unusual_time", "structuring"]
            type_stats = {}
            
            for detection_type in detection_types:
                query = select(func.count(SuspiciousActivity.id)).where(
                    and_(
                        SuspiciousActivity.detection_type == detection_type,
                        SuspiciousActivity.detected_at >= start_date,
                        SuspiciousActivity.detected_at <= end_date
                    )
                )
                result = await self.db.execute(query)
                count = result.scalar_one_or_none() or 0
                type_stats[detection_type] = count
            
            # 심각도별 통계
            severity_stats = {}
            for severity in RiskLevel:
                query = select(func.count(SuspiciousActivity.id)).where(
                    and_(
                        SuspiciousActivity.severity == severity,
                        SuspiciousActivity.detected_at >= start_date,
                        SuspiciousActivity.detected_at <= end_date
                    )
                )
                result = await self.db.execute(query)
                count = result.scalar_one_or_none() or 0
                severity_stats[severity.value] = count
            
            # 해결 상태 통계
            resolved_query = select(func.count(SuspiciousActivity.id)).where(
                and_(
                    SuspiciousActivity.detected_at >= start_date,
                    SuspiciousActivity.detected_at <= end_date,
                    SuspiciousActivity.resolved_at.isnot(None)
                )
            )
            result = await self.db.execute(resolved_query)
            resolved_count = result.scalar_one_or_none() or 0
            
            unresolved_count = total_detections - resolved_count
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_detections": total_detections,
                "detection_type_stats": type_stats,
                "severity_stats": severity_stats,
                "resolution_stats": {
                    "resolved": resolved_count,
                    "unresolved": unresolved_count,
                    "resolution_rate": resolved_count / total_detections if total_detections > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"탐지 통계 조회 오류: {e}")
            return {}
