#!/bin/bash

# 백엔드 API 요청 실시간 모니터링 스크립트

echo "🔍 백엔드 API 요청 실시간 모니터링 시작..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. 백엔드 서버 상태 확인
echo "📡 백엔드 서버 상태 확인:"
if curl -s http://localhost:8000/api/v1/test > /dev/null; then
    echo "✅ 백엔드 서버 정상 (포트 8000)"
else
    echo "❌ 백엔드 서버 응답 없음"
    exit 1
fi

# 2. 프론트엔드에서 테스트 요청 보내기
echo ""
echo "🧪 프론트엔드 시뮬레이션 테스트 요청:"

test_requests() {
    echo "$(date '+%H:%M:%S') - 기본 API 테스트"
    curl -s -w "Status: %{http_code} | Time: %{time_total}s\n" \
         -H "Origin: http://localhost:8080" \
         http://localhost:8000/api/v1/test > /dev/null
    
    echo "$(date '+%H:%M:%S') - 관리자 대시보드 요청"
    curl -s -w "Status: %{http_code} | Time: %{time_total}s\n" \
         -H "Origin: http://localhost:8080" \
         -H "Authorization: Bearer test_token" \
         http://localhost:8000/api/v1/admin/dashboard/overview > /dev/null
    
    echo "$(date '+%H:%M:%S') - 시스템 상태 요청"
    curl -s -w "Status: %{http_code} | Time: %{time_total}s\n" \
         -H "Origin: http://localhost:8080" \
         -H "Authorization: Bearer test_token" \
         http://localhost:8000/api/v1/admin/dashboard/system-health > /dev/null
}

# 3. 실시간 모니터링 시작
echo ""
echo "🔄 실시간 API 요청 모니터링 (Ctrl+C로 중지):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 10초마다 테스트 요청 보내기
while true; do
    test_requests
    echo "$(date '+%H:%M:%S') - 대기 중... (10초 후 다시 테스트)"
    echo ""
    sleep 10
done
