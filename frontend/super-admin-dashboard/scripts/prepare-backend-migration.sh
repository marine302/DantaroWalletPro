#!/bin/bash

# 백엔드 API 준비 후 프론트엔드 즉시 변경 스크립트
# 작성일: 2025년 7월 21일
# 목적: 백엔드 API 완성 후 프론트엔드를 즉시 백엔드 연동으로 전환

echo "🔄 백엔드 API 연동을 위한 프론트엔드 변경을 시작합니다..."

# 1. 환경변수 백업 및 업데이트
echo "📝 환경변수 업데이트 중..."
cp .env.local .env.local.backup

# 기존 TronNRG 직접 API 설정 제거하고 백엔드 API 설정 추가
cat > .env.local << 'EOF'
# 백엔드 API 설정
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000/api/v1

# WebSocket 설정 (백엔드)
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_BACKEND_WS_URL=ws://localhost:8000/ws

# 포트 설정
NEXT_PUBLIC_FRONTEND_PORT=3020

# 개발 설정
NEXT_PUBLIC_DEBUG=true
NEXT_PUBLIC_USE_MOCK_DATA=false

# Auth 설정
NEXTAUTH_SECRET=dantaro-super-admin-secret-key-2025
NEXTAUTH_URL=http://localhost:3020

# 외부 API 설정 (백엔드에서 관리 - 프론트엔드에서 제거)
# NEXT_PUBLIC_TRONNRG_API_URL=  # 백엔드에서 관리
# NEXT_PUBLIC_TRONNRG_API_KEY=  # 백엔드에서 관리
EOF

echo "✅ 환경변수 업데이트 완료"

# 2. TronNRG 서비스 파일 수정 준비
echo "🔧 TronNRG 서비스 파일 백업 생성..."
cp src/services/tron-nrg-service.ts src/services/tron-nrg-service.ts.backup

echo "📋 수정할 파일 목록:"
echo "  - .env.local (완료)"
echo "  - src/services/tron-nrg-service.ts (수동 수정 필요)"
echo "  - src/lib/api.ts (확인 필요)"
echo ""

echo "🚨 다음 단계를 수동으로 진행해주세요:"
echo ""
echo "1. src/services/tron-nrg-service.ts 수정:"
echo "   - Line 73: baseURL을 백엔드 엔드포인트로 변경"
echo "   - Line 74: apiKey 대신 JWT 토큰 사용으로 변경"
echo "   - Line 85-90: 인증 헤더를 Bearer 토큰으로 변경"
echo "   - Line 310-320: WebSocket URL을 백엔드로 변경"
echo ""
echo "2. 백엔드 API 엔드포인트 확인:"
echo "   - GET /api/v1/energy/external/tronnrg/market/price"
echo "   - GET /api/v1/energy/external/tronnrg/market/data"
echo "   - GET /api/v1/energy/external/tronnrg/providers"
echo "   - POST /api/v1/energy/external/tronnrg/order"
echo ""
echo "3. 테스트 실행:"
echo "   npm run dev"
echo "   에너지 외부 마켓 페이지 접속하여 백엔드 연동 확인"
echo ""

# 변경 필요한 라인들을 주석으로 표시
echo "📝 변경 필요한 주요 라인들을 표시합니다..."

echo ""
echo "=== src/services/tron-nrg-service.ts 수정 가이드 ==="
echo ""
echo "🔍 Line 73-74 (현재):"
echo "    this.baseURL = process.env.NEXT_PUBLIC_TRONNRG_API_URL || 'https://api.tronnrg.com/v1';"
echo "    this.apiKey = process.env.NEXT_PUBLIC_TRONNRG_API_KEY || 'demo_key';"
echo ""
echo "✅ Line 73-74 (변경 후):"
echo "    this.baseURL = process.env.NEXT_PUBLIC_BACKEND_API_URL + '/energy/external/tronnrg' || 'http://localhost:8000/api/v1/energy/external/tronnrg';"
echo "    // this.apiKey는 제거 - JWT 토큰 사용"
echo ""
echo "🔍 Line 85-90 (현재):"
echo "    const defaultHeaders = {"
echo "      'Content-Type': 'application/json',"
echo "      'X-API-Key': this.apiKey,"
echo "      'User-Agent': 'DantaroWallet-SuperAdmin/1.0'"
echo "    };"
echo ""
echo "✅ Line 85-90 (변경 후):"
echo "    const defaultHeaders = {"
echo "      'Content-Type': 'application/json',"
echo "      'Authorization': \`Bearer \${this.getAuthToken()}\`,"
echo "      'User-Agent': 'DantaroWallet-SuperAdmin/1.0'"
echo "    };"
echo ""

echo "💾 백업 파일 생성 완료:"
echo "  - .env.local.backup"
echo "  - src/services/tron-nrg-service.ts.backup"
echo ""
echo "🎯 백엔드 API 준비 완료 시 위 가이드를 참고하여 수정해주세요!"
