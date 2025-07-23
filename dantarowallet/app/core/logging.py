"""
로깅 시스템 설정 모듈.
애플리케이션 전체에서 사용할 표준화된 로깅 시스템을 구성합니다.
"""

import logging
import os
import sys
from datetime import datetime

from pythonjsonlogger.json import JsonFormatter

from app.core.config import settings


class CustomJsonFormatter(JsonFormatter):
    """
    JSON 형식의 로그를 생성하는 커스텀 포매터.
    로그에 추가 컨텍스트 정보 포함.
    """

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["level"] = record.levelname
        log_record["app_name"] = settings.APP_NAME
        log_record["app_version"] = settings.APP_VERSION
        # request_id는 extra dict로 전달될 수 있으므로 getattr 사용
        request_id = getattr(record, "request_id", None)
        if request_id:
            log_record["request_id"] = request_id


def setup_logging() -> logging.Logger:
    """
    애플리케이션 로거를 설정하고 반환합니다.
    환경 설정에 따라 JSON 또는 일반 텍스트 포맷을 지원합니다.
    """
    logger = logging.getLogger("dantarowallet")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL, "INFO"))
    if logger.handlers:
        logger.handlers.clear()
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.LOG_FORMAT.lower() == "json":
        formatter = CustomJsonFormatter("%(message)s")
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    # 운영 환경에서 파일 핸들러 추가
    if not settings.DEBUG:
        os.makedirs("logs", exist_ok=True)
        file_handler = logging.FileHandler("logs/app.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    logger.propagate = False
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    지정된 이름의 로거를 반환합니다.

    Args:
        name: 로거 이름

    Returns:
        logging.Logger: 설정된 로거
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # 기본 로거 설정이 없는 경우 설정
        logger.setLevel(getattr(logging, settings.LOG_LEVEL, "INFO"))
        console_handler = logging.StreamHandler(sys.stdout)

        if settings.LOG_FORMAT.lower() == "json":
            formatter = CustomJsonFormatter("%(message)s")
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.propagate = False

    return logger
