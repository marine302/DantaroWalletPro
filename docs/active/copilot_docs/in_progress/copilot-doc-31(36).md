# Copilot 문서 #36: 트론 에너지 렌탈 서비스 구현

## 목표
본사가 파트너사에게 TRON 에너지를 렌탈하는 서비스를 구축합니다. 파트너사는 초기 TRX 스테이킹 없이도 사용한 만큼만 에너지 비용을 지불하며, 본사는 규모의 경제를 통해 안정적인 수익을 창출합니다.

## 전제 조건
- Copilot 문서 #1-35가 완료되어 있어야 합니다
- 파트너사 관리 시스템이 구축되어 있어야 합니다
- 에너지 풀 관리 시스템이 구현되어 있어야 합니다
- TRON 네트워크 연동이 완료되어 있어야 합니다

## 🎯 에너지 렌탈 서비스 구조

### 📊 비즈니스 모델
```
에너지 렌탈 서비스
├── 💰 가격 정책
│   ├── 종량제 (사용량 기반)
│   ├── 구독제 (월정액)
│   ├── 하이브리드 (기본+추가)
│   └── 대량 할인 정책
├── 🔋 에너지 관리
│   ├── 본사 에너지 풀
│   ├── 파트너별 할당량
│   ├── 실시간 사용량 추적
│   └── 자동 재충전 시스템
├── 💳 과금 시스템
│   ├── 실시간 차감
│   ├── 일괄 정산
│   ├── 선불/후불 옵션
│   └── 자동 결제
├── 📊 모니터링
│   ├── 사용량 대시보드
│   ├── 비용 분석
│   ├── 예측 모델
│   └── 알림 시스템
└── 🛡️ 리스크 관리
    ├── 에너지 부족 대응
    ├── 가격 변동 헤징
    ├── 미수금 관리
    └── SLA 보장
```

## 🛠️ 구현 단계

### Phase 1: 에너지 렌탈 모델 설계 (2일)

#### 1.1 데이터베이스 모델
```python
# app/models/energy_rental.py
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from decimal import Decimal
import enum

class RentalPlanType(enum.Enum):
    """렌탈 플랜 유형"""
    PAY_AS_YOU_GO = "pay_as_you_go"  # 종량제
    SUBSCRIPTION = "subscription"      # 구독제
    HYBRID = "hybrid"                 # 하이브리드

class SubscriptionTier(enum.Enum):
    """구독 등급"""
    BRONZE = "bronze"    # 월 50만 에너지
    SILVER = "silver"    # 월 500만 에너지
    GOLD = "gold"       # 월 5000만 에너지
    ENTERPRISE = "enterprise"  # 무제한

class EnergyRentalPlan(Base):
    """에너지 렌탈 플랜"""
    __tablename__ = "energy_rental_plans"
    
    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    plan_type = Column(Enum(RentalPlanType), nullable=False)
    subscription_tier = Column(Enum(SubscriptionTier))
    
    # 가격 설정
    price_per_energy = Column(Numeric(20, 10), default=Decimal("0.00008"))  # TRX per 에너지
    monthly_fee = Column(Numeric(20, 6))  # 월 구독료
    
    # 할당량 및 사용량
    monthly_energy_quota = Column(Integer, default=0)
    monthly_energy_used = Column(Integer, default=0)
    daily_limit = Column(Integer)
    
    # 할인 및 프로모션
    discount_rate = Column(Numeric(5, 4), default=Decimal("0"))
    promotional_end_date = Column(DateTime)
    
    # 결제 설정
    payment_method = Column(String(50))  # "prepaid", "postpaid"
    auto_recharge_enabled = Column(Boolean, default=False)
    auto_recharge_threshold = Column(Integer)  # 잔여 에너지 임계값
    
    # 상태
    is_active = Column(Boolean, default=True)
    activated_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    partner = relationship("Partner", back_populates="energy_rental_plan")
    usage_records = relationship("EnergyUsageRecord", back_populates="rental_plan")
    settlements = relationship("EnergySettlement", back_populates="rental_plan")

class EnergyUsageRecord(Base):
    """에너지 사용 기록"""
    __tablename__ = "energy_usage_records"
    
    id = Column(Integer, primary_key=True)
    rental_plan_id = Column(Integer, ForeignKey("energy_rental_plans.id"))
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    
    energy_used = Column(Integer, nullable=False)
    price_per_energy = Column(Numeric(20, 10), nullable=False)
    total_cost = Column(Numeric(20, 6), nullable=False)
    
    # 비용 처리
    payment_status = Column(String(20), default="pending")  # pending, charged, failed
    payment_method = Column(String(20))  # "trx", "usdt"
    charged_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    rental_plan = relationship("EnergyRentalPlan", back_populates="usage_records")
    transaction = relationship("Transaction")

class EnergySettlement(Base):
    """에너지 정산"""
    __tablename__ = "energy_settlements"
    
    id = Column(Integer, primary_key=True)
    rental_plan_id = Column(Integer, ForeignKey("energy_rental_plans.id"))
    
    settlement_type = Column(String(20))  # "daily", "weekly", "monthly"
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # 사용량 및 비용
    total_energy_used = Column(Integer, nullable=False)
    base_cost = Column(Numeric(20, 6), nullable=False)
    discount_amount = Column(Numeric(20, 6), default=Decimal("0"))
    final_cost = Column(Numeric(20, 6), nullable=False)
    
    # 결제 정보
    payment_status = Column(String(20), default="pending")
    payment_method = Column(String(20))
    payment_tx_hash = Column(String(64))
    paid_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    rental_plan = relationship("EnergyRentalPlan", back_populates="settlements")

class EnergyPricing(Base):
    """에너지 가격 정책"""
    __tablename__ = "energy_pricing"
    
    id = Column(Integer, primary_key=True)
    tier_name = Column(String(50), unique=True)
    min_volume = Column(Integer, nullable=False)  # 최소 사용량
    max_volume = Column(Integer)  # 최대 사용량 (NULL = 무제한)
    price_per_energy = Column(Numeric(20, 10), nullable=False)
    
    # 시간대별 가격
    peak_hour_multiplier = Column(Numeric(3, 2), default=Decimal("1.0"))
    off_peak_discount = Column(Numeric(3, 2), default=Decimal("0"))
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Phase 2: 에너지 렌탈 서비스 구현 (2일)

#### 2.1 에너지 렌탈 서비스
```python
# app/services/energy_rental_service.py
from typing import Optional, List, Dict
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.energy_rental import (
    EnergyRentalPlan, EnergyUsageRecord, 
    EnergySettlement, RentalPlanType, SubscriptionTier
)
from app.core.exceptions import InsufficientEnergyError, PaymentError

