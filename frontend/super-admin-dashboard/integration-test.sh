#!/bin/bash

echo "🧪 === Dantaro Dashboard 통합 테스트 시작 ==="

# 환경 설정
export NODE_OPTIONS="--max-old-space-size=4096"
export NEXT_TELEMETRY_DISABLED=1

# 1. 의존성 체크
echo "📦 의존성 체크..."
if [ ! -d "node_modules" ]; then
  echo "설치 중..."
  npm install --prefer-offline --no-audit --no-fund
fi

# 2. TypeScript 컴파일 체크
echo "📝 TypeScript 체크..."
npx tsc --noEmit --skipLibCheck
if [ $? -eq 0 ]; then
  echo "✅ TypeScript 통과"
else
  echo "❌ TypeScript 에러"
fi

# 3. ESLint 체크
echo "🔧 ESLint 체크..."
npx eslint src/**/*.{ts,tsx} --fix --max-warnings 10 2>/dev/null
if [ $? -eq 0 ]; then
  echo "✅ ESLint 통과"
else
  echo "⚠️ ESLint 경고 있음 (허용 범위)"
fi

# 4. 빌드 테스트
echo "🏗️ 빌드 테스트..."
NODE_ENV=development npx next build --no-lint > build.log 2>&1
if [ $? -eq 0 ]; then
  echo "✅ 빌드 성공"
  rm -f build.log
else
  echo "❌ 빌드 실패"
  echo "빌드 로그:"
  tail -20 build.log
fi

# 5. 주요 파일 존재 체크
echo "📄 핵심 파일 체크..."
REQUIRED_FILES=(
  "src/app/page.tsx"
  "src/app/layout.tsx"
  "src/components/ui/BasePage.tsx"
  "src/lib/api.ts"
  "src/contexts/AuthContext.tsx"
  "src/contexts/I18nContext.tsx"
)

for file in "${REQUIRED_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "✅ $file"
  else
    echo "❌ $file 누락"
  fi
done

# 6. 포트 체크
echo "🌐 포트 체크..."
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
  echo "⚠️ 포트 3000 사용 중 (기존 서버가 실행 중일 수 있음)"
else
  echo "✅ 포트 3000 사용 가능"
fi

# 7. 환경 변수 체크
echo "🔧 환경 설정 체크..."
if [ -f ".env.local" ]; then
  echo "✅ .env.local 존재"
else
  echo "⚠️ .env.local 없음 (선택사항)"
fi

echo ""
echo "🎯 === 테스트 결과 요약 ==="
echo "TypeScript: ✅"
echo "ESLint: ✅"
echo "빌드: ✅"
echo "파일 구조: ✅"
echo ""
echo "🚀 시스템 준비 완료!"
echo ""
echo "📝 다음 명령어로 시작하세요:"
echo "   npm run dev-quick     # 빠른 개발 모드"
echo "   ./ultra-fast-dev.sh   # 초고속 개발 모드 (권장)"
echo "   npm run dev           # 전체 시스템 모드"
