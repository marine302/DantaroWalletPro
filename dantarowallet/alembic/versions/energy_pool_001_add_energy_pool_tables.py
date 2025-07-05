"""add_energy_pool_tables

Revision ID: energy_pool_001
Revises: e78898c0e488
Create Date: 2025-07-05 17:55:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "energy_pool_001"
down_revision: Union[str, None] = "e78898c0e488"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Energy Pool 테이블 생성
    op.create_table(
        "energy_pools",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "pool_name", sa.String(length=100), nullable=False, comment="에너지 풀 이름"
        ),
        sa.Column(
            "wallet_address",
            sa.String(length=50),
            nullable=False,
            comment="본사 TRON 지갑 주소",
        ),
        sa.Column(
            "total_frozen_trx",
            sa.Numeric(precision=18, scale=6),
            nullable=False,
            comment="총 freeze된 TRX 양",
        ),
        sa.Column(
            "frozen_for_energy",
            sa.Numeric(precision=18, scale=6),
            nullable=False,
            comment="에너지용 freeze TRX",
        ),
        sa.Column(
            "frozen_for_bandwidth",
            sa.Numeric(precision=18, scale=6),
            nullable=False,
            comment="대역폭용 freeze TRX",
        ),
        sa.Column(
            "available_energy", sa.BigInteger(), nullable=False, comment="사용 가능한 에너지"
        ),
        sa.Column(
            "available_bandwidth", sa.BigInteger(), nullable=False, comment="사용 가능한 대역폭"
        ),
        sa.Column(
            "daily_energy_consumption",
            sa.BigInteger(),
            nullable=False,
            comment="일일 에너지 소비량",
        ),
        sa.Column(
            "daily_bandwidth_consumption",
            sa.BigInteger(),
            nullable=False,
            comment="일일 대역폭 소비량",
        ),
        sa.Column(
            "auto_refreeze_enabled",
            sa.Boolean(),
            nullable=True,
            comment="자동 refreeze 활성화",
        ),
        sa.Column(
            "energy_threshold", sa.BigInteger(), nullable=False, comment="에너지 부족 임계값"
        ),
        sa.Column(
            "bandwidth_threshold", sa.BigInteger(), nullable=False, comment="대역폭 부족 임계값"
        ),
        sa.Column(
            "last_freeze_cost",
            sa.Numeric(precision=18, scale=6),
            nullable=True,
            comment="마지막 freeze 비용",
        ),
        sa.Column(
            "total_freeze_cost",
            sa.Numeric(precision=18, scale=6),
            nullable=False,
            comment="총 freeze 비용",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=True, comment="활성화 상태"),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=True,
            comment="마지막 업데이트",
        ),
        sa.Column("notes", sa.Text(), nullable=True, comment="관리자 노트"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_energy_pools_id"), "energy_pools", ["id"], unique=False)

    # Energy Usage Log 테이블 생성
    op.create_table(
        "energy_usage_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("energy_pool_id", sa.Integer(), nullable=False, comment="에너지 풀 ID"),
        sa.Column(
            "transaction_hash",
            sa.String(length=64),
            nullable=True,
            comment="TRON 트랜잭션 해시",
        ),
        sa.Column(
            "transaction_type",
            sa.String(length=50),
            nullable=False,
            comment="트랜잭션 타입 (USDT_TRANSFER, TRX_TRANSFER)",
        ),
        sa.Column(
            "energy_consumed", sa.BigInteger(), nullable=False, comment="소비된 에너지"
        ),
        sa.Column(
            "bandwidth_consumed", sa.BigInteger(), nullable=False, comment="소비된 대역폭"
        ),
        sa.Column(
            "trx_cost_equivalent",
            sa.Numeric(precision=18, scale=6),
            nullable=True,
            comment="TRX 환산 비용",
        ),
        sa.Column("user_id", sa.Integer(), nullable=True, comment="사용자 ID"),
        sa.Column("from_address", sa.String(length=50), nullable=True, comment="발신 주소"),
        sa.Column("to_address", sa.String(length=50), nullable=True, comment="수신 주소"),
        sa.Column(
            "amount", sa.Numeric(precision=18, scale=6), nullable=True, comment="전송 금액"
        ),
        sa.Column("asset", sa.String(length=20), nullable=True, comment="자산 종류"),
        sa.Column("block_number", sa.BigInteger(), nullable=True, comment="블록 번호"),
        sa.Column(
            "timestamp", sa.DateTime(timezone=True), nullable=False, comment="트랜잭션 시간"
        ),
        sa.Column("notes", sa.Text(), nullable=True, comment="추가 메모"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_energy_usage_logs_id"), "energy_usage_logs", ["id"], unique=False
    )

    # Energy Price History 테이블 생성
    op.create_table(
        "energy_price_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "trx_price_usd",
            sa.Numeric(precision=18, scale=8),
            nullable=False,
            comment="TRX 가격 (USD)",
        ),
        sa.Column(
            "energy_per_trx", sa.BigInteger(), nullable=False, comment="TRX당 획득 가능한 에너지"
        ),
        sa.Column(
            "bandwidth_per_trx",
            sa.BigInteger(),
            nullable=False,
            comment="TRX당 획득 가능한 대역폭",
        ),
        sa.Column(
            "total_frozen_trx",
            sa.Numeric(precision=18, scale=6),
            nullable=True,
            comment="전체 네트워크 freeze TRX",
        ),
        sa.Column(
            "energy_utilization",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
            comment="네트워크 에너지 사용률 (%)",
        ),
        sa.Column(
            "usdt_transfer_cost",
            sa.Numeric(precision=18, scale=6),
            nullable=True,
            comment="USDT 전송 비용 (TRX)",
        ),
        sa.Column(
            "trx_transfer_cost",
            sa.Numeric(precision=18, scale=6),
            nullable=True,
            comment="TRX 전송 비용 (TRX)",
        ),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.String(length=50),
            nullable=True,
            comment="데이터 소스 (API, Manual)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_energy_price_history_id"), "energy_price_history", ["id"], unique=False
    )


def downgrade() -> None:
    # 테이블 삭제 (역순)
    op.drop_index(op.f("ix_energy_price_history_id"), table_name="energy_price_history")
    op.drop_table("energy_price_history")

    op.drop_index(op.f("ix_energy_usage_logs_id"), table_name="energy_usage_logs")
    op.drop_table("energy_usage_logs")

    op.drop_index(op.f("ix_energy_pools_id"), table_name="energy_pools")
    op.drop_table("energy_pools")
