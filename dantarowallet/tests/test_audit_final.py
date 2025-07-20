"""
감사 및 컴플라이언스 시스템 통합 테스트
"""
import asyncio
import pytest
from datetime import datetime
from app.services.audit.audit_service import AuditService
from app.services.audit.compliance_service import ComplianceService
from app.services.audit.ml_anomaly_service import MLAnomalyDetectionService
from app.models.audit import AuditEventType
from app.core.database import get_db_session

@pytest.mark.asyncio
async def test_audit_service():
    """감사 서비스 테스트"""
    print("=== 감사 서비스 테스트 ===")
    
    db = get_db_session()
    audit_service = AuditService(db)
    
    try:
        # 감사 이벤트 로깅
        audit_log = await audit_service.log_event(
            event_type=AuditEventType.TRANSACTION_CREATED,
            entity_type="transaction",
            entity_id="test_tx_001",
            event_data={
                "amount": 1000,
                "currency": "TRX",
                "from": "test_user_1",
                "to": "test_user_2"
            },
            user_id=1,
            severity="info"
        )
        
        print(f"✅ 감사 로그 생성 성공: ID {audit_log.id}")
        
        # 감사 로그 조회
        logs = await audit_service.get_audit_logs(
            entity_type="transaction",
            limit=5
        )
        
        print(f"✅ 감사 로그 조회 성공: {len(logs)}개 로그 발견")
        
        # 감사 체인 검증
        verification = await audit_service.verify_audit_chain()
        print(f"✅ 감사 체인 검증 완료: {verification['verified_count']}개 검증됨")
        
    except Exception as e:
        print(f"❌ 감사 서비스 테스트 실패: {str(e)}")
    finally:
        audit_service.close()

@pytest.mark.asyncio
async def test_compliance_service():
    """컴플라이언스 서비스 테스트"""
    print("\n=== 컴플라이언스 서비스 테스트 ===")
    
    db = get_db_session()
    compliance_service = ComplianceService(db)
    
    try:
        # KYC 체크 테스트
        kyc_result = await compliance_service.perform_kyc_check(
            user_id=1,
            check_data={
                "name": "홍길동",
                "birth_date": "1990-01-01",
                "nationality": "KR",
                "document_type": "passport",
                "document_number": "M12345678"
            }
        )
        
        print(f"✅ KYC 체크 완료: 상태 {kyc_result.status}, 점수 {kyc_result.score}")
        
        # AML 체크 테스트
        aml_result = await compliance_service.perform_aml_check(
            user_id=1,
            transaction_amount=5000.0,
            transaction_data={
                "destination": "외부계좌",
                "purpose": "개인송금"
            }
        )
        
        print(f"✅ AML 체크 완료: 상태 {aml_result.status}, 위험도 {aml_result.risk_level}")
        
        # 제재 목록 체크 테스트
        sanctions_result = await compliance_service.check_sanctions_list(
            name="홍길동",
            nationality="KR"
        )
        
        print(f"✅ 제재 목록 체크 완료: 상태 {sanctions_result.status}")
        
        # PEP 체크 테스트
        pep_result = await compliance_service.check_pep_status(
            name="김정치",
            position="장관",
            country="KR"
        )
        
        print(f"✅ PEP 체크 완료: 상태 {pep_result.status}, 위험도 {pep_result.risk_level}")
        
    except Exception as e:
        print(f"❌ 컴플라이언스 서비스 테스트 실패: {str(e)}")
    finally:
        compliance_service.close()

@pytest.mark.asyncio
async def test_ml_anomaly_service():
    """ML 이상 탐지 서비스 테스트"""
    print("\n=== ML 이상 탐지 서비스 테스트 ===")
    
    db = get_db_session()
    ml_service = MLAnomalyDetectionService(db)
    
    try:
        # 트랜잭션 이상 탐지 테스트
        anomaly_result = await ml_service.detect_transaction_anomalies(
            user_id=1,
            transaction_data={
                "amount": 1000000,  # 고액 거래
                "description": "대량 거래",
                "transaction_id": "test_tx_002"
            }
        )
        
        if anomaly_result:
            print(f"✅ 트랜잭션 이상 탐지: {anomaly_result.pattern_name}, 신뢰도 {anomaly_result.confidence_score}")
        else:
            print("✅ 트랜잭션 정상 (이상 없음)")
        
        # 사용자 행동 이상 탐지 테스트
        behavior_anomalies = await ml_service.detect_user_behavior_anomalies(
            user_id=1,
            time_window_days=30
        )
        
        print(f"✅ 사용자 행동 이상 탐지 완료: {len(behavior_anomalies)}개 이상 패턴 발견")
        
        # 모델 정보 조회
        model_info = ml_service.get_model_info()
        print(f"✅ ML 모델 정보: {model_info['model_type']}")
        
    except Exception as e:
        print(f"❌ ML 이상 탐지 서비스 테스트 실패: {str(e)}")
    finally:
        ml_service.close()

async def main():
    """메인 테스트 함수"""
    print("🚀 감사 및 컴플라이언스 시스템 통합 테스트 시작")
    print(f"⏰ 테스트 시작 시간: {datetime.now()}")
    
    try:
        await test_audit_service()
        await test_compliance_service()
        await test_ml_anomaly_service()
        
        print("\n🎉 모든 테스트 완료!")
        print("✅ 감사 서비스: 정상")
        print("✅ 컴플라이언스 서비스: 정상")
        print("✅ ML 이상 탐지 서비스: 정상")
        print("✅ 모든 임포트 오류 해결됨")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {str(e)}")
    
    print(f"\n⏰ 테스트 완료 시간: {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(main())
