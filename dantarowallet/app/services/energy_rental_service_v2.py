"""
에너지 렌탈 서비스 (수정된 버전)

본사가 파트너사에게 TRON 에너지를 렌탈하는 서비스를 제공하는 핵심 서비스
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, update
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import logging

from app.models.energy_rental import (
    EnergyRentalPlan, EnergyUsageRecord, EnergyBillingRecord,
    EnergyPool, EnergyPricing, EnergyAllocation,
    RentalPlanType, SubscriptionTier, UsageStatus, PaymentStatus,
    get_subscription_tier_limits, calculate_energy_cost
)
from app.models.partners import Partner
from app.exceptions.energy_rental import (
    EnergyRentalException, InsufficientEnergyException,
    InvalidRentalPlanException, PaymentException
)

logger = logging.getLogger(__name__)

class EnergyRentalService:
    """에너지 렌탈 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_rental_plan(
        self,
        partner_id: int,
        plan_type: RentalPlanType,
        subscription_tier: Optional[SubscriptionTier] = None,
        **kwargs
    ) -> EnergyRentalPlan:
        """
        에너지 렌탈 플랜 생성
        
        Args:
            partner_id: 파트너 ID
            plan_type: 플랜 유형
            subscription_tier: 구독 등급 (구독제인 경우)
            **kwargs: 추가 설정
        
        Returns:
            생성된 렌탈 플랜
        """
        try:
            # 파트너 존재 확인
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise InvalidRentalPlanException(f"파트너 ID {partner_id}가 존재하지 않습니다")
            
            # 구독제인 경우 등급 정보 설정
            if plan_type == RentalPlanType.SUBSCRIPTION:
                if not subscription_tier:
                    raise InvalidRentalPlanException("구독제 플랜에는 구독 등급이 필요합니다")
                
                tier_limits = get_subscription_tier_limits(subscription_tier)
                kwargs.update({
                    'monthly_energy_quota': tier_limits.get('monthly_quota'),
                    'daily_limit': tier_limits.get('daily_limit'),
                    'monthly_fee': tier_limits.get('monthly_fee')
                })
            
            # 렌탈 플랜 생성
            rental_plan = EnergyRentalPlan(
                partner_id=partner_id,
                plan_name=kwargs.get('plan_name', f"{partner.name} {plan_type.value} Plan"),
                plan_type=plan_type,
                subscription_tier=subscription_tier,
                **kwargs
            )
            
            self.db.add(rental_plan)
            self.db.commit()
            self.db.refresh(rental_plan)
            
            logger.info(f"에너지 렌탈 플랜 생성: Partner {partner_id}, Plan {rental_plan.id}")
            return rental_plan
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"렌탈 플랜 생성 실패: {str(e)}")
            raise EnergyRentalException(f"렌탈 플랜 생성 실패: {str(e)}")
    
    def allocate_energy(
        self,
        partner_id: int,
        energy_amount: int,
        from_pool_id: Optional[int] = None
    ) -> EnergyAllocation:
        """
        파트너에게 에너지 할당
        
        Args:
            partner_id: 파트너 ID
            energy_amount: 할당할 에너지 양
            from_pool_id: 에너지 풀 ID (지정하지 않으면 자동 선택)
        
        Returns:
            에너지 할당 기록
        """
        try:
            # 에너지 풀 선택
            if from_pool_id:
                energy_pool = self.db.query(EnergyPool).filter(
                    EnergyPool.id == from_pool_id,
                    EnergyPool.is_active == True
                ).first()
            else:
                # 사용 가능한 에너지가 가장 많은 풀 선택
                energy_pool = self.db.query(EnergyPool).filter(
                    EnergyPool.is_active == True,
                    EnergyPool.available_energy >= energy_amount
                ).order_by(desc(EnergyPool.available_energy)).first()
            
            if not energy_pool:
                raise InsufficientEnergyException(f"할당 가능한 에너지가 부족합니다: {energy_amount}")
            
            # 에너지 풀 상태 확인
            if energy_pool.available_energy < energy_amount:
                raise InsufficientEnergyException(
                    f"에너지 풀 {energy_pool.id}에 충분한 에너지가 없습니다: "
                    f"요청 {energy_amount}, 사용가능 {energy_pool.available_energy}"
                )
            
            # 에너지 할당
            allocation = EnergyAllocation(
                partner_id=partner_id,
                energy_pool_id=energy_pool.id,
                allocated_energy=energy_amount,
                remaining_energy=energy_amount,
                allocation_date=datetime.now(timezone.utc),
                expiry_date=datetime.now(timezone.utc) + timedelta(days=30)  # 30일 유효
            )
            
            # 에너지 풀에서 차감 (update 사용)
            self.db.execute(
                update(EnergyPool)
                .where(EnergyPool.id == energy_pool.id)
                .values(
                    available_energy=energy_pool.available_energy - energy_amount,
                    reserved_energy=energy_pool.reserved_energy + energy_amount,
                    last_updated=datetime.now(timezone.utc)
                )
            )
            
            self.db.add(allocation)
            self.db.commit()
            self.db.refresh(allocation)
            
            logger.info(f"에너지 할당 완료: Partner {partner_id}, Amount {energy_amount}")
            return allocation
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"에너지 할당 실패: {str(e)}")
            raise EnergyRentalException(f"에너지 할당 실패: {str(e)}")
    
    def record_energy_usage(
        self,
        partner_id: int,
        energy_used: int,
        transaction_hash: str,
        from_address: str,
        to_address: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EnergyUsageRecord:
        """
        에너지 사용 기록
        
        Args:
            partner_id: 파트너 ID
            energy_used: 사용한 에너지
            transaction_hash: 트랜잭션 해시
            from_address: 송신 주소
            to_address: 수신 주소
            metadata: 추가 메타데이터
        
        Returns:
            에너지 사용 기록
        """
        try:
            # 활성 렌탈 플랜 조회
            rental_plan = self.db.query(EnergyRentalPlan).filter(
                EnergyRentalPlan.partner_id == partner_id,
                EnergyRentalPlan.is_active == True
            ).first()
            
            if not rental_plan:
                raise InvalidRentalPlanException(f"파트너 {partner_id}의 활성 렌탈 플랜이 없습니다")
            
            # 일일 한도 확인
            if rental_plan.daily_limit is not None and rental_plan.daily_limit > 0:
                today = datetime.now(timezone.utc).date()
                daily_usage = self.db.query(func.sum(EnergyUsageRecord.energy_used)).filter(
                    EnergyUsageRecord.partner_id == partner_id,
                    func.date(EnergyUsageRecord.used_at) == today
                ).scalar() or 0
                
                if daily_usage + energy_used > rental_plan.daily_limit:
                    raise EnergyRentalException(
                        f"일일 에너지 한도 초과: 한도 {rental_plan.daily_limit}, "
                        f"사용량 {daily_usage + energy_used}"
                    )
            
            # 월간 할당량 확인 (구독제인 경우)
            if (rental_plan.plan_type == RentalPlanType.SUBSCRIPTION and 
                rental_plan.monthly_energy_quota is not None and 
                rental_plan.monthly_energy_quota > 0):
                
                current_month = datetime.now(timezone.utc).replace(day=1)
                monthly_usage = self.db.query(func.sum(EnergyUsageRecord.energy_used)).filter(
                    EnergyUsageRecord.partner_id == partner_id,
                    EnergyUsageRecord.used_at >= current_month
                ).scalar() or 0
                
                if monthly_usage + energy_used > rental_plan.monthly_energy_quota:
                    raise EnergyRentalException(
                        f"월간 에너지 할당량 초과: 할당량 {rental_plan.monthly_energy_quota}, "
                        f"사용량 {monthly_usage + energy_used}"
                    )
            
            # 비용 계산
            total_cost = calculate_energy_cost(energy_used, rental_plan)
            
            # 사용 기록 생성
            usage_record = EnergyUsageRecord(
                rental_plan_id=rental_plan.id,
                partner_id=partner_id,
                energy_used=energy_used,
                transaction_hash=transaction_hash,
                from_address=from_address,
                to_address=to_address,
                unit_price=rental_plan.price_per_energy,
                total_cost=total_cost,
                used_at=datetime.now(timezone.utc),
                metadata=metadata
            )
            
            # 렌탈 플랜 사용량 업데이트
            current_monthly_used = self.db.query(EnergyRentalPlan.monthly_energy_used).filter(
                EnergyRentalPlan.id == rental_plan.id
            ).scalar() or 0
            
            self.db.execute(
                update(EnergyRentalPlan)
                .where(EnergyRentalPlan.id == rental_plan.id)
                .values(monthly_energy_used=current_monthly_used + energy_used)
            )
            
            self.db.add(usage_record)
            self.db.commit()
            self.db.refresh(usage_record)
            
            logger.info(f"에너지 사용 기록: Partner {partner_id}, Energy {energy_used}")
            return usage_record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"에너지 사용 기록 실패: {str(e)}")
            raise EnergyRentalException(f"에너지 사용 기록 실패: {str(e)}")
    
    def generate_billing_record(
        self,
        partner_id: int,
        billing_period_start: datetime,
        billing_period_end: datetime
    ) -> EnergyBillingRecord:
        """
        청구서 생성
        
        Args:
            partner_id: 파트너 ID
            billing_period_start: 청구 기간 시작
            billing_period_end: 청구 기간 종료
        
        Returns:
            청구 기록
        """
        try:
            # 렌탈 플랜 조회
            rental_plan = self.db.query(EnergyRentalPlan).filter(
                EnergyRentalPlan.partner_id == partner_id,
                EnergyRentalPlan.is_active == True
            ).first()
            
            if not rental_plan:
                raise InvalidRentalPlanException(f"파트너 {partner_id}의 활성 렌탈 플랜이 없습니다")
            
            # 청구 기간 내 사용량 집계
            usage_records = self.db.query(EnergyUsageRecord).filter(
                EnergyUsageRecord.partner_id == partner_id,
                EnergyUsageRecord.used_at >= billing_period_start,
                EnergyUsageRecord.used_at <= billing_period_end,
                EnergyUsageRecord.status == UsageStatus.CONFIRMED
            ).all()
            
            total_energy_used = sum(record.energy_used for record in usage_records)
            total_cost = sum(record.total_cost for record in usage_records)
            
            # 월 구독료 추가
            monthly_fee = rental_plan.monthly_fee or Decimal("0")
            
            # 할인 적용
            discount_amount = Decimal("0")
            if rental_plan.discount_rate is not None and rental_plan.discount_rate > 0:
                discount_amount = total_cost * rental_plan.discount_rate
            
            # 최종 청구 금액
            final_amount = total_cost + monthly_fee - discount_amount
            
            # 청구서 번호 생성
            invoice_number = f"INV-{partner_id}-{billing_period_start.strftime('%Y%m')}-{datetime.now().strftime('%d%H%M%S')}"
            
            # 청구 기록 생성
            billing_record = EnergyBillingRecord(
                rental_plan_id=rental_plan.id,
                partner_id=partner_id,
                billing_period_start=billing_period_start,
                billing_period_end=billing_period_end,
                total_energy_used=total_energy_used,
                total_cost=total_cost,
                monthly_fee=monthly_fee,
                discount_amount=discount_amount,
                final_amount=final_amount,
                invoice_number=invoice_number,
                due_date=datetime.now(timezone.utc) + timedelta(days=30)  # 30일 후 만료
            )
            
            # 사용 기록 상태 업데이트
            usage_record_ids = [record.id for record in usage_records]
            if usage_record_ids:
                self.db.execute(
                    update(EnergyUsageRecord)
                    .where(EnergyUsageRecord.id.in_(usage_record_ids))
                    .values(status=UsageStatus.BILLED)
                )
            
            self.db.add(billing_record)
            self.db.commit()
            self.db.refresh(billing_record)
            
            logger.info(f"청구서 생성: Partner {partner_id}, Amount {final_amount}")
            return billing_record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"청구서 생성 실패: {str(e)}")
            raise EnergyRentalException(f"청구서 생성 실패: {str(e)}")
    
    def get_partner_usage_statistics(
        self,
        partner_id: int,
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """
        파트너의 에너지 사용 통계 조회
        
        Args:
            partner_id: 파트너 ID
            period_start: 조회 기간 시작
            period_end: 조회 기간 종료
        
        Returns:
            사용 통계 데이터
        """
        try:
            # 기본 통계
            usage_query = self.db.query(EnergyUsageRecord).filter(
                EnergyUsageRecord.partner_id == partner_id,
                EnergyUsageRecord.used_at >= period_start,
                EnergyUsageRecord.used_at <= period_end
            )
            
            total_energy_used = usage_query.with_entities(
                func.sum(EnergyUsageRecord.energy_used)
            ).scalar() or 0
            
            total_cost = usage_query.with_entities(
                func.sum(EnergyUsageRecord.total_cost)
            ).scalar() or Decimal("0")
            
            usage_count = usage_query.count()
            
            # 일별 사용량
            daily_usage = self.db.query(
                func.date(EnergyUsageRecord.used_at).label('date'),
                func.sum(EnergyUsageRecord.energy_used).label('energy_used'),
                func.sum(EnergyUsageRecord.total_cost).label('cost')
            ).filter(
                EnergyUsageRecord.partner_id == partner_id,
                EnergyUsageRecord.used_at >= period_start,
                EnergyUsageRecord.used_at <= period_end
            ).group_by(func.date(EnergyUsageRecord.used_at)).all()
            
            # 평균 단가
            avg_unit_price = usage_query.with_entities(
                func.avg(EnergyUsageRecord.unit_price)
            ).scalar() or Decimal("0")
            
            return {
                'total_energy_used': total_energy_used,
                'total_cost': float(total_cost),
                'usage_count': usage_count,
                'avg_unit_price': float(avg_unit_price),
                'daily_usage': [
                    {
                        'date': str(day.date),
                        'energy_used': day.energy_used,
                        'cost': float(day.cost)
                    }
                    for day in daily_usage
                ],
                'period_start': period_start.isoformat(),
                'period_end': period_end.isoformat()
            }
            
        except Exception as e:
            logger.error(f"사용 통계 조회 실패: {str(e)}")
            raise EnergyRentalException(f"사용 통계 조회 실패: {str(e)}")
    
    def get_energy_pool_status(self) -> List[Dict[str, Any]]:
        """
        에너지 풀 상태 조회
        
        Returns:
            에너지 풀 상태 목록
        """
        try:
            pools = self.db.query(EnergyPool).filter(
                EnergyPool.is_active == True
            ).all()
            
            pool_status = []
            for pool in pools:
                total_energy = pool.total_energy or 0
                available_energy = pool.available_energy or 0
                
                utilization_rate = (
                    (total_energy - available_energy) / total_energy * 100
                    if total_energy > 0 else 0
                )
                
                status = "normal"
                emergency_threshold = pool.emergency_threshold or 0
                low_threshold = pool.low_energy_threshold or 0
                
                if available_energy <= emergency_threshold:
                    status = "emergency"
                elif available_energy <= low_threshold:
                    status = "low"
                
                pool_status.append({
                    'id': pool.id,
                    'name': pool.pool_name,
                    'total_energy': total_energy,
                    'available_energy': available_energy,
                    'reserved_energy': pool.reserved_energy or 0,
                    'utilization_rate': round(float(utilization_rate), 2),
                    'status': status,
                    'staked_trx': float(pool.staked_trx) if pool.staked_trx else 0,
                    'energy_per_trx': float(pool.energy_per_trx) if pool.energy_per_trx else 0,
                    'last_updated': pool.last_updated.isoformat() if pool.last_updated else None
                })
            
            return pool_status
            
        except Exception as e:
            logger.error(f"에너지 풀 상태 조회 실패: {str(e)}")
            raise EnergyRentalException(f"에너지 풀 상태 조회 실패: {str(e)}")
    
    def auto_recharge_check(self, partner_id: int) -> bool:
        """
        자동 재충전 확인 및 실행
        
        Args:
            partner_id: 파트너 ID
        
        Returns:
            재충전 실행 여부
        """
        try:
            # 자동 재충전 설정된 플랜 조회
            rental_plan = self.db.query(EnergyRentalPlan).filter(
                EnergyRentalPlan.partner_id == partner_id,
                EnergyRentalPlan.is_active == True,
                EnergyRentalPlan.auto_recharge_enabled == True
            ).first()
            
            if not rental_plan:
                return False
            
            # 잔여 에너지 확인
            remaining_energy = self.get_partner_remaining_energy(partner_id)
            threshold = rental_plan.auto_recharge_threshold or 0
            
            if remaining_energy <= threshold:
                # 자동 재충전 실행
                recharge_amount = int(rental_plan.auto_recharge_amount or 1000000)  # 기본 100만 에너지
                
                self.allocate_energy(partner_id, recharge_amount)
                
                logger.info(f"자동 재충전 실행: Partner {partner_id}, Amount {recharge_amount}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"자동 재충전 확인 실패: {str(e)}")
            return False
    
    def get_partner_remaining_energy(self, partner_id: int) -> int:
        """
        파트너의 잔여 에너지 조회
        
        Args:
            partner_id: 파트너 ID
        
        Returns:
            잔여 에너지
        """
        try:
            allocation = self.db.query(EnergyAllocation).filter(
                EnergyAllocation.partner_id == partner_id,
                EnergyAllocation.is_active == True,
                EnergyAllocation.expiry_date > datetime.now(timezone.utc)
            ).first()
            
            return allocation.remaining_energy if allocation else 0
            
        except Exception as e:
            logger.error(f"잔여 에너지 조회 실패: {str(e)}")
            return 0
