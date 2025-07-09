#!/usr/bin/env python3
"""
현재 데이터베이스 테이블 상태 확인
"""
import sqlite3
import sys
import os

db_path = "dev.db"

if not os.path.exists(db_path):
    print(f"❌ 데이터베이스 파일이 없습니다: {db_path}")
    sys.exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 모든 테이블 목록 조회
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"📋 현재 데이터베이스 테이블 목록 ({len(tables)}개):")
    for table in sorted(tables):
        print(f"   - {table[0]}")
    
    # alembic_version 테이블 확인
    if ('alembic_version',) in tables:
        cursor.execute("SELECT version_num FROM alembic_version;")
        version = cursor.fetchone()
        if version:
            print(f"\n🔄 현재 alembic 버전: {version[0]}")
        else:
            print("\n⚠️  alembic_version 테이블은 있지만 버전 정보가 없습니다")
    else:
        print("\n⚠️  alembic_version 테이블이 없습니다")
    
    conn.close()
    
except Exception as e:
    print(f"❌ 데이터베이스 조회 실패: {e}")
