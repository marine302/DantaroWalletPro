# DantaroWallet Pro - Partner Admin Template

## 프로젝트 개요
Tron 블록체인 기반의 에너지 대여 서비스를 위한 파트너 관리자 대시보드입니다.

## 최근 완료 사항 (2025.07.20)

### ✅ UI/UX 개선
- **텍스트 가시성 문제 해결**: 모든 페이지에서 텍스트가 배경색과 동일해 보이지 않던 문제 완전 해결
- **다크모드 대응**: 모든 컴포넌트에 다크모드 색상 클래스 적용
- **shadcn/ui 테마 표준화**: 일관된 디자인 시스템 적용
- **검은색 블록 문제 해결**: 분석페이지 등에서 나타나던 검은색 placeholder 문제 해결

### ✅ 컴포넌트 개선
- **분석 페이지**: 차트 placeholder 및 통계 박스 스타일 개선
- **사용자 관리**: 텍스트 가시성 및 테이블 스타일 개선
- **출금 관리**: API 폴백 데이터 처리 및 UI 개선
- **에너지 관리**: 실시간 모니터링 위젯 개선

### ✅ 시스템 안정성
- **React Query 최적화**: 무한 로딩 방지 및 폴백 데이터 처리
- **에러 핸들링**: 백엔드 API 없이도 정상 동작하도록 개선
- **코드 정리**: 불필요한 임시 파일 및 디버깅 코드 제거

## 기술 스택
- **Frontend**: Next.js 15, React 18, TypeScript
- **UI**: Tailwind CSS, shadcn/ui
- **상태관리**: React Query
- **블록체인**: TronWeb, TronLink 연동

## 주요 기능
1. **대시보드**: 실시간 통계 및 주요 지표 모니터링
2. **분석 및 보고서**: 수익/비용 분석, 사용자/거래 통계
3. **사용자 관리**: 파트너 사용자 목록 및 상태 관리
4. **출금 관리**: 출금 요청 승인/거부 처리
5. **에너지 관리**: Tron 에너지 풀 모니터링 및 관리
6. **지갑 연동**: TronLink 지갑 연결 및 관리

## 개발 환경 설정

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 빌드
npm run build

# 린트 검사
npm run lint
```

## 프로젝트 구조
```
src/
├── app/                 # Next.js App Router 페이지
├── components/          # 재사용 가능한 컴포넌트
│   ├── ui/             # shadcn/ui 컴포넌트
│   ├── layout/         # 레이아웃 컴포넌트
│   └── dashboard/      # 대시보드 전용 컴포넌트
├── contexts/           # React Context 파일
├── lib/               # 유틸리티 및 훅
└── types/             # TypeScript 타입 정의
```

## 현재 상태
- ✅ Phase 1: 기본 UI/UX 완료
- 🚧 Phase 2: 백엔드 API 연동 준비 중
- 📋 Phase 3: 고급 기능 및 최적화 예정

## 다음 단계
1. 백엔드 API 서버 연동
2. 실시간 데이터 업데이트 구현
3. TronLink 지갑 연동 고도화
4. 차트 라이브러리 적용 (Chart.js/Recharts)
5. 모바일 반응형 최적화

---
*Last Updated: 2025.07.20*
