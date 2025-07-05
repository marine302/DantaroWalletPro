"""
TRON 네트워크 통계 및 정보 서비스.
네트워크 상태, 블록 정보, 시스템 통계를 담당합니다.
"""
import logging
from datetime import datetime
from typing import Any, Dict

from app.core.config import settings
from app.core.tron.network import TronNetworkService

logger = logging.getLogger(__name__)


class TronNetworkStatsService(TronNetworkService):
    """TRON 네트워크 통계 서비스"""
    
    async def get_network_stats(self) -> Dict[str, Any]:
        """TRON 네트워크 전체 통계 정보"""
        try:
            self.ensure_connection()
            
            # 노드 정보
            node_info = self.client.get_node_info()
            
            # 체인 파라미터
            chain_parameters = self.client.get_chain_parameters()
            
            # 최신 블록 정보
            latest_block = self.client.get_latest_block()
            
            network_stats = {
                "block_height": latest_block.get("block_header", {}).get("raw_data", {}).get("number", 0),
                "block_timestamp": latest_block.get("block_header", {}).get("raw_data", {}).get("timestamp", 0),
                "witness_count": len(latest_block.get("block_header", {}).get("raw_data", {}).get("witness_signature", [])),
                "node_version": node_info.get("configNodeInfo", {}).get("codeVersion", "unknown"),
                "total_transaction": node_info.get("machineInfo", {}).get("totalTransactionCount", 0),
                "timestamp": datetime.utcnow().isoformat(),
                "network": settings.TRON_NETWORK
            }
            
            # 에너지 관련 체인 파라미터 추출
            for param in chain_parameters:
                key = param.get("key", "")
                if "Energy" in key or "energy" in key:
                    network_stats[f"param_{key.lower()}"] = param.get("value", 0)
            
            logger.info(f"Network stats retrieved for block #{network_stats['block_height']}")
            return network_stats
            
        except Exception as e:
            logger.error(f"Failed to get network stats: {str(e)}")
            return {
                "block_height": 0,
                "block_timestamp": 0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "network": settings.TRON_NETWORK
            }

    async def get_chain_parameters(self) -> Dict[str, Any]:
        """TRON 체인 파라미터 조회"""
        try:
            self.ensure_connection()
            
            chain_parameters = self.client.get_chain_parameters()
            
            # 파라미터를 딕셔너리로 변환
            params_dict = {}
            for param in chain_parameters:
                key = param.get("key", "")
                value = param.get("value", 0)
                params_dict[key] = value
            
            return {
                "parameters": params_dict,
                "timestamp": datetime.utcnow().isoformat(),
                "count": len(params_dict)
            }
            
        except Exception as e:
            logger.error(f"Failed to get chain parameters: {str(e)}")
            return {
                "parameters": {},
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def get_node_info(self) -> Dict[str, Any]:
        """노드 정보 조회"""
        try:
            self.ensure_connection()
            
            node_info = self.client.get_node_info()
            
            return {
                "node_info": node_info,
                "timestamp": datetime.utcnow().isoformat(),
                "network": settings.TRON_NETWORK
            }
            
        except Exception as e:
            logger.error(f"Failed to get node info: {str(e)}")
            return {
                "node_info": {},
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "network": settings.TRON_NETWORK
            }
