#!/usr/bin/env python3

import sys
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 간단한 FastAPI 앱
app = FastAPI(title="DantaroWallet Simple API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3010", "http://localhost:3000", "http://127.0.0.1:3010"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 간단한 테스트 엔드포인트
@app.get("/api/v1/test")
async def test():
    return {"message": "Simple API working", "status": "success"}

# 대시보드 통계 엔드포인트 (더미 데이터)
@app.get("/api/v1/admin/dashboard/stats")
async def get_dashboard_stats():
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
        "last_updated": "2025-07-16T12:00:00Z"
    }

# 시스템 헬스 엔드포인트
@app.get("/api/v1/admin/system-health")
async def get_system_health():
    return {
        "status": "healthy",
        "database": {
            "status": "connected",
            "response_time": 25
        },
        "api": {
            "status": "operational",
            "average_response_time": 120,
            "uptime": 99.9
        },
        "last_check": "2025-07-16T12:00:00Z"
    }

if __name__ == "__main__":
    print("🚀 Starting Simple DantaroWallet API Server...")
    print("📍 Server available at: http://localhost:8001")
    print("📚 Test endpoint: http://localhost:8001/api/v1/test")
    print("📊 Dashboard stats: http://localhost:8001/api/v1/admin/dashboard/stats")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=False,
        access_log=True,
        log_level="info"
    )
