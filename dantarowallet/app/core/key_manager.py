"""
Secure Key Manager for DantaroWallet.
Handles encryption, decryption, and key management for the TronLink auto-signing system.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet

from app.core.config import settings
from app.core.logging import setup_logging

logger = setup_logging()


class SecureKeyManager:
    """
    보안 키 관리자 클래스.
    데이터 암호화/복호화, 세션 토큰 생성/검증, 감사 해시 생성 등을 담당합니다.
    """

    def __init__(self):
        """키 관리자 초기화"""
        # 마스터 키에서 Fernet 키 생성
        self._fernet_key = self._derive_fernet_key(settings.SECRET_KEY)
        self._fernet = Fernet(self._fernet_key)

    def _derive_fernet_key(self, master_key: str) -> bytes:
        """마스터 키에서 Fernet 키 파생"""
        # PBKDF2를 사용하여 안전한 키 파생
        import base64

        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        salt = b"dantaro_wallet_salt"  # 프로덕션에서는 환경변수로 관리
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        return key

    def encrypt_data(self, data: str) -> str:
        """
        데이터 암호화

        Args:
            data: 암호화할 평문 데이터

        Returns:
            str: 암호화된 데이터 (base64 인코딩)
        """
        try:
            encrypted_data = self._fernet.encrypt(data.encode())
            return encrypted_data.decode()
        except Exception as e:
            logger.error(f"데이터 암호화 실패: {e}")
            raise

    def decrypt_data(self, encrypted_data: str) -> str:
        """
        데이터 복호화

        Args:
            encrypted_data: 암호화된 데이터 (base64 인코딩)

        Returns:
            str: 복호화된 평문 데이터
        """
        try:
            decrypted_data = self._fernet.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"데이터 복호화 실패: {e}")
            raise

    def generate_session_token(
        self, user_id: str, address: str, expires_in: int = 3600
    ) -> str:
        """
        세션 토큰 생성

        Args:
            user_id: 사용자 ID
            address: 지갑 주소
            expires_in: 만료 시간(초)

        Returns:
            str: 암호화된 세션 토큰
        """
        try:
            # 세션 데이터 구성
            session_data = {
                "user_id": user_id,
                "address": address,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (
                    datetime.utcnow() + timedelta(seconds=expires_in)
                ).isoformat(),
                "nonce": secrets.token_hex(16),
            }

            # JSON 직렬화 후 암호화
            import json

            session_json = json.dumps(session_data)
            encrypted_token = self.encrypt_data(session_json)

            logger.info(f"세션 토큰 생성 완료: user_id={user_id}, address={address}")
            return encrypted_token

        except Exception as e:
            logger.error(f"세션 토큰 생성 실패: {e}")
            raise

    def verify_session_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        세션 토큰 검증

        Args:
            token: 검증할 세션 토큰

        Returns:
            Optional[Dict[str, Any]]: 유효한 경우 세션 데이터, 무효한 경우 None
        """
        try:
            # 토큰 복호화
            session_json = self.decrypt_data(token)

            import json

            session_data = json.loads(session_json)

            # 만료 시간 확인
            expires_at = datetime.fromisoformat(session_data["expires_at"])
            if datetime.utcnow() > expires_at:
                logger.warning("만료된 세션 토큰")
                return None

            logger.info(f"세션 토큰 검증 성공: user_id={session_data.get('user_id')}")
            return session_data

        except Exception as e:
            logger.error(f"세션 토큰 검증 실패: {e}")
            return None

    def generate_audit_hash(self, data: Dict[str, Any]) -> str:
        """
        감사용 해시 생성

        Args:
            data: 해시할 데이터

        Returns:
            str: SHA-256 해시
        """
        try:
            import json

            # 데이터를 JSON으로 직렬화 (키 정렬)
            data_json = json.dumps(data, sort_keys=True, ensure_ascii=False)

            # HMAC-SHA256으로 해시 생성
            hash_value = hmac.new(
                settings.SECRET_KEY.encode(), data_json.encode(), hashlib.sha256
            ).hexdigest()

            return hash_value

        except Exception as e:
            logger.error(f"감사 해시 생성 실패: {e}")
            raise

    def create_signature(self, data: str, private_key: Optional[str] = None) -> str:
        """
        데이터 서명 생성

        Args:
            data: 서명할 데이터
            private_key: 개인키 (None인 경우 마스터 키 사용)

        Returns:
            str: 서명
        """
        try:
            key = private_key or settings.SECRET_KEY
            signature = hmac.new(
                key.encode(), data.encode(), hashlib.sha256
            ).hexdigest()

            return signature

        except Exception as e:
            logger.error(f"서명 생성 실패: {e}")
            raise

    def verify_signature(
        self, data: str, signature: str, private_key: Optional[str] = None
    ) -> bool:
        """
        서명 검증

        Args:
            data: 원본 데이터
            signature: 검증할 서명
            private_key: 개인키 (None인 경우 마스터 키 사용)

        Returns:
            bool: 서명 유효성
        """
        try:
            expected_signature = self.create_signature(data, private_key)
            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            logger.error(f"서명 검증 실패: {e}")
            return False

    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """
        보안 이벤트 로깅

        Args:
            event_type: 이벤트 유형
            details: 이벤트 상세 정보
        """
        try:
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "details": details,
                "audit_hash": self.generate_audit_hash(details),
            }

            logger.info(f"보안 이벤트: {event_type}", extra=log_data)

        except Exception as e:
            logger.error(f"보안 이벤트 로깅 실패: {e}")


# 전역 인스턴스
key_manager = SecureKeyManager()
