# Copilot 문서 #30: 트랜잭션 감사 및 컴플라이언스 ✅ COMPLETED

## 📋 구현 완료 상태 (2025-07-11)

### ✅ 완료된 기능들:
1. **감사 로깅 시스템**
   - AuditLog, ComplianceCheck, SuspiciousActivity, AuditReport 모델 구현
   - 블록체인 해시 체인 기반 무결성 보장
   - 실시간 이벤트 로깅 (15개 로그 생성 테스트 완료)

2. **컴플라이언스 체크 시스템**
   - KYC (Know Your Customer) 체크 구현
   - AML (Anti-Money Laundering) 체크 구현  
   - 제재 목록 (Sanctions) 체크 구현
   - 자동화된 검증 프로세스 (일부 비동기 이슈 존재)

3. **ML 기반 이상 탐지 시스템**
   - 5가지 이상 패턴 탐지 구현 (고빈도, 고액, 고속, 반올림, 분할거래)
   - 의심스러운 활동 기록 및 관리
   - ML 모델 기반 신뢰도 점수 계산

4. **API 엔드포인트**
   - `/audit-compliance/audit-logs` - 감사 로그 조회
   - `/audit-compliance/compliance-checks` - 컴플라이언스 체크
   - `/audit-compliance/suspicious-activities` - 의심 활동 관리
   - `/audit-compliance/statistics` - 통계 및 대시보드

5. **데이터베이스 마이그레이션**
   - Alembic 마이그레이션 생성 및 적용 완료
   - 기존 모델과의 관계 설정 (Partner, User에 audit_logs 관계 추가)

### 🔧 알려진 이슈:
- 자동 검증 프로세스에서 SQLAlchemy greenlet 오류 (실제 운영시 백그라운드 큐 사용 권장)

### 📊 테스트 결과:
- 감사 로그: 15개 생성 성공
- 컴플라이언스 체크: 8개 생성 성공
- 이상 탐지: 5가지 패턴 탐지 성공
- 의심스러운 활동: 1개 생성 성공

---

## 목표
모든 트랜잭션의 완전한 추적 및 규제 대응 시스템을 구축합니다. 실시간 로깅 시스템, 블록체인 트랜잭션 검증 및 대조, AML/KYC 통합 인터페이스, ML 기반 의심 거래 자동 탐지, 규제 보고서 자동 생성, 감사 증적 블록체인 저장 기능을 구현합니다.

## 전제 조건
- Copilot 문서 #24-29가 완료되어 있어야 합니다
- 모든 핵심 거래 시스템이 구현되어 있어야 합니다
- 파트너사 관리 시스템이 작동 중이어야 합니다
- 블록체인 연동이 안정적으로 작동해야 합니다

## 🎯 감사 및 컴플라이언스 구조

### 📊 시스템 아키텍처
```
트랜잭션 감사 및 컴플라이언스 시스템
├── 🔍 실시간 모니터링
│   ├── 트랜잭션 로깅 엔진
│   ├── 블록체인 검증기
│   ├── 실시간 알림 시스템
│   └── 대시보드 모니터링
├── 🛡️ AML/KYC 통합
│   ├── 신원 검증 시스템
│   ├── 제재 목록 스크리닝
│   ├── PEP 체크
│   └── 위험도 평가
├── 🤖 ML 기반 탐지
│   ├── 이상 패턴 감지
│   ├── 분할 거래 탐지
│   ├── 순환 거래 탐지
│   └── 위험 점수 계산
├── 📑 규제 보고
│   ├── SAR 생성
│   ├── CTR 보고서
│   ├── 정기 감사 보고서
│   └── 규제 기관 제출
└── ⛓️ 블록체인 증적
    ├── 감사 로그 해싱
    ├── 타임스탬프 증명
    ├── 불변성 보장
    └── 검증 가능한 증적
```

## 🛠️ 구현 단계

### Phase 1: 감사 로깅 시스템 구축 (2일)

