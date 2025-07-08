# DantaroWallet Pro - 데이터베이스 ERD

> 생성일: 2025-07-08T11:54:26.557075  
> 데이터베이스: dev.db

## 📊 데이터베이스 개요

- **총 테이블 수**: 27개
- **총 관계 수**: 27개
- **총 데이터 행**: 30개

## 🏗️ 모듈별 테이블 구조

### User Auth 모듈

#### users
- **행 수**: 8개
- **컬럼 수**: 9개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| email | VARCHAR(255) | ❌ | - |  |
| password_hash | VARCHAR(255) | ❌ | - |  |
| is_active | BOOLEAN | ❌ | - |  |
| is_admin | BOOLEAN | ❌ | - |  |
| is_verified | BOOLEAN | ❌ | - |  |
| tron_address | VARCHAR(42) | ✅ | - |  |
| id | INTEGER | ❌ | - | 🔑 |
| created_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |
| updated_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |

### Partner 모듈

#### partner_energy_policies
- **행 수**: 0개
- **컬럼 수**: 15개
- **외래키**: 1개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| id | INTEGER | ❌ | - | 🔑 |
| partner_id | VARCHAR(36) | ❌ | - |  |
| default_policy | VARCHAR(14) | ✅ | - |  |
| trx_payment_enabled | BOOLEAN | ✅ | - |  |
| trx_payment_markup | NUMERIC(5, 4) | ✅ | - |  |
| trx_payment_max_fee | NUMERIC(18, 6) | ✅ | - |  |
| queue_enabled | BOOLEAN | ✅ | - |  |
| queue_max_wait_hours | INTEGER | ✅ | - |  |
| queue_notification_enabled | BOOLEAN | ✅ | - |  |
| priority_queue_enabled | BOOLEAN | ✅ | - |  |
| vip_priority_levels | JSON | ✅ | - |  |
| energy_saving_enabled | BOOLEAN | ✅ | - |  |
| energy_saving_threshold | INTEGER | ✅ | - |  |
| created_at | DATETIME | ✅ | now() |  |
| updated_at | DATETIME | ✅ | - |  |

#### partner_energy_pools
- **행 수**: 0개
- **컬럼 수**: 24개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| id | INTEGER | ❌ | - | 🔑 |
| partner_id | INTEGER | ❌ | - |  |
| wallet_address | VARCHAR(42) | ❌ | - |  |
| total_energy | NUMERIC(20, 0) | ✅ | - |  |
| available_energy | NUMERIC(20, 0) | ✅ | - |  |
| used_energy | NUMERIC(20, 0) | ✅ | - |  |
| energy_limit | NUMERIC(20, 0) | ✅ | - |  |
| total_bandwidth | NUMERIC(20, 0) | ✅ | - |  |
| available_bandwidth | NUMERIC(20, 0) | ✅ | - |  |
| frozen_trx_amount | NUMERIC(18, 6) | ✅ | - |  |
| frozen_for_energy | NUMERIC(18, 6) | ✅ | - |  |
| frozen_for_bandwidth | NUMERIC(18, 6) | ✅ | - |  |
| status | VARCHAR(20) | ✅ | - |  |
| depletion_estimated_at | DATETIME | ✅ | - |  |
| daily_average_usage | NUMERIC(20, 0) | ✅ | - |  |
| peak_usage_hour | INTEGER | ✅ | - |  |
| warning_threshold | INTEGER | ✅ | - |  |
| critical_threshold | INTEGER | ✅ | - |  |
| auto_response_enabled | BOOLEAN | ✅ | - |  |
| last_checked_at | DATETIME | ✅ | - |  |
| last_alert_sent_at | DATETIME | ✅ | - |  |
| metrics_history | JSON | ✅ | - |  |
| created_at | DATETIME | ✅ | CURRENT_TIMESTAMP |  |
| updated_at | DATETIME | ✅ | - |  |

#### partner_energy_usage_logs
- **행 수**: 0개
- **컬럼 수**: 9개
- **외래키**: 1개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| id | INTEGER | ❌ | - | 🔑 |
| energy_pool_id | INTEGER | ❌ | - |  |
| transaction_type | VARCHAR(50) | ❌ | - |  |
| transaction_hash | VARCHAR(66) | ✅ | - |  |
| energy_consumed | NUMERIC(20, 0) | ❌ | - |  |
| bandwidth_consumed | NUMERIC(20, 0) | ✅ | - |  |
| energy_unit_price | NUMERIC(10, 6) | ✅ | - |  |
| total_cost | NUMERIC(18, 6) | ✅ | - |  |
| created_at | DATETIME | ✅ | CURRENT_TIMESTAMP |  |

