# Copilot 문서 #28: 파트너사 관리 시스템 (화이트라벨링) 구현

## 목표
여러 파트너사가 각자의 브랜드로 서비스를 운영할 수 있도록 완전한 멀티테넌트 화이트라벨 시스템을 구축합니다.

## 상세 지시사항

### 1. 파트너사 모델 및 관계 설정

#### 1.1 파트너사 관련 모델
```python
# app/models/partner.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Numeric, ForeignKey, Enum
from sqlalchemy.orm import relationship
from decimal import Decimal
import enum
import uuid

class PartnerTier(enum.Enum):
    STARTER = "starter"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

class PartnerStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"

class Partner(Base):
    __tablename__ = "partners"
    
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    
    # 기본 정보
    company_name = Column(String(200), nullable=False, unique=True)
    legal_name = Column(String(200))
    business_registration = Column(String(100))
    tax_id = Column(String(100))
    
    # 연락처 정보
    primary_email = Column(String(255), nullable=False)
    billing_email = Column(String(255))
    support_email = Column(String(255))
    phone = Column(String(50))
    
    # 주소
    address = Column(JSON)  # {street, city, state, postal_code, country}
    
    # 계정 정보
    subdomain = Column(String(100), unique=True)  # partner.dantarowallet.com
    custom_domain = Column(String(255))  # www.partnerwallet.com
    api_key = Column(String(64), unique=True, nullable=False)
    secret_key = Column(String(64), nullable=False)
    webhook_url = Column(String(500))
    webhook_secret = Column(String(64))
    
    # 서비스 설정
    tier = Column(Enum(PartnerTier), default=PartnerTier.STARTER)
    status = Column(Enum(PartnerStatus), default=PartnerStatus.PENDING)
    
    # 브랜딩
    branding_config = Column(JSON)  # 로고, 색상, 텍스트 등
    
    # 수수료 및 수익
    commission_rate = Column(Numeric(5, 2), default=30.00)  # 파트너 수수료율 (%)
    revenue_share_model = Column(String(20), default="percentage")  # percentage, fixed
    settlement_frequency = Column(String(20), default="monthly")  # daily, weekly, monthly
    minimum_settlement = Column(Numeric(20, 6), default=100.00)  # 최소 정산 금액
    
    # 한도 설정
    daily_withdrawal_limit = Column(Numeric(20, 6))
    monthly_withdrawal_limit = Column(Numeric(20, 6))
    per_transaction_limit = Column(Numeric(20, 6))
    
    # 기능 활성화
    features = Column(JSON, default=dict)  # 활성화된 기능 목록
    
    # 보안
    ip_whitelist = Column(JSON)  # 허용된 IP 목록
    allowed_origins = Column(JSON)  # CORS 허용 도메인
    
    # 메타데이터
    metadata = Column(JSON, default=dict)
    notes = Column(String(1000))
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activated_at = Column(DateTime)
    suspended_at = Column(DateTime)
    
    # 관계
    users = relationship("User", back_populates="partner")
    fee_configs = relationship("FeeConfiguration", back_populates="partner")
    settlements = relationship("PartnerSettlement", back_populates="partner")
    api_logs = relationship("PartnerAPILog", back_populates="partner")
    tickets = relationship("SupportTicket", back_populates="partner")

class PartnerBankAccount(Base):
    __tablename__ = "partner_bank_accounts"
    
    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey("partners.id"))
    
    # 은행 정보
    bank_name = Column(String(200), nullable=False)
    bank_code = Column(String(20))
    branch_name = Column(String(200))
    account_holder = Column(String(200), nullable=False)
    account_number = Column(String(100), nullable=False)
    swift_code = Column(String(20))
    
    # 상태
    is_primary = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime)
    
    partner = relationship("Partner")

class PartnerSettlement(Base):
    __tablename__ = "partner_settlements"
    
    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey("partners.id"))
    
    # 정산 정보
    settlement_period_start = Column(DateTime, nullable=False)
    settlement_period_end = Column(DateTime, nullable=False)
    
    # 금액
    total_revenue = Column(Numeric(20, 6), nullable=False)  # 총 수수료 수익
    partner_share = Column(Numeric(20, 6), nullable=False)  # 파트너 몫
    platform_share = Column(Numeric(20, 6), nullable=False)  # 플랫폼 몫
    
    # 거래 정보
    transaction_count = Column(Integer, default=0)
    user_count = Column(Integer, default=0)
    
    # 상태
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    processed_at = Column(DateTime)
    
    # 송금 정보
    bank_account_id = Column(Integer, ForeignKey("partner_bank_accounts.id"))
    transaction_reference = Column(String(100))
    
    partner = relationship("Partner", back_populates="settlements")
    bank_account = relationship("PartnerBankAccount")

class PartnerAPILog(Base):
    __tablename__ = "partner_api_logs"
    
    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey("partners.id"))
    
    # 요청 정보
    endpoint = Column(String(200))
    method = Column(String(10))
    request_headers = Column(JSON)
    request_body = Column(JSON)
    ip_address = Column(String(45))
    
    # 응답 정보
    status_code = Column(Integer)
    response_body = Column(JSON)
    response_time_ms = Column(Integer)
    
    # 에러 정보
    error_code = Column(String(50))
    error_message = Column(String(500))
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    partner = relationship("Partner", back_populates="api_logs")
```

