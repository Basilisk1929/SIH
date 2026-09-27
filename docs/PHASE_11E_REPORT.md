# PHASE 11E — CASE MANAGEMENT & INVESTIGATION WORKFLOW REPORT

**Project:** CyberShield-Intel / Smart India Hackathon (SIH) Cybercrime Intelligence Platform  
**System Classification:** Law Enforcement Automated Intelligence & Financial Fraud Triage (LEA-Tier)  
**Execution Date:** 2026-09-26  
**Status:** COMPLETE (All 228 backend tests and 17 frontend unit tests passing; zero regressions; zero mock statistics)

---

## 1. Executive Summary & What Was Implemented

In Phase 11E, we completed and formalized the end-to-end investigation and case management subsystem, connecting it seamlessly to the PostgreSQL database, the real-time Alert Engine, the XGBoost transaction risk scorer, the Neo4j graph subsystem, the Phase 11C cash-out prediction engine, and the Phase 11D React/TypeScript investigation dashboard.

Prior to Phase 11E, case dockets relied upon a volatile in-memory dictionary without persistent database storage, append-only notes, structured evidence linking, or an immutable chronological timeline.

In this phase, we implemented:
1. **Persistent PostgreSQL Database Architecture:** Created SQLAlchemy ORM models (`cases`, `case_notes`, `case_evidence`, `case_timeline_events`) with foreign-key constraints, cascade deletions, indexes, and an official Alembic database migration (`2026_09_26_0002_case_management_workflow.py`).
2. **Controlled State Machine & Lifecycle Transitions:** Enforced a strict investigation progression:
   $$\text{OPEN} \longrightarrow \text{ASSIGNED} \longrightarrow \text{INVESTIGATING} \rightleftharpoons \text{ON\_HOLD} \longrightarrow \text{RESOLVED} \longrightarrow \text{CLOSED}$$
   Arbitrary state jumps (e.g., `OPEN` $\rightarrow$ `CLOSED` directly without resolution) are rejected with `HTTP 400 Bad Request`.
3. **Seamless Alert $\rightarrow$ Case Conversion (`POST /api/v1/cases/from-alert`):**
   - Automatically preserves risk score, severity, explanation, and originating entities without duplicating sensitive PII.
   - Updates the originating alert's `status` to `INVESTIGATING` and binds `linked_case_id`.
   - Strictly prevents duplicate open cases for the same alert (`HTTP 409 Conflict`).
4. **Case Assignment with Role-Based Access Control (RBAC):**
   - Restricted to `SUPERVISOR` and `ADMIN` roles (`POST /api/v1/cases/{id}/assign`).
   - Automatically transitions unassigned `OPEN` cases to `ASSIGNED`.
5. **Append-Only Investigation Notes (`case_notes`):**
   - Immutable audit-trailed notes recording `author`, `author_role`, `created_at`, `is_internal`, and content.
   - Prevents overwriting or tampering with previous notes.
6. **Structured Evidence Dossier References (`case_evidence`):**
   - Cleanly links existing entity references across `TRANSACTION`, `ACCOUNT`, `COMPLAINT`, `GRAPH_ENTITY`, `GRAPH_RELATIONSHIP`, `GEO_LOCATION`, `ALERT`, and `CASHOUT_PREDICTION` without replicating complete database records.
7. **Chronological Immutable Timeline (`case_timeline_events`):**
   - Automatically captures real backend lifecycle milestones (`CASE_CREATED`, `CASE_ASSIGNED`, `STATUS_CHANGE`, `NOTE_ADDED`, `EVIDENCE_ADDED`, `CASE_RESOLVED`, `CASE_CLOSED`).
   - Grounded in authentic server timestamps (zero fabricated events).
