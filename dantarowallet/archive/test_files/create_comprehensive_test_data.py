#!/usr/bin/env python3
"""
체계적인 테스트 데이터 생성 - 빠른 실행 스크립트
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from scripts.test_data.main import ComprehensiveDataGenerator


async def main():
    """메인 실행 함수"""
    print("🔥 DantaroWallet 체계적인 테스트 데이터 생성")
    print("=" * 50)
    
    generator = ComprehensiveDataGenerator()
    await generator.generate_all_data()


if __name__ == "__main__":
    asyncio.run(main())
