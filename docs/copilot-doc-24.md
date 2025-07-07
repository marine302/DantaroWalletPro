# Copilot 문서 #24: 트론 에너지 풀 관리 시스템 구현

## 목표
TRON 네트워크의 에너지 풀을 효율적으로 관리하여 사용자의 USDT 출금 시 네트워크 수수료를 본사가 대신 지불하는 시스템을 구축합니다.

## 상세 지시사항

### 1. 에너지 풀 모델 확장

#### 1.1 에너지 풀 상세 모델
```python
# app/models/energy_pool.py
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from decimal import Decimal
import enum

class EnergyPoolStatus(enum.Enum):
    ACTIVE = "active"
    LOW = "low"  # 20% 미만
    CRITICAL = "critical"  # 10% 미만
    DEPLETED = "depleted"  # 0%
    MAINTENANCE = "maintenance"

class EnergyPoolModel(Base):
    __tablename__ = "energy_pools"
    
    id = Column(Integer, primary_key=True)
    pool_name = Column(String(100), nullable=False)
    owner_address = Column(String(34), nullable=False)  # TRON 주소
    
    # TRX 동결 정보
    frozen_trx = Column(Numeric(20, 6), default=0)  # 동결된 TRX
    total_energy = Column(Integer, default=0)  # 총 에너지
    available_energy = Column(Integer, default=0)  # 사용 가능 에너지
    used_energy = Column(Integer, default=0)  # 사용된 에너지
    
    # 상태 및 임계값
    status = Column(Enum(EnergyPoolStatus), default=EnergyPoolStatus.ACTIVE)
    low_threshold = Column(Integer, default=20)  # 낮음 경고 임계값 (%)
    critical_threshold = Column(Integer, default=10)  # 위급 경고 임계값 (%)
    
    # 자동 관리 설정
    auto_refill = Column(Boolean, default=False)  # 자동 충전 활성화
    auto_refill_amount = Column(Numeric(20, 6), default=10000)  # 자동 충전 금액
    auto_refill_trigger = Column(Integer, default=15)  # 자동 충전 트리거 (%)
    
    # 통계
    daily_consumption = Column(JSON, default=dict)  # 일별 소비량
    peak_usage_hours = Column(JSON, default=dict)  # 피크 사용 시간대
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    last_refilled_at = Column(DateTime)
    last_checked_at = Column(DateTime)
    
    # 관계
    usage_logs = relationship("EnergyUsageLog", back_populates="pool")
    price_history = relationship("EnergyPriceHistory", back_populates="pool")

class EnergyUsageLog(Base):
    __tablename__ = "energy_usage_logs"
    
    id = Column(Integer, primary_key=True)
    pool_id = Column(Integer, ForeignKey("energy_pools.id"))
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    
    # 사용 정보
    energy_consumed = Column(Integer, nullable=False)  # 소비된 에너지
    transaction_type = Column(String(50))  # 거래 유형 (transfer, approve 등)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # 비용 계산
    energy_price = Column(Numeric(20, 8))  # 에너지 단가 (TRX/Energy)
    actual_cost = Column(Numeric(20, 6))  # 실제 비용 (TRX)
    
    # 타임스탬프
    used_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    pool = relationship("EnergyPoolModel", back_populates="usage_logs")
    transaction = relationship("Transaction")
    user = relationship("User")

class EnergyPriceHistory(Base):
    __tablename__ = "energy_price_history"
    
    id = Column(Integer, primary_key=True)
    pool_id = Column(Integer, ForeignKey("energy_pools.id"))
    
    # 가격 정보
    trx_price_usd = Column(Numeric(20, 8))  # TRX/USD 가격
    energy_price_trx = Column(Numeric(20, 8))  # Energy/TRX 가격
    energy_price_usd = Column(Numeric(20, 8))  # Energy/USD 가격
    
    # 시장 정보
    market_demand = Column(String(20))  # high, medium, low
    network_congestion = Column(Integer)  # 0-100%
    
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    pool = relationship("EnergyPoolModel", back_populates="price_history")
```

