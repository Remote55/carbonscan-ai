-- =============================================================================
-- CarbonScan AI — Supabase Initial Setup
-- =============================================================================
-- Run this ONCE in the Supabase SQL Editor before running Alembic migrations.
-- (Supabase Dashboard → SQL Editor → New Query → paste this → Run)
--
-- Required extensions:
--   - postgis      (spatial queries — required by app)
--   - pg_trgm      (trigram fuzzy text search — for species name lookup)
--   - uuid-ossp    (UUID generation — gen_random_uuid is built-in but uuid-ossp adds more)
-- =============================================================================

-- 1. Enable PostGIS (spatial geometry support)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- 2. Enable text search extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- 3. UUID helpers (gen_random_uuid is in pgcrypto on older Postgres)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 4. Verify versions (output is informational)
SELECT
    extname AS extension,
    extversion AS version
FROM pg_extension
WHERE extname IN ('postgis', 'pg_trgm', 'pgcrypto', 'unaccent')
ORDER BY extname;

-- =============================================================================
-- Storage Buckets (run via Supabase Dashboard → Storage → Create bucket)
-- =============================================================================
--
-- Create these buckets manually with the listed settings:
--
-- 1. point-clouds      (private, file size limit: 500MB)
-- 2. photos            (private, file size limit: 20MB per file)
-- 3. reports           (public, file size limit: 5MB)
-- 4. brand-assets      (public, file size limit: 5MB) — optional, for logos
--
-- =============================================================================

-- =============================================================================
-- Row Level Security (RLS) policies — run AFTER Alembic migration creates tables
-- =============================================================================
--
-- Uncomment + run after `alembic upgrade head` succeeded.
--
-- ALTER TABLE users         ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE plots         ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE trees         ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE jobs          ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE transactions  ENABLE ROW LEVEL SECURITY;
--
-- -- Public can see verified, available trees (marketplace browsing)
-- CREATE POLICY "Public can see verified available trees"
--     ON trees FOR SELECT
--     USING (is_available = TRUE AND verified_at IS NOT NULL);
--
-- -- Users see their own trees regardless of verification
-- CREATE POLICY "Users see own trees"
--     ON trees FOR SELECT
--     USING (owner_id = auth.uid());
--
-- -- Users insert their own trees
-- CREATE POLICY "Users insert own trees"
--     ON trees FOR INSERT
--     WITH CHECK (owner_id = auth.uid());
--
-- -- Auditors verify trees
-- CREATE POLICY "Auditors verify trees"
--     ON trees FOR UPDATE
--     USING (
--         EXISTS (
--             SELECT 1 FROM users
--             WHERE id = auth.uid() AND role IN ('auditor', 'admin')
--         )
--     );