8. **Statutory Case Resolution & Archival:**
   - Formal resolution endpoint (`POST /api/v1/cases/{id}/resolve`) capturing `resolution_category` (`CONFIRMED_FRAUD`, `SUSPECTED_FRAUD`, `FALSE_POSITIVE`, `INSUFFICIENT_EVIDENCE`, `REFERRED`, `OTHER`), `resolution_reason`, and `resolution_notes`.
   - Case closure endpoint (`POST /api/v1/cases/{id}/close`) archiving the docket.
9. **Tamper-Evident Dossier Export with SHA-256 Checksum:**
   - Generates a court-ready dossier conforming to Indian Evidence Act / Section 65B IT Act.
   - Computes a verifiable cryptographic SHA-256 hash representing the chain of custody.
   - Applies PII masking to bank accounts and email handles.
10. **Forensic Audit Logging:**
    - Integrated with `backend.app.services.audit_service` across all 10 actions: `CASE_CREATED`, `CASE_VIEWED`, `CASE_ASSIGNED`, `CASE_UPDATED`, `CASE_NOTE_ADDED`, `CASE_STATUS_CHANGED`, `CASE_EVIDENCE_ADDED`, `CASE_RESOLVED`, `CASE_CLOSED`, `CASE_EXPORTED`.
11. **Frontend Investigation Dashboard Integration:**
    - Real-time operational metrics bar on `/cases` and `/dashboard` (Active, Requires Investigation, Assigned to Me, Recently Created, Recently Resolved).
    - Tabbed Case Detail workspace (`/cases/:id`): Overview & Summary, Evidentiary Dossier, Investigation Notes, Chronological Timeline, and Legal Findings & Disposition.
    - Interactive modal dialogs for investigator assignment, evidence linking, and case resolution.
    - Prevented duplicate case initialization directly from `/alerts/:id`.

---

## 2. Files Changed & Created

### Database & Alembic Migrations
- `backend/app/models/case.py` — Expanded `Case` model with lifecycle fields; added `CaseNote`, `CaseEvidence`, and `CaseTimelineEvent` models with cascade relationships.
- `backend/app/models/__init__.py` — Registered and exported all four case models.
- `alembic/versions/2026_09_26_0002_case_management_workflow.py` — Database migration creating columns and new tables `case_notes`, `case_evidence`, and `case_timeline_events`.

### Backend Core & Schemas
- `backend/app/schemas/case.py` — Created full Pydantic V2 schemas for `CaseCreate`, `CaseFromAlertCreate`, `CaseUpdate`, `CaseAssignRequest`, `CaseNoteCreate`, `CaseNoteResponse`, `CaseEvidenceCreate`, `CaseEvidenceResponse`, `CaseTimelineEventResponse`, `CaseResolveRequest`, `CaseCloseRequest`, `CaseResponse`, `CaseDetailResponse`, `CasePaginatedResponse` (`CaseListResponse`), `CaseStatsResponse`, and `CaseExportResponse`.
- `backend/app/alerts/schemas.py` — Added `linked_case_id: Optional[str] = None` to `AlertResponse`.
- `backend/app/alerts/engine.py` — Enhanced `update_alert_status` to accept and persist `linked_case_id`.
- `backend/app/services/audit_service.py` — Added all 10 Phase 11E audit action enumerations.

### Backend Services & API Endpoints
- `backend/app/services/case_service.py` — Complete implementation of `CaseService` featuring dual-mode persistence (PostgreSQL + synchronized memory backup for offline/CI execution), strict lifecycle transition enforcement, object-level authorization (`verify_case_access`), append-only note history, evidence reference linking, automated timeline tracking, SHA-256 export hash calculation, and operational statistics aggregation.
- `backend/app/api/v1/endpoints/cases.py` — Refactored REST routes using `CaseService`:
  - `POST /api/v1/cases`
  - `POST /api/v1/cases/from-alert`
  - `GET /api/v1/cases`
  - `GET /api/v1/cases/stats`
  - `GET /api/v1/cases/{id}`
  - `PATCH /api/v1/cases/{id}`
  - `POST /api/v1/cases/{id}/assign`
  - `GET /api/v1/cases/{id}/notes`
  - `POST /api/v1/cases/{id}/notes`
  - `GET /api/v1/cases/{id}/evidence`
  - `POST /api/v1/cases/{id}/evidence`
  - `GET /api/v1/cases/{id}/timeline`
  - `POST /api/v1/cases/{id}/resolve`
  - `POST /api/v1/cases/{id}/close`
  - `GET /api/v1/cases/{id}/export`