### 2. 에너지 풀 관리 서비스

#### 2.1 에너지 풀 매니저
```python
# app/services/energy/pool_manager.py
from typing import Dict, List, Optional
from decimal import Decimal
from tronpy import Tron
from tronpy.keys import PrivateKey
import asyncio

class EnergyPoolManager:
    def __init__(self, tron_client: Tron, redis_client):
        self.tron = tron_client
        self.redis = redis_client
        self.ENERGY_PER_TRX = 1  # 1 TRX = 1 Energy (대략적인 비율)
        
    async def create_energy_pool(
        self,
        pool_name: str,
        owner_private_key: str,
        initial_trx_amount: Decimal
    ) -> EnergyPoolModel:
        """새 에너지 풀 생성"""
        # 프라이빗 키로 주소 생성
        priv_key = PrivateKey(bytes.fromhex(owner_private_key))
        owner_address = priv_key.public_key.to_base58check_address()
        
        # TRX 동결하여 에너지 획득
        frozen_result = await self.freeze_trx_for_energy(
            owner_address, 
            owner_private_key, 
            initial_trx_amount
        )
        
        # 에너지 풀 DB 생성
        pool = EnergyPoolModel(
            pool_name=pool_name,
            owner_address=owner_address,
            frozen_trx=initial_trx_amount,
            total_energy=frozen_result['energy_received'],
            available_energy=frozen_result['energy_received'],
            status=EnergyPoolStatus.ACTIVE
        )
        
        await self.db.add(pool)
        await self.db.commit()
        
        # 캐시에 저장
        await self.cache_pool_status(pool)
        
        return pool
        
    async def freeze_trx_for_energy(
        self,
        owner_address: str,
        private_key: str,
        amount: Decimal
    ) -> Dict:
        """TRX를 동결하여 에너지 획득"""
        try:
            # TRX를 SUN 단위로 변환 (1 TRX = 1,000,000 SUN)
            amount_sun = int(amount * 1_000_000)
            
            # Stake 2.0 사용 (TRON의 새로운 스테이킹 방식)
            txn = (
                self.tron.transaction_builder.freeze_balance_v2(
                    owner_address=owner_address,
                    frozen_balance=amount_sun,
                    resource="ENERGY"
                )
            )
            
            # 트랜잭션 서명 및 전송
            txn = txn.sign(PrivateKey(bytes.fromhex(private_key)))
            result = txn.broadcast()
            
            # 에너지 계산 (대략적인 추정치)
            energy_received = int(amount * self.ENERGY_PER_TRX)
            
            return {
                "success": True,
                "tx_id": result['txid'],
                "frozen_amount": amount,
                "energy_received": energy_received
            }
            
        except Exception as e:
            logger.error(f"TRX 동결 실패: {str(e)}")
            raise
            
    async def check_pool_status(self, pool_id: int) -> Dict:
        """에너지 풀 상태 확인"""
        # 캐시 확인
        cached = await self.redis.get(f"energy_pool:{pool_id}")
        if cached:
            return json.loads(cached)
            
        pool = await self.db.get(EnergyPoolModel, pool_id)
        if not pool:
            raise ValueError("에너지 풀을 찾을 수 없습니다")
            
        # TRON 네트워크에서 실제 에너지 확인
        account_resource = self.tron.get_account_resource(pool.owner_address)
        
        # 사용 가능 에너지 계산
        total_energy = account_resource.get('EnergyLimit', 0)
        used_energy = account_resource.get('EnergyUsed', 0)
        available_energy = total_energy - used_energy
        
        # 상태 업데이트
        pool.total_energy = total_energy
        pool.used_energy = used_energy
        pool.available_energy = available_energy
        
        # 상태 판단
        usage_percentage = (used_energy / total_energy * 100) if total_energy > 0 else 100
        
        if usage_percentage >= 100:
            pool.status = EnergyPoolStatus.DEPLETED
        elif usage_percentage >= 100 - pool.critical_threshold:
            pool.status = EnergyPoolStatus.CRITICAL
        elif usage_percentage >= 100 - pool.low_threshold:
            pool.status = EnergyPoolStatus.LOW
        else:
            pool.status = EnergyPoolStatus.ACTIVE
            
        pool.last_checked_at = datetime.utcnow()
        await self.db.commit()
        
        status_data = {
            "pool_id": pool.id,
            "status": pool.status.value,
            "total_energy": total_energy,
            "available_energy": available_energy,
            "used_energy": used_energy,
            "usage_percentage": usage_percentage,
            "frozen_trx": float(pool.frozen_trx),
            "auto_refill": pool.auto_refill,
            "last_checked": pool.last_checked_at.isoformat()
        }
        
        # 캐시 저장 (5분)
        await self.redis.setex(
            f"energy_pool:{pool_id}",
            300,
            json.dumps(status_data)
        )
        
        # 자동 충전 확인
        if pool.auto_refill and usage_percentage >= 100 - pool.auto_refill_trigger:
            await self.trigger_auto_refill(pool)
            
        return status_data
        
    async def estimate_energy_cost(
        self,
        transaction_type: str,
        token_type: str = "TRC20"
    ) -> Dict:
        """트랜잭션 유형별 에너지 비용 추정"""
        # TRON 트랜잭션별 평균 에너지 소비량
        energy_costs = {
            "TRC20": {
                "transfer": 13_000,      # USDT 전송
                "approve": 12_000,       # 승인
                "transferFrom": 29_000,  # 대리 전송
            },
            "TRX": {
                "transfer": 0,  # TRX 전송은 대역폭만 사용
            }
        }
        
        base_cost = energy_costs.get(token_type, {}).get(transaction_type, 15_000)
        
        # 네트워크 혼잡도 반영
        congestion_factor = await self.get_network_congestion()
        adjusted_cost = int(base_cost * (1 + congestion_factor / 100))
        
        # 현재 에너지 가격 조회
        energy_price = await self.get_current_energy_price()
        
        return {
            "transaction_type": transaction_type,
            "base_energy_cost": base_cost,
            "adjusted_energy_cost": adjusted_cost,
            "congestion_factor": congestion_factor,
            "energy_price_trx": float(energy_price),
            "estimated_cost_trx": adjusted_cost * float(energy_price),
            "estimated_cost_usd": adjusted_cost * float(energy_price) * await self.get_trx_price()
        }
```

