#!/bin/bash

# DantaroWallet 시스템 진단 스크립트
# 사용법: ./diagnose.sh

echo "🔍 DantaroWallet 시스템 진단 시작 $(date)"
echo "=================================================="

# 로그 파일 생성
LOG_FILE="diagnostic_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo "📋 진단 결과가 $LOG_FILE 에 저장됩니다."
echo ""

# 1. 프로세스 상태 확인
echo "1️⃣ 프로세스 상태 확인"
echo "----------------------------------------"
echo "🔍 백엔드 서버 (uvicorn) 프로세스:"
if pgrep -f "uvicorn" > /dev/null; then
    echo "✅ 백엔드 서버 실행 중"
    ps aux | grep uvicorn | grep -v grep | head -5
else
    echo "❌ 백엔드 서버 실행되지 않음"
fi

echo ""
echo "🔍 프론트엔드 서버 (next) 프로세스:"
if pgrep -f "next" > /dev/null; then
    echo "✅ 프론트엔드 서버 실행 중"
    ps aux | grep next | grep -v grep | head -5
else
    echo "❌ 프론트엔드 서버 실행되지 않음"
fi

echo ""
echo "🔍 포트 사용 현황:"
echo "포트 8000 (백엔드):"
lsof -i :8000 2>/dev/null || echo "포트 8000 사용 안됨"
echo "포트 3010 (프론트엔드):"
lsof -i :3010 2>/dev/null || echo "포트 3010 사용 안됨"

echo ""

# 2. 네트워크 연결 테스트
echo "2️⃣ 네트워크 연결 테스트"
echo "----------------------------------------"
echo "🔍 백엔드 연결 테스트:"
if curl -s --max-time 5 http://localhost:8000/health > /dev/null; then
    echo "✅ 백엔드 health 응답 정상"
    echo "응답 내용:"
    curl -s http://localhost:8000/health | jq . 2>/dev/null || curl -s http://localhost:8000/health
else
    echo "❌ 백엔드 health 응답 실패"
    echo "상세 오류:"
    curl -v http://localhost:8000/health 2>&1 | head -10
fi

echo ""
echo "🔍 프론트엔드 연결 테스트:"
if curl -s --max-time 5 http://localhost:3010 > /dev/null; then
    echo "✅ 프론트엔드 응답 정상"
else
    echo "❌ 프론트엔드 응답 실패"
    echo "상세 오류:"
    curl -v http://localhost:3010 2>&1 | head -10
fi

echo ""

# 3. API 엔드포인트 테스트
echo "3️⃣ 주요 API 엔드포인트 테스트"
echo "----------------------------------------"
API_ENDPOINTS=(
    "/health"
    "/api/v1/admin/dashboard/stats"
    "/api/v1/admin/system/health"
    "/api/v1/admin/partners"
)

