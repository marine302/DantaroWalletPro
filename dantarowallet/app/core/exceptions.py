"""
애플리케이션의 커스텀 예외 정의.
일관된 API 오류 처리와 응답 형식을 위한 예외 계층.
"""
from typing import Any, Dict, Optional

from fastapi import status


class DantaroException(Exception):
    """
    DantaroWallet의 기본 예외 클래스.
    모든 커스텀 비즈니스 예외는 이 클래스를 상속받아야 합니다.
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(DantaroException):
    """인증 관련 예외 (로그인 실패, 토큰 만료 등)"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTH_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationError(DantaroException):
    """권한 관련 예외 (접근 권한 부족 등)"""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            error_code="PERMISSION_DENIED",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ValidationError(DantaroException):
    """데이터 검증 관련 예외 (잘못된 입력값 등)"""

    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class NotFoundError(DantaroException):
    """리소스 미존재 예외"""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConflictError(DantaroException):
    """리소스 충돌 예외 (중복 생성, 동시성 충돌 등)"""

    def __init__(self, message: str):
        super().__init__(
            message=message, error_code="CONFLICT", status_code=status.HTTP_409_CONFLICT
        )


class RateLimitError(DantaroException):
    """요청 제한 초과 예외"""

    def __init__(self, retry_after: int):
        super().__init__(
            message="Rate limit exceeded",
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after": retry_after},
        )


class InsufficientBalanceError(DantaroException):
    """잔액 부족 예외 (암호화폐 송금 등에서 사용)"""

    def __init__(self, required: float, available: float):
        super().__init__(
            message="Insufficient balance",
            error_code="INSUFFICIENT_BALANCE",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"required": required, "available": available},
        )


class BlockchainError(DantaroException):
    """블록체인 통신 관련 예외"""

    def __init__(self, message: str, blockchain_error: Optional[str] = None):
        details = {"blockchain_error": blockchain_error} if blockchain_error else {}
        super().__init__(
            message=message,
            error_code="BLOCKCHAIN_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


class DatabaseError(DantaroException):
    """데이터베이스 관련 예외"""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
