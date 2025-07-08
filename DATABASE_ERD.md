# DantaroWallet 데이터베이스 ERD (Entity Relationship Diagram)

```mermaid
erDiagram
    %% Core System Tables
    users {
        int id PK
        varchar email UK
        varchar password_hash
        boolean is_active
        boolean is_admin
        boolean is_verified
        varchar tron_address UK
        datetime created_at
        datetime updated_at
    }
    
    balances {
        int id PK
        int user_id FK
        varchar asset
        decimal amount
        decimal locked_amount
        datetime created_at
        datetime updated_at
    }
    
    wallets {
        int id PK
        int user_id FK
        varchar address UK
        varchar private_key_encrypted
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    transactions {
        int id PK
        int user_id FK
        varchar type
        varchar direction
        varchar status
        varchar asset
        decimal amount
        decimal fee
        int related_user_id FK
        varchar reference_id
        varchar tx_hash
        text description
        text transaction_metadata
        datetime created_at
        datetime updated_at
    }
    
    deposits {
        int id PK
        int user_id FK
        varchar asset
        decimal amount
        varchar status
        varchar tx_hash
        varchar from_address
        varchar to_address
        datetime confirmed_at
        datetime created_at
        datetime updated_at
    }
    
    withdrawals {
        int id PK
        int user_id FK
        varchar asset
        decimal amount
        decimal fee
        varchar status
        varchar to_address
        varchar tx_hash
        text rejection_reason
        datetime processed_at
        datetime created_at
        datetime updated_at
    }
    
    %% Partner System Tables
    partners {
        varchar id PK
        varchar name
        varchar api_key UK
        varchar api_secret_hash
        boolean is_active
        varchar webhook_url
        datetime created_at
        datetime updated_at
    }
    
    partner_wallets {
        int id PK
        varchar partner_id FK
        varchar address UK
        varchar private_key_encrypted
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    partner_fee_policies {
        int id PK
        varchar partner_id FK UK
        enum fee_type
        decimal base_fee_rate
        decimal min_fee_amount
        decimal max_fee_amount
        decimal withdrawal_fee_rate
        decimal internal_transfer_fee_rate
        datetime created_at
        datetime updated_at
    }
    
    fee_tiers {
        int id PK
        int partner_fee_policy_id FK
        decimal min_amount
        decimal max_amount
        decimal fee_rate
        decimal fixed_fee
        datetime created_at
        datetime updated_at
    }
    
    partner_withdrawal_policies {
        int id PK
        varchar partner_id FK UK
        enum processing_policy
        decimal min_amount
        decimal max_amount
        decimal daily_limit
        json allowed_hours
        int batch_delay_minutes
        decimal auto_approval_threshold
        boolean require_admin_approval
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    partner_energy_policies {
        int id PK
        varchar partner_id FK UK
        enum shortage_policy
        int min_energy_threshold
        int max_energy_usage
        int daily_energy_limit
        int queue_timeout_minutes
        int priority_timeout_minutes
        decimal trx_rate_per_energy
        boolean auto_recharge_enabled
        int recharge_threshold
        int recharge_amount
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    user_tiers {
        int id PK
        varchar partner_id FK
        int user_id FK
        varchar tier_name
        int tier_level
        decimal discount_rate
        json special_benefits
        json requirements
        datetime expires_at
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    partner_policy_calculation_logs {
        int id PK
        varchar partner_id FK
        int user_id FK
        varchar calculation_type
        json request_data
        json result_data
        datetime calculated_at
        int admin_id FK
    }
    
    %% Energy System Tables
    energy_pools {
        int id PK
        varchar name
        int total_energy
        int available_energy
        decimal price_per_energy
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    partner_energy_pools {
        int id PK
        varchar partner_id FK
        int energy_pool_id FK
        int allocated_energy
        int used_energy
        int daily_limit
        int priority_level
        datetime created_at
        datetime updated_at
    }
    
    energy_alerts {
        int id PK
        varchar partner_id FK
        int energy_pool_id FK
        varchar alert_type
        varchar severity
        varchar message
        json alert_data
        boolean is_resolved
        datetime resolved_at
        datetime created_at
    }
    
    energy_predictions {
        int id PK
        varchar partner_id FK
        int energy_pool_id FK
        datetime prediction_time
        int predicted_usage
        decimal confidence_score
        json prediction_data
        datetime created_at
    }
    
    energy_usage_history {
        int id PK
        varchar partner_id FK
        int energy_pool_id FK
        int energy_used
        decimal cost
        varchar transaction_type
        datetime usage_time
        datetime created_at
    }
    
    energy_usage_logs {
        int id PK
        varchar partner_id FK
        int energy_amount
        varchar usage_type
        json transaction_data
        datetime created_at
    }
    
    energy_price_history {
        int id PK
        int energy_pool_id FK
        decimal price_per_energy
        datetime effective_from
        datetime effective_to
        varchar price_change_reason
        datetime created_at
    }
    
    %% Analytics Tables
    fee_calculation_logs {
        int id PK
        varchar transaction_id
        int user_id FK
        int partner_id FK
        varchar transaction_type
        decimal transaction_amount
        decimal base_fee
        decimal percentage_fee
        decimal dynamic_multiplier
        decimal final_fee
        int fee_config_id FK
        text applied_rules
        text calculation_details
        datetime created_at
    }
    
    transactionalerts {
        int id PK
        int user_id FK
        varchar alert_type
        varchar severity
        varchar message
        json alert_data
        boolean is_read
        datetime created_at
    }
    
    transactionsummarys {
        int id PK
        int user_id FK
        varchar period_type
        date period_start
        date period_end
        int total_transactions
        decimal total_amount
        decimal total_fees
        json summary_data
        datetime created_at
        datetime updated_at
    }
    
    system_transaction_alerts {
        int id PK
        varchar alert_type
        varchar severity
        varchar message
        json alert_data
        boolean is_resolved
        datetime resolved_at
        datetime created_at
    }
    
    %% Core Relationships
    users ||--o{ balances : "has"
    users ||--o{ wallets : "owns"
    users ||--o{ transactions : "makes"
    users ||--o{ deposits : "receives"
    users ||--o{ withdrawals : "initiates"
    users ||--o{ user_tiers : "assigned"
    users ||--o{ transactionalerts : "receives"
    users ||--o{ transactionsummarys : "generates"
    users ||--o{ fee_calculation_logs : "subject_to"
    
    transactions ||--o| users : "related_to"
    
    %% Partner Relationships
    partners ||--o{ partner_wallets : "owns"
    partners ||--o| partner_fee_policies : "has"
    partners ||--o| partner_withdrawal_policies : "has"
    partners ||--o| partner_energy_policies : "has"
    partners ||--o{ user_tiers : "defines"
    partners ||--o{ partner_policy_calculation_logs : "generates"
    
    partner_fee_policies ||--o{ fee_tiers : "contains"
    
    %% Energy Relationships
    partners ||--o{ partner_energy_pools : "allocated"
    energy_pools ||--o{ partner_energy_pools : "allocated_to"
    energy_pools ||--o{ energy_alerts : "triggers"
    energy_pools ||--o{ energy_predictions : "forecasted"
    energy_pools ||--o{ energy_usage_history : "tracks"
    energy_pools ||--o{ energy_price_history : "prices"
    
    partners ||--o{ energy_alerts : "receives"
    partners ||--o{ energy_predictions : "forecasted_for"
    partners ||--o{ energy_usage_history : "consumes"
    partners ||--o{ energy_usage_logs : "logs"
```

