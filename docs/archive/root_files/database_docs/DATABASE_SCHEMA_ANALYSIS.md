# DantaroWallet Pro 데이터베이스 스키마 분석서

## 📊 시스템 개요

**생성일**: 2025년 7월 8일  
**데이터베이스**: SQLite  
**총 테이블 수**: 26개  
**주요 도메인**: 사용자 관리, 지갑 관리, 거래 처리, 파트너 관리, 에너지 관리, 수수료 정책

---

## 🏗️ 데이터베이스 구조

### 1. 핵심 사용자 도메인 (User Domain)

#### 👥 **users** (사용자)
```sql
- id: INTEGER (PK)
- email: VARCHAR(255) NOT NULL
- password_hash: VARCHAR(255) NOT NULL
- is_active: BOOLEAN NOT NULL
- is_admin: BOOLEAN NOT NULL
- is_verified: BOOLEAN NOT NULL
- tron_address: VARCHAR(42)
- created_at: DATETIME NOT NULL
- updated_at: DATETIME NOT NULL
```

#### 💳 **wallets** (지갑)
```sql
- id: INTEGER (PK)
- user_id: INTEGER NOT NULL → users.id
- address: VARCHAR(42) NOT NULL
- hex_address: VARCHAR(42) NOT NULL
- encrypted_private_key: TEXT NOT NULL
- encryption_salt: VARCHAR(32) NOT NULL
- is_active: BOOLEAN NOT NULL
- is_monitored: BOOLEAN NOT NULL
- wallet_metadata: TEXT
- created_at: DATETIME NOT NULL
- updated_at: DATETIME NOT NULL
```

#### 💰 **balances** (잔고)
```sql
- id: INTEGER (PK)
- user_id: INTEGER NOT NULL → users.id
- asset: VARCHAR(10) NOT NULL
- amount: NUMERIC(18, 6) NOT NULL
- locked_amount: NUMERIC(18, 6) NOT NULL
- created_at: DATETIME NOT NULL
- updated_at: DATETIME NOT NULL
```

---

### 2. 거래 도메인 (Transaction Domain)

#### 🔄 **transactions** (거래)
```sql
- id: INTEGER (PK)
- user_id: INTEGER NOT NULL → users.id
- type: VARCHAR(10) NOT NULL
- direction: VARCHAR(8) NOT NULL
- status: VARCHAR(10) NOT NULL
- asset: VARCHAR(10) NOT NULL
- amount: NUMERIC(18, 6) NOT NULL
- fee: NUMERIC(18, 6) NOT NULL
- related_user_id: INTEGER → users.id
- reference_id: VARCHAR(100)
- tx_hash: VARCHAR(100)
- description: TEXT
- transaction_metadata: TEXT
- created_at: DATETIME NOT NULL
- updated_at: DATETIME NOT NULL
```

#### 📥 **deposits** (입금)
```sql
- id: INTEGER (PK)
- user_id: INTEGER NOT NULL → users.id
- wallet_id: INTEGER NOT NULL → wallets.id
- tx_hash: VARCHAR(64) NOT NULL
- from_address: VARCHAR(42) NOT NULL
- to_address: VARCHAR(42) NOT NULL
- amount: NUMERIC(28, 8) NOT NULL
- token_symbol: VARCHAR(10) NOT NULL
- token_contract: VARCHAR(42)
- block_number: INTEGER NOT NULL
- block_timestamp: INTEGER NOT NULL
- transaction_index: INTEGER NOT NULL
- confirmations: INTEGER NOT NULL
- is_confirmed: BOOLEAN NOT NULL
- min_confirmations: INTEGER NOT NULL
- is_processed: BOOLEAN NOT NULL
- processed_at: VARCHAR
- error_message: VARCHAR
- retry_count: INTEGER NOT NULL
- max_retries: INTEGER NOT NULL
- status: VARCHAR(20)
- created_at: DATETIME NOT NULL
- updated_at: DATETIME NOT NULL
```

