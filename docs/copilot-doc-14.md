# Copilot 문서 #14: 동적 수수료 관리 시스템 구현

## 목표
관리자가 실시간으로 수수료율을 조정할 수 있는 동적 수수료 관리 시스템을 구현합니다.

## 전제 조건
- Copilot 문서 #1-13이 완료되어 있어야 합니다.
- 기본 관리자 시스템이 구현되어 있어야 합니다.
- 출금 시스템이 구현되어 있어야 합니다.

## 상세 지시사항

### 1. 수수료 설정 모델 구현

`app/models/fee_config.py` 파일을 생성하세요:

```python
"""수수료 설정 관련 모델"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.models.base import Base

class FeeConfig(Base):
    """수수료 설정 테이블"""
    __tablename__ = "fee_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_type = Column(String(50), nullable=False, comment="거래 유형")
    base_fee = Column(Numeric(18, 8), nullable=False, comment="기본 수수료")
    percentage_fee = Column(Numeric(5, 4), nullable=False, comment="비율 수수료")
    min_fee = Column(Numeric(18, 8), nullable=False, comment="최소 수수료")
    max_fee = Column(Numeric(18, 8), nullable=False, comment="최대 수수료")
    partner_id = Column(Integer, nullable=True, comment="파트너사 ID (NULL이면 글로벌)")
    is_active = Column(Boolean, default=True, comment="활성 상태")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class FeeHistory(Base):
    """수수료 변경 이력 테이블"""
    __tablename__ = "fee_history"
    
    id = Column(Integer, primary_key=True, index=True)
    fee_config_id = Column(Integer, nullable=False, comment="수수료 설정 ID")
    old_values = Column(Text, comment="이전 설정값 (JSON)")
    new_values = Column(Text, comment="새 설정값 (JSON)")
    changed_by = Column(Integer, nullable=False, comment="변경한 관리자 ID")
    change_reason = Column(String(500), comment="변경 사유")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### 2. 수수료 관리 API 엔드포인트 구현

`app/api/v1/endpoints/admin/fees.py` 파일을 업데이트하세요:

```python
"""수수료 관리 API 엔드포인트"""
from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_admin_user
from app.models.user import User
from app.schemas.fee import FeeConfigCreate, FeeConfigUpdate, FeeConfigResponse
from app.services.fee.config_manager import FeeConfigService

router = APIRouter(tags=["수수료 관리"])

