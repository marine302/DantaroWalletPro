"""
출금 서비스
사용자 출금 요청 처리 및 관리 기능을 제공합니다.
"""
from typing import Optional, Dict, Any, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
import logging

from app.models.withdrawal import Withdrawal
from app.models.user import User
from app.models.balance import Balance

logger = logging.getLogger(__name__)


def safe_decimal(value: Any) -> Decimal:
    """안전한 Decimal 변환"""
    if isinstance(value, Decimal):
        return value
    elif hasattr(value, 'value'):
        return Decimal(str(value.value))
    else:
        return Decimal(str(value))


def safe_int(value: Any) -> int:
    """안전한 int 변환"""
    if isinstance(value, int):
        return value
    elif hasattr(value, 'value'):
        return int(value.value)
    else:
        return int(value)


def safe_str(value: Any) -> str:
    """안전한 str 변환"""
    if isinstance(value, str):
        return value
    elif hasattr(value, 'value'):
        return str(value.value)
    else:
        return str(value)


def safe_datetime_now() -> datetime:
    """안전한 datetime 반환"""
    return datetime.utcnow()


class WithdrawalService:
    """출금 서비스 클래스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_withdrawal_request(
        self,
        user_id: int,
        to_address: str,
        amount: Decimal,
        asset: str = "USDT"
    ) -> Dict[str, Any]:
        """출금 요청 생성"""
        try:
            # 잔액 확인
            balance_stmt = select(Balance).where(
                Balance.user_id == user_id,
                Balance.asset == asset
            )
            balance_result = await self.db.execute(balance_stmt)
            balance = balance_result.scalar_one_or_none()
            
            if not balance:
                return {
                    "success": False,
                    "error": "Insufficient balance"
                }
            
            available_amount = safe_decimal(balance.amount) - safe_decimal(balance.locked_amount)
            if available_amount < amount:
                return {
                    "success": False,
                    "error": "Insufficient available balance"
                }
            
            # 수수료 계산 (예시: 1 USDT 고정 수수료)
            fee = Decimal('1.0')
            net_amount = amount - fee
            
            if net_amount <= 0:
                return {
                    "success": False,
                    "error": "Amount too small after fee deduction"
                }
            
            # 출금 요청 생성
            withdrawal = Withdrawal(
                user_id=user_id,
                to_address=to_address,
                amount=amount,
                fee=fee,
                net_amount=net_amount,
                asset=asset,
                status="pending",
                priority="normal",
                auto_approved=False,
                whitelist_verified=False,
                retry_count=0
            )
            
            self.db.add(withdrawal)
            await self.db.commit()
            await self.db.refresh(withdrawal)
            
            return {
                "success": True,
                "withdrawal_id": withdrawal.id,
                "status": withdrawal.status,
                "amount": str(amount),
                "fee": str(fee),
                "net_amount": str(net_amount)
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create withdrawal request: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_withdrawal(self, withdrawal_id: int) -> Optional[Withdrawal]:
        """출금 정보 조회"""
        try:
            stmt = select(Withdrawal).where(Withdrawal.id == withdrawal_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get withdrawal: {e}")
            return None
    
    async def get_user_withdrawals(
        self,
        user_id: int,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Withdrawal]:
        """사용자 출금 내역 조회"""
        try:
            stmt = select(Withdrawal).where(Withdrawal.user_id == user_id)
            
            if status:
                stmt = stmt.where(Withdrawal.status == status)
            
            stmt = stmt.order_by(Withdrawal.created_at.desc()).limit(limit)
            
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get user withdrawals: {e}")
            return []
    
    async def update_withdrawal_status(
        self,
        withdrawal_id: int,
        status: str,
        tx_hash: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """출금 상태 업데이트"""
        try:
            withdrawal = await self.get_withdrawal(withdrawal_id)
            if not withdrawal:
                return {
                    "success": False,
                    "error": "Withdrawal not found"
                }
            
            update_data = {
                "status": status,
                "updated_at": safe_datetime_now()
            }
            
            if tx_hash:
                update_data["tx_hash"] = tx_hash
            
            if error_message:
                update_data["rejection_reason"] = error_message
            
            # 상태별 특별 처리
            if status == "approved":
                update_data["approved_at"] = safe_datetime_now()
            elif status == "processed":
                update_data["processed_at"] = safe_datetime_now()
            elif status == "completed":
                update_data["completed_at"] = safe_datetime_now()
            elif status == "failed":
                update_data["retry_count"] = safe_decimal(withdrawal.retry_count) + 1
            
            update_stmt = (
                update(Withdrawal)
                .where(Withdrawal.id == withdrawal_id)
                .values(**update_data)
            )
            await self.db.execute(update_stmt)
            await self.db.commit()
            
            return {
                "success": True,
                "withdrawal_id": withdrawal_id,
                "status": status
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update withdrawal status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cancel_withdrawal(
        self,
        withdrawal_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """출금 취소"""
        try:
            withdrawal = await self.get_withdrawal(withdrawal_id)
            if not withdrawal:
                return {
                    "success": False,
                    "error": "Withdrawal not found"
                }
            
            if safe_int(withdrawal.user_id) != user_id:
                return {
                    "success": False,
                    "error": "Access denied"
                }
            
            if withdrawal.status not in ["pending", "approved"]:
                return {
                    "success": False,
                    "error": f"Cannot cancel withdrawal with status: {withdrawal.status}"
                }
            
            # 상태를 cancelled로 변경
            update_stmt = (
                update(Withdrawal)
                .where(Withdrawal.id == withdrawal_id)
                .values(
                    status="cancelled",
                    updated_at=safe_datetime_now()
                )
            )
            await self.db.execute(update_stmt)
            await self.db.commit()
            
            return {
                "success": True,
                "withdrawal_id": withdrawal_id,
                "status": "cancelled"
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to cancel withdrawal: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_withdrawal_statistics(self) -> Dict[str, Any]:
        """출금 통계 조회"""
        try:
            stmt = select(Withdrawal)
            result = await self.db.execute(stmt)
            withdrawals = result.scalars().all()
            
            stats = {
                "total_count": 0,
                "pending_count": 0,
                "completed_count": 0,
                "failed_count": 0,
                "cancelled_count": 0,
                "total_amount": Decimal('0'),
                "total_fees": Decimal('0')
            }
            
            for withdrawal in withdrawals:
                stats["total_count"] += 1
                stats["total_amount"] += safe_decimal(withdrawal.amount)
                stats["total_fees"] += safe_decimal(withdrawal.fee)
                
                status = safe_str(withdrawal.status)
                if status == "pending":
                    stats["pending_count"] += 1
                elif status == "completed":
                    stats["completed_count"] += 1
                elif status == "failed":
                    stats["failed_count"] += 1
                elif status == "cancelled":
                    stats["cancelled_count"] += 1
            
            # Decimal을 문자열로 변환
            stats["total_amount"] = str(stats["total_amount"])
            stats["total_fees"] = str(stats["total_fees"])
            
            return {
                "success": True,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get withdrawal statistics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
