# DantaroWallet 데이터베이스 스키마 문서

생성일: 2025-07-08  
분석 대상: DantaroWallet Dev Database  

## 📊 개요

DantaroWallet은 TRON 네트워크 기반의 암호화폐 지갑 서비스로, 다음과 같은 주요 기능을 제공합니다:
- 사용자 관리 및 인증
- 지갑 및 잔액 관리
- 입출금 거래 처리
- 파트너사 수수료 정책 관리
- 에너지 풀 및 모니터링
- 거래 분석 및 리포팅

## 🗄️ 테이블 구조

### 📋 총 25개 테이블

```
📊 Core System Tables (핵심 시스템)
├── users                    # 사용자 정보
├── balances                 # 사용자 잔액
├── wallets                  # 지갑 정보
├── transactions             # 거래 내역
├── deposits                 # 입금 기록
└── withdrawals              # 출금 기록

🤝 Partner & Policy Tables (파트너 및 정책)
├── partners                 # 파트너사 정보
├── partner_wallets          # 파트너 지갑
├── partner_fee_policies     # 수수료 정책
├── fee_tiers               # 구간별 수수료
├── partner_withdrawal_policies  # 출금 정책
├── partner_energy_policies  # 에너지 정책
├── user_tiers              # 사용자 등급
└── partner_policy_calculation_logs  # 정책 계산 로그

⚡ Energy System Tables (에너지 시스템)
├── energy_pools            # 에너지 풀
├── partner_energy_pools    # 파트너 에너지 풀
├── energy_alerts           # 에너지 알림
├── energy_predictions      # 에너지 예측
├── energy_usage_history    # 에너지 사용 이력
├── energy_usage_logs       # 에너지 사용 로그
└── energy_price_history    # 에너지 가격 이력

📈 Analytics & Monitoring (분석 및 모니터링)
├── transactionalerts       # 거래 알림
├── transactionsummarys     # 거래 요약
├── system_transaction_alerts  # 시스템 거래 알림
└── fee_calculation_logs    # 수수료 계산 로그

🔧 System Tables (시스템)
└── alembic_version         # 마이그레이션 버전
```

## 🔗 주요 관계도

### 사용자 중심 관계
```
users (사용자)
├── 1:N → balances (잔액)
├── 1:N → wallets (지갑)
├── 1:N → transactions (거래)
├── 1:N → deposits (입금)
├── 1:N → withdrawals (출금)
└── N:M → user_tiers (등급) ← partners
```

### 파트너사 중심 관계
```
partners (파트너사)
├── 1:1 → partner_fee_policies (수수료 정책)
│   └── 1:N → fee_tiers (구간별 수수료)
├── 1:1 → partner_withdrawal_policies (출금 정책)
├── 1:1 → partner_energy_policies (에너지 정책)
├── 1:N → partner_wallets (파트너 지갑)
├── 1:N → partner_energy_pools (에너지 풀)
├── 1:N → user_tiers (사용자 등급)
└── 1:N → partner_policy_calculation_logs (계산 로그)
```

### 에너지 시스템 관계
```
energy_pools (에너지 풀)
├── 1:N → partner_energy_pools (파트너별 풀)
├── 1:N → energy_alerts (알림)
├── 1:N → energy_predictions (예측)
├── 1:N → energy_usage_history (사용 이력)
├── 1:N → energy_usage_logs (사용 로그)
└── 1:N → energy_price_history (가격 이력)
```

## 📋 상세 테이블 스키마

### 핵심 시스템 테이블

#### users (사용자)
| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | INTEGER | PK, AUTO_INCREMENT | 사용자 ID |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 이메일 주소 |
| password_hash | VARCHAR(255) | NOT NULL | 암호화된 비밀번호 |
| is_active | BOOLEAN | NOT NULL | 활성 상태 |
| is_admin | BOOLEAN | NOT NULL | 관리자 여부 |
| is_verified | BOOLEAN | NOT NULL | 이메일 인증 여부 |
| tron_address | VARCHAR(42) | UNIQUE | TRON 지갑 주소 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 생성일시 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 수정일시 |

**인덱스:**
- `idx_user_email_active` (email, is_active)
- `ix_users_email` (email) UNIQUE
- `ix_users_tron_address` (tron_address) UNIQUE

#### balances (잔액)
| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | INTEGER | PK, AUTO_INCREMENT | 잔액 ID |
| user_id | INTEGER | FK → users(id), NOT NULL | 사용자 ID |
| asset | VARCHAR(10) | NOT NULL | 자산 종류 (USDT, TRX 등) |
| amount | NUMERIC(18,6) | NOT NULL, CHECK ≥ 0 | 사용 가능 잔액 |
| locked_amount | NUMERIC(18,6) | NOT NULL, CHECK ≥ 0 | 잠금 잔액 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 생성일시 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 수정일시 |

**제약조건:**
- `uq_user_asset` (user_id, asset) UNIQUE
- `check_positive_amount` (amount ≥ 0)
- `check_positive_locked` (locked_amount ≥ 0)
- `check_locked_not_exceed_amount` (locked_amount ≤ amount)

