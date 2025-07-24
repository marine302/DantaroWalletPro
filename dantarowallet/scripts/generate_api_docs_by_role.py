#!/usr/bin/env python3
"""
API 역할별 분류 자동화 스크립트
OpenAPI JSON에서 tags 기반으로 API를 역할별로 분류하여 문서 생성
"""

import json
import requests
from typing import Dict, List, Set
from pathlib import Path

# API 역할별 태그 매핑
ROLE_MAPPINGS = {
    "super_admin": {
        "tags": [
            "admin", "admin_dashboard", "admin_partners", "admin_energy", 
            "admin_fees", "partner_onboarding", "audit_compliance",
            "withdrawal_management", "sweep", "admin_energy_rental"
        ],
        "title": "🔐 Super Admin Dashboard 전용 API",
        "description": "포트 3020: /frontend/super-admin-dashboard/",
        "frontend_port": 3020
    },
    "partner_admin": {
        "tags": [
            "tronlink", "energy_management", "fee_policy", "partner",
            "partner_energy_rental", "energy_rental"
        ],
        "title": "🔗 Partner Admin Template 전용 API", 
        "description": "포트 3030: /frontend/partner-admin-template/",
        "frontend_port": 3030
    },
    "common": {
        "tags": [
            "authentication", "balance", "wallet", "deposit", 
            "withdrawal", "users", "transactions", "analytics"
        ],
        "title": "🔄 공통 API (양쪽 모두 사용)",
        "description": "Super Admin Dashboard와 Partner Admin Template 공통 사용",
        "frontend_port": None
    },
    "development": {
        "tags": [
            "simple-energy", "test", "optimization"
        ],
        "title": "🌟 개발/테스트용 API",
        "description": "개발 및 테스트 전용",
        "frontend_port": None
    }
}

TAG_DESCRIPTIONS = {
    "admin": "👑 시스템 관리",
    "admin_dashboard": "📊 Super Admin Dashboard", 
    "admin_partners": "🤝 파트너사 관리",
    "admin_energy": "⚡ 에너지 풀 관리",
    "admin_fees": "💰 수수료 관리",
    "partner_onboarding": "🚀 파트너 온보딩",
    "audit_compliance": "📋 감사 및 컴플라이언스",
    "withdrawal_management": "💸 출금 관리",
    "sweep": "🧹 자금 정리",
    "admin_energy_rental": "⚡ 에너지 렌탈 관리",
    
    "tronlink": "🔗 TronLink 연동",
    "energy_management": "⚡ 에너지 관리",
    "fee_policy": "💰 수수료 정책",
    "partner": "🏢 파트너 관리",
    "partner_energy_rental": "⚡ 파트너 에너지 렌탈",
    "energy_rental": "⚡ 에너지 렌탈",
    
    "authentication": "🔐 인증",
    "balance": "💳 잔액 관리",
    "wallet": "👛 지갑 관리",
    "deposit": "📥 입금 관리",
    "withdrawal": "📤 출금 관리",
    "users": "👥 사용자 관리",
    "transactions": "💰 거래 내역",
    "analytics": "📊 분석",
    
    "simple-energy": "⚡ Simple Energy Service",
    "test": "🧪 테스트",
    "optimization": "🔧 최적화"
}

def fetch_openapi_spec(api_url: str = "http://localhost:8000/api/v1/openapi.json") -> dict:
    """OpenAPI 스펙 가져오기"""
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"⚠️ API 스펙 가져오기 실패: {e}")
        return {}

def classify_endpoints_by_role(openapi_spec: dict) -> Dict[str, Dict[str, List]]:
    """엔드포인트를 역할별로 분류"""
    classified = {role: {} for role in ROLE_MAPPINGS.keys()}
    
    paths = openapi_spec.get("paths", {})
    
    for path, methods in paths.items():
        for method, spec in methods.items():
            if method.upper() not in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                continue
                
            tags = spec.get("tags", [])
            summary = spec.get("summary", "")
            description = spec.get("description", "")
            
            # 각 태그에 대해 역할 분류
            for tag in tags:
                role = find_role_for_tag(tag)
                if role:
                    if tag not in classified[role]:
                        classified[role][tag] = []
                    
                    classified[role][tag].append({
                        "method": method.upper(),
                        "path": path,
                        "summary": summary,
                        "description": description
                    })
    
    return classified

def find_role_for_tag(tag: str) -> str:
    """태그에 해당하는 역할 찾기"""
    for role, config in ROLE_MAPPINGS.items():
        if tag in config["tags"]:
            return role
    return "common"  # 기본값

