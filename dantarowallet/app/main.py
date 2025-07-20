"""
Main FastAPI application module for DantaroWallet.
Production-ready FastAPI application with advanced middleware, logging, and error handling.
"""
import asyncio
import os
import time
from contextlib import asynccontextmanager

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import DantaroException
from app.core.logging import setup_logging
from app.middleware.admin_auth import AdminAuthMiddleware
from app.middleware.exception import dantaro_exception_handler, global_exception_handler
from app.middleware.logging import RequestIdAndLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.validation import RequestValidationMiddleware
from app.services.deposit_monitoring_service import deposit_monitor
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# 로깅 설정
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 생명주기 관리.
    시작 시 리소스를 초기화하고 종료 시 정리합니다.
    """
    # 시작 시 작업
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📊 Debug mode: {settings.DEBUG}")
    logger.info(f"🌐 Environment: {settings.TRON_NETWORK}")

    # 입금 모니터링 백그라운드 시작 (개발환경에서는 비활성화)
    if not deposit_monitor.is_monitoring and not settings.DEBUG:
        logger.info("🔍 Starting deposit monitoring...")
        asyncio.create_task(deposit_monitor.start_monitoring())
    elif settings.DEBUG:
        logger.info("🔧 Development mode: Deposit monitoring disabled")

    # FastAPI에게 "준비 완료" 신호 전달
    yield

    # 종료 시 작업
    logger.info("🛑 Stopping deposit monitoring...")
    await deposit_monitor.stop_monitoring()
    logger.info(f"🛑 Shutting down {settings.APP_NAME}")


# FastAPI 태그 메타데이터 - 각 엔드포인트 그룹의 용도를 명확히 정의
tags_metadata = [
    # === Super Admin Dashboard 전용 ===
    {
        "name": "admin",
        "description": "**🔐 Super Admin Dashboard** - Administrative operations for super administrators",
        "externalDocs": {
            "description": "Frontend: /frontend/super-admin-dashboard/",
            "url": "http://localhost:3020"
        }
    },
    {
        "name": "admin_dashboard",
        "description": "**📊 Super Admin Dashboard** - Dashboard statistics and system health monitoring",
        "externalDocs": {
            "description": "Frontend: /frontend/super-admin-dashboard/",
            "url": "http://localhost:3020"
        }
    },
    {
        "name": "admin_fees",
        "description": "**💰 Super Admin Dashboard** - Fee configuration and revenue management",
    },
    {
        "name": "admin_energy",
        "description": "**⚡ Super Admin Dashboard** - Energy pool administration and monitoring",
    },
    {
        "name": "admin_partners",
        "description": "**🤝 Super Admin Dashboard** - Partner management and performance tracking",
    },
    {
        "name": "audit-compliance",
        "description": "**🔍 Super Admin Dashboard** - Transaction auditing and compliance monitoring",
        "externalDocs": {
            "description": "Frontend: /app/audit-compliance/page.tsx",
            "url": "http://localhost:3020/audit-compliance"
        }
    },
    {
        "name": "integrated_dashboard",
        "description": "**📈 Super Admin Dashboard** - Comprehensive partner analytics dashboard",
        "externalDocs": {
            "description": "Frontend: /app/integrated-dashboard/page.tsx", 
            "url": "http://localhost:3020/integrated-dashboard"
        }
    },
    {
        "name": "withdrawal_management",
        "description": "**💸 Super Admin Dashboard** - Advanced withdrawal policies and batch processing",
    },
    {
        "name": "sweep",
        "description": "**🧹 Super Admin Dashboard** - Deposit sweep automation and master wallet management",
    },
    {
        "name": "partner_onboarding",
        "description": "**🚀 Super Admin Dashboard** - Partner onboarding automation and progress tracking",
    },
    
    # === Partner Admin Template 전용 ===
    {
        "name": "tronlink",
        "description": "**🔗 Partner Admin Template** - TronLink wallet integration for partner users",
        "externalDocs": {
            "description": "Frontend: /frontend/partner-admin-template/",
            "url": "http://localhost:3030"
        }
    },
    {
        "name": "energy_management",
        "description": "**⚡ Partner Admin Template** - Energy pool CRUD operations for partners",
    },
    {
        "name": "fee_policy",
        "description": "**💰 Partner Admin Template** - Partner-specific fee policies and tier management",
    },
    
    # === 공통 사용 (양쪽 프론트엔드) ===
    {
        "name": "authentication",
        "description": "**🔐 Common** - User authentication and authorization (both frontends)",
    },
    {
        "name": "balance",
        "description": "**💰 Common** - Internal balance management (different from on-chain wallet balance)",
    },
    {
        "name": "wallet",
        "description": "**👝 Common** - User wallet management and on-chain balance operations",
    },
    {
        "name": "deposit",
        "description": "**📥 Common** - Deposit monitoring and processing",
    },
    {
        "name": "withdrawal",
        "description": "**📤 Common** - Basic withdrawal operations",
    },
    {
        "name": "energy",
        "description": "**⚡ Common** - Energy monitoring and analytics (different purposes per frontend)",
    },
    {
        "name": "external_energy",
        "description": "**🔌 Common** - External energy provider integration",
    },
    
    # === 시스템/분석 ===
    {
        "name": "analytics",
        "description": "**📊 Analytics** - Transaction analytics and anomaly detection",
    },
    {
        "name": "statistics",
        "description": "**📈 Statistics** - General system statistics and metrics",
    },
    {
        "name": "transactions",
        "description": "**💳 Management** - Transaction management and monitoring",
    },
    {
        "name": "users",
        "description": "**👥 Management** - User management and activity tracking",
    },
    {
        "name": "partners",
        "description": "**🤝 Management** - Basic partner CRUD operations",
    },
    
    # === 시스템 ===
    {
        "name": "health",
        "description": "**🏥 System** - Health check endpoints",
    },
    {
        "name": "root",
        "description": "**🏠 System** - Root API information",
    },
    {
        "name": "auth-pages",
        "description": "**📄 Web Pages** - Authentication web pages",
    },
    {
        "name": "web-dashboard",
        "description": "**🌐 Web Pages** - Dashboard web pages",
    },
]

# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## 🏦 DantaroWallet Pro - Multi-Tenant USDT Wallet System

Advanced hybrid wallet system with comprehensive admin and partner management capabilities.

### 🎯 Frontend Applications:
- **Super Admin Dashboard** (Port 3020): Complete system administration
- **Partner Admin Template** (Port 3030): Partner-specific operations

### 📋 API Categories:
- **Admin APIs**: Super admin exclusive operations
- **Partner APIs**: Partner admin template functions  
- **Common APIs**: Shared across both frontends
- **System APIs**: Health checks and system information

### 🔧 Development:
- Use `/health` for system status
- API docs available at `/api/v1/docs` (development only)
- OpenAPI spec at `/api/v1/openapi.json`
    """,
    # DEBUG 모드에서만 API 문서 노출
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json" if settings.DEBUG else None,
    docs_url=f"{settings.API_V1_PREFIX}/docs" if settings.DEBUG else None,
    redoc_url=f"{settings.API_V1_PREFIX}/redoc" if settings.DEBUG else None,
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)


