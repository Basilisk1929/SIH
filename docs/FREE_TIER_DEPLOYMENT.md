# CyberShield-Intel — ₹0 Free-Tier Public Deployment Architecture

> **Smart India Hackathon (SIH) Evaluation Platform**  
> Public Demonstration Environment — Synthetic Data Only  
> Total Monthly Infrastructure Cost: **₹0 / month**

---

## 1. System Architecture Overview

```
                                 INTERNET / SIH JUDGE
                                          |
                                          v
                    +--------------------------------------------+
                    |           Vercel (Hobby / Free)            |
                    |         React 18 + Vite Frontend           |
                    |   https://frontend-bay-tau-86.vercel.app   |
                    +---------------------+----------------------+
                                          |
                        HTTPS (REST) / WSS (WebSockets)
                                          |
                                          v
                    +--------------------------------------------+
                    |        Render Free Web Service             |
                    |      FastAPI Modular Engine (Python 3.12)  |
                    |    https://<render-service>.onrender.com    |
                    +------------------+-------------------------+
                                       |
                   +-------------------+-------------------+
                   |                                       |
                   v                                       v
+------------------------------------+  +------------------------------------+
|       Supabase PostgreSQL          |  |          Neo4j Aura Free           |
|        (Free Cloud Tier)           |  |        (Free Cloud Instance)       |
|  - PostgreSQL 16 + AsyncPG (SSL)   |  |  - AuraDB Free Tier (200k nodes)   |
|  - Cases, Alerts, Complaints       |  |  - Mule Account Network Topology   |
|  - Financial Transactions, Audit   |  |  - Smurfing & Layering Traversal   |
+------------------------------------+  +------------------------------------+
```

### Critical Zero-Cost Guarantees:
- **No Paid Render Services**: Uses the Render Free Web Service (512MB RAM, dynamic port binding).
- **No Expiring Render PostgreSQL**: Render's free PostgreSQL expires after 30 days. We use **Supabase Free PostgreSQL** which has no 30-day automatic deletion timer.
- **No Paid Neo4j**: Uses Neo4j AuraDB Free tier (sufficient for SIH synthetic mule graphs).
- **No Redis Required**: All token revocation, rate limiting, and alert broadcasting operate via robust in-memory structures with graceful fallbacks.
- **No Paid Domains / SSL**: Managed wildcard certificates provided by Vercel and Render at ₹0.
- **No MacBook Dependency**: The entire stack runs in independent cloud infrastructure. No local Docker, no local FastAPI, and no local tunnels (ngrok/Cloudflare/LocalTunnel).

---

## 2. Infrastructure Inventory & Free Tier Specifications

| Component | Provider & Tier | Specifications & Free Limits | Cost |
|---|---|---|---|
| **Frontend** | Vercel (Hobby Free) | Global Edge CDN, automated deployments from GitHub, custom rewrites | **₹0** |
| **Backend** | Render Free Web Service | 512MB RAM, 0.1 CPU, spins down after 15 min inactivity, auto-wakes on request | **₹0** |
| **Relational DB** | Supabase Free | 500MB PostgreSQL 16 database, SSL connection pooling, direct connection | **₹0** |
| **Graph DB** | Neo4j AuraDB Free | 1 free instance, 200,000 nodes, 400,000 relationships, `neo4j+s://` TLS | **₹0** |
| **In-Memory Cache** | In-Memory (Built-in) | Python process in-memory sliding window limiter & revoked token set | **₹0** |

---

## 3. Required Environment Variables

All secrets and credentials must be set exclusively via provider dashboard configuration and never committed to source control.

### Render Backend Web Service Environment Variables:

| Variable Name | Required / Optional | Purpose | Recommended Value |
|---|---|---|---|
| `ENVIRONMENT` | Required | Enforces production security checks | `production` |
| `DEBUG` | Required | Suppresses internal error traces | `False` |
| `SYNTHETIC_DATA_ONLY` | Required | Compliance banner and synthetic guard | `True` |
| `AUTO_SEED` | Required | Automatically populates DB if empty | `true` |
| `PORT` | Managed | Render assigns this dynamically (default 8000) | `10000` (Render default) |
| `ALLOWED_CORS_ORIGINS` | Required | Whitelisted frontend origins | `["https://frontend-bay-tau-86.vercel.app","http://localhost:5173"]` |
| `DATABASE_URL` | Required | Supabase PostgreSQL asyncpg connection string | `postgresql://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:6543/postgres?sslmode=require` |
| `JWT_SECRET_KEY` | Required | Cryptographic secret for signing auth tokens | 64-char random hex string |
| `JWT_ALGORITHM` | Required | JWT signature algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Required | Session duration | `120` |
| `NEO4J_URI` | Required | Neo4j Aura encrypted connection URI | `neo4j+s://[instance-id].databases.neo4j.io` |
| `NEO4J_USER` | Required | Neo4j Aura username | `neo4j` |
| `NEO4J_PASSWORD` | Required | Neo4j Aura password | *(Aura instance password)* |
| `REDIS_URL` | Optional | Redis connection (empty = in-memory mode) | `""` |
| `PGSSLMODE` | Optional | Enforces SSL mode for PostgreSQL | `require` |

### Vercel Frontend Environment Variables:

| Variable Name | Required / Optional | Purpose | Value |
|---|---|---|---|
| `VITE_API_BASE_URL` | Required | Target Render backend REST API | `https://<render-service-name>.onrender.com/api/v1` |
| `VITE_WS_ALERT_URL` | Required | Target Render backend WebSocket | `wss://<render-service-name>.onrender.com/alerts/ws` |

