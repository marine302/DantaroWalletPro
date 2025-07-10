"""
Doc #30 간단한 감사 시스템 테스트
SQLAlchemy 세션 문제 해결을 위한 간단한 테스트
"""
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.models.audit import AuditEventType
from app.services.audit.audit_service import AuditService

# 데이터베이스 연결 설정
DATABASE_URL = "sqlite+aiosqlite:///./dev.db"
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine)


async def test_simple_audit():
    """간단한 감사 시스템 테스트"""
    print("=== Doc #30 간단한 감사 시스템 테스트 ===\n")
    
    async with async_session() as db:
        # 서비스 초기화
        audit_service = AuditService(db)
        
        # 1. 감사 로그 테스트
        print("1. 감사 로그 생성 테스트...")
        audit_log = await audit_service.log_event(
            event_type=AuditEventType.TRANSACTION_CREATED,
            entity_type="transaction",
            entity_id="test_tx_simple",
            event_data={
                "amount": "1000.0",
                "currency": "USDT",
                "test": "simple"
            },
            user_id=1,
            severity="info",
            event_category="transaction"
        )
        
        if audit_log:
            print(f"✅ 감사 로그 생성 성공: ID {audit_log.id}")
            print(f"   - 이벤트 타입: {audit_log.event_type}")
            print(f"   - 엔티티: {audit_log.entity_type}:{audit_log.entity_id}")
            print(f"   - 타임스탬프: {audit_log.timestamp}")
        else:
            print("❌ 감사 로그 생성 실패")
        
        # 2. 통계 조회 테스트
        print("\n2. 통계 조회 테스트...")
        audit_stats = await audit_service.get_audit_statistics()
        print(f"✅ 감사 통계:")
        print(f"   - 총 로그 수: {audit_stats.get('total_logs', 0)}")
        print(f"   - 이벤트 타입별 통계: {audit_stats.get('by_event_type', {})}")
        
        print("\n=== 간단한 테스트 완료 ===")


if __name__ == "__main__":
    asyncio.run(test_simple_audit())
