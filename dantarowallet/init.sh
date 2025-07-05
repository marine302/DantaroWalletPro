#!/bin/bash
# DantaroWallet - 2단계 설정 스크립트

echo "🚀 DantaroWallet 2단계 설정 스크립트 실행 중..."

# 필요한 디렉토리 생성
mkdir -p logs

# 의존성 업데이트
echo "📦 의존성 설치 중..."
poetry add python-json-logger aiosqlite

# 테스트 실행
echo "🧪 테스트 실행 중..."
poetry run pytest -v

# 개발 서버 실행
echo "🌐 개발 서버 시작 중..."
echo "FastAPI 서버가 시작되면 http://localhost:8000/health 및 http://localhost:8000/api/v1/docs에 접속할 수 있습니다."
poetry run uvicorn app.main:app --reload

echo "✅ 모든 설정이 완료되었습니다."
