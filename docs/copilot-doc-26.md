# Copilot 문서 #26: 파트너사 수수료 및 정책 관리

## 목표
파트너사별로 독립적인 수수료 체계와 운영 정책을 설정할 수 있는 유연한 관리 시스템을 구축합니다. 각 파트너사는 자신의 비즈니스 모델에 맞게 수수료율, 출금 정책, 에너지 대응 방식을 자유롭게 설정할 수 있습니다.

## 전제 조건
- Copilot 문서 #24-25가 완료되어 있어야 합니다.
- 파트너사 외부 지갑 연동이 구현되어 있어야 합니다.
- 에너지 모니터링 시스템이 작동 중이어야 합니다.
- Redis 캐시가 구동 중이어야 합니다.

## 🎯 수수료 및 정책 관리 구조

### 📊 시스템 아키텍처
```
파트너사 수수료/정책 관리
├── 💰 수수료 체계
│   ├── 기본 수수료율 설정
│   ├── 거래 유형별 차등 수수료
│   ├── 사용자 등급별 할인율
│   ├── 프로모션 수수료
│   └── 최소/최대 수수료 한도
├── 📋 출금 정책
│   ├── 출금 방식 (실시간/일괄/혼합)
│   ├── 자동 승인 규칙
│   ├── 출금 한도 설정
│   ├── 출금 스케줄 관리
│   └── 화이트리스트 정책
├── 🔋 에너지 대응 정책
│   ├── 에너지 부족 시 대응 방식
│   ├── TRX 직접 결제 옵션
│   ├── 대기열 우선순위
│   ├── 긴급 출금 정책
│   └── 에너지 절약 모드
├── 👥 사용자 등급 관리
│   ├── VIP 등급 설정
│   ├── 등급별 혜택
│   ├── 승급 조건
│   └── 등급 유지 정책
└── 📊 정책 분석
    ├── 수수료 수익 분석
    ├── 정책 효과 측정
    ├── A/B 테스트
    └── 최적화 제안
```

## 🛠️ 구현 단계

### Phase 1: 수수료/정책 모델 설계 (1일)

