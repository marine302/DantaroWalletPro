"""
테스트용 온보딩 API 호출 스크립트
Doc #29: 파트너사 온보딩 자동화 테스트
"""

import asyncio
import json
from datetime import datetime

from app.core.database import get_db
from app.models.partner_onboarding import OnboardingStatus, OnboardingStepStatus
from app.services.onboarding.simple_onboarding_service import SimpleOnboardingService


def safe_int(value) -> int:
    """Safely extract integer value from SQLAlchemy column or return actual value."""
    if hasattr(value, "__class__") and hasattr(value.__class__, "__name__"):
        if "Column" in value.__class__.__name__:
            return int(value)
    return value


async def test_onboarding_service():
    """온보딩 서비스 기본 기능 테스트"""
    print("🚀 Doc #29 온보딩 자동화 시스템 테스트 시작")
    print("=" * 60)

    # 데이터베이스 세션 생성
    async for db in get_db():
        service = SimpleOnboardingService(db)

        # 테스트 파트너 ID
        test_partner_id = "TEST_PARTNER_001"

        try:
            # 1. 온보딩 생성
            print("\n1️⃣ 온보딩 프로세스 생성")
            config_data = {
                "company_name": "테스트 파트너사",
                "contact_email": "test@partner.com",
                "business_type": "crypto_exchange",
                "auto_proceed": True,
                "notification_email": "admin@partner.com",
                "main_wallet_address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
            }

            onboarding = await service.create_onboarding(test_partner_id, config_data)
            print(f"✅ 온보딩 생성 완료 - ID: {onboarding.id}")

            # 2. 온보딩 상태 조회
            print("\n2️⃣ 온보딩 상태 조회")
            status = await service.get_onboarding_status(test_partner_id)
            if status:
                print(f"✅ 상태: {status.status}")
                print(f"   진행률: {status.progress_percentage}%")
                print(f"   현재 단계: {status.current_step}/{status.total_steps}")

            # 3. 단계별 진행
            print("\n3️⃣ 단계별 진행 시뮬레이션")
            steps = ["등록", "계정 설정", "지갑 설정", "시스템 구성", "배포", "테스트"]

            for i, step_name in enumerate(steps, 1):
                print(f"   단계 {i}: {step_name} 시작...")

                # 단계 상태 업데이트
                success = await service.update_step_status(
                    safe_int(onboarding.id),
                    i,
                    OnboardingStepStatus.COMPLETED,
                    {"step_result": f"{step_name} 완료"},
                    None,
                )

                if success:
                    print(f"   ✅ 단계 {i} 완료")
                else:
                    print(f"   ❌ 단계 {i} 실패")

            # 4. 최종 상태 확인
            print("\n4️⃣ 최종 상태 확인")
            final_status = await service.get_onboarding_status(test_partner_id)
            if final_status:
                print(f"✅ 최종 상태: {final_status.status}")
                print(f"   최종 진행률: {final_status.progress_percentage}%")

            # 5. 로그 확인
            print("\n5️⃣ 온보딩 로그 확인")
            logs = await service.get_onboarding_logs(safe_int(onboarding.id))
            print(f"✅ 총 {len(logs)}개의 로그 기록")

            if logs:
                latest_log = logs[-1]
                print(f"   최신 로그: {latest_log.message}")

            print("\n" + "=" * 60)
            print("🎉 Doc #29 온보딩 자동화 시스템 테스트 완료!")

        except Exception as e:
            print(f"❌ 테스트 실패: {str(e)}")
            import traceback

            traceback.print_exc()

        break  # 첫 번째 세션만 사용


if __name__ == "__main__":
    print("Doc #29: 파트너사 온보딩 자동화 시스템")
    print(f"테스트 시작 시간: {datetime.now()}")

    # 비동기 테스트 실행
    asyncio.run(test_onboarding_service())
