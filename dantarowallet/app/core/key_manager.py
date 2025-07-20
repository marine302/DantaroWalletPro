"""
보안 키 관리 시스템
암호화, 복호화, 키 순환, 감사 로깅 기능 제공
"""
import os
import base64
import hashlib
import hmac
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class SecureKeyManager:
    """보안 키 관리자"""
    
    def __init__(self):
        self.master_key = self._get_or_create_master_key()
        self.fernet = Fernet(self.master_key)
        
    def _get_or_create_master_key(self) -> bytes:
        """마스터 키 가져오기 또는 생성"""
        master_key_env = getattr(settings, 'MASTER_ENCRYPTION_KEY', None)
        
        if master_key_env:
            try:
                return base64.urlsafe_b64decode(master_key_env.encode())
            except Exception as e:
                logger.warning(f"환경 변수에서 마스터 키 로드 실패: {e}")
        
        # 새 마스터 키 생성
        key = Fernet.generate_key()
        encoded_key = base64.urlsafe_b64encode(key).decode()
        
        logger.warning("새 마스터 키가 생성되었습니다. 환경 변수 MASTER_ENCRYPTION_KEY에 저장하세요.")
        logger.warning(f"MASTER_ENCRYPTION_KEY={encoded_key}")
        
        return key
    
    def encrypt_data(self, data: str) -> str:
        """데이터 암호화"""
        try:
            encrypted = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"데이터 암호화 실패: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """데이터 복호화"""
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"데이터 복호화 실패: {e}")
            raise
    
    def generate_session_token(self, user_data: Dict[str, Any]) -> str:
        """세션 토큰 생성"""
        import json
        import secrets
        
        # 사용자 데이터와 타임스탬프, 랜덤 값 조합
        token_data = {
            "user_data": user_data,
            "timestamp": datetime.utcnow().isoformat(),
            "nonce": secrets.token_hex(16)
        }
        
        # JSON 직렬화 후 암호화
        json_data = json.dumps(token_data, sort_keys=True)
        return self.encrypt_data(json_data)
    
    def verify_session_token(self, token: str) -> Optional[Dict[str, Any]]:
        """세션 토큰 검증"""
        import json
        
        try:
            # 복호화
            decrypted_data = self.decrypt_data(token)
            token_data = json.loads(decrypted_data)
            
            # 타임스탬프 검증 (24시간 유효)
            timestamp = datetime.fromisoformat(token_data["timestamp"])
            if datetime.utcnow() - timestamp > timedelta(hours=24):
                logger.warning("만료된 세션 토큰")
                return None
            
            return token_data["user_data"]
            
        except Exception as e:
            logger.error(f"세션 토큰 검증 실패: {e}")
            return None
    
    def generate_audit_hash(self, data: Dict[str, Any]) -> str:
        """감사 로그용 해시 생성"""
        import json
        
        # 데이터를 정렬된 JSON으로 변환
        json_data = json.dumps(data, sort_keys=True)
        
        # HMAC-SHA256으로 해시 생성
        key = self.master_key[:32]  # 32바이트 키 사용
        hash_obj = hmac.new(key, json_data.encode(), hashlib.sha256)
        
        return hash_obj.hexdigest()
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """보안 이벤트 로깅"""
        audit_data = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
            "hash": self.generate_audit_hash(details)
        }
        
        logger.info(f"보안 이벤트: {audit_data}")
