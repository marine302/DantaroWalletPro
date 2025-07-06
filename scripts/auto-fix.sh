#!/bin/bash

echo "🚀 DantaroWallet 자동 복구 시작..."
echo "==============================================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. 백엔드 서버 확인 및 재시작
echo -e "\n📡 백엔드 서버 확인..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ 백엔드 서버 오프라인. 재시작 중...${NC}"
    
    # 기존 프로세스 종료
    pkill -f uvicorn
    sleep 2
    
    # 새로 시작
    cd /workspaces/DantaroWalletPro/dantarowallet
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
    
    # 시작 대기
    echo "백엔드 시작 대기 중..."
    for i in {1..10}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 백엔드 서버 재시작 완료${NC}"
            break
        fi
        sleep 2
        echo "대기 중... ($i/10)"
    done
else
    echo -e "${GREEN}✅ 백엔드 서버 정상 실행 중${NC}"
fi

# 2. 프론트엔드 서버 확인 및 재시작
echo -e "\n🌐 프론트엔드 서버 확인..."
if ! curl -s http://localhost:3010 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ 프론트엔드 서버 오프라인. 재시작 중...${NC}"
    
    # 기존 프로세스 종료
    pkill -f "next dev"
    sleep 2
    
    # 새로 시작
    cd /workspaces/DantaroWalletPro/frontend/super-admin-dashboard
    nohup npm run dev > /tmp/frontend.log 2>&1 &
    
    # 시작 대기
    echo "프론트엔드 시작 대기 중..."
    for i in {1..15}; do
        if curl -s http://localhost:3010 > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 프론트엔드 서버 재시작 완료${NC}"
            break
        fi
        sleep 3
        echo "대기 중... ($i/15)"
    done
else
    echo -e "${GREEN}✅ 프론트엔드 서버 정상 실행 중${NC}"
fi

# 3. 최종 상태 확인
echo -e "\n🔍 최종 상태 확인..."
/workspaces/DantaroWalletPro/scripts/diagnose.sh

echo -e "\n🏁 자동 복구 완료"
echo "브라우저에서 http://localhost:3010 접속해보세요."
