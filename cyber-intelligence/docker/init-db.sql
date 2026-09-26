-- ==============================================================================
-- Cyber-Intelligence Platform - Initial Database Schema (PostgreSQL 16)
-- Domain: Cybercrime Complaints (NCRP/1930 Synthetic) & Transaction Risk
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: users (Analysts, Investigators, Law Enforcement Officers, Admins)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    badge_number VARCHAR(100),
    department VARCHAR(150) DEFAULT 'Cyber Cell / LEA',
    role VARCHAR(50) NOT NULL DEFAULT 'analyst', -- analyst, investigator, supervisor, admin
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table: complaints (Simulated NCRP / 1930 Cyber Fraud Records)
CREATE TABLE IF NOT EXISTS complaints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    acknowledgement_no VARCHAR(100) UNIQUE NOT NULL, -- e.g. NCRP-SYN-2024-XXXXX
    category VARCHAR(100) NOT NULL,                  -- Financial Fraud, Phishing, Loan App, etc.
    subcategory VARCHAR(150),
    victim_state VARCHAR(100) NOT NULL,
    victim_district VARCHAR(100),
    reported_loss_inr NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    suspect_upi VARCHAR(255),
    suspect_account_number VARCHAR(50),
    suspect_ifsc VARCHAR(20),
    suspect_phone VARCHAR(20),
    incident_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    reported_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'NEW',       -- NEW, UNDER_INVESTIGATION, ESCALATED, FROZEN, CLOSED
    triage_priority VARCHAR(20) DEFAULT 'MEDIUM',    -- LOW, MEDIUM, HIGH, CRITICAL
    risk_score NUMERIC(5, 4) DEFAULT 0.0000,         -- 0.0 to 1.0 ML score
    description_synthetic TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table: bank_accounts (Simulated Beneficiary / Mule Accounts)
CREATE TABLE IF NOT EXISTS bank_accounts (
    account_number VARCHAR(50) PRIMARY KEY,
    ifsc_code VARCHAR(20) NOT NULL,
    bank_name VARCHAR(150) NOT NULL,
    branch_name VARCHAR(150),
    holder_synthetic_name VARCHAR(255) NOT NULL,
    phone_linked VARCHAR(20),
    is_frozen BOOLEAN NOT NULL DEFAULT FALSE,
    risk_score NUMERIC(5, 4) DEFAULT 0.0000,
    mule_layer_detected INT DEFAULT 0,               -- 0=clean, 1=primary receiver, 2=layer 2 mule, 3=cashout
    flagged_reasons TEXT[],
    total_credit_volume_inr NUMERIC(18, 2) DEFAULT 0.00,
    total_debit_volume_inr NUMERIC(18, 2) DEFAULT 0.00,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table: transactions (Simulated Indian Financial Rails: UPI, IMPS, NEFT, RTGS)
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    txn_ref_no VARCHAR(100) UNIQUE NOT NULL,         -- UPI RRN or UTR
    sender_account VARCHAR(50),
    receiver_account VARCHAR(50) REFERENCES bank_accounts(account_number),
    sender_upi VARCHAR(255),
    receiver_upi VARCHAR(255),
    amount_inr NUMERIC(15, 2) NOT NULL,
    rail_type VARCHAR(20) NOT NULL,                  -- UPI, IMPS, NEFT, RTGS, AEPS
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    layer_depth INT NOT NULL DEFAULT 1,              -- Flow layer from primary victim
    is_flagged_suspicious BOOLEAN NOT NULL DEFAULT FALSE,
    anomaly_score NUMERIC(5, 4) DEFAULT 0.0000,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table: audit_logs (Strict Chain-of-Custody & Evidence Access Log)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,                    -- VIEW_COMPLAINT, FREEZE_REQUEST, GRAPH_EXPAND, EXPORT_REPORT
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100) NOT NULL,
    details JSONB,
    client_ip VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- High-performance indices for analytical querying & multi-parameter filtering
CREATE INDEX IF NOT EXISTS idx_complaints_ack_no ON complaints(acknowledgement_no);
CREATE INDEX IF NOT EXISTS idx_complaints_suspect_upi ON complaints(suspect_upi);
CREATE INDEX IF NOT EXISTS idx_complaints_suspect_account ON complaints(suspect_account_number);
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_complaints_risk_score ON complaints(risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_bank_accounts_risk ON bank_accounts(risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_txns_receiver ON transactions(receiver_account);
CREATE INDEX IF NOT EXISTS idx_txns_timestamp ON transactions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
