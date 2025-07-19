#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.main import app
    from app.core.config import settings
    import uvicorn
    
    # 중앙화된 포트 설정 사용
    port = settings.BACKEND_PORT
    host = "127.0.0.1"
    
    print(f"🚀 서버 시작 중... (http://{host}:{port})")
    print(f"📊 대시보드: http://{host}:{port}/docs")
    
    uvicorn.run(app, host=host, port=port, log_level="warning")
    
except Exception as e:
    print(f"❌ 오류: {e}")
    import traceback
    traceback.print_exc()