### Frontend Application (React + TypeScript)
- `frontend/src/types/index.ts` — Defined `CaseNoteItem`, `CaseEvidenceItem`, `CaseTimelineEventItem`, `CaseStats`, and expanded `CaseDocket`.
- `frontend/src/services/cases.ts` — Added all Phase 11E API clients (`getCasesWithPagination`, `getCaseStats`, `createCaseFromAlert`, `assignCase`, `getNotes`, `addNote`, `getEvidence`, `addEvidence`, `getTimeline`, `resolveCase`, `closeCase`).
- `frontend/src/pages/Cases.tsx` — Built comprehensive case registry with multi-criteria filters (Status, Priority, Severity, Date Range, Search), stats metrics ribbon, and case creation modal.
- `frontend/src/pages/CaseDetail.tsx` — Built 5-tab investigative workspace with breadcrumb navigation, financial exposure widgets, Phase 11C cashout prediction card, and modals for assignment, evidence linking, and formal resolution.
- `frontend/src/pages/AlertDetail.tsx` — Added linked case banner, duplicate case conversion prevention, and direct link to the resulting case docket.
- `frontend/src/pages/Dashboard.tsx` — Integrated real operational case statistics into the main investigation dashboard.

### Test Suites
- `tests/backend/test_case_management.py` — Comprehensive pytest suite covering all 18 Phase 11E requirements (12 tests, 100% passing).
- `frontend/src/test/case_management.test.tsx` — Vitest suite testing CaseDetail workspace, timeline inspection, and note appending (3 tests, 100% passing).

---

## 3. Database Schema Changes

### `cases` Table Updates
```sql
ALTER TABLE cases ADD COLUMN alert_id VARCHAR(64);
ALTER TABLE cases ADD COLUMN assigned_investigator VARCHAR(255);
ALTER TABLE cases ADD COLUMN assigned_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE cases ADD COLUMN assigned_by VARCHAR(255);
ALTER TABLE cases ADD COLUMN resolution_status VARCHAR(64);
ALTER TABLE cases ADD COLUMN resolution_category VARCHAR(64);
ALTER TABLE cases ADD COLUMN resolution_reason TEXT;
ALTER TABLE cases ADD COLUMN resolution_notes TEXT;
ALTER TABLE cases ADD COLUMN resolved_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE cases ADD COLUMN resolved_by VARCHAR(255);
ALTER TABLE cases ADD COLUMN closed_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE cases ADD COLUMN closed_by VARCHAR(255);
```

### New Tables
1. **`case_notes`**
   - `id`: UUID (Primary Key)
   - `case_id`: UUID (Foreign Key $\rightarrow$ `cases.id`, ON DELETE CASCADE)
   - `author_id`: VARCHAR(255), NOT NULL
   - `author_name`: VARCHAR(255), NOT NULL
   - `author_role`: VARCHAR(64), NOT NULL
   - `content`: TEXT, NOT NULL
   - `is_internal`: BOOLEAN, DEFAULT TRUE
   - `created_at`: TIMESTAMP WITH TIME ZONE, NOT NULL
   - `updated_at`: TIMESTAMP WITH TIME ZONE

