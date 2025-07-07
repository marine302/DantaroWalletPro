"""
Core configuration module for DantaroWallet.
Implements clean architecture principles for configuration management.
"""
from typing import List, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with validation and type safety.
    Follows the Single Responsibility Principle.
    """

    # 개발/테스트 환경을 위한 기본값
    # 운영 환경에서는 반드시 실제 값으로 대체해야 함

    # Application Configuration
    APP_NAME: str = "DantaroWallet"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    # .env 파일에서 사용되는 추가 필드들
    SYNC_DATABASE_URL: str = "sqlite:///./dev.db"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "DantaroWallet"
    VERSION: str = "1.0.0"
    TRON_API_KEYS: str = '["your-tronapi-key"]'
    DEFAULT_ENERGY_POOL_SIZE: int = 1000000
    ENERGY_REFRESH_INTERVAL: int = 300
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 43200

    # Security Configuration
    SECRET_KEY: str = "dev_secret_key_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"  # 개발용 기본값
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 0

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"  # 개발용 기본값

    # TRON Network Configuration
    TRON_NETWORK: str = "nile"  # nile for testnet, mainnet for production
    TRON_API_KEY: str = ""
    TRON_NODE_URL: str = "https://api.nileex.io"  # Testnet default
    TRON_SCAN_URL: str = "https://nile.tronscan.org"
    TRON_DEFAULT_FEE_LIMIT: int = 100000000  # 100 TRX default
    
    # TRON Monitoring Configuration
    BLOCKS_TO_CHECK_ON_START: int = 10
    BLOCK_CONFIRMATION_COUNT: int = 19
    DEPOSIT_CHECK_INTERVAL: int = 30  # seconds

    # TRON Token Contract Addresses
    @property
    def USDT_CONTRACT_ADDRESS(self) -> str:
        """네트워크별 USDT 계약 주소"""
        if self.TRON_NETWORK == "nile":
            return "TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf"  # Nile testnet USDT
        else:
            return "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # Mainnet USDT

    # Encryption Configuration
    ENCRYPTION_KEY: str = "your-encryption-key-32bytes-change-me-now"  # 32바이트 키
    WALLET_ENCRYPTION_KEY: str = (
        "your-wallet-encryption-key-32bytes-change-me-now"  # 지갑용 암호화 키
    )

    # Wallet Monitor Configuration
    WALLET_MONITOR_INTERVAL: int = 60  # 초 단위
    WALLET_CONFIRMATIONS_REQUIRED: int = 1  # 필요한 블록 컨펌 수

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # CORS Configuration - 개발용으로 모든 origin 허용
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # 보안 설정
    ALLOWED_HOSTS: List[str] = ["*"]

    # Rate Limiting 설정
    RATE_LIMIT_CALLS: int = 100  # 시간당 허용 요청 수
    RATE_LIMIT_PERIOD: int = 60  # 초 단위

    # 요청 사이즈 제한
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10MB

    # 테스트 환경 설정
    TESTING: bool = False

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """
        Validate and parse CORS origins.
        Supports both string and list input formats.
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(f"Invalid CORS origins format: {v}")

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v: Union[str, List[str]]) -> List[str]:
        """
        Validate and parse allowed hosts.
        Supports both string and list input formats.
        """
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json

                return json.loads(v)
            return [i.strip() for i in v.split(",")]
        return v

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        case_sensitive = True
        extra = "forbid"  # Prevent unknown configuration variables


# Global settings instance (Singleton pattern)
settings = Settings()
