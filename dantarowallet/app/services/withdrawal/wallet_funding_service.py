"""
지갑 자금 조달 서비스 - 문서 #41 기반
"""

from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.partner_wallet import PartnerWallet, WalletType
from app.models.partner import Partner
from app.models.company_wallet import CompanyWallet, CompanyWalletType
from app.core.logging import get_logger

logger = get_logger(__name__)


class WalletFundingService:
    """지갑 자금 조달 서비스"""

    def __init__(self, db: Session):
        self.db = db

    async def fund_partner_wallet(
        self,
        partner_id: int,
        wallet_type: WalletType,
        amount_usdt: Decimal,
        purpose: str = "출금 처리"
    ) -> Dict:
        """파트너 지갑에 자금 지원"""
        try:
            # 파트너 지갑 조회
            partner_wallet = self.db.query(PartnerWallet).filter(
                PartnerWallet.partner_id == partner_id,
                PartnerWallet.wallet_type == wallet_type
            ).first()

            if not partner_wallet:
                raise ValueError("파트너 지갑을 찾을 수 없습니다")

            # 본사 운영 지갑 조회
            company_wallet = self.db.query(CompanyWallet).filter(
                CompanyWallet.wallet_type == CompanyWalletType.OPERATING
            ).first()

            if not company_wallet:
                raise ValueError("본사 운영 지갑을 찾을 수 없습니다")

            # 본사 지갑 잔액 확인
            company_balance = await self._get_wallet_balance(company_wallet.address)  # type: ignore
            if company_balance < amount_usdt:
                raise ValueError("본사 지갑 잔액이 부족합니다")

            # 자금 이체 실행 (실제로는 TRON 네트워크 호출)
            transfer_result = await self._transfer_funds(
                from_address=company_wallet.address,  # type: ignore
                to_address=partner_wallet.address,  # type: ignore
                amount=amount_usdt
            )

            if transfer_result["success"]:
                # 지갑 잔액 업데이트
                self.db.query(PartnerWallet).filter(
                    PartnerWallet.id == partner_wallet.id
                ).update({
                    'balance_usdt': PartnerWallet.balance_usdt + amount_usdt,
                    'last_funded_at': datetime.utcnow()
                })

                self.db.commit()

                logger.info(f"파트너 지갑 자금 조달 완료: {partner_id} - {amount_usdt} USDT")

                return {
                    "success": True,
                    "partner_id": partner_id,
                    "wallet_address": partner_wallet.address,
                    "amount_funded": float(amount_usdt),
                    "tx_hash": transfer_result.get("tx_hash"),
                    "new_balance": float(partner_wallet.balance_usdt + amount_usdt),  # type: ignore
                    "purpose": purpose
                }
            else:
                raise Exception(f"자금 이체 실패: {transfer_result.get('error')}")

        except Exception as e:
            logger.error(f"파트너 지갑 자금 조달 실패: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }

    async def check_funding_requirements(self, partner_id: int) -> Dict:
        """자금 조달 필요량 확인"""
        try:
            # 파트너의 모든 지갑 조회
            wallets = self.db.query(PartnerWallet).filter(
                PartnerWallet.partner_id == partner_id
            ).all()

            funding_requirements = []
            total_needed = Decimal("0")

            for wallet in wallets:
                current_balance = wallet.balance_usdt or Decimal("0")  # type: ignore
                min_balance = wallet.min_balance_usdt or Decimal("100")  # type: ignore

                if current_balance < min_balance:
                    shortfall = min_balance - current_balance
                    funding_requirements.append({
                        "wallet_type": wallet.wallet_type.value,  # type: ignore
                        "address": wallet.address,
                        "current_balance": float(current_balance),
                        "min_balance": float(min_balance),
                        "shortfall": float(shortfall)
                    })
                    total_needed += shortfall

            return {
                "partner_id": partner_id,
                "total_funding_needed": float(total_needed),
                "wallets_needing_funding": len(funding_requirements),
                "requirements": funding_requirements,
                "funding_needed": total_needed > 0
            }

        except Exception as e:
            logger.error(f"자금 조달 필요량 확인 실패: {e}")
            return {
                "partner_id": partner_id,
                "error": str(e),
                "funding_needed": False
            }

    async def auto_fund_if_needed(self, partner_id: int) -> Dict:
        """필요시 자동 자금 조달"""
        try:
            requirements = await self.check_funding_requirements(partner_id)
            
            if not requirements.get("funding_needed"):
                return {
                    "action": "none",
                    "message": "자금 조달이 필요하지 않습니다"
                }

            results = []
            total_funded = Decimal("0")

            for req in requirements["requirements"]:
                funding_result = await self.fund_partner_wallet(
                    partner_id=partner_id,
                    wallet_type=WalletType(req["wallet_type"]),
                    amount_usdt=Decimal(str(req["shortfall"])),
                    purpose="자동 자금 조달"
                )

                results.append(funding_result)
                if funding_result["success"]:
                    total_funded += Decimal(str(funding_result["amount_funded"]))

            return {
                "action": "auto_funded",
                "partner_id": partner_id,
                "total_funded": float(total_funded),
                "funding_results": results,
                "success": all(r["success"] for r in results)
            }

        except Exception as e:
            logger.error(f"자동 자금 조달 실패: {e}")
            return {
                "action": "failed",
                "error": str(e)
            }

    async def get_funding_history(
        self, 
        partner_id: int, 
        days: int = 30
    ) -> List[Dict]:
        """자금 조달 이력 조회"""
        try:
            from datetime import timedelta
            start_date = datetime.utcnow() - timedelta(days=days)

            wallets = self.db.query(PartnerWallet).filter(
                PartnerWallet.partner_id == partner_id,
                PartnerWallet.last_funded_at >= start_date
            ).all()

            history = []
            for wallet in wallets:
                if wallet.last_funded_at:  # type: ignore
                    history.append({
                        "wallet_type": wallet.wallet_type.value,  # type: ignore
                        "address": wallet.address,
                        "funded_at": wallet.last_funded_at.isoformat(),  # type: ignore
                        "current_balance": float(wallet.balance_usdt or 0)  # type: ignore
                    })

            return sorted(history, key=lambda x: x["funded_at"], reverse=True)

        except Exception as e:
            logger.error(f"자금 조달 이력 조회 실패: {e}")
            return []

    async def _get_wallet_balance(self, address: str) -> Decimal:
        """지갑 잔액 조회 (실제로는 TRON 네트워크 호출)"""
        # 실제 구현에서는 TRON API 호출
        return Decimal("1000000")  # 임시 값

    async def _transfer_funds(
        self, 
        from_address: str, 
        to_address: str, 
        amount: Decimal
    ) -> Dict:
        """자금 이체 (실제로는 TRON 네트워크 호출)"""
        # 실제 구현에서는 TRON 트랜잭션 생성 및 전송
        import uuid
        return {
            "success": True,
            "tx_hash": f"0x{uuid.uuid4().hex}",
            "amount": float(amount),
            "from_address": from_address,
            "to_address": to_address
        }

    async def get_company_wallet_status(self) -> Dict:
        """본사 지갑 상태 조회"""
        try:
            wallets = self.db.query(CompanyWallet).all()
            
            wallet_status = []
            for wallet in wallets:
                balance = await self._get_wallet_balance(wallet.address)  # type: ignore
                wallet_status.append({
                    "wallet_type": wallet.wallet_type.value,  # type: ignore
                    "address": wallet.address,
                    "balance_usdt": float(balance),
                    "last_updated": datetime.utcnow().isoformat()
                })

            return {
                "company_wallets": wallet_status,
                "total_balance": sum(w["balance_usdt"] for w in wallet_status),
                "last_checked": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"본사 지갑 상태 조회 실패: {e}")
            return {
                "error": str(e),
                "company_wallets": []
            }
