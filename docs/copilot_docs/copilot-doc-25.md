# Copilot 문서 #25: 에너지 풀 고급 관리 시스템

## 목표
파트너사가 보유한 TRX 스테이킹 및 에너지 풀을 실시간으로 모니터링하고, 에너지 부족 상황을 사전에 감지하여 서비스 중단을 방지하는 고급 관리 시스템을 구축합니다.

## 전제 조건
- Copilot 문서 #24 (TronLink 연동)가 완료되어 있어야 합니다.
- 파트너사 외부 지갑이 연동되어 있어야 합니다.
- TronWeb 라이브러리가 설치되어 있어야 합니다.
- Redis 캐시 서버가 구동 중이어야 합니다.

## 🎯 에너지 풀 관리 시스템 구조

### 📊 시스템 아키텍처
```
에너지 풀 고급 관리
├── 🔋 실시간 모니터링
│   ├── 파트너별 에너지 잔량
│   ├── TRX Freeze 상태
│   ├── 대역폭 사용량
│   └── 에너지 회복률
├── 📈 예측 분석
│   ├── 에너지 소진 예상 시간
│   ├── 일일 사용 패턴 분석
│   ├── 피크 시간대 예측
│   └── 필요 TRX 계산
├── 🚨 알림 시스템
│   ├── 임계값 도달 알림
│   ├── 에너지 부족 경고
│   ├── 긴급 충전 알림
│   └── 일일 리포트
├── 💡 대응 정책
│   ├── 자동 대응 규칙
│   ├── 수동 개입 가이드
│   ├── 대체 출금 옵션
│   └── 에너지 절약 모드
└── 📊 분석 대시보드
    ├── 에너지 사용 통계
    ├── 비용 분석
    ├── 효율성 지표
    └── 최적화 제안
```

## 🛠️ 구현 단계

### Phase 1: 에너지 모니터링 모델 (1일)

