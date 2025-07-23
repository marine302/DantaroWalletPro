#!/usr/bin/env python3
"""실제 테이블 구조에 맞는 간단한 샘플 데이터 생성"""

import json
import random
import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal


def create_simple_sample_data():
    """간단한 샘플 데이터 생성"""

    conn = sqlite3.connect("dev.db")
    cursor = conn.cursor()

    try:
        print("🔄 실제 테이블 구조에 맞는 샘플 데이터 생성 시작...")

        # 1. 파트너 데이터 생성
        partner_id = "test_partner_001"
        cursor.execute("SELECT id FROM partners WHERE id = ?", (partner_id,))
        if not cursor.fetchone():
            cursor.execute(
                """
                INSERT INTO partners (
                    id, name, display_name, contact_email, business_type,
                    api_key, api_secret_hash, status, onboarding_status,
                    commission_rate, monthly_limit, energy_balance,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    partner_id,
                    "DantaroWallet Test Partner",
                    "테스트 파트너",
                    "partner@test.com",
                    "crypto_exchange",
                    "test_api_key_123",
                    "hashed_secret_123",
                    "active",
                    "completed",
                    0.02,
                    30000000.0,
                    1000000.0,
                    datetime.utcnow(),
                    datetime.utcnow(),
                ),
            )
            print("✅ 파트너 생성됨")

        # 2. 사용자 데이터 생성 (50명)
        cursor.execute("DELETE FROM users WHERE email LIKE 'testuser%'")
        user_ids = []
        for i in range(50):
            cursor.execute(
                """
                INSERT INTO users (
                    email, password_hash, is_active, is_admin, is_verified,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    f"testuser{i+1:03d}@test.com",
                    "hashed_password_123",
                    random.choice([True, True, True, False]),  # 75% 활성
                    False,
                    True,
                    datetime.utcnow() - timedelta(days=random.randint(1, 365)),
                    datetime.utcnow(),
                ),
            )
            user_ids.append(cursor.lastrowid)
        print(f"✅ 사용자 생성: {len(user_ids)}개")

        # 3. 지갑 데이터 생성
        cursor.execute("DELETE FROM wallets WHERE address LIKE 'TEST%'")
        wallet_types = ["hot", "warm", "cold"]
        for i, user_id in enumerate(user_ids[:10]):  # 처음 10명만 지갑 생성
            wallet_type = wallet_types[i % 3]
            address = f"TEST{wallet_type.upper()}{random.randint(100000, 999999)}"

            cursor.execute(
                """
                INSERT INTO wallets (
                    user_id, address, hex_address, encrypted_private_key,
                    encryption_salt, is_active, is_monitored,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    address,
                    f"0x{address[4:]}",  # hex 주소
                    f"encrypted_key_{address}",
                    f"salt_{address}",
                    True,
                    True,
                    datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                    datetime.utcnow(),
                ),
            )
        print("✅ 지갑 생성: 10개")

        # 4. 거래 데이터 생성 (최근 30일)
        cursor.execute(
            "DELETE FROM transactions WHERE description LIKE 'Test transaction%'"
        )
        transaction_types = ["deposit", "withdrawal", "transfer"]
        directions = ["in", "out", "internal"]
        statuses = ["completed", "pending", "processing"]

        for i in range(200):  # 200개 거래
            user_id = random.choice(user_ids)
            tx_type = random.choice(transaction_types)
            direction = random.choice(directions)

            cursor.execute(
                """
                INSERT INTO transactions (
                    user_id, type, direction, status, asset, amount, fee,
                    reference_id, description, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    tx_type,
                    direction,
                    random.choice(statuses),
                    "TRX",
                    random.uniform(10, 10000),
                    random.uniform(1, 10),
                    f"ref_{i+1:06d}",
                    f"Test transaction {i+1}",
                    datetime.utcnow()
                    - timedelta(
                        days=random.randint(0, 30), hours=random.randint(0, 23)
                    ),
                    datetime.utcnow(),
                ),
            )
        print("✅ 거래 데이터 생성: 200개")

        # 5. 에너지 풀 데이터 생성
        cursor.execute("DELETE FROM energy_pools WHERE pool_name LIKE 'Test%'")
        pool_data = [
            {
                "pool_name": "Test Main Pool",
                "total_energy": 1000000,
                "available_energy": 750000,
                "used_energy": 250000,
            },
            {
                "pool_name": "Test Reserve Pool",
                "total_energy": 500000,
                "available_energy": 400000,
                "used_energy": 100000,
            },
        ]

        for i, pool in enumerate(pool_data):
            cursor.execute(
                """
                INSERT INTO energy_pools (
                    pool_name, owner_address, frozen_trx, total_energy,
                    available_energy, used_energy, status, low_threshold,
                    critical_threshold, auto_refill, auto_refill_amount,
                    auto_refill_trigger, daily_consumption, peak_usage_hours,
                    created_at, last_checked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    pool["pool_name"],
                    f"TOWNER{i+1:03d}{random.randint(100000, 999999)}",
                    random.uniform(10000, 50000),
                    pool["total_energy"],
                    pool["available_energy"],
                    pool["used_energy"],
                    "active",
                    100000,  # low_threshold
                    50000,  # critical_threshold
                    True,  # auto_refill
                    10000.0,  # auto_refill_amount
                    80000,  # auto_refill_trigger
                    json.dumps({"hourly_avg": 1000}),  # daily_consumption
                    json.dumps(
                        {"peak_hours": [9, 10, 11, 14, 15, 16]}
                    ),  # peak_usage_hours
                    datetime.utcnow() - timedelta(days=random.randint(1, 10)),
                    datetime.utcnow(),
                ),
            )
        print(f"✅ 에너지 풀 생성: {len(pool_data)}개")

        # 6. 잔액 데이터 생성
        cursor.execute(
            "DELETE FROM balances WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'testuser%')"
        )
        # 사용자별 잔액 생성
        for user_id in user_ids:
            cursor.execute(
                """
                INSERT INTO balances (
                    user_id, asset, amount, locked_amount, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    "TRX",
                    random.uniform(1000, 100000),
                    random.uniform(0, 1000),
                    datetime.utcnow(),
                    datetime.utcnow(),
                ),
            )
        print(f"✅ 잔액 데이터 생성: {len(user_ids)}개")

        conn.commit()
        print("\n🎉 샘플 데이터 생성 완료!")
        print(f"📊 생성된 데이터:")
        print(f"   - 파트너: 1개")
        print(f"   - 사용자: 50개")
        print(f"   - 지갑: 10개")
        print(f"   - 거래: 200개")
        print(f"   - 에너지 풀: {len(pool_data)}개")
        print(f"   - 잔액: {len(user_ids)}개")

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    create_simple_sample_data()