class EnergyRentalService:
    def __init__(self, db: Session):
        self.db = db
        
    # 플랜 관리
    async def create_rental_plan(
        self, 
        partner_id: int, 
        plan_type: RentalPlanType,
        subscription_tier: Optional[SubscriptionTier] = None
    ) -> EnergyRentalPlan:
        """렌탈 플랜 생성"""
        # 기존 플랜 확인
        existing = self.db.query(EnergyRentalPlan).filter(
            EnergyRentalPlan.partner_id == partner_id,
            EnergyRentalPlan.is_active == True
        ).first()
        
        if existing:
            existing.is_active = False
            
        # 가격 및 할당량 설정
        pricing = self._get_pricing_for_tier(subscription_tier)
        
        plan = EnergyRentalPlan(
            partner_id=partner_id,
            plan_type=plan_type,
            subscription_tier=subscription_tier,
            price_per_energy=pricing["price_per_energy"],
            monthly_fee=pricing.get("monthly_fee", 0),
            monthly_energy_quota=pricing.get("quota", 0),
            activated_at=datetime.utcnow()
        )
        
        if plan_type == RentalPlanType.SUBSCRIPTION:
            plan.expires_at = datetime.utcnow() + timedelta(days=30)
            
        self.db.add(plan)
        self.db.commit()
        return plan
        
    def _get_pricing_for_tier(self, tier: Optional[SubscriptionTier]) -> Dict:
        """등급별 가격 정보"""
        pricing_map = {
            SubscriptionTier.BRONZE: {
                "price_per_energy": Decimal("0.00010"),
                "monthly_fee": Decimal("40"),
                "quota": 500000
            },
            SubscriptionTier.SILVER: {
                "price_per_energy": Decimal("0.00008"),
                "monthly_fee": Decimal("300"),
                "quota": 5000000
            },
            SubscriptionTier.GOLD: {
                "price_per_energy": Decimal("0.00006"),
                "monthly_fee": Decimal("2000"),
                "quota": 50000000
            },
            SubscriptionTier.ENTERPRISE: {
                "price_per_energy": Decimal("0.00005"),
                "monthly_fee": Decimal("10000"),
                "quota": None  # 무제한
            }
        }
        
        if tier and tier in pricing_map:
            return pricing_map[tier]
        
        # 종량제 기본 가격
        return {"price_per_energy": Decimal("0.00010")}
        
    # 에너지 사용 처리
    async def use_energy(
        self, 
        partner_id: int, 
        energy_amount: int,
        transaction_id: Optional[int] = None
    ) -> EnergyUsageRecord:
        """에너지 사용 처리"""
        # 활성 플랜 조회
        plan = self.db.query(EnergyRentalPlan).filter(
            EnergyRentalPlan.partner_id == partner_id,
            EnergyRentalPlan.is_active == True
        ).first()
        
        if not plan:
            raise ValueError("활성 렌탈 플랜이 없습니다")
            
        # 사용 가능 여부 확인
        can_use, reason = await self._check_energy_availability(plan, energy_amount)
        if not can_use:
            raise InsufficientEnergyError(reason)
            
        # 비용 계산
        cost = await self._calculate_energy_cost(plan, energy_amount)
        
        # 사용 기록 생성
        usage = EnergyUsageRecord(
            rental_plan_id=plan.id,
            transaction_id=transaction_id,
            energy_used=energy_amount,
            price_per_energy=plan.price_per_energy,
            total_cost=cost
        )
        
        # 즉시 차감 처리 (선불제)
        if plan.payment_method == "prepaid":
            charged = await self._charge_energy_cost(partner_id, cost)
            if charged:
                usage.payment_status = "charged"
                usage.charged_at = datetime.utcnow()
            else:
                raise PaymentError("에너지 비용 차감 실패")
                
        # 플랜 사용량 업데이트
        plan.monthly_energy_used += energy_amount
        
        self.db.add(usage)
        self.db.commit()
        return usage
        
    async def _check_energy_availability(
        self, 
        plan: EnergyRentalPlan, 
        energy_amount: int
    ) -> tuple[bool, Optional[str]]:
        """에너지 사용 가능 여부 확인"""
        # 플랜 만료 확인
        if plan.expires_at and plan.expires_at < datetime.utcnow():
            return False, "렌탈 플랜이 만료되었습니다"
            
        # 일일 한도 확인
        if plan.daily_limit:
            today_usage = self._get_today_usage(plan.id)
            if today_usage + energy_amount > plan.daily_limit:
                return False, "일일 사용 한도 초과"
                
        # 구독 플랜 할당량 확인
        if plan.plan_type == RentalPlanType.SUBSCRIPTION:
            if plan.monthly_energy_quota and \
               plan.monthly_energy_used + energy_amount > plan.monthly_energy_quota:
                return False, "월 할당량 초과"
                
        # 본사 에너지 풀 확인
        available_energy = await self._get_headquarters_energy()
        if available_energy < energy_amount:
            return False, "본사 에너지 풀 부족"
            
        return True, None
        
    async def _calculate_energy_cost(
        self, 
        plan: EnergyRentalPlan, 
        energy_amount: int
    ) -> Decimal:
        """에너지 비용 계산"""
        # 구독 플랜은 할당량 내 무료
        if plan.plan_type == RentalPlanType.SUBSCRIPTION:
            remaining_quota = plan.monthly_energy_quota - plan.monthly_energy_used
            if energy_amount <= remaining_quota:
                return Decimal("0")
            # 초과분만 과금
            billable_amount = energy_amount - remaining_quota
        else:
            billable_amount = energy_amount
            
        # 볼륨 할인 적용
        price_per_energy = await self._get_volume_price(
            plan.partner_id, 
            billable_amount
        )
        
        # 프로모션 할인 적용
        if plan.discount_rate > 0 and \
           (not plan.promotional_end_date or plan.promotional_end_date > datetime.utcnow()):
            price_per_energy *= (1 - plan.discount_rate)
            
        return Decimal(billable_amount) * price_per_energy
        
    async def _get_volume_price(self, partner_id: int, amount: int) -> Decimal:
        """볼륨별 단가 조회"""
        # 월간 총 사용량 기준
        monthly_total = self._get_monthly_usage(partner_id)
        total_volume = monthly_total + amount
        
        # 가격 테이블에서 적용 가격 조회
        pricing = self.db.query(EnergyPricing).filter(
            EnergyPricing.is_active == True,
            EnergyPricing.min_volume <= total_volume
        ).order_by(EnergyPricing.min_volume.desc()).first()
        
        if pricing:
            # 시간대별 가격 조정
            current_hour = datetime.utcnow().hour
            if 18 <= current_hour <= 22:  # 피크 시간
                return pricing.price_per_energy * pricing.peak_hour_multiplier
            elif 0 <= current_hour <= 6:  # 오프피크
                return pricing.price_per_energy * (1 - pricing.off_peak_discount)
            return pricing.price_per_energy
            
        return Decimal("0.00010")  # 기본가
        
    # 정산 처리
    async def process_settlement(
        self, 
        partner_id: int, 
        settlement_type: str = "daily"
    ) -> EnergySettlement:
        """에너지 사용 정산"""
        plan = self.db.query(EnergyRentalPlan).filter(
            EnergyRentalPlan.partner_id == partner_id,
            EnergyRentalPlan.is_active == True
        ).first()
        
        if not plan:
            return None
            
        # 정산 기간 설정
        period_end = datetime.utcnow()
        if settlement_type == "daily":
            period_start = period_end - timedelta(days=1)
        elif settlement_type == "weekly":
            period_start = period_end - timedelta(days=7)
        else:  # monthly
            period_start = period_end - timedelta(days=30)
            
        # 기간 내 사용량 집계
        usage_records = self.db.query(EnergyUsageRecord).filter(
            EnergyUsageRecord.rental_plan_id == plan.id,
            EnergyUsageRecord.created_at >= period_start,
            EnergyUsageRecord.created_at < period_end,
            EnergyUsageRecord.payment_status == "pending"
        ).all()
        
        if not usage_records:
            return None
            
        total_energy = sum(u.energy_used for u in usage_records)
        base_cost = sum(u.total_cost for u in usage_records)
        
        # 추가 할인 적용 (충성도, 선불 등)
        discount = await self._calculate_settlement_discount(
            partner_id, 
            base_cost
        )
        
        final_cost = base_cost - discount
        
        # 정산 기록 생성
        settlement = EnergySettlement(
            rental_plan_id=plan.id,
            settlement_type=settlement_type,
            period_start=period_start,
            period_end=period_end,
            total_energy_used=total_energy,
            base_cost=base_cost,
            discount_amount=discount,
            final_cost=final_cost
        )
        
        # 자동 결제 처리
        if plan.payment_method == "postpaid":
            payment_result = await self._process_settlement_payment(
                partner_id, 
                final_cost
            )
            if payment_result["success"]:
                settlement.payment_status = "paid"
                settlement.payment_method = payment_result["method"]
                settlement.payment_tx_hash = payment_result["tx_hash"]
                settlement.paid_at = datetime.utcnow()
                
                # 사용 기록 업데이트
                for usage in usage_records:
                    usage.payment_status = "charged"
                    usage.charged_at = datetime.utcnow()
                    
        self.db.add(settlement)
        self.db.commit()
        return settlement
        
    # 모니터링 및 알림
    async def check_energy_alerts(self, partner_id: int) -> List[Dict]:
        """에너지 관련 알림 확인"""
        alerts = []
        plan = self.db.query(EnergyRentalPlan).filter(
            EnergyRentalPlan.partner_id == partner_id,
            EnergyRentalPlan.is_active == True
        ).first()
        
        if not plan:
            return alerts
            
        # 구독 만료 임박
        if plan.expires_at:
            days_until_expiry = (plan.expires_at - datetime.utcnow()).days
            if days_until_expiry <= 3:
                alerts.append({
                    "type": "subscription_expiry",
                    "severity": "warning",
                    "message": f"구독이 {days_until_expiry}일 후 만료됩니다",
                    "action": "renew_subscription"
                })
                
        # 할당량 소진 임박
        if plan.monthly_energy_quota:
            usage_percent = (plan.monthly_energy_used / plan.monthly_energy_quota) * 100
            if usage_percent >= 90:
                alerts.append({
                    "type": "quota_warning",
                    "severity": "warning",
                    "message": f"월 할당량의 {usage_percent:.1f}%를 사용했습니다",
                    "action": "upgrade_plan"
                })
                
        # 미결제 정산
        unpaid_settlements = self.db.query(EnergySettlement).filter(
            EnergySettlement.rental_plan_id == plan.id,
            EnergySettlement.payment_status == "pending"
        ).count()
        
        if unpaid_settlements > 0:
            alerts.append({
                "type": "unpaid_settlement",
                "severity": "critical",
                "message": f"{unpaid_settlements}건의 미결제 정산이 있습니다",
                "action": "pay_settlement"
            })
            
        return alerts
