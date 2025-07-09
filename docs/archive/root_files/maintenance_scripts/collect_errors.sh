#!/bin/bash

# DantaroWallet 에러 로그 수집 스크립트
# 사용법: ./collect_errors.sh [최근_분] (기본값: 10분)

MINUTES=${1:-10}
OUTPUT_FILE="error_report_$(date +%Y%m%d_%H%M%S).txt"

echo "🚨 DantaroWallet 에러 로그 수집 (최근 ${MINUTES}분)" > "$OUTPUT_FILE"
echo "수집 시간: $(date)" >> "$OUTPUT_FILE"
echo "==================================================" >> "$OUTPUT_FILE"

# 시스템 정보
echo "" >> "$OUTPUT_FILE"
echo "📋 시스템 정보" >> "$OUTPUT_FILE"
echo "----------------------------------------" >> "$OUTPUT_FILE"
echo "OS: $(uname -a)" >> "$OUTPUT_FILE"
echo "메모리: $(free -h | grep Mem)" >> "$OUTPUT_FILE"
echo "디스크: $(df -h / | tail -1)" >> "$OUTPUT_FILE"

# 실행 중인 프로세스
echo "" >> "$OUTPUT_FILE"
echo "🔧 관련 프로세스" >> "$OUTPUT_FILE"
echo "----------------------------------------" >> "$OUTPUT_FILE"
echo "백엔드 프로세스:" >> "$OUTPUT_FILE"
ps aux | grep uvicorn | grep -v grep >> "$OUTPUT_FILE" 2>/dev/null || echo "없음" >> "$OUTPUT_FILE"
echo "프론트엔드 프로세스:" >> "$OUTPUT_FILE"
ps aux | grep next | grep -v grep >> "$OUTPUT_FILE" 2>/dev/null || echo "없음" >> "$OUTPUT_FILE"

# 포트 사용 현황
echo "" >> "$OUTPUT_FILE"
echo "🌐 포트 사용 현황" >> "$OUTPUT_FILE"
echo "----------------------------------------" >> "$OUTPUT_FILE"
echo "포트 8000:" >> "$OUTPUT_FILE"
lsof -i :8000 >> "$OUTPUT_FILE" 2>/dev/null || echo "사용 안됨" >> "$OUTPUT_FILE"
echo "포트 3010:" >> "$OUTPUT_FILE"
lsof -i :3010 >> "$OUTPUT_FILE" 2>/dev/null || echo "사용 안됨" >> "$OUTPUT_FILE"

# 최근 시스템 로그에서 에러 찾기
echo "" >> "$OUTPUT_FILE"
echo "🚨 시스템 에러 로그 (최근 ${MINUTES}분)" >> "$OUTPUT_FILE"
echo "----------------------------------------" >> "$OUTPUT_FILE"
journalctl --since="${MINUTES} minutes ago" --no-pager | grep -i error | tail -20 >> "$OUTPUT_FILE" 2>/dev/null || echo "시스템 로그 없음" >> "$OUTPUT_FILE"

# 백엔드 로그 파일
echo "" >> "$OUTPUT_FILE"
echo "🔍 백엔드 로그" >> "$OUTPUT_FILE"
echo "----------------------------------------" >> "$OUTPUT_FILE"
if [ -f "/workspaces/DantaroWalletPro/logs/app.log" ]; then
    echo "최근 백엔드 로그 (최근 50줄):" >> "$OUTPUT_FILE"
    tail -50 /workspaces/DantaroWalletPro/logs/app.log >> "$OUTPUT_FILE"
else
    echo "백엔드 로그 파일 없음" >> "$OUTPUT_FILE"
fi

# Python 에러 로그
echo "" >> "$OUTPUT_FILE"
echo "🐍 Python/FastAPI 에러" >> "$OUTPUT_FILE"
echo "----------------------------------------" >> "$OUTPUT_FILE"
if command -v journalctl &> /dev/null; then
    journalctl --since="${MINUTES} minutes ago" --no-pager | grep -E "(python|fastapi|uvicorn)" | grep -i error | tail -10 >> "$OUTPUT_FILE" 2>/dev/null || echo "Python 에러 없음" >> "$OUTPUT_FILE"
else
    echo "journalctl 사용 불가" >> "$OUTPUT_FILE"
fi

