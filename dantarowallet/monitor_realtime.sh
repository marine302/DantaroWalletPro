#!/bin/bash

# 🚀 실시간 시스템 모니터링
# DantaroWallet 백엔드 실시간 모니터링 대시보드

echo "🚀 DantaroWallet 실시간 시스템 모니터링"
echo "=========================================="

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 모니터링 함수
monitor_system() {
    while true; do
        clear
        echo -e "${BLUE}🚀 DantaroWallet 실시간 모니터링 대시보드${NC}"
        echo "=========================================="
        echo "$(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        
        # 백엔드 서버 상태
        echo -e "${GREEN}🔍 백엔드 서버 상태:${NC}"
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "   ✅ 백엔드 서버: ${GREEN}정상${NC}"
            health_data=$(curl -s http://localhost:8000/health)
            echo "   📊 상태: $(echo $health_data | jq -r '.status // "unknown"')"
            echo "   📱 환경: $(echo $health_data | jq -r '.environment // "unknown"')"
        else
            echo -e "   ❌ 백엔드 서버: ${RED}오프라인${NC}"
        fi
        echo ""
        
        # API 응답 시간 테스트
        echo -e "${GREEN}⚡ API 응답 시간:${NC}"
        start_time=$(date +%s%N)
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            end_time=$(date +%s%N)
            response_time=$(( (end_time - start_time) / 1000000 ))
            if [ $response_time -lt 100 ]; then
                echo -e "   ⚡ 응답시간: ${GREEN}${response_time}ms${NC}"
            elif [ $response_time -lt 500 ]; then
                echo -e "   ⚠️  응답시간: ${YELLOW}${response_time}ms${NC}"
            else
                echo -e "   🐌 응답시간: ${RED}${response_time}ms${NC}"
            fi
        else
            echo -e "   ❌ 응답없음: ${RED}서버 오프라인${NC}"
        fi
        echo ""
        
        # 시스템 리소스
        echo -e "${GREEN}💻 시스템 리소스:${NC}"
        
        # CPU 사용률 (macOS용)
        cpu_usage=$(top -l 1 -s 0 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
        if [ ! -z "$cpu_usage" ]; then
            echo "   🔧 CPU 사용률: ${cpu_usage}%"
        fi
        
        # 메모리 사용률
        memory_info=$(vm_stat)
        pages_free=$(echo "$memory_info" | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
        pages_active=$(echo "$memory_info" | grep "Pages active" | awk '{print $3}' | sed 's/\.//')
        pages_inactive=$(echo "$memory_info" | grep "Pages inactive" | awk '{print $3}' | sed 's/\.//')
        pages_wired=$(echo "$memory_info" | grep "Pages wired down" | awk '{print $4}' | sed 's/\.//')
        
        if [ ! -z "$pages_free" ] && [ ! -z "$pages_active" ]; then
            total_pages=$((pages_free + pages_active + pages_inactive + pages_wired))
            used_pages=$((pages_active + pages_inactive + pages_wired))
            memory_usage=$(( (used_pages * 100) / total_pages ))
            echo "   💾 메모리 사용률: ${memory_usage}%"
        fi
        
        # 디스크 사용률
        disk_usage=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
        echo "   💽 디스크 사용률: ${disk_usage}%"
        echo ""
        
        # 최근 API 요청 (로그가 있는 경우)
        echo -e "${GREEN}📡 최근 API 요청 (최근 5개):${NC}"
        if [ -f "server.log" ]; then
            tail -5 server.log | grep -E "(GET|POST|PUT|DELETE)" | while read line; do
                method=$(echo "$line" | grep -o -E "(GET|POST|PUT|DELETE)" | head -1)
                path=$(echo "$line" | grep -o -E '/[^ ]*' | head -1)
                time=$(echo "$line" | grep -o -E '[0-9]{2}:[0-9]{2}:[0-9]{2}' | head -1)
                
                case "$method" in
                    GET) method_color="${GREEN}" ;;
                    POST) method_color="${BLUE}" ;;
                    PUT) method_color="${YELLOW}" ;;
                    DELETE) method_color="${RED}" ;;
                    *) method_color="${NC}" ;;
                esac
                
                if [ ! -z "$method" ] && [ ! -z "$path" ]; then
                    printf "   ${method_color}%s${NC} %s %s\n" "$method" "$path" "$time"
                fi
            done
        else
            echo "   📝 로그 파일 없음 (server.log)"
        fi
        echo ""
        
        echo -e "${YELLOW}🔄 5초마다 자동 새로고침 | Ctrl+C로 종료${NC}"
        sleep 5
    done
}

# 트랩 설정 (Ctrl+C 시 정리)
trap 'echo -e "\n${GREEN}✅ 모니터링 종료${NC}"; exit 0' INT

# 모니터링 시작
monitor_system
