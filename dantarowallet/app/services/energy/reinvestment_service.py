"""
에너지 재투자 서비스 - 문서 #40 기반
"""

from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.company_wallet import CompanyWallet, CompanyWalletType
from app.models.energy_supplier import EnergySupplier, SupplierType
from app.core.logging import get_logger

logger = get_logger(__name__)


class EnergyReinvestmentService:
    """에너지 재투자 서비스"""

    def __init__(self, db: Session):
        self.db = db

    async def calculate_reinvestment_amount(self) -> Dict:
        """재투자 가능 금액 계산"""
        try:
            # 본사 수익금 지갑 조회
            revenue_wallet = self.db.query(CompanyWallet).filter(
                CompanyWallet.wallet_type == CompanyWalletType.REVENUE
            ).first()

            if not revenue_wallet:
                raise ValueError("수익금 지갑을 찾을 수 없습니다")

            # 현재 수익금 잔액 조회
            current_balance = await self._get_wallet_balance(revenue_wallet.address)  # type: ignore
            
            # 재투자 정책 적용
            min_reserve = Decimal("50000")  # 최소 보유 금액
            max_reinvest_ratio = Decimal("0.7")  # 최대 재투자 비율 70%

            if current_balance <= min_reserve:
                reinvestable_amount = Decimal("0")
            else:
                available_for_reinvest = current_balance - min_reserve
                reinvestable_amount = available_for_reinvest * max_reinvest_ratio

            return {
                "current_balance": float(current_balance),
                "min_reserve": float(min_reserve),
                "available_for_reinvest": float(available_for_reinvest) if 'available_for_reinvest' in locals() else 0,
                "recommended_reinvest": float(reinvestable_amount),
                "max_reinvest_ratio": float(max_reinvest_ratio),
                "can_reinvest": reinvestable_amount > 0
            }

        except Exception as e:
            logger.error(f"재투자 금액 계산 실패: {e}")
            return {
                "error": str(e),
                "can_reinvest": False
            }

    async def execute_staking_reinvestment(self, amount_trx: Decimal) -> Dict:
        """스테이킹 재투자 실행"""
        try:
            # 수익금 지갑에서 스테이킹 지갑으로 이체
            revenue_wallet = self.db.query(CompanyWallet).filter(
                CompanyWallet.wallet_type == CompanyWalletType.REVENUE
            ).first()

            staking_wallet = self.db.query(CompanyWallet).filter(
                CompanyWallet.wallet_type == CompanyWalletType.STAKING
            ).first()

            if not revenue_wallet or not staking_wallet:
                raise ValueError("필요한 지갑을 찾을 수 없습니다")

            # 자금 이체
            transfer_result = await self._transfer_funds(
                from_address=revenue_wallet.address,  # type: ignore
                to_address=staking_wallet.address,  # type: ignore
                amount=amount_trx
            )

            if not transfer_result["success"]:
                raise Exception(f"자금 이체 실패: {transfer_result.get('error')}")

            # 스테이킹 실행
            staking_result = await self._execute_staking(
                wallet_address=staking_wallet.address,  # type: ignore
                amount_trx=amount_trx
            )

            if staking_result["success"]:
                # 자체 스테이킹 공급원 업데이트
                self_staking = self.db.query(EnergySupplier).filter(
                    EnergySupplier.supplier_type == SupplierType.SELF_STAKING
                ).first()

                if self_staking:
                    # 새로운 에너지 용량 계산 (1 TRX = ~28,000 에너지)
                    additional_energy = int(amount_trx * 28000)
                    
                    self.db.query(EnergySupplier).filter(
                        EnergySupplier.id == self_staking.id
                    ).update({
                        'max_energy_capacity': EnergySupplier.max_energy_capacity + additional_energy,
                        'available_energy': EnergySupplier.available_energy + additional_energy,
                        'daily_energy_generation': EnergySupplier.daily_energy_generation + additional_energy
                    })

                self.db.commit()

                logger.info(f"스테이킹 재투자 완료: {amount_trx} TRX")

                return {
                    "success": True,
                    "amount_invested": float(amount_trx),
                    "transfer_tx_hash": transfer_result.get("tx_hash"),
                    "staking_tx_hash": staking_result.get("tx_hash"),
                    "additional_energy": additional_energy if 'additional_energy' in locals() else 0,
                    "reinvestment_type": "staking"
                }
            else:
                raise Exception(f"스테이킹 실행 실패: {staking_result.get('error')}")

        except Exception as e:
            logger.error(f"스테이킹 재투자 실패: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }

    async def execute_auto_reinvestment(self) -> Dict:
        """자동 재투자 실행"""
        try:
            # 재투자 가능 금액 계산
            calc_result = await self.calculate_reinvestment_amount()
            
            if not calc_result.get("can_reinvest"):
                return {
                    "action": "none",
                    "message": "재투자 가능한 금액이 없습니다",
                    "current_balance": calc_result.get("current_balance", 0)
                }

            recommended_amount = Decimal(str(calc_result["recommended_reinvest"]))
            
            # 최소 재투자 금액 체크
            min_reinvest = Decimal("1000")  # 최소 1000 TRX
            if recommended_amount < min_reinvest:
                return {
                    "action": "deferred",
                    "message": f"재투자 금액이 최소 기준({min_reinvest} TRX)보다 작습니다",
                    "recommended_amount": float(recommended_amount)
                }

            # 스테이킹 재투자 실행
            reinvest_result = await self.execute_staking_reinvestment(recommended_amount)

            if reinvest_result["success"]:
                return {
                    "action": "reinvested",
                    "reinvestment_result": reinvest_result,
                    "strategy": "auto_staking"
                }
            else:
                return {
                    "action": "failed",
                    "error": reinvest_result.get("error")
                }

        except Exception as e:
            logger.error(f"자동 재투자 실행 실패: {e}")
            return {
                "action": "failed",
                "error": str(e)
            }

    async def get_reinvestment_history(self, days: int = 30) -> List[Dict]:
        """재투자 이력 조회"""
        try:
            # 실제로는 재투자 이력 테이블에서 조회
            # 여기서는 간단한 예시 데이터 반환
            from datetime import timedelta
            
            history = []
            base_date = datetime.utcnow()
            
            # 예시 데이터 (실제로는 DB에서 조회)
            for i in range(min(days, 10)):  # 최근 10건만
                if i % 3 == 0:  # 3일마다 재투자했다고 가정
                    history.append({
                        "date": (base_date - timedelta(days=i)).isoformat(),
                        "type": "staking",
                        "amount_trx": 5000.0 + (i * 100),
                        "additional_energy": 140000 + (i * 2800),
                        "status": "completed",
                        "roi_estimate": "8.5%"
                    })

            return history

        except Exception as e:
            logger.error(f"재투자 이력 조회 실패: {e}")
            return []

    async def get_reinvestment_analytics(self) -> Dict:
        """재투자 분석 데이터"""
        try:
            # 자체 스테이킹 공급원 조회
            self_staking = self.db.query(EnergySupplier).filter(
                EnergySupplier.supplier_type == SupplierType.SELF_STAKING
            ).first()

            analytics = {
                "total_staked_capacity": 0,
                "current_energy_generation": 0,
                "estimated_monthly_revenue": 0.0,
                "staking_efficiency": 0.0,
                "reinvestment_recommendation": "maintain"
            }

            if self_staking:
                analytics.update({
                    "total_staked_capacity": self_staking.max_energy_capacity or 0,
                    "current_energy_generation": self_staking.daily_energy_generation or 0,
                    "estimated_monthly_revenue": float((self_staking.daily_energy_generation or 0) * 30 * (self_staking.cost_per_energy or 0)),  # type: ignore
                    "staking_efficiency": 85.2,  # 예시 효율성
                })

                # 재투자 추천 로직
                if analytics["current_energy_generation"] < 1000000:  # 100만 에너지 미만
                    analytics["reinvestment_recommendation"] = "increase"
                elif analytics["staking_efficiency"] > 90:
                    analytics["reinvestment_recommendation"] = "maintain"
                else:
                    analytics["reinvestment_recommendation"] = "optimize"

            return analytics

        except Exception as e:
            logger.error(f"재투자 분석 실패: {e}")
            return {
                "error": str(e)
            }

    async def _get_wallet_balance(self, address: str) -> Decimal:
        """지갑 잔액 조회"""
        # 실제로는 TRON API 호출
        return Decimal("100000")  # 임시 값

    async def _transfer_funds(self, from_address: str, to_address: str, amount: Decimal) -> Dict:
        """자금 이체"""
        # 실제로는 TRON 트랜잭션
        import uuid
        return {
            "success": True,
            "tx_hash": f"0x{uuid.uuid4().hex}",
            "amount": float(amount)
        }

    async def _execute_staking(self, wallet_address: str, amount_trx: Decimal) -> Dict:
        """스테이킹 실행"""
        # 실제로는 TRON 스테이킹 트랜잭션
        import uuid
        return {
            "success": True,
            "tx_hash": f"0x{uuid.uuid4().hex}",
            "staked_amount": float(amount_trx),
            "expected_energy": int(amount_trx * 28000)
        }