```

### Phase 3: API 엔드포인트 구현 (1일)

#### 3.1 파트너용 에너지 렌탈 API
```python
# app/api/v1/endpoints/partner/energy_rental.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from app.api import deps
from app.schemas.energy_rental import (
    RentalPlanCreate, RentalPlanResponse,
    EnergyUsageRequest, EnergyUsageResponse,
    SettlementResponse, PricingResponse
)
from app.services.energy_rental_service import EnergyRentalService

router = APIRouter()

@router.post("/rental-plans", response_model=RentalPlanResponse)
async def create_rental_plan(
    plan_data: RentalPlanCreate,
    partner_id: int = Depends(deps.get_current_partner_id),
    db: Session = Depends(deps.get_db)
):
    """에너지 렌탈 플랜 생성/변경"""
    service = EnergyRentalService(db)
    plan = await service.create_rental_plan(
        partner_id=partner_id,
        plan_type=plan_data.plan_type,
        subscription_tier=plan_data.subscription_tier
    )
    return plan

@router.get("/rental-plans/current", response_model=RentalPlanResponse)
async def get_current_plan(
    partner_id: int = Depends(deps.get_current_partner_id),
    db: Session = Depends(deps.get_db)
):
    """현재 활성 렌탈 플랜 조회"""
    plan = db.query(EnergyRentalPlan).filter(
        EnergyRentalPlan.partner_id == partner_id,
        EnergyRentalPlan.is_active == True
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="활성 플랜이 없습니다")
    
    return plan