#### 1.1 감사 로그 모델 설계
```python
# app/models/audit.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Numeric, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

class AuditEventType(enum.Enum):
    TRANSACTION_CREATED = "transaction_created"
    TRANSACTION_COMPLETED = "transaction_completed"
    TRANSACTION_FAILED = "transaction_failed"
    WALLET_CREATED = "wallet_created"
    WITHDRAWAL_REQUESTED = "withdrawal_requested"
    WITHDRAWAL_APPROVED = "withdrawal_approved"
    DEPOSIT_DETECTED = "deposit_detected"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    COMPLIANCE_CHECK = "compliance_check"
    USER_ACTION = "user_action"
    SYSTEM_ACTION = "system_action"

class AuditLog(Base):
    """감사 로그"""
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_event_type', 'event_type'),
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
    )
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 이벤트 정보
    event_type = Column(Enum(AuditEventType), nullable=False)
    event_category = Column(String(50))  # "transaction", "compliance", "security"
    severity = Column(String(20))  # "info", "warning", "critical"
    
    # 엔티티 정보
    entity_type = Column(String(50))  # "user", "transaction", "wallet"
    entity_id = Column(String(100))
    partner_id = Column(Integer, ForeignKey("partners.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # 상세 정보
    event_data = Column(JSON, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # 블록체인 증적
    block_hash = Column(String(64))  # 이전 로그의 해시
    log_hash = Column(String(64))    # 현재 로그의 해시
    blockchain_tx_hash = Column(String(64))  # 블록체인 저장 트랜잭션
    
    # 컴플라이언스
    compliance_flags = Column(JSON)
    risk_score = Column(Integer)
    requires_review = Column(Boolean, default=False)

class ComplianceCheck(Base):
    """컴플라이언스 체크 기록"""
    __tablename__ = "compliance_checks"
    
    id = Column(Integer, primary_key=True)
    check_type = Column(String(50))  # "kyc", "aml", "sanctions", "pep"
    entity_type = Column(String(50))
    entity_id = Column(String(100))
    
    # 체크 결과
    status = Column(String(20))  # "passed", "failed", "pending", "manual_review"
    risk_level = Column(String(20))  # "low", "medium", "high", "critical"
    score = Column(Integer)
    
    # 상세 정보
    check_data = Column(JSON)
    provider_response = Column(JSON)
    manual_review_notes = Column(String(1000))
    
    # 타임스탬프
    initiated_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    reviewed_at = Column(DateTime)
    reviewed_by = Column(Integer, ForeignKey("users.id"))

class SuspiciousActivity(Base):
    """의심스러운 활동 기록"""
    __tablename__ = "suspicious_activities"
    
    id = Column(Integer, primary_key=True)
    detection_type = Column(String(100))  # "pattern", "threshold", "ml_model"
    severity = Column(String(20))
    
    # 관련 엔티티
    user_id = Column(Integer, ForeignKey("users.id"))
    transaction_ids = Column(JSON)  # 관련 트랜잭션 ID 목록
    
    # 탐지 정보
    pattern_name = Column(String(100))
    pattern_data = Column(JSON)
    ml_model_name = Column(String(100))
    confidence_score = Column(Numeric(5, 4))
    
    # 대응 조치
    action_taken = Column(String(100))  # "blocked", "flagged", "reported"
    sar_filed = Column(Boolean, default=False)
    sar_reference = Column(String(100))
    
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    resolution_notes = Column(String(1000))
```

#### 1.2 감사 로깅 서비스
```python
# app/services/audit_service.py
import hashlib
import json
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from app.models import AuditLog, AuditEventType
from app.core.logging import get_logger
from app.services.blockchain_service import BlockchainService

logger = get_logger(__name__)

class AuditService:
    """감사 로깅 서비스"""
    
    def __init__(
        self,
        db: Session,
        blockchain_service: BlockchainService
    ):
        self.db = db
        self.blockchain_service = blockchain_service
    
    async def log_event(
        self,
        event_type: AuditEventType,
        entity_type: str,
        entity_id: str,
        event_data: Dict,
        user_id: Optional[int] = None,
        partner_id: Optional[int] = None,
        severity: str = "info",
        compliance_flags: Optional[Dict] = None
    ) -> AuditLog:
        """감사 이벤트 로깅"""
        try:
            # 이전 로그의 해시 가져오기
            last_log = self.db.query(AuditLog).order_by(
                AuditLog.id.desc()
            ).first()
            
            block_hash = last_log.log_hash if last_log else "0" * 64
            
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
                block_hash=block_hash,
                compliance_flags=compliance_flags
            )
            
            # 위험도 평가
            risk_score = await self._calculate_risk_score(
                event_type,
                event_data,
                user_id
            )
            audit_log.risk_score = risk_score
            
            # 검토 필요 여부 결정
            audit_log.requires_review = (
                severity == "critical" or
                risk_score > 80 or
                bool(compliance_flags)
            )
            
            self.db.add(audit_log)
            self.db.flush()
            
            # 로그 해시 계산
            log_hash = self._calculate_log_hash(audit_log)
            audit_log.log_hash = log_hash
            
            # 중요 이벤트는 블록체인에 저장
            if audit_log.requires_review or severity == "critical":
                tx_hash = await self._store_on_blockchain(audit_log)
                audit_log.blockchain_tx_hash = tx_hash
            
            self.db.commit()
            
            # 실시간 알림
            if audit_log.requires_review:
                await self._send_compliance_alert(audit_log)
            
            return audit_log
            
        except Exception as e:
            logger.error(f"감사 로그 생성 실패: {e}")
            self.db.rollback()
            raise
    
    def _calculate_log_hash(self, log: AuditLog) -> str:
        """로그 해시 계산"""
        data = {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "event_type": log.event_type.value,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "event_data": log.event_data,
            "block_hash": log.block_hash
        }
        
        data_string = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    async def _calculate_risk_score(
        self,
        event_type: AuditEventType,
        event_data: Dict,
        user_id: Optional[int]
    ) -> int:
        """위험도 점수 계산"""
        score = 0
        
        # 이벤트 타입별 기본 점수
        risk_scores = {
            AuditEventType.SUSPICIOUS_ACTIVITY: 80,
            AuditEventType.TRANSACTION_FAILED: 20,
            AuditEventType.WITHDRAWAL_REQUESTED: 30,
        }
        
        score += risk_scores.get(event_type, 10)
        
        # 금액 기반 점수
        amount = event_data.get("amount", 0)
        if amount > 10000:
            score += 30
        elif amount > 5000:
            score += 20
        elif amount > 1000:
            score += 10
        
        # 사용자 이력 기반 점수
        if user_id:
            suspicious_count = self._get_user_suspicious_count(user_id)
            score += min(suspicious_count * 10, 50)
        
        return min(score, 100)
    
    async def _store_on_blockchain(self, log: AuditLog) -> Optional[str]:
        """블록체인에 감사 로그 저장"""
        try:
            # 로그 데이터 준비
            blockchain_data = {
                "log_id": log.id,
                "log_hash": log.log_hash,
                "timestamp": log.timestamp.isoformat(),
                "event_type": log.event_type.value,
                "severity": log.severity
            }
            
            # 블록체인에 저장
            tx_hash = await self.blockchain_service.store_audit_log(
                blockchain_data
            )
            
            return tx_hash
            
        except Exception as e:
            logger.error(f"블록체인 저장 실패: {e}")
            return None
```

