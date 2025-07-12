# Copilot 문서 #38: 외부 에너지 공급자 연동 시스템

## 목표
본사 에너지 풀이 부족할 때 외부 에너지 공급자로부터 실시간으로 에너지를 구매/대여하여 서비스 중단을 방지합니다. 자동/수동 구매 옵션을 제공하고, 구매한 에너지에 마진을 추가하여 파트너사에게 제공합니다.

## 전제 조건
- Copilot 문서 #36(에너지 렌탈 서비스)이 완료되어 있어야 합니다
- 본사 에너지 풀 모니터링 시스템이 구축되어 있어야 합니다
- TRON 네트워크 연동이 완료되어 있어야 합니다
- 충분한 TRX/USDT 유동성이 확보되어 있어야 합니다

## 🎯 외부 에너지 공급자 연동 구조

### 📊 시스템 아키텍처
```
외부 에너지 공급자 연동
├── 🏪 공급자 관리
│   ├── JustLend Energy Market
│   ├── TronNRG
│   ├── TRONSCAN Energy
│   └── P2P Energy Trading
├── 💱 가격 모니터링
│   ├── 실시간 시세 조회
│   ├── 가격 비교 엔진
│   ├── 최적 공급자 선택
│   └── 가격 히스토리
├── 🤖 자동 구매 시스템
│   ├── 임계값 모니터링
│   ├── 구매 규칙 엔진
│   ├── 리스크 관리
│   └── 구매 실행
├── 👤 수동 구매 인터페이스
│   ├── 시장 현황 대시보드
│   ├── 구매 승인 프로세스
│   ├── 긴급 구매 옵션
│   └── 구매 이력
└── 💰 마진 관리
    ├── 동적 마진 설정
    ├── 공급자별 마진
    ├── 긴급도별 마진
    └── 수익성 분석
```

## 🛠️ 구현 단계

### Phase 1: 외부 공급자 통합 모델 (2일)

