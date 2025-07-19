#!/bin/bash

# 백엔드 서버 시작 스크립트
# 가상환경을 활성화하고 백엔드 서버를 시작합니다

cd "$(dirname "$0")"

# 가상환경 활성화
echo "🔧 가상환경 활성화 중..."
source .venv/bin/activate

# Python 버전 확인
echo "🐍 Python 버전: $(python3 --version)"

# 백엔드 서버 시작
echo "🚀 백엔드 서버 시작 중..."
python3 run_server.py