#### partner_fee_policies
- **행 수**: 0개
- **컬럼 수**: 15개
- **외래키**: 1개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| id | INTEGER | ❌ | - | 🔑 |
| partner_id | VARCHAR(36) | ❌ | - |  |
| fee_type | VARCHAR(10) | ✅ | - |  |
| base_fee_rate | NUMERIC(5, 4) | ✅ | - |  |
| min_fee_amount | NUMERIC(18, 6) | ✅ | - |  |
| max_fee_amount | NUMERIC(18, 6) | ✅ | - |  |
| withdrawal_fee_rate | NUMERIC(5, 4) | ✅ | - |  |
| internal_transfer_fee_rate | NUMERIC(5, 4) | ✅ | - |  |
| vip_discount_rates | JSON | ✅ | - |  |
| promotion_active | BOOLEAN | ✅ | - |  |
| promotion_fee_rate | NUMERIC(5, 4) | ✅ | - |  |
| promotion_end_date | DATETIME | ✅ | - |  |
| platform_share_rate | NUMERIC(5, 4) | ✅ | - |  |
| created_at | DATETIME | ✅ | now() |  |
| updated_at | DATETIME | ✅ | - |  |

#### partner_policy_calculation_logs
- **행 수**: 0개
- **컬럼 수**: 8개
- **외래키**: 1개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| id | INTEGER | ✅ | - | 🔑 |
| partner_id | VARCHAR(36) | ❌ | - |  |
| user_id | INTEGER | ✅ | - |  |
| calculation_type | VARCHAR(50) | ❌ | - |  |
| request_data | TEXT | ✅ | - |  |
| result_data | TEXT | ✅ | - |  |
| calculated_at | DATETIME | ✅ | CURRENT_TIMESTAMP |  |
| admin_id | INTEGER | ✅ | - |  |

#### partner_wallets
- **행 수**: 0개
- **컬럼 수**: 13개
- **외래키**: 1개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| id | VARCHAR(36) | ❌ | - | 🔑 |
| partner_id | VARCHAR(36) | ❌ | - |  |
| wallet_type | VARCHAR(12) | ❌ | - |  |
| address | VARCHAR(42) | ❌ | - |  |
| label | VARCHAR(100) | ✅ | - |  |
| is_active | BOOLEAN | ❌ | - |  |
| is_primary | BOOLEAN | ❌ | - |  |
| balance_usdt | NUMERIC(20, 6) | ❌ | - |  |
| balance_trx | NUMERIC(20, 6) | ❌ | - |  |
| last_sync_at | DATETIME | ✅ | - |  |
| metadata | JSON | ✅ | - |  |
| created_at | DATETIME | ❌ | - |  |
| updated_at | DATETIME | ❌ | - |  |

#### partner_withdrawal_policies
- **행 수**: 0개
- **컬럼 수**: 19개
- **외래키**: 1개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| id | INTEGER | ❌ | - | 🔑 |
| partner_id | VARCHAR(36) | ❌ | - |  |
| policy_type | VARCHAR(8) | ✅ | - |  |
| realtime_enabled | BOOLEAN | ✅ | - |  |
| realtime_max_amount | NUMERIC(18, 6) | ✅ | - |  |
| auto_approve_enabled | BOOLEAN | ✅ | - |  |
| auto_approve_max_amount | NUMERIC(18, 6) | ✅ | - |  |
| batch_enabled | BOOLEAN | ✅ | - |  |
| batch_schedule | JSON | ✅ | - |  |
| batch_min_amount | NUMERIC(18, 6) | ✅ | - |  |
| daily_limit_per_user | NUMERIC(18, 6) | ✅ | - |  |
| daily_limit_total | NUMERIC(18, 6) | ✅ | - |  |
| single_transaction_limit | NUMERIC(18, 6) | ✅ | - |  |
| whitelist_required | BOOLEAN | ✅ | - |  |
| whitelist_addresses | JSON | ✅ | - |  |
| require_2fa | BOOLEAN | ✅ | - |  |
| confirmation_blocks | INTEGER | ✅ | - |  |
| created_at | DATETIME | ✅ | now() |  |
| updated_at | DATETIME | ✅ | - |  |

