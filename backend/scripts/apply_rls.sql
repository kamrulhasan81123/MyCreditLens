-- Row Level Security for MyCreditLens (defence in depth).
--
-- The FastAPI backend connects as the `postgres` role via the Supavisor pooler
-- and is the table owner, so it BYPASSES RLS — application authorization in
-- FastAPI remains the primary, mandatory control. RLS here denies the Supabase
-- `anon` / `authenticated` roles (i.e. any future direct-from-browser access via
-- PostgREST) on sensitive tables, and would carry owner-scoped policies for
-- client-readable tables if/when direct client access is introduced.
--
-- Idempotent: safe to run repeatedly. Enables + FORCEs RLS with no permissive
-- policy on backend-only tables => deny-all to non-owner roles.

-- BACKEND_ONLY / PRIVATE tables: no direct client access at all.
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'predictions','explanations','decisions','audit_logs','ml_models',
    'fairness_metrics','monitoring_metrics','integrity_alerts',
    'policy_rules','policy_results','engineered_features','reports'
  ] LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', t);
    EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY;', t);
  END LOOP;
END $$;

-- READ_ONLY_CLIENT / controlled tables: enable RLS now (deny-all until explicit
-- owner-scoped policies are added when direct-client access is introduced).
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'users','borrowers','applications','consents','data_sources','transactions',
    'appeals','notifications'
  ] LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', t);
  END LOOP;
END $$;

-- Example owner-scoped policy to ADD when direct-client reads are enabled
-- (kept as documentation; not applied automatically):
--   CREATE POLICY borrower_self_read ON public.borrowers
--     FOR SELECT TO authenticated
--     USING (user_id = auth.uid()::text);
