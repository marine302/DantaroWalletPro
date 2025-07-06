#!/bin/bash

# 테스트용 관리자 사용자 생성 스크립트
echo "👤 테스트용 관리자 사용자 생성"
echo "=================================="

# 관리자 사용자 생성 API 호출
echo "🔍 관리자 사용자 생성 중..."

# 회원가입 API 호출
signup_response=$(curl -s -w "%{http_code}" \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3010" \
  -d '{
    "email": "admin@dantarowallet.com",
    "password": "admin123456",
    "password_confirm": "admin123456"
  }' \
  -o /tmp/signup_response.json \
  http://localhost:8000/api/v1/auth/register)

signup_status="${signup_response: -3}"

echo "회원가입 응답: $signup_status"
if [ "$signup_status" = "201" ] || [ "$signup_status" = "200" ]; then
    echo "✅ 회원가입 성공"
    cat /tmp/signup_response.json | jq . 2>/dev/null || cat /tmp/signup_response.json
elif [ "$signup_status" = "400" ]; then
    echo "⚠️ 이미 존재하는 사용자이거나 잘못된 데이터"
    cat /tmp/signup_response.json
else
    echo "❌ 회원가입 실패: $signup_status"
    cat /tmp/signup_response.json
fi

echo ""

# 로그인 테스트
echo "🔍 로그인 테스트 중..."
login_response=$(curl -s -w "%{http_code}" \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3010" \
  -d '{
    "email": "admin@dantarowallet.com",
    "password": "admin123456"
  }' \
  -o /tmp/login_response.json \
  http://localhost:8000/api/v1/auth/login)

login_status="${login_response: -3}"

echo "로그인 응답: $login_status"
if [ "$login_status" = "200" ]; then
    echo "✅ 로그인 성공"
    echo "토큰 정보:"
    cat /tmp/login_response.json | jq '.access_token' 2>/dev/null || cat /tmp/login_response.json
    
    # 토큰 추출
    access_token=$(cat /tmp/login_response.json | jq -r '.access_token' 2>/dev/null)
    
    echo ""
    echo "🔍 인증된 API 테스트..."
    
    # 대시보드 API 인증 테스트
    dashboard_response=$(curl -s -w "%{http_code}" \
      -H "Authorization: Bearer $access_token" \
      -H "Origin: http://localhost:3010" \
      -o /tmp/dashboard_auth_test.json \
      http://localhost:8000/api/v1/admin/dashboard/stats)
    
    dashboard_auth_status="${dashboard_response: -3}"
    echo "인증된 대시보드 API: $dashboard_auth_status"
    if [ "$dashboard_auth_status" = "200" ]; then
        echo "✅ 인증된 API 호출 성공!"
        cat /tmp/dashboard_auth_test.json | jq . 2>/dev/null || cat /tmp/dashboard_auth_test.json
    else
        echo "❌ 인증된 API 호출 실패"
        cat /tmp/dashboard_auth_test.json
    fi
    
else
    echo "❌ 로그인 실패: $login_status"
    cat /tmp/login_response.json
fi

echo ""
echo "🎯 브라우저 테스트 가이드:"
echo "1. http://localhost:3010 에서 로그인"
echo "2. 이메일: admin@dantarowallet.com"
echo "3. 비밀번호: admin123456"
echo ""
echo "📊 사용자 확인:"
cd /workspaces/DantaroWalletPro/dantarowallet
sqlite3 test.db "SELECT email, is_admin, is_active FROM users;"