# Node.js/Next.js 에러 로그
echo "" >> "$OUTPUT_FILE"
echo "📦 Node.js/Next.js 에러" >> "$OUTPUT_FILE"
echo "----------------------------------------" >> "$OUTPUT_FILE"
if [ -d "/workspaces/DantaroWalletPro/frontend/super-admin-dashboard/.next" ]; then
    echo "Next.js 빌드 에러:" >> "$OUTPUT_FILE"
    find /workspaces/DantaroWalletPro/frontend/super-admin-dashboard/.next -name "*.log" -mmin -$MINUTES -exec cat {} \; >> "$OUTPUT_FILE" 2>/dev/null || echo "Next.js 에러 로그 없음" >> "$OUTPUT_FILE"
else
    echo "Next.js 빌드 폴더 없음" >> "$OUTPUT_FILE"
fi

# 네트워크 연결 테스트
echo "" >> "$OUTPUT_FILE"
echo "🌐 네트워크 연결 테스트" >> "$OUTPUT_FILE"
echo "----------------------------------------" >> "$OUTPUT_FILE"
echo "백엔드 연결 테스트:" >> "$OUTPUT_FILE"
timeout 5 curl -v http://localhost:8000/health >> "$OUTPUT_FILE" 2>&1 || echo "백엔드 연결 실패" >> "$OUTPUT_FILE"

echo "" >> "$OUTPUT_FILE"
echo "프론트엔드 연결 테스트:" >> "$OUTPUT_FILE"
timeout 5 curl -v http://localhost:3010 >> "$OUTPUT_FILE" 2>&1 || echo "프론트엔드 연결 실패" >> "$OUTPUT_FILE"

# CORS 테스트
echo "" >> "$OUTPUT_FILE"
echo "🔒 CORS 테스트" >> "$OUTPUT_FILE"
echo "----------------------------------------" >> "$OUTPUT_FILE"
timeout 5 curl -H "Origin: http://localhost:3010" -H "Access-Control-Request-Method: GET" -X OPTIONS -v http://localhost:8000/api/v1/admin/partners/ >> "$OUTPUT_FILE" 2>&1 || echo "CORS 테스트 실패" >> "$OUTPUT_FILE"

# 환경 설정 문제
echo "" >> "$OUTPUT_FILE"
echo "⚙️ 환경 설정" >> "$OUTPUT_FILE"
echo "----------------------------------------" >> "$OUTPUT_FILE"
echo "백엔드 .env 파일:" >> "$OUTPUT_FILE"
if [ -f "/workspaces/DantaroWalletPro/dantarowallet/.env" ]; then
    echo "존재함 - 주요 설정 (민감 정보 제외):" >> "$OUTPUT_FILE"
    grep -E "^(DATABASE_URL|TRON_NETWORK|DEBUG|API_V1_STR)" /workspaces/DantaroWalletPro/dantarowallet/.env >> "$OUTPUT_FILE" 2>/dev/null
else
    echo "없음" >> "$OUTPUT_FILE"
fi

echo "프론트엔드 .env.local 파일:" >> "$OUTPUT_FILE"
if [ -f "/workspaces/DantaroWalletPro/frontend/super-admin-dashboard/.env.local" ]; then
    echo "존재함 - API 설정:" >> "$OUTPUT_FILE"
    grep -E "^NEXT_PUBLIC_" /workspaces/DantaroWalletPro/frontend/super-admin-dashboard/.env.local >> "$OUTPUT_FILE" 2>/dev/null
else
    echo "없음" >> "$OUTPUT_FILE"
fi

# 요약
echo "" >> "$OUTPUT_FILE"
echo "📊 요약" >> "$OUTPUT_FILE"
echo "=========================================" >> "$OUTPUT_FILE"
echo "리포트 생성: $(date)" >> "$OUTPUT_FILE"
echo "파일 위치: $OUTPUT_FILE" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "🎯 이 파일을 Copilot에게 공유하여 문제 해결을 받으세요!" >> "$OUTPUT_FILE"

# 결과 출력
echo "✅ 에러 로그 수집 완료!"
echo "📄 파일: $OUTPUT_FILE"
echo ""
echo "📋 수집된 정보:"
echo "- 시스템 상태"
echo "- 프로세스 정보"
echo "- 최근 ${MINUTES}분간의 에러 로그"
echo "- 네트워크 연결 테스트"
echo "- 환경 설정 정보"
echo ""
echo "🚀 이 파일을 Copilot에게 공유하면 정확한 문제 진단을 받을 수 있습니다!"

# 파일 크기 표시
file_size=$(ls -lh "$OUTPUT_FILE" | awk '{print $5}')
echo "📊 리포트 크기: $file_size"
