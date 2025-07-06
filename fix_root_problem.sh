#!/bin/bash

# DantaroWallet 근본 문제 해결 스크립트
# 브라우저 "Error loading dashboard" 완전 해결

echo "🔧 DantaroWallet 근본 문제 해결"
echo "=================================="

# 1. 현재 상황 파악
echo "1️⃣ 현재 상황 빠른 파악"
echo "------------------------"

# 프로세스 상태
backend_running=$(pgrep -f uvicorn | wc -l)
frontend_running=$(pgrep -f next | wc -l)

echo "백엔드 프로세스: $backend_running개"
echo "프론트엔드 프로세스: $frontend_running개"

# API 기본 테스트
health_check=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:8000/health 2>/dev/null)
echo "백엔드 Health: $health_check"

frontend_check=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:3010 2>/dev/null)
echo "프론트엔드: $frontend_check"

echo ""

# 2. 사용자 및 인증 문제 해결
echo "2️⃣ 사용자 및 인증 문제 해결"
echo "-----------------------------"

echo "🔍 데이터베이스 사용자 확인..."
cd /workspaces/DantaroWalletPro/dantarowallet

user_count=$(sqlite3 test.db "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")
echo "사용자 수: $user_count"

if [ "$user_count" = "0" ]; then
    echo "❌ 사용자가 없음 - 테스트 사용자 생성"
    
    # 직접 SQL로 사용자 생성 (bcrypt 대신 간단한 해시)
    sqlite3 test.db "
    INSERT OR IGNORE INTO users (
        email, 
        password_hash, 
        is_admin, 
        is_verified, 
        is_active, 
        created_at, 
        updated_at
    ) VALUES (
        'admin@test.com',
        '\$2b\$12\$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
        1,
        1,
        1,
        datetime('now'),
        datetime('now')
    );
    "
    
    # 잔고 생성
    user_id=$(sqlite3 test.db "SELECT id FROM users WHERE email='admin@test.com';")
    if [ -n "$user_id" ]; then
        sqlite3 test.db "
        INSERT OR IGNORE INTO balances (user_id, asset, amount, locked_amount, created_at, updated_at)
        VALUES ($user_id, 'USDT', 0, 0, datetime('now'), datetime('now'));
        "
        echo "✅ 테스트 사용자 생성 완료: admin@test.com / secret"
    fi
else
    echo "✅ 사용자 존재: $user_count명"
    sqlite3 test.db "SELECT email, is_admin, is_active FROM users LIMIT 3;"
fi

echo ""

# 3. 실제 로그인 테스트
echo "3️⃣ 실제 로그인 API 테스트"
echo "-------------------------"

echo "🔍 로그인 테스트 (admin@test.com / secret)..."
login_result=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@test.com","password":"secret"}' \
    http://localhost:8000/api/v1/auth/login 2>/dev/null)