#### 1.1 에너지 풀 상태 모델
```python
# app/models/energy_pool.py
"""에너지 풀 관리 관련 모델"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base
import enum

class EnergyStatus(enum.Enum):
    """에너지 상태"""
    SUFFICIENT = "sufficient"      # 충분
    WARNING = "warning"           # 경고
    CRITICAL = "critical"         # 위험
    DEPLETED = "depleted"        # 고갈

class EnergyAlertType(enum.Enum):
    """알림 유형"""
    THRESHOLD_WARNING = "threshold_warning"
    THRESHOLD_CRITICAL = "threshold_critical"
    DEPLETION_IMMINENT = "depletion_imminent"
    RECOVERY_NEEDED = "recovery_needed"
    DAILY_REPORT = "daily_report"

class PartnerEnergyPool(Base):
    """파트너사 에너지 풀 상태"""
    __tablename__ = "partner_energy_pools"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, nullable=False, unique=True, comment="파트너사 ID")
    wallet_address = Column(String(42), nullable=False, comment="모니터링 지갑 주소")
    
    # 에너지 상태
    total_energy = Column(Numeric(20, 0), default=0, comment="총 에너지")
    available_energy = Column(Numeric(20, 0), default=0, comment="사용 가능 에너지")
    used_energy = Column(Numeric(20, 0), default=0, comment="사용된 에너지")
    energy_limit = Column(Numeric(20, 0), default=0, comment="에너지 한도")
    
    # 대역폭 상태
    total_bandwidth = Column(Numeric(20, 0), default=0, comment="총 대역폭")
    available_bandwidth = Column(Numeric(20, 0), default=0, comment="사용 가능 대역폭")
    
    # TRX 스테이킹 정보
    frozen_trx_amount = Column(Numeric(18, 6), default=0, comment="동결된 TRX")
    frozen_for_energy = Column(Numeric(18, 6), default=0, comment="에너지용 동결 TRX")
    frozen_for_bandwidth = Column(Numeric(18, 6), default=0, comment="대역폭용 동결 TRX")
    
    # 상태 및 예측
    status = Column(Enum(EnergyStatus), default=EnergyStatus.SUFFICIENT, comment="현재 상태")
    depletion_estimated_at = Column(DateTime(timezone=True), comment="예상 고갈 시간")
    daily_average_usage = Column(Numeric(20, 0), default=0, comment="일평균 사용량")
    peak_usage_hour = Column(Integer, comment="피크 사용 시간")
    
    # 임계값 설정
    warning_threshold = Column(Integer, default=30, comment="경고 임계값 (%)")
    critical_threshold = Column(Integer, default=10, comment="위험 임계값 (%)")
    auto_response_enabled = Column(Boolean, default=True, comment="자동 대응 활성화")
    
    # 메타데이터
    last_checked_at = Column(DateTime(timezone=True), comment="마지막 확인 시간")
    last_alert_sent_at = Column(DateTime(timezone=True), comment="마지막 알림 시간")
    metrics_history = Column(JSON, comment="과거 지표 (최근 24시간)")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    alerts = relationship("EnergyAlert", back_populates="energy_pool")
    usage_logs = relationship("EnergyUsageLog", back_populates="energy_pool")

class EnergyAlert(Base):
    """에너지 알림 이력"""
    __tablename__ = "energy_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    energy_pool_id = Column(Integer, nullable=False, comment="에너지 풀 ID")
    alert_type = Column(Enum(EnergyAlertType), nullable=False, comment="알림 유형")
    
    # 알림 내용
    severity = Column(String(20), nullable=False, comment="심각도")
    title = Column(String(200), nullable=False, comment="알림 제목")
    message = Column(String(1000), nullable=False, comment="알림 내용")
    
    # 상태 정보
    energy_percentage = Column(Integer, comment="에너지 잔량 (%)")
    available_energy = Column(Numeric(20, 0), comment="사용 가능 에너지")
    estimated_hours_remaining = Column(Integer, comment="예상 잔여 시간")
    
    # 알림 전송 정보
    sent_via = Column(JSON, comment="전송 채널 (email, telegram, webhook)")
    sent_to = Column(JSON, comment="수신자 목록")
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged = Column(Boolean, default=False, comment="확인 여부")
    acknowledged_at = Column(DateTime(timezone=True), comment="확인 시간")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    energy_pool = relationship("PartnerEnergyPool", back_populates="alerts")

class EnergyUsageLog(Base):
    """에너지 사용 로그"""
    __tablename__ = "energy_usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    energy_pool_id = Column(Integer, nullable=False, comment="에너지 풀 ID")
    
    # 사용 정보
    transaction_type = Column(String(50), nullable=False, comment="트랜잭션 유형")
    transaction_hash = Column(String(66), comment="트랜잭션 해시")
    energy_consumed = Column(Numeric(20, 0), nullable=False, comment="소비된 에너지")
    bandwidth_consumed = Column(Numeric(20, 0), default=0, comment="소비된 대역폭")
    
    # 비용 정보
    energy_unit_price = Column(Numeric(10, 6), comment="에너지 단가 (TRX)")
    total_cost = Column(Numeric(18, 6), comment="총 비용 (TRX)")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    energy_pool = relationship("PartnerEnergyPool", back_populates="usage_logs")
```

### Phase 2: 에너지 모니터링 서비스 (2일)

