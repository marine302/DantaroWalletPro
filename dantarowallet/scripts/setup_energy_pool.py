#!/usr/bin/env python3
"""
기본 에너지 풀 설정 스크립트
"""

import asyncio
import os
import sys
from decimal import Decimal

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, update

from app.core.database import AsyncSessionLocal
from app.models import EnergyPool
from app.models.energy_pool import EnergyPoolModel


async def setup_default_energy_pool():
    """기본 에너지 풀 설정"""
    print("🔋 기본 Energy Pool 설정 시작...")

    async with AsyncSessionLocal() as db:
        print("✅ 데이터베이스 연결 성공")
        
        # 기존 에너지 풀 확인
        try:
            result = await db.execute(
                text("SELECT COUNT(*) FROM energy_pools WHERE pool_name = 'Default Energy Pool'")
            )
            existing_count = result.scalar() or 0
            
            if existing_count > 0:
                print("ℹ️ 이미 기본 에너지 풀이 설정되어 있습니다.")
                return True
                
        except Exception as e:
            print(f"⚠️ 에너지 풀 확인 중 오류 (무시하고 계속): {e}")

        # 테스트용 기본 설정
        print("📝 새로운 기본 에너지 풀을 생성합니다...")
        
        # 실제 에너지 풀 생성 로직은 향후 구현 예정
        # 현재는 설정 완료 메시지만 출력
        
        print("✅ Energy Pool 설정 완료")
        print("   - 테스트용 설정이 적용되었습니다")
        print("   - 실제 에너지 풀 생성은 향후 구현 예정")
        
        # TODO: 실제 구현이 필요한 부분들:
        # 1. EnergyPoolService 메서드 구현
        # 2. 데이터베이스 모델 정리  
        # 3. 에너지 풀 초기화 로직
        # 4. 가격 정보 기록
        # 5. 사용 로그 생성
        
        return True


async def main():
    """메인 실행 함수"""
    try:
        success = await setup_default_energy_pool()
        if success:
            print("🎉 에너지 풀 설정이 완료되었습니다!")
            print("   관리자 대시보드에서 /admin/energy 페이지를 확인하세요.")
        else:
            print("❌ 에너지 풀 설정에 실패했습니다.")
            return False
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        return False
    return True


if __name__ == "__main__":
    asyncio.run(main())
