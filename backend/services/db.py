"""
Database schema management for Aegis.

Creates all required tables on startup:
  - incidents        — persistent incident records (survives coordinator restarts)
  - agent_logs       — per-agent action log for every pipeline run
  - memory_records   — vector embeddings of resolved incidents (pgvector)
"""

import logging

import asyncpg

from backend.config.settings import get_settings

logger = logging.getLogger("aegis.db")
settings = get_settings()

SCHEMA_SQL = """
-- pgvector extension (required for memory_records.embedding)
CREATE EXTENSION IF NOT EXISTS vector;

-- ── incidents ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS incidents (
    id               TEXT PRIMARY KEY,
    title            TEXT NOT NULL,
    service          TEXT NOT NULL,
    server           TEXT NOT NULL,
    severity         TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'detected',
    root_cause       TEXT,
    is_auto_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    matched_memory_id TEXT,
    detected_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at      TIMESTAMPTZ,
    evidence         JSONB NOT NULL DEFAULT '[]',
    remediation_steps JSONB NOT NULL DEFAULT '[]',
    metrics          JSONB NOT NULL DEFAULT '{}',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS incidents_status_idx ON incidents (status);
CREATE INDEX IF NOT EXISTS incidents_detected_at_idx ON incidents (detected_at DESC);

-- ── agent_logs ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agent_logs (
    id           BIGSERIAL PRIMARY KEY,
    incident_id  TEXT NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    agent_id     TEXT NOT NULL,
    event_type   TEXT NOT NULL,        -- 'start', 'complete', 'error', 'timeline_event'
    title        TEXT NOT NULL,
    detail       TEXT,
    duration_ms  REAL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS agent_logs_incident_idx ON agent_logs (incident_id, created_at);

-- ── memory_records (pgvector) ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS memory_records (
    id             UUID PRIMARY KEY,
    incident_title TEXT NOT NULL,
    root_cause     TEXT NOT NULL,
    fix_applied    JSONB NOT NULL,
    embedding      VECTOR(1024) NOT NULL,
    occurrences    INTEGER NOT NULL DEFAULT 1,
    last_seen      TIMESTAMPTZ NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS memory_records_embedding_idx
    ON memory_records USING hnsw (embedding vector_cosine_ops);

-- ── auto-update updated_at on incidents ──────────────────────────────────────
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS incidents_updated_at ON incidents;
CREATE TRIGGER incidents_updated_at
    BEFORE UPDATE ON incidents
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
"""


async def run_migrations(dsn: str | None = None) -> None:
    """Apply the schema to the database. Idempotent — safe to call on every startup."""
    _dsn = dsn or settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    try:
        conn = await asyncpg.connect(_dsn)
        await conn.execute(SCHEMA_SQL)
        await conn.close()
        logger.info("Database schema applied successfully")
    except Exception:
        logger.exception(
            "Database migration failed — check DATABASE_URL and that the postgres service is running. "
            "The API will continue starting but persistence features won't work."
        )