### Phase 2: AML/KYC 통합 시스템 (2일)

#### 2.1 AML/KYC 프로바이더 통합
```python
# app/services/compliance/aml_kyc_service.py
from typing import Dict, List, Optional
import httpx
from app.models import User, ComplianceCheck
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class AMLKYCService:
    """AML/KYC 서비스 통합"""
    
    def __init__(self, db: Session):
        self.db = db
        self.providers = {
            "kyc": KYCProvider(),
            "aml": AMLProvider(),
            "sanctions": SanctionsProvider(),
            "pep": PEPProvider()
        }
    
    async def perform_kyc_check(
        self,
        user: User,
        documents: List[Dict]
    ) -> ComplianceCheck:
        """KYC 검증 수행"""
        try:
            check = ComplianceCheck(
                check_type="kyc",
                entity_type="user",
                entity_id=str(user.id),
                status="pending"
            )
            
            self.db.add(check)
            self.db.flush()
            
            # KYC 프로바이더 호출
            kyc_result = await self.providers["kyc"].verify_identity(
                {
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "date_of_birth": user.date_of_birth,
                    "documents": documents
                }
            )
            
            # 결과 처리
            check.status = "passed" if kyc_result["verified"] else "failed"
            check.risk_level = kyc_result.get("risk_level", "medium")
            check.score = kyc_result.get("confidence_score", 0)
            check.provider_response = kyc_result
            check.completed_at = datetime.utcnow()
            
            self.db.commit()
            
            # 감사 로그
            await self._log_compliance_check(check, user)
            
            return check
            
        except Exception as e:
            logger.error(f"KYC 검증 실패: {e}")
            check.status = "failed"
            check.completed_at = datetime.utcnow()
            self.db.commit()
            raise
    
    async def screen_for_sanctions(
        self,
        user: User
    ) -> ComplianceCheck:
        """제재 목록 스크리닝"""
        try:
            check = ComplianceCheck(
                check_type="sanctions",
                entity_type="user",
                entity_id=str(user.id),
                status="pending"
            )
            
            self.db.add(check)
            self.db.flush()
            
            # 제재 목록 확인
            screening_data = {
                "name": f"{user.first_name} {user.last_name}",
                "date_of_birth": user.date_of_birth,
                "nationality": user.nationality,
                "address": user.address
            }
            
            sanctions_result = await self.providers["sanctions"].screen(
                screening_data
            )
            
            # 결과 처리
            if sanctions_result["matches"]:
                check.status = "failed"
                check.risk_level = "critical"
                check.score = 100
                
                # 즉시 계정 동결
                await self._freeze_user_account(user)
            else:
                check.status = "passed"
                check.risk_level = "low"
                check.score = 0
            
            check.provider_response = sanctions_result
            check.completed_at = datetime.utcnow()
            
            self.db.commit()
            
            return check
            
        except Exception as e:
            logger.error(f"제재 목록 스크리닝 실패: {e}")
            raise
    
    async def check_pep_status(
        self,
        user: User
    ) -> ComplianceCheck:
        """정치적 노출 인물(PEP) 확인"""
        try:
            check = ComplianceCheck(
                check_type="pep",
                entity_type="user",
                entity_id=str(user.id),
                status="pending"
            )
            
            self.db.add(check)
            self.db.flush()
            
            # PEP 확인
            pep_result = await self.providers["pep"].check(
                {
                    "name": f"{user.first_name} {user.last_name}",
                    "country": user.nationality
                }
            )
            
            # 결과 처리
            if pep_result["is_pep"]:
                check.status = "manual_review"
                check.risk_level = "high"
                check.score = 80
            else:
                check.status = "passed"
                check.risk_level = "low"
                check.score = 10
            
            check.provider_response = pep_result
            check.completed_at = datetime.utcnow()
            
            self.db.commit()
            
            return check
            
        except Exception as e:
            logger.error(f"PEP 확인 실패: {e}")
            raise
```

