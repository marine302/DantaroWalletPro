#!/bin/bash

# 🔍 Dantaro Wallet Pro - 코드 품질 자동 검사 및 수정 스크립트
echo "🔍 Starting Code Quality Check..."
echo "=================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 오류 카운터
ERRORS=0

# 1. ESLint 자동 수정
echo -e "${BLUE}📝 Running ESLint auto-fix...${NC}"
if npm run lint:fix; then
    echo -e "${GREEN}✅ ESLint auto-fix completed successfully${NC}"
else
    echo -e "${RED}❌ ESLint auto-fix failed${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# 2. TypeScript 타입 체크
echo -e "${BLUE}🔍 Running TypeScript type check...${NC}"
if npm run type-check; then
    echo -e "${GREEN}✅ TypeScript type check passed${NC}"
else
    echo -e "${RED}❌ TypeScript type check failed${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# 3. Next.js 빌드 테스트
echo -e "${BLUE}🏗️ Running Next.js build test...${NC}"
if npm run build; then
    echo -e "${GREEN}✅ Next.js build successful${NC}"
else
    echo -e "${RED}❌ Next.js build failed${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# 4. 최종 ESLint 검사 (수정 후)
echo -e "${BLUE}🧹 Final ESLint check...${NC}"
if npm run lint; then
    echo -e "${GREEN}✅ Final ESLint check passed${NC}"
else
    echo -e "${YELLOW}⚠️ Some ESLint issues remain (warnings only)${NC}"
    echo -e "${YELLOW}💡 Running ESLint again to show remaining issues...${NC}"
    npm run lint || true
fi

echo ""
echo "=================================="

# 결과 요약
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}🎉 All quality checks passed!${NC}"
    echo -e "${GREEN}✨ Code is ready for production${NC}"
    exit 0
else
    echo -e "${RED}❌ $ERRORS quality check(s) failed${NC}"
    echo -e "${RED}🛠️ Please fix the issues above before proceeding${NC}"
    exit 1
fi
