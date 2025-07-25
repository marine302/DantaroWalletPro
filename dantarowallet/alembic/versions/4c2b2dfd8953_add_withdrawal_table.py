"""Add withdrawal table

Revision ID: 4c2b2dfd8953
Revises: eb77262afa97
Create Date: 2025-07-03 04:29:33.245889

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4c2b2dfd8953"
down_revision: Union[str, None] = "eb77262afa97"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "withdrawals",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("to_address", sa.String(length=42), nullable=False),
        sa.Column("amount", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column("fee", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column("net_amount", sa.Numeric(precision=28, scale=8), nullable=False),
        sa.Column("asset", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("priority", sa.String(length=10), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("processed_by", sa.Integer(), nullable=True),
        sa.Column("tx_hash", sa.String(length=100), nullable=True),
        sa.Column("tx_fee", sa.Numeric(precision=28, scale=8), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=200), nullable=True),
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
            ["approved_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["processed_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_withdrawal_requested_at", "withdrawals", ["requested_at"], unique=False
    )
    op.create_index(
        "idx_withdrawal_status_priority",
        "withdrawals",
        ["status", "priority"],
        unique=False,
    )
    op.create_index(
        "idx_withdrawal_user_status", "withdrawals", ["user_id", "status"], unique=False
    )
    op.create_index(op.f("ix_withdrawals_id"), "withdrawals", ["id"], unique=False)
    op.create_index(
        op.f("ix_withdrawals_status"), "withdrawals", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_withdrawals_to_address"), "withdrawals", ["to_address"], unique=False
    )
    op.create_index(
        op.f("ix_withdrawals_tx_hash"), "withdrawals", ["tx_hash"], unique=True
    )
    op.create_index(
        op.f("ix_withdrawals_user_id"), "withdrawals", ["user_id"], unique=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_withdrawals_user_id"), table_name="withdrawals")
    op.drop_index(op.f("ix_withdrawals_tx_hash"), table_name="withdrawals")
    op.drop_index(op.f("ix_withdrawals_to_address"), table_name="withdrawals")
    op.drop_index(op.f("ix_withdrawals_status"), table_name="withdrawals")
    op.drop_index(op.f("ix_withdrawals_id"), table_name="withdrawals")
    op.drop_index("idx_withdrawal_user_status", table_name="withdrawals")
    op.drop_index("idx_withdrawal_status_priority", table_name="withdrawals")
    op.drop_index("idx_withdrawal_requested_at", table_name="withdrawals")
    op.drop_table("withdrawals")
    # ### end Alembic commands ###
