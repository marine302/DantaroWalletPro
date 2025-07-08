"""Add Sweep automation models (Doc-27) - simplified

Revision ID: doc27_001_sweep_automation
Revises: doc26_001_partner_fee_policies
Create Date: 2025-07-08 12:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'doc27_001_sweep_automation'
down_revision: Union[str, None] = 'doc26_001_partner_fee_policies'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade: Add Sweep automation tables"""
    
    # HD Wallet Masters table
    op.create_table('hd_wallet_masters',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('partner_id', sa.Integer(), nullable=False),
        sa.Column('encrypted_seed', sa.String(500), nullable=False, comment='암호화된 마스터 시드'),
        sa.Column('public_key', sa.String(130), nullable=False, comment='마스터 공개키'),
        sa.Column('derivation_path', sa.String(100), default="m/44'/195'/0'/0", comment='TRON 파생 경로'),
        sa.Column('last_index', sa.Integer(), default=0, comment='마지막 사용 인덱스'),
        sa.Column('encryption_method', sa.String(50), default="AES-256-GCM", comment='암호화 방식'),
        sa.Column('key_version', sa.Integer(), default=1, comment='키 버전'),
        sa.Column('total_addresses_generated', sa.Integer(), default=0, comment='생성된 총 주소 수'),
        sa.Column('total_sweep_amount', sa.Numeric(18, 6), default=0, comment='총 Sweep 금액'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id']),
        sa.UniqueConstraint('partner_id')
    )
    op.create_index('ix_hd_wallet_masters_id', 'hd_wallet_masters', ['id'])
    
    # User Deposit Addresses table
    op.create_table('user_deposit_addresses',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('hd_wallet_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('address', sa.String(42), nullable=False, comment='TRON 입금 주소'),
        sa.Column('derivation_index', sa.Integer(), nullable=False, comment='HD Wallet 파생 인덱스'),
        sa.Column('encrypted_private_key', sa.String(500), nullable=False, comment='암호화된 개인키'),
        sa.Column('is_active', sa.Boolean(), default=True, comment='활성 상태'),
        sa.Column('is_monitored', sa.Boolean(), default=True, comment='모니터링 활성화'),
        sa.Column('total_received', sa.Numeric(18, 6), default=0, comment='총 입금액 (USDT)'),
        sa.Column('total_swept', sa.Numeric(18, 6), default=0, comment='총 Sweep 금액'),
        sa.Column('last_deposit_at', sa.DateTime(timezone=True), comment='마지막 입금 시간'),
        sa.Column('last_sweep_at', sa.DateTime(timezone=True), comment='마지막 Sweep 시간'),
        sa.Column('min_sweep_amount', sa.Numeric(18, 6), comment='최소 Sweep 금액 (개별 설정)'),
        sa.Column('priority_level', sa.Integer(), default=1, comment='우선순위 (1-10)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['hd_wallet_id'], ['hd_wallet_masters.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.UniqueConstraint('address')
    )
    op.create_index('ix_user_deposit_addresses_id', 'user_deposit_addresses', ['id'])
    op.create_index('ix_user_deposit_addresses_address', 'user_deposit_addresses', ['address'])
    op.create_index('idx_deposit_address_user', 'user_deposit_addresses', ['user_id'])
    op.create_index('idx_deposit_address_active', 'user_deposit_addresses', ['is_active'])
    op.create_index('idx_deposit_address_monitored', 'user_deposit_addresses', ['is_monitored'])
    
    # Sweep Configurations table
    op.create_table('sweep_configurations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('partner_id', sa.Integer(), nullable=False),
        sa.Column('destination_wallet_id', sa.Integer(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), default=True, comment='Sweep 활성화'),
        sa.Column('auto_sweep_enabled', sa.Boolean(), default=True, comment='자동 Sweep 활성화'),
        sa.Column('min_sweep_amount', sa.Numeric(18, 6), default=10, comment='최소 Sweep 금액 (USDT)'),
        sa.Column('max_sweep_amount', sa.Numeric(18, 6), comment='최대 Sweep 금액 (제한없으면 NULL)'),
        sa.Column('sweep_interval_minutes', sa.Integer(), default=60, comment='Sweep 간격 (분)'),
        sa.Column('immediate_threshold', sa.Numeric(18, 6), default=1000, comment='즉시 Sweep 임계값'),
        sa.Column('daily_sweep_time', sa.String(5), comment='일일 Sweep 시간 (HH:MM)'),
        sa.Column('max_gas_price_sun', sa.Numeric(20, 0), default=1000, comment='최대 가스비 (SUN)'),
        sa.Column('gas_optimization_enabled', sa.Boolean(), default=True, comment='가스비 최적화'),
        sa.Column('gas_price_multiplier', sa.Numeric(3, 2), default=1.1, comment='가스비 승수'),
        sa.Column('batch_enabled', sa.Boolean(), default=True, comment='배치 처리 활성화'),
        sa.Column('max_batch_size', sa.Integer(), default=20, comment='최대 배치 크기'),
        sa.Column('batch_delay_seconds', sa.Integer(), default=5, comment='배치 처리 간 지연 시간'),
        sa.Column('daily_sweep_limit', sa.Numeric(18, 6), comment='일일 Sweep 한도'),
        sa.Column('monthly_sweep_limit', sa.Numeric(18, 6), comment='월간 Sweep 한도'),
        sa.Column('consecutive_failure_limit', sa.Integer(), default=3, comment='연속 실패 제한'),
        sa.Column('notification_enabled', sa.Boolean(), default=True, comment='알림 활성화'),
        sa.Column('notification_channels', sa.JSON(), comment='알림 채널 설정'),
        sa.Column('success_notification', sa.Boolean(), default=False, comment='성공 알림'),
        sa.Column('failure_notification', sa.Boolean(), default=True, comment='실패 알림'),
        sa.Column('last_sweep_at', sa.DateTime(timezone=True), comment='마지막 Sweep 실행 시간'),
        sa.Column('total_sweeps', sa.Integer(), default=0, comment='총 Sweep 횟수'),
        sa.Column('total_sweep_amount', sa.Numeric(18, 6), default=0, comment='총 Sweep 금액'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['partner_id'], ['partners.id']),
        sa.ForeignKeyConstraint(['destination_wallet_id'], ['partner_wallets.id']),
        sa.UniqueConstraint('partner_id')
    )
    op.create_index('ix_sweep_configurations_id', 'sweep_configurations', ['id'])
    
    # Sweep Logs table
    op.create_table('sweep_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('configuration_id', sa.Integer(), nullable=False),
        sa.Column('deposit_address_id', sa.Integer(), nullable=False),
        sa.Column('sweep_type', sa.String(20), default='auto', comment='Sweep 유형 (auto/manual/emergency)'),
        sa.Column('sweep_amount', sa.Numeric(18, 6), nullable=False, comment='Sweep 금액 (USDT)'),
        sa.Column('balance_before', sa.Numeric(18, 6), comment='Sweep 전 잔액'),
        sa.Column('balance_after', sa.Numeric(18, 6), comment='Sweep 후 잔액'),
        sa.Column('tx_hash', sa.String(66), comment='트랜잭션 해시'),
        sa.Column('from_address', sa.String(42), nullable=False, comment='출금 주소'),
        sa.Column('to_address', sa.String(42), nullable=False, comment='입금 주소'),
        sa.Column('gas_limit', sa.Numeric(20, 0), comment='가스 한도'),
        sa.Column('gas_used', sa.Numeric(20, 0), comment='사용된 가스'),
        sa.Column('gas_price', sa.Numeric(20, 0), comment='가스 가격 (SUN)'),
        sa.Column('gas_fee_trx', sa.Numeric(18, 6), comment='가스비 (TRX)'),
        sa.Column('status', sa.String(20), default='pending', comment='상태 (pending/confirmed/failed)'),
        sa.Column('error_message', sa.String(1000), comment='에러 메시지'),
        sa.Column('error_code', sa.String(50), comment='에러 코드'),
        sa.Column('retry_count', sa.Integer(), default=0, comment='재시도 횟수'),
        sa.Column('max_retries', sa.Integer(), default=3, comment='최대 재시도 횟수'),
        sa.Column('batch_id', sa.String(36), comment='배치 ID'),
        sa.Column('priority', sa.Integer(), default=1, comment='우선순위'),
        sa.Column('notes', sa.String(500), comment='메모'),
        sa.Column('initiated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), comment='확인 시간'),
        sa.Column('failed_at', sa.DateTime(timezone=True), comment='실패 시간'),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), comment='다음 재시도 시간'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['configuration_id'], ['sweep_configurations.id']),
        sa.ForeignKeyConstraint(['deposit_address_id'], ['user_deposit_addresses.id'])
    )
    op.create_index('ix_sweep_logs_id', 'sweep_logs', ['id'])
    op.create_index('ix_sweep_logs_tx_hash', 'sweep_logs', ['tx_hash'])
    op.create_index('idx_sweep_log_status', 'sweep_logs', ['status'])
    op.create_index('idx_sweep_log_batch', 'sweep_logs', ['batch_id'])
    op.create_index('idx_sweep_log_retry', 'sweep_logs', ['status', 'next_retry_at'])
    op.create_index('idx_sweep_log_date', 'sweep_logs', ['initiated_at'])
    
    # Sweep Queues table
    op.create_table('sweep_queues',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('deposit_address_id', sa.Integer(), nullable=False),
        sa.Column('queue_type', sa.String(20), default='normal', comment='큐 유형 (normal/priority/emergency)'),
        sa.Column('priority', sa.Integer(), default=1, comment='우선순위 (1-10, 높을수록 우선)'),
        sa.Column('expected_amount', sa.Numeric(18, 6), comment='예상 Sweep 금액'),
        sa.Column('status', sa.String(20), default='queued', comment='상태 (queued/processing/completed/failed)'),
        sa.Column('attempts', sa.Integer(), default=0, comment='처리 시도 횟수'),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), comment='예약 실행 시간'),
        sa.Column('expires_at', sa.DateTime(timezone=True), comment='만료 시간'),
        sa.Column('reason', sa.String(200), comment='큐 등록 사유'),
        sa.Column('queue_metadata', sa.JSON(), comment='추가 메타데이터'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['deposit_address_id'], ['user_deposit_addresses.id'])
    )
    op.create_index('ix_sweep_queues_id', 'sweep_queues', ['id'])
    op.create_index('idx_sweep_queue_status', 'sweep_queues', ['status'])
    op.create_index('idx_sweep_queue_priority', 'sweep_queues', ['priority', 'scheduled_at'])
    op.create_index('idx_sweep_queue_type', 'sweep_queues', ['queue_type'])


def downgrade() -> None:
    """Downgrade: Remove Sweep automation tables"""
    op.drop_table('sweep_queues')
    op.drop_table('sweep_logs')
    op.drop_table('sweep_configurations')
    op.drop_table('user_deposit_addresses')
    op.drop_table('hd_wallet_masters')
