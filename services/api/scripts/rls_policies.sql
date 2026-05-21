-- =============================================================================
-- CarbonScan AI — Row-Level Security (RLS) Policies
-- =============================================================================
-- Run AFTER alembic upgrade head + seed_species_db.sql.
-- Idempotent (uses DROP IF EXISTS + CREATE) — safe to re-run.
--
-- Pattern:
--   - All app tables have RLS enabled
--   - Most data is isolated per-user (owner_id = auth.uid())
--   - Marketplace allows public to browse verified+available trees
--   - Auditors can update tree verification status
--   - Admins bypass everything
--   - species_db is public-read (reference data — no RLS)
-- =============================================================================

-- ============================================================================
-- 1. Auto-sync trigger: auth.users → public.users on signup
-- ============================================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.users (id, email, name, role)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'name', NEW.email),
        COALESCE(NEW.raw_user_meta_data->>'role', 'community')
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();


-- ============================================================================
-- 2. Helper function: is_admin / is_auditor
-- ============================================================================

CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.users
        WHERE id = auth.uid() AND role = 'admin'
    );
$$;

CREATE OR REPLACE FUNCTION public.is_auditor_or_admin()
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.users
        WHERE id = auth.uid() AND role IN ('auditor', 'admin')
    );
$$;


-- ============================================================================
-- 3. Enable RLS on all app tables
-- ============================================================================

ALTER TABLE public.users        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.plots        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trees        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jobs         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
-- species_db stays public-read (reference table)


-- ============================================================================
-- 4. USERS table policies
-- ============================================================================

-- Drop existing
DROP POLICY IF EXISTS "users_select_own"   ON public.users;
DROP POLICY IF EXISTS "users_update_own"   ON public.users;
DROP POLICY IF EXISTS "users_admin_all"    ON public.users;

-- Users see + update their own profile
CREATE POLICY "users_select_own" ON public.users
    FOR SELECT
    USING (id = auth.uid());

CREATE POLICY "users_update_own" ON public.users
    FOR UPDATE
    USING (id = auth.uid());

-- Admins see everyone
CREATE POLICY "users_admin_all" ON public.users
    FOR ALL
    USING (public.is_admin());


-- ============================================================================
-- 5. PLOTS table policies
-- ============================================================================

DROP POLICY IF EXISTS "plots_owner_all"    ON public.plots;
DROP POLICY IF EXISTS "plots_admin_all"    ON public.plots;

-- Owner can do everything with their plots
CREATE POLICY "plots_owner_all" ON public.plots
    FOR ALL
    USING (owner_id = auth.uid());

CREATE POLICY "plots_admin_all" ON public.plots
    FOR ALL
    USING (public.is_admin());


-- ============================================================================
-- 6. TREES table policies (most complex — marketplace logic)
-- ============================================================================

DROP POLICY IF EXISTS "trees_owner_all"          ON public.trees;
DROP POLICY IF EXISTS "trees_public_marketplace" ON public.trees;
DROP POLICY IF EXISTS "trees_auditor_verify"     ON public.trees;
DROP POLICY IF EXISTS "trees_admin_all"          ON public.trees;

-- Owners: full control over their own trees
CREATE POLICY "trees_owner_all" ON public.trees
    FOR ALL
    USING (owner_id = auth.uid());

-- Public (incl. anonymous): can browse verified + available trees for marketplace
CREATE POLICY "trees_public_marketplace" ON public.trees
    FOR SELECT
    USING (is_available = TRUE AND verified_at IS NOT NULL);

-- Auditors: can update verification fields on any tree
CREATE POLICY "trees_auditor_verify" ON public.trees
    FOR UPDATE
    USING (public.is_auditor_or_admin());

-- Admins: bypass everything
CREATE POLICY "trees_admin_all" ON public.trees
    FOR ALL
    USING (public.is_admin());


-- ============================================================================
-- 7. JOBS table policies (ML processing jobs)
-- ============================================================================

