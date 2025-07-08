#!/usr/bin/env python3
"""
hd_wallet_masters 테이블 스키마 확인
"""
import sqlite3

try:
    conn = sqlite3.connect("dev.db")
    cursor = conn.cursor()
    
    # 테이블 스키마 확인
    cursor.execute("PRAGMA table_info(hd_wallet_masters);")
    columns = cursor.fetchall()
    
    print("📋 hd_wallet_masters 테이블 컬럼:")
    for col in columns:
        cid, name, type_, notnull, default, pk = col
        print(f"   {name}: {type_} (NOT NULL: {bool(notnull)}, DEFAULT: {default}, PK: {bool(pk)})")
    
    # collection_address 컬럼이 있는지 확인
    collection_address_exists = any(col[1] == 'collection_address' for col in columns)
    
    if collection_address_exists:
        print("\n✅ collection_address 컬럼이 이미 존재합니다!")
        
        # 기존 데이터 확인
        cursor.execute("SELECT id, collection_address FROM hd_wallet_masters;")
        rows = cursor.fetchall()
        
        print(f"\n📊 기존 데이터 ({len(rows)}개):")
        for row in rows:
            print(f"   ID: {row[0]}, collection_address: {row[1]}")
    else:
        print("\n❌ collection_address 컬럼이 없습니다")
    
    conn.close()
    
except Exception as e:
    print(f"❌ 오류: {e}")
