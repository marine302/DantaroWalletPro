"""Add partner fee and policy models for Doc-26

Revision ID: doc26_001_partner_fee_policies
Revises: doc25_001_add_doc25_energy_monitoring_models
Create Date: 2025-07-08 18:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'doc26_001_partner_fee_policies'
down_revision = 'doc25_001'
branch_labels = None
depends_on = None


def upgrade():
    """Create partner fee and policy tables"""
    
    # Create partner_fee_policies table
    op.create_table('partner_fee_policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.String(length=36), nullable=False),
        sa.Column('fee_type', sa.Enum('FLAT', 'PERCENTAGE', 'TIERED', 'DYNAMIC', name='feetype'), nullable=True),
        sa.Column('base_fee_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('min_fee_amount', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('max_fee_amount', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('withdrawal_fee_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('internal_transfer_fee_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('vip_discount_rates', sa.JSON(), nullable=True),
        sa.Column('promotion_active', sa.Boolean(), nullable=True),
        sa.Column('promotion_fee_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('promotion_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('platform_share_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='파트너사 수수료 정책'
    )
    op.create_index(op.f('ix_partner_fee_policies_id'), 'partner_fee_policies', ['id'], unique=False)
    op.create_index('ix_partner_fee_policies_partner_id', 'partner_fee_policies', ['partner_id'], unique=True)
    
    # Create fee_tiers table
    op.create_table('fee_tiers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fee_policy_id', sa.Integer(), nullable=False),
        sa.Column('min_amount', sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column('max_amount', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('fee_rate', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('fixed_fee', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['fee_policy_id'], ['partner_fee_policies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='구간별 수수료 설정'
    )
    op.create_index(op.f('ix_fee_tiers_id'), 'fee_tiers', ['id'], unique=False)
    op.create_index('ix_fee_tiers_policy_amount', 'fee_tiers', ['fee_policy_id', 'min_amount'], unique=False)
    
    # Create partner_withdrawal_policies table
    op.create_table('partner_withdrawal_policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.String(length=36), nullable=False),
        sa.Column('policy_type', sa.Enum('REALTIME', 'BATCH', 'HYBRID', 'MANUAL', name='withdrawalpolicy'), nullable=True),
        sa.Column('realtime_enabled', sa.Boolean(), nullable=True),
        sa.Column('realtime_max_amount', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('auto_approve_enabled', sa.Boolean(), nullable=True),
        sa.Column('auto_approve_max_amount', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('batch_enabled', sa.Boolean(), nullable=True),
        sa.Column('batch_schedule', sa.JSON(), nullable=True),
        sa.Column('batch_min_amount', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('daily_limit_per_user', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('daily_limit_total', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('single_transaction_limit', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('whitelist_required', sa.Boolean(), nullable=True),
        sa.Column('whitelist_addresses', sa.JSON(), nullable=True),
        sa.Column('require_2fa', sa.Boolean(), nullable=True),
        sa.Column('confirmation_blocks', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='파트너사 출금 정책'
    )
    op.create_index(op.f('ix_partner_withdrawal_policies_id'), 'partner_withdrawal_policies', ['id'], unique=False)
    op.create_index('ix_partner_withdrawal_policies_partner_id', 'partner_withdrawal_policies', ['partner_id'], unique=True)
    
    # Create partner_energy_policies table
    op.create_table('partner_energy_policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.String(length=36), nullable=False),
        sa.Column('default_policy', sa.Enum('WAIT_QUEUE', 'TRX_PAYMENT', 'PRIORITY_QUEUE', 'REJECT', name='energypolicy'), nullable=True),
        sa.Column('trx_payment_enabled', sa.Boolean(), nullable=True),
        sa.Column('trx_payment_markup', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('trx_payment_max_fee', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('queue_enabled', sa.Boolean(), nullable=True),
        sa.Column('queue_max_wait_hours', sa.Integer(), nullable=True),
        sa.Column('queue_notification_enabled', sa.Boolean(), nullable=True),
        sa.Column('priority_queue_enabled', sa.Boolean(), nullable=True),
        sa.Column('vip_priority_levels', sa.JSON(), nullable=True),
        sa.Column('energy_saving_enabled', sa.Boolean(), nullable=True),
        sa.Column('energy_saving_threshold', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='파트너사 에너지 대응 정책'
    )
    op.create_index(op.f('ix_partner_energy_policies_id'), 'partner_energy_policies', ['id'], unique=False)
    op.create_index('ix_partner_energy_policies_partner_id', 'partner_energy_policies', ['partner_id'], unique=True)
    
    # Create user_tiers table
    op.create_table('user_tiers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.String(length=36), nullable=False),
        sa.Column('tier_name', sa.String(length=50), nullable=False),
        sa.Column('tier_level', sa.Integer(), nullable=False),
        sa.Column('min_volume', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('fee_discount_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('withdrawal_limit_multiplier', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('benefits', sa.JSON(), nullable=True),
        sa.Column('upgrade_conditions', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='사용자 등급 관리'
    )
    op.create_index(op.f('ix_user_tiers_id'), 'user_tiers', ['id'], unique=False)
    op.create_index('ix_user_tiers_partner_level', 'user_tiers', ['partner_id', 'tier_level'], unique=False)
    
    # Create partner_fee_calculation_logs table
    op.create_table('partner_fee_calculation_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.String(length=36), nullable=False),
        sa.Column('transaction_id', sa.String(length=100), nullable=True),
        sa.Column('transaction_amount', sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column('base_fee_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('applied_fee_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('discount_rate', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('calculated_fee', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('platform_share', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('partner_share', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('policy_details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='수수료 계산 로그'
    )
    op.create_index(op.f('ix_partner_fee_calculation_logs_id'), 'partner_fee_calculation_logs', ['id'], unique=False)
    op.create_index('ix_partner_fee_calculation_logs_partner_date', 'partner_fee_calculation_logs', ['partner_id', 'created_at'], unique=False)
    op.create_index('ix_partner_fee_calculation_logs_transaction', 'partner_fee_calculation_logs', ['transaction_id'], unique=False)


def downgrade():
    """Drop partner fee and policy tables"""
    
    # Drop tables in reverse order
    op.drop_index('ix_partner_fee_calculation_logs_transaction', table_name='partner_fee_calculation_logs')
    op.drop_index('ix_partner_fee_calculation_logs_partner_date', table_name='partner_fee_calculation_logs')
    op.drop_index(op.f('ix_partner_fee_calculation_logs_id'), table_name='partner_fee_calculation_logs')
    op.drop_table('partner_fee_calculation_logs')
    
    op.drop_index('ix_user_tiers_partner_level', table_name='user_tiers')
    op.drop_index(op.f('ix_user_tiers_id'), table_name='user_tiers')
    op.drop_table('user_tiers')
    
    op.drop_index('ix_partner_energy_policies_partner_id', table_name='partner_energy_policies')
    op.drop_index(op.f('ix_partner_energy_policies_id'), table_name='partner_energy_policies')
    op.drop_table('partner_energy_policies')
    
    op.drop_index('ix_partner_withdrawal_policies_partner_id', table_name='partner_withdrawal_policies')
    op.drop_index(op.f('ix_partner_withdrawal_policies_id'), table_name='partner_withdrawal_policies')
    op.drop_table('partner_withdrawal_policies')
    
    op.drop_index('ix_fee_tiers_policy_amount', table_name='fee_tiers')
    op.drop_index(op.f('ix_fee_tiers_id'), table_name='fee_tiers')
    op.drop_table('fee_tiers')
    
    op.drop_index('ix_partner_fee_policies_partner_id', table_name='partner_fee_policies')
    op.drop_index(op.f('ix_partner_fee_policies_id'), table_name='partner_fee_policies')
    op.drop_table('partner_fee_policies')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS energypolicy CASCADE")
    op.execute("DROP TYPE IF EXISTS withdrawalpolicy CASCADE") 
    op.execute("DROP TYPE IF EXISTS feetype CASCADE")
