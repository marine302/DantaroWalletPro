#!/usr/bin/env python3
"""
체계적인 테스트 데이터 생성 메인 스크립트
"""
import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from test_data.generators.user_generator import UserDataGenerator
from test_data.generators.base_generator import BaseDataGenerator


class ComprehensiveDataGenerator:
    """포괄적인 테스트 데이터 생성기"""
    
    def __init__(self):
        self.generators = {
            'users': UserDataGenerator(),
        }
        
    async def generate_all_data(self):
        """모든 테스트 데이터 생성"""
        print("🚀 체계적인 테스트 데이터 생성 시작...")
        print("=" * 50)
        
        # 데이터베이스 초기화
        for generator in self.generators.values():
            await generator.initialize_db()
            
        try:
            # 1. 파트너 데이터 생성 (사용자보다 먼저)
            print("\n📋 1단계: 파트너 데이터 생성")
            user_gen = self.generators['users']
            partners = await user_gen.generate_partners()
            await user_gen.save_partners_to_db(partners)
            
            # 2. 사용자 데이터 생성
            print("\n👥 2단계: 사용자 데이터 생성")
            users = await user_gen.generate_users()
            await user_gen.save_users_to_db(users)
            
            # 3. 요약 정보 출력
            print("\n📊 생성된 데이터 요약:")
            print("-" * 30)
            print(f"• 파트너: {len(partners)}개")
            print(f"• 사용자: {len(users)}명")
            
            print("\n✅ 모든 테스트 데이터 생성 완료!")
            
        except Exception as e:
            print(f"\n❌ 데이터 생성 중 오류 발생: {e}")
            raise
            
        finally:
            # 데이터베이스 연결 정리
            for generator in self.generators.values():
                await generator.close_db()
                
    async def clean_existing_data(self):
        """기존 테스트 데이터 정리 (선택적)"""
        print("🧹 기존 테스트 데이터 정리...")
        # TODO: 필요시 기존 데이터 삭제 로직 구현


async def main():
    """메인 실행 함수"""
    generator = ComprehensiveDataGenerator()
    
    # 데이터 생성 실행
    await generator.generate_all_data()
    

if __name__ == "__main__":
    asyncio.run(main())