@router.get("/config", response_model=List[FeeConfigResponse])
async def get_fee_configs(
    partner_id: Optional[int] = Query(None, description="파트너사 ID"),
    transaction_type: Optional[str] = Query(None, description="거래 유형"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """현재 수수료 설정을 조회합니다."""
    fee_service = FeeConfigService(db)
    return await fee_service.get_configs(partner_id, transaction_type)

@router.post("/config", response_model=FeeConfigResponse)
async def create_fee_config(
    config_data: FeeConfigCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """새로운 수수료 설정을 생성합니다."""
    fee_service = FeeConfigService(db)
    return await fee_service.create_config(config_data, current_admin.id)

@router.patch("/config/{config_id}", response_model=FeeConfigResponse)
async def update_fee_config(
    config_id: int,
    config_update: FeeConfigUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """기존 수수료 설정을 수정합니다."""
    fee_service = FeeConfigService(db)
    return await fee_service.update_config(config_id, config_update, current_admin.id)

@router.post("/calculate")
async def calculate_fee(
    transaction_type: str,
    amount: Decimal,
    partner_id: Optional[int] = None,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """특정 거래에 대한 수수료를 미리 계산합니다."""
    fee_calculator = FeeCalculator(db)
    calculated_fee = await fee_calculator.calculate(transaction_type, amount, partner_id)
    return {
        "amount": str(amount),
        "calculated_fee": str(calculated_fee),
        "effective_rate": str(calculated_fee / amount * 100) + "%"
    }
```

### 3. 수수료 계산 서비스 구현

`app/services/fee/` 디렉토리를 생성하고 다음 파일들을 구현하세요:

#### `calculator.py`:
```python
"""동적 수수료 계산 서비스"""
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.fee_config import FeeConfig

class FeeCalculator:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def calculate(
        self, 
        transaction_type: str, 
        amount: Decimal,
        partner_id: Optional[int] = None
    ) -> Decimal:
        """수수료를 계산합니다."""
        
        # 파트너별 설정 우선 조회
        config = await self._get_fee_config(transaction_type, partner_id)
        
        if not config:
            # 글로벌 설정 조회
            config = await self._get_fee_config(transaction_type, None)
        
        if not config:
            raise ValueError(f"수수료 설정을 찾을 수 없습니다: {transaction_type}")
        
        # 수수료 계산
        percentage_fee = amount * config.percentage_fee
        total_fee = config.base_fee + percentage_fee
        
        # 최소/최대 수수료 적용
        total_fee = max(total_fee, config.min_fee)
        total_fee = min(total_fee, config.max_fee)
        
        return total_fee
    
    async def _get_fee_config(
        self, 
        transaction_type: str, 
        partner_id: Optional[int]
    ) -> Optional[FeeConfig]:
        """수수료 설정 조회"""
        query = select(FeeConfig).where(
            FeeConfig.transaction_type == transaction_type,
            FeeConfig.partner_id == partner_id,
            FeeConfig.is_active == True
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
```

#### `config_manager.py`:
```python
"""수수료 설정 관리 서비스"""
import json
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.fee_config import FeeConfig, FeeHistory
from app.schemas.fee import FeeConfigCreate, FeeConfigUpdate

class FeeConfigService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_config(
        self, 
        config_data: FeeConfigCreate, 
        admin_id: int
    ) -> FeeConfig:
        """새 수수료 설정 생성"""
        config = FeeConfig(**config_data.dict())
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        
        # 변경 이력 기록
        await self._record_history(config.id, None, config_data.dict(), admin_id)
        
        return config
    
    async def update_config(
        self, 
        config_id: int, 
        config_update: FeeConfigUpdate, 
        admin_id: int
    ) -> FeeConfig:
        """수수료 설정 수정"""
        # 기존 설정 조회
        query = select(FeeConfig).where(FeeConfig.id == config_id)
        result = await self.db.execute(query)
        config = result.scalar_one_or_none()
        
        if not config:
            raise ValueError("수수료 설정을 찾을 수 없습니다")
        
        # 이전 값 저장
        old_values = {
            "base_fee": str(config.base_fee),
            "percentage_fee": str(config.percentage_fee),
            "min_fee": str(config.min_fee),
            "max_fee": str(config.max_fee)
        }
        
        # 새 값 적용
        update_data = config_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)
        
        await self.db.commit()
        await self.db.refresh(config)
        
        # 변경 이력 기록
        await self._record_history(config_id, old_values, update_data, admin_id)
        
        return config
    
    async def _record_history(
        self, 
        config_id: int, 
        old_values: dict, 
        new_values: dict, 
        admin_id: int
    ):
        """변경 이력 기록"""
        history = FeeHistory(
            fee_config_id=config_id,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values),
            changed_by=admin_id
        )
        self.db.add(history)
        await self.db.commit()
```

### 4. 사용자 수수료 안내 API

`app/api/v1/endpoints/fees.py` 파일을 생성하세요:

```python
"""사용자용 수수료 안내 API"""
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.fee.calculator import FeeCalculator

router = APIRouter(tags=["수수료 안내"])

@router.get("/estimate")
async def estimate_withdrawal_fee(
    amount: Decimal = Query(..., description="출금 금액"),
    currency: str = Query("USDT", description="통화"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """출금 수수료를 견적합니다."""
    fee_calculator = FeeCalculator(db)
    
    # 사용자 파트너 ID 확인 (없으면 None)
    partner_id = getattr(current_user, 'partner_id', None)
    
    calculated_fee = await fee_calculator.calculate(
        "withdrawal", amount, partner_id
    )
    
    return {
        "withdrawal_amount": str(amount),
        "currency": currency,
        "platform_fee": str(calculated_fee),
        "actual_amount": str(amount - calculated_fee),
        "network_fee": "0 (본사 지원)",
        "total_cost": str(calculated_fee)
    }

@router.get("/current-rates")
async def get_current_fee_rates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """현재 적용되는 수수료율을 조회합니다."""
    # TODO: 사용자별 적용 수수료율 조회
    return {
        "withdrawal": {
            "percentage": "2.0%",
            "minimum": "1.0 USDT",
            "maximum": "50.0 USDT"
        },
        "internal_transfer": {
            "percentage": "0%",
            "minimum": "0 USDT",
            "maximum": "0 USDT"
        }
    }
```

### 5. 프론트엔드 수수료 관리 인터페이스

#### 관리자 수수료 설정 페이지:
```typescript
// FeeManagementPage.tsx
interface FeeConfig {
  id: number;
  transaction_type: string;
  base_fee: string;
  percentage_fee: string;
  min_fee: string;
  max_fee: string;
  partner_id?: number;
  is_active: boolean;
}

const FeeManagementPage = () => {
  const [feeConfigs, setFeeConfigs] = useState<FeeConfig[]>([]);
  const [editingConfig, setEditingConfig] = useState<FeeConfig | null>(null);

  return (
    <div className="fee-management">
      <h2>💰 수수료 관리</h2>
      
      <div className="global-settings">
        <h3>글로벌 설정</h3>
        <FeeConfigTable 
          configs={feeConfigs.filter(c => !c.partner_id)}
          onEdit={setEditingConfig}
        />
      </div>
      
      <div className="partner-settings">
        <h3>파트너별 설정</h3>
        <FeeConfigTable 
          configs={feeConfigs.filter(c => c.partner_id)}
          onEdit={setEditingConfig}
        />
      </div>
      
      {editingConfig && (
        <FeeConfigEditModal 
          config={editingConfig}
          onSave={handleSave}
          onClose={() => setEditingConfig(null)}
        />
      )}
    </div>
  );
};
```

#### 사용자 수수료 안내 컴포넌트:
```typescript
// WithdrawalFeeInfo.tsx
const WithdrawalFeeInfo = ({ amount }: { amount: number }) => {
  const [feeEstimate, setFeeEstimate] = useState(null);

  useEffect(() => {
    if (amount > 0) {
      fetchFeeEstimate(amount).then(setFeeEstimate);
    }
  }, [amount]);

  return (
    <div className="fee-info-card">
      <h4>✅ 출금 수수료 안내</h4>
      <div className="fee-breakdown">
        <div className="fee-line">
          <span>출금 금액:</span>
          <span>{amount} USDT</span>
        </div>
        <div className="fee-line">
          <span>플랫폼 수수료:</span>
          <span>{feeEstimate?.platform_fee} USDT</span>
        </div>
        <hr />
        <div className="fee-line total">
          <span>실제 출금액:</span>
          <span>{feeEstimate?.actual_amount} USDT</span>
        </div>
        <div className="network-fee-notice">
          🎉 TRON 네트워크 수수료: 무료 (본사가 대신 지불합니다)
        </div>
      </div>
    </div>
  );
};
```

### 6. 데이터베이스 마이그레이션

Alembic 마이그레이션 파일을 생성하세요:

```python
"""수수료 관리 테이블 추가

Revision ID: fee_config_001
Revises: previous_revision
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # 수수료 설정 테이블
    op.create_table('fee_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(50), nullable=False),
        sa.Column('base_fee', sa.Numeric(18, 8), nullable=False),
        sa.Column('percentage_fee', sa.Numeric(5, 4), nullable=False),
        sa.Column('min_fee', sa.Numeric(18, 8), nullable=False),
        sa.Column('max_fee', sa.Numeric(18, 8), nullable=False),
        sa.Column('partner_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 수수료 변경 이력 테이블
    op.create_table('fee_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fee_config_id', sa.Integer(), nullable=False),
        sa.Column('old_values', sa.Text()),
        sa.Column('new_values', sa.Text()),
        sa.Column('changed_by', sa.Integer(), nullable=False),
        sa.Column('change_reason', sa.String(500)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('fee_history')
    op.drop_table('fee_configs')
```

### 7. API 라우터 등록

메인 API 라우터에 수수료 관련 엔드포인트를 등록하세요:

```python
# app/api/v1/api.py
from app.api.v1.endpoints import fees

api_router.include_router(fees.router, prefix="/fees", tags=["fees"])
```

## 검증 포인트

- [ ] 관리자가 수수료율을 실시간으로 변경할 수 있는가?
- [ ] 파트너별 수수료 차별화가 정상 작동하는가?
- [ ] 수수료 변경 이력이 올바르게 기록되는가?
- [ ] 사용자가 출금 전 정확한 수수료를 확인할 수 있는가?
- [ ] 수수료 계산 로직이 정확하게 작동하는가?

## 예상 결과
- 관리자가 시장 상황에 따라 수수료를 유연하게 조정 가능
- 파트너사별로 차별화된 수수료 정책 적용 가능  
- 사용자에게 투명한 수수료 정보 제공
- 모든 수수료 변경 내역의 완전한 추적 가능
