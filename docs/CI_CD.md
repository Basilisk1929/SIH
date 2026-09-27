# CyberShield-Intel: Continuous Integration & Continuous Delivery (CI/CD)

**Automated Quality Engineering, Static Analysis, Testing Pipelines & Branch Protection**

---

## 1. Overview & CI/CD Philosophy

CyberShield-Intel employs an automated, zero-trust CI/CD pipeline implemented via GitHub Actions (`.github/workflows/ci.yml`). Every code change proposed via Pull Request or pushed to core development branches is validated against rigorous linting, type safety, end-to-end integration tests, container builds, and security leak scans before merging.

### Core CI/CD Principles:
1. **Zero Secret Exposure**: CI workflows use synthetic test fixtures and disposable service containers. No production secrets, cloud credentials, or private keys are ever stored in the repository or printed to logs.
2. **Deterministic Parity**: The CI runner replicates production conditions using PostgreSQL 16 and Redis 7.2 service containers, executing database migrations before running test suites.
3. **Fail-Fast & Zero Masking**: No error-hiding commands (e.g. `|| true`) are permitted for required checks. Any test failure, type error, or missing build artifact fails the pipeline immediately.
4. **Manual Production Promotion**: Deployment to production environments (such as Vercel and cloud compute clusters) is intentionally decoupled from CI; deployment requires explicit release tags and human verification.

---

## 2. Branching Strategy & Branch Protection

The repository follows a structured Git workflow:

```
[ feature/* or bugfix/* ]
           │
           ▼ (Pull Request + Full CI Validation)
      [ develop ]  ────────► Staging / Integration Environment
           │
           ▼ (Release Candidate PR + Full CI Validation)
       [ main ]    ────────► Production Release / SIH Presentation Tag
```

### Branch Rules:
- **`develop`**: Active integration branch. Receives merged features after all CI jobs pass and peer review is approved.
- **`main`**: Production-ready, stable release branch. Direct pushes are blocked. Merges into `main` require:
  - All CI jobs (`backend-test`, `frontend-check`, `docker-ci`, `security-scan`) passing.
  - Linear history / squash-merge preferred.
  - Branch protection with required status checks enabled.
- **Feature Branches**: Named `feature/<name>`, `fix/<name>`, or `phase-<num>-<name>`.

---

## 3. Workflow Structure & Matrix of Checks

The GitHub Actions workflow (`.github/workflows/ci.yml`) triggers on:
- `push` to branches `main` and `develop`
- `pull_request` targeting `main` and `develop`

Concurrency management ensures that subsequent commits to an open PR automatically cancel obsolete in-flight runs to conserve compute resources.

```mermaid
graph TD
    A[PR or Push to main/develop] --> B1[Job: backend-test]
    A --> B2[Job: frontend-check]
    A --> B3[Job: docker-ci]
    A --> B4[Job: security-scan]

    subgraph Backend["Job 1: backend-test (Python 3.12)"]
        B1 --> C1[PostgreSQL 16 Service]
        B1 --> C2[Redis 7.2 Service]
        B1 --> C3[Install backend/requirements.txt]
        B1 --> C4[Download spaCy en_core_web_sm]
        B1 --> C5[Static Lint: ruff check .]
        B1 --> C6[Migrations: alembic upgrade head]
        B1 --> C7[Pytest: 235 backend/ML/NLP/Geo tests]
    end

    subgraph Frontend["Job 2: frontend-check (Node 20)"]
        B2 --> D1[Clean Install: npm ci]
        B2 --> D2[TypeScript Check: npm run lint]
        B2 --> D3[Unit Tests: npm test -- --run]
        B2 --> D4[Vite Production Build: npm run build]
        B2 --> D5[Verify dist/index.html artifact]
    end

    subgraph Docker["Job 3: docker-ci (Container Builds)"]
        B3 --> E1[Validate docker-compose.yml]
        B3 --> E2[Build Backend Image]
        B3 --> E3[Build Frontend Production Image]
    end

    subgraph Security["Job 4: security-scan (Leak Prevention)"]
        B4 --> F1[Verify no .env / key files tracked]
        B4 --> F2[Scan for unencrypted private keys]
    end
```

### Detailed Job Matrix:

| Job Name | Runner Environment | Services / Dependencies | Verification Command | Gate / Failure Condition |
|---|---|---|---|---|
| **`backend-test`** | `ubuntu-latest` (Python 3.12) | PostgreSQL 16, Redis 7.2 | `ruff check .`<br>`alembic upgrade head`<br>`pytest -v --tb=short` | Non-zero exit on lint, unapplied migration, or test failure |
| **`frontend-check`** | `ubuntu-latest` (Node.js 20) | npm cache, React/Vite | `npm ci`<br>`npm run lint`<br>`npm test -- --run`<br>`npm run build` | Non-zero exit on type errors, test failures, or missing `dist/` |
| **`docker-ci`** | `ubuntu-latest` (Docker daemon) | Docker Buildx / Compose | `docker compose config --quiet`<br>`docker build -f docker/Dockerfile.backend .`<br>`docker build -f docker/Dockerfile.frontend ./frontend` | Compose configuration error or Dockerfile build crash |
| **`security-scan`** | `ubuntu-latest` (Git tools) | Source repository | `git ls-files` forbidden file check<br>`git grep` private key scan | Detection of `.env`, `.env.local`, or private cryptographic keys |