#### transactions (거래)
| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | INTEGER | PK, AUTO_INCREMENT | 거래 ID |
| user_id | INTEGER | FK → users(id), NOT NULL | 사용자 ID |
| type | VARCHAR(10) | NOT NULL | 거래 유형 |
| direction | VARCHAR(8) | NOT NULL | 거래 방향 (IN/OUT) |
| status | VARCHAR(10) | NOT NULL | 거래 상태 |
| asset | VARCHAR(10) | NOT NULL | 자산 종류 |
| amount | NUMERIC(18,6) | NOT NULL | 거래 금액 |
| fee | NUMERIC(18,6) | NOT NULL | 수수료 |
| related_user_id | INTEGER | FK → users(id) | 연관 사용자 ID |
| reference_id | VARCHAR(100) | | 참조 ID |
| tx_hash | VARCHAR(100) | | 트랜잭션 해시 |
| description | TEXT | | 거래 설명 |
| transaction_metadata | TEXT | | 메타데이터 (JSON) |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 생성일시 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 수정일시 |

### 파트너 시스템 테이블

#### partners (파트너사)
| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | VARCHAR(36) | PK | 파트너 ID (UUID) |
| name | VARCHAR(255) | NOT NULL | 파트너명 |
| api_key | VARCHAR(255) | UNIQUE | API 키 |
| api_secret_hash | VARCHAR(255) | | API 시크릿 해시 |
| is_active | BOOLEAN | DEFAULT TRUE | 활성 상태 |
| webhook_url | VARCHAR(500) | | 웹훅 URL |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 생성일시 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 수정일시 |

#### partner_fee_policies (파트너 수수료 정책)
| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | INTEGER | PK, AUTO_INCREMENT | 정책 ID |
| partner_id | VARCHAR(36) | FK → partners(id), UNIQUE | 파트너 ID |
| fee_type | ENUM | DEFAULT 'PERCENTAGE' | 수수료 유형 |
| base_fee_rate | NUMERIC(5,4) | DEFAULT 0.001 | 기본 수수료율 |
| min_fee_amount | NUMERIC(18,6) | DEFAULT 0.1 | 최소 수수료 |
| max_fee_amount | NUMERIC(18,6) | | 최대 수수료 |
| withdrawal_fee_rate | NUMERIC(5,4) | DEFAULT 0.001 | 출금 수수료율 |
| internal_transfer_fee_rate | NUMERIC(5,4) | DEFAULT 0 | 내부 이체 수수료율 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 생성일시 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 수정일시 |

### 에너지 시스템 테이블

#### energy_pools (에너지 풀)
| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | INTEGER | PK, AUTO_INCREMENT | 풀 ID |
| name | VARCHAR(255) | NOT NULL | 풀 이름 |
| total_energy | INTEGER | NOT NULL | 총 에너지 |
| available_energy | INTEGER | NOT NULL | 사용 가능 에너지 |
| price_per_energy | NUMERIC(10,6) | NOT NULL | 에너지당 가격 |
| is_active | BOOLEAN | DEFAULT TRUE | 활성 상태 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 생성일시 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 수정일시 |

#### partner_energy_pools (파트너 에너지 풀)
| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | INTEGER | PK, AUTO_INCREMENT | 할당 ID |
| partner_id | VARCHAR(36) | FK → partners(id) | 파트너 ID |
| energy_pool_id | INTEGER | FK → energy_pools(id) | 에너지 풀 ID |
| allocated_energy | INTEGER | NOT NULL | 할당된 에너지 |
| used_energy | INTEGER | DEFAULT 0 | 사용된 에너지 |
| daily_limit | INTEGER | | 일일 한도 |
| priority_level | INTEGER | DEFAULT 1 | 우선순위 레벨 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 생성일시 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 수정일시 |

## 🔧 시스템 특징

### 확장성
- **모듈화된 구조**: 각 기능별로 독립적인 테이블 그룹
- **파트너 시스템**: 다중 파트너사 지원
- **정책 기반**: 유연한 수수료 및 정책 관리

### 보안성
- **사용자 인증**: 이메일 인증 및 관리자 권한
- **API 보안**: 파트너사별 API 키/시크릿
- **잔액 제약**: 음수 잔액 방지 및 잠금 잔액 관리

### 성능
- **인덱스 최적화**: 주요 조회 패턴에 대한 인덱스
- **제약조건**: 데이터 무결성 보장
- **정규화**: 적절한 정규화로 중복 최소화

### 확장 기능
- **에너지 시스템**: TRON 네트워크 에너지 관리
- **분석 시스템**: 거래 분석 및 모니터링
- **알림 시스템**: 실시간 알림 및 경고

## 📈 주요 비즈니스 플로우

### 1. 사용자 가입 및 인증
```
users → email verification → tron_address linking
```

### 2. 입금 프로세스
```
deposits → balances update → transactions record
```

### 3. 출금 프로세스
```
withdrawal request → policy validation → balance lock → 
energy allocation → blockchain transaction → completion
```

### 4. 수수료 계산
```
transaction → partner_fee_policies → fee_tiers → 
user_tiers discount → final fee calculation
```

### 5. 에너지 관리
```
energy_pools → partner allocation → usage tracking → 
price calculation → billing
```

---

## 📊 통계 정보

- **총 테이블 수**: 25개
- **핵심 시스템**: 6개 테이블
- **파트너 시스템**: 8개 테이블  
- **에너지 시스템**: 7개 테이블
- **분석 시스템**: 4개 테이블

## 🔄 최근 업데이트

- **Doc-25**: 에너지 풀 고급 관리 시스템 추가
- **Doc-26**: 파트너사 수수료 및 정책 관리 시스템 추가
- **테이블 분리**: 기존 시스템과 새 기능 간 충돌 방지

---

*이 문서는 자동 생성되었으며, 데이터베이스 구조 변경 시 업데이트가 필요합니다.*
