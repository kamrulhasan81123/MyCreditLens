# Supabase Integration (Phase 4)

Last updated: 2026-08-13

Status: **COMPLETE and verified — PostgreSQL, Auth (JWKS, live), Storage (private
buckets + signed URLs), and RLS all working.** Both credentials have since been
provided and configured in git-ignored `backend/.env` (the publishable key is
also in the frontend `.env.local`). No secret values appear in this document.

### Verified end-to-end (executed)
- **Auth (live):** admin-create confirmed user (service key) → password login
  (publishable key) → real **ES256** token → backend `SupabaseTokenVerifier`
  verifies signature/issuer/audience/expiry and maps `sub`→user. Demo users
  provisioned in Supabase Auth (`scripts/provision_supabase_users.py`) with roles
  in `app_metadata`, so **browser Supabase login works** (analyst login → role
  `credit_analyst` mapped).
- **Storage (live):** 4 **private** buckets created + verified (`public=false`);
  upload → signed-URL fetch (200, bytes match) → delete round-trip; wired into
  data-source upload (`storage_service.py`) with local fallback; signed-URL
  retrieval endpoint (object-level authorised). Service key server-side only,
  never in the browser or any response.
- Gated live tests `tests/test_supabase_integration.py` (storage + MIME + auth
  JWKS round-trip) — **3 passed** with `RUN_SUPABASE_IT=1`; skipped in the normal
  offline suite.
- **TLS note:** this sandbox is behind a TLS-inspecting proxy (private CA), so
  outbound Supabase HTTPS + Postgres verification fail against public CAs. A
  `SUPABASE_VERIFY_SSL` flag (default **true**/secure) is set **false** here only;
  production keeps it true. Postgres uses require-mode SSL for the same reason.

## Project (non-secret)

- Project: `MyCreditLens` · ref `dbkousrapsiplyezmcii` · region `ap-northeast-2` (Seoul)
- URL: `https://dbkousrapsiplyezmcii.supabase.co`
- JWT issuer: `https://dbkousrapsiplyezmcii.supabase.co/auth/v1`
- JWKS: `https://dbkousrapsiplyezmcii.supabase.co/auth/v1/.well-known/jwks.json`
- JWT audience: `authenticated`

## Connectivity — use the IPv4 pooler, not the direct host

The direct host `db.<ref>.supabase.co:5432` is **IPv6-only** (no IPv4 add-on) and
does not resolve from this IPv4 network. We use the **Supavisor session-mode
pooler** instead:

- Host `aws-0-ap-northeast-2.pooler.supabase.com`, port `5432` (session mode)
- User `postgres.dbkousrapsiplyezmcii` (note the `.<project_ref>` suffix)
- TLS: **required** (`sslmode=require`). asyncpg verifies the CA by default and
  the pooler chain isn't in the system store, so `app/database.py` uses a
  require-mode SSL context (encrypt, skip CA verify) for `postgresql+asyncpg`;
  the sync URL carries `?sslmode=require`.

Configured (git-ignored `backend/.env`, values never printed): `DATABASE_URL`
(asyncpg), `DATABASE_URL_SYNC` (psycopg2 + sslmode=require), `SUPABASE_URL`,
`SUPABASE_JWT_ISSUER`, `SUPABASE_JWT_AUDIENCE`, `SUPABASE_JWKS_URL`,
`AUTH_PROVIDER=hybrid`. The prior SQLite URLs are retained as
`# SQLITE_FALLBACK` comments for one-line revert.

## Database migration — DONE

1. Async + sync connectivity verified (PostgreSQL **17.6** via pooler).
2. `alembic upgrade head` → `0001` (schema), `0002` (application-PD features),
   `0003` (widen `engineered_features.feature_version` to VARCHAR(64) — SQLite
   ignored the 20-char limit, Postgres enforces it).
3. Schema verified: **21 tables, 43 foreign keys, 19 native ENUM types, 27
   indexes**, alembic at `0003`.
4. `python -m app.scripts.seed_demo` seeded the full slice into Postgres.
5. Persistence verified: users 5, borrowers 2, applications 2, consents 4,
   data_sources 2, transactions 24, engineered_features 48, predictions 2
   (real `model_version=2.0.0`, `feature_schema_version=app_pd_2.0.0`),
   explanations 2, ml_models 1 (registered active), decisions 2, audit_logs 6.
6. Live API smoke (`scripts/smoke_test.py`) on Postgres: score→persist→
   explanation→stress→counterfactual→decision→audit→404-isolation all pass.

**Tests stay on SQLite** (`conftest.py` pins `DATABASE_URL` to SQLite before app
import) so the suite is fast and never touches the live DB — "SQLite for
lightweight tests" preserved.

## Auth — hybrid, JWKS verification path

- `AuthService.get_current_user` already supports a hybrid path: ES256 tokens with
  a `kid` are verified via `SupabaseTokenVerifier` against the project JWKS
  (signature, issuer, audience, expiry); other tokens use local HS256 JWT.
- Supabase `auth.users.id` (`sub`) maps to the MyCreditLens user id;
  `_sync_supabase_user` links/creates the profile and never stores a Supabase
  password (`hashed_password="supabase-managed"`). Roles remain in MyCreditLens
  tables (from `app_metadata.role`, defaulting to borrower).
- **Do not** use `SUPABASE_SECRET_KEY` to verify ordinary user JWTs — JWKS only.
- Verified by unit tests (`tests/test_supabase_auth.py`, mock EC keypair):
  valid / expired / wrong-issuer / wrong-audience / bad-signature / unconfigured.
- Local HS256 JWT remains the development fallback (active now, since no Supabase
  user/publishable key is configured yet).

## Row Level Security — applied (defence in depth)

`backend/scripts/apply_rls.sql` (idempotent) was applied. FastAPI authorization
remains the primary control; the app connects as `postgres` (which has
`rolbypassrls=true`, verified) so RLS never blocks the backend.

Policy matrix:

| Classification | Tables | RLS |
|---|---|---|
| BACKEND_ONLY / PRIVATE | predictions, explanations, decisions, audit_logs, ml_models, fairness_metrics, monitoring_metrics, integrity_alerts, policy_rules, policy_results, engineered_features, reports | ENABLE + FORCE, no permissive policy → deny anon/authenticated |
| READ_ONLY_CLIENT (controlled) | users, borrowers, applications, consents, data_sources, transactions, appeals, notifications | ENABLE (owner-scoped policies to be added when direct-client access is introduced; SQL example in the script) |

Verified: 20 tables RLS-enabled; app SELECT on FORCE-RLS `predictions` still
returns rows (bypass confirmed).

## Storage — DONE

Private buckets `financial-documents`, `appeal-documents`, `generated-reports`,
`consent-evidence` created (`SupabaseStorageService.ensure_buckets`). Object path
`{borrower_id}/{application_id}/{file_id}` (appeals:
`.../appeals/{appeal_id}/{file_id}`). Upload validates MIME + computes SHA-256;
`data_sources` persists bucket/path/hash/size/mime. Short-lived signed URLs are
generated **server-side only** via `GET /applications/{id}/data-sources/{ds}/signed-url`
(object-level authorised). Service key never leaves the backend.

## Remaining USER INPUT REQUIRED

**None for the Supabase integration** — DB, Auth, Storage, and RLS are configured
and verified. The only outstanding product item is unrelated: a documented,
RM-scale labelled default dataset to move the model beyond development-grade (see
the main `USER_INPUT_REQUIRED.md`). Actual cloud deploy needs Vercel + Render/
Railway account credentials when you're ready (plan in `DEPLOYMENT_PLAN.md`).
