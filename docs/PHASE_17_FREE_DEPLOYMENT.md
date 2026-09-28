# CyberShield-Intel — Phase 17 Permanent ₹0 Cloud Deployment & SIH Judge Readiness Report

> **Smart India Hackathon (SIH) Evaluation Platform**  
> Public Demonstration Environment — Synthetic Data Only  
> Total Monthly Infrastructure Cost: **₹0 / month**  
> Workstation Independence: **Verified (MacBook completely offline)**

---

## 1. Final Architecture

```
                                 INTERNET / SIH JUDGE EVALUATION
                                               |
                                               v
                        +--------------------------------------------+
                        |           Vercel (Hobby / Free)            |
                        |         React 18 + Vite Frontend           |
                        |   https://frontend-bay-tau-86.vercel.app   |
                        +----------------------+---------------------+
                                               |
                             HTTPS (REST) / WSS (WebSockets)
                                               |
                                               v
                        +--------------------------------------------+
                        |        Render Free Web Service             |
                        |      FastAPI Modular Engine (Python 3.12)  |
                        | https://cybershield-intel-backend.onrender.com
                        +----------------------+---------------------+
                                               |
                       +-----------------------+-----------------------+
                       |                                               |
                       v                                               v
    +------------------------------------+  +------------------------------------+
    |       Supabase PostgreSQL          |  |          Neo4j Aura Free           |
    |        (Free Cloud Tier)           |  |        (Free Cloud Instance)       |
    |  - PostgreSQL 16 + AsyncPG (SSL)   |  |  - AuraDB Free (Instance c9d53e67) |
    |  - Cases, Alerts, Complaints       |  |  - Mule Account Network Topology   |
    |  - Financial Transactions, Audit   |  |  - Smurfing & Layering Traversal   |
    +------------------------------------+  +------------------------------------+
                       |
                       v
    +------------------------------------+
    |         In-Memory Fallback         |
    |  - Sliding-Window Rate Limiter     |
    |  - In-Memory Token Revocation      |
    |  - In-Memory AlertBroadcaster      |
    |  (Zero Redis hosting overhead)     |
    +------------------------------------+
```

---

## 2. Infrastructure Services Inventory & ₹0 Cost Verification

| Subsystem | Service Provider & Tier | Cost | Status | URL / Identifier |
|---|---|---|---|---|
| **Frontend** | Vercel (Hobby / Free) | **₹0** | Active | `https://frontend-bay-tau-86.vercel.app` |
| **Backend** | Render (Free Web Service) | **₹0** | Active | `https://cybershield-intel-backend.onrender.com` |
| **Relational DB** | Supabase (Free PostgreSQL 16) | **₹0** | Active | Project `pkobmgvudnibrkunhjmn` (Region: `ap-south-1`) |
| **Graph DB** | Neo4j Aura (AuraDB Free) | **₹0** | Active | Instance `c9d53e67` (`neo4j+s://c9d53e67.databases.neo4j.io`) |
| **Cache / Broker** | Built-in Python In-Memory | **₹0** | Active | No external Redis required; zero provisioning cost |
| **DNS / SSL** | Vercel & Render Automated TLS | **₹0** | Active | Fully managed Let's Encrypt / Cloudflare certificates |
| **Tunnels** | Removed (No Cloudflare/ngrok) | **₹0** | Inactive | Direct public HTTPS endpoints |

**Total Monthly Infrastructure Cost: ₹0 / month**

---

## 3. Free-Tier Characteristics & Transparent Limitations

In full compliance with SIH evaluation rules and engineering transparency:

1. **Render Free Web Service Sleep Behavior:**
   - **Spin-Down:** Render Free automatically spins down after **15 minutes** of HTTP inactivity.
   - **Cold Start:** The initial wake-up request after spin-down takes **45 to 70 seconds** while Render spins up the container.
   - **UX Handling:** The frontend displays animated loading skeletons and informative status banners during initial wake-up. Subsequent interactions are sub-second.
   - **No Artificial Keep-Alive:** In compliance with hackathon integrity guidelines and Render ToS, no automated cron pings or uptime bots are deployed.

2. **Supabase Free Tier Inactivity Pause:**
   - Supabase free tier databases pause after **7 days** of total inactivity. Unpausing is instantaneous with one click in the Supabase console without data loss.

3. **Neo4j Aura Free Tier Node & Memory Quotas:**
   - Free tier AuraDB instances support up to **200,000 nodes** and **400,000 relationships**.
   - The synthetic demonstration graph utilizes ~55,000 entities and relationships, operating well within 15% of free tier limits.

---

## 4. Environment Variables Configuration

Secrets are managed exclusively through provider dashboards and never committed to source code or git history.

### Render Backend Web Service (`cybershield-intel-backend`):