@router.get("/pricing", response_model=PricingResponse)
async def get_energy_pricing(
    volume: Optional[int] = None,
    db: Session = Depends(deps.get_db)
):
    """에너지 가격 정보 조회"""
    # 가격 테이블 조회
    pricing_tiers = db.query(EnergyPricing).filter(
        EnergyPricing.is_active == True
    ).order_by(EnergyPricing.min_volume).all()
    
    # 특정 볼륨에 대한 가격 계산
    if volume:
        applicable_tier = None
        for tier in pricing_tiers:
            if tier.min_volume <= volume:
                if not tier.max_volume or volume <= tier.max_volume:
                    applicable_tier = tier
                    break
                    
        if applicable_tier:
            current_hour = datetime.utcnow().hour
            if 18 <= current_hour <= 22:
                price = applicable_tier.price_per_energy * applicable_tier.peak_hour_multiplier
            else:
                price = applicable_tier.price_per_energy
        else:
            price = Decimal("0.00010")
            
        return {
            "volume": volume,
            "price_per_energy": price,
            "total_cost": price * volume,
            "pricing_tiers": pricing_tiers
        }
    
    return {"pricing_tiers": pricing_tiers}

@router.post("/energy/use", response_model=EnergyUsageResponse)
async def use_energy(
    request: EnergyUsageRequest,
    partner_id: int = Depends(deps.get_current_partner_id),
    db: Session = Depends(deps.get_db)
):
    """에너지 사용 (실시간 차감)"""
    service = EnergyRentalService(db)
    
    try:
        usage = await service.use_energy(
            partner_id=partner_id,
            energy_amount=request.energy_amount,
            transaction_id=request.transaction_id
        )
        
        return {
            "usage_id": usage.id,
            "energy_used": usage.energy_used,
            "cost": usage.total_cost,
            "payment_status": usage.payment_status,
            "message": "에너지가 성공적으로 사용되었습니다"
        }
    except InsufficientEnergyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PaymentError as e:
        raise HTTPException(status_code=402, detail=str(e))

