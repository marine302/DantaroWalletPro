# Copilot 문서 #17: 본사 슈퍼 어드민 시스템 구현

## 목표
본사가 모든 파트너사를 통합 관리할 수 있는 슈퍼 어드민 시스템을 구축합니다. 파트너사 등록, 시스템 배포, 리소스 관리, 매출 분석 등 SaaS 플랫폼 운영에 필요한 모든 기능을 제공합니다.

## 전제 조건
- Copilot 문서 #13-16이 완료되어 있어야 합니다.
- 파트너, 에너지, 수수료 모델이 정의되어 있어야 합니다.
- 기본 API 엔드포인트들이 스켈레톤 상태로 준비되어 있어야 합니다.

## 🎯 슈퍼 어드민 시스템 구조

### 📊 본사 관점의 관리 영역
```
Super Admin Dashboard
├── 🏢 파트너사 관리
│   ├── 파트너 등록/수정/삭제
│   ├── 파트너별 설정 관리
│   ├── API 키 발급/회전
│   └── 파트너별 상태 모니터링
├── 💰 에너지 풀 관리
│   ├── 전체 에너지 풀 현황
│   ├── 파트너별 에너지 할당
│   ├── 에너지 충전/소진 이력
│   └── 에너지 부족 알림
├── 💸 수수료 & 매출 관리
│   ├── 파트너별 수수료 설정
│   ├── 거래 수수료 통계
│   ├── 매출 분석 대시보드
│   └── 정산 관리
├── 📈 통합 모니터링
│   ├── 전체 시스템 상태
│   ├── 파트너별 거래량 통계
│   ├── 오류 로그 통합 관리
│   └── 성능 메트릭스
└── 🚀 온보딩 & 배포
    ├── 파트너 온보딩 프로세스
    ├── 템플릿 배포 자동화
    ├── 설정 가이드 관리
    └── 기술 지원 도구
```

## 🛠️ 구현 단계

### Phase 1: 핵심 서비스 레이어 구현 (1주)

#### 1.1 파트너 관리 서비스 ✅ (완료)
```python
# app/services/partner/partner_service.py
class PartnerService:
    async def get_all_partners() -> List[Partner]  # ✅ 구현됨
    async def get_partner_statistics_detailed() -> Dict[str, Any]  # ✅ 구현됨 
    async def bulk_update_partners() -> List[Partner]  # ✅ 구현됨
    async def get_partner_performance_ranking() -> List[Dict[str, Any]]  # ✅ 구현됨
    async def export_partner_data() -> str  # ✅ 구현됨
```

#### 1.2 에너지 풀 관리 서비스 🔄 (진행 중 - SQLAlchemy 타입 오류 수정 필요)
```python
# app/services/energy/energy_pool_service.py  
class EnergyPoolService:
    async def get_total_energy_status() -> Dict[str, Any]  # ✅ 구현됨
    async def allocate_energy_to_partner() -> bool  # ✅ 구현됨
    async def get_partner_energy_usage() -> List[Dict[str, Any]]  # ✅ 구현됨
    async def recharge_energy_pool() -> bool  # ✅ 구현됨
    async def monitor_energy_alerts() -> List[Dict[str, Any]]  # ✅ 구현됨
    async def get_energy_usage_history() -> List[Dict[str, Any]]  # ✅ 구현됨
    async def get_energy_analytics() -> Dict[str, Any]  # ✅ 구현됨
```

#### 1.3 수수료 & 매출 관리 서비스 🔄 (진행 중 - SQLAlchemy 타입 오류 수정 필요)
```python
# app/services/fee/super_admin_fee_service.py
class SuperAdminFeeService:
    async def get_total_revenue_stats() -> TotalRevenueStats  # ✅ 구현됨
    async def process_bulk_settlement() -> List[Settlement]  # ✅ 구현됨
    async def get_fee_analytics() -> Dict[str, Any]  # ✅ 구현됨
    async def configure_dynamic_pricing() -> Dict[str, Any]  # ✅ 구현됨
```
```

#### 1.2 에너지 풀 관리 서비스
```python
# app/services/energy/energy_pool_service.py
class EnergyPoolService:
    async def get_total_energy_status() -> EnergyPoolStatus
    async def allocate_energy_to_partner(partner_id: str, amount: int) -> bool
    async def get_partner_energy_usage(partner_id: str) -> EnergyUsage
    async def recharge_energy_pool(amount: int) -> bool
    async def monitor_energy_alerts() -> List[EnergyAlert]
    async def get_energy_usage_history(partner_id: str) -> List[EnergyHistory]