| Variable Name | Type | Purpose | Production Value / Pattern |
|---|---|---|---|
| `ENVIRONMENT` | Configuration | Enforces production mode and security guards | `production` |
| `DEBUG` | Configuration | Disables verbose debug logging and stack traces | `False` |
| `SYNTHETIC_DATA_ONLY` | Compliance | Enforces synthetic data mode and warning banners | `True` |
| `AUTO_SEED` | Database | Seeds default synthetic entities if database is empty | `true` |
| `PORT` | Managed | Assigned dynamically by Render | `10000` |
| `ALLOWED_CORS_ORIGINS` | Security | Whitelists production frontend domains | `["https://frontend-bay-tau-86.vercel.app","http://localhost:5173"]` |
| `DATABASE_URL` | Secret | Cloud PostgreSQL URI (pooler with SSL) | `postgresql://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:6543/postgres?sslmode=require` |
| `PGSSLMODE` | Security | Enforces SSL encryption for PostgreSQL | `require` |
| `JWT_SECRET_KEY` | Secret | 64-character CSPRNG secret for JWT signing | `[REDACTED_64_CHAR_HEX]` |
| `JWT_ALGORITHM` | Security | Cryptographic algorithm for JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Security | Access token lifespan | `120` |
| `NEO4J_URI` | Secret | Encrypted Neo4j Aura connection endpoint | `neo4j+s://c9d53e67.databases.neo4j.io` |
| `NEO4J_USER` | Secret | Neo4j Aura username | `c9d53e67` |
| `NEO4J_PASSWORD` | Secret | Neo4j Aura instance password | `[REDACTED_AURA_PASSWORD]` |
| `REDIS_URL` | Optional | External Redis URL (empty string enables in-memory) | `""` |

### Vercel Frontend (`frontend`):

| Variable Name | Purpose | Production Value |
|---|---|---|
| `VITE_API_BASE_URL` | REST API target | `https://cybershield-intel-backend.onrender.com/api/v1` |
| `VITE_WS_ALERT_URL` | WebSocket target | `wss://cybershield-intel-backend.onrender.com/alerts/ws` |
| `VITE_APP_ENV` | Application mode | `SYNTHETIC_DEVELOPMENT` |

---

## 5. Database Migration & Setup Process

### PostgreSQL (Supabase Free) Setup:
1. Created Supabase project in Mumbai region (`ap-south-1`).
2. Configured SSL-enabled asyncpg connection string with connection pooler on port 6543.
3. Applied Alembic migrations against cloud PostgreSQL:
   ```bash
   alembic upgrade head
   ```
   - Migration `0001_initial_schema`: Core users, complaints, transactions, accounts, alerts, audit logs.
   - Migration `0002_case_management_workflow`: Case dockets, evidence items, notes, workflow history.
4. Seeded initial synthetic evaluation records:
   - Users: 4 evaluation roles (Investigator, Supervisor, Analyst, Admin)
   - Complaints: 26 synthetic NCRP complaints
   - Transactions: High-velocity synthetic financial transaction streams
   - Cases: `CASE-2024-001` (Operation Nightshade)

### Neo4j Aura Setup:
1. Provisioned Neo4j AuraDB Free tier instance `c9d53e67`.
2. Created 23 schema constraints and uniqueness indexes:
   ```cypher
   CREATE CONSTRAINT FOR (a:Account) REQUIRE a.account_number IS UNIQUE;
   CREATE CONSTRAINT FOR (u:UPI) REQUIRE u.vpa IS UNIQUE;
   CREATE CONSTRAINT FOR (d:Device) REQUIRE d.device_id IS UNIQUE;
   CREATE CONSTRAINT FOR (p:Phone) REQUIRE p.phone_number IS UNIQUE;
   CREATE CONSTRAINT FOR (c:Customer) REQUIRE c.customer_id IS UNIQUE;
   CREATE CONSTRAINT FOR (atm:ATM) REQUIRE atm.atm_id IS UNIQUE;
   ```
3. Ingested synthetic financial topology:
   - 10,000 Accounts, 12,500 UPI handles, 8,000 Devices, 7,500 Phones, 4,122 ATMs.
   - Money flow edges (`TRANSFERRED_TO`), shared device links (`USED_DEVICE`), and ATM cash-out relations (`WITHDREW_AT`).

---

## 6. Deployment Process

### Backend Deployment (Render Docker Web Service):
1. Connected GitHub repository `Basilisk1929/SIH` (branch `main`) to Render.
2. Runtime set to **Docker** targeting `docker/Dockerfile.backend`.
3. Entrypoint script (`docker/entrypoint.sh`):
   - Validates cloud environment variables.
   - Executes database readiness check.
   - Runs `alembic upgrade head` migrations over SSL.
   - Launches Uvicorn bound to `0.0.0.0:$PORT`.