#### 2.1 에너지 모니터링 서비스
```python
# app/services/energy/energy_monitor_service.py
"""에너지 풀 모니터링 서비스"""
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from tronpy import Tron
import redis.asyncio as redis

from app.models.partner_wallet import PartnerWallet
from app.models.energy_pool import (
    PartnerEnergyPool, EnergyStatus, EnergyAlert, 
    EnergyAlertType, EnergyUsageLog
)
from app.core.config import settings
from app.utils.logger import logger
from app.services.notification.alert_service import AlertService

class EnergyMonitorService:
    """에너지 풀 실시간 모니터링"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tron = Tron(network=settings.TRON_NETWORK)
        self.redis = redis.from_url(settings.REDIS_URL)
        self.alert_service = AlertService(db)
    
    async def check_partner_energy(self, partner_id: int) -> Dict:
        """파트너사 에너지 상태 확인"""
        try:
            # 파트너 에너지 풀 정보 조회
            energy_pool = await self.db.query(PartnerEnergyPool).filter(
                PartnerEnergyPool.partner_id == partner_id
            ).first()
            
            if not energy_pool:
                # 초기화
                energy_pool = await self._initialize_energy_pool(partner_id)
            
            # 블록체인에서 실시간 정보 조회
            account_info = self.tron.get_account_resource(energy_pool.wallet_address)
            
            # 에너지 정보 업데이트
            energy_pool.total_energy = account_info.get('EnergyLimit', 0)
            energy_pool.available_energy = account_info.get('EnergyUsed', 0)
            energy_pool.used_energy = energy_pool.total_energy - energy_pool.available_energy
            
            # 대역폭 정보 업데이트
            energy_pool.total_bandwidth = account_info.get('NetLimit', 0)
            energy_pool.available_bandwidth = account_info.get('NetUsed', 0)
            
            # 스테이킹 정보 업데이트
            frozen_info = await self._get_frozen_info(energy_pool.wallet_address)
            energy_pool.frozen_trx_amount = frozen_info['total']
            energy_pool.frozen_for_energy = frozen_info['energy']
            energy_pool.frozen_for_bandwidth = frozen_info['bandwidth']
            
            # 상태 분석
            energy_percentage = self._calculate_energy_percentage(energy_pool)
            energy_pool.status = self._determine_status(energy_percentage)
            
            # 예측 분석
            prediction = await self._predict_depletion(energy_pool)
            energy_pool.depletion_estimated_at = prediction['estimated_depletion']
            energy_pool.daily_average_usage = prediction['daily_average']
            
            # 캐시 업데이트
            await self._update_cache(partner_id, energy_pool)
            
            # 임계값 체크 및 알림
            await self._check_thresholds(energy_pool, energy_percentage)
            
            # 저장
            energy_pool.last_checked_at = datetime.utcnow()
            await self.db.commit()
            
            return {
                "partner_id": partner_id,
                "status": energy_pool.status.value,
                "energy": {
                    "total": energy_pool.total_energy,
                    "available": energy_pool.available_energy,
                    "used": energy_pool.used_energy,
                    "percentage": energy_percentage
                },
                "bandwidth": {
                    "total": energy_pool.total_bandwidth,
                    "available": energy_pool.available_bandwidth
                },
                "staking": {
                    "total_frozen": float(energy_pool.frozen_trx_amount),
                    "for_energy": float(energy_pool.frozen_for_energy),
                    "for_bandwidth": float(energy_pool.frozen_for_bandwidth)
                },
                "prediction": {
                    "depletion_time": energy_pool.depletion_estimated_at,
                    "hours_remaining": prediction.get('hours_remaining'),
                    "daily_average_usage": float(energy_pool.daily_average_usage)
                },
                "last_checked": energy_pool.last_checked_at
            }
            
        except Exception as e:
            logger.error(f"Failed to check partner energy: {e}")
            raise
    
    async def _initialize_energy_pool(self, partner_id: int) -> PartnerEnergyPool:
        """에너지 풀 초기화"""
        # 파트너의 주 지갑 조회
        wallet = await self.db.query(PartnerWallet).filter(
            PartnerWallet.partner_id == partner_id,
            PartnerWallet.is_primary == True
        ).first()
        
        if not wallet:
            raise ValueError(f"No primary wallet found for partner {partner_id}")
        
        energy_pool = PartnerEnergyPool(
            partner_id=partner_id,
            wallet_address=wallet.wallet_address
        )
        
        self.db.add(energy_pool)
        await self.db.commit()
        await self.db.refresh(energy_pool)
        
        return energy_pool
    
    async def _get_frozen_info(self, address: str) -> Dict[str, Decimal]:
        """동결된 TRX 정보 조회"""
        account = self.tron.get_account(address)
        frozen_info = {
            'total': Decimal('0'),
            'energy': Decimal('0'),
            'bandwidth': Decimal('0')
        }
        
        # V2 동결 정보
        if 'account_resource' in account:
            resource = account['account_resource']
            if 'frozen_balance_for_energy' in resource:
                frozen_info['energy'] = Decimal(str(
                    resource['frozen_balance_for_energy'].get('frozen_balance', 0) / 1e6
                ))
        
        # 총 동결량 계산
        frozen_info['total'] = frozen_info['energy'] + frozen_info['bandwidth']
        
        return frozen_info
    
    def _calculate_energy_percentage(self, energy_pool: PartnerEnergyPool) -> int:
        """에너지 잔량 백분율 계산"""
        if energy_pool.total_energy == 0:
            return 0
        
        percentage = (energy_pool.available_energy / energy_pool.total_energy) * 100
        return int(percentage)
    
    def _determine_status(self, percentage: int) -> EnergyStatus:
        """에너지 상태 결정"""
        if percentage >= 50:
            return EnergyStatus.SUFFICIENT
        elif percentage >= 30:
            return EnergyStatus.WARNING
        elif percentage >= 10:
            return EnergyStatus.CRITICAL
        else:
            return EnergyStatus.DEPLETED
    
    async def _predict_depletion(self, energy_pool: PartnerEnergyPool) -> Dict:
        """에너지 고갈 예측"""
        # 최근 24시간 사용량 조회
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        result = await self.db.query(
            func.sum(EnergyUsageLog.energy_consumed)
        ).filter(
            EnergyUsageLog.energy_pool_id == energy_pool.id,
            EnergyUsageLog.created_at >= yesterday
        ).scalar()
        
        daily_usage = result or 0
        hourly_average = daily_usage / 24 if daily_usage > 0 else 0
        
        # 고갈 예상 시간 계산
        if hourly_average > 0 and energy_pool.available_energy > 0:
            hours_remaining = float(energy_pool.available_energy) / float(hourly_average)
            estimated_depletion = datetime.utcnow() + timedelta(hours=hours_remaining)
        else:
            hours_remaining = None
            estimated_depletion = None
        
        return {
            'daily_average': daily_usage,
            'hourly_average': hourly_average,
            'hours_remaining': hours_remaining,
            'estimated_depletion': estimated_depletion
        }
    
    async def _check_thresholds(
        self, 
        energy_pool: PartnerEnergyPool, 
        percentage: int
    ) -> None:
        """임계값 체크 및 알림 발송"""
        # 마지막 알림으로부터 충분한 시간이 지났는지 확인
        if energy_pool.last_alert_sent_at:
            time_since_last_alert = datetime.utcnow() - energy_pool.last_alert_sent_at
            if time_since_last_alert < timedelta(hours=1):
                return
        
        alert_type = None
        severity = "info"
        
        if percentage <= energy_pool.critical_threshold:
            alert_type = EnergyAlertType.THRESHOLD_CRITICAL
            severity = "critical"
        elif percentage <= energy_pool.warning_threshold:
            alert_type = EnergyAlertType.THRESHOLD_WARNING
            severity = "warning"
        
        if alert_type:
            # 알림 생성
            alert = EnergyAlert(
                energy_pool_id=energy_pool.id,
                alert_type=alert_type,
                severity=severity,
                title=f"에너지 풀 {severity.upper()} 알림",
                message=f"현재 에너지 잔량이 {percentage}%입니다. 즉시 확인이 필요합니다.",
                energy_percentage=percentage,
                available_energy=energy_pool.available_energy,
                estimated_hours_remaining=self._predict_depletion(energy_pool).get('hours_remaining')
            )
            
            self.db.add(alert)
            
            # 알림 발송
            await self.alert_service.send_energy_alert(
                partner_id=energy_pool.partner_id,
                alert=alert
            )
            
            energy_pool.last_alert_sent_at = datetime.utcnow()
    
    async def _update_cache(
        self, 
        partner_id: int, 
        energy_pool: PartnerEnergyPool
    ) -> None:
        """Redis 캐시 업데이트"""
        cache_key = f"energy:partner:{partner_id}"
        cache_data = {
            "status": energy_pool.status.value,
            "available_energy": str(energy_pool.available_energy),
            "percentage": self._calculate_energy_percentage(energy_pool),
            "last_checked": energy_pool.last_checked_at.isoformat()
        }
        
        await self.redis.setex(
            cache_key,
            300,  # 5분 TTL
            json.dumps(cache_data)
        )
```