### 2. 파트너 관리 서비스

#### 2.1 파트너 온보딩 서비스
```python
# app/services/partner/onboarding_service.py
from typing import Dict, Optional
import secrets
import hashlib
from datetime import datetime, timedelta

class PartnerOnboardingService:
    def __init__(self, db_session, email_service, subdomain_service):
        self.db = db_session
        self.email_service = email_service
        self.subdomain_service = subdomain_service
        
    async def create_partner(
        self,
        partner_data: CreatePartnerRequest,
        admin_id: int
    ) -> Partner:
        """새 파트너사 생성 및 온보딩"""
        # 1. 기본 정보 검증
        await self.validate_partner_data(partner_data)
        
        # 2. API 키 생성
        api_key = self.generate_api_key()
        secret_key = self.generate_secret_key()
        webhook_secret = secrets.token_urlsafe(32)
        
        # 3. 서브도메인 설정
        subdomain = await self.subdomain_service.reserve_subdomain(
            partner_data.preferred_subdomain or 
            self.generate_subdomain(partner_data.company_name)
        )
        
        # 4. 파트너 생성
        partner = Partner(
            company_name=partner_data.company_name,
            legal_name=partner_data.legal_name,
            business_registration=partner_data.business_registration,
            tax_id=partner_data.tax_id,
            primary_email=partner_data.primary_email,
            billing_email=partner_data.billing_email or partner_data.primary_email,
            support_email=partner_data.support_email or partner_data.primary_email,
            phone=partner_data.phone,
            address=partner_data.address.dict() if partner_data.address else None,
            subdomain=subdomain,
            api_key=api_key,
            secret_key=secret_key,
            webhook_url=partner_data.webhook_url,
            webhook_secret=webhook_secret,
            tier=partner_data.tier or PartnerTier.STARTER,
            commission_rate=self.get_tier_commission_rate(partner_data.tier),
            features=self.get_tier_features(partner_data.tier)
        )
        
        self.db.add(partner)
        await self.db.commit()
        
        # 5. 초기 설정
        await self.setup_partner_environment(partner)
        
        # 6. 환영 이메일 발송
        await self.send_welcome_email(partner)
        
        # 7. 온보딩 체크리스트 생성
        await self.create_onboarding_checklist(partner.id)
        
        return partner
        
    async def setup_partner_environment(self, partner: Partner):
        """파트너 환경 설정"""
        # 1. 기본 수수료 설정 생성
        await self.create_default_fee_configs(partner.id)
        
        # 2. 샌드박스 환경 설정
        await self.setup_sandbox_environment(partner)
        
        # 3. 샘플 데이터 생성 (옵션)
        if partner.tier in [PartnerTier.STARTER, PartnerTier.GROWTH]:
            await self.create_sample_data(partner.id)
            
        # 4. 모니터링 설정
        await self.setup_monitoring(partner)
        
    async def activate_partner(
        self,
        partner_id: int,
        admin_id: int
    ) -> Partner:
        """파트너 활성화"""
        partner = await self.db.get(Partner, partner_id)
        if not partner:
            raise ValueError("파트너를 찾을 수 없습니다")
            
        if partner.status != PartnerStatus.PENDING:
            raise ValueError("대기 중인 파트너만 활성화할 수 있습니다")
            
        # 필수 검증
        validation_result = await self.validate_activation_requirements(partner)
        if not validation_result['passed']:
            raise ValueError(f"활성화 요구사항 미충족: {validation_result['missing']}")
            
        # 상태 업데이트
        partner.status = PartnerStatus.ACTIVE
        partner.activated_at = datetime.utcnow()
        
        # 프로덕션 환경 활성화
        await self.activate_production_environment(partner)
        
        # 알림 발송
        await self.notify_partner_activation(partner)
        
        await self.db.commit()
        
        return partner
        
    def generate_api_key(self) -> str:
        """API 키 생성"""
        return f"pk_{'live' if settings.ENVIRONMENT == 'production' else 'test'}_{secrets.token_urlsafe(32)}"
        
    def generate_secret_key(self) -> str:
        """시크릿 키 생성"""
        return f"sk_{'live' if settings.ENVIRONMENT == 'production' else 'test'}_{secrets.token_urlsafe(32)}"
```

