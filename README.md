# MyCreditLens

AI-powered **credit-assessment decision-support** MVP for thin-file and
alternative-income borrowers (gig workers, micro-entrepreneurs, small merchants).
A borrower's application is scored by a calibrated probability-of-default (PD)
model; analysts review the result in a **Decision Room** with SHAP explanations,
data-reliability and cash-flow evidence, stress tests, counterfactuals, and a full
audit trail.

> **Status: development-grade MVP.** The active model is trained on a public
> dataset whose original provenance has not been independently verified. It is
> **not** a production-validated, Malaysian-validated, regulator-certified, or
> autonomous lending system. Every decision requires a human analyst.

---

## What it does

- **Application → PD score.** A borrower application (age, income, employment,
  home ownership, loan intent, amount, term) is mapped by an explicit
  `ApplicationToModelAdapter` to the model's feature contract, scored, calibrated,
  and persisted with a risk band, uncertainty, and OOD signal.
- **Explainability.** Real SHAP contributions with human-readable reason codes.
- **Decision Room.** Consolidated, backend-computed view: scoring, SHAP, data
  reliability, cash-flow analytics, integrity alerts, model agreement, and a
  timeline — returning `not_available` / `insufficient_data` rather than fabricating
  values.
- **Stress tests & counterfactuals** over the same feature contract.
- **Monitoring & fairness.** DB-backed monitoring (no fabricated production
  metrics — reports `outcome_data_unavailable` until real repayment outcomes
  exist) and an age-band fairness + calibration-by-segment audit on the model's
  held-out evaluation split.
- **Alternative-data pipeline** (transaction ingestion, cash-flow features, data
  reliability, integrity signals) kept **separate** from the application-PD model
  as analyst evidence — not a statistically validated PD predictor (yet).

### Active model

`application_pd_hist_gradient_boosting` **v2.0.0** — HistGradientBoosting on 8
inference-safe application features, sigmoid-calibrated, held-out test
ROC-AUC ≈ 0.867 / PR-AUC ≈ 0.733 / Brier ≈ 0.097 (development-grade). Bundle:
`backend/ml/artifacts/application_pd/` (committed). See its `model_card.md`.

---

## Architecture

```
Next.js (App Router)  →  FastAPI  →  Supabase PostgreSQL + Storage
      │                     │
   Supabase Auth  →  access token  →  FastAPI JWKS verification
                          │
                    ML inference (versioned tabular artifacts, SHAP, OOD)
```

- **Frontend:** Next.js 16, React 19, Tailwind, Recharts.
- **Backend:** FastAPI, SQLAlchemy 2.0 (async), Alembic, scikit-learn / XGBoost /
  LightGBM / SHAP.
- **Data/Auth/Storage:** Supabase (PostgreSQL, Auth with asymmetric JWT/JWKS,
  private Storage buckets, RLS). **SQLite** is a supported lightweight local /
  test fallback.
- Auth is **hybrid**: Supabase Auth (JWKS-verified) in the browser, with local
  HS256 JWT as a development fallback.

---

## Repository layout

```
app/, components/, src/, lib/     Next.js frontend
backend/
  app/            FastAPI (routers, services, models, ai runtime + adapter)
  ml/             training pipeline, datasets, model artifacts (application_pd/)
  alembic/        migrations
  scripts/        smoke_test, seed, provision_supabase_users, apply_rls.sql
  tests/          pytest (unit + gated Supabase integration)
e2e/              Playwright API workflow spec
docs/             architecture, Supabase, deployment, dataset, and progress docs
```

Key docs: `docs/IMPLEMENTATION_PROGRESS.md`, `docs/SUPABASE_INTEGRATION.md`,
`docs/DEPLOYMENT_PLAN.md`, `docs/E2E_TEST_PLAN.md`,
`docs/FRONTEND_INTEGRATION_MATRIX.md`, `docs/USER_INPUT_REQUIRED.md`.

---

## Prerequisites

- Python 3.12, Node 18+ with `pnpm` (via `corepack`), Git.
- (Optional) A Supabase project for the managed Postgres/Auth/Storage path.

---

## Configuration

Secrets are **never** committed. Copy the examples and fill real values locally:

