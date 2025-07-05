# 🏗️ DantaroWallet Pro - 아키텍처 가이드

**업데이트**: 2025년 7월 5일  
**상태**: 리팩토링 완료, 모듈화 아키텍처 적용

---

## 📋 **전체 아키텍처 개요**

DantaroWallet Pro는 **클린 아키텍처** 원칙을 따르는 모듈화된 TRON 블록체인 지갑 시스템입니다.

### 🎯 **설계 원칙**
1. **단일 책임 원칙 (SRP)**: 각 모듈은 하나의 도메인만 담당
2. **의존성 역전 (DIP)**: 추상화에 의존, 구현체에 의존하지 않음
3. **모듈화 우선**: 폴더 기반 도메인 분리
4. **레거시 호환성**: 기존 import 경로 지원

---

## 📁 **폴더 구조**

```
DantaroWalletPro/
├── dantarowallet/                 # 메인 애플리케이션
│   ├── app/
│   │   ├── api/                   # API 레이어
│   │   │   └── v1/endpoints/      # REST API 엔드포인트
│   │   ├── core/                  # 핵심 인프라
│   │   │   ├── tron/              # TRON 블록체인 모듈
│   │   │   ├── config.py          # 설정 관리
│   │   │   ├── database.py        # DB 연결
│   │   │   ├── security.py        # 보안 기능
│   │   │   └── exceptions.py      # 예외 처리
│   │   ├── services/              # 비즈니스 로직 레이어
│   │   │   ├── admin/             # 관리자 기능
│   │   │   ├── balance/           # 잔고 관리
│   │   │   ├── wallet/            # 지갑 관리
│   │   │   ├── withdrawal/        # 출금 처리
│   │   │   ├── deposit_monitoring/ # 입금 모니터링
│   │   │   ├── transaction_analytics/ # 트랜잭션 분석
│   │   │   └── energy/            # 에너지 관리
│   │   ├── models/                # 데이터 모델
│   │   ├── schemas/               # API 스키마
│   │   └── middleware/            # 미들웨어
│   └── tests/                     # 테스트 코드
└── docs/                          # 프로젝트 문서
```

---

## 🔧 **핵심 모듈 설명**

### 1. **TRON 블록체인 모듈** (`app/core/tron/`)

**완전히 모듈화된 TRON 연동 시스템**

```
app/core/tron/
├── __init__.py          # 모든 클래스 export
├── constants.py         # TRON 상수 및 설정
├── network.py          # 네트워크 연결 관리
├── wallet.py           # 지갑 관리
├── balance.py          # 잔고 조회
├── energy.py           # 에너지 및 리소스 관리
├── stats.py            # 네트워크 통계
├── transaction.py      # 트랜잭션 관리
└── service.py          # 통합 서비스 (Facade)
```

**주요 특징:**
- ✅ 네이밍 중복 문제 해결 (`tron_*.py` → `tron/*.py`)
- ✅ 단일 책임 원칙 적용
- ✅ Facade 패턴으로 복잡성 숨김
- ✅ 레거시 호환성 유지

### 2. **서비스 레이어** (`app/services/`)

**도메인별 모듈화된 비즈니스 로직**

#### **모듈화된 서비스들:**
- **Admin**: 관리자 기능 (시스템 모니터링, 사용자 관리, 트랜잭션 모니터링)
- **Balance**: 잔고 관리 (조회, 트랜잭션, 이체, 조정)
- **Wallet**: 지갑 관리 (생성, 조회, 모니터링)
- **Withdrawal**: 출금 처리 (검증, 요청, 처리, 조회)
- **Deposit Monitoring**: 입금 모니터링 (블록체인 스캔, 자동 처리)
- **Transaction Analytics**: 트랜잭션 분석 (통계, 리포트)
- **Energy**: TRON 에너지 관리 (에너지 풀, 대여)

#### **호환성 보장:**
```python
# 새로운 모듈화 방식
from app.services.admin import AdminService

# 기존 방식 (레거시 호환)
from app.services.admin_service import AdminService
```

### 3. **API 레이어** (`app/api/v1/endpoints/`)

**RESTful API 엔드포인트**
- 18개 API 파일 구현
- 버전 관리 지원 (v1/)
- 자동 문서화 (FastAPI)
- 인증 및 권한 관리

---

## 🎨 **적용된 디자인 패턴**

### 1. **Facade 패턴**
- `TronService`: 복잡한 TRON 모듈들을 단순한 인터페이스로 제공
- `AdminService`: 여러 관리자 기능을 통합 인터페이스로 제공

### 2. **Repository 패턴**
- 각 모델별 데이터 접근 로직 분리
- ORM과 비즈니스 로직 분리

### 3. **Service Layer 패턴**
- 도메인별 비즈니스 로직 캡슐화
- API와 데이터 레이어 사이의 중간 계층

### 4. **Module 패턴**
- 기능별 폴더 구조
- 명확한 의존성 관리

---

## 🔗 **의존성 관계**

```
API Layer (endpoints)
    ↓
Service Layer (services)
    ↓
Core Layer (tron, database, etc)
    ↓
Model Layer (SQLAlchemy models)
```

**주요 원칙:**
- 상위 레이어는 하위 레이어에만 의존
- 하위 레이어는 상위 레이어를 알지 못함
- 인터페이스를 통한 의존성 주입

---

## 🚀 **성능 및 확장성**

### **현재 구현된 최적화:**
- ✅ 모듈별 독립적 로딩
- ✅ 지연 로딩 (Lazy Loading) 적용
- ✅ 캐싱 레이어 준비
- ✅ 비동기 처리 (FastAPI + AsyncIO)

### **향후 확장 가능성:**
- 🔄 마이크로서비스 분리 가능
- 🔄 Redis 캐싱 레이어 추가
- 🔄 메시지 큐 시스템 연동
- 🔄 로드 밸런싱 지원

---

## 📝 **개발 가이드라인**

### **새로운 기능 추가 시:**
1. 적절한 도메인 폴더에 모듈 생성
2. 단일 책임 원칙 준수
3. 기존 패턴 일관성 유지
4. 레거시 호환성 고려

### **코드 품질 기준:**
- Type hints 필수
- Docstring 작성
- 단위 테스트 포함
- 에러 처리 강화

---

*이 아키텍처는 지속적으로 개선되며, 새로운 요구사항에 따라 확장됩니다.*