#### 📤 **withdrawals** (출금)
```sql
- id: INTEGER (PK)
- user_id: INTEGER NOT NULL → users.id
- to_address: VARCHAR(42) NOT NULL
- amount: NUMERIC(28, 8) NOT NULL
- fee: NUMERIC(28, 8) NOT NULL
- net_amount: NUMERIC(28, 8) NOT NULL
- asset: VARCHAR(10) NOT NULL
- status: VARCHAR(20) NOT NULL
- priority: VARCHAR(10) NOT NULL
- requested_at: DATETIME
- reviewed_at: DATETIME
- approved_at: DATETIME
- processed_at: DATETIME
- completed_at: DATETIME
- reviewed_by: INTEGER → users.id
- approved_by: INTEGER → users.id
- processed_by: INTEGER → users.id
- tx_hash: VARCHAR(100)
- tx_fee: NUMERIC(28, 8)
- notes: TEXT
- admin_notes: TEXT
- rejection_reason: TEXT
- error_message: TEXT
- ip_address: VARCHAR(45)
- user_agent: VARCHAR(200)
- created_at: DATETIME NOT NULL
- updated_at: DATETIME NOT NULL
```

---

### 3. 파트너 도메인 (Partner Domain)

#### 🤝 **partners** (파트너사)
```sql
- id: VARCHAR(36) (PK)
- name: VARCHAR(100) NOT NULL
- display_name: VARCHAR(100)
- domain: VARCHAR(255)
- contact_email: VARCHAR(255) NOT NULL
- contact_phone: VARCHAR(50)
- business_type: VARCHAR(50) NOT NULL
- api_key: VARCHAR(255) NOT NULL
- api_secret_hash: VARCHAR(255) NOT NULL
- previous_api_key: VARCHAR(255)
- api_key_created_at: DATETIME
- status: VARCHAR(20)
- onboarding_status: VARCHAR(50)
- subscription_plan: VARCHAR(50)
- monthly_limit: DECIMAL(18,8)
- commission_rate: DECIMAL(5,4)
- energy_balance: DECIMAL(18,8)
- settings: JSON
- deployment_config: JSON
- last_activity_at: DATETIME
- activated_at: DATETIME
- suspended_at: DATETIME
- created_at: DATETIME
- updated_at: DATETIME
```

#### 💼 **partner_wallets** (파트너 지갑)
```sql
- id: VARCHAR(36) (PK)
- partner_id: VARCHAR(36) NOT NULL → partners.id
- wallet_type: VARCHAR(12) NOT NULL
- address: VARCHAR(42) NOT NULL
- label: VARCHAR(100)
- is_active: BOOLEAN NOT NULL
- is_primary: BOOLEAN NOT NULL
- balance_usdt: NUMERIC(20, 6) NOT NULL
- balance_trx: NUMERIC(20, 6) NOT NULL
- last_sync_at: DATETIME
- metadata: JSON
- created_at: DATETIME NOT NULL
- updated_at: DATETIME NOT NULL
```

---

### 4. 에너지 관리 도메인 (Energy Management Domain)

