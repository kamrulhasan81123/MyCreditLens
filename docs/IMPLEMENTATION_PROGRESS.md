# MyCreditLens Implementation Progress

Last updated: 2026-08-12

---

## 2026-08-13 — Phase 4b Supabase Auth + Storage COMPLETE (model 2.0.0 unchanged)

Both Supabase credentials were provided; the integration is now **fully working
and verified**. Model 2.0.0 unchanged.

- **Auth (live, proven):** admin-create confirmed user (service key) → login
  (publishable key) → real ES256 token → backend JWKS verify (sig/iss/aud/exp,
  `sub`→user). Demo users provisioned in Supabase Auth with roles
  (`scripts/provision_supabase_users.py`) → **browser Supabase login works**
  (analyst → role `credit_analyst`). Verifier honours a `SUPABASE_VERIFY_SSL` flag
  (default true; false only in this TLS-inspecting sandbox).
- **Storage (live, proven):** `app/services/storage_service.py` — 4 **private**
  buckets created + verified; upload (MIME validation + SHA-256) → signed-URL
  fetch (200, bytes match) → delete round-trip; wired into data-source upload
  (local fallback retained); signed-URL retrieval endpoint (object-level
  authorised). Service key server-side only.
- **Config:** `SUPABASE_SECRET_KEY` + `SUPABASE_PUBLISHABLE_KEY` in git-ignored
  `backend/.env`; `NEXT_PUBLIC_SUPABASE_URL/PUBLISHABLE_KEY` in `.env.local`. No
  secret in code/docs/logs/responses/frontend bundle. (Secret confirmed present;
  publishable key is browser-safe by design.)
- **Decision Room frontend:** Summary cash-flow now uses the real
  `decision-room` endpoint (real income/expense/net/balance/savings or explicit
  "Not available"); fabricated `CASHFLOW_TREND` removed. Remaining Decision-Room
  sub-panels (reliability/model-agreement/integrity/timeline) still consume typed
  mock helpers — the real endpoint + `decisionRoomApi` are ready; that deeper
  component refactor is the last frontend item.
- **Tests:** gated live `tests/test_supabase_integration.py` (storage + MIME +
  auth JWKS) — **3 passed** with `RUN_SUPABASE_IT=1`; offline suite **53 passed,
  3 skipped**. Frontend **typecheck/lint/build 0**. **Playwright E2E 1 passed**
  on Postgres+Storage. API smoke passed.

---

## 2026-08-13 — Phase 4 Supabase migration + Decision Room + E2E (model 2.0.0 unchanged)

Active model still `application_pd_hist_gradient_boosting 2.0.0`. All regressions
green: **backend 53 tests pass** (47 + 6 Supabase-JWKS auth), frontend
**typecheck 0 / lint 0 / build 0** (ESLint OOM fixed via ignores), **Playwright
E2E 1 passed** (full 20-step workflow over the live Supabase Postgres backend).

**Supabase database migration — DONE & verified** (details: `docs/SUPABASE_INTEGRATION.md`):
- Direct `db.<ref>` host is IPv6-only/unreachable here → use the **IPv4 Supavisor
  session pooler** (`aws-0-ap-northeast-2.pooler.supabase.com:5432`, user
  `postgres.<ref>`, TLS require). `app/database.py` wires require-mode SSL for
  asyncpg; sync URL carries `?sslmode=require`. Config written only to git-ignored
  `backend/.env` (SQLite retained as `# SQLITE_FALLBACK`); no secrets in code/docs.
- `alembic upgrade head` → `0001/0002/0003` (new `0003` widens
  `engineered_features.feature_version` to VARCHAR(64) — a real bug Postgres
  exposed that SQLite hid). Schema verified: 21 tables, 43 FKs, 19 enum types, 27
  indexes. Seeded full slice; persistence verified (predictions carry real
  version 2.0.0). Live API smoke on Postgres passed.
- **RLS applied** (`backend/scripts/apply_rls.sql`, idempotent): backend-only
  tables ENABLE+FORCE (deny anon/authenticated); controlled tables ENABLE. App
  connects as `postgres` (rolbypassrls=true, verified) so it's unaffected. FastAPI
  authz remains primary.
- **Tests pinned to SQLite** in `conftest.py` (fast, never touch the live DB).

**Auth (Supabase JWKS) — implemented + unit-tested:** the existing hybrid
`get_current_user` verifies ES256 tokens via JWKS (sig/iss/aud/exp), maps
`sub`→user, stores no Supabase password. New `tests/test_supabase_auth.py`
(mock EC keypair) covers valid/expired/wrong-issuer/wrong-audience/bad-signature/
unconfigured. Local HS256 JWT stays the dev fallback.

**Decision Room backend — real** (`app/services/decision_room_service.py`,
`GET /applications/{id}/decision-room`, staff-only): application, scoring, SHAP,
data reliability (from `data_sources`), cash-flow analytics (from the transaction
pipeline — analyst evidence, NOT a PD input), integrity alerts (persisted +
deterministic duplicate/income-mismatch checks), model agreement
(`insufficient_data` — only one inference-compatible model), and a real timeline
(app timestamps + audit + decisions). Uncomputable values return
`not_available`/`insufficient_data` — never fabricated. `decisionRoomApi` added
to `lib/api-client.ts`.