#### partners
- **행 수**: 3개
- **컬럼 수**: 24개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| id | VARCHAR(36) | ✅ | - | 🔑 |
| name | VARCHAR(100) | ❌ | - |  |
| display_name | VARCHAR(100) | ✅ | - |  |
| domain | VARCHAR(255) | ✅ | - |  |
| contact_email | VARCHAR(255) | ❌ | - |  |
| contact_phone | VARCHAR(50) | ✅ | - |  |
| business_type | VARCHAR(50) | ❌ | - |  |
| api_key | VARCHAR(255) | ❌ | - |  |
| api_secret_hash | VARCHAR(255) | ❌ | - |  |
| previous_api_key | VARCHAR(255) | ✅ | - |  |
| api_key_created_at | DATETIME | ✅ | - |  |
| status | VARCHAR(20) | ✅ | 'pending' |  |
| onboarding_status | VARCHAR(50) | ✅ | 'pending' |  |
| subscription_plan | VARCHAR(50) | ✅ | 'basic' |  |
| monthly_limit | DECIMAL(18,8) | ✅ | - |  |
| commission_rate | DECIMAL(5,4) | ✅ | 0 |  |
| energy_balance | DECIMAL(18,8) | ✅ | 0 |  |
| settings | JSON | ✅ | '{}' |  |
| deployment_config | JSON | ✅ | '{}' |  |
| last_activity_at | DATETIME | ✅ | - |  |
| activated_at | DATETIME | ✅ | - |  |
| suspended_at | DATETIME | ✅ | - |  |
| created_at | DATETIME | ✅ | CURRENT_TIMESTAMP |  |
| updated_at | DATETIME | ✅ | CURRENT_TIMESTAMP |  |

### Wallet 모듈

#### wallets
- **행 수**: 4개
- **컬럼 수**: 11개
- **외래키**: 1개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| user_id | INTEGER | ❌ | - |  |
| address | VARCHAR(42) | ❌ | - |  |
| hex_address | VARCHAR(42) | ❌ | - |  |
| encrypted_private_key | TEXT | ❌ | - |  |
| encryption_salt | VARCHAR(32) | ❌ | - |  |
| is_active | BOOLEAN | ❌ | - |  |
| is_monitored | BOOLEAN | ❌ | - |  |
| wallet_metadata | TEXT | ✅ | - |  |
| id | INTEGER | ❌ | - | 🔑 |
| created_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |
| updated_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |

### Transaction 모듈

#### transactions
- **행 수**: 0개
- **컬럼 수**: 15개
- **외래키**: 2개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| user_id | INTEGER | ❌ | - |  |
| type | VARCHAR(10) | ❌ | - |  |
| direction | VARCHAR(8) | ❌ | - |  |
| status | VARCHAR(10) | ❌ | - |  |
| asset | VARCHAR(10) | ❌ | - |  |
| amount | NUMERIC(18, 6) | ❌ | - |  |
| fee | NUMERIC(18, 6) | ❌ | - |  |
| related_user_id | INTEGER | ✅ | - |  |
| reference_id | VARCHAR(100) | ✅ | - |  |
| tx_hash | VARCHAR(100) | ✅ | - |  |
| description | TEXT | ✅ | - |  |
| transaction_metadata | TEXT | ✅ | - |  |
| id | INTEGER | ❌ | - | 🔑 |
| created_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |
| updated_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |

### Deposit 모듈

#### deposits
- **행 수**: 0개
- **컬럼 수**: 23개
- **외래키**: 2개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| tx_hash | VARCHAR(64) | ❌ | - |  |
| from_address | VARCHAR(42) | ❌ | - |  |
| to_address | VARCHAR(42) | ❌ | - |  |
| amount | NUMERIC(28, 8) | ❌ | - |  |
| token_symbol | VARCHAR(10) | ❌ | - |  |
| token_contract | VARCHAR(42) | ✅ | - |  |
| block_number | INTEGER | ❌ | - |  |
| block_timestamp | INTEGER | ❌ | - |  |
| transaction_index | INTEGER | ❌ | - |  |
| confirmations | INTEGER | ❌ | - |  |
| is_confirmed | BOOLEAN | ❌ | - |  |
| min_confirmations | INTEGER | ❌ | - |  |
| is_processed | BOOLEAN | ❌ | - |  |
| processed_at | VARCHAR | ✅ | - |  |
| user_id | INTEGER | ❌ | - |  |
| wallet_id | INTEGER | ❌ | - |  |
| error_message | VARCHAR | ✅ | - |  |
| retry_count | INTEGER | ❌ | - |  |
| max_retries | INTEGER | ❌ | - |  |
| id | INTEGER | ❌ | - | 🔑 |
| created_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |
| updated_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |
| status | VARCHAR(20) | ✅ | "pending" |  |

### Withdrawal 모듈