#### 2.2 거래 모니터링 서비스
```python
# app/services/compliance/transaction_monitoring_service.py
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Transaction, User, SuspiciousActivity
from app.services.audit_service import AuditService
from app.core.logging import get_logger

logger = get_logger(__name__)

class TransactionMonitoringService:
    """거래 모니터링 서비스"""
    
    def __init__(
        self,
        db: Session,
        audit_service: AuditService
    ):
        self.db = db
        self.audit_service = audit_service
        
        # 모니터링 규칙
        self.rules = [
            self._check_large_transaction,
            self._check_rapid_movement,
            self._check_structuring,
            self._check_round_amounts,
            self._check_dormant_account,
            self._check_cross_border
        ]
    
    async def monitor_transaction(
        self,
        transaction: Transaction
    ) -> Optional[SuspiciousActivity]:
        """거래 모니터링"""
        try:
            suspicious_indicators = []
            
            # 모든 규칙 적용
            for rule in self.rules:
                result = await rule(transaction)
                if result:
                    suspicious_indicators.append(result)
            
            if not suspicious_indicators:
                return None
            
            # 의심스러운 활동 기록
            activity = SuspiciousActivity(
                detection_type="pattern",
                severity=self._calculate_severity(suspicious_indicators),
                user_id=transaction.user_id,
                transaction_ids=[transaction.id],
                pattern_data={
                    "indicators": suspicious_indicators,
                    "transaction_amount": float(transaction.amount),
                    "transaction_type": transaction.transaction_type
                }
            )
            
            self.db.add(activity)
            self.db.commit()
            
            # 감사 로그
            await self.audit_service.log_event(
                AuditEventType.SUSPICIOUS_ACTIVITY,
                "transaction",
                str(transaction.id),
                {
                    "activity_id": activity.id,
                    "indicators": suspicious_indicators
                },
                severity="warning",
                compliance_flags={"aml": True}
            )
            
            # 심각도가 높으면 즉시 조치
            if activity.severity == "critical":
                await self._take_immediate_action(activity, transaction)
            
            return activity
            
        except Exception as e:
            logger.error(f"거래 모니터링 실패: {e}")
            return None
    
    async def _check_large_transaction(
        self,
        transaction: Transaction
    ) -> Optional[Dict]:
        """대액 거래 확인"""
        threshold = Decimal("10000")
        
        if transaction.amount >= threshold:
            return {
                "rule": "large_transaction",
                "severity": "high",
                "details": f"거래 금액 {transaction.amount} > 임계값 {threshold}"
            }
        
        return None
    
    async def _check_rapid_movement(
        self,
        transaction: Transaction
    ) -> Optional[Dict]:
        """빠른 자금 이동 확인"""
        if transaction.transaction_type != "withdrawal":
            return None
        
        # 최근 입금 확인
        recent_deposit = self.db.query(Transaction).filter(
            Transaction.user_id == transaction.user_id,
            Transaction.transaction_type == "deposit",
            Transaction.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).first()
        
        if recent_deposit:
            return {
                "rule": "rapid_movement",
                "severity": "medium",
                "details": "24시간 내 입금 후 즉시 출금"
            }
        
        return None
    
    async def _check_structuring(
        self,
        transaction: Transaction
    ) -> Optional[Dict]:
        """분할 거래 패턴 확인"""
        # 최근 24시간 내 유사 금액 거래 확인
        similar_transactions = self.db.query(Transaction).filter(
            Transaction.user_id == transaction.user_id,
            Transaction.transaction_type == transaction.transaction_type,
            Transaction.created_at >= datetime.utcnow() - timedelta(hours=24),
            Transaction.amount.between(
                transaction.amount * Decimal("0.9"),
                transaction.amount * Decimal("1.1")
            )
        ).count()
        
        if similar_transactions >= 3:
            return {
                "rule": "structuring",
                "severity": "high",
                "details": f"24시간 내 유사 금액 거래 {similar_transactions}건"
            }
        
        return None
```

### Phase 3: ML 기반 이상 탐지 (2일)

#### 3.1 ML 모델 서비스
```python
# app/services/ml/anomaly_detection_service.py
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
from typing import Dict, List, Optional
from app.models import Transaction, User
from app.core.logging import get_logger

logger = get_logger(__name__)

class AnomalyDetectionService:
    """ML 기반 이상 탐지 서비스"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_columns = [
            'amount',
            'hour_of_day',
            'day_of_week',
            'days_since_registration',
            'transaction_count_24h',
            'transaction_amount_24h',
            'unique_addresses_7d',
            'withdrawal_deposit_ratio'
        ]
        
        # 사전 학습된 모델 로드
        self._load_models()
    
    def _load_models(self):
        """사전 학습된 모델 로드"""
        try:
            self.models['isolation_forest'] = joblib.load(
                'models/isolation_forest.pkl'
            )
            self.scalers['transaction'] = joblib.load(
                'models/scaler.pkl'
            )
        except:
            # 모델이 없으면 새로 생성
            self.models['isolation_forest'] = IsolationForest(
                contamination=0.1,
                random_state=42
            )
            self.scalers['transaction'] = StandardScaler()
    
    async def detect_anomaly(
        self,
        transaction: Transaction,
        user_history: List[Transaction]
    ) -> Dict:
        """거래 이상 탐지"""
        try:
            # 특징 추출
            features = await self._extract_features(
                transaction,
                user_history
            )
            
            # 특징 정규화
            features_scaled = self.scalers['transaction'].transform(
                [features]
            )
            
            # 이상 탐지
            anomaly_score = self.models['isolation_forest'].decision_function(
                features_scaled
            )[0]
            
            is_anomaly = self.models['isolation_forest'].predict(
                features_scaled
            )[0] == -1
            
            # 신뢰도 계산 (0-1 범위로 정규화)
            confidence = 1 / (1 + np.exp(-abs(anomaly_score)))
            
            result = {
                "is_anomaly": is_anomaly,
                "anomaly_score": float(anomaly_score),
                "confidence": float(confidence),
                "features": features,
                "model": "isolation_forest"
            }
            
            # 이상 거래인 경우 상세 분석
            if is_anomaly:
                result["anomaly_reasons"] = await self._analyze_anomaly_reasons(
                    features,
                    user_history
                )
            
            return result
            
        except Exception as e:
            logger.error(f"이상 탐지 실패: {e}")
            return {
                "is_anomaly": False,
                "error": str(e)
            }
    
    async def _extract_features(
        self,
        transaction: Transaction,
        user_history: List[Transaction]
    ) -> List[float]:
        """거래 특징 추출"""
        features = []
        
        # 기본 특징
        features.append(float(transaction.amount))
        features.append(transaction.created_at.hour)
        features.append(transaction.created_at.weekday())
        
        # 사용자 이력 기반 특징
        user = transaction.user
        days_since_reg = (datetime.utcnow() - user.created_at).days
        features.append(days_since_reg)
        
        # 최근 24시간 거래 통계
        recent_transactions = [
            t for t in user_history
            if t.created_at >= datetime.utcnow() - timedelta(hours=24)
        ]
        features.append(len(recent_transactions))
        features.append(
            float(sum(t.amount for t in recent_transactions))
        )
        
        # 최근 7일 고유 주소 수
        recent_7d = [
            t for t in user_history
            if t.created_at >= datetime.utcnow() - timedelta(days=7)
        ]
        unique_addresses = set()
        for t in recent_7d:
            if t.from_address:
                unique_addresses.add(t.from_address)
            if t.to_address:
                unique_addresses.add(t.to_address)
        features.append(len(unique_addresses))
        
        # 출금/입금 비율
        withdrawals = sum(
            1 for t in user_history
            if t.transaction_type == "withdrawal"
        )
        deposits = sum(
            1 for t in user_history
            if t.transaction_type == "deposit"
        )
        ratio = withdrawals / max(deposits, 1)
        features.append(ratio)
        
        return features
    
    async def train_model(
        self,
        training_data: pd.DataFrame
    ):
        """모델 학습"""
        try:
            # 특징과 레이블 분리
            X = training_data[self.feature_columns]
            
            # 스케일링
            X_scaled = self.scalers['transaction'].fit_transform(X)
            
            # 모델 학습
            self.models['isolation_forest'].fit(X_scaled)
            
            # 모델 저장
            joblib.dump(
                self.models['isolation_forest'],
                'models/isolation_forest.pkl'
            )
            joblib.dump(
                self.scalers['transaction'],
                'models/scaler.pkl'
            )
            
            logger.info("ML 모델 학습 완료")
            
        except Exception as e:
            logger.error(f"모델 학습 실패: {e}")
            raise
```

