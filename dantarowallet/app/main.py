"""
Main FastAPI application module for DantaroWallet.
Production-ready FastAPI application with advanced middleware, logging, and error handling.
"""

import asyncio
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.v1.api import api_router
from app.api.v1.endpoints.admin import optimization
from app.core.config import settings
from app.core.exceptions import DantaroException
from app.core.logging import setup_logging
from app.core.optimization_manager import optimization_manager
from app.middleware.admin_auth import AdminAuthMiddleware
from app.middleware.exception import dantaro_exception_handler, global_exception_handler
from app.middleware.logging import RequestIdAndLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.validation import RequestValidationMiddleware
from app.services.deposit_monitoring_service import deposit_monitor

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

    # 최적화 시스템 초기화
    try:
        logger.info("⚡ Initializing optimization system...")
        await optimization_manager.initialize()
        logger.info("✅ Optimization system initialized successfully")
    except Exception as e:
        logger.error(f"❌ Optimization system initialization failed: {e}")

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


# FastAPI 태그 메타데이터 - 역할별 API 구분을 위한 명확한 정의
tags_metadata = [
    # === 🔐 SUPER ADMIN DASHBOARD APIs (Port 3020) ===
    {
        "name": "admin",
        "description": "**🔐 SUPER ADMIN ONLY** - Administrative operations for super administrators",
        "externalDocs": {
            "description": "Super Admin Dashboard | API Docs: /api/v1/admin/docs",
            "url": "http://localhost:3020",
        },
    },
    {
        "name": "admin_dashboard", 
        "description": "**🔐 SUPER ADMIN ONLY** - Dashboard statistics and system health monitoring",
        "externalDocs": {
            "description": "Super Admin Dashboard | API Docs: /api/v1/admin/docs",
            "url": "http://localhost:3020",
        },
    },
    {
        "name": "admin_fees",
        "description": "**🔐 SUPER ADMIN ONLY** - Fee configuration and revenue management",
        "externalDocs": {
            "description": "API Docs: /api/v1/admin/docs",
            "url": "http://localhost:3020",
        },
    },
    {
        "name": "admin_energy_pool",
        "description": "**🔐 SUPER ADMIN ONLY** - Energy pool administration and monitoring",
        "externalDocs": {
            "description": "API Docs: /api/v1/admin/docs",
            "url": "http://localhost:3020",
        },
    },
    {
        "name": "admin_partners",
        "description": "**🔐 SUPER ADMIN ONLY** - Partner management and performance tracking",
        "externalDocs": {
            "description": "API Docs: /api/v1/admin/docs",
            "url": "http://localhost:3020",
        },
    },
    {
        "name": "audit-compliance",
        "description": "**🔐 SUPER ADMIN ONLY** - Transaction auditing and compliance monitoring",
        "externalDocs": {
            "description": "Super Admin Dashboard | API Docs: /api/v1/admin/docs",
            "url": "http://localhost:3020/audit-compliance",
        },
    },
    {
        "name": "integrated_dashboard",
        "description": "**🔐 SUPER ADMIN ONLY** - Comprehensive partner analytics dashboard",
        "externalDocs": {
            "description": "Super Admin Dashboard | API Docs: /api/v1/admin/docs",
            "url": "http://localhost:3020/integrated-dashboard",
        },
    },
    {
        "name": "withdrawal_management",
        "description": "**🔐 SUPER ADMIN ONLY** - Advanced withdrawal policies and batch processing",
        "externalDocs": {
            "description": "API Docs: /api/v1/admin/docs",
            "url": "http://localhost:3020",
        },
    },
    {
        "name": "sweep",
        "description": "**🧹 Super Admin Dashboard** - Deposit sweep automation and master wallet management",
    },
    {
        "name": "partner_onboarding",
        "description": "**🔐 SUPER ADMIN ONLY** - Partner onboarding automation and progress tracking",
        "externalDocs": {
            "description": "API Docs: /api/v1/admin/docs",
            "url": "http://localhost:3020",
        },
    },
    # === 🔗 PARTNER ADMIN TEMPLATE APIs (Port 3030) ===
    {
        "name": "tronlink",
        "description": "**🔗 PARTNER ADMIN ONLY** - TronLink wallet integration for partner users",
        "externalDocs": {
            "description": "Partner Admin Template | API Docs: /api/v1/partner/docs",
            "url": "http://localhost:3030",
        },
    },
    {
        "name": "partner_energy",
        "description": "**🔗 PARTNER ADMIN ONLY** - Energy pool CRUD operations for partners",
        "externalDocs": {
            "description": "API Docs: /api/v1/partner/docs",
            "url": "http://localhost:3030",
        },
    },
    {
        "name": "fee_policy",
        "description": "**🔗 PARTNER ADMIN ONLY** - Partner-specific fee policies and tier management",
        "externalDocs": {
            "description": "API Docs: /api/v1/partner/docs", 
            "url": "http://localhost:3030",
        },
    },
    {
        "name": "partner",
        "description": "**🔗 PARTNER ADMIN ONLY** - Partner profile and settings management",
        "externalDocs": {
            "description": "API Docs: /api/v1/partner/docs",
            "url": "http://localhost:3030",
        },
    },
    {
        "name": "partners_simple",
        "description": "**🔗 PARTNER ADMIN ONLY** - Simple partner management operations",
        "externalDocs": {
            "description": "API Docs: /api/v1/partner/docs",
            "url": "http://localhost:3030",
        },
    },
    # === 🔄 COMMON APIs (양쪽 프론트엔드 공통 사용) ===
    {
        "name": "authentication",
        "description": "**🔄 COMMON** - User authentication and authorization (both frontends)",
        "externalDocs": {
            "description": "Super Admin: /api/v1/admin/docs | Partner Admin: /api/v1/partner/docs",
            "url": "http://localhost:8000",
        },
    },
    {
        "name": "balance",
        "description": "**🔄 COMMON** - Internal balance management (different from on-chain wallet balance)",
        "externalDocs": {
            "description": "Used by both Super Admin and Partner Admin",
            "url": "http://localhost:8000",
        },
    },
    {
        "name": "wallet",
        "description": "**🔄 COMMON** - User wallet management and on-chain balance operations",
        "externalDocs": {
            "description": "Used by both Super Admin and Partner Admin",
            "url": "http://localhost:8000",
        },
    },
    {
        "name": "deposit",
        "description": "**🔄 COMMON** - Deposit monitoring and processing",
        "externalDocs": {
            "description": "Used by both Super Admin and Partner Admin",
            "url": "http://localhost:8000",
        },
    },
    {
        "name": "withdrawal",
        "description": "**🔄 COMMON** - Basic withdrawal operations",
        "externalDocs": {
            "description": "Used by both Super Admin and Partner Admin",
            "url": "http://localhost:8000",
        },
    },
    {
        "name": "users",
        "description": "**🔄 COMMON** - User management and activity tracking",
        "externalDocs": {
            "description": "Used by both Super Admin and Partner Admin",
            "url": "http://localhost:8000",
        },
    },
    {
        "name": "transactions", 
        "description": "**🔄 COMMON** - Transaction management and monitoring",
        "externalDocs": {
            "description": "Used by both Super Admin and Partner Admin",
            "url": "http://localhost:8000",
        },
    },
    {
        "name": "analytics",
        "description": "**🔄 COMMON** - Transaction analytics and reports",
        "externalDocs": {
            "description": "Used by both Super Admin and Partner Admin",
            "url": "http://localhost:8000",
        },
    },
    # === 🌟 DEVELOPMENT & TESTING APIs ===
    {
        "name": "simple_energy_dev",
        "description": "**🌟 DEVELOPMENT** - Simple Energy Service for easy development and testing",
        "externalDocs": {
            "description": "Development API | API Docs: /api/v1/dev/docs",
            "url": "http://localhost:8000/api/v1/dev/docs",
        },
    },
    {
        "name": "test",
        "description": "**🌟 DEVELOPMENT** - Testing endpoints and utilities",
        "externalDocs": {
            "description": "Development API | API Docs: /api/v1/dev/docs",
            "url": "http://localhost:8000/api/v1/dev/docs",
        },
    },
    {
        "name": "optimization",
        "description": "**🌟 DEVELOPMENT** - Backend performance optimization and monitoring",
        "externalDocs": {
            "description": "Development API | API Docs: /api/v1/dev/docs",
            "url": "http://localhost:8000/api/v1/dev/docs",
        },
    },
    # === 🏥 SYSTEM APIs ===
    {
        "name": "health",
        "description": "**🏥 SYSTEM** - Health check endpoints",
    },
    {
        "name": "root", 
        "description": "**🏥 SYSTEM** - Root API information and role-based documentation links",
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


# 루트 경로 정보 (역할별 API 문서 안내)
@app.get("/", tags=["root"])
async def root():
    """API에 대한 기본 정보를 제공합니다."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "environment": settings.TRON_NETWORK,
        "health": "/health",
        "api_docs": {
            "super_admin": {
                "title": "🔐 Super Admin API",
                "description": "시스템 관리, 파트너 관리, 에너지 풀 관리",
                "frontend": "http://localhost:3020 (Super Admin Dashboard)",
                "docs": "/api/v1/admin/docs",
                "openapi": "/api/v1/admin/openapi.json"
            },
            "partner_admin": {
                "title": "🔗 Partner Admin API", 
                "description": "TronLink 연동, 파트너 에너지 관리, 수수료 정책",
                "frontend": "http://localhost:3030 (Partner Admin Template)",
                "docs": "/api/v1/partner/docs",
                "openapi": "/api/v1/partner/openapi.json"
            },
            "development": {
                "title": "🌟 Development API",
                "description": "Simple Energy Service, 테스트, 최적화",
                "docs": "/api/v1/dev/docs", 
                "openapi": "/api/v1/dev/openapi.json"
            },
            "complete": {
                "title": "📋 Complete API (All)",
                "description": "모든 API 엔드포인트 (개발용)",
                "docs": f"{settings.API_V1_PREFIX}/docs" if settings.DEBUG else None,
                "openapi": f"{settings.API_V1_PREFIX}/openapi.json" if settings.DEBUG else None
            }
        }
    }


# API 라우터 등록
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# === 역할별 API 문서 엔드포인트 ===
from fastapi.responses import HTMLResponse
from app.core.role_based_docs import (
    create_super_admin_openapi, 
    create_partner_admin_openapi,
    create_development_openapi
)

@app.get("/api/v1/admin/openapi.json", tags=["admin_docs"])
async def get_super_admin_openapi():
    """Super Admin 전용 OpenAPI 스키마"""
    return create_super_admin_openapi(app)

@app.get("/api/v1/admin/docs", response_class=HTMLResponse, include_in_schema=False)
async def get_super_admin_docs():
    """Super Admin 전용 Swagger UI"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🔐 Super Admin API - DantaroWallet</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css" />
        <style>
            .swagger-ui .topbar {{ display: none; }}
            .swagger-ui .info .title {{ color: #1f2937; }}
            .swagger-ui .info .title:after {{ 
                content: " 🔐 Super Admin Only"; 
                color: #dc2626; 
                font-size: 0.7em;
                border: 1px solid #dc2626;
                padding: 2px 6px;
                border-radius: 4px;
                margin-left: 10px;
            }}
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
        <script>
            const ui = SwaggerUIBundle({{
                url: '/api/v1/admin/openapi.json',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.presets.standalone
                ],
                layout: "StandaloneLayout"
            }});
        </script>
    </body>
    </html>
    """

@app.get("/api/v1/partner/openapi.json", tags=["partner_docs"])
async def get_partner_admin_openapi():
    """Partner Admin 전용 OpenAPI 스키마"""
    return create_partner_admin_openapi(app)

@app.get("/api/v1/partner/docs", response_class=HTMLResponse, include_in_schema=False)
async def get_partner_admin_docs():
    """Partner Admin 전용 Swagger UI"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🔗 Partner Admin API - DantaroWallet</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css" />
        <style>
            .swagger-ui .topbar {{ display: none; }}
            .swagger-ui .info .title {{ color: #1f2937; }}
            .swagger-ui .info .title:after {{ 
                content: " 🔗 Partner Admin Only"; 
                color: #059669; 
                font-size: 0.7em;
                border: 1px solid #059669;
                padding: 2px 6px;
                border-radius: 4px;
                margin-left: 10px;
            }}
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
        <script>
            const ui = SwaggerUIBundle({{
                url: '/api/v1/partner/openapi.json',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.presets.standalone
                ],
                layout: "StandaloneLayout"
            }});
        </script>
    </body>
    </html>
    """

@app.get("/api/v1/dev/openapi.json", tags=["dev_docs"])
async def get_development_openapi():
    """개발/테스트 전용 OpenAPI 스키마"""
    return create_development_openapi(app)

@app.get("/api/v1/dev/docs", response_class=HTMLResponse, include_in_schema=False) 
async def get_development_docs():
    """개발/테스트 전용 Swagger UI"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🌟 Development API - DantaroWallet</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css" />
        <style>
            .swagger-ui .topbar {{ display: none; }}
            .swagger-ui .info .title {{ color: #1f2937; }}
            .swagger-ui .info .title:after {{ 
                content: " 🌟 Development Only"; 
                color: #7c3aed; 
                font-size: 0.7em;
                border: 1px solid #7c3aed;
                padding: 2px 6px;
                border-radius: 4px;
                margin-left: 10px;
            }}
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
        <script>
            const ui = SwaggerUIBundle({{
                url: '/api/v1/dev/openapi.json',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.presets.standalone
                ],
                layout: "StandaloneLayout"
            }});
        </script>
    </body>
    </html>
    """


# === 공개 API 엔드포인트들 (인증 불필요) ===


@app.get("/public/providers", tags=["public"])
async def get_public_providers():
    """공급업체 목록 공개 조회 (인증 불필요)"""
    try:
        import sqlite3

        conn = sqlite3.connect("dev.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 
                id, 
                name, 
                status, 
                reliability_score, 
                min_order_size, 
                max_order_size,
                trading_fee,
                withdrawal_fee
            WHERE status = 'ONLINE'
            ORDER BY reliability_score DESC
        """
        )
        providers = cursor.fetchall()

        # 각 공급업체의 최신 가격 정보도 조회
        provider_data = []
        for provider in providers:
            cursor.execute(
                """
                WHERE provider_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            """,
                (provider[0],),
            )
            price_info = cursor.fetchone()

            provider_info = {
                "id": provider[0],
                "name": provider[1],
                "status": provider[2],
                "reliability": float(provider[3]) if provider[3] else 0.0,
                "min_order": provider[4],
                "max_order": provider[5],
                "trading_fee": float(provider[6]) if provider[6] else 0.0,
                "withdrawal_fee": float(provider[7]) if provider[7] else 0.0,
            }

            if price_info:
                provider_info.update(
                    {
                        "current_price": float(price_info[0]) if price_info[0] else 0.0,
                    }
                )

            provider_data.append(provider_info)

        conn.close()

        return {
            "success": True,
            "count": len(provider_data),
            "data": provider_data,
            "timestamp": time.time(),
        }
    except Exception as e:
        return {"success": False, "error": str(e), "timestamp": time.time()}


@app.get("/public/providers/summary", tags=["public"])
async def get_providers_summary():
    """공급업체 요약 정보 (인증 불필요)"""
    try:
        import sqlite3

        conn = sqlite3.connect("dev.db")
        cursor = conn.cursor()

        # 활성 공급업체 수
        active_count = cursor.fetchone()[0]

        # 평균 신뢰성
        cursor.execute(
            "SELECT AVG(reliability_score) FROM energy_suppliers WHERE is_active = 1"
        )
        avg_reliability = cursor.fetchone()[0] or 0.0

        # 최저 가격
        cursor.execute(
            """
            WHERE provider_id IN (
            )
        """
        )
        min_price = cursor.fetchone()[0] or 0.0

        # 총 가용 에너지
        cursor.execute(
            """
            WHERE provider_id IN (
            )
        """
        )
        total_available = cursor.fetchone()[0] or 0

        conn.close()

        return {
            "success": True,
            "summary": {
                "active_providers": active_count,
                "average_reliability": round(float(avg_reliability), 2),
                "best_price": float(min_price),
            },
            "timestamp": time.time(),
        }
    except Exception as e:
        return {"success": False, "error": str(e), "timestamp": time.time()}


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
