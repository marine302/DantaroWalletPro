"""Add Sweep HD Wallet tables

Revision ID: sweep_001
Revises: 6df3c98916b7
Create Date: 2025-07-08 15:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'sweep_001'
down_revision = '6df3c98916b7'
branch_labels = None
depends_on = None


def upgrade():
    # HD Wallet Masters 테이블
    op.create_table('hd_wallet_masters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.String(36), nullable=False),
        sa.Column('encrypted_seed', sa.String(500), nullable=False, comment='암호화된 마스터 시드'),
        sa.Column('public_key', sa.String(130), nullable=False, comment='마스터 공개키'),
        sa.Column('derivation_path', sa.String(100), nullable=True, default="m/44'/195'/0'/0", comment='TRON 파생 경로'),
        sa.Column('last_index', sa.Integer(), nullable=True, default=0, comment='마지막 사용 인덱스'),
        sa.Column('encryption_method', sa.String(50), nullable=True, default='AES-256-GCM', comment='암호화 방식'),
        sa.Column('key_version', sa.Integer(), nullable=True, default=1, comment='키 버전'),
        sa.Column('total_addresses_generated', sa.Integer(), nullable=True, default=0, comment='총 생성된 주소 수'),
        sa.Column('total_sweep_amount', sa.Numeric(18, 8), nullable=True, default=0, comment='총 Sweep 금액'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('partner_id')
    )
    op.create_index(op.f('ix_hd_wallet_masters_id'), 'hd_wallet_masters', ['id'], unique=False)

    # User Deposit Addresses 테이블
    op.create_table('user_deposit_addresses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hd_wallet_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('address', sa.String(50), nullable=False, comment='TRON 주소'),
        sa.Column('derivation_index', sa.Integer(), nullable=False, comment='파생 인덱스'),
        sa.Column('encrypted_private_key', sa.String(500), nullable=False, comment='암호화된 개인키'),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True, comment='활성 상태'),
        sa.Column('is_monitored', sa.Boolean(), nullable=True, default=True, comment='모니터링 상태'),
        sa.Column('total_received', sa.Numeric(18, 8), nullable=True, default=0, comment='총 수신 금액'),
        sa.Column('total_swept', sa.Numeric(18, 8), nullable=True, default=0, comment='총 Sweep 금액'),
        sa.Column('last_deposit_at', sa.DateTime(timezone=True), nullable=True, comment='마지막 입금 시간'),
        sa.Column('last_sweep_at', sa.DateTime(timezone=True), nullable=True, comment='마지막 Sweep 시간'),
        sa.Column('min_sweep_amount', sa.Numeric(18, 8), nullable=True, comment='최소 Sweep 금액'),
        sa.Column('priority_level', sa.Integer(), nullable=True, default=1, comment='우선순위'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['hd_wallet_id'], ['hd_wallet_masters.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('address')
    )
    op.create_index(op.f('ix_user_deposit_addresses_id'), 'user_deposit_addresses', ['id'], unique=False)
    op.create_index(op.f('ix_user_deposit_addresses_user_id'), 'user_deposit_addresses', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_deposit_addresses_address'), 'user_deposit_addresses', ['address'], unique=False)

    # Sweep Configuration 테이블
    op.create_table('sweep_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.String(36), nullable=False),
        sa.Column('collection_address', sa.String(50), nullable=False, comment='수집 주소'),
        sa.Column('min_sweep_amount', sa.Numeric(18, 8), nullable=True, default=1.0, comment='최소 Sweep 금액'),
        sa.Column('max_sweep_amount', sa.Numeric(18, 8), nullable=True, comment='최대 Sweep 금액'),
        sa.Column('sweep_fee_rate', sa.Numeric(5, 4), nullable=True, default=0.001, comment='Sweep 수수료율'),
        sa.Column('energy_limit', sa.Integer(), nullable=True, default=15000000, comment='에너지 한도'),
        sa.Column('auto_sweep_enabled', sa.Boolean(), nullable=True, default=True, comment='자동 Sweep 활성화'),
        sa.Column('sweep_interval_seconds', sa.Integer(), nullable=True, default=300, comment='Sweep 주기(초)'),
        sa.Column('max_batch_size', sa.Integer(), nullable=True, default=10, comment='배치 최대 크기'),
        sa.Column('priority_threshold', sa.Numeric(18, 8), nullable=True, comment='우선 처리 임계값'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('partner_id')
    )
    op.create_index(op.f('ix_sweep_configurations_id'), 'sweep_configurations', ['id'], unique=False)

    # Sweep Queue 테이블
    op.create_table('sweep_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('deposit_address_id', sa.Integer(), nullable=False),
        sa.Column('sweep_config_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(18, 8), nullable=False, comment='Sweep 금액'),
        sa.Column('estimated_fee', sa.Numeric(18, 8), nullable=True, comment='예상 수수료'),
        sa.Column('status', sa.String(20), nullable=True, default='pending', comment='상태'),
        sa.Column('priority', sa.Integer(), nullable=True, default=1, comment='우선순위'),
        sa.Column('retry_count', sa.Integer(), nullable=True, default=0, comment='재시도 횟수'),
        sa.Column('max_retry_count', sa.Integer(), nullable=True, default=3, comment='최대 재시도 횟수'),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True, comment='예약 시간'),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True, comment='처리 시간'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='오류 메시지'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['deposit_address_id'], ['user_deposit_addresses.id'], ),
        sa.ForeignKeyConstraint(['sweep_config_id'], ['sweep_configurations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sweep_queue_id'), 'sweep_queue', ['id'], unique=False)
    op.create_index(op.f('ix_sweep_queue_status'), 'sweep_queue', ['status'], unique=False)

    # Sweep Logs 테이블
    op.create_table('sweep_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sweep_queue_id', sa.Integer(), nullable=True),
        sa.Column('deposit_address_id', sa.Integer(), nullable=False),
        sa.Column('transaction_hash', sa.String(64), nullable=True, comment='트랜잭션 해시'),
        sa.Column('from_address', sa.String(50), nullable=False, comment='송신 주소'),
        sa.Column('to_address', sa.String(50), nullable=False, comment='수신 주소'),
        sa.Column('amount', sa.Numeric(18, 8), nullable=False, comment='Sweep 금액'),
        sa.Column('fee_amount', sa.Numeric(18, 8), nullable=True, comment='수수료'),
        sa.Column('energy_used', sa.Integer(), nullable=True, comment='사용된 에너지'),
        sa.Column('status', sa.String(20), nullable=False, comment='상태'),
        sa.Column('error_code', sa.String(50), nullable=True, comment='오류 코드'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='오류 메시지'),
        sa.Column('block_number', sa.Integer(), nullable=True, comment='블록 번호'),
        sa.Column('confirmation_count', sa.Integer(), nullable=True, default=0, comment='확인 수'),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True, comment='실행 시간(ms)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True, comment='확인 시간'),
        sa.ForeignKeyConstraint(['deposit_address_id'], ['user_deposit_addresses.id'], ),
        sa.ForeignKeyConstraint(['sweep_queue_id'], ['sweep_queue.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sweep_logs_id'), 'sweep_logs', ['id'], unique=False)
    op.create_index(op.f('ix_sweep_logs_transaction_hash'), 'sweep_logs', ['transaction_hash'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_sweep_logs_transaction_hash'), table_name='sweep_logs')
    op.drop_index(op.f('ix_sweep_logs_id'), table_name='sweep_logs')
    op.drop_table('sweep_logs')
    
    op.drop_index(op.f('ix_sweep_queue_status'), table_name='sweep_queue')
    op.drop_index(op.f('ix_sweep_queue_id'), table_name='sweep_queue')
    op.drop_table('sweep_queue')
    
    op.drop_index(op.f('ix_sweep_configurations_id'), table_name='sweep_configurations')
    op.drop_table('sweep_configurations')
    
    op.drop_index(op.f('ix_user_deposit_addresses_address'), table_name='user_deposit_addresses')
    op.drop_index(op.f('ix_user_deposit_addresses_user_id'), table_name='user_deposit_addresses')
    op.drop_index(op.f('ix_user_deposit_addresses_id'), table_name='user_deposit_addresses')
    op.drop_table('user_deposit_addresses')
    
    op.drop_index(op.f('ix_hd_wallet_masters_id'), table_name='hd_wallet_masters')
    op.drop_table('hd_wallet_masters')
