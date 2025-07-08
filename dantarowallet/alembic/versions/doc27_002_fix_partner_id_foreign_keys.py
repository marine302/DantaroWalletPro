"""fix_partner_id_foreign_keys

Revision ID: doc27_002
Revises: doc27_001_sweep_automation
Create Date: 2025-07-08 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'doc27_002'
down_revision = 'doc27_001_sweep_automation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Partner ID foreign key 타입을 Integer에서 String(36)으로 변경
    
    SQLite의 제한으로 인해 테이블을 다시 생성해야 합니다.
    """
    
    # SQLite에서는 ALTER COLUMN이 제한되어 있으므로 테이블 재생성 방식 사용
    
    # 1. 기존 데이터 백업을 위한 임시 테이블 생성
    op.execute("""
        CREATE TABLE hd_wallet_masters_backup AS 
        SELECT * FROM hd_wallet_masters
    """)
    
    op.execute("""
        CREATE TABLE sweep_configurations_backup AS 
        SELECT * FROM sweep_configurations
    """)
    
    # 2. 기존 테이블 삭제
    op.drop_table('hd_wallet_masters')
    op.drop_table('sweep_configurations')
    
    # 3. 새로운 스키마로 테이블 재생성 (partner_id를 String(36)으로)
    op.create_table('hd_wallet_masters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.String(length=36), nullable=False),
        sa.Column('encrypted_seed', sa.String(length=500), nullable=False),
        sa.Column('public_key', sa.String(length=130), nullable=False),
        sa.Column('derivation_path', sa.String(length=100), nullable=True),
        sa.Column('last_index', sa.Integer(), nullable=True),
        sa.Column('encryption_method', sa.String(length=50), nullable=True),
        sa.Column('key_version', sa.Integer(), nullable=True),
        sa.Column('total_addresses_generated', sa.Integer(), nullable=True),
        sa.Column('total_sweep_amount', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('partner_id')
    )
    
    op.create_table('sweep_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.String(length=36), nullable=False),
        sa.Column('destination_wallet_id', sa.Integer(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=True),
        sa.Column('auto_sweep_enabled', sa.Boolean(), nullable=True),
        sa.Column('min_sweep_amount', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('max_sweep_amount', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('sweep_interval_minutes', sa.Integer(), nullable=True),
        sa.Column('immediate_threshold', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('daily_sweep_time', sa.String(length=5), nullable=True),
        sa.Column('max_gas_price_sun', sa.Numeric(precision=20, scale=0), nullable=True),
        sa.Column('gas_optimization_enabled', sa.Boolean(), nullable=True),
        sa.Column('gas_price_multiplier', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('batch_enabled', sa.Boolean(), nullable=True),
        sa.Column('max_batch_size', sa.Integer(), nullable=True),
        sa.Column('batch_delay_seconds', sa.Integer(), nullable=True),
        sa.Column('daily_sweep_limit', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('total_sweeps', sa.Integer(), nullable=True),
        sa.Column('total_sweep_amount', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('last_sweep_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['destination_wallet_id'], ['partner_wallets.id'], ),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('partner_id')
    )
    
    # 4. 데이터 복원 (partner_id를 적절히 변환)
    op.execute("""
        INSERT INTO hd_wallet_masters 
        SELECT * FROM hd_wallet_masters_backup
    """)
    
    op.execute("""
        INSERT INTO sweep_configurations 
        SELECT * FROM sweep_configurations_backup
    """)
    
    # 5. 백업 테이블 삭제
    op.drop_table('hd_wallet_masters_backup')
    op.drop_table('sweep_configurations_backup')
    
    # 6. 인덱스 생성
    op.create_index('ix_hd_wallet_masters_id', 'hd_wallet_masters', ['id'])
    op.create_index('ix_sweep_configurations_id', 'sweep_configurations', ['id'])


def downgrade() -> None:
    """
    String(36)에서 Integer로 되돌리기
    """
    
    # 1. 기존 데이터 백업
    op.execute("""
        CREATE TABLE hd_wallet_masters_backup AS 
        SELECT * FROM hd_wallet_masters
    """)
    
    op.execute("""
        CREATE TABLE sweep_configurations_backup AS 
        SELECT * FROM sweep_configurations
    """)
    
    # 2. 기존 테이블 삭제
    op.drop_table('hd_wallet_masters')
    op.drop_table('sweep_configurations')
    
    # 3. 이전 스키마로 테이블 재생성 (partner_id를 Integer로)
    op.create_table('hd_wallet_masters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.Integer(), nullable=False),
        sa.Column('encrypted_seed', sa.String(length=500), nullable=False),
        sa.Column('public_key', sa.String(length=130), nullable=False),
        sa.Column('derivation_path', sa.String(length=100), nullable=True),
        sa.Column('last_index', sa.Integer(), nullable=True),
        sa.Column('encryption_method', sa.String(length=50), nullable=True),
        sa.Column('key_version', sa.Integer(), nullable=True),
        sa.Column('total_addresses_generated', sa.Integer(), nullable=True),
        sa.Column('total_sweep_amount', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('partner_id')
    )
    
    op.create_table('sweep_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.Integer(), nullable=False),
        sa.Column('destination_wallet_id', sa.Integer(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=True),
        sa.Column('auto_sweep_enabled', sa.Boolean(), nullable=True),
        sa.Column('min_sweep_amount', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('max_sweep_amount', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('sweep_interval_minutes', sa.Integer(), nullable=True),
        sa.Column('immediate_threshold', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('daily_sweep_time', sa.String(length=5), nullable=True),
        sa.Column('max_gas_price_sun', sa.Numeric(precision=20, scale=0), nullable=True),
        sa.Column('gas_optimization_enabled', sa.Boolean(), nullable=True),
        sa.Column('gas_price_multiplier', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('batch_enabled', sa.Boolean(), nullable=True),
        sa.Column('max_batch_size', sa.Integer(), nullable=True),
        sa.Column('batch_delay_seconds', sa.Integer(), nullable=True),
        sa.Column('daily_sweep_limit', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('total_sweeps', sa.Integer(), nullable=True),
        sa.Column('total_sweep_amount', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('last_sweep_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['destination_wallet_id'], ['partner_wallets.id'], ),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('partner_id')
    )
    
    # 4. 데이터 복원
    op.execute("""
        INSERT INTO hd_wallet_masters 
        SELECT * FROM hd_wallet_masters_backup
    """)
    
    op.execute("""
        INSERT INTO sweep_configurations 
        SELECT * FROM sweep_configurations_backup
    """)
    
    # 5. 백업 테이블 삭제
    op.drop_table('hd_wallet_masters_backup')
    op.drop_table('sweep_configurations_backup')