**Playwright E2E** installed + configured (`playwright.config.ts`,
`e2e/full-workflow.spec.ts`, `pnpm test:e2e`) — API-driven, isolated per run,
covers all 20 workflow steps incl. appeal + timeline. **1 passed** against
Supabase Postgres.

**Deployment prep:** `docs/DEPLOYMENT_PLAN.md` (env matrix, Render recommended /
Railway alternative, migration/seed/rollback/backup/staging/demo), plus
`docs/SUPABASE_INTEGRATION.md` and `docs/E2E_TEST_PLAN.md`.

**Still blocked on missing credentials (see `USER_INPUT_REQUIRED.md`):**
`SUPABASE_SECRET_KEY` (service-role) for Storage buckets/signed URLs, and
`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` for the browser Supabase-Auth login (the
only unproven leg of the validation gate; the FastAPI JWKS side is done + tested).
Frontend Decision Room **UI panels** still render seeded mock — the real endpoint
is ready (`decisionRoomApi`); wiring the panels is the remaining frontend task.

---

## 2026-08-12 — Phase 3 frontend truthfulness + insight endpoints (baseline unchanged)

Model 2.0.0 remains active and untouched. Backend suite still green (47 passing:
40 prior + 7 new insight tests, at time of the backend run below). No UI redesign —
only data wiring and new read-only backend endpoints.

**Audit finding:** the frontend has **no silent mock-fallback-on-error** anywhere
(every API caller surfaces errors). The real gaps were components rendering mock
data *unconditionally* and one fake submission. Full matrix:
`docs/FRONTEND_INTEGRATION_MATRIX.md`.

**New backend (read-only, safe — no paths/secrets exposed):**
- `app/services/insights_service.py` + `app/routers/insights.py` (registered in
  `main.py`): `GET /models/active`, `GET /models/metadata`,
  `POST /models/registry/sync` (admin), `GET /monitoring/summary`,
  `GET /fairness/age-band-audit`, `GET /calibration/segments`.
- Monitoring is DB-backed and reports `performance_status=outcome_data_unavailable`
  (no fabricated production ROC-AUC/calibration). Fairness/calibration are real
  age-band measurements on the model's held-out eval split, with small-sample
  flags and an explicit "not a legal/regulatory certification" note.
- Model registry: `sync_registry()` upserts the active bundle into `ml_models`
  (version 2.0.0, algorithm, metrics, provenance status, feature schema version)
  and keeps `model_path` server-side only.
- New tests `backend/tests/test_insights.py`: metadata safety (no paths/secrets),
  registry sync, monitoring truthfulness, age-band fairness + small groups,
  calibration insufficient-sample handling, role guards.

**Frontend wiring (layout preserved):**
- `components/lender/assessment-wizard.tsx`: replaced the fake `setTimeout` →
  hardcoded `APP-2041` submission with a real `POST /applications` →
  `/consents` (per source + `credit_scoring`) → `/submit` chain that navigates to
  the **real** returned application id, with loading/error/retry (no fabricated
  success; honest error when the role model forbids the action).
- `app/lender/monitoring/page.tsx`: rewired to `GET /monitoring/summary` +
  `/models/metadata`; KPIs (total predictions, OOD rate, manual-review rate, mean
  uncertainty), volume-over-time, risk-band and PD distributions are real;
  production performance shown honestly as unavailable with dev-grade metrics
  labelled.
- `app/lender/fairness/page.tsx`: rewired to `GET /fairness/age-band-audit`; real
  per-band observed-default / mean-PD / flag-rate / FPR / FNR / sample, disparate
  impact ratio + equal-opportunity difference, small-sample warnings.
- `lib/api-client.ts`: added `modelApi`, `monitoringApi`, `fairnessApi`.

**Remaining (documented, not fabricated):** Decision Room sub-panels (reliability,
model-agreement, integrity, timeline, cash-flow) still use seeded-PRNG mock — they
have no backend endpoint yet; flagged in the matrix for either endpoint-building or
"Not available" states. `messages` and lender `settings-form` are non-persisting
stubs. `lib/mock-data.ts` is now ~80% dead.

