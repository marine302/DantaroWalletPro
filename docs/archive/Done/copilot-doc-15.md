# Copilot 문서 #15: 파트너사 관리 시스템 (화이트라벨링) 구현

## 목표
여러 파트너사가 각자의 사용자 풀을 관리할 수 있는 멀티테넌트 화이트라벨링 시스템을 구현합니다.

## 전제 조건
- Copilot 문서 #1-14가 완료되어 있어야 합니다.
- 기본 사용자 관리 시스템이 구현되어 있어야 합니다.
- 동적 수수료 시스템이 구현되어 있어야 합니다.

## 상세 지시사항

### 1. 파트너사 모델 구현

`app/models/partner.py` 파일을 생성하세요:

```python
"""파트너사 관련 모델"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

class Partner(Base):
    """파트너사 테이블"""
    __tablename__ = "partners"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="파트너사명")
    domain = Column(String(255), comment="도메인")
    api_key = Column(String(255), unique=True, nullable=False, comment="API 키")
    api_secret = Column(String(255), nullable=False, comment="API 시크릿")
    webhook_url = Column(String(500), comment="웹훅 URL")
    commission_rate = Column(Numeric(5, 4), default=0, comment="수수료율")
    is_active = Column(Boolean, default=True, comment="활성 상태")
    settings = Column(Text, comment="커스텀 설정 (JSON)")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    users = relationship("PartnerUser", back_populates="partner")

class PartnerUser(Base):
    """파트너-사용자 매핑 테이블"""
    __tablename__ = "partner_users"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, nullable=False, comment="파트너사 ID")
    user_id = Column(Integer, nullable=False, comment="사용자 ID")
    partner_user_id = Column(String(255), comment="파트너사 내부 사용자 ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    partner = relationship("Partner", back_populates="users")

class PartnerBranding(Base):
    """파트너사 브랜딩 설정 테이블"""
    __tablename__ = "partner_branding"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, nullable=False, unique=True, comment="파트너사 ID")
    logo_url = Column(String(500), comment="로고 URL")
    primary_color = Column(String(7), comment="기본 색상 (#FFFFFF)")
    secondary_color = Column(String(7), comment="보조 색상")
    custom_css = Column(Text, comment="커스텀 CSS")
    favicon_url = Column(String(500), comment="파비콘 URL")
    company_name = Column(String(100), comment="회사명 표시")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 2. 파트너사 관리 API 구현

`app/api/v1/endpoints/admin/partners.py` 파일을 업데이트하세요:

```python
"""파트너사 관리 API 엔드포인트"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_admin_user
from app.models.user import User
from app.schemas.partner import (
    PartnerCreate, PartnerUpdate, PartnerResponse,
    PartnerBrandingUpdate, PartnerStatsResponse
)
from app.services.partner.partner_manager import PartnerService

router = APIRouter(tags=["파트너사 관리"])

@router.get("/", response_model=List[PartnerResponse])
async def get_partners_list(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    search: Optional[str] = Query(None, description="파트너사명 검색"),
    is_active: Optional[bool] = Query(None, description="활성 상태 필터"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """파트너사 목록을 조회합니다."""
    partner_service = PartnerService(db)
    return await partner_service.get_partners_list(page, size, search, is_active)

@router.post("/", response_model=PartnerResponse)
async def create_partner(
    partner_data: PartnerCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """새로운 파트너사를 등록합니다."""
    partner_service = PartnerService(db)
    return await partner_service.create_partner(partner_data, current_admin.id)

@router.get("/{partner_id}", response_model=PartnerResponse)
async def get_partner_detail(
    partner_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """파트너사 상세 정보를 조회합니다."""
    partner_service = PartnerService(db)
    partner = await partner_service.get_partner_by_id(partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="파트너사를 찾을 수 없습니다")
    return partner

@router.patch("/{partner_id}", response_model=PartnerResponse)
async def update_partner(
    partner_id: int,
    partner_update: PartnerUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """파트너사 정보를 수정합니다."""
    partner_service = PartnerService(db)
    return await partner_service.update_partner(partner_id, partner_update)

@router.get("/{partner_id}/stats", response_model=PartnerStatsResponse)
async def get_partner_stats(
    partner_id: int,
    days: int = Query(30, ge=1, le=365, description="통계 기간 (일)"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """파트너사별 통계를 조회합니다."""
    partner_service = PartnerService(db)
    return await partner_service.get_partner_stats(partner_id, days)

@router.put("/{partner_id}/branding")
async def update_partner_branding(
    partner_id: int,
    branding_data: PartnerBrandingUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """파트너사 브랜딩 설정을 업데이트합니다."""
    partner_service = PartnerService(db)
    return await partner_service.update_branding(partner_id, branding_data)

@router.post("/{partner_id}/users/{user_id}")
async def assign_user_to_partner(
    partner_id: int,
    user_id: int,
    partner_user_id: Optional[str] = None,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """사용자를 파트너사에 할당합니다."""
    partner_service = PartnerService(db)
    return await partner_service.assign_user(partner_id, user_id, partner_user_id)
```

### 3. 파트너 API (외부 연동용) 구현

`app/api/v1/endpoints/partner_api.py` 파일을 생성하세요:

```python
"""파트너사용 외부 API 엔드포인트"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_partner_from_api_key
from app.models.partner import Partner
from app.schemas.partner_api import (
    PartnerUserCreate, PartnerUserResponse,
    PartnerTransactionResponse
)
from app.services.partner.api_service import PartnerAPIService

