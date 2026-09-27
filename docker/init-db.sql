-- ==============================================================================
-- CyberShield-Intel Platform - PostgreSQL 16 Database Initialization Script
-- Executed automatically on fresh volume creation by postgres:16-alpine entrypoint.
-- Enables cryptographic & UUID extensions.
-- Relational tables and indices are managed exclusively by Alembic migrations.
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'CyberShield-Intel PostgreSQL extensions (uuid-ossp, pgcrypto) initialized successfully.';
END $$;
