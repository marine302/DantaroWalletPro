#!/bin/bash

# DantaroWallet 문제 보고 통합 스크립트
# 사용법: ./report_issue.sh [문제설명]

ISSUE_DESC="${1:-일반적인 문제}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="reports/${TIMESTAMP}"

echo "🚨 DantaroWallet 문제 보고 생성기"
echo "문제 설명: $ISSUE_DESC"
echo "=================================================="

# 보고서 디렉토리 생성
mkdir -p "$REPORT_DIR"

echo "📁 보고서 폴더 생성: $REPORT_DIR"

# 1. 전체 시스템 진단 실행
echo "🔍 1단계: 전체 시스템 진단 실행 중..."
./diagnose.sh > "$REPORT_DIR/system_diagnosis.log" 2>&1
echo "✅ 시스템 진단 완료: $REPORT_DIR/system_diagnosis.log"

# 2. 에러 로그 수집
echo "🚨 2단계: 에러 로그 수집 중..."
./collect_errors.sh 15 > "$REPORT_DIR/error_collection.log" 2>&1
mv error_report_*.txt "$REPORT_DIR/" 2>/dev/null || true
echo "✅ 에러 로그 수집 완료"

# 3. 현재 상태 스냅샷
echo "📸 3단계: 현재 상태 스냅샷 생성 중..."
{
    echo "=== 문제 보고 스냅샷 ==="
    echo "생성 시간: $(date)"
    echo "문제 설명: $ISSUE_DESC"
    echo ""
    
    echo "=== 프로세스 상태 ==="
    ps aux | grep -E "(uvicorn|next)" | grep -v grep
    echo ""
    
    echo "=== 포트 사용 현황 ==="
    lsof -i :8000 2>/dev/null || echo "포트 8000 사용 안됨"
    lsof -i :3010 2>/dev/null || echo "포트 3010 사용 안됨"
    echo ""
    
    echo "=== 즉시 API 테스트 ==="
    echo "백엔드 health:"
    curl -s --max-time 3 http://localhost:8000/health 2>&1 || echo "실패"
    echo ""
    echo "프론트엔드:"
    curl -s --max-time 3 -I http://localhost:3010 2>&1 | head -3 || echo "실패"
    echo ""
    
    echo "=== 최근 백엔드 로그 (마지막 5줄) ==="
    tail -5 /workspaces/DantaroWalletPro/logs/app.log 2>/dev/null || echo "로그 없음"
    echo ""
    
    echo "=== 시스템 리소스 ==="
    echo "메모리:"
    free -h | grep Mem
    echo "디스크:"
    df -h / | tail -1
    echo ""
    
} > "$REPORT_DIR/snapshot.txt"

echo "✅ 스냅샷 생성 완료: $REPORT_DIR/snapshot.txt"

# 4. 브라우저 테스트 스크립트 생성
echo "🌐 4단계: 브라우저 테스트 가이드 생성 중..."
{
    echo "=== 브라우저 테스트 가이드 ==="
    echo "문제 재현을 위한 브라우저 테스트 단계:"
    echo ""
    echo "1. 브라우저에서 http://localhost:3010 접속"
    echo "2. 개발자 도구 열기 (F12)"
    echo "3. Network 탭 확인"
    echo "4. Console 탭에서 에러 메시지 확인"
    echo "5. 로그인 시도 및 API 호출 확인"
    echo ""
    echo "주요 확인 사항:"
    echo "- CORS 에러 여부"
    echo "- 401/403 인증 에러"
    echo "- ERR_CONNECTION_REFUSED"
    echo "- Failed to fetch"
    echo ""
    echo "현재 환경 설정:"
    echo "백엔드: http://localhost:8000"
    echo "프론트엔드: http://localhost:3010"
    echo ""
} > "$REPORT_DIR/browser_test_guide.txt"

echo "✅ 브라우저 테스트 가이드 생성 완료"

# 5. 요약 보고서 생성
echo "📋 5단계: 요약 보고서 생성 중..."
{
    echo "🚨 DantaroWallet 문제 보고서"
    echo "=================================="
    echo "생성 시간: $(date)"
    echo "문제 설명: $ISSUE_DESC"
    echo ""
    
    echo "📁 포함된 파일들:"
    echo "- system_diagnosis.log: 전체 시스템 진단 결과"
    echo "- error_collection.log: 에러 로그 수집 과정"
    echo "- error_report_*.txt: 상세 에러 로그 분석"
    echo "- snapshot.txt: 현재 상태 즉시 스냅샷"
    echo "- browser_test_guide.txt: 브라우저 테스트 가이드"
    echo "- summary.txt: 이 요약 보고서"
    echo ""
    
    echo "🎯 Copilot에게 보고하는 방법:"
    echo "1. 이 폴더의 모든 파일을 확인"
    echo "2. 주요 에러 메시지나 문제 상황을 설명"
    echo "3. '이 로그들을 분석해서 문제를 해결해 줘' 요청"
    echo ""
    
    echo "🚀 빠른 공유 명령어:"
    echo "cat $REPORT_DIR/snapshot.txt"
    echo "cat $REPORT_DIR/system_diagnosis.log | tail -50"
    echo ""
    
    echo "📊 보고서 크기:"
    du -sh "$REPORT_DIR"
    
} > "$REPORT_DIR/summary.txt"

echo "✅ 요약 보고서 생성 완료"

# 결과 출력
echo ""
echo "🎉 문제 보고서 생성 완료!"
echo "=================================================="
echo "📁 보고서 위치: $REPORT_DIR"
echo ""
echo "📋 생성된 파일들:"
ls -la "$REPORT_DIR/"
echo ""
echo "🚀 Copilot에게 보고하는 방법:"
echo "1. 즉시 확인: cat $REPORT_DIR/snapshot.txt"
echo "2. 전체 진단: cat $REPORT_DIR/system_diagnosis.log"
echo "3. 에러 로그: cat $REPORT_DIR/error_report_*.txt"
echo ""
echo "💡 사용 예시:"
echo "Copilot: '$(pwd)/$REPORT_DIR 폴더에 문제 보고서를 생성했습니다. 분석해서 해결 방법을 알려주세요.'"
echo ""

# 압축 파일 생성 (선택사항)
echo "📦 압축 파일 생성 중..."
tar -czf "${REPORT_DIR}.tar.gz" "$REPORT_DIR/"
echo "✅ 압축 완료: ${REPORT_DIR}.tar.gz"
echo ""
echo "🎯 모든 준비 완료! Copilot에게 분석을 요청하세요!"
