"""
슈퍼 어드민 인증 및 권한 관리
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db

# HTTP Bearer 토큰 인증
security = HTTPBearer()


class SuperAdminPermission:
    """슈퍼 어드민 권한"""
    MANAGE_PARTNERS = "manage:partners"
    MANAGE_ENERGY = "manage:energy"
    MANAGE_BILLING = "manage:billing"
    VIEW_ANALYTICS = "view:analytics"
    SYSTEM_CONFIG = "system:config"
    ALL_PERMISSIONS = [
        MANAGE_PARTNERS,
        MANAGE_ENERGY,
        MANAGE_BILLING,
        VIEW_ANALYTICS,
        SYSTEM_CONFIG
    ]


def get_current_super_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """현재 슈퍼 어드민 사용자 인증"""
    # 실제 구현에서는 JWT 토큰 검증, 사용자 조회 등 수행
    # 현재는 기본적인 토큰 검증만 구현
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    token = credentials.credentials
    
    # 기본 토큰 검증 (실제 구현에서는 JWT 검증)
    if not token or token != "super_admin_token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # 슈퍼 어드민 사용자 정보 반환 (임시)
    return {
        "id": "super_admin_001",
        "username": "super_admin",
        "email": "admin@dantarowallet.com",
        "role": "super_admin",
        "permissions": SuperAdminPermission.ALL_PERMISSIONS
    }


def require_super_admin_permission(required_permissions: list):
    """슈퍼 어드민 권한 확인 데코레이터"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 현재 사용자의 권한 확인
            current_admin = kwargs.get("current_admin")
            if not current_admin:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_permissions = current_admin.get("permissions", [])
            
            # 필요한 권한 확인
            for permission in required_permissions:
                if permission not in user_permissions:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied. Required: {permission}"
                    )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user_id(current_admin = Depends(get_current_super_admin)) -> str:
    """현재 사용자 ID 반환"""
    return current_admin.get("id")


def get_current_user_permissions(current_admin = Depends(get_current_super_admin)) -> list:
    """현재 사용자 권한 반환"""
    return current_admin.get("permissions", [])
