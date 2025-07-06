# DantaroWallet 자동 진단 및 유지보수 체계

## 📋 개요

DantaroWallet의 백엔드(FastAPI)와 프론트엔드(Next.js) 시스템의 안정성을 보장하기 위한 자동 진단 및 문제 보고 체계입니다.

## 🛠️ 진단 도구들

### 1. 전체 시스템 진단 (`diagnose.sh`)
```bash
./diagnose.sh
```
**수행 작업:**
- 프로세스 상태 확인 (uvicorn, next)
- 포트 사용 현황 (8000, 3010)
- API 엔드포인트 테스트
- CORS 설정 확인
- 환경 변수 검증
- 시스템 리소스 상태

**출력:** `diagnostic_YYYYMMDD_HHMMSS.log`

### 2. 에러 로그 수집 (`collect_errors.sh`)
```bash
./collect_errors.sh [분]  # 기본값: 10분
```
**수행 작업:**
- 최근 N분간의 시스템 에러 로그
- Python/FastAPI 관련 에러
- Node.js/Next.js 에러
- 네트워크 연결 문제
- CORS 및 환경 설정 이슈

**출력:** `error_report_YYYYMMDD_HHMMSS.txt`

### 3. 실시간 모니터링 (`monitor.sh`)
```bash
./monitor.sh [간격_초]  # 기본값: 30초
```
**수행 작업:**
- 주기적 서비스 상태 확인
- 메모리 사용률 모니터링
- API 응답 상태 추적
- 실시간 로그 저장

**출력:** `monitor_YYYYMMDD_HHMMSS.log`
**중지:** `Ctrl+C`

### 4. 통합 문제 보고 (`report_issue.sh`) ⭐
```bash
./report_issue.sh "문제 설명"
```
**수행 작업:**
- 전체 진단 + 에러 수집 + 현재 스냅샷
- 브라우저 테스트 가이드 생성
- Copilot 보고용 요약 생성
- 모든 자료를 압축 패키지로 제공

**출력:** `reports/YYYYMMDD_HHMMSS/` 폴더 + 압축 파일

## 🚨 문제 발생 시 대응 절차

### 1단계: 즉시 진단
```bash
cd /workspaces/DantaroWalletPro
./report_issue.sh "로그인 불가능"
```

### 2단계: 결과 확인
```bash
# 즉시 상태 확인
cat reports/최신폴더/snapshot.txt

# 상세 진단 확인  
cat reports/최신폴더/system_diagnosis.log | tail -50
```

### 3단계: Copilot에게 보고
```
GitHub Copilot에게 전달:
"reports/YYYYMMDD_HHMMSS 폴더에 문제 보고서를 생성했습니다. 
[문제 상황 간단 설명]이 발생했는데, 로그를 분석해서 해결 방법을 알려주세요."
```

## 📊 주요 체크 포인트

### 백엔드 (FastAPI)
- ✅ 프로세스 실행: `uvicorn` 
- ✅ 포트 응답: `8000`
- ✅ Health API: `/health`
- ✅ Admin API: `/api/v1/admin/dashboard/stats`
- ✅ CORS 설정: `localhost:3010` 허용

### 프론트엔드 (Next.js)
- ✅ 프로세스 실행: `next`
- ✅ 포트 응답: `3010`
- ✅ 환경 변수: `NEXT_PUBLIC_API_BASE_URL`
- ✅ API 연결: 백엔드 통신

### 네트워크 & 보안
- ✅ CORS 헤더 정상
- ✅ 인증 토큰 처리
- ✅ API 응답 코드 (200, 401, 403)

## 🔧 일반적인 문제 해결

### 백엔드 서버 시작 안됨
```bash
cd /workspaces/DantaroWalletPro/dantarowallet
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 프론트엔드 서버 시작 안됨
```bash
cd /workspaces/DantaroWalletPro/frontend/super-admin-dashboard
npm run dev
```

### CORS 에러
- `app/main.py`의 CORS 설정 확인
- `allow_origins = ["http://localhost:3010"]`
- `allow_credentials = True`

### 환경 변수 문제
```bash
# 백엔드 환경 변수
cat /workspaces/DantaroWalletPro/dantarowallet/.env

# 프론트엔드 환경 변수  
cat /workspaces/DantaroWalletPro/frontend/super-admin-dashboard/.env.local
```

## 📈 실시간 모니터링 설정

### 지속적 모니터링 (백그라운드)
```bash
# 터미널 1: 모니터링 시작
./monitor.sh 60 &  # 1분 간격

# 터미널 2: 로그 실시간 확인
tail -f monitor_*.log
```

### 자동 문제 감지 (크론잡 설정)
```bash
# 10분마다 자동 진단
echo "*/10 * * * * cd /workspaces/DantaroWalletPro && ./diagnose.sh > /tmp/auto_diagnosis.log 2>&1" | crontab -
```

## 🎯 Copilot 보고 템플릿

### 문제 보고 예시
```
GitHub Copilot님,

DantaroWallet에서 [구체적 문제]가 발생했습니다.

상황:
- 브라우저에서 로그인 시 CORS 에러 발생
- 프론트엔드는 정상 작동하지만 API 호출 실패

진단 결과:
[report_issue.sh 실행 결과 붙여넣기]

분석 및 해결 방법을 알려주세요.
```

## 📝 로그 파일 관리

### 자동 정리 (선택사항)
```bash
# 7일 이상 된 진단 로그 삭제
find . -name "diagnostic_*.log" -mtime +7 -delete
find . -name "error_report_*.txt" -mtime +7 -delete
find . -name "monitor_*.log" -mtime +7 -delete

# 보고서 폴더 정리 (30일)
find reports/ -type d -mtime +30 -exec rm -rf {} \;
```

## 🚀 고급 활용

### 성능 모니터링
```bash
# 메모리/CPU 사용률 추적
watch -n 5 'ps aux | grep -E "(uvicorn|next)" | grep -v grep'

# API 응답 시간 측정
time curl -s http://localhost:8000/health
```

### 외부 알림 연동 (선택사항)
```bash
# Slack 웹훅 알림 (webhook URL 설정 필요)
if ! curl -s http://localhost:8000/health; then
    curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"🚨 DantaroWallet 백엔드 서버 다운!"}' \
    YOUR_SLACK_WEBHOOK_URL
fi
```

---

## 💡 팁

1. **정기 진단**: 매일 오전 `./diagnose.sh` 실행으로 사전 점검
2. **로그 관찰**: 개발 중에는 `./monitor.sh` 백그라운드 실행
3. **문제 발생 시**: 당황하지 말고 `./report_issue.sh` 실행 후 Copilot에게 보고
4. **환경 변화 시**: 설정 변경 후 반드시 전체 진단 수행

**🎯 목표: 문제 발생 → 자동 진단 → Copilot 분석 → 빠른 해결**