#### 2.2 에너지 사용량 추적 서비스
```python
# app/services/energy/usage_tracker_service.py
"""에너지 사용량 추적 서비스"""
from typing import Dict, List
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.energy_pool import EnergyUsageLog, PartnerEnergyPool
from app.utils.logger import logger

class EnergyUsageTracker:
    """에너지 사용량 추적 및 분석"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_energy_usage(
        self,
        partner_id: int,
        transaction_type: str,
        energy_consumed: int,
        bandwidth_consumed: int = 0,
        tx_hash: Optional[str] = None
    ) -> None:
        """에너지 사용 로그 기록"""
        try:
            # 에너지 풀 조회
            energy_pool = await self.db.query(PartnerEnergyPool).filter(
                PartnerEnergyPool.partner_id == partner_id
            ).first()
            
            if not energy_pool:
                logger.warning(f"Energy pool not found for partner {partner_id}")
                return
            
            # 현재 에너지 가격 (SUN 단위)
            energy_price = await self._get_current_energy_price()
            total_cost = Decimal(str(energy_consumed * energy_price / 1e6))
            
            # 로그 생성
            usage_log = EnergyUsageLog(
                energy_pool_id=energy_pool.id,
                transaction_type=transaction_type,
                transaction_hash=tx_hash,
                energy_consumed=energy_consumed,
                bandwidth_consumed=bandwidth_consumed,
                energy_unit_price=energy_price,
                total_cost=total_cost
            )
            
            self.db.add(usage_log)
            await self.db.commit()
            
            # 일평균 업데이트
            await self._update_daily_average(energy_pool.id)
            
        except Exception as e:
            logger.error(f"Failed to log energy usage: {e}")
            raise
    
    async def get_usage_statistics(
        self,
        partner_id: int,
        period_days: int = 7
    ) -> Dict:
        """사용량 통계 조회"""
        try:
            energy_pool = await self.db.query(PartnerEnergyPool).filter(
                PartnerEnergyPool.partner_id == partner_id
            ).first()
            
            if not energy_pool:
                return {}
            
            start_date = datetime.utcnow() - timedelta(days=period_days)
            
            # 기간별 통계
            stats = await self.db.query(
                func.date(EnergyUsageLog.created_at).label('date'),
                func.sum(EnergyUsageLog.energy_consumed).label('total_energy'),
                func.sum(EnergyUsageLog.bandwidth_consumed).label('total_bandwidth'),
                func.sum(EnergyUsageLog.total_cost).label('total_cost'),
                func.count(EnergyUsageLog.id).label('transaction_count')
            ).filter(
                EnergyUsageLog.energy_pool_id == energy_pool.id,
                EnergyUsageLog.created_at >= start_date
            ).group_by(
                func.date(EnergyUsageLog.created_at)
            ).all()
            
            # 트랜잭션 유형별 통계
            type_stats = await self.db.query(
                EnergyUsageLog.transaction_type,
                func.sum(EnergyUsageLog.energy_consumed).label('total_energy'),
                func.count(EnergyUsageLog.id).label('count')
            ).filter(
                EnergyUsageLog.energy_pool_id == energy_pool.id,
                EnergyUsageLog.created_at >= start_date
            ).group_by(
                EnergyUsageLog.transaction_type
            ).all()
            
            # 시간대별 패턴 분석
            hourly_stats = await self.db.query(
                func.extract('hour', EnergyUsageLog.created_at).label('hour'),
                func.avg(EnergyUsageLog.energy_consumed).label('avg_energy')
            ).filter(
                EnergyUsageLog.energy_pool_id == energy_pool.id,
                EnergyUsageLog.created_at >= start_date
            ).group_by(
                func.extract('hour', EnergyUsageLog.created_at)
            ).all()
            
            return {
                "period_days": period_days,
                "daily_stats": [
                    {
                        "date": stat.date.isoformat(),
                        "total_energy": int(stat.total_energy or 0),
                        "total_bandwidth": int(stat.total_bandwidth or 0),
                        "total_cost": float(stat.total_cost or 0),
                        "transaction_count": stat.transaction_count
                    }
                    for stat in stats
                ],
                "type_breakdown": [
                    {
                        "type": stat.transaction_type,
                        "total_energy": int(stat.total_energy or 0),
                        "count": stat.count
                    }
                    for stat in type_stats
                ],
                "hourly_pattern": [
                    {
                        "hour": int(stat.hour),
                        "avg_energy": float(stat.avg_energy or 0)
                    }
                    for stat in hourly_stats
                ],
                "summary": {
                    "total_energy_consumed": sum(s.total_energy or 0 for s in stats),
                    "total_cost": float(sum(s.total_cost or 0 for s in stats)),
                    "avg_daily_energy": sum(s.total_energy or 0 for s in stats) / period_days,
                    "peak_hour": max(hourly_stats, key=lambda x: x.avg_energy).hour if hourly_stats else None
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get usage statistics: {e}")
            raise
    
    async def _get_current_energy_price(self) -> Decimal:
        """현재 에너지 가격 조회 (SUN)"""
        # TODO: 실제 TRON 네트워크에서 에너지 가격 조회
        # 임시로 고정값 사용 (280 SUN per energy)
        return Decimal("280")
    
    async def _update_daily_average(self, energy_pool_id: int) -> None:
        """일평균 사용량 업데이트"""
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        result = await self.db.query(
            func.avg(EnergyUsageLog.energy_consumed)
        ).filter(
            EnergyUsageLog.energy_pool_id == energy_pool_id,
            EnergyUsageLog.created_at >= yesterday
        ).scalar()
        
        if result:
            await self.db.query(PartnerEnergyPool).filter(
                PartnerEnergyPool.id == energy_pool_id
            ).update({
                PartnerEnergyPool.daily_average_usage: result
            })
```

