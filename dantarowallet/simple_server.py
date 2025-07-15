#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting DantaroWallet API Server...")
    print("📍 Server will be available at: http://localhost:8001")
    print("📚 API Documentation: http://localhost:8001/api/v1/docs")
    print("🔄 Auto-reload: Disabled")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=False,
        access_log=True,
        log_level="info"
    )
