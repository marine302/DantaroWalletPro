#!/bin/bash

# 프론트엔드-백엔드 연결 종합 체크 스크립트

echo "🔍 DantaroWallet 프론트엔드-백엔드 연결 상태 체크"
echo "=================================================="

# 1. 백엔드 서버 상태 체크
echo "1. 백엔드 서버 상태 체크"
echo "----------------------"

# 헬스체크
echo -n "헬스체크: "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 정상"
    curl -s http://localhost:8000/health | jq -r '"   버전: " + .version + ", 환경: " + .environment'
else
    echo "❌ 서버 응답 없음"
fi

# API 기본 경로
echo -n "API 테스트: "
if curl -s http://localhost:8000/api/v1/test > /dev/null 2>&1; then
    echo "✅ 정상"
else
    echo "❌ API 응답 없음"
fi

# WebSocket 테스트 (간단히 포트 확인)
echo -n "WebSocket 포트: "
if netstat -an | grep -q ":8000.*LISTEN"; then
    echo "✅ 8000번 포트 활성"
else
    echo "❌ 포트 비활성"
fi

echo ""

# 2. CORS 설정 체크
echo "2. CORS 설정 체크"
echo "----------------"

# OPTIONS 요청으로 CORS 헤더 확인
echo -n "CORS 헤더: "
cors_response=$(curl -s -I -X OPTIONS http://localhost:8000/api/v1/test \
    -H "Origin: http://localhost:3020" \
    -H "Access-Control-Request-Method: GET" 2>/dev/null)

if echo "$cors_response" | grep -q "Access-Control-Allow-Origin"; then
    echo "✅ CORS 활성화됨"
    echo "$cors_response" | grep "Access-Control" | sed 's/^/   /'
else
    echo "❌ CORS 헤더 없음"
fi

echo ""

# 3. 프론트엔드 확인
echo "3. 프론트엔드 확인"
echo "---------------"

# Super Admin Dashboard (포트 3020)
echo -n "Super Admin Dashboard (3020): "
if ls /Users/danielkwon/DantaroWalletPro/frontend/super-admin-dashboard/package.json > /dev/null 2>&1; then
    echo "✅ 존재"
    if netstat -an | grep -q ":3020.*LISTEN"; then
        echo "   🟢 서버 실행 중"
    else
        echo "   🔴 서버 미실행"
    fi
else
    echo "❌ 없음"
fi

# Partner Admin Template (포트 3030)
echo -n "Partner Admin Template (3030): "
if ls /Users/danielkwon/DantaroWalletPro/frontend/partner-admin-template/package.json > /dev/null 2>&1; then
    echo "✅ 존재"
    if netstat -an | grep -q ":3030.*LISTEN"; then
        echo "   🟢 서버 실행 중"
    else
        echo "   🔴 서버 미실행"
    fi
else
    echo "❌ 없음"
fi

echo ""

# 4. 주요 API 엔드포인트 체크
echo "4. 주요 API 엔드포인트 체크"
echo "------------------------"

endpoints=(
    "/health"
    "/api/v1/test"
    "/api/v1/auth/register"
    "/api/v1/wallets"
    "/api/v1/admin/dashboard/overview"
    "/docs"
)

for endpoint in "${endpoints[@]}"; do
    echo -n "$endpoint: "
    status_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000$endpoint)
    if [[ $status_code =~ ^(200|201|422|401)$ ]]; then
        echo "✅ 응답 (HTTP $status_code)"
    else
        echo "❌ 오류 (HTTP $status_code)"
    fi
done

echo ""

# 5. 데이터베이스 연결 체크
echo "5. 데이터베이스 연결 체크"
echo "----------------------"

if [ -f /Users/danielkwon/DantaroWalletPro/dantarowallet/dev.db ]; then
    echo "✅ SQLite DB 파일 존재"
    db_size=$(du -h /Users/danielkwon/DantaroWalletPro/dantarowallet/dev.db | cut -f1)
    echo "   크기: $db_size"
else
    echo "❌ DB 파일 없음"
fi

echo ""

# 6. 권장사항
echo "6. 프론트엔드 연결을 위한 권장사항"
echo "==============================="

echo "📋 체크리스트:"
echo "   ✅ 백엔드 서버 (8000) 실행 확인"
echo "   🔄 프론트엔드 서버들 시작 필요:"
echo "      - Super Admin: cd frontend/super-admin-dashboard && npm run dev"
echo "      - Partner Admin: cd frontend/partner-admin-template && npm run dev"
echo "   🔧 API 문서: http://localhost:8000/docs"
echo "   🌐 CORS 설정: 3020, 3030 포트 허용됨"

echo ""
echo "🚀 연결 테스트를 위한 다음 단계:"
echo "1. 프론트엔드 서버 시작"
echo "2. 브라우저에서 http://localhost:3020 (Super Admin) 접속"
echo "3. 브라우저에서 http://localhost:3030 (Partner Admin) 접속"
echo "4. 로그인/회원가입 기능 테스트"

echo ""
echo "=================================================="
echo "✨ 체크 완료 - $(date)"
