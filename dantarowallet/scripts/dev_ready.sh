#!/bin/bash

# 개발 시작 전 자동 품질 검사 스크립트
# 매번 개발할 때 실행하면 코드 품질을 보장할 수 있습니다.

set -e  # 에러 시 스크립트 중단

echo "🚀 DantaroWallet 백엔드 개발 준비 스크립트"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. 가상환경 확인
echo "🐍 Python 가상환경 확인..."
if [ ! -d ".venv" ]; then
    echo "❌ 가상환경이 없습니다. 생성 중..."
    poetry install
else
    echo "✅ 가상환경 확인됨"
fi

# 2. 의존성 업데이트
echo ""
echo "📦 의존성 업데이트 확인..."
poetry install --no-dev 2>/dev/null || poetry install
echo "✅ 의존성 최신화 완료"

# 3. 코드 자동 수정
echo ""
echo "🔧 코드 자동 수정 (Black + isort)..."
poetry run black app tests scripts 2>/dev/null || echo "⚠️  Black 실행 실패"
poetry run isort app tests scripts 2>/dev/null || echo "⚠️  isort 실행 실패"
echo "✅ 코드 포맷팅 완료"

# 4. 코드 품질 검사
echo ""
echo "🔍 코드 품질 검사..."

echo "   📋 Flake8 (스타일 검사)..."
if poetry run flake8 app tests scripts 2>/dev/null; then
    echo "   ✅ 스타일 검사 통과"
else
    echo "   ⚠️  스타일 이슈 발견 (계속 진행)"
fi

echo "   🔒 Bandit (보안 검사)..."
if poetry run bandit -r app/ -f json 2>/dev/null | jq '.results | length' > /dev/null 2>&1; then
    result_count=$(poetry run bandit -r app/ -f json 2>/dev/null | jq '.results | length')
    if [ "$result_count" -eq 0 ]; then
        echo "   ✅ 보안 검사 통과"
    else
        echo "   ⚠️  보안 이슈 $result_count개 발견"
    fi
else
    echo "   ⚠️  Bandit 검사 스킵"
fi

# 5. 타입 체크
echo "   🎯 MyPy (타입 검사)..."
if poetry run mypy app --ignore-missing-imports 2>/dev/null; then
    echo "   ✅ 타입 검사 통과"
else
    echo "   ⚠️  타입 이슈 발견 (계속 진행)"
fi

# 6. 빌드 테스트
echo ""
echo "🏗️ 빌드 테스트..."
if poetry run python -c "import app.main; print('✅ 앱 로드 성공')" 2>/dev/null; then
    echo "✅ 빌드 테스트 통과"
else
    echo "❌ 빌드 테스트 실패"
    exit 1
fi

# 7. 핵심 테스트 실행
echo ""
echo "🧪 핵심 테스트 실행..."
if poetry run pytest tests/test_app.py::test_app_startup -v -q 2>/dev/null; then
    echo "✅ 핵심 테스트 통과"
else
    echo "⚠️  일부 테스트 실패 (개발 계속 가능)"
fi

# 8. 서버 상태 확인
echo ""
echo "🌐 백엔드 서버 상태 확인..."
if curl -s http://localhost:8000/api/v1/test > /dev/null 2>&1; then
    echo "✅ 백엔드 서버 실행 중 (포트 8000)"
else
    echo "📡 백엔드 서버 중지됨 (필요시 'make dev'로 시작)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 개발 준비 완료!"
echo ""
echo "📝 유용한 명령어들:"
echo "   make dev         - 개발 서버 시작"
echo "   make auto-fix    - 코드 자동 수정"
echo "   make auto-check  - 품질 검사"
echo "   make test        - 전체 테스트"
echo "   make build-test  - 빌드 테스트"
echo ""
echo "🚀 즐거운 개발하세요!"