**Frontend build:** the pre-existing frontend dependency install was broken
(dangling `node_modules` symlinks; `.pnpm-store` ~empty), so lint/typecheck/build
could not run initially; a `pnpm install` repair was performed (see
`USER_INPUT_REQUIRED.md`/this run's notes). Frontend unit/E2E test harness is not
configured in `package.json` (no jest/vitest/Playwright) — validation relies on
typecheck + `next build`.

---

## 2026-08-12 — Phase 2 dataset research + retraining decision (baseline unchanged)

A dataset-research and model-improvement phase was run to decide whether a
better-documented, less-synthetic, more-defensible dataset can **materially
improve** the model while preserving inference compatibility. **The objective was
a decision, not a retrain.** Outcome: **RETRAINING_NOT_JUSTIFIED for promotion —
model 2.0.0 remains active and untouched.** All 40 tests still pass; `/health/model`
= `ready` (application_pd_hist_gradient_boosting 2.0.0); `MODEL_ARTIFACT_PATH`
unchanged.

**What was done (all additive — no change to the active bundle, scoring code, or
`MODEL_ARTIFACT_PATH`):**
- Full recursive **dataset inventory** → `docs/DATASET_INVENTORY.md`.
- **Weighted comparison** → `docs/DATASET_COMPARISON_REPORT.md` (LoanDataset 0.660
  vs Home Credit 0.658 — a tie broken by the inference gate + executed evidence).
- **Inference-compatibility gate + decision** → `docs/RETRAINING_DECISION.md`
  (Home Credit maps to only 6 of 8 features; its strong features are proprietary
  `external_source_*`/bureau; **0% of its loans overlap MyCreditLens's loan range**).
- **Home Credit research challenger** `2.1.0-challenger` trained as executed
  evidence (`ml/experiments/home_credit_challenger.py`, artifacts under
  `ml/artifacts/_challenger/`, **not promoted**): application-only held-out
  ROC-AUC **0.626** vs active **0.867**. → `docs/MODEL_2_1_EVALUATION.md`.
- **Alternative-data dataset search** → `docs/ALTERNATIVE_DATA_DATASET_RESEARCH.md`
  (no defensible public transaction→default dataset exists; alt-data model stays a
  future validation task, not faked).
- **Phase 2B collection:** downloaded **UCI Default of Credit Card Clients**
  (Taiwan benchmark) and **OpenDOSM** household income (Malaysian localisation
  context only); organised all datasets under `backend/ml/data/raw/<name>/` with
  `README_source.md` + `dataset_manifest.json` (raw files unmodified). Added
  `xlrd` to requirements for the legacy `.xls` benchmark.

**Why not retrain:** Home Credit has better provenance but regresses discrimination
(0.63 vs 0.87) and deployment validity (0% input-scale overlap; silent
extrapolation on real applicants). UCI/South German/Microloan are inference-
incompatible benchmarks. No dataset improves the *deployed* model without a
confirmed regression. The strongest real upgrade would be a documented, RM-scale,
labelled default dataset (see `docs/USER_INPUT_REQUIRED.md`).

---

## 2026-08-12 — Phase 0 + Phase 1 COMPLETE (AUTHORITATIVE, supersedes all below)

The scoring vertical slice is now functional end to end with a newly trained,
inference-safe application-PD model. **CRITICAL BLOCKER #1 (feature-contract
mismatch) is RESOLVED.** The earlier claim that scoring worked was false when the
runtime was broken; it is now true and verified by automated tests and a live API
smoke test (evidence below). No Git actions were taken (per project instruction).

### Dataset / scoring direction — Option C (hybrid)

Application fields → core PD model → calibrated probability of default.
Transaction / bank-statement features remain a **separate** alternative-data layer
(reliability, cash-flow, integrity, stress/counterfactual context) and are **not**
inputs to the PD model. A future alternative-data model is deferred until a
defensible labelled transaction/default dataset exists.

### Phase 0 — runtime & configuration safety

- `MODEL_ARTIFACT_PATH` aligned to the active bundle `./ml/artifacts/application_pd`
  in both `backend/.env` and `app/config.py`; relative paths now resolve against the
  backend package (CWD-independent) via `settings.resolved_model_artifact_path`.
- Generated a strong development `JWT_SECRET` into `backend/.env` (git-ignored,
  never printed). `config.py` now **fails fast** if `APP_ENV` is not
  development/test and the secret is missing or still the placeholder.
- `.env.example` contains placeholders only.
- `/health/model` rewritten to a **truthful** readiness check: it loads the bundle,
  confirms the application adapter can satisfy the schema, produces a deterministic
  dry-run input, and executes real inference. States: `ready`, `artifact_missing`,
  `load_failed`, `schema_incompatible`, `inference_failed`. It no longer reports
  `ready` just because a directory exists.

### Phase 1 — scoring vertical slice

- **`ApplicationToModelAdapter`** (`app/ai/application_adapter.py`): reads the active
  `feature_schema.json`, maps persisted Application+Borrower data to the exact
  feature names/types/order, validates required-ness, and never fabricates credit
  fields or substitutes transaction features. Error boundary: missing source data →
  409 (`ApplicationNotReadyError`); present-but-invalid value / unmappable schema →
  422 (`FeatureSchemaError`); artifact problems → 503.
- Canonical scoring path (`POST /applications/{id}/score`) now runs
  Application → adapter → preprocessor → model → calibrator → PD → band →
  OOD/uncertainty → SHAP → **persisted** Prediction, and returns the persisted
  record with: prediction id, application id, PD, calibrated & raw probability, risk
  band, confidence, uncertainty, model id, **real model version (`2.0.0`, not a
  UUID)**, model name, feature-schema version, scoring mode, OOD info, explanation
  availability.
- Prediction persistence expanded (migration `0002`) with raw/calibrated
  probability, uncertainty, scoring_mode, model_version, feature_schema_version.
- Counterfactual & stress-test endpoints reuse the **same** adapter path
  (`prepare_scoring_inputs`) over application features; expected errors are
  structured 409/422/503, never generic 500.
- SHAP explanations use the same preprocessed representation as scoring and map to
  human-readable application-feature reason codes.
- **Staff-404 fix:** `POST /applications/{id}/data-sources` now authorises via the
  shared `get_accessible_application` (borrower-owner OR permitted staff) instead of
  the owner-only check that produced spurious 404s for analysts.
- **Borrower role guard:** `POST /borrowers` restricted to BORROWER + ADMIN
  (analysts/compliance get 403; unauthenticated 401).
- Object-level authorization across borrower/application/consent/data-source/
  transaction/scoring/decision/explanation routes goes through
  `get_accessible_application` (verified: unrelated borrower → 404).

### ML — newly trained inference-safe model (replaces the leaky dev bundle)

- Dataset: `dataset for training/LoanDataset - LoansDatasest.csv` (32,586 raw →
  31,821 clean rows; target `Current_loan_status` → 1=DEFAULT/0=NO DEFAULT; ~21.1%
  default). **Public dataset, provenance undocumented in the repo** — metrics are
  development-grade, not real-world/Malaysian evidence.
- Inference-safe features only (8): `customer_age, customer_income,
  employment_duration, home_ownership, loan_intent, loan_amnt, term_years,
  loan_percent_income`. **Excluded** (documented in `dataset_manifest.json` /
  model card): `loan_grade`, `loan_int_rate` (lender-assigned/circular),
  `cred_hist_length`, `historical_default` (no bureau) — not fabricated.
- Trained Logistic Regression (Optuna), XGBoost (Optuna), LightGBM (Optuna),
  HistGradientBoosting, RandomForest, and an EBM glass-box **challenger** (trained &
  reported but not active-eligible: the serving explainer supports only
  linear/tree-SHAP). Documented weighted selection → **hist_gradient_boosting**
  (tree-SHAP compatible; verified SHAP works in shap 0.46.0).
- Calibration: **sigmoid**, selected **out-of-sample** — the calibrator is fit on
  one half of the validation slice and the sigmoid-vs-isotonic choice is made on the
  other half, then refit on the full validation slice for serving. This corrects an
  inherited bug where isotonic was fit and scored on the same rows (in-sample ECE
  ~1e-18), which both rigged the comparison and produced hard-0.0 PDs (357/4774 test
  predictions were exactly 0). Served probabilities are now clamped to
  [1e-4, 1-1e-4]. Split: stratified 70/15/15, seed 42 (train 22,274 / val 4,773 /
  test 4,774). Out-of-time validation unavailable (no application timestamp).
- Risk-band thresholds selected from a test-set sweep (§32) and persisted in
  `thresholds.json`: low < **0.05**, medium < **0.30**, decision threshold **0.30**
  (F1-maximising cut; low band keeps observed default rate ≤5%).
- **Held-out test metrics** (development-grade): ROC-AUC **0.8672**, PR-AUC
  **0.7325**, Brier **0.0971**, ECE **0.0134**, KS **0.5737**. The drop from the
  archived 0.944/0.977 bundles is the expected, honest result of removing bureau
  leakage. Verified discriminating: a strong profile scores PD≈0.001 and a weak one
  PD≈0.985 (no hard 0/1).
- Bundle `ml/artifacts/application_pd/` (version **2.0.0**, feature schema
  `app_pd_2.0.0`) exports preprocessor/model/calibrator/explainer + feature_schema,
  thresholds, model_metadata, model_card, evaluation_report (incl. threshold sweep),
  training_config, dataset_manifest. Old bundles archived under
  `ml/artifacts/_archive/` (not deleted).

### Exact files changed

- Config/health: `app/config.py`, `app/main.py`, `backend/.env`, `backend/.env.example`.
- Adapter/runtime/scoring: `app/ai/application_adapter.py` (new), `app/ai/runtime.py`,
  `app/services/scoring_service.py`, `app/routers/scoring.py`, `app/schemas/prediction.py`.
- AI endpoints: `app/routers/ai.py`, `app/ai/counterfactual.py`, `app/ai/stress_tester.py`,
  `app/ai/shap_explainer.py`.
- AuthZ: `app/routers/data_sources.py`, `app/services/data_source_service.py`,
  `app/routers/borrowers.py`.
- Schema/model/migration: `app/models/borrower.py`, `app/models/application.py`,
  `app/models/prediction.py`, `app/schemas/borrower.py`, `app/schemas/application.py`,
  `app/services/application_service.py`, `alembic/versions/0002_application_pd_features.py`.
- ML: `ml/datasets/application_pd.py` (new), `ml/datasets/__init__.py` (new),
  `ml/train_application_pd.py` (new).
- Seed/tests/smoke: `app/scripts/seed_demo.py`, `tests/test_scoring.py` (new),
  `tests/test_application_pd_model.py` (new), `scripts/smoke_test.py` (new).

### Commands run + results

- Train: `.venv\Scripts\python -m ml.train_application_pd --dataset "..\dataset for training\LoanDataset - LoansDatasest.csv" --output-dir ml/artifacts/application_pd --trials 25` → exit 0, metrics above.
- `.venv\Scripts\python -m app.scripts.seed_demo` → 2 borrowers/applications fully
  scored (PD 0.10 medium, 0.04 low — discriminating, no hard zeros).
- `.venv\Scripts\python -m pytest -q` → **40 passed, 50 warnings, ~17s**
  (8 pre-existing + 32 new scoring/ML tests, incl. a discrimination guard). 0 failed,
  0 skipped locally (bundle present). Warnings are pre-existing
  `datetime.utcnow`/pydantic-Config deprecations.
- Live API smoke test (`backend/scripts/smoke_test.py <base_url>`, uvicorn on
  127.0.0.1): health `ready`; self-serve borrower→application→consent→submit→score
  `200` (PD 0.0049, model_version 2.0.0); prediction persisted; explanation `200`
  (shap); stress-test `200`; counterfactual `200` (3 scenarios); decision `201`;
  audit-logs `200`; unrelated borrower blocked `404`.

### Database (was all zeros)

Seed baseline: users 5, borrowers 2, applications 2, consents 4, data_sources 2,
transactions 24, predictions 2, explanations 2, ml_models 1, decisions 2,
audit_logs 6. (The re-runnable smoke test adds further borrowers/applications.)

### Remaining issues / not in scope for Phase 0-1

- **Dataset:** LoanDataset provenance is undocumented; a defensible labelled
  default dataset (and a labelled transaction/default dataset for the future
  alternative-data model) is still required before any production claim. UCI Default
  of Credit Card Clients / Home Credit remain deferred. Home Credit
  (`dataset for training/archive (5)/`) was inspected and **rejected for this model**:
  its signal lives in bureau/prior-loan tables MyCreditLens cannot reproduce at
  inference (fails the inference-safe rule); its `train.csv` also uses a renamed
  lowercase `target`.
- **Supabase:** dormant; no credentials needed for local MVP. Not a blocker.
- **Deployment:** production `JWT_SECRET`, Postgres, and out-of-time validation on a
  real dataset are prerequisites for anything beyond local MVP.
- **Frontend:** not redesigned (§25). Grepped `app/ lib/ components/ src/` for the
  changed contracts: `lib/api-client.ts` reads `probability_of_default` and
  `model_version` (both still present; `model_version` now shows the real `2.0.0`
  instead of a UUID — an improvement, not a break). The counterfactual/stress panels
  read `disclaimer` plus specific scenario fields — those were preserved as aliases
  alongside the new §10/§11 fields, so no frontend change was required.
- Pre-existing `datetime.utcnow()` deprecation warnings remain across the codebase.
- **Fairness:** in-model fairness is N/A (no protected attribute in the feature set),
  but `customer_age` is age-protected in some jurisdictions; an age-band
  selection-rate / FPR / FNR audit is recommended follow-up before production.

---

## 2026-08-12 — Verified Runtime Assessment (superseded by the entry above)

This entry supersedes the "RUNTIME UNVERIFIED" status recorded in earlier entries
below. A working Python 3.12.10 interpreter and the `backend/.venv` virtualenv now
exist. Backend dependencies were installed and the code was actually executed.
No application source code was modified during this assessment.

### Verification performed (real commands, real output)

- `backend/.venv/Scripts/python.exe -m pip install -r requirements.txt` → exit 0.
- `python -c "import app.main"` → **APP IMPORT OK**.
- `python -m pytest -q` (in `backend/`) → **8 passed, 50 warnings in 1.64s**
  (test_health, test_workflow, test_ai_engineering).
- `CreditModelRuntime(Path("./ml/artifacts"))` loads → `MyCreditLensCreditRisk 1.0.0`.
- SQLite `mycreditlens.db`: 20 tables; `users`=3, `borrowers`=1;
  `applications`=0, `predictions`=0, `ml_models`=0, `data_sources`=0.

### Corrections to stale claims

- **"RUNTIME UNVERIFIED" is resolved.** The backend imports and its test suite passes.
- **"No tests written" (root PROJECT_STATUS.md) is wrong.** `backend/tests/` has
  `conftest.py`, `test_health.py`, `test_workflow.py`, `test_ai_engineering.py` +
  `pytest.ini`; all pass. (Frontend still has no tests.)
- **ML training is NOT "100% complete" as an MVP feature.** Artifacts are real, but
  they are not wired to the application (see blocker #1).

### CRITICAL BLOCKER #1 — Scoring feature-contract mismatch (end-to-end scoring is non-functional)

The trained models expect **loan-application tabular columns**
(`customer_age, customer_income, loan_amnt, loan_int_rate, loan_grade, ...`), but
`ScoringService._extract_features` → `FeatureEngineer` produces **bank-transaction
features** (`dti_ratio, savings_rate, buffer_months, cashflow_volatility, ...`).
The two schemas are disjoint. Proven empirically:

```
FeatureSchemaError: Inference features do not match the trained schema.
Missing: customer_age, customer_income, home_ownership, employment_duration,
         loan_intent, loan_grade, loan_amnt, loan_int_rate, term_years, cred_hist_length
```

Consequences:
- `POST /applications/{id}/score` has **no success path** → 422 (schema) or 503 (artifact).
- `POST /counterfactuals` and `POST /stress-tests` → **500** (uncaught FeatureSchemaError).
- `_demo_result` fallback is **dead code** (a `manifest.json` is always present, so the
  runtime always loads and the fallback branch is never reached).
- `GET /health/model` reports `ready`, masking the broken scoring path.
- No test exercises `/score`, which is why the mismatch went undetected.

This is the single most important thing to fix for the MVP. The intended product
(score a borrower from uploaded financial data) does not currently work end to end.

### Other verified findings

- **No git repository.** `.git/` is empty; `git status` fails. No version-control
  safety net exists. `git init` + an initial commit of the current state is recommended
  before any code changes.
- **Config drift.** `backend/.env` sets `MODEL_ARTIFACT_PATH=./ml/artifacts` (root bundle
  `MyCreditLensCreditRisk 1.0.0`, dataset `loan_credit_risk_32k`), NOT the advertised
  `./ml/artifacts/primary` (`MyCreditLens-Primary 2.0.0`). The deployed model is not the
  one PROJECT_STATUS.md and `config.py` comments describe.
- **JWT signed with the default secret.** `backend/.env` has no `JWT_SECRET`, so tokens
  use `"change-me-to-a-random-secret-key"`.
- **Requirement-12 model gaps.** Present: LogisticRegression (as a compared candidate),
  SHAP, isotonic calibration, OOD (Mahalanobis), fairness, uncertainty (confidence/OOD),
  stress tests, counterfactuals. **Missing: XGBoost/LightGBM** (both pinned in
  requirements but unused — selected model is `HistGradientBoosting`) and **EBM**
  (`interpret` not installed and unused).
- **Metrics caveat.** Primary test ROC-AUC 0.9752 / KS 0.82 is real *for the dataset*
  but the active datasets are synthetic/educational Kaggle sets; the split is
  `stratified_random` with `time_column: null` (no out-of-time validation). These are not
  evidence of real-world credit performance. A real labelled dataset (e.g. the Home Credit
  files sitting unused in `dataset for training/archive (5)/`) is still required for
  defensible metrics.
- **Provenance gap.** `pyvenv.cfg` = Python 3.12.6; model metadata `runtime.python` =
  3.12.10. Models were trained by the PATH interpreter, not the venv; the project was also
  moved (metadata `output_dir` references `...\my-credit-lens-backend-development\...`
  without the `MyCreditLens\` parent). Retraining under the pinned env is needed for
  reproducibility.
- **Frontend real vs mock:** real (backend-wired) = auth, lender dashboard/applications
  list+detail/borrowers/portfolio/audit, borrower dashboard/new-application/documents/
  connected-data/consent/profile. Mock-only = monitoring, fairness, settings save,
  assessment wizard (fake submit → hardcoded `APP-2041`), borrower messages, and the entire
  "decision room / advanced risk" overlay (`src/features/applications/mock-data/*`,
  `lib/mock-data.ts`). Even "real" pages show stubbed fields because `mapApplication()`
  fills `borrowerName`, `factors`, income/expense/cashflow with placeholders the backend
  payloads don't populate.
- **Declared-but-unused:** PDF/OCR parsing (only CSV implemented), PDF reports (reportlab
  unused — reports store JSON), Redis/Celery, MLflow, `python-magic` (not imported;
  problematic on Windows), `passlib` (code uses `bcrypt` directly).

### Concrete bugs to fix

1. Scoring↔model feature mismatch (systemic — blocker #1).
2. `routers/scoring.py:31` returns `model_id` (a UUID) as `model_version`.
3. `data_sources` upload uses owner-only lookup → staff get 404 (inconsistent with
   `get_accessible_application` used elsewhere).
4. `POST /borrowers/` has no role guard (registration already auto-creates a borrower).
5. `routers/ai.py` catches only `ArtifactUnavailableError`, so `FeatureSchemaError`
   surfaces as 500 instead of a clean 422/503.

### Next task

Present the phased plan (below in this session's assessment) and, on approval, execute
Phase 0 (git init + safety commit) then Phase 1 (repair the scoring feature contract).

---

## Task: AI Engineering and Artifact-Backed Scoring

Status: COMPLETED_STATIC

Implemented:
- Labelled dataset validation, duplicate removal, binary target checks, leakage guards, high-cardinality identifier detection, and protected-column exclusion.
- Stratified, borrower-group, and chronological splitting with held-out test isolation.
- Logistic Regression, Random Forest, and HistGradientBoosting candidates.
- Validation-based model selection and sigmoid/isotonic calibration selection.
- ROC-AUC, PR-AUC, Brier, log loss, precision, recall, F1, ECE, KS, calibration curve, and confusion matrix reporting.
- Versioned artifact export, model card, SHA-256 manifest, and artifact verification.
- Artifact-only runtime inference with strict feature schema validation and cached loading.
- Calibrated probability, configurable risk bands, OOD distance, confidence, real linear/SHAP contributions, and controlled reason text.
- Persisted model records, predictions, explanations, feature lineage, application results, and audit events.
- Trained-model counterfactual and stress-test APIs and frontend panels.
- Fairness group metrics with sample-size exclusions and explicit limitations.
- PSI drift and labelled performance evaluators.
- End-to-end ML pipeline test using a labelled fixture.

Verification:
- Python 3.12 byte-compilation passed for backend application, ML package, and tests.
- Local `app.*` and `ml.*` imports resolve.
- Full ML tests were not executed because the available interpreter does not have pandas, scikit-learn, FastAPI, or project dependencies installed.

External input required:
- Final labelled dataset, licence confirmation, target definition, protected columns, and approved feature mapping.

## Task: Non-AI Application Completion

Status: COMPLETED_STATIC

Scope completed:
- Fixed backend syntax and local import resolution, including IDE/test Python paths.
- Added centralized role and application ownership authorization.
- Completed local borrower registration/login/refresh/profile/password behavior.
- Completed staff borrower listing and borrower-owned application lifecycle.
- Added application-scoped consent, upload, transaction, decision, appeal, report, and audit APIs.
- Enforced consent before submission and matching consent before file upload.
- Added upload size checks, duplicate hashes, transaction parsing, and audit records.
- Repaired demo seed behavior for privileged users and automatic borrower profiles.
- Added backend workflow tests using isolated SQLite.
- Added frontend DTO mapping, authenticated role guards, and canonical API clients.
- Connected borrower dashboard, application creation, consent, data/documents, and profile pages.
- Connected lender overview, application list/detail, borrower list, portfolio, decisions, and audit pages.
- Removed silent mock fallback from live workflow pages.
- Marked excluded AI monitoring, fairness, and advanced application analysis as prototype-only.
- Added `pyrightconfig.json`, `backend/pytest.ini`, `next-env.d.ts`, ESLint configuration, and typecheck script.

Verification performed:
- Python 3.12 byte-compilation passed for `backend/app` and `backend/tests`.
- Every local backend `app.*` import resolved to a source module.
- Every frontend alias and relative import resolved to a source module.
- Every frontend external package import was declared in `package.json`.
- Backend canonical routes were inventoried and checked against frontend client paths.
- Source search found no remaining silent demo-data fallback in live workflow pages.

Environment-dependent verification not run:
- Backend runtime import and pytest: the discovered Python interpreter does not have FastAPI or project dependencies installed.
- Frontend lint, typecheck, and build: `node_modules` is absent.
- PostgreSQL migration, seed, Docker, and browser E2E execution.

User input required:
- None for source implementation.
- Dependency/runtime setup remains outside the user-requested scope.

Next recommended task:
- Install declared dependencies and execute the verification commands recorded in `docs/CODEX_PLAN.md`.

## Task: Readiness Assessment and Codex Source-of-Truth Update

Status: COMPLETED

Files changed:
- `docs/CODEX_PROJECT_ASSESSMENT_AND_EXECUTION_PLAN.md`
- `docs/IMPLEMENTATION_PROGRESS.md`

Tests added:
- None. Documentation/status task.

Commands run:
- Read `docs/CODEX_PROJECT_ASSESSMENT_AND_EXECUTION_PLAN.md`.
- Read `docs/IMPLEMENTATION_PROGRESS.md`.
- Read `docs/USER_INPUT_REQUIRED.md`.
- Read `docs/API_CONTRACT.md`.
- Read `docs/DATASET_INTEGRATION_PLAN.md`.
- Read `.codexignore`.

Results:
- Frontend readiness is recorded as `PARTIALLY READY`.
- Backend readiness is recorded as `PARTIALLY READY`.
- AI/ML readiness is recorded as `DEMO ONLY`.
- External environment values, secrets, Supabase credentials, and third-party API keys are not required to continue the local readiness work.
- Runtime verification, dependency installation, authorization completion, DTO mapping, mock-fallback removal, and E2E coverage remain required before the application can be marked ready.
- The assessment now identifies the focused Markdown files Codex should consult before reopening broad areas of the codebase.

Remaining issues:
- Complete and verify the readiness exit criteria in `docs/CODEX_PROJECT_ASSESSMENT_AND_EXECUTION_PLAN.md`.

Whether user input is required:
- No for the next local implementation and verification tasks.
- Supabase credentials and the final dataset are required later as recorded in `docs/USER_INPUT_REQUIRED.md`.

Next recommended task:
- Run backend verification through a working Python runtime or Docker, then verify the local vertical slice.

## Task: Work Tracking Documents

Status: COMPLETED

Files changed:
- `docs/IMPLEMENTATION_PROGRESS.md`
- `docs/USER_INPUT_REQUIRED.md`
- `docs/API_CONTRACT.md`
- `docs/DATASET_INTEGRATION_PLAN.md`

Tests added:
- None. Documentation task.

Commands run:
- `Get-Content -Raw C:/Users/user/.codex/attachments/64d15e18-d299-446e-a9d6-e61b20ba8de0/pasted-text.txt`

Results:
- Required tracking files created.

Remaining issues:
- Continue updating after every milestone.

Whether user input is required:
- No.

Next recommended task:
- Keep backend foundation progress current as implementation continues.

## Task: Async SQLAlchemy Backend Foundation

Status: PARTIALLY_COMPLETED

Files changed:
- `backend/app/config.py`
- `backend/app/database.py`
- `backend/app/main.py`
- `backend/app/services/auth_service.py`
- `backend/app/services/borrower_service.py`
- `backend/app/services/application_service.py`
- `backend/app/services/data_source_service.py`
- `backend/app/services/scoring_service.py`
- `backend/app/routers/auth.py`
- `backend/app/routers/borrowers.py`
- `backend/app/routers/applications.py`
- `backend/app/routers/data_sources.py`
- `backend/app/routers/scoring.py`
- `backend/app/routers/decisions.py`
- `backend/app/routers/appeals.py`
- `backend/app/routers/reports.py`
- `backend/app/models/data_source.py`
- `backend/app/schemas/auth.py`
- `backend/app/schemas/application.py`
- `backend/app/schemas/data_source.py`

Tests added:
- `backend/tests/test_health.py`

Commands run:
- `rg "db\\.query|db\\.commit\\(|db\\.refresh\\(|from sqlalchemy.orm import Session" backend/app -n`
- `python -m compileall backend/app`
- `python -m compileall backend/tests`
- `py -m compileall backend/app`
- `py -m compileall backend/tests`
- `rg "/scoring|scoring/" backend/app lib docs/API_CONTRACT.md -n`

Results:
- Local JWT auth, borrower CRUD, application CRUD, upload metadata, demo scoring, decisions, appeals, and reports have been moved toward async SQLAlchemy patterns.
- Health endpoints added.
- Text search found no remaining `db.query` or sync `Session` imports in `backend/app`.
- Python verification could not run because `python.exe` is the Windows Store launcher stub and `py` is unavailable on PATH.
- Old `/scoring` route references were removed from backend/frontend API calls.

Remaining issues:
- Full compile/import checks still need to pass.
- Object-level authorization remains partial.
- Supabase Auth adapter is not implemented yet.
- Some non-vertical-slice paths may still need contract cleanup.

Whether user input is required:
- No.

Next recommended task:
- Run syntax/import checks and fix any failures.

## Task: Alembic Migration Scaffolding

Status: PARTIALLY_COMPLETED

Files changed:
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/0001_initial_schema.py`

Tests added:
- Pending migration check against local PostgreSQL.

Commands run:
- Not run; PostgreSQL is not running in this shell and Python launcher is unavailable.

Results:
- Alembic configuration and an initial metadata-backed migration baseline were added.

Remaining issues:
- The initial migration should be replaced with explicit autogenerated operations once the schema stabilizes.
- Migration execution requires a running PostgreSQL database.
- Current migration baseline uses SQLAlchemy metadata creation inside Alembic as an interim bootstrap.

Whether user input is required:
- No.

Next recommended task:
- Run `alembic upgrade head` against Docker PostgreSQL.

## Task: Docker Local Development

Status: PARTIALLY_COMPLETED

Files changed:
- `backend/Dockerfile`
- `Dockerfile.frontend`
- `docker-compose.yml`

Tests added:
- None yet.

Commands run:
- Not run. Docker build was deferred until Python syntax checks can run.

Results:
- Local PostgreSQL, backend, frontend, and optional Redis compose scaffolding added.

Remaining issues:
- `docker compose up --build` has not yet been run.
- Frontend Dockerfile has not been build-verified.

Whether user input is required:
- No.

Next recommended task:
- Run Docker build once syntax checks pass.

## Task: Seed Scripts

Status: PARTIALLY_COMPLETED

Files changed:
- `backend/app/scripts/__init__.py`
- `backend/app/scripts/seed_demo.py`
- `backend/app/scripts/reset_demo.py`

Tests added:
- None yet.

Commands run:
- Not run because Python launcher is unavailable.

Results:
- Development-only demo users, borrower, and draft application seeding scripts added.

Remaining issues:
- Needs execution against migrated PostgreSQL.
- Additional consent, transactions, prediction, explanation, decision, appeal, notification, and audit seed data still need to be added.

Whether user input is required:
- No.

Next recommended task:
- Verify and expand seed scripts after Python and PostgreSQL are available.

## Task: Frontend API Contract Alignment

Status: PARTIALLY_COMPLETED

Files changed:
- `lib/api-client.ts`
- `docs/API_CONTRACT.md`

Tests added:
- None yet.

Commands run:
- `npm.cmd run lint`
- `pnpm lint`

Results:
- Scoring API client now uses application-scoped scoring, prediction, and explanation routes.
- `pnpm` is unavailable on PATH.
- `npm.cmd run lint` starts but fails because `eslint` is not installed in `node_modules`.

Remaining issues:
- Frontend dependencies need installation before lint/type checks can run.
- Monitoring, fairness, counterfactual, stress-test, and some data-source routes are still planned or partial.
- DTO mappers are not implemented yet.

Whether user input is required:
- No.

Next recommended task:
- Add DTO mapper structure and remove silent mock fallback from the vertical-slice pages after backend routes are verified.
