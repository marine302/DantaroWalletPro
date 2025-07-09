# Copilot 문서 #4: JWT 기반 사용자 인증 시스템

## 목표
JWT 토큰을 사용한 사용자 인증 시스템을 구현합니다. 회원가입, 로그인, 토큰 갱신, 인증 미들웨어를 포함합니다.

## 전제 조건
- Copilot 문서 #1, #2, #3이 완료되어 있어야 합니다.
- User 모델이 데이터베이스에 생성되어 있어야 합니다.

## 상세 지시사항

### 1. 보안 유틸리티 (app/core/security.py)

```python
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
import secrets

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 설정
ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: Dict[str, Any]) -> str:
    """액세스 토큰 생성"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """리프레시 토큰 생성"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": secrets.token_urlsafe(32)  # JWT ID for revocation
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """토큰 검증"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)

def generate_verification_token() -> str:
    """이메일 인증 토큰 생성"""
    return secrets.token_urlsafe(32)

def validate_password_strength(password: str) -> tuple[bool, str]:
    """비밀번호 강도 검증"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one digit"
    
    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(char.islower() for char in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is valid"
```

### 2. 인증 스키마 (app/schemas/auth.py)

```python
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

class UserRegister(BaseModel):
    """회원가입 요청 스키마"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    password_confirm: str
    
    @validator('password_confirm')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserLogin(BaseModel):
    """로그인 요청 스키마"""
    email: EmailStr
    password: str

class Token(BaseModel):
    """토큰 응답 스키마"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

class TokenRefresh(BaseModel):
    """토큰 갱신 요청 스키마"""
    refresh_token: str

class UserResponse(BaseModel):
    """사용자 응답 스키마"""
    id: int
    email: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class PasswordChange(BaseModel):
    """비밀번호 변경 요청 스키마"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    new_password_confirm: str
    
    @validator('new_password_confirm')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class PasswordReset(BaseModel):
    """비밀번호 재설정 요청 스키마"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """비밀번호 재설정 확인 스키마"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
```

### 3. 의존성 주입 (app/api/deps.py)

```python
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User
from app.core.exceptions import AuthenticationError, AuthorizationError

# Bearer 토큰 스키마
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """현재 인증된 사용자 가져오기"""
    token = credentials.credentials
    
    # 토큰 검증
    payload = verify_token(token, token_type="access")
    if not payload:
        raise AuthenticationError("Invalid authentication credentials")
    
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")
    
    # 사용자 조회
    result = await db.execute(
        select(User).filter(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise AuthenticationError("User not found")
    
    if not user.is_active:
        raise AuthenticationError("Inactive user")
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """활성 사용자만 허용"""
    if not current_user.is_active:
        raise AuthorizationError("Inactive user")
    return current_user

async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """인증된 사용자만 허용"""
    if not current_user.is_verified:
        raise AuthorizationError("Email not verified")
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """관리자만 허용"""
    if not current_user.is_admin:
        raise AuthorizationError("Not enough permissions")
    return current_user

# Optional user dependency (for public endpoints that may have auth)
async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """선택적 인증 - 인증되지 않아도 접근 가능"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except AuthenticationError:
        return None
```

### 4. 인증 엔드포인트 (app/api/v1/endpoints/auth.py)

```python
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.api import deps
from app.core.database import get_db
from app.core.security import (
    get_password_hash, verify_password, create_access_token,
    create_refresh_token, verify_token, validate_password_strength
)
from app.core.config import settings
from app.core.exceptions import ValidationError, ConflictError, AuthenticationError
from app.models.user import User
from app.models.balance import Balance
from app.schemas.auth import (
    UserRegister, UserLogin, Token, TokenRefresh,
    UserResponse, PasswordChange
)
from decimal import Decimal

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """사용자 회원가입"""
    # 이메일 중복 확인
    result = await db.execute(
        select(User).filter(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise ConflictError("Email already registered")
    
    # 비밀번호 강도 검증
    is_valid, message = validate_password_strength(user_data.password)
    if not is_valid:
        raise ValidationError(message, field="password")
    
    # 사용자 생성
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        is_active=True,
        is_verified=False  # 이메일 인증 필요
    )
    db.add(user)
    await db.flush()
    
    # 초기 잔고 생성 (0 USDT)
    balance = Balance(
        user_id=user.id,
        asset="USDT",
        amount=Decimal("0.000000"),
        locked_amount=Decimal("0.000000")
    )
    db.add(balance)
    
    await db.commit()
    await db.refresh(user)
    
    # TODO: 백그라운드 태스크로 환영 이메일 발송
    # background_tasks.add_task(send_welcome_email, user.email)
    
    logger.info(f"New user registered: {user.email}")
    return user

@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """사용자 로그인"""
    # 사용자 조회
    result = await db.execute(
        select(User).filter(User.email == user_credentials.email)
    )
    user = result.scalar_one_or_none()
    
    # 인증 실패
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise AuthenticationError("Incorrect email or password")
    
    # 계정 상태 확인
    if not user.is_active:
        raise AuthenticationError("Account is deactivated")
    
    # 토큰 생성
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    logger.info(f"User logged in: {user.email}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """토큰 갱신"""
    # 리프레시 토큰 검증
    payload = verify_token(token_data.refresh_token, token_type="refresh")
    if not payload:
        raise AuthenticationError("Invalid refresh token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")
    
    # 사용자 확인
    result = await db.execute(
        select(User).filter(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise AuthenticationError("User not found or inactive")
    
    # 새 토큰 생성
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(deps.get_current_active_user)
):
    """현재 사용자 정보 조회"""
    return current_user

@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """비밀번호 변경"""
    # 현재 비밀번호 확인
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise ValidationError("Current password is incorrect", field="current_password")
    
    # 새 비밀번호 강도 검증
    is_valid, message = validate_password_strength(password_data.new_password)
    if not is_valid:
        raise ValidationError(message, field="new_password")
    
    # 비밀번호 업데이트
    current_user.password_hash = get_password_hash(password_data.new_password)
    await db.commit()
    
    logger.info(f"Password changed for user: {current_user.email}")
    
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(deps.get_current_active_user)
):
    """로그아웃 (클라이언트에서 토큰 삭제)"""
    # 서버 측에서는 특별한 작업 없음
    # 실제 운영에서는 토큰 블랙리스트를 Redis에 저장할 수 있음
    logger.info(f"User logged out: {current_user.email}")
    return
```

