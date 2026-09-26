// ==============================================================================
// Cyber-Intelligence Platform - Initial Neo4j Graph Schema & Constraints
// Domain: Financial Mule Networks, Link Analysis & Shared Identifiers
// ==============================================================================

// Uniqueness Constraints for Core Intelligence Entities
CREATE CONSTRAINT c_bank_account_num IF NOT EXISTS
FOR (a:BankAccount) REQUIRE a.account_number IS UNIQUE;

CREATE CONSTRAINT c_upi_id_vpa IF NOT EXISTS
FOR (u:UPI_ID) REQUIRE u.vpa IS UNIQUE;

CREATE CONSTRAINT c_phone_number IF NOT EXISTS
FOR (p:Phone) REQUIRE p.phone_number IS UNIQUE;

CREATE CONSTRAINT c_device_fingerprint IF NOT EXISTS
FOR (d:Device) REQUIRE d.device_id IS UNIQUE;

CREATE CONSTRAINT c_complaint_ack IF NOT EXISTS
FOR (c:Complaint) REQUIRE c.acknowledgement_no IS UNIQUE;

CREATE CONSTRAINT c_mule_ring_id IF NOT EXISTS
FOR (r:MuleRing) REQUIRE r.ring_id IS UNIQUE;

// Performance Indexes for Pattern Matching & Link Analytics
CREATE INDEX idx_account_risk IF NOT EXISTS
FOR (a:BankAccount) ON (a.risk_score);

CREATE INDEX idx_txn_timestamp IF NOT EXISTS
FOR ()-[t:TRANSFERRED_TO]-() ON (t.timestamp);

CREATE INDEX idx_phone_location IF NOT EXISTS
FOR (p:Phone) ON (p.state, p.district);
