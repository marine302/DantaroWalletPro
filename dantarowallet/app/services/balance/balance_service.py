"""
잔액 서비스
사용자 잔액 관리 및 조회 기능을 제공합니다.
"""
from typing import Optional, Dict, Any, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
import logging

from app.models.balance import Balance
from app.models.user import User

logger = logging.getLogger(__name__)


def safe_decimal(value: Any) -> Decimal:
    """안전한 Decimal 변환"""
    if isinstance(value, Decimal):
        return value
    elif hasattr(value, 'value'):
        return Decimal(str(value.value))
    else:
        return Decimal(str(value))


def safe_datetime_now() -> datetime:
    """안전한 datetime 반환"""
    return datetime.utcnow()


class BalanceService:
    """잔액 서비스 클래스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_balance(self, user_id: int, asset: str = "USDT") -> Optional[Balance]:
        """사용자 잔액 조회"""
        try:
            stmt = select(Balance).where(
                Balance.user_id == user_id,
                Balance.asset == asset
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user balance: {e}")
            return None
    
    async def get_all_user_balances(self, user_id: int) -> List[Balance]:
        """사용자의 모든 자산 잔액 조회"""
        try:
            stmt = select(Balance).where(Balance.user_id == user_id)
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get all user balances: {e}")
            return []
    
    async def update_balance(
        self, 
        user_id: int, 
        asset: str, 
        amount: Decimal, 
        operation: str = "add"
    ) -> Dict[str, Any]:
        """잔액 업데이트"""
        try:
            # 기존 잔액 조회
            balance = await self.get_user_balance(user_id, asset)
            
            if not balance:
                # 새 잔액 생성
                if operation == "add":
                    balance = Balance(
                        user_id=user_id,
                        asset=asset,
                        amount=amount,
                        locked_amount=Decimal('0')
                    )
                    self.db.add(balance)
                else:
                    return {
                        "success": False,
                        "error": "Cannot subtract from non-existent balance"
                    }
            else:
                # 기존 잔액 업데이트 - SQLAlchemy update 사용
                current_amount = safe_decimal(balance.amount)
                
                if operation == "add":
                    new_amount = current_amount + amount
                elif operation == "subtract":
                    if current_amount < amount:
                        return {
                            "success": False,
                            "error": "Insufficient balance"
                        }
                    new_amount = current_amount - amount
                else:
                    return {
                        "success": False,
                        "error": "Invalid operation"
                    }
                
                # update 문 사용하여 안전하게 업데이트
                update_stmt = (
                    update(Balance)
                    .where(Balance.id == balance.id)
                    .values(
                        amount=new_amount,
                        updated_at=safe_datetime_now()
                    )
                )
                await self.db.execute(update_stmt)
            
            await self.db.commit()
            
            # 업데이트된 잔액 다시 조회
            updated_balance = await self.get_user_balance(user_id, asset)
            if not updated_balance:
                return {
                    "success": False,
                    "error": "Failed to retrieve updated balance"
                }
            
            return {
                "success": True,
                "balance": {
                    "user_id": updated_balance.user_id,
                    "asset": updated_balance.asset,
                    "amount": str(safe_decimal(updated_balance.amount)),
                    "locked_amount": str(safe_decimal(updated_balance.locked_amount))
                }
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update balance: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def lock_balance(
        self, 
        user_id: int, 
        asset: str, 
        amount: Decimal
    ) -> Dict[str, Any]:
        """잔액 락 설정"""
        try:
            balance = await self.get_user_balance(user_id, asset)
            
            if not balance:
                return {
                    "success": False,
                    "error": "Balance not found"
                }
            
            current_amount = safe_decimal(balance.amount)
            current_locked = safe_decimal(balance.locked_amount)
            available_amount = current_amount - current_locked
            
            if available_amount < amount:
                return {
                    "success": False,
                    "error": "Insufficient available balance"
                }
            
            new_locked_amount = current_locked + amount
            
            # update 문 사용하여 안전하게 업데이트
            update_stmt = (
                update(Balance)
                .where(Balance.id == balance.id)
                .values(
                    locked_amount=new_locked_amount,
                    updated_at=safe_datetime_now()
                )
            )
            await self.db.execute(update_stmt)
            
            await self.db.commit()
            
            return {
                "success": True,
                "locked_amount": str(amount),
                "total_locked": str(new_locked_amount)
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to lock balance: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def unlock_balance(
        self, 
        user_id: int, 
        asset: str, 
        amount: Decimal
    ) -> Dict[str, Any]:
        """잔액 락 해제"""
        try:
            balance = await self.get_user_balance(user_id, asset)
            
            if not balance:
                return {
                    "success": False,
                    "error": "Balance not found"
                }
            
            current_locked = safe_decimal(balance.locked_amount)
            
            if current_locked < amount:
                return {
                    "success": False,
                    "error": "Insufficient locked balance"
                }
            
            new_locked_amount = current_locked - amount
            
            # update 문 사용하여 안전하게 업데이트
            update_stmt = (
                update(Balance)
                .where(Balance.id == balance.id)
                .values(
                    locked_amount=new_locked_amount,
                    updated_at=safe_datetime_now()
                )
            )
            await self.db.execute(update_stmt)
            
            await self.db.commit()
            
            return {
                "success": True,
                "unlocked_amount": str(amount),
                "total_locked": str(new_locked_amount)
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to unlock balance: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_total_balance_stats(self) -> Dict[str, Any]:
        """전체 잔액 통계 조회"""
        try:
            # 이 부분은 실제 구현에서 더 상세한 통계를 제공할 수 있습니다
            stmt = select(Balance)
            result = await self.db.execute(stmt)
            balances = result.scalars().all()
            
            stats = {}
            for balance in balances:
                asset = balance.asset
                if asset not in stats:
                    stats[asset] = {
                        "total_amount": Decimal('0'),
                        "total_locked": Decimal('0'),
                        "user_count": 0
                    }
                
                stats[asset]["total_amount"] += safe_decimal(balance.amount)
                stats[asset]["total_locked"] += safe_decimal(balance.locked_amount)
                stats[asset]["user_count"] += 1
            
            # Decimal을 문자열로 변환하여 JSON 직렬화 가능하게 만듦
            for asset in stats:
                stats[asset]["total_amount"] = str(stats[asset]["total_amount"])
                stats[asset]["total_locked"] = str(stats[asset]["total_locked"])
            
            return {
                "success": True,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get balance stats: {e}")
            return {
                "success": False,
                "error": str(e)
            }