if echo "$login_result" | grep -q "access_token"; then
    echo "✅ 로그인 성공!"
    
    # 토큰 추출
    access_token=$(echo "$login_result" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$access_token" ]; then
        echo "🔍 인증 토큰으로 대시보드 API 테스트..."
        
        dashboard_result=$(curl -s -w "%{http_code}" \
            -H "Authorization: Bearer $access_token" \
            -H "Content-Type: application/json" \
            -o /tmp/dashboard_result.json \
            http://localhost:8000/api/v1/admin/dashboard/stats 2>/dev/null)
        
        dashboard_status="${dashboard_result: -3}"
        
        if [ "$dashboard_status" = "200" ]; then
            echo "✅ 대시보드 API 성공!"
            echo "응답 데이터:"
            head -5 /tmp/dashboard_result.json
        else
            echo "❌ 대시보드 API 실패: $dashboard_status"
            cat /tmp/dashboard_result.json
        fi
    fi
else
    echo "❌ 로그인 실패"
    echo "응답: $login_result"
fi

echo ""

# 4. 프론트엔드 문제 해결
echo "4️⃣ 프론트엔드 설정 확인 및 수정"
echo "-------------------------------"

env_file="/workspaces/DantaroWalletPro/frontend/super-admin-dashboard/.env.local"

echo "🔍 프론트엔드 환경 변수 확인..."
if [ -f "$env_file" ]; then
    echo "현재 설정:"
    cat "$env_file"
    
    # API URL이 올바른지 확인
    api_url=$(grep "NEXT_PUBLIC_API_BASE_URL" "$env_file" | cut -d'=' -f2)
    if curl -s --max-time 3 "$api_url/../health" > /dev/null 2>&1; then
        echo "✅ API URL 연결 가능"
    else
        echo "❌ API URL 연결 불가 - 수정 필요"
        
        # 환경 변수 수정
        cat > "$env_file" << EOF
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_ADMIN_API_BASE_URL=http://localhost:8000/api/v1/admin
EOF
        echo "✅ 환경 변수 수정 완료"
    fi
else
    echo "❌ .env.local 파일 없음 - 생성"
    cat > "$env_file" << EOF
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_ADMIN_API_BASE_URL=http://localhost:8000/api/v1/admin
EOF
    echo "✅ 환경 변수 파일 생성 완료"
fi

echo ""

# 5. 서버 재시작 (필요한 경우)
echo "5️⃣ 서버 상태 최적화"
echo "-------------------"

if [ "$health_check" != "200" ]; then
    echo "🔄 백엔드 재시작 중..."
    pkill -f uvicorn 2>/dev/null
    sleep 2
    cd /workspaces/DantaroWalletPro/dantarowallet
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend_restart.log 2>&1 &
    sleep 3
    
    new_health=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:8000/health 2>/dev/null)
    if [ "$new_health" = "200" ]; then
        echo "✅ 백엔드 재시작 성공"
    else
        echo "❌ 백엔드 재시작 실패"
        tail -5 /tmp/backend_restart.log
    fi
fi

if [ "$frontend_check" != "200" ]; then
    echo "🔄 프론트엔드 재시작 중..."
    pkill -f next 2>/dev/null
    sleep 2
    cd /workspaces/DantaroWalletPro/frontend/super-admin-dashboard
    nohup npm run dev > /tmp/frontend_restart.log 2>&1 &
    sleep 5
    
    new_frontend=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:3010 2>/dev/null)
    if [ "$new_frontend" = "200" ]; then
        echo "✅ 프론트엔드 재시작 성공"
    else
        echo "❌ 프론트엔드 재시작 실패"
        tail -5 /tmp/frontend_restart.log
    fi
fi

echo ""

# 6. 최종 검증
echo "6️⃣ 최종 전체 시스템 검증"
echo "------------------------"

echo "🔍 전체 플로우 테스트..."

# 1. 로그인
final_login=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@test.com","password":"secret"}' \
    http://localhost:8000/api/v1/auth/login 2>/dev/null)

if echo "$final_login" | grep -q "access_token"; then
    echo "✅ 로그인 성공"
    
    final_token=$(echo "$final_login" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    
    # 2. 대시보드 데이터
    final_dashboard=$(curl -s -w "%{http_code}" \
        -H "Authorization: Bearer $final_token" \
        http://localhost:8000/api/v1/admin/dashboard/stats 2>/dev/null)
    
    final_status="${final_dashboard: -3}"
    
    if [ "$final_status" = "200" ]; then
        echo "✅ 대시보드 API 성공"
    else
        echo "❌ 대시보드 API 실패: $final_status"
    fi
    
    # 3. 프론트엔드 접근
    final_frontend=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:3010 2>/dev/null)
    if [ "$final_frontend" = "200" ]; then
        echo "✅ 프론트엔드 접근 성공"
    else
        echo "❌ 프론트엔드 접근 실패"
    fi
    
else
    echo "❌ 최종 로그인 실패"
fi

echo ""
echo "🎯 해결 완료!"
echo "=================================="
echo "🌐 브라우저에서 테스트:"
echo "1. http://localhost:3010 접속"
echo "2. 로그인: admin@test.com / secret"
echo "3. 대시보드 확인"
echo ""
echo "📊 모든 API가 정상 작동하면 브라우저 오류가 해결되어야 합니다!"
