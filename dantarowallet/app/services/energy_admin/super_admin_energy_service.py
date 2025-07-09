"""
슈퍼 어드민용 에너지 풀 관리 서비스 - 확장 기능
"""
import uuid
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from fastapi import HTTPException

from app.models.energy_pool import EnergyPool
from app.models.partner import Partner, EnergyUsageHistory
from app.schemas.energy import (
    EnergyPoolStatus, EnergyUsage, EnergyAlert,
    EnergyHistory, EnergyAllocation
)
from app.core.database import get_db


class SuperAdminEnergyService:
    """본사 슈퍼 어드민용 에너지 풀 관리 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_total_energy_status(self) -> EnergyPoolStatus:
        """전체 에너지 풀 현황 조회"""
        try:
            # 전체 에너지 풀 상태
            energy_pool = self.db.query(EnergyPool).order_by(desc(EnergyPool.id)).first()
            
            if not energy_pool:
                # 기본 에너지 풀 생성
                energy_pool = EnergyPool(
                    id=str(uuid.uuid4()),
                    total_energy=1000000,
                    available_energy=1000000,
                    reserved_energy=0,
                    daily_consumption=0,
                    alert_threshold=100000,
                    critical_threshold=50000
                )
                self.db.add(energy_pool)
                self.db.commit()
                self.db.refresh(energy_pool)
            
            # 파트너별 에너지 할당 통계
            partner_allocations = self.db.query(
                Partner.id,
                Partner.name,
                Partner.energy_balance
            ).filter(
                Partner.status == "active"
            ).all()
            
            total_allocated = sum(p.energy_balance or 0 for p in partner_allocations)
            
            # 최근 24시간 사용량
            yesterday = datetime.utcnow() - timedelta(days=1)
            daily_usage = self.db.query(
                func.sum(EnergyUsageHistory.energy_amount)
            ).filter(
                EnergyUsageHistory.created_at >= yesterday
            ).scalar() or 0
            
            return EnergyPoolStatus(
                total_energy=energy_pool.total_energy,
                available_energy=energy_pool.available_energy,
                reserved_energy=energy_pool.reserved_energy,
                allocated_energy=total_allocated,
                daily_consumption=daily_usage,
                alert_threshold=energy_pool.alert_threshold,
                critical_threshold=energy_pool.critical_threshold,
                is_sufficient=energy_pool.available_energy > energy_pool.alert_threshold,
                partner_count=len(partner_allocations),
                last_updated=energy_pool.updated_at or energy_pool.created_at
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get energy status: {str(e)}")
    
    async def allocate_energy_to_partner(self, partner_id: str, amount: int) -> bool:
        """파트너에게 에너지 할당"""
        try:
            # 파트너 조회
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            # 에너지 풀 조회
            energy_pool = self.db.query(EnergyPool).order_by(desc(EnergyPool.id)).first()
            if not energy_pool:
                raise HTTPException(status_code=404, detail="Energy pool not found")
            
            # 할당 가능한 에너지 확인
            if energy_pool.available_energy < amount:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient energy. Available: {energy_pool.available_energy}, Requested: {amount}"
                )
            
            # 에너지 할당
            partner.energy_balance = (partner.energy_balance or 0) + amount
            energy_pool.available_energy -= amount
            energy_pool.reserved_energy += amount
            
            # 에너지 사용 이력 기록
            usage_history = EnergyUsageHistory(
                id=str(uuid.uuid4()),
                partner_id=partner_id,
                transaction_type="allocation",
                energy_amount=amount,
                balance_before=(partner.energy_balance - amount),
                balance_after=partner.energy_balance,
                transaction_hash=f"alloc_{uuid.uuid4().hex[:16]}"
            )
            
            self.db.add(usage_history)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to allocate energy: {str(e)}")
    
    async def get_partner_energy_usage(self, partner_id: str) -> EnergyUsage:
        """파트너 에너지 사용량 조회"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            # 최근 30일 사용량
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            monthly_usage = self.db.query(
                func.sum(EnergyUsageHistory.energy_amount)
            ).filter(
                and_(
                    EnergyUsageHistory.partner_id == partner_id,
                    EnergyUsageHistory.transaction_type == "usage",
                    EnergyUsageHistory.created_at >= thirty_days_ago
                )
            ).scalar() or 0
            
            # 오늘 사용량
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            daily_usage = self.db.query(
                func.sum(EnergyUsageHistory.energy_amount)
            ).filter(
                and_(
                    EnergyUsageHistory.partner_id == partner_id,
                    EnergyUsageHistory.transaction_type == "usage",
                    EnergyUsageHistory.created_at >= today
                )
            ).scalar() or 0
            
            # 평균 일간 사용량 (최근 7일)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            weekly_usage = self.db.query(
                func.sum(EnergyUsageHistory.energy_amount)
            ).filter(
                and_(
                    EnergyUsageHistory.partner_id == partner_id,
                    EnergyUsageHistory.transaction_type == "usage",
                    EnergyUsageHistory.created_at >= seven_days_ago
                )
            ).scalar() or 0
            
            avg_daily_usage = weekly_usage / 7 if weekly_usage > 0 else 0
            
            return EnergyUsage(
                partner_id=partner_id,
                current_balance=partner.energy_balance or 0,
                daily_usage=daily_usage,
                monthly_usage=monthly_usage,
                avg_daily_usage=int(avg_daily_usage),
                usage_efficiency=0.0,  # 실제 계산 로직 필요
                last_usage=None  # 마지막 사용 시간
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get partner energy usage: {str(e)}")
    
    async def recharge_energy_pool(self, amount: int, description: str = "") -> bool:
        """에너지 풀 충전"""
        try:
            energy_pool = self.db.query(EnergyPool).order_by(desc(EnergyPool.id)).first()
            if not energy_pool:
                raise HTTPException(status_code=404, detail="Energy pool not found")
            
            # 에너지 충전
            energy_pool.total_energy += amount
            energy_pool.available_energy += amount
            energy_pool.updated_at = datetime.utcnow()
            
            # 충전 이력 기록 (시스템 파트너로 기록)
            recharge_history = EnergyUsageHistory(
                id=str(uuid.uuid4()),
                partner_id="system",  # 시스템 충전
                transaction_type="recharge",
                energy_amount=amount,
                balance_before=energy_pool.total_energy - amount,
                balance_after=energy_pool.total_energy,
                transaction_hash=f"recharge_{uuid.uuid4().hex[:16]}"
            )
            
            self.db.add(recharge_history)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to recharge energy pool: {str(e)}")
    
    async def monitor_energy_alerts(self) -> List[EnergyAlert]:
        """에너지 알림 모니터링"""
        try:
            alerts = []
            
            # 전체 에너지 풀 상태 확인
            energy_pool = self.db.query(EnergyPool).order_by(desc(EnergyPool.id)).first()
            if energy_pool:
                if energy_pool.available_energy <= energy_pool.critical_threshold:
                    alerts.append(EnergyAlert(
                        alert_type="critical",
                        message=f"Critical energy level: {energy_pool.available_energy}",
                        current_energy=energy_pool.available_energy,
                        threshold=energy_pool.critical_threshold,
                        partner_id=None,
                        created_at=datetime.utcnow()
                    ))
                elif energy_pool.available_energy <= energy_pool.alert_threshold:
                    alerts.append(EnergyAlert(
                        alert_type="warning",
                        message=f"Low energy level: {energy_pool.available_energy}",
                        current_energy=energy_pool.available_energy,
                        threshold=energy_pool.alert_threshold,
                        partner_id=None,
                        created_at=datetime.utcnow()
                    ))
            
            # 파트너별 에너지 부족 확인
            low_energy_partners = self.db.query(Partner).filter(
                and_(
                    Partner.status == "active",
                    Partner.energy_balance <= 1000  # 임계값
                )
            ).all()
            
            for partner in low_energy_partners:
                alerts.append(EnergyAlert(
                    alert_type="partner_low_energy",
                    message=f"Partner {partner.name} has low energy: {partner.energy_balance}",
                    current_energy=partner.energy_balance or 0,
                    threshold=1000,
                    partner_id=partner.id,
                    created_at=datetime.utcnow()
                ))
            
            return alerts
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to monitor energy alerts: {str(e)}")
    
    async def get_energy_usage_history(
        self, 
        partner_id: Optional[str] = None,
        limit: int = 100,
        transaction_type: Optional[str] = None
    ) -> List[EnergyHistory]:
        """에너지 사용 이력 조회"""
        try:
            query = self.db.query(EnergyUsageHistory).order_by(desc(EnergyUsageHistory.created_at))
            
            # 필터 적용
            if partner_id:
                query = query.filter(EnergyUsageHistory.partner_id == partner_id)
            
            if transaction_type:
                query = query.filter(EnergyUsageHistory.transaction_type == transaction_type)
            
            # 페이징
            histories = query.limit(limit).all()
            
            result = []
            for history in histories:
                # 파트너 정보 조회
                partner_name = "System"
                if history.partner_id != "system":
                    partner = self.db.query(Partner).filter(Partner.id == history.partner_id).first()
                    if partner:
                        partner_name = partner.name
                
                result.append(EnergyHistory(
                    id=history.id,
                    partner_id=history.partner_id,
                    partner_name=partner_name,
                    transaction_type=history.transaction_type,
                    energy_amount=history.energy_amount,
                    balance_before=history.balance_before,
                    balance_after=history.balance_after,
                    transaction_hash=history.transaction_hash,
                    created_at=history.created_at
                ))
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get energy usage history: {str(e)}")
    
    async def get_energy_statistics(self) -> Dict[str, Any]:
        """에너지 통계 조회"""
        try:
            # 전체 통계
            energy_pool = self.db.query(EnergyPool).order_by(desc(EnergyPool.id)).first()
            
            # 파트너별 에너지 할당 현황
            partner_stats = self.db.query(
                Partner.id,
                Partner.name,
                Partner.energy_balance
            ).filter(
                Partner.status == "active"
            ).all()
            
            # 최근 7일 사용량 추이
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            daily_usage = []
            
            for i in range(7):
                day_start = seven_days_ago + timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                
                usage = self.db.query(
                    func.sum(EnergyUsageHistory.energy_amount)
                ).filter(
                    and_(
                        EnergyUsageHistory.transaction_type == "usage",
                        EnergyUsageHistory.created_at >= day_start,
                        EnergyUsageHistory.created_at < day_end
                    )
                ).scalar() or 0
                
                daily_usage.append({
                    "date": day_start.strftime("%Y-%m-%d"),
                    "usage": usage
                })
            
            # 상위 사용 파트너
            top_partners = self.db.query(
                EnergyUsageHistory.partner_id,
                func.sum(EnergyUsageHistory.energy_amount).label("total_usage")
            ).filter(
                and_(
                    EnergyUsageHistory.transaction_type == "usage",
                    EnergyUsageHistory.created_at >= seven_days_ago
                )
            ).group_by(
                EnergyUsageHistory.partner_id
            ).order_by(
                desc("total_usage")
            ).limit(10).all()
            
            return {
                "total_energy": energy_pool.total_energy if energy_pool else 0,
                "available_energy": energy_pool.available_energy if energy_pool else 0,
                "allocated_energy": sum(p.energy_balance or 0 for p in partner_stats),
                "active_partners": len(partner_stats),
                "daily_usage_trend": daily_usage,
                "top_energy_consumers": [
                    {
                        "partner_id": tp.partner_id,
                        "usage": tp.total_usage
                    } for tp in top_partners
                ]
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get energy statistics: {str(e)}")
    
    async def emergency_energy_rebalance(self) -> Dict[str, Any]:
        """긴급 에너지 재분배"""
        try:
            # 현재 상태 분석
            energy_pool = self.db.query(EnergyPool).order_by(desc(EnergyPool.id)).first()
            if not energy_pool:
                raise HTTPException(status_code=404, detail="Energy pool not found")
            
            # 파트너별 에너지 잔액 조회
            partners = self.db.query(Partner).filter(
                Partner.status == "active"
            ).all()
            
            actions_taken = []
            
            # 에너지 부족 파트너에게 최소한의 에너지 할당
            for partner in partners:
                if (partner.energy_balance or 0) < 100:  # 최소 임계값
                    if energy_pool.available_energy >= 1000:
                        await self.allocate_energy_to_partner(partner.id, 1000)
                        actions_taken.append(f"Allocated 1000 energy to {partner.name}")
            
            return {
                "status": "completed",
                "actions_taken": actions_taken,
                "remaining_energy": energy_pool.available_energy
            }
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Emergency rebalance failed: {str(e)}")