```

#### 1.3 수수료 & 매출 관리 서비스
```python
# app/services/fee/fee_service.py
class FeeService:
    async def set_partner_fee_config(partner_id: str, config: FeeConfig) -> bool
    async def calculate_transaction_fee(partner_id: str, amount: Decimal) -> Decimal
    async def get_partner_revenue_stats(partner_id: str) -> RevenueStats
    async def get_total_revenue_stats() -> TotalRevenueStats
    async def process_settlement(partner_id: str, period: str) -> Settlement
```

### Phase 2: 슈퍼 어드민 API 엔드포인트 구현 (3일)

#### 2.1 파트너 관리 API 강화
```python
# app/api/v1/endpoints/admin/partners.py

@router.post("/partners", response_model=Partner)
async def create_partner(partner_data: PartnerCreate)

@router.get("/partners", response_model=List[Partner])
async def list_partners(skip: int = 0, limit: int = 100)

@router.get("/partners/{partner_id}", response_model=Partner)
async def get_partner(partner_id: str)

@router.patch("/partners/{partner_id}", response_model=Partner)
async def update_partner(partner_id: str, update_data: PartnerUpdate)

@router.delete("/partners/{partner_id}")
async def delete_partner(partner_id: str)

@router.post("/partners/{partner_id}/api-key", response_model=ApiKeyResponse)
async def generate_api_key(partner_id: str)

@router.post("/partners/{partner_id}/api-key/rotate", response_model=ApiKeyResponse)
async def rotate_api_key(partner_id: str)

@router.get("/partners/{partner_id}/statistics", response_model=PartnerStats)
async def get_partner_statistics(partner_id: str)
```

#### 2.2 통합 대시보드 API
```python
# app/api/v1/endpoints/admin/dashboard.py

@router.get("/dashboard/overview", response_model=DashboardOverview)
async def get_dashboard_overview()

@router.get("/dashboard/energy-status", response_model=EnergyPoolStatus)
async def get_energy_status()

@router.get("/dashboard/revenue-stats", response_model=TotalRevenueStats)
async def get_revenue_stats()

@router.get("/dashboard/system-health", response_model=SystemHealth)
async def get_system_health()

@router.get("/dashboard/partner-rankings", response_model=List[PartnerRanking])
async def get_partner_rankings()
```

### Phase 3: 데이터베이스 확장 및 마이그레이션 (2일)

#### 3.1 새 테이블 추가
```sql
-- 파트너 설정 확장
ALTER TABLE partners ADD COLUMN custom_branding JSONB;
ALTER TABLE partners ADD COLUMN onboarding_status VARCHAR(50) DEFAULT 'pending';
ALTER TABLE partners ADD COLUMN deployment_config JSONB;

-- 에너지 사용 이력 테이블
CREATE TABLE energy_usage_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_id UUID REFERENCES partners(id),
    transaction_type VARCHAR(50),
    energy_amount INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 수수료 설정 이력 테이블
CREATE TABLE fee_config_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_id UUID REFERENCES partners(id),
    old_config JSONB,
    new_config JSONB,
    changed_by UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 시스템 메트릭스 테이블
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_type VARCHAR(100),
    metric_value DECIMAL,
    metadata JSONB,
    recorded_at TIMESTAMP DEFAULT NOW()
);
```

#### 3.2 Alembic 마이그레이션 생성
```bash
# 새 마이그레이션 파일 생성
alembic revision --autogenerate -m "add_super_admin_tables"
alembic upgrade head
```

### Phase 4: 슈퍼 어드민 프론트엔드 템플릿 (1주)

#### 4.1 React/Next.js 기반 어드민 대시보드
```typescript
// components/SuperAdminDashboard.tsx
interface SuperAdminDashboardProps {
  partnersData: Partner[];
  energyStatus: EnergyPoolStatus;
  revenueStats: TotalRevenueStats;
}

// 주요 컴포넌트들
- PartnerManagementTable
- EnergyPoolMonitor  
- RevenueAnalytics
- SystemHealthMonitor
- OnboardingWizard
```

#### 4.2 핵심 페이지 구성
```
📁 Super Admin Frontend
├── 📄 Dashboard (통합 현황)
├── 👥 Partners Management
│   ├── Partners List
│   ├── Partner Details
│   ├── Add New Partner
│   └── Partner Settings
├── ⚡ Energy Management
│   ├── Energy Pool Status
│   ├── Energy Allocation
│   └── Usage Analytics
├── 💰 Revenue & Billing
│   ├── Revenue Dashboard
│   ├── Partner Billing
│   └── Settlement Management
├── 📊 Analytics & Reports
│   ├── Business Intelligence
│   ├── Performance Metrics
│   └── Custom Reports
└── ⚙️ System Settings
    ├── Global Configuration
    ├── API Management
    └── Security Settings