#### 1.1 수수료 정책 모델
```python
# app/models/fee_policy.py
"""파트너사 수수료 및 정책 관련 모델"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, JSON, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base
import enum

class FeeType(enum.Enum):
    """수수료 유형"""
    FLAT = "flat"              # 고정 수수료
    PERCENTAGE = "percentage"   # 비율 수수료
    TIERED = "tiered"          # 구간별 수수료
    DYNAMIC = "dynamic"        # 동적 수수료

class WithdrawalPolicy(enum.Enum):
    """출금 정책"""
    REALTIME = "realtime"      # 실시간 처리
    BATCH = "batch"            # 일괄 처리
    HYBRID = "hybrid"          # 혼합 (조건부)
    MANUAL = "manual"          # 수동 처리

class EnergyPolicy(enum.Enum):
    """에너지 부족 대응 정책"""
    WAIT_QUEUE = "wait_queue"           # 대기열 등록
    TRX_PAYMENT = "trx_payment"         # TRX 직접 결제
    PRIORITY_QUEUE = "priority_queue"   # 우선순위 큐
    REJECT = "reject"                   # 거부

class PartnerFeePolicy(Base):
    """파트너사 수수료 정책"""
    __tablename__ = "partner_fee_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False, unique=True)
    
    # 기본 수수료 설정
    fee_type = Column(Enum(FeeType), default=FeeType.PERCENTAGE, comment="수수료 유형")
    base_fee_rate = Column(Numeric(5, 4), default=0.001, comment="기본 수수료율 (0.1%)")
    min_fee_amount = Column(Numeric(18, 6), default=0.1, comment="최소 수수료")
    max_fee_amount = Column(Numeric(18, 6), comment="최대 수수료")
    
    # 거래 유형별 수수료
    withdrawal_fee_rate = Column(Numeric(5, 4), default=0.001, comment="출금 수수료율")
    internal_transfer_fee_rate = Column(Numeric(5, 4), default=0, comment="내부 이체 수수료율")
    
    # 사용자 등급별 할인
    vip_discount_rates = Column(JSON, comment="VIP 등급별 할인율")
    
    # 프로모션 설정
    promotion_active = Column(Boolean, default=False, comment="프로모션 활성화")
    promotion_fee_rate = Column(Numeric(5, 4), comment="프로모션 수수료율")
    promotion_end_date = Column(DateTime(timezone=True), comment="프로모션 종료일")
    
    # 수익 분배
    platform_share_rate = Column(Numeric(5, 4), default=0.3, comment="플랫폼 수수료 분배율 (30%)")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    partner = relationship("Partner", back_populates="fee_policy")
    fee_tiers = relationship("FeeTier", back_populates="fee_policy")

class FeeTier(Base):
    """구간별 수수료 설정"""
    __tablename__ = "fee_tiers"
    
    id = Column(Integer, primary_key=True, index=True)
    fee_policy_id = Column(Integer, ForeignKey("partner_fee_policies.id"), nullable=False)
    
    min_amount = Column(Numeric(18, 6), nullable=False, comment="최소 금액")
    max_amount = Column(Numeric(18, 6), comment="최대 금액 (NULL=무제한)")
    fee_rate = Column(Numeric(5, 4), nullable=False, comment="수수료율")
    fixed_fee = Column(Numeric(18, 6), default=0, comment="고정 수수료")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    fee_policy = relationship("PartnerFeePolicy", back_populates="fee_tiers")

class PartnerWithdrawalPolicy(Base):
    """파트너사 출금 정책"""
    __tablename__ = "partner_withdrawal_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False, unique=True)
    
    # 출금 방식
    policy_type = Column(Enum(WithdrawalPolicy), default=WithdrawalPolicy.HYBRID, comment="출금 정책")
    
    # 실시간 출금 설정
    realtime_enabled = Column(Boolean, default=True, comment="실시간 출금 활성화")
    realtime_max_amount = Column(Numeric(18, 6), default=1000, comment="실시간 최대 금액")
    auto_approve_enabled = Column(Boolean, default=False, comment="자동 승인 활성화")
    auto_approve_max_amount = Column(Numeric(18, 6), default=100, comment="자동 승인 최대 금액")
    
    # 일괄 출금 설정
    batch_enabled = Column(Boolean, default=True, comment="일괄 출금 활성화")
    batch_schedule = Column(JSON, comment="일괄 처리 스케줄")
    batch_min_amount = Column(Numeric(18, 6), default=10, comment="일괄 처리 최소 금액")
    
    # 출금 한도
    daily_limit_per_user = Column(Numeric(18, 6), default=10000, comment="사용자별 일일 한도")
    daily_limit_total = Column(Numeric(18, 6), default=1000000, comment="전체 일일 한도")
    single_transaction_limit = Column(Numeric(18, 6), default=5000, comment="단일 거래 한도")
    
    # 화이트리스트
    whitelist_required = Column(Boolean, default=False, comment="화이트리스트 필수")
    whitelist_addresses = Column(JSON, comment="화이트리스트 주소 목록")
    
    # 보안 설정
    require_2fa = Column(Boolean, default=True, comment="2FA 필수")
    confirmation_blocks = Column(Integer, default=19, comment="확인 블록 수")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    partner = relationship("Partner", back_populates="withdrawal_policy")

class PartnerEnergyPolicy(Base):
    """파트너사 에너지 대응 정책"""
    __tablename__ = "partner_energy_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False, unique=True)
    
    # 기본 대응 정책
    default_policy = Column(Enum(EnergyPolicy), default=EnergyPolicy.WAIT_QUEUE, comment="기본 대응 정책")
    
    # TRX 직접 결제 설정
    trx_payment_enabled = Column(Boolean, default=True, comment="TRX 결제 활성화")
    trx_payment_markup = Column(Numeric(5, 4), default=0.1, comment="TRX 결제 마크업 (10%)")
    trx_payment_max_fee = Column(Numeric(18, 6), default=20, comment="최대 TRX 수수료")
    
    # 대기열 설정
    queue_enabled = Column(Boolean, default=True, comment="대기열 활성화")
    queue_max_wait_hours = Column(Integer, default=24, comment="최대 대기 시간")
    queue_notification_enabled = Column(Boolean, default=True, comment="대기열 알림")
    
    # 우선순위 설정
    priority_queue_enabled = Column(Boolean, default=True, comment="우선순위 큐 활성화")
    vip_priority_levels = Column(JSON, comment="VIP 등급별 우선순위")
    
    # 에너지 절약 모드
    energy_saving_enabled = Column(Boolean, default=False, comment="에너지 절약 모드")
    energy_saving_threshold = Column(Integer, default=20, comment="절약 모드 임계값 (%)")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    partner = relationship("Partner", back_populates="energy_policy")

class UserTier(Base):
    """사용자 등급 설정"""
    __tablename__ = "user_tiers"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    
    tier_name = Column(String(50), nullable=False, comment="등급명")
    tier_level = Column(Integer, nullable=False, comment="등급 레벨")
    
    # 승급 조건
    min_monthly_volume = Column(Numeric(18, 6), default=0, comment="최소 월 거래량")
    min_balance = Column(Numeric(18, 6), default=0, comment="최소 잔액")
    min_transactions = Column(Integer, default=0, comment="최소 거래 횟수")
    
    # 혜택
    fee_discount_rate = Column(Numeric(5, 4), default=0, comment="수수료 할인율")
    withdrawal_priority = Column(Integer, default=0, comment="출금 우선순위")
    daily_limit_multiplier = Column(Numeric(3, 1), default=1.0, comment="일일 한도 배수")
    
    # 추가 혜택
    benefits = Column(JSON, comment="추가 혜택 설정")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### Phase 2: 수수료 계산 및 정책 서비스 (2일)

#### 2.1 수수료 계산 서비스
```python
# app/services/fee/fee_calculator_service.py
"""수수료 계산 서비스"""
from typing import Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.fee_policy import (
    PartnerFeePolicy, FeeTier, FeeType, UserTier
)
from app.models.user import User
from app.utils.logger import logger

