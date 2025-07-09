# Copilot 문서 #26: 동적 수수료 관리 시스템 구현

## 목표
관리자가 실시간으로 수수료를 조정하고, 파트너사별/거래유형별로 차별화된 수수료를 적용할 수 있는 동적 수수료 관리 시스템을 구축합니다.

## 상세 지시사항

### 1. 수수료 설정 모델 확장

#### 1.1 동적 수수료 모델
```python
# app/models/fee_config.py
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, JSON, Enum, ForeignKey
from sqlalchemy.orm import relationship
from decimal import Decimal
import enum

class FeeType(enum.Enum):
    PERCENTAGE = "percentage"  # 비율 수수료
    FIXED = "fixed"  # 고정 수수료
    TIERED = "tiered"  # 구간별 수수료
    DYNAMIC = "dynamic"  # 동적 수수료

class TransactionType(enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    INTERNAL_TRANSFER = "internal_transfer"

class FeeConfiguration(Base):
    __tablename__ = "fee_configurations"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    
    # 수수료 타입
    fee_type = Column(Enum(FeeType), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    
    # 기본 수수료 설정
    base_percentage = Column(Numeric(5, 4), default=0)  # 0.00% ~ 99.99%
    base_fixed_amount = Column(Numeric(20, 6), default=0)  # 고정 금액
    
    # 최소/최대 제한
    min_fee = Column(Numeric(20, 6), default=0)
    max_fee = Column(Numeric(20, 6))
    
    # 구간별 수수료 (티어)
    tier_config = Column(JSON)  # [{"min": 0, "max": 100, "fee": 2.0}, ...]
    
    # 동적 수수료 규칙
    dynamic_rules = Column(JSON)  # 조건별 수수료 조정 규칙
    
    # 활성화 상태
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # 우선순위 (높을수록 우선)
    
    # 적용 범위
    partner_id = Column(Integer, ForeignKey("partners.id"))  # 특정 파트너용
    user_tier = Column(String(20))  # VIP, Premium, Standard 등
    
    # 유효 기간
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)
    
    # 메타데이터
    created_by = Column(Integer, ForeignKey("admin_users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    partner = relationship("Partner", back_populates="fee_configs")
    history = relationship("FeeConfigHistory", back_populates="config")

class FeeConfigHistory(Base):
    __tablename__ = "fee_config_history"
    
    id = Column(Integer, primary_key=True)
    config_id = Column(Integer, ForeignKey("fee_configurations.id"))
    
    # 변경 내용
    changed_fields = Column(JSON)  # 변경된 필드와 이전/이후 값
    change_reason = Column(String(500))
    
    # 변경자 정보
    changed_by = Column(Integer, ForeignKey("admin_users.id"))
    changed_at = Column(DateTime, default=datetime.utcnow)
    
    config = relationship("FeeConfiguration", back_populates="history")

class FeeCalculationLog(Base):
    __tablename__ = "fee_calculation_logs"
    
    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    
    # 계산 정보
    config_id = Column(Integer, ForeignKey("fee_configurations.id"))
    transaction_amount = Column(Numeric(20, 6))
    calculated_fee = Column(Numeric(20, 6))
    final_fee = Column(Numeric(20, 6))  # 조정 후 최종 수수료
    
    # 계산 과정
    calculation_steps = Column(JSON)  # 단계별 계산 과정
    applied_rules = Column(JSON)  # 적용된 규칙들
    
    calculated_at = Column(DateTime, default=datetime.utcnow)
```

### 2. 수수료 계산 엔진