#### 1.1 데이터베이스 모델
```python
# app/models/external_energy.py
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, Enum, JSON, ForeignKey
from sqlalchemy.orm import relationship
from decimal import Decimal
import enum

class EnergyProviderType(enum.Enum):
    """에너지 공급자 유형"""
    JUSTLEND = "justlend"          # JustLend Energy Market
    TRONNRG = "tronnrg"            # TronNRG
    TRONSCAN = "tronscan"          # TRONSCAN Energy
    P2P = "p2p"                    # P2P Trading Platform
    SPOT = "spot"                  # Spot Market

class PurchaseStatus(enum.Enum):
    """구매 상태"""
    PENDING = "pending"            # 대기중
    APPROVED = "approved"          # 승인됨
    EXECUTING = "executing"        # 실행중
    COMPLETED = "completed"        # 완료
    FAILED = "failed"              # 실패
    CANCELLED = "cancelled"        # 취소됨

class ExternalEnergyProvider(Base):
    """외부 에너지 공급자"""
    __tablename__ = "external_energy_providers"
    
    id = Column(Integer, primary_key=True)
    provider_type = Column(Enum(EnergyProviderType), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    api_endpoint = Column(String(500))
    api_key = Column(String(255))
    api_secret = Column(String(255))
    
    # 공급자 설정
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)  # 낮을수록 우선순위 높음
    max_daily_purchase = Column(Numeric(20, 6))  # 일일 최대 구매량
    min_purchase_amount = Column(Integer)  # 최소 구매 에너지
    max_purchase_amount = Column(Integer)  # 최대 구매 에너지
    
    # 가격 정보
    last_price = Column(Numeric(20, 10))  # 마지막 조회 가격
    price_updated_at = Column(DateTime)
    average_price_24h = Column(Numeric(20, 10))
    
    # 신뢰도 및 성능
    success_rate = Column(Numeric(5, 2), default=Decimal("100"))
    average_response_time = Column(Integer)  # milliseconds
    total_purchases = Column(Integer, default=0)
    total_energy_purchased = Column(Numeric(20, 0), default=0)
    
    # 메타데이터
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    price_history = relationship("EnergyPriceHistory", back_populates="provider")
    purchases = relationship("ExternalEnergyPurchase", back_populates="provider")

class EnergyPriceHistory(Base):
    """에너지 가격 히스토리"""
    __tablename__ = "energy_price_history"
    
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("external_energy_providers.id"))
    
    price_per_energy = Column(Numeric(20, 10), nullable=False)
    available_amount = Column(Integer)  # 구매 가능량
    min_order = Column(Integer)
    max_order = Column(Integer)
    
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    provider = relationship("ExternalEnergyProvider", back_populates="price_history")

class ExternalEnergyPurchase(Base):
    """외부 에너지 구매 기록"""
    __tablename__ = "external_energy_purchases"
    
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("external_energy_providers.id"))
    
    # 구매 정보
    energy_amount = Column(Integer, nullable=False)
    price_per_energy = Column(Numeric(20, 10), nullable=False)
    total_cost = Column(Numeric(20, 6), nullable=False)
    payment_currency = Column(String(10))  # "TRX", "USDT"
    
    # 상태 관리
    status = Column(Enum(PurchaseStatus), default=PurchaseStatus.PENDING)
    purchase_type = Column(String(20))  # "auto", "manual", "emergency"
    
    # 승인 정보
    requested_by = Column(Integer, ForeignKey("users.id"))
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    
    # 실행 정보
    transaction_hash = Column(String(64))
    energy_received_at = Column(DateTime)
    actual_energy_received = Column(Integer)
    
    # 마진 및 재판매
    margin_rate = Column(Numeric(5, 4), default=Decimal("0.2"))  # 20% 기본 마진
    resale_price = Column(Numeric(20, 10))
    
    # 자동 구매 트리거
    trigger_reason = Column(String(100))  # "low_energy", "scheduled", "emergency"
    energy_level_at_purchase = Column(Integer)  # 구매 시점 에너지 잔량
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # 관계
    provider = relationship("ExternalEnergyProvider", back_populates="purchases")
    requested_user = relationship("User", foreign_keys=[requested_by])
    approved_user = relationship("User", foreign_keys=[approved_by])

class EnergyPurchaseRule(Base):
    """에너지 자동 구매 규칙"""
    __tablename__ = "energy_purchase_rules"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)
    
    # 트리거 조건
    trigger_type = Column(String(50))  # "threshold", "schedule", "prediction"
    energy_threshold = Column(Integer)  # 에너지 임계값
    threshold_percentage = Column(Numeric(5, 2))  # 임계 비율
    schedule_cron = Column(String(100))  # 스케줄 (cron 표현식)
    
    # 구매 설정
    purchase_amount = Column(Integer)  # 구매할 에너지량
    purchase_percentage = Column(Numeric(5, 2))  # 전체 용량의 %
    max_price = Column(Numeric(20, 10))  # 최대 허용 가격
    preferred_providers = Column(JSON)  # 선호 공급자 목록
    
    # 마진 설정
    margin_type = Column(String(20))  # "fixed", "dynamic"
    base_margin = Column(Numeric(5, 4), default=Decimal("0.2"))
    emergency_margin = Column(Numeric(5, 4), default=Decimal("0.5"))
    
    # 실행 제한
    max_daily_executions = Column(Integer, default=10)
    cooldown_minutes = Column(Integer, default=30)
    last_executed_at = Column(DateTime)
    daily_execution_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Phase 2: 외부 공급자 연동 서비스 (3일)

#### 2.1 가격 모니터링 서비스
```python
# app/services/external_energy/price_monitor.py
from typing import List, Dict, Optional
from decimal import Decimal
import asyncio
import aiohttp
from datetime import datetime, timedelta

