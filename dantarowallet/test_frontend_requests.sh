#!/bin/bash

# 🚀 프론트엔드-백엔드 API 연결 테스트 스크립트
# 역할별로 구분된 API 엔드포인트 완전 테스트

BASE_URL="http://localhost:8000"
SUPER_ADMIN_PORT="3020"
PARTNER_ADMIN_PORT="3030"

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 테스트 결과 카운터
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 테스트 함수
test_api() {
    local endpoint="$1"
    local description="$2"
    local expected_status="${3:-200}"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    printf "  %-50s" "$description..."
    
    response=$(curl -s -w "%{http_code}" -o /tmp/api_response "$BASE_URL$endpoint" 2>/dev/null)
    status_code="${response: -3}"
    
    if [[ "$status_code" == "$expected_status" ]]; then
        echo -e "${GREEN}✅ PASS${NC} ($status_code)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        
        # JSON 응답인 경우 요약 표시
        if [[ "$status_code" == "200" ]] && jq . /tmp/api_response > /dev/null 2>&1; then
            echo "     $(jq -r 'if type == "object" then keys[0:3] | join(", ") else .[0:3] | map(tostring) | join(", ") end' /tmp/api_response 2>/dev/null | head -1)"
        fi
    else
        echo -e "${RED}❌ FAIL${NC} ($status_code)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        
        # 에러 내용 표시
        if [[ -s /tmp/api_response ]]; then
            echo "     Error: $(cat /tmp/api_response | head -1)"
        fi
    fi
}

# 메인 테스트 시작
echo -e "${CYAN}🚀 프론트엔드-백엔드 API 연결 완전 테스트${NC}"
echo "=================================================="

# 1. 백엔드 서버 상태 확인
echo -e "\n${BLUE}1️⃣ 백엔드 서버 상태 확인${NC}"
test_api "/health" "헬스 체크"
test_api "/" "루트 엔드포인트 (API 문서 링크)"

if [[ $FAILED_TESTS -gt 0 ]]; then
    echo -e "\n${RED}❌ 백엔드 서버가 실행되지 않고 있습니다.${NC}"
    echo "다음 명령으로 백엔드를 실행하세요: make dev-server"
    exit 1
fi

# 2. Super Admin API 테스트
echo -e "\n${BLUE}2️⃣ Super Admin API 테스트 (포트 $SUPER_ADMIN_PORT)${NC}"
echo "🔐 Super Admin 전용 API 엔드포인트"

# 에너지 관리 API
echo -e "\n${PURPLE}  ⚡ 에너지 관리 API${NC}"
test_api "/api/v1/admin/energy/status" "에너지 풀 상태"
test_api "/api/v1/admin/energy/usage-stats" "에너지 사용량 통계"
test_api "/api/v1/admin/energy/price-history" "에너지 가격 히스토리"
test_api "/api/v1/admin/energy/network-status" "네트워크 상태"
test_api "/api/v1/admin/energy/efficiency-report" "효율성 리포트"

# 파트너 관리 API
echo -e "\n${PURPLE}  👥 파트너 관리 API${NC}"
test_api "/api/v1/admin/partners" "파트너 목록"
test_api "/api/v1/admin/energy-rental/providers/status" "에너지 공급업체 상태"

# 대시보드 API
echo -e "\n${PURPLE}  📊 관리자 대시보드 API${NC}"
test_api "/api/v1/admin/dashboard/overview" "대시보드 개요"

# 수수료 관리 API
echo -e "\n${PURPLE}  💰 수수료 관리 API${NC}"
test_api "/api/v1/admin/fees/configs" "수수료 설정"

# 백업 관리 API
echo -e "\n${PURPLE}  💾 백업 관리 API${NC}"
test_api "/api/v1/admin/backups" "백업 목록"

# 3. Partner Admin API 테스트
echo -e "\n${BLUE}3️⃣ Partner Admin API 테스트 (포트 $PARTNER_ADMIN_PORT)${NC}"
echo "🔗 Partner Admin 전용 API 엔드포인트"

# TronLink API
echo -e "\n${PURPLE}  🔗 TronLink 연동 API${NC}"
test_api "/api/v1/tronlink/status" "TronLink 상태"
test_api "/api/v1/tronlink/network-info" "네트워크 정보"
test_api "/api/v1/tronlink/balance" "지갑 잔액"

# 파트너 에너지 렌탈 API
echo -e "\n${PURPLE}  ⚡ 파트너 에너지 렌탈 API${NC}"
test_api "/api/v1/partner/energy-rental/current-rates" "현재 에너지 요금"
test_api "/api/v1/partner/energy-rental/allocation" "에너지 할당량"
test_api "/api/v1/partner/energy-rental/active" "활성 렌탈"
test_api "/api/v1/partner/energy-rental/history" "렌탈 내역"

# 수수료 정책 API
echo -e "\n${PURPLE}  💰 수수료 정책 API${NC}"
test_api "/api/v1/fee-policy/current" "현재 수수료 정책"
test_api "/api/v1/fee-policy/partner-settings" "파트너 수수료 설정"

# 에너지 관리 API
echo -e "\n${PURPLE}  🎯 에너지 관리 API${NC}"
test_api "/api/v1/energy-management/pool-status" "에너지 풀 상태"
test_api "/api/v1/energy-management/optimization-suggestions" "최적화 제안"

# 4. 공통 API 테스트
echo -e "\n${BLUE}4️⃣ 공통 API 테스트${NC}"
echo "🔄 양쪽 프론트엔드에서 모두 사용하는 API"

# 인증 API
echo -e "\n${PURPLE}  🔐 인증 API${NC}"
test_api "/api/v1/auth/me" "현재 사용자 정보" 401