---

## 4. Required Secrets & Environment Configuration

### In CI Environment
The CI pipeline is **completely self-contained** and uses synthetic credentials configured within `.github/workflows/ci.yml`. No third-party API keys or cloud credentials are required for standard PR validation:

```yaml
env:
  ENVIRONMENT: test
  SYNTHETIC_DATA_ONLY: "True"
  DEBUG: "False"
  DATABASE_URL: "postgresql+asyncpg://cyber_user:ChangeMeInProd_123!@localhost:5432/cyber_intel_db"
  JWT_SECRET_KEY: "ci-synthetic-test-key-not-for-production-use-only-for-automated-github-actions"
  JWT_ALGORITHM: "HS256"
  ACCESS_TOKEN_EXPIRE_MINUTES: "480"
  REDIS_URL: "redis://localhost:6379/0"
  ALLOWED_CORS_ORIGINS: '["http://localhost:5173"]'
```

### Future Production Deployment Secrets (When Activated)
When deployment automation is configured in later phases, the following GitHub Repository Secrets should be set in GitHub Settings > Secrets and variables > Actions:

| Secret Name | Purpose | Example / Format |
|---|---|---|
| `VERCEL_TOKEN` | Token for authenticating Vercel CLI | `Bearer ...` |
| `VERCEL_ORG_ID` | Vercel Organization ID | `team_...` |
| `VERCEL_PROJECT_ID` | Vercel Project ID | `prj_...` |
| `PROD_DATABASE_URL` | Production PostgreSQL connection string | `postgresql+asyncpg://user:pass@host:5432/db` |
| `PROD_NEO4J_URI` | Neo4j AuraDB Bolt endpoint | `neo4j+s://xxxx.databases.neo4j.io` |
| `PROD_NEO4J_USER` | Neo4j AuraDB username | `neo4j` |
| `PROD_NEO4J_PASSWORD` | Neo4j AuraDB password | `ChangeMe...` |
| `PROD_JWT_SECRET` | 64+ char random hex key for JWT signing | `openssl rand -hex 32` |

---

## 5. How to Run CI Checks Locally

Developers should run the exact CI verification steps locally before pushing changes or opening a Pull Request:

### 1. Backend Linting & Test Suite
```bash
# 1. Activate virtual environment
source .venv/bin/activate  # or conda activate

# 2. Run Ruff syntax and static analysis
ruff check .

# 3. Ensure database migrations are applied
alembic upgrade head

# 4. Run Pytest suite
pytest -q
```

### 2. Frontend Typecheck, Tests & Build
```bash
cd frontend

# 1. TypeScript static analysis
npm run lint

# 2. Vitest unit & component tests
npm test -- --run

# 3. Production bundle build
npm run build

cd ..
```

### 3. Docker Compose & Image Builds
```bash
# 1. Validate Compose syntax
docker compose config --quiet

# 2. Build Backend Docker image
docker build -t test-backend -f docker/Dockerfile.backend .

# 3. Build Frontend Production Docker image
docker build --target production -t test-frontend -f docker/Dockerfile.frontend ./frontend
```

### 4. Security & Secret Leak Check
```bash
# Verify no .env or sensitive files are tracked
FORBIDDEN=(".env" ".env.local" ".env.production" "id_rsa" "id_rsa.pub")
for file in "${FORBIDDEN[@]}"; do
  if git ls-files --error-unmatch "$file" 2>/dev/null; then
    echo "ERROR: $file is tracked!"
    exit 1
  fi
done

# Verify no plaintext private keys are committed
git grep -E -- "-----BEGIN [A-Z]+ PRIVATE KEY-----" ":!docs" || echo "No private keys found."
```

---

## 6. Release Management & Deployment Policy

### Why Deployment is Intentionally Not Automatic Yet
Continuous Deployment (CD) directly to production environments is intentionally deferred at Phase 13 because:
1. **Judicial Presentation Safety**: For Smart India Hackathon demonstrations, infrastructure should remain locked and deterministic until the jury demonstration session.
2. **Cloud Provider Provisioning**: Cloud database instances (PostgreSQL RDS and Neo4j Aura) must be provisioned with designated VPC security groups before pointing production domains.
3. **Vercel Frontend Linking**: Vercel configuration requires project ownership association in the user's personal/organization account.

### Recommended Release Process:
1. All pull requests to `main` must pass all 4 CI jobs.
2. Tag release versions on `main`: `git tag -a v1.0.0 -m "Release v1.0.0 — SIH Grand Finale Edition"`.
3. Push tag: `git push origin v1.0.0`.
4. Trigger manual or gated deployment to staging/production.