### 3. 파트너 API 인증 및 미들웨어

#### 3.1 파트너 인증 미들웨어
```python
# app/middleware/partner_auth.py
from fastapi import Request, HTTPException
from typing import Optional
import hmac
import hashlib
import time

class PartnerAuthMiddleware:
    def __init__(self, db_session):
        self.db = db_session
        
    async def __call__(self, request: Request, call_next):
        # 파트너 API 경로 확인
        if not request.url.path.startswith("/api/v1/partner"):
            return await call_next(request)
            
        # API 키 확인
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="API key required"
            )
            
        # 파트너 조회
        partner = await self.get_partner_by_api_key(api_key)
        if not partner:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
            
        # 파트너 상태 확인
        if partner.status != PartnerStatus.ACTIVE:
            raise HTTPException(
                status_code=403,
                detail=f"Partner account is {partner.status.value}"
            )
            
        # IP 화이트리스트 확인
        if partner.ip_whitelist:
            client_ip = request.client.host
            if client_ip not in partner.ip_whitelist:
                raise HTTPException(
                    status_code=403,
                    detail="IP address not whitelisted"
                )
                
        # 서명 검증 (POST 요청)
        if request.method in ["POST", "PUT", "PATCH"]:
            await self.verify_request_signature(request, partner)
            
        # 요청 속도 제한
        await self.check_rate_limit(partner.id)
        
        # 파트너 정보를 request state에 저장
        request.state.partner = partner
        
        # API 로그 기록
        start_time = time.time()
        response = await call_next(request)
        response_time = int((time.time() - start_time) * 1000)
        
        await self.log_api_request(
            partner=partner,
            request=request,
            response=response,
            response_time=response_time
        )
        
        return response
        
    async def verify_request_signature(
        self,
        request: Request,
        partner: Partner
    ):
        """요청 서명 검증"""
        signature = request.headers.get("X-Signature")
        if not signature:
            raise HTTPException(
                status_code=401,
                detail="Request signature required"
            )
            
        # 요청 본문 읽기
        body = await request.body()
        
        # 타임스탬프 확인
        timestamp = request.headers.get("X-Timestamp")
        if not timestamp:
            raise HTTPException(
                status_code=401,
                detail="Request timestamp required"
            )
            
        # 타임스탬프 유효성 (5분 이내)
        current_time = int(time.time())
        request_time = int(timestamp)
        if abs(current_time - request_time) > 300:
            raise HTTPException(
                status_code=401,
                detail="Request timestamp expired"
            )
            
        # 서명 생성
        message = f"{timestamp}.{body.decode('utf-8')}"
        expected_signature = hmac.new(
            partner.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # 서명 비교
        if not hmac.compare_digest(signature, expected_signature):
            raise HTTPException(
                status_code=401,
                detail="Invalid request signature"
            )
```

### 4. 파트너 전용 API 엔드포인트

