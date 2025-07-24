# 🎯 **역할별 API 참조 가이드**

프론트엔드 개발자를 위한 역할별 API 엔드포인트 분류

---

## 🔐 Super Admin Dashboard 전용 API
**포트 3020: /frontend/super-admin-dashboard/**

### **⚡ 에너지 렌탈 관리**
- ➕ `POST /api/v1/admin/energy-rental/allocate-to-partner` - Allocate Energy To Partner
- 🔍 `GET /api/v1/admin/energy-rental/partners/{partner_id}/energy-usage` - Get Partner Energy Usage
- 🔍 `GET /api/v1/admin/energy-rental/providers/status` - Get Energy Providers Status
- ➕ `POST /api/v1/admin/energy-rental/purchase-from-provider` - Purchase Energy From Provider
- 🔍 `GET /api/v1/admin/energy-rental/revenue-analytics` - Get Energy Rental Revenue

### **👑 시스템 관리**
- ➕ `POST /api/v1/admin/backup` - Create Backup
- ➕ `POST /api/v1/admin/backup` - Create Backup
- 🔍 `GET /api/v1/admin/backups` - List Backups
- 🔍 `GET /api/v1/admin/backups` - List Backups
- ✏️ `PUT /api/v1/admin/energy/auto-manage` - Update Auto Management Settings
- ✏️ `PUT /api/v1/admin/energy/auto-manage` - Update Auto Management Settings
- 🔍 `GET /api/v1/admin/energy/cost-estimate` - Get Energy Cost Estimate
- 🔍 `GET /api/v1/admin/energy/cost-estimate` - Get Energy Cost Estimate
- ➕ `POST /api/v1/admin/energy/create-pool` - Create Energy Pool
- ➕ `POST /api/v1/admin/energy/create-pool` - Create Energy Pool
- 🔍 `GET /api/v1/admin/energy/efficiency-report` - Get Efficiency Report
- 🔍 `GET /api/v1/admin/energy/efficiency-report` - Get Efficiency Report
- 🔍 `GET /api/v1/admin/energy/network-status` - Get Network Status
- 🔍 `GET /api/v1/admin/energy/network-status` - Get Network Status
- 🔍 `GET /api/v1/admin/energy/price-history` - Get Energy Price History
- 🔍 `GET /api/v1/admin/energy/price-history` - Get Energy Price History
- ➕ `POST /api/v1/admin/energy/simulate-usage` - Simulate Energy Usage
- ➕ `POST /api/v1/admin/energy/simulate-usage` - Simulate Energy Usage
- 🔍 `GET /api/v1/admin/energy/status` - Get Energy Pool Status
- 🔍 `GET /api/v1/admin/energy/status` - Get Energy Pool Status
- 🔍 `GET /api/v1/admin/energy/top-consumers` - Get Top Energy Consumers
- 🔍 `GET /api/v1/admin/energy/top-consumers` - Get Top Energy Consumers
- ➕ `POST /api/v1/admin/energy/update-prices` - Update Energy Prices
- ➕ `POST /api/v1/admin/energy/update-prices` - Update Energy Prices
- 🔍 `GET /api/v1/admin/energy/usage-logs` - Get Energy Usage Logs
- 🔍 `GET /api/v1/admin/energy/usage-logs` - Get Energy Usage Logs
- 🔍 `GET /api/v1/admin/energy/usage-stats` - Get Energy Usage Statistics
- 🔍 `GET /api/v1/admin/energy/usage-stats` - Get Energy Usage Statistics
- ➕ `POST /api/v1/admin/fees/calculate` - Calculate Fee
- ➕ `POST /api/v1/admin/fees/calculate` - Calculate Fee
- ➕ `POST /api/v1/admin/fees/configs` - Create Fee Config
- ➕ `POST /api/v1/admin/fees/configs` - Create Fee Config
- 🔧 `PATCH /api/v1/admin/fees/configs/{config_id}` - Update Fee Config
- 🔧 `PATCH /api/v1/admin/fees/configs/{config_id}` - Update Fee Config
- 🔍 `GET /api/v1/admin/fees/partner/{partner_id}/revenue-stats` - Get Partner Revenue Stats
- 🔍 `GET /api/v1/admin/fees/partner/{partner_id}/revenue-stats` - Get Partner Revenue Stats
- 🔍 `GET /api/v1/admin/fees/total-revenue-stats` - Get Total Revenue Stats
- 🔍 `GET /api/v1/admin/fees/total-revenue-stats` - Get Total Revenue Stats
- 🔍 `GET /api/v1/admin/partners/` - Get Partners List
- 🔍 `GET /api/v1/admin/partners/` - Get Partners List
- ➕ `POST /api/v1/admin/partners/` - Create Partner
- ➕ `POST /api/v1/admin/partners/` - Create Partner
- ➕ `POST /api/v1/admin/partners/bulk-update` - Bulk Update Partners
- ➕ `POST /api/v1/admin/partners/bulk-update` - Bulk Update Partners
- ➕ `POST /api/v1/admin/partners/export-data` - Export Partner Data
- ➕ `POST /api/v1/admin/partners/export-data` - Export Partner Data
- 🔍 `GET /api/v1/admin/partners/performance-ranking` - Get Partner Performance Ranking
- 🔍 `GET /api/v1/admin/partners/performance-ranking` - Get Partner Performance Ranking
- 🔍 `GET /api/v1/admin/partners/statistics/detailed/{partner_id}` - Get Partner Detailed Statistics
- 🔍 `GET /api/v1/admin/partners/statistics/detailed/{partner_id}` - Get Partner Detailed Statistics
- 🗑️ `DELETE /api/v1/admin/partners/{partner_id}` - Delete Partner
- 🗑️ `DELETE /api/v1/admin/partners/{partner_id}` - Delete Partner
- 🔍 `GET /api/v1/admin/partners/{partner_id}` - Get Partner Detail
- 🔍 `GET /api/v1/admin/partners/{partner_id}` - Get Partner Detail
- 🔧 `PATCH /api/v1/admin/partners/{partner_id}` - Update Partner
- 🔧 `PATCH /api/v1/admin/partners/{partner_id}` - Update Partner
- ➕ `POST /api/v1/admin/partners/{partner_id}/api-key` - Generate Api Key
- ➕ `POST /api/v1/admin/partners/{partner_id}/api-key` - Generate Api Key
- ➕ `POST /api/v1/admin/partners/{partner_id}/api-key/rotate` - Rotate Api Key
- ➕ `POST /api/v1/admin/partners/{partner_id}/api-key/rotate` - Rotate Api Key
- 🔍 `GET /api/v1/admin/partners/{partner_id}/statistics` - Get Partner Statistics
- 🔍 `GET /api/v1/admin/partners/{partner_id}/statistics` - Get Partner Statistics
- ➕ `POST /api/v1/admin/restore` - Restore Backup
- ➕ `POST /api/v1/admin/restore` - Restore Backup
- 🔍 `GET /api/v1/admin/risk-summary` - Get System Risk Summary
- 🔍 `GET /api/v1/admin/risk-summary` - Get System Risk Summary
- 🔍 `GET /api/v1/admin/stats` - Get System Stats
- 🔍 `GET /api/v1/admin/stats` - Get System Stats
- 🔍 `GET /api/v1/admin/suspicious-activities` - Get Suspicious Activities
- 🔍 `GET /api/v1/admin/suspicious-activities` - Get Suspicious Activities
- 🔍 `GET /api/v1/admin/transactions` - Get Transaction Monitor
- 🔍 `GET /api/v1/admin/transactions` - Get Transaction Monitor
- 🔍 `GET /api/v1/admin/users` - Get Users List
- 🔍 `GET /api/v1/admin/users` - Get Users List
- 🔍 `GET /api/v1/admin/users/{user_id}` - Get User Detail
- 🔍 `GET /api/v1/admin/users/{user_id}` - Get User Detail
- 🔧 `PATCH /api/v1/admin/users/{user_id}` - Update User
- 🔧 `PATCH /api/v1/admin/users/{user_id}` - Update User
- ➕ `POST /api/v1/admin/users/{user_id}/disable` - Disable User
- ➕ `POST /api/v1/admin/users/{user_id}/disable` - Disable User
- ➕ `POST /api/v1/admin/users/{user_id}/enable` - Enable User
- ➕ `POST /api/v1/admin/users/{user_id}/enable` - Enable User
- 🔍 `GET /api/v1/admin/users/{user_id}/risk` - Get User Risk Analysis
- 🔍 `GET /api/v1/admin/users/{user_id}/risk` - Get User Risk Analysis
- ➕ `POST /api/v1/admin/users/{user_id}/verify` - Verify User
- ➕ `POST /api/v1/admin/users/{user_id}/verify` - Verify User

### **⚡ 에너지 풀 관리**
- ✏️ `PUT /api/v1/admin/energy/auto-manage` - Update Auto Management Settings
- 🔍 `GET /api/v1/admin/energy/cost-estimate` - Get Energy Cost Estimate
- ➕ `POST /api/v1/admin/energy/create-pool` - Create Energy Pool
- 🔍 `GET /api/v1/admin/energy/efficiency-report` - Get Efficiency Report
- 🔍 `GET /api/v1/admin/energy/network-status` - Get Network Status
- 🔍 `GET /api/v1/admin/energy/price-history` - Get Energy Price History
- ➕ `POST /api/v1/admin/energy/simulate-usage` - Simulate Energy Usage
- 🔍 `GET /api/v1/admin/energy/status` - Get Energy Pool Status
- 🔍 `GET /api/v1/admin/energy/top-consumers` - Get Top Energy Consumers
- ➕ `POST /api/v1/admin/energy/update-prices` - Update Energy Prices
- 🔍 `GET /api/v1/admin/energy/usage-logs` - Get Energy Usage Logs
- 🔍 `GET /api/v1/admin/energy/usage-stats` - Get Energy Usage Statistics

### **💰 수수료 관리**
- ➕ `POST /api/v1/admin/fees/calculate` - Calculate Fee
- ➕ `POST /api/v1/admin/fees/configs` - Create Fee Config
- 🔧 `PATCH /api/v1/admin/fees/configs/{config_id}` - Update Fee Config
- 🔍 `GET /api/v1/admin/fees/partner/{partner_id}/revenue-stats` - Get Partner Revenue Stats
- 🔍 `GET /api/v1/admin/fees/total-revenue-stats` - Get Total Revenue Stats

### **🤝 파트너사 관리**
- 🔍 `GET /api/v1/admin/partners/` - Get Partners List
- ➕ `POST /api/v1/admin/partners/` - Create Partner
- ➕ `POST /api/v1/admin/partners/bulk-update` - Bulk Update Partners
- ➕ `POST /api/v1/admin/partners/export-data` - Export Partner Data
- 🔍 `GET /api/v1/admin/partners/performance-ranking` - Get Partner Performance Ranking
- 🔍 `GET /api/v1/admin/partners/statistics/detailed/{partner_id}` - Get Partner Detailed Statistics
- 🗑️ `DELETE /api/v1/admin/partners/{partner_id}` - Delete Partner
- 🔍 `GET /api/v1/admin/partners/{partner_id}` - Get Partner Detail
- 🔧 `PATCH /api/v1/admin/partners/{partner_id}` - Update Partner
- ➕ `POST /api/v1/admin/partners/{partner_id}/api-key` - Generate Api Key
- ➕ `POST /api/v1/admin/partners/{partner_id}/api-key/rotate` - Rotate Api Key
- 🔍 `GET /api/v1/admin/partners/{partner_id}/statistics` - Get Partner Statistics

### **📊 Super Admin Dashboard**
- 🔍 `GET /api/v1/admin/dashboard/activity-feed` - Get Activity Feed
- 🔍 `GET /api/v1/admin/dashboard/energy-status` - Get Energy Status
- 🔍 `GET /api/v1/admin/dashboard/overview` - Get Dashboard Overview
- 🔍 `GET /api/v1/admin/dashboard/partner-rankings` - Get Partner Rankings
- 🔍 `GET /api/v1/admin/dashboard/quick-stats` - Get Quick Stats
- 🔍 `GET /api/v1/admin/dashboard/revenue-stats` - Get Revenue Stats
- 🔍 `GET /api/v1/admin/dashboard/system-health` - Get System Health
- 🔍 `GET /api/v1/admin/dashboard/system-metrics` - Get System Metrics

### **💸 출금 관리**
- 🔍 `GET /api/v1/withdrawal-management/approval-rules` - Get Approval Rules
- ➕ `POST /api/v1/withdrawal-management/approval-rules` - Create Approval Rule
- 🔍 `GET /api/v1/withdrawal-management/batches` - Get Pending Batches
- ➕ `POST /api/v1/withdrawal-management/batches` - Create Withdrawal Batch
- ➕ `POST /api/v1/withdrawal-management/batches/{batch_id}/execute` - Execute Batch With Auto Sign
- ➕ `POST /api/v1/withdrawal-management/evaluate` - Evaluate Withdrawal Request
- 🔍 `GET /api/v1/withdrawal-management/fee-optimization` - Get Fee Optimization Suggestions
- ➕ `POST /api/v1/withdrawal-management/optimize` - Optimize Withdrawal Batches
- 🔍 `GET /api/v1/withdrawal-management/policies` - Get Withdrawal Policy
- ➕ `POST /api/v1/withdrawal-management/policies` - Create Withdrawal Policy
- ✏️ `PUT /api/v1/withdrawal-management/policies` - Update Withdrawal Policy
- ➕ `POST /api/v1/withdrawal-management/statistics` - Get Withdrawal Statistics
- 🔍 `GET /api/v1/withdrawal-management/whitelist` - Get Whitelist Entries
- ➕ `POST /api/v1/withdrawal-management/whitelist` - Create Whitelist Entry
- 🗑️ `DELETE /api/v1/withdrawal-management/whitelist/{whitelist_id}` - Delete Whitelist Entry

### **🧹 자금 정리**
- 🔍 `GET /api/v1/sweep/addresses` - List Deposit Addresses
- ➕ `POST /api/v1/sweep/addresses` - Create Deposit Address
- 🗑️ `DELETE /api/v1/sweep/addresses/{address_id}` - Deactivate Deposit Address
- ✏️ `PUT /api/v1/sweep/addresses/{address_id}` - Update Deposit Address
- 🔍 `GET /api/v1/sweep/config` - Get Sweep Configuration
- ➕ `POST /api/v1/sweep/config` - Create Sweep Configuration
- ✏️ `PUT /api/v1/sweep/config` - Update Sweep Configuration
- ➕ `POST /api/v1/sweep/emergency` - Emergency Sweep
- ➕ `POST /api/v1/sweep/manual` - Manual Sweep
- ➕ `POST /api/v1/sweep/manual/batch` - Batch Manual Sweep
- 🔍 `GET /api/v1/sweep/wallets/master` - Get Master Wallet
- ➕ `POST /api/v1/sweep/wallets/master` - Create Master Wallet

---

## 🔗 Partner Admin Template 전용 API
**포트 3030: /frontend/partner-admin-template/**

### **⚡ 에너지 렌탈**
- ➕ `POST /api/v1/energy-rental/allocate-energy` - 에너지 할당
- 🔍 `GET /api/v1/energy-rental/analytics` - 렌탈 분석 데이터
- 🔧 `PATCH /api/v1/energy-rental/billing/{billing_id}/payment-status` - 결제 상태 업데이트
- ➕ `POST /api/v1/energy-rental/billing/{partner_id}` - 청구서 생성
- 🔍 `GET /api/v1/energy-rental/energy-pools/status` - 에너지 풀 상태
- 🔍 `GET /api/v1/energy-rental/optimization` - 수익성 최적화 제안
- 🔍 `GET /api/v1/energy-rental/overview` - 에너지 렌탈 서비스 개요
- ➕ `POST /api/v1/energy-rental/partner/{partner_id}/auto-recharge-check` - 자동 재충전 확인
- 🔍 `GET /api/v1/energy-rental/partner/{partner_id}/billing` - 파트너 청구 정보
- 🔍 `GET /api/v1/energy-rental/partner/{partner_id}/billing-history` - 청구 이력
- 🔍 `GET /api/v1/energy-rental/partner/{partner_id}/energy-allocation` - 파트너 에너지 할당 정보
- 🔍 `GET /api/v1/energy-rental/partner/{partner_id}/usage` - 파트너 에너지 사용 통계
- 🔍 `GET /api/v1/energy-rental/partner/{partner_id}/usage-statistics` - 파트너 사용 통계
- 🔍 `GET /api/v1/energy-rental/plans` - 렌탈 플랜 목록 조회
- 🔍 `GET /api/v1/energy-rental/pools` - 에너지 풀 목록
- ➕ `POST /api/v1/energy-rental/pools` - 에너지 풀 생성
- 🔍 `GET /api/v1/energy-rental/pools/status` - 에너지 풀 상태 조회
- 🗑️ `DELETE /api/v1/energy-rental/pools/{pool_id}` - 에너지 풀 삭제
- ✏️ `PUT /api/v1/energy-rental/pools/{pool_id}` - 에너지 풀 업데이트
- ➕ `POST /api/v1/energy-rental/record-usage` - 에너지 사용 기록
- ➕ `POST /api/v1/energy-rental/rent` - 에너지 렌탈 요청
- 🔍 `GET /api/v1/energy-rental/rental-plans` - 활성 렌탈 플랜 조회
- ➕ `POST /api/v1/energy-rental/rental-plans` - 렌탈 플랜 생성
- 🔧 `PATCH /api/v1/energy-rental/rental-plans/{plan_id}/deactivate` - 렌탈 플랜 비활성화
- 🔍 `GET /api/v1/energy-rental/system/status` - 시스템 상태
- 🔍 `GET /api/v1/energy-rental/transactions` - 렌탈 거래 목록

### **⚡ 파트너 에너지 렌탈**
- ➕ `POST /api/v1/partner/energy-rental/allocate-energy-for-withdrawal` - Allocate Energy For User Withdrawal
- 🔍 `GET /api/v1/partner/energy-rental/billing-summary` - Get Energy Billing Summary
- 🔍 `GET /api/v1/partner/energy-rental/my-energy-balance` - Get Partner Energy Balance
- ➕ `POST /api/v1/partner/energy-rental/rent-from-super-admin` - Rent Energy From Super Admin
- 🔍 `GET /api/v1/partner/energy-rental/users-energy-usage` - Get Users Energy Usage

### **💰 수수료 정책**
- ➕ `POST /api/v1/fee-policy/partners/{partner_id}/calculate-fee` - Calculate Fee
- 🔍 `GET /api/v1/fee-policy/partners/{partner_id}/calculation-logs` - Get Calculation Logs
- 🔍 `GET /api/v1/fee-policy/partners/{partner_id}/energy-policy` - Get Energy Policy
- ➕ `POST /api/v1/fee-policy/partners/{partner_id}/energy-policy` - Create Energy Policy
- ✏️ `PUT /api/v1/fee-policy/partners/{partner_id}/energy-policy` - Update Energy Policy
- 🗑️ `DELETE /api/v1/fee-policy/partners/{partner_id}/fee-policy` - Delete Partner Fee Policy
- 🔍 `GET /api/v1/fee-policy/partners/{partner_id}/fee-policy` - Get Partner Fee Policy
- ➕ `POST /api/v1/fee-policy/partners/{partner_id}/fee-policy` - Create Partner Fee Policy
- ✏️ `PUT /api/v1/fee-policy/partners/{partner_id}/fee-policy` - Update Partner Fee Policy
- 🔍 `GET /api/v1/fee-policy/partners/{partner_id}/fee-tiers` - Get Fee Tiers
- ➕ `POST /api/v1/fee-policy/partners/{partner_id}/fee-tiers` - Create Fee Tier
- 🔍 `GET /api/v1/fee-policy/partners/{partner_id}/user-tiers` - Get Partner User Tiers
- 🗑️ `DELETE /api/v1/fee-policy/partners/{partner_id}/users/{user_id}/tier` - Deactivate User Tier
- 🔍 `GET /api/v1/fee-policy/partners/{partner_id}/users/{user_id}/tier` - Get User Tier
- ➕ `POST /api/v1/fee-policy/partners/{partner_id}/users/{user_id}/tier` - Create User Tier
- ✏️ `PUT /api/v1/fee-policy/partners/{partner_id}/users/{user_id}/tier` - Update User Tier
- ➕ `POST /api/v1/fee-policy/partners/{partner_id}/validate-energy` - Validate Energy Usage
- ➕ `POST /api/v1/fee-policy/partners/{partner_id}/validate-withdrawal` - Validate Withdrawal Request
- 🔍 `GET /api/v1/fee-policy/partners/{partner_id}/withdrawal-policy` - Get Withdrawal Policy
- ➕ `POST /api/v1/fee-policy/partners/{partner_id}/withdrawal-policy` - Create Withdrawal Policy
- ✏️ `PUT /api/v1/fee-policy/partners/{partner_id}/withdrawal-policy` - Update Withdrawal Policy

### **🔗 TronLink 연동**
- 🔍 `GET /api/v1/tronlink/admin/all-connections` - Get All Tronlink Connections
- 🔍 `GET /api/v1/tronlink/admin/all-connections` - Get All Tronlink Connections
- ➕ `POST /api/v1/tronlink/auth` - Authenticate With Tronlink
- ➕ `POST /api/v1/tronlink/auth` - Authenticate With Tronlink
- ➕ `POST /api/v1/tronlink/auto-signing/authorize` - Authorize Auto Signing
- ➕ `POST /api/v1/tronlink/auto-signing/authorize` - Authorize Auto Signing
- ➕ `POST /api/v1/tronlink/auto-signing/batch` - Batch Sign Transactions
- ➕ `POST /api/v1/tronlink/auto-signing/batch` - Batch Sign Transactions
- 🔍 `GET /api/v1/tronlink/auto-signing/batch/{batch_id}/result` - Get Batch Result
- 🔍 `GET /api/v1/tronlink/auto-signing/batch/{batch_id}/result` - Get Batch Result
- 🔍 `GET /api/v1/tronlink/auto-signing/batch/{batch_id}/status` - Get Batch Status
- 🔍 `GET /api/v1/tronlink/auto-signing/batch/{batch_id}/status` - Get Batch Status
- ➕ `POST /api/v1/tronlink/auto-signing/session` - Create Auto Signing Session
- ➕ `POST /api/v1/tronlink/auto-signing/session` - Create Auto Signing Session
- ➕ `POST /api/v1/tronlink/auto-signing/session/revoke` - Revoke Session
- ➕ `POST /api/v1/tronlink/auto-signing/session/revoke` - Revoke Session
- 🔍 `GET /api/v1/tronlink/auto-signing/session/status` - Get Session Status
- 🔍 `GET /api/v1/tronlink/auto-signing/session/status` - Get Session Status
- ➕ `POST /api/v1/tronlink/auto-signing/sign` - Sign Transaction Auto
- ➕ `POST /api/v1/tronlink/auto-signing/sign` - Sign Transaction Auto
- ➕ `POST /api/v1/tronlink/connect` - Connect Tronlink Wallet
- ➕ `POST /api/v1/tronlink/connect` - Connect Tronlink Wallet
- ➕ `POST /api/v1/tronlink/disconnect` - Disconnect Wallet
- ➕ `POST /api/v1/tronlink/disconnect` - Disconnect Wallet
- 🔍 `GET /api/v1/tronlink/status` - Get Tronlink Status
- 🔍 `GET /api/v1/tronlink/status` - Get Tronlink Status
- 🔍 `GET /api/v1/tronlink/wallet/{wallet_address}/balance` - Get Wallet Balance
- 🔍 `GET /api/v1/tronlink/wallet/{wallet_address}/balance` - Get Wallet Balance
- 🔍 `GET /api/v1/tronlink/wallets` - Get Partner Wallets
- 🔍 `GET /api/v1/tronlink/wallets` - Get Partner Wallets
- 🔍 `GET /tronlink` - Tronlink Page

### **⚡ 에너지 관리**
- 🔍 `GET /api/v1/energy-management/pools` - Get Energy Pools
- 🔍 `GET /api/v1/energy-management/pools` - Get Energy Pools
- ➕ `POST /api/v1/energy-management/pools` - Create Energy Pool
- ➕ `POST /api/v1/energy-management/pools` - Create Energy Pool
- 🗑️ `DELETE /api/v1/energy-management/pools/{pool_id}` - Delete Energy Pool
- 🗑️ `DELETE /api/v1/energy-management/pools/{pool_id}` - Delete Energy Pool
- 🔍 `GET /api/v1/energy-management/pools/{pool_id}` - Get Energy Pool
- 🔍 `GET /api/v1/energy-management/pools/{pool_id}` - Get Energy Pool
- ✏️ `PUT /api/v1/energy-management/pools/{pool_id}` - Update Energy Pool
- ✏️ `PUT /api/v1/energy-management/pools/{pool_id}` - Update Energy Pool
- ➕ `POST /api/v1/energy-management/pools/{pool_id}/allocate` - Allocate Energy
- ➕ `POST /api/v1/energy-management/pools/{pool_id}/allocate` - Allocate Energy
- 🔍 `GET /api/v1/energy-management/pools/{pool_id}/allocations` - Get Energy Allocations
- 🔍 `GET /api/v1/energy-management/pools/{pool_id}/allocations` - Get Energy Allocations
- ✏️ `PUT /api/v1/energy-management/pools/{pool_id}/auto-recharge` - Update Auto Recharge Settings
- ✏️ `PUT /api/v1/energy-management/pools/{pool_id}/auto-recharge` - Update Auto Recharge Settings
- ➕ `POST /api/v1/energy-management/pools/{pool_id}/recharge` - Recharge Energy Pool
- ➕ `POST /api/v1/energy-management/pools/{pool_id}/recharge` - Recharge Energy Pool
- ✏️ `PUT /api/v1/energy-management/pools/{pool_id}/thresholds` - Update Energy Thresholds
- ✏️ `PUT /api/v1/energy-management/pools/{pool_id}/thresholds` - Update Energy Thresholds
- 🔍 `GET /api/v1/energy-management/statistics` - Get Energy Usage Statistics
- 🔍 `GET /api/v1/energy-management/statistics` - Get Energy Usage Statistics

---

## 🔄 공통 API (양쪽 모두 사용)
**Super Admin Dashboard와 Partner Admin Template 공통 사용**

### **health**
- 🔍 `GET /health` - Health Check

### **root**
- 🔍 `GET /` - Root

### **🔐 인증**
- ➕ `POST /api/v1/auth/change-password` - Change Password
- ➕ `POST /api/v1/auth/login` - Login
- 🔍 `GET /api/v1/auth/me` - Get Current User
- ➕ `POST /api/v1/auth/partner/login` - Partner Login
- ➕ `POST /api/v1/auth/refresh` - Refresh Token
- ➕ `POST /api/v1/auth/register` - Register
- ➕ `POST /api/v1/auth/super-admin/login` - Super Admin Login
- ➕ `POST /api/v1/auth/super-admin/quick-login` - Super Admin Quick Login
- 🔍 `GET /api/v1/auth/test` - Test Endpoint
- ➕ `POST /api/v1/auth/user/login` - User Login

### **💳 잔액 관리**
- 🔍 `GET /api/v1/balance/` - Get Balance
- ➕ `POST /api/v1/balance/admin/adjust` - Adjust Balance
- 🔍 `GET /api/v1/balance/summary` - Get Balance Summary
- 🔍 `GET /api/v1/balance/transactions` - Get Transactions
- 🔍 `GET /api/v1/balance/transactions/{transaction_id}` - Get Transaction Detail
- ➕ `POST /api/v1/balance/transfer` - Internal Transfer

### **👛 지갑 관리**
- 🔍 `GET /api/v1/wallet/` - Get Wallet
- 🔍 `GET /api/v1/wallet/balance` - Get Wallet Balance
- ➕ `POST /api/v1/wallet/create` - Create Wallet
- ➕ `POST /api/v1/wallet/monitoring` - Update Monitoring
- 🔍 `GET /api/v1/wallet/network-info` - Get Network Info
- ➕ `POST /api/v1/wallet/validate-address` - Validate Address

### **📥 입금 관리**
- 🔍 `GET /api/v1/deposit/monitor/info` - Get Monitoring Info
- ➕ `POST /api/v1/deposit/monitor/start` - Start Monitoring
- ➕ `POST /api/v1/deposit/monitor/stop` - Stop Monitoring
- 🔍 `GET /api/v1/deposit/status` - Get Deposit Status

### **📤 출금 관리**
- 🔍 `GET /api/v1/withdrawals/` - Get Withdrawals
- 🔍 `GET /api/v1/withdrawals/admin/pending` - Get Pending Withdrawals
- 🔍 `GET /api/v1/withdrawals/admin/stats` - Get Withdrawal Stats
- ➕ `POST /api/v1/withdrawals/admin/{withdrawal_id}/complete` - Complete Withdrawal
- ➕ `POST /api/v1/withdrawals/admin/{withdrawal_id}/process` - Mark As Processing
- 🔍 `GET /api/v1/withdrawals/admin/{withdrawal_id}/processing-guide` - Get Processing Guide
- ➕ `POST /api/v1/withdrawals/admin/{withdrawal_id}/review` - Review Withdrawal
- ➕ `POST /api/v1/withdrawals/request` - Request Withdrawal
- 🔍 `GET /api/v1/withdrawals/{withdrawal_id}` - Get Withdrawal Detail
- ➕ `POST /api/v1/withdrawals/{withdrawal_id}/cancel` - Cancel Withdrawal

### **energy-rental**
- ➕ `POST /api/v1/energy-rental/allocate-energy` - 에너지 할당
- 🔍 `GET /api/v1/energy-rental/analytics` - 렌탈 분석 데이터
- 🔧 `PATCH /api/v1/energy-rental/billing/{billing_id}/payment-status` - 결제 상태 업데이트
- ➕ `POST /api/v1/energy-rental/billing/{partner_id}` - 청구서 생성
- 🔍 `GET /api/v1/energy-rental/energy-pools/status` - 에너지 풀 상태
- 🔍 `GET /api/v1/energy-rental/optimization` - 수익성 최적화 제안
- 🔍 `GET /api/v1/energy-rental/overview` - 에너지 렌탈 서비스 개요
- ➕ `POST /api/v1/energy-rental/partner/{partner_id}/auto-recharge-check` - 자동 재충전 확인
- 🔍 `GET /api/v1/energy-rental/partner/{partner_id}/billing` - 파트너 청구 정보
- 🔍 `GET /api/v1/energy-rental/partner/{partner_id}/billing-history` - 청구 이력
- 🔍 `GET /api/v1/energy-rental/partner/{partner_id}/energy-allocation` - 파트너 에너지 할당 정보
- 🔍 `GET /api/v1/energy-rental/partner/{partner_id}/usage` - 파트너 에너지 사용 통계
- 🔍 `GET /api/v1/energy-rental/partner/{partner_id}/usage-statistics` - 파트너 사용 통계
- 🔍 `GET /api/v1/energy-rental/plans` - 렌탈 플랜 목록 조회
- 🔍 `GET /api/v1/energy-rental/pools` - 에너지 풀 목록
- ➕ `POST /api/v1/energy-rental/pools` - 에너지 풀 생성
- 🔍 `GET /api/v1/energy-rental/pools/status` - 에너지 풀 상태 조회
- 🗑️ `DELETE /api/v1/energy-rental/pools/{pool_id}` - 에너지 풀 삭제
- ✏️ `PUT /api/v1/energy-rental/pools/{pool_id}` - 에너지 풀 업데이트
- ➕ `POST /api/v1/energy-rental/record-usage` - 에너지 사용 기록
- ➕ `POST /api/v1/energy-rental/rent` - 에너지 렌탈 요청
- 🔍 `GET /api/v1/energy-rental/rental-plans` - 활성 렌탈 플랜 조회
- ➕ `POST /api/v1/energy-rental/rental-plans` - 렌탈 플랜 생성
- 🔧 `PATCH /api/v1/energy-rental/rental-plans/{plan_id}/deactivate` - 렌탈 플랜 비활성화
- 🔍 `GET /api/v1/energy-rental/system/status` - 시스템 상태
- 🔍 `GET /api/v1/energy-rental/transactions` - 렌탈 거래 목록

### **Super Admin Energy Rental**
- ➕ `POST /api/v1/admin/energy-rental/allocate-to-partner` - Allocate Energy To Partner
- 🔍 `GET /api/v1/admin/energy-rental/partners/{partner_id}/energy-usage` - Get Partner Energy Usage
- 🔍 `GET /api/v1/admin/energy-rental/providers/status` - Get Energy Providers Status
- ➕ `POST /api/v1/admin/energy-rental/purchase-from-provider` - Purchase Energy From Provider
- 🔍 `GET /api/v1/admin/energy-rental/revenue-analytics` - Get Energy Rental Revenue

### **Partner Energy Rental**
- ➕ `POST /api/v1/partner/energy-rental/allocate-energy-for-withdrawal` - Allocate Energy For User Withdrawal
- 🔍 `GET /api/v1/partner/energy-rental/billing-summary` - Get Energy Billing Summary
- 🔍 `GET /api/v1/partner/energy-rental/my-energy-balance` - Get Partner Energy Balance
- ➕ `POST /api/v1/partner/energy-rental/rent-from-super-admin` - Rent Energy From Super Admin
- 🔍 `GET /api/v1/partner/energy-rental/users-energy-usage` - Get Users Energy Usage

### **Super Admin Dashboard**
- 🔍 `GET /api/v1/admin/dashboard/activity-feed` - Get Activity Feed
- 🔍 `GET /api/v1/admin/dashboard/energy-status` - Get Energy Status
- 🔍 `GET /api/v1/admin/dashboard/overview` - Get Dashboard Overview
- 🔍 `GET /api/v1/admin/dashboard/partner-rankings` - Get Partner Rankings
- 🔍 `GET /api/v1/admin/dashboard/quick-stats` - Get Quick Stats
- 🔍 `GET /api/v1/admin/dashboard/revenue-stats` - Get Revenue Stats
- 🔍 `GET /api/v1/admin/dashboard/system-health` - Get System Health
- 🔍 `GET /api/v1/admin/dashboard/system-metrics` - Get System Metrics

### **👥 사용자 관리**
- 🔍 `GET /api/v1/users/` - Get Users
- 🔍 `GET /api/v1/users/test` - Test Users Router
- 🔍 `GET /api/v1/users/users/activity/recent` - Get Recent User Activity
- 🔍 `GET /api/v1/users/users/stats/daily` - Get Daily User Stats
- 🔍 `GET /api/v1/users/users/{user_id}` - Get User Detail
- ✏️ `PUT /api/v1/users/users/{user_id}/status` - Update User Status

### **💰 거래 내역**
- 🔍 `GET /api/v1/transactions/transactions` - Get Transactions
- 🔍 `GET /api/v1/transactions/transactions/analytics/daily` - Get Daily Transaction Analytics
- 🔍 `GET /api/v1/transactions/transactions/analytics/hourly` - Get Hourly Transaction Analytics
- 🔍 `GET /api/v1/transactions/transactions/failed` - Get Failed Transactions
- 🔍 `GET /api/v1/transactions/transactions/status/summary` - Get Transaction Status Summary
- 🔍 `GET /api/v1/transactions/transactions/{transaction_id}` - Get Transaction Detail
- ✏️ `PUT /api/v1/transactions/transactions/{transaction_id}/retry` - Retry Failed Transaction

### **audit-compliance**
- ➕ `POST /api/v1/audit-compliance/aml-check` - Perform Aml Check
- 🔍 `GET /api/v1/audit-compliance/audit-chain-verification` - Verify Audit Chain
- 🔍 `GET /api/v1/audit-compliance/compliance-history` - Get Compliance History
- ➕ `POST /api/v1/audit-compliance/detect-anomalies` - Detect Anomalies
- ➕ `POST /api/v1/audit-compliance/kyc-check` - Perform Kyc Check
- ➕ `POST /api/v1/audit-compliance/log-event` - Log Audit Event
- 🔍 `GET /api/v1/audit-compliance/logs` - Get Audit Logs
- 🔍 `GET /api/v1/audit-compliance/pending-reviews` - Get Pending Reviews
- ➕ `POST /api/v1/audit-compliance/pep-check` - Check Pep Status
- ➕ `POST /api/v1/audit-compliance/sanctions-check` - Check Sanctions List
- 🔍 `GET /api/v1/audit-compliance/stats` - Get Audit Stats
- 🔍 `GET /api/v1/audit-compliance/suspicious-activities` - Get Suspicious Activities

### **integrated_dashboard**
- 🔍 `GET /api/v1/integrated-dashboard/energy-status/{partner_id}` - Get Energy Status
- 🔍 `GET /api/v1/integrated-dashboard/overview/{partner_id}` - Get Dashboard Overview
- 🔍 `GET /api/v1/integrated-dashboard/predictions/{partner_id}` - Get Predictions
- 🔍 `GET /api/v1/integrated-dashboard/revenue-metrics/{partner_id}` - Get Revenue Metrics
- 🔍 `GET /api/v1/integrated-dashboard/risk-alerts/{partner_id}` - Get Risk Alerts
- 🔍 `GET /api/v1/integrated-dashboard/system-health/{partner_id}` - Get System Health
- 🔍 `GET /api/v1/integrated-dashboard/test` - Test Dashboard
- 🔍 `GET /api/v1/integrated-dashboard/transaction-flow/{partner_id}` - Get Transaction Flow
- 🔍 `GET /api/v1/integrated-dashboard/user-analytics/{partner_id}` - Get User Analytics
- 🔍 `GET /api/v1/integrated-dashboard/wallet-overview/{partner_id}` - Get Wallet Overview

### **Integrated Dashboard**
- 🔍 `GET /api/v1/integrated-dashboard/energy-status/{partner_id}` - Get Energy Status
- 🔍 `GET /api/v1/integrated-dashboard/overview/{partner_id}` - Get Dashboard Overview
- 🔍 `GET /api/v1/integrated-dashboard/predictions/{partner_id}` - Get Predictions
- 🔍 `GET /api/v1/integrated-dashboard/revenue-metrics/{partner_id}` - Get Revenue Metrics
- 🔍 `GET /api/v1/integrated-dashboard/risk-alerts/{partner_id}` - Get Risk Alerts
- 🔍 `GET /api/v1/integrated-dashboard/system-health/{partner_id}` - Get System Health
- 🔍 `GET /api/v1/integrated-dashboard/test` - Test Dashboard
- 🔍 `GET /api/v1/integrated-dashboard/transaction-flow/{partner_id}` - Get Transaction Flow
- 🔍 `GET /api/v1/integrated-dashboard/user-analytics/{partner_id}` - Get User Analytics
- 🔍 `GET /api/v1/integrated-dashboard/wallet-overview/{partner_id}` - Get Wallet Overview

### **statistics**
- 🔍 `GET /api/v1/analytics/revenue` - Get Revenue Analytics
- 🔍 `GET /api/v1/dashboard/overview` - Get Dashboard Overview
- 🔍 `GET /api/v1/partners/stats` - Get Partner Stats
- 🔍 `GET /api/v1/users/stats` - Get User Stats

### **📊 분석**
- 🔍 `GET /api/v1/transaction-analytics/anomalies` - Detect Anomalies
- 🔍 `GET /api/v1/transaction-analytics/stats` - Get Transaction Stats
- 🔍 `GET /api/v1/transaction-analytics/user-analytics` - Get User Analytics

### **simple_energy**
- 🔍 `GET /api/v1/simple-energy/account/{address}` - Get Account Energy Info
- 🔍 `GET /api/v1/simple-energy/config` - Get Simple Energy Config
- 🔍 `GET /api/v1/simple-energy/health` - Check Simple Energy Health
- 🔍 `GET /api/v1/simple-energy/price` - Get Simple Energy Price
- 🔍 `GET /api/v1/simple-energy/pricing-comparison` - Get Pricing Comparison
- 🔍 `GET /api/v1/simple-energy/providers` - Get Simple Providers
- 🔍 `GET /api/v1/simple-energy/quick-start` - Get Quick Start Guide
- ➕ `POST /api/v1/simple-energy/simulate-purchase` - Simulate Energy Purchase

### **public**
- 🔍 `GET /public/providers` - Get Public Providers
- 🔍 `GET /public/providers/summary` - Get Providers Summary

### **auth-pages**
- 🔍 `GET /auth/login` - Login Page
- 🔍 `GET /auth/logout` - Logout Page
- 🔍 `GET /auth/register` - Register Page

### **web-dashboard**
- 🔍 `GET /dashboard/` - Dashboard Page
- 🔍 `GET /dashboard/analytics` - Analytics Page
- 🔍 `GET /dashboard/logout` - Logout Page
- 🔍 `GET /dashboard/profile` - Profile Page
- 🔍 `GET /dashboard/settings` - Settings Page
- 🔍 `GET /dashboard/transactions` - Transactions Page
- 🔍 `GET /dashboard/wallet` - Wallet Page

---

## 🌟 개발/테스트용 API
**개발 및 테스트 전용**

### **🔧 최적화**
- ➕ `POST /api/v1/admin/optimization/actions/{action_type}` - Execute Optimization Action
- ➕ `POST /api/v1/admin/optimization/actions/{action_type}` - Execute Optimization Action
- 🔍 `GET /api/v1/admin/optimization/api-performance` - Get Api Performance Stats
- 🔍 `GET /api/v1/admin/optimization/api-performance` - Get Api Performance Stats
- ➕ `POST /api/v1/admin/optimization/cache/clear` - Clear Cache
- ➕ `POST /api/v1/admin/optimization/cache/clear` - Clear Cache
- 🔍 `GET /api/v1/admin/optimization/database/optimization` - Get Database Optimization Info
- 🔍 `GET /api/v1/admin/optimization/database/optimization` - Get Database Optimization Info
- 🔍 `GET /api/v1/admin/optimization/health-check` - Optimization Health Check
- 🔍 `GET /api/v1/admin/optimization/health-check` - Optimization Health Check
- 🔍 `GET /api/v1/admin/optimization/performance/metrics` - Get Performance Metrics
- 🔍 `GET /api/v1/admin/optimization/performance/metrics` - Get Performance Metrics
- 🔍 `GET /api/v1/admin/optimization/recommendations` - Get Optimization Recommendations
- 🔍 `GET /api/v1/admin/optimization/recommendations` - Get Optimization Recommendations
- ➕ `POST /api/v1/admin/optimization/scaling/adjust` - Adjust Scaling
- ➕ `POST /api/v1/admin/optimization/scaling/adjust` - Adjust Scaling
- 🔍 `GET /api/v1/admin/optimization/status` - Get Optimization Status
- 🔍 `GET /api/v1/admin/optimization/status` - Get Optimization Status

---