# CORS 설정 미들웨어 - 동적 포트 설정 사용
cors_origins = settings.DYNAMIC_CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,  # credentials를 True로 설정
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# 신뢰할 수 있는 호스트 제한 (운영 환경에서만 적용)
if not settings.DEBUG:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

# 관리자 인증 미들웨어 추가
app.add_middleware(AdminAuthMiddleware, admin_paths=["/admin"])

# 요청 검증 미들웨어 추가
app.add_middleware(
    RequestValidationMiddleware,
    max_content_length=settings.MAX_REQUEST_SIZE,
)

# 요청 제한 미들웨어 추가
app.add_middleware(
    RateLimitMiddleware,
    calls=settings.RATE_LIMIT_CALLS,
    period=settings.RATE_LIMIT_PERIOD,
)

# 요청 추적 미들웨어 (클래스 기반으로 변경)
app.add_middleware(RequestIdAndLoggingMiddleware)


def exception_handler_wrapper(handler):
    async def wrapper(request, exc):
        return await handler(request, exc)

    return wrapper


# 커스텀 예외 처리
app.add_exception_handler(
    DantaroException, exception_handler_wrapper(dantaro_exception_handler)
)
# 글로벌 예외 처리
app.add_exception_handler(
    Exception, exception_handler_wrapper(global_exception_handler)
)


# Health check 엔드포인트
@app.get("/health", tags=["health"])
async def health_check():
    """
    시스템 상태를 확인하기 위한 헬스 체크 엔드포인트.
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "environment": settings.TRON_NETWORK,
    }


# 루트 경로 정보
@app.get("/", tags=["root"])
async def root():
    """API에 대한 기본 정보를 제공합니다."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs" if settings.DEBUG else None,
        "health": "/health",
        "environment": settings.TRON_NETWORK,
    }


# API 라우터 등록
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# 인증 페이지 라우터 등록
from app.api.v1.auth_pages import router as auth_pages_router

app.include_router(auth_pages_router, prefix="/auth", tags=["auth-pages"])

# 웹 대시보드 라우터 등록
from app.api.v1.web_dashboard import router as web_dashboard_router

app.include_router(web_dashboard_router, prefix="/dashboard", tags=["web-dashboard"])

# TronLink 연동 페이지 라우터 등록
templates = Jinja2Templates(directory="templates")


@app.get("/tronlink", response_class=HTMLResponse, tags=["tronlink"])
async def tronlink_page(request: Request):
    """TronLink 연동 페이지"""
    return templates.TemplateResponse("tronlink.html", {"request": request})

# 정적 파일 마운트 (CSS, JS, 이미지 등)
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