#### withdrawals
- **행 수**: 0개
- **컬럼 수**: 27개
- **외래키**: 4개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| user_id | INTEGER | ❌ | - |  |
| to_address | VARCHAR(42) | ❌ | - |  |
| amount | NUMERIC(28, 8) | ❌ | - |  |
| fee | NUMERIC(28, 8) | ❌ | - |  |
| net_amount | NUMERIC(28, 8) | ❌ | - |  |
| asset | VARCHAR(10) | ❌ | - |  |
| status | VARCHAR(20) | ❌ | - |  |
| priority | VARCHAR(10) | ❌ | - |  |
| requested_at | DATETIME | ✅ | - |  |
| reviewed_at | DATETIME | ✅ | - |  |
| approved_at | DATETIME | ✅ | - |  |
| processed_at | DATETIME | ✅ | - |  |
| completed_at | DATETIME | ✅ | - |  |
| reviewed_by | INTEGER | ✅ | - |  |
| approved_by | INTEGER | ✅ | - |  |
| processed_by | INTEGER | ✅ | - |  |
| tx_hash | VARCHAR(100) | ✅ | - |  |
| tx_fee | NUMERIC(28, 8) | ✅ | - |  |
| notes | TEXT | ✅ | - |  |
| admin_notes | TEXT | ✅ | - |  |
| rejection_reason | TEXT | ✅ | - |  |
| error_message | TEXT | ✅ | - |  |
| ip_address | VARCHAR(45) | ✅ | - |  |
| user_agent | VARCHAR(200) | ✅ | - |  |
| id | INTEGER | ❌ | - | 🔑 |
| created_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |
| updated_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |

### Energy 모듈

#### energy_alerts
- **행 수**: 0개
- **컬럼 수**: 15개
- **외래키**: 1개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| id | INTEGER | ❌ | - | 🔑 |
| energy_pool_id | INTEGER | ❌ | - |  |
| alert_type | VARCHAR(50) | ❌ | - |  |
| severity | VARCHAR(20) | ❌ | - |  |
| title | VARCHAR(200) | ❌ | - |  |
| message | TEXT | ❌ | - |  |
| threshold_value | NUMERIC(10, 2) | ✅ | - |  |
| current_value | NUMERIC(10, 2) | ✅ | - |  |
| estimated_hours_remaining | INTEGER | ✅ | - |  |
| sent_via | JSON | ✅ | - |  |
| sent_to | JSON | ✅ | - |  |
| sent_at | DATETIME | ✅ | CURRENT_TIMESTAMP |  |
| acknowledged | BOOLEAN | ✅ | - |  |
| acknowledged_at | DATETIME | ✅ | - |  |
| created_at | DATETIME | ✅ | CURRENT_TIMESTAMP |  |

#### energy_pools
- **행 수**: 1개
- **컬럼 수**: 34개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| id | INTEGER | ❌ | - | 🔑 |
| pool_name | VARCHAR(100) | ❌ | - |  |
| wallet_address | VARCHAR(50) | ❌ | - |  |
| total_frozen_trx | NUMERIC(18, 6) | ❌ | - |  |
| frozen_for_energy | NUMERIC(18, 6) | ❌ | - |  |
| frozen_for_bandwidth | NUMERIC(18, 6) | ❌ | - |  |
| available_energy | BIGINT | ❌ | - |  |
| available_bandwidth | BIGINT | ❌ | - |  |
| daily_energy_consumption | BIGINT | ❌ | - |  |
| daily_bandwidth_consumption | BIGINT | ❌ | - |  |
| auto_refreeze_enabled | BOOLEAN | ✅ | - |  |
| energy_threshold | BIGINT | ❌ | - |  |
| bandwidth_threshold | BIGINT | ❌ | - |  |
| last_freeze_cost | NUMERIC(18, 6) | ✅ | - |  |
| total_freeze_cost | NUMERIC(18, 6) | ❌ | - |  |
| is_active | BOOLEAN | ✅ | - |  |
| last_updated | DATETIME | ✅ | CURRENT_TIMESTAMP |  |
| notes | TEXT | ✅ | - |  |
| created_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |
| updated_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |
| owner_address | VARCHAR(34) | ✅ | - |  |
| frozen_trx | NUMERIC(20,6) | ✅ | 0 |  |
| total_energy | INTEGER | ✅ | 0 |  |
| used_energy | INTEGER | ✅ | 0 |  |
| status | VARCHAR(20) | ✅ | "active" |  |
| low_threshold | INTEGER | ✅ | 20 |  |
| critical_threshold | INTEGER | ✅ | 10 |  |
| auto_refill | BOOLEAN | ✅ | 0 |  |
| auto_refill_amount | NUMERIC(20,6) | ✅ | 10000 |  |
| auto_refill_trigger | INTEGER | ✅ | 15 |  |
| daily_consumption | TEXT | ✅ | - |  |
| peak_usage_hours | TEXT | ✅ | - |  |
| last_refilled_at | DATETIME | ✅ | - |  |
| last_checked_at | DATETIME | ✅ | - |  |

