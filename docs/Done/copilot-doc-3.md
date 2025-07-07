# Copilot 문서 #3: 데이터베이스 설정 및 기본 모델

## 목표
PostgreSQL 데이터베이스를 설정하고, SQLAlchemy 2.0을 사용하여 User와 Balance 모델을 구현합니다. Alembic을 통한 마이그레이션 시스템도 구축합니다.

## 전제 조건
- Copilot 문서 #1, #2가 완료되어 있어야 합니다.
- Docker Compose로 PostgreSQL이 실행 중이어야 합니다.

## 상세 지시사항

### 1. 데이터베이스 연결 설정 (app/core/database.py)

```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# 데이터베이스 엔진 생성
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # SQL 로깅 (개발 환경에서만)
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # 연결 상태 체크
    # 테스트 환경에서는 연결 풀 비활성화
    poolclass=NullPool if settings.TESTING else None,
)

# 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base 클래스
Base = declarative_base()

# 의존성 주입용 세션 getter
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# 데이터베이스 연결 테스트
async def check_database_connection():
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

# 테이블 생성 (개발용)
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")

# 테이블 삭제 (테스트용)
async def drop_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped")
```

### 2. 기본 모델 클래스 (app/models/base.py)

```python
from datetime import datetime
from typing import Any, Dict
from sqlalchemy import Column, DateTime, Integer, func
from sqlalchemy.ext.declarative import declared_attr
from app.core.database import Base

class BaseModel(Base):
    """모든 모델의 기본 클래스"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """테이블명을 클래스명의 소문자 복수형으로 자동 생성"""
        return cls.__name__.lower() + "s"
    
    def dict(self) -> Dict[str, Any]:
        """모델을 딕셔너리로 변환"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def update(self, **kwargs):
        """모델 속성 업데이트"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self
```

### 3. User 모델 (app/models/user.py)

```python
from sqlalchemy import Column, String, Boolean, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class User(BaseModel):
    """사용자 모델"""
    
    # 기본 정보
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # 상태
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # 지갑 정보 (나중에 추가될 예정)
    tron_address = Column(String(42), unique=True, nullable=True, index=True)
    
    # 관계 (나중에 추가)
    # balances = relationship("Balance", back_populates="user", lazy="selectin")
    # transactions = relationship("Transaction", back_populates="user", lazy="selectin")
    
    # 인덱스
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
    
    @property
    def is_authenticated(self) -> bool:
        """인증된 사용자인지 확인"""
        return True if self.is_active else False
    
    def has_wallet(self) -> bool:
        """지갑이 생성되었는지 확인"""
        return bool(self.tron_address)
```

### 4. Balance 모델 (app/models/balance.py)

```python
from decimal import Decimal
from sqlalchemy import Column, String, Numeric, ForeignKey, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Balance(BaseModel):
    """잔고 모델"""
    
    # 외래 키
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 자산 정보
    asset = Column(String(10), nullable=False, default="USDT")
    
    # 잔고
    amount = Column(
        Numeric(precision=18, scale=6),
        nullable=False,
        default=Decimal("0.000000")
    )
    
    # 잠긴 잔고 (출금 제한 등)
    locked_amount = Column(
        Numeric(precision=18, scale=6),
        nullable=False,
        default=Decimal("0.000000")
    )
    
    # 관계 (User 모델에 relationship 추가 필요)
    # user = relationship("User", back_populates="balances")
    
    # 제약 조건
    __table_args__ = (
        # 사용자당 자산별로 하나의 잔고만 존재
        UniqueConstraint('user_id', 'asset', name='uq_user_asset'),
        # 잔고는 음수가 될 수 없음
        CheckConstraint('amount >= 0', name='check_positive_amount'),
        CheckConstraint('locked_amount >= 0', name='check_positive_locked'),
        CheckConstraint('locked_amount <= amount', name='check_locked_not_exceed_amount'),
        # 인덱스
        Index('idx_balance_user_asset', 'user_id', 'asset'),
    )
    
    def __repr__(self):
        return f"<Balance(user_id={self.user_id}, asset={self.asset}, amount={self.amount})>"
    
    @property
    def available_amount(self) -> Decimal:
        """사용 가능한 잔고 (전체 - 잠긴 금액)"""
        return self.amount - self.locked_amount
    
    def can_withdraw(self, amount: Decimal) -> bool:
        """출금 가능 여부 확인"""
        return self.available_amount >= amount
    
    def lock(self, amount: Decimal) -> bool:
        """금액 잠금"""
        if self.available_amount >= amount:
            self.locked_amount += amount
            return True
        return False
    
    def unlock(self, amount: Decimal) -> bool:
        """금액 잠금 해제"""
        if self.locked_amount >= amount:
            self.locked_amount -= amount
            return True
        return False
```

### 5. 모델 집합 파일 (app/models/__init__.py)

```python
from app.models.base import BaseModel
from app.models.user import User
from app.models.balance import Balance

__all__ = ["BaseModel", "User", "Balance"]
```

### 6. Alembic 초기화 및 설정

터미널에서 실행:
```bash
poetry run alembic init alembic
```

그런 다음 `alembic.ini` 파일을 수정:
```ini
# alembic.ini의 sqlalchemy.url 라인을 주석 처리
# sqlalchemy.url = driver://user:pass@localhost/dbname
```

### 7. Alembic 환경 설정 (alembic/env.py)

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# 프로젝트 설정 import
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.database import Base