---

## 4. Setup & Deployment Procedure

### Step 1: Provision Supabase Free PostgreSQL
1. Sign in to [Supabase](https://supabase.com/dashboard).
2. Click **New Project**, choose a region close to your target audience (e.g., `ap-south-1` Mumbai or `us-west-1` Oregon).
3. Set a strong database password and keep it safe.
4. Navigate to **Project Settings** → **Database** → **Connection String** → **URI**.
5. Copy the connection string. It will look like:
   ```
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```
   *(Note: The platform's connection handler automatically translates `postgres://` or `postgresql://` to `postgresql+asyncpg://` and enables SSL).*

### Step 2: Provision Neo4j AuraDB Free
1. Sign in to [Neo4j Aura Console](https://console.neo4j.io/).
2. Click **Create Instance** and select **AuraDB Free**.
3. Download the generated credentials file immediately (`credentials-[instance].txt`).
4. Note your Connection URI:
   ```
   neo4j+s://[INSTANCE-ID].databases.neo4j.io
   ```
   Username is `neo4j`.

### Step 3: Deploy Backend on Render Free
1. Sign in to [Render Dashboard](https://dashboard.render.com/) with GitHub.
2. Click **New +** → **Web Service**.
3. Select GitHub repository `Basilisk1929/SIH` (branch `main`).
4. Set configurations:
   - **Name**: `cybershield-intel-backend`
   - **Runtime**: `Docker`
   - **Dockerfile Path**: `docker/Dockerfile.backend`
   - **Docker Context**: `.`
   - **Instance Type**: `Free`
5. Under **Environment Variables**, add the variables specified in Section 3 above.
6. Click **Deploy Web Service**.
7. The build will:
   - Compile Python dependencies (including spaCy, XGBoost, GeoPandas).
   - Download the spaCy `en_core_web_sm` model.
   - Run `docker/entrypoint.sh` which executes `alembic upgrade head` and seeds synthetic data if the database is unpopulated.

### Step 4: Update Vercel Frontend
1. Using the Vercel CLI or Dashboard:
   ```bash
   npx vercel env add VITE_API_BASE_URL production
   # Enter: https://<your-render-backend-url>/api/v1
   
   npx vercel env add VITE_WS_ALERT_URL production
   # Enter: wss://<your-render-backend-url>/alerts/ws
   
   npx vercel --prod
   ```
2. Verify production bundle does not contain any reference to `trycloudflare.com`, `loca.lt`, or `localhost`.

---

## 5. Free-Tier Characteristics & Cold-Start Behavior

### Render Free Web Service Spin-Down (Honest Transparency):
- **Sleep Behavior**: Render Free web services automatically spin down into a sleep state after **15 minutes** of HTTP inactivity.
- **Cold-Start Latency**: When an SIH judge accesses the site after inactivity, the first HTTP request wakes the container. This initial cold start takes approximately **45 to 70 seconds**.
- **User Experience Handling**: The frontend handles connection latencies with loading spinners, retry banners, and friendly status indicators. Subsequent requests respond in sub-second speeds.
- **No Artificial Keep-Alive**: In accordance with hackathon ethics and provider Terms of Service, no artificial ping bots, cron loops, or fake traffic generators are employed.

### Supabase Free Tier Auto-Pausing:
- Free projects are subject to pause after 7 days of inactivity. If paused, a single click in the Supabase dashboard unpauses the database within 60 seconds with zero data loss.

### Neo4j Aura Free Limits:
- Storage limit is capped at 200,000 nodes and 400,000 relationships. Synthetic seed datasets are strictly scoped to ~1,500 nodes and ~5,000 relationships, utilizing < 1% of the free allocation.

---

## 6. Authentication & SIH Judge Evaluation Mode

The platform includes **SIH Evaluation Mode** designed specifically for judging:

### Judge Credentials:
All demo accounts utilize securely hashed credentials with fine-grained Role-Based Access Control (RBAC):

| Role | Email | Password | Access Privileges |
|---|---|---|---|
| **Investigator** | `investigator.demo@cybershield.local` | `InvestigatorDemo@2026!` | Full investigation, mule graph visualizer, case filing, transaction tracing |
| **Supervisor** | `supervisor.demo@cybershield.local` | `SupervisorDemo@2026!` | Case approval, audit oversight, team dispatch, high-value freeze orders |
| **Analyst** | `analyst.demo@cybershield.local` | `AnalystDemo@2026!` | Intelligence analytics, ML risk assessment, geofence heatmaps |
| **Admin** | `admin.demo@cybershield.local` | `AdminDemo@2026!` | Full administrative control, subsystem health, platform telemetry |

### Quick Demo Access:
The login page provides one-click **"Quick Demo Access"** buttons for all four roles. These buttons execute real calls against `/api/v1/auth/login`, receive genuine signed JWT bearer tokens, and route directly to the role's authorized workspace.

---

## 7. Mandatory Mac-Independence Verification

To prove that the production deployment operates completely independent of the developer's workstation:

1. Terminate all local Docker containers:
   ```bash
   docker stop $(docker ps -q)
   ```
2. Verify no background tunnels or services are running:
   ```bash
   ps aux | grep -E "cloudflared|localtunnel|ngrok|uvicorn"
   ```
3. Open a private/incognito browser window on a mobile device or separate network.
4. Navigate to:
   ```
   https://frontend-bay-tau-86.vercel.app
   ```
5. Click **"Investigator"** Quick Demo Access.
6. Verify live graph traversal, transaction telemetry, alert engine, and case management respond directly from Render, Supabase, and Neo4j Aura.