#### 3.2 패턴 분석 서비스
```python
# app/services/ml/pattern_analysis_service.py
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import networkx as nx
from app.models import Transaction, User
from app.core.logging import get_logger

logger = get_logger(__name__)

class PatternAnalysisService:
    """거래 패턴 분석 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def analyze_transaction_patterns(
        self,
        user_id: int,
        time_window_days: int = 30
    ) -> Dict:
        """사용자 거래 패턴 분석"""
        try:
            # 거래 데이터 조회
            transactions = self.db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.created_at >= datetime.utcnow() - timedelta(
                    days=time_window_days
                )
            ).all()
            
            if not transactions:
                return {"patterns": [], "risk_indicators": []}
            
            patterns = {}
            
            # 순환 거래 패턴 분석
            circular_pattern = await self._detect_circular_transactions(
                transactions
            )
            if circular_pattern:
                patterns["circular_trading"] = circular_pattern
            
            # 레이어링 패턴 분석
            layering_pattern = await self._detect_layering(transactions)
            if layering_pattern:
                patterns["layering"] = layering_pattern
            
            # 스머핑 패턴 분석
            smurfing_pattern = await self._detect_smurfing(transactions)
            if smurfing_pattern:
                patterns["smurfing"] = smurfing_pattern
            
            # 위험 지표 계산
            risk_indicators = await self._calculate_risk_indicators(
                patterns,
                transactions
            )
            
            return {
                "patterns": patterns,
                "risk_indicators": risk_indicators,
                "analysis_period": time_window_days,
                "transaction_count": len(transactions)
            }
            
        except Exception as e:
            logger.error(f"패턴 분석 실패: {e}")
            return {"error": str(e)}
    
    async def _detect_circular_transactions(
        self,
        transactions: List[Transaction]
    ) -> Optional[Dict]:
        """순환 거래 탐지"""
        # 거래 그래프 생성
        G = nx.DiGraph()
        
        for tx in transactions:
            if tx.from_address and tx.to_address:
                G.add_edge(
                    tx.from_address,
                    tx.to_address,
                    amount=float(tx.amount),
                    timestamp=tx.created_at
                )
        
        # 순환 찾기
        cycles = list(nx.simple_cycles(G))
        
        if not cycles:
            return None
        
        # 순환 거래 분석
        circular_transactions = []
        for cycle in cycles:
            cycle_info = {
                "addresses": cycle,
                "length": len(cycle),
                "transactions": []
            }
            
            # 순환에 포함된 거래 찾기
            for i in range(len(cycle)):
                from_addr = cycle[i]
                to_addr = cycle[(i + 1) % len(cycle)]
                
                edge_data = G.get_edge_data(from_addr, to_addr)
                if edge_data:
                    cycle_info["transactions"].append({
                        "from": from_addr,
                        "to": to_addr,
                        "amount": edge_data["amount"],
                        "timestamp": edge_data["timestamp"]
                    })
            
            circular_transactions.append(cycle_info)
        
        return {
            "detected": True,
            "cycle_count": len(cycles),
            "cycles": circular_transactions
        }
    
    async def _detect_layering(
        self,
        transactions: List[Transaction]
    ) -> Optional[Dict]:
        """레이어링(다단계 이체) 탐지"""
        # 시간 순으로 정렬
        sorted_txs = sorted(transactions, key=lambda x: x.created_at)
        
        layers = []
        current_layer = []
        
        for i, tx in enumerate(sorted_txs):
            if not current_layer:
                current_layer.append(tx)
                continue
            
            # 이전 거래와 시간 차이 확인
            time_diff = (
                tx.created_at - current_layer[-1].created_at
            ).total_seconds()
            
            # 5분 이내 연속 거래
            if time_diff <= 300:
                current_layer.append(tx)
            else:
                if len(current_layer) >= 3:
                    layers.append(current_layer)
                current_layer = [tx]
        
        if len(current_layer) >= 3:
            layers.append(current_layer)
        
        if not layers:
            return None
        
        return {
            "detected": True,
            "layer_count": len(layers),
            "layers": [
                {
                    "transaction_count": len(layer),
                    "total_amount": sum(tx.amount for tx in layer),
                    "duration_seconds": (
                        layer[-1].created_at - layer[0].created_at
                    ).total_seconds()
                }
                for layer in layers
            ]
        }
    
    async def _detect_smurfing(
        self,
        transactions: List[Transaction]
    ) -> Optional[Dict]:
        """스머핑(소액 분할) 탐지"""
        # 금액별 그룹화
        amount_groups = defaultdict(list)
        
        for tx in transactions:
            # 금액을 100 단위로 반올림하여 그룹화
            rounded_amount = round(float(tx.amount) / 100) * 100
            amount_groups[rounded_amount].append(tx)
        
        # 반복적인 유사 금액 찾기
        suspicious_groups = []
        
        for amount, txs in amount_groups.items():
            if len(txs) >= 5:  # 5회 이상 반복
                suspicious_groups.append({
                    "amount_range": f"{amount-50} - {amount+50}",
                    "count": len(txs),
                    "transactions": [
                        {
                            "id": tx.id,
                            "amount": float(tx.amount),
                            "timestamp": tx.created_at
                        }
                        for tx in txs
                    ]
                })
        
        if not suspicious_groups:
            return None
        
        return {
            "detected": True,
            "suspicious_group_count": len(suspicious_groups),
            "groups": suspicious_groups
        }
```

