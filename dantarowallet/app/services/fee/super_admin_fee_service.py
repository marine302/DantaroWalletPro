"""
슈퍼 어드민용 수수료 & 매출 관리 서비스 - 확장 기능
"""
import uuid
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from fastapi import HTTPException

from app.models.fee_config import FeeConfig
from app.models.partner import Partner
from app.schemas.fee import (
    FeeConfigResponse, RevenueStats, TotalRevenueStats,
    Settlement, PartnerBilling
)
from app.core.database import get_db


class SuperAdminFeeService:
    """본사 슈퍼 어드민용 수수료 & 매출 관리 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def set_partner_fee_config(self, partner_id: str, config_data: dict) -> FeeConfigResponse:
        """파트너별 수수료 설정"""
        try:
            # 파트너 확인
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            # 기존 설정 조회
            existing_config = self.db.query(FeeConfig).filter(
                and_(
                    FeeConfig.partner_id == partner_id,
                    FeeConfig.is_active == True
                )
            ).first()
            
            # 기존 설정 비활성화
            if existing_config:
                existing_config.is_active = False
                existing_config.updated_at = datetime.utcnow()
            
            # 새 설정 생성
            new_config = FeeConfig(
                id=str(uuid.uuid4()),
                partner_id=partner_id,
                transaction_type=config_data.get("transaction_type", "all"),
                base_fee=Decimal(str(config_data.get("base_fee", "0.001"))),
                percentage_fee=Decimal(str(config_data.get("percentage_fee", "0.01"))),
                minimum_fee=Decimal(str(config_data.get("minimum_fee", "1.0"))),
                maximum_fee=Decimal(str(config_data.get("maximum_fee", "100.0"))),
                tier_config=config_data.get("tier_config", {}),
                volume_discounts=config_data.get("volume_discounts", {}),
                time_based_pricing=config_data.get("time_based_pricing", {}),
                is_active=True
            )
            
            self.db.add(new_config)
            self.db.commit()
            self.db.refresh(new_config)
            
            return FeeConfigResponse(
                id=new_config.id,
                partner_id=new_config.partner_id,
                transaction_type=new_config.transaction_type,
                base_fee=new_config.base_fee,
                percentage_fee=new_config.percentage_fee,
                minimum_fee=new_config.minimum_fee,
                maximum_fee=new_config.maximum_fee,
                tier_config=new_config.tier_config,
                volume_discounts=new_config.volume_discounts,
                time_based_pricing=new_config.time_based_pricing,
                is_active=new_config.is_active,
                created_at=new_config.created_at,
                updated_at=new_config.updated_at
            )
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to set fee config: {str(e)}")
    
    async def calculate_transaction_fee(
        self, 
        partner_id: str, 
        amount: Decimal,
        transaction_type: str = "transfer"
    ) -> Decimal:
        """거래 수수료 계산"""
        try:
            # 파트너별 수수료 설정 조회
            fee_config = self.db.query(FeeConfig).filter(
                and_(
                    FeeConfig.partner_id == partner_id,
                    or_(
                        FeeConfig.transaction_type == transaction_type,
                        FeeConfig.transaction_type == "all"
                    ),
                    FeeConfig.is_active == True
                )
            ).order_by(desc(FeeConfig.created_at)).first()
            
            if not fee_config:
                # 기본 수수료 설정 사용
                return Decimal("1.0")  # 기본 수수료
            
            # 기본 수수료 계산
            base_fee = fee_config.base_fee
            percentage_fee = amount * fee_config.percentage_fee
            total_fee = base_fee + percentage_fee
            
            # 최소/최대 수수료 적용
            total_fee = max(total_fee, fee_config.minimum_fee)
            if fee_config.maximum_fee:
                total_fee = min(total_fee, fee_config.maximum_fee)
            
            # 볼륨 할인 적용
            if fee_config.volume_discounts:
                monthly_volume = await self._get_partner_monthly_volume(partner_id)
                discount_rate = self._calculate_volume_discount(
                    monthly_volume, 
                    fee_config.volume_discounts
                )
                total_fee = total_fee * (1 - discount_rate)
            
            # 시간대별 가격 적용
            if fee_config.time_based_pricing:
                time_multiplier = self._get_time_based_multiplier(
                    fee_config.time_based_pricing
                )
                total_fee = total_fee * time_multiplier
            
            return total_fee
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to calculate fee: {str(e)}")
    
    async def get_partner_revenue_stats(self, partner_id: str) -> RevenueStats:
        """파트너별 매출 통계 조회"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            # 기간별 매출 통계 (실제 구현에서는 transaction, fee 테이블 활용)
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            this_month = today.replace(day=1)
            
            # 오늘 매출 (임시 계산)
            daily_revenue = Decimal("0.00")
            
            # 이번 달 매출 (임시 계산)  
            monthly_revenue = Decimal("0.00")
            
            # 총 매출 (임시 계산)
            total_revenue = Decimal("0.00")
            
            # 거래 통계 (임시 계산)
            total_transactions = 0
            total_volume = Decimal("0.00")
            
            # 수수료 통계 (임시 계산)
            avg_fee_rate = partner.commission_rate
            total_fees_collected = Decimal("0.00")
            
            return RevenueStats(
                partner_id=partner_id,
                partner_name=partner.name,
                daily_revenue=daily_revenue,
                monthly_revenue=monthly_revenue,
                total_revenue=total_revenue,
                total_transactions=total_transactions,
                total_volume=total_volume,
                avg_fee_rate=float(avg_fee_rate),
                total_fees_collected=total_fees_collected,
                growth_rate=0.0,  # 성장률 계산
                last_transaction=None,  # 마지막 거래 시간
                status=partner.status
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get partner revenue stats: {str(e)}")
    
    async def get_total_revenue_stats(self) -> TotalRevenueStats:
        """전체 매출 통계 조회"""
        try:
            # 활성 파트너 조회
            active_partners = self.db.query(Partner).filter(Partner.status == "active").all()
            
            # 전체 통계 계산 (실제 구현에서는 집계 테이블 활용)
            total_partners = len(active_partners)
            total_revenue = Decimal("0.00")
            total_transactions = 0
            total_volume = Decimal("0.00")
            total_fees = Decimal("0.00")
            
            # 오늘 통계
            daily_revenue = Decimal("0.00")
            daily_transactions = 0
            
            # 이번 달 통계
            monthly_revenue = Decimal("0.00")
            monthly_transactions = 0
            
            # 파트너별 매출 순위
            partner_rankings = []
            for partner in active_partners[:10]:  # 상위 10개
                partner_stats = await self.get_partner_revenue_stats(partner.id)
                partner_rankings.append({
                    "partner_id": partner.id,
                    "partner_name": partner.name,
                    "revenue": partner_stats.total_revenue,
                    "transactions": partner_stats.total_transactions,
                    "rank": len(partner_rankings) + 1
                })
            
            # 성장률 계산 (전월 대비)
            growth_rate = 0.0  # 실제 계산 로직 필요
            
            return TotalRevenueStats(
                total_partners=total_partners,
                total_revenue=total_revenue,
                daily_revenue=daily_revenue,
                monthly_revenue=monthly_revenue,
                total_transactions=total_transactions,
                daily_transactions=daily_transactions,
                monthly_transactions=monthly_transactions,
                total_volume=total_volume,
                total_fees=total_fees,
                avg_fee_rate=0.01,  # 평균 수수료율
                growth_rate=growth_rate,
                partner_rankings=partner_rankings,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get total revenue stats: {str(e)}")
    
    async def process_settlement(self, partner_id: str, period: str) -> Settlement:
        """파트너 정산 처리"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            # 정산 기간 설정
            if period == "monthly":
                start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date.replace(month=start_date.month + 1) - timedelta(days=1)
            elif period == "weekly":
                start_date = datetime.utcnow() - timedelta(days=7)
                end_date = datetime.utcnow()
            else:
                raise HTTPException(status_code=400, detail="Invalid period. Use 'monthly' or 'weekly'")
            
            # 정산 데이터 계산 (실제 구현에서는 transaction 테이블 활용)
            settlement_amount = Decimal("0.00")
            total_transactions = 0
            total_volume = Decimal("0.00")
            total_fees = Decimal("0.00")
            
            settlement_id = str(uuid.uuid4())
            
            return Settlement(
                settlement_id=settlement_id,
                partner_id=partner_id,
                partner_name=partner.name,
                period=period,
                start_date=start_date,
                end_date=end_date,
                total_transactions=total_transactions,
                total_volume=total_volume,
                total_fees=total_fees,
                settlement_amount=settlement_amount,
                status="pending",
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process settlement: {str(e)}")
    
    async def get_fee_config_history(self, partner_id: str) -> List[FeeConfigResponse]:
        """파트너 수수료 설정 이력 조회"""
        try:
            configs = self.db.query(FeeConfig).filter(
                FeeConfig.partner_id == partner_id
            ).order_by(desc(FeeConfig.created_at)).all()
            
            return [
                FeeConfigResponse(
                    id=config.id,
                    partner_id=config.partner_id,
                    transaction_type=config.transaction_type,
                    base_fee=config.base_fee,
                    percentage_fee=config.percentage_fee,
                    minimum_fee=config.minimum_fee,
                    maximum_fee=config.maximum_fee,
                    tier_config=config.tier_config,
                    volume_discounts=config.volume_discounts,
                    time_based_pricing=config.time_based_pricing,
                    is_active=config.is_active,
                    created_at=config.created_at,
                    updated_at=config.updated_at
                ) for config in configs
            ]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get fee config history: {str(e)}")
    
    async def bulk_update_fees(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """일괄 수수료 업데이트"""
        try:
            results = {
                "success": [],
                "failed": []
            }
            
            for update in updates:
                try:
                    partner_id = update.get("partner_id")
                    config_data = update.get("config", {})
                    
                    result = await self.set_partner_fee_config(partner_id, config_data)
                    results["success"].append({
                        "partner_id": partner_id,
                        "config_id": result.id
                    })
                    
                except Exception as e:
                    results["failed"].append({
                        "partner_id": update.get("partner_id"),
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to bulk update fees: {str(e)}")
    
    # 유틸리티 메서드들
    async def _get_partner_monthly_volume(self, partner_id: str) -> Decimal:
        """파트너 월간 거래량 조회"""
        # 실제 구현에서는 transaction 테이블에서 집계
        return Decimal("0.00")
    
    def _calculate_volume_discount(self, volume: Decimal, discount_config: dict) -> Decimal:
        """볼륨 할인율 계산"""
        for tier in sorted(discount_config.keys(), reverse=True):
            if volume >= Decimal(tier):
                return Decimal(str(discount_config[tier]))
        return Decimal("0.00")
    
    def _get_time_based_multiplier(self, time_config: dict) -> Decimal:
        """시간대별 수수료 배수 계산"""
        current_hour = datetime.utcnow().hour
        
        for time_range, multiplier in time_config.items():
            start_hour, end_hour = map(int, time_range.split("-"))
            if start_hour <= current_hour <= end_hour:
                return Decimal(str(multiplier))
        
        return Decimal("1.0")  # 기본 배수
