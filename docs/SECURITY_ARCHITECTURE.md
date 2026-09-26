# Security Architecture & Production Adaptation Guide
## Cybercrime Intelligence & Financial Transaction Risk Detection Platform

---

## 1. Executive Summary & Defense-in-Depth Model

The CyberShield-Intel platform is engineered for Law Enforcement Agencies (LEAs), Financial Intelligence Units (FIU-IND), and banking fraud risk cells. It implements an enterprise-grade, defense-in-depth security architecture protecting sensitive intelligence, maintaining unbroken evidentiary chain-of-custody, and preventing unauthorized surveillance or data exfiltration.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Edge Security Layer                           │
│  - Strict CORS Origin Allowlist     - TLS 1.3 Termination               │
│  - Defense-in-Depth HTTP Headers    - Sliding-Window Rate Limiter       │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                        Authentication & Identity                        │
│  - Salted Bcrypt Hashing (12 rounds) - JWT Access/Refresh Lifecycle     │
│  - In-Memory Token Revocation Blacklist                                │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                   Authorization & Access Governance                     │
│  - Role-Based Access Control (RBAC) at API Dependency Layer             │
│  - 4 Discrete Roles: ADMIN | SUPERVISOR | INVESTIGATOR | ANALYST        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                       Data Protection & Masking                         │
│  - Field-Level Masking (Bank Accounts: SYN******4455, Phones, Emails)   │
│  - Automated Log Sanitizer Scrubbing Passwords, Tokens, & Accounts      │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                 Evidentiary Audit & Chain-of-Custody                    │
│  - Mandatory Audit Logging across 8 High-Impact Actions                 │
│  - Cryptographic SHA-256 Checksum on Exported Forensic Dossiers         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Implemented Core Security Controls

### 2.1 JWT Authentication & Session Lifecycle
- **Tokens**: Dual-token architecture using ephemeral, short-lived **Access Tokens** (default: 60 minutes) and cryptographically bound **Refresh Tokens** (default: 7 days).
- **Cryptographic Algorithm**: Strictly enforces `HS256`. The verification engine rejects unverified tokens and explicitly disallows the `'none'` algorithm.
- **Session Revocation**: A centralized token blacklist tracks logged-out or invalidated tokens (`POST /auth/logout`), preventing replay attacks.
- **Payload Claims**: Contains `sub` (user identity), `role` (canonical RBAC tier), `jti` (unique token UUID), `type` (`access` or `refresh`), `iat` (issued at), and `exp` (expiration).

### 2.2 Password Security & Cryptographic Hashing
- **Hashing Algorithm**: Salted **Bcrypt** with a work factor of 12 rounds (`bcrypt.gensalt(12)`).
- **Salt Generation**: Unique cryptographically secure pseudo-random number generator (CSPRNG) salt generated per user.
- **Password Strength Policy**: Validated before hashing. Requires a minimum of 8 characters (12+ recommended) and rejects trivially guessable common passwords. Inputs are capped at 72 bytes to prevent bcrypt Denial-of-Service (DoS) attacks.

### 2.3 Role-Based Access Control (RBAC)
Enforced at the FastAPI route dependency level via `require_roles(...)`. Access is divided into four distinct operational tiers:

| Role | Permitted Actions | Restricted Actions |
| :--- | :--- | :--- |
| **`ADMIN`** | User provisioning, role assignment, system configuration, audit trail query, all investigative actions | None |
| **`SUPERVISOR`** | Case allocation, case disposition, audit trail query, forensic report exports, viewing unmasked accounts | User creation, system secrets |
| **`INVESTIGATOR`** | Case creation, case updates, debit freeze requests, viewing unmasked account intelligence, single-case export | Bulk exports, user administration, audit queries |
| **`ANALYST`** | Viewing alerts, running risk predictions, graph querying, geospatial intelligence | Creating cases, unmasked account numbers, data exports |