@router.get("/usage/history", response_model=List[EnergyUsageResponse])
async def get_usage_history(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    partner_id: int = Depends(deps.get_current_partner_id),
    db: Session = Depends(deps.get_db)
):
    """에너지 사용 내역 조회"""
    query = db.query(EnergyUsageRecord).join(
        EnergyRentalPlan
    ).filter(
        EnergyRentalPlan.partner_id == partner_id
    )
    
    if start_date:
        query = query.filter(EnergyUsageRecord.created_at >= start_date)
    if end_date:
        query = query.filter(EnergyUsageRecord.created_at <= end_date)
        
    usage_records = query.order_by(
        EnergyUsageRecord.created_at.desc()
    ).limit(100).all()
    
    return usage_records

@router.get("/settlements", response_model=List[SettlementResponse])
async def get_settlements(
    status: Optional[str] = None,
    partner_id: int = Depends(deps.get_current_partner_id),
    db: Session = Depends(deps.get_db)
):
    """정산 내역 조회"""
    query = db.query(EnergySettlement).join(
        EnergyRentalPlan
    ).filter(
        EnergyRentalPlan.partner_id == partner_id
    )
    
    if status:
        query = query.filter(EnergySettlement.payment_status == status)
        
    settlements = query.order_by(
        EnergySettlement.created_at.desc()
    ).limit(50).all()
    
    return settlements