### Phase 3: 에너지 관리 API (1일)

#### 3.1 에너지 모니터링 API
```python
# app/api/v1/endpoints/partner/energy.py
"""파트너 에너지 관리 API"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_partner
from app.models.partner import Partner
from app.schemas.energy import (
    EnergyStatusResponse,
    EnergyUsageStats,
    EnergyAlertResponse,
    EnergyPolicyUpdate
)
from app.services.energy.energy_monitor_service import EnergyMonitorService
from app.services.energy.usage_tracker_service import EnergyUsageTracker

router = APIRouter(tags=["파트너 에너지 관리"])

@router.get("/status", response_model=EnergyStatusResponse)
async def get_energy_status(
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """현재 에너지 상태 조회"""
    monitor_service = EnergyMonitorService(db)
    
    try:
        status = await monitor_service.check_partner_energy(current_partner.id)
        return EnergyStatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/usage/stats", response_model=EnergyUsageStats)
async def get_usage_statistics(
    period_days: int = Query(7, ge=1, le=90, description="조회 기간 (일)"),
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """에너지 사용량 통계 조회"""
    tracker_service = EnergyUsageTracker(db)
    
    try:
        stats = await tracker_service.get_usage_statistics(
            partner_id=current_partner.id,
            period_days=period_days
        )
        return EnergyUsageStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts", response_model=List[EnergyAlertResponse])
async def get_energy_alerts(
    start_date: Optional[datetime] = Query(None, description="시작일"),
    end_date: Optional[datetime] = Query(None, description="종료일"),
    acknowledged: Optional[bool] = Query(None, description="확인 여부"),
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """에너지 알림 이력 조회"""
    from app.models.energy_pool import EnergyAlert, PartnerEnergyPool
    
    # 기본 기간 설정 (최근 7일)
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=7)
    if not end_date:
        end_date = datetime.utcnow()
    
    # 파트너 에너지 풀 조회
    energy_pool = await db.query(PartnerEnergyPool).filter(
        PartnerEnergyPool.partner_id == current_partner.id
    ).first()
    
    if not energy_pool:
        return []
    
    # 알림 조회
    query = db.query(EnergyAlert).filter(
        EnergyAlert.energy_pool_id == energy_pool.id,
        EnergyAlert.created_at.between(start_date, end_date)
    )
    
    if acknowledged is not None:
        query = query.filter(EnergyAlert.acknowledged == acknowledged)
    
    alerts = await query.order_by(EnergyAlert.created_at.desc()).all()
    
    return [EnergyAlertResponse.from_orm(alert) for alert in alerts]

@router.put("/policy", response_model=Dict)
async def update_energy_policy(
    policy: EnergyPolicyUpdate,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """에너지 관리 정책 업데이트"""
    from app.models.energy_pool import PartnerEnergyPool
    
    energy_pool = await db.query(PartnerEnergyPool).filter(
        PartnerEnergyPool.partner_id == current_partner.id
    ).first()
    
    if not energy_pool:
        raise HTTPException(status_code=404, detail="Energy pool not found")
    
    # 정책 업데이트
    if policy.warning_threshold is not None:
        energy_pool.warning_threshold = policy.warning_threshold
    if policy.critical_threshold is not None:
        energy_pool.critical_threshold = policy.critical_threshold
    if policy.auto_response_enabled is not None:
        energy_pool.auto_response_enabled = policy.auto_response_enabled
    
    await db.commit()
    
    return {
        "success": True,
        "message": "Energy policy updated successfully",
        "policy": {
            "warning_threshold": energy_pool.warning_threshold,
            "critical_threshold": energy_pool.critical_threshold,
            "auto_response_enabled": energy_pool.auto_response_enabled
        }
    }

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    current_partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """알림 확인 처리"""
    from app.models.energy_pool import EnergyAlert, PartnerEnergyPool
    
    # 알림 조회 및 권한 확인
    alert = await db.query(EnergyAlert).join(
        PartnerEnergyPool
    ).filter(
        EnergyAlert.id == alert_id,
        PartnerEnergyPool.partner_id == current_partner.id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.acknowledged = True
    alert.acknowledged_at = datetime.utcnow()
    await db.commit()
    
    return {"success": True, "message": "Alert acknowledged"}
```

