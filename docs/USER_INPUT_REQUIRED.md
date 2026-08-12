# MyCreditLens — User Input Required

Last updated: 2026-08-12

This file lists only inputs that genuinely require **you**. Everything else can proceed
locally without waiting. Items resolved since the earlier (2026-07-11) version are listed
at the bottom for the record.

---

## 1. Dataset decision — DECIDED: Option C (hybrid). Provenance still needed (MEDIUM)

**Decision made:** Option **C (hybrid)**. An inference-safe application-PD model is now
trained and wired end to end (see `IMPLEMENTATION_PROGRESS.md`, 2026-08-12 top entry).
Transaction/alternative-data features are preserved as a separate layer for a future
alternative-data model. This item is no longer a hard blocker to the MVP scoring workflow.

**What is still required from you (before any production/real-world claim):**
- A **defensible, licensed, documented default/repayment dataset** to replace the current
  training source. The active model uses
  `dataset for training/LoanDataset - LoansDatasest.csv` — a public CSV whose **provenance is
  undocumented in the repo**. Its metrics (ROC-AUC 0.866 held-out) are **development-grade
  only**, not evidence of real-world or Malaysian-market performance, and there is no
  out-of-time validation (the dataset has no application timestamp).
- For the **future alternative-data model**: a labelled dataset pairing historical
  transaction behaviour with a verified future default/repayment outcome. Home Credit
  (`dataset for training/archive (5)/`) is present but was rejected for the application-PD
  model because its predictive signal lives in bureau/prior-loan tables that MyCreditLens
  cannot reproduce at inference time.

**Exact format if you supply a new dataset:** name, source URL or local path, licence, target
column + definition, observation/default window, data dictionary, and any protected columns
to exclude.

**Can development continue without it:** Yes — the vertical slice works now with the current
labelled (clearly-flagged development-grade) model.

---

## 2. Supabase — FULLY INTEGRATED & VERIFIED (no input required)

**Resolved.** Both credentials were provided and configured in git-ignored
`backend/.env` (publishable key also in frontend `.env.local`). Supabase
**PostgreSQL + Auth (JWKS, live) + Storage (private buckets + signed URLs) + RLS**
are all working and verified (live API smoke + Playwright E2E on Postgres+Storage;
browser Supabase login provisioned for demo users). Details:
`docs/SUPABASE_INTEGRATION.md`. Nothing further needed here.

### (historical) previously-blocked items — now done

**Update (Phase 4):** Supabase **PostgreSQL is configured and working** — migrated
(`alembic upgrade head`), schema verified, seeded, RLS applied, and the full
vertical slice passes a live API smoke + Playwright E2E against Supabase Postgres
via the IPv4 pooler. Supabase **Auth JWKS verification** is implemented and
unit-tested. `DATABASE_URL`, `DATABASE_URL_SYNC`, `SUPABASE_URL`,
`SUPABASE_JWT_ISSUER/AUDIENCE/JWKS_URL` are set in git-ignored `backend/.env`.

**Still required from you (two credentials, never as `NEXT_PUBLIC_*` except the publishable key):**

- `SUPABASE_SECRET_KEY` (service-role key) — **backend only**. Needed to create the
  private Storage buckets (`financial-documents`, `appeal-documents`,
  `generated-reports`, `consent-evidence`) and to generate signed URLs. Obtain:
  Supabase dashboard → Project Settings → API → **service_role** secret. Store:
  `backend/.env` (never in the frontend or `NEXT_PUBLIC_*`). Until then, uploads
  use the local storage path.
- `SUPABASE_PUBLISHABLE_KEY` **and** `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` — the
  browser publishable/anon key. Needed for the frontend to perform a real
  Supabase-Auth login (the only unproven leg of the validation gate; the FastAPI
  JWKS verification side is done + tested). Obtain: Supabase dashboard → API →
  **publishable/anon** key. Store: `backend/.env` (`SUPABASE_PUBLISHABLE_KEY`) and
  frontend `.env.local` (`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`,
  `NEXT_PUBLIC_SUPABASE_URL`).