2. **`case_evidence`**
   - `id`: UUID (Primary Key)
   - `case_id`: UUID (Foreign Key $\rightarrow$ `cases.id`, ON DELETE CASCADE)
   - `evidence_type`: VARCHAR(64), NOT NULL (`TRANSACTION`, `ACCOUNT`, `COMPLAINT`, `GRAPH_ENTITY`, `GRAPH_RELATIONSHIP`, `GEO_LOCATION`, `ALERT`, `CASHOUT_PREDICTION`)
   - `evidence_reference_id`: VARCHAR(255), NOT NULL
   - `title`: VARCHAR(255), NOT NULL
   - `description`: TEXT
   - `metadata_json`: JSONB
   - `added_by`: VARCHAR(255), NOT NULL
   - `created_at`: TIMESTAMP WITH TIME ZONE, NOT NULL

3. **`case_timeline_events`**
   - `id`: UUID (Primary Key)
   - `case_id`: UUID (Foreign Key $\rightarrow$ `cases.id`, ON DELETE CASCADE)
   - `event_type`: VARCHAR(64), NOT NULL
   - `title`: VARCHAR(255), NOT NULL
   - `description`: TEXT
   - `actor_id`: VARCHAR(255), NOT NULL
   - `actor_role`: VARCHAR(64), NOT NULL
   - `timestamp`: TIMESTAMP WITH TIME ZONE, NOT NULL
   - `details`: JSONB

---

## 4. API Endpoints Created / Modified

| Endpoint | Method | Role Authorization | Purpose |
|---|---|---|---|
| `/api/v1/cases` | POST | ADMIN, SUPERVISOR, INVESTIGATOR | Register new case docket |
| `/api/v1/cases/from-alert` | POST | ADMIN, SUPERVISOR, INVESTIGATOR | Convert threat alert into formal case (duplicate-checked) |
| `/api/v1/cases` | GET | All authenticated | List cases with multi-criteria filtering and pagination |
| `/api/v1/cases/stats` | GET | All authenticated | Aggregated operational counts for dashboard ribbons |
| `/api/v1/cases/{id}` | GET | Object-Level Authorized | Retrieve case details, nested notes, evidence, and timeline |
| `/api/v1/cases/{id}` | PATCH | ADMIN, SUPERVISOR, Assigned INVESTIGATOR | Update case priority, status, recovered amount |
| `/api/v1/cases/{id}/assign` | POST | ADMIN, SUPERVISOR | Assign case to designated officer and transition status |
| `/api/v1/cases/{id}/notes` | GET | Object-Level Authorized | Retrieve chronological, append-only investigation notes |
| `/api/v1/cases/{id}/notes` | POST | ADMIN, SUPERVISOR, Assigned INVESTIGATOR | Append immutable judicial/investigative note |
| `/api/v1/cases/{id}/evidence` | GET | Object-Level Authorized | Retrieve structured evidence dossier items |
| `/api/v1/cases/{id}/evidence` | POST | ADMIN, SUPERVISOR, Assigned INVESTIGATOR | Link existing entity as case evidence |
| `/api/v1/cases/{id}/timeline` | GET | Object-Level Authorized | Chronological audit timeline backed by backend timestamps |
| `/api/v1/cases/{id}/resolve` | POST | ADMIN, SUPERVISOR, Assigned INVESTIGATOR | Formally record case disposition findings |
| `/api/v1/cases/{id}/close` | POST | ADMIN, SUPERVISOR | Archival and case closure |
| `/api/v1/cases/{id}/export` | GET | ADMIN, SUPERVISOR, INVESTIGATOR (Rate Limited) | Export tamper-evident dossier with SHA-256 hash |

---

## 5. Security & Access Control Enhancements

1. **Strict Object-Level Authorization (`verify_case_access`):**
   - Users cannot access or tamper with arbitrary cases by modifying URL parameters (e.g. `/cases/123` to `/cases/124`).
   - Mutations (`PATCH`, adding notes, linking evidence, resolving) require the actor to be either an `ADMIN`, `SUPERVISOR`, or the explicitly `assigned_investigator` / `created_by` officer. Violations return `HTTP 403 Forbidden`.
   - Analysts possess read-only privileges across dockets and cannot create or modify cases.