@router.post("/settlements/{settlement_id}/pay")
async def pay_settlement(
    settlement_id: int,
    payment_method: str,
    partner_id: int = Depends(deps.get_current_partner_id),
    db: Session = Depends(deps.get_db)
):
    """정산 수동 결제"""
    settlement = db.query(EnergySettlement).join(
        EnergyRentalPlan
    ).filter(
        EnergySettlement.id == settlement_id,
        EnergyRentalPlan.partner_id == partner_id
    ).first()
    
    if not settlement:
        raise HTTPException(status_code=404, detail="정산을 찾을 수 없습니다")
        
    if settlement.payment_status == "paid":
        raise HTTPException(status_code=400, detail="이미 결제된 정산입니다")
        
    # 결제 처리 (실제 구현 시 결제 서비스 호출)
    # payment_result = await process_payment(...)
    
    settlement.payment_status = "paid"
    settlement.payment_method = payment_method
    settlement.paid_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "정산이 성공적으로 결제되었습니다"}
```

#### 3.2 본사 슈퍼 어드민 API
```python
# app/api/v1/endpoints/admin/energy_rental.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.api import deps
from app.schemas.energy_rental import (
    EnergyPoolStatus, RentalStatistics,
    PartnerEnergyUsage, RevenueReport
)

router = APIRouter()

@router.get("/energy-pool/status", response_model=EnergyPoolStatus)
async def get_energy_pool_status(
    current_user=Depends(deps.get_current_superadmin),
    db: Session = Depends(deps.get_db)
):
    """본사 에너지 풀 현황"""
    # 전체 스테이킹 TRX
    total_staked = db.query(func.sum(EnergyPool.staked_amount)).scalar() or 0
    
    # 전체 에너지 용량
    total_capacity = total_staked * 1500  # 1 TRX = 1500 에너지
    
    # 현재 사용 중인 에너지
    today_usage = db.query(
        func.sum(EnergyUsageRecord.energy_used)
    ).filter(
        EnergyUsageRecord.created_at >= datetime.utcnow().date()
    ).scalar() or 0
    
    # 파트너별 할당량
    partner_allocations = db.query(
        Partner.name,
        func.sum(EnergyUsageRecord.energy_used).label("daily_usage")
    ).join(
        EnergyRentalPlan
    ).join(
        EnergyUsageRecord
    ).filter(
        EnergyUsageRecord.created_at >= datetime.utcnow().date()
    ).group_by(Partner.id).all()
    
    return {
        "total_staked_trx": total_staked,
        "total_energy_capacity": total_capacity,
        "available_energy": total_capacity - today_usage,
        "utilization_rate": (today_usage / total_capacity) * 100 if total_capacity > 0 else 0,
        "partner_allocations": partner_allocations
    }

@router.get("/rental/statistics", response_model=RentalStatistics)
async def get_rental_statistics(
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    current_user=Depends(deps.get_current_superadmin),
    db: Session = Depends(deps.get_db)
):
    """에너지 렌탈 통계"""
    # 기간 설정
    if period == "daily":
        start_date = datetime.utcnow() - timedelta(days=1)
    elif period == "weekly":
        start_date = datetime.utcnow() - timedelta(days=7)
    else:
        start_date = datetime.utcnow() - timedelta(days=30)
        
    # 총 렌탈 수익
    total_revenue = db.query(
        func.sum(EnergyUsageRecord.total_cost)
    ).filter(
        EnergyUsageRecord.created_at >= start_date,
        EnergyUsageRecord.payment_status == "charged"
    ).scalar() or 0
    
    # 총 에너지 사용량
    total_energy_used = db.query(
        func.sum(EnergyUsageRecord.energy_used)
    ).filter(
        EnergyUsageRecord.created_at >= start_date
    ).scalar() or 0
    
    # 활성 파트너 수
    active_partners = db.query(
        func.count(func.distinct(EnergyRentalPlan.partner_id))
    ).filter(
        EnergyRentalPlan.is_active == True
    ).scalar() or 0
    
    # 플랜별 분포
    plan_distribution = db.query(
        EnergyRentalPlan.plan_type,
        func.count(EnergyRentalPlan.id).label("count")
    ).filter(
        EnergyRentalPlan.is_active == True
    ).group_by(EnergyRentalPlan.plan_type).all()
    
    return {
        "period": period,
        "total_revenue": total_revenue,
        "total_energy_used": total_energy_used,
        "average_price_per_energy": total_revenue / total_energy_used if total_energy_used > 0 else 0,
        "active_partners": active_partners,
        "plan_distribution": plan_distribution
    }

