"""add_partner_wallet_for_tronlink

Revision ID: tronlink_001
Revises: 6df3c98916b7
Create Date: 2025-07-08 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = 'tronlink_001'
down_revision: Union[str, None] = '6df3c98916b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create partner_wallets table for TronLink integration
    op.create_table('partner_wallets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('partner_id', sa.String(length=36), nullable=False),
        sa.Column('wallet_type', sa.Enum('TRONLINK', 'METAMASK', 'TRONLINK_PRO', 'INTERNAL', name='partnerwallettype'), nullable=False),
        sa.Column('address', sa.String(length=42), nullable=False),
        sa.Column('label', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, default=False),
        sa.Column('balance_usdt', sa.Numeric(precision=20, scale=6), nullable=False, default=0),
        sa.Column('balance_trx', sa.Numeric(precision=20, scale=6), nullable=False, default=0),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], name='fk_partner_wallets_partner_id'),
        sa.UniqueConstraint('partner_id', 'address', name='uq_partner_wallet_address')
    )
    
    # Create indexes
    op.create_index('ix_partner_wallets_id', 'partner_wallets', ['id'])
    op.create_index('ix_partner_wallets_partner_id', 'partner_wallets', ['partner_id'])
    op.create_index('ix_partner_wallets_address', 'partner_wallets', ['address'])
    op.create_index('ix_partner_wallets_wallet_type', 'partner_wallets', ['wallet_type'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_partner_wallets_wallet_type', 'partner_wallets')
    op.drop_index('ix_partner_wallets_address', 'partner_wallets')
    op.drop_index('ix_partner_wallets_partner_id', 'partner_wallets')
    op.drop_index('ix_partner_wallets_id', 'partner_wallets')
    
    # Drop partner_wallets table
    op.drop_table('partner_wallets')