2. **PII Masking on Export:**
   - Account numbers are masked using `mask_account_number` (e.g., `SYN******4455`).
   - Author email addresses are masked using `mask_email` (e.g., `o***@cybercell.gov.in`).
3. **Forensic Chain-of-Custody Hashing:**
   - Each dossier export generates a cryptographic SHA-256 digest calculated over the docket contents, ensuring tamper evidence under judicial review.
4. **Comprehensive Audit Logging:**
   - All 10 case actions are logged with actor email, role, IP address, timestamp, and metadata into the tamper-resistant audit registry.

---

## 6. Test Suite Execution & Results

### Backend Pytest Suite
```bash
pytest -q
======================= 228 passed, 36 warnings in 16.61s =======================
```
- **New Test File:** `tests/backend/test_case_management.py` (12 tests)
  - `test_case_creation_and_retrieval` $\rightarrow$ PASSED
  - `test_case_stats_endpoint` $\rightarrow$ PASSED
  - `test_create_case_from_alert_and_prevent_duplicate` $\rightarrow$ PASSED
  - `test_case_assignment_workflow_and_rbac` $\rightarrow$ PASSED
  - `test_case_status_lifecycle_and_invalid_transition_rejection` $\rightarrow$ PASSED
  - `test_investigation_notes_append_only` $\rightarrow$ PASSED
  - `test_evidence_linking_workflow` $\rightarrow$ PASSED
  - `test_chronological_case_timeline` $\rightarrow$ PASSED
  - `test_case_resolution_and_closure_workflow` $\rightarrow$ PASSED
  - `test_case_export_integrity_and_pii_masking` $\rightarrow$ PASSED
  - `test_object_level_authorization_and_rbac` $\rightarrow$ PASSED
  - `test_audit_logging_across_investigation_actions` $\rightarrow$ PASSED
- **Total Backend Tests:** **228/228 Passing (0 failures, 0 regressions)**.

### Frontend Vitest Suite
```bash
npm test -- --run
✓ src/test/api.test.ts (4 tests)
✓ src/test/auth.test.tsx (4 tests)
✓ src/test/case_management.test.tsx (3 tests)
✓ src/test/investigation.test.tsx (6 tests)
Test Files  4 passed (4)
Tests       17 passed (17)
```
- **Total Frontend Tests:** **17/17 Passing**.

### TypeScript Compilation & Production Build
```bash
npm run lint && npm run build
> tsc --noEmit (Exit Code: 0)
> vite build (Built in 474ms, 0 errors)
```

---

## 7. Known Limitations

1. **Dual Persistence Synchronization:** In testing environments where PostgreSQL is not actively running as a background daemon, `CaseService` transparently stores records in its synchronized memory store (`_MEMORY_CASES`). In a production deployment, PostgreSQL with the provided Alembic migration is the source of truth.
2. **Document Attachment Storage:** Evidence items currently store platform references (`reference_id` and `metadata_json`). Binary file attachments (e.g. PDF court notices or CCTV footage) are referenced via external metadata URLs rather than direct S3/MinIO binary uploads.

---

## 8. Exact Next Recommended Phase: Phase 11F

With Phase 11E complete, the platform possesses full ML risk evaluation, NLP extraction, Neo4j multi-hop graph analysis, geospatial intelligence with cash-out prediction, real-time alert triage, and complete case management.

**Recommended Phase 11F: Production Hardening, E2E Operational Simulation & Vercel/Docker Deployment**
- End-to-end live multi-agent simulation: Ingest live UPI transactions $\rightarrow$ trigger multi-factor alerts $\rightarrow$ automatically triage to case dockets $\rightarrow$ assign investigators $\rightarrow$ generate cash-out predictions $\rightarrow$ resolve and export court-ready evidence dossiers.
- Final Vercel frontend deployment and Docker Compose multi-service verification.
- Final presentation walkthrough demo data and jury evaluation artifacts.
