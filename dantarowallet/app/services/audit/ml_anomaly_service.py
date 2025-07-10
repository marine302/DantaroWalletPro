"""
ML 이상 탐지 서비스 - 기본 통계 기반 의심스러운 활동 탐지
"""
import statistics
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.audit import SuspiciousActivity
from app.models.transaction import Transaction
from app.core.logging import get_logger
from app.core.database import get_db_session

logger = get_logger(__name__)

def safe_float_extract(value) -> float:
    """SQLAlchemy 컬럼 값을 안전하게 float로 변환"""
    try:
        if hasattr(value, '__float__'):
            return float(value)
        elif hasattr(value, 'to_eng_string'):  # Decimal 타입
            return float(str(value))
        else:
            return float(value)
    except (ValueError, TypeError):
        return 0.0

class MLAnomalyDetectionService:
    """기본 통계 기반 이상 탐지 서비스"""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db or get_db_session()
        self.config = {
            "frequency_threshold": 20,
            "amount_multiplier": 10,
            "high_risk_threshold": 0.8
        }
        logger.info("통계 기반 이상 탐지 서비스 초기화 완료")
    
    async def detect_transaction_anomalies(
        self,
        user_id: int,
        transaction_data: Dict[str, Any]
    ) -> Optional[SuspiciousActivity]:
        """트랜잭션 이상 탐지"""
        try:
            # 사용자 거래 패턴 분석
            user_patterns = await self._get_user_transaction_patterns(user_id)
            
            # 현재 거래 특성 추출
            amount = float(transaction_data.get("amount", 0))
            avg_amount = user_patterns.get("avg_amount", 1)
            
            # 간단한 이상 탐지
            anomaly_score = 0.0
            if amount > avg_amount * 10:  # 평균의 10배 초과
                anomaly_score = 0.9
            elif amount > avg_amount * 5:  # 평균의 5배 초과
                anomaly_score = 0.6
            
            # 임계값 확인
            if anomaly_score > self.config["high_risk_threshold"]:
                suspicious_activity = SuspiciousActivity(
                    detection_type="ml_model",
                    severity="high" if anomaly_score > 0.9 else "medium",
                    user_id=user_id,
                    transaction_ids=[str(transaction_data.get("transaction_id", ""))],
                    pattern_name="transaction_anomaly",
                    pattern_data={
                        "amount": amount,
                        "avg_amount": avg_amount,
                        "anomaly_score": anomaly_score
                    },
                    ml_model_name="StatisticalAnomalyDetection",
                    confidence_score=anomaly_score,
                    action_taken="flagged",
                    detected_at=datetime.utcnow()
                )
                
                self.db.add(suspicious_activity)
                self.db.commit()
                
                logger.warning(f"트랜잭션 이상 탐지: 사용자 {user_id}, 점수 {anomaly_score:.3f}")
                return suspicious_activity
            
            return None
            
        except Exception as e:
            logger.error(f"트랜잭션 이상 탐지 실패: {str(e)}")
            return None
    
    async def detect_user_behavior_anomalies(
        self,
        user_id: int,
        time_window_days: int = 30
    ) -> List[SuspiciousActivity]:
        """사용자 행동 이상 탐지"""
        try:
            anomalies = []
            
            # 거래 빈도 이상 탐지
            freq_anomaly = await self._detect_frequency_anomaly(user_id)
            if freq_anomaly:
                anomalies.append(freq_anomaly)
            
            # 거래 금액 이상 탐지
            amount_anomaly = await self._detect_amount_anomaly(user_id)
            if amount_anomaly:
                anomalies.append(amount_anomaly)
            
            # 데이터베이스에 저장
            for anomaly in anomalies:
                self.db.add(anomaly)
            
            if anomalies:
                self.db.commit()
                logger.warning(f"사용자 {user_id}에서 {len(anomalies)}개 이상 행동 탐지")
            
            return anomalies
            
        except Exception as e:
            logger.error(f"사용자 행동 이상 탐지 실패: {str(e)}")
            return []
    
    async def _get_user_transaction_patterns(self, user_id: int) -> Dict[str, float]:
        """사용자 거래 패턴 분석"""
        try:
            # 최근 30일간 거래 데이터
            recent_transactions = self.db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.created_at >= datetime.utcnow() - timedelta(days=30)
            ).all()
            
            if not recent_transactions:
                return {"avg_amount": 0.0, "std_amount": 0.0, "avg_daily_count": 0.0}
            
            amounts = [safe_float_extract(tx.amount) for tx in recent_transactions]
            
            # 통계 계산
            avg_amount = statistics.mean(amounts) if amounts else 0.0
            std_amount = statistics.stdev(amounts) if len(amounts) > 1 else 0.0
            daily_count = len(recent_transactions) / 30
            
            return {
                "avg_amount": avg_amount,
                "std_amount": std_amount,
                "avg_daily_count": daily_count
            }
            
        except Exception as e:
            logger.error(f"사용자 패턴 분석 실패: {str(e)}")
            return {"avg_amount": 0.0, "std_amount": 0.0, "avg_daily_count": 0.0}
    
    async def _detect_frequency_anomaly(self, user_id: int) -> Optional[SuspiciousActivity]:
        """거래 빈도 이상 탐지"""
        try:
            # 오늘 거래 수
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_count = self.db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.created_at >= today_start
            ).count()
            
            # 임계값 초과 시 이상
            if today_count > self.config["frequency_threshold"]:
                return SuspiciousActivity(
                    detection_type="pattern",
                    severity="high",
                    user_id=user_id,
                    pattern_name="excessive_frequency",
                    pattern_data={"today_count": today_count},
                    confidence_score=0.85,
                    action_taken="flagged",
                    detected_at=datetime.utcnow()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"빈도 이상 탐지 실패: {str(e)}")
            return None
    
    async def _detect_amount_anomaly(self, user_id: int) -> Optional[SuspiciousActivity]:
        """거래 금액 이상 탐지"""
        try:
            # 오늘 최대 거래 금액
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_transactions = self.db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.created_at >= today_start
            ).all()
            
            if not today_transactions:
                return None
            
            amounts = [safe_float_extract(tx.amount) for tx in today_transactions]
            max_amount = max(amounts)
            
            # 고액 거래 탐지 (100만원 초과)
            if max_amount > 1000000:
                return SuspiciousActivity(
                    detection_type="threshold",
                    severity="high",
                    user_id=user_id,
                    pattern_name="large_amount",
                    pattern_data={"max_amount": max_amount},
                    confidence_score=0.9,
                    action_taken="flagged",
                    detected_at=datetime.utcnow()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"금액 이상 탐지 실패: {str(e)}")
            return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_type": "StatisticalAnomalyDetection",
            "config": self.config,
            "description": "기본 통계 기반 이상 탐지"
        }
    
    def close(self):
        """세션 종료"""
        if self.db:
            self.db.close()
