#!/usr/bin/env python3
"""
DantaroWallet Pro 데이터베이스 구조 분석 도구
현재 시스템의 모든 테이블과 관계를 분석하여 문서화합니다.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

def analyze_database():
    """데이터베이스 구조를 분석합니다."""
    
    db_path = "dev.db"
    if not Path(db_path).exists():
        print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return None
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    analysis = {
        "analysis_date": datetime.now().isoformat(),
        "database_file": db_path,
        "tables": {},
        "relationships": [],
        "indexes": {},
        "statistics": {}
    }
    
    try:
        # 1. 모든 테이블 목록 조회
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        table_names = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 총 {len(table_names)}개의 테이블 발견")
        
        # 2. 각 테이블의 상세 정보 분석
        for table_name in table_names:
            print(f"🔍 분석 중: {table_name}")
            
            # 테이블 스키마 정보
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # 외래키 정보
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = cursor.fetchall()
            
            # 인덱스 정보
            cursor.execute(f"PRAGMA index_list({table_name})")
            indexes = cursor.fetchall()
            
            # 행 개수
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            analysis["tables"][table_name] = {
                "columns": [
                    {
                        "id": col[0],
                        "name": col[1],
                        "type": col[2],
                        "not_null": bool(col[3]),
                        "default_value": col[4],
                        "primary_key": bool(col[5])
                    }
                    for col in columns
                ],
                "foreign_keys": [
                    {
                        "id": fk[0],
                        "seq": fk[1],
                        "table": fk[2],
                        "from_column": fk[3],
                        "to_column": fk[4],
                        "on_update": fk[5],
                        "on_delete": fk[6],
                        "match": fk[7]
                    }
                    for fk in foreign_keys
                ],
                "indexes": [
                    {
                        "seq": idx[0],
                        "name": idx[1],
                        "unique": bool(idx[2]),
                        "origin": idx[3],
                        "partial": bool(idx[4])
                    }
                    for idx in indexes
                ],
                "row_count": row_count
            }
            
            # 관계 정보 수집
            for fk in foreign_keys:
                analysis["relationships"].append({
                    "from_table": table_name,
                    "from_column": fk[3],
                    "to_table": fk[2],
                    "to_column": fk[4],
                    "relationship_type": "many_to_one"
                })
        
        # 3. 통계 정보
        analysis["statistics"] = {
            "total_tables": len(table_names),
            "total_relationships": len(analysis["relationships"]),
            "tables_by_module": classify_tables_by_module(table_names),
            "total_rows": sum(table["row_count"] for table in analysis["tables"].values())
        }
        
        print(f"✅ 분석 완료: {len(table_names)}개 테이블, {len(analysis['relationships'])}개 관계")
        
    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {e}")
        return None
    finally:
        conn.close()
    
    return analysis

def classify_tables_by_module(table_names):
    """테이블을 모듈별로 분류합니다."""
    modules = {
        "core": [],
        "user_auth": [],
        "partner": [],
        "wallet": [],
        "transaction": [],
        "deposit": [],
        "withdrawal": [],
        "energy": [],
        "fee_policy": [],
        "analytics": [],
        "monitoring": [],
        "system": [],
        "other": []
    }
    
    for table in table_names:
        if table in ["users", "user_sessions"]:
            modules["user_auth"].append(table)
        elif table.startswith("partner"):
            modules["partner"].append(table)
        elif table in ["wallets", "wallet_transactions", "balance"]:
            modules["wallet"].append(table)
        elif table in ["transactions", "transaction_logs"]:
            modules["transaction"].append(table)
        elif table.startswith("deposit"):
            modules["deposit"].append(table)
        elif table.startswith("withdrawal"):
            modules["withdrawal"].append(table)
        elif table.startswith("energy") or "energy" in table:
            modules["energy"].append(table)
        elif "fee" in table or "policy" in table:
            modules["fee_policy"].append(table)
        elif "analytics" in table or "stats" in table:
            modules["analytics"].append(table)
        elif "monitoring" in table or "alert" in table or "log" in table:
            modules["monitoring"].append(table)
        elif table.startswith("alembic"):
            modules["system"].append(table)
        else:
            modules["other"].append(table)
    
    return {k: v for k, v in modules.items() if v}

def generate_erd_markdown(analysis):
    """ERD 마크다운 문서를 생성합니다."""
    
    md_content = f"""# DantaroWallet Pro - 데이터베이스 ERD

> 생성일: {analysis['analysis_date']}  
> 데이터베이스: {analysis['database_file']}

## 📊 데이터베이스 개요

- **총 테이블 수**: {analysis['statistics']['total_tables']}개
- **총 관계 수**: {analysis['statistics']['total_relationships']}개
- **총 데이터 행**: {analysis['statistics']['total_rows']:,}개

## 🏗️ 모듈별 테이블 구조

