#!/bin/bash

echo "🔍 DantaroWallet 시스템 진단 시작..."
echo "==============================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 백엔드 서버 상태 확인
echo -e "\n📡 백엔드 서버 상태 확인..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 백엔드 서버 정상 실행 중${NC}"
    
    # API 엔드포인트들 확인
    echo -e "\n🔍 주요 API 엔드포인트 확인..."
    endpoints=(
        "/health"
        "/api/v1/admin/dashboard/stats"
        "/api/v1/admin/system/health"
        "/api/v1/admin/partners"
        "/api/v1/admin/energy/status"
        "/api/v1/admin/fees/configs"
    )
    
    for endpoint in "${endpoints[@]}"; do
        response_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000$endpoint)
        if [ "$response_code" = "200" ] || [ "$response_code" = "401" ]; then
            echo -e "${GREEN}✅ $endpoint (${response_code})${NC}"
        else
            echo -e "${RED}❌ $endpoint (${response_code})${NC}"
        fi
    done
    
else
    echo -e "${RED}❌ 백엔드 서버 연결 실패${NC}"
    echo "🔧 해결방법: cd /workspaces/DantaroWalletPro/dantarowallet && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
fi

# 2. 프론트엔드 서버 상태 확인
echo -e "\n🌐 프론트엔드 서버 상태 확인..."
if curl -s http://localhost:3010 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 프론트엔드 서버 정상 실행 중${NC}"
else
    echo -e "${RED}❌ 프론트엔드 서버 연결 실패${NC}"
    echo "🔧 해결방법: cd /workspaces/DantaroWalletPro/frontend/super-admin-dashboard && npm run dev"
fi

# 3. CORS 설정 확인
echo -e "\n🔒 CORS 설정 확인..."
cors_headers=$(curl -s -H "Origin: http://localhost:3010" -H "Access-Control-Request-Method: GET" -X OPTIONS http://localhost:8000/api/v1/admin/partners/ -I | grep -i "access-control")
if [ ! -z "$cors_headers" ]; then
    echo -e "${GREEN}✅ CORS 헤더 정상 설정${NC}"
    echo "$cors_headers"
else
    echo -e "${RED}❌ CORS 설정 문제${NC}"
fi

# 4. 프로세스 확인
echo -e "\n🔄 실행 중인 프로세스 확인..."
echo "백엔드 프로세스:"
ps aux | grep uvicorn | grep -v grep || echo -e "${YELLOW}⚠️ uvicorn 프로세스 없음${NC}"

echo -e "\n프론트엔드 프로세스:"
ps aux | grep "next\|node.*dev" | grep -v grep || echo -e "${YELLOW}⚠️ Next.js 프로세스 없음${NC}"

# 5. 포트 사용 현황
echo -e "\n🔌 포트 사용 현황..."
echo "포트 8000 (백엔드):"
lsof -i :8000 || echo -e "${YELLOW}⚠️ 포트 8000 사용 중인 프로세스 없음${NC}"

echo -e "\n포트 3010 (프론트엔드):"
lsof -i :3010 || echo -e "${YELLOW}⚠️ 포트 3010 사용 중인 프로세스 없음${NC}"

# 6. 로그 파일 확인
echo -e "\n📝 최근 에러 로그 확인..."
if [ -f "/workspaces/DantaroWalletPro/logs/app.log" ]; then
    echo "최근 에러 로그 (마지막 10줄):"
    tail -10 /workspaces/DantaroWalletPro/logs/app.log | grep -i error || echo "최근 에러 없음"
else
    echo -e "${YELLOW}⚠️ 로그 파일 없음${NC}"
fi

echo -e "\n==============================================="
echo "🏁 진단 완료"
echo "문제가 발견되면 위의 🔧 해결방법을 참고하세요."
