"""로깅 설정"""

import logging
import sys
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """로거 인스턴스를 반환합니다."""
    logger = logging.getLogger(name or __name__)

    if not logger.handlers:
        # 콘솔 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)

        # 파일 핸들러 (선택적)
        # file_handler = logging.FileHandler('logs/debug.log')
        # file_handler.setFormatter(console_formatter)

        logger.addHandler(console_handler)
        # logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)  # DEBUG 레벨로 변경
        logger.propagate = False  # 중복 로그 방지

    return logger
