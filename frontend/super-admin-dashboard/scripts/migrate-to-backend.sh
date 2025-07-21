#!/bin/bash

# 백엔드 API 완성 후 자동 마이그레이션 스크립트
# 사용법: ./scripts/migrate-to-backend.sh [BACKEND_URL]
# 예시: ./scripts/migrate-to-backend.sh http://localhost:8000

BACKEND_URL=${1:-"http://localhost:8000"}
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"

echo "🚀 백엔드 API 마이그레이션을 시작합니다..."
echo "📍 백엔드 URL: $BACKEND_URL"
echo ""

# 백업 디렉토리 생성
mkdir -p "$BACKUP_DIR"
echo "📦 백업 디렉토리 생성: $BACKUP_DIR"

# 1. 기존 파일들 백업
echo "💾 기존 파일 백업 중..."
cp .env.local "$BACKUP_DIR/.env.local"
cp src/services/tron-nrg-service.ts "$BACKUP_DIR/tron-nrg-service.ts"
cp src/lib/api.ts "$BACKUP_DIR/api.ts"

# 2. 환경변수 업데이트
echo "📝 환경변수 업데이트 중..."
cat > .env.local << EOF
# 백엔드 API 설정
NEXT_PUBLIC_API_BASE_URL=$BACKEND_URL
NEXT_PUBLIC_API_URL=$BACKEND_URL/api/v1
NEXT_PUBLIC_BACKEND_API_URL=$BACKEND_URL/api/v1

# WebSocket 설정 (백엔드)
NEXT_PUBLIC_WS_URL=${BACKEND_URL/http/ws}/ws
NEXT_PUBLIC_BACKEND_WS_URL=${BACKEND_URL/http/ws}/ws

# 포트 설정
NEXT_PUBLIC_FRONTEND_PORT=3020

# 개발 설정
NEXT_PUBLIC_DEBUG=true
NEXT_PUBLIC_USE_MOCK_DATA=false

# Auth 설정
NEXTAUTH_SECRET=dantaro-super-admin-secret-key-2025
NEXTAUTH_URL=http://localhost:3020
EOF

# 3. TronNRG 서비스 파일 자동 수정
echo "🔧 TronNRG 서비스 파일 수정 중..."

# baseURL 변경
sed -i '' "s|this\.baseURL = process\.env\.NEXT_PUBLIC_TRONNRG_API_URL.*|this.baseURL = (process.env.NEXT_PUBLIC_BACKEND_API_URL || '$BACKEND_URL/api/v1') + '/energy/external/tronnrg';|g" src/services/tron-nrg-service.ts

# apiKey 라인 주석 처리
sed -i '' "s|this\.apiKey = .*|// this.apiKey = 제거됨 - JWT 토큰 사용|g" src/services/tron-nrg-service.ts

# 클래스 속성에서 apiKey 제거
sed -i '' "s|private apiKey: string;|// private apiKey: string; // 제거됨|g" src/services/tron-nrg-service.ts

# X-API-Key 헤더를 Authorization 헤더로 변경
sed -i '' "s|'X-API-Key': this\.apiKey,|'Authorization': \`Bearer \${this.getAuthToken()}\`,|g" src/services/tron-nrg-service.ts

# getAuthToken 메서드 추가
TEMP_FILE=$(mktemp)
awk '
/private makeRequest/ {
    print "  /**"
    print "   * 인증 토큰 가져오기"
    print "   */"
    print "  private getAuthToken(): string {"
    print "    if (typeof window === \"undefined\") return \"\";"
    print "    return localStorage.getItem(\"accessToken\") || \"\";"
    print "  }"
    print ""
    print "  /**"
    print "   * API 요청 헬퍼 메서드"
    print "   */"
}
{print}
' src/services/tron-nrg-service.ts > "$TEMP_FILE"
mv "$TEMP_FILE" src/services/tron-nrg-service.ts

# WebSocket URL 변경
sed -i '' "s|'wss://api\.tronnrg\.com/ws'|process.env.NEXT_PUBLIC_BACKEND_WS_URL + '/energy/tronnrg' || '$BACKEND_URL/ws/energy/tronnrg'|g" src/services/tron-nrg-service.ts
sed -i '' "s|'ws://localhost:3002'|process.env.NEXT_PUBLIC_BACKEND_WS_URL + '/energy/tronnrg' || '${BACKEND_URL/http/ws}/ws/energy/tronnrg'|g" src/services/tron-nrg-service.ts

# 4. 타입스크립트 컴파일 체크
echo "🔍 타입스크립트 컴파일 체크..."
if npm run type-check; then
    echo "✅ 타입스크립트 컴파일 성공"
else
    echo "❌ 타입스크립트 컴파일 오류 발생"
    echo "🔄 백업에서 복원 중..."
    cp "$BACKUP_DIR/.env.local" .env.local
    cp "$BACKUP_DIR/tron-nrg-service.ts" src/services/tron-nrg-service.ts
    echo "❌ 마이그레이션 실패 - 백업에서 복원됨"
    exit 1
fi

# 5. 변경사항 확인
echo ""
echo "✅ 백엔드 API 마이그레이션 완료!"
echo ""
echo "📋 변경된 파일:"
echo "  - .env.local"
echo "  - src/services/tron-nrg-service.ts"
echo ""
echo "💾 백업 위치: $BACKUP_DIR"
echo ""
echo "🧪 테스트 실행:"
echo "  npm run dev"
echo ""
echo "🔗 확인할 페이지:"
echo "  http://localhost:3020/energy/external-market"
echo ""

# 6. 선택적 자동 테스트 실행
read -p "🤖 자동으로 개발 서버를 시작하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 개발 서버 시작 중..."
    npm run dev
fi
