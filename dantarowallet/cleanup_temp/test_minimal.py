#!/usr/bin/env python3
"""
최소한의 DB 연결 테스트
"""
import asyncio
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("1. 시작")

from app.core.database import get_db

print("2. DB import 완료")

async def minimal_test():
    print("3. async 함수 시작")
    
    try:
        print("4. DB 연결 시도...")
        async for db in get_db():
            print("5. DB 연결 성공!")
            break
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()
    
    print("6. 테스트 완료")

if __name__ == "__main__":
    print("7. asyncio.run 시작")
    asyncio.run(minimal_test())
    print("8. 전체 완료")
