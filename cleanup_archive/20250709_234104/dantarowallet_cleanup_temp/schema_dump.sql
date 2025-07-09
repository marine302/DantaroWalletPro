CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL, 
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
CREATE TABLE users (
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	is_admin BOOLEAN NOT NULL, 
	is_verified BOOLEAN NOT NULL, 
	tron_address VARCHAR(42), 
	id INTEGER NOT NULL, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	PRIMARY KEY (id)
);
CREATE INDEX idx_user_email_active ON users (email, is_active);
CREATE UNIQUE INDEX ix_users_email ON users (email);
CREATE INDEX ix_users_id ON users (id);
CREATE UNIQUE INDEX ix_users_tron_address ON users (tron_address);
CREATE TABLE balances (
	user_id INTEGER NOT NULL, 
	asset VARCHAR(10) NOT NULL, 
	amount NUMERIC(18, 6) NOT NULL, 
	locked_amount NUMERIC(18, 6) NOT NULL, 
	id INTEGER NOT NULL, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT check_positive_amount CHECK (amount >= 0), 
	CONSTRAINT check_locked_not_exceed_amount CHECK (locked_amount <= amount), 
	CONSTRAINT check_positive_locked CHECK (locked_amount >= 0), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	CONSTRAINT uq_user_asset UNIQUE (user_id, asset)
);
CREATE INDEX idx_balance_user_asset ON balances (user_id, asset);
CREATE INDEX ix_balances_id ON balances (id);
CREATE TABLE transactions (
	user_id INTEGER NOT NULL, 
	type VARCHAR(10) NOT NULL, 
	direction VARCHAR(8) NOT NULL, 
	status VARCHAR(10) NOT NULL, 
	asset VARCHAR(10) NOT NULL, 
	amount NUMERIC(18, 6) NOT NULL, 
	fee NUMERIC(18, 6) NOT NULL, 
	related_user_id INTEGER, 
	reference_id VARCHAR(100), 
	tx_hash VARCHAR(100), 
	description TEXT, 
	transaction_metadata TEXT, 
	id INTEGER NOT NULL, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(related_user_id) REFERENCES users (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX idx_tx_reference ON transactions (reference_id);
CREATE INDEX idx_tx_status_type ON transactions (status, type);
CREATE INDEX idx_tx_user_created ON transactions (user_id, created_at);
CREATE INDEX ix_transactions_id ON transactions (id);
CREATE UNIQUE INDEX ix_transactions_reference_id ON transactions (reference_id);
CREATE INDEX ix_transactions_status ON transactions (status);
CREATE INDEX ix_transactions_tx_hash ON transactions (tx_hash);
CREATE INDEX ix_transactions_type ON transactions (type);
CREATE INDEX ix_transactions_user_id ON transactions (user_id);
CREATE TABLE wallets (
	user_id INTEGER NOT NULL, 
	address VARCHAR(42) NOT NULL, 
	hex_address VARCHAR(42) NOT NULL, 
	encrypted_private_key TEXT NOT NULL, 
	encryption_salt VARCHAR(32) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	is_monitored BOOLEAN NOT NULL, 
	wallet_metadata TEXT, 
	id INTEGER NOT NULL, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (hex_address), 
	UNIQUE (user_id)
);
CREATE INDEX idx_wallet_address_active ON wallets (address, is_active);
CREATE INDEX idx_wallet_user_active ON wallets (user_id, is_active);
CREATE UNIQUE INDEX ix_wallets_address ON wallets (address);
CREATE INDEX ix_wallets_id ON wallets (id);
CREATE TABLE deposits (
	tx_hash VARCHAR(64) NOT NULL, 
	from_address VARCHAR(42) NOT NULL, 
	to_address VARCHAR(42) NOT NULL, 
	amount NUMERIC(28, 8) NOT NULL, 
	token_symbol VARCHAR(10) NOT NULL, 
	token_contract VARCHAR(42), 
	block_number INTEGER NOT NULL, 
	block_timestamp INTEGER NOT NULL, 
	transaction_index INTEGER NOT NULL, 
	confirmations INTEGER NOT NULL, 
	is_confirmed BOOLEAN NOT NULL, 
	min_confirmations INTEGER NOT NULL, 
	is_processed BOOLEAN NOT NULL, 
	processed_at VARCHAR, 
	user_id INTEGER NOT NULL, 
	wallet_id INTEGER NOT NULL, 
	error_message VARCHAR, 
	retry_count INTEGER NOT NULL, 
	max_retries INTEGER NOT NULL, 
	id INTEGER NOT NULL, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, status VARCHAR(20) DEFAULT "pending", 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(wallet_id) REFERENCES wallets (id)
);
CREATE INDEX idx_deposit_block ON deposits (block_number, transaction_index);
CREATE INDEX idx_deposit_status ON deposits (is_confirmed, is_processed);
CREATE INDEX idx_deposit_user_token ON deposits (user_id, token_symbol);
CREATE INDEX ix_deposits_block_number ON deposits (block_number);
CREATE INDEX ix_deposits_from_address ON deposits (from_address);
CREATE INDEX ix_deposits_id ON deposits (id);
CREATE INDEX ix_deposits_to_address ON deposits (to_address);
CREATE UNIQUE INDEX ix_deposits_tx_hash ON deposits (tx_hash);
CREATE INDEX ix_deposits_user_id ON deposits (user_id);
CREATE INDEX ix_deposits_wallet_id ON deposits (wallet_id);
CREATE TABLE withdrawals (
	user_id INTEGER NOT NULL, 
	to_address VARCHAR(42) NOT NULL, 
	amount NUMERIC(28, 8) NOT NULL, 
	fee NUMERIC(28, 8) NOT NULL, 
	net_amount NUMERIC(28, 8) NOT NULL, 
	asset VARCHAR(10) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	priority VARCHAR(10) NOT NULL, 
	requested_at DATETIME, 
	reviewed_at DATETIME, 
	approved_at DATETIME, 
	processed_at DATETIME, 
	completed_at DATETIME, 
	reviewed_by INTEGER, 
	approved_by INTEGER, 
	processed_by INTEGER, 
	tx_hash VARCHAR(100), 
	tx_fee NUMERIC(28, 8), 
	notes TEXT, 
	admin_notes TEXT, 
	rejection_reason TEXT, 
	error_message TEXT, 
	ip_address VARCHAR(45), 
	user_agent VARCHAR(200), 
	id INTEGER NOT NULL, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(approved_by) REFERENCES users (id), 
	FOREIGN KEY(processed_by) REFERENCES users (id), 
	FOREIGN KEY(reviewed_by) REFERENCES users (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX idx_withdrawal_requested_at ON withdrawals (requested_at);
CREATE INDEX idx_withdrawal_status_priority ON withdrawals (status, priority);
CREATE INDEX idx_withdrawal_user_status ON withdrawals (user_id, status);
CREATE INDEX ix_withdrawals_id ON withdrawals (id);
CREATE INDEX ix_withdrawals_status ON withdrawals (status);
CREATE INDEX ix_withdrawals_to_address ON withdrawals (to_address);
CREATE UNIQUE INDEX ix_withdrawals_tx_hash ON withdrawals (tx_hash);
CREATE INDEX ix_withdrawals_user_id ON withdrawals (user_id);
CREATE TABLE transactionsummarys (
	user_id INTEGER NOT NULL, 
	period_type VARCHAR(20) NOT NULL, 
	period_start DATETIME NOT NULL, 
	period_end DATETIME NOT NULL, 
	trx_deposits_count INTEGER NOT NULL, 
	trx_deposits_amount NUMERIC(18, 6) NOT NULL, 
	trx_withdrawals_count INTEGER NOT NULL, 
	trx_withdrawals_amount NUMERIC(18, 6) NOT NULL, 
	usdt_deposits_count INTEGER NOT NULL, 
	usdt_deposits_amount NUMERIC(18, 6) NOT NULL, 
	usdt_withdrawals_count INTEGER NOT NULL, 
	usdt_withdrawals_amount NUMERIC(18, 6) NOT NULL, 
	total_transactions INTEGER NOT NULL, 
	total_volume_usd NUMERIC(18, 6) NOT NULL, 
	total_fees_trx NUMERIC(18, 6) NOT NULL, 
	total_fees_usdt NUMERIC(18, 6) NOT NULL, 
	id INTEGER NOT NULL, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX idx_summary_period_type ON transactionsummarys (period_type, period_start);
CREATE INDEX idx_summary_user_period ON transactionsummarys (user_id, period_type, period_start);
CREATE INDEX ix_transactionsummarys_id ON transactionsummarys (id);
CREATE INDEX ix_transactionsummarys_period_end ON transactionsummarys (period_end);
CREATE INDEX ix_transactionsummarys_period_start ON transactionsummarys (period_start);
CREATE INDEX ix_transactionsummarys_user_id ON transactionsummarys (user_id);
CREATE TABLE transactionalerts (
	user_id INTEGER NOT NULL, 
	transaction_id INTEGER, 
	alert_type VARCHAR(50) NOT NULL, 
	level VARCHAR(20) NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	description TEXT NOT NULL, 
	is_resolved BOOLEAN NOT NULL, 
	resolved_by INTEGER, 
	resolved_at DATETIME, 
	resolution_notes TEXT, 
	alert_data TEXT, 
	id INTEGER NOT NULL, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(resolved_by) REFERENCES users (id), 
	FOREIGN KEY(transaction_id) REFERENCES transactions (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX idx_alert_level_resolved ON transactionalerts (level, is_resolved);
CREATE INDEX idx_alert_type_created ON transactionalerts (alert_type, created_at);
CREATE INDEX idx_alert_user_created ON transactionalerts (user_id, created_at);
CREATE INDEX ix_transactionalerts_alert_type ON transactionalerts (alert_type);
CREATE INDEX ix_transactionalerts_id ON transactionalerts (id);
CREATE INDEX ix_transactionalerts_is_resolved ON transactionalerts (is_resolved);
CREATE INDEX ix_transactionalerts_level ON transactionalerts (level);
CREATE INDEX ix_transactionalerts_transaction_id ON transactionalerts (transaction_id);
CREATE INDEX ix_transactionalerts_user_id ON transactionalerts (user_id);
CREATE TABLE energy_pools (
	id INTEGER NOT NULL, 
	pool_name VARCHAR(100) NOT NULL, 
	wallet_address VARCHAR(50) NOT NULL, 
	total_frozen_trx NUMERIC(18, 6) NOT NULL, 
	frozen_for_energy NUMERIC(18, 6) NOT NULL, 
	frozen_for_bandwidth NUMERIC(18, 6) NOT NULL, 
	available_energy BIGINT NOT NULL, 
	available_bandwidth BIGINT NOT NULL, 
	daily_energy_consumption BIGINT NOT NULL, 
	daily_bandwidth_consumption BIGINT NOT NULL, 
	auto_refreeze_enabled BOOLEAN, 
	energy_threshold BIGINT NOT NULL, 
	bandwidth_threshold BIGINT NOT NULL, 
	last_freeze_cost NUMERIC(18, 6), 
	total_freeze_cost NUMERIC(18, 6) NOT NULL, 
	is_active BOOLEAN, 
	last_updated DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	notes TEXT, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, owner_address VARCHAR(34), frozen_trx NUMERIC(20,6) DEFAULT 0, total_energy INTEGER DEFAULT 0, used_energy INTEGER DEFAULT 0, status VARCHAR(20) DEFAULT "active", low_threshold INTEGER DEFAULT 20, critical_threshold INTEGER DEFAULT 10, auto_refill BOOLEAN DEFAULT 0, auto_refill_amount NUMERIC(20,6) DEFAULT 10000, auto_refill_trigger INTEGER DEFAULT 15, daily_consumption TEXT, peak_usage_hours TEXT, last_refilled_at DATETIME, last_checked_at DATETIME, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_energy_pools_id ON energy_pools (id);
CREATE TABLE energy_price_history (
	id INTEGER NOT NULL, 
	trx_price_usd NUMERIC(18, 8) NOT NULL, 
	energy_per_trx BIGINT NOT NULL, 
	bandwidth_per_trx BIGINT NOT NULL, 
	total_frozen_trx NUMERIC(18, 6), 
	energy_utilization NUMERIC(5, 2), 
	usdt_transfer_cost NUMERIC(18, 6), 
	trx_transfer_cost NUMERIC(18, 6), 
	recorded_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	source VARCHAR(50), 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_energy_price_history_id ON energy_price_history (id);
CREATE TABLE energy_usage_logs (
	id INTEGER NOT NULL, 
	energy_pool_id INTEGER NOT NULL, 
	transaction_hash VARCHAR(64), 
	transaction_type VARCHAR(50) NOT NULL, 
	energy_consumed BIGINT NOT NULL, 
	bandwidth_consumed BIGINT NOT NULL, 
	trx_cost_equivalent NUMERIC(18, 6), 
	user_id INTEGER, 
	from_address VARCHAR(50), 
	to_address VARCHAR(50), 
	amount NUMERIC(18, 6), 
	asset VARCHAR(20), 
	block_number BIGINT, 
	timestamp DATETIME NOT NULL, 
	notes TEXT, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_energy_usage_logs_id ON energy_usage_logs (id);
CREATE TABLE partners (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(100),
    domain VARCHAR(255) UNIQUE,
    contact_email VARCHAR(255) NOT NULL UNIQUE,
    contact_phone VARCHAR(50),
    business_type VARCHAR(50) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    api_secret_hash VARCHAR(255) NOT NULL,
    previous_api_key VARCHAR(255),
    api_key_created_at DATETIME,
    status VARCHAR(20) DEFAULT 'pending',
    onboarding_status VARCHAR(50) DEFAULT 'pending',
    subscription_plan VARCHAR(50) DEFAULT 'basic',
    monthly_limit DECIMAL(18,8),
    commission_rate DECIMAL(5,4) DEFAULT 0,
    energy_balance DECIMAL(18,8) DEFAULT 0,
    settings JSON DEFAULT '{}',
    deployment_config JSON DEFAULT '{}',
    last_activity_at DATETIME,
    activated_at DATETIME,
    suspended_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE energy_usage_history (
	id VARCHAR(36) NOT NULL, 
	partner_id VARCHAR(36) NOT NULL, 
	transaction_type VARCHAR(50) NOT NULL, 
	energy_amount INTEGER NOT NULL, 
	transaction_id VARCHAR(100), 
	description VARCHAR(255), 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(partner_id) REFERENCES partners (id)
);
CREATE TABLE system_transaction_alerts (
	title VARCHAR(200) NOT NULL, 
	message TEXT NOT NULL, 
	alert_type VARCHAR(50) NOT NULL, 
	level VARCHAR(20) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	is_resolved BOOLEAN NOT NULL, 
	resolved_by INTEGER, 
	resolved_at DATETIME, 
	alert_data TEXT, 
	id INTEGER NOT NULL, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(resolved_by) REFERENCES users (id)
);
CREATE TABLE partner_wallets (
	id VARCHAR(36) NOT NULL, 
	partner_id VARCHAR(36) NOT NULL, 
	wallet_type VARCHAR(12) NOT NULL, 
	address VARCHAR(42) NOT NULL, 
	label VARCHAR(100), 
	is_active BOOLEAN NOT NULL, 
	is_primary BOOLEAN NOT NULL, 
	balance_usdt NUMERIC(20, 6) NOT NULL, 
	balance_trx NUMERIC(20, 6) NOT NULL, 
	last_sync_at DATETIME, 
	metadata JSON, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_partner_wallets_partner_id FOREIGN KEY(partner_id) REFERENCES partners (id), 
	CONSTRAINT uq_partner_wallet_address UNIQUE (partner_id, address)
);
CREATE INDEX ix_partner_wallets_id ON partner_wallets (id);
CREATE INDEX ix_partner_wallets_partner_id ON partner_wallets (partner_id);
CREATE INDEX ix_partner_wallets_address ON partner_wallets (address);
CREATE INDEX ix_partner_wallets_wallet_type ON partner_wallets (wallet_type);
CREATE TABLE partner_energy_pools (
	id INTEGER NOT NULL, 
	partner_id INTEGER NOT NULL, 
	wallet_address VARCHAR(42) NOT NULL, 
	total_energy NUMERIC(20, 0), 
	available_energy NUMERIC(20, 0), 
	used_energy NUMERIC(20, 0), 
	energy_limit NUMERIC(20, 0), 
	total_bandwidth NUMERIC(20, 0), 
	available_bandwidth NUMERIC(20, 0), 
	frozen_trx_amount NUMERIC(18, 6), 
	frozen_for_energy NUMERIC(18, 6), 
	frozen_for_bandwidth NUMERIC(18, 6), 
	status VARCHAR(20), 
	depletion_estimated_at DATETIME, 
	daily_average_usage NUMERIC(20, 0), 
	peak_usage_hour INTEGER, 
	warning_threshold INTEGER, 
	critical_threshold INTEGER, 
	auto_response_enabled BOOLEAN, 
	last_checked_at DATETIME, 
	last_alert_sent_at DATETIME, 
	metrics_history JSON, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (partner_id)
);
CREATE INDEX idx_partner_energy_pools_status ON partner_energy_pools (status);
CREATE INDEX idx_partner_energy_pools_partner ON partner_energy_pools (partner_id);
CREATE TABLE energy_alerts (
	id INTEGER NOT NULL, 
	energy_pool_id INTEGER NOT NULL, 
	alert_type VARCHAR(50) NOT NULL, 
	severity VARCHAR(20) NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	message TEXT NOT NULL, 
	threshold_value NUMERIC(10, 2), 
	current_value NUMERIC(10, 2), 
	estimated_hours_remaining INTEGER, 
	sent_via JSON, 
	sent_to JSON, 
	sent_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	acknowledged BOOLEAN, 
	acknowledged_at DATETIME, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	PRIMARY KEY (id), 
	FOREIGN KEY(energy_pool_id) REFERENCES partner_energy_pools (id)
);
CREATE INDEX idx_energy_alerts_type ON energy_alerts (alert_type);
CREATE INDEX idx_energy_alerts_pool ON energy_alerts (energy_pool_id);
CREATE INDEX idx_energy_alerts_severity ON energy_alerts (severity);
CREATE TABLE partner_energy_usage_logs (
	id INTEGER NOT NULL, 
	energy_pool_id INTEGER NOT NULL, 
	transaction_type VARCHAR(50) NOT NULL, 
	transaction_hash VARCHAR(66), 
	energy_consumed NUMERIC(20, 0) NOT NULL, 
	bandwidth_consumed NUMERIC(20, 0), 
	energy_unit_price NUMERIC(10, 6), 
	total_cost NUMERIC(18, 6), 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	PRIMARY KEY (id), 
	FOREIGN KEY(energy_pool_id) REFERENCES partner_energy_pools (id)
);
CREATE INDEX idx_partner_energy_usage_logs_pool ON partner_energy_usage_logs (energy_pool_id);
CREATE INDEX idx_partner_energy_usage_logs_hash ON partner_energy_usage_logs (transaction_hash);
CREATE INDEX idx_partner_energy_usage_logs_type ON partner_energy_usage_logs (transaction_type);
CREATE TABLE energy_predictions (
	id INTEGER NOT NULL, 
	energy_pool_id INTEGER NOT NULL, 
	prediction_date DATETIME NOT NULL, 
	predicted_usage NUMERIC(20, 0) NOT NULL, 
	predicted_depletion DATETIME, 
	confidence_score NUMERIC(5, 2), 
	historical_pattern JSON, 
	trend_factors JSON, 
	seasonal_adjustments JSON, 
	recommended_action VARCHAR(100), 
	action_priority VARCHAR(20), 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	PRIMARY KEY (id), 
	FOREIGN KEY(energy_pool_id) REFERENCES partner_energy_pools (id)
);
CREATE INDEX idx_energy_predictions_pool ON energy_predictions (energy_pool_id);
CREATE INDEX idx_energy_predictions_date ON energy_predictions (prediction_date);
CREATE TABLE partner_fee_policies (
	id INTEGER NOT NULL, 
	partner_id VARCHAR(36) NOT NULL, 
	fee_type VARCHAR(10), 
	base_fee_rate NUMERIC(5, 4), 
	min_fee_amount NUMERIC(18, 6), 
	max_fee_amount NUMERIC(18, 6), 
	withdrawal_fee_rate NUMERIC(5, 4), 
	internal_transfer_fee_rate NUMERIC(5, 4), 
	vip_discount_rates JSON, 
	promotion_active BOOLEAN, 
	promotion_fee_rate NUMERIC(5, 4), 
	promotion_end_date DATETIME, 
	platform_share_rate NUMERIC(5, 4), 
	created_at DATETIME DEFAULT (now()), 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(partner_id) REFERENCES partners (id)
);
CREATE INDEX ix_partner_fee_policies_id ON partner_fee_policies (id);
CREATE UNIQUE INDEX ix_partner_fee_policies_partner_id ON partner_fee_policies (partner_id);
CREATE TABLE fee_tiers (
	id INTEGER NOT NULL, 
	fee_policy_id INTEGER NOT NULL, 
	min_amount NUMERIC(18, 6) NOT NULL, 
	max_amount NUMERIC(18, 6), 
	fee_rate NUMERIC(5, 4) NOT NULL, 
	fixed_fee NUMERIC(18, 6), 
	created_at DATETIME DEFAULT (now()), 
	PRIMARY KEY (id), 
	FOREIGN KEY(fee_policy_id) REFERENCES partner_fee_policies (id)
);
CREATE INDEX ix_fee_tiers_id ON fee_tiers (id);
CREATE INDEX ix_fee_tiers_policy_amount ON fee_tiers (fee_policy_id, min_amount);
CREATE TABLE partner_withdrawal_policies (
	id INTEGER NOT NULL, 
	partner_id VARCHAR(36) NOT NULL, 
	policy_type VARCHAR(8), 
	realtime_enabled BOOLEAN, 
	realtime_max_amount NUMERIC(18, 6), 
	auto_approve_enabled BOOLEAN, 
	auto_approve_max_amount NUMERIC(18, 6), 
	batch_enabled BOOLEAN, 
	batch_schedule JSON, 
	batch_min_amount NUMERIC(18, 6), 
	daily_limit_per_user NUMERIC(18, 6), 
	daily_limit_total NUMERIC(18, 6), 
	single_transaction_limit NUMERIC(18, 6), 
	whitelist_required BOOLEAN, 
	whitelist_addresses JSON, 
	require_2fa BOOLEAN, 
	confirmation_blocks INTEGER, 
	created_at DATETIME DEFAULT (now()), 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(partner_id) REFERENCES partners (id)
);
CREATE INDEX ix_partner_withdrawal_policies_id ON partner_withdrawal_policies (id);
CREATE UNIQUE INDEX ix_partner_withdrawal_policies_partner_id ON partner_withdrawal_policies (partner_id);
CREATE TABLE partner_energy_policies (
	id INTEGER NOT NULL, 
	partner_id VARCHAR(36) NOT NULL, 
	default_policy VARCHAR(14), 
	trx_payment_enabled BOOLEAN, 
	trx_payment_markup NUMERIC(5, 4), 
	trx_payment_max_fee NUMERIC(18, 6), 
	queue_enabled BOOLEAN, 
	queue_max_wait_hours INTEGER, 
	queue_notification_enabled BOOLEAN, 
	priority_queue_enabled BOOLEAN, 
	vip_priority_levels JSON, 
	energy_saving_enabled BOOLEAN, 
	energy_saving_threshold INTEGER, 
	created_at DATETIME DEFAULT (now()), 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(partner_id) REFERENCES partners (id)
);
CREATE INDEX ix_partner_energy_policies_id ON partner_energy_policies (id);
CREATE UNIQUE INDEX ix_partner_energy_policies_partner_id ON partner_energy_policies (partner_id);
CREATE TABLE user_tiers (
	id INTEGER NOT NULL, 
	partner_id VARCHAR(36) NOT NULL, 
	tier_name VARCHAR(50) NOT NULL, 
	tier_level INTEGER NOT NULL, 
	min_volume NUMERIC(18, 6), 
	fee_discount_rate NUMERIC(5, 4), 
	withdrawal_limit_multiplier NUMERIC(5, 2), 
	benefits JSON, 
	upgrade_conditions JSON, 
	created_at DATETIME DEFAULT (now()), 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(partner_id) REFERENCES partners (id)
);
CREATE INDEX ix_user_tiers_id ON user_tiers (id);
CREATE INDEX ix_user_tiers_partner_level ON user_tiers (partner_id, tier_level);
CREATE TABLE fee_calculation_logs (
	id INTEGER NOT NULL, 
	partner_id VARCHAR(36) NOT NULL, 
	transaction_id VARCHAR(100), 
	transaction_amount NUMERIC(18, 6) NOT NULL, 
	base_fee_rate NUMERIC(5, 4), 
	applied_fee_rate NUMERIC(5, 4), 
	discount_rate NUMERIC(5, 4), 
	calculated_fee NUMERIC(18, 6), 
	platform_share NUMERIC(18, 6), 
	partner_share NUMERIC(18, 6), 
	policy_details JSON, 
	created_at DATETIME DEFAULT (now()), 
	PRIMARY KEY (id), 
	FOREIGN KEY(partner_id) REFERENCES partners (id)
);
CREATE INDEX ix_fee_calculation_logs_id ON fee_calculation_logs (id);
CREATE INDEX ix_fee_calculation_logs_partner_date ON fee_calculation_logs (partner_id, created_at);
CREATE INDEX ix_fee_calculation_logs_transaction ON fee_calculation_logs (transaction_id);
CREATE TABLE partner_policy_calculation_logs (
    id INTEGER PRIMARY KEY,
    partner_id VARCHAR(36) NOT NULL,
    user_id INTEGER,
    calculation_type VARCHAR(50) NOT NULL,
    request_data TEXT,
    result_data TEXT,
    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    admin_id INTEGER,
    FOREIGN KEY (partner_id) REFERENCES partners (id)
);
CREATE INDEX ix_partner_policy_calculation_logs_id ON partner_policy_calculation_logs (id);
CREATE INDEX ix_partner_policy_calculation_logs_partner_date ON partner_policy_calculation_logs (partner_id, calculated_at);
CREATE INDEX ix_partner_policy_calculation_logs_type ON partner_policy_calculation_logs (calculation_type);