#### 4.1 파트너 API 라우터
```python
# app/api/v1/partner/router.py
from fastapi import APIRouter, Depends, Request
from typing import List, Optional

router = APIRouter(prefix="/api/v1/partner")

def get_current_partner(request: Request) -> Partner:
    """현재 요청의 파트너 정보 반환"""
    if not hasattr(request.state, 'partner'):
        raise HTTPException(status_code=401, detail="Partner not authenticated")
    return request.state.partner

@router.post("/users", response_model=PartnerUserResponse)
async def create_partner_user(
    user_data: CreatePartnerUserRequest,
    partner: Partner = Depends(get_current_partner),
    user_service: UserService = Depends(get_user_service)
):
    """파트너사 사용자 생성"""
    # 파트너 한도 확인
    user_count = await user_service.get_partner_user_count(partner.id)
    
    tier_limits = {
        PartnerTier.STARTER: 1000,
        PartnerTier.GROWTH: 10000,
        PartnerTier.ENTERPRISE: None
    }
    
    limit = tier_limits.get(partner.tier)
    if limit and user_count >= limit:
        raise HTTPException(
            status_code=403,
            detail=f"User limit reached for {partner.tier.value} tier"
        )
        
    # 사용자 생성
    user = await user_service.create_user(
        email=user_data.email,
        external_id=user_data.external_id,
        partner_id=partner.id,
        metadata=user_data.metadata
    )
    
    # 웹훅 전송
    if partner.webhook_url:
        await send_partner_webhook(
            partner=partner,
            event="user.created",
            data={"user_id": user.id, "external_id": user.external_id}
        )
        
    return PartnerUserResponse.from_user(user)

@router.get("/users/{external_id}", response_model=PartnerUserResponse)
async def get_partner_user(
    external_id: str,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """파트너사 사용자 조회 (외부 ID 기준)"""
    user = await db.execute(
        select(User).where(
            User.partner_id == partner.id,
            User.external_id == external_id
        )
    )
    user = user.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return PartnerUserResponse.from_user(user)

@router.post("/users/{external_id}/wallets", response_model=WalletResponse)
async def create_user_wallet(
    external_id: str,
    partner: Partner = Depends(get_current_partner),
    wallet_service: WalletService = Depends(get_wallet_service)
):
    """사용자 지갑 생성"""
    user = await get_partner_user_by_external_id(partner.id, external_id)
    
    wallet = await wallet_service.create_wallet(user.id)
    
    # 웹훅 전송
    if partner.webhook_url:
        await send_partner_webhook(
            partner=partner,
            event="wallet.created",
            data={
                "user_id": user.id,
                "external_id": user.external_id,
                "wallet_address": wallet.address
            }
        )
        
    return WalletResponse.from_orm(wallet)

@router.get("/stats/overview", response_model=PartnerStatsResponse)
async def get_partner_statistics(
    time_range: str = Query("30d", regex="^(24h|7d|30d|90d)$"),
    partner: Partner = Depends(get_current_partner),
    stats_service: StatsService = Depends(get_stats_service)
):
    """파트너 통계 개요"""
    stats = await stats_service.get_partner_statistics(
        partner_id=partner.id,
        time_range=time_range
    )
    
    return PartnerStatsResponse(
        partner_id=partner.id,
        time_range=time_range,
        users={
            "total": stats['user_count'],
            "active": stats['active_users'],
            "new": stats['new_users']
        },
        transactions={
            "count": stats['transaction_count'],
            "volume": stats['transaction_volume'],
            "fees_collected": stats['fees_collected']
        },
        revenue={
            "total": stats['total_revenue'],
            "partner_share": stats['partner_revenue'],
            "pending_settlement": stats['pending_settlement']
        }
    )

@router.post("/webhooks/test", response_model=WebhookTestResponse)
async def test_webhook(
    test_data: WebhookTestRequest,
    partner: Partner = Depends(get_current_partner)
):
    """웹훅 테스트"""
    if not partner.webhook_url:
        raise HTTPException(
            status_code=400,
            detail="Webhook URL not configured"
        )
        
    result = await test_partner_webhook(
        partner=partner,
        test_event=test_data.event_type,
        test_data=test_data.sample_data
    )
    
    return WebhookTestResponse(
        success=result['success'],
        status_code=result.get('status_code'),
        response_time_ms=result.get('response_time'),
        error=result.get('error')
    )
```

### 5. 파트너 브랜딩 시스템

