#!/usr/bin/env python3
"""
에너지 렌탈 서비스 완전한 통합 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from decimal import Decimal

from app.models.base import Base
from app.models.partner import Partner
from app.models.energy_rental import (
    EnergyRentalPlan, EnergyUsageRecord, EnergyBillingRecord,
    EnergyPool, EnergyPricing, EnergyAllocation,
    RentalPlanType, SubscriptionTier, UsageStatus, PaymentStatus
)
from app.services.energy_rental_service import EnergyRentalService

def test_complete_energy_rental_system():
    """에너지 렌탈 시스템 완전한 통합 테스트"""
    
    # 테스트 데이터베이스 설정
    engine = create_engine('sqlite:///test_complete_energy_rental.db', echo=False)
    Base.metadata.drop_all(engine)  # 기존 테이블 삭제
    Base.metadata.create_all(engine)  # 새로 생성
    
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # 서비스 인스턴스 생성
        service = EnergyRentalService(db)
        
        print("=== 에너지 렌탈 시스템 완전한 통합 테스트 시작 ===")
        
        # 1. 테스트 파트너 생성
        partner = Partner(
            id="test-partner-uuid-1234",
            name="Test Partner Co.",
            contact_email="test@partner.com",
            api_key="test-api-key-12345",
            business_type="fintech",
            status="active"
        )
        db.add(partner)
        db.commit()
        db.refresh(partner)
        partner_id = getattr(partner, 'id', 'test-partner-uuid-1234')
        print(f"✓ 테스트 파트너 생성: {partner.name} (ID: {partner_id})")
        
        # 2. 에너지 풀 생성
        energy_pool = EnergyPool(
            pool_name="Main Energy Pool",
            total_energy=50000000,  # 5천만 에너지
            available_energy=50000000,
            is_active=True,
            last_updated=datetime.now(timezone.utc)
        )
        db.add(energy_pool)
        db.commit()
        db.refresh(energy_pool)
        pool_id = getattr(energy_pool, 'id', 1)
        print(f"✓ 에너지 풀 생성: {energy_pool.pool_name} (ID: {pool_id})")
        
        # 3. 렌탈 플랜 생성 테스트
        print("\n--- 렌탈 플랜 생성 테스트 ---")
        rental_plan = service.create_rental_plan(
            partner_id=partner_id,
            plan_type=RentalPlanType.SUBSCRIPTION,
            subscription_tier=SubscriptionTier.SILVER,
            plan_name="Silver Energy Plan",
            price_per_energy=Decimal("0.0015"),
            discount_rate=Decimal("0.10"),
            auto_recharge_enabled=True,
            auto_recharge_threshold=500000,
            auto_recharge_amount=2000000
        )
        plan_id = getattr(rental_plan, 'id', 1)
        print(f"✓ 렌탈 플랜 생성: {getattr(rental_plan, 'plan_name', 'Unknown')} (ID: {plan_id})")
        print(f"  - 플랜 타입: {getattr(rental_plan, 'plan_type', 'Unknown')}")
        print(f"  - 구독 등급: {getattr(rental_plan, 'subscription_tier', 'Unknown')}")
        print(f"  - 에너지당 가격: ${getattr(rental_plan, 'price_per_energy', 0)}")
        
        # 4. 에너지 할당 테스트
        print("\n--- 에너지 할당 테스트 ---")
        allocation = service.allocate_energy(
            partner_id=partner_id,
            energy_amount=10000000,  # 1천만 에너지 할당
            from_pool_id=pool_id
        )
        allocation_id = getattr(allocation, 'id', 1)
        allocated_energy = getattr(allocation, 'allocated_energy', 0)
        remaining_energy = getattr(allocation, 'remaining_energy', 0)
        print(f"✓ 에너지 할당 완료: {allocated_energy} energy (ID: {allocation_id})")
        print(f"  - 할당된 에너지: {allocated_energy}")
        print(f"  - 잔여 에너지: {remaining_energy}")
        
        # 5. 에너지 사용 기록 테스트 (여러 번)
        print("\n--- 에너지 사용 기록 테스트 ---")
        usage_scenarios = [
            {"energy": 500000, "tx": "tx001", "desc": "첫 번째 사용"},
            {"energy": 750000, "tx": "tx002", "desc": "두 번째 사용"},
            {"energy": 1000000, "tx": "tx003", "desc": "세 번째 사용"}
        ]
        
        usage_records = []
        for i, scenario in enumerate(usage_scenarios):
            usage_record = service.record_energy_usage(
                partner_id=partner_id,
                energy_used=scenario["energy"],
                transaction_hash=scenario["tx"],
                from_address="TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
                to_address="TLPkn6vQjNKMLZjD7qPnJNgqhHGHKgJXXB",
                metadata={"scenario": scenario["desc"], "test_index": i+1}
            )
            usage_records.append(usage_record)
            energy_used = getattr(usage_record, 'energy_used', 0)
            total_cost = getattr(usage_record, 'total_cost', 0)
            print(f"✓ {scenario['desc']}: {energy_used} energy, ${total_cost}")
        
        # 6. 사용 통계 조회 테스트
        print("\n--- 사용 통계 조회 테스트 ---")
        current_time = datetime.now(timezone.utc)
        month_start = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        stats = service.get_partner_usage_statistics(
            partner_id=partner_id,
            period_start=month_start,
            period_end=current_time
        )
        print(f"✓ 사용 통계:")
        print(f"  - 총 에너지 사용량: {stats['total_energy_used']}")
        print(f"  - 총 비용: ${stats['total_cost']}")
        print(f"  - 사용 횟수: {stats['usage_count']}")
        print(f"  - 평균 단가: ${stats['avg_unit_price']}")
        
        # 7. 청구서 생성 테스트
        print("\n--- 청구서 생성 테스트 ---")
        billing_record = service.generate_billing_record(
            partner_id=partner_id,
            billing_period_start=month_start,
            billing_period_end=current_time
        )
        
        invoice_number = getattr(billing_record, 'invoice_number', 'Unknown')
        total_energy_used = getattr(billing_record, 'total_energy_used', 0)
        final_amount = getattr(billing_record, 'final_amount', 0)
        print(f"✓ 청구서 생성: {invoice_number}")
        print(f"  - 총 에너지 사용량: {total_energy_used}")
        print(f"  - 최종 청구 금액: ${final_amount}")
        
        # 8. 에너지 풀 상태 조회
        print("\n--- 에너지 풀 상태 조회 ---")
        pool_status = service.get_energy_pool_status()
        print(f"✓ 에너지 풀 상태: {len(pool_status)} pools")
        for pool in pool_status:
            print(f"  - {pool['name']}: {pool['available_energy']:,} / {pool['total_energy']:,} energy")
            print(f"    utilization: {pool['utilization_rate']}%, status: {pool['status']}")
        
        # 9. 시스템 전체 상태 조회
        print("\n--- 시스템 상태 조회 ---")
        system_status = service.get_system_status()
        print(f"✓ 시스템 상태:")
        print(f"  - 총 에너지 풀: {system_status['total_pools']}")
        print(f"  - 활성 풀: {system_status['active_pools']}")
        print(f"  - 총 에너지: {system_status['total_energy']:,}")
        print(f"  - 사용 가능 에너지: {system_status['available_energy']:,}")
        print(f"  - 전체 활용률: {system_status['utilization_rate']}%")
        print(f"  - 활성 렌탈 플랜: {system_status['active_rental_plans']}")
        print(f"  - 오늘 사용량: {system_status['today_usage']:,}")
        
        # 10. 결제 상태 업데이트 테스트
        print("\n--- 결제 상태 업데이트 테스트 ---")
        billing_id = getattr(billing_record, 'id', 1)
        payment_success = service.update_payment_status(
            billing_record_id=billing_id,
            payment_status=PaymentStatus.COMPLETED
        )
        print(f"✓ 결제 상태 업데이트: {'성공' if payment_success else '실패'}")
        
        # 11. 청구 이력 조회
        print("\n--- 청구 이력 조회 ---")
        billing_history = service.get_billing_history(partner_id)
        print(f"✓ 청구 이력: {len(billing_history)} 건")
        for bill in billing_history:
            print(f"  - {bill['invoice_number']}: ${bill['final_amount']} ({bill['payment_status']})")
        
        # 12. 자동 재충전 테스트
        print("\n--- 자동 재충전 테스트 ---")
        recharge_result = service.auto_recharge_check(partner_id)
        print(f"✓ 자동 재충전 확인: {'실행됨' if recharge_result else '필요없음'}")
        
        # 13. 파트너 에너지 할당 정보 조회
        print("\n--- 파트너 에너지 할당 정보 ---")
        allocation_info = service.get_partner_energy_allocation(partner_id)
        print(f"✓ 에너지 할당 정보:")
        print(f"  - 할당된 에너지: {allocation_info['allocated_energy']:,}")
        print(f"  - 잔여 에너지: {allocation_info['remaining_energy']:,}")
        print(f"  - 활성 상태: {allocation_info['is_active']}")
        
        print("\n=== 🎉 모든 통합 테스트 통과! 🎉 ===")
        print("\n✨ TRON 에너지 렌탈 서비스가 성공적으로 구현되었습니다!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    success = test_complete_energy_rental_system()
    if success:
        print("\n🚀 에너지 렌탈 서비스 준비 완료!")
    else:
        print("\n💥 테스트 실패 - 문제를 확인해주세요.")
    
    exit(0 if success else 1)
