#!/bin/bash

# 백엔드 API 상태 확인 및 전환 스크립트
# 사용법: ./scripts/check-backend-api.sh [start|stop|status|toggle]

BACKEND_URL="http://localhost:8000"
FRONTEND_DIR="/Users/danielkwon/DantaroWalletPro/frontend/super-admin-dashboard"

echo "🔍 백엔드 API 상태 확인 도구"
echo "================================"

# 백엔드 API 상태 확인
check_backend_status() {
    echo "📡 백엔드 API 상태 확인 중..."
    
    if curl -s --connect-timeout 3 "$BACKEND_URL/health" > /dev/null 2>&1; then
        echo "✅ 백엔드 API 정상 동작 중 ($BACKEND_URL)"
        return 0
    else
        echo "❌ 백엔드 API 연결 실패 ($BACKEND_URL)"
        return 1
    fi
}

# Mock 서버 상태 확인
check_mock_status() {
    echo "🎭 Mock 서버 상태 확인 중..."
    
    if curl -s --connect-timeout 3 "http://localhost:3001/health" > /dev/null 2>&1; then
        echo "✅ Mock 서버 정상 동작 중 (http://localhost:3001)"
        return 0
    else
        echo "❌ Mock 서버 연결 실패 (http://localhost:3001)"
        return 1
    fi
}

# 환경변수 상태 확인
check_env_status() {
    echo "⚙️ 환경변수 설정 확인..."
    
    if [ -f "$FRONTEND_DIR/.env.local" ]; then
        echo "📄 .env.local 파일 발견"
        
        # 현재 설정 표시
        echo ""
        echo "현재 설정:"
        grep -E "NEXT_PUBLIC_(USE_BACKEND_API|BACKEND_API_URL|API_URL)" "$FRONTEND_DIR/.env.local" | while read line; do
            echo "  $line"
        done
        echo ""
    else
        echo "❌ .env.local 파일을 찾을 수 없습니다"
        return 1
    fi
}

# 백엔드 API 사용 활성화
enable_backend_api() {
    echo "🔄 백엔드 API 사용 활성화 중..."
    
    if [ -f "$FRONTEND_DIR/.env.local" ]; then
        # 백업 생성
        cp "$FRONTEND_DIR/.env.local" "$FRONTEND_DIR/.env.local.backup"
        
        # 설정 변경
        sed -i '' 's/NEXT_PUBLIC_USE_BACKEND_API=false/NEXT_PUBLIC_USE_BACKEND_API=true/' "$FRONTEND_DIR/.env.local"
        
        echo "✅ 백엔드 API 사용 활성화 완료"
        echo "💡 프론트엔드를 재시작하세요: npm run dev"
    else
        echo "❌ .env.local 파일을 찾을 수 없습니다"
        return 1
    fi
}

# 백엔드 API 사용 비활성화 (Mock만 사용)
disable_backend_api() {
    echo "🔄 백엔드 API 사용 비활성화 중 (Mock 전용)..."
    
    if [ -f "$FRONTEND_DIR/.env.local" ]; then
        # 백업 생성
        cp "$FRONTEND_DIR/.env.local" "$FRONTEND_DIR/.env.local.backup"
        
        # 설정 변경
        sed -i '' 's/NEXT_PUBLIC_USE_BACKEND_API=true/NEXT_PUBLIC_USE_BACKEND_API=false/' "$FRONTEND_DIR/.env.local"
        
        echo "✅ 백엔드 API 사용 비활성화 완료 (Mock만 사용)"
        echo "💡 프론트엔드를 재시작하세요: npm run dev"
    else
        echo "❌ .env.local 파일을 찾을 수 없습니다"
        return 1
    fi
}

# API 전환 (현재 설정의 반대로 변경)
toggle_api() {
    echo "🔄 API 설정 전환 중..."
    
    if [ -f "$FRONTEND_DIR/.env.local" ]; then
        current_setting=$(grep "NEXT_PUBLIC_USE_BACKEND_API" "$FRONTEND_DIR/.env.local" | cut -d'=' -f2)
        
        if [ "$current_setting" = "true" ]; then
            disable_backend_api
        else
            enable_backend_api
        fi
    else
        echo "❌ .env.local 파일을 찾을 수 없습니다"
        return 1
    fi
}

# 전체 상태 확인
show_status() {
    echo ""
    echo "📊 전체 시스템 상태"
    echo "===================="
    
    # 백엔드 API 상태
    if check_backend_status; then
        BACKEND_STATUS="🟢 정상"
    else
        BACKEND_STATUS="🔴 오프라인"
    fi
    
    # Mock 서버 상태
    if check_mock_status; then
        MOCK_STATUS="🟢 정상"
    else
        MOCK_STATUS="🔴 오프라인"
    fi
    
    # 환경변수 설정
    if [ -f "$FRONTEND_DIR/.env.local" ]; then
        current_setting=$(grep "NEXT_PUBLIC_USE_BACKEND_API" "$FRONTEND_DIR/.env.local" | cut -d'=' -f2)
        if [ "$current_setting" = "true" ]; then
            API_SETTING="🔵 백엔드 API (Fallback: Mock)"
        else
            API_SETTING="🟡 Mock API 전용"
        fi
    else
        API_SETTING="❓ 설정 파일 없음"
    fi
    
    echo "백엔드 API:     $BACKEND_STATUS"
    echo "Mock 서버:      $MOCK_STATUS"
    echo "현재 설정:      $API_SETTING"
    echo ""
    
    # 권장사항
    if [ "$current_setting" = "true" ] && ! check_backend_status > /dev/null 2>&1; then
        echo "⚠️  백엔드 API가 활성화되어 있지만 서버가 오프라인입니다."
        echo "   Mock 서버로 자동 fallback됩니다."
    elif [ "$current_setting" != "true" ] && check_backend_status > /dev/null 2>&1; then
        echo "💡 백엔드 API가 사용 가능합니다. 활성화하려면:"
        echo "   $0 enable"
    fi
}

# 명령어 처리
case "${1:-status}" in
    "start"|"enable")
        enable_backend_api
        ;;
    "stop"|"disable")
        disable_backend_api
        ;;
    "toggle")
        toggle_api
        ;;
    "status"|*)
        show_status
        ;;
esac

echo ""
echo "🛠️ 사용법:"
echo "  $0 enable    # 백엔드 API 사용 활성화"
echo "  $0 disable   # 백엔드 API 사용 비활성화 (Mock만)"
echo "  $0 toggle    # 현재 설정 전환"
echo "  $0 status    # 전체 상태 확인 (기본값)"