#### ⚡ **energy_pools** (에너지 풀)
```sql
- id: INTEGER (PK)
- pool_name: VARCHAR(100) NOT NULL
- wallet_address: VARCHAR(50) NOT NULL
- owner_address: VARCHAR(34)
- total_frozen_trx: NUMERIC(18, 6) NOT NULL
- frozen_trx: NUMERIC(20,6)
- frozen_for_energy: NUMERIC(18, 6) NOT NULL
- frozen_for_bandwidth: NUMERIC(18, 6) NOT NULL
- total_energy: INTEGER
- available_energy: BIGINT NOT NULL
- used_energy: INTEGER
- available_bandwidth: BIGINT NOT NULL
- daily_energy_consumption: BIGINT NOT NULL
- daily_bandwidth_consumption: BIGINT NOT NULL
- status: VARCHAR(20)
- low_threshold: INTEGER
- critical_threshold: INTEGER
- auto_refreeze_enabled: BOOLEAN
- auto_refill: BOOLEAN
- auto_refill_amount: NUMERIC(20,6)
- auto_refill_trigger: INTEGER
- energy_threshold: BIGINT NOT NULL
- bandwidth_threshold: BIGINT NOT NULL
- last_freeze_cost: NUMERIC(18, 6)
- total_freeze_cost: NUMERIC(18, 6) NOT NULL
- daily_consumption: TEXT
- peak_usage_hours: TEXT
- last_refilled_at: DATETIME
- last_checked_at: DATETIME
- is_active: BOOLEAN
- last_updated: DATETIME
- notes: TEXT
- created_at: DATETIME NOT NULL
- updated_at: DATETIME NOT NULL
```

#### 🔋 **partner_energy_pools** (파트너 에너지 풀)
```sql
- id: INTEGER (PK)
- partner_id: INTEGER NOT NULL
- wallet_address: VARCHAR(42) NOT NULL
- total_energy: NUMERIC(20, 0)
- available_energy: NUMERIC(20, 0)
- used_energy: NUMERIC(20, 0)
- energy_limit: NUMERIC(20, 0)
- total_bandwidth: NUMERIC(20, 0)
- available_bandwidth: NUMERIC(20, 0)
- frozen_trx_amount: NUMERIC(18, 6)
- frozen_for_energy: NUMERIC(18, 6)
- frozen_for_bandwidth: NUMERIC(18, 6)
- status: VARCHAR(20)
- depletion_estimated_at: DATETIME
- daily_average_usage: NUMERIC(20, 0)
- peak_usage_hour: INTEGER
- warning_threshold: INTEGER
- critical_threshold: INTEGER
- auto_response_enabled: BOOLEAN
- last_checked_at: DATETIME
- last_alert_sent_at: DATETIME
- metrics_history: JSON
- created_at: DATETIME
- updated_at: DATETIME
```

#### 🚨 **energy_alerts** (에너지 알림)
```sql
- id: INTEGER (PK)
- energy_pool_id: INTEGER NOT NULL → partner_energy_pools.id
- alert_type: VARCHAR(50) NOT NULL
- severity: VARCHAR(20) NOT NULL
- title: VARCHAR(200) NOT NULL
- message: TEXT NOT NULL
- threshold_value: NUMERIC(10, 2)
- current_value: NUMERIC(10, 2)
- estimated_hours_remaining: INTEGER
- sent_via: JSON
- sent_to: JSON
- sent_at: DATETIME
- acknowledged: BOOLEAN
- acknowledged_at: DATETIME
- created_at: DATETIME
```

#### 🔮 **energy_predictions** (에너지 예측)
```sql
- id: INTEGER (PK)
- energy_pool_id: INTEGER NOT NULL → partner_energy_pools.id
- prediction_date: DATETIME NOT NULL
- predicted_usage: NUMERIC(20, 0) NOT NULL
- predicted_depletion: DATETIME
- confidence_score: NUMERIC(5, 2)
- historical_pattern: JSON
- trend_factors: JSON
- seasonal_adjustments: JSON
- recommended_action: VARCHAR(100)
- action_priority: VARCHAR(20)
- created_at: DATETIME
```

#### 📊 **energy_usage_history** (에너지 사용 이력)
```sql
- id: VARCHAR(36) (PK)
- partner_id: VARCHAR(36) NOT NULL → partners.id
- transaction_type: VARCHAR(50) NOT NULL
- energy_amount: INTEGER NOT NULL
- transaction_id: VARCHAR(100)
- description: VARCHAR(255)
- created_at: DATETIME NOT NULL
```