class EnergyPriceMonitor:
    def __init__(self, db):
        self.db = db
        self.providers = self._load_active_providers()
        
    async def fetch_current_prices(self) -> Dict:
        """모든 공급자의 현재 가격 조회"""
        tasks = []
        for provider in self.providers:
            task = self._fetch_provider_price(provider)
            tasks.append(task)
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        prices = {}
        for provider, result in zip(self.providers, results):
            if not isinstance(result, Exception):
                prices[provider.provider_type.value] = result
                
        return prices
        
    async def _fetch_provider_price(self, provider: ExternalEnergyProvider) -> Dict:
        """개별 공급자 가격 조회"""
        if provider.provider_type == EnergyProviderType.JUSTLEND:
            return await self._fetch_justlend_price(provider)
        elif provider.provider_type == EnergyProviderType.TRONNRG:
            return await self._fetch_tronnrg_price(provider)
        elif provider.provider_type == EnergyProviderType.TRONSCAN:
            return await self._fetch_tronscan_price(provider)
        elif provider.provider_type == EnergyProviderType.P2P:
            return await self._fetch_p2p_price(provider)
            
    async def _fetch_justlend_price(self, provider) -> Dict:
        """JustLend Energy Market 가격 조회"""
        async with aiohttp.ClientSession() as session:
            headers = {"API-Key": provider.api_key}
            url = f"{provider.api_endpoint}/energy/price"
            
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                
                return {
                    "provider": "JustLend",
                    "price": Decimal(str(data["price"])),
                    "available": data["available_energy"],
                    "min_order": data["min_order_size"],
                    "max_order": data["max_order_size"],
                    "estimated_time": data["fulfillment_time"],
                    "timestamp": datetime.utcnow()
                }
                
    async def _fetch_tronnrg_price(self, provider) -> Dict:
        """TronNRG 가격 조회"""
        async with aiohttp.ClientSession() as session:
            url = f"{provider.api_endpoint}/api/v1/energy/market"
            
            async with session.get(url) as response:
                data = await response.json()
                
                # TronNRG는 여러 판매자가 있을 수 있음
                best_offer = min(data["offers"], key=lambda x: x["price"])
                
                return {
                    "provider": "TronNRG",
                    "price": Decimal(str(best_offer["price"])),
                    "available": best_offer["amount"],
                    "min_order": 100000,  # 10만 에너지
                    "max_order": best_offer["amount"],
                    "seller_rating": best_offer["seller"]["rating"],
                    "timestamp": datetime.utcnow()
                }
                
    async def find_best_price(self, energy_amount: int) -> Optional[Dict]:
        """필요한 에너지량에 대한 최적 가격 찾기"""
        prices = await self.fetch_current_prices()
        
        valid_offers = []
        for provider_type, price_info in prices.items():
            if (price_info["available"] >= energy_amount and
                price_info["min_order"] <= energy_amount <= price_info["max_order"]):
                valid_offers.append({
                    "provider_type": provider_type,
                    **price_info
                })
                
        if not valid_offers:
            return None
            
        # 가격순 정렬
        return min(valid_offers, key=lambda x: x["price"])
        
    async def record_price_history(self):
        """가격 히스토리 기록"""
        prices = await self.fetch_current_prices()
        
        for provider in self.providers:
            if provider.provider_type.value in prices:
                price_info = prices[provider.provider_type.value]
                
                history = EnergyPriceHistory(
                    provider_id=provider.id,
                    price_per_energy=price_info["price"],
                    available_amount=price_info.get("available"),
                    min_order=price_info.get("min_order"),
                    max_order=price_info.get("max_order")
                )
                
                self.db.add(history)
                
                # 공급자 정보 업데이트
                provider.last_price = price_info["price"]
                provider.price_updated_at = datetime.utcnow()
                
        self.db.commit()
