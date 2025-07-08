#!/usr/bin/env python3
"""
메인 시스템을 통한 새 마스터 지갑 및 사용자 주소 생성
FastAPI Sweep API를 사용하여 진행
"""
import asyncio
import httpx
import json
import sys
from typing import List, Dict

# API 기본 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1/sweep"

class SweepSystemManager:
    def __init__(self):
        self.base_url = BASE_URL
        self.api_prefix = API_PREFIX
        self.partner_id = "test_partner_001"
        
    async def create_master_wallet(self) -> Dict:
        """새 마스터 지갑 생성"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{self.api_prefix}/wallets/master",
                json={"partner_id": self.partner_id}
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"마스터 지갑 생성 실패: {response.text}")
    
    async def get_master_wallet(self) -> Dict:
        """마스터 지갑 조회"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{self.api_prefix}/wallets/master",
                params={"partner_id": self.partner_id}
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"마스터 지갑 조회 실패: {response.text}")
    
    async def create_user_addresses(self, count: int = 10) -> List[Dict]:
        """사용자 입금 주소들 생성"""
        addresses = []
        async with httpx.AsyncClient() as client:
            for i in range(count):
                user_id = f"user_{1000 + i}"
                response = await client.post(
                    f"{self.base_url}{self.api_prefix}/addresses",
                    json={
                        "partner_id": self.partner_id,
                        "user_id": user_id,
                        "min_sweep_amount": "1.0"
                    }
                )
                if response.status_code == 200:
                    address_data = response.json()
                    addresses.append(address_data)
                    print(f"✅ {i+1}번 주소 생성: {address_data['address']} (사용자: {user_id})")
                else:
                    print(f"❌ {i+1}번 주소 생성 실패: {response.text}")
        
        return addresses
    
    async def get_user_addresses(self) -> List[Dict]:
        """사용자 주소 목록 조회"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{self.api_prefix}/addresses",
                params={"partner_id": self.partner_id}
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"주소 목록 조회 실패: {response.text}")

async def main():
    print("🚀 메인 시스템을 통한 새 마스터 지갑 및 사용자 주소 설정")
    print("=" * 60)
    
    manager = SweepSystemManager()
    
    try:
        # 1. 기존 마스터 지갑 확인
        print("\n1️⃣ 기존 마스터 지갑 확인...")
        try:
            existing_master = await manager.get_master_wallet()
            print(f"기존 마스터 지갑 발견: ID {existing_master.get('id')}")
            print("⚠️ 새 마스터 지갑을 생성하면 기존 지갑은 사용되지 않습니다.")
        except:
            print("기존 마스터 지갑 없음")
        
        # 2. 새 마스터 지갑 생성
        print("\n2️⃣ 새 마스터 지갑 생성...")
        master_wallet = await manager.create_master_wallet()
        print(f"✅ 마스터 지갑 생성 완료!")
        print(f"   - ID: {master_wallet['id']}")
        print(f"   - 파트너: {master_wallet['partner_id']}")
        print(f"   - 파생 경로: {master_wallet['derivation_path']}")
        
        # 3. 사용자 주소 10개 생성
        print("\n3️⃣ 사용자 입금 주소 10개 생성...")
        user_addresses = await manager.create_user_addresses(10)
        print(f"✅ 총 {len(user_addresses)}개 주소 생성 완료!")
        
        # 4. 생성된 주소 목록 출력
        print("\n4️⃣ 생성된 주소 목록:")
        for i, addr in enumerate(user_addresses):
            print(f"   {i+1:2d}. {addr['address']} (사용자: {addr['user_id']})")
        
        # 5. 마스터 수집 주소 안내
        print("\n5️⃣ 마스터 수집 주소 확인:")
        print("   메인 시스템에서 마스터 수집 주소를 조회해야 합니다.")
        print("   또는 HDWalletService에서 index 0으로 생성된 주소입니다.")
        
        print("\n🎉 설정 완료!")
        print("다음 단계:")
        print("1. 마스터 수집 주소에 200 TRX 전송")
        print("2. 각 사용자 주소에 20 TRX씩 분산 전송")
        print("3. Sweep 테스트 실행")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