## 🔗 주요 관계 설명

### 1. 사용자 중심 관계
- **users ↔ balances**: 1:N (한 사용자가 여러 자산의 잔액을 가질 수 있음)
- **users ↔ transactions**: 1:N (한 사용자가 여러 거래를 할 수 있음)
- **users ↔ user_tiers**: N:M through partners (파트너별로 다른 등급 가능)

### 2. 파트너 시스템 관계
- **partners ↔ partner_fee_policies**: 1:1 (파트너당 하나의 수수료 정책)
- **partner_fee_policies ↔ fee_tiers**: 1:N (정책당 여러 구간 수수료)
- **partners ↔ user_tiers**: 1:N (파트너가 사용자 등급 정의)

### 3. 에너지 시스템 관계
- **energy_pools ↔ partner_energy_pools**: 1:N (풀을 여러 파트너에게 할당)
- **partners ↔ energy_usage_logs**: 1:N (파트너별 에너지 사용 기록)

### 4. 분석 시스템 관계
- **users ↔ transactionsummarys**: 1:N (사용자별 거래 요약)
- **fee_calculation_logs**: 수수료 계산의 상세 로그

## 📊 데이터 플로우

### 입금 플로우
```
External Blockchain → deposits → balances → transactions
```

### 출금 플로우
```
users → withdrawals → partner_withdrawal_policies → 
energy allocation → blockchain → completion
```

### 수수료 계산 플로우
```
transaction → partner_fee_policies → fee_tiers → 
user_tiers → partner_policy_calculation_logs
```

### 에너지 관리 플로우
```
energy_pools → partner_energy_pools → energy_usage_logs → 
energy_alerts → energy_predictions
```