### 5. API 라우터 업데이트 (app/api/v1/api.py)

```python
from fastapi import APIRouter
from app.api.v1.endpoints import auth  # 추가

api_router = APIRouter()

# 인증 라우터 추가
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# 기존 테스트 엔드포인트
@api_router.get("/test")
async def test_endpoint():
    return {"message": "API v1 is working"}
```

### 6. 인증 테스트 (tests/test_auth.py)

```python
import pytest
from httpx import AsyncClient
from app.main import app
from app.core.security import verify_token
import json

@pytest.mark.asyncio
async def test_user_registration():
    """사용자 회원가입 테스트"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "Test123!@#",
                "password_confirm": "Test123!@#"
            }
        )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["is_active"] is True
    assert data["is_verified"] is False
    assert "password" not in data

@pytest.mark.asyncio
async def test_duplicate_registration():
    """중복 회원가입 방지 테스트"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 첫 번째 가입
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "Test123!@#",
                "password_confirm": "Test123!@#"
            }
        )
        
        # 중복 가입 시도
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "Test123!@#",
                "password_confirm": "Test123!@#"
            }
        )
    
    assert response.status_code == 409
    assert response.json()["error"] == "CONFLICT"

@pytest.mark.asyncio
async def test_weak_password():
    """약한 비밀번호 거부 테스트"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "weakpass@example.com",
                "password": "weak",
                "password_confirm": "weak"
            }
        )
    
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_user_login():
    """로그인 테스트"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 사용자 생성
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "logintest@example.com",
                "password": "Test123!@#",
                "password_confirm": "Test123!@#"
            }
        )
        
        # 로그인
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "logintest@example.com",
                "password": "Test123!@#"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    
    # 토큰 검증
    payload = verify_token(data["access_token"])
    assert payload is not None
    assert payload["type"] == "access"

@pytest.mark.asyncio
async def test_invalid_login():
    """잘못된 로그인 정보 테스트"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "WrongPass123!"
            }
        )
    
    assert response.status_code == 401
    assert response.json()["error"] == "AUTH_ERROR"

@pytest.mark.asyncio
async def test_get_current_user():
    """현재 사용자 정보 조회 테스트"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 회원가입 및 로그인
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "currentuser@example.com",
                "password": "Test123!@#",
                "password_confirm": "Test123!@#"
            }
        )
        
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "currentuser@example.com",
                "password": "Test123!@#"
            }
        )
        
        token = login_response.json()["access_token"]
        
        # 사용자 정보 조회
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "currentuser@example.com"

@pytest.mark.asyncio
async def test_token_refresh():
    """토큰 갱신 테스트"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 로그인하여 토큰 획득
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "refreshtest@example.com",
                "password": "Test123!@#",
                "password_confirm": "Test123!@#"
            }
        )
        
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "refreshtest@example.com",
                "password": "Test123!@#"
            }
        )
        
        refresh_token = login_response.json()["refresh_token"]
        
        # 토큰 갱신
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
```

### 7. 환경 변수 추가 (.env)

`.env` 파일에 다음 설정이 있는지 확인:

```env
# Security
SECRET_KEY=your-very-secure-secret-key-at-least-32-characters-long
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256
```

## 실행 및 검증

1. 서버 재시작:
   ```bash
   make dev
   ```

2. API 문서에서 인증 엔드포인트 확인:
   http://localhost:8000/api/v1/docs

3. 테스트 실행:
   ```bash
   make test tests/test_auth.py
   ```

4. 수동 테스트:
   ```bash
   # 회원가입
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"Test123!@#","password_confirm":"Test123!@#"}'
   
   # 로그인
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"Test123!@#"}'
   ```

## 검증 포인트

- [ ] 회원가입이 정상 작동하는가?
- [ ] 비밀번호 강도 검증이 작동하는가?
- [ ] 로그인 시 JWT 토큰이 발급되는가?
- [ ] 토큰으로 인증이 필요한 엔드포인트에 접근 가능한가?
- [ ] 토큰 갱신이 정상 작동하는가?
- [ ] 잘못된 토큰으로 접근 시 401 에러가 발생하는가?
- [ ] 비밀번호 변경이 작동하는가?
- [ ] 모든 테스트가 통과하는가?

이 문서를 완료하면 JWT 기반의 완전한 인증 시스템이 구축되며, 사용자 관리의 기초가 완성됩니다.