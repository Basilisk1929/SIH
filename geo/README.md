# Geospatial Intelligence Module

## Overview
The Geospatial Intelligence subsystem provides tactical location-based cybercrime risk detection, discrete global grid indexing, density-based hotspot clustering, and cashout corridor proximity analysis for financial transactions and citizen complaint reports across the Republic of India.

```
Incoming Georeferenced Event (Txn / Complaint / ATM)
                        │
                        ▼
            [Coordinate Validator] ──> Global/Indian bounds & inverted coord correction
                        │
                        ▼
               [H3 Spatial Indexer] ──> Res 7/8 Discrete Global Grid (Hexagons)
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
[Transaction Agg]  [Complaint Agg]  [ATM Proximity (BallTree)]
 (volume, fraud)     (losses, scams)    (RBI Banking Outlets)
       │                │                │
       └────────────────┼────────────────┘
                        │
                        ▼
       [DBSCAN Geodesic Hotspot Detector] ──> Haversine spatial clusters & convex hulls
                        │
                        ▼
             [Temporal Analyzer] ──> Time-of-day (nocturnal burst) & Day-of-week
                        │
                        ▼
            [Unified Spatial Risk Engine] ──> 0-100 score, risk bands, nearest ATMs
                        │
                        ▼
           [RFC 7946 GeoJSON Exporter] ──> Leaflet, Mapbox, QGIS, Kepler.gl
```

---

## 1. Core Capabilities

### 1. Coordinate Validation (`geo.validation.CoordinateValidator`)
- **Global & Indian Bounding Boxes**: Validates coordinate ranges (Lat: $6.55^{\circ}\text{N}$ to $37.10^{\circ}\text{N}$, Lng: $68.11^{\circ}\text{E}$ to $97.40^{\circ}\text{E}$).
- **Inverted Coordinate Detection & Auto-Swap**: Automatically detects and rectifies swapped `(lng, lat)` inputs commonly introduced by external feeds.
- **Batch Validation**: Validates pandas DataFrames into clean records and rejected records with explicit rejection reasons.

### 2. Uber H3 Hexagonal Grid Indexing (`geo.indexing.H3Indexer`)
- **Discrete Global Grid System**: Indexes continuous spherical coordinates into discrete hexagonal cells without latitude-distortion artifacts.
- **Configurable Resolutions**:
  - `Resolution 8`: ~460m edge length, ~0.74 km² area (urban neighborhood/ward level).
  - `Resolution 7` (Default): ~1.22 km edge length, ~5.16 km² area (police station / commercial sector level).
  - `Resolution 6`: ~3.23 km edge length, ~36.1 km² area (sub-district / taluk level).
  - `Resolution 5`: ~8.54 km edge length, ~252.9 km² area (district level).
- **Topology Operations**: Centroids, 6-vertex boundaries, $k$-ring neighbors (`grid_disk`), grid distances, parent/children hierarchical zoom.

### 3. Transaction & Complaint Aggregation (`geo.aggregation.H3CellAggregator`)
- **Transactions by Cell**: `transaction_count`, `fraud_count`, `fraud_ratio`, `total_transaction_amount`, `avg_transaction_amount`, `unique_senders`, `unique_receivers`.
- **Complaints by Cell**: `complaint_count`, `total_complaint_loss`, `avg_complaint_loss`, `dominant_scam_type`.
- **Spatial Risk Scoring (0–100)**: Combines fraud ratio (30%), fraud volume (20%), complaint loss density (25%), DBSCAN cluster membership (15%), and proximity to known reference cybercrime hubs (10%).
- **Risk Bands**: `LOW` (0–29.99), `MEDIUM` (30–59.99), `HIGH` (60–84.99), `CRITICAL` (85–100).

### 4. RBI ATM & Bank Outlets Registry (`geo.datasets.RBIAtmRegistry`)
- Comprehensive coverage of real Indian banking geography across:
  - **Public Sector Banks**: State Bank of India, Punjab National Bank, Bank of Baroda, Canara Bank, Union Bank of India.
  - **Private Sector Banks**: HDFC Bank, ICICI Bank, Axis Bank, Kotak Mahindra Bank, IndusInd Bank.
  - **Small Finance Banks**: AU Small Finance Bank, Equitas SFB.
  - **White-Label ATM Operators (WLA)**: Tata Indicash, India1 Payments.
- **Outlet Typologies**: `ON_SITE_ATM`, `OFF_SITE_ATM`, `CASH_RECYCLER` (CRM), `BANK_BRANCH`, `WHITE_LABEL_ATM`.
- **Population Categories**: `METROPOLITAN`, `URBAN`, `SEMI_URBAN`, `RURAL`.

