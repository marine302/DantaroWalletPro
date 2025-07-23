"""
암호화 관련 유틸리티.
지갑 프라이빗 키 등 민감한 데이터를 안전하게 암호화/복호화하는 기능 제공.
"""

import base64
import secrets
from typing import Dict, Optional, Tuple

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings


class EncryptionService:
    """
    암호화/복호화 서비스
    - 프라이빗 키 등 민감 데이터 보호
    - salt 및 키 파생
    """

    @staticmethod
    def generate_salt() -> str:
        """32자 랜덤 salt 생성"""
        return secrets.token_hex(16)

    @staticmethod
    def derive_key(password: str, salt: str) -> bytes:
        """비밀번호와 salt로부터 32바이트 키 파생"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
            backend=default_backend(),
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    @classmethod
    def encrypt(cls, data: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """
        데이터 암호화
        :param data: 평문 데이터
        :param salt: salt(생략 시 자동 생성)
        :return: (암호문, salt)
        """
        if salt is None:
            salt = cls.generate_salt()
        key = cls.derive_key(settings.WALLET_ENCRYPTION_KEY, salt)
        f = Fernet(key)
        try:
            encrypted = f.encrypt(data.encode())
            return base64.b64encode(encrypted).decode(), salt
        except Exception as e:
            raise ValueError(f"암호화 실패: {e}")

    @classmethod
    def decrypt(cls, encrypted_data: str, salt: str) -> str:
        """
        데이터 복호화
        :param encrypted_data: 암호문(base64)
        :param salt: 암호화에 사용된 salt
        :return: 평문 데이터
        """
        key = cls.derive_key(settings.WALLET_ENCRYPTION_KEY, salt)
        f = Fernet(key)
        try:
            encrypted = base64.b64decode(encrypted_data.encode())
            decrypted = f.decrypt(encrypted)
            return decrypted.decode()
        except InvalidToken:
            raise ValueError("복호화 실패: 잘못된 키 또는 데이터")
        except Exception as e:
            raise ValueError(f"복호화 실패: {e}")

    @classmethod
    def encrypt_dict(cls, data: dict, salt: Optional[str] = None) -> Tuple[str, str]:
        """
        dict 객체를 JSON 문자열로 암호화
        :param data: dict
        :param salt: salt(생략 시 자동 생성)
        :return: (암호문, salt)
        """
        import json

        return cls.encrypt(json.dumps(data), salt)

    @classmethod
    def decrypt_dict(cls, encrypted_data: str, salt: str) -> Dict:
        """
        암호화된 JSON 문자열을 dict로 복호화
        :param encrypted_data: 암호문(base64)
        :param salt: 암호화에 사용된 salt
        :return: dict
        """
        import json

        return json.loads(cls.decrypt(encrypted_data, salt))


def encrypt_private_key(private_key: str) -> Tuple[str, str]:
    """
    프라이빗 키 암호화
    :param private_key: 평문 프라이빗 키
    :return: (암호화된 키, salt)
    """
    return EncryptionService.encrypt(private_key)


def decrypt_private_key(encrypted_key: str, salt: str) -> str:
    """
    프라이빗 키 복호화
    :param encrypted_key: 암호화된 키
    :param salt: salt
    :return: 평문 프라이빗 키
    """
    return EncryptionService.decrypt(encrypted_key, salt)