#### 2.1 동적 수수료 계산기
```python
# app/services/fee/dynamic_calculator.py
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import json

class DynamicFeeCalculator:
    def __init__(self, db_session, redis_client):
        self.db = db_session
        self.redis = redis_client
        self.cache_ttl = 300  # 5분
        
    async def calculate_fee(
        self,
        transaction_type: TransactionType,
        amount: Decimal,
        user_id: int,
        partner_id: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """동적 수수료 계산"""
        # 사용자 정보 조회
        user = await self.get_user_with_tier(user_id)
        
        # 적용 가능한 수수료 설정 조회
        configs = await self.get_applicable_configs(
            transaction_type=transaction_type,
            partner_id=partner_id or user.partner_id,
            user_tier=user.tier
        )
        
        if not configs:
            raise ValueError("적용 가능한 수수료 설정이 없습니다")
            
        # 우선순위가 가장 높은 설정 선택
        config = configs[0]
        
        # 수수료 계산
        calculation_result = await self._calculate_by_config(
            config=config,
            amount=amount,
            user=user,
            metadata=metadata
        )
        
        # 계산 로그 저장
        await self.save_calculation_log(
            transaction_type=transaction_type,
            amount=amount,
            config=config,
            result=calculation_result
        )
        
        return calculation_result
        
    async def _calculate_by_config(
        self,
        config: FeeConfiguration,
        amount: Decimal,
        user: User,
        metadata: Dict
    ) -> Dict:
        """설정에 따른 수수료 계산"""
        steps = []
        
        # 1. 기본 수수료 계산
        if config.fee_type == FeeType.PERCENTAGE:
            base_fee = amount * (config.base_percentage / 100)
            steps.append({
                "step": "base_percentage",
                "calculation": f"{amount} * {config.base_percentage}%",
                "result": float(base_fee)
            })
            
        elif config.fee_type == FeeType.FIXED:
            base_fee = config.base_fixed_amount
            steps.append({
                "step": "fixed_amount",
                "result": float(base_fee)
            })
            
        elif config.fee_type == FeeType.TIERED:
            base_fee = await self._calculate_tiered_fee(
                amount=amount,
                tiers=config.tier_config
            )
            steps.append({
                "step": "tiered_calculation",
                "tiers": config.tier_config,
                "result": float(base_fee)
            })
            
        elif config.fee_type == FeeType.DYNAMIC:
            base_fee = await self._calculate_dynamic_fee(
                config=config,
                amount=amount,
                user=user,
                metadata=metadata
            )
            steps.extend(base_fee['steps'])
            base_fee = base_fee['fee']
            
        # 2. 최소/최대 제한 적용
        final_fee = base_fee
        
        if config.min_fee and final_fee < config.min_fee:
            final_fee = config.min_fee
            steps.append({
                "step": "min_fee_applied",
                "original": float(base_fee),
                "adjusted": float(final_fee)
            })
            
        if config.max_fee and final_fee > config.max_fee:
            final_fee = config.max_fee
            steps.append({
                "step": "max_fee_applied",
                "original": float(base_fee),
                "adjusted": float(final_fee)
            })
            
        return {
            "config_id": config.id,
            "config_name": config.name,
            "transaction_amount": float(amount),
            "calculated_fee": float(base_fee),
            "final_fee": float(final_fee),
            "fee_percentage": float((final_fee / amount * 100) if amount > 0 else 0),
            "calculation_steps": steps,
            "applied_at": datetime.utcnow().isoformat()
        }
        
    async def _calculate_tiered_fee(
        self,
        amount: Decimal,
        tiers: List[Dict]
    ) -> Decimal:
        """구간별 수수료 계산"""
        for tier in sorted(tiers, key=lambda x: x['min']):
            if tier['min'] <= amount <= tier.get('max', float('inf')):
                if tier.get('type') == 'percentage':
                    return amount * Decimal(str(tier['fee'])) / 100
                else:
                    return Decimal(str(tier['fee']))
                    
        # 기본값
        return Decimal('0')
        
    async def _calculate_dynamic_fee(
        self,
        config: FeeConfiguration,
        amount: Decimal,
        user: User,
        metadata: Dict
    ) -> Dict:
        """동적 규칙 기반 수수료 계산"""
        base_fee = amount * (config.base_percentage / 100)
        steps = [{
            "step": "base_calculation",
            "fee": float(base_fee)
        }]
        
        # 동적 규칙 적용
        for rule in config.dynamic_rules:
            if await self._evaluate_rule(rule, amount, user, metadata):
                adjustment = await self._apply_rule_adjustment(
                    rule=rule,
                    current_fee=base_fee,
                    amount=amount
                )
                
                base_fee = adjustment['new_fee']
                steps.append({
                    "step": f"rule_{rule['name']}",
                    "adjustment": adjustment['adjustment'],
                    "new_fee": float(base_fee)
                })
                
        return {
            "fee": base_fee,
            "steps": steps
        }
        
    async def _evaluate_rule(
        self,
        rule: Dict,
        amount: Decimal,
        user: User,
        metadata: Dict
    ) -> bool:
        """규칙 조건 평가"""
        condition_type = rule.get('condition_type')
        
        if condition_type == 'volume_based':
            # 거래량 기반
            user_volume = await self.get_user_monthly_volume(user.id)
            return user_volume >= rule['threshold']
            
        elif condition_type == 'time_based':
            # 시간 기반 (피크/오프피크)
            current_hour = datetime.utcnow().hour
            return current_hour in rule['hours']
            
        elif condition_type == 'energy_based':
            # 에너지 상태 기반
            energy_status = await self.get_energy_pool_status()
            return energy_status['usage_percentage'] >= rule['threshold']
            
        elif condition_type == 'user_tier':
            # 사용자 등급 기반
            return user.tier in rule['tiers']
            
        elif condition_type == 'transaction_count':
            # 거래 횟수 기반
            tx_count = await self.get_user_transaction_count(user.id)
            return tx_count >= rule['threshold']
            
        return False
```

