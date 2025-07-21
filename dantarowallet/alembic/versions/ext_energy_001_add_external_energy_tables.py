"""add external energy tables

Revision ID: ext_energy_001
Revises: doc25_001
Create Date: 2025-07-21 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ext_energy_001'
down_revision = 'doc25_001'
branch_labels = None
depends_on = None


def upgrade():
    # Create energy_providers table
    op.create_table('energy_providers',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('api_endpoint', sa.String(length=255), nullable=False),
        sa.Column('api_key_encrypted', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('ONLINE', 'OFFLINE', 'MAINTENANCE', name='providerstatus'), server_default='ONLINE'),
        sa.Column('reliability_score', sa.Numeric(precision=5, scale=2), server_default='0.00'),
        sa.Column('response_time_avg', sa.Numeric(precision=8, scale=2), server_default='0.00'),
        sa.Column('min_order_size', sa.BigInteger(), server_default='0'),
        sa.Column('max_order_size', sa.BigInteger(), server_default='0'),
        sa.Column('trading_fee', sa.Numeric(precision=8, scale=6), server_default='0.000000'),
        sa.Column('withdrawal_fee', sa.Numeric(precision=8, scale=6), server_default='0.000000'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create energy_prices table
    op.create_table('energy_prices',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('provider_id', sa.String(length=50), nullable=False),
        sa.Column('price', sa.Numeric(precision=12, scale=8), nullable=False),
        sa.Column('currency', sa.String(length=10), server_default='TRX'),
        sa.Column('available_energy', sa.BigInteger(), server_default='0'),
        sa.Column('volume_24h', sa.BigInteger(), server_default='0'),
        sa.Column('change_24h', sa.Numeric(precision=8, scale=4), server_default='0.0000'),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['provider_id'], ['energy_providers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index
    op.create_index('idx_provider_timestamp', 'energy_prices', ['provider_id', 'timestamp'])

    # Create energy_orders table
    op.create_table('energy_orders',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('provider_id', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.BigInteger(), nullable=False),
        sa.Column('price', sa.Numeric(precision=12, scale=8), nullable=False),
        sa.Column('total_cost', sa.Numeric(precision=16, scale=8), nullable=False),
        sa.Column('order_type', sa.Enum('MARKET', 'LIMIT', name='ordertype'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'FILLED', 'CANCELLED', 'FAILED', name='orderstatus'), server_default='PENDING'),
        sa.Column('duration', sa.BigInteger(), server_default='1'),
        sa.Column('trading_fee', sa.Numeric(precision=16, scale=8), server_default='0.00000000'),
        sa.Column('withdrawal_fee', sa.Numeric(precision=16, scale=8), server_default='0.00000000'),
        sa.Column('external_order_id', sa.String(length=100)),
        sa.Column('transaction_hash', sa.String(length=100)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('filled_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['provider_id'], ['energy_providers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_user_status', 'energy_orders', ['user_id', 'status'])
    op.create_index('idx_provider_status', 'energy_orders', ['provider_id', 'status'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_provider_status', table_name='energy_orders')
    op.drop_index('idx_user_status', table_name='energy_orders')
    op.drop_index('idx_provider_timestamp', table_name='energy_prices')
    
    # Drop tables
    op.drop_table('energy_orders')
    op.drop_table('energy_prices')
    op.drop_table('energy_providers')
