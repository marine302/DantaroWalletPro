"""
Doc #30 트랜잭션 감사 및 컴플라이언스 시스템 테스트
"""
import asyncio
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.models.audit import AuditEventType, ComplianceCheckType, RiskLevel
from app.services.audit.audit_service import AuditService
from app.services.audit.compliance_service import ComplianceService
from app.services.audit.ml_anomaly_service import MLAnomalyDetectionService

# 데이터베이스 연결 설정
DATABASE_URL = "sqlite+aiosqlite:///./dev.db"
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine)


async def test_audit_system():
    """감사 시스템 테스트"""
    print("=== Doc #30 트랜잭션 감사 및 컴플라이언스 시스템 테스트 ===\n")
    
    async with async_session() as db:
        # 서비스 초기화
        audit_service = AuditService(db)
        compliance_service = ComplianceService(db, audit_service)
        ml_service = MLAnomalyDetectionService(db, audit_service)
        
        # 1. 감사 로그 테스트
        print("1. 감사 로그 생성 테스트...")
        audit_log = await audit_service.log_event(
            event_type=AuditEventType.TRANSACTION_CREATED,
            entity_type="transaction",
            entity_id="test_tx_001",
            event_data={
                "amount": "1000.0",
                "currency": "USDT",
                "from_address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
                "to_address": "TG3XXyExBkPp9nzdajDZsozEu4BkaSJozs"
            },
            user_id=1,
            severity="info",
            event_category="transaction"
        )
        
        if audit_log:
            # 세션이 활성화된 상태에서 ID 접근
            audit_log_id = audit_log.id
            print(f"✅ 감사 로그 생성 성공: ID {audit_log_id}")
        else:
            print("❌ 감사 로그 생성 실패")
        
        # 2. KYC 체크 테스트
        print("\n2. KYC 체크 테스트...")
        kyc_check = await compliance_service.perform_kyc_check(
            user_id=1,
            kyc_data={
                "user_email": "test@example.com",
                "kyc_level": "basic",
                "documents": ["passport", "address_proof"]
            }
        )
        
        if kyc_check:
            kyc_check_id = kyc_check.id
            kyc_check_status = kyc_check.status
            print(f"✅ KYC 체크 성공: ID {kyc_check_id}, 상태: {kyc_check_status}")
        else:
            print("❌ KYC 체크 실패")
        
        # 3. AML 체크 테스트
        print("\n3. AML 체크 테스트...")
        aml_check = await compliance_service.perform_aml_check(
            transaction_id="test_tx_001",
            transaction_data={
                "amount": "15000.0",  # 고액 거래
                "currency": "USDT",
                "from_address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
                "to_address": "TG3XXyExBkPp9nzdajDZsozEu4BkaSJozs",
                "transaction_type": "withdrawal",
                "user_id": 1
            }
        )
        
        if aml_check:
            aml_check_id = aml_check.id
            aml_check_status = aml_check.status
            aml_check_risk = aml_check.risk_level
            print(f"✅ AML 체크 성공: ID {aml_check_id}, 상태: {aml_check_status}, 위험도: {aml_check_risk}")
        else:
            print("❌ AML 체크 실패")
        
        # 4. 제재 목록 체크 테스트
        print("\n4. 제재 목록 체크 테스트...")
        sanctions_check = await compliance_service.perform_sanctions_check(
            entity_type="user",
            entity_id="1",
            entity_data={
                "name": "Normal User",
                "address": "123 Main St",
                "country": "US"
            }
        )
        
        if sanctions_check:
            sanctions_check_id = sanctions_check.id
            sanctions_check_status = sanctions_check.status
            print(f"✅ 제재 목록 체크 성공: ID {sanctions_check_id}, 상태: {sanctions_check_status}")
        else:
            print("❌ 제재 목록 체크 실패")
        
        # 5. ML 이상 탐지 테스트
        print("\n5. ML 이상 탐지 테스트...")
        anomalies = await ml_service.analyze_transaction_patterns(
            user_id=1,
            transaction_data={
                "transaction_id": "test_tx_002",
                "amount": "12000.0",
                "currency": "USDT",
                "timestamp": datetime.utcnow()
            }
        )
        
        print(f"✅ 이상 패턴 {len(anomalies)}개 탐지:")
        for anomaly in anomalies:
            print(f"   - {anomaly['type']}: {anomaly['description']} (신뢰도: {anomaly['confidence']:.2f})")
        
        # 6. 의심스러운 활동 생성 테스트
        if anomalies:
            print("\n6. 의심스러운 활동 생성 테스트...")
            activity = await ml_service.create_suspicious_activity(
                user_id=1,
                detection_type=anomalies[0]['type'],
                anomaly_data=anomalies[0],
                transaction_ids=["test_tx_002"]
            )
            
            if activity:
                activity_id = activity.id
                print(f"✅ 의심스러운 활동 생성 성공: ID {activity_id}")
            else:
                print("❌ 의심스러운 활동 생성 실패")
        
        # 7. 통계 조회 테스트
        print("\n7. 통계 조회 테스트...")
        
        # 감사 통계
        audit_stats = await audit_service.get_audit_statistics()
        print(f"✅ 감사 통계: 총 {audit_stats.get('total_logs', 0)}개 로그")
        
        # 컴플라이언스 통계
        compliance_stats = await compliance_service.get_compliance_statistics()
        print(f"✅ 컴플라이언스 통계: 총 {compliance_stats.get('total_checks', 0)}개 체크")
        
        # 탐지 통계
        detection_stats = await ml_service.get_detection_statistics()
        print(f"✅ 탐지 통계: 총 {detection_stats.get('total_detections', 0)}개 탐지")
        
        print("\n=== 모든 테스트 완료 ===")


if __name__ == "__main__":
    asyncio.run(test_audit_system())
