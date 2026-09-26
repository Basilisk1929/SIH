# CyberShield Intel: Cybercrime Intelligence & Financial Risk Detection Platform
> **Smart India Hackathon (SIH) Prototype Specification**  
> *Production-Oriented Cyber Threat Intelligence, NCRP/1930 Incident Triage, and Multi-Hop Mule Account Tracing*

[![CI Pipeline](https://github.com/organization/cyber-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/organization/cyber-intelligence/actions)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6.svg)](https://www.typescriptlang.org/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.18-008CC1.svg)](https://neo4j.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)

---

## 1. Compliance & Non-Disclosure Notice
> [!IMPORTANT]
> **SYNTHETIC & OPEN DATA MANDATE:**  
> Real NCRP/1930 complaint feeds and live Indian bank transaction telemetries are strictly restricted by law enforcement and regulatory privacy frameworks. **This repository operates exclusively with synthetic and simulated data**. Zero real personal, financial, or LEA records are collected, stored, or processed. All account numbers, phone numbers, VPAs, and narrative descriptions are programmatically generated pseudo-entities.

---

## 2. Platform Architecture Overview
CyberShield Intel is designed as a **modular cybercrime intelligence platform** enabling state cyber cells, intelligence analysts, and bank fraud response units to:
1. **Triage 1930 / NCRP complaints** in real-time using NLP entity extraction (extracting UPI VPAs, IFSCs, phone numbers, and malicious APK names).
2. **Detect multi-layer mule account syndicates** across Indian payment rails (UPI, IMPS, NEFT) using graph network analysis.
3. **Execute "Golden-Hour" emergency interventions**, flagging suspect beneficiary accounts and recommending immediate lien holds before funds exit via ATM or crypto off-ramps.
4. **Map geographic threat clusters** correlating cyber incident hotspots (e.g. Mewat, Jamtara, Bharatpur) with synthetic mobile tower and IP centroids.

---

## 3. Monorepo Directory Structure

```text
. (SIH Repository Root)
├── backend/                  # Python 3.12 + FastAPI Core Application
│   ├── app/
│   │   ├── api/v1/           # Modular REST Endpoints (Complaints, Txns, Graph, Auth)
│   │   ├── core/             # Settings, JWT, RBAC Guards, Structured Logging
│   │   ├── db/               # PostgreSQL Asyncpg Session & Neo4j Driver Pool
│   │   ├── models/           # SQLAlchemy 2.0 Database ORM Models
│   │   ├── schemas/          # Pydantic v2 Request/Response Data Contracts
│   │   └── services/         # Domain Business Logic & Risk Engines
│   ├── pyproject.toml        # Ruff, Pytest, and Packaging Configuration
│   └── requirements.txt      # Production Python Dependencies
├── frontend/                 # React 18 + TypeScript + Vite Investigator UI
│   ├── public/               # Static Assets
│   ├── src/
│   │   ├── components/       # Layout (Header, Sidebar) & Common UI Elements
│   │   ├── pages/            # Dashboard, 1930 Workbench, Graph, Hotspot Heatmap
│   │   ├── services/         # Typed API Service Client & PII Masking
│   │   ├── styles/           # Modern Dark Cyber Theme (Vanilla CSS)
│   │   └── types/            # Domain TypeScript Interfaces
│   ├── index.html            # Vite Entrypoint with Security Headers
│   ├── package.json          # Frontend Dependencies & Scripts
│   └── vite.config.ts        # Vite Dev Server with Backend API Proxy
├── data/                     # Synthetic Data & Simulation Generators
│   ├── generators/           # Deterministic Synthetic Complaint & Txn Generator
│   ├── raw/                  # Staging for Publicly Available Reference Datasets
│   └── synthetic/            # Sample Pre-generated Test Fixtures (JSON)
├── ml/                       # Machine Learning Risk & Anomaly Models
│   ├── inference/            # Real-time High-Velocity Transaction Risk Scorer
│   ├── models/               # Mule Account Detection Isolation Forest Models
│   └── training/             # Model Training Pipelines & Feature Extractors
├── nlp/                      # Narrative Analysis & Entity Extraction
│   ├── classifiers/          # Cyber Fraud Modus Operandi Text Classifier
│   └── extractors/           # Regex & NER Extractor for VPAs, IFSCs, Phones, APKs
├── graph/                    # Graph Network Analysis & Neo4j Integration
│   ├── algorithms/           # Multi-hop Flow Tracing & Cycle Detection
│   └── queries/              # Parameterized Cypher Queries for Mule Linkage
├── geo/                      # Spatial Analysis & Cluster Mapping
│   ├── clustering/           # Spatial Density & Haversine Distance Analyzer
│   └── mappings/             # Benchmark Centroids for Indian Cybercrime Hubs
├── ingestion/                # Data Streaming & Event Normalization
│   ├── connectors/           # Batch Ingestors for NCRP Files
│   └── pipelines/            # Async Transaction Streaming Simulator
├── tests/                    # Automated Test Suite (Pytest)
│   ├── backend/              # Health, Complaint API, and Risk Engine Tests
│   ├── ml/                   # ML Feature Extraction & Decision Boundary Tests
│   ├── nlp/                  # Entity Extraction & Scam Classification Tests
│   ├── graph/                # Flow Tracing Algorithm Tests
│   └── conftest.py           # Shared Async Fixtures & Test Client Setup
├── docker/                   # Containerization & Initialization Scripts
│   ├── Dockerfile.backend    # Hardened Non-Root Python 3.12 Image
│   ├── Dockerfile.frontend   # Lightweight Node 20 Dev/Build Image
│   ├── init-db.sql           # PostgreSQL Schema, Indices, and Tables
│   └── neo4j-init.cypher     # Neo4j Constraints, Node Keys, and Indices
├── docs/                     # Comprehensive Architecture & API Documentation
│   ├── architecture/         # C4 Architecture, Data Flow, and Mule Typology
│   ├── api/                  # OpenAPI / ReDoc Endpoint Specifications
│   └── schemas/              # Detailed Synthetic Data Dictionaries
├── .github/workflows/ci.yml  # GitHub Actions Automated CI/CD Pipeline
├── .env.example              # Environment Configuration Template
├── .gitignore                # Multi-language Git Exclusions
└── docker-compose.yml        # Multi-Container Stack (FastAPI, Postgres, Neo4j, Redis, React)
```

---

## 4. How to Run the Platform

### Option A: Using Docker Compose (Full Stack - Recommended)

1. **Clone and enter repository**:
   ```bash
   cd SIH
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   ```

3. **Launch the orchestrated stack**:
   ```bash
   docker compose up --build
   ```

4. **Access the platform interfaces**:
   - **Investigator UI**: [http://localhost:5173](http://localhost:5173)
   - **FastAPI Interactive Docs (Swagger)**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
   - **FastAPI ReDoc**: [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)
   - **Neo4j Browser**: [http://localhost:7474](http://localhost:7474) (Auth: `neo4j` / `cyber_graph_password_123!`)
   - **PostgreSQL**: `localhost:5432` (`cyber_intelligence_db`)

---

### Option B: Local Standalone Development (Bare-Metal)

#### 1. Backend Setup (Python 3.12)
```bash
# Create and activate virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Seed synthetic test data
python3 data/generators/synthetic_generator.py

# Launch FastAPI development server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Frontend Setup (React + TypeScript)
```bash
cd frontend

# Install node dependencies
npm install

# Start Vite dev server
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) to view the workbench.

---

## 5. Running Automated Tests & Data Validation

### A. Synthetic Data Validation (Referential Integrity)
Validate that all generated entities, accounts, transactions, and complaints satisfy 100% referential integrity and label consistency:
```bash
# Validate CSV files
python3 data/validators/validate_referential_integrity.py csv

# Validate Parquet files
python3 data/validators/validate_referential_integrity.py parquet
```

### B. Generate Custom Dataset Scales (10K, 50K, 100K, 500K)
```bash
# 10K records (Default development scale)
python3 data/generators/synthetic_generator.py --scale 10K --format both

# 50K, 100K, or 500K production scale
python3 data/generators/synthetic_generator.py --scale 50K --format both
python3 data/generators/synthetic_generator.py --scale 100K --format both
python3 data/generators/synthetic_generator.py --scale 500K --format both
```

### C. Automated Test Suite (Pytest)
Run the complete backend, ML, NLP, graph, and data test suite using `pytest`:
```bash
pytest tests/ -v
```

Run code formatting and security linting:
```bash
ruff check backend/ app/ tests/
```

Run frontend type checking:
```bash
cd frontend
npm run lint
```

---

## 6. What Should Be Implemented Next (Roadmap)

To elevate this prototype into a full hackathon-winning evaluation submission, implement the following prioritized modules:

### Phase 2: Core Enhancements
1. **Neo4j Graph Visualizer Integration**:
   - Integrate an interactive canvas library (such as Cytoscape.js or Vis.js) into `src/pages/GraphVisualizer.tsx` to render real-time force-directed network graphs with collapsible mule clusters.
2. **Indian Map Geospatial Layer**:
   - Integrate Leaflet or Mapbox GL with Indian state and district GeoJSON boundaries (`geo/geojson/`) to render interactive choropleths and crime density heatmaps.
3. **Advanced Multilingual NLP (Bhashini API / IndicBERT)**:
   - Expand `nlp/classifiers/` to support Hinglish and regional language incident narratives (e.g. Hindi, Marathi, Telugu, Tamil).
4. **Automated Golden-Hour Nodal Officer Notification**:
   - Implement an automated bank API dispatcher / simulated webhook service in `backend/app/services/` that generates standard LEA Section 91 CrPC / Section 79 notices to bank nodal officers.
5. **Real-Time WebSocket Stream**:
   - Add a WebSocket endpoint in FastAPI streaming simulated 1930 calls and transaction alerts directly into the investigator dashboard with zero polling.
