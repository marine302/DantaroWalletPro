#!/usr/bin/env python3
"""
Dantaro Wallet Pro 백엔드 서버 시작 스크립트
"""
import uvicorn

if __name__ == "__main__":
    print("🚀 Dantaro Wallet Pro 백엔드 서버를 시작합니다...")
    print("📍 서버 주소: http://localhost:8000")
    print("📚 API 문서: http://localhost:8000/docs")
    print("🔌 WebSocket 엔드포인트: ws://localhost:8000/api/v1/ws/")
    print("=" * 50)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