### 3. 수수료 관리 서비스

#### 3.1 수수료 설정 관리자
```python
# app/services/fee/config_manager.py
from typing import List, Optional, Dict
from datetime import datetime, timedelta

class FeeConfigManager:
    def __init__(self, db_session, redis_client, calculator):
        self.db = db_session
        self.redis = redis_client
        self.calculator = calculator
        
    async def create_fee_config(
        self,
        config_data: CreateFeeConfigRequest,
        admin_id: int
    ) -> FeeConfiguration:
        """새 수수료 설정 생성"""
        # 중복 확인
        existing = await self.check_duplicate_config(config_data)
        if existing:
            raise ValueError("동일한 조건의 수수료 설정이 이미 존재합니다")
            
        # 설정 생성
        config = FeeConfiguration(
            **config_data.dict(),
            created_by=admin_id
        )
        
        self.db.add(config)
        await self.db.commit()
        
        # 캐시 무효화
        await self.invalidate_fee_cache()
        
        # 변경 이력 기록
        await self.record_config_change(
            config_id=config.id,
            change_type="created",
            changed_by=admin_id
        )
        
        return config
        
    async def update_fee_config(
        self,
        config_id: int,
        update_data: UpdateFeeConfigRequest,
        admin_id: int,
        reason: str
    ) -> FeeConfiguration:
        """수수료 설정 업데이트"""
        config = await self.db.get(FeeConfiguration, config_id)
        if not config:
            raise ValueError("수수료 설정을 찾을 수 없습니다")
            
        # 변경 전 값 저장
        old_values = {
            key: getattr(config, key)
            for key in update_data.dict(exclude_unset=True).keys()
        }
        
        # 업데이트
        for key, value in update_data.dict(exclude_unset=True).items():
            setattr(config, key, value)
            
        config.updated_at = datetime.utcnow()
        
        # 변경 이력 기록
        history = FeeConfigHistory(
            config_id=config_id,
            changed_fields={
                key: {
                    "old": str(old_values[key]),
                    "new": str(value)
                }
                for key, value in update_data.dict(exclude_unset=True).items()
            },
            change_reason=reason,
            changed_by=admin_id
        )
        
        self.db.add(history)
        await self.db.commit()
        
        # 캐시 무효화
        await self.invalidate_fee_cache()
        
        # 파트너사에 변경 알림
        if config.partner_id:
            await self.notify_partner_fee_change(config.partner_id, config)
            
        return config
        
    async def get_applicable_configs(
        self,
        transaction_type: TransactionType,
        partner_id: Optional[int] = None,
        user_tier: Optional[str] = None
    ) -> List[FeeConfiguration]:
        """적용 가능한 수수료 설정 조회"""
        # 캐시 확인
        cache_key = f"fee_configs:{transaction_type.value}:{partner_id}:{user_tier}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
            
        # 쿼리 구성
        query = select(FeeConfiguration).where(
            FeeConfiguration.transaction_type == transaction_type,
            FeeConfiguration.is_active == True,
            FeeConfiguration.valid_from <= datetime.utcnow(),
            or_(
                FeeConfiguration.valid_until.is_(None),
                FeeConfiguration.valid_until > datetime.utcnow()
            )
        )
        
        # 파트너 조건
        if partner_id:
            query = query.where(
                or_(
                    FeeConfiguration.partner_id == partner_id,
                    FeeConfiguration.partner_id.is_(None)
                )
            )
        else:
            query = query.where(FeeConfiguration.partner_id.is_(None))
            
        # 사용자 등급 조건
        if user_tier:
            query = query.where(
                or_(
                    FeeConfiguration.user_tier == user_tier,
                    FeeConfiguration.user_tier.is_(None)
                )
            )
            
        # 우선순위 정렬
        query = query.order_by(
            FeeConfiguration.priority.desc(),
            FeeConfiguration.created_at.desc()
        )
        
        result = await self.db.execute(query)
        configs = result.scalars().all()
        
        # 캐시 저장
        await self.redis.setex(
            cache_key,
            self.cache_ttl,
            json.dumps([config.to_dict() for config in configs])
        )
        
        return configs
```