#### energy_predictions
- **행 수**: 0개
- **컬럼 수**: 12개
- **외래키**: 1개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| id | INTEGER | ❌ | - | 🔑 |
| energy_pool_id | INTEGER | ❌ | - |  |
| prediction_date | DATETIME | ❌ | - |  |
| predicted_usage | NUMERIC(20, 0) | ❌ | - |  |
| predicted_depletion | DATETIME | ✅ | - |  |
| confidence_score | NUMERIC(5, 2) | ✅ | - |  |
| historical_pattern | JSON | ✅ | - |  |
| trend_factors | JSON | ✅ | - |  |
| seasonal_adjustments | JSON | ✅ | - |  |
| recommended_action | VARCHAR(100) | ✅ | - |  |
| action_priority | VARCHAR(20) | ✅ | - |  |
| created_at | DATETIME | ✅ | CURRENT_TIMESTAMP |  |

#### energy_price_history
- **행 수**: 1개
- **컬럼 수**: 11개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| id | INTEGER | ❌ | - | 🔑 |
| trx_price_usd | NUMERIC(18, 8) | ❌ | - |  |
| energy_per_trx | BIGINT | ❌ | - |  |
| bandwidth_per_trx | BIGINT | ❌ | - |  |
| total_frozen_trx | NUMERIC(18, 6) | ✅ | - |  |
| energy_utilization | NUMERIC(5, 2) | ✅ | - |  |
| usdt_transfer_cost | NUMERIC(18, 6) | ✅ | - |  |
| trx_transfer_cost | NUMERIC(18, 6) | ✅ | - |  |
| recorded_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |
| source | VARCHAR(50) | ✅ | - |  |
| created_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |

#### energy_usage_history
- **행 수**: 0개
- **컬럼 수**: 7개
- **외래키**: 1개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| id | VARCHAR(36) | ❌ | - | 🔑 |
| partner_id | VARCHAR(36) | ❌ | - |  |
| transaction_type | VARCHAR(50) | ❌ | - |  |
| energy_amount | INTEGER | ❌ | - |  |
| transaction_id | VARCHAR(100) | ✅ | - |  |
| description | VARCHAR(255) | ✅ | - |  |
| created_at | DATETIME | ❌ | - |  |

#### energy_usage_logs
- **행 수**: 5개
- **컬럼 수**: 16개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| id | INTEGER | ❌ | - | 🔑 |
| energy_pool_id | INTEGER | ❌ | - |  |
| transaction_hash | VARCHAR(64) | ✅ | - |  |
| transaction_type | VARCHAR(50) | ❌ | - |  |
| energy_consumed | BIGINT | ❌ | - |  |
| bandwidth_consumed | BIGINT | ❌ | - |  |
| trx_cost_equivalent | NUMERIC(18, 6) | ✅ | - |  |
| user_id | INTEGER | ✅ | - |  |
| from_address | VARCHAR(50) | ✅ | - |  |
| to_address | VARCHAR(50) | ✅ | - |  |
| amount | NUMERIC(18, 6) | ✅ | - |  |
| asset | VARCHAR(20) | ✅ | - |  |
| block_number | BIGINT | ✅ | - |  |
| timestamp | DATETIME | ❌ | - |  |
| notes | TEXT | ✅ | - |  |
| created_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |

### Fee Policy 모듈

#### fee_calculation_logs
- **행 수**: 0개
- **컬럼 수**: 12개
- **외래키**: 1개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| id | INTEGER | ❌ | - | 🔑 |
| partner_id | VARCHAR(36) | ❌ | - |  |
| transaction_id | VARCHAR(100) | ✅ | - |  |
| transaction_amount | NUMERIC(18, 6) | ❌ | - |  |
| base_fee_rate | NUMERIC(5, 4) | ✅ | - |  |
| applied_fee_rate | NUMERIC(5, 4) | ✅ | - |  |
| discount_rate | NUMERIC(5, 4) | ✅ | - |  |
| calculated_fee | NUMERIC(18, 6) | ✅ | - |  |
| platform_share | NUMERIC(18, 6) | ✅ | - |  |
| partner_share | NUMERIC(18, 6) | ✅ | - |  |
| policy_details | JSON | ✅ | - |  |
| created_at | DATETIME | ✅ | now() |  |

#### fee_tiers
- **행 수**: 0개
- **컬럼 수**: 7개
- **외래키**: 1개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| id | INTEGER | ❌ | - | 🔑 |
| fee_policy_id | INTEGER | ❌ | - |  |
| min_amount | NUMERIC(18, 6) | ❌ | - |  |
| max_amount | NUMERIC(18, 6) | ✅ | - |  |
| fee_rate | NUMERIC(5, 4) | ❌ | - |  |
| fixed_fee | NUMERIC(18, 6) | ✅ | - |  |
| created_at | DATETIME | ✅ | now() |  |

