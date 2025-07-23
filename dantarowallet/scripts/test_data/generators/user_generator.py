#!/usr/bin/env python3
"""
사용자 테스트 데이터 생성기
"""
import random
from typing import List

from app.models.partner import Partner
from app.models.user import User

from .base_generator import BaseDataGenerator, DataValidator


class UserDataGenerator(BaseDataGenerator):
    """사용자 테스트 데이터 생성기"""

    def __init__(self):
        super().__init__()
        self.user_config = None

    async def generate_users(self) -> List[User]:
        """사용자 데이터 생성"""
        self.user_config = self.load_config("user_profiles.yaml")

        users = []
        user_id_counter = 1

        for profile_key, profile in self.user_config["user_profiles"].items():
            self.log_progress(f"{profile['name']} 생성 중...", 0, profile["count"])

            for i in range(profile["count"]):
                user = await self._create_user(profile, user_id_counter)
                users.append(user)
                user_id_counter += 1

                self.log_progress(
                    f"{profile['name']} 생성 중...", i + 1, profile["count"]
                )

        # 데이터 검증
        if DataValidator.validate_user_data(users):
            self.log_progress(f"✅ 사용자 데이터 생성 완료: {len(users)}명")
        else:
            self.log_progress("❌ 사용자 데이터 검증 실패")

        return users

    async def _create_user(self, profile: dict, user_id: int) -> User:
        """개별 사용자 생성"""
        email = f"user{user_id:03d}@test.com"

        # 특별한 사용자들
        if profile.get("activity_level") == "admin":
            if "super_admin" in profile.get("permissions", []):
                email = "admin@dantarowallet.com"
            else:
                email = f"partner_admin{user_id}@test.com"

        user = User(
            email=email,
            password_hash=self._generate_password_hash(),
            is_active=True,
            is_verified=profile.get("verification_status", True),
            created_at=self.random_datetime(profile["registration_days_ago"]),
            updated_at=self.random_datetime([0, 7]),
        )

        # 추가 속성들
        if "last_login_days_ago" in profile:
            user.last_login = self.random_datetime(profile["last_login_days_ago"])

        return user

    def _generate_password_hash(self) -> str:
        """테스트용 패스워드 해시 생성"""
        # 실제로는 bcrypt 등을 사용해야 하지만, 테스트용으로 간단히
        return "$2b$12$test_hashed_password_for_development"

    async def generate_partners(self) -> List[Partner]:
        """파트너 데이터 생성"""
        partners = []

        # 메인 테스트 파트너
        main_partner = Partner(
            id="partner_001",
            name="DantaroWallet Test Partner",
            display_name="테스트 파트너",
            contact_email="partner@test.com",
            contact_phone="010-1234-5678",
            business_type="crypto_exchange",
            status="active",
            onboarding_status="completed",
            commission_rate=0.02,
            api_key="test_api_key_main",
            api_secret_hash="hashed_secret_main",
            monthly_limit=50000000.0,
            energy_balance=2000000.0,
        )
        partners.append(main_partner)

        # 소규모 파트너
        small_partner = Partner(
            id="partner_002",
            name="Small Crypto Service",
            display_name="소규모 서비스",
            contact_email="small@test.com",
            contact_phone="010-2345-6789",
            business_type="wallet_service",
            status="active",
            onboarding_status="completed",
            commission_rate=0.025,
            api_key="test_api_key_small",
            api_secret_hash="hashed_secret_small",
            monthly_limit=10000000.0,
            energy_balance=500000.0,
        )
        partners.append(small_partner)

        # 대기 중인 파트너
        pending_partner = Partner(
            id="partner_003",
            name="Pending Partner Service",
            display_name="승인 대기 파트너",
            contact_email="pending@test.com",
            contact_phone="010-3456-7890",
            business_type="defi_platform",
            status="pending",
            onboarding_status="documents_submitted",
            commission_rate=0.02,
            api_key="temp_api_key_pending",  # 임시 키
            api_secret_hash="temp_hashed_secret_pending",  # 임시 해시
            monthly_limit=0.0,
            energy_balance=0.0,
        )
        partners.append(pending_partner)

        self.log_progress(f"✅ 파트너 데이터 생성 완료: {len(partners)}개")
        return partners

    async def save_users_to_db(self, users: List[User]):
        """사용자 데이터를 데이터베이스에 저장"""
        async with await self.get_session() as db:
            try:
                db.add_all(users)
                await db.commit()
                self.log_progress(f"💾 사용자 {len(users)}명 데이터베이스 저장 완료")
            except Exception as e:
                await db.rollback()
                self.log_progress(f"❌ 사용자 데이터 저장 실패: {e}")
                raise

    async def save_partners_to_db(self, partners: List[Partner]):
        """파트너 데이터를 데이터베이스에 저장"""
        async with await self.get_session() as db:
            try:
                db.add_all(partners)
                await db.commit()
                self.log_progress(f"💾 파트너 {len(partners)}개 데이터베이스 저장 완료")
            except Exception as e:
                await db.rollback()
                self.log_progress(f"❌ 파트너 데이터 저장 실패: {e}")
                raise
