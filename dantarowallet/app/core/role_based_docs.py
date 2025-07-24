"""
역할별 별도 API 문서 생성
Super Admin과 Partner Admin을 위한 분리된 API 문서 제공
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.api.v1.api import api_router
from app.core.config import settings

# Super Admin 전용 태그
SUPER_ADMIN_TAGS = [
    "admin", "admin_dashboard", "admin_partners", "admin_energy", 
    "admin_fees", "partner_onboarding", "audit_compliance",
    "withdrawal_management", "sweep", "admin_energy_rental"
]

# Partner Admin 전용 태그
PARTNER_ADMIN_TAGS = [
    "tronlink", "energy_management", "fee_policy", "partner",
    "partner_energy_rental", "energy_rental"
]

# 공통 태그
COMMON_TAGS = [
    "authentication", "balance", "wallet", "deposit", 
    "withdrawal", "users", "transactions", "analytics"
]

def create_super_admin_openapi(app: FastAPI) -> dict:
    """Super Admin 전용 OpenAPI 스키마 생성"""
    if app.openapi_schema:
        return app.openapi_schema
        
    openapi_schema = get_openapi(
        title=f"{settings.APP_NAME} - Super Admin API",
        version=settings.APP_VERSION,
        description="""
        ## 🔐 Super Admin Dashboard API
        
        **슈퍼 어드민 전용 API 문서**
        
        ### 🎯 Target: Super Admin Dashboard (Port 3020)
        - 시스템 전체 관리
        - 파트너사 관리  
        - 에너지 풀 관리
        - 수수료 관리
        - 온보딩 관리
        
        ### 📊 포함된 API:
        - **Admin**: 시스템 관리
        - **Partner Management**: 파트너사 관리
        - **Energy Management**: 에너지 풀 관리
        - **Fee Management**: 수수료 관리
        - **Compliance**: 감사 및 컴플라이언스
        - **Common APIs**: 공통 기능
        """,
        routes=app.routes,
    )
    
    # Super Admin과 공통 태그만 필터링
    allowed_tags = set(SUPER_ADMIN_TAGS + COMMON_TAGS)
    filtered_paths = {}
    
    for path, path_item in openapi_schema.get("paths", {}).items():
        filtered_path_item = {}
        for method, operation in path_item.items():
            if method.lower() in ["get", "post", "put", "patch", "delete", "options", "head"]:
                operation_tags = operation.get("tags", [])
                if any(tag in allowed_tags for tag in operation_tags):
                    filtered_path_item[method] = operation
        
        if filtered_path_item:
            filtered_paths[path] = filtered_path_item
    
    openapi_schema["paths"] = filtered_paths
    return openapi_schema

def create_partner_admin_openapi(app: FastAPI) -> dict:
    """Partner Admin 전용 OpenAPI 스키마 생성"""
    openapi_schema = get_openapi(
        title=f"{settings.APP_NAME} - Partner Admin API", 
        version=settings.APP_VERSION,
        description="""
        ## 🔗 Partner Admin Template API
        
        **파트너 어드민 전용 API 문서**
        
        ### 🎯 Target: Partner Admin Template (Port 3030)
        - TronLink 연동
        - 파트너별 에너지 관리
        - 파트너 수수료 정책
        - 파트너 사용자 관리
        
        ### 📊 포함된 API:
        - **TronLink**: TronLink 지갑 연동
        - **Energy**: 파트너 에너지 관리
        - **Fee Policy**: 파트너 수수료 정책
        - **Partner Management**: 파트너 관리
        - **Common APIs**: 공통 기능
        """,
        routes=app.routes,
    )
    
    # Partner Admin과 공통 태그만 필터링
    allowed_tags = set(PARTNER_ADMIN_TAGS + COMMON_TAGS)
    filtered_paths = {}
    
    for path, path_item in openapi_schema.get("paths", {}).items():
        filtered_path_item = {}
        for method, operation in path_item.items():
            if method.lower() in ["get", "post", "put", "patch", "delete", "options", "head"]:
                operation_tags = operation.get("tags", [])
                if any(tag in allowed_tags for tag in operation_tags):
                    filtered_path_item[method] = operation
        
        if filtered_path_item:
            filtered_paths[path] = filtered_path_item
    
    openapi_schema["paths"] = filtered_paths
    return openapi_schema

def create_development_openapi(app: FastAPI) -> dict:
    """개발/테스트 전용 OpenAPI 스키마 생성"""
    openapi_schema = get_openapi(
        title=f"{settings.APP_NAME} - Development API",
        version=settings.APP_VERSION,
        description="""
        ## 🌟 Development & Testing API
        
        **개발 및 테스트 전용 API 문서**
        
        ### 🎯 Target: 개발자 및 QA 팀
        - Simple Energy Service (개발용)
        - 테스트 API
        - 시스템 최적화
        
        ### 📊 포함된 API:
        - **Simple Energy**: 개발용 간단 에너지 서비스
        - **Testing**: 테스트 전용 API  
        - **Optimization**: 시스템 최적화
        """,
        routes=app.routes,
    )
    
    # 개발용 태그만 필터링
    allowed_tags = {"simple-energy", "test", "optimization"}
    filtered_paths = {}
    
    for path, path_item in openapi_schema.get("paths", {}).items():
        filtered_path_item = {}
        for method, operation in path_item.items():
            if method.lower() in ["get", "post", "put", "patch", "delete", "options", "head"]:
                operation_tags = operation.get("tags", [])
                if any(tag in allowed_tags for tag in operation_tags):
                    filtered_path_item[method] = operation
        
        if filtered_path_item:
            filtered_paths[path] = filtered_path_item
    
    openapi_schema["paths"] = filtered_paths
    return openapi_schema
