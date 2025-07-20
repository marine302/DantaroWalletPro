# DantaroWallet Pro - 하이브리드 USDT 지갑 SaaS 플랫폼

[![개발 상태](https://img.shields.io/badge/개발상태-95%25완성-brightgreen.svg)]()
[![백엔드](https://img.shields.io/badge/백엔드-FastAPI-009688.svg)]()
[![프론트엔드](https://img.shields.io/badge/프론트엔드-Next.js-000000.svg)]()
[![데이터베이스](https://img.shields.io/badge/DB-SQLite/PostgreSQL-336791.svg)]()

## 🚀 **2025-07-20 최신 업데이트**

### ✅ **완전 자동화된 개발 환경 구축 완료**
- **스마트 포트 관리**: 백엔드 서버가 이미 실행 중이면 재시작하지 않고 기존 서버 유지
- **자동 의존성 해결**: 누락된 패키지(mnemonic, hdwallet) 자동 설치
- **Health 체크 우선**: 포트 사용 여부보다 서버 응답 상태를 우선 확인
- **반복 메시지 방지**: "포트가 사용 중" 메시지 반복 없이 현재 상태만 안내

### 🛠️ **개발 환경 관리 자동화**
- **통합 관리 스크립트**: `dev-manager.sh`로 모든 환경 설정부터 서버 관리까지 원스톱
- **상태 기반 처리**: 서버 상태에 따른 지능적 처리 (실행 중/응답 없음/포트 비어있음)
- **완전 자동화**: `./dev-manager.sh auto` 명령 하나로 전체 개발 환경 구동

### ✅ **백엔드 시스템 안정화 완료**
- **포트 관리 중앙화**: config.py를 통한 통합 포트 관리 (8000번 포트)
- **가상환경 활용**: .venv 가상환경을 통한 의존성 격리
- **API 연결성 확인**: 모든 엔드포인트 정상 작동 ✅

## 📋 개요

DantaroWallet Pro는 **파트너사 중심의 USDT 지갑 관리 SaaS 플랫폼**입니다. 
트론 네트워크 기반으로 멀티 테넌트 아키텍처를 제공하며, 에너지 풀 관리부터 
고급 분석까지 완전한 지갑 서비스 인프라를 제공합니다.

### 🎯 핵심 기능
- **🏢 파트너사 관리**: 멀티 테넌트 온보딩 및 관리
- **⚡ 에너지 풀 시스템**: 트론 에너지 임대/관리 서비스
- **💰 자동화된 Sweep**: 입금 자동 수집 시스템
- **📊 고급 분석**: 실시간 트랜잭션 분석 및 리포팅
- **🔒 감사/컴플라이언스**: AML/KYC 통합 모니터링
- **🌐 외부 에너지 연동**: 외부 에너지 공급자 통합

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  슈퍼어드민      │    │  파트너 관리자   │    │   파트너 API    │
│   대시보드       │    │    대시보드      │    │    인터페이스   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   FastAPI       │
                    │   백엔드 서버    │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   SQLAlchemy    │
                    │   ORM + DB      │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   TRON 네트워크  │
                    │   블록체인 연동   │
                    └─────────────────┘
```

## 🚀 빠른 시작

### 📋 필수 요구사항
- Python 3.9+ (가상환경 권장)
- Node.js 18+
- SQLite (개발) / PostgreSQL (운영)
- Docker (선택사항)

### ⚡ 완전 자동화 - 1분 설치 & 실행

```bash
# 저장소 클론
git clone <repository-url>
cd DantaroWalletPro

# 🚀 완전 자동화 (처음 실행 시 - 모든 환경 설정부터 서버 시작까지)
./dev-manager.sh auto

# 🔄 일반 사용 (이미 설정된 환경에서)
./dev-manager.sh start
```

### 🎯 개별 서버 관리

```bash
# 백엔드만 시작 (포트 8000)
./dev-manager.sh backend

# 프론트엔드만 시작
./dev-manager.sh super      # Super Admin (포트 3020)  
./dev-manager.sh partner    # Partner Admin (포트 3030)

# 상태 확인 및 유틸리티
./dev-manager.sh status     # 서버 상태 확인
./dev-manager.sh health     # 환경 건강성 검사
./dev-manager.sh test       # API 연결 테스트
./dev-manager.sh ports      # 포트 관리
./dev-manager.sh clean      # 정리
```

### 🔧 개발 환경 설정 (필요시만)

```bash
# 환경 설정만 따로 실행
./dev-manager.sh setup

# 문제 해결
./dev-manager.sh health     # 환경 진단
./dev-manager.sh restart    # 모든 서버 재시작
```

## 📁 프로젝트 구조

```
DantaroWalletPro/
├── dantarowallet/              # 백엔드 (FastAPI)
│   ├── app/
│   │   ├── api/v1/            # API 엔드포인트
│   │   ├── models/            # SQLAlchemy 모델
│   │   ├── services/          # 비즈니스 로직
│   │   ├── core/              # 핵심 설정
│   │   └── middleware/        # 미들웨어
│   ├── start_backend.sh       # 백엔드 시작 스크립트
│   └── run_server.py          # 서버 실행 파일
├── frontend/
│   └── super-admin-dashboard/ # 슈퍼어드민 프론트엔드
│       ├── src/app/          # Next.js 페이지
│       ├── src/components/   # React 컴포넌트
│       ├── src/lib/         # 유틸리티
│       └── start_frontend.sh # 프론트엔드 시작 스크립트
├── docs/                     # 문서
├── dev-manager.sh           # 통합 개발환경 관리자
└── README.md
```

## 🌐 액세스 포인트

### 🖥️ 웹 인터페이스
- **슈퍼어드민 대시보드**: http://localhost:3020
- **백엔드 API 문서**: http://localhost:8000/docs
- **백엔드 헬스체크**: http://localhost:8000/health

### 📡 주요 API 엔드포인트
```
# 시스템 상태
GET /health
GET /api/v1/superadmin/system-health

# 대시보드 통계
GET /api/v1/superadmin/dashboard/stats

# 파트너 관리
GET /api/v1/admin/partners
POST /api/v1/admin/partners

# 에너지 관리
GET /api/v1/energy/pools
POST /api/v1/energy/allocate
```

## 📊 개발 진행 상황

### **백엔드 시스템: 95% 완성** ✅
- ✅ 모든 핵심 API 엔드포인트 구현
- ✅ SQLAlchemy 모델 및 스키마 완성
- ✅ 미들웨어 및 인증 시스템 완성
- ✅ 에러 핸들링 및 로깅 시스템
- ✅ 포트 관리 중앙화 및 설정 통합

### **프론트엔드 시스템: 85% 완성** ⬆️
- ✅ 슈퍼어드민 대시보드 기본 레이아웃
- ✅ 핵심 페이지 구현 (대시보드, 파트너, 에너지)
- ✅ API 클라이언트 및 상태 관리
- ⚠️ API 연동 및 실제 데이터 처리 (진행중)

### **개발 환경: 100% 완성** ✅
- ✅ 자동화된 서버 관리 스크립트
- ✅ 통합 개발환경 관리자
- ✅ 포트 충돌 방지 시스템
- ✅ 실시간 상태 모니터링

## 🔧 개발 도구

### **백엔드 개발**
```bash
cd dantarowallet

# 가상환경 활성화
source .venv/bin/activate

# 개발 서버 시작
./start_backend.sh

# 데이터베이스 마이그레이션
alembic upgrade head

# 테스트 실행
python -m pytest
```

### **프론트엔드 개발**
```bash
cd frontend/super-admin-dashboard

# 개발 서버 시작
./start_frontend.sh

# 또는 NPM으로
npm run dev

# 빌드
npm run build
```

## 📚 관련 문서

- [📖 개발 진행 상황 보고서](./DEVELOPMENT_PROGRESS_REPORT.md)
- [✅ 슈퍼어드민 최종 점검](./SUPERADMIN_FINAL_CHECK.md)
- [📋 상세 테스팅 체크리스트](./DETAILED_TESTING_CHECKLIST.md)
- [📁 문서 아카이브](./docs/)

## 🤝 기여 가이드

1. **이슈 생성**: 버그 리포트나 기능 요청
2. **브랜치 생성**: `feature/기능명` 또는 `fix/버그명`
3. **개발 및 테스트**: 로컬에서 충분한 테스트
4. **Pull Request**: 상세한 설명과 함께 제출

## 📞 지원

프로젝트 관련 문의사항이나 기술 지원이 필요한 경우:
- 📧 이메일: support@dantarowallet.com
- 💬 Discord: [DantaroWallet 개발자 채널]
- 📋 이슈 트래커: GitHub Issues

---

**DantaroWallet Pro** - *차세대 USDT 지갑 SaaS 플랫폼* 🚀

## 🚀 개발 환경 자동화

### ⚡ 완전 자동화 (권장)

**매번 개발 시 한 번의 명령으로 모든 환경 설정 + 서버 시작:**

```bash
cd /Users/danielkwon/DantaroWalletPro
./dev-manager.sh auto
```

이 명령어는 다음을 자동으로 수행합니다:
- ✅ 환경 건강성 검사 및 자동 수정
- ✅ Python 가상환경 설정 및 패키지 설치
- ✅ Node.js 의존성 설치
- ✅ 데이터베이스 초기화
- ✅ 포트 충돌 해결
- ✅ 모든 서버 시작 (백엔드 + 두 프론트엔드)
- ✅ 브라우저 자동 접속
- ✅ VS Code 워크스페이스 열기

### 🛠️ 개발 환경 관리 도구

```bash
# 환경 설정만 (서버 시작 안 함)
./dev-manager.sh setup

# 환경 건강성 검사
./dev-manager.sh health

# 모든 서버 시작
./dev-manager.sh start

# 서버 상태 확인
./dev-manager.sh status

# 포트 관리
./dev-manager.sh ports check    # 포트 사용 현황
./dev-manager.sh ports cleanup  # 포트 충돌 해결

# API 연결 테스트
./dev-manager.sh test

# 프로젝트 정리
./dev-manager.sh clean
```

### 🎯 개별 서버 제어

```bash
# 백엔드만 시작 (포트 8000)
./dev-manager.sh backend

# Super Admin Dashboard만 시작 (포트 3020)
./dev-manager.sh super

# Partner Admin Template만 시작 (포트 3030)
./dev-manager.sh partner

# 모든 서버 중지
./dev-manager.sh stop

# 모든 서버 재시작
./dev-manager.sh restart
```

### 🌐 서비스 접속 주소

자동으로 브라우저에서 열립니다:
- 🔧 **API 문서**: http://localhost:8000/docs
- 🔒 **Super Admin**: http://localhost:3020
- 👥 **Partner Admin**: http://localhost:3030

### 💡 일반적인 개발 워크플로우

1. **컴퓨터 켤 때**: `./dev-manager.sh auto`
2. **코딩**: 모든 서버가 자동 리로드됨
3. **컴퓨터 끌 때**: 터미널 창들 닫기

**더 이상 환경 설정으로 시간을 낭비하지 마세요!** 🎯

### 🆘 문제 해결

```bash
# 환경에 문제가 있을 때
./dev-manager.sh auto        # 완전 자동화로 모든 문제 해결

# 포트 충돌 시  
./dev-manager.sh ports cleanup

# 환경 상태만 확인할 때
./dev-manager.sh health
```

---