### 3. 에너지 사용 추적 서비스

#### 3.1 사용량 추적기
```python
# app/services/energy/usage_tracker.py
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio

class EnergyUsageTracker:
    def __init__(self, db_session, redis_client):
        self.db = db_session
        self.redis = redis_client
        
    async def record_energy_usage(
        self,
        pool_id: int,
        transaction_id: int,
        energy_consumed: int,
        transaction_type: str,
        user_id: int
    ) -> EnergyUsageLog:
        """에너지 사용 기록"""
        # 현재 에너지 가격 조회
        energy_price = await self.get_current_energy_price()
        actual_cost = Decimal(energy_consumed) * energy_price
        
        # 사용 로그 생성
        usage_log = EnergyUsageLog(
            pool_id=pool_id,
            transaction_id=transaction_id,
            energy_consumed=energy_consumed,
            transaction_type=transaction_type,
            user_id=user_id,
            energy_price=energy_price,
            actual_cost=actual_cost
        )
        
        self.db.add(usage_log)
        
        # 에너지 풀 업데이트
        pool = await self.db.get(EnergyPoolModel, pool_id)
        pool.used_energy += energy_consumed
        pool.available_energy -= energy_consumed
        
        # 일일 통계 업데이트
        await self.update_daily_stats(pool_id, energy_consumed)
        
        await self.db.commit()
        
        # 실시간 모니터링을 위한 이벤트 발행
        await self.publish_usage_event(usage_log)
        
        return usage_log
        
    async def get_usage_statistics(
        self,
        pool_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """에너지 사용 통계 조회"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
            
        # 기간별 사용량 집계
        usage_stats = await self.db.execute(
            select(
                func.date(EnergyUsageLog.used_at).label('date'),
                func.sum(EnergyUsageLog.energy_consumed).label('total_energy'),
                func.sum(EnergyUsageLog.actual_cost).label('total_cost'),
                func.count(EnergyUsageLog.id).label('transaction_count')
            )
            .where(
                EnergyUsageLog.pool_id == pool_id,
                EnergyUsageLog.used_at >= start_date,
                EnergyUsageLog.used_at <= end_date
            )
            .group_by(func.date(EnergyUsageLog.used_at))
            .order_by(func.date(EnergyUsageLog.used_at))
        )
        
        # 거래 유형별 통계
        type_stats = await self.db.execute(
            select(
                EnergyUsageLog.transaction_type,
                func.sum(EnergyUsageLog.energy_consumed).label('total_energy'),
                func.count(EnergyUsageLog.id).label('count')
            )
            .where(
                EnergyUsageLog.pool_id == pool_id,
                EnergyUsageLog.used_at >= start_date,
                EnergyUsageLog.used_at <= end_date
            )
            .group_by(EnergyUsageLog.transaction_type)
        )
        
        # 시간대별 사용 패턴
        hourly_stats = await self.db.execute(
            select(
                func.hour(EnergyUsageLog.used_at).label('hour'),
                func.avg(EnergyUsageLog.energy_consumed).label('avg_energy')
            )
            .where(
                EnergyUsageLog.pool_id == pool_id,
                EnergyUsageLog.used_at >= start_date,
                EnergyUsageLog.used_at <= end_date
            )
            .group_by(func.hour(EnergyUsageLog.used_at))
        )
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "daily_usage": [
                {
                    "date": row.date.isoformat(),
                    "total_energy": row.total_energy,
                    "total_cost": float(row.total_cost),
                    "transaction_count": row.transaction_count
                }
                for row in usage_stats
            ],
            "by_type": [
                {
                    "type": row.transaction_type,
                    "total_energy": row.total_energy,
                    "count": row.count
                }
                for row in type_stats
            ],
            "hourly_pattern": [
                {
                    "hour": row.hour,
                    "avg_energy": float(row.avg_energy)
                }
                for row in hourly_stats
            ],
            "summary": {
                "total_energy_consumed": sum(row.total_energy for row in usage_stats),
                "total_cost": sum(row.total_cost for row in usage_stats),
                "total_transactions": sum(row.transaction_count for row in usage_stats),
                "avg_energy_per_transaction": (
                    sum(row.total_energy for row in usage_stats) / 
                    sum(row.transaction_count for row in usage_stats)
                ) if sum(row.transaction_count for row in usage_stats) > 0 else 0
            }
        }
```

