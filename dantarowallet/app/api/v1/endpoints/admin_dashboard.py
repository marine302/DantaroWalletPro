"""
메인 대시보드 API 엔드포인트
슈퍼어드민 메인 대시보드에서 사용되는 통계 데이터를 제공합니다.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_sync_db
from app.models.user import User
from app.models.partner import Partner
from app.models.transaction import Transaction
from app.models.wallet import Wallet
from app.models.energy_pool import EnergyPoolModel
from app.models.withdrawal import Withdrawal

router = APIRouter()

@router.get("/dashboard/stats")
async def get_dashboard_stats() -> Dict[str, Any]:
    """
    메인 대시보드 통계 조회 (임시 더미 데이터)
    """
    # 임시로 하드코딩된 더미 데이터 반환
    return {
        "total_partners": 5,
        "active_partners": 4,
        "total_users": 150,
        "active_users": 120,
        "total_revenue": 75000.0,
        "transactions_today": 25,
        "daily_volume": 125000.0,
        "total_energy": 1500000,
        "available_energy": 1150000,
        "total_energy_consumed": 350000,
        "total_transactions_today": 25,
        "active_wallets": 45,
        "system_health": {
            "overall_score": 95,
            "database_health": 98,
            "api_response_time": 120,
            "uptime": 99.9
        },
        "last_updated": datetime.utcnow().isoformat()
    }

@router.get("/system-health")
async def get_system_health() -> Dict[str, Any]:
    """
    시스템 헬스 상태 조회 (임시 더미 데이터)
    """
    return {
        "status": "healthy",
        "database": {
            "status": "connected",
            "response_time": 25,
            "connection_pool": {
                "active": 3,
                "idle": 7,
                "total": 10
            }
        },
        "api": {
            "status": "operational",
            "average_response_time": 120,
            "uptime": 99.9
        },
        "memory": {
            "used": 245.7,
            "total": 512.0,
            "percentage": 48.0
        },
        "disk": {
            "used": 12.3,
            "total": 50.0,
            "percentage": 24.6
        },
        "last_check": datetime.utcnow().isoformat()
    }
