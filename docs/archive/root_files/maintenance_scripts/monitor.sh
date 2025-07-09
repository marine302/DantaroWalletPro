#!/bin/bash

# DantaroWallet 실시간 모니터링 스크립트
# 사용법: ./monitor.sh [간격_초] (기본값: 30초)

INTERVAL=${1:-30}
LOG_FILE="monitor_$(date +%Y%m%d_%H%M%S).log"

echo "🔍 DantaroWallet 실시간 모니터링 시작"
echo "📍 간격: ${INTERVAL}초, 로그: $LOG_FILE"
echo "⏹️  중지: Ctrl+C"
echo "=================================================="

# 로그 파일에도 저장
exec > >(tee -a "$LOG_FILE")
exec 2>&1

# 함수 정의
check_service() {
    local service_name="$1"
    local url="$2"
    local expected_status="$3"
    
    response=$(curl -s -w "%{http_code}" -o /dev/null --max-time 5 "$url" 2>/dev/null)
    
    if [ "$response" = "$expected_status" ] || [ "$response" = "200" ] || [ "$response" = "401" ]; then
        echo "✅ $service_name: $response"
        return 0
    else
        echo "❌ $service_name: $response (예상: $expected_status)"
        return 1
    fi
}

# 모니터링 루프
counter=1
while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo ""
    echo "📊 체크 #$counter - $timestamp"
    echo "----------------------------------------"
    
    # 프로세스 확인
    backend_proc=$(pgrep -f "uvicorn" | wc -l)
    frontend_proc=$(pgrep -f "next" | wc -l)
    
    echo "🔧 프로세스: 백엔드($backend_proc) 프론트엔드($frontend_proc)"
    
    # 서비스 응답 확인
    check_service "백엔드 Health" "http://localhost:8000/health" "200"
    check_service "백엔드 API" "http://localhost:8000/api/v1/admin/dashboard/stats" "401"
    check_service "프론트엔드" "http://localhost:3010" "200"
    
    # 메모리 사용량 (간단)
    memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    echo "💾 메모리 사용률: ${memory_usage}%"
    
    # 에러가 발생한 경우 더 자세한 정보
    if [ $? -ne 0 ]; then
        echo "⚠️  에러 감지 - 상세 정보:"
        echo "포트 사용 현황:"
        lsof -i :8000 2>/dev/null || echo "포트 8000 사용 안됨"
        lsof -i :3010 2>/dev/null || echo "포트 3010 사용 안됨"
    fi
    
    counter=$((counter + 1))
    sleep $INTERVAL
done