### 4. 에너지 가격 모니터링

#### 4.1 가격 추적 서비스
```python
# app/services/energy/price_monitor.py
import httpx
from decimal import Decimal
from typing import Dict, Optional

class EnergyPriceMonitor:
    def __init__(self, db_session, redis_client):
        self.db = db_session
        self.redis = redis_client
        self.http_client = httpx.AsyncClient()
        
    async def update_energy_price(self) -> Dict:
        """에너지 가격 업데이트 (외부 소스에서)"""
        try:
            # TRX 가격 조회 (CoinGecko 등)
            trx_price = await self.get_trx_market_price()
            
            # 에너지 시장 가격 조회 (TRON 에너지 거래소)
            energy_market_data = await self.get_energy_market_data()
            
            # 네트워크 혼잡도 확인
            network_stats = await self.get_network_statistics()
            
            # 가격 계산
            energy_price_trx = energy_market_data.get('price_per_energy', 0.000065)
            energy_price_usd = energy_price_trx * trx_price
            
            # 가격 이력 저장
            price_history = EnergyPriceHistory(
                pool_id=1,  # 기본 풀
                trx_price_usd=trx_price,
                energy_price_trx=energy_price_trx,
                energy_price_usd=energy_price_usd,
                market_demand=self.calculate_market_demand(energy_market_data),
                network_congestion=network_stats.get('congestion_level', 0)
            )
            
            self.db.add(price_history)
            await self.db.commit()
            
            # 캐시 업데이트
            await self.redis.setex(
                "energy_price:current",
                300,  # 5분
                json.dumps({
                    "trx_price_usd": float(trx_price),
                    "energy_price_trx": float(energy_price_trx),
                    "energy_price_usd": float(energy_price_usd),
                    "updated_at": datetime.utcnow().isoformat()
                })
            )
            
            return {
                "trx_price_usd": float(trx_price),
                "energy_price_trx": float(energy_price_trx),
                "energy_price_usd": float(energy_price_usd),
                "market_demand": price_history.market_demand,
                "network_congestion": price_history.network_congestion
            }
            
        except Exception as e:
            logger.error(f"에너지 가격 업데이트 실패: {str(e)}")
            # 실패 시 기본값 사용
            return await self.get_default_energy_price()
            
    async def get_energy_market_data(self) -> Dict:
        """에너지 시장 데이터 조회"""
        # TRON 에너지 거래소 API 호출
        # 실제로는 여러 소스에서 데이터를 수집하여 평균값 계산
        sources = [
            "https://api.tronenergymarket.com/price",
            "https://api.justlend.org/energy/price"
        ]
        
        prices = []
        for source in sources:
            try:
                response = await self.http_client.get(source, timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    prices.append(data.get('price_per_energy', 0))
            except:
                continue
                
        if prices:
            avg_price = sum(prices) / len(prices)
            return {
                "price_per_energy": avg_price,
                "sources_count": len(prices),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # 기본값
            return {"price_per_energy": 0.000065}
```