#### 5.1 브랜딩 구성 서비스
```python
# app/services/partner/branding_service.py
from typing import Dict, Optional
import json

class PartnerBrandingService:
    def __init__(self, db_session, storage_service):
        self.db = db_session
        self.storage = storage_service
        
    async def update_branding(
        self,
        partner_id: int,
        branding_config: BrandingConfigRequest
    ) -> Dict:
        """파트너 브랜딩 업데이트"""
        partner = await self.db.get(Partner, partner_id)
        if not partner:
            raise ValueError("파트너를 찾을 수 없습니다")
            
        # 로고 업로드 처리
        if branding_config.logo:
            logo_url = await self.upload_logo(
                partner_id,
                branding_config.logo
            )
            branding_config.logo_url = logo_url
            
        # 파비콘 업로드 처리
        if branding_config.favicon:
            favicon_url = await self.upload_favicon(
                partner_id,
                branding_config.favicon
            )
            branding_config.favicon_url = favicon_url
            
        # 브랜딩 구성 저장
        config_dict = {
            "colors": {
                "primary": branding_config.colors.primary,
                "secondary": branding_config.colors.secondary,
                "accent": branding_config.colors.accent,
                "error": branding_config.colors.error,
                "warning": branding_config.colors.warning,
                "success": branding_config.colors.success,
                "background": branding_config.colors.background,
                "text": branding_config.colors.text
            },
            "typography": {
                "font_family": branding_config.typography.font_family,
                "heading_font": branding_config.typography.heading_font,
                "font_size_base": branding_config.typography.font_size_base
            },
            "logos": {
                "primary": branding_config.logo_url,
                "white": branding_config.logo_white_url,
                "favicon": branding_config.favicon_url
            },
            "texts": {
                "company_name": branding_config.texts.company_name,
                "tagline": branding_config.texts.tagline,
                "support_email": branding_config.texts.support_email,
                "support_phone": branding_config.texts.support_phone,
                "footer_text": branding_config.texts.footer_text
            },
            "custom_css": branding_config.custom_css,
            "email_templates": branding_config.email_templates
        }
        
        partner.branding_config = config_dict
        await self.db.commit()
        
        # CSS 파일 생성
        await self.generate_custom_css(partner_id, config_dict)
        
        # 캐시 무효화
        await self.invalidate_branding_cache(partner_id)
        
        return config_dict
        
    async def generate_custom_css(
        self,
        partner_id: int,
        config: Dict
    ) -> str:
        """커스텀 CSS 생성"""
        colors = config.get('colors', {})
        typography = config.get('typography', {})
        
        css_template = f"""
        /* Partner {partner_id} Custom Styles */
        :root {{
            --primary-color: {colors.get('primary', '#1890ff')};
            --secondary-color: {colors.get('secondary', '#52c41a')};
            --accent-color: {colors.get('accent', '#fa8c16')};
            --error-color: {colors.get('error', '#ff4d4f')};
            --warning-color: {colors.get('warning', '#faad14')};
            --success-color: {colors.get('success', '#52c41a')};
            --background-color: {colors.get('background', '#ffffff')};
            --text-color: {colors.get('text', '#262626')};
            
            --font-family: {typography.get('font_family', 'Inter, system-ui, sans-serif')};
            --heading-font: {typography.get('heading_font', 'var(--font-family)')};
            --font-size-base: {typography.get('font_size_base', '16px')};
        }}
        
        body {{
            font-family: var(--font-family);
            font-size: var(--font-size-base);
            color: var(--text-color);
            background-color: var(--background-color);
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            font-family: var(--heading-font);
        }}
        
        .btn-primary {{
            background-color: var(--primary-color);
            border-color: var(--primary-color);
        }}
        
        .btn-primary:hover {{
            background-color: color-mix(in srgb, var(--primary-color) 85%, black);
            border-color: color-mix(in srgb, var(--primary-color) 85%, black);
        }}
        
        {config.get('custom_css', '')}
        """
        
        # CSS 파일 저장
        css_path = f"partner_{partner_id}_custom.css"
        await self.storage.save_file(css_path, css_template)
        
        return css_path
```

### 6. 파트너 정산 시스템