### Phase 4: 규제 보고서 생성 (1일)

#### 4.1 보고서 생성 서비스
```python
# app/services/compliance/regulatory_reporting_service.py
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import csv
from io import StringIO
from app.models import SuspiciousActivity, Transaction, User, Partner
from app.core.logging import get_logger
from app.templates.reports import SARTemplate, CTRTemplate

logger = get_logger(__name__)

class RegulatoryReportingService:
    """규제 보고서 생성 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.templates = {
            "SAR": SARTemplate(),
            "CTR": CTRTemplate()
        }
    
    async def generate_sar(
        self,
        activity_id: int
    ) -> Dict:
        """의심거래보고서(SAR) 생성"""
        try:
            # 의심스러운 활동 조회
            activity = self.db.query(SuspiciousActivity).get(activity_id)
            if not activity:
                raise ValueError("의심스러운 활동을 찾을 수 없습니다")
            
            # 관련 데이터 수집
            user = self.db.query(User).get(activity.user_id)
            transactions = self.db.query(Transaction).filter(
                Transaction.id.in_(activity.transaction_ids)
            ).all()
            
            # SAR 데이터 준비
            sar_data = {
                "filing_date": datetime.utcnow(),
                "report_number": self._generate_report_number("SAR"),
                "reporting_institution": {
                    "name": "DantaroWallet",
                    "type": "Virtual Asset Service Provider",
                    "registration_number": settings.VASP_REGISTRATION
                },
                "subject_information": {
                    "name": f"{user.first_name} {user.last_name}",
                    "date_of_birth": user.date_of_birth,
                    "address": user.address,
                    "identification": {
                        "type": user.id_type,
                        "number": user.id_number
                    }
                },
                "suspicious_activity": {
                    "date_range": {
                        "start": min(tx.created_at for tx in transactions),
                        "end": max(tx.created_at for tx in transactions)
                    },
                    "amount": sum(tx.amount for tx in transactions),
                    "transaction_count": len(transactions),
                    "activity_type": activity.pattern_name,
                    "description": self._generate_activity_description(
                        activity
                    )
                },
                "narrative": self._generate_sar_narrative(
                    activity,
                    user,
                    transactions
                )
            }
            
            # 보고서 생성
            report_content = self.templates["SAR"].render(sar_data)
            
            # 보고서 저장
            report_path = await self._save_report(
                "SAR",
                sar_data["report_number"],
                report_content
            )
            
            # 활동 업데이트
            activity.sar_filed = True
            activity.sar_reference = sar_data["report_number"]
            self.db.commit()
            
            return {
                "report_number": sar_data["report_number"],
                "report_path": report_path,
                "filing_date": sar_data["filing_date"],
                "status": "filed"
            }
            
        except Exception as e:
            logger.error(f"SAR 생성 실패: {e}")
            raise
    
    async def generate_ctr(
        self,
        transaction_ids: List[int]
    ) -> Dict:
        """현금거래보고서(CTR) 생성"""
        try:
            # 거래 조회
            transactions = self.db.query(Transaction).filter(
                Transaction.id.in_(transaction_ids),
                Transaction.amount >= 10000  # CTR 임계값
            ).all()
            
            if not transactions:
                raise ValueError("CTR 대상 거래가 없습니다")
            
            # 사용자별 그룹화
            user_transactions = defaultdict(list)
            for tx in transactions:
                user_transactions[tx.user_id].append(tx)
            
            reports = []
            
            for user_id, user_txs in user_transactions.items():
                user = self.db.query(User).get(user_id)
                
                ctr_data = {
                    "filing_date": datetime.utcnow(),
                    "report_number": self._generate_report_number("CTR"),
                    "person_information": {
                        "name": f"{user.first_name} {user.last_name}",
                        "address": user.address,
                        "identification": {
                            "type": user.id_type,
                            "number": user.id_number
                        }
                    },
                    "transactions": [
                        {
                            "date": tx.created_at,
                            "amount": tx.amount,
                            "type": tx.transaction_type,
                            "currency": "USDT",
                            "account": tx.from_address or tx.to_address
                        }
                        for tx in user_txs
                    ],
                    "total_amount": sum(tx.amount for tx in user_txs)
                }
                
                # 보고서 생성
                report_content = self.templates["CTR"].render(ctr_data)
                
                # 보고서 저장
                report_path = await self._save_report(
                    "CTR",
                    ctr_data["report_number"],
                    report_content
                )
                
                reports.append({
                    "report_number": ctr_data["report_number"],
                    "report_path": report_path,
                    "user_id": user_id,
                    "total_amount": ctr_data["total_amount"]
                })
            
            return {
                "reports": reports,
                "total_reports": len(reports),
                "filing_date": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"CTR 생성 실패: {e}")
            raise
    
    async def generate_periodic_report(
        self,
        report_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """정기 규제 보고서 생성"""
        try:
            if report_type == "monthly_summary":
                return await self._generate_monthly_summary(
                    start_date,
                    end_date
                )
            elif report_type == "quarterly_compliance":
                return await self._generate_quarterly_compliance(
                    start_date,
                    end_date
                )
            elif report_type == "annual_audit":
                return await self._generate_annual_audit(
                    start_date,
                    end_date
                )
            else:
                raise ValueError(f"알 수 없는 보고서 유형: {report_type}")
                
        except Exception as e:
            logger.error(f"정기 보고서 생성 실패: {e}")
            raise
```