### 4. 파트너별 수수료 관리

#### 4.1 파트너 수수료 서비스
```python
# app/services/fee/partner_fee_service.py
from typing import Dict, List, Optional
from decimal import Decimal

class PartnerFeeService:
    def __init__(self, db_session, fee_manager):
        self.db = db_session
        self.fee_manager = fee_manager
        
    async def set_partner_fee_override(
        self,
        partner_id: int,
        fee_override: PartnerFeeOverrideRequest,
        admin_id: int
    ) -> Dict:
        """파트너별 수수료 오버라이드 설정"""
        partner = await self.db.get(Partner, partner_id)
        if not partner:
            raise ValueError("파트너를 찾을 수 없습니다")
            
        # 기존 설정 비활성화
        await self.deactivate_existing_configs(partner_id, fee_override.transaction_type)
        
        # 새 설정 생성
        configs = []
        
        # 기본 수수료 설정
        if fee_override.base_config:
            base_config = await self.fee_manager.create_fee_config(
                CreateFeeConfigRequest(
                    name=f"{partner.name} - {fee_override.transaction_type.value}",
                    fee_type=fee_override.base_config.fee_type,
                    transaction_type=fee_override.transaction_type,
                    base_percentage=fee_override.base_config.percentage,
                    base_fixed_amount=fee_override.base_config.fixed_amount,
                    min_fee=fee_override.base_config.min_fee,
                    max_fee=fee_override.base_config.max_fee,
                    partner_id=partner_id,
                    priority=100  # 파트너 설정 우선
                ),
                admin_id=admin_id
            )
            configs.append(base_config)
            
        # 등급별 수수료 설정
        if fee_override.tier_configs:
            for tier, tier_config in fee_override.tier_configs.items():
                tier_fee_config = await self.fee_manager.create_fee_config(
                    CreateFeeConfigRequest(
                        name=f"{partner.name} - {tier} 등급",
                        fee_type=FeeType.PERCENTAGE,
                        transaction_type=fee_override.transaction_type,
                        base_percentage=tier_config.percentage,
                        min_fee=tier_config.min_fee,
                        max_fee=tier_config.max_fee,
                        partner_id=partner_id,
                        user_tier=tier,
                        priority=110  # 등급별 설정이 더 우선
                    ),
                    admin_id=admin_id
                )
                configs.append(tier_fee_config)
                
        # 수익 분배 설정 업데이트
        if fee_override.revenue_share:
            partner.revenue_share_percentage = fee_override.revenue_share.percentage
            partner.revenue_share_model = fee_override.revenue_share.model
            await self.db.commit()
            
        return {
            "partner_id": partner_id,
            "configs_created": len(configs),
            "effective_date": datetime.utcnow().isoformat(),
            "configs": [
                {
                    "id": config.id,
                    "name": config.name,
                    "type": config.fee_type.value
                }
                for config in configs
            ]
        }
        
    async def get_partner_fee_summary(
        self,
        partner_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """파트너 수수료 수익 요약"""
        if not start_date:
            start_date = datetime.utcnow().replace(day=1)  # 이번 달 1일
        if not end_date:
            end_date = datetime.utcnow()
            
        # 수수료 수익 집계
        revenue_query = select(
            func.sum(FeeCalculationLog.final_fee).label('total_revenue'),
            func.count(FeeCalculationLog.id).label('transaction_count'),
            func.avg(FeeCalculationLog.final_fee).label('avg_fee')
        ).join(
            Transaction,
            FeeCalculationLog.transaction_id == Transaction.id
        ).join(
            User,
            Transaction.user_id == User.id
        ).where(
            User.partner_id == partner_id,
            FeeCalculationLog.calculated_at >= start_date,
            FeeCalculationLog.calculated_at <= end_date
        )
        
        result = await self.db.execute(revenue_query)
        revenue_data = result.first()
        
        # 거래 유형별 분석
        type_analysis = await self.get_revenue_by_type(
            partner_id, start_date, end_date
        )
        
        # 수익 분배 계산
        partner = await self.db.get(Partner, partner_id)
        total_revenue = revenue_data.total_revenue or Decimal('0')
        
        if partner.revenue_share_model == 'percentage':
            partner_share = total_revenue * (partner.revenue_share_percentage / 100)
            platform_share = total_revenue - partner_share
        else:
            # 고정 수수료 모델
            partner_share = total_revenue
            platform_share = Decimal('0')
            
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_revenue": float(total_revenue),
                "transaction_count": revenue_data.transaction_count or 0,
                "average_fee": float(revenue_data.avg_fee or 0)
            },
            "by_type": type_analysis,
            "revenue_share": {
                "model": partner.revenue_share_model,
                "partner_percentage": float(partner.revenue_share_percentage),
                "partner_share": float(partner_share),
                "platform_share": float(platform_share)
            },
            "trend": await self.get_revenue_trend(partner_id, start_date, end_date)
        }
```