```

#### 2.2 자동 구매 엔진
```python
# app/services/external_energy/auto_purchase_engine.py
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class AutoPurchaseEngine:
    def __init__(self, db, price_monitor: EnergyPriceMonitor):
        self.db = db
        self.price_monitor = price_monitor
        
    async def check_and_execute_rules(self) -> List[ExternalEnergyPurchase]:
        """자동 구매 규칙 확인 및 실행"""
        executed_purchases = []
        
        # 활성 규칙 조회
        active_rules = self.db.query(EnergyPurchaseRule).filter(
            EnergyPurchaseRule.is_active == True
        ).order_by(EnergyPurchaseRule.priority).all()
        
        current_energy = await self._get_current_energy_level()
        total_capacity = await self._get_total_capacity()
        
        for rule in active_rules:
            if self._should_execute_rule(rule, current_energy, total_capacity):
                purchase = await self._execute_purchase(rule, current_energy)
                if purchase:
                    executed_purchases.append(purchase)
                    
        return executed_purchases
        
    def _should_execute_rule(
        self, 
        rule: EnergyPurchaseRule, 
        current_energy: int,
        total_capacity: int
    ) -> bool:
        """규칙 실행 여부 판단"""
        # 쿨다운 체크
        if rule.last_executed_at:
            cooldown_end = rule.last_executed_at + timedelta(minutes=rule.cooldown_minutes)
            if datetime.utcnow() < cooldown_end:
                return False
                
        # 일일 실행 제한 체크
        if rule.daily_execution_count >= rule.max_daily_executions:
            return False
            
        # 트리거 조건 체크
        if rule.trigger_type == "threshold":
            if rule.energy_threshold and current_energy < rule.energy_threshold:
                return True
            if rule.threshold_percentage:
                current_percentage = (current_energy / total_capacity) * 100
                if current_percentage < rule.threshold_percentage:
                    return True
                    
        elif rule.trigger_type == "schedule":
            # 스케줄 기반 실행 (cron 파싱 필요)
            pass
            
        elif rule.trigger_type == "prediction":
            # ML 기반 예측 (향후 구현)
            pass
            
        return False
        
    async def _execute_purchase(
        self, 
        rule: EnergyPurchaseRule,
        current_energy: int
    ) -> Optional[ExternalEnergyPurchase]:
        """자동 구매 실행"""
        # 구매량 계산
        if rule.purchase_amount:
            amount = rule.purchase_amount
        elif rule.purchase_percentage:
            total_capacity = await self._get_total_capacity()
            amount = int(total_capacity * rule.purchase_percentage / 100)
        else:
            return None
            
        # 최적 가격 찾기
        best_offer = await self.price_monitor.find_best_price(amount)
        if not best_offer:
            logger.warning(f"No suitable offer found for {amount} energy")
            return None
            
        # 최대 가격 체크
        if rule.max_price and best_offer["price"] > rule.max_price:
            logger.warning(f"Price {best_offer['price']} exceeds max price {rule.max_price}")
            return None
            
        # 선호 공급자 체크
        if rule.preferred_providers:
            if best_offer["provider_type"] not in rule.preferred_providers:
                # 선호 공급자 중에서 다시 찾기
                # ... 구현 필요
                pass
                
        # 마진 계산
        if current_energy < total_capacity * 0.1:  # 10% 미만 = 긴급
            margin = rule.emergency_margin
            purchase_type = "emergency"
        else:
            margin = rule.base_margin
            purchase_type = "auto"
            
        # 구매 레코드 생성
        provider = self.db.query(ExternalEnergyProvider).filter(
            ExternalEnergyProvider.provider_type == best_offer["provider_type"]
        ).first()
        
        purchase = ExternalEnergyPurchase(
            provider_id=provider.id,
            energy_amount=amount,
            price_per_energy=best_offer["price"],
            total_cost=best_offer["price"] * amount,
            payment_currency="TRX",
            status=PurchaseStatus.APPROVED,
            purchase_type=purchase_type,
            margin_rate=margin,
            resale_price=best_offer["price"] * (1 + margin),
            trigger_reason=f"rule:{rule.name}",
            energy_level_at_purchase=current_energy
        )
        
        self.db.add(purchase)
        
        # 규칙 업데이트
        rule.last_executed_at = datetime.utcnow()
        rule.daily_execution_count += 1
        
        self.db.commit()
        
        # 실제 구매 실행
        await self._process_purchase(purchase)
        
        return purchase
        
    async def _process_purchase(self, purchase: ExternalEnergyPurchase):
        """실제 구매 프로세스 실행"""
        try:
            purchase.status = PurchaseStatus.EXECUTING
            self.db.commit()
            
            # 공급자별 구매 API 호출
            provider = purchase.provider
            if provider.provider_type == EnergyProviderType.JUSTLEND:
                result = await self._purchase_from_justlend(purchase)
            elif provider.provider_type == EnergyProviderType.TRONNRG:
                result = await self._purchase_from_tronnrg(purchase)
            # ... 다른 공급자들
            
            if result["success"]:
                purchase.status = PurchaseStatus.COMPLETED
                purchase.transaction_hash = result["tx_hash"]
                purchase.actual_energy_received = result["energy_received"]
                purchase.completed_at = datetime.utcnow()
                
                # 공급자 통계 업데이트
                provider.total_purchases += 1
                provider.total_energy_purchased += result["energy_received"]
            else:
                purchase.status = PurchaseStatus.FAILED
                
        except Exception as e:
            logger.error(f"Purchase failed: {str(e)}")
            purchase.status = PurchaseStatus.FAILED
            
        self.db.commit()
