# CyberShield Intel: API Documentation & Contract Specification

**Interactive Documentation URLs (when backend is running):**
- **Swagger UI**: [http://127.0.0.1:8000/api/v1/docs](http://127.0.0.1:8000/api/v1/docs)
- **ReDoc UI**: [http://127.0.0.1:8000/api/v1/redoc](http://127.0.0.1:8000/api/v1/redoc)
- **OpenAPI JSON**: [http://127.0.0.1:8000/api/v1/openapi.json](http://127.0.0.1:8000/api/v1/openapi.json)

---

## 1. Authentication & Security
The API uses **OAuth2 Password Bearer Tokens (JWT)** for non-public endpoints.
All API state mutations require valid bearer credentials in the `Authorization` header:
```http
Authorization: Bearer <access_token>
```

### 1.1 Development Credentials
| Role | Email | Password |
|---|---|---|
| **Investigator / Analyst** | `analyst@cybercell.gov.in` | `Investigate@2024!` |
| **Supervisor / Admin** | `admin@cybercell.gov.in` | `AdminSecure@2024!` |

---

## 2. API Endpoints Catalog

### 2.1 System Health & Diagnostics (`/api/v1/health`)
- `GET /api/v1/health`: Liveness probe returning operational state and synthetic compliance mode.
- `GET /api/v1/health/ready`: Readiness probe verifying PostgreSQL and Neo4j connectivity.

### 2.2 Authentication & User Profile (`/api/v1/auth`)
- `POST /api/v1/auth/login`: Form-encoded login returning signed JWT access token.
- `GET /api/v1/auth/me`: Current user credentials, badge number, and RBAC privileges.

### 2.3 NCRP / 1930 Cybercrime Complaints (`/api/v1/complaints`)
- `GET /api/v1/complaints`: Paginated list of complaints with search and filtering by state, category, status, and loss threshold.
- `POST /api/v1/complaints`: Ingest a new simulated complaint record.
- `GET /api/v1/complaints/{id}`: Detailed record by UUID.
- `GET /api/v1/complaints/ack/{ack_no}`: Lookup by NCRP acknowledgement number (`NCRP-SYN-2024-XXXXX`).
- `PATCH /api/v1/complaints/{id}`: Update investigation status (`NEW`, `UNDER_INVESTIGATION`, `ESCALATED`, `FROZEN`, `CLOSED`).
- `POST /api/v1/complaints/seed`: Seed the development database with synthetic records.

### 2.4 Financial Transactions & Risk Engine (`/api/v1/transactions`)
- `GET /api/v1/transactions`: Feed of simulated high-velocity transactions across UPI/IMPS rails.
- `POST /api/v1/transactions/assess-risk`: Evaluate multi-factor risk score for an account, UPI VPA, or phone number.
- `GET /api/v1/transactions/accounts/{account_number}`: Retrieve risk assessment, mule layer, and freeze status for an account.

### 2.5 Mule Network Graph Analysis (`/api/v1/graph`)
- `GET /api/v1/graph/subgraph/{account_number}?depth=2`: Neo4j multi-hop neighborhood graph centered on a suspect bank account.
- `GET /api/v1/graph/mule-chain/{complaint_ack}`: Trace end-to-end money flow from victim to downstream cash-out.

### 2.6 Executive Analytics (`/api/v1/analytics`)
- `GET /api/v1/analytics/overview`: High-level intelligence KPIs (total reported, loss INR, active rings, freezes).
- `GET /api/v1/analytics/category-distribution`: Cyber fraud category percentage breakdown.
- `GET /api/v1/analytics/state-distribution`: State-wise cyber fraud statistics for Indian hotspot mapping.

---

## 3. Standard Request & Response Samples

### 3.1 Risk Assessment Request
`POST /api/v1/transactions/assess-risk`
```json
{
  "account_number": "MULE_ACC_99812",
  "upi_id": "fastmule@synthaxis",
  "transaction_amount_inr": 150000.0,
  "complaint_ids": ["NCRP-SYN-2024-10024", "NCRP-SYN-2024-10025"]
}
```

### 3.2 Risk Assessment Response
```json
{
  "entity_id": "MULE_ACC_99812",
  "entity_type": "ACCOUNT",
  "overall_risk_score": 0.814,
  "risk_level": "SEVERE",
  "is_mule_candidate": true,
  "recommended_action": "EMERGENCY_FREEZE",
  "contributing_factors": [
    {
      "name": "Complaint Association",
      "weight": 0.4,
      "score": 0.7,
      "description": "Referenced in 2 citizen cybercrime complaint."
    },
    {
      "name": "Transaction Velocity & Drain Rate",
      "weight": 0.3,
      "score": 0.85,
      "description": "High value transfer (₹150,000.00) matching typical mule account drain patterns."
    },
    {
      "name": "Entity Cluster Affinity",
      "weight": 0.2,
      "score": 0.92,
      "description": "Account mapped to high-risk beneficiary cluster identified in prior investigations."
    }
  ]
}
```

---

## 4. Error Responses
All errors adhere to standard HTTP status codes and provide sanitized JSON payloads:
```json
{
  "error": "ResourceNotFound",
  "detail": "Complaint record not found."
}
```
*Note: SQL syntax or internal stack traces are never exposed in production error responses.*