#### 📈 **energy_usage_logs** (에너지 사용 로그)
```sql
- id: INTEGER (PK)
- energy_pool_id: INTEGER NOT NULL
- transaction_hash: VARCHAR(64)
- transaction_type: VARCHAR(50) NOT NULL
- energy_consumed: BIGINT NOT NULL
- bandwidth_consumed: BIGINT NOT NULL
- trx_cost_equivalent: NUMERIC(18, 6)
- user_id: INTEGER
- from_address: VARCHAR(50)
- to_address: VARCHAR(50)
- amount: NUMERIC(18, 6)
- asset: VARCHAR(20)
- block_number: BIGINT
- timestamp: DATETIME NOT NULL
- notes: TEXT
- created_at: DATETIME NOT NULL
```

#### 📋 **partner_energy_usage_logs** (파트너 에너지 사용 로그)
```sql
- id: INTEGER (PK)
- energy_pool_id: INTEGER NOT NULL → partner_energy_pools.id
- transaction_type: VARCHAR(50) NOT NULL
- transaction_hash: VARCHAR(66)
- energy_consumed: NUMERIC(20, 0) NOT NULL
- bandwidth_consumed: NUMERIC(20, 0)
- energy_unit_price: NUMERIC(10, 6)
- total_cost: NUMERIC(18, 6)
- created_at: DATETIME
```

#### 💹 **energy_price_history** (에너지 가격 이력)
```sql
- id: INTEGER (PK)
- trx_price_usd: NUMERIC(18, 8) NOT NULL
- energy_per_trx: BIGINT NOT NULL
- bandwidth_per_trx: BIGINT NOT NULL
- total_frozen_trx: NUMERIC(18, 6)
- energy_utilization: NUMERIC(5, 2)
- usdt_transfer_cost: NUMERIC(18, 6)
- trx_transfer_cost: NUMERIC(18, 6)
- recorded_at: DATETIME NOT NULL
- source: VARCHAR(50)
- created_at: DATETIME NOT NULL
```

---

### 5. 수수료 및 정책 도메인 (Fee & Policy Domain)

#### 💸 **partner_fee_policies** (파트너 수수료 정책)
```sql
- id: INTEGER (PK)
- partner_id: VARCHAR(36) NOT NULL → partners.id
- fee_type: VARCHAR(10)
- base_fee_rate: NUMERIC(5, 4)
- min_fee_amount: NUMERIC(18, 6)
- max_fee_amount: NUMERIC(18, 6)
- withdrawal_fee_rate: NUMERIC(5, 4)
- internal_transfer_fee_rate: NUMERIC(5, 4)
- vip_discount_rates: JSON
- promotion_active: BOOLEAN
- promotion_fee_rate: NUMERIC(5, 4)
- promotion_end_date: DATETIME
- platform_share_rate: NUMERIC(5, 4)
- created_at: DATETIME
- updated_at: DATETIME
```

#### 📊 **fee_tiers** (구간별 수수료)
```sql
- id: INTEGER (PK)
- fee_policy_id: INTEGER NOT NULL → partner_fee_policies.id
- min_amount: NUMERIC(18, 6) NOT NULL
- max_amount: NUMERIC(18, 6)
- fee_rate: NUMERIC(5, 4) NOT NULL
- fixed_fee: NUMERIC(18, 6)
- created_at: DATETIME
```

#### 📤 **partner_withdrawal_policies** (파트너 출금 정책)
```sql
- id: INTEGER (PK)
- partner_id: VARCHAR(36) NOT NULL → partners.id
- policy_type: VARCHAR(8)
- realtime_enabled: BOOLEAN
- realtime_max_amount: NUMERIC(18, 6)
- auto_approve_enabled: BOOLEAN
- auto_approve_max_amount: NUMERIC(18, 6)
- batch_enabled: BOOLEAN
- batch_schedule: JSON
- batch_min_amount: NUMERIC(18, 6)
- daily_limit_per_user: NUMERIC(18, 6)
- daily_limit_total: NUMERIC(18, 6)
- single_transaction_limit: NUMERIC(18, 6)
- whitelist_required: BOOLEAN
- whitelist_addresses: JSON
- require_2fa: BOOLEAN
- confirmation_blocks: INTEGER
- created_at: DATETIME
- updated_at: DATETIME
```