4. Render automatically builds and deploys upon commits to `main`.

### Frontend Deployment (Vercel Free):
1. Connected GitHub repository `Basilisk1929/SIH` to Vercel.
2. Build command: `npm run build` (`tsc && vite build`).
3. Single-Page Application (SPA) routing handled via `frontend/vercel.json` rewrites.
4. Clean bundle verified: Zero references to `localhost`, `127.0.0.1`, `trycloudflare.com`, or `loca.lt`.

---

## 7. SIH Judge Evaluation & Demo Accounts

The platform includes **SIH Evaluation Mode** on the login page with one-click **Quick Demo Access**:

| Role | Email | Password | Privileges & Responsibilities |
|---|---|---|---|
| **Investigator** | `investigator.demo@cybershield.local` | `InvestigatorDemo@2024!` | Incident triage, live mule graph traversal, case management, ATM cash-out alerts |
| **Supervisor** | `supervisor.demo@cybershield.local` | `SupervisorDemo@2024!` | Case approval, audit oversight, team dispatch, emergency freeze orders |
| **Analyst** | `analyst.demo@cybershield.local` | `AnalystDemo@2024!` | Intelligence analytics, XGBoost ML risk models, geospatial hotspot heatmaps |
| **Admin** | `admin.demo@cybershield.local` | `AdminDemo@2024!` | Subsystem health telemetry, user RBAC administration, demo simulator control |

> **Quick Demo Access:** Clicking any role button automatically populates credentials and executes authentic OAuth2 authentication against `/api/v1/auth/login`, issuing a signed HS256 JWT bearer token.

---

## 8. Troubleshooting Guide

| Issue | Root Cause | Resolution |
|---|---|---|
| 502 / 504 on first request | Render Free container waking up from sleep | Allow 45-70 seconds for container spin-up. Subsequent requests respond in < 1 second. |
| CORS Error in browser console | Origin not present in `ALLOWED_CORS_ORIGINS` | Verify `ALLOWED_CORS_ORIGINS` in Render dashboard includes `https://frontend-bay-tau-86.vercel.app`. |
| Database connection timeout | Supabase project paused due to 7-day inactivity | Log in to Supabase dashboard and click "Restore" to unpause the project. |
| Neo4j authentication failure | Aura instance credentials changed or user mismatch | Ensure `NEO4J_USER` matches the Aura instance ID (e.g. `c9d53e67`) and `NEO4J_PASSWORD` is correct. |
| WebSocket connection fails | Protocol mismatch or missing token | Verify frontend connects via `wss://` with `?token=<jwt_access_token>`. |

---

## 9. Rollback & Backup Procedure

- **Git Backup Tag:** `v0.1.0-pre-render` is permanently preserved in the repository.
- To inspect or roll back to the pre-Render checkpoint:
  ```bash
  git checkout v0.1.0-pre-render
  ```
- **Local Development Recovery:** Local Docker containers and volumes remain intact and stopped (`docker compose stop`), preserving full local recovery without data loss.

---

## 10. Mac-Independence Test Verification

To certify that the production deployment operates completely independent of the developer's workstation:

1. **Local Services Shutdown Verified:**
   - 0 processes listening on `:8000`, `:5432`, `:7474`, `:7687`, `:6379`, `:5173`.
   - Docker daemon stopped; 0 active local containers.
   - 0 tunnel processes (`cloudflared`, `ngrok`, `localtunnel`).

2. **Cloud Stack Verification (Local Machine Offline):**
   - **Frontend:** Loaded from `https://frontend-bay-tau-86.vercel.app` on Vercel CDN.
   - **Health Probes:**
     - `/health` -> `HTTP 200` (`"status":"healthy"`)
     - `/api/v1/health/ready` -> `HTTP 200` (`"postgresql":"connected"`, `"neo4j":"connected"`, `"redis":"not_provisioned_using_in_memory"`)
   - **Authentication:** All 4 roles issued authentic signed JWT tokens.
   - **Intelligence Subsystems:**
     - Cases Docket: Loaded live from Supabase PostgreSQL.
     - Graph Subgraph: Loaded live from Neo4j Aura.
     - ML Risk Engine: XGBoost evaluated 85k INR transaction with 99.69% risk score.
     - NLP Entity Extraction: Extracted 4 cybercrime entities from text.
     - Geo / ATM Locator: Loaded RBI ATM registry and H3 cells.
     - WebSocket Stream: Connected to `wss://cybershield-intel-backend.onrender.com/alerts/ws` with Ping/Pong roundtrip.
     - Demo Simulator: `POST /api/v1/demo/simulate-fraud` executed full cross-subsystem pipeline.

**Mac-Independence Status: PASS**