### Monitoring 모듈

#### system_transaction_alerts
- **행 수**: 0개
- **컬럼 수**: 12개
- **외래키**: 1개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| title | VARCHAR(200) | ❌ | - |  |
| message | TEXT | ❌ | - |  |
| alert_type | VARCHAR(50) | ❌ | - |  |
| level | VARCHAR(20) | ❌ | - |  |
| is_active | BOOLEAN | ❌ | - |  |
| is_resolved | BOOLEAN | ❌ | - |  |
| resolved_by | INTEGER | ✅ | - |  |
| resolved_at | DATETIME | ✅ | - |  |
| alert_data | TEXT | ✅ | - |  |
| id | INTEGER | ❌ | - | 🔑 |
| created_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |
| updated_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |

#### transactionalerts
- **행 수**: 0개
- **컬럼 수**: 14개
- **외래키**: 3개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| user_id | INTEGER | ❌ | - |  |
| transaction_id | INTEGER | ✅ | - |  |
| alert_type | VARCHAR(50) | ❌ | - |  |
| level | VARCHAR(20) | ❌ | - |  |
| title | VARCHAR(200) | ❌ | - |  |
| description | TEXT | ❌ | - |  |
| is_resolved | BOOLEAN | ❌ | - |  |
| resolved_by | INTEGER | ✅ | - |  |
| resolved_at | DATETIME | ✅ | - |  |
| resolution_notes | TEXT | ✅ | - |  |
| alert_data | TEXT | ✅ | - |  |
| id | INTEGER | ❌ | - | 🔑 |
| created_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |
| updated_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |

### System 모듈

#### alembic_version
- **행 수**: 1개
- **컬럼 수**: 1개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| version_num | VARCHAR(32) | ❌ | - | 🔑 |

### Other 모듈

#### balances
- **행 수**: 7개
- **컬럼 수**: 7개
- **외래키**: 1개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| user_id | INTEGER | ❌ | - |  |
| asset | VARCHAR(10) | ❌ | - |  |
| amount | NUMERIC(18, 6) | ❌ | - |  |
| locked_amount | NUMERIC(18, 6) | ❌ | - |  |
| id | INTEGER | ❌ | - | 🔑 |
| created_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |
| updated_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |

#### transactionsummarys
- **행 수**: 0개
- **컬럼 수**: 19개
- **외래키**: 1개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| user_id | INTEGER | ❌ | - |  |
| period_type | VARCHAR(20) | ❌ | - |  |
| period_start | DATETIME | ❌ | - |  |
| period_end | DATETIME | ❌ | - |  |
| trx_deposits_count | INTEGER | ❌ | - |  |
| trx_deposits_amount | NUMERIC(18, 6) | ❌ | - |  |
| trx_withdrawals_count | INTEGER | ❌ | - |  |
| trx_withdrawals_amount | NUMERIC(18, 6) | ❌ | - |  |
| usdt_deposits_count | INTEGER | ❌ | - |  |
| usdt_deposits_amount | NUMERIC(18, 6) | ❌ | - |  |
| usdt_withdrawals_count | INTEGER | ❌ | - |  |
| usdt_withdrawals_amount | NUMERIC(18, 6) | ❌ | - |  |
| total_transactions | INTEGER | ❌ | - |  |
| total_volume_usd | NUMERIC(18, 6) | ❌ | - |  |
| total_fees_trx | NUMERIC(18, 6) | ❌ | - |  |
| total_fees_usdt | NUMERIC(18, 6) | ❌ | - |  |
| id | INTEGER | ❌ | - | 🔑 |
| created_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |
| updated_at | DATETIME | ❌ | CURRENT_TIMESTAMP |  |

#### user_tiers
- **행 수**: 0개
- **컬럼 수**: 11개
- **외래키**: 1개

**컬럼 구조**:

| 컬럼명 | 타입 | NULL 허용 | 기본값 | PK |
|--------|------|----------|--------|----|\n| id | INTEGER | ❌ | - | 🔑 |
| partner_id | VARCHAR(36) | ❌ | - |  |
| tier_name | VARCHAR(50) | ❌ | - |  |
| tier_level | INTEGER | ❌ | - |  |
| min_volume | NUMERIC(18, 6) | ✅ | - |  |
| fee_discount_rate | NUMERIC(5, 4) | ✅ | - |  |
| withdrawal_limit_multiplier | NUMERIC(5, 2) | ✅ | - |  |
| benefits | JSON | ✅ | - |  |
| upgrade_conditions | JSON | ✅ | - |  |
| created_at | DATETIME | ✅ | now() |  |
| updated_at | DATETIME | ✅ | - |  |