def generate_api_documentation(classified_endpoints: Dict[str, Dict[str, List]]) -> str:
    """역할별 API 문서 생성"""
    doc = "# 🎯 **역할별 API 참조 가이드**\n\n"
    doc += "프론트엔드 개발자를 위한 역할별 API 엔드포인트 분류\n\n"
    doc += "---\n\n"
    
    for role, role_config in ROLE_MAPPINGS.items():
        endpoints = classified_endpoints.get(role, {})
        if not endpoints:
            continue
            
        # 역할별 섹션 헤더
        doc += f"## {role_config['title']}\n"
        doc += f"**{role_config['description']}**\n\n"
        
        # 각 태그별 API 목록
        for tag, apis in endpoints.items():
            if not apis:
                continue
                
            tag_desc = TAG_DESCRIPTIONS.get(tag, tag)
            doc += f"### **{tag_desc}**\n"
            
            for api in sorted(apis, key=lambda x: (x['path'], x['method'])):
                method_emoji = {
                    'GET': '🔍', 'POST': '➕', 'PUT': '✏️', 
                    'PATCH': '🔧', 'DELETE': '🗑️'
                }.get(api['method'], '📡')
                
                doc += f"- {method_emoji} `{api['method']} {api['path']}` - {api['summary']}\n"
            
            doc += "\n"
        
        doc += "---\n\n"
    
    return doc

def generate_typescript_types(classified_endpoints: Dict[str, Dict[str, List]]) -> str:
    """TypeScript 타입 정의 생성"""
    ts_code = "// 🎯 역할별 API 엔드포인트 타입 정의\n\n"
    
    for role, role_config in ROLE_MAPPINGS.items():
        endpoints = classified_endpoints.get(role, {})
        if not endpoints:
            continue
            
        tags = list(endpoints.keys())
        ts_code += f"// {role_config['title']}\n"
        ts_code += f"export const {role.upper()}_APIS = {json.dumps(tags, indent=2)};\n\n"
    
    # API 권한 체크 함수
    ts_code += """
// 권한별 API 접근 제어
export const hasAPIAccess = (userRole: string, apiTag: string): boolean => {
  switch (userRole) {
    case 'super_admin':
      return SUPER_ADMIN_APIS.includes(apiTag) || COMMON_APIS.includes(apiTag);
    case 'partner_admin':
      return PARTNER_ADMIN_APIS.includes(apiTag) || COMMON_APIS.includes(apiTag);
    default:
      return COMMON_APIS.includes(apiTag);
  }
};

// API 엔드포인트 분류
export const API_CLASSIFICATION = {
  super_admin: SUPER_ADMIN_APIS,
  partner_admin: PARTNER_ADMIN_APIS,
  common: COMMON_APIS,
  development: DEVELOPMENT_APIS
};
"""
    
    return ts_code

def save_documentation(content: str, filename: str = "API_REFERENCE_BY_ROLE.md"):
    """문서 파일 저장"""
    docs_dir = Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    file_path = docs_dir / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 문서 저장: {file_path}")

def save_typescript_types(content: str, filename: str = "api-classification.ts"):
    """TypeScript 타입 파일 저장"""
    frontend_dirs = [
        Path(__file__).parent.parent / "frontend" / "super-admin-dashboard" / "src" / "lib",
        Path(__file__).parent.parent / "frontend" / "partner-admin-template" / "src" / "lib"
    ]
    
    for frontend_dir in frontend_dirs:
        if frontend_dir.exists():
            file_path = frontend_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ TypeScript 타입 저장: {file_path}")

def main():
    """메인 실행 함수"""
    print("🚀 API 역할별 분류 시작...")
    
    # 1. OpenAPI 스펙 가져오기
    openapi_spec = fetch_openapi_spec()
    if not openapi_spec:
        print("❌ OpenAPI 스펙을 가져올 수 없습니다.")
        return
    
    # 2. 엔드포인트 분류
    classified_endpoints = classify_endpoints_by_role(openapi_spec)
    
    # 3. 통계 출력
    total_endpoints = sum(
        len(apis) for role_endpoints in classified_endpoints.values()
        for apis in role_endpoints.values()
    )
    print(f"📊 총 {total_endpoints}개 엔드포인트 분류 완료")
    
    for role, endpoints in classified_endpoints.items():
        count = sum(len(apis) for apis in endpoints.values())
        role_title = ROLE_MAPPINGS[role]["title"].split("**")[1] if "**" in ROLE_MAPPINGS[role]["title"] else role
        print(f"  - {role_title}: {count}개")
    
    # 4. 마크다운 문서 생성
    markdown_doc = generate_api_documentation(classified_endpoints)
    save_documentation(markdown_doc)
    
    # 5. TypeScript 타입 생성
    typescript_types = generate_typescript_types(classified_endpoints)
    save_typescript_types(typescript_types)
    
    print("🎉 API 분류 및 문서 생성 완료!")

if __name__ == "__main__":
    main()
