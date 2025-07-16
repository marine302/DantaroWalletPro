#!/bin/bash
# 수퍼어드민 대시보드 빠른 시작 스크립트

echo "🧹 환경 정리..."
pkill -f "python3.*server" 2>/dev/null
pkill -f "uvicorn" 2>/dev/null
lsof -ti:8001 | xargs kill -9 2>/dev/null

echo "🚀 백엔드 서버 시작..."
cd /Users/danielkwon/DantaroWalletPro/dantarowallet
PYTHONPATH=/Users/danielkwon/DantaroWalletPro/dantarowallet python3 -c "
import uvicorn
from app.main import app
print('✅ 서버 시작 중...')
uvicorn.run(app, host='0.0.0.0', port=8001, log_level='error')
" > ../quick-server.log 2>&1 &

SERVER_PID=$!
echo "📍 서버 PID: $SERVER_PID"

echo "⏳ 서버 시작 대기..."
sleep 3

echo "🔍 서버 상태 확인..."
if curl -s http://localhost:8001/api/v1/test >/dev/null 2>&1; then
    echo "✅ 백엔드 서버 정상 실행 (포트 8001)"
else
    echo "❌ 백엔드 서버 실행 실패"
    exit 1
fi

echo "🌐 API 테스트..."
echo "- Test API: $(curl -s http://localhost:8001/api/v1/test | jq -r '.status' 2>/dev/null || echo 'OK')"

if curl -s http://localhost:8001/api/v1/admin/dashboard/stats >/dev/null 2>&1; then
    echo "- Admin API: ✅ 정상"
else
    echo "- Admin API: ❌ 인증 문제 또는 오류"
fi

echo "🎯 프론트엔드 확인..."
if curl -s http://localhost:3010 >/dev/null 2>&1; then
    echo "✅ 프론트엔드 서버 정상 실행 (포트 3010)"
    echo ""
    echo "🌟 준비 완료!"
    echo "   - 백엔드: http://localhost:8001"
    echo "   - 프론트엔드: http://localhost:3010"
    echo "   - 대시보드: http://localhost:3010/"
else
    echo "❌ 프론트엔드 서버 실행 필요"
    echo "다음 명령어로 프론트엔드를 시작하세요:"
    echo "cd /Users/danielkwon/DantaroWalletPro/frontend/super-admin-dashboard && npm run dev"
fi
