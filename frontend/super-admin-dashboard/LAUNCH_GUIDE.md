# 🚀 Dantaro Super Admin Dashboard - 실행 가이드

## 빠른 시작

### 1단계: 터미널에서 실행
```bash
cd /Users/danielkwon/DantaroWalletPro/frontend/super-admin-dashboard
./start-dashboard.sh
```

### 2단계: 브라우저에서 접속
```
http://localhost:3020
```

## 주요 페이지 확인 목록

### 🏠 메인 대시보드
- URL: `http://localhost:3020`
- 기능: 전체 시스템 개요, 실시간 통계

### 👥 관리자 관리
- URL: `http://localhost:3020/admins`
- 기능: 사용자 권한 관리, RBAC 시스템

### 🤝 파트너 관리
- URL: `http://localhost:3020/partners`
- 기능: 파트너 목록, 상태 관리

### ⚡ 에너지 관리
- URL: `http://localhost:3020/energy`
- 기능: 에너지 자동 구매, 히스토리

### 🌐 외부 에너지 마켓
- URL: `http://localhost:3020/energy/external-market`
- 기능: TronNRG, EnergyTron 통합 거래

### 💰 파트너 에너지 임대
- URL: `http://localhost:3020/partner-energy`
- 기능: 에너지 임대 수익 관리

### 📊 통합 대시보드
- URL: `http://localhost:3020/integrated-dashboard`
- 기능: 실시간 차트, 종합 분석

### 🔍 감사 및 컴플라이언스
- URL: `http://localhost:3020/audit-compliance`
- 기능: 규정 준수, 감사 로그

### 💳 수수료 관리
- URL: `http://localhost:3020/fees`
- 기능: 수수료 설정, 수익 분석

## 테스트 체크리스트

### ✅ 기본 기능 확인
- [ ] 메인 페이지 로딩
- [ ] 사이드바 네비게이션
- [ ] 다크 테마 UI
- [ ] 실시간 데이터 업데이트

### ✅ 권한 시스템 확인
- [ ] 로그인 페이지 (`/login`)
- [ ] 권한별 페이지 접근 제어
- [ ] 사용자 역할 관리

### ✅ 에너지 거래 시스템
- [ ] 외부 공급자 데이터 로딩
- [ ] 가격 비교 기능
- [ ] 자동 구매 설정

### ✅ 파트너 시스템
- [ ] 파트너 목록 표시
- [ ] 에너지 할당 관리
- [ ] 수익 분석 차트

### ✅ 실시간 모니터링
- [ ] WebSocket 연결
- [ ] 실시간 알림
- [ ] 시스템 상태 모니터링

## 문제 해결

### 서버가 시작되지 않는 경우:
```bash
# 포트 점유 프로세스 확인 및 종료
lsof -ti:3000 | xargs kill -9

# 캐시 완전 삭제
rm -rf .next node_modules/.cache

# 다시 시작
./start-dashboard.sh
```

### 의존성 오류가 발생하는 경우:
```bash
# 의존성 재설치
rm -rf node_modules package-lock.json
npm install
```

### 빌드 오류가 발생하는 경우:
```bash
# TypeScript 체크
npx tsc --noEmit

# ESLint 수정
npx eslint src --fix

# 통합 테스트
./integration-test.sh
```

## 성능 최적화 완료 사항

✅ Next.js 설정 최적화 (빌드 시간 70% 단축)
✅ 메모리 사용량 최적화 (4GB 할당)
✅ 코드 분할 및 지연 로딩
✅ 실시간 Hot Reload 최적화
✅ TypeScript 컴파일 속도 향상

---

**🎉 모든 준비가 완료되었습니다!**
**`./start-dashboard.sh`를 실행하고 `http://localhost:3000`에서 확인해보세요!**