## 🔗 테이블 관계

```mermaid
erDiagram
    alembic_version {
        VARCHAR_32 version_num
    }
    balances {
        INTEGER user_id
        VARCHAR_10 asset
        NUMERIC_18_ 6 amount
        NUMERIC_18_ 6 locked_amount
        INTEGER id
        string etc
    }
    deposits {
        VARCHAR_64 tx_hash
        VARCHAR_42 from_address
        VARCHAR_42 to_address
        NUMERIC_28_ 8 amount
        VARCHAR_10 token_symbol
        string etc
    }
    energy_alerts {
        INTEGER id
        INTEGER energy_pool_id
        VARCHAR_50 alert_type
        VARCHAR_20 severity
        VARCHAR_200 title
        string etc
    }
    energy_pools {
        INTEGER id
        VARCHAR_100 pool_name
        VARCHAR_50 wallet_address
        NUMERIC_18_ 6 total_frozen_trx
        NUMERIC_18_ 6 frozen_for_energy
        string etc
    }
    energy_predictions {
        INTEGER id
        INTEGER energy_pool_id
        DATETIME prediction_date
        NUMERIC_20_ 0 predicted_usage
        DATETIME predicted_depletion
        string etc
    }
    energy_price_history {
        INTEGER id
        NUMERIC_18_ 8 trx_price_usd
        BIGINT energy_per_trx
        BIGINT bandwidth_per_trx
        NUMERIC_18_ 6 total_frozen_trx
        string etc
    }
    energy_usage_history {
        VARCHAR_36 id
        VARCHAR_36 partner_id
        VARCHAR_50 transaction_type
        INTEGER energy_amount
        VARCHAR_100 transaction_id
        string etc
    }
    energy_usage_logs {
        INTEGER id
        INTEGER energy_pool_id
        VARCHAR_64 transaction_hash
        VARCHAR_50 transaction_type
        BIGINT energy_consumed
        string etc
    }
    fee_calculation_logs {
        INTEGER id
        VARCHAR_36 partner_id
        VARCHAR_100 transaction_id
        NUMERIC_18_ 6 transaction_amount
        NUMERIC_5_ 4 base_fee_rate
        string etc
    }
    fee_tiers {
        INTEGER id
        INTEGER fee_policy_id
        NUMERIC_18_ 6 min_amount
        NUMERIC_18_ 6 max_amount
        NUMERIC_5_ 4 fee_rate
        string etc
    }
    partner_energy_policies {
        INTEGER id
        VARCHAR_36 partner_id
        VARCHAR_14 default_policy
        BOOLEAN trx_payment_enabled
        NUMERIC_5_ 4 trx_payment_markup
        string etc
    }
    partner_energy_pools {
        INTEGER id
        INTEGER partner_id
        VARCHAR_42 wallet_address
        NUMERIC_20_ 0 total_energy
        NUMERIC_20_ 0 available_energy
        string etc
    }
    partner_energy_usage_logs {
        INTEGER id
        INTEGER energy_pool_id
        VARCHAR_50 transaction_type
        VARCHAR_66 transaction_hash
        NUMERIC_20_ 0 energy_consumed
        string etc
    }
    partner_fee_policies {
        INTEGER id
        VARCHAR_36 partner_id
        VARCHAR_10 fee_type
        NUMERIC_5_ 4 base_fee_rate
        NUMERIC_18_ 6 min_fee_amount
        string etc
    }
    partner_policy_calculation_logs {
        INTEGER id
        VARCHAR_36 partner_id
        INTEGER user_id
        VARCHAR_50 calculation_type
        TEXT request_data
        string etc
    }
    partner_wallets {
        VARCHAR_36 id
        VARCHAR_36 partner_id
        VARCHAR_12 wallet_type
        VARCHAR_42 address
        VARCHAR_100 label
        string etc
    }
    partner_withdrawal_policies {
        INTEGER id
        VARCHAR_36 partner_id
        VARCHAR_8 policy_type
        BOOLEAN realtime_enabled
        NUMERIC_18_ 6 realtime_max_amount
        string etc
    }
    partners {
        VARCHAR_36 id
        VARCHAR_100 name
        VARCHAR_100 display_name
        VARCHAR_255 domain
        VARCHAR_255 contact_email
        string etc
    }
    system_transaction_alerts {
        VARCHAR_200 title
        TEXT message
        VARCHAR_50 alert_type
        VARCHAR_20 level
        BOOLEAN is_active
        string etc
    }
    transactionalerts {
        INTEGER user_id
        INTEGER transaction_id
        VARCHAR_50 alert_type
        VARCHAR_20 level
        VARCHAR_200 title
        string etc
    }
    transactions {
        INTEGER user_id
        VARCHAR_10 type
        VARCHAR_8 direction
        VARCHAR_10 status
        VARCHAR_10 asset
        string etc
    }
    transactionsummarys {
        INTEGER user_id
        VARCHAR_20 period_type
        DATETIME period_start
        DATETIME period_end
        INTEGER trx_deposits_count
        string etc
    }
    user_tiers {
        INTEGER id
        VARCHAR_36 partner_id
        VARCHAR_50 tier_name
        INTEGER tier_level
        NUMERIC_18_ 6 min_volume
        string etc
    }
    users {
        VARCHAR_255 email
        VARCHAR_255 password_hash
        BOOLEAN is_active
        BOOLEAN is_admin
        BOOLEAN is_verified
        string etc
    }
    wallets {
        INTEGER user_id
        VARCHAR_42 address
        VARCHAR_42 hex_address
        TEXT encrypted_private_key
        VARCHAR_32 encryption_salt
        string etc
    }
    withdrawals {
        INTEGER user_id
        VARCHAR_42 to_address
        NUMERIC_28_ 8 amount
        NUMERIC_28_ 8 fee
        NUMERIC_28_ 8 net_amount
        string etc
    }
    balances ||--o{ users : user_id
    deposits ||--o{ wallets : wallet_id
    deposits ||--o{ users : user_id
    energy_alerts ||--o{ partner_energy_pools : energy_pool_id
    energy_predictions ||--o{ partner_energy_pools : energy_pool_id
    energy_usage_history ||--o{ partners : partner_id
    fee_calculation_logs ||--o{ partners : partner_id
    fee_tiers ||--o{ partner_fee_policies : fee_policy_id
    partner_energy_policies ||--o{ partners : partner_id
    partner_energy_usage_logs ||--o{ partner_energy_pools : energy_pool_id
    partner_fee_policies ||--o{ partners : partner_id
    partner_policy_calculation_logs ||--o{ partners : partner_id
    partner_wallets ||--o{ partners : partner_id
    partner_withdrawal_policies ||--o{ partners : partner_id
    system_transaction_alerts ||--o{ users : resolved_by
    transactionalerts ||--o{ users : user_id
    transactionalerts ||--o{ transactions : transaction_id
    transactionalerts ||--o{ users : resolved_by
    transactions ||--o{ users : user_id
    transactions ||--o{ users : related_user_id
    transactionsummarys ||--o{ users : user_id
    user_tiers ||--o{ partners : partner_id
    wallets ||--o{ users : user_id
    withdrawals ||--o{ users : user_id
    withdrawals ||--o{ users : reviewed_by
    withdrawals ||--o{ users : processed_by
    withdrawals ||--o{ users : approved_by
```