```

#### 2.3 수동 구매 서비스
```python
# app/services/external_energy/manual_purchase_service.py
class ManualPurchaseService:
    def __init__(self, db, price_monitor: EnergyPriceMonitor):
        self.db = db
        self.price_monitor = price_monitor
        
    async def create_purchase_request(
        self,
        requested_by: int,
        energy_amount: int,
        max_price: Optional[Decimal] = None,
        preferred_provider: Optional[str] = None,
        urgency: str = "normal"  # "normal", "urgent", "emergency"
    ) -> ExternalEnergyPurchase:
        """수동 구매 요청 생성"""
        # 현재 시장 가격 조회
        if preferred_provider:
            provider = self.db.query(ExternalEnergyProvider).filter(
                ExternalEnergyProvider.provider_type == preferred_provider
            ).first()
            prices = await self.price_monitor._fetch_provider_price(provider)
        else:
            best_offer = await self.price_monitor.find_best_price(energy_amount)
            if not best_offer:
                raise ValueError("No suitable offer found")
                
        # 마진 설정
        margin_rates = {
            "normal": Decimal("0.2"),    # 20%
            "urgent": Decimal("0.35"),   # 35%
            "emergency": Decimal("0.5")  # 50%
        }
        margin = margin_rates.get(urgency, Decimal("0.2"))
        
        # 구매 요청 생성
        purchase = ExternalEnergyPurchase(
            provider_id=provider.id if preferred_provider else None,
            energy_amount=energy_amount,
            price_per_energy=best_offer["price"],
            total_cost=best_offer["price"] * energy_amount,
            payment_currency="TRX",
            status=PurchaseStatus.PENDING,
            purchase_type="manual",
            requested_by=requested_by,
            margin_rate=margin,
            resale_price=best_offer["price"] * (1 + margin),
            trigger_reason=f"manual:{urgency}"
        )
        
        self.db.add(purchase)
        self.db.commit()
        
        return purchase
        
    async def approve_purchase(
        self,
        purchase_id: int,
        approved_by: int
    ) -> ExternalEnergyPurchase:
        """구매 승인"""
        purchase = self.db.query(ExternalEnergyPurchase).filter(
            ExternalEnergyPurchase.id == purchase_id,
            ExternalEnergyPurchase.status == PurchaseStatus.PENDING
        ).first()
        
        if not purchase:
            raise ValueError("Purchase not found or already processed")
            
        purchase.status = PurchaseStatus.APPROVED
        purchase.approved_by = approved_by
        purchase.approved_at = datetime.utcnow()
        
        self.db.commit()
        
        # 자동으로 구매 실행
        await self._process_purchase(purchase)
        
        return purchase
```

### Phase 3: API 엔드포인트 구현 (2일)

#### 3.1 슈퍼 어드민 API
```python
# app/api/v1/endpoints/admin/external_energy.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from app.api import deps
from app.schemas.external_energy import (
    ProviderResponse, PriceComparisonResponse,
    PurchaseRequest, PurchaseResponse,
    PurchaseRuleCreate, PurchaseRuleResponse
)

router = APIRouter()