### 5. 에너지 관리 API 엔드포인트

#### 5.1 관리자 API
```python
# app/api/v1/endpoints/admin/energy.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/admin/energy/status", response_model=EnergyPoolStatusResponse)
async def get_energy_pool_status(
    pool_id: int = Query(1, description="에너지 풀 ID"),
    current_admin: Admin = Depends(get_current_admin),
    energy_service: EnergyPoolManager = Depends(get_energy_service)
):
    """에너지 풀 현황 조회"""
    try:
        status = await energy_service.check_pool_status(pool_id)
        
        # 추가 정보 조회
        usage_trend = await energy_service.get_usage_trend(pool_id, days=7)
        depletion_estimate = await energy_service.estimate_depletion_time(pool_id)
        
        return {
            **status,
            "usage_trend": usage_trend,
            "estimated_depletion": depletion_estimate,
            "recommendations": await energy_service.get_recommendations(status)
        }
    except Exception as e:
        logger.error(f"에너지 풀 상태 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="에너지 풀 상태 조회 실패")

@router.post("/admin/energy/create-pool", response_model=EnergyPoolResponse)
async def create_energy_pool(
    pool_data: CreateEnergyPoolRequest,
    current_admin: Admin = Depends(get_current_admin),
    energy_service: EnergyPoolManager = Depends(get_energy_service)
):
    """새 에너지 풀 생성"""
    if not current_admin.is_super_admin:
        raise HTTPException(status_code=403, detail="슈퍼 관리자만 가능합니다")
        
    try:
        pool = await energy_service.create_energy_pool(
            pool_name=pool_data.pool_name,
            owner_private_key=pool_data.owner_private_key,
            initial_trx_amount=pool_data.initial_trx_amount
        )
        
        return EnergyPoolResponse.from_orm(pool)
    except Exception as e:
        logger.error(f"에너지 풀 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/energy/usage-stats", response_model=EnergyUsageStatsResponse)
async def get_energy_usage_statistics(
    pool_id: int = Query(1),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_admin: Admin = Depends(get_current_admin),
    usage_tracker: EnergyUsageTracker = Depends(get_usage_tracker)
):
    """에너지 사용 통계 조회"""
    stats = await usage_tracker.get_usage_statistics(
        pool_id=pool_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return EnergyUsageStatsResponse(**stats)

@router.get("/admin/energy/usage-logs", response_model=List[EnergyUsageLogResponse])
async def get_energy_usage_logs(
    pool_id: int = Query(1),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    user_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """에너지 사용 로그 조회"""
    query = select(EnergyUsageLog).where(EnergyUsageLog.pool_id == pool_id)
    
    if user_id:
        query = query.where(EnergyUsageLog.user_id == user_id)
    if transaction_type:
        query = query.where(EnergyUsageLog.transaction_type == transaction_type)
        
    query = query.order_by(EnergyUsageLog.used_at.desc())
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return [EnergyUsageLogResponse.from_orm(log) for log in logs]

@router.post("/admin/energy/simulate-usage", response_model=EnergySimulationResponse)
async def simulate_energy_usage(
    simulation_data: EnergySimulationRequest,
    current_admin: Admin = Depends(get_current_admin),
    energy_service: EnergyPoolManager = Depends(get_energy_service)
):
    """에너지 사용량 시뮬레이션"""
    simulation_result = await energy_service.simulate_usage(
        transaction_count=simulation_data.transaction_count,
        transaction_types=simulation_data.transaction_types,
        time_period_hours=simulation_data.time_period_hours
    )
    
    return EnergySimulationResponse(**simulation_result)

@router.put("/admin/energy/auto-manage", response_model=MessageResponse)
async def update_auto_management_settings(
    pool_id: int,
    settings: AutoManagementSettings,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """자동 에너지 관리 설정"""
    pool = await db.get(EnergyPoolModel, pool_id)
    if not pool:
        raise HTTPException(status_code=404, detail="에너지 풀을 찾을 수 없습니다")
        
    pool.auto_refill = settings.enabled
    pool.auto_refill_amount = settings.refill_amount
    pool.auto_refill_trigger = settings.trigger_percentage
    
    await db.commit()
    
    return {"message": "자동 관리 설정이 업데이트되었습니다"}

@router.get("/admin/energy/price-history", response_model=List[EnergyPriceHistoryResponse])
async def get_energy_price_history(
    days: int = Query(7, le=30),
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """에너지 가격 히스토리 조회"""
    since = datetime.utcnow() - timedelta(days=days)
    
    query = select(EnergyPriceHistory).where(
        EnergyPriceHistory.recorded_at >= since
    ).order_by(EnergyPriceHistory.recorded_at.desc())
    
    result = await db.execute(query)
    history = result.scalars().all()
    
    return [EnergyPriceHistoryResponse.from_orm(record) for record in history]
```

