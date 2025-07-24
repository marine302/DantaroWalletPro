#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Dantaro Super Admin Dashboard - 개발 환경 시작${NC}"
echo "=================================================="

# 1. 포트 정리
echo -e "${YELLOW}🧹 기존 프로세스 정리 중...${NC}"
pkill -f "next dev" 2>/dev/null || true
pkill -f "mock-server.js" 2>/dev/null || true
pkill -f "mock-realtime-server.js" 2>/dev/null || true
sleep 2

# 2. Mock 서버들 시작
echo -e "${YELLOW}🔧 Mock 서버들 시작 중...${NC}"

# Mock HTTP Server
node mock-server.js &
MOCK_HTTP_PID=$!

# Mock WebSocket Server  
node mock-realtime-server.js &
MOCK_WS_PID=$!

sleep 3

# 3. Next.js 개발 서버 시작
echo -e "${YELLOW}🌐 Next.js 개발 서버 시작 중...${NC}"
npm run frontend-only &
NEXTJS_PID=$!

# 4. 서버들이 준비될 때까지 대기
echo -e "${YELLOW}⏳ 서버들이 준비될 때까지 대기 중...${NC}"
sleep 10

# 5. 서버 상태 확인
echo -e "${BLUE}📊 서버 상태 확인:${NC}"

# Next.js 서버 확인
if curl -s http://localhost:3020 > /dev/null; then
    echo -e "${GREEN}✅ Next.js (3020): 실행 중${NC}"
else
    echo -e "${RED}❌ Next.js (3020): 실행 실패${NC}"
fi

# Mock HTTP 서버 확인
if curl -s http://localhost:3001/health > /dev/null; then
    echo -e "${GREEN}✅ Mock HTTP (3001): 실행 중${NC}"
else
    echo -e "${RED}❌ Mock HTTP (3001): 실행 실패${NC}"
fi

# Mock WebSocket 서버 확인 (포트만 확인)
if netstat -an | grep -q ":3002.*LISTEN"; then
    echo -e "${GREEN}✅ Mock WebSocket (3002): 실행 중${NC}"
else
    echo -e "${RED}❌ Mock WebSocket (3002): 실행 실패${NC}"
fi

# 6. 런타임 에러 체크 (puppeteer가 설치되어 있는 경우)
echo -e "${BLUE}🔍 런타임 에러 체크:${NC}"
if command -v node > /dev/null && npm list puppeteer > /dev/null 2>&1; then
    echo -e "${YELLOW}Puppeteer로 런타임 에러 체크 중...${NC}"
    sleep 2
    node check-runtime-errors.js
else
    echo -e "${YELLOW}⚠️  Puppeteer가 설치되지 않음. 수동으로 브라우저에서 확인해주세요.${NC}"
    echo -e "${YELLOW}설치: npm install puppeteer${NC}"
fi

# 7. 최종 안내
echo -e "${BLUE}🎉 개발 환경 준비 완료!${NC}"
echo "=================================================="
echo -e "📱 Frontend: ${GREEN}http://localhost:3020${NC}"
echo -e "🔌 Mock API: ${GREEN}http://localhost:3001${NC}"
echo -e "📡 WebSocket: ${GREEN}ws://localhost:3002${NC}"
echo ""
echo -e "${YELLOW}개발을 시작하세요! 종료하려면 Ctrl+C를 누르세요.${NC}"

# 8. 종료 시그널 처리
cleanup() {
    echo -e "\n${YELLOW}🛑 서버들을 종료하는 중...${NC}"
    kill $NEXTJS_PID 2>/dev/null || true
    kill $MOCK_HTTP_PID 2>/dev/null || true  
    kill $MOCK_WS_PID 2>/dev/null || true
    pkill -f "next dev" 2>/dev/null || true
    pkill -f "mock-server.js" 2>/dev/null || true
    pkill -f "mock-realtime-server.js" 2>/dev/null || true
    echo -e "${GREEN}✅ 모든 서버가 종료되었습니다.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 9. 대기 (무한 루프)
while true; do
    sleep 1
done