#### 6.1 정산 처리 서비스
```python
# app/services/partner/settlement_service.py
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

class PartnerSettlementService:
    def __init__(self, db_session, payment_service, notification_service):
        self.db = db_session
        self.payment_service = payment_service
        self.notification_service = notification_service
        
    async def process_settlements(
        self,
        settlement_date: Optional[datetime] = None
    ) -> List[PartnerSettlement]:
        """파트너 정산 처리"""
        if not settlement_date:
            settlement_date = datetime.utcnow()
            
        # 정산 대상 파트너 조회
        partners = await self.get_partners_for_settlement(settlement_date)
        
        settlements = []
        
        for partner in partners:
            try:
                settlement = await self.create_partner_settlement(
                    partner=partner,
                    settlement_date=settlement_date
                )
                
                if settlement.partner_share >= partner.minimum_settlement:
                    await self.execute_settlement_payment(settlement)
                    settlements.append(settlement)
                else:
                    # 최소 금액 미달 - 다음 정산으로 이월
                    await self.carry_forward_settlement(settlement)
                    
            except Exception as e:
                logger.error(f"파트너 {partner.id} 정산 실패: {str(e)}")
                await self.handle_settlement_error(partner, e)
                
        return settlements
        
    async def create_partner_settlement(
        self,
        partner: Partner,
        settlement_date: datetime
    ) -> PartnerSettlement:
        """파트너 정산 생성"""
        # 정산 기간 계산
        if partner.settlement_frequency == "daily":
            period_start = settlement_date.replace(hour=0, minute=0, second=0) - timedelta(days=1)
            period_end = period_start + timedelta(days=1) - timedelta(seconds=1)
        elif partner.settlement_frequency == "weekly":
            period_start = settlement_date - timedelta(days=7)
            period_end = settlement_date
        else:  # monthly
            period_start = (settlement_date.replace(day=1) - timedelta(days=1)).replace(day=1)
            period_end = settlement_date.replace(day=1) - timedelta(seconds=1)
            
        # 기간 내 수수료 수익 계산
        revenue_data = await self.calculate_period_revenue(
            partner_id=partner.id,
            start_date=period_start,
            end_date=period_end
        )
        
        # 이전 이월금 확인
        carried_forward = await self.get_carried_forward_amount(partner.id)
        
        # 정산 금액 계산
        total_revenue = revenue_data['total_fees'] + carried_forward
        
        if partner.revenue_share_model == "percentage":
            partner_share = total_revenue * (partner.commission_rate / 100)
            platform_share = total_revenue - partner_share
        else:
            # 고정 수수료 모델
            partner_share = total_revenue
            platform_share = Decimal('0')
            
        # 정산 레코드 생성
        settlement = PartnerSettlement(
            partner_id=partner.id,
            settlement_period_start=period_start,
            settlement_period_end=period_end,
            total_revenue=total_revenue,
            partner_share=partner_share,
            platform_share=platform_share,
            transaction_count=revenue_data['transaction_count'],
            user_count=revenue_data['unique_users'],
            status="pending"
        )
        
        self.db.add(settlement)
        await self.db.commit()
        
        return settlement
        
    async def execute_settlement_payment(
        self,
        settlement: PartnerSettlement
    ):
        """정산 송금 실행"""
        partner = settlement.partner
        
        # 은행 계좌 확인
        bank_account = await self.get_primary_bank_account(partner.id)
        if not bank_account or not bank_account.is_verified:
            raise ValueError("검증된 은행 계좌가 없습니다")
            
        settlement.bank_account_id = bank_account.id
        settlement.status = "processing"
        await self.db.commit()
        
        try:
            # 송금 처리
            transfer_result = await self.payment_service.create_bank_transfer(
                amount=settlement.partner_share,
                currency="USD",
                recipient={
                    "bank_name": bank_account.bank_name,
                    "account_number": bank_account.account_number,
                    "account_holder": bank_account.account_holder,
                    "swift_code": bank_account.swift_code
                },
                reference=f"SETTLEMENT-{settlement.id}"
            )
            
            # 정산 완료 처리
            settlement.status = "completed"
            settlement.processed_at = datetime.utcnow()
            settlement.transaction_reference = transfer_result['transaction_id']
            
            # 알림 발송
            await self.notification_service.send_settlement_notification(
                partner=partner,
                settlement=settlement
            )
            
        except Exception as e:
            settlement.status = "failed"
            settlement.error_message = str(e)
            raise
            
        finally:
            await self.db.commit()
```

### 7. 파트너 모니터링 및 분석

