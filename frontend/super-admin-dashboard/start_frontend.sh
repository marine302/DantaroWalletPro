#!/bin/bash

# 프론트엔드 서버 시작 스크립트
# Next.js 개발 서버를 시작합니다

cd "$(dirname "$0")"

# .env.local 파일에서 포트 읽기
FRONTEND_PORT=$(grep NEXT_PUBLIC_FRONTEND_PORT .env.local | cut -d'=' -f2)
if [ -z "$FRONTEND_PORT" ]; then
    FRONTEND_PORT=3020
fi

echo "🔧 프론트엔드 설정..."
echo "📁 현재 디렉토리: $(pwd)"
echo "🌐 포트: $FRONTEND_PORT"

# Node 버전 확인
echo "🟢 Node 버전: $(node --version)"
echo "📦 NPM 버전: $(npm --version)"

# 백엔드 연결성 확인
echo "🔍 백엔드 연결 확인 중..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 백엔드가 실행 중입니다"
else
    echo "⚠️ 백엔드가 실행되지 않았습니다. 먼저 백엔드를 시작해주세요."
fi

# 프론트엔드 서버 시작
echo "🚀 프론트엔드 서버 시작 중..."
npx next dev -p $FRONTEND_PORT
