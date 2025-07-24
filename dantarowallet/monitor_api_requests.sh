#!/bin/bash

# 🔍 API 요청 실시간 모니터링
# DantaroWallet 백엔드 API 요청 실시간 추적

echo "🔍 DantaroWallet API 요청 실시간 모니터링 시작..."
echo "=============================================="
echo ""

# 로그 파일 확인
LOG_FILE="server.log"

if [[ ! -f "$LOG_FILE" ]]; then
    echo "❌ 서버 로그 파일을 찾을 수 없습니다: $LOG_FILE"
    echo "백엔드 서버가 실행 중인지 확인하세요: make dev-server"
    exit 1
fi

echo "📊 실시간 API 요청 모니터링 중..."
echo "Ctrl+C로 중지"
echo ""

# 실시간 로그 모니터링
tail -f "$LOG_FILE" | grep -E "(GET|POST|PUT|DELETE|PATCH)" --line-buffered | while read line; do
    # 타임스탬프 추출
    timestamp=$(echo "$line" | grep -o '[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}' | head -1)
    
    # HTTP 메서드와 경로 추출
    method=$(echo "$line" | grep -o -E "(GET|POST|PUT|DELETE|PATCH)" | head -1)
    path=$(echo "$line" | grep -o -E '/(api/)?[^ ]*' | head -1)
    
    # 상태 코드 추출 (있는 경우)
    status=$(echo "$line" | grep -o -E ' [0-9]{3} ' | head -1 | tr -d ' ')
    
    # 색상 설정
    case "$method" in
        GET) color="\033[0;32m" ;;      # 녹색
        POST) color="\033[0;34m" ;;     # 파란색
        PUT) color="\033[0;33m" ;;      # 노란색
        DELETE) color="\033[0;31m" ;;   # 빨간색
        PATCH) color="\033[0;35m" ;;    # 보라색
        *) color="\033[0m" ;;           # 기본색
    esac
    
    # 상태 코드별 색상
    case "$status" in
        2*) status_color="\033[0;32m" ;;  # 2xx - 녹색
        3*) status_color="\033[0;33m" ;;  # 3xx - 노란색
        4*) status_color="\033[0;31m" ;;  # 4xx - 빨간색
        5*) status_color="\033[0;31m" ;;  # 5xx - 빨간색
        *) status_color="\033[0m" ;;      # 기본색
    esac
    
    # 출력 포맷
    if [[ -n "$timestamp" && -n "$method" && -n "$path" ]]; then
        printf "${color}%s${status_color} %s${color} %s${status_color} %s\033[0m\n" \
            "[$timestamp]" "$status" "$method" "$path"
    fi
done