@router.get("/partners/{partner_id}/energy-usage", response_model=PartnerEnergyUsage)
async def get_partner_energy_usage(
    partner_id: int,
    current_user=Depends(deps.get_current_superadmin),
    db: Session = Depends(deps.get_db)
):
    """특정 파트너사 에너지 사용 현황"""
    # 현재 플랜
    current_plan = db.query(EnergyRentalPlan).filter(
        EnergyRentalPlan.partner_id == partner_id,
        EnergyRentalPlan.is_active == True
    ).first()
    
    if not current_plan:
        raise HTTPException(status_code=404, detail="활성 플랜이 없습니다")
        
    # 이번 달 사용량
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    monthly_usage = db.query(
        func.sum(EnergyUsageRecord.energy_used)
    ).filter(
        EnergyUsageRecord.rental_plan_id == current_plan.id,
        EnergyUsageRecord.created_at >= month_start
    ).scalar() or 0
    
    # 이번 달 비용
    monthly_cost = db.query(
        func.sum(EnergyUsageRecord.total_cost)
    ).filter(
        EnergyUsageRecord.rental_plan_id == current_plan.id,
        EnergyUsageRecord.created_at >= month_start
    ).scalar() or 0
    
    # 미결제 금액
    unpaid_amount = db.query(
        func.sum(EnergySettlement.final_cost)
    ).filter(
        EnergySettlement.rental_plan_id == current_plan.id,
        EnergySettlement.payment_status == "pending"
    ).scalar() or 0
    
    return {
        "partner_id": partner_id,
        "current_plan": current_plan,
        "monthly_usage": monthly_usage,
        "monthly_cost": monthly_cost,
        "unpaid_amount": unpaid_amount,
        "usage_percentage": (monthly_usage / current_plan.monthly_energy_quota * 100) 
                           if current_plan.monthly_energy_quota else None
    }

@router.post("/energy-pool/recharge")
async def recharge_energy_pool(
    amount_trx: int,
    current_user=Depends(deps.get_current_superadmin),
    db: Session = Depends(deps.get_db)
):
    """에너지 풀 충전 (TRX 스테이킹)"""
    # 실제 스테이킹 처리
    # staking_result = await stake_trx(amount_trx)
    
    # 에너지 풀 업데이트
    energy_pool = db.query(EnergyPool).first()
    if not energy_pool:
        energy_pool = EnergyPool(staked_amount=0)
        db.add(energy_pool)
        
    energy_pool.staked_amount += amount_trx
    energy_pool.last_recharged_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": f"{amount_trx} TRX가 성공적으로 스테이킹되었습니다",
        "new_total": energy_pool.staked_amount,
        "additional_energy": amount_trx * 1500
    }
```

### Phase 4: 자동화 시스템 구현 (1일)

#### 4.1 자동 정산 스케줄러
```python
# app/services/schedulers/energy_settlement_scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EnergySettlementScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
    def start(self):
        """스케줄러 시작"""
        # 일일 정산 (매일 자정)
        self.scheduler.add_job(
            self.daily_settlement,
            'cron',
            hour=0,
            minute=0,
            id='daily_energy_settlement'
        )
        
        # 주간 정산 (매주 월요일)
        self.scheduler.add_job(
            self.weekly_settlement,
            'cron',
            day_of_week='mon',
            hour=0,
            minute=0,
            id='weekly_energy_settlement'
        )
        
        # 월간 정산 (매월 1일)
        self.scheduler.add_job(
            self.monthly_settlement,
            'cron',
            day=1,
            hour=0,
            minute=0,
            id='monthly_energy_settlement'
        )
        
        # 에너지 풀 모니터링 (10분마다)
        self.scheduler.add_job(
            self.monitor_energy_pool,
            'interval',
            minutes=10,
            id='monitor_energy_pool'
        )
        
        self.scheduler.start()
        logger.info("에너지 정산 스케줄러가 시작되었습니다")
        
    async def daily_settlement(self):
        """일일 정산 처리"""
        logger.info("일일 에너지 정산 시작")
        
        with get_db() as db:
            service = EnergyRentalService(db)
            
            # 모든 활성 파트너 조회
            active_partners = db.query(Partner).join(
                EnergyRentalPlan
            ).filter(
                EnergyRentalPlan.is_active == True
            ).all()
            
            for partner in active_partners:
                try:
                    settlement = await service.process_settlement(
                        partner.id, 
                        "daily"
                    )
                    if settlement:
                        logger.info(f"파트너 {partner.id} 일일 정산 완료: {settlement.final_cost}")
                except Exception as e:
                    logger.error(f"파트너 {partner.id} 정산 실패: {str(e)}")
                    
    async def monitor_energy_pool(self):
        """에너지 풀 모니터링"""
        with get_db() as db:
            # 현재 에너지 사용률 확인
            total_capacity = db.query(
                func.sum(EnergyPool.staked_amount)
            ).scalar() or 0
            
            total_capacity *= 1500  # TRX to Energy
            
            today_usage = db.query(
                func.sum(EnergyUsageRecord.energy_used)
            ).filter(
                EnergyUsageRecord.created_at >= datetime.utcnow().date()
            ).scalar() or 0
            
            utilization_rate = (today_usage / total_capacity * 100) if total_capacity > 0 else 0
            
            # 임계값 알림
            if utilization_rate > 80:
                await send_alert(
                    "ENERGY_POOL_WARNING",
                    f"에너지 풀 사용률이 {utilization_rate:.1f}%에 도달했습니다"
                )
            elif utilization_rate > 90:
                await send_alert(
                    "ENERGY_POOL_CRITICAL",
                    f"에너지 풀이 거의 소진되었습니다 ({utilization_rate:.1f}%)"
                )