#### ⚡ **partner_energy_policies** (파트너 에너지 정책)
```sql
- id: INTEGER (PK)
- partner_id: VARCHAR(36) NOT NULL → partners.id
- default_policy: VARCHAR(14)
- trx_payment_enabled: BOOLEAN
- trx_payment_markup: NUMERIC(5, 4)
- trx_payment_max_fee: NUMERIC(18, 6)
- queue_enabled: BOOLEAN
- queue_max_wait_hours: INTEGER
- queue_notification_enabled: BOOLEAN
- priority_queue_enabled: BOOLEAN
- vip_priority_levels: JSON
- energy_saving_enabled: BOOLEAN
- energy_saving_threshold: INTEGER
- created_at: DATETIME
- updated_at: DATETIME
```

#### 🏆 **user_tiers** (사용자 등급)
```sql
- id: INTEGER (PK)
- partner_id: VARCHAR(36) NOT NULL → partners.id
- tier_name: VARCHAR(50) NOT NULL
- tier_level: INTEGER NOT NULL
- min_volume: NUMERIC(18, 6)
- fee_discount_rate: NUMERIC(5, 4)
- withdrawal_limit_multiplier: NUMERIC(5, 2)
- benefits: JSON
- upgrade_conditions: JSON
- created_at: DATETIME
- updated_at: DATETIME
```

#### 📋 **fee_calculation_logs** (수수료 계산 로그)
```sql
- id: INTEGER (PK)
- partner_id: VARCHAR(36) NOT NULL → partners.id
- transaction_id: VARCHAR(100)
- transaction_amount: NUMERIC(18, 6) NOT NULL
- base_fee_rate: NUMERIC(5, 4)
- applied_fee_rate: NUMERIC(5, 4)
- discount_rate: NUMERIC(5, 4)
- calculated_fee: NUMERIC(18, 6)
- platform_share: NUMERIC(18, 6)
- partner_share: NUMERIC(18, 6)
- policy_details: JSON
- created_at: DATETIME
```

#### 📝 **partner_policy_calculation_logs** (파트너 정책 계산 로그)
```sql
- id: INTEGER (PK)
- partner_id: VARCHAR(36) NOT NULL → partners.id
- user_id: INTEGER
- calculation_type: VARCHAR(50) NOT NULL
- request_data: TEXT
- result_data: TEXT
- calculated_at: DATETIME
- admin_id: INTEGER
```

---

### 6. 분석 및 알림 도메인 (Analytics & Alert Domain)

#### 📊 **transactionsummarys** (거래 요약)
```sql
- id: INTEGER (PK)
- user_id: INTEGER NOT NULL → users.id
- period_type: VARCHAR(20) NOT NULL
- period_start: DATETIME NOT NULL
- period_end: DATETIME NOT NULL
- trx_deposits_count: INTEGER NOT NULL
- trx_deposits_amount: NUMERIC(18, 6) NOT NULL
- trx_withdrawals_count: INTEGER NOT NULL
- trx_withdrawals_amount: NUMERIC(18, 6) NOT NULL
- usdt_deposits_count: INTEGER NOT NULL
- usdt_deposits_amount: NUMERIC(18, 6) NOT NULL
- usdt_withdrawals_count: INTEGER NOT NULL
- usdt_withdrawals_amount: NUMERIC(18, 6) NOT NULL
- total_transactions: INTEGER NOT NULL
- total_volume_usd: NUMERIC(18, 6) NOT NULL
- total_fees_trx: NUMERIC(18, 6) NOT NULL
- total_fees_usdt: NUMERIC(18, 6) NOT NULL
- created_at: DATETIME NOT NULL
- updated_at: DATETIME NOT NULL
```

