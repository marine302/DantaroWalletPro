"""doc30_001_add_audit_compliance_models

Revision ID: doc30_001
Revises: doc29_001
Create Date: 2025-07-11 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'doc30_001'
down_revision = 'doc29_001'
branch_labels = None
depends_on = None


def upgrade():
    # Create audit_logs table
    op.create_table('audit_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('event_type', sa.Enum('TRANSACTION_CREATED', 'TRANSACTION_COMPLETED', 'TRANSACTION_FAILED', 'WALLET_CREATED', 'WITHDRAWAL_REQUESTED', 'WITHDRAWAL_APPROVED', 'WITHDRAWAL_REJECTED', 'DEPOSIT_DETECTED', 'SUSPICIOUS_ACTIVITY', 'COMPLIANCE_CHECK', 'USER_ACTION', 'ADMIN_ACTION', 'SYSTEM_ACTION', 'PARTNER_ONBOARDING', 'PARTNER_ACTION', name='auditeventtype'), nullable=False),
    sa.Column('event_category', sa.String(length=50), nullable=True),
    sa.Column('severity', sa.String(length=20), nullable=True),
    sa.Column('entity_type', sa.String(length=50), nullable=True),
    sa.Column('entity_id', sa.String(length=100), nullable=True),
    sa.Column('partner_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('event_data', sa.JSON(), nullable=False),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('user_agent', sa.String(length=500), nullable=True),
    sa.Column('previous_hash', sa.String(length=64), nullable=True),
    sa.Column('log_hash', sa.String(length=64), nullable=True),
    sa.Column('blockchain_tx_hash', sa.String(length=64), nullable=True),
    sa.Column('compliance_flags', sa.JSON(), nullable=True),
    sa.Column('risk_score', sa.Integer(), nullable=True),
    sa.Column('requires_review', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_entity', 'audit_logs', ['entity_type', 'entity_id'], unique=False)
    op.create_index('idx_audit_event_type', 'audit_logs', ['event_type'], unique=False)
    op.create_index('idx_audit_partner', 'audit_logs', ['partner_id'], unique=False)
    op.create_index('idx_audit_review', 'audit_logs', ['requires_review'], unique=False)
    op.create_index('idx_audit_severity', 'audit_logs', ['severity'], unique=False)
    op.create_index('idx_audit_timestamp', 'audit_logs', ['timestamp'], unique=False)
    op.create_index('idx_audit_user', 'audit_logs', ['user_id'], unique=False)
    
    # Create compliance_checks table
    op.create_table('compliance_checks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('check_type', sa.Enum('KYC', 'AML', 'SANCTIONS', 'PEP', 'TRANSACTION_LIMIT', 'SUSPICIOUS_PATTERN', name='compliancechecktype'), nullable=False),
    sa.Column('entity_type', sa.String(length=50), nullable=False),
    sa.Column('entity_id', sa.String(length=100), nullable=False),
    sa.Column('status', sa.Enum('PASSED', 'FAILED', 'PENDING', 'MANUAL_REVIEW', 'REJECTED', name='compliancestatus'), nullable=False),
    sa.Column('risk_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='risklevel'), nullable=True),
    sa.Column('score', sa.Integer(), nullable=True),
    sa.Column('check_data', sa.JSON(), nullable=True),
    sa.Column('provider_response', sa.JSON(), nullable=True),
    sa.Column('manual_review_notes', sa.String(length=1000), nullable=True),
    sa.Column('initiated_at', sa.DateTime(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(), nullable=True),
    sa.Column('reviewed_by', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_compliance_entity', 'compliance_checks', ['entity_type', 'entity_id'], unique=False)
    op.create_index('idx_compliance_risk', 'compliance_checks', ['risk_level'], unique=False)
    op.create_index('idx_compliance_status', 'compliance_checks', ['status'], unique=False)
    op.create_index('idx_compliance_type', 'compliance_checks', ['check_type'], unique=False)
    
    # Create suspicious_activities table
    op.create_table('suspicious_activities',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('detection_type', sa.String(length=100), nullable=False),
    sa.Column('severity', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='risklevel'), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('transaction_ids', sa.JSON(), nullable=True),
    sa.Column('pattern_name', sa.String(length=100), nullable=True),
    sa.Column('pattern_data', sa.JSON(), nullable=True),
    sa.Column('ml_model_name', sa.String(length=100), nullable=True),
    sa.Column('ml_model_version', sa.String(length=50), nullable=True),
    sa.Column('confidence_score', sa.Numeric(precision=5, scale=4), nullable=True),
    sa.Column('description', sa.String(length=1000), nullable=True),
    sa.Column('additional_data', sa.JSON(), nullable=True),
    sa.Column('action_taken', sa.String(length=100), nullable=True),
    sa.Column('sar_filed', sa.Boolean(), nullable=True),
    sa.Column('sar_reference', sa.String(length=100), nullable=True),
    sa.Column('detected_at', sa.DateTime(), nullable=False),
    sa.Column('resolved_at', sa.DateTime(), nullable=True),
    sa.Column('resolution_notes', sa.String(length=1000), nullable=True),
    sa.Column('resolved_by', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_suspicious_detected_at', 'suspicious_activities', ['detected_at'], unique=False)
    op.create_index('idx_suspicious_detection', 'suspicious_activities', ['detection_type'], unique=False)
    op.create_index('idx_suspicious_severity', 'suspicious_activities', ['severity'], unique=False)
    op.create_index('idx_suspicious_user', 'suspicious_activities', ['user_id'], unique=False)
    
    # Create audit_reports table
    op.create_table('audit_reports',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('report_type', sa.String(length=50), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('description', sa.String(length=1000), nullable=True),
    sa.Column('period_start', sa.DateTime(), nullable=False),
    sa.Column('period_end', sa.DateTime(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('report_data', sa.JSON(), nullable=True),
    sa.Column('summary', sa.JSON(), nullable=True),
    sa.Column('recommendations', sa.JSON(), nullable=True),
    sa.Column('file_path', sa.String(length=500), nullable=True),
    sa.Column('file_format', sa.String(length=20), nullable=True),
    sa.Column('file_size', sa.Integer(), nullable=True),
    sa.Column('submitted_to', sa.String(length=100), nullable=True),
    sa.Column('submitted_at', sa.DateTime(), nullable=True),
    sa.Column('submission_reference', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('approved_at', sa.DateTime(), nullable=True),
    sa.Column('approved_by', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_report_period', 'audit_reports', ['period_start', 'period_end'], unique=False)
    op.create_index('idx_audit_report_status', 'audit_reports', ['status'], unique=False)
    op.create_index('idx_audit_report_type', 'audit_reports', ['report_type'], unique=False)


def downgrade():
    # Drop indexes first
    op.drop_index('idx_audit_report_type', table_name='audit_reports')
    op.drop_index('idx_audit_report_status', table_name='audit_reports')
    op.drop_index('idx_audit_report_period', table_name='audit_reports')
    op.drop_index('idx_suspicious_user', table_name='suspicious_activities')
    op.drop_index('idx_suspicious_severity', table_name='suspicious_activities')
    op.drop_index('idx_suspicious_detection', table_name='suspicious_activities')
    op.drop_index('idx_suspicious_detected_at', table_name='suspicious_activities')
    op.drop_index('idx_compliance_type', table_name='compliance_checks')
    op.drop_index('idx_compliance_status', table_name='compliance_checks')
    op.drop_index('idx_compliance_risk', table_name='compliance_checks')
    op.drop_index('idx_compliance_entity', table_name='compliance_checks')
    op.drop_index('idx_audit_user', table_name='audit_logs')
    op.drop_index('idx_audit_timestamp', table_name='audit_logs')
    op.drop_index('idx_audit_severity', table_name='audit_logs')
    op.drop_index('idx_audit_review', table_name='audit_logs')
    op.drop_index('idx_audit_partner', table_name='audit_logs')
    op.drop_index('idx_audit_event_type', table_name='audit_logs')
    op.drop_index('idx_audit_entity', table_name='audit_logs')
    
    # Drop tables
    op.drop_table('audit_reports')
    op.drop_table('suspicious_activities')
    op.drop_table('compliance_checks')
    op.drop_table('audit_logs')
