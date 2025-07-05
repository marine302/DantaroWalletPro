"""
TRON 네트워크 연결 및 기본 클라이언트 관리.
네트워크 연결의 단일 책임을 담당합니다.
"""
import logging
from typing import Optional

from app.core.config import settings
from app.core.tron.constants import TronNetwork
from tronpy import Tron

logger = logging.getLogger(__name__)


class TronNetworkClient:
    """TRON 네트워크 클라이언트 관리"""
    
    _instance: Optional['TronNetworkClient'] = None
    _client: Optional[Tron] = None
    
    def __new__(cls):
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._network = TronNetwork(settings.TRON_NETWORK)
            self._api_key = settings.TRON_API_KEY
            self._node_url = settings.TRON_NODE_URL
            self._initialized = True
            self._connect()
    
    def _connect(self) -> None:
        """TRON 네트워크에 연결"""
        try:
            if self._network == TronNetwork.NILE:
                self._client = Tron(network="nile")
            elif self._network == TronNetwork.MAINNET:
                self._client = Tron()
            else:
                raise ValueError(f"Unsupported network: {self._network}")
            
            # API 키가 있으면 설정
            if self._api_key:
                # TronGrid API 키 설정 (실제 구현에서는 TronGrid 클라이언트 사용)
                pass
            
            logger.info(f"Connected to TRON {self._network} network")
            
        except Exception as e:
            logger.error(f"Failed to connect to TRON network: {e}")
            raise
    
    @property
    def client(self) -> Tron:
        """TRON 클라이언트 인스턴스 반환"""
        if self._client is None:
            self._connect()
        
        if self._client is None:
            raise RuntimeError("Failed to initialize TRON client")
        
        return self._client
    
    @property
    def network(self) -> TronNetwork:
        """현재 네트워크 반환"""
        return self._network
    
    def is_connected(self) -> bool:
        """네트워크 연결 상태 확인"""
        try:
            if self._client is None:
                return False
            
            # 간단한 네트워크 상태 확인
            self._client.get_latest_block_number()
            return True
            
        except Exception as e:
            logger.warning(f"Network connection check failed: {e}")
            return False
    
    def reconnect(self) -> None:
        """네트워크 재연결"""
        logger.info("Reconnecting to TRON network...")
        self._client = None
        self._connect()


class TronNetworkService:
    """TRON 네트워크 서비스 기본 클래스"""
    
    def __init__(self):
        self._network_client = TronNetworkClient()
    
    @property
    def client(self) -> Tron:
        """TRON 클라이언트 반환"""
        return self._network_client.client
    
    @property
    def network(self) -> TronNetwork:
        """현재 네트워크 반환"""
        return self._network_client.network
    
    def ensure_connection(self) -> None:
        """연결 상태 확인 및 재연결"""
        if not self._network_client.is_connected():
            self._network_client.reconnect()
    
    async def get_latest_block_number(self) -> int:
        """최신 블록 번호 조회"""
        self.ensure_connection()
        try:
            return self.client.get_latest_block_number()
        except Exception as e:
            logger.error(f"Failed to get latest block number: {e}")
            raise
    
    async def get_latest_block(self) -> dict:
        """최신 블록 정보 조회"""
        self.ensure_connection()
        try:
            block_number = await self.get_latest_block_number()
            return self.client.get_block(block_number)
        except Exception as e:
            logger.error(f"Failed to get latest block: {e}")
            raise
