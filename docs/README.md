# DantaroWallet Pro - 문서 체계

## 📁 문서 구조

### 🚀 active/ - 활성 문서들
현재 개발 중이거나 참조하는 문서들

#### copilot_docs/
- **completed/**: 완료된 Copilot 문서들 (Doc #24-27)
  - `copilot-doc-24.md` - 기본 TronLink 연동
  - `copilot-doc-24-tronlink.md` - TronLink 연동 세부사항
  - `copilot-doc-25.md` - 에너지 풀 고급 관리
  - `copilot-doc-26.md` - 파트너사 수수료 및 정책 관리
  - `copilot-doc-27.md` - 입금 Sweep 자동화

- **in_progress/**: 진행 중인 Copilot 문서들 (Doc #28-35)
  - `copilot-doc-28.md` - 파트너사 출금 관리 고도화
  - `copilot-doc-29.md` - 파트너사 온보딩 자동화
  - `copilot-doc-30.md` - 트랜잭션 감사 및 컴플라이언스
  - `copilot-doc-31.md` - 파트너 관리자 템플릿
  - `copilot-doc-32.md` - 사용자 모바일 앱 템플릿
  - `copilot-doc-33.md` - 운영 가이드 및 매뉴얼
  - `copilot-doc-34.md` - 종합 운영 대시보드
  - `copilot-doc-35.md` - SaaS 플랫폼 최종 점검

- **templates/**: 템플릿 문서들
  - `copilot-doc-17.md` - 빈 템플릿
  - `copilot-doc-18.md` - 빈 템플릿
  - `copilot-doc-19.md` - 빈 템플릿
  - `copilot-doc-20.md` - 빈 템플릿

#### progress/
- `PROGRESS.md` - 전체 프로젝트 진행 상황
- `DOC25_PROGRESS_REPORT.md` - Doc #25 진행 보고서

#### project_status/
- `PROJECT_STATUS_COMPREHENSIVE.md` - 종합 프로젝트 상태

#### roadmap/
- `dantaro-ai-roadmap2.md` - 개발 로드맵 (문서 25-35)

### 📦 archive/ - 아카이브 문서들
과거 문서들과 참조용 자료들

#### root_files/
루트 폴더에서 이동한 문서들

- **database_docs/**: 데이터베이스 관련 문서들
  - `DATABASE_ERD.md` - 데이터베이스 ERD
  - `DATABASE_SCHEMA_ANALYSIS.md` - 스키마 분석
  - `DATABASE_SCHEMA_DOCUMENTATION.md` - 스키마 문서화

- **progress_reports/**: 진행 보고서들
  - `DOC26_PROGRESS_REPORT.md` - Doc #26 진행 보고서

- **maintenance_scripts/**: 유지보수 스크립트들
  - `MAINTENANCE_GUIDE.md` - 유지보수 가이드
  - `*.sh` - 각종 유지보수 스크립트들

- **debug_logs/**: 디버그 로그들
  - `*.log` - 시스템 로그
  - `*.txt` - 에러 리포트
  - `*.js` - 디버그 스크립트

#### Done/, Pass/, No Need/
기존 분류 폴더들 (정리 완료)

#### ALL_DOCUMENTS_COLLECTION/
모든 문서들의 백업 컬렉션

#### organized/
이전 정리 시도 폴더들

## 🎯 현재 개발 상태 (2025-07-09)

### ✅ 완료된 개발
- **Doc #1-24**: 기본 시스템 구축 완료
- **Doc #25-27**: 에너지 관리, 수수료 정책, HD Wallet & Sweep 자동화 **완료**
- **코드베이스 정리**: 타입 오류 해결 및 시스템 안정화 완료

### 🔄 다음 단계
- **Doc #28**: 파트너사 출금 관리 고도화 (우선순위 1)
- **Doc #29**: 파트너사 온보딩 자동화 (우선순위 2)
- **Doc #30**: 트랜잭션 감사 및 컴플라이언스 (우선순위 3)

### 🚀 최종 목표
- **Doc #31-35**: 파트너 지원 시스템 및 SaaS 플랫폼 완성

## 📋 문서 관리 규칙

### 활성 문서 (active/)
- 현재 참조하거나 개발 중인 문서들
- 정기적으로 업데이트됨
- 중요한 변경사항은 Git으로 추적

### 아카이브 문서 (archive/)
- 완료되었거나 더 이상 사용하지 않는 문서들
- 참조용으로만 사용
- 삭제하지 않고 보관

### 문서 이동 규칙
1. 완료된 문서: `active/` → `archive/`
2. 더 이상 사용하지 않는 문서: `archive/`로 이동
3. 중복 문서: 최신 버전만 `active/`에 보관, 나머지는 `archive/`

---
**마지막 업데이트**: 2025-07-09  
**정리 완료**: 루트 폴더 + docs 폴더 전체 정리 완료  
**다음 작업**: Doc #28 파트너사 출금 관리 고도화 개발 시작
