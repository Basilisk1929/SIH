# CyberShield-Intel: Public Deployment Operations Guide
**Smart India Hackathon (SIH 2024) Public Deployment Specifications**

---

## 1. Verified Public Deployment URLs

- **Public Frontend (Vercel):**  
  [https://frontend-bay-tau-86.vercel.app](https://frontend-bay-tau-86.vercel.app)
  *(Preview alias: `https://frontend-gdclpz34g-me-cb7b.vercel.app`)*

- **Public Backend (Cloudflare Edge Gateway):**  
  [https://dimension-scholar-mainly-focusing.trycloudflare.com](https://dimension-scholar-mainly-focusing.trycloudflare.com)

- **API Base Prefix:**  
  `https://dimension-scholar-mainly-focusing.trycloudflare.com/api/v1`

- **Real-Time WebSocket Stream:**  
  `wss://dimension-scholar-mainly-focusing.trycloudflare.com/alerts/ws`

---

## 2. Hosting Platforms & Infrastructure Providers

| Tier | Hosting Provider | Deployment Mechanism | Operational Role |
|---|---|---|---|
| **Frontend** | Vercel | Git / Vercel CLI Edge Static Hosting | React 18 SPA with client-side routing rewrites |
| **Ingress Gateway** | Cloudflare | Global Edge Network / Tunnel Ingress | SSL/TLS 1.3 termination, DDoS protection, WSS proxy |
| **Backend Engine** | Docker Compose / Cloud Container | Python 3.12 / Uvicorn ASGI Container | FastAPI Core, REST APIs, ML/NLP/Geo pipelines |
| **Relational Database** | Managed PostgreSQL 16 | Dockerized Alpine Container | Relational tables, Alembic migrations, audit logs |
| **Graph Database** | Neo4j 5.18 Community / Aura | Bolt Protocol Docker Container | Multi-hop mule ring analysis, Cypher graph traversal |
| **In-Memory Cache** | Redis 7.2 | Alpine Container | Token invalidation store, real-time alert broadcasts |

---

## 3. Required Environment Variables

### 3.1 Frontend Build Environment (Vercel)
Configured under Vercel Project Settings > Environment Variables:

| Variable | Target | Example / Production Value | Description |
|---|---|---|---|
| `VITE_API_BASE_URL` | Build / Runtime | `https://dimension-scholar-mainly-focusing.trycloudflare.com/api/v1` | Public HTTPS backend URL |
| `VITE_WS_ALERT_URL` | Build / Runtime | `wss://dimension-scholar-mainly-focusing.trycloudflare.com/alerts/ws` | Public WSS alert stream endpoint |
| `VITE_APP_ENV` | Build / Runtime | `PRODUCTION` | Indicator badge in UI |

> [!CAUTION]
> Under no circumstances should backend secrets (`JWT_SECRET_KEY`, database passwords, Neo4j credentials) be placed in `VITE_*` variables. `VITE_*` variables are statically bundled into browser JavaScript.

### 3.2 Backend Service Environment (FastAPI Container)

| Variable | Type | Production Setting | Description |
|---|---|---|---|
| `ENVIRONMENT` | string | `production` | Enables strict production guards |
| `DEBUG` | boolean | `False` | Disables verbose debug stacktraces |
| `ALLOWED_CORS_ORIGINS` | CSV / JSON | `["https://frontend-bay-tau-86.vercel.app"]` | Whitelisted frontend origins (no wildcards) |
| `JWT_SECRET_KEY` | string | *Platform secret* (min 32 chars) | Cryptographic signature key for JWT tokens |
| `JWT_ALGORITHM` | string | `HS256` | Cryptographic signature algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| integer | `60` | Token validity duration |
| `DATABASE_URL` | string | *Platform secret* | Async PostgreSQL connection string |
| `NEO4J_URI` | string | `bolt://neo4j:7687` | Neo4j Bolt protocol URI |
| `NEO4J_USER` | string | *Platform secret* | Neo4j username |
| `NEO4J_PASSWORD` | string | *Platform secret* | Neo4j password |
| `REDIS_URL` | string | `redis://redis:6379/0` | Redis caching & pub/sub broker URI |
| `SYNTHETIC_DATA_ONLY` | boolean | `True` | Statutory synthetic compliance guard |

---

## 4. Deployment Procedure

### 4.1 Backend & Persistence Deployment
1. Start core data stores and backend container:
   ```bash
   docker compose up -d postgres neo4j redis backend
   ```
2. Verify container health:
   ```bash
   docker compose ps
   ```
3. Run Alembic schema migrations:
   ```bash
   docker compose exec backend alembic upgrade head
   ```
4. Verify database constraints and Neo4j indexes:
   ```bash
   docker compose exec backend python -m graph.schema.constraints
   ```

### 4.2 Ingress Gateway Activation (Cloudflare)
Launch Cloudflare edge tunnel forwarding to port 8000:
```bash
cloudflared tunnel --url http://127.0.0.1:8000
```
Capture the generated `https://*.trycloudflare.com` URL.

### 4.3 Frontend Deployment to Vercel
1. Set public environment variables pointing to Cloudflare ingress:
   ```bash
   npx vercel deploy ./frontend --prod --yes --non-interactive \
     -b VITE_API_BASE_URL=https://dimension-scholar-mainly-focusing.trycloudflare.com/api/v1 \
     -b VITE_WS_ALERT_URL=wss://dimension-scholar-mainly-focusing.trycloudflare.com/alerts/ws
   ```
2. Vercel automatically runs `npm install`, `tsc && vite build`, and pushes the static assets to the Vercel Global Edge Network.

---

## 5. Rollback Procedure

- **Frontend Rollback:**
  In the Vercel Dashboard, select **Deployments** > locate the previous stable deployment ID > click **Instant Rollback**. Vercel will instantly repoint the production domain alias (`frontend-bay-tau-86.vercel.app`) without requiring a rebuild.
- **Backend Rollback:**
  If a new backend container image causes regressions, roll back using Docker Compose:
  ```bash
  docker compose down
  git checkout <previous-stable-tag>
  docker compose up -d
  ```

---

## 6. Health Checks & Monitoring

- **Public Backend Health Check:**
  ```bash
  curl -s https://dimension-scholar-mainly-focusing.trycloudflare.com/health
  # Expected Response:
  # {"status":"healthy","app":"CyberShield-Intel","version":"0.1.0","mode":"SYNTHETIC_DEVELOPMENT","timestamp_compliance":"Synthetic data mode enforced"}
  ```
- **Local Backend Health Check:**
  ```bash
  curl -s http://127.0.0.1:8000/api/v1/health
  ```
- **Database Readiness:**
  ```bash
  docker compose exec postgres pg_isready -U cyber_admin -d cyber_intelligence_db
  ```
- **Neo4j Graph Readiness:**
  ```bash
  curl -s http://localhost:7474
  ```

---

## 7. CORS & WebSocket Configuration

### 7.1 CORS Configuration
In [`backend/app/main.py`](file:///Users/ronitsingh/Anti/SIH/backend/app/main.py):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_CORS_ORIGINS,
    allow_origin_regex=r"^https:\/\/([a-zA-Z0-9_-]+\.)?vercel\.app$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-Forwarded-For",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "bypass-tunnel-reminder",
    ],
)
```

### 7.2 WebSocket / WSS Configuration
In [`frontend/src/hooks/useAlertStream.ts`](file:///Users/ronitsingh/Anti/SIH/frontend/src/hooks/useAlertStream.ts):
- WebSockets are served over secure `wss://` protocol to comply with browser Mixed Content policies.
- Automatically handles reconnection with exponential backoff if the network drops.
- Authenticates using standard JWT token query parameters (`/alerts/ws?token=<jwt>`).

---

## 8. Known Limitations & Recommendations

1. **Quick Cloudflare Ingress Tunnel Lifetime:**
   The ephemeral quick tunnel (`trycloudflare.com`) is suitable for evaluation sessions and hackathon demos. For enterprise 24/7 cloud deployments, a named Cloudflare Tunnel (`cloudflared tunnel run <named-tunnel>`) or AWS ALB with a permanent domain (e.g. `api.cybershield.gov.in`) should be provisioned.
2. **Ephemeral In-Memory Rate Limiter Fallback:**
   If Redis becomes unreachable, the backend automatically degrades gracefully to an in-process sliding-window rate limiter without throwing unhandled exceptions.
