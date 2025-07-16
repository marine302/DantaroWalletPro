#!/bin/bash

echo "🔍 포트 8001 사용 현황 체크..."

# 포트 8001을 사용하는 프로세스 확인
PROCESS=$(lsof -ti:8001)

if [ ! -z "$PROCESS" ]; then
    echo "⚠️  포트 8001을 사용하는 프로세스 발견: $PROCESS"
    echo "🔧 프로세스 종료 중..."
    kill -9 $PROCESS
    sleep 2
    
    # 재확인
    PROCESS_AFTER=$(lsof -ti:8001)
    if [ ! -z "$PROCESS_AFTER" ]; then
        echo "❌ 프로세스 종료 실패"
        exit 1
    else
        echo "✅ 프로세스 종료 완료"
    fi
else
    echo "✅ 포트 8001 사용 가능"
fi

echo ""
echo "🚀 서버 시작 중..."

# PYTHONPATH 설정하여 서버 시작
cd /Users/danielkwon/DantaroWalletPro/dantarowallet
PYTHONPATH=/Users/danielkwon/DantaroWalletPro/dantarowallet python3 -c "
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from app.main import app
    import uvicorn
    print('✅ App imported successfully')
    print('🌐 Starting server on http://localhost:8001')
    uvicorn.run(app, host='127.0.0.1', port=8001, log_level='warning')
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
"
