# Frontend Integration Matrix (Phase 3)

Last updated: 2026-08-12

Truthfulness audit of every major page/component: its data source, the backend
endpoint, and whether it uses real data, mock data, or honest "unavailable"
states. **No UI redesign** — layout, design system, components, and routes are
preserved. Only data wiring changed.

**Key finding (audit):** there is **no silent mock fallback on API failure**
anywhere — every real API caller surfaces errors to the UI. The gaps were
components that rendered mock/fabricated data *unconditionally* (never calling the
backend) and one fake submission.

Legend — API status: ✅ wired to real backend · 🟡 partial/hybrid · 🔴 mock/fabricated · ⛔ non-persisting stub.

## Lender pages

| Route / component | Current data source | Backend endpoint | API | Mock/hardcoded before | Change made | Status |
|---|---|---|---|---|---|---|
| `app/lender/page.tsx` (overview) | `useApplications`/`useBorrowers` | `GET /applications`, `/borrowers` | ✅ | none | — | Done (already real) |
| `app/lender/applications/page.tsx` | `useApplications` | `GET /applications` | ✅ | none | — | Done |
| `app/lender/applications/[id]` — score + SHAP | `useApplication` + `scoringApi.getExplanation` | `GET /applications/{id}`, `/explanations` | ✅ | none | — | Done (real score/version/SHAP) |
| `app/lender/applications/[id]` — counterfactual / stress panels | `aiApi` | `POST /counterfactuals`, `/stress-tests` | ✅ | none | — | Done |
| `app/lender/applications/[id]` — decision panel | `decisionsApi.create` | `POST /applications/{id}/decisions` | ✅ | none | — | Done |
| `app/lender/applications/[id]` — reliability / model-agreement / integrity / timeline / cash-flow tabs | `src/features/applications/mock-data/*` (seeded PRNG) | **`GET /applications/{id}/decision-room` (NEW, real)** | 🔴→🟡 | fabricated values | **Backend now real** (data reliability, cash-flow, integrity, model-agreement=insufficient_data, timeline — with `not_available`/`insufficient_data`). `decisionRoomApi.get` added. **UI panel wiring is the remaining frontend task.** | Backend done; UI wiring pending |
| `app/lender/assessments/new` (`assessment-wizard.tsx`) | was `setTimeout`→`APP-2041` | `POST /applications` → `/consents` → `/submit` | 🔴→✅ | fake submit + hardcoded `APP-2041` | **Rewired to real create→consent→submit→real id**; loading/error/retry; no fabricated success | Done |
| `app/lender/monitoring/page.tsx` | was `lib/mock-data` (AUC 0.78, Brier 0.121, drift, calibration) | `GET /monitoring/summary`, `/models/metadata` | 🔴→✅ | hardcoded AUC/Brier/drift/calibration | **Rewired to real DB-backed summary**; production performance shown as `outcome_data_unavailable`; dev-grade metrics labelled | Done |
| `app/lender/fairness/page.tsx` | was `lib/mock-data` (`FAIRNESS_BY_SEGMENT`) | `GET /fairness/age-band-audit` | 🔴→✅ | mock segments/DI/FPR/FNR | **Rewired to real age-band audit** on eval split; small-sample flags; "not a certification" note | Done |
| `app/lender/portfolio/page.tsx` | `useApplications` | `GET /applications` | ✅ | none | — | Done |
| `app/lender/borrowers/page.tsx` | `useBorrowers` | `GET /borrowers` | ✅ | none | — | Done |
| `app/lender/audit/page.tsx` | `auditApi.list` | `GET /audit-logs` | ✅ | `ip` shown as "not captured" | — | Done |
| `components/lender/settings-form.tsx` | local state; toast only | *(no settings endpoint)* | ⛔ | hardcoded org/regulator/PD defaults | Documented; non-persisting stub (out of scope) | Pending |
| `app/lender/api/page.tsx` | static info card | n/a | ✅ | honest (no fake keys) | — | Done |

## Borrower pages

| Route / component | Backend endpoint | API | Status |
|---|---|---|---|
| `app/borrower/page.tsx` (dashboard) | `GET /applications` | ✅ | Done |
| `app/borrower/new-application` | `POST /applications` → `/consents` → `/submit` | ✅ | Done (the reference real flow) |
| `app/borrower/connected-data` | `/applications`, `/data-sources` (list+upload) | ✅ | Done |
| `app/borrower/consent` | `/consents` (list/grant/revoke) | ✅ | Done |
| `app/borrower/documents` | `/data-sources` | ✅ | Done |
| `app/borrower/profile` | `authApi.me` + `borrowersApi.me`/`updateMe` | ✅ | Done |
| `app/borrower/messages` | local state only | ⛔ | Pending (no messages endpoint; non-persisting stub) |

## New backend endpoints added this phase (read-only, safe)

| Endpoint | Purpose | Role guard |
|---|---|---|
| `GET /models/active` | active model registry status (safe fields) | any authenticated |
| `GET /models/metadata` | model-card-safe metadata (no paths/secrets) | any authenticated |
| `POST /models/registry/sync` | upsert active bundle into `ml_models` | admin |
| `GET /monitoring/summary` | DB-backed monitoring; `performance_status=outcome_data_unavailable` | admin/analyst/compliance |
| `GET /fairness/age-band-audit` | real age-band fairness on eval split | admin/compliance |
| `GET /calibration/segments` | calibration by age band on eval split | admin/compliance |

## Decision Room — remaining (documented, not fabricated)

The application detail page is a **hybrid**: application record, probability,
calibrated probability, risk band, model name/version, SHAP factors,
counterfactuals, stress tests, and analyst decision are **real**. The
reliability score, model-agreement level, integrity alerts, audit timeline, and
cash-flow chart are still sourced from `src/features/applications/mock-data/*`
(seeded PRNG). These have **no backend endpoint yet**. Recommended next step:
either (a) build endpoints (data-reliability from `data_sources.reliability_score`,
cash-flow/transactions from the transaction pipeline, timeline from `audit_logs`,
integrity from `integrity_alerts`) and wire them, or (b) replace the fabricated
values with explicit "Not available / Not calculated / Insufficient data" states.
Until then they remain the only fabricated surfaces and are flagged here.

## Dead code noted (not removed — no behaviour impact)

- `NEXT_PUBLIC_DEMO_MODE` — defined in env, never read anywhere.
- `lib/mock-data.ts` — ~80% dead exports after monitoring/fairness were rewired;
  only Decision Room mock files still consumed. Safe to delete in a later cleanup.