### 6. 스키마 정의

#### 6.1 요청/응답 스키마
```python
# app/schemas/energy.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from decimal import Decimal

class CreateEnergyPoolRequest(BaseModel):
    pool_name: str = Field(..., description="에너지 풀 이름")
    owner_private_key: str = Field(..., description="소유자 프라이빗 키")
    initial_trx_amount: Decimal = Field(..., description="초기 동결할 TRX 금액")

class EnergyPoolResponse(BaseModel):
    id: int
    pool_name: str
    owner_address: str
    frozen_trx: Decimal
    total_energy: int
    available_energy: int
    used_energy: int
    status: str
    created_at: datetime
    
    class Config:
        orm_mode = True

class EnergyPoolStatusResponse(BaseModel):
    pool_id: int
    status: str
    total_energy: int
    available_energy: int
    used_energy: int
    usage_percentage: float
    frozen_trx: float
    auto_refill: bool
    last_checked: str
    usage_trend: Dict  # 7일간 사용 추이
    estimated_depletion: Optional[str]  # 예상 소진 시간
    recommendations: List[str]  # 추천 조치사항

class EnergyUsageLogResponse(BaseModel):
    id: int
    transaction_id: int
    energy_consumed: int
    transaction_type: str
    user_id: int
    energy_price: Decimal
    actual_cost: Decimal
    used_at: datetime
    
    class Config:
        orm_mode = True

class EnergyUsageStatsResponse(BaseModel):
    period: Dict[str, str]
    daily_usage: List[Dict]
    by_type: List[Dict]
    hourly_pattern: List[Dict]
    summary: Dict

class EnergySimulationRequest(BaseModel):
    transaction_count: int
    transaction_types: List[str]
    time_period_hours: int = 24

class EnergySimulationResponse(BaseModel):
    total_energy_required: int
    estimated_cost_trx: float
    estimated_cost_usd: float
    current_pool_capacity: float
    can_handle: bool
    shortage_amount: Optional[int]
    recommendations: List[str]

class AutoManagementSettings(BaseModel):
    enabled: bool
    refill_amount: Decimal = Field(..., ge=1000)
    trigger_percentage: int = Field(..., ge=5, le=50)

class EnergyPriceHistoryResponse(BaseModel):
    id: int
    trx_price_usd: Decimal
    energy_price_trx: Decimal
    energy_price_usd: Decimal
    market_demand: str
    network_congestion: int
    recorded_at: datetime
    
    class Config:
        orm_mode = True
```