#### 7.1 파트너 활동 모니터링
```python
# app/services/partner/monitoring_service.py
from typing import Dict, List
import asyncio
from datetime import datetime, timedelta

class PartnerMonitoringService:
    def __init__(self, db_session, alert_service):
        self.db = db_session
        self.alert_service = alert_service
        
    async def monitor_partner_health(self):
        """파트너 상태 모니터링"""
        while True:
            try:
                partners = await self.get_active_partners()
                
                for partner in partners:
                    health_check = await self.check_partner_health(partner)
                    
                    if health_check['issues']:
                        await self.handle_health_issues(partner, health_check['issues'])
                        
                await asyncio.sleep(300)  # 5분마다
                
            except Exception as e:
                logger.error(f"파트너 모니터링 오류: {str(e)}")
                await asyncio.sleep(600)
                
    async def check_partner_health(self, partner: Partner) -> Dict:
        """파트너 상태 체크"""
        issues = []
        metrics = {}
        
        # 1. API 사용량 체크
        api_usage = await self.get_api_usage_stats(partner.id, hours=24)
        metrics['api_usage'] = api_usage
        
        if api_usage['error_rate'] > 10:  # 10% 이상 에러율
            issues.append({
                'type': 'high_error_rate',
                'severity': 'warning',
                'value': api_usage['error_rate'],
                'message': f"API 에러율이 {api_usage['error_rate']}%로 높습니다"
            })
            
        # 2. 거래 이상 감지
        transaction_anomalies = await self.detect_transaction_anomalies(partner.id)
        if transaction_anomalies:
            issues.extend(transaction_anomalies)
            
        # 3. 보안 체크
        security_issues = await self.check_security_status(partner)
        if security_issues:
            issues.extend(security_issues)
            
        # 4. 정산 상태 체크
        settlement_status = await self.check_settlement_status(partner.id)
        metrics['settlement'] = settlement_status
        
        if settlement_status['overdue_count'] > 0:
            issues.append({
                'type': 'overdue_settlement',
                'severity': 'critical',
                'value': settlement_status['overdue_count'],
                'message': f"{settlement_status['overdue_count']}건의 정산이 지연되고 있습니다"
            })
            
        return {
            'partner_id': partner.id,
            'checked_at': datetime.utcnow(),
            'metrics': metrics,
            'issues': issues,
            'health_score': self.calculate_health_score(metrics, issues)
        }
        
    async def generate_partner_report(
        self,
        partner_id: int,
        report_type: str = "monthly"
    ) -> Dict:
        """파트너 리포트 생성"""
        partner = await self.db.get(Partner, partner_id)
        
        if report_type == "monthly":
            start_date = datetime.utcnow().replace(day=1) - timedelta(days=1)
            start_date = start_date.replace(day=1)
            end_date = datetime.utcnow()
        else:
            # 주간, 일간 등 다른 기간 처리
            pass
            
        # 리포트 데이터 수집
        report_data = {
            'partner': {
                'id': partner.id,
                'name': partner.company_name,
                'tier': partner.tier.value
            },
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'type': report_type
            },
            'summary': await self.get_period_summary(partner_id, start_date, end_date),
            'users': await self.get_user_analytics(partner_id, start_date, end_date),
            'transactions': await self.get_transaction_analytics(partner_id, start_date, end_date),
            'revenue': await self.get_revenue_analytics(partner_id, start_date, end_date),
            'api_usage': await self.get_api_usage_analytics(partner_id, start_date, end_date),
            'issues': await self.get_period_issues(partner_id, start_date, end_date)
        }
        
        # PDF 리포트 생성
        pdf_path = await self.generate_pdf_report(report_data)
        
        # 리포트 저장
        await self.save_report_record(partner_id, report_type, report_data, pdf_path)
        
        return {
            'report_data': report_data,
            'pdf_url': pdf_path,
            'generated_at': datetime.utcnow()
        }
```

### 8. 파트너 관리자 API

