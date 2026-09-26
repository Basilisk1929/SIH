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

## 3. REST API Specification

Start the standalone geospatial microservice:
```bash
uvicorn geo.api.service:app --host 127.0.0.1 --port 8005
```

### Endpoints

#### 1. `POST /geo/cell-analysis`
**Request:**
```json
{
  "h3_cell": "873ca91adffffff"
}
```

**Response:**
```json
{
  "h3_cell": "873ca91adffffff",
  "latitude": 23.958068,
  "longitude": 86.80196,
  "transaction_count": 0,
  "complaint_count": 564,
  "fraud_count": 0,
  "fraud_ratio": 0.0,
  "total_transaction_amount": 0.0,
  "total_complaint_loss": 29343613.69,
  "risk_score": 50.0,
  "risk_band": "MEDIUM",
  "hotspot_cluster": 0,
  "nearest_atms": [
    {
      "outlet_id": "RBI_OUTLET_000177",
      "bank_name": "State Bank of India",
      "bank_code": "SBI",
      "outlet_type": "ON_SITE_ATM",
      "city": "Jamtara-Karmatanr",
      "district": "Jamtara",
      "state": "Jharkhand",
      "distance_km": 0.45,
      "distance_meters": 450.2
    }
  ],
  "dominant_scam_type": "phishing",
  "nearest_cyber_hub": "Jamtara-Karmatanr Hub",
  "distance_to_cyber_hub_km": 0.37,
  "disclaimer": "Do not claim that a geospatial risk score or hotspot cluster proves criminal activity. It represents a model-generated spatial risk signal for tactical intelligence and investigation."
}
```

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

---

## 4. Statutory & Evidentiary Disclaimer

> [!IMPORTANT]
> **Evidentiary Notice**:
> *"Do not claim that a geospatial risk score or hotspot cluster proves criminal activity. It represents a model-generated spatial risk signal for tactical intelligence and investigation."*
> 
> Spatial scores, H3 densities, and DBSCAN clusters emitted by this engine provide investigative prioritization for Law Enforcement Agencies (LEAs), cyber monitoring units, and banking fraud cells. They do not constitute statutory proof of guilt or penal liability without independent corroborative evidence, tower CDR verification, and certified bank statements (Section 65B Indian Evidence Act).

---

## 5. Automated Verification & Test Coverage

Run all geospatial unit and integration tests:
```bash
pytest tests/geo/ -v
```
All **41 geospatial tests** pass in ~1.7s, with **144 tests passing monorepo-wide**.
