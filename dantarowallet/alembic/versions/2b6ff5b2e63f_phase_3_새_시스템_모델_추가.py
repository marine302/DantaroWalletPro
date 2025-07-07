"""Phase 3: 새 시스템 모델 추가

Revision ID: 2b6ff5b2e63f
Revises: sa002
Create Date: 2025-07-07 14:48:51.392742

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b6ff5b2e63f'
down_revision: Union[str, None] = 'sa002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 에너지 사용 이력 테이블
    op.create_table('energy_usage_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('partner_id', sa.String(), nullable=True),
        sa.Column('transaction_type', sa.String(50), nullable=False),
        sa.Column('energy_amount', sa.Integer(), nullable=False),
        sa.Column('before_amount', sa.Integer(), nullable=True),
        sa.Column('after_amount', sa.Integer(), nullable=True),
        sa.Column('transaction_id', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 수수료 설정 이력 테이블
    op.create_table('fee_config_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('partner_id', sa.String(), nullable=True),
        sa.Column('old_config', sa.JSON(), nullable=True),
        sa.Column('new_config', sa.JSON(), nullable=True),
        sa.Column('change_reason', sa.String(255), nullable=True),
        sa.Column('changed_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 시스템 메트릭스 테이블
    op.create_table('system_metrics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('metric_type', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.DECIMAL(10, 4), nullable=False),
        sa.Column('metric_unit', sa.String(20), nullable=True),
        sa.Column('partner_id', sa.String(), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('system_metrics')
    op.drop_table('fee_config_history') 
    op.drop_table('energy_usage_history')
