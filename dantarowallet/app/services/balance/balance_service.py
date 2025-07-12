"""
임시 Balance Service 구현
"""
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional

class BalanceService:
    """임시 Balance Service 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_balance(self, user_id: str) -> Dict[str, Any]:
        """잔액 조회"""
        return {"balance": 0, "user_id": user_id}
    
    def update_balance(self, user_id: str, amount: float) -> Dict[str, Any]:
        """잔액 업데이트"""
        return {"success": True, "user_id": user_id, "amount": amount}
    
    def get_transaction_history(self, user_id: str) -> List[Dict[str, Any]]:
        """거래 내역 조회"""
        return []
