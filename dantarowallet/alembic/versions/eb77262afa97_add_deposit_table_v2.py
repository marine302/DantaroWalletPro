"""add_deposit_table_v2

Revision ID: eb77262afa97
Revises: 4badefa63d4b
Create Date: 2025-07-03 04:00:40.609923

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "eb77262afa97"
down_revision: Union[str, None] = "4badefa63d4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "deposits",
        sa.Column("tx_hash", sa.String(length=64), nullable=False),
        sa.Column("from_address", sa.String(length=42), nullable=False),
        sa.Column("to_address", sa.String(length=42), nullable=False),
        sa.Column("amount", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column("token_symbol", sa.String(length=10), nullable=False),
        sa.Column("token_contract", sa.String(length=42), nullable=True),
        sa.Column("block_number", sa.Integer(), nullable=False),
        sa.Column("block_timestamp", sa.Integer(), nullable=False),
        sa.Column("transaction_index", sa.Integer(), nullable=False),
        sa.Column("confirmations", sa.Integer(), nullable=False),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False),
        sa.Column("min_confirmations", sa.Integer(), nullable=False),
        sa.Column("is_processed", sa.Boolean(), nullable=False),
        sa.Column("processed_at", sa.String(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("wallet_id", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["wallet_id"],
            ["wallets.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_deposit_block",
        "deposits",
        ["block_number", "transaction_index"],
        unique=False,
    )
    op.create_index(
        "idx_deposit_status", "deposits", ["is_confirmed", "is_processed"], unique=False
    )
    op.create_index(
        "idx_deposit_user_token", "deposits", ["user_id", "token_symbol"], unique=False
    )
    op.create_index(
        op.f("ix_deposits_block_number"), "deposits", ["block_number"], unique=False
    )
    op.create_index(
        op.f("ix_deposits_from_address"), "deposits", ["from_address"], unique=False
    )
    op.create_index(op.f("ix_deposits_id"), "deposits", ["id"], unique=False)
    op.create_index(
        op.f("ix_deposits_to_address"), "deposits", ["to_address"], unique=False
    )
    op.create_index(op.f("ix_deposits_tx_hash"), "deposits", ["tx_hash"], unique=True)
    op.create_index(op.f("ix_deposits_user_id"), "deposits", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_deposits_wallet_id"), "deposits", ["wallet_id"], unique=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_deposits_wallet_id"), table_name="deposits")
    op.drop_index(op.f("ix_deposits_user_id"), table_name="deposits")
    op.drop_index(op.f("ix_deposits_tx_hash"), table_name="deposits")
    op.drop_index(op.f("ix_deposits_to_address"), table_name="deposits")
    op.drop_index(op.f("ix_deposits_id"), table_name="deposits")
    op.drop_index(op.f("ix_deposits_from_address"), table_name="deposits")
    op.drop_index(op.f("ix_deposits_block_number"), table_name="deposits")
    op.drop_index("idx_deposit_user_token", table_name="deposits")
    op.drop_index("idx_deposit_status", table_name="deposits")
    op.drop_index("idx_deposit_block", table_name="deposits")
    op.drop_table("deposits")
    # ### end Alembic commands ###
