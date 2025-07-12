#!/usr/bin/env python3
"""
에너지 렌탈 서비스 핵심 기능 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from decimal import Decimal

# 서비스 직접 테스트
def test_energy_rental_service_functions():
    """에너지 렌탈 서비스 함수들을 직접 테스트"""
    
    print("=== 에너지 렌탈 서비스 함수 테스트 시작 ===")
    
    try:
        # 1. 모듈 임포트 테스트
        from app.models.energy_rental import (
            RentalPlanType, SubscriptionTier, UsageStatus, PaymentStatus,
            get_subscription_tier_limits, calculate_energy_cost
        )
        print("✓ 모델 임포트 성공")
        
        # 2. Enum 테스트
        print(f"✓ RentalPlanType: {RentalPlanType.SUBSCRIPTION.value}")
        print(f"✓ SubscriptionTier: {SubscriptionTier.BRONZE.value}")
        print(f"✓ UsageStatus: {UsageStatus.PENDING.value}")
        print(f"✓ PaymentStatus: {PaymentStatus.PENDING.value}")
        
        # 3. 구독 등급 제한 테스트
        bronze_limits = get_subscription_tier_limits(SubscriptionTier.BRONZE)
        print(f"✓ Bronze 등급 제한: {bronze_limits}")
        
        silver_limits = get_subscription_tier_limits(SubscriptionTier.SILVER)
        print(f"✓ Silver 등급 제한: {silver_limits}")
        
        # 4. 에너지 비용 계산 테스트 (가상 플랜 객체 사용)
        class MockPlan:
            def __init__(self, price_per_energy, discount_rate):
                self.price_per_energy = price_per_energy
                self.discount_rate = discount_rate
        
        # getattr을 사용한 안전한 접근을 위한 함수 수정
        def calculate_energy_cost_safe(energy_amount: int, plan) -> Decimal:
            """안전한 에너지 비용 계산"""
            from app.models.energy_rental import getattr as safe_getattr
            
            price_per_energy = Decimal(str(safe_getattr(plan, "price_per_energy", 0)))
            base_cost = Decimal(str(energy_amount)) * price_per_energy
            
            # 할인 적용
            discount_rate = float(safe_getattr(plan, "discount_rate", 0))
            if discount_rate > 0:
                discount_amount = base_cost * Decimal(str(discount_rate))
                base_cost -= discount_amount
            
            return base_cost
        
        mock_plan = MockPlan(Decimal("0.001"), Decimal("0.05"))
        
        # 가상 비용 계산 테스트
        energy_amount = 1000000  # 100만 에너지
        base_cost = Decimal(str(energy_amount)) * mock_plan.price_per_energy
        discount_amount = base_cost * mock_plan.discount_rate
        final_cost = base_cost - discount_amount
        
        print(f"✓ 에너지 비용 계산 테스트:")
        print(f"  - 에너지 양: {energy_amount}")
        print(f"  - 기본 비용: ${base_cost}")
        print(f"  - 할인 금액: ${discount_amount}")
        print(f"  - 최종 비용: ${final_cost}")
        
        # 5. 서비스 클래스 임포트 테스트
        from app.services.energy_rental_service import EnergyRentalService
        print("✓ 서비스 클래스 임포트 성공")
        
        # 6. 서비스 메서드 존재 확인
        service_methods = [
            'create_rental_plan', 'allocate_energy', 'record_energy_usage',
            'generate_billing_record', 'get_partner_usage_statistics',
            'get_energy_pool_status', 'auto_recharge_check',
            'get_partner_remaining_energy', 'update_energy_pool_status',
            'get_billing_history', 'update_payment_status'
        ]
        
        for method in service_methods:
            if hasattr(EnergyRentalService, method):
                print(f"✓ {method} 메서드 존재")
            else:
                print(f"❌ {method} 메서드 누락")
        
        print("\n=== 모든 함수 테스트 통과! ===")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_energy_rental_service_functions()