### 관계 상세

| From Table | From Column | To Table | To Column | Type |
|------------|-------------|----------|-----------|------|
| balances | user_id | users | id | many_to_one |
| deposits | wallet_id | wallets | id | many_to_one |
| deposits | user_id | users | id | many_to_one |
| energy_alerts | energy_pool_id | partner_energy_pools | id | many_to_one |
| energy_predictions | energy_pool_id | partner_energy_pools | id | many_to_one |
| energy_usage_history | partner_id | partners | id | many_to_one |
| fee_calculation_logs | partner_id | partners | id | many_to_one |
| fee_tiers | fee_policy_id | partner_fee_policies | id | many_to_one |
| partner_energy_policies | partner_id | partners | id | many_to_one |
| partner_energy_usage_logs | energy_pool_id | partner_energy_pools | id | many_to_one |
| partner_fee_policies | partner_id | partners | id | many_to_one |
| partner_policy_calculation_logs | partner_id | partners | id | many_to_one |
| partner_wallets | partner_id | partners | id | many_to_one |
| partner_withdrawal_policies | partner_id | partners | id | many_to_one |
| system_transaction_alerts | resolved_by | users | id | many_to_one |
| transactionalerts | user_id | users | id | many_to_one |
| transactionalerts | transaction_id | transactions | id | many_to_one |
| transactionalerts | resolved_by | users | id | many_to_one |
| transactions | user_id | users | id | many_to_one |
| transactions | related_user_id | users | id | many_to_one |
| transactionsummarys | user_id | users | id | many_to_one |
| user_tiers | partner_id | partners | id | many_to_one |
| wallets | user_id | users | id | many_to_one |
| withdrawals | user_id | users | id | many_to_one |
| withdrawals | reviewed_by | users | id | many_to_one |
| withdrawals | processed_by | users | id | many_to_one |
| withdrawals | approved_by | users | id | many_to_one |
