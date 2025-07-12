"""
임시 Withdrawal Service 구현
"""
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional

class WithdrawalService:
    """임시 Withdrawal Service 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_withdrawal(self, user_id: str, amount: float) -> Dict[str, Any]:
        """출금 요청 생성"""
        return {"withdrawal_id": "temp_id", "user_id": user_id, "amount": amount, "status": "pending"}
    
    def get_withdrawal(self, withdrawal_id: str) -> Dict[str, Any]:
        """출금 요청 조회"""
        return {"withdrawal_id": withdrawal_id, "status": "pending"}
    
    def process_withdrawal(self, withdrawal_id: str) -> Dict[str, Any]:
        """출금 처리"""
        return {"withdrawal_id": withdrawal_id, "status": "completed"}
    
    def get_withdrawal_history(self, user_id: str) -> List[Dict[str, Any]]:
        """출금 내역 조회"""
        return []
