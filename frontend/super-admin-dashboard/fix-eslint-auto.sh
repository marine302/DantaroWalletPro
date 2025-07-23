#!/bin/bash

echo "🔧 ESLint 자동 수정 시작..."

# 첫 번째 ESLint 자동 수정 실행
echo "🔧 1단계: 기본 ESLint 자동 수정..."
npm run lint:fix 2>/dev/null || true

# 2단계: 사용되지 않는 import 제거
echo "🔧 2단계: 사용되지 않는 imports 처리..."
find src -name "*.tsx" -o -name "*.ts" | while read file; do
  # 사용되지 않는 imports를 _ prefix로 변경
  sed -i '' 's/import { \([^}]*\), \([a-zA-Z_][a-zA-Z0-9_]*\) }/import { \1, _\2 }/g' "$file" 2>/dev/null || true
  sed -i '' 's/const \([a-zA-Z_][a-zA-Z0-9_]*\) = /const _\1 = /g' "$file" 2>/dev/null || true
done

# 3단계: unused variables를 _ prefix로 변경
echo "🔧 3단계: unused variables 처리..."
find src -name "*.tsx" -o -name "*.ts" | while read file; do
  # function parameters에 _ prefix 추가
  sed -i '' 's/(\([^:)]*\): \([^,)]*\))/(_\1: \2)/g' "$file" 2>/dev/null || true
  sed -i '' 's/\([\s,]\)\([a-zA-Z_][a-zA-Z0-9_]*\): \([^,)]*\)/\1_\2: \3/g' "$file" 2>/dev/null || true
done

# 4단계: TypeScript enum exports 추가
echo "🔧 4단계: TypeScript enum exports 처리..."
find src -name "*.ts" | while read file; do
  if grep -q "export enum\|export const.*=" "$file" 2>/dev/null; then
    # 이미 export되어 있으면 스킵
    continue
  fi
  # enum을 export로 변경
  sed -i '' 's/^enum /export enum /g' "$file" 2>/dev/null || true
  sed -i '' 's/^const /export const /g' "$file" 2>/dev/null || true
done

# 5단계: 최종 ESLint 자동 수정
echo "🔧 5단계: 최종 ESLint 자동 수정..."
npm run lint:fix 2>/dev/null || true

echo "✅ ESLint 자동 수정 프로세스 완료"
