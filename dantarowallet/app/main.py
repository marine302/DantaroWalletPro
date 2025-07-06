"""
Main FastAPI application module for DantaroWallet.
Production-ready FastAPI application with advanced middleware, logging, and error handling.
"""
import asyncio
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
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

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

    # 입금 모니터링 백그라운드 시작 (임시 비활성화)
    # if not deposit_monitor.is_monitoring:
    #     logger.info("🔍 Starting deposit monitoring...")
    #     asyncio.create_task(deposit_monitor.start_monitoring())

    # FastAPI에게 "준비 완료" 신호 전달
    yield

    # 종료 시 작업
    logger.info("🛑 Stopping deposit monitoring...")
    # await deposit_monitor.stop_monitoring()
    logger.info(f"🛑 Shutting down {settings.APP_NAME}")


# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Hybrid USDT wallet system with multi-tenant support",
    # DEBUG 모드에서만 API 문서 노출
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json" if settings.DEBUG else None,
    docs_url=f"{settings.API_V1_PREFIX}/docs" if settings.DEBUG else None,
    redoc_url=f"{settings.API_V1_PREFIX}/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)


# CORS 설정 미들웨어 - 개발용으로 모든 origin 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3010", "http://localhost:3000", "http://127.0.0.1:3010", "http://127.0.0.1:3000", "https://localhost:3010"],  # 명시적 origin 지정
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

# 정적 파일 마운트 (CSS, JS, 이미지 등)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