### 5. 에너지 비용 연동 수수료

#### 5.1 에너지 비용 기반 수수료 조정
```python
# app/services/fee/energy_cost_adjuster.py
from typing import Dict, Optional
from decimal import Decimal

class EnergyCostAdjuster:
    def __init__(self, energy_service, price_monitor):
        self.energy_service = energy_service
        self.price_monitor = price_monitor
        
    async def calculate_energy_adjusted_fee(
        self,
        base_fee: Decimal,
        transaction_type: str,
        auto_adjust: bool = True
    ) -> Dict:
        """에너지 비용을 반영한 수수료 계산"""
        # 현재 에너지 가격 조회
        energy_price = await self.price_monitor.get_current_energy_price()
        
        # 거래 유형별 예상 에너지 소비량
        energy_required = await self.energy_service.estimate_energy_cost(
            transaction_type=transaction_type
        )
        
        # 에너지 비용 계산
        energy_cost_trx = energy_required['adjusted_energy_cost'] * energy_price['energy_price_trx']
        energy_cost_usd = energy_cost_trx * energy_price['trx_price_usd']
        
        # 수수료 조정
        adjusted_fee = base_fee
        adjustment_reason = []
        
        if auto_adjust:
            # 에너지 비용이 기본 수수료의 50% 이상인 경우 조정
            if energy_cost_usd > base_fee * Decimal('0.5'):
                adjustment = energy_cost_usd * Decimal('0.2')  # 20% 마진
                adjusted_fee = base_fee + adjustment
                adjustment_reason.append({
                    "type": "energy_cost_high",
                    "adjustment": float(adjustment),
                    "reason": "높은 에너지 비용 반영"
                })
                
            # 네트워크 혼잡도 반영
            if energy_required['congestion_factor'] > 50:
                congestion_adjustment = base_fee * Decimal('0.1')  # 10% 추가
                adjusted_fee += congestion_adjustment
                adjustment_reason.append({
                    "type": "network_congestion",
                    "adjustment": float(congestion_adjustment),
                    "reason": f"네트워크 혼잡도 {energy_required['congestion_factor']}%"
                })
                
        return {
            "base_fee": float(base_fee),
            "energy_cost": {
                "energy_required": energy_required['adjusted_energy_cost'],
                "cost_trx": float(energy_cost_trx),
                "cost_usd": float(energy_cost_usd)
            },
            "adjusted_fee": float(adjusted_fee),
            "adjustments": adjustment_reason,
            "total_cost": float(adjusted_fee + energy_cost_usd),
            "profit_margin": float(adjusted_fee - energy_cost_usd),
            "profit_percentage": float(
                ((adjusted_fee - energy_cost_usd) / adjusted_fee * 100)
                if adjusted_fee > 0 else 0
            )
        }
```

### 6. 관리자 API 엔드포인트