### 5. ATM Proximity Analysis (`geo.proximity.ATMProximityAnalyzer`)
- **Fast Spatial Tree Index**: Uses `sklearn.neighbors.BallTree` with the `haversine` metric over radians for sub-millisecond nearest ATM queries.
- **Proximity Risk Modifiers**: Computes spatial cashout risk based on walking distance to nearest ATM (<300m), transaction cashout flags, and nocturnal timing.

### 6. Geodesic DBSCAN Hotspot Detection (`geo.clustering.DBSCANHotspotDetector`)
- **Great-Circle Distance Density Clustering**: Clusters incident points on the earth's surface using Haversine DBSCAN without planar projection distortions.
- **Noise Classification**: Dispersed incidents are flagged as noise (`cluster_id = -1`).
- **Cluster Summaries**: Automatically generates cluster centroids, radii, total financial losses, dominant scam typologies, and Shapely convex hull polygon geometries.
- **Reference Hub Alignment**: Automatically maps clusters to known Indian cybercrime regions (Jamtara, Mewat-Nuh, Bharatpur-Alwar, Cyberabad, Noida Sector-62, Bidhannagar Salt Lake).

### 7. Diachronic Temporal Analysis (`geo.temporal.TemporalAnalyzer`)
- **Time-of-Day (24h) Profiling**:
  - `NOCTURNAL` (23:00–05:00): Flags nocturnal cashout bursts indicative of mule withdrawal rings.
  - `MORNING` (05:00–11:00) / `BUSINESS_HOURS` (11:00–17:00) / `EVENING` (17:00–23:00).
- **Day-of-Week Profiling**: Monday through Sunday distribution, weekend surge ratio (targeting bank closure windows).

### 8. Chicago Crime Validation Benchmark (`geo.datasets.validation.ChicagoCrimeValidationBenchmark`)
- **Methodology & Algorithm Validation**: An open benchmark dataset from the City of Chicago portal used exclusively to validate H3 indexing, DBSCAN clustering, and point pattern algorithms.
- **Strict Isolation**: Explicitly metadata-tagged (`is_methodology_validation = True`, `is_indian_cybercrime = False`) and forbidden from contaminating Indian cybercrime operational workflows.

---

## 2. Visualizable RFC 7946 GeoJSON Output

The module exports RFC 7946 compliant GeoJSON (`[longitude, latitude]` coordinate ordering) directly viewable in map renderers:

- **H3 Hexagonal Polygons (`GET /geo/geojson/h3-cells`)**: Polygons with 7 closed vertices and properties containing risk scores, counts, and nearest ATMs.
- **Hotspot Clusters (`GET /geo/geojson/hotspots`)**: Centroid Points and Convex Hull Polygons for active DBSCAN clusters.
- **RBI ATM Network (`GET /geo/geojson/atms`)**: Points representing banking outlets and cash recyclers.

---

### 9. Cash-Out Location Prediction Subsystem (`geo.prediction`)
- **Predictive Ranking Engine**: Given a suspicious mule account and its recent transaction history, ranks nearby operational RBI ATM outlets by predicted likelihood of being a future physical cash-out destination.
- **5-Stage Decision Support Pipeline**:
  1. *Anchor Resolution & Candidate Generation*: Resolves geographic center of activity (explicit GPS coordinates, latest georeferenced transaction, or transaction centroid) and queries candidate operational ATMs within a configurable radius ($1$ to $50$ km, default $15$ km).
  2. *Strict Spatial Filtering*: Enforces Indian territorial bounds via `CoordinateValidator(require_india=True)`, operational status (`is_operational == True`), and active cash dispensing (`cash_dispenser_active == True`).
  3. *Multi-Dimensional Feature Engineering*:
     - Haversine distance decay from recent account activity ($\lambda = 2.5$ km).
     - Proximity to prior known cash-out locations in account history.
     - Spatial cybercrime risk of the ATM's H3 cell ($0$–$100$).
     - Local cash-out frequency and DBSCAN cybercrime corridor proximity (`is_hotspot_adjacent`).
     - Outlet infrastructure suitability (Cash Recyclers [CRMs] / 24/7 Off-Site ATMs vs branch counters).
     - Time-of-day nocturnal fit and weekend closure surge patterns.
     - Urgent transaction burst multiplier ($>4$ txns/1h, cashout ratio $>0.7$).
  4. *Calibrated Scoring & Monotonic Ranking*: Generates normalized prediction scores in $[5.0, 98.5]$ and assigns strict 1-indexed relative priority ranks.
  5. *Natural Language Explanation Generation*: Emits evidentiary, human-readable tactical bullet points explaining the ranking of each ATM.

---

## 2. Visualizable RFC 7946 GeoJSON Output

The module exports RFC 7946 compliant GeoJSON (`[longitude, latitude]` coordinate ordering) directly viewable in map renderers:

- **H3 Hexagonal Polygons (`GET /geo/geojson/h3-cells`)**: Polygons with 7 closed vertices and properties containing risk scores, counts, and nearest ATMs.
- **Hotspot Clusters (`GET /geo/geojson/hotspots`)**: Centroid Points and Convex Hull Polygons for active DBSCAN clusters.
- **RBI ATM Network (`GET /geo/geojson/atms`)**: Points representing banking outlets and cash recyclers.

