#!/bin/bash

# 브라우저 오류 빠른 체크 스크립트
echo "🌐 브라우저 오류 빠른 진단"
echo "=================================="

# 1. 대시보드 API 직접 테스트
echo "1️⃣ 대시보드 API 테스트"
echo "curl http://localhost:8000/api/v1/admin/dashboard/stats"
curl -s -w "상태: %{http_code}\n" http://localhost:8000/api/v1/admin/dashboard/stats | head -5

echo ""

# 2. 인증 토큰 없이 접근 테스트
echo "2️⃣ 인증 상태 확인"
echo "curl -H 'Origin: http://localhost:3010' http://localhost:8000/api/v1/admin/dashboard/stats"
curl -s -w "상태: %{http_code}\n" -H "Origin: http://localhost:3010" http://localhost:8000/api/v1/admin/dashboard/stats | head -3

echo ""

# 3. CORS 헤더 확인
echo "3️⃣ CORS 설정 확인"
echo "OPTIONS 요청으로 CORS 헤더 확인:"
curl -s -X OPTIONS \
  -H "Origin: http://localhost:3010" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: authorization,content-type" \
  -v http://localhost:8000/api/v1/admin/dashboard/stats 2>&1 | grep -i "access-control"

echo ""

# 4. 프론트엔드 환경 변수 확인
echo "4️⃣ 프론트엔드 환경 변수"
echo "API 베이스 URL 설정:"
grep "NEXT_PUBLIC_" /workspaces/DantaroWalletPro/frontend/super-admin-dashboard/.env.local 2>/dev/null || echo "환경 변수 파일 없음"

echo ""

# 5. 최근 백엔드 로그에서 에러 검색
echo "5️⃣ 최근 백엔드 에러 로그"
if [ -f "/workspaces/DantaroWalletPro/logs/app.log" ]; then
    echo "최근 5개 에러:"
    tail -20 /workspaces/DantaroWalletPro/logs/app.log | grep -i error | tail -5 || echo "최근 에러 없음"
else
    echo "로그 파일 없음"
fi

echo ""
echo "🎯 브라우저 오류의 가능한 원인:"
echo "- 401 응답: 인증 토큰이 없거나 만료됨"
echo "- CORS 오류: preflight 요청 실패"
echo "- 500 오류: 백엔드 서버 내부 문제"
echo "- 연결 거부: 백엔드 서버가 실행되지 않음"
