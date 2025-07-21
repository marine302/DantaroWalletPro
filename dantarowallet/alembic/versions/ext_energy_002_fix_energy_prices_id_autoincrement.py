"""fix energy_prices id autoincrement

Revision ID: ext_energy_002
Revises: ext_energy_001
Create Date: 2025-07-21 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ext_energy_002'
down_revision = 'ext_energy_001'
branch_labels = None
depends_on = None


def upgrade():
    # Drop existing table and recreate with correct autoincrement
    op.drop_table('energy_prices')
    
    # Recreate with INTEGER for SQLite autoincrement
    op.create_table('energy_prices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
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
    
    # Recreate index
    op.create_index('idx_provider_timestamp', 'energy_prices', ['provider_id', 'timestamp'])


def downgrade():
    # Drop and recreate with original schema
    op.drop_table('energy_prices')
    
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
    
    op.create_index('idx_provider_timestamp', 'energy_prices', ['provider_id', 'timestamp'])
