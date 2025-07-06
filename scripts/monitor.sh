#!/bin/bash

echo "🔄 DantaroWallet 실시간 모니터링 시작..."
echo "Ctrl+C로 종료하세요."
echo "==============================================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

while true; do
    clear
    echo -e "🕐 $(date)"
    echo "==============================================="
    
    # 백엔드 상태
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 백엔드: 정상${NC}"
    else
        echo -e "${RED}❌ 백엔드: 오프라인${NC}"
    fi
    
    # 프론트엔드 상태
    if curl -s http://localhost:3010 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 프론트엔드: 정상${NC}"
    else
        echo -e "${RED}❌ 프론트엔드: 오프라인${NC}"
    fi
    
    # 최근 API 요청 로그 (마지막 3개)
    echo -e "\n📊 최근 API 요청:"
    tail -3 /tmp/api_requests.log 2>/dev/null || echo "로그 없음"
    
    sleep 5
done