class FeeCalculatorService:
    """수수료 계산 엔진"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def calculate_fee(
        self,
        partner_id: int,
        user_id: int,
        amount: Decimal,
        transaction_type: str
    ) -> Dict[str, Decimal]:
        """수수료 계산"""
        try:
            # 파트너 수수료 정책 조회
            fee_policy = await self.db.query(PartnerFeePolicy).filter(
                PartnerFeePolicy.partner_id == partner_id
            ).first()
            
            if not fee_policy:
                # 기본 수수료 적용
                return self._default_fee_calculation(amount)
            
            # 기본 수수료율 결정
            base_rate = self._get_base_rate(fee_policy, transaction_type)
            
            # 프로모션 확인
            if fee_policy.promotion_active and fee_policy.promotion_end_date:
                if datetime.utcnow() <= fee_policy.promotion_end_date:
                    base_rate = fee_policy.promotion_fee_rate or base_rate
            
            # 수수료 유형별 계산
            if fee_policy.fee_type == FeeType.FLAT:
                fee_amount = Decimal(str(base_rate))
            elif fee_policy.fee_type == FeeType.PERCENTAGE:
                fee_amount = amount * base_rate
            elif fee_policy.fee_type == FeeType.TIERED:
                fee_amount = await self._calculate_tiered_fee(fee_policy.id, amount)
            else:  # DYNAMIC
                fee_amount = await self._calculate_dynamic_fee(
                    fee_policy, amount, transaction_type
                )
            
            # 사용자 등급 할인 적용
            discount_rate = await self._get_user_discount(partner_id, user_id)
            if discount_rate > 0:
                fee_amount = fee_amount * (1 - discount_rate)
            
            # 최소/최대 수수료 적용
            if fee_policy.min_fee_amount:
                fee_amount = max(fee_amount, fee_policy.min_fee_amount)
            if fee_policy.max_fee_amount:
                fee_amount = min(fee_amount, fee_policy.max_fee_amount)
            
            # 플랫폼 수수료 계산
            platform_fee = fee_amount * fee_policy.platform_share_rate
            partner_fee = fee_amount - platform_fee
            
            return {
                "total_fee": fee_amount,
                "platform_fee": platform_fee,
                "partner_fee": partner_fee,
                "discount_applied": discount_rate,
                "fee_rate": base_rate,
                "net_amount": amount - fee_amount
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate fee: {e}")
            return self._default_fee_calculation(amount)
    
    def _get_base_rate(
        self, 
        fee_policy: PartnerFeePolicy, 
        transaction_type: str
    ) -> Decimal:
        """거래 유형별 기본 수수료율"""
        if transaction_type == "withdrawal":
            return fee_policy.withdrawal_fee_rate
        elif transaction_type == "internal_transfer":
            return fee_policy.internal_transfer_fee_rate
        else:
            return fee_policy.base_fee_rate
    
    async def _calculate_tiered_fee(
        self, 
        fee_policy_id: int, 
        amount: Decimal
    ) -> Decimal:
        """구간별 수수료 계산"""
        tiers = await self.db.query(FeeTier).filter(
            FeeTier.fee_policy_id == fee_policy_id
        ).order_by(FeeTier.min_amount).all()
        
        total_fee = Decimal('0')
        remaining_amount = amount
        
        for tier in tiers:
            if remaining_amount <= 0:
                break
            
            # 현재 구간에서 처리할 금액
            if tier.max_amount:
                tier_amount = min(
                    remaining_amount, 
                    tier.max_amount - tier.min_amount
                )
            else:
                tier_amount = remaining_amount
            
            # 구간 수수료 계산
            tier_fee = tier_amount * tier.fee_rate + tier.fixed_fee
            total_fee += tier_fee
            remaining_amount -= tier_amount
        
        return total_fee
    
    async def _calculate_dynamic_fee(
        self,
        fee_policy: PartnerFeePolicy,
        amount: Decimal,
        transaction_type: str
    ) -> Decimal:
        """동적 수수료 계산 (네트워크 상태 기반)"""
        base_rate = self._get_base_rate(fee_policy, transaction_type)
        
        # 네트워크 혼잡도 확인
        congestion_factor = await self._get_network_congestion()
        
        # 시간대별 가중치
        hour = datetime.utcnow().hour
        time_factor = 1.0
        if 9 <= hour <= 17:  # 업무 시간
            time_factor = 1.2
        elif 0 <= hour <= 6:  # 새벽 시간
            time_factor = 0.8
        
        # 동적 수수료 계산
        dynamic_rate = base_rate * congestion_factor * time_factor
        
        return amount * dynamic_rate
    
    async def _get_user_discount(
        self, 
        partner_id: int, 
        user_id: int
    ) -> Decimal:
        """사용자 등급별 할인율 조회"""
        # 사용자 정보 조회
        user = await self.db.query(User).filter(
            User.id == user_id
        ).first()
        
        if not user or not user.tier_level:
            return Decimal('0')
        
        # 사용자 등급 조회
        user_tier = await self.db.query(UserTier).filter(
            UserTier.partner_id == partner_id,
            UserTier.tier_level == user.tier_level
        ).first()
        
        if user_tier:
            return user_tier.fee_discount_rate
        
        return Decimal('0')
    
    async def _get_network_congestion(self) -> Decimal:
        """네트워크 혼잡도 조회"""
        # TODO: 실제 TRON 네트워크 상태 조회
        # 임시로 고정값 반환
        return Decimal('1.0')
    
    def _default_fee_calculation(self, amount: Decimal) -> Dict[str, Decimal]:
        """기본 수수료 계산"""
        fee_rate = Decimal('0.001')  # 0.1%
        fee_amount = amount * fee_rate
        
        return {
            "total_fee": fee_amount,
            "platform_fee": fee_amount * Decimal('0.3'),
            "partner_fee": fee_amount * Decimal('0.7'),
            "discount_applied": Decimal('0'),
            "fee_rate": fee_rate,
            "net_amount": amount - fee_amount
        }
```

#### 2.2 정책 실행 서비스
```python
# app/services/policy/policy_executor_service.py
"""정책 실행 서비스"""
from typing import Dict, Optional, List
from decimal import Decimal
from datetime import datetime, time
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fee_policy import (
    PartnerWithdrawalPolicy, PartnerEnergyPolicy,
    WithdrawalPolicy, EnergyPolicy
)
from app.models.energy_pool import EnergyStatus
from app.utils.logger import logger

class PolicyExecutorService:
    """정책 실행 엔진"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def check_withdrawal_eligibility(
        self,
        partner_id: int,
        user_id: int,
        amount: Decimal,
        to_address: str
    ) -> Tuple[bool, Optional[str], Dict]:
        """출금 가능 여부 확인"""
        try:
            # 출금 정책 조회
            policy = await self.db.query(PartnerWithdrawalPolicy).filter(
                PartnerWithdrawalPolicy.partner_id == partner_id
            ).first()
            
            if not policy:
                return True, None, {"policy": "default"}
            
            # 출금 방식 결정
            withdrawal_type = self._determine_withdrawal_type(policy, amount)
            
            # 화이트리스트 확인
            if policy.whitelist_required:
                if to_address not in (policy.whitelist_addresses or []):
                    return False, "Address not in whitelist", {"policy": "whitelist"}
            
            # 한도 확인
            limit_check = await self._check_limits(policy, user_id, amount)
            if not limit_check["passed"]:
                return False, limit_check["reason"], limit_check
            
            # 자동 승인 확인
            auto_approve = False
            if withdrawal_type == "realtime" and policy.auto_approve_enabled:
                if amount <= policy.auto_approve_max_amount:
                    auto_approve = True
            
            return True, None, {
                "policy": policy.policy_type.value,
                "withdrawal_type": withdrawal_type,
                "auto_approve": auto_approve,
                "requires_2fa": policy.require_2fa,
                "confirmation_blocks": policy.confirmation_blocks
            }
            
        except Exception as e:
            logger.error(f"Failed to check withdrawal eligibility: {e}")
            return False, "System error", {"error": str(e)}
    
    async def determine_energy_response(
        self,
        partner_id: int,
        user_id: int,
        energy_status: EnergyStatus
    ) -> Dict:
        """에너지 부족 시 대응 방안 결정"""
        try:
            # 에너지 정책 조회
            policy = await self.db.query(PartnerEnergyPolicy).filter(
                PartnerEnergyPolicy.partner_id == partner_id
            ).first()
            
            if not policy:
                return {"action": "wait_queue", "options": {}}
            
            # 에너지 상태별 대응
            if energy_status == EnergyStatus.SUFFICIENT:
                return {"action": "proceed", "options": {}}
            
            # 사용자 등급 확인
            user_priority = await self._get_user_priority(partner_id, user_id)
            
            # 정책별 대응 결정
            response = {"action": policy.default_policy.value, "options": {}}
            
            if policy.default_policy == EnergyPolicy.TRX_PAYMENT:
                if policy.trx_payment_enabled:
                    response["options"] = {
                        "enabled": True,
                        "markup": float(policy.trx_payment_markup),
                        "max_fee": float(policy.trx_payment_max_fee),
                        "estimated_fee": await self._estimate_trx_fee()
                    }
            
            elif policy.default_policy == EnergyPolicy.WAIT_QUEUE:
                if policy.queue_enabled:
                    response["options"] = {
                        "enabled": True,
                        "max_wait_hours": policy.queue_max_wait_hours,
                        "notification": policy.queue_notification_enabled,
                        "estimated_wait": await self._estimate_queue_time(partner_id)
                    }
            
            elif policy.default_policy == EnergyPolicy.PRIORITY_QUEUE:
                if policy.priority_queue_enabled:
                    response["options"] = {
                        "enabled": True,
                        "user_priority": user_priority,
                        "queue_position": await self._get_queue_position(
                            partner_id, user_priority
                        )
                    }
            
            # 에너지 절약 모드 확인
            if policy.energy_saving_enabled:
                current_percentage = await self._get_energy_percentage(partner_id)
                if current_percentage <= policy.energy_saving_threshold:
                    response["energy_saving_mode"] = True
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to determine energy response: {e}")
            return {"action": "wait_queue", "error": str(e)}
    
    def _determine_withdrawal_type(
        self,
        policy: PartnerWithdrawalPolicy,
        amount: Decimal
    ) -> str:
        """출금 방식 결정"""
        if policy.policy_type == WithdrawalPolicy.REALTIME:
            return "realtime"
        elif policy.policy_type == WithdrawalPolicy.BATCH:
            return "batch"
        elif policy.policy_type == WithdrawalPolicy.MANUAL:
            return "manual"
        else:  # HYBRID
            # 금액 기준으로 결정
            if policy.realtime_enabled and amount <= policy.realtime_max_amount:
                return "realtime"
            elif policy.batch_enabled and amount >= policy.batch_min_amount:
                return "batch"
            else:
                return "manual"
    
    async def _check_limits(
        self,
        policy: PartnerWithdrawalPolicy,
        user_id: int,
        amount: Decimal
    ) -> Dict:
        """출금 한도 확인"""
        # 단일 거래 한도
        if amount > policy.single_transaction_limit:
            return {
                "passed": False,
                "reason": f"Exceeds single transaction limit: {policy.single_transaction_limit}"
            }
        
        # 일일 한도 확인
        daily_total = await self._get_user_daily_withdrawal(user_id)
        if daily_total + amount > policy.daily_limit_per_user:
            return {
                "passed": False,
                "reason": f"Exceeds daily limit: {policy.daily_limit_per_user}"
            }
        
        # 전체 일일 한도 확인
        total_daily = await self._get_total_daily_withdrawal(policy.partner_id)
        if total_daily + amount > policy.daily_limit_total:
            return {
                "passed": False,
                "reason": "System daily limit reached"
            }
        
        return {"passed": True}
    
    async def is_batch_schedule_time(self, partner_id: int) -> bool:
        """현재 시간이 일괄 처리 시간인지 확인"""
        policy = await self.db.query(PartnerWithdrawalPolicy).filter(
            PartnerWithdrawalPolicy.partner_id == partner_id
        ).first()
        
        if not policy or not policy.batch_enabled:
            return False
        
        schedule = policy.batch_schedule or {}
        current_time = datetime.utcnow().time()
        current_day = datetime.utcnow().strftime("%A").lower()
        
        # 스케줄 확인
        if current_day in schedule:
            for time_slot in schedule[current_day]:
                start_time = time.fromisoformat(time_slot["start"])
                end_time = time.fromisoformat(time_slot["end"])
                
                if start_time <= current_time <= end_time:
                    return True
        
        return False