router = APIRouter(tags=["파트너 API"])

@router.post("/auth")
async def authenticate_partner(
    api_key: str = Header(..., alias="X-API-Key"),
    api_secret: str = Header(..., alias="X-API-Secret"),
    db: AsyncSession = Depends(get_db),
):
    """파트너 API 키 인증"""
    partner_service = PartnerAPIService(db)
    partner = await partner_service.authenticate(api_key, api_secret)
    if not partner:
        raise HTTPException(status_code=401, detail="인증 실패")
    
    return {
        "partner_id": partner.id,
        "partner_name": partner.name,
        "authenticated": True
    }

@router.get("/users", response_model=List[PartnerUserResponse])
async def get_partner_users(
    page: int = 1,
    size: int = 50,
    current_partner: Partner = Depends(get_partner_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    """파트너사 사용자 목록 조회"""
    partner_service = PartnerAPIService(db)
    return await partner_service.get_users(current_partner.id, page, size)

@router.post("/users", response_model=PartnerUserResponse)
async def create_partner_user(
    user_data: PartnerUserCreate,
    current_partner: Partner = Depends(get_partner_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    """파트너사 사용자 생성"""
    partner_service = PartnerAPIService(db)
    return await partner_service.create_user(current_partner.id, user_data)

@router.get("/transactions", response_model=List[PartnerTransactionResponse])
async def get_partner_transactions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    transaction_type: Optional[str] = None,
    current_partner: Partner = Depends(get_partner_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    """파트너사 거래 내역 조회"""
    partner_service = PartnerAPIService(db)
    return await partner_service.get_transactions(
        current_partner.id, start_date, end_date, transaction_type
    )

@router.post("/webhook")
async def receive_webhook(
    webhook_data: dict,
    current_partner: Partner = Depends(get_partner_from_api_key),
    db: AsyncSession = Depends(get_db),
):
    """웹훅 수신 처리"""
    partner_service = PartnerAPIService(db)
    return await partner_service.process_webhook(current_partner.id, webhook_data)
```

### 4. 파트너사 관리 서비스 구현

`app/services/partner/` 디렉토리를 생성하고 다음 파일들을 구현하세요:

#### `partner_manager.py`:
```python
"""파트너사 관리 서비스"""
import secrets
import hashlib
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.partner import Partner, PartnerUser, PartnerBranding
from app.schemas.partner import PartnerCreate, PartnerUpdate

class PartnerService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_partner(self, partner_data: PartnerCreate, admin_id: int) -> Partner:
        """새 파트너사 생성"""
        # API 키/시크릿 생성
        api_key = self._generate_api_key()
        api_secret = self._generate_api_secret()
        
        partner = Partner(
            **partner_data.dict(),
            api_key=api_key,
            api_secret=hashlib.sha256(api_secret.encode()).hexdigest()
        )
        
        self.db.add(partner)
        await self.db.commit()
        await self.db.refresh(partner)
        
        # 초기 브랜딩 설정 생성
        await self._create_default_branding(partner.id)
        
        return partner
    
    async def get_partners_list(
        self, 
        page: int, 
        size: int, 
        search: Optional[str], 
        is_active: Optional[bool]
    ) -> List[Partner]:
        """파트너사 목록 조회"""
        query = select(Partner)
        
        if search:
            query = query.where(Partner.name.ilike(f"%{search}%"))
        if is_active is not None:
            query = query.where(Partner.is_active == is_active)
        
        query = query.offset((page - 1) * size).limit(size)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def assign_user(
        self, 
        partner_id: int, 
        user_id: int, 
        partner_user_id: Optional[str] = None
    ):
        """사용자를 파트너사에 할당"""
        partner_user = PartnerUser(
            partner_id=partner_id,
            user_id=user_id,
            partner_user_id=partner_user_id
        )
        
        self.db.add(partner_user)
        await self.db.commit()
        
        return {"message": "사용자가 파트너사에 할당되었습니다"}
    
    def _generate_api_key(self) -> str:
        """API 키 생성"""
        return f"pk_{secrets.token_urlsafe(32)}"
    
    def _generate_api_secret(self) -> str:
        """API 시크릿 생성"""
        return secrets.token_urlsafe(64)
    
    async def _create_default_branding(self, partner_id: int):
        """기본 브랜딩 설정 생성"""
        branding = PartnerBranding(
            partner_id=partner_id,
            primary_color="#3B82F6",
            secondary_color="#1E40AF",
            company_name="DantaroWallet"
        )
        
        self.db.add(branding)
        await self.db.commit()
```

#### `user_mapper.py`:
```python
"""파트너사 사용자 매핑 관리"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.partner import PartnerUser
from app.models.user import User

class PartnerUserMapper:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_partner_users(self, partner_id: int) -> List[User]:
        """파트너사의 모든 사용자 조회"""
        query = select(User).join(PartnerUser).where(
            PartnerUser.partner_id == partner_id
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_user_partner(self, user_id: int) -> Optional[int]:
        """사용자의 파트너사 ID 조회"""
        query = select(PartnerUser.partner_id).where(
            PartnerUser.user_id == user_id
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def is_partner_user(self, partner_id: int, user_id: int) -> bool:
        """사용자가 특정 파트너사에 속하는지 확인"""
        query = select(PartnerUser).where(
            and_(
                PartnerUser.partner_id == partner_id,
                PartnerUser.user_id == user_id
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
```

### 5. 프론트엔드 파트너사 관리 인터페이스

#### 관리자 파트너사 목록 페이지:
```typescript
// PartnerManagementPage.tsx
interface Partner {
  id: number;
  name: string;
  domain: string;
  is_active: boolean;
  commission_rate: number;
  user_count: number;
  created_at: string;
}

const PartnerManagementPage = () => {
  const [partners, setPartners] = useState<Partner[]>([]);
  const [selectedPartner, setSelectedPartner] = useState<Partner | null>(null);

  return (
    <div className="partner-management">
      <div className="page-header">
        <h2>🏢 파트너사 관리</h2>
        <button 
          className="btn btn-primary"
          onClick={() => setShowCreateModal(true)}
        >
          + 파트너사 등록
        </button>
      </div>
      
      <div className="partners-grid">
        {partners.map(partner => (
          <PartnerCard 
            key={partner.id}
            partner={partner}
            onClick={() => setSelectedPartner(partner)}
          />
        ))}
      </div>
      
      {selectedPartner && (
        <PartnerDetailModal 
          partner={selectedPartner}
          onClose={() => setSelectedPartner(null)}
        />
      )}
    </div>
  );
};

const PartnerCard = ({ partner, onClick }) => (
  <div className="partner-card" onClick={onClick}>
    <div className="partner-header">
      <h4>{partner.name}</h4>
      <span className={`status ${partner.is_active ? 'active' : 'inactive'}`}>
        {partner.is_active ? '활성' : '비활성'}
      </span>
    </div>
    <div className="partner-stats">
      <div className="stat">
        <span>도메인:</span>
        <span>{partner.domain || 'N/A'}</span>
      </div>
      <div className="stat">
        <span>사용자 수:</span>
        <span>{partner.user_count}명</span>
      </div>
      <div className="stat">
        <span>수수료율:</span>
        <span>{partner.commission_rate}%</span>
      </div>
    </div>
  </div>
);
```

#### 파트너사 브랜딩 설정 페이지:
```typescript
// PartnerBrandingPage.tsx
const PartnerBrandingPage = ({ partnerId }: { partnerId: number }) => {
  const [branding, setBranding] = useState({
    logo_url: '',
    primary_color: '#3B82F6',
    secondary_color: '#1E40AF',
    company_name: '',
    custom_css: ''
  });

  return (
    <div className="branding-settings">
      <h3>🎨 브랜딩 설정</h3>
      
      <div className="branding-form">
        <div className="form-group">
          <label>로고 URL</label>
          <input 
            type="url"
            value={branding.logo_url}
            onChange={(e) => setBranding({...branding, logo_url: e.target.value})}
          />
        </div>
        
        <div className="color-settings">
          <div className="form-group">
            <label>기본 색상</label>
            <input 
              type="color"
              value={branding.primary_color}
              onChange={(e) => setBranding({...branding, primary_color: e.target.value})}
            />
          </div>
          
          <div className="form-group">
            <label>보조 색상</label>
            <input 
              type="color"
              value={branding.secondary_color}
              onChange={(e) => setBranding({...branding, secondary_color: e.target.value})}
            />
          </div>
        </div>
        
        <div className="form-group">
          <label>회사명</label>
          <input 
            type="text"
            value={branding.company_name}
            onChange={(e) => setBranding({...branding, company_name: e.target.value})}
          />
        </div>
        
        <div className="form-group">
          <label>커스텀 CSS</label>
          <textarea 
            value={branding.custom_css}
            onChange={(e) => setBranding({...branding, custom_css: e.target.value})}
            rows={10}
          />
        </div>
      </div>
      
      <div className="preview-section">
        <h4>미리보기</h4>
        <BrandingPreview branding={branding} />
      </div>
    </div>
  );
};
```

### 6. 데이터베이스 마이그레이션

```python
"""파트너사 관리 테이블 추가

Revision ID: partner_system_001
Revises: fee_config_001
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # 파트너사 테이블
    op.create_table('partners',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('domain', sa.String(255), nullable=True),
        sa.Column('api_key', sa.String(255), nullable=False, unique=True),
        sa.Column('api_secret', sa.String(255), nullable=False),
        sa.Column('webhook_url', sa.String(500), nullable=True),
        sa.Column('commission_rate', sa.Numeric(5, 4), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('settings', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 파트너-사용자 매핑 테이블
    op.create_table('partner_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('partner_user_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('partner_id', 'user_id'),
        sa.UniqueConstraint('partner_id', 'partner_user_id')
    )
    
    # 파트너 브랜딩 테이블
    op.create_table('partner_branding',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.Integer(), nullable=False, unique=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('primary_color', sa.String(7), nullable=True),
        sa.Column('secondary_color', sa.String(7), nullable=True),
        sa.Column('custom_css', sa.Text(), nullable=True),
        sa.Column('favicon_url', sa.String(500), nullable=True),
        sa.Column('company_name', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 기존 users 테이블에 partner_id 컬럼 추가
    op.add_column('users', sa.Column('partner_id', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('users', 'partner_id')
    op.drop_table('partner_branding')
    op.drop_table('partner_users')
    op.drop_table('partners')
```

## 검증 포인트

- [ ] 파트너사 등록 및 관리가 정상 작동하는가?
- [ ] 파트너별 사용자 분리가 올바르게 구현되었는가?
- [ ] 파트너 API 인증이 안전하게 작동하는가?
- [ ] 브랜딩 설정이 정상 적용되는가?
- [ ] 파트너별 통계 조회가 정확한가?

## 예상 결과
- 여러 파트너사가 독립적으로 사용자 풀 관리 가능
- 파트너별 브랜딩으로 화이트라벨 서비스 제공
- 안전한 API 기반 외부 연동 지원
- 파트너사별 상세 통계 및 분석 제공