@router.get("/providers", response_model=List[ProviderResponse])
async def get_energy_providers(
    active_only: bool = True,
    current_user=Depends(deps.get_current_superadmin),
    db: Session = Depends(deps.get_db)
):
    """외부 에너지 공급자 목록 조회"""
    query = db.query(ExternalEnergyProvider)
    if active_only:
        query = query.filter(ExternalEnergyProvider.is_active == True)
    
    providers = query.order_by(ExternalEnergyProvider.priority).all()
    return providers

@router.get("/prices/compare", response_model=PriceComparisonResponse)
async def compare_energy_prices(
    amount: int = Query(..., description="필요한 에너지량"),
    current_user=Depends(deps.get_current_superadmin),
    db: Session = Depends(deps.get_db)
):
    """공급자별 가격 비교"""
    price_monitor = EnergyPriceMonitor(db)
    prices = await price_monitor.fetch_current_prices()
    
    comparisons = []
    for provider_type, price_info in prices.items():
        if price_info["available"] >= amount:
            comparisons.append({
                "provider": provider_type,
                "price_per_energy": price_info["price"],
                "total_cost": price_info["price"] * amount,
                "available": price_info["available"],
                "estimated_time": price_info.get("estimated_time", "즉시")
            })
    
    # 가격순 정렬
    comparisons.sort(key=lambda x: x["total_cost"])
    
    return {
        "requested_amount": amount,
        "comparisons": comparisons,
        "best_offer": comparisons[0] if comparisons else None
    }

@router.post("/purchase/manual", response_model=PurchaseResponse)
async def create_manual_purchase(
    request: PurchaseRequest,
    current_user=Depends(deps.get_current_superadmin),
    db: Session = Depends(deps.get_db)
):
    """수동 구매 요청 생성"""
    service = ManualPurchaseService(db, EnergyPriceMonitor(db))
    
    purchase = await service.create_purchase_request(
        requested_by=current_user.id,
        energy_amount=request.energy_amount,
        max_price=request.max_price,
        preferred_provider=request.preferred_provider,
        urgency=request.urgency
    )
    
    return purchase

@router.post("/purchase/{purchase_id}/approve", response_model=PurchaseResponse)
async def approve_purchase(
    purchase_id: int,
    current_user=Depends(deps.get_current_superadmin),
    db: Session = Depends(deps.get_db)
):
    """구매 승인"""
    service = ManualPurchaseService(db, EnergyPriceMonitor(db))
    
    purchase = await service.approve_purchase(
        purchase_id=purchase_id,
        approved_by=current_user.id
    )
    
    return purchase