#### 8.1 슈퍼 어드민 파트너 관리 API
```python
# app/api/v1/endpoints/admin/partners.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

router = APIRouter()

@router.get("/admin/partners", response_model=List[PartnerListResponse])
async def list_partners(
    status: Optional[PartnerStatus] = None,
    tier: Optional[PartnerTier] = None,
    search: Optional[str] = None,
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """파트너사 목록 조회"""
    if not current_admin.can_manage_partners:
        raise HTTPException(status_code=403, detail="권한이 없습니다")
        
    query = select(Partner)
    
    if status:
        query = query.where(Partner.status == status)
    if tier:
        query = query.where(Partner.tier == tier)
    if search:
        query = query.where(
            or_(
                Partner.company_name.ilike(f"%{search}%"),
                Partner.primary_email.ilike(f"%{search}%"),
                Partner.subdomain.ilike(f"%{search}%")
            )
        )
        
    query = query.order_by(Partner.created_at.desc())
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    partners = result.scalars().all()
    
    return [PartnerListResponse.from_orm(p) for p in partners]

@router.post("/admin/partners", response_model=PartnerDetailResponse)
async def create_partner(
    partner_data: CreatePartnerRequest,
    current_admin: Admin = Depends(get_current_admin),
    onboarding_service: PartnerOnboardingService = Depends(get_onboarding_service)
):
    """새 파트너사 생성"""
    if not current_admin.is_super_admin:
        raise HTTPException(status_code=403, detail="슈퍼 관리자만 가능합니다")
        
    try:
        partner = await onboarding_service.create_partner(
            partner_data=partner_data,
            admin_id=current_admin.id
        )
        
        return PartnerDetailResponse.from_orm(partner)
        
    except Exception as e:
        logger.error(f"파트너 생성 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/admin/partners/{partner_id}", response_model=PartnerDetailResponse)
async def get_partner_detail(
    partner_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """파트너사 상세 정보"""
    if not current_admin.can_manage_partners:
        raise HTTPException(status_code=403, detail="권한이 없습니다")
        
    partner = await db.get(Partner, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="파트너를 찾을 수 없습니다")
        
    return PartnerDetailResponse.from_orm(partner)

@router.put("/admin/partners/{partner_id}", response_model=PartnerDetailResponse)
async def update_partner(
    partner_id: int,
    update_data: UpdatePartnerRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """파트너사 정보 수정"""
    if not current_admin.can_manage_partners:
        raise HTTPException(status_code=403, detail="권한이 없습니다")
        
    partner = await db.get(Partner, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="파트너를 찾을 수 없습니다")
        
    # 업데이트
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(partner, field, value)
        
    partner.updated_at = datetime.utcnow()
    await db.commit()
    
    return PartnerDetailResponse.from_orm(partner)

@router.post("/admin/partners/{partner_id}/activate")
async def activate_partner(
    partner_id: int,
    current_admin: Admin = Depends(get_current_admin),
    onboarding_service: PartnerOnboardingService = Depends(get_onboarding_service)
):
    """파트너 활성화"""
    if not current_admin.is_super_admin:
        raise HTTPException(status_code=403, detail="슈퍼 관리자만 가능합니다")
        
    try:
        partner = await onboarding_service.activate_partner(
            partner_id=partner_id,
            admin_id=current_admin.id
        )
        
        return {"message": "파트너가 활성화되었습니다", "partner_id": partner.id}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/admin/partners/{partner_id}/suspend")
async def suspend_partner(
    partner_id: int,
    reason: SuspendReasonRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """파트너 일시 정지"""
    if not current_admin.is_super_admin:
        raise HTTPException(status_code=403, detail="슈퍼 관리자만 가능합니다")
        
    partner = await db.get(Partner, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="파트너를 찾을 수 없습니다")
        
    partner.status = PartnerStatus.SUSPENDED
    partner.suspended_at = datetime.utcnow()
    partner.notes = f"Suspended: {reason.reason}"
    
    await db.commit()
    
    # 파트너에게 알림
    await send_partner_suspension_notification(partner, reason.reason)
    
    return {"message": "파트너가 일시 정지되었습니다"}

@router.get("/admin/partners/{partner_id}/stats", response_model=PartnerStatsDetailResponse)
async def get_partner_statistics(
    partner_id: int,
    time_range: str = Query("30d"),
    current_admin: Admin = Depends(get_current_admin),
    stats_service: StatsService = Depends(get_stats_service)
):
    """파트너사 통계"""
    if not current_admin.can_view_analytics:
        raise HTTPException(status_code=403, detail="권한이 없습니다")
        
    stats = await stats_service.get_partner_statistics_detailed(
        partner_id=partner_id,
        time_range=time_range
    )
    
    return PartnerStatsDetailResponse(**stats)

@router.get("/admin/partners/{partner_id}/settlements", response_model=List[SettlementResponse])
async def get_partner_settlements(
    partner_id: int,
    status: Optional[str] = None,
    limit: int = Query(20, le=100),
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """파트너 정산 내역"""
    if not current_admin.can_manage_settlements:
        raise HTTPException(status_code=403, detail="권한이 없습니다")
        
    query = select(PartnerSettlement).where(
        PartnerSettlement.partner_id == partner_id
    )
    
    if status:
        query = query.where(PartnerSettlement.status == status)
        
    query = query.order_by(PartnerSettlement.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    settlements = result.scalars().all()
    
    return [SettlementResponse.from_orm(s) for s in settlements]

@router.post("/admin/partners/{partner_id}/manual-settlement")
async def create_manual_settlement(
    partner_id: int,
    settlement_data: ManualSettlementRequest,
    current_admin: Admin = Depends(get_current_admin),
    settlement_service: PartnerSettlementService = Depends(get_settlement_service)
):
    """수동 정산 생성"""
    if not current_admin.is_super_admin:
        raise HTTPException(status_code=403, detail="슈퍼 관리자만 가능합니다")
        
    settlement = await settlement_service.create_manual_settlement(
        partner_id=partner_id,
        amount=settlement_data.amount,
        reason=settlement_data.reason,
        admin_id=current_admin.id
    )
    
    return {"message": "수동 정산이 생성되었습니다", "settlement_id": settlement.id}
```

## 검증 포인트

- [ ] 파트너 생성 및 온보딩이 정상 작동하는가?
- [ ] API 인증 및 서명 검증이 작동하는가?
- [ ] 파트너별 사용자 격리가 되는가?
- [ ] 브랜딩 커스터마이징이 적용되는가?
- [ ] 정산 시스템이 정확히 계산하는가?
- [ ] 파트너 상태 모니터링이 작동하는가?
- [ ] 웹훅이 정상 전송되는가?
- [ ] 파트너 통계가 정확히 집계되는가?

이 시스템을 통해 완전한 B2B SaaS 화이트라벨 플랫폼으로 운영할 수 있으며, 각 파트너사는 독립적인 서비스처럼 운영할 수 있습니다.