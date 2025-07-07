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
            
            # 기존 설정 조회 및 비활성화
            existing_config = self.db.query(FeeConfig).filter(
                and_(
                    FeeConfig.partner_id == int(partner_id),
                    FeeConfig.is_active == True
                )
            ).first()
            
            if existing_config:
                # 기존 설정 비활성화
                self.db.query(FeeConfig).filter(
                    FeeConfig.id == existing_config.id
                ).update({
                    "is_active": False, 
                    "updated_at": datetime.utcnow()
                })
            
            # 새 설정 생성
            new_config = FeeConfig(
                transaction_type=config_data.get("transaction_type", "all"),
                base_fee=Decimal(str(config_data.get("base_fee", "0.001"))),
                percentage_fee=Decimal(str(config_data.get("percentage_fee", "0.01"))),
                min_fee=Decimal(str(config_data.get("minimum_fee", "1.0"))),
                max_fee=Decimal(str(config_data.get("maximum_fee", "100.0"))),
                partner_id=int(partner_id) if partner_id else None,
                is_active=True
            )
            
            self.db.add(new_config)
            self.db.commit()
            self.db.refresh(new_config)
            
            return FeeConfigResponse(
                id=str(new_config.id),
                partner_id=str(new_config.partner_id),
                transaction_type=new_config.transaction_type,
                base_fee=new_config.base_fee,
                percentage_fee=new_config.percentage_fee,
                minimum_fee=new_config.min_fee,  # 모델의 필드명은 min_fee
                maximum_fee=new_config.max_fee,  # 모델의 필드명은 max_fee
                tier_config={},  # 모델에 tier_config가 없으므로 빈 dict
                volume_discounts={},  # 모델에 volume_discounts가 없으므로 빈 dict
                time_based_pricing={},  # 모델에 time_based_pricing가 없으므로 빈 dict
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
            
            # 볼륨 할인 적용 (임시로 주석 처리)
            # if fee_config.volume_discounts:
            #     monthly_volume = await self._get_partner_monthly_volume(partner_id)
            #     discount_rate = self._calculate_volume_discount(
            #         monthly_volume, 
            #         fee_config.volume_discounts
            #     )
            #     total_fee = total_fee * (1 - discount_rate)
            
            # 시간대별 가격 적용 (임시로 주석 처리)
            # if fee_config.time_based_pricing:
            #     time_multiplier = self._get_time_based_multiplier(
            #         fee_config.time_based_pricing
            #     )
            #     total_fee = total_fee * time_multiplier
            
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
    
    async def get_total_revenue_stats(self, days: int = 30) -> dict:
        """전체 매출 통계 (슈퍼 어드민용)"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # 실제 구현에서는 transaction 테이블에서 계산
            # 임시 데이터 반환
            
            total_revenue = Decimal("125000.50")
            total_transactions = 2847
            avg_transaction_value = total_revenue / total_transactions if total_transactions > 0 else Decimal("0")
            
            # 파트너별 매출 순위
            partner_revenue = [
                {
                    "partner_id": "partner_1",
                    "partner_name": "Partner A",
                    "revenue": Decimal("52000.25"),
                    "transactions": 1200,
                    "percentage": 41.6
                },
                {
                    "partner_id": "partner_2", 
                    "partner_name": "Partner B",
                    "revenue": Decimal("43500.75"),
                    "transactions": 987,
                    "percentage": 34.8
                },
                {
                    "partner_id": "partner_3",
                    "partner_name": "Partner C",
                    "revenue": Decimal("29499.50"),
                    "transactions": 660,
                    "percentage": 23.6
                }
            ]
            
            # 일별 매출 추이
            daily_revenue = []
            for i in range(days):
                date = start_date + timedelta(days=i)
                # 주말은 낮게, 평일은 높게
                base_amount = 3000 if date.weekday() < 5 else 1500
                daily_amount = base_amount + (i % 7) * 200
                
                daily_revenue.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "revenue": Decimal(str(daily_amount)),
                    "transactions": daily_amount // 50,
                    "avg_value": Decimal("50.00")
                })
            
            return {
                "period_days": days,
                "total_revenue": total_revenue,
                "total_transactions": total_transactions,
                "average_transaction_value": avg_transaction_value,
                "revenue_growth_rate": 15.7,  # %
                "partner_rankings": partner_revenue,
                "daily_breakdown": daily_revenue,
                "revenue_by_type": {
                    "deposit_fees": Decimal("45000.00"),
                    "withdrawal_fees": Decimal("65000.00"),
                    "api_usage_fees": Decimal("15000.50")
                },
                "projections": {
                    "next_month_forecast": total_revenue * Decimal("1.12"),
                    "quarterly_target": total_revenue * Decimal("3.5"),
                    "annual_projection": total_revenue * Decimal("12.3")
                }
            }
            
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
    
    async def get_fee_analytics(self, days: int = 30) -> dict:
        """수수료 분석 데이터"""
        try:
            # 실제 구현에서는 실제 데이터 기반으로 계산
            # 임시 분석 데이터
            
            total_fees_collected = Decimal("25000.75")
            avg_fee_rate = Decimal("0.025")  # 2.5%
            
            # 수수료 유형별 분석
            fee_breakdown = {
                "deposit_fees": {
                    "amount": Decimal("8500.25"),
                    "count": 1700,
                    "avg_rate": Decimal("0.015")
                },
                "withdrawal_fees": {
                    "amount": Decimal("12750.50"),
                    "count": 850,
                    "avg_rate": Decimal("0.035")
                },
                "api_fees": {
                    "amount": Decimal("3750.00"),
                    "count": 15000,
                    "avg_rate": Decimal("0.25")  # per API call
                }
            }
            
            # 파트너별 수수료 기여도
            partner_contributions = [
                {
                    "partner_id": "partner_1",
                    "partner_name": "Partner A",
                    "fees_generated": Decimal("10500.30"),
                    "percentage": 42.0,
                    "efficiency_score": 87.5
                },
                {
                    "partner_id": "partner_2",
                    "partner_name": "Partner B", 
                    "fees_generated": Decimal("9250.25"),
                    "percentage": 37.0,
                    "efficiency_score": 92.1
                },
                {
                    "partner_id": "partner_3",
                    "partner_name": "Partner C",
                    "fees_generated": Decimal("5250.20"),
                    "percentage": 21.0,
                    "efficiency_score": 78.9
                }
            ]
            
            return {
                "period_days": days,
                "total_fees_collected": total_fees_collected,
                "average_fee_rate": avg_fee_rate,
                "fee_growth_rate": 18.2,  # %
                "fee_breakdown_by_type": fee_breakdown,
                "partner_contributions": partner_contributions,
                "optimization_suggestions": [
                    {
                        "type": "fee_adjustment",
                        "description": "Consider reducing withdrawal fees for high-volume partners",
                        "potential_impact": "15% transaction increase"
                    },
                    {
                        "type": "pricing_strategy",
                        "description": "Implement tiered pricing for API usage",
                        "potential_impact": "22% revenue increase"
                    }
                ],
                "market_comparison": {
                    "our_avg_rate": avg_fee_rate,
                    "market_avg_rate": Decimal("0.028"),
                    "competitive_position": "below_average",
                    "recommendation": "room_for_increase"
                }
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get fee analytics: {str(e)}")
    
    async def configure_dynamic_pricing(
        self, 
        partner_id: str, 
        pricing_rules: dict
    ) -> dict:
        """동적 가격 설정 구성"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")
            
            # 동적 가격 규칙 설정 (partner.settings에 저장)
            current_settings = partner.settings or {}
            current_settings["dynamic_pricing"] = {
                "enabled": pricing_rules.get("enabled", False),
                "rules": pricing_rules.get("rules", []),
                "updated_at": datetime.utcnow().isoformat(),
                "updated_by": "super_admin"
            }
            
            # 파트너 설정 업데이트
            # partner.settings = current_settings  # 실제로는 이렇게 업데이트
            
            return {
                "partner_id": partner_id,
                "dynamic_pricing_enabled": pricing_rules.get("enabled", False),
                "rules_count": len(pricing_rules.get("rules", [])),
                "configuration": current_settings["dynamic_pricing"],
                "status": "configured"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to configure dynamic pricing: {str(e)}")
