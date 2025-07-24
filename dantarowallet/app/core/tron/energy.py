"""
TronEnergyService - 에너지 관련 서비스 (현재 비활성화)
"""
from typing import Optional

class TronEnergyService:
    """에너지 서비스 더미 클래스"""
    
    def __init__(self):
        pass
    
    async def get_account_resources(self, address: str):
        """계정 리소스 조회 (비활성화)"""
        return {"energy": 0, "bandwidth": 0}
    
    async def get_energy_price_info(self):
        """에너지 가격 정보 조회 (비활성화)"""
        return {"price": 0}
    
    async def estimate_transaction_cost(self, transaction_type: str):
        """트랜잭션 비용 추정 (비활성화)"""
        return {"cost": 0}
    
    async def get_energy_info(self, address: str):
        """에너지 정보 조회 (비활성화)"""
        return {"energy": 0}
    
    async def get_energy_price(self):
        """에너지 가격 조회 (비활성화)"""
        return 0
    
    async def estimate_transaction_energy(self, contract_address: str, function_selector: str, parameter: str = "", caller_address: Optional[str] = None):
        """트랜잭션 에너지 추정 (비활성화)"""
        return {"energy": 0}