### Phase 4: 에너지 대시보드 UI (1일)

#### 4.1 에너지 모니터링 대시보드
```typescript
// frontend/components/energy/EnergyDashboard.tsx
import React, { useState, useEffect } from 'react';
import { Card, Alert, Progress } from '@/components/ui';
import { Battery, Zap, AlertTriangle, TrendingUp } from 'lucide-react';
import { useEnergyMonitor } from '@/hooks/useEnergyMonitor';
import { formatNumber, formatPercentage } from '@/utils/format';
import { EnergyChart } from './EnergyChart';
import { EnergyAlerts } from './EnergyAlerts';

export const EnergyDashboard: React.FC = () => {
  const { status, usage, alerts, loading, error, refresh } = useEnergyMonitor();

  // 자동 새로고침 (30초마다)
  useEffect(() => {
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [refresh]);

  if (loading) return <div>Loading energy data...</div>;
  if (error) return <Alert variant="error">{error}</Alert>;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'sufficient': return 'green';
      case 'warning': return 'yellow';
      case 'critical': return 'red';
      case 'depleted': return 'gray';
      default: return 'blue';
    }
  };

  const statusColor = getStatusColor(status?.status || 'unknown');

  return (
    <div className="space-y-6">
      {/* 상태 개요 */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">에너지 풀 상태</h2>
          <Battery 
            className={`w-8 h-8 text-${statusColor}-500`} 
            fill={status?.energy?.percentage > 50 ? 'currentColor' : 'none'}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* 에너지 상태 */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-600">에너지</span>
              <span className={`font-bold text-${statusColor}-600`}>
                {status?.status?.toUpperCase()}
              </span>
            </div>
            <Progress 
              value={status?.energy?.percentage || 0} 
              max={100}
              className={`bg-${statusColor}-100`}
            />
            <div className="mt-2 text-sm text-gray-600">
              {formatNumber(status?.energy?.available || 0)} / 
              {formatNumber(status?.energy?.total || 0)}
            </div>
          </div>

          {/* 대역폭 상태 */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-600">대역폭</span>
              <Zap className="w-5 h-5 text-blue-500" />
            </div>
            <Progress 
              value={(status?.bandwidth?.available / status?.bandwidth?.total) * 100 || 0} 
              max={100}
              className="bg-blue-100"
            />
            <div className="mt-2 text-sm text-gray-600">
              {formatNumber(status?.bandwidth?.available || 0)} / 
              {formatNumber(status?.bandwidth?.total || 0)}
            </div>
          </div>

          {/* 스테이킹 정보 */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-600">동결 TRX</span>
              <TrendingUp className="w-5 h-5 text-purple-500" />
            </div>
            <div className="text-2xl font-bold">
              {formatNumber(status?.staking?.total_frozen || 0)} TRX
            </div>
            <div className="mt-2 text-sm text-gray-600">
              에너지: {formatNumber(status?.staking?.for_energy || 0)} TRX
            </div>
          </div>
        </div>

        {/* 예측 정보 */}
        {status?.prediction?.depletion_time && (
          <Alert variant="warning" className="mt-4">
            <AlertTriangle className="w-4 h-4" />
            <div>
              <strong>예상 고갈 시간:</strong> {' '}
              {new Date(status.prediction.depletion_time).toLocaleString()}
              ({status.prediction.hours_remaining?.toFixed(1)}시간 후)
            </div>
          </Alert>
        )}
      </Card>

      {/* 사용량 차트 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">에너지 사용 추이</h3>
        <EnergyChart data={usage?.daily_stats || []} />
      </Card>

      {/* 알림 목록 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">최근 알림</h3>
        <EnergyAlerts alerts={alerts || []} />
      </Card>

      {/* 정책 설정 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">에너지 관리 정책</h3>
        <EnergyPolicySettings 
          currentPolicy={{
            warning_threshold: status?.policy?.warning_threshold || 30,
            critical_threshold: status?.policy?.critical_threshold || 10,
            auto_response_enabled: status?.policy?.auto_response_enabled || true
          }}
          onUpdate={(policy) => console.log('Update policy:', policy)}
        />
      </Card>
    </div>
  );
};
```

