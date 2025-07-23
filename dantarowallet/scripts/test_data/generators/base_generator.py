#!/usr/bin/env python3
"""
테스트 데이터 생성을 위한 기본 클래스
"""
import asyncio
import os
import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from app.core.config import settings


class BaseDataGenerator:
    """테스트 데이터 생성을 위한 기본 클래스"""

    def __init__(self):
        self.engine: Optional[Any] = None
        self.session_maker: Optional[Any] = None
        self.config_path = Path(__file__).parent.parent / "config"

    async def initialize_db(self):
        """데이터베이스 연결 초기화"""
        self.engine = create_async_engine(settings.DATABASE_URL, echo=False)
        self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False)

    async def close_db(self):
        """데이터베이스 연결 종료"""
        if self.engine:
            await self.engine.dispose()

    def load_config(self, config_file: str) -> Dict[str, Any]:
        """설정 파일 로드"""
        config_path = self.config_path / config_file
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def random_datetime(self, days_ago_range: List[int]) -> datetime:
        """랜덤 날짜/시간 생성"""
        days_ago = random.randint(*days_ago_range)
        return datetime.utcnow() - timedelta(days=days_ago)

    def random_amount(self, amount_range: List[float]) -> Decimal:
        """랜덤 금액 생성"""
        amount = random.uniform(*amount_range)
        return Decimal(str(round(amount, 6)))

    def weighted_choice(self, choices: Dict[str, float]) -> str:
        """가중치 기반 랜덤 선택"""
        total = sum(choices.values())
        r = random.uniform(0, total)

        cumulative = 0
        for choice, weight in choices.items():
            cumulative += weight
            if r <= cumulative:
                return choice

        return list(choices.keys())[-1]

    def generate_wallet_address(self, prefix: str = "T") -> str:
        """지갑 주소 생성"""
        chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        address = prefix + "".join(random.choices(chars, k=33))
        return address

    def generate_transaction_hash(self) -> str:
        """트랜잭션 해시 생성"""
        chars = "0123456789abcdef"
        return "".join(random.choices(chars, k=64))

    async def get_session(self) -> AsyncSession:
        """데이터베이스 세션 생성"""
        if not self.session_maker:
            raise RuntimeError("Database not initialized. Call initialize_db() first.")
        return self.session_maker()

    def log_progress(
        self, message: str, current: Optional[int] = None, total: Optional[int] = None
    ):
        """진행 상황 로그"""
        if current is not None and total is not None:
            progress = f"({current}/{total}) "
        else:
            progress = ""

        print(f"📊 {progress}{message}")


class DataValidator:
    """생성된 데이터 검증"""

    @staticmethod
    def validate_user_data(users: List[Any]) -> bool:
        """사용자 데이터 검증"""
        if not users:
            return False

        # 이메일 중복 체크
        emails = [user.email for user in users]
        if len(emails) != len(set(emails)):
            print("❌ 중복된 이메일이 발견되었습니다.")
            return False

        # 슈퍼 관리자가 정확히 1명인지 체크 (이메일로 확인)
        super_admins = [u for u in users if u.email == "admin@dantarowallet.com"]
        if len(super_admins) != 1:
            print(f"❌ 슈퍼 관리자는 1명이어야 합니다. 현재: {len(super_admins)}명")
            return False

        return True

    @staticmethod
    def validate_transaction_data(transactions: List[Any]) -> bool:
        """거래 데이터 검증"""
        if not transactions:
            return False

        # 트랜잭션 해시 중복 체크
        hashes = [
            t.transaction_hash for t in transactions if hasattr(t, "transaction_hash")
        ]
        if len(hashes) != len(set(hashes)):
            print("❌ 중복된 트랜잭션 해시가 발견되었습니다.")
            return False

        # 금액 유효성 체크
        for t in transactions:
            if hasattr(t, "amount") and t.amount <= 0:
                print("❌ 유효하지 않은 거래 금액이 발견되었습니다.")
                return False

        return True