for endpoint in "${API_ENDPOINTS[@]}"; do
    echo "🔍 테스트: $endpoint"
    response=$(curl -s -w "%{http_code}" -o /tmp/response.txt http://localhost:8000$endpoint)
    status_code="${response: -3}"
    
    if [ "$status_code" = "200" ] || [ "$status_code" = "401" ] || [ "$status_code" = "403" ]; then
        echo "✅ 상태 코드: $status_code (정상)"
    else
        echo "❌ 상태 코드: $status_code"
        echo "응답 내용:"
        head -3 /tmp/response.txt 2>/dev/null
    fi
    echo ""
done

# 4. CORS 설정 확인
echo "4️⃣ CORS 설정 확인"
echo "----------------------------------------"
echo "🔍 CORS preflight 테스트 (localhost:3010 → localhost:8000):"
cors_response=$(curl -s -H "Origin: http://localhost:3010" \
                     -H "Access-Control-Request-Method: GET" \
                     -H "Access-Control-Request-Headers: content-type" \
                     -X OPTIONS \
                     -w "%{http_code}" \
                     -o /tmp/cors_response.txt \
                     http://localhost:8000/api/v1/admin/partners/)

cors_status="${cors_response: -3}"

if [ "$cors_status" = "200" ]; then
    echo "✅ CORS preflight 성공"
    echo "CORS 헤더:"
    curl -s -H "Origin: http://localhost:3010" \
         -H "Access-Control-Request-Method: GET" \
         -H "Access-Control-Request-Headers: content-type" \
         -X OPTIONS \
         -v \
         http://localhost:8000/api/v1/admin/partners/ 2>&1 | grep -i "access-control" || echo "CORS 헤더 없음"
else
    echo "❌ CORS preflight 실패: $cors_status"
    cat /tmp/cors_response.txt 2>/dev/null
fi

echo ""

# 5. 로그 파일 확인
echo "5️⃣ 최근 로그 확인"
echo "----------------------------------------"
echo "🔍 백엔드 로그 (최근 10줄):"
if [ -f "/workspaces/DantaroWalletPro/logs/app.log" ]; then
    tail -10 /workspaces/DantaroWalletPro/logs/app.log
else
    echo "백엔드 로그 파일 없음"
fi

echo ""
echo "🔍 시스템 메모리 사용량:"
free -h

echo ""
echo "🔍 디스크 사용량:"
df -h | head -5

echo ""

# 6. 환경 설정 확인
echo "6️⃣ 환경 설정 확인"
echo "----------------------------------------"
echo "🔍 백엔드 환경 변수:"
if [ -f "/workspaces/DantaroWalletPro/dantarowallet/.env" ]; then
    echo "✅ .env 파일 존재"
    echo "주요 설정 (민감 정보 제외):"
    grep -E "^(DATABASE_URL|TRON_NETWORK|DEBUG|API_V1_STR)" /workspaces/DantaroWalletPro/dantarowallet/.env 2>/dev/null || echo "주요 설정 없음"
else
    echo "❌ .env 파일 없음"
fi

echo ""
echo "🔍 프론트엔드 환경 변수:"
if [ -f "/workspaces/DantaroWalletPro/frontend/super-admin-dashboard/.env.local" ]; then
    echo "✅ .env.local 파일 존재"
    echo "API 설정:"
    grep -E "^NEXT_PUBLIC_" /workspaces/DantaroWalletPro/frontend/super-admin-dashboard/.env.local 2>/dev/null || echo "API 설정 없음"
else
    echo "❌ .env.local 파일 없음"
fi

echo ""
echo "=================================================="
echo "🎯 진단 완료 $(date)"
echo "📄 전체 로그: $LOG_FILE"
echo ""

# 7. 요약 및 추천 사항
echo "📊 진단 요약"
echo "----------------------------------------"
backend_running=$(pgrep -f "uvicorn" > /dev/null && echo "1" || echo "0")
frontend_running=$(pgrep -f "next" > /dev/null && echo "1" || echo "0")
backend_responding=$(curl -s --max-time 5 http://localhost:8000/health > /dev/null && echo "1" || echo "0")
frontend_responding=$(curl -s --max-time 5 http://localhost:3010 > /dev/null && echo "1" || echo "0")

echo "백엔드 프로세스: $([ $backend_running -eq 1 ] && echo "✅ 실행중" || echo "❌ 중지됨")"
echo "프론트엔드 프로세스: $([ $frontend_running -eq 1 ] && echo "✅ 실행중" || echo "❌ 중지됨")"
echo "백엔드 응답: $([ $backend_responding -eq 1 ] && echo "✅ 정상" || echo "❌ 비정상")"
echo "프론트엔드 응답: $([ $frontend_responding -eq 1 ] && echo "✅ 정상" || echo "❌ 비정상")"

echo ""
echo "🔧 추천 조치사항:"
if [ $backend_running -eq 0 ]; then
    echo "• 백엔드 서버 시작: cd /workspaces/DantaroWalletPro/dantarowallet && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
fi

if [ $frontend_running -eq 0 ]; then
    echo "• 프론트엔드 서버 시작: cd /workspaces/DantaroWalletPro/frontend/super-admin-dashboard && npm run dev"
fi

if [ $backend_running -eq 1 ] && [ $backend_responding -eq 0 ]; then
    echo "• 백엔드는 실행 중이지만 응답하지 않음 - 재시작 필요"
fi

if [ $frontend_running -eq 1 ] && [ $frontend_responding -eq 0 ]; then
    echo "• 프론트엔드는 실행 중이지만 응답하지 않음 - 재시작 필요"
fi

echo ""
echo "🚀 이 로그를 Copilot에게 공유하면 정확한 문제 진단을 받을 수 있습니다!"
