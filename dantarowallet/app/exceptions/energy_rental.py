"""
에너지 렌탈 서비스 관련 예외 클래스
"""

class EnergyRentalException(Exception):
    """에너지 렌탈 서비스 기본 예외"""
    pass

class InsufficientEnergyException(EnergyRentalException):
    """에너지 부족 예외"""
    pass

class InvalidRentalPlanException(EnergyRentalException):
    """잘못된 렌탈 플랜 예외"""
    pass

class PaymentException(EnergyRentalException):
    """결제 관련 예외"""
    pass

class EnergyPoolException(EnergyRentalException):
    """에너지 풀 관련 예외"""
    pass

class BillingException(EnergyRentalException):
    """청구 관련 예외"""
    pass