#### 6.1 수수료 관리 API
```python
# app/api/v1/endpoints/admin/fees.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime

router = APIRouter()

@router.get("/admin/fees/current", response_model=CurrentFeesResponse)
async def get_current_fee_settings(
    transaction_type: Optional[TransactionType] = None,
    partner_id: Optional[int] = None,
    current_admin: Admin = Depends(get_current_admin),
    fee_manager: FeeConfigManager = Depends(get_fee_manager)
):
    """현재 활성 수수료 설정 조회"""
    if transaction_type:
        configs = await fee_manager.get_applicable_configs(
            transaction_type=transaction_type,
            partner_id=partner_id
        )
    else:
        # 모든 거래 유형의 설정 조회
        all_configs = {}
        for tx_type in TransactionType:
            all_configs[tx_type.value] = await fee_manager.get_applicable_configs(
                transaction_type=tx_type,
                partner_id=partner_id
            )
            
        return CurrentFeesResponse(
            configs=all_configs,
            summary=await fee_manager.get_fee_summary()
        )
        
    return CurrentFeesResponse(
        configs={transaction_type.value: configs},
        summary=await fee_manager.get_fee_summary()
    )

@router.put("/admin/fees/internal", response_model=FeeConfigResponse)
async def update_internal_fee_rate(
    fee_update: UpdateInternalFeeRequest,
    current_admin: Admin = Depends(get_current_admin),
    fee_manager: FeeConfigManager = Depends(get_fee_manager)
):
    """내부 수수료율 설정"""
    if not current_admin.can_manage_fees:
        raise HTTPException(
            status_code=403,
            detail="수수료 관리 권한이 없습니다"
        )
        
    try:
        # 기본 수수료 설정 업데이트
        config = await fee_manager.update_or_create_base_fee(
            transaction_type=fee_update.transaction_type,
            fee_type=fee_update.fee_type,
            percentage=fee_update.percentage,
            fixed_amount=fee_update.fixed_amount,
            min_fee=fee_update.min_fee,
            max_fee=fee_update.max_fee,
            admin_id=current_admin.id,
            reason=fee_update.reason
        )
        
        # 모든 파트너에게 변경 알림
        await fee_manager.broadcast_fee_change(config)
        
        return FeeConfigResponse.from_orm(config)
        
    except Exception as e:
        logger.error(f"수수료 업데이트 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/fees/energy-cost", response_model=EnergyCostResponse)
async def get_real_time_energy_cost(
    current_admin: Admin = Depends(get_current_admin),
    adjuster: EnergyCostAdjuster = Depends(get_energy_cost_adjuster)
):
    """실시간 에너지 비용 조회"""
    # 각 거래 유형별 에너지 비용 계산
    costs = {}
    
    for tx_type in ['transfer', 'approve']:
        cost_data = await adjuster.calculate_energy_adjusted_fee(
            base_fee=Decimal('2.0'),  # 기본 2 USDT 가정
            transaction_type=tx_type,
            auto_adjust=False
        )
        costs[tx_type] = cost_data
        
    # 에너지 풀 상태
    pool_status = await adjuster.energy_service.check_pool_status()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "energy_pool_status": pool_status,
        "costs_by_type": costs,
        "recommendations": await adjuster.get_fee_recommendations(costs, pool_status)
    }

@router.post("/admin/fees/simulate", response_model=FeeSimulationResponse)
async def simulate_fee_calculation(
    simulation: FeeSimulationRequest,
    current_admin: Admin = Depends(get_current_admin),
    calculator: DynamicFeeCalculator = Depends(get_fee_calculator)
):
    """수수료 계산 시뮬레이션"""
    results = []
    
    for scenario in simulation.scenarios:
        try:
            result = await calculator.calculate_fee(
                transaction_type=scenario.transaction_type,
                amount=scenario.amount,
                user_id=scenario.user_id or simulation.default_user_id,
                partner_id=scenario.partner_id,
                metadata=scenario.metadata
            )
            
            results.append({
                "scenario": scenario.dict(),
                "result": result,
                "success": True
            })
            
        except Exception as e:
            results.append({
                "scenario": scenario.dict(),
                "error": str(e),
                "success": False
            })
            
    return FeeSimulationResponse(
        simulation_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow(),
        results=results,
        summary=calculate_simulation_summary(results)
    )

@router.put("/admin/fees/partner/{partner_id}", response_model=PartnerFeeConfigResponse)
async def update_partner_fee_config(
    partner_id: int,
    fee_config: PartnerFeeConfigRequest,
    current_admin: Admin = Depends(get_current_admin),
    partner_service: PartnerFeeService = Depends(get_partner_fee_service)
):
    """파트너별 수수료 설정"""
    if not current_admin.is_super_admin:
        raise HTTPException(
            status_code=403,
            detail="파트너 수수료 설정은 슈퍼 관리자만 가능합니다"
        )
        
    result = await partner_service.set_partner_fee_override(
        partner_id=partner_id,
        fee_override=fee_config,
        admin_id=current_admin.id
    )
    
    return PartnerFeeConfigResponse(**result)

@router.get("/admin/fees/history", response_model=List[FeeHistoryResponse])
async def get_fee_change_history(
    days: int = Query(30, le=365),
    config_id: Optional[int] = None,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """수수료 변경 이력 조회"""
    since = datetime.utcnow() - timedelta(days=days)
    
    query = select(FeeConfigHistory).where(
        FeeConfigHistory.changed_at >= since
    )
    
    if config_id:
        query = query.where(FeeConfigHistory.config_id == config_id)
        
    query = query.order_by(FeeConfigHistory.changed_at.desc())
    
    result = await db.execute(query)
    history = result.scalars().all()
    
    return [
        FeeHistoryResponse(
            id=record.id,
            config_id=record.config_id,
            changed_fields=record.changed_fields,
            change_reason=record.change_reason,
            changed_by=record.changed_by,
            changed_at=record.changed_at,
            config_name=record.config.name if record.config else None
        )
        for record in history
    ]
```

