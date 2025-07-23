"""
EnergyTRON 공급업체 데이터 초기화 스크립트
"""

import os
import sqlite3
import sys
from datetime import datetime, timedelta
from decimal import Decimal


def init_energytron_data():
    """EnergyTRON 공급업체 데이터 초기화"""

    # SQLite 데이터베이스 연결
    db_path = "dev.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. EnergyTRON 공급업체가 이미 있는지 확인
        cursor.execute("SELECT * FROM energy_providers WHERE name = 'EnergyTRON'")
        existing_provider = cursor.fetchone()

        if existing_provider:
            print("EnergyTRON 공급업체가 이미 존재합니다.")
        else:
            # 2. EnergyTRON 공급업체 생성
            cursor.execute(
                """
                INSERT INTO energy_providers (
                    id, name, api_endpoint, api_key_encrypted, status, reliability_score, response_time_avg,
                    min_order_size, max_order_size, trading_fee, withdrawal_fee,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    "energytron",
                    "EnergyTRON",
                    "https://api.energytron.io/v1",
                    "encrypted_api_key_placeholder",  # 실제 사용시 암호화된 키 필요
                    "ONLINE",
                    0.94,  # 94% 신뢰성
                    1.8,  # 1.8초 평균 응답시간
                    500,
                    5000000,
                    0.015,  # 1.5% 거래 수수료
                    0.01,  # 1% 출금 수수료
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                ),
            )
            print("✅ EnergyTRON 공급업체 생성 완료")

        # 3. 기존 가격 데이터 삭제
        cursor.execute("DELETE FROM energy_prices WHERE provider_id = 'energytron'")

        # 4. EnergyTRON 가격 데이터 추가
        price_tiers = [
            ("0.00012", 50000),
            ("0.00011", 100000),
            ("0.000105", 250000),
            ("0.0001", 500000),
            ("0.000095", 1000000),
            ("0.00009", 2000000),
            ("0.000085", 5000000),
        ]

        for price, available in price_tiers:
            cursor.execute(
                """
                INSERT INTO energy_prices (
                    provider_id, price, available_energy, timestamp
                ) VALUES (?, ?, ?, ?)
            """,
                ("energytron", price, available, datetime.now().isoformat()),
            )

        conn.commit()
        print("✅ EnergyTRON 가격 데이터 추가 완료")

        # 5. 추가된 데이터 확인
        cursor.execute("SELECT * FROM energy_providers WHERE id = 'energytron'")
        provider = cursor.fetchone()

        cursor.execute("SELECT * FROM energy_prices WHERE provider_id = 'energytron'")
        prices = cursor.fetchall()

        print(f"\n📊 EnergyTRON 가격 정보:")
        print(f"공급업체 ID: {provider[0]}")
        print(f"공급업체 이름: {provider[1]}")
        print(f"API 엔드포인트: {provider[2]}")
        print(f"상태: {provider[4]}")
        print(f"신뢰성: {provider[5]}")
        print(f"평균 응답시간: {provider[6]}초")
        print(f"최소 주문: {provider[7]:,} 에너지")
        print(f"최대 주문: {provider[8]:,} 에너지")
        print(f"거래 수수료: {provider[9]}%")
        print(f"출금 수수료: {provider[10]}%")

        print(f"\n💰 가격 정보 ({len(prices)}개):")
        for price in prices:
            print(f"  {price[2]} TRX/단위 (가용: {price[4]:,} 에너지)")

        print(f"\n🎉 EnergyTRON 초기화 완료!")
        print(f"   - B2B/B2C 하이브리드 모델")
        print(f"   - 파트너십 프로그램 지원")
        print(f"   - 화이트라벨 솔루션 제공")
        print(f"   - 커스텀 API 개발 지원")

    except Exception as e:
        conn.rollback()
        print(f"❌ 오류 발생: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("🚀 EnergyTRON 공급업체 데이터 초기화 시작...")
    init_energytron_data()
