# CyberShield Intel: Synthetic Data Dictionary & Schema Specification

**Compliance Disclaimer:**
All data definitions described herein represent **purely synthetic schemas** modeled to emulate the operational structures of the National Cyber Crime Reporting Portal (NCRP / 1930) and Indian banking rails (UPI, IMPS, NEFT) for hackathon evaluation without handling classified or private data.

---

## 1. Complaint Entity Schema (`complaints`)
Modeled after standard NCRP / 1930 Citizen Cyber Fraud Incident Reports:

| Field Name | Type | Description | Synthetic Example |
|---|---|---|---|
| `id` | UUID | Unique internal record identifier | `a1b2c3d4-e5f6-7890-abcd-1234567890ab` |
| `acknowledgement_no` | VARCHAR(100) | Public citizen complaint tracking number | `NCRP-SYN-2024-10024` |
| `category` | VARCHAR(100) | Top-level crime category | `Financial Fraud` |
| `subcategory` | VARCHAR(150) | Specific crime modus operandi | `UPI QR Code Impersonation Scam` |
| `victim_state` | VARCHAR(100) | State of reporting citizen | `Maharashtra` |
| `victim_district` | VARCHAR(100) | District jurisdiction | `Mumbai Suburban` |
| `reported_loss_inr` | NUMERIC(15,2) | Defrauded amount in Indian Rupees | `48000.00` |
| `suspect_upi` | VARCHAR(255) | Beneficiary UPI VPA provided by victim | `mule.849@synthaxis` |
| `suspect_account_number` | VARCHAR(50) | Beneficiary bank account number | `SYN9810482019` |
| `suspect_ifsc` | VARCHAR(20) | Indian Financial System Code | `SYNB000101` |
| `suspect_phone` | VARCHAR(20) | Calling or WhatsApp suspect phone | `+919876543210` |
| `incident_timestamp` | TIMESTAMP WITH TIME ZONE | Timestamp when fraudulent debit occurred | `2024-09-20T10:15:00Z` |
| `status` | VARCHAR(50) | Investigation workflow status | `UNDER_INVESTIGATION` |
| `triage_priority` | VARCHAR(20) | Automated heuristic priority | `HIGH` |
| `risk_score` | NUMERIC(5,4) | Machine learning anomaly score [0.0 - 1.0] | `0.8800` |
| `description_synthetic` | TEXT | De-identified synthesized narrative | Synthetic fraud case summary |

---

## 2. Bank Account Entity Schema (`bank_accounts`)

| Field Name | Type | Description | Synthetic Example |
|---|---|---|---|
| `account_number` | VARCHAR(50) | Primary key bank account number | `SYN9810482019` |
| `ifsc_code` | VARCHAR(20) | Bank branch code | `SYNB000101` |
| `bank_name` | VARCHAR(150) | Institution name | `State Bank of Synth` |
| `holder_synthetic_name` | VARCHAR(255) | Synthesized account holder identity | `Synthetic Beneficiary Identity` |
| `is_frozen` | BOOLEAN | Indicates if lien has been applied | `false` |
| `mule_layer_detected` | INT | Layer hierarchy (0=clean, 1=L1, 2=L2, 3=cashout) | `1` |
| `risk_score` | NUMERIC(5,4) | Composite mule risk score | `0.8400` |
| `total_credit_volume_inr`| NUMERIC(18,2) | Cumulative lifetime credits | `450000.00` |
| `total_debit_volume_inr` | NUMERIC(18,2) | Cumulative lifetime debits | `442000.00` |

---

## 3. Financial Transaction Entity Schema (`transactions`)

| Field Name | Type | Description | Synthetic Example |
|---|---|---|---|
| `txn_ref_no` | VARCHAR(100) | Unique banking reference (UPI RRN / UTR) | `UPI/42890184/SYN` |
| `sender_account` | VARCHAR(50) | Originating account | `VIC10482019` |
| `receiver_account` | VARCHAR(50) | Target account | `SYN9810482019` |
| `amount_inr` | NUMERIC(15,2) | Transfer amount in INR | `48000.00` |
| `rail_type` | VARCHAR(20) | Payment rail (`UPI`, `IMPS`, `NEFT`, `RTGS`) | `UPI` |
| `timestamp` | TIMESTAMP WITH TIME ZONE | Transfer execution timestamp | `2024-09-20T10:18:00Z` |
| `layer_depth` | INT | Flow hop depth from primary victim | `1` |
| `is_flagged_suspicious` | BOOLEAN | Flagged by real-time risk engine | `true` |
| `anomaly_score` | NUMERIC(5,4) | Isolation forest / rule score | `0.8800` |