"""
    
    for module, tables in analysis['statistics']['tables_by_module'].items():
        md_content += f"### {module.replace('_', ' ').title()} 모듈\n\n"
        for table in tables:
            table_info = analysis['tables'][table]
            md_content += f"#### {table}\n"
            md_content += f"- **행 수**: {table_info['row_count']:,}개\n"
            md_content += f"- **컬럼 수**: {len(table_info['columns'])}개\n"
            
            if table_info['foreign_keys']:
                md_content += f"- **외래키**: {len(table_info['foreign_keys'])}개\n"
            
            md_content += "\n**컬럼 구조**:\n\n"
            md_content += "| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |\n"
            md_content += "|--------|------|----------|--------|----|\\n"
            
            for col in table_info['columns']:
                null_allowed = "❌" if col['not_null'] else "✅"
                is_pk = "🔑" if col['primary_key'] else ""
                default_val = col['default_value'] or "-"
                md_content += f"| {col['name']} | {col['type']} | {null_allowed} | {default_val} | {is_pk} |\n"
            
            md_content += "\n"
    
    # 관계 다이어그램
    md_content += "## 🔗 테이블 관계\n\n"
    md_content += "```mermaid\nerDiagram\n"
    
    # 테이블 정의
    for table_name, table_info in analysis['tables'].items():
        md_content += f"    {table_name} {{\n"
        for col in table_info['columns'][:5]:  # 처음 5개 컬럼만 표시
            col_type = col['type'].replace('(', '_').replace(')', '').replace(',', '_')
            md_content += f"        {col_type} {col['name']}\n"
        if len(table_info['columns']) > 5:
            md_content += f"        string etc\n"
        md_content += "    }\n"
    
    # 관계 정의
    for rel in analysis['relationships']:
        md_content += f"    {rel['from_table']} ||--o{{ {rel['to_table']} : {rel['from_column']}\n"
    
    md_content += "```\n\n"
    
    # 상세 관계 목록
    md_content += "### 관계 상세\n\n"
    md_content += "| From Table | From Column | To Table | To Column | Type |\n"
    md_content += "|------------|-------------|----------|-----------|------|\n"
    
    for rel in analysis['relationships']:
        md_content += f"| {rel['from_table']} | {rel['from_column']} | {rel['to_table']} | {rel['to_column']} | {rel['relationship_type']} |\n"
    
    return md_content

def generate_sql_schema(analysis):
    """SQL DDL 스키마를 생성합니다."""
    
    sql_content = f"""-- DantaroWallet Pro Database Schema
-- Generated: {analysis['analysis_date']}
-- Database: {analysis['database_file']}

"""
    
    for table_name, table_info in analysis['tables'].items():
        sql_content += f"-- Table: {table_name}\n"
        sql_content += f"-- Rows: {table_info['row_count']:,}\n"
        sql_content += f"CREATE TABLE {table_name} (\n"
        
        columns = []
        for col in table_info['columns']:
            col_def = f"    {col['name']} {col['type']}"
            if col['not_null']:
                col_def += " NOT NULL"
            if col['default_value']:
                col_def += f" DEFAULT {col['default_value']}"
            if col['primary_key']:
                col_def += " PRIMARY KEY"
            columns.append(col_def)
        
        sql_content += ",\n".join(columns)
        
        # 외래키 제약조건
        if table_info['foreign_keys']:
            sql_content += ",\n"
            fk_constraints = []
            for fk in table_info['foreign_keys']:
                fk_def = f"    FOREIGN KEY ({fk['from_column']}) REFERENCES {fk['table']}({fk['to_column']})"
                if fk['on_delete'] != 'NO ACTION':
                    fk_def += f" ON DELETE {fk['on_delete']}"
                if fk['on_update'] != 'NO ACTION':
                    fk_def += f" ON UPDATE {fk['on_update']}"
                fk_constraints.append(fk_def)
            sql_content += ",\n".join(fk_constraints)
        
        sql_content += "\n);\n\n"
        
        # 인덱스
        for idx in table_info['indexes']:
            if idx['origin'] == 'c':  # Created index (not auto-generated)
                unique_clause = "UNIQUE " if idx['unique'] else ""
                sql_content += f"CREATE {unique_clause}INDEX {idx['name']} ON {table_name};\n"
        
        sql_content += "\n"
    
    return sql_content

def main():
    """메인 실행 함수"""
    print("🔍 DantaroWallet Pro 데이터베이스 구조 분석 시작")
    print("=" * 60)
    
    # 데이터베이스 분석
    analysis = analyze_database()
    if not analysis:
        print("❌ 데이터베이스 분석 실패")
        return
    
    # 결과 저장
    output_dir = Path("database_schema")
    output_dir.mkdir(exist_ok=True)
    
    # 1. JSON 분석 결과
    json_path = output_dir / "database_analysis.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"📄 JSON 분석 결과 저장: {json_path}")
    
    # 2. ERD 마크다운
    erd_content = generate_erd_markdown(analysis)
    erd_path = output_dir / "database_erd.md"
    with open(erd_path, 'w', encoding='utf-8') as f:
        f.write(erd_content)
    print(f"📋 ERD 마크다운 저장: {erd_path}")
    
    # 3. SQL 스키마
    sql_content = generate_sql_schema(analysis)
    sql_path = output_dir / "database_schema.sql"
    with open(sql_path, 'w', encoding='utf-8') as f:
        f.write(sql_content)
    print(f"🗃️ SQL 스키마 저장: {sql_path}")
    
    print("\n✅ 데이터베이스 구조 분석 완료!")
    print(f"📁 결과 파일들이 {output_dir} 디렉토리에 저장되었습니다.")
    
    # 요약 정보 출력
    print("\n📊 분석 요약:")
    print(f"   • 총 테이블: {analysis['statistics']['total_tables']}개")
    print(f"   • 총 관계: {analysis['statistics']['total_relationships']}개")
    print(f"   • 총 데이터: {analysis['statistics']['total_rows']:,}행")
    print(f"   • 모듈 수: {len(analysis['statistics']['tables_by_module'])}개")

if __name__ == "__main__":
    main()