---

## 3. REST API Specification

Start the standalone geospatial microservice:
```bash
uvicorn geo.api.service:app --host 127.0.0.1 --port 8005
```

### Endpoints

#### 1. `POST /geo/cell-analysis`
Analyzes cyber risk, fraud volume, and nearest ATMs for an H3 cell.

#### 2. `POST /geo/coordinate-analysis`
Accepts `latitude`, `longitude`, and optional `resolution`, converts to H3 cell and returns the spatial risk analysis.

#### 3. `GET /geo/nearest-atms?lat=28.6315&lng=77.2167&top_k=5`
Returns nearest RBI banking outlets and ATMs with exact geodesic distances.

#### 4. `GET /geo/hotspots`
Returns all active DBSCAN spatial clusters, centroids, radii, and loss totals.

#### 5. `GET /geo/temporal`
Returns 24-hour and day-of-week breakdown and flags nocturnal or weekend surges.

#### 6. `GET /geo/geojson/h3-cells?min_risk_score=30.0`
Returns visualizable GeoJSON FeatureCollection of hexagonal risk cells.

#### 7. `GET /geo/validation/chicago-benchmark`
Executes spatial algorithm methodology verification on the Chicago validation benchmark.

#### 8. `POST /geo/predict-cashout-location`
Predicts and ranks candidate RBI ATMs for an investigated account.

**Request:**
```json
{
  "account_id": "SYN1000004465",
  "current_latitude": 28.6280,
  "current_longitude": 77.3649,
  "candidate_radius_km": 10.0,
  "top_k": 3,
  "account_risk_score": 92.0,
  "cashout_ratio": 0.94,
  "transactions_last_1h": 8
}
```

**Response:**
```json
{
  "account_id": "SYN1000004465",
  "prediction_timestamp": "2026-09-26T13:45:00+00:00",
  "anchor_location": {
    "latitude": 28.628,
    "longitude": 77.3649,
    "source": "explicit_current_location"
  },
  "candidate_radius_km": 10.0,
  "total_candidates_evaluated": 16,
  "predicted_atms": [
    {
      "atm_id": "RBI_OUTLET_000099",
      "bank_name": "State Bank of India",
      "latitude": 28.6289,
      "longitude": 77.3655,
      "distance_km": 0.12,
      "prediction_score": 88.6,
      "rank": 1,
      "explanations": [
        "Close to recent account activity (0.1 km)",
        "Elevated cash-out activity in H3 cell 873da1146ffffff (Risk score: 85.0)",
        "Located in known cybercrime surveillance corridor (Noida Sector-62)",
        "High-throughput 24/7 cash recycler (CRM) with elevated withdrawal limits",
        "Current transaction burst (8 txns in last 1h) indicates urgent cash-out dissipation"
      ],
      "outlet_type": "CASH_RECYCLER",
      "city": "Noida Sector-62",
      "district": "Gautam Buddha Nagar",
      "state": "Uttar Pradesh"
    }
  ],
  "urgency_level": "CRITICAL",
  "disclaimer": "DISCLAIMER & DATA LIMITATION: This cash-out location prediction model is an investigative prototype evaluated on synthetic financial transactions and Reserve Bank of India (RBI) ATM outlet registries. PaySim and synthetic transaction benchmarks do not contain genuine Indian ATM-level destination identifiers. Predictions represent tactical likelihood ranking based on spatial proximity, H3 cybercrime cell risk, outlet accessibility, and transaction velocity. It must NOT be claimed that this prediction identifies the actual ATM used for criminal cash withdrawal."
}
```

#### 9. `GET /geo/prediction/linkage-metadata`
Retrieves explicit dataset limitation notice confirming synthetic PaySim-RBI linkage and prototype status.

---

## 4. Statutory & Evidentiary Disclaimer

> [!IMPORTANT]
> **Evidentiary Notice**:
> *"Do not claim that a geospatial risk score or hotspot cluster proves criminal activity. It represents a model-generated spatial risk signal for tactical intelligence and investigation."*

> [!WARNING]
> **Dataset Limitation Notice**:
> *PaySim and open fraud datasets do NOT provide genuine Indian ATM-level destination data. This system utilizes a transparent, clearly labelled synthetic linkage between synthetic cash-out transaction events and real operational RBI ATM outlets. Predictions represent tactical likelihood prioritization and must NEVER be claimed as proof that a suspect withdrew funds from a specific physical ATM.*

---

## 5. Automated Verification & Test Coverage

Run all geospatial unit and integration tests:
```bash
pytest tests/geo/ -v
```
All **57 geospatial tests** pass in ~1.2s, with **216 tests passing monorepo-wide** (100% pass rate).