#### 🚨 **transactionalerts** (거래 알림)
```sql
- id: INTEGER (PK)
- user_id: INTEGER NOT NULL → users.id
- transaction_id: INTEGER → transactions.id
- alert_type: VARCHAR(50) NOT NULL
- level: VARCHAR(20) NOT NULL
- title: VARCHAR(200) NOT NULL
- description: TEXT NOT NULL
- is_resolved: BOOLEAN NOT NULL
- resolved_by: INTEGER → users.id
- resolved_at: DATETIME
- resolution_notes: TEXT
- alert_data: TEXT
- created_at: DATETIME NOT NULL
- updated_at: DATETIME NOT NULL
```

#### 🖥️ **system_transaction_alerts** (시스템 거래 알림)
```sql
- id: INTEGER (PK)
- title: VARCHAR(200) NOT NULL
- message: TEXT NOT NULL
- alert_type: VARCHAR(50) NOT NULL
- level: VARCHAR(20) NOT NULL
- is_active: BOOLEAN NOT NULL
- is_resolved: BOOLEAN NOT NULL
- resolved_by: INTEGER → users.id
- resolved_at: DATETIME
- alert_data: TEXT
- created_at: DATETIME NOT NULL
- updated_at: DATETIME NOT NULL
```

---

## 🔗 관계 다이어그램 (ERD)

### 핵심 관계 매핑

```
users (1) ----< wallets (N)
users (1) ----< balances (N)
users (1) ----< transactions (N)
users (1) ----< deposits (N)
users (1) ----< withdrawals (N)
users (1) ----< transactionsummarys (N)
users (1) ----< transactionalerts (N)

partners (1) ----< partner_wallets (N)
partners (1) ----< partner_fee_policies (1)
partners (1) ----< partner_withdrawal_policies (1)
partners (1) ----< partner_energy_policies (1)
partners (1) ----< user_tiers (N)
partners (1) ----< energy_usage_history (N)
partners (1) ----< fee_calculation_logs (N)
partners (1) ----< partner_policy_calculation_logs (N)

partner_fee_policies (1) ----< fee_tiers (N)

partner_energy_pools (1) ----< energy_alerts (N)
partner_energy_pools (1) ----< energy_predictions (N)
partner_energy_pools (1) ----< partner_energy_usage_logs (N)

wallets (1) ----< deposits (N)
transactions (1) ----< transactionalerts (N)
```

---

## 🎯 주요 특징

### 1. **다중 도메인 아키텍처**
- 사용자 관리 (User Management)
- 지갑 관리 (Wallet Management)  
- 거래 처리 (Transaction Processing)
- 파트너 관리 (Partner Management)
- 에너지 관리 (Energy Management)
- 수수료 정책 (Fee Policy)

### 2. **고급 에너지 관리 시스템**
- 실시간 에너지 모니터링
- 예측 분석 및 알림
- 파트너별 에너지 풀 관리
- 에너지 사용량 추적

### 3. **유연한 수수료 시스템**
- 파트너별 맞춤 수수료 정책
- 구간별 차등 수수료
- 사용자 등급별 할인
- 상세한 계산 로그

### 4. **포괄적인 알림 시스템**
- 거래 알림
- 시스템 알림
- 에너지 부족 알림
- 실시간 모니터링

### 5. **확장 가능한 설계**
- JSON 필드를 통한 유연한 메타데이터
- 파트너별 설정 관리
- 모듈화된 정책 시스템

---

## 📈 통계

- **총 테이블**: 26개
- **총 관계**: 20+ 개
- **JSON 필드**: 15개 (유연한 설정 관리)
- **감사 로그**: 7개 테이블
- **인덱스**: 자동 생성 + 커스텀

---

**생성자**: DantaroWallet Pro Development Team  
**문서 버전**: 1.0  
**마지막 업데이트**: 2025년 7월 8일
