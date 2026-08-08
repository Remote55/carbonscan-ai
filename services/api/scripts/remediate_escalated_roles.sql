-- =============================================================================
-- TreeQ Carbon — remediation for self-assigned privileged roles
-- =============================================================================
-- Run ONCE, with the service key, AFTER applying the corrected rls_policies.sql.
--
-- Why this exists
-- ---------------
-- Two independent paths let a signed-up user hold a role they were never
-- granted:
--
--   1. handle_new_user() took the role straight from raw_user_meta_data, which
--      is whatever the client passed to supabase.auth.signUp. Signing up as
--      'admin' was a request-body edit.
--   2. The users_update_own policy had no WITH CHECK. Postgres then defaults it
--      to the USING clause, so an UPDATE was only checked for id = auth.uid()
--      and the role column was unconstrained - PATCH /rest/v1/users with
--      {"role":"admin"} through the public anon key.
--
-- Both are closed in rls_policies.sql now. Closing them does not undo anything
-- that already happened, which is what this script is for.
--
-- Read the SELECT first. Do not run the UPDATE until you have looked at the
-- rows and confirmed which of them, if any, are legitimate grants you made
-- deliberately. There is no way for this script to tell those apart.
-- =============================================================================

-- Step 1 — look. Every account above 'community', with when it was created and
-- what the client sent at signup. A role here that matches raw_user_meta_data
-- came in through path 1; one that does not came in through path 2, or was
-- granted properly.
SELECT
    u.id,
    u.email,
    u.role                              AS current_role,
    au.raw_user_meta_data ->> 'role'    AS role_requested_at_signup,
    au.created_at,
    au.last_sign_in_at
FROM public.users u
JOIN auth.users au ON au.id = u.id
WHERE u.role IS DISTINCT FROM 'community'
ORDER BY au.created_at;

-- Step 2 — reset. Uncomment and run once you have decided.
--
-- Re-grant afterwards, one account at a time, by id and not by email:
--   UPDATE public.users SET role = 'auditor' WHERE id = '<uuid>';
--
-- UPDATE public.users
-- SET role = 'community'
-- WHERE role IS DISTINCT FROM 'community'
--   AND id <> '<uuid of the account you actually want to keep privileged>';

-- Step 3 — check the damage an escalated account could have done. Verification
-- is the trust anchor of this product: trees_auditor_verify let anyone holding
-- 'auditor' mark ANY tree verified, not only their own.
SELECT
    t.id,
    t.owner_id,
    t.verified_at,
    t.verified_by,
    u.email AS verified_by_email,
    u.role  AS verifier_role_now
FROM public.trees t
LEFT JOIN public.users u ON u.id = t.verified_by
WHERE t.verified_at IS NOT NULL
ORDER BY t.verified_at DESC;

-- Step 4 — confirm the hole is shut. As a normal signed-in user (anon key, not
-- service key), this must fail rather than succeed:
--
--   UPDATE public.users SET role = 'admin' WHERE id = auth.uid();
--
-- Expected: "new row violates row-level security policy for table users".
-- If it succeeds, rls_policies.sql has not been applied to this project.
