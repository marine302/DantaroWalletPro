#!/bin/bash

# DantaroWallet 개발 환경 관리 스크립트
# 백엔드와 프론트엔드를 함께 관리합니다

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/dantarowallet"
FRONTEND_DIR="$PROJECT_ROOT/frontend/super-admin-dashboard"

function show_help() {
    echo "DantaroWallet 개발 환경 관리 스크립트"
    echo ""
    echo "사용법: $0 [명령어]"
    echo ""
    echo "명령어:"
    echo "  start-backend    백엔드 서버만 시작"
    echo "  start-frontend   프론트엔드 서버만 시작"
    echo "  start-all        백엔드와 프론트엔드 모두 시작"
    echo "  stop-all         모든 서버 중지"
    echo "  status           서버 상태 확인"
    echo "  test-api         API 연결 테스트"
    echo "  help             이 도움말 표시"
}

function start_backend() {
    echo "🚀 백엔드 서버 시작 중..."
    cd "$BACKEND_DIR"
    ./start_backend.sh &
    BACKEND_PID=$!
    echo "백엔드 PID: $BACKEND_PID"
    echo $BACKEND_PID > /tmp/dantaro_backend.pid
}

function start_frontend() {
    echo "🚀 프론트엔드 서버 시작 중..."
    cd "$FRONTEND_DIR"
    ./start_frontend.sh &
    FRONTEND_PID=$!
    echo "프론트엔드 PID: $FRONTEND_PID"
    echo $FRONTEND_PID > /tmp/dantaro_frontend.pid
}

function stop_all() {
    echo "🛑 모든 서버 중지 중..."
    
    # 백엔드 중지
    if [ -f /tmp/dantaro_backend.pid ]; then
        BACKEND_PID=$(cat /tmp/dantaro_backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            echo "백엔드 서버 중지됨 (PID: $BACKEND_PID)"
        fi
        rm -f /tmp/dantaro_backend.pid
    fi
    
    # 프론트엔드 중지
    if [ -f /tmp/dantaro_frontend.pid ]; then
        FRONTEND_PID=$(cat /tmp/dantaro_frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            echo "프론트엔드 서버 중지됨 (PID: $FRONTEND_PID)"
        fi
        rm -f /tmp/dantaro_frontend.pid
    fi
    
    # 추가로 포트를 사용하는 프로세스 확인
    echo "포트 8000과 3020을 사용하는 프로세스 확인 중..."
    lsof -ti:8000 | xargs -r kill -9 2>/dev/null || true
    lsof -ti:3020 | xargs -r kill -9 2>/dev/null || true
}

function check_status() {
    echo "📊 서버 상태 확인 중..."
    
    # 백엔드 상태
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ 백엔드: 실행 중 (http://localhost:8000)"
    else
        echo "❌ 백엔드: 중지됨"
    fi
    
    # 프론트엔드 상태
    if curl -s http://localhost:3020 > /dev/null; then
        echo "✅ 프론트엔드: 실행 중 (http://localhost:3020)"
    else
        echo "❌ 프론트엔드: 중지됨"
    fi
}

function test_api() {
    echo "🧪 API 연결 테스트 중..."
    
    # 헬스체크
    echo "백엔드 헬스체크:"
    curl -s http://localhost:8000/health | jq . || echo "헬스체크 실패"
    
    echo ""
    echo "시스템 상태:"
    curl -s http://localhost:8000/api/v1/superadmin/system-health | jq . || echo "시스템 상태 조회 실패"
    
    echo ""
    echo "대시보드 통계:"
    curl -s http://localhost:8000/api/v1/superadmin/dashboard/stats | jq . || echo "대시보드 통계 조회 실패"
}

case "$1" in
    "start-backend")
        start_backend
        ;;
    "start-frontend")
        start_frontend
        ;;
    "start-all")
        start_backend
        sleep 5  # 백엔드가 시작될 시간을 줌
        start_frontend
        ;;
    "stop-all")
        stop_all
        ;;
    "status")
        check_status
        ;;
    "test-api")
        test_api
        ;;
    "help"|"")
        show_help
        ;;
    *)
        echo "알 수 없는 명령어: $1"
        show_help
        exit 1
        ;;
esac
