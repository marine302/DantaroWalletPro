#!/usr/bin/env python3
"""
alembic_version 테이블에 올바른 버전 설정
"""
import sqlite3
import sys
import os

db_path = "dev.db"
target_version = "ca0829d8a731"  # 최신 head 버전

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 현재 버전 확인
    cursor.execute("SELECT version_num FROM alembic_version;")
    current = cursor.fetchone()
    
    if current:
        print(f"현재 버전: {current[0]}")
        cursor.execute("UPDATE alembic_version SET version_num = ?;", (target_version,))
        print(f"✅ 버전을 {target_version}으로 업데이트했습니다")
    else:
        cursor.execute("INSERT INTO alembic_version (version_num) VALUES (?);", (target_version,))
        print(f"✅ 새로운 버전 {target_version}을 설정했습니다")
    
    conn.commit()
    conn.close()
    
    print(f"🔄 alembic_version 설정 완료: {target_version}")
    
except Exception as e:
    print(f"❌ 버전 설정 실패: {e}")
    sys.exit(1)
