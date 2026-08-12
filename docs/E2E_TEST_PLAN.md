# End-to-End Test Plan (Playwright)

Last updated: 2026-08-13

Playwright drives the full MyCreditLens workflow against a running stack
(FastAPI backend + Next.js frontend). Uses **isolated E2E accounts/records** with
repeatable cleanup, and never asserts on fabricated data.

## Prerequisites
- Backend running on `http://127.0.0.1:8000` (`uvicorn app.main:app`), DB migrated + seeded.
- Frontend dev server on `http://127.0.0.1:3000` (Playwright `webServer` starts it).
- `pnpm exec playwright install chromium` (one-time browser download).

Run: `pnpm exec playwright test` (config: `playwright.config.ts`).

## Isolation & cleanup
- Each run registers a **unique borrower** (`e2e-<timestamp>@example.com`) and its
  own application, so runs don't collide. Staff accounts use the seeded demo
  analyst/admin. Records are development-grade demo data; a teardown project can
  delete the run's application via API if desired.

## Covered workflow (spec: `e2e/full-workflow.spec.ts`)

| # | Step | Assertion |
|---|---|---|
| 1 | Borrower authentication | sign-in → borrower dashboard |
| 2 | Borrower profile | profile fields persist (`/borrowers/me`) |
| 3 | Create application | real application id returned (no `APP-2041`) |
| 4 | Consent | consent recorded |
| 5 | Financial-data upload | data source stored |
| 6 | Transaction validation | records parsed / reliability shown |
| 7 | Submit application | status → submitted |
| 8 | Analyst authentication | analyst sign-in |
| 9 | Analyst application view | application detail loads |
| 10 | Real PD score | `POST /score` 200; PD + band shown; version `2.0.0` |
| 11 | Real model metadata | model name/version from `/models/metadata` |
| 12 | SHAP | explanation factors present (real feature names) |
| 13 | Decision Room | `/decision-room` blocks render (real or `not_available`) |
| 14 | Data reliability | real value or `insufficient_data` |
| 15 | Stress test | `POST /stress-tests` 200 |
| 16 | Counterfactual | `POST /counterfactuals` 200 |
| 17 | Analyst decision | decision recorded (201) |
| 18 | Borrower explanation | borrower can view explanation |
| 19 | Borrower appeal | appeal created |
| 20 | Audit / timeline | audit entries present for the application |

## Status
- Config + spec are committed. Running requires both servers up + the Chromium
  download. Results are reported honestly; a skipped/blocked run is never reported
  as passed. Where the live Supabase-Auth login is used instead of local JWT, the
  `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` must be configured (otherwise the spec
  uses the local-JWT sign-in path).
