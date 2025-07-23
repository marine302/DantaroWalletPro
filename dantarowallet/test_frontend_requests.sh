#!/bin/bash

# 간단한 API 요청 테스트 및 응답 시간 측정

echo "🔍 프론트엔드 API 요청 시뮬레이션"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 현재 시간과 함께 요청
echo "⏰ $(date '+%Y-%m-%d %H:%M:%S')"

# 1. 기본 API 테스트
echo "📡 GET /api/v1/test"
curl -w "   → 응답시간: %{time_total}s | 상태코드: %{http_code}\n" \
     -s -o response.json \
     -H "Origin: http://localhost:8080" \
     http://localhost:8000/api/v1/test

echo "   응답: $(cat response.json)"
echo ""

# 2. 관리자 대시보드
echo "📊 GET /api/v1/admin/dashboard/overview"
curl -w "   → 응답시간: %{time_total}s | 상태코드: %{http_code}\n" \
     -s -o admin_response.json \
     -H "Origin: http://localhost:8080" \
     -H "Authorization: Bearer test_token" \
     http://localhost:8000/api/v1/admin/dashboard/overview

echo "   응답: $(cat admin_response.json | jq -r '.data.system_status // "N/A"') (총 사용자: $(cat admin_response.json | jq -r '.data.total_users // "N/A"'))"
echo ""

# 3. CORS 프리플라이트 테스트
echo "🌐 OPTIONS (CORS 프리플라이트)"
curl -w "   → 응답시간: %{time_total}s | 상태코드: %{http_code}\n" \
     -s -X OPTIONS \
     -H "Origin: http://localhost:8080" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: authorization" \
     http://localhost:8000/api/v1/admin/dashboard/overview

# 정리
rm -f response.json admin_response.json

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 테스트 완료"