```

### Phase 3: 정책 관리 API (1일)

#### 3.1 수수료 정책 API
```python
# app/api/v1/endpoints/partner/fee_policy.py
"""파트너 수수료 정책 관리 API"""
from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_partner
from app.models.partner import Partner
from app.schemas.fee_policy import (
    FeePolicyResponse,
    FeePolicyUpdate,
    FeeCalculateRequest,
    FeeCalculateResponse,
    UserTierCreate,
    UserTierResponse
)
from app.services.fee.fee_calculator_service import FeeCalculatorService

router = APIRouter(tags=["파트너 수수료 정책"])

@router.get("/fee-policy", response_model=FeePolicyResponse)
async def get_fee_policy(
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """현재 수수료 정책 조회"""
    from app.models.fee_policy import PartnerFeePolicy
    
    policy = await db.query(PartnerFeePolicy).filter(
        PartnerFeePolicy.partner_id == current_partner.id
    ).first()
    
    if not policy:
        # 기본 정책 생성
        policy = PartnerFeePolicy(partner_id=current_partner.id)
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
    
    return FeePolicyResponse.from_orm(policy)

@router.put("/fee-policy", response_model=FeePolicyResponse)
async def update_fee_policy(
    policy_update: FeePolicyUpdate,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """수수료 정책 업데이트"""
    from app.models.fee_policy import PartnerFeePolicy
    
    policy = await db.query(PartnerFeePolicy).filter(
        PartnerFeePolicy.partner_id == current_partner.id
    ).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Fee policy not found")
    
    # 정책 업데이트
    update_data = policy_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(policy, field, value)
    
    await db.commit()
    await db.refresh(policy)
    
    return FeePolicyResponse.from_orm(policy)

@router.post("/fee/calculate", response_model=FeeCalculateResponse)
async def calculate_fee(
    request: FeeCalculateRequest,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """수수료 계산"""
    calculator = FeeCalculatorService(db)
    
    fee_info = await calculator.calculate_fee(
        partner_id=current_partner.id,
        user_id=request.user_id,
        amount=request.amount,
        transaction_type=request.transaction_type
    )
    
    return FeeCalculateResponse(**fee_info)

@router.post("/user-tiers", response_model=UserTierResponse)
async def create_user_tier(
    tier_data: UserTierCreate,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """사용자 등급 생성"""
    from app.models.fee_policy import UserTier
    
    # 중복 확인
    existing = await db.query(UserTier).filter(
        UserTier.partner_id == current_partner.id,
        UserTier.tier_level == tier_data.tier_level
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Tier level already exists")
    
    tier = UserTier(
        partner_id=current_partner.id,
        **tier_data.dict()
    )
    
    db.add(tier)
    await db.commit()
    await db.refresh(tier)
    
    return UserTierResponse.from_orm(tier)

@router.get("/user-tiers", response_model=List[UserTierResponse])
async def get_user_tiers(
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """사용자 등급 목록 조회"""
    from app.models.fee_policy import UserTier
    
    tiers = await db.query(UserTier).filter(
        UserTier.partner_id == current_partner.id
    ).order_by(UserTier.tier_level).all()
    
    return [UserTierResponse.from_orm(tier) for tier in tiers]
```

#### 3.2 출금/에너지 정책 API
```python
# app/api/v1/endpoints/partner/withdrawal_policy.py
"""파트너 출금 정책 관리 API"""
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_partner
from app.models.partner import Partner
from app.schemas.policy import (
    WithdrawalPolicyResponse,
    WithdrawalPolicyUpdate,
    EnergyPolicyResponse,
    EnergyPolicyUpdate,
    PolicyCheckRequest,
    PolicyCheckResponse
)
from app.services.policy.policy_executor_service import PolicyExecutorService

router = APIRouter(tags=["파트너 정책 관리"])

@router.get("/withdrawal-policy", response_model=WithdrawalPolicyResponse)
async def get_withdrawal_policy(
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """출금 정책 조회"""
    from app.models.fee_policy import PartnerWithdrawalPolicy
    
    policy = await db.query(PartnerWithdrawalPolicy).filter(
        PartnerWithdrawalPolicy.partner_id == current_partner.id
    ).first()
    
    if not policy:
        # 기본 정책 생성
        policy = PartnerWithdrawalPolicy(partner_id=current_partner.id)
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
    
    return WithdrawalPolicyResponse.from_orm(policy)

@router.put("/withdrawal-policy", response_model=WithdrawalPolicyResponse)
async def update_withdrawal_policy(
    policy_update: WithdrawalPolicyUpdate,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """출금 정책 업데이트"""
    from app.models.fee_policy import PartnerWithdrawalPolicy
    
    policy = await db.query(PartnerWithdrawalPolicy).filter(
        PartnerWithdrawalPolicy.partner_id == current_partner.id
    ).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Withdrawal policy not found")
    
    # 정책 업데이트
    update_data = policy_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(policy, field, value)
    
    await db.commit()
    await db.refresh(policy)
    
    return WithdrawalPolicyResponse.from_orm(policy)

@router.get("/energy-policy", response_model=EnergyPolicyResponse)
async def get_energy_policy(
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """에너지 정책 조회"""
    from app.models.fee_policy import PartnerEnergyPolicy
    
    policy = await db.query(PartnerEnergyPolicy).filter(
        PartnerEnergyPolicy.partner_id == current_partner.id
    ).first()
    
    if not policy:
        # 기본 정책 생성
        policy = PartnerEnergyPolicy(partner_id=current_partner.id)
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
    
    return EnergyPolicyResponse.from_orm(policy)

@router.put("/energy-policy", response_model=EnergyPolicyResponse)
async def update_energy_policy(
    policy_update: EnergyPolicyUpdate,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """에너지 정책 업데이트"""
    from app.models.fee_policy import PartnerEnergyPolicy
    
    policy = await db.query(PartnerEnergyPolicy).filter(
        PartnerEnergyPolicy.partner_id == current_partner.id
    ).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Energy policy not found")
    
    # 정책 업데이트
    update_data = policy_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(policy, field, value)
    
    await db.commit()
    await db.refresh(policy)
    
    return EnergyPolicyResponse.from_orm(policy)

@router.post("/check-withdrawal", response_model=PolicyCheckResponse)
async def check_withdrawal_policy(
    request: PolicyCheckRequest,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """출금 정책 확인"""
    executor = PolicyExecutorService(db)
    
    eligible, reason, details = await executor.check_withdrawal_eligibility(
        partner_id=current_partner.id,
        user_id=request.user_id,
        amount=request.amount,
        to_address=request.to_address
    )
    
    return PolicyCheckResponse(
        eligible=eligible,
        reason=reason,
        details=details
    )
```

### Phase 4: 정책 관리 UI (1일)

#### 4.1 수수료 정책 관리 UI
```typescript
// frontend/components/policy/FeePolicyManager.tsx
import React, { useState, useEffect } from 'react';
import { Card, Button, Input, Select, Switch, Alert } from '@/components/ui';
import { Save, TrendingUp, Percent, DollarSign } from 'lucide-react';
import { useFeePolicy } from '@/hooks/useFeePolicy';
import { FeeCalculator } from './FeeCalculator';
import { UserTierManager } from './UserTierManager';

export const FeePolicyManager: React.FC = () => {
  const { policy, loading, error, updatePolicy, calculateFee } = useFeePolicy();
  const [formData, setFormData] = useState(policy);
  const [testAmount, setTestAmount] = useState('100');

  useEffect(() => {
    if (policy) {
      setFormData(policy);
    }
  }, [policy]);

  const handleSave = async () => {
    try {
      await updatePolicy(formData);
      toast.success('수수료 정책이 업데이트되었습니다');
    } catch (err) {
      toast.error('정책 업데이트 실패');
    }
  };

  const handleTestCalculation = async () => {
    const result = await calculateFee({
      amount: parseFloat(testAmount),
      transaction_type: 'withdrawal',
      user_id: 1 // 테스트 사용자
    });
    
    console.log('Fee calculation result:', result);
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <Alert variant="error">{error}</Alert>;

  return (
    <div className="space-y-6">
      {/* 기본 수수료 설정 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">기본 수수료 설정</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              수수료 유형
            </label>
            <Select
              value={formData?.fee_type || 'percentage'}
              onChange={(e) => setFormData({
                ...formData,
                fee_type: e.target.value
              })}
            >
              <option value="flat">고정 수수료</option>
              <option value="percentage">비율 수수료</option>
              <option value="tiered">구간별 수수료</option>
              <option value="dynamic">동적 수수료</option>
            </Select>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">
              기본 수수료율 (%)
            </label>
            <Input
              type="number"
              step="0.01"
              value={formData?.base_fee_rate * 100 || 0}
              onChange={(e) => setFormData({
                ...formData,
                base_fee_rate: parseFloat(e.target.value) / 100
              })}
              placeholder="0.1"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">
              최소 수수료 (USDT)
            </label>
            <Input
              type="number"
              step="0.01"
              value={formData?.min_fee_amount || 0}
              onChange={(e) => setFormData({
                ...formData,
                min_fee_amount: parseFloat(e.target.value)
              })}
              placeholder="0.1"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">
              최대 수수료 (USDT)
            </label>
            <Input
              type="number"
              step="0.01"
              value={formData?.max_fee_amount || ''}
              onChange={(e) => setFormData({
                ...formData,
                max_fee_amount: e.target.value ? parseFloat(e.target.value) : null
              })}
              placeholder="제한 없음"
            />
          </div>
        </div>
        
        <div className="mt-4 flex justify-end">
          <Button onClick={handleSave}>
            <Save className="w-4 h-4 mr-2" />
            저장
          </Button>
        </div>
      </Card>

      {/* 거래 유형별 수수료 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">거래 유형별 수수료</h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span>출금 수수료율</span>
            <div className="flex items-center space-x-2">
              <Input
                type="number"
                step="0.01"
                className="w-24"
                value={formData?.withdrawal_fee_rate * 100 || 0}
                onChange={(e) => setFormData({
                  ...formData,
                  withdrawal_fee_rate: parseFloat(e.target.value) / 100
                })}
              />
              <span>%</span>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <span>내부 이체 수수료율</span>
            <div className="flex items-center space-x-2">
              <Input
                type="number"
                step="0.01"
                className="w-24"
                value={formData?.internal_transfer_fee_rate * 100 || 0}
                onChange={(e) => setFormData({
                  ...formData,
                  internal_transfer_fee_rate: parseFloat(e.target.value) / 100
                })}
              />
              <span>%</span>
            </div>
          </div>
        </div>
      </Card>

      {/* 프로모션 설정 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">프로모션 설정</h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span>프로모션 활성화</span>
            <Switch
              checked={formData?.promotion_active || false}
              onChange={(checked) => setFormData({
                ...formData,
                promotion_active: checked
              })}
            />
          </div>
          
          {formData?.promotion_active && (
            <>
              <div>
                <label className="block text-sm font-medium mb-2">
                  프로모션 수수료율 (%)
                </label>
                <Input
                  type="number"
                  step="0.01"
                  value={formData?.promotion_fee_rate * 100 || 0}
                  onChange={(e) => setFormData({
                    ...formData,
                    promotion_fee_rate: parseFloat(e.target.value) / 100
                  })}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">
                  프로모션 종료일
                </label>
                <Input
                  type="datetime-local"
                  value={formData?.promotion_end_date || ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    promotion_end_date: e.target.value
                  })}
                />
              </div>
            </>
          )}
        </div>
      </Card>

      {/* 수수료 계산기 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">수수료 계산 테스트</h3>
        <FeeCalculator 
          onCalculate={handleTestCalculation}
          testAmount={testAmount}
          setTestAmount={setTestAmount}
        />
      </Card>

      {/* 사용자 등급 관리 */}
      <UserTierManager />
    </div>
  );
};
```

## 🔧 데이터베이스 마이그레이션

```sql
-- 파트너 수수료 정책 테이블
CREATE TABLE partner_fee_policies (
    id SERIAL PRIMARY KEY,
    partner_id INTEGER NOT NULL UNIQUE REFERENCES partners(id),
    fee_type VARCHAR(20) DEFAULT 'percentage',
    base_fee_rate DECIMAL(5,4) DEFAULT 0.001,
    min_fee_amount DECIMAL(18,6) DEFAULT 0.1,
    max_fee_amount DECIMAL(18,6),
    withdrawal_fee_rate DECIMAL(5,4) DEFAULT 0.001,
    internal_transfer_fee_rate DECIMAL(5,4) DEFAULT 0,
    vip_discount_rates JSONB,
    promotion_active BOOLEAN DEFAULT FALSE,
    promotion_fee_rate DECIMAL(5,4),
    promotion_end_date TIMESTAMP WITH TIME ZONE,
    platform_share_rate DECIMAL(5,4) DEFAULT 0.3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 구간별 수수료 테이블
CREATE TABLE fee_tiers (
    id SERIAL PRIMARY KEY,
    fee_policy_id INTEGER NOT NULL REFERENCES partner_fee_policies(id),
    min_amount DECIMAL(18,6) NOT NULL,
    max_amount DECIMAL(18,6),
    fee_rate DECIMAL(5,4) NOT NULL,
    fixed_fee DECIMAL(18,6) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_fee_tiers_policy_id (fee_policy_id),
    INDEX idx_fee_tiers_amount (min_amount, max_amount)
);

-- 파트너 출금 정책 테이블
CREATE TABLE partner_withdrawal_policies (
    id SERIAL PRIMARY KEY,
    partner_id INTEGER NOT NULL UNIQUE REFERENCES partners(id),
    policy_type VARCHAR(20) DEFAULT 'hybrid',
    realtime_enabled BOOLEAN DEFAULT TRUE,
    realtime_max_amount DECIMAL(18,6) DEFAULT 1000,
    auto_approve_enabled BOOLEAN DEFAULT FALSE,
    auto_approve_max_amount DECIMAL(18,6) DEFAULT 100,
    batch_enabled BOOLEAN DEFAULT TRUE,
    batch_schedule JSONB,
    batch_min_amount DECIMAL(18,6) DEFAULT 10,
    daily_limit_per_user DECIMAL(18,6) DEFAULT 10000,
    daily_limit_total DECIMAL(18,6) DEFAULT 1000000,
    single_transaction_limit DECIMAL(18,6) DEFAULT 5000,
    whitelist_required BOOLEAN DEFAULT FALSE,
    whitelist_addresses JSONB,
    require_2fa BOOLEAN DEFAULT TRUE,
    confirmation_blocks INTEGER DEFAULT 19,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 파트너 에너지 정책 테이블
CREATE TABLE partner_energy_policies (
    id SERIAL PRIMARY KEY,
    partner_id INTEGER NOT NULL UNIQUE REFERENCES partners(id),
    default_policy VARCHAR(20) DEFAULT 'wait_queue',
    trx_payment_enabled BOOLEAN DEFAULT TRUE,
    trx_payment_markup DECIMAL(5,4) DEFAULT 0.1,
    trx_payment_max_fee DECIMAL(18,6) DEFAULT 20,
    queue_enabled BOOLEAN DEFAULT TRUE,
    queue_max_wait_hours INTEGER DEFAULT 24,
    queue_notification_enabled BOOLEAN DEFAULT TRUE,
    priority_queue_enabled BOOLEAN DEFAULT TRUE,
    vip_priority_levels JSONB,
    energy_saving_enabled BOOLEAN DEFAULT FALSE,
    energy_saving_threshold INTEGER DEFAULT 20,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 사용자 등급 테이블
CREATE TABLE user_tiers (
    id SERIAL PRIMARY KEY,
    partner_id INTEGER NOT NULL REFERENCES partners(id),
    tier_name VARCHAR(50) NOT NULL,
    tier_level INTEGER NOT NULL,
    min_monthly_volume DECIMAL(18,6) DEFAULT 0,
    min_balance DECIMAL(18,6) DEFAULT 0,
    min_transactions INTEGER DEFAULT 0,
    fee_discount_rate DECIMAL(5,4) DEFAULT 0,
    withdrawal_priority INTEGER DEFAULT 0,
    daily_limit_multiplier DECIMAL(3,1) DEFAULT 1.0,
    benefits JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(partner_id, tier_level),
    INDEX idx_user_tiers_partner_id (partner_id)
);
```

## ✅ 검증 포인트

- [ ] 파트너별 독립적인 수수료 정책이 적용되는가?
- [ ] 거래 유형별 차등 수수료가 계산되는가?
- [ ] 사용자 등급별 할인이 정확히 적용되는가?
- [ ] 프로모션 기간 동안 할인 수수료가 적용되는가?
- [ ] 출금 정책에 따라 처리 방식이 결정되는가?
- [ ] 에너지 부족 시 설정한 정책대로 대응되는가?
- [ ] 일괄 출금 스케줄이 정상 작동하는가?
- [ ] 화이트리스트 및 한도 체크가 작동하는가?

## 🎉 기대 효과

1. **비즈니스 유연성**: 파트너사별 맞춤형 수수료 정책
2. **경쟁력 강화**: 차별화된 서비스 제공 가능
3. **수익 최적화**: 동적 수수료로 수익 극대화
4. **리스크 관리**: 출금 정책으로 안전성 확보
5. **사용자 만족**: 등급별 혜택으로 충성도 향상

이 시스템을 통해 각 파트너사는 자신의 비즈니스 모델에 최적화된 정책을 운영할 수 있습니다.