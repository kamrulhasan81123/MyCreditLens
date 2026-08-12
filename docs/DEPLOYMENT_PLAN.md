# Deployment Plan

Last updated: 2026-08-13

Architecture (unchanged): **Next.js → FastAPI → Supabase PostgreSQL + Storage**,
auth **Next.js → Supabase Auth → access token → FastAPI JWKS verification**.
No Edge Functions for scoring, no microservices, no Kubernetes. ML inference runs
in FastAPI loading versioned tabular artifacts.

## Backend host: **Render** (recommended) — Railway as equivalent alternative

Evaluated Render vs Railway for this repo:

- **Render (recommended):** first-class long-running Python/Docker web service,
  simple `render.yaml`, persistent process (keeps the model bundle warm in
  memory), straightforward secret env management, built-in health checks. Best
  fit for a single FastAPI service that loads model artifacts at startup.
- **Railway (viable alternative):** equally capable (Nixpacks/Dockerfile,
  env vars, private networking). Choose it if you prefer its DX/pricing; the
  service definition below maps 1:1.

Either way: **one** backend web service, model artifacts baked into the image
(`backend/ml/artifacts/application_pd/`, a few MB), Supabase as the managed
DB/Auth/Storage.

## Environment-variable matrix

| Variable | Frontend (Vercel) | Backend (Render/Railway) | Secret? | Source |
|---|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | ✅ | — | no | backend public URL + `/api/v1` |
| `NEXT_PUBLIC_SUPABASE_URL` | ✅ | — | no | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | ✅ | — | no (publishable) | Supabase → API keys |
| `DATABASE_URL` | — | ✅ | **yes** | Supabase pooler (asyncpg, session mode) |
| `DATABASE_URL_SYNC` | — | ✅ | **yes** | Supabase pooler (psycopg2, `?sslmode=require`) |
| `SUPABASE_URL` | — | ✅ | no | project URL |
| `SUPABASE_PUBLISHABLE_KEY` | — | ✅ | no | API keys |
| `SUPABASE_SECRET_KEY` | — | ✅ | **yes** | API keys (service role) — Storage/admin only |
| `SUPABASE_JWT_ISSUER` | — | ✅ | no | `<url>/auth/v1` |
| `SUPABASE_JWT_AUDIENCE` | — | ✅ | no | `authenticated` |
| `SUPABASE_JWKS_URL` | — | ✅ | no | `<url>/auth/v1/.well-known/jwks.json` |
| `JWT_SECRET` | — | ✅ | **yes** | unique per environment (`secrets.token_urlsafe(48)`) |
| `MODEL_ARTIFACT_PATH` | — | ✅ | no | `./ml/artifacts/application_pd` |
| `APP_ENV` | — | ✅ | no | `production` / `staging` |
| `CORS_ORIGINS` | — | ✅ | no | the Vercel frontend origin(s) |

Secrets live only in the platform's secret store — never in the repo, frontend
bundle, docs, or `NEXT_PUBLIC_*`.

## Steps

### Local setup
```
cd backend && python -m venv .venv && .venv\Scripts\pip install -r requirements.txt
# backend/.env: DATABASE_URL(_SYNC) → pooler, SUPABASE_*, JWT_SECRET
.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python -m app.scripts.seed_demo
.venv\Scripts\python -m uvicorn app.main:app --port 8000
# frontend: corepack pnpm install && pnpm dev
```

### Supabase setup
- Enable IPv4 add-on OR use the Supavisor pooler host/user (this project uses the pooler).
- Apply RLS: `psql "$DATABASE_URL_SYNC" -f backend/scripts/apply_rls.sql`.
- Create private Storage buckets (needs service-role key): `financial-documents`,
  `appeal-documents`, `generated-reports`, `consent-evidence`.

### Vercel (frontend)
- Root = repo; framework Next.js; build `pnpm build`; set the four `NEXT_PUBLIC_*` vars.

### Backend host (Render example `render.yaml`)
- Docker or Python env; start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`;
  health check path `/health`; set all backend env vars above.

### Migration / seed commands
- Migrate: `python -m alembic upgrade head`
- Seed demo: `python -m app.scripts.seed_demo`
- Register active model: `POST /api/v1/models/registry/sync` (admin) or it self-registers on first score.

### Model-artifact deployment
- `backend/ml/artifacts/application_pd/` is committed and shipped in the image.
  `MODEL_ARTIFACT_PATH` points at it; `/health/model` must report `ready` post-deploy.

## Health checks
- `GET /health` (liveness), `GET /health/database` (DB reachable),
  `GET /health/model` (must be `ready` with real dry-run inference).

## Smoke test (post-deploy)
`python backend/scripts/smoke_test.py https://<backend-url>` — proves auth →
score(200) → persist → explanation → stress → counterfactual → decision → audit →
object-level 404 isolation.

## Rollback
- Backend: redeploy the previous image/commit (model bundle is immutable in-image).
- DB: `alembic downgrade -1` (migrations `0002`/`0003` are reversible and additive).
- Model: `MODEL_ARTIFACT_PATH` → an archived bundle under `ml/artifacts/_archive/`;
  never delete the active `2.0.0` bundle.

## Backup
- Supabase automated Postgres backups (enable PITR on the project). Storage objects
  are retained in their buckets. Export `ml_models` + artifacts with each release.

## Staging workflow
- Separate Supabase project (or schema) + separate backend service + Vercel preview.
- Distinct `JWT_SECRET`, DB URLs, and buckets. Run `alembic upgrade head` + smoke
  before promoting.

## Demo workflow
- Seed with `app.scripts.seed_demo` (synthetic personas, no real PII). Demo logins:
  `admin@mycreditlens.com`, `analyst@mycreditlens.com`, `compliance@mycreditlens.com`,
  `borrower@example.com` (`DemoPass123!`).

## Not yet possible (needs credentials)
- Actual cloud deploy requires the Vercel + Render/Railway account credentials.
- Storage bucket creation requires `SUPABASE_SECRET_KEY`.
