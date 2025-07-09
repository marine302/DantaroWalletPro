#!/bin/bash

# DantaroWallet 빠른 문제 해결 스크립트
# 사용법: ./quick_fix.sh

echo "🚀 DantaroWallet 빠른 문제 해결 도구"
echo "=================================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 진단 함수
check_status() {
    local service="$1"
    local command="$2"
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service: 정상${NC}"
        return 0
    else
        echo -e "${RED}❌ $service: 문제 발견${NC}"
        return 1
    fi
}

# 1. 현재 상태 빠른 체크
echo -e "${BLUE}📊 현재 상태 체크${NC}"
echo "----------------------------------------"

backend_ok=$(check_status "백엔드 프로세스" "pgrep -f uvicorn")
frontend_ok=$(check_status "프론트엔드 프로세스" "pgrep -f next")
backend_api_ok=$(check_status "백엔드 API" "curl -s --max-time 3 http://localhost:8000/health")
frontend_web_ok=$(check_status "프론트엔드 웹" "curl -s --max-time 3 http://localhost:3010")

echo ""

# 2. 문제별 해결 제안
echo -e "${BLUE}🔧 문제 해결 제안${NC}"
echo "----------------------------------------"

if [ $backend_ok -ne 0 ]; then
    echo -e "${YELLOW}⚡ 백엔드 시작:${NC}"
    echo "cd /workspaces/DantaroWalletPro/dantarowallet && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    echo ""
fi

if [ $frontend_ok -ne 0 ]; then
    echo -e "${YELLOW}⚡ 프론트엔드 시작:${NC}"
    echo "cd /workspaces/DantaroWalletPro/frontend/super-admin-dashboard && npm run dev"
    echo ""
fi

if [ $backend_ok -eq 0 ] && [ $backend_api_ok -ne 0 ]; then
    echo -e "${YELLOW}⚡ 백엔드 재시작 필요 (프로세스는 있지만 응답 없음):${NC}"
    echo "pkill -f uvicorn && sleep 2 && cd /workspaces/DantaroWalletPro/dantarowallet && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    echo ""
fi

# 3. 데이터베이스 문제 체크
echo -e "${BLUE}🗄️ 데이터베이스 체크${NC}"
echo "----------------------------------------"

if curl -s http://localhost:8000/health 2>/dev/null | grep -q "users.*no such table"; then
    echo -e "${RED}❌ 데이터베이스 테이블 없음${NC}"
    echo -e "${YELLOW}⚡ 데이터베이스 초기화:${NC}"
    echo "cd /workspaces/DantaroWalletPro/dantarowallet && alembic upgrade head"
    echo ""
elif [ -f "/workspaces/DantaroWalletPro/logs/app.log" ] && tail -10 /workspaces/DantaroWalletPro/logs/app.log | grep -q "no such table"; then
    echo -e "${RED}❌ 데이터베이스 테이블 없음 (로그에서 발견)${NC}"
    echo -e "${YELLOW}⚡ 데이터베이스 마이그레이션:${NC}"
    echo "cd /workspaces/DantaroWalletPro/dantarowallet && alembic upgrade head"
    echo ""
else
    echo -e "${GREEN}✅ 데이터베이스 상태 정상${NC}"
fi

# 4. 포트 충돌 체크
echo -e "${BLUE}🌐 포트 충돌 체크${NC}"
echo "----------------------------------------"

port8000=$(lsof -ti:8000 2>/dev/null | wc -l)
port3010=$(netstat -tlnp 2>/dev/null | grep :3010 | wc -l)

if [ $port8000 -gt 1 ]; then
    echo -e "${RED}❌ 포트 8000에 여러 프로세스${NC}"
    echo -e "${YELLOW}⚡ 포트 정리:${NC}"
    echo "pkill -f uvicorn && sleep 2"
    echo ""
elif [ $port8000 -eq 0 ] && [ $backend_ok -eq 0 ]; then
    echo -e "${YELLOW}⚠️ 백엔드 프로세스는 있지만 포트 8000 미사용${NC}"
    echo "프로세스 재시작 권장"
    echo ""
fi

# 5. 환경 설정 체크
echo -e "${BLUE}⚙️ 환경 설정 체크${NC}"
echo "----------------------------------------"

if [ ! -f "/workspaces/DantaroWalletPro/dantarowallet/.env" ]; then
    echo -e "${RED}❌ 백엔드 .env 파일 없음${NC}"
    echo -e "${YELLOW}⚡ .env 파일 생성 필요${NC}"
    echo ""
