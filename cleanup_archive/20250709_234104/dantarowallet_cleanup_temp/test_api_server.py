#!/usr/bin/env python3
"""
FastAPI 서버 테스트용 스크립트
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from app.main import app

if __name__ == "__main__":
    print("🚀 FastAPI 서버 시작 중...")
    print("📝 Sweep API 엔드포인트가 포함된 서버입니다.")
    print("🔗 http://127.0.0.1:8000/docs 에서 API 문서를 확인할 수 있습니다.")
    
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8000, 
        log_level="info",
        reload=False
    )