@router.get("/purchases", response_model=List[PurchaseResponse])
async def get_purchase_history(
    status: Optional[PurchaseStatus] = None,
    provider_type: Optional[EnergyProviderType] = None,
    skip: int = 0,
    limit: int = 50,
    current_user=Depends(deps.get_current_superadmin),
    db: Session = Depends(deps.get_db)
):
    """구매 이력 조회"""
    query = db.query(ExternalEnergyPurchase)
    
    if status:
        query = query.filter(ExternalEnergyPurchase.status == status)
    if provider_type:
        query = query.join(ExternalEnergyProvider).filter(
            ExternalEnergyProvider.provider_type == provider_type
        )
    
    purchases = query.order_by(
        ExternalEnergyPurchase.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return purchases

# 자동 구매 규칙 관리
@router.get("/rules", response_model=List[PurchaseRuleResponse])
async def get_purchase_rules(
    active_only: bool = True,
    current_user=Depends(deps.get_current_superadmin),
    db: Session = Depends(deps.get_db)
):
    """자동 구매 규칙 목록"""
    query = db.query(EnergyPurchaseRule)
    if active_only:
        query = query.filter(EnergyPurchaseRule.is_active == True)
    
    rules = query.order_by(EnergyPurchaseRule.priority).all()
    return rules

@router.post("/rules", response_model=PurchaseRuleResponse)
async def create_purchase_rule(
    rule_data: PurchaseRuleCreate,
    current_user=Depends(deps.get_current_superadmin),
    db: Session = Depends(deps.get_db)
):
    """자동 구매 규칙 생성"""
    rule = EnergyPurchaseRule(**rule_data.dict())
    db.add(rule)
    db.commit()
    return rule

@router.put("/rules/{rule_id}/toggle")
async def toggle_purchase_rule(
    rule_id: int,
    current_user=Depends(deps.get_current_superadmin),
    db: Session = Depends(deps.get_db)
):
    """규칙 활성화/비활성화"""
    rule = db.query(EnergyPurchaseRule).filter(
        EnergyPurchaseRule.id == rule_id
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    rule.is_active = not rule.is_active
    db.commit()
    
    return {"message": f"Rule {'activated' if rule.is_active else 'deactivated'}"}
```

#### 3.2 모니터링 대시보드 API
```python
@router.get("/dashboard/overview")
async def get_external_energy_dashboard(
    current_user=Depends(deps.get_current_superadmin),
    db: Session = Depends(deps.get_db)
):
    """외부 에너지 구매 대시보드"""
    # 오늘의 구매 현황
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
    
    today_purchases = db.query(
        func.count(ExternalEnergyPurchase.id).label("count"),
        func.sum(ExternalEnergyPurchase.energy_amount).label("total_energy"),
        func.sum(ExternalEnergyPurchase.total_cost).label("total_cost")
    ).filter(
        ExternalEnergyPurchase.created_at >= today_start,
        ExternalEnergyPurchase.status == PurchaseStatus.COMPLETED
    ).first()
    
    # 공급자별 통계
    provider_stats = db.query(
        ExternalEnergyProvider.name,
        func.count(ExternalEnergyPurchase.id).label("purchase_count"),
        func.avg(ExternalEnergyPurchase.price_per_energy).label("avg_price")
    ).join(
        ExternalEnergyPurchase
    ).filter(
        ExternalEnergyPurchase.created_at >= today_start - timedelta(days=7)
    ).group_by(
        ExternalEnergyProvider.id
    ).all()
    
    # 자동 구매 성공률
    auto_purchases = db.query(
        func.count(ExternalEnergyPurchase.id).label("total"),
        func.sum(
            case([(ExternalEnergyPurchase.status == PurchaseStatus.COMPLETED, 1)], else_=0)
        ).label("success")
    ).filter(
        ExternalEnergyPurchase.purchase_type == "auto"
    ).first()
    
    success_rate = (auto_purchases.success / auto_purchases.total * 100) if auto_purchases.total > 0 else 0
    
    return {
        "today_summary": {
            "purchases": today_purchases.count or 0,
            "total_energy": today_purchases.total_energy or 0,
            "total_cost": today_purchases.total_cost or 0,
            "average_price": (today_purchases.total_cost / today_purchases.total_energy) 
                           if today_purchases.total_energy else 0
        },
        "provider_performance": provider_stats,
        "automation": {
            "success_rate": success_rate,
            "active_rules": db.query(EnergyPurchaseRule).filter(
                EnergyPurchaseRule.is_active == True
            ).count()
        }
    }
```

### Phase 4: 자동화 및 스케줄러 (1일)

#### 4.1 가격 모니터링 스케줄러
```python
# app/services/schedulers/energy_price_scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

logger = logging.getLogger(__name__)

class EnergyPriceScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
    def start(self):
        # 5분마다 가격 체크
        self.scheduler.add_job(
            self.check_prices,
            'interval',
            minutes=5,
            id='check_energy_prices'
        )
        
        # 1시간마다 가격 히스토리 기록
        self.scheduler.add_job(
            self.record_price_history,
            'interval',
            hours=1,
            id='record_price_history'
        )
        
        # 10분마다 자동 구매 규칙 체크
        self.scheduler.add_job(
            self.check_auto_purchase_rules,
            'interval',
            minutes=10,
            id='check_auto_purchase_rules'
        )
        
        # 매일 자정에 규칙 카운터 리셋
        self.scheduler.add_job(
            self.reset_daily_counters,
            'cron',
            hour=0,
            minute=0,
            id='reset_daily_counters'
        )
        
        self.scheduler.start()
        logger.info("Energy price scheduler started")
        
    async def check_prices(self):
        """가격 체크 및 알림"""
        with get_db() as db:
            monitor = EnergyPriceMonitor(db)
            prices = await monitor.fetch_current_prices()
            
            # 가격 급등 알림
            for provider_type, price_info in prices.items():
                provider = db.query(ExternalEnergyProvider).filter(
                    ExternalEnergyProvider.provider_type == provider_type
                ).first()
                
                if provider.last_price:
                    price_change = ((price_info["price"] - provider.last_price) / 
                                   provider.last_price * 100)
                    
                    if price_change > 20:  # 20% 이상 상승
                        await send_alert(
                            "ENERGY_PRICE_SURGE",
                            f"{provider.name} 가격 급등: {price_change:.1f}%"
                        )
                        
    async def check_auto_purchase_rules(self):
        """자동 구매 규칙 실행"""
        with get_db() as db:
            engine = AutoPurchaseEngine(db, EnergyPriceMonitor(db))
            purchases = await engine.check_and_execute_rules()
            
            if purchases:
                logger.info(f"Executed {len(purchases)} auto purchases")
                
    async def reset_daily_counters(self):
        """일일 카운터 리셋"""
        with get_db() as db:
            db.query(EnergyPurchaseRule).update({
                "daily_execution_count": 0
            })
            db.commit()
```

## 📊 마진 관리 및 수익성 분석

### 동적 마진 전략
```python
class MarginCalculator:
    """동적 마진 계산"""
    
    BASE_MARGINS = {
        "normal": 0.20,      # 평상시 20%
        "low_energy": 0.35,  # 에너지 부족 시 35%
        "emergency": 0.50,   # 긴급 상황 50%
        "bulk": 0.15        # 대량 구매 15%
    }
    
    def calculate_margin(self, context: Dict) -> Decimal:
        # 에너지 수준에 따른 마진
        energy_level = context.get("energy_level_percentage", 50)
        if energy_level < 10:
            base_margin = self.BASE_MARGINS["emergency"]
        elif energy_level < 30:
            base_margin = self.BASE_MARGINS["low_energy"]
        else:
            base_margin = self.BASE_MARGINS["normal"]
            
        # 구매량에 따른 조정
        amount = context.get("amount", 0)
        if amount > 10000000:  # 1000만 에너지 이상
            base_margin = min(base_margin, self.BASE_MARGINS["bulk"])
            
        # 시간대별 조정 (피크 시간 추가 마진)
        current_hour = datetime.utcnow().hour
        if 18 <= current_hour <= 22:  # 피크 시간
            base_margin *= 1.2
            
        return Decimal(str(base_margin))
```

## ✅ 검증 포인트

### 기능 검증
- [ ] 외부 공급자 API 연동이 정상 작동하는가?
- [ ] 가격 비교 및 최적 공급자 선택이 작동하는가?
- [ ] 자동 구매 규칙이 정확히 실행되는가?
- [ ] 수동 구매 승인 프로세스가 작동하는가?
- [ ] 마진이 정확히 계산되고 적용되는가?

### 안정성 검증
- [ ] API 장애 시 폴백 처리가 되는가?
- [ ] 중복 구매가 방지되는가?
- [ ] 트랜잭션 실패 시 롤백이 되는가?
- [ ] 가격 급등 시 알림이 발송되는가?

### 성능 검증
- [ ] 동시 다발적 구매 요청을 처리할 수 있는가?
- [ ] 가격 조회가 5초 내에 완료되는가?
- [ ] 스케줄러가 안정적으로 작동하는가?

## 🎉 기대 효과

1. **서비스 안정성**: 에너지 부족으로 인한 서비스 중단 방지
2. **비용 최적화**: 여러 공급자 중 최적 가격 선택
3. **수익 창출**: 마진을 통한 추가 수익
4. **자동화**: 24/7 자동 에너지 관리
5. **리스크 관리**: 가격 급등 및 공급 부족 대응

이 시스템을 통해 안정적인 에너지 공급과 추가 수익을 동시에 달성할 수 있습니다!