```bash
cp backend/.env.example backend/.env      # backend secrets (git-ignored)
# create .env.local for the frontend (git-ignored)
```

**`backend/.env`** (see `backend/.env.example` for the full list):

| Variable | Purpose |
|---|---|
| `DATABASE_URL` / `DATABASE_URL_SYNC` | async / sync DB URLs. Default = local SQLite (works out of the box). For Supabase use the **IPv4 session pooler** host `aws-0-<region>.pooler.supabase.com:5432`, user `postgres.<project_ref>`, `?sslmode=require`. |
| `JWT_SECRET` | local-JWT signing (generate: `python -c "import secrets;print(secrets.token_urlsafe(48))"`). Required non-default outside development. |
| `MODEL_ARTIFACT_PATH` | `./ml/artifacts/application_pd` |
| `SUPABASE_URL`, `SUPABASE_JWT_ISSUER`, `SUPABASE_JWT_AUDIENCE`, `SUPABASE_JWKS_URL` | Supabase Auth (non-secret) |
| `SUPABASE_PUBLISHABLE_KEY` | browser/anon key (non-secret) |
| `SUPABASE_SECRET_KEY` | **service-role key — backend only, never in the frontend** (Storage admin/signed URLs) |
| `SUPABASE_VERIFY_SSL` | keep `true` (secure) in normal networks; set `false` only behind a TLS-inspecting proxy |

**`.env.local`** (frontend, browser-safe only):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_SUPABASE_URL=https://<project_ref>.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=<publishable key>
```

> If Supabase is not configured, the app runs fully on local SQLite + local JWT
> auth + local file storage.

---

## Run it

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv
# Windows:            .venv\Scripts\pip install -r requirements.txt
# macOS/Linux: source .venv/bin/activate && pip install -r requirements.txt

# apply migrations + seed demo data (synthetic, no real PII)
.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python -m app.scripts.seed_demo

# run
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Health: `GET /health`, `GET /health/database`, `GET /health/model` (must report
`ready`). API docs at `http://localhost:8000/api/docs`.

Supabase-only helpers (when configured): apply RLS
`psql "$DATABASE_URL_SYNC" -f backend/scripts/apply_rls.sql`; provision Supabase
Auth demo users `python -m scripts.provision_supabase_users`.

### Frontend (Next.js)

```bash
corepack pnpm install
corepack pnpm dev            # http://localhost:3000
```

### Demo logins (from the seed)

`admin@mycreditlens.com`, `analyst@mycreditlens.com`,
`compliance@mycreditlens.com`, `borrower@example.com` — password `DemoPass123!`.

---

## Datasets (not committed)

The `dataset for training/` folder (incl. the large Home Credit archive) is
**git-ignored**. The committed model bundle lets the app score/explain without
it. To **retrain**, or to run the eval-set **fairness/calibration** endpoints,
re-place the training CSV(s) under `dataset for training/`; those endpoints
otherwise return `dataset_unavailable` (handled gracefully). Retrain:

```bash
cd backend
.venv\Scripts\python -m ml.train_application_pd \
  --dataset "../dataset for training/LoanDataset - LoansDatasest.csv" \
  --output-dir ml/artifacts/application_pd
```

---

## Testing

```bash
# backend unit suite (SQLite, offline)
cd backend && .venv\Scripts\python -m pytest -q
# live Supabase integration (needs configured Supabase)
RUN_SUPABASE_IT=1 .venv\Scripts\python -m pytest tests/test_supabase_integration.py -q
# API smoke against a running server
.venv\Scripts\python scripts/smoke_test.py http://127.0.0.1:8000

# frontend
corepack pnpm run typecheck && corepack pnpm run lint && corepack pnpm run build
# end-to-end (starts the backend automatically)
corepack pnpm run test:e2e
```

---

## Deployment

Target: Vercel (frontend) + Render/Railway (backend) + Supabase
(DB/Auth/Storage). Full env matrix, migration/seed/rollback/backup/staging steps
are in **`docs/DEPLOYMENT_PLAN.md`**.

## License / data notes

Development/educational MVP. Datasets referenced are public; the primary training
dataset's provenance is undocumented and its metrics are development-grade only.
Do not present the model as production- or regulator-validated.