### 2.4 API Rate Limiting
Implemented via a high-performance sliding-window rate limiter ([`backend/app/core/rate_limit.py`](file:///Users/ronitsingh/Anti/SIH/backend/app/core/rate_limit.py)):
- **Authentication Endpoints** (`/auth/login`, `/auth/login-json`): Maximum **5 requests / minute** per client IP to mitigate brute-force and credential-stuffing attacks.
- **Data Export Endpoints** (`/cases/{id}/export`): Maximum **10 requests / minute** to prevent bulk exfiltration.
- **Standard API Endpoints**: Maximum **120 requests / minute**.
- **Violation Response**: Returns HTTP `429 Too Many Requests` with `Retry-After`, `X-RateLimit-Limit`, and `X-RateLimit-Remaining` headers.

### 2.5 Strict CORS Configuration
Configured in [`backend/app/main.py`](file:///Users/ronitsingh/Anti/SIH/backend/app/main.py):
- **Origin Allowlist**: Explicitly controlled via `settings.ALLOWED_CORS_ORIGINS`.
- **Zero Wildcards**: Wildcard (`*`) origins are prohibited when `allow_credentials=True`.
- **Restricted Methods**: Allows only necessary HTTP verbs: `GET`, `POST`, `PATCH`, `PUT`, `DELETE`, `OPTIONS`.

### 2.6 Secure HTTP Headers Middleware
Every HTTP response carries protective defense-in-depth headers:
- `X-Content-Type-Options: nosniff`: Prevents MIME-type sniffing attacks.
- `X-Frame-Options: DENY`: Defends against clickjacking.
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`: Enforces TLS encryption.
- `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self';`: Eliminates cross-site scripting (XSS) and frame embedding.
- `Referrer-Policy: strict-origin-when-cross-origin`: Minimizes referrer information leakage.
- `Permissions-Policy: accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()`: Disables unneeded browser APIs.
- `Cache-Control: no-store, no-cache, must-revalidate`: Enforced on all authenticated API responses to prevent local browser caching of sensitive intelligence.

### 2.7 Request Validation & Sanitized Error Responses
- **Pydantic v2 Schema Enforcement**: All incoming payloads undergo strict validation with regex boundary constraints on bank accounts (`^[A-Z0-9]{8,18}$`), Indian phones (`^\+91[6-9]\d{9}$`), and UUIDs.
- **Sanitized Error Handlers**:
  - `422 Unprocessable Entity`: Returns structured parameter location and messages without exposing server internals.
  - `500 Internal Server Error`: Replaces raw stack traces with a generic sanitized error code and reference ID.

### 2.8 Forensic Audit Logging (8 Mandatory Actions)
Managed by the [`AuditService`](file:///Users/ronitsingh/Anti/SIH/backend/app/services/audit_service.py):

| Action | Trigger Point | Forensic Details Recorded |
| :--- | :--- | :--- |
| **`LOGIN`** | Successful or failed login attempt | Timestamp, Actor Email, Client IP, User-Agent, Result Status |
| **`LOGOUT`** | Session termination | Actor Email, Session Token Signature, IP |
| **`VIEW_ALERT`** | Viewing alert details (`GET /alerts/{id}`) | Alert ID, Severity, Composite Risk Score |
| **`VIEW_ACCOUNT`** | Accessing bank account intelligence | Masked Account Number, Bank Name, Mule Risk Score |
| **`CREATE_CASE`** | Opening a new investigation docket | Case Number, Title, Priority, Assigned Officer |
| **`UPDATE_CASE`** | Changing status, priority, or notes | Case Number, Status Change, Recovery Amount |
| **`EXPORT_DATA`** | Generating forensic intelligence dossier | Export ID, Case Number, Cryptographic SHA-256 Hash |
| **`ADMIN_ACTION`** | Provisioning users, changing permissions | Target User, Role Assigned, Invoking Admin |

### 2.9 Sensitive Field Protection
- **Masking Engine** ([`backend/app/core/sanitizer.py`](file:///Users/ronitsingh/Anti/SIH/backend/app/core/sanitizer.py)):
  - Bank Accounts: Middle digits masked (`SYN1122334455` $\to$ `SYN******4455`).
  - Mobile Phones: Middle digits masked (`+919876543210` $\to$ `+91******3210`).
  - Passwords & Tokens: Scrubbed entirely (`[REDACTED]`).
- **SafeLogFormatter**: A custom logging formatter scans all output streams and scrubs passwords, bearer tokens, and raw account numbers using regular expressions.

### 2.10 Secret Management Through Environment Variables
- Centralized in `backend/app/core/config.py` using Pydantic `BaseSettings`.
- **Production Safety Check**: In `production` mode, the application halts startup (`RuntimeError`) if `JWT_SECRET_KEY` is not provided via an external environment variable or Docker secret mount. Ephemeral fallback secrets are strictly restricted to local development sandboxes.

---

## 3. Production Adaptation for Government & Banking Environments

When deploying this system within authorized Indian Law Enforcement Agencies (I4C, CBI, State Police Cyber Wings) or Scheduled Commercial Banks, the following controls require adaptation:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       GOVERNMENT / BANK ADAPTATION MATRIX                       │
├────────────────────────────┬────────────────────────────────────────────────────┤
│ Regulatory Framework       │ Required Production Adaptation                     │
├────────────────────────────┼────────────────────────────────────────────────────┤
│ CERT-In Directions 2022    │ - Synchronize system clocks with Indian Standard   │
│ (Cyber Security Directives)│   Time (NTP via NPL / NIC).                        │
│                            │ - Retain audit trails & logs for 180+ days.       │
│                            │ - Mandate 6-hour cybersecurity incident reporting. │
├────────────────────────────┼────────────────────────────────────────────────────┤
│ RBI Master Direction on    │ - Replace symmetric HS256 with asymmetric RS256/   │
│ Cyber Security in Banks    │   ES384 backed by FIPS 140-2 Level 3 HSM.          │
│                            │ - Mutual TLS (mTLS) for all inter-bank connections.│
│                            │ - At-rest encryption using AES-256-GCM.            │
├────────────────────────────┼────────────────────────────────────────────────────┤
│ Bharatiya Sakshya          │ - Generate automated Section 63 BSA (formerly 65B  │
│ Adhiniyam, 2023 (BSA)      │   IEA) Electronic Certificates on exported files.  │
│ (Electronic Evidence)      │ - Digital signature by authorized officer DSC.    │
├────────────────────────────┼────────────────────────────────────────────────────┤
│ National SSO & Identity    │ - Integrate with e-Pramaan or Jan Parichay SSO.    │
│ Federation                 │ - Connect with LEA LDAP / Active Directory.        │
│                            │ - Multi-Factor Authentication (MFA / SMS / TOTP).  │
├────────────────────────────┼────────────────────────────────────────────────────┤
│ Sovereign Infrastructure   │ - Deploy on MeghRaj (NIC Cloud) or GovCloud.       │
│ Air-Gapped Deployment      │ - Enforce private isolated VPCs with zero direct   │
│                            │   public internet ingress/egress.                  │
└────────────────────────────┴────────────────────────────────────────────────────┘
```

### Detailed Adaptation Specifications

#### 1. Hardware Security Module (HSM) Integration
- **Current State**: JWTs are signed using symmetric `HS256` keys loaded from environment variables.
- **Government/Bank Production**:
  - Deploy FIPS 140-2 Level 3 compliant Hardware Security Modules (e.g., Thales Luna, AWS CloudHSM, or nCipher).
  - Migrate JWT signing to asymmetric `RS256` or `ES384` where private keys never leave the tamper-proof HSM boundary.
  - Implement automated key rotation schedules every 90 days with dual-key validation windows.

#### 2. Mutual TLS (mTLS) for Inter-Agency & Bank Communications
- **Current State**: Unilateral TLS with Bearer token authentication.
- **Government/Bank Production**:
  - Implement bidirectional Mutual TLS (mTLS) for API gateways interfacing with NPCI, 1930 NCRP, and core banking systems.
  - Require X.509 client certificates issued by authorized Certifying Authorities (CAs) under the Controller of Certifying Authorities (CCA India).

#### 3. Section 63 BSA (formerly Sec 65B IEA) Evidentiary Certificates
- **Current State**: Export endpoints generate SHA-256 integrity checksums.
- **Government/Bank Production**:
  - Integrate an automated Electronic Evidence Generator producing Section 63 BSA compliance certificates.
  - Sign exported dossiers using the investigating officer's Class 3 Digital Signature Certificate (DSC) / eSign.
  - Embed timestamped metadata including server MAC addresses, system uptime, and cryptographic hash verification logs.

#### 4. Sovereign Air-Gapped & NIC Cloud Deployment
- **Current State**: Containerized microservices running on local Docker network.
- **Government/Bank Production**:
  - Host inside MeghRaj (Government of India GI-Cloud) or police intranet air-gapped enclaves.
  - Demilitarized Zone (DMZ) for receiving citizen complaints and webhook streams; internal secure zone for Neo4j knowledge graph, XGBoost ML engine, and database clusters.
  - Integrate with State Police CCTNS (Crime and Criminal Tracking Network & Systems) via dedicated secure lease-lines.

---

## 4. Statutory & Regulatory Compliance Statement

> **NOTICE ON SYNTHETIC ENVIRONMENT**:
> During design, prototyping, and local testing, all datasets (citizens, bank accounts, UPI identifiers, complaints, and telephone numbers) are 100% synthetically generated. No actual Personally Identifiable Information (PII) is processed.
