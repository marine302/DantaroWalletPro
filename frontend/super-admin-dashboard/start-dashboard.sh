#!/bin/bash

echo "🚀 Dantaro Dashboard 시작 스크립트"
echo "================================"

# 환경 설정
export NODE_OPTIONS="--max-old-space-size=4096"
export NEXT_TELEMETRY_DISABLED=1

# 포트 정리
echo "🧹 포트 3020 정리..."
lsof -ti:3020 | xargs kill -9 2>/dev/null || true

# 캐시 정리
echo "🗑️ 캐시 정리..."
rm -rf .next
rm -rf node_modules/.cache

# 개발 서버 시작
echo "🌟 개발 서버 시작 중..."
echo "   - 포트: 3020"
echo "   - 메모리: 4GB"
echo "   - URL: http://localhost:3020"
echo ""

npx next dev -p 3020
