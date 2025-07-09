# Copilot 문서 #2: 기본 FastAPI 애플리케이션 구성

## 목표
FastAPI 애플리케이션의 기본 구조를 완성하고 필수 미들웨어, 에러 핸들러, 로깅 시스템을 구축합니다.

## 전제 조건
- Copilot 문서 #1이 완료되어 있어야 합니다.
- 개발 환경이 정상적으로 구동되어야 합니다.

## 상세 지시사항

### 1. 향상된 메인 애플리케이션 (app/main.py)

기존 main.py를 다음과 같이 업데이트하세요:

```python
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.api import api_router
from app.core.exceptions import DantaroException

# 로깅 설정
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    yield
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json" if settings.DEBUG else None,
    docs_url=f"{settings.API_V1_PREFIX}/docs" if settings.DEBUG else None,
    redoc_url=f"{settings.API_V1_PREFIX}/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Middleware 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 신뢰할 수 있는 호스트 설정
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Request ID 미들웨어
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(time.time_ns()))
    request.state.request_id = request_id
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s",
        extra={"request_id": request_id}
    )
    
    return response

# 글로벌 예외 처리
@app.exception_handler(DantaroException)
async def dantaro_exception_handler(request: Request, exc: DantaroException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An internal error occurred",
            "request_id": getattr(request.state, "request_id", None)
        }
    )

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG
    }

# API 라우터 포함
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
```

### 2. 로깅 시스템 (app/core/logging.py)

```python
import logging
import sys
import json
from datetime import datetime
from pythonjsonlogger import jsonlogger

from app.core.config import settings

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['app_name'] = settings.APP_NAME
        log_record['app_version'] = settings.APP_VERSION
        
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id

def setup_logging():
    logger = logging.getLogger("dantarowallet")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if settings.LOG_FORMAT == "json":
        formatter = CustomJsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (운영 환경용)
    if not settings.DEBUG:
        file_handler = logging.FileHandler('logs/app.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
```

### 3. 커스텀 예외 처리 (app/core/exceptions.py)

```python
from typing import Optional, Dict, Any
from fastapi import status

class DantaroException(Exception):
    """Base exception for DantaroWallet"""
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class AuthenticationError(DantaroException):
    """인증 관련 에러"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTH_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class AuthorizationError(DantaroException):
    """권한 관련 에러"""
    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            error_code="PERMISSION_DENIED",
            status_code=status.HTTP_403_FORBIDDEN
        )

class ValidationError(DantaroException):
    """검증 관련 에러"""
    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )

class NotFoundError(DantaroException):
    """리소스를 찾을 수 없음"""
    def __init__(self, resource: str):
        super().__init__(
            message=f"{resource} not found",
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource}
        )

class ConflictError(DantaroException):
    """리소스 충돌"""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT
        )

class RateLimitError(DantaroException):
    """요청 제한 초과"""
    def __init__(self, retry_after: int):
        super().__init__(
            message="Rate limit exceeded",
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after": retry_after}
        )

class InsufficientBalanceError(DantaroException):
    """잔액 부족"""
    def __init__(self, required: float, available: float):
        super().__init__(
            message="Insufficient balance",
            error_code="INSUFFICIENT_BALANCE",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={
                "required": required,
                "available": available
            }
        )
```

### 4. API 라우터 구조 (app/api/v1/api.py)

```python
from fastapi import APIRouter

# 엔드포인트 임포트 (추후 추가)
# from app.api.v1.endpoints import auth, users, wallets, transactions

api_router = APIRouter()

# 라우터 포함 (추후 추가)
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(wallets.router, prefix="/wallets", tags=["wallets"])
# api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])

# 임시 테스트 엔드포인트
@api_router.get("/test")
async def test_endpoint():
    return {"message": "API v1 is working"}
```

### 5. 요청 검증 미들웨어 (app/middleware/validation.py)

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import json

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """요청 크기 및 컨텐츠 타입 검증"""
    
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    
    async def dispatch(self, request: Request, call_next):
        # Content-Length 체크
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_CONTENT_LENGTH:
            return JSONResponse(
                status_code=413,
                content={"error": "Request entity too large"}
            )
        
        # JSON 요청 검증
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    await request.json()
                except json.JSONDecodeError:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid JSON"}
                    )
        
        response = await call_next(request)
        return response
```

### 6. Rate Limiting 미들웨어 (app/middleware/rate_limit.py)

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
from collections import defaultdict
from typing import Dict, Tuple

class RateLimitMiddleware(BaseHTTPMiddleware):
    """간단한 인메모리 rate limiting (개발용)"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, 0))
    
    async def dispatch(self, request: Request, call_next):
        # IP 주소 추출
        client_ip = request.client.host
        
        # 현재 시간
        now = time.time()
        
        # 클라이언트 정보 가져오기
        calls, window_start = self.clients[client_ip]
        
        # 시간 윈도우 리셋
        if now - window_start > self.period:
            calls = 0
            window_start = now
        
        # 요청 수 증가
        calls += 1
        
        # 제한 체크
        if calls > self.calls:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": int(self.period - (now - window_start))
                }
            )
        
        # 클라이언트 정보 업데이트
        self.clients[client_ip] = (calls, window_start)
        
        response = await call_next(request)
        return response
```

### 7. 업데이트된 설정 파일 (app/core/config.py 추가)

기존 config.py에 다음 설정을 추가하세요:

```python
# 기존 imports...
from typing import List, Union, Optional

class Settings(BaseSettings):
    # 기존 설정들...
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" or "plain"
    
    # Security
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_CALLS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Request
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # 기존 설정 계속...
```

### 8. 의존성 추가 (pyproject.toml)

pyproject.toml의 dependencies 섹션에 추가:

```toml
python-json-logger = "^2.0.7"
```

### 9. 통합 테스트 (tests/test_app.py)

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_api_test_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/test")
    assert response.status_code == 200
    assert response.json()["message"] == "API v1 is working"

@pytest.mark.asyncio
async def test_request_id_header():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time" in response.headers

@pytest.mark.asyncio
async def test_404_error():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/nonexistent")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_cors_headers():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.options(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
    assert response.status_code == 200
```

## 실행 및 검증

1. 의존성 업데이트:
   ```bash
   poetry add python-json-logger
   ```

2. 서버 재시작:
   ```bash
   make dev
   ```

3. 테스트 실행:
   ```bash
   make test
   ```

4. 로그 확인 (JSON 형식으로 출력되는지 확인)

5. API 문서 확인: http://localhost:8000/api/v1/docs

## 검증 포인트

- [ ] 모든 미들웨어가 정상 작동하는가?
- [ ] 로그가 JSON 형식으로 출력되는가?
- [ ] Request ID가 모든 응답에 포함되는가?
- [ ] 에러 핸들링이 일관된 형식으로 작동하는가?
- [ ] Rate limiting이 작동하는가?
- [ ] CORS가 정상 작동하는가?
- [ ] 모든 테스트가 통과하는가?

이 문서를 완료하면 production-ready FastAPI 애플리케이션 기본 구조가 완성됩니다.