```

#### 4.2 가격 최적화 엔진
```python
# app/services/energy_price_optimizer.py
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

class EnergyPriceOptimizer:
    def __init__(self, db):
        self.db = db
        
    async def optimize_pricing(self) -> Dict:
        """AI 기반 가격 최적화"""
        # 과거 데이터 수집
        historical_data = self._collect_historical_data()
        
        # 수요 예측
        demand_forecast = self._forecast_demand(historical_data)
        
        # 경쟁사 가격 분석
        market_prices = await self._analyze_market_prices()
        
        # 최적 가격 계산
        optimal_prices = self._calculate_optimal_prices(
            demand_forecast,
            market_prices
        )
        
        return optimal_prices
        
    def _forecast_demand(self, historical_data: List) -> Dict:
        """수요 예측 (간단한 이동평균)"""
        # 실제로는 더 복잡한 ML 모델 사용
        recent_usage = [d['usage'] for d in historical_data[-30:]]
        avg_usage = np.mean(recent_usage)
        trend = np.polyfit(range(len(recent_usage)), recent_usage, 1)[0]
        
        return {
            "expected_daily_usage": avg_usage,
            "growth_rate": trend,
            "peak_hours": [18, 19, 20, 21],
            "confidence": 0.85
        }
        
    def _calculate_optimal_prices(
        self, 
        demand_forecast: Dict,
        market_prices: Dict
    ) -> Dict:
        """최적 가격 계산"""
        base_price = market_prices['average'] * 0.8  # 시장가 대비 20% 할인
        
        # 수요 탄력성 고려
        if demand_forecast['growth_rate'] > 0:
            # 수요 증가 시 가격 상향
            base_price *= 1.05
        
        # 시간대별 가격
        peak_multiplier = 1.2 if datetime.utcnow().hour in demand_forecast['peak_hours'] else 1.0
        
        return {
            "base_price": base_price,
            "peak_price": base_price * peak_multiplier,
            "volume_discounts": {
                1000000: 0.05,    # 100만 에너지 이상 5% 할인
                10000000: 0.10,   # 1000만 에너지 이상 10% 할인
                100000000: 0.15   # 1억 에너지 이상 15% 할인
            }
        }
```

## 📊 구현 완료 시 예상 효과

### 수익 시뮬레이션
```
파트너 10개 기준 (일일 1,000건 출금):
- 일일 에너지 사용: 3,200만
- 일일 수익: 2,560 TRX ($307)
- 월 순수익: 68,910 TRX ($8,269)
- 연간 순수익: $99,228

파트너 50개 확보 시:
- 월 순수익: $41,345
- 연간 순수익: $496,140
```

## ✅ 검증 포인트

- [ ] 렌탈 플랜이 정상적으로 생성되는가?
- [ ] 에너지 사용 시 실시간 과금이 되는가?
- [ ] 구독 플랜 할당량이 정확히 관리되는가?
- [ ] 볼륨 할인이 자동 적용되는가?
- [ ] 정산이 스케줄대로 실행되는가?
- [ ] 미결제 알림이 발송되는가?
- [ ] 에너지 부족 시 알림이 작동하는가?

## 🎉 기대 효과

1. **파트너사 진입장벽 제거**: 초기 투자 없이 서비스 시작
2. **안정적 수익원**: 본사는 높은 수익률 확보
3. **규모의 경제**: 대량 스테이킹으로 원가 절감
4. **자동화**: 과금/정산 완전 자동화
5. **확장성**: 파트너 증가에 따른 선형적 수익 증가

이 시스템을 통해 본사와 파트너사 모두 Win-Win하는 혁신적인 비즈니스 모델을 구축할 수 있습니다!