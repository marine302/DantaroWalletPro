#!/bin/bash

# DantaroWallet 브라우저 오류 진단 스크립트
# 실제 프론트엔드에서 발생하는 오류들을 자동으로 체크

echo "🌐 DantaroWallet 브라우저 오류 진단"
echo "=================================================="

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="browser_error_report_${TIMESTAMP}.txt"

# 로그 파일에 출력 저장
exec > >(tee -a "$REPORT_FILE")
exec 2>&1

echo "📋 브라우저 오류 진단 보고서"
echo "생성 시간: $(date)"
echo "=================================================="

# 1. API 연결 상태 체크
echo ""
echo "1️⃣ API 연결 상태 진단"
echo "----------------------------------------"

# 대시보드 데이터 API 테스트
echo "🔍 대시보드 API 테스트:"
dashboard_response=$(curl -s -w "%{http_code}" -o /tmp/dashboard_test.json http://localhost:8000/api/v1/admin/dashboard/stats 2>/dev/null)
dashboard_status="${dashboard_response: -3}"

if [ "$dashboard_status" = "401" ]; then
    echo "✅ 대시보드 API 응답: $dashboard_status (인증 필요 - 정상)"
elif [ "$dashboard_status" = "200" ]; then
    echo "✅ 대시보드 API 응답: $dashboard_status (정상)"
    echo "응답 내용:"
    head -5 /tmp/dashboard_test.json 2>/dev/null
elif [ "$dashboard_status" = "500" ]; then
    echo "❌ 대시보드 API 응답: $dashboard_status (서버 내부 오류)"
    echo "오류 내용:"
    cat /tmp/dashboard_test.json 2>/dev/null
else
    echo "❌ 대시보드 API 응답: $dashboard_status (연결 실패)"
fi

# 프론트엔드 페이지 로드 테스트
echo ""
echo "🔍 프론트엔드 페이지 로드 테스트:"
frontend_response=$(curl -s -w "%{http_code}" -o /tmp/frontend_test.html http://localhost:3010 2>/dev/null)
frontend_status="${frontend_response: -3}"

if [ "$frontend_status" = "200" ]; then
    echo "✅ 프론트엔드 응답: $frontend_status (정상)"
    # JavaScript 에러 체크
    if grep -q "Error\|error\|Error:" /tmp/frontend_test.html 2>/dev/null; then
        echo "⚠️ HTML에서 에러 메시지 발견:"
        grep -i "error" /tmp/frontend_test.html 2>/dev/null | head -3
    fi
else
    echo "❌ 프론트엔드 응답: $frontend_status"
fi

# 2. 인증 관련 오류 체크
echo ""
echo "2️⃣ 인증 관련 오류 진단"
echo "----------------------------------------"

# 인증 없이 보호된 엔드포인트 호출 테스트
protected_endpoints=(
    "/admin/dashboard/stats"
    "/admin/system/health"
    "/admin/partners"
    "/admin/users"
)

for endpoint in "${protected_endpoints[@]}"; do
    echo "🔍 테스트: $endpoint"
    auth_response=$(curl -s -w "%{http_code}" -o /tmp/auth_test.json http://localhost:8000/api/v1$endpoint 2>/dev/null)
    auth_status="${auth_response: -3}"
    
    if [ "$auth_status" = "401" ]; then
        echo "✅ 인증 필요 응답: $auth_status (정상)"
    elif [ "$auth_status" = "403" ]; then
        echo "⚠️ 권한 없음 응답: $auth_status"
    elif [ "$auth_status" = "404" ]; then
        echo "❌ 엔드포인트 없음: $auth_status"
    elif [ "$auth_status" = "500" ]; then
        echo "❌ 서버 내부 오류: $auth_status"
        echo "오류 상세:"
        head -3 /tmp/auth_test.json 2>/dev/null
    else
        echo "❌ 예상치 못한 응답: $auth_status"
    fi
done

# 3. CORS 오류 체크
echo ""
echo "3️⃣ CORS 오류 진단"
echo "----------------------------------------"

echo "🔍 CORS preflight 테스트:"
cors_response=$(curl -s -w "%{http_code}" \
    -H "Origin: http://localhost:3010" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: content-type,authorization" \
    -X OPTIONS \
    -v \
    http://localhost:8000/api/v1/admin/dashboard/stats 2>&1)

if echo "$cors_response" | grep -q "access-control-allow-origin"; then
    echo "✅ CORS 헤더 정상"
    echo "허용된 Origin:"
    echo "$cors_response" | grep -i "access-control-allow-origin" | head -1
else
    echo "❌ CORS 헤더 누락"
    echo "CORS 응답:"
    echo "$cors_response" | grep -i "access-control" || echo "CORS 헤더 없음"
fi

# 4. 네트워크 연결 오류 체크
echo ""
echo "4️⃣ 네트워크 연결 오류 진단"
echo "----------------------------------------"

# 실제 브라우저가 호출하는 API들 테스트
browser_api_calls=(
    "http://localhost:8000/api/v1/admin/dashboard/stats"
    "http://localhost:8000/api/v1/admin/partners"
    "http://localhost:8000/api/v1/admin/system/health"
    "http://localhost:8000/health"
)

for api_url in "${browser_api_calls[@]}"; do
    echo "🔍 네트워크 테스트: $api_url"
    
    # 실제 브라우저처럼 헤더 포함해서 테스트
    network_response=$(curl -s -w "%{http_code}|%{time_total}" \
        -H "Origin: http://localhost:3010" \
        -H "User-Agent: Mozilla/5.0 (Browser Test)" \
        -H "Accept: application/json" \
        -o /tmp/network_test.json \
        "$api_url" 2>/dev/null)
    
    status_code=$(echo "$network_response" | cut -d'|' -f1)
    response_time=$(echo "$network_response" | cut -d'|' -f2)
    
    if [ "$status_code" = "000" ]; then
        echo "❌ 연결 실패 (ERR_CONNECTION_REFUSED)"
    elif [ "$status_code" = "200" ]; then
        echo "✅ 연결 성공: ${status_code} (${response_time}초)"
    elif [ "$status_code" = "401" ]; then
        echo "✅ 인증 필요: ${status_code} (${response_time}초) - 정상"
    else
        echo "⚠️ 상태 코드: ${status_code} (${response_time}초)"
        echo "응답 내용:"
        head -2 /tmp/network_test.json 2>/dev/null
    fi
done

# 5. JavaScript 런타임 오류 시뮬레이션
echo ""
echo "5️⃣ JavaScript/런타임 오류 진단"
echo "----------------------------------------"

# Next.js 빌드 상태 확인
echo "🔍 Next.js 빌드 상태 확인:"
if [ -d "/workspaces/DantaroWalletPro/frontend/super-admin-dashboard/.next" ]; then
    echo "✅ Next.js 빌드 폴더 존재"
    
    # 빌드 에러 로그 확인
    if find /workspaces/DantaroWalletPro/frontend/super-admin-dashboard/.next -name "*.log" -mmin -60 2>/dev/null | grep -q .; then
        echo "⚠️ 최근 빌드 에러 로그 발견:"
        find /workspaces/DantaroWalletPro/frontend/super-admin-dashboard/.next -name "*.log" -mmin -60 -exec tail -3 {} \; 2>/dev/null
    else
        echo "✅ 최근 빌드 에러 없음"
    fi
else
    echo "❌ Next.js 빌드 폴더 없음 - 빌드 실행 필요"
fi

# 환경 변수 확인
echo ""
echo "🔍 프론트엔드 환경 변수 확인:"
if [ -f "/workspaces/DantaroWalletPro/frontend/super-admin-dashboard/.env.local" ]; then
    echo "✅ .env.local 파일 존재"
    echo "API 설정:"
    grep "NEXT_PUBLIC_" /workspaces/DantaroWalletPro/frontend/super-admin-dashboard/.env.local 2>/dev/null
    
    # API URL 유효성 검사
    api_base_url=$(grep "NEXT_PUBLIC_API_BASE_URL" /workspaces/DantaroWalletPro/frontend/super-admin-dashboard/.env.local 2>/dev/null | cut -d'=' -f2)
    if [ -n "$api_base_url" ]; then
        echo "🔍 설정된 API URL 테스트: $api_base_url"
        if curl -s --max-time 3 "${api_base_url%/api/v1}/health" > /dev/null 2>&1; then
            echo "✅ API URL 연결 가능"
        else
            echo "❌ API URL 연결 불가"
        fi
    fi
else
    echo "❌ .env.local 파일 없음"
fi

# 6. 일반적인 브라우저 오류 패턴 체크
echo ""
echo "6️⃣ 일반적인 브라우저 오류 패턴 분석"
echo "----------------------------------------"

common_errors=(
    "Failed to fetch"
    "ERR_CONNECTION_REFUSED"
    "TypeError"
    "ReferenceError"
    "SyntaxError"
    "Network Error"
    "CORS error"
    "401"
    "403"
    "500"
)

echo "🔍 최근 로그에서 일반적인 오류 패턴 검색:"
for error_pattern in "${common_errors[@]}"; do
    if [ -f "/workspaces/DantaroWalletPro/logs/app.log" ]; then
        error_count=$(grep -c "$error_pattern" /workspaces/DantaroWalletPro/logs/app.log 2>/dev/null || echo "0")
        if [ "$error_count" -gt 0 ]; then
            echo "⚠️ '$error_pattern' 발견: ${error_count}회"
            echo "최근 사례:"
            grep "$error_pattern" /workspaces/DantaroWalletPro/logs/app.log 2>/dev/null | tail -2
        fi
    fi
done

# 7. 해결 방법 제안
echo ""
echo "7️⃣ 문제 해결 방법 제안"
echo "----------------------------------------"

if [ "$dashboard_status" != "200" ] && [ "$dashboard_status" != "401" ]; then
    echo "🔧 대시보드 API 문제 해결:"
    echo "- 백엔드 서버 재시작: pkill -f uvicorn && cd /workspaces/DantaroWalletPro/dantarowallet && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    echo "- 데이터베이스 마이그레이션: cd /workspaces/DantaroWalletPro/dantarowallet && alembic upgrade head"
fi

if [ "$frontend_status" != "200" ]; then
    echo "🔧 프론트엔드 문제 해결:"
    echo "- 프론트엔드 재시작: pkill -f next && cd /workspaces/DantaroWalletPro/frontend/super-admin-dashboard && npm run dev"
    echo "- 의존성 재설치: cd /workspaces/DantaroWalletPro/frontend/super-admin-dashboard && npm install"
fi

if ! echo "$cors_response" | grep -q "access-control-allow-origin"; then
    echo "🔧 CORS 문제 해결:"
    echo "- main.py에서 CORS 설정 확인"
    echo "- allow_origins에 'http://localhost:3010' 포함 확인"
fi

echo ""
echo "=================================================="
echo "🎯 브라우저 오류 진단 완료 $(date)"
echo "📄 상세 보고서: $REPORT_FILE"
echo ""
echo "🚀 이 보고서를 Copilot에게 공유하여 브라우저 오류를 해결하세요!"
echo ""

# 파일 크기 표시
file_size=$(ls -lh "$REPORT_FILE" | awk '{print $5}')
echo "📊 보고서 크기: $file_size"