# 모든 모델 import (중요!)
from app.models import *  # noqa

# Alembic Config 객체
config = context.config

# 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 메타데이터
target_metadata = Base.metadata

def get_url():
    """데이터베이스 URL 가져오기"""
    return settings.DATABASE_URL

def run_migrations_offline() -> None:
    """오프라인 모드에서 마이그레이션 실행"""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """비동기 모드에서 마이그레이션 실행"""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    """온라인 모드에서 마이그레이션 실행"""
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 8. 첫 마이그레이션 생성

```bash
# 첫 마이그레이션 생성
poetry run alembic revision --autogenerate -m "Initial migration with users and balances"

# 마이그레이션 실행
poetry run alembic upgrade head
```

### 9. 데이터베이스 초기화 스크립트 (scripts/init_db.py)

```python
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import engine, create_tables, check_database_connection
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db():
    """데이터베이스 초기화"""
    logger.info("Initializing database...")
    
    # 연결 확인
    if not await check_database_connection():
        logger.error("Failed to connect to database")
        return False
    
    # 개발 환경에서만 테이블 생성 (운영에서는 Alembic 사용)
    if settings.DEBUG:
        await create_tables()
        logger.info("Database tables created successfully")
    
    return True

if __name__ == "__main__":
    asyncio.run(init_db())
```

### 10. 설정 파일 업데이트 (app/core/config.py)

기존 Settings 클래스에 추가:
```python
class Settings(BaseSettings):
    # 기존 설정들...
    
    # Testing
    TESTING: bool = False
    
    # 기존 설정 계속...
```

### 11. 데이터베이스 테스트 (tests/test_database.py)

```python
import pytest
from sqlalchemy import select
from app.core.database import AsyncSessionLocal, check_database_connection
from app.models.user import User
from app.models.balance import Balance
from decimal import Decimal

@pytest.mark.asyncio
async def test_database_connection():
    """데이터베이스 연결 테스트"""
    assert await check_database_connection() is True

@pytest.mark.asyncio
async def test_create_user():
    """사용자 생성 테스트"""
    async with AsyncSessionLocal() as session:
        # 사용자 생성
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            is_active=True
        )
        session.add(user)
        await session.commit()
        
        # 조회
        result = await session.execute(
            select(User).filter_by(email="test@example.com")
        )
        saved_user = result.scalar_one_or_none()
        
        assert saved_user is not None
        assert saved_user.email == "test@example.com"
        assert saved_user.is_active is True
        
        # 정리
        await session.delete(saved_user)
        await session.commit()

@pytest.mark.asyncio
async def test_create_balance():
    """잔고 생성 테스트"""
    async with AsyncSessionLocal() as session:
        # 사용자 먼저 생성
        user = User(email="balance_test@example.com", password_hash="hash")
        session.add(user)
        await session.flush()
        
        # 잔고 생성
        balance = Balance(
            user_id=user.id,
            asset="USDT",
            amount=Decimal("100.50"),
            locked_amount=Decimal("10.00")
        )
        session.add(balance)
        await session.commit()
        
        # 검증
        assert balance.available_amount == Decimal("90.50")
        assert balance.can_withdraw(Decimal("90.00")) is True
        assert balance.can_withdraw(Decimal("100.00")) is False
        
        # 정리
        await session.delete(balance)
        await session.delete(user)
        await session.commit()

@pytest.mark.asyncio
async def test_balance_constraints():
    """잔고 제약 조건 테스트"""
    async with AsyncSessionLocal() as session:
        # 사용자 생성
        user = User(email="constraint_test@example.com", password_hash="hash")
        session.add(user)
        await session.flush()
        
        # 같은 사용자, 같은 자산으로 두 개의 잔고 생성 시도
        balance1 = Balance(user_id=user.id, asset="USDT")
        balance2 = Balance(user_id=user.id, asset="USDT")
        
        session.add(balance1)
        await session.commit()
        
        session.add(balance2)
        with pytest.raises(Exception):  # UniqueConstraint violation
            await session.commit()
        
        await session.rollback()
        
        # 정리
        await session.delete(balance1)
        await session.delete(user)
        await session.commit()
```

### 12. Makefile 업데이트

Makefile에 데이터베이스 관련 명령 추가:

```makefile
# 기존 내용에 추가

db-init:
	poetry run python scripts/init_db.py

db-migrate:
	poetry run alembic revision --autogenerate -m "$(m)"

db-upgrade:
	poetry run alembic upgrade head

db-downgrade:
	poetry run alembic downgrade -1

db-history:
	poetry run alembic history
```

## 실행 및 검증

1. 데이터베이스 마이그레이션 실행:
   ```bash
   make db-upgrade
   ```

2. 테스트 실행:
   ```bash
   make test
   ```

3. 데이터베이스 테이블 확인:
   ```bash
   docker exec -it dantarowallet_postgres_1 psql -U postgres -d dantarowallet
   \dt
   \d users
   \d balances
   ```

## 검증 포인트

- [ ] Alembic 마이그레이션이 정상 실행되는가?
- [ ] users와 balances 테이블이 생성되었는가?
- [ ] 모든 제약 조건이 정상 작동하는가?
- [ ] 비동기 세션이 정상 작동하는가?
- [ ] 모델 관계가 올바르게 설정되었는가?
- [ ] 모든 테스트가 통과하는가?

이 문서를 완료하면 데이터베이스 기초 구조가 완성되며, User와 Balance 모델을 사용할 준비가 됩니다.