### 7. 실시간 수수료 모니터링

#### 7.1 수수료 대시보드 데이터
```python
# app/services/fee/monitoring.py
from typing import Dict, List
from datetime import datetime, timedelta
import asyncio

class FeeMonitoringService:
    def __init__(self, db_session, redis_client):
        self.db = db_session
        self.redis = redis_client
        
    async def get_fee_dashboard_data(
        self,
        time_range: str = "24h"
    ) -> Dict:
        """수수료 대시보드 데이터 조회"""
        # 시간 범위 설정
        time_ranges = {
            "1h": timedelta(hours=1),
            "24h": timedelta(days=1),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        
        delta = time_ranges.get(time_range, timedelta(days=1))
        start_time = datetime.utcnow() - delta
        
        # 수수료 수익 통계
        revenue_stats = await self.get_revenue_statistics(start_time)
        
        # 거래 유형별 분석
        type_analysis = await self.get_fee_by_transaction_type(start_time)
        
        # 파트너별 수익
        partner_revenue = await self.get_partner_revenue_ranking(start_time)
        
        # 실시간 추이
        hourly_trend = await self.get_hourly_fee_trend(start_time)
        
        # 수수료율 분포
        fee_distribution = await self.get_fee_rate_distribution(start_time)
        
        return {
            "time_range": time_range,
            "last_updated": datetime.utcnow().isoformat(),
            "revenue_stats": revenue_stats,
            "by_type": type_analysis,
            "partner_ranking": partner_revenue,
            "hourly_trend": hourly_trend,
            "fee_distribution": fee_distribution,
            "alerts": await self.get_fee_alerts()
        }
        
    async def monitor_fee_anomalies(self):
        """수수료 이상 감지"""
        while True:
            try:
                # 최근 1시간 데이터
                recent_fees = await self.get_recent_fee_calculations(hours=1)
                
                # 이상 패턴 감지
                anomalies = []
                
                # 1. 비정상적으로 높은 수수료
                high_fees = [
                    fee for fee in recent_fees
                    if fee.fee_percentage > 10  # 10% 이상
                ]
                if high_fees:
                    anomalies.append({
                        "type": "high_fee_rate",
                        "count": len(high_fees),
                        "examples": high_fees[:5]
                    })
                    
                # 2. 수수료 계산 실패
                failed_calcs = await self.get_failed_calculations(hours=1)
                if failed_calcs:
                    anomalies.append({
                        "type": "calculation_failures",
                        "count": len(failed_calcs),
                        "errors": [fc.error_message for fc in failed_calcs[:5]]
                    })
                    
                # 3. 급격한 수익 변화
                revenue_change = await self.detect_revenue_anomaly()
                if revenue_change:
                    anomalies.append(revenue_change)
                    
                # 알림 발송
                if anomalies:
                    await self.send_anomaly_alerts(anomalies)
                    
                await asyncio.sleep(300)  # 5분마다
                
            except Exception as e:
                logger.error(f"수수료 모니터링 오류: {str(e)}")
                await asyncio.sleep(600)
```

### 8. 사용자 수수료 정보 API

