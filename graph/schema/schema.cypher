// ==============================================================================
// Neo4j Aura-Compatible Cypher Schema: Constraints & Indexes
// Cybercrime Intelligence & Financial Transaction Risk Detection Platform
// ==============================================================================

// 1. UNIQUE NODE CONSTRAINTS (Neo4j 5.x / Aura Syntax)
CREATE CONSTRAINT customer_id_unique IF NOT EXISTS FOR (c:Customer) REQUIRE c.customer_id IS UNIQUE;
CREATE CONSTRAINT account_number_unique IF NOT EXISTS FOR (a:Account) REQUIRE a.account_number IS UNIQUE;
CREATE CONSTRAINT transaction_id_unique IF NOT EXISTS FOR (t:Transaction) REQUIRE t.transaction_id IS UNIQUE;
CREATE CONSTRAINT complaint_ack_unique IF NOT EXISTS FOR (cmp:Complaint) REQUIRE cmp.acknowledgement_no IS UNIQUE;
CREATE CONSTRAINT complaint_id_unique IF NOT EXISTS FOR (cmp:Complaint) REQUIRE cmp.complaint_id IS UNIQUE;
CREATE CONSTRAINT upi_vpa_unique IF NOT EXISTS FOR (u:UPI) REQUIRE u.vpa IS UNIQUE;
CREATE CONSTRAINT phone_number_unique IF NOT EXISTS FOR (p:Phone) REQUIRE p.phone_number IS UNIQUE;
CREATE CONSTRAINT device_id_unique IF NOT EXISTS FOR (d:Device) REQUIRE d.device_id IS UNIQUE;
CREATE CONSTRAINT bank_code_unique IF NOT EXISTS FOR (b:Bank) REQUIRE b.bank_code IS UNIQUE;
CREATE CONSTRAINT atm_id_unique IF NOT EXISTS FOR (atm:ATM) REQUIRE atm.atm_id IS UNIQUE;
CREATE CONSTRAINT location_id_unique IF NOT EXISTS FOR (l:Location) REQUIRE l.location_id IS UNIQUE;

// 2. RANGE & COMPOSITE PROPERTY INDEXES
CREATE INDEX account_mule_idx IF NOT EXISTS FOR (a:Account) ON (a.is_mule, a.mule_tier);
CREATE INDEX account_risk_idx IF NOT EXISTS FOR (a:Account) ON (a.risk_score);
CREATE INDEX transaction_ts_idx IF NOT EXISTS FOR (t:Transaction) ON (t.timestamp);
CREATE INDEX transaction_amount_idx IF NOT EXISTS FOR (t:Transaction) ON (t.amount);
CREATE INDEX transaction_fraud_idx IF NOT EXISTS FOR (t:Transaction) ON (t.is_fraud);
CREATE INDEX complaint_category_idx IF NOT EXISTS FOR (cmp:Complaint) ON (cmp.category);
CREATE INDEX complaint_reported_date_idx IF NOT EXISTS FOR (cmp:Complaint) ON (cmp.reported_date);
CREATE INDEX location_city_state_idx IF NOT EXISTS FOR (l:Location) ON (l.city, l.state);
CREATE INDEX location_hotspot_idx IF NOT EXISTS FOR (l:Location) ON (l.is_cyber_hotspot);
CREATE INDEX phone_suspect_idx IF NOT EXISTS FOR (p:Phone) ON (p.is_suspect);
CREATE INDEX upi_suspicious_idx IF NOT EXISTS FOR (u:UPI) ON (u.is_suspicious);
CREATE INDEX device_shared_idx IF NOT EXISTS FOR (d:Device) ON (d.is_shared_device);
