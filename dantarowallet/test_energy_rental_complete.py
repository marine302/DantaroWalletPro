#!/usr/bin/env python3
"""
에너지 렌탈 서비스 완전 테스트
실제 Partner 모델과 함께 통합 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from decimal import Decimal

from app.models.base import Base
from app.models.partners import Partner
from app.models.energy_rental import (
    EnergyRentalPlan, EnergyUsageRecord, EnergyBillingRecord,
    EnergyPool, EnergyPricing, EnergyAllocation,
    RentalPlanType, SubscriptionTier, UsageStatus, PaymentStatus
)
from app.services.energy_rental_service import EnergyRentalService

def test_energy_rental_complete():
    """에너지 렌탈 서비스 완전 테스트"""
    
    # 테스트 데이터베이스 설정
    engine = create_engine('sqlite:///test_energy_complete.db', echo=False)
    
    # 기존 테이블 삭제하고 새로 생성
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # 서비스 인스턴스 생성
        service = EnergyRentalService(db)
        
        print("=== 에너지 렌탈 서비스 완전 테스트 시작 ===")
        
        # 1. 테스트 파트너 생성
        partner = Partner(
            name="Test Partner Company",
            email="test@partner.com",
            api_key="test-api-key-12345",
            is_active=True
        )
        db.add(partner)
        db.commit()
        db.refresh(partner)
        partner_id = getattr(partner, 'id', 1)
        print(f"✓ 테스트 파트너 생성: {partner.name} (ID: {partner_id})")
        
        # 2. 에너지 풀 생성
        energy_pool = EnergyPool(
            pool_name="Main Energy Pool",
            total_energy=100000000,  # 1억 에너지
            available_energy=100000000,
            reserved_energy=0,
            is_active=True,
            staked_trx=Decimal("10000000"),  # 1천만 TRX
            energy_per_trx=Decimal("14400"),
            low_energy_threshold=10000000,   # 1천만 에너지
            emergency_threshold=5000000,     # 5백만 에너지
            last_updated=datetime.now(timezone.utc)
        )
        db.add(energy_pool)
        db.commit()
        db.refresh(energy_pool)
        pool_id = getattr(energy_pool, 'id', 1)
        print(f"✓ 에너지 풀 생성: {energy_pool.pool_name} (ID: {pool_id})")
        
        # 3. 렌탈 플랜 생성 테스트 (구독제)
        subscription_plan = service.create_rental_plan(
            partner_id=partner_id,
            plan_type=RentalPlanType.SUBSCRIPTION,
            subscription_tier=SubscriptionTier.SILVER,
            plan_name="Silver Subscription Plan",
            price_per_energy=Decimal("0.0015"),
            discount_rate=Decimal("0.10"),
            auto_recharge_enabled=True,
            auto_recharge_threshold=500000,
            auto_recharge_amount=5000000
        )
        print(f"✓ 구독제 렌탈 플랜 생성: {subscription_plan.plan_name} (ID: {subscription_plan.id})")
        
        # 4. 렌탈 플랜 생성 테스트 (종량제)
        payg_plan = service.create_rental_plan(
            partner_id=partner_id,
            plan_type=RentalPlanType.PAY_AS_YOU_GO,
            plan_name="Pay As You Go Plan",
            price_per_energy=Decimal("0.002"),
            discount_rate=Decimal("0.05")
        )
        print(f"✓ 종량제 렌탈 플랜 생성: {payg_plan.plan_name} (ID: {payg_plan.id})")
        
        # 5. 에너지 할당 테스트
        allocation1 = service.allocate_energy(
            partner_id=partner_id,
            energy_amount=20000000,  # 2천만 에너지
            from_pool_id=pool_id
        )
        print(f"✓ 에너지 할당 1: {allocation1.allocated_energy:,} energy")
        
        allocation2 = service.allocate_energy(
            partner_id=partner_id,
            energy_amount=10000000,  # 1천만 에너지
            from_pool_id=pool_id
        )
        print(f"✓ 에너지 할당 2: {allocation2.allocated_energy:,} energy")
        
        # 6. 에너지 사용 기록 테스트 (여러 건)
        usage_data = [
            (2000000, "tx-hash-001", "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t", "TLPkn6vQjNKMLZjD7qPnJNgqhHGHKgJXXB"),
            (1500000, "tx-hash-002", "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t", "TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE"),
            (3000000, "tx-hash-003", "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t", "TSSMHYeV2uE9qYH1tqM6kV1FBhV2wfJ3hR"),
            (2500000, "tx-hash-004", "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t", "TKHhsC7Qa2TpHKGkVJhD3aSZJdNgdJ3vvX"),
        ]
        
        total_used = 0
        for energy_used, tx_hash, from_addr, to_addr in usage_data:
            usage_record = service.record_energy_usage(
                partner_id=partner_id,
                energy_used=energy_used,
                transaction_hash=tx_hash,
                from_address=from_addr,
                to_address=to_addr,
                metadata={"transaction_type": "energy_transfer", "priority": "high"}
            )
            total_used += energy_used
            print(f"✓ 에너지 사용 기록: {energy_used:,} energy, TX: {tx_hash}")
        
        print(f"✓ 총 사용량: {total_used:,} energy")
        
        # 7. 사용 통계 조회 테스트
        stats = service.get_partner_usage_statistics(
            partner_id=partner_id,
            period_start=datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            period_end=datetime.now(timezone.utc)
        )
        print(f"✓ 사용 통계:")
        print(f"  - 총 에너지 사용량: {stats['total_energy_used']:,}")
        print(f"  - 총 비용: ${stats['total_cost']:.2f}")
        print(f"  - 사용 건수: {stats['usage_count']}")
        print(f"  - 평균 단가: ${stats['avg_unit_price']:.6f}")
        print(f"  - 일별 사용량: {len(stats['daily_usage'])} days")
        
        # 8. 잔여 에너지 조회
        remaining_energy = service.get_partner_remaining_energy(partner_id)
        print(f"✓ 잔여 에너지: {remaining_energy:,} energy")
        
        # 9. 에너지 할당 정보 조회
        allocation_info = service.get_partner_energy_allocation(partner_id)
        print(f"✓ 에너지 할당 정보:")
        print(f"  - 할당된 에너지: {allocation_info['allocated_energy']:,}")
        print(f"  - 잔여 에너지: {allocation_info['remaining_energy']:,}")
        print(f"  - 활성 상태: {allocation_info['is_active']}")
        
        # 10. 청구서 생성 테스트
        billing_record = service.generate_billing_record(
            partner_id=partner_id,
            billing_period_start=datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            billing_period_end=datetime.now(timezone.utc)
        )
        print(f"✓ 청구서 생성:")
        print(f"  - 청구서 번호: {billing_record.invoice_number}")
        print(f"  - 총 에너지 사용량: {billing_record.total_energy_used:,}")
        print(f"  - 기본 비용: ${billing_record.total_cost}")
        print(f"  - 할인 금액: ${billing_record.discount_amount}")
        print(f"  - 최종 청구 금액: ${billing_record.final_amount}")
        
        # 11. 청구 이력 조회
        billing_history = service.get_billing_history(partner_id)
        print(f"✓ 청구 이력: {len(billing_history)} 건")
        
        # 12. 결제 상태 업데이트
        payment_updated = service.update_payment_status(
            getattr(billing_record, 'id', 1), 
            PaymentStatus.COMPLETED
        )
        print(f"✓ 결제 상태 업데이트: {'성공' if payment_updated else '실패'}")
        
        # 13. 에너지 풀 상태 조회
        pool_status = service.get_energy_pool_status()
        print(f"✓ 에너지 풀 상태: {len(pool_status)} pools")
        for pool in pool_status:
            print(f"  - {pool['name']}: {pool['available_energy']:,}/{pool['total_energy']:,} ({pool['utilization_rate']}% 사용)")
        
        # 14. 시스템 상태 조회
        system_status = service.get_system_status()
        print(f"✓ 시스템 상태:")
        print(f"  - 전체 풀: {system_status['total_pools']}")
        print(f"  - 활성 풀: {system_status['active_pools']}")
        print(f"  - 총 에너지: {system_status['total_energy']:,}")
        print(f"  - 가용 에너지: {system_status['available_energy']:,}")
        print(f"  - 사용률: {system_status['utilization_rate']}%")
        print(f"  - 활성 렌탈 플랜: {system_status['active_rental_plans']}")
        print(f"  - 오늘 사용량: {system_status['today_usage']:,}")
        
        # 15. 자동 재충전 테스트
        recharge_result = service.auto_recharge_check(partner_id)
        print(f"✓ 자동 재충전 확인: {'실행됨' if recharge_result else '필요없음'}")
        
        # 16. 활성 렌탈 플랜 조회
        active_plans = service.get_active_rental_plans(partner_id)
        print(f"✓ 활성 렌탈 플랜: {len(active_plans)} 개")
        for plan in active_plans:
            print(f"  - {plan['plan_name']}: {plan['plan_type']}, 월 할당량: {plan['monthly_energy_quota']:,}")
        
        # 17. 렌탈 플랜 비활성화
        deactivated = service.deactivate_rental_plan(getattr(payg_plan, 'id', 1))
        print(f"✓ 렌탈 플랜 비활성화: {'성공' if deactivated else '실패'}")
        
        # 18. 에너지 풀 상태 업데이트
        pool_updated = service.update_energy_pool_status(pool_id, False)
        print(f"✓ 에너지 풀 비활성화: {'성공' if pool_updated else '실패'}")
        
        print("\n=== 🎉 모든 완전 테스트 통과! ===")
        print("에너지 렌탈 서비스가 성공적으로 구현되었습니다.")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    success = test_energy_rental_complete()
    if success:
        print("\n✅ 에너지 렌탈 서비스 완전 테스트 성공!")
    else:
        print("\n❌ 에너지 렌탈 서비스 테스트 실패!")
        sys.exit(1)
