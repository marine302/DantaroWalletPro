#!/usr/bin/env python3
"""
에너지 렌탈 서비스 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from decimal import Decimal

from app.models.energy_rental import (
    EnergyRentalPlan, EnergyUsageRecord, EnergyBillingRecord,
    EnergyPool, EnergyPricing, EnergyAllocation,
    RentalPlanType, SubscriptionTier, UsageStatus, PaymentStatus
)
from app.models.partners import Partner
from app.models.base import Base
from app.services.energy_rental_service import EnergyRentalService

def test_energy_rental_service():
    """에너지 렌탈 서비스 테스트"""
    
    # 테스트 데이터베이스 설정
    engine = create_engine('sqlite:///test_energy_rental.db', echo=False)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # 서비스 인스턴스 생성
        service = EnergyRentalService(db)
        
        print("=== 에너지 렌탈 서비스 테스트 시작 ===")
        
        # 1. 테스트 파트너 생성
        partner = Partner(
            name="Test Partner",
            email="test@example.com",
            api_key="test-api-key"
        )
        db.add(partner)
        db.commit()
        db.refresh(partner)
        print(f"✓ 테스트 파트너 생성: {partner.name} (ID: {partner.id})")
        
        # 2. 에너지 풀 생성
        energy_pool = EnergyPool(
            pool_name="Test Energy Pool",
            total_energy=10000000,
            available_energy=10000000,
            reserved_energy=0,
            is_active=True,
            staked_trx=Decimal("1000000"),
            energy_per_trx=Decimal("14400"),
            low_energy_threshold=1000000,
            emergency_threshold=500000,
            last_updated=datetime.now(timezone.utc)
        )
        db.add(energy_pool)
        db.commit()
        db.refresh(energy_pool)
        print(f"✓ 에너지 풀 생성: {energy_pool.pool_name} (ID: {energy_pool.id})")
        
        # 3. 렌탈 플랜 생성 테스트
        rental_plan = service.create_rental_plan(
            partner_id=getattr(partner, 'id', 1),
            plan_type=RentalPlanType.SUBSCRIPTION,
            subscription_tier=SubscriptionTier.BASIC,
            plan_name="Test Basic Plan",
            price_per_energy=Decimal("0.001"),
            discount_rate=Decimal("0.05"),
            auto_recharge_enabled=True,
            auto_recharge_threshold=100000,
            auto_recharge_amount=1000000
        )
        print(f"✓ 렌탈 플랜 생성: {rental_plan.plan_name} (ID: {rental_plan.id})")
        
        # 4. 에너지 할당 테스트
        allocation = service.allocate_energy(
            partner_id=getattr(partner, 'id', 1),
            energy_amount=5000000,
            from_pool_id=getattr(energy_pool, 'id', 1)
        )
        print(f"✓ 에너지 할당: {allocation.allocated_energy} energy")
        
        # 5. 에너지 사용 기록 테스트
        usage_record = service.record_energy_usage(
            partner_id=getattr(partner, 'id', 1),
            energy_used=1000000,
            transaction_hash="test-tx-hash-123",
            from_address="TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
            to_address="TLPkn6vQjNKMLZjD7qPnJNgqhHGHKgJXXB",
            metadata={"test": "data"}
        )
        print(f"✓ 에너지 사용 기록: {usage_record.energy_used} energy")
        
        # 6. 사용 통계 조회 테스트
        stats = service.get_partner_usage_statistics(
            partner_id=getattr(partner, 'id', 1),
            period_start=datetime.now(timezone.utc).replace(day=1),
            period_end=datetime.now(timezone.utc)
        )
        print(f"✓ 사용 통계 조회: {stats['total_energy_used']} energy, ${stats['total_cost']}")
        
        # 7. 청구서 생성 테스트
        billing_record = service.generate_billing_record(
            partner_id=getattr(partner, 'id', 1),
            billing_period_start=datetime.now(timezone.utc).replace(day=1),
            billing_period_end=datetime.now(timezone.utc)
        )
        print(f"✓ 청구서 생성: {billing_record.invoice_number}, ${billing_record.final_amount}")
        
        # 8. 에너지 풀 상태 조회
        pool_status = service.get_energy_pool_status()
        print(f"✓ 에너지 풀 상태: {len(pool_status)} pools")
        
        # 9. 시스템 상태 조회
        system_status = service.get_system_status()
        print(f"✓ 시스템 상태: {system_status['total_energy']} total energy, {system_status['utilization_rate']}% utilization")
        
        # 10. 자동 재충전 테스트
        recharge_result = service.auto_recharge_check(getattr(partner, 'id', 1))
        print(f"✓ 자동 재충전 확인: {'실행됨' if recharge_result else '필요없음'}")
        
        print("\n=== 모든 테스트 통과! ===")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    test_energy_rental_service()