#### 8.1 사용자용 수수료 조회
```python
# app/api/v1/endpoints/fees.py
from fastapi import APIRouter, Depends
from typing import Optional

router = APIRouter()

@router.get("/fees/estimate", response_model=FeeEstimateResponse)
async def estimate_withdrawal_fee(
    amount: Decimal = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    calculator: DynamicFeeCalculator = Depends(get_fee_calculator),
    adjuster: EnergyCostAdjuster = Depends(get_energy_cost_adjuster)
):
    """출금 수수료 견적 (USDT 기준)"""
    # 기본 수수료 계산
    fee_result = await calculator.calculate_fee(
        transaction_type=TransactionType.WITHDRAWAL,
        amount=amount,
        user_id=current_user.id,
        partner_id=current_user.partner_id
    )
    
    # 에너지 비용 반영
    energy_adjusted = await adjuster.calculate_energy_adjusted_fee(
        base_fee=Decimal(str(fee_result['final_fee'])),
        transaction_type='transfer',
        auto_adjust=True
    )
    
    return {
        "withdrawal_amount": float(amount),
        "fee_amount": energy_adjusted['adjusted_fee'],
        "fee_percentage": fee_result['fee_percentage'],
        "net_amount": float(amount - Decimal(str(energy_adjusted['adjusted_fee']))),
        "breakdown": {
            "base_fee": fee_result['calculated_fee'],
            "adjustments": energy_adjusted['adjustments'],
            "final_fee": energy_adjusted['adjusted_fee']
        },
        "energy_info": {
            "included": True,
            "message": "네트워크 수수료는 플랫폼에서 지원합니다"
        }
    }

@router.get("/fees/current", response_model=UserFeeInfoResponse)
async def get_current_fee_rates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """현재 적용되는 수수료율 조회"""
    # 사용자 등급 확인
    user_tier = current_user.tier or "standard"
    
    # 적용 가능한 수수료 설정
    fee_info = {}
    
    for tx_type in TransactionType:
        configs = await get_applicable_configs(
            transaction_type=tx_type,
            partner_id=current_user.partner_id,
            user_tier=user_tier
        )
        
        if configs:
            config = configs[0]  # 최우선 설정
            fee_info[tx_type.value] = {
                "type": config.fee_type.value,
                "rate": float(config.base_percentage) if config.fee_type == FeeType.PERCENTAGE else None,
                "fixed": float(config.base_fixed_amount) if config.fee_type == FeeType.FIXED else None,
                "min": float(config.min_fee) if config.min_fee else None,
                "max": float(config.max_fee) if config.max_fee else None
            }
            
    return {
        "user_tier": user_tier,
        "fee_rates": fee_info,
        "benefits": await get_tier_benefits(user_tier),
        "next_tier": await get_next_tier_info(current_user)
    }

@router.get("/fees/explanation", response_model=FeeExplanationResponse)
async def get_fee_explanation(
    language: str = Query("ko", regex="^(ko|en)$"),
    current_user: User = Depends(get_current_user)
):
    """수수료 체계 설명"""
    explanations = {
        "ko": {
            "title": "DantaroWallet 수수료 안내",
            "sections": [
                {
                    "heading": "수수료 구조",
                    "content": "저희는 투명하고 합리적인 수수료 정책을 운영합니다.",
                    "items": [
                        "출금 수수료: 거래액의 2% (최소 2 USDT)",
                        "내부 이체: 무료",
                        "입금: 무료"
                    ]
                },
                {
                    "heading": "네트워크 수수료",
                    "content": "TRON 네트워크 수수료는 플랫폼에서 지원합니다.",
                    "items": [
                        "에너지(Energy) 비용 플랫폼 부담",
                        "대역폭(Bandwidth) 비용 플랫폼 부담",
                        "사용자 추가 부담 없음"
                    ]
                },
                {
                    "heading": "VIP 혜택",
                    "content": "거래량에 따른 수수료 할인 혜택",
                    "items": [
                        "Bronze (월 $10,000+): 10% 할인",
                        "Silver (월 $50,000+): 20% 할인",
                        "Gold (월 $100,000+): 30% 할인"
                    ]
                }
            ]
        },
        "en": {
            # 영문 설명...
        }
    }
    
    return {
        "language": language,
        "explanation": explanations[language],
        "user_tier_info": {
            "current_tier": current_user.tier,
            "discount_rate": await get_user_discount_rate(current_user)
        },
        "last_updated": "2025-01-07"
    }
```

## 검증 포인트

- [ ] 동적 수수료 계산이 정확한가?
- [ ] 파트너별 수수료 설정이 적용되는가?
- [ ] 사용자 등급별 할인이 적용되는가?
- [ ] 에너지 비용이 수수료에 반영되는가?
- [ ] 수수료 변경 이력이 기록되는가?
- [ ] 실시간 수수료 조정이 가능한가?
- [ ] 수수료 시뮬레이션이 작동하는가?
- [ ] 이상 수수료가 감지되는가?

이 시스템을 통해 유연하고 투명한 수수료 정책을 운영하며, 파트너사별로 차별화된 수수료 전략을 구현할 수 있습니다.