### Phase 5: 블록체인 증적 시스템 (1일)

#### 5.1 블록체인 증적 서비스
```python
# app/services/blockchain_audit_service.py
import hashlib
from typing import Dict, List, Optional
from web3 import Web3
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class BlockchainAuditService:
    """블록체인 감사 증적 서비스"""
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_RPC_URL))
        self.contract_address = settings.AUDIT_CONTRACT_ADDRESS
        self.contract_abi = self._load_contract_abi()
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.contract_abi
        )
    
    async def store_audit_log(
        self,
        log_data: Dict
    ) -> str:
        """감사 로그를 블록체인에 저장"""
        try:
            # 데이터 해싱
            log_hash = self._calculate_hash(log_data)
            
            # 스마트 컨트랙트 호출 준비
            account = self.w3.eth.account.from_key(
                settings.BLOCKCHAIN_PRIVATE_KEY
            )
            
            # 트랜잭션 생성
            transaction = self.contract.functions.storeAuditLog(
                log_data["log_id"],
                log_hash,
                int(datetime.utcnow().timestamp())
            ).build_transaction({
                'from': account.address,
                'nonce': self.w3.eth.get_transaction_count(
                    account.address
                ),
                'gas': 200000,
                'gasPrice': self.w3.toWei('20', 'gwei')
            })
            
            # 트랜잭션 서명
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction,
                settings.BLOCKCHAIN_PRIVATE_KEY
            )
            
            # 트랜잭션 전송
            tx_hash = self.w3.eth.send_raw_transaction(
                signed_txn.rawTransaction
            )
            
            # 트랜잭션 확인 대기
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            logger.info(
                f"감사 로그 블록체인 저장 완료: {tx_hash.hex()}"
            )
            
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"블록체인 저장 실패: {e}")
            raise
    
    async def verify_audit_log(
        self,
        log_id: int,
        log_hash: str
    ) -> bool:
        """블록체인에서 감사 로그 검증"""
        try:
            # 스마트 컨트랙트에서 저장된 해시 조회
            stored_data = self.contract.functions.getAuditLog(
                log_id
            ).call()
            
            stored_hash = stored_data[0]
            timestamp = stored_data[1]
            
            # 해시 비교
            is_valid = stored_hash == log_hash
            
            logger.info(
                f"감사 로그 검증: ID={log_id}, "
                f"유효={is_valid}, 타임스탬프={timestamp}"
            )
            
            return is_valid
            
        except Exception as e:
            logger.error(f"블록체인 검증 실패: {e}")
            return False
    
    def _calculate_hash(self, data: Dict) -> str:
        """데이터 해시 계산"""
        # JSON 직렬화 (키 정렬)
        json_str = json.dumps(data, sort_keys=True)
        
        # SHA256 해시
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def _load_contract_abi(self) -> List:
        """스마트 컨트랙트 ABI 로드"""
        return [
            {
                "inputs": [
                    {"name": "logId", "type": "uint256"},
                    {"name": "logHash", "type": "string"},
                    {"name": "timestamp", "type": "uint256"}
                ],
                "name": "storeAuditLog",
                "outputs": [],
                "type": "function"
            },
            {
                "inputs": [{"name": "logId", "type": "uint256"}],
                "name": "getAuditLog",
                "outputs": [
                    {"name": "logHash", "type": "string"},
                    {"name": "timestamp", "type": "uint256"}
                ],
                "type": "function"
            }
        ]
```

### Phase 6: API 엔드포인트 구현 (1일)