else
    echo -e "${GREEN}✅ 백엔드 .env 존재${NC}"
fi

if [ ! -f "/workspaces/DantaroWalletPro/frontend/super-admin-dashboard/.env.local" ]; then
    echo -e "${RED}❌ 프론트엔드 .env.local 파일 없음${NC}"
    echo -e "${YELLOW}⚡ .env.local 파일 생성 필요${NC}"
    echo ""
else
    echo -e "${GREEN}✅ 프론트엔드 .env.local 존재${NC}"
fi

# 6. 빠른 실행 명령어
echo -e "${BLUE}🚀 빠른 실행 명령어${NC}"
echo "----------------------------------------"
echo "1. 전체 시스템 재시작:"
echo "   pkill -f uvicorn; pkill -f next; sleep 3"
echo "   cd /workspaces/DantaroWalletPro/dantarowallet && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &"
echo "   cd /workspaces/DantaroWalletPro/frontend/super-admin-dashboard && npm run dev &"
echo ""

echo "2. 데이터베이스 초기화:"
echo "   cd /workspaces/DantaroWalletPro/dantarowallet && alembic upgrade head"
echo ""

echo "3. 로그 실시간 확인:"
echo "   tail -f /workspaces/DantaroWalletPro/logs/app.log"
echo ""

echo "4. 상세 진단:"
echo "   ./diagnose.sh"
echo ""

echo "5. 문제 보고:"
echo "   ./report_issue.sh \"문제 설명\""
echo ""

# 7. 자동 수정 제안
echo -e "${BLUE}🤖 자동 수정 옵션${NC}"
echo "----------------------------------------"
echo "다음 명령어들을 실행하시겠습니까?"

read -p "1. 데이터베이스 마이그레이션 실행? (y/n): " db_fix
if [ "$db_fix" = "y" ] || [ "$db_fix" = "Y" ]; then
    echo "🗄️ 데이터베이스 마이그레이션 실행 중..."
    cd /workspaces/DantaroWalletPro/dantarowallet
    if alembic upgrade head; then
        echo -e "${GREEN}✅ 데이터베이스 마이그레이션 완료${NC}"
    else
        echo -e "${RED}❌ 데이터베이스 마이그레이션 실패${NC}"
    fi
    echo ""
fi

read -p "2. 백엔드 서버 재시작? (y/n): " backend_restart
if [ "$backend_restart" = "y" ] || [ "$backend_restart" = "Y" ]; then
    echo "🔄 백엔드 서버 재시작 중..."
    pkill -f uvicorn 2>/dev/null
    sleep 2
    cd /workspaces/DantaroWalletPro/dantarowallet
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
    sleep 3
    if curl -s --max-time 3 http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✅ 백엔드 재시작 완료${NC}"
    else
        echo -e "${RED}❌ 백엔드 재시작 실패${NC}"
        echo "로그 확인: tail /tmp/backend.log"
    fi
    echo ""
fi

read -p "3. 프론트엔드 서버 재시작? (y/n): " frontend_restart
if [ "$frontend_restart" = "y" ] || [ "$frontend_restart" = "Y" ]; then
    echo "🔄 프론트엔드 서버 재시작 중..."
    pkill -f next 2>/dev/null
    sleep 2
    cd /workspaces/DantaroWalletPro/frontend/super-admin-dashboard
    nohup npm run dev > /tmp/frontend.log 2>&1 &
    sleep 5
    if curl -s --max-time 3 http://localhost:3010 > /dev/null; then
        echo -e "${GREEN}✅ 프론트엔드 재시작 완료${NC}"
    else
        echo -e "${RED}❌ 프론트엔드 재시작 실패${NC}"
        echo "로그 확인: tail /tmp/frontend.log"
    fi
    echo ""
fi

# 8. 최종 상태 확인
echo -e "${BLUE}📊 최종 상태 확인${NC}"
echo "----------------------------------------"
sleep 2

check_status "백엔드 API" "curl -s --max-time 3 http://localhost:8000/health"
check_status "프론트엔드 웹" "curl -s --max-time 3 http://localhost:3010"

echo ""
echo -e "${GREEN}🎉 빠른 수정 완료!${NC}"
echo ""
echo -e "${BLUE}💡 추가 도움이 필요하면:${NC}"
echo "- 상세 진단: ./diagnose.sh"
echo "- 문제 보고: ./report_issue.sh \"문제설명\""
echo "- 실시간 모니터링: ./monitor.sh"
