# Vercel Deployment Architecture & Guide
**CyberShield-Intel / SIH Law Enforcement Investigation Dashboard**

This guide documents the procedures for deploying the React + TypeScript frontend to Vercel and connecting it to the production FastAPI backend.

---

## 1. Vercel Project Creation

1. Sign in to your [Vercel Dashboard](https://vercel.com).
2. Click **"Add New..."** > **"Project"**.
3. Import the repository: `Basilisk1929/SIH` (or your organizational repository clone).
4. Select the project type as **Vite / React**.

---

## 2. Root Directory Configuration

In the Vercel project import settings:
- **Root Directory**: `frontend`
- Click **"Save"** or ensure the toggle for "Include source files outside the Root Directory" is enabled if monorepo references are needed.

---

## 3. Build & Output Configuration

Vercel automatically detects Vite framework presets:

| Setting | Value | Notes |
|---|---|---|
| **Framework Preset** | `Vite` | Auto-detected |
| **Build Command** | `npm run build` | Runs `tsc && vite build` |
| **Output Directory** | `dist` | Generated static bundle assets |
| **Install Command** | `npm install` | Clean dependency resolution |
| **Node.js Version** | `18.x` or `20.x` | Modern LTS runtime |

---

## 4. Single-Page Application (SPA) Routing & Fallback

Client-side routes (`/alerts/:id`, `/cases/:id`, `/accounts/:id`, `/graph`, `/map`, etc.) require rewriting requests to `/index.html` to avoid 404 errors on direct browser refreshes.

The project contains `frontend/vercel.json`:
```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```
This guarantees that all client routes resolve to `index.html` where `react-router-dom` handles route transitions.

---

## 5. Required Environment Variables

Configure the following environment variables in the Vercel Project Settings under **Environment Variables**:

| Variable Name | Environment | Example Value | Description |
|---|---|---|---|
| `VITE_API_BASE_URL` | Production / Preview | `https://api.cybershield.gov.in/api/v1` | Public HTTPS URL of the FastAPI backend router |
| `VITE_WS_ALERT_URL` | Production / Preview | `wss://api.cybershield.gov.in/alerts/ws` | Secure WSS endpoint for real-time alerts |
| `VITE_APP_ENV` | Production | `PRODUCTION` | Environment display indicator |

> [!IMPORTANT]
> - Never hardcode `http://localhost` or `http://127.0.0.1` into components.
> - Do NOT commit backend secrets (`JWT_SECRET_KEY`, database credentials) to the frontend repository or environment.
> - Only variables prefixed with `VITE_` are bundled into client-side browser code.

---

## 6. Backend CORS Configuration

For the Vercel frontend to communicate with the FastAPI backend without browser CORS violations:

In `.env` or cloud container environment settings (via `ALLOWED_CORS_ORIGINS`):
```bash
ALLOWED_CORS_ORIGINS=["https://cybershield-intel.vercel.app","http://localhost:5173"]
# Or comma-delimited:
ALLOWED_CORS_ORIGINS=https://cybershield-intel.vercel.app,http://localhost:5173
```

> [!WARNING]
> Do NOT use `*` as a CORS origin in production. The backend rejects wildcard origins when running in `ENVIRONMENT=production`.

Ensure the backend responds with appropriate `Access-Control-Allow-Origin`, `Access-Control-Allow-Credentials: true`, and supports preflight `OPTIONS` requests for `Authorization`, `Content-Type`, and rate limit headers.

---

## 7. WebSocket / SSE Considerations

1. **Protocol Security**:
   - Vercel serves the application over **HTTPS**.
   - Browsers block unencrypted `ws://` connections from an HTTPS origin due to Mixed Content policies.
   - Therefore, `VITE_WS_ALERT_URL` in production MUST use the `wss://` protocol (e.g. `wss://api.cybershield.gov.in/alerts/ws`).

2. **Connection Recovery**:
   - `useAlertStream.ts` implements automatic exponential backoff reconnection (1s -> 2s -> 4s -> max 10s) with deduplication so network interruptions do not crash the investigation workspace.

---

## 8. Production API URL & Reverse Proxy Option

### Option A: Direct Backend Hosting (Recommended for SIH)
Point `VITE_API_BASE_URL` directly to the hosted FastAPI URL:
```bash
VITE_API_BASE_URL=https://cybershield-api.onrender.com/api/v1
```

### Option B: Vercel Path Proxy
You can route `/api/v1/(.*)` through `vercel.json` rewrites to avoid any cross-origin CORS negotiation:
```json
{
  "rewrites": [
    {
      "source": "/api/v1/(.*)",
      "destination": "https://api.cybershield.gov.in/api/v1/$1"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

---

## 9. Custom Domain Configuration (Optional)

1. Navigate to **Project Settings** > **Domains**.
2. Add your custom institutional domain (e.g. `intel.cybercell.gov.in` or `cybershield.in`).
3. Add the DNS `CNAME` or `A` records provided by Vercel to your DNS registrar.
4. Vercel automatically provisions and renews Let's Encrypt SSL/TLS certificates.

---

## 10. Deployment Verification Checklist

After deploying to Vercel, verify:

- [ ] Production build succeeds without TypeScript or Vite errors.
- [ ] Visiting root `/` redirects to `/login` for unauthenticated sessions.
- [ ] Login screen authenticates with backend and stores JWT in session storage.
- [ ] Navigation to `/dashboard`, `/alerts`, `/cases`, `/transactions`, `/complaints`, `/graph`, and `/map` works smoothly.
- [ ] Direct page refresh on `/alerts/ALT-1001` or `/cases/CASE-2024-001` loads without 404s (verifying `vercel.json` SPA rewrite).
- [ ] WebSocket connection status indicator displays green (`WS LIVE`).
- [ ] Phase 11C Cash-Out Prediction Card loads candidate ATMs and displays statutory disclaimer.
- [ ] Browser console has zero CORS errors and zero unhandled Promise rejections.
- [ ] Logging out cleanly clears token and returns to `/login`.
