#!/usr/bin/env python3
"""
DantaroWallet 데이터베이스 구조 분석기
현재 시스템의 모든 테이블, 컬럼, 관계를 분석하여 ERD와 스키마 문서를 생성합니다.
"""
import sqlite3
import json
from datetime import datetime
import os

def analyze_database():
    """데이터베이스 구조를 분석합니다."""
    
    db_path = 'dev.db'
    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return None
    
    print("🔍 DantaroWallet 데이터베이스 구조 분석")
    print("=" * 60)
    print(f"분석 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"데이터베이스: {db_path}")
    print()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 모든 테이블 조회
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 총 {len(tables)}개 테이블 발견")
        print("-" * 40)
        
        db_schema = {
            "database_name": "DantaroWallet",
            "analyzed_at": datetime.now().isoformat(),
            "total_tables": len(tables),
            "tables": {}
        }
        
        # 2. 각 테이블의 구조 분석
        for table_name in tables:
            print(f"\n🔸 테이블: {table_name}")
            
            # 테이블 스키마 조회
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            # 외래키 조회
            cursor.execute(f"PRAGMA foreign_key_list({table_name});")
            foreign_keys = cursor.fetchall()
            
            # 인덱스 조회
            cursor.execute(f"PRAGMA index_list({table_name});")
            indexes = cursor.fetchall()
            
            table_info = {
                "name": table_name,
                "columns": [],
                "foreign_keys": [],
                "indexes": [],
                "row_count": 0
            }
            
            # 컬럼 정보 처리
            for col in columns:
                col_info = {
                    "name": col[1],
                    "type": col[2],
                    "not_null": bool(col[3]),
                    "default_value": col[4],
                    "primary_key": bool(col[5])
                }
                table_info["columns"].append(col_info)
                print(f"  📋 {col[1]}: {col[2]} {'PK' if col[5] else ''} {'NOT NULL' if col[3] else ''}")
            
            # 외래키 정보 처리
            for fk in foreign_keys:
                fk_info = {
                    "column": fk[3],
                    "referenced_table": fk[2],
                    "referenced_column": fk[4]
                }
                table_info["foreign_keys"].append(fk_info)
                print(f"  🔗 FK: {fk[3]} -> {fk[2]}.{fk[4]}")
            
            # 인덱스 정보 처리
            for idx in indexes:
                table_info["indexes"].append({
                    "name": idx[1],
                    "unique": bool(idx[2])
                })
            
            # 행 개수 조회
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                table_info["row_count"] = cursor.fetchone()[0]
                print(f"  📊 행 개수: {table_info['row_count']}")
            except:
                print(f"  📊 행 개수: 조회 불가")
            
            db_schema["tables"][table_name] = table_info
        
        conn.close()
        return db_schema
        
    except Exception as e:
        print(f"❌ 데이터베이스 분석 중 오류 발생: {e}")
        return None

def generate_schema_document(schema):
    """스키마 정보를 바탕으로 문서를 생성합니다."""
    
    if not schema:
        return
    
    doc_content = f"""# DantaroWallet 데이터베이스 스키마 문서

## 📊 기본 정보
- **데이터베이스명**: {schema['database_name']}
- **분석 일시**: {schema['analyzed_at']}
- **총 테이블 수**: {schema['total_tables']}

## 📋 테이블 목록

"""
    
    # 테이블별 상세 정보
    for table_name, table_info in schema["tables"].items():
        doc_content += f"""### {table_name}
- **행 개수**: {table_info['row_count']}
- **컬럼 수**: {len(table_info['columns'])}

#### 컬럼 구조
| 컬럼명 | 타입 | PK | Not Null | 기본값 |
|--------|------|----| ---------|--------|
"""
        
        for col in table_info["columns"]:
            pk = "✅" if col["primary_key"] else ""
            not_null = "✅" if col["not_null"] else ""
            default = col["default_value"] if col["default_value"] else ""
            doc_content += f"| {col['name']} | {col['type']} | {pk} | {not_null} | {default} |\n"
        
        # 외래키 정보
        if table_info["foreign_keys"]:
            doc_content += "\n#### 외래키\n"
            for fk in table_info["foreign_keys"]:
                doc_content += f"- `{fk['column']}` → `{fk['referenced_table']}.{fk['referenced_column']}`\n"
        
        # 인덱스 정보
        if table_info["indexes"]:
            doc_content += "\n#### 인덱스\n"
            for idx in table_info["indexes"]:
                unique = "UNIQUE" if idx["unique"] else ""
                doc_content += f"- `{idx['name']}` {unique}\n"
        
        doc_content += "\n---\n\n"
    
    # 파일 저장
    with open("DATABASE_SCHEMA.md", "w", encoding="utf-8") as f:
        f.write(doc_content)
    
    # JSON 파일로도 저장
    with open("database_schema.json", "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    
    print("\n✅ 스키마 문서 생성 완료:")
    print("📄 DATABASE_SCHEMA.md - 마크다운 문서")
    print("📄 database_schema.json - JSON 스키마 파일")

if __name__ == "__main__":
    schema = analyze_database()
    if schema:
        generate_schema_document(schema)
    else:
        print("❌ 스키마 분석 실패")
