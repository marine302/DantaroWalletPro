"""
에너지 렌탈 서비스

본사가 파트너사에게 TRON 에너지를 렌탈하는 서비스를 제공하는 핵심 서비스
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Union
import logging

from app.models.energy_rental import (
    EnergyRentalPlan, EnergyUsageRecord, EnergyBillingRecord,
    EnergyPool, EnergyPricing, EnergyAllocation,
    RentalPlanType, SubscriptionTier, UsageStatus, PaymentStatus,
    get_subscription_tier_limits, calculate_energy_cost
)
from app.models.partner import Partner
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
        partner_id: Union[int, str],
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
        partner_id: Union[int, str],
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
            
            # 에너지 풀에서 할당 가능한 에너지 확인
            available_energy_val = getattr(energy_pool, "available_energy", 0)
            if int(available_energy_val) < energy_amount:
                raise InsufficientEnergyException(
                    f"풀에서 할당 가능한 에너지가 부족합니다: 요청 {energy_amount}, 가용 {int(available_energy_val)}"
                )
            
            # 에너지 풀에서 에너지 차감
            new_available = int(available_energy_val) - energy_amount
            setattr(energy_pool, "available_energy", new_available)
            
            # 에너지 할당 기록 생성
            allocation = EnergyAllocation(
                partner_id=partner_id,
                energy_pool_id=energy_pool.id,
                allocated_energy=energy_amount,
                remaining_energy=energy_amount,
                expiry_date=datetime.now(timezone.utc) + timedelta(days=30),  # 30일 유효
                is_active=True,
                allocated_at=datetime.now(timezone.utc)
            )
            
            self.db.add(allocation)
            self.db.commit()
            self.db.refresh(allocation)
            
            logger.info(f"에너지 할당 완료: Partner {partner_id}, Energy {energy_amount}")
            return allocation
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"에너지 사용 기록 실패: {str(e)}")
            raise EnergyRentalException(f"에너지 사용 기록 실패: {str(e)}")
    
    def generate_billing_record(
        self,
        partner_id: Union[int, str],
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
            monthly_fee_val = getattr(rental_plan, "monthly_fee", 0)
            monthly_fee = Decimal(str(monthly_fee_val)) if monthly_fee_val else Decimal("0")
            
            # 할인 적용
            discount_amount = Decimal("0")
            discount_rate_val = getattr(rental_plan, "discount_rate", 0)
            if float(discount_rate_val) > 0:
                discount_amount = Decimal(str(total_cost)) * Decimal(str(discount_rate_val))
            
            # 최종 청구 금액
            final_amount = Decimal(str(total_cost)) + monthly_fee - discount_amount
            
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
            for record in usage_records:
                setattr(record, "status", UsageStatus.BILLED.value)
            
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
        partner_id: Union[int, str],
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
                total_energy_val = getattr(pool, "total_energy", 0)
                available_energy_val = getattr(pool, "available_energy", 0)
                utilization_rate = (float(total_energy_val) - float(available_energy_val)) / float(total_energy_val) * 100 if float(total_energy_val) > 0 else 0
                
                status = "normal"
                if float(available_energy_val) <= float(getattr(pool, "emergency_threshold", 0)):
                    status = "emergency"
                elif float(available_energy_val) <= float(getattr(pool, "low_energy_threshold", 0)):
                    status = "low"
                
                pool_status.append({
                    'id': pool.id,
                    'name': getattr(pool, "pool_name", "Unknown"),
                    'total_energy': int(total_energy_val),
                    'available_energy': int(available_energy_val),
                    'reserved_energy': int(getattr(pool, "reserved_energy", 0)),
                    'utilization_rate': round(float(utilization_rate), 2),
                    'status': status,
                    'staked_trx': float(getattr(pool, "staked_trx", 0)),
                    'energy_per_trx': float(getattr(pool, "energy_per_trx", 0)),
                    'last_updated': getattr(pool, "last_updated", datetime.now(timezone.utc)).isoformat()
                })
            
            return pool_status
            
        except Exception as e:
            logger.error(f"에너지 풀 상태 조회 실패: {str(e)}")
            raise EnergyRentalException(f"에너지 풀 상태 조회 실패: {str(e)}")
    
    def auto_recharge_check(self, partner_id: Union[int, str]) -> bool:
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
            
            auto_recharge_threshold_val = getattr(rental_plan, "auto_recharge_threshold", 0)
            if remaining_energy <= int(auto_recharge_threshold_val):
                # 자동 재충전 실행
                auto_recharge_amount_val = getattr(rental_plan, "auto_recharge_amount", 1000000)
                recharge_amount = int(float(auto_recharge_amount_val))
                
                self.allocate_energy(partner_id, recharge_amount)
                
                logger.info(f"자동 재충전 실행: Partner {partner_id}, Amount {recharge_amount}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"자동 재충전 확인 실패: {str(e)}")
            return False
    
    def get_partner_remaining_energy(self, partner_id: Union[int, str]) -> int:
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
            
            if allocation:
                remaining_energy_val = getattr(allocation, "remaining_energy", 0)
                return int(remaining_energy_val)
            else:
                return 0
            
        except Exception as e:
            logger.error(f"잔여 에너지 조회 실패: {str(e)}")
            return 0
    
    def record_energy_usage(
        self,
        partner_id: Union[int, str],
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
            metadata: 메타데이터
        
        Returns:
            에너지 사용 기록
        """
        try:
            # 렌탈 플랜 조회
            rental_plan = self.db.query(EnergyRentalPlan).filter(
                EnergyRentalPlan.partner_id == partner_id,
                EnergyRentalPlan.is_active == True
            ).first()
            
            if not rental_plan:
                raise InvalidRentalPlanException(f"파트너 {partner_id}의 활성 렌탈 플랜이 없습니다")
            
            # 한도 확인
            current_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # 조건문에서 컬럼 값 추출
            daily_limit_val = getattr(rental_plan, "daily_limit", None)
            if daily_limit_val is not None and int(daily_limit_val) > 0:
                # 일일 한도 확인
                today = datetime.now(timezone.utc).date()
                daily_usage = self.db.query(func.sum(EnergyUsageRecord.energy_used)).filter(
                    EnergyUsageRecord.partner_id == partner_id,
                    func.date(EnergyUsageRecord.used_at) == today
                ).scalar() or 0
                
                if int(daily_usage) + energy_used > int(daily_limit_val):
                    raise EnergyRentalException(
                        f"일일 에너지 한도 초과: 한도 {int(daily_limit_val)}, 사용량 {int(daily_usage) + energy_used}"
                    )
            
            # 월간 한도 체크
            monthly_quota_val = getattr(rental_plan, "monthly_energy_quota", None)
            plan_type_val = getattr(rental_plan, "plan_type", None)
            if (plan_type_val == RentalPlanType.SUBSCRIPTION and 
                monthly_quota_val is not None and int(monthly_quota_val) > 0):
                monthly_usage = self.db.query(func.sum(EnergyUsageRecord.energy_used)).filter(
                    EnergyUsageRecord.partner_id == partner_id,
                    EnergyUsageRecord.used_at >= current_month
                ).scalar() or 0
                
                if int(monthly_usage) + energy_used > int(monthly_quota_val):
                    raise EnergyRentalException(
                        f"월간 에너지 할당량 초과: 할당량 {int(monthly_quota_val)}, 사용량 {int(monthly_usage) + energy_used}"
                    )
            
            # 단가 및 총 비용 계산
            price_per_energy_val = getattr(rental_plan, "price_per_energy", 0)
            unit_price = Decimal(str(price_per_energy_val))
            total_cost = unit_price * Decimal(str(energy_used))
            
            # 사용 기록 생성
            usage_record = EnergyUsageRecord(
                rental_plan_id=rental_plan.id,
                partner_id=partner_id,
                energy_used=energy_used,
                transaction_hash=transaction_hash,
                from_address=from_address,
                to_address=to_address,
                unit_price=unit_price,
                total_cost=total_cost,
                used_at=datetime.now(timezone.utc),
                meta_data=metadata
            )
            
            # 렌탈 플랜 사용량 업데이트
            monthly_used_val = getattr(rental_plan, "monthly_energy_used", 0)
            setattr(rental_plan, "monthly_energy_used", int(monthly_used_val) + energy_used)
            
            self.db.add(usage_record)
            self.db.commit()
            self.db.refresh(usage_record)
            
            logger.info(f"에너지 사용 기록: Partner {partner_id}, Energy {energy_used}")
            return usage_record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"에너지 사용 기록 실패: {str(e)}")
            raise EnergyRentalException(f"에너지 사용 기록 실패: {str(e)}")
    
    def update_energy_pool_status(self, pool_id: int, new_status: bool) -> bool:
        """
        에너지 풀 상태 업데이트
        
        Args:
            pool_id: 풀 ID
            new_status: 새 상태 (True: 활성, False: 비활성)
        
        Returns:
            업데이트 성공 여부
        """
        try:
            energy_pool = self.db.query(EnergyPool).filter(
                EnergyPool.id == pool_id
            ).first()
            
            if not energy_pool:
                logger.error(f"에너지 풀을 찾을 수 없음: {pool_id}")
                return False
            
            setattr(energy_pool, "is_active", new_status)
            setattr(energy_pool, "last_updated", datetime.now(timezone.utc))
            
            self.db.commit()
            
            logger.info(f"에너지 풀 상태 업데이트: Pool {pool_id}, Status {new_status}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"에너지 풀 상태 업데이트 실패: {str(e)}")
            return False
    
    def get_billing_history(
        self,
        partner_id: Union[int, str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        청구 이력 조회
        
        Args:
            partner_id: 파트너 ID
            start_date: 조회 시작 날짜
            end_date: 조회 종료 날짜
        
        Returns:
            청구 이력 목록
        """
        try:
            query = self.db.query(EnergyBillingRecord).filter(
                EnergyBillingRecord.partner_id == partner_id
            )
            
            if start_date:
                query = query.filter(EnergyBillingRecord.billing_period_start >= start_date)
            if end_date:
                query = query.filter(EnergyBillingRecord.billing_period_end <= end_date)
            
            billing_records = query.order_by(desc(EnergyBillingRecord.billing_period_start)).all()
            
            billing_history = []
            for record in billing_records:
                billing_history.append({
                    'id': record.id,
                    'invoice_number': getattr(record, "invoice_number", ""),
                    'billing_period_start': getattr(record, "billing_period_start", datetime.now(timezone.utc)).isoformat(),
                    'billing_period_end': getattr(record, "billing_period_end", datetime.now(timezone.utc)).isoformat(),
                    'total_energy_used': int(getattr(record, "total_energy_used", 0)),
                    'total_cost': float(getattr(record, "total_cost", 0)),
                    'monthly_fee': float(getattr(record, "monthly_fee", 0)),
                    'discount_amount': float(getattr(record, "discount_amount", 0)),
                    'final_amount': float(getattr(record, "final_amount", 0)),
                    'payment_status': getattr(record, "payment_status", PaymentStatus.PENDING.value),
                    'due_date': getattr(record, "due_date", datetime.now(timezone.utc)).isoformat(),
                    'created_at': getattr(record, "created_at", datetime.now(timezone.utc)).isoformat()
                })
            
            return billing_history
            
        except Exception as e:
            logger.error(f"청구 이력 조회 실패: {str(e)}")
            raise EnergyRentalException(f"청구 이력 조회 실패: {str(e)}")
    
    def update_payment_status(self, billing_record_id: int, payment_status: PaymentStatus) -> bool:
        """
        결제 상태 업데이트
        
        Args:
            billing_record_id: 청구 기록 ID
            payment_status: 결제 상태
        
        Returns:
            업데이트 성공 여부
        """
        try:
            billing_record = self.db.query(EnergyBillingRecord).filter(
                EnergyBillingRecord.id == billing_record_id
            ).first()
            
            if not billing_record:
                logger.error(f"청구 기록을 찾을 수 없음: {billing_record_id}")
                return False
            
            setattr(billing_record, "payment_status", payment_status.value)
            if payment_status.value == "paid":
                setattr(billing_record, "paid_at", datetime.now(timezone.utc))
            
            self.db.commit()
            
            logger.info(f"결제 상태 업데이트: Billing {billing_record_id}, Status {payment_status.value}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"결제 상태 업데이트 실패: {str(e)}")
            return False
    
    def get_partner_energy_allocation(self, partner_id: Union[int, str]) -> Dict[str, Any]:
        """
        파트너의 에너지 할당 정보 조회
        
        Args:
            partner_id: 파트너 ID
        
        Returns:
            에너지 할당 정보
        """
        try:
            allocation = self.db.query(EnergyAllocation).filter(
                EnergyAllocation.partner_id == partner_id,
                EnergyAllocation.is_active == True,
                EnergyAllocation.expiry_date > datetime.now(timezone.utc)
            ).first()
            
            if not allocation:
                return {
                    'partner_id': partner_id,
                    'allocated_energy': 0,
                    'remaining_energy': 0,
                    'is_active': False,
                    'expiry_date': None
                }
            
            return {
                'id': allocation.id,
                'partner_id': partner_id,
                'energy_pool_id': getattr(allocation, "energy_pool_id", None),
                'allocated_energy': int(getattr(allocation, "allocated_energy", 0)),
                'remaining_energy': int(getattr(allocation, "remaining_energy", 0)),
                'is_active': bool(getattr(allocation, "is_active", False)),
                'expiry_date': getattr(allocation, "expiry_date", datetime.now(timezone.utc)).isoformat(),
                'allocated_at': getattr(allocation, "allocated_at", datetime.now(timezone.utc)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"에너지 할당 정보 조회 실패: {str(e)}")
            raise EnergyRentalException(f"에너지 할당 정보 조회 실패: {str(e)}")
    
    def deactivate_rental_plan(self, plan_id: int) -> bool:
        """
        렌탈 플랜 비활성화
        
        Args:
            plan_id: 렌탈 플랜 ID
        
        Returns:
            비활성화 성공 여부
        """
        try:
            rental_plan = self.db.query(EnergyRentalPlan).filter(
                EnergyRentalPlan.id == plan_id
            ).first()
            
            if not rental_plan:
                logger.error(f"렌탈 플랜을 찾을 수 없음: {plan_id}")
                return False
            
            setattr(rental_plan, "is_active", False)
            setattr(rental_plan, "deactivated_at", datetime.now(timezone.utc))
            
            self.db.commit()
            
            logger.info(f"렌탈 플랜 비활성화: Plan {plan_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"렌탈 플랜 비활성화 실패: {str(e)}")
            return False
    
    def get_active_rental_plans(self, partner_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        활성 렌탈 플랜 조회
        
        Args:
            partner_id: 파트너 ID (지정하지 않으면 모든 파트너)
        
        Returns:
            활성 렌탈 플랜 목록
        """
        try:
            query = self.db.query(EnergyRentalPlan).filter(
                EnergyRentalPlan.is_active == True
            )
            
            if partner_id:
                query = query.filter(EnergyRentalPlan.partner_id == partner_id)
            
            rental_plans = query.all()
            
            plans_data = []
            for plan in rental_plans:
                plans_data.append({
                    'id': plan.id,
                    'partner_id': getattr(plan, "partner_id", None),
                    'plan_name': getattr(plan, "plan_name", ""),
                    'plan_type': str(getattr(plan, "plan_type", "")),
                    'subscription_tier': str(getattr(plan, "subscription_tier", "")),
                    'monthly_energy_quota': int(getattr(plan, "monthly_energy_quota", 0)),
                    'price_per_energy': float(getattr(plan, "price_per_energy", 0)),
                    'created_at': getattr(plan, "created_at", datetime.now(timezone.utc)).isoformat()
                })
            
            return plans_data
            
        except Exception as e:
            logger.error(f"활성 렌탈 플랜 조회 실패: {str(e)}")
            return []
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        시스템 상태 조회
        
        Returns:
            시스템 상태 정보
        """
        try:
            # 전체 에너지 풀 통계
            total_pools = self.db.query(EnergyPool).count()
            active_pools = self.db.query(EnergyPool).filter(EnergyPool.is_active == True).count()
            
            # 전체 에너지 통계
            total_energy = self.db.query(func.sum(EnergyPool.total_energy)).filter(
                EnergyPool.is_active == True
            ).scalar() or 0
            
            available_energy = self.db.query(func.sum(EnergyPool.available_energy)).filter(
                EnergyPool.is_active == True
            ).scalar() or 0
            
            # 활성 렌탈 플랜 수
            active_rental_plans = self.db.query(EnergyRentalPlan).filter(
                EnergyRentalPlan.is_active == True
            ).count()
            
            # 오늘 에너지 사용량
            today = datetime.now(timezone.utc).date()
            today_usage = self.db.query(func.sum(EnergyUsageRecord.energy_used)).filter(
                func.date(EnergyUsageRecord.used_at) == today
            ).scalar() or 0
            
            return {
                'total_pools': total_pools,
                'active_pools': active_pools,
                'total_energy': int(total_energy),
                'available_energy': int(available_energy),
                'utilization_rate': round((int(total_energy) - int(available_energy)) / int(total_energy) * 100, 2) if int(total_energy) > 0 else 0,
                'active_rental_plans': active_rental_plans,
                'today_usage': int(today_usage),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"시스템 상태 조회 실패: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
