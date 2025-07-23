#!/usr/bin/env python3
"""
파트너사 온보딩 자동화 시스템 테스트 스크립트
Doc #29 구현 검증용
"""
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.partner_onboarding import OnboardingStatus, OnboardingStepStatus
from app.services.onboarding.simple_onboarding_service import SimpleOnboardingService


def safe_int(value) -> int:
    """Safely extract integer value from SQLAlchemy column"""
    if hasattr(value, "__class__") and hasattr(value.__class__, "__name__"):
        if "Column" in value.__class__.__name__:
            return int(value)
    return value


def safe_str(value) -> str:
    """Safely extract string value from SQLAlchemy column"""
    if hasattr(value, "__class__") and hasattr(value.__class__, "__name__"):
        if "Column" in value.__class__.__name__:
            return str(value)
    return value


async def test_onboarding_system():
    """온보딩 시스템 기본 테스트"""
    print("=== 파트너사 온보딩 자동화 시스템 테스트 ===")

    # 데이터베이스 세션 생성
    async for db in get_db():
        service = SimpleOnboardingService(db)

        try:
            # 1. 온보딩 생성 테스트
            print("\n1. 온보딩 생성 테스트...")
            import random

            test_partner_id = f"TEST_PARTNER_{random.randint(1000, 9999)}"
            configuration_data = {
                "company_name": "테스트 파트너사",
                "contact_email": "test@partner.com",
                "business_type": "암호화폐 거래소",
                "auto_proceed": True,
                "notification_email": "admin@partner.com",
                "main_wallet_address": "TTestWalletAddress123456789",
                "brand_color": "#FF5722",
                "logo_url": "https://example.com/logo.png",
            }

            onboarding = await service.create_onboarding(
                test_partner_id, configuration_data
            )
            onboarding_id = safe_int(onboarding.id)
            print(f"✅ 온보딩 생성 성공: ID {onboarding_id}")

            # 2. 상태 조회 테스트
            print("\n2. 온보딩 상태 조회 테스트...")
            status = await service.get_onboarding_status(test_partner_id)
            if status:
                print(f"✅ 상태 조회 성공: {safe_str(status.status)}")
                print(f"   진행률: {safe_int(status.progress_percentage)}%")
                print(
                    f"   현재 단계: {safe_int(status.current_step)}/{safe_int(status.total_steps)}"
                )
            else:
                print("❌ 상태 조회 실패")
                return

            # 3. 단계별 진행 테스트
            print("\n3. 단계별 진행 테스트...")
            steps = await service.get_onboarding_steps(onboarding_id)
            print(f"✅ 총 {len(steps)}개 단계 생성됨")

            # 첫 번째 단계 완료
            if steps:
                first_step = steps[0]
                success = await service.update_step_status(
                    onboarding_id,
                    safe_int(first_step.step_number),
                    OnboardingStepStatus.COMPLETED,
                    {"test_result": "성공"},
                    None,
                )
                if success:
                    print(f"✅ 1단계 완료 처리 성공")
                else:
                    print("❌ 1단계 완료 처리 실패")

            # 4. 체크리스트 테스트
            print("\n4. 체크리스트 테스트...")
            checklist = await service.get_onboarding_checklist(onboarding_id)
            print(f"✅ 총 {len(checklist)}개 체크리스트 항목 생성됨")

            if checklist:
                # 첫 번째 항목 완료
                first_item = checklist[0]
                success = await service.update_checklist_item(
                    onboarding_id,
                    safe_str(first_item.item_name),
                    True,
                    "테스트 관리자",
                    "테스트 완료",
                )
                if success:
                    print(f"✅ 체크리스트 항목 완료 처리 성공")
                else:
                    print("❌ 체크리스트 항목 완료 처리 실패")

            # 5. 로그 테스트
            print("\n5. 로그 테스트...")
            await service.add_onboarding_log(
                onboarding_id,
                "INFO",
                "테스트 로그 메시지",
                {"test": True, "timestamp": "2025-07-11"},
            )

            logs = await service.get_onboarding_logs(onboarding_id)
            print(f"✅ 총 {len(logs)}개 로그 기록됨")

            # 6. 진행률 업데이트 테스트
            print("\n6. 진행률 업데이트 테스트...")
            success = await service.update_onboarding_progress(
                onboarding_id,
                2,  # current_step
                25,  # progress_percentage
                None,  # status
            )
            if success:
                print("✅ 진행률 업데이트 성공")
            else:
                print("❌ 진행률 업데이트 실패")

            # 최종 상태 확인
            print("\n=== 최종 상태 확인 ===")
            final_status = await service.get_onboarding_status(test_partner_id)
            if final_status:
                print(f"파트너 ID: {final_status.partner_id}")
                print(f"상태: {final_status.status}")
                print(f"진행률: {final_status.progress_percentage}%")
                print(
                    f"현재 단계: {final_status.current_step}/{final_status.total_steps}"
                )
                print(f"생성일: {final_status.created_at}")
                print(f"마지막 업데이트: {final_status.updated_at}")

            print("\n✅ 모든 테스트 완료!")

        except Exception as e:
            print(f"\n❌ 테스트 중 오류 발생: {str(e)}")
            import traceback

            traceback.print_exc()

        break


if __name__ == "__main__":
    asyncio.run(test_onboarding_system())