# 지갑 API
echo -e "\n${PURPLE}  💼 지갑 API${NC}"
test_api "/api/v1/wallet" "지갑 목록"

# 잔액 API
echo -e "\n${PURPLE}  💰 잔액 API${NC}"
test_api "/api/v1/balance" "전체 잔액"

# 거래 API
echo -e "\n${PURPLE}  📈 거래 API${NC}"
test_api "/api/v1/transactions" "거래 내역"

# 5. Simple Energy Service 테스트 (개발용)
echo -e "\n${BLUE}5️⃣ Simple Energy Service 테스트 (개발용)${NC}"
echo "🌟 개발 및 테스트용 API"

test_api "/api/v1/simple-energy/providers" "에너지 공급업체 목록"
test_api "/api/v1/simple-energy/price" "에너지 가격 정보"
test_api "/api/v1/simple-energy/quick-start" "빠른 시작 가이드"
test_api "/api/v1/simple-energy/config" "Simple Energy 설정"

# 6. API 문서 접근성 테스트
echo -e "\n${BLUE}6️⃣ API 문서 접근성 테스트${NC}"

test_api "/api/v1/admin/docs" "Super Admin API 문서"
test_api "/api/v1/partner/docs" "Partner Admin API 문서"
test_api "/api/v1/dev/docs" "개발용 API 문서"
test_api "/api/v1/docs" "전체 API 문서"

# OpenAPI JSON 테스트
echo -e "\n${PURPLE}  📄 OpenAPI JSON 테스트${NC}"
test_api "/api/v1/admin/openapi.json" "Super Admin OpenAPI"
test_api "/api/v1/partner/openapi.json" "Partner Admin OpenAPI"
test_api "/api/v1/dev/openapi.json" "개발용 OpenAPI"

# 7. WebSocket 연결 테스트
echo -e "\n${BLUE}7️⃣ WebSocket 연결 테스트${NC}"

# WebSocket 테스트는 별도 스크립트로 실행
if command -v wscat > /dev/null 2>&1; then
    echo "  🔌 WebSocket 테스트 (wscat 사용)..."
    timeout 3s wscat -c ws://localhost:8000/ws/admin/system >/dev/null 2>&1 && \
        echo -e "  ${GREEN}✅ Admin WebSocket 연결 가능${NC}" || \
        echo -e "  ${YELLOW}⚠️ Admin WebSocket 연결 실패 (정상: 인증 필요)${NC}"
    
    timeout 3s wscat -c ws://localhost:8000/ws/partner/energy >/dev/null 2>&1 && \
        echo -e "  ${GREEN}✅ Partner WebSocket 연결 가능${NC}" || \
        echo -e "  ${YELLOW}⚠️ Partner WebSocket 연결 실패 (정상: 인증 필요)${NC}"
else
    echo -e "  ${YELLOW}⚠️ wscat 미설치 - WebSocket 테스트 스킵${NC}"
    echo "    설치: npm install -g wscat"
fi

# 테스트 결과 요약
echo -e "\n${CYAN}🎉 테스트 완료!${NC}"
echo "=================================================="
echo -e "총 테스트: ${TOTAL_TESTS}"
echo -e "${GREEN}통과: ${PASSED_TESTS}${NC}"
echo -e "${RED}실패: ${FAILED_TESTS}${NC}"

if [[ $FAILED_TESTS -eq 0 ]]; then
    echo -e "\n${GREEN}✅ 모든 API가 정상적으로 작동합니다!${NC}"
else
    echo -e "\n${YELLOW}⚠️ 일부 API에 문제가 있습니다. 백엔드 로그를 확인하세요.${NC}"
fi

# 프론트엔드 개발팀 가이드
echo -e "\n${CYAN}📋 프론트엔드 개발팀 가이드:${NC}"
echo "=================================================="
echo ""
echo -e "${GREEN}🔐 Super Admin Dashboard:${NC} http://localhost:$SUPER_ADMIN_PORT"
echo "   📚 API 문서: $BASE_URL/api/v1/admin/docs"
echo "   📄 OpenAPI: $BASE_URL/api/v1/admin/openapi.json"
echo "   📁 TypeScript: frontend/super-admin-dashboard/src/lib/api-client.ts"
echo "   📝 예제 코드: frontend/super-admin-dashboard/src/examples/"
echo ""
echo -e "${GREEN}🔗 Partner Admin Template:${NC} http://localhost:$PARTNER_ADMIN_PORT"
echo "   📚 API 문서: $BASE_URL/api/v1/partner/docs"
echo "   📄 OpenAPI: $BASE_URL/api/v1/partner/openapi.json"
echo "   📁 TypeScript: frontend/partner-admin-template/src/lib/api-client.ts"
echo "   📝 예제 코드: frontend/partner-admin-template/src/examples/"
echo ""
echo -e "${GREEN}🌟 개발/테스트용 API:${NC}"
echo "   📚 API 문서: $BASE_URL/api/v1/dev/docs"
echo "   📄 OpenAPI: $BASE_URL/api/v1/dev/openapi.json"
echo ""
echo -e "${GREEN}📖 문서:${NC}"
echo "   🚀 개발 가이드: docs/FRONTEND_DEVELOPMENT_GUIDE.md"
echo "   🎯 API 참조: docs/API_REFERENCE_BY_ROLE.md"
echo "   ⚡ Simple Energy: docs/SIMPLE_ENERGY_SERVICE.md"
echo ""
echo -e "${GREEN}🔧 개발 도구:${NC}"
echo "   📊 API 문서 업데이트: make update-api-docs"
echo "   🧪 API 타입 생성: make generate-api-types"
echo "   🔍 실시간 모니터링: ./monitor_api_requests.sh"

# 정리
rm -f /tmp/api_response

exit $FAILED_TESTS
