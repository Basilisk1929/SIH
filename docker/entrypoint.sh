#!/usr/bin/env bash
set -e

echo "=== CyberShield-Intel Backend Service Starting ==="
echo "Environment: ${ENVIRONMENT:-development}"
echo "Port: ${PORT:-8000}"

# 1. Wait for PostgreSQL Database Connectivity
echo "Waiting for PostgreSQL database to accept connections..."
python - <<'EOF'
import asyncio
import os
import sys
import time
from urllib.parse import urlparse
import asyncpg

db_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://cyber_admin:cyber_dev_password_123!@postgres:5432/cyber_intelligence_db",
)

# Parse connection params
cleaned_url = db_url.replace("postgresql+asyncpg://", "http://").replace("postgresql://", "http://")
parsed = urlparse(cleaned_url)
user = parsed.username or "cyber_admin"
password = parsed.password or "cyber_dev_password_123!"
host = parsed.hostname or "postgres"
port = parsed.port or 5432
database = parsed.path.lstrip("/") or "cyber_intelligence_db"

# Render managed PostgreSQL may require SSL
ssl_mode = os.getenv("PGSSLMODE", None)
use_ssl = ssl_mode == "require" or host.endswith(".render.com") or host.endswith(".oregon-postgres.render.com")

max_retries = 30
for attempt in range(1, max_retries + 1):
    try:
        async def probe():
            connect_kwargs = dict(
                user=user,
                password=password,
                host=host,
                port=port,
                database=database,
                timeout=5.0,
            )
            if use_ssl:
                import ssl as ssl_mod
                ssl_ctx = ssl_mod.create_default_context()
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl_mod.CERT_NONE
                connect_kwargs["ssl"] = ssl_ctx
            conn = await asyncpg.connect(**connect_kwargs)
            await conn.execute("SELECT 1")
            await conn.close()

        asyncio.run(probe())
        print(f"[✓] PostgreSQL connection confirmed ({host}:{port}/{database}) on attempt {attempt}.")
        sys.exit(0)
    except Exception as exc:
        print(f"[*] PostgreSQL not ready yet ({host}:{port}). Attempt {attempt}/{max_retries}: {exc}")
        time.sleep(2)

print("[!] FATAL: Could not connect to PostgreSQL within timeout period.")
sys.exit(1)
EOF

# 2. Apply Alembic Database Migrations
echo "Applying Alembic database migrations (alembic upgrade head)..."
alembic upgrade head
echo "[✓] Alembic database migrations applied successfully."

# 3. Optional Database Seeding
if [ "${AUTO_SEED}" = "true" ] || [ "${AUTO_SEED}" = "True" ] || [ "${AUTO_SEED}" = "1" ]; then
    echo "AUTO_SEED flag detected. Checking database seed state..."
    python - <<'EOF'
import asyncio
from sqlalchemy import func, select
from backend.app.db.seeds import seed_database
from backend.app.db.session import AsyncSessionLocal
from backend.app.models import User

async def maybe_seed():
    async with AsyncSessionLocal() as session:
        count = await session.scalar(select(func.count(User.id)))
        if count == 0:
            print("[*] Database is empty. Seeding initial synthetic cybercrime intelligence dataset...")
            await seed_database(session)
            print("[✓] Initial database seeding completed successfully.")
        else:
            print(f"[*] Database already contains {count} users. Skipping auto-seeding.")

asyncio.run(maybe_seed())
EOF
fi

# 4. Optional Neo4j Constraints Initialization
if [ -n "${NEO4J_URI}" ]; then
    echo "Ensuring Neo4j graph schema constraints and indexes..."
    python - <<'EOF'
import asyncio
from backend.app.db.neo4j import check_neo4j_health, get_neo4j_driver
from graph.schema.constraints import apply_graph_schema

async def init_neo4j():
    try:
        is_healthy = await check_neo4j_health()
        if is_healthy:
            driver = get_neo4j_driver()
            count = await apply_graph_schema(driver)
            print(f"[✓] Neo4j graph schema constraints ensured ({count} statements).")
        else:
            print("[*] Neo4j is offline or initializing. Graph fallback engine will be used.")
    except Exception as exc:
        print(f"[*] Neo4j constraint check notice: {exc}")

asyncio.run(init_neo4j())
EOF
fi

echo "=== CyberShield-Intel Backend Ready ==="
exec "$@"
