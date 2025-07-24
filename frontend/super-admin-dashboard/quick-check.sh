#!/bin/bash

# 주요 페이지들의 기본 컴파일 및 타입 체크
echo "🔍 Quick Quality Check Starting..."

# TypeScript 컴파일 체크
echo "📝 TypeScript Check..."
npx tsc --noEmit --skipLibCheck

# ESLint 기본 체크
echo "🔧 ESLint Check..."
npx eslint src/app/**/*.tsx --fix --max-warnings 0 2>/dev/null || echo "ESLint warnings present"

# Next.js 빌드 시뮬레이션 (빠른 체크)
echo "🚀 Build Check..."
NODE_ENV=development npx next build --no-lint 2>&1 | head -20

echo "✅ Quick Quality Check Complete!"