## 🔧 데이터베이스 마이그레이션

```sql
-- 파트너 에너지 풀 테이블
CREATE TABLE partner_energy_pools (
    id SERIAL PRIMARY KEY,
    partner_id INTEGER NOT NULL UNIQUE REFERENCES partners(id),
    wallet_address VARCHAR(42) NOT NULL,
    
    -- 에너지 상태
    total_energy NUMERIC(20,0) DEFAULT 0,
    available_energy NUMERIC(20,0) DEFAULT 0,
    used_energy NUMERIC(20,0) DEFAULT 0,
    energy_limit NUMERIC(20,0) DEFAULT 0,
    
    -- 대역폭 상태
    total_bandwidth NUMERIC(20,0) DEFAULT 0,
    available_bandwidth NUMERIC(20,0) DEFAULT 0,
    
    -- TRX 스테이킹
    frozen_trx_amount DECIMAL(18,6) DEFAULT 0,
    frozen_for_energy DECIMAL(18,6) DEFAULT 0,
    frozen_for_bandwidth DECIMAL(18,6) DEFAULT 0,
    
    -- 상태 및 예측
    status VARCHAR(20) DEFAULT 'sufficient',
    depletion_estimated_at TIMESTAMP WITH TIME ZONE,
    daily_average_usage NUMERIC(20,0) DEFAULT 0,
    peak_usage_hour INTEGER,
    
    -- 임계값 설정
    warning_threshold INTEGER DEFAULT 30,
    critical_threshold INTEGER DEFAULT 10,
    auto_response_enabled BOOLEAN DEFAULT TRUE,
    
    -- 메타데이터
    last_checked_at TIMESTAMP WITH TIME ZONE,
    last_alert_sent_at TIMESTAMP WITH TIME ZONE,
    metrics_history JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_partner_energy_pools_partner_id (partner_id),
    INDEX idx_partner_energy_pools_status (status)
);

-- 에너지 알림 테이블
CREATE TABLE energy_alerts (
    id SERIAL PRIMARY KEY,
    energy_pool_id INTEGER NOT NULL REFERENCES partner_energy_pools(id),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message VARCHAR(1000) NOT NULL,
    energy_percentage INTEGER,
    available_energy NUMERIC(20,0),
    estimated_hours_remaining INTEGER,
    sent_via JSONB,
    sent_to JSONB,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_energy_alerts_pool_id (energy_pool_id),
    INDEX idx_energy_alerts_type (alert_type),
    INDEX idx_energy_alerts_acknowledged (acknowledged)
);

-- 에너지 사용 로그 테이블
CREATE TABLE energy_usage_logs (
    id SERIAL PRIMARY KEY,
    energy_pool_id INTEGER NOT NULL REFERENCES partner_energy_pools(id),
    transaction_type VARCHAR(50) NOT NULL,
    transaction_hash VARCHAR(66),
    energy_consumed NUMERIC(20,0) NOT NULL,
    bandwidth_consumed NUMERIC(20,0) DEFAULT 0,
    energy_unit_price DECIMAL(10,6),
    total_cost DECIMAL(18,6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_energy_usage_logs_pool_id (energy_pool_id),
    INDEX idx_energy_usage_logs_created_at (created_at),
    INDEX idx_energy_usage_logs_tx_type (transaction_type)
);
```

## ✅ 검증 포인트

- [ ] 파트너사별 에너지 상태가 실시간 조회되는가?
- [ ] 에너지 고갈 예측이 정확하게 계산되는가?
- [ ] 임계값 도달 시 알림이 발송되는가?
- [ ] 사용량 통계가 정확히 집계되는가?
- [ ] 시간대별 패턴 분석이 작동하는가?
- [ ] 대시보드에서 실시간 모니터링이 가능한가?
- [ ] 정책 설정 변경이 즉시 반영되는가?
- [ ] 알림 확인 처리가 정상 작동하는가?

## 🎉 기대 효과

1. **사전 예방**: 에너지 고갈을 미리 예측하여 대응
2. **비용 최적화**: 사용 패턴 분석을 통한 효율적 관리
3. **서비스 안정성**: 실시간 모니터링으로 중단 방지
4. **투명성**: 파트너사가 직접 에너지 상태 확인
5. **자동화**: 임계값 기반 자동 알림 시스템

이 시스템을 통해 파트너사는 자신의 에너지 풀을 효과적으로 관리하고, 서비스 중단 없이 안정적으로 운영할 수 있습니다.