### 7. 자동화 및 모니터링

#### 7.1 백그라운드 태스크
```python
# app/tasks/energy_tasks.py
from app.core.celery import celery_app
from typing import Dict

@celery_app.task
async def monitor_energy_pools():
    """에너지 풀 상태 모니터링 (5분마다)"""
    energy_service = get_energy_service()
    
    pools = await energy_service.get_all_active_pools()
    
    for pool in pools:
        status = await energy_service.check_pool_status(pool.id)
        
        # 임계값 확인
        if status['status'] in ['CRITICAL', 'DEPLETED']:
            await send_critical_alert(pool, status)
        elif status['status'] == 'LOW':
            await send_warning_alert(pool, status)
            
        # 자동 충전 처리
        if pool.auto_refill and status['usage_percentage'] >= 100 - pool.auto_refill_trigger:
            await energy_service.execute_auto_refill(pool)

@celery_app.task
async def update_energy_prices():
    """에너지 가격 업데이트 (1시간마다)"""
    price_monitor = get_price_monitor()
    
    try:
        updated_prices = await price_monitor.update_energy_price()
        logger.info(f"에너지 가격 업데이트 완료: {updated_prices}")
    except Exception as e:
        logger.error(f"에너지 가격 업데이트 실패: {str(e)}")
        
@celery_app.task
async def generate_energy_report():
    """일일 에너지 사용 리포트 생성"""
    yesterday = datetime.utcnow().date() - timedelta(days=1)
    
    report = await generate_daily_energy_report(yesterday)
    
    # 관리자에게 이메일 전송
    await send_admin_email(
        subject=f"에너지 풀 일일 리포트 - {yesterday}",
        content=report
    )
```

## 검증 포인트

- [ ] TRX 동결 및 에너지 획득이 정상 작동하는가?
- [ ] 에너지 풀 상태가 실시간으로 업데이트되는가?
- [ ] 에너지 사용 로그가 정확히 기록되는가?
- [ ] 에너지 부족 시 알림이 발송되는가?
- [ ] 자동 충전 기능이 작동하는가?
- [ ] 가격 모니터링이 정상 작동하는가?
- [ ] 사용 통계가 정확히 집계되는가?
- [ ] API 응답 시간이 적절한가?

이 시스템을 통해 TRON 에너지를 효율적으로 관리하고, 사용자들에게 안정적인 USDT 출금 서비스를 제공할 수 있습니다.