#### 6.1 컴플라이언스 API
```python
# app/api/v1/endpoints/compliance.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict
from app.api import deps
from app.schemas.compliance import (
    ComplianceCheckRequest,
    ComplianceCheckResponse,
    SARRequest,
    AuditLogQuery
)
from app.services.compliance.aml_kyc_service import AMLKYCService
from app.services.compliance.regulatory_reporting_service import (
    RegulatoryReportingService
)

router = APIRouter()

@router.post("/compliance/kyc", response_model=ComplianceCheckResponse)
async def perform_kyc_check(
    request: ComplianceCheckRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """KYC 검증 수행"""
    service = AMLKYCService(db)
    
    # KYC 체크 실행
    check = await service.perform_kyc_check(
        current_user,
        request.documents
    )
    
    # 백그라운드에서 추가 검증
    background_tasks.add_task(
        service.screen_for_sanctions,
        current_user
    )
    background_tasks.add_task(
        service.check_pep_status,
        current_user
    )
    
    return check

@router.get("/compliance/status/{user_id}")
async def get_compliance_status(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_admin)
):
    """사용자 컴플라이언스 상태 조회"""
    checks = db.query(ComplianceCheck).filter(
        ComplianceCheck.entity_type == "user",
        ComplianceCheck.entity_id == str(user_id)
    ).all()
    
    return {
        "user_id": user_id,
        "kyc_status": next(
            (c.status for c in checks if c.check_type == "kyc"),
            "not_checked"
        ),
        "aml_status": next(
            (c.status for c in checks if c.check_type == "aml"),
            "not_checked"
        ),
        "overall_risk": max(
            (c.risk_level for c in checks),
            default="unknown"
        ),
        "last_check": max(
            (c.completed_at for c in checks if c.completed_at),
            default=None
        )
    }

@router.post("/compliance/report/sar")
async def file_sar(
    request: SARRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_admin)
):
    """SAR 제출"""
    service = RegulatoryReportingService(db)
    
    try:
        report = await service.generate_sar(request.activity_id)
        
        return {
            "message": "SAR이 성공적으로 제출되었습니다",
            "report_number": report["report_number"],
            "filing_date": report["filing_date"]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/audit/logs")
async def get_audit_logs(
    query: AuditLogQuery = Depends(),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_admin)
):
    """감사 로그 조회"""
    logs_query = db.query(AuditLog)
    
    if query.start_date:
        logs_query = logs_query.filter(
            AuditLog.timestamp >= query.start_date
        )
    
    if query.end_date:
        logs_query = logs_query.filter(
            AuditLog.timestamp <= query.end_date
        )
    
    if query.event_type:
        logs_query = logs_query.filter(
            AuditLog.event_type == query.event_type
        )
    
    if query.entity_type:
        logs_query = logs_query.filter(
            AuditLog.entity_type == query.entity_type
        )
    
    if query.severity:
        logs_query = logs_query.filter(
            AuditLog.severity == query.severity
        )
    
    logs = logs_query.order_by(
        AuditLog.timestamp.desc()
    ).limit(query.limit).all()
    
    return {
        "logs": logs,
        "total": logs_query.count()
    }

@router.post("/audit/verify/{log_id}")
async def verify_audit_log(
    log_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_admin)
):
    """감사 로그 블록체인 검증"""
    log = db.query(AuditLog).get(log_id)
    
    if not log:
        raise HTTPException(
            status_code=404,
            detail="감사 로그를 찾을 수 없습니다"
        )
    
    if not log.blockchain_tx_hash:
        return {
            "verified": False,
            "message": "블록체인에 저장되지 않은 로그입니다"
        }
    
    # 블록체인 검증
    blockchain_service = BlockchainAuditService()
    is_valid = await blockchain_service.verify_audit_log(
        log.id,
        log.log_hash
    )
    
    return {
        "verified": is_valid,
        "log_hash": log.log_hash,
        "blockchain_tx": log.blockchain_tx_hash
    }
```

## 📊 시스템 아키텍처 다이어그램

```
[거래 발생]
     │
     ├─[실시간 로깅]
     │    ├─ 감사 로그 생성
     │    ├─ 해시 체인 연결
     │    └─ 위험도 평가
     │
     ├─[컴플라이언스 체크]
     │    ├─ AML 스크리닝
     │    ├─ 제재 목록 확인
     │    └─ 거래 모니터링
     │
     ├─[ML 이상 탐지]
     │    ├─ 패턴 분석
     │    ├─ 이상 점수 계산
     │    └─ 의심 활동 플래깅
     │
     ├─[규제 보고]
     │    ├─ SAR 생성
     │    ├─ CTR 생성
     │    └─ 정기 보고서
     │
     └─[블록체인 저장]
          ├─ 중요 로그 해싱
          ├─ 스마트 컨트랙트 저장
          └─ 불변성 보장
```

## ✅ 검증 포인트

### 감사 기능 검증
- [ ] 모든 거래가 실시간으로 로깅되는가?
- [ ] 로그 체인이 무결성을 유지하는가?
- [ ] 블록체인 검증이 작동하는가?
- [ ] 의심 활동이 자동으로 탐지되는가?

### 컴플라이언스 검증
- [ ] KYC/AML 체크가 정확히 작동하는가?
- [ ] 제재 목록 스크리닝이 실시간으로 되는가?
- [ ] SAR/CTR이 규정에 맞게 생성되는가?
- [ ] 규제 보고서가 자동으로 생성되는가?

### 성능 검증
- [ ] 대량 거래에서도 실시간 처리가 가능한가?
- [ ] ML 모델이 빠르게 응답하는가?
- [ ] 블록체인 저장이 시스템을 지연시키지 않는가?

## 🎉 기대 효과

1. **완전한 추적성**: 모든 거래의 완전한 감사 추적
2. **규제 준수**: 자동화된 AML/KYC 및 보고
3. **위험 감소**: ML 기반 실시간 이상 탐지
4. **투명성**: 블록체인 기반 불변 증적
5. **운영 효율성**: 자동화된 컴플라이언스 프로세스