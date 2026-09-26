# Real-Time Alert Engine for Cybercrime Intelligence Platform

A high-throughput, low-latency alert generation and triage subsystem that consumes incoming financial transaction events, evaluates multi-dimensional risk factors in real time, suppresses duplicate alerts, broadcasts live updates via WebSockets and Server-Sent Events (SSE), and manages investigator triage lifecycles.

---

## 1. Architecture Overview

```
                      Transaction Event
                             │
                             ▼
               ┌───────────────────────────┐
               │  Alert Deduplicator       │ ◄── Window: 300s (configurable)
               │  - SHA-256 fingerprint    │
               │  - Duplicate counter      │
               └─────────────┬─────────────┘
                             │ (New / Non-duplicate)
                             ▼
               ┌───────────────────────────┐
               │  Alert Rule Evaluator     │
               │  1. ML Risk Score (0-100) │
               │  2. Transaction Velocity  │
               │  3. Graph Connections     │
               │  4. Rapid Cash-Out        │
               │  5. Geographic Anomalies  │
               │  6. Complaint Linkage     │
               └─────────────┬─────────────┘
                             │
                             ▼
               ┌───────────────────────────┐
               │  Severity Assignment      │
               │  LOW | MEDIUM | HIGH |    │
               │  CRITICAL                 │
               └─────────────┬─────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
   ┌──────────────────────┐      ┌──────────────────────┐
   │  Alert Broadcaster   │      │   In-Memory / DB     │
   │  - WebSocket /ws     │      │   Storage            │
   │  - SSE /sse          │      │   Lifecycle States   │
   └──────────────────────┘      └──────────────────────┘
```

---

## 2. Six-Factor Threat Dimension Evaluation

The `AlertRuleEvaluator` computes a weighted composite risk score (0 to 100) across six investigative vectors:

| Threat Factor | Evaluated Metrics | Severity Contribution |
| :--- | :--- | :--- |
| **1. ML Risk Score** | Model risk score (0–100), risk band (`HIGH`, `CRITICAL`), model explanations | 0.25 × ML Score (up to 25 pts) |
| **2. Transaction Velocity** | 1-hour burst count (`transactions_last_1h`), 24-hour frequency (`transactions_last_24h`) | Up to 25 pts (thresholds: 4, 8 tx/hr; 12, 25 tx/day) |
| **3. Suspicious Graph Connections** | Graph node degree, PageRank/betweenness centrality, counterparty fan-in (`unique_senders`) and fan-out (`unique_receivers`) | Up to 25 pts (thresholds: degree ≥ 12, 25; centrality ≥ 0.04) |
| **4. Rapid Cash-Out** | Cashout ratio (`cashout_ratio`), transaction type (`CASH_OUT`), pattern type (`RAPID_CASHOUT`), ATM drainage heuristics | Up to 30 pts (ratio ≥ 0.65, 0.85; cash-out ≥ ₹20,000) |
| **5. Geographic Anomalies** | Distance from account baseline (`geographic_distance` in km), georeference in known cybercrime hotspot cells (Nuh, Jamtara, Bharatpur, Alwar, etc.) | Up to 25 pts (dist ≥ 400 km, 1000 km; hotspot presence) |
| **6. Complaint Linkage** | Prior citizen cybercrime complaints (`complaint_link_count`), suspect phone / UPI handle linkage | Up to 40 pts (1 complaint: 25 pts; ≥2 complaints: 35–40 pts) |

### Severity Assignment Matrix
- **`CRITICAL`**: Composite score $\ge 85.0$, OR $\ge 2$ linked citizen complaints, OR rapid cashout ($\ge 85\%$) during transaction burst ($\ge 4$ tx/hr), OR ML risk score $\ge 90.0$.
- **`HIGH`**: Composite score $\ge 60.0$, OR 1 linked citizen complaint.
- **`MEDIUM`**: Composite score $\ge 30.0$.
- **`LOW`**: Composite score $< 30.0$.

---

## 3. Alert Deduplication Mechanism

To prevent notification storms when upstream payment rails re-deliver duplicate webhooks or when rapid identical payments occur, the `AlertDeduplicator` creates a cryptographic SHA-256 fingerprint:

$$\text{Fingerprint} = \text{SHA256}(\text{account\_id} \parallel \text{rule\_type} \parallel \text{amount\_bucket})$$

- **Time Window**: Configurable via `dedup_window_seconds` (default: **300 seconds** / 5 minutes).
- **Suppression**: If an identical event arrives within the active window:
  - No new alert is spawned.
  - The existing alert's `duplicate_count` is incremented.
  - The alert's `updated_at` timestamp is refreshed.
  - A `DEDUPLICATED` broadcast event is emitted to live listeners.
- **Window Expiration**: After 300 seconds without matches, old fingerprints expire, allowing subsequent events to trigger fresh alerts.

---

## 4. Alert Workflow & Lifecycle States

Alerts progress through a finite state machine:

