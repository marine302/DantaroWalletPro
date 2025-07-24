#!/bin/bash
# 🎯 API 문서 업데이트 자동화 스크립트

echo "🚀 API 문서 자동 업데이트 시작..."

# 1. 서버 상태 확인
echo "📡 백엔드 서버 상태 확인..."
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ 백엔드 서버가 실행되지 않았습니다. 서버를 먼저 시작하세요."
    echo "💡 서버 시작: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    exit 1
fi

echo "✅ 백엔드 서버 정상 작동 중"

# 2. API 문서 생성
echo "📚 역할별 API 문서 생성..."
python3 scripts/generate_api_docs_by_role.py

if [ $? -eq 0 ]; then
    echo "✅ API 문서 생성 완료"
else
    echo "❌ API 문서 생성 실패"
    exit 1
fi

# 3. API 통계 출력
echo "📊 API 통계:"
curl -s http://localhost:8000/api/v1/openapi.json | jq '.paths | keys' | grep -o '/api/v1/[^/]*' | sort | uniq -c | sort -nr | head -10

# 4. 프론트엔드 타입 검증
echo "🔍 TypeScript 타입 검증..."

# Super Admin Dashboard 타입 검증
if [ -f "frontend/super-admin-dashboard/src/lib/api-classification.ts" ]; then
    echo "✅ Super Admin Dashboard API 타입 파일 존재"
else
    echo "⚠️ Super Admin Dashboard API 타입 파일 없음"
fi

# Partner Admin Template 타입 검증
if [ -f "frontend/partner-admin-template/src/lib/api-classification.ts" ]; then
    echo "✅ Partner Admin Template API 타입 파일 존재"
else
    echo "⚠️ Partner Admin Template API 타입 파일 없음"
fi

# 5. API 엔드포인트 테스트 (선택사항)
echo "🧪 주요 API 엔드포인트 테스트..."

# Health check
if curl -s http://localhost:8000/health | jq -e '.status == "healthy"' > /dev/null; then
    echo "✅ Health Check"
else
    echo "❌ Health Check 실패"
fi

# Simple Energy Service 테스트
if curl -s http://localhost:8000/api/v1/simple-energy/providers | jq -e '.success == true' > /dev/null; then
    echo "✅ Simple Energy Service"
else
    echo "❌ Simple Energy Service 실패"
fi

echo ""
echo "🎉 API 문서 업데이트 완료!"
echo ""
echo "📋 생성된 파일:"
echo "  - docs/API_REFERENCE_BY_ROLE.md"
echo "  - frontend/super-admin-dashboard/src/lib/api-classification.ts"
echo "  - frontend/partner-admin-template/src/lib/api-classification.ts"
echo ""
echo "🌐 API 문서 확인:"
echo "  - Swagger UI: http://localhost:8000/api/v1/docs"
echo "  - ReDoc: http://localhost:8000/api/v1/redoc"
echo "  - 역할별 가이드: docs/API_REFERENCE_BY_ROLE.md"
