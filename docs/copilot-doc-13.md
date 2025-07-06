# Copilot 문서 #13: 에너지 풀 부족 대응 시스템 구현

## 목표
TRON 에너지 풀 부족 상황에서 서비스 중단을 방지하기 위한 대응 시스템을 구현합니다.

## 전제 조건
- Copilot 문서 #1-12가 완료되어 있어야 합니다.
- 기본 출금 시스템이 구현되어 있어야 합니다.
- TRON 네트워크 연동이 완료되어 있어야 합니다.

## 상세 지시사항

### 1. 사용자용 에너지 상태 확인 API 구현

`app/api/v1/endpoints/energy.py` 파일을 생성하세요:

```python
"""
사용자용 에너지 관련 API 엔드포인트
"""
from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(tags=["에너지 상태"])

@router.get("/status")
async def get_energy_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """현재 에너지 풀 상태를 확인합니다."""
    return {
        "available_energy": 1500000,
        "daily_consumption": 85000,
        "energy_sufficient": True,
        "estimated_wait_time": 0,
        "queue_position": 0,
        "alert_message": None
    }

@router.post("/emergency-withdrawal")
async def create_emergency_withdrawal(
    to_address: str,
    amount: Decimal,
    currency: str = "USDT",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """에너지 부족 시 TRX 직접 지불하여 즉시 출금합니다."""
    return {
        "message": "긴급 출금 요청이 접수되었습니다",
        "withdrawal_id": "temp_id_123",
        "estimated_trx_fee": 13,
        "status": "pending_trx_payment"
    }
```

### 2. 관리자용 에너지 풀 관리 API 구현

`app/api/v1/endpoints/admin/energy.py` 파일을 업데이트하세요:

```python
"""
TRON 에너지 풀 관리 API 엔드포인트
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_admin_user
from app.models.user import User

router = APIRouter(tags=["에너지 풀 관리"])

@router.get("/status")
async def get_energy_pools_status(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """모든 에너지 풀의 현재 상태를 조회합니다."""
    # TODO: 실제 에너지 풀 조회 로직 구현
    return {
        "pools": [
            {
                "id": 1,
                "wallet_address": "TRX123...",
                "frozen_trx": 50000,
                "available_energy": 1500000,
                "daily_consumption": 85000,
                "status": "active"
            }
        ]
    }

@router.post("/create-pool")
async def create_energy_pool(
    wallet_address: str,
    trx_amount: float,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """새로운 에너지 풀을 생성합니다."""
    # TODO: 에너지 풀 생성 로직 구현
    return {"message": "에너지 풀 생성 완료", "pool_id": 1}
```

### 3. 에너지 서비스 레이어 구현

`app/services/energy/` 디렉토리를 생성하고 다음 파일들을 구현하세요:

#### `pool_manager.py`:
```python
"""에너지 풀 관리 서비스"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.energy_pool import EnergyPool

class EnergyPoolManager:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_current_status(self):
        """현재 에너지 상태 조회"""
        # TODO: 실제 구현
        pass
    
    async def check_sufficient_energy(self, required_energy: int) -> bool:
        """에너지 충분 여부 확인"""
        # TODO: 실제 구현
        return True
```

#### `emergency_handler.py`:
```python
"""에너지 부족 시 긴급 처리 서비스"""
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

class EmergencyWithdrawalService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def process_emergency_withdrawal(
        self, 
        user_id: int, 
        to_address: str, 
        amount: Decimal
    ):
        """TRX 직접 결제로 긴급 출금 처리"""
        # TODO: 실제 구현
        pass
```

### 4. 프론트엔드 에너지 상태 UI 컴포넌트

#### 사용자 출금 페이지에 에너지 상태 표시:
```javascript
// EnergyStatusAlert.tsx
const EnergyStatusAlert = () => {
  return (
    <div className="energy-status-alert">
      {energyStatus.energy_sufficient ? (
        <div className="alert alert-success">
          ✅ 네트워크 수수료 무료 (에너지 충분)
        </div>
      ) : (
        <div className="alert alert-warning">
          ⚠️ 현재 네트워크가 혼잡합니다
          <div className="emergency-options">
            <button>대기 (예상: 2-4시간)</button>
            <button>TRX로 즉시 출금 (~13 TRX)</button>
          </div>
        </div>
      )}
    </div>
  );
};
```

#### 관리자 에너지 모니터링 대시보드:
```javascript
// EnergyPoolDashboard.tsx
const EnergyPoolDashboard = () => {
  return (
    <div className="energy-dashboard">
      <div className="energy-status-card">
        <h3>🔋 에너지 풀 현황</h3>
        <div className="status-indicator">
          🟢 에너지 충분 (1,500,000)
        </div>
        <div className="metrics">
          <p>📊 일일 소비율: 85%</p>
          <p>💰 동결 TRX: 50,000</p>
          <p>⚡ 예상 지속시간: 17일</p>
        </div>
      </div>
    </div>
  );
};
```

### 5. 데이터베이스 마이그레이션

#### 에너지 대기열 테이블 추가:
```sql
-- 에너지 대기열 테이블
CREATE TABLE energy_withdrawal_queue (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    withdrawal_id INTEGER NOT NULL,
    queue_position INTEGER NOT NULL,
    estimated_wait_time INTEGER, -- 분 단위
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'waiting'
);

-- 긴급 출금 테이블  
CREATE TABLE emergency_withdrawals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    withdrawal_id INTEGER NOT NULL,
    trx_fee_amount DECIMAL(18,8) NOT NULL,
    trx_tx_hash VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);
```

### 6. 에너지 모니터링 및 알림

#### 에너지 임계값 모니터링:
```python
# app/services/energy/threshold_monitor.py
class EnergyThresholdMonitor:
    ALERT_THRESHOLDS = {
        "warning": 0.9,  # 90%
        "critical": 0.95,  # 95%
        "emergency": 0.98  # 98%
    }
    
    async def check_and_alert(self):
        """에너지 임계값 확인 및 알림"""
        current_usage = await self.get_current_usage_rate()
        
        if current_usage >= self.ALERT_THRESHOLDS["emergency"]:
            await self.send_emergency_alert()
        elif current_usage >= self.ALERT_THRESHOLDS["critical"]:
            await self.send_critical_alert()
        elif current_usage >= self.ALERT_THRESHOLDS["warning"]:
            await self.send_warning_alert()
```

### 7. API 라우터 등록

`app/api/v1/api.py`에 새로운 라우터를 등록하세요:

```python
from app.api.v1.endpoints import energy

api_router.include_router(energy.router, prefix="/energy", tags=["energy"])
```

## 검증 포인트

- [ ] 에너지 상태 확인 API가 정상 작동하는가?
- [ ] 에너지 부족 시 TRX 직접 결제 옵션이 제공되는가?
- [ ] 관리자가 에너지 풀 상태를 모니터링할 수 있는가?
- [ ] 에너지 임계값 알림이 정상 작동하는가?
- [ ] 사용자 UI에서 에너지 상태가 명확히 표시되는가?

## 예상 결과
- 에너지 풀 부족 시에도 서비스 중단 없이 운영 가능
- 사용자가 상황에 따라 대기 또는 즉시 처리 선택 가능
- 관리자가 실시간으로 에너지 상태 모니터링 가능