DROP POLICY IF EXISTS "jobs_owner_all"  ON public.jobs;
DROP POLICY IF EXISTS "jobs_admin_all"  ON public.jobs;

CREATE POLICY "jobs_owner_all" ON public.jobs
    FOR ALL
    USING (user_id = auth.uid());

CREATE POLICY "jobs_admin_all" ON public.jobs
    FOR ALL
    USING (public.is_admin());


-- ============================================================================
-- 8. TRANSACTIONS table policies (carbon credit purchases)
-- ============================================================================

DROP POLICY IF EXISTS "tx_buyer_select"   ON public.transactions;
DROP POLICY IF EXISTS "tx_seller_select"  ON public.transactions;
DROP POLICY IF EXISTS "tx_buyer_insert"   ON public.transactions;
DROP POLICY IF EXISTS "tx_admin_all"      ON public.transactions;

-- Buyer can see their own purchases
CREATE POLICY "tx_buyer_select" ON public.transactions
    FOR SELECT
    USING (buyer_id = auth.uid());

-- Seller can see purchases of their trees
CREATE POLICY "tx_seller_select" ON public.transactions
    FOR SELECT
    USING (seller_id = auth.uid());

-- Only authenticated buyers can create transactions (where buyer = themselves)
CREATE POLICY "tx_buyer_insert" ON public.transactions
    FOR INSERT
    WITH CHECK (buyer_id = auth.uid());

CREATE POLICY "tx_admin_all" ON public.transactions
    FOR ALL
    USING (public.is_admin());


-- ============================================================================
-- 9. Storage bucket policies
-- ============================================================================
-- Note: Supabase Storage uses storage.objects table. Policies below restrict
-- file access per bucket. These DROP/CREATE should be safe to re-run.

-- point-clouds: private — owner-only read/write
DROP POLICY IF EXISTS "pointclouds_owner_select" ON storage.objects;
DROP POLICY IF EXISTS "pointclouds_owner_insert" ON storage.objects;

CREATE POLICY "pointclouds_owner_select" ON storage.objects
    FOR SELECT
    USING (
        bucket_id = 'point-clouds'
        AND auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "pointclouds_owner_insert" ON storage.objects
    FOR INSERT
    WITH CHECK (
        bucket_id = 'point-clouds'
        AND auth.uid()::text = (storage.foldername(name))[1]
    );

-- photos: same pattern as point-clouds
DROP POLICY IF EXISTS "photos_owner_select" ON storage.objects;
DROP POLICY IF EXISTS "photos_owner_insert" ON storage.objects;

CREATE POLICY "photos_owner_select" ON storage.objects
    FOR SELECT
    USING (
        bucket_id = 'photos'
        AND auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "photos_owner_insert" ON storage.objects
    FOR INSERT
    WITH CHECK (
        bucket_id = 'photos'
        AND auth.uid()::text = (storage.foldername(name))[1]
    );

-- reports + brand-assets: public buckets — anyone can read, only owners can write
-- (Supabase auto-handles public read via bucket setting; INSERT requires policy)
DROP POLICY IF EXISTS "reports_owner_insert"    ON storage.objects;
DROP POLICY IF EXISTS "brand_assets_admin_only" ON storage.objects;

CREATE POLICY "reports_owner_insert" ON storage.objects
    FOR INSERT
    WITH CHECK (
        bucket_id = 'reports'
        AND auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "brand_assets_admin_only" ON storage.objects
    FOR INSERT
    WITH CHECK (
        bucket_id = 'brand-assets'
        AND public.is_admin()
    );


-- ============================================================================
-- 10. Verification
-- ============================================================================

SELECT
    schemaname,
    tablename,
    rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname='public'
    AND tablename IN ('users', 'plots', 'trees', 'jobs', 'transactions', 'species_db')
ORDER BY tablename;

SELECT
    schemaname,
    tablename,
    policyname,
    cmd AS for_command
FROM pg_policies
WHERE schemaname='public'
ORDER BY tablename, policyname;
