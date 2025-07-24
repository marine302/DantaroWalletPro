#!/usr/bin/env python3
"""
외부 에너지 가격 히스토리 데이터 생성 스크립트
"""
import random
import sqlite3
import sys
from datetime import datetime, timedelta
from decimal import Decimal


def create_price_history():
    """가격 히스토리 데이터 생성"""
    conn = sqlite3.connect("dev.db")
    cursor = conn.cursor()

    print("=== 외부 에너지 가격 히스토리 생성 ===")

    # 공급자 조회
    cursor.execute("SELECT id, provider_type, name FROM external_energy_providers")
    providers = cursor.fetchall()

    print(f"공급자 수: {len(providers)}")

    # 각 공급자별로 가격 히스토리 생성
    for provider_id, provider_type, name in providers:
        print(f"\n{name} ({provider_type}) 가격 히스토리 생성 중...")

        # 기본 가격 설정 (공급자별로 다르게)
        base_prices = {"JUSTLEND": 0.00028, "TRONNRG": 0.00032, "TRONSCAN": 0.00035}

        base_price = base_prices.get(provider_type, 0.0003)

        # 지난 30일간의 가격 데이터 생성
        for i in range(30):
            recorded_at = datetime.utcnow() - timedelta(days=i)

            # 가격 변동 (±20% 범위)
            variation = random.uniform(0.8, 1.2)
            price = base_price * variation

            # 가용량 (10만 ~ 100만)
            available_amount = random.randint(100000, 1000000)

            cursor.execute(
                """
                INSERT INTO external_energy_price_history 
                (provider_id, price_per_energy, available_amount, recorded_at)
                VALUES (?, ?, ?, ?)
            """,
                (provider_id, price, available_amount, recorded_at),
            )

        print(f"  - 30개 가격 기록 생성 완료")

    # 최신 가격으로 공급자 테이블 업데이트
    print("\n=== 공급자 테이블 최신 가격 업데이트 ===")
    for provider_id, provider_type, name in providers:
        # 최신 가격 조회
        cursor.execute(
            """
            SELECT price_per_energy, recorded_at 
            FROM external_energy_price_history 
            WHERE provider_id = ? 
            ORDER BY recorded_at DESC 
            LIMIT 1
        """,
            (provider_id,),
        )

        result = cursor.fetchone()
        if result:
            latest_price, recorded_at = result
            cursor.execute(
                """
                UPDATE external_energy_providers 
                SET last_price = ?, price_updated_at = ? 
                WHERE id = ?
            """,
                (latest_price, recorded_at, provider_id),
            )
            print(f"  - {name}: {latest_price} (업데이트: {recorded_at})")

    conn.commit()
    print(f"\n✅ 가격 히스토리 데이터 생성 완료!")

    # 결과 확인
    cursor.execute("SELECT COUNT(*) FROM external_energy_price_history")
    total_count = cursor.fetchone()[0]
    print(f"총 가격 기록 수: {total_count}")

    conn.close()


if __name__ == "__main__":
    create_price_history()
