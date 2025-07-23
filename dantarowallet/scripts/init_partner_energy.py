"""
파트너 에너지 렌탈 시스템 데이터베이스 초기화 스크립트

기본 마진 설정 및 테스트 데이터를 생성합니다.
"""

import os
import sys
from datetime import datetime, timezone

from sqlalchemy.orm import Session

# 현재 디렉토리를 파이썬 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models.partner_energy_allocation import (
    AllocationStatus,
    BillingCycle,
    EnergyMarginConfig,
    PartnerEnergyAllocation,
    PartnerTier,
)


def init_energy_margin_config(db: Session):
    """기본 마진 설정 초기화"""

    print("🔧 에너지 마진 설정 초기화 중...")

    # 기본 마진 설정
    margin_configs = [
        {
            "partner_tier": PartnerTier.STARTUP,
            "default_margin_percentage": 35.0,
            "min_margin_percentage": 25.0,
            "max_margin_percentage": 50.0,
            "volume_threshold_1": 500000,  # 50만 에너지
            "volume_margin_1": 5.0,  # 5% 할인
            "volume_threshold_2": 2000000,  # 200만 에너지
            "volume_margin_2": 10.0,  # 10% 할인
        },
        {
            "partner_tier": PartnerTier.BUSINESS,
            "default_margin_percentage": 25.0,
            "min_margin_percentage": 15.0,
            "max_margin_percentage": 35.0,
            "volume_threshold_1": 1000000,  # 100만 에너지
            "volume_margin_1": 3.0,  # 3% 할인
            "volume_threshold_2": 5000000,  # 500만 에너지
            "volume_margin_2": 7.0,  # 7% 할인
        },
        {
            "partner_tier": PartnerTier.ENTERPRISE,
            "default_margin_percentage": 15.0,
            "min_margin_percentage": 8.0,
            "max_margin_percentage": 25.0,
            "volume_threshold_1": 10000000,  # 1000만 에너지
            "volume_margin_1": 2.0,  # 2% 할인
            "volume_threshold_2": 50000000,  # 5000만 에너지
            "volume_margin_2": 5.0,  # 5% 할인
        },
    ]

    for config_data in margin_configs:
        # 기존 설정 확인
        existing = (
            db.query(EnergyMarginConfig)
            .filter(
                EnergyMarginConfig.partner_tier == config_data["partner_tier"],
                EnergyMarginConfig.is_active == True,
            )
            .first()
        )

        if not existing:
            config = EnergyMarginConfig(
                partner_tier=config_data["partner_tier"],
                default_margin_percentage=config_data["default_margin_percentage"],
                min_margin_percentage=config_data["min_margin_percentage"],
                max_margin_percentage=config_data["max_margin_percentage"],
                volume_threshold_1=config_data["volume_threshold_1"],
                volume_margin_1=config_data["volume_margin_1"],
                volume_threshold_2=config_data["volume_threshold_2"],
                volume_margin_2=config_data["volume_margin_2"],
                created_by="system_init",
            )
            db.add(config)
            print(
                f"  ✅ {config_data['partner_tier'].value} 등급 마진 설정 생성: {config_data['default_margin_percentage']}%"
            )
        else:
            print(
                f"  ⚠️  {config_data['partner_tier'].value} 등급 마진 설정이 이미 존재함"
            )

    db.commit()
    print("✅ 마진 설정 초기화 완료")


def create_test_allocations(db: Session):
    """테스트용 파트너 에너지 할당 생성"""

    print("\n🧪 테스트 에너지 할당 생성 중...")

    # 테스트 할당 데이터
    test_allocations = [
        {
            "partner_id": "partner_001",
            "partner_name": "테스트 스타트업",
            "partner_tier": PartnerTier.STARTUP,
            "allocated_amount": 1000000,  # 100만 에너지
            "purchase_price": 0.00001,  # 0.00001 TRX/Energy
            "markup_percentage": 35.0,  # 35% 마진
        },
        {
            "partner_id": "partner_002",
            "partner_name": "테스트 중소기업",
            "partner_tier": PartnerTier.BUSINESS,
            "allocated_amount": 5000000,  # 500만 에너지
            "purchase_price": 0.00001,  # 0.00001 TRX/Energy
            "markup_percentage": 25.0,  # 25% 마진
        },
        {
            "partner_id": "partner_003",
            "partner_name": "테스트 대기업",
            "partner_tier": PartnerTier.ENTERPRISE,
            "allocated_amount": 20000000,  # 2000만 에너지
            "purchase_price": 0.00001,  # 0.00001 TRX/Energy
            "markup_percentage": 15.0,  # 15% 마진
        },
    ]

    for allocation_data in test_allocations:
        # 기존 할당 확인
        existing = (
            db.query(PartnerEnergyAllocation)
            .filter(
                PartnerEnergyAllocation.partner_id == allocation_data["partner_id"],
                PartnerEnergyAllocation.status == AllocationStatus.ACTIVE,
            )
            .first()
        )

        if not existing:
            rental_price = allocation_data["purchase_price"] * (
                1 + allocation_data["markup_percentage"] / 100
            )

            allocation = PartnerEnergyAllocation(
                partner_id=allocation_data["partner_id"],
                partner_name=allocation_data["partner_name"],
                partner_tier=allocation_data["partner_tier"],
                allocated_amount=allocation_data["allocated_amount"],
                remaining_amount=allocation_data["allocated_amount"],
                purchase_price=allocation_data["purchase_price"],
                markup_percentage=allocation_data["markup_percentage"],
                rental_price=rental_price,
                billing_cycle=BillingCycle.MONTHLY,
                created_by="system_init",
            )
            db.add(allocation)
            print(
                f"  ✅ {allocation_data['partner_name']} 할당 생성: {allocation_data['allocated_amount']:,} Energy"
            )
        else:
            print(f"  ⚠️  {allocation_data['partner_name']} 할당이 이미 존재함")

    db.commit()
    print("✅ 테스트 할당 생성 완료")


def main():
    """메인 초기화 함수"""
    print("🚀 파트너 에너지 렌탈 시스템 초기화 시작")
    print("=" * 50)

    # 데이터베이스 연결
    db = SessionLocal()

    try:
        # 1. 마진 설정 초기화
        init_energy_margin_config(db)

        # 2. 테스트 할당 생성
        create_test_allocations(db)

        print("\n" + "=" * 50)
        print("🎉 파트너 에너지 렌탈 시스템 초기화 완료!")
        print("\n📊 생성된 데이터:")

        # 생성된 데이터 확인
        margin_configs = (
            db.query(EnergyMarginConfig)
            .filter(EnergyMarginConfig.is_active == True)
            .all()
        )
        allocations = (
            db.query(PartnerEnergyAllocation)
            .filter(PartnerEnergyAllocation.status == AllocationStatus.ACTIVE)
            .all()
        )

        print(f"  • 마진 설정: {len(margin_configs)}개")
        print(f"  • 활성 할당: {len(allocations)}개")

        print("\n🌐 API 엔드포인트:")
        print("  • POST /api/v1/partners/{partner_id}/energy/allocate")
        print("  • GET  /api/v1/partners/{partner_id}/energy/allocations")
        print("  • POST /api/v1/partners/{partner_id}/energy/usage")
        print("  • GET  /api/v1/admin/energy/revenue-analytics")
        print("  • GET  /api/v1/admin/energy/margin-config")

    except Exception as e:
        print(f"❌ 초기화 중 오류 발생: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