```
           ┌───────────┐
     ┌───► │    NEW    │ ◄─── (Created)
     │     └─────┬─────┘
     │           │
     │           ▼
     │     ┌──────────────┐
     │     │ ACKNOWLEDGED │
     │     └─────┬────────┘
     │           │
     │           ▼
     │     ┌──────────────┐
     └──── │INVESTIGATING │ ◄──┐
           └─────┬────────┘    │
                 │             │
        ┌────────┴────────┐    │ (Reopened upon
        ▼                 ▼    │  new complaint)
  ┌───────────┐    ┌────────────────┐
  │ RESOLVED  │    │ FALSE_POSITIVE │
  └───────────┘    └────────────────┘
```

### Valid State Transitions
- `NEW` $\to$ `ACKNOWLEDGED`, `INVESTIGATING`, `FALSE_POSITIVE`
- `ACKNOWLEDGED` $\to$ `INVESTIGATING`, `RESOLVED`, `FALSE_POSITIVE`
- `INVESTIGATING` $\to$ `RESOLVED`, `FALSE_POSITIVE`, `ACKNOWLEDGED`
- `RESOLVED` $\to$ `INVESTIGATING` (reopening case upon new intelligence)
- `FALSE_POSITIVE` $\to$ `INVESTIGATING` (re-evaluating on new evidence)

---

## 5. Real-Time Streaming (WebSockets & SSE)

### WebSocket Endpoint: `ws://localhost:8000/alerts/ws`
- Connects live browser triage dashboards and operational war rooms.
- Bi-directional: supports heartbeats/pings (`{"type":"ping"}` $\to$ `{"type":"PONG"}`).
- Broadcasts:
  - `ALERT_CREATED`
  - `ALERT_DEDUPLICATED`
  - `ALERT_STATUS_UPDATED`

### Server-Sent Events (SSE) Endpoint: `http://localhost:8000/alerts/sse`
- Provides an HTTP-based unidirectional event stream (`text/event-stream`).
- Automatically handles connection handshake:
  ```json
  data: {"type": "CONNECTED", "message": "Subscribed to Golden-Hour alert feed"}
  ```
- Compatible with native browser `EventSource` and Python/Go/curl clients.

---

## 6. REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/alerts` | Ingest transaction event, run 6-factor evaluation, deduplicate, and create alert |
| `GET` | `/alerts` | Filter alerts by `severity`, `status`, `account_id` with pagination (`page`, `limit`) |
| `GET` | `/alerts/{id}` | Fetch alert details by UUID or business `alert_id` (e.g. `ALT-20260926-XXXX`) |
| `PATCH` | `/alerts/{id}/status` | Transition alert workflow status (`NEW`, `ACKNOWLEDGED`, `INVESTIGATING`, `RESOLVED`, `FALSE_POSITIVE`) |
| `GET` | `/alerts/stats` | Dashboard statistics: total alerts, breakdown by severity, status, and deduplications |
| `WS` | `/alerts/ws` | Live WebSocket feed for real-time dashboard updates |
| `GET` | `/alerts/sse` | Live Server-Sent Events HTTP stream |

*Note: All endpoints are accessible both at root `/alerts` and under `/api/v1/alerts`.*

### Example: Create Alert (`POST /alerts`)
```bash
curl -X POST "http://localhost:8000/alerts" \
  -H "Content-Type: application/json" \
  -d '{
    "event": {
      "transaction_id": "TXN_CYBER_889102",
      "account_id": "MULE_ACCT_881920",
      "amount": 95000.0,
      "transaction_type": "CASH_OUT",
      "pattern_type": "RAPID_CASHOUT",
      "ml_risk_score": 92.5,
      "transactions_last_1h": 6,
      "transactions_last_24h": 22,
      "graph_degree": 28,
      "graph_centrality": 0.052,
      "cashout_ratio": 0.94,
      "geographic_distance": 1250.0,
      "is_hotspot_location": true,
      "location_name": "Bharatpur, Rajasthan",
      "complaint_link_count": 2,
      "suspect_phone": "+919876543210"
    }
  }'
```

### Example: Update Alert Status (`PATCH /alerts/{id}/status`)
```bash
curl -X PATCH "http://localhost:8000/alerts/ALT-20260926-B101E980/status" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "INVESTIGATING",
    "investigator_id": "INV_OFFICER_402",
    "resolution_notes": "Freezing debit freeze request dispatched to bank nodal officer under Sec 91 CrPC."
  }'
```

---

## 7. Rate Limiting & Structured Logging

- **Sliding-Window Rate Limiting**: Client IP-based rate limiting (`InMemoryRateLimiter`) with configurable requests per minute (default: 120 req/min). Returns HTTP 429 (`Too Many Requests`) with `Retry-After` header when exceeded.
- **Structured Logging**: Every alert creation, deduplication hit, and status transition logs structured forensic metadata with token/secret masking.

---

## 8. Compliance & Legal Notice

> **IMPORTANT**:
> Do not claim that an alert proves criminal activity. It represents a model-generated risk signal for tactical intelligence, cybercrime investigation, and rapid golden-hour response.