**Connectivity note:** the direct `db.<ref>.supabase.co` host is IPv6-only and not
reachable from this IPv4 network; the working config uses the **Supavisor session
pooler** (`aws-0-ap-northeast-2.pooler.supabase.com:5432`, user `postgres.<ref>`,
`sslmode=require`). Enable the IPv4 add-on if you want to use the direct host.

**Fallback in use:** SQLite is retained (commented `# SQLITE_FALLBACK` in
`backend/.env`) and remains the test database; revert by uncommenting.

---

## 3. JWT secret for anything shared/deployed (MEDIUM — local dev already secured)

**Update (Phase 0):** a strong random `JWT_SECRET` is now generated into
`backend/.env` (git-ignored, never printed), and `config.py` fails fast if the
secret is missing/default when `APP_ENV` is not development/test. Local dev is
secured.

**Still required from you for staging/production:** a distinct, strong per-
environment secret (do not reuse the local one). Provide it via the environment,
not committed:

```env
JWT_SECRET=<64+ char random string, unique per environment>
```

Obtain: generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
Store: deployment platform's secret manager / environment variables.

---

## 4. Demo user roles & deployment target (LOW)

- **Demo accounts:** current seed users are `analyst@lender.example`, `borrower@example.com`,
  `admin@mycreditlens.com` (`Password123!`) plus a second script using `*@mycreditlens.local`
  (`DemoPass123!`). Confirm the canonical demo set and whether a `compliance_reviewer` account
  is wanted. Fallback: keep the existing analyst/borrower/admin set.
- **Deployment target:** Vercel (frontend) + Render/Railway/Fly.io (backend) + Supabase, or a
  single VM? Fallback: local `docker-compose` + placeholder deployment docs.

---

## 5. Frontend tooling — no test harness; repo-wide lint OOMs (LOW, not blocking)

- **No frontend unit/E2E test runner** is configured (`package.json` has only
  `dev/build/start/lint/typecheck`; no jest/vitest/Playwright). Frontend
  validation currently relies on `tsc --noEmit` + `next build` (both pass).
  Decide whether to add Playwright for the 13-step E2E flow. Fallback: manual
  smoke via the running app.
- **`pnpm lint` (`eslint .`) runs out of memory** on the whole repo (a pre-existing
  flat-config/ignore issue, not a code error — changed files lint clean with a
  raised heap). Fallback: lint specific paths with
  `NODE_OPTIONS=--max-old-space-size=4096`. A later fix should add proper `ignores`
  to `eslint.config.mjs`.
- The frontend `node_modules` was found broken (dangling symlinks); it was
  repaired with `pnpm install`. If you clone fresh, run `pnpm install` (or
  `corepack pnpm install` with `CI=true`) before building.

## 6. Decision Room advanced panels — backend endpoints (LOW, optional)

The application detail page's reliability / model-agreement / integrity /
timeline / cash-flow panels still render seeded-PRNG mock (no backend source).
To make them real, decide whether to build endpoints (data-reliability from
`data_sources`, cash-flow from the transaction pipeline, timeline from
`audit_logs`, integrity from `integrity_alerts`) or to display explicit
"Not available" states. Not blocking — score, SHAP, counterfactual, stress, and
decision on that page are already real.

## Resolved since 2026-07-11 (no longer blocking)

- **Local Python runtime — RESOLVED.** Python 3.12.10 is installed and on PATH; `backend/.venv`
  exists. Backend imports and `pytest` runs (8 passed).
- **Frontend dependency installation — RESOLVED.** `node_modules/` is present; `package.json`
  now includes the real stack (Next 16, React 19, Supabase JS, Recharts). (Frontend lint/build
  not yet run in this pass, but dependencies are installed.)
- **External API keys / deployment credentials — not required** to continue local MVP work.