```

## 🔧 기술 구현 세부사항

### 인증 & 권한 관리
```python
# app/core/security.py - 슈퍼 어드민 전용 권한
class SuperAdminPermission:
    MANAGE_PARTNERS = "manage:partners"
    MANAGE_ENERGY = "manage:energy" 
    MANAGE_BILLING = "manage:billing"
    VIEW_ANALYTICS = "view:analytics"
    SYSTEM_CONFIG = "system:config"

# 슈퍼 어드민 인증 데코레이터
@require_super_admin_permission([SuperAdminPermission.MANAGE_PARTNERS])
async def create_partner():
    pass
```

### 실시간 모니터링
```python
# app/services/monitoring/system_monitor.py
class SystemMonitorService:
    async def collect_system_metrics() -> SystemMetrics
    async def check_partner_health(partner_id: str) -> HealthStatus
    async def send_alert_notifications(alert: Alert) -> bool
    async def generate_performance_report() -> PerformanceReport
```

### 자동화된 배포
```python
# app/services/deployment/deployment_service.py
class DeploymentService:
    async def create_partner_instance(partner: Partner) -> DeploymentResult
    async def configure_partner_environment(partner_id: str) -> bool
    async def deploy_partner_templates(partner_id: str) -> DeploymentStatus
    async def setup_partner_database(partner_id: str) -> bool
```

## 📝 구현 체크리스트

### ✅ 완료해야 할 작업들

#### Phase 1: 서비스 레이어 (1주)
- [x] `PartnerService` 완전 구현 - ✅ 슈퍼 어드민용 메서드 추가 완료
- [x] `EnergyPoolService` 완전 구현 - ✅ 슈퍼 어드민용 메서드 추가 완료 
- [x] `SuperAdminFeeService` 완전 구현 - ✅ 슈퍼 어드민용 메서드 추가 완료
- [x] `SystemMonitorService` 기본 구현 - ✅ 완료
- [x] `DeploymentService` 기본 구현 - ✅ 슈퍼 어드민용 메서드 추가 완료
- [ ] 🔄 SQLAlchemy 타입 오류 수정 (진행 중)

#### Phase 2: API 엔드포인트 (3일)
- [x] 파트너 관리 API 완성 - ✅ `/admin/partners` 엔드포인트 구현 완료
- [x] 에너지 관리 API 완성 - ✅ `/admin/energy` 엔드포인트 구현 완료
- [x] 수수료 관리 API 완성 - ✅ `/admin/fee-management` 엔드포인트 구현 완료
- [x] 대시보드 API 구현 - ✅ `/admin/dashboard` 엔드포인트 구현 완료
- [x] 시스템 모니터링 API 구현 - ✅ `/admin/monitoring` 및 `/admin/system` 엔드포인트 구현 완료
- [x] 배포 관리 API 구현 - ✅ `/admin/deployment-management` 엔드포인트 구현 완료
- [ ] 🔄 임포트 오류 수정 (EnergyUsageHistory 모델 누락)

#### Phase 3: 데이터베이스 (2일)
- [ ] 새 테이블 설계 및 생성
- [ ] Alembic 마이그레이션 작성 및 실행
- [ ] 기존 데이터 무결성 검증
- [ ] 성능 최적화 (인덱스 등)

#### Phase 4: 프론트엔드 (1주)
- [ ] React/Next.js 프로젝트 설정
- [ ] 슈퍼 어드민 레이아웃 구현
- [ ] 파트너 관리 페이지
- [ ] 에너지 모니터링 대시보드
- [ ] 매출 분석 페이지
- [ ] 시스템 설정 페이지

## 🎯 성공 기준

### 기능적 요구사항
1. **파트너 관리**: 파트너사 CRUD, API 키 관리, 설정 변경이 완전히 작동해야 함
2. **에너지 관리**: 전체 에너지 풀 상태 실시간 모니터링, 파트너별 할당 관리가 가능해야 함
3. **매출 관리**: 파트너별 매출 통계, 수수료 설정, 정산 기능이 작동해야 함
4. **모니터링**: 시스템 상태, 파트너별 성능 지표를 실시간으로 확인 가능해야 함

### 비기능적 요구사항
1. **성능**: 대시보드 로딩 시간 < 3초
2. **확장성**: 100개 파트너사까지 동시 관리 가능
3. **보안**: 슈퍼 어드민 권한 체계 완전 구현
4. **가용성**: 99.9% 업타임 목표

## 🚀 다음 단계 (copilot-doc-18)
본사 슈퍼 어드민 시스템 구현 완료 후, 파트너용 템플릿(어드민 + 사용자 UI) 개발에 착수합니다. 파트너사가 즉시 사용할 수 있는 완전한 화이트라벨 솔루션을 제공하는 것이 목표입니다.

---

**구현 순서**: 서비스 레이어 → API 강화 → DB 마이그레이션 → 프론트엔드 → 통합 테스트 → 문서화
