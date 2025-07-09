#!/usr/bin/env python3
import sqlite3
import json
from datetime import datetime

def analyze_database():
    """데이터베이스 스키마를 분석하여 ERD 형태의 문서를 생성합니다."""
    conn = sqlite3.connect('dev.db')
    cursor = conn.cursor()
    
    # 모든 테이블 조회
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = cursor.fetchall()
    
    database_schema = {
        'tables': {},
        'relationships': []
    }
    
    print('=== DantaroWallet Pro 데이터베이스 스키마 분석 ===\n')
    print(f'분석 일시: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'총 테이블 수: {len(tables)}\n')
    
    for table in tables:
        table_name = table[0]
        
        # 테이블 정보
        cursor.execute(f'PRAGMA table_info({table_name});')
        columns = cursor.fetchall()
        
        # 외래 키 정보
        cursor.execute(f'PRAGMA foreign_key_list({table_name});')
        foreign_keys = cursor.fetchall()
        
        # 인덱스 정보
        cursor.execute(f'PRAGMA index_list({table_name});')
        indexes = cursor.fetchall()
        
        table_info = {
            'columns': [],
            'foreign_keys': [],
            'indexes': []
        }
        
        print(f'📋 테이블: {table_name}')
        print('=' * 80)
        
        # 컬럼 정보
        print('📝 컬럼:')
        for col in columns:
            cid, name, type_, notnull, default, pk = col
            col_info = {
                'name': name,
                'type': type_,
                'nullable': not bool(notnull),
                'default': default,
                'primary_key': bool(pk)
            }
            table_info['columns'].append(col_info)
            
            nullable = 'NULL' if not notnull else 'NOT NULL'
            primary = '🔑 (PK)' if pk else ''
            default_val = f'DEFAULT {default}' if default else ''
            print(f'  • {name}: {type_} {nullable} {primary} {default_val}'.strip())
        
        # 외래 키 정보
        if foreign_keys:
            print('\n🔗 외래 키:')
            for fk in foreign_keys:
                id_, seq, table_ref, from_col, to_col, on_update, on_delete, match = fk
                fk_info = {
                    'from_column': from_col,
                    'to_table': table_ref,
                    'to_column': to_col,
                    'on_update': on_update,
                    'on_delete': on_delete
                }
                table_info['foreign_keys'].append(fk_info)
                print(f'  • {from_col} ➔ {table_ref}.{to_col} (UPDATE: {on_update}, DELETE: {on_delete})')
                
                # 관계 정보 저장
                database_schema['relationships'].append({
                    'from_table': table_name,
                    'from_column': from_col,
                    'to_table': table_ref,
                    'to_column': to_col
                })
        
        # 인덱스 정보
        if indexes:
            print('\n📊 인덱스:')
            for idx in indexes:
                seq, name, unique, origin, partial = idx
                unique_str = '🔒 UNIQUE' if unique else '📇 INDEX'
                print(f'  • {name} ({unique_str})')
        
        database_schema['tables'][table_name] = table_info
        print('\n')
    
    conn.close()
    
    # 관계 요약
    print('🔄 관계 요약')
    print('=' * 80)
    for rel in database_schema['relationships']:
        print(f'{rel["from_table"]}.{rel["from_column"]} ➔ {rel["to_table"]}.{rel["to_column"]}')
    
    # 도메인별 테이블 분류
    print('\n📂 도메인별 테이블 분류')
    print('=' * 80)
    
    domains = {
        '👤 사용자 관리': [],
        '💰 지갑 관리': [],
        '💸 거래': [],
        '⚡ 에너지 풀': [],
        '🤝 파트너사': [],
        '📊 분석/로그': [],
        '🔧 시스템': []
    }
    
    for table_name in database_schema['tables'].keys():
        if 'user' in table_name:
            domains['👤 사용자 관리'].append(table_name)
        elif 'wallet' in table_name:
            domains['💰 지갑 관리'].append(table_name)
        elif any(word in table_name for word in ['transaction', 'deposit', 'withdrawal', 'balance']):
            domains['💸 거래'].append(table_name)
        elif 'energy' in table_name:
            domains['⚡ 에너지 풀'].append(table_name)
        elif 'partner' in table_name or 'fee' in table_name:
            domains['🤝 파트너사'].append(table_name)
        elif any(word in table_name for word in ['analytics', 'log', 'audit']):
            domains['📊 분석/로그'].append(table_name)
        else:
            domains['🔧 시스템'].append(table_name)
    
    for domain, tables in domains.items():
        if tables:
            print(f'\n{domain}:')
            for table in tables:
                print(f'  • {table}')
    
    return database_schema

if __name__ == "__main__":
    schema = analyze_database()
