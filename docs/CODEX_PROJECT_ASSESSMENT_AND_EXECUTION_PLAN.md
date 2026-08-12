# MyCreditLens Project Assessment and Execution Plan

Date: 2026-07-11

## Current Readiness Snapshot

Short answer: **No. The frontend and backend are not completely ready yet, even when environment variables, secrets, and external API keys are excluded from the assessment.**

| Area | Status | Current boundary |
|---|---|---|
| Backend | SOURCE COMPLETE, RUNTIME UNVERIFIED | The non-AI local backend now has async data access, local JWT auth, centralized roles and ownership, application workflows, consent, uploads, transactions, decisions, appeals, reports, audit records, migration/seed scaffolding, and focused tests. Runtime tests and migrations still require the excluded dependency/database environment. Supabase remains outside this local scope. |
| Frontend | SOURCE COMPLETE, RUNTIME UNVERIFIED | Live workflow pages use canonical APIs with DTO mapping and role guards. Silent mock fallback was removed. AI-only prototype screens are explicitly disclosed. Lint, typecheck, build, and browser execution still require the excluded `node_modules` environment. |
| AI/ML | SOURCE COMPLETE, ARTIFACTS PENDING | Supervised training, leakage controls, candidate selection, calibration, held-out evaluation, model cards, checksummed artifacts, artifact-only inference, OOD, real linear/SHAP contributions, controlled explanations, counterfactuals, stress tests, fairness, and monitoring code are implemented. A final labelled dataset has not been supplied, so no final trained artifact or performance claim exists yet. |
| Local infrastructure | SCAFFOLDED, UNVERIFIED | Dockerfiles, Compose, Alembic, environment examples, and seed scripts exist, but the containers and migrations have not been run end to end. |

External Supabase credentials, deployment secrets, and third-party API keys are **not blockers for continuing local development**. Local PostgreSQL, local JWT authentication, synthetic fixtures, and demo scoring can support the core vertical slice. However, the application cannot be called complete until a working Python runtime or Docker environment and installed frontend dependencies are used to run verification.

### Readiness Exit Criteria

The frontend and backend may be marked ready only after all of the following pass:

1. Backend compile/import checks and automated tests.
2. Alembic migration and seed scripts against PostgreSQL.
3. Authentication, borrower, application, upload, submit, score, explanation, and decision workflow tests.
4. Object-level role and ownership authorization tests.
5. Frontend install, lint, typecheck, and production build.
6. Removal of silent mock fallbacks from live pages, or an explicit visible demo mode.
7. Frontend-to-backend DTO mapping and API error-state verification.
8. At least one browser E2E test for the borrower-to-analyst workflow.

### Codex Working Source of Truth

To avoid repeatedly reading the entire repository, future work should begin with this document and the focused tracking documents below. Code should be reopened only for the files involved in the current task or when the tracking documents may be stale.

- `docs/IMPLEMENTATION_PROGRESS.md`: completed work, verification evidence, blockers, and next task.
- `docs/API_CONTRACT.md`: canonical frontend/backend routes and implementation status.
- `docs/USER_INPUT_REQUIRED.md`: inputs that require the user and available fallbacks.
- `docs/DATASET_INTEGRATION_PLAN.md`: dataset decisions and ML artifact contract.
- `docs/SUPABASE_INTEGRATION_ARCHITECTURE_AND_PHASE_1_PLAN.md`: selected infrastructure boundaries.
- `.codexignore`: generated, dependency, cache, secret, and low-value asset exclusions.

These documents must be updated whenever implementation or verification changes the project state. The codebase remains authoritative if a document conflicts with current code.

## Scope Reviewed

I reviewed the main product and AI specification first:

- `docs/MyCreditLens_Complete_Application_AI_Engineering_and_Deployment_Guide.md`
- `PROJECT_STATUS.md`
- `docs/MyCreditLens_Backend_AI_Development_Plan.md`
- `docs/MyCreditLens_Frontend_UIUX_Development_Plan.md`
- `docs/MyCreditLens_v0_Incremental_Frontend_Improvement_Plan.md`

I then reviewed the current codebase structure across:

- `backend/app/main.py`, `config.py`, `database.py`
- backend routers, services, schemas, models, and AI helper modules
- `package.json`, `backend/requirements.txt`
- `lib/api-client.ts`, `lib/auth-context.tsx`, `lib/hooks/*`
- representative lender and borrower pages
- current mock-data usage and API references

Note: the pasted `AGENTS.md` instructions describe Qovarix, but this workspace is MyCreditLens. I treated the active repository as authoritative.

## Current State

MyCreditLens is currently a broad scaffold for an explainable alternative-data credit-risk MVP. The project has a good product direction and many named modules already exist, but the implementation is not yet a reliable end-to-end system.

The frontend is visually substantial and includes public, borrower, and lender routes. However, many views still depend on `lib/mock-data.ts` or feature-level mock files, and the API-connected pages fall back to demo data when backend calls fail.

The backend contains models, schemas, routers, and services for authentication, borrowers, applications, scoring, data sources, decisions, appeals, and reports. The active scoring path now loads checksum-verified trained artifacts when available, emits calibrated probabilities, enforces the trained feature schema, computes OOD confidence, and persists real model contributions. If artifacts are absent, it uses a clearly labelled deterministic fallback unless configuration requires trained artifacts.

The original async SQLAlchemy mismatch has been substantially addressed in the core services and routers. The remaining immediate blocker is verification: the current machine exposed a Windows Store Python launcher rather than a working interpreter, and frontend dependencies are not installed. Until imports, tests, migrations, builds, and the vertical slice run successfully, the implementation must remain classified as partially ready.

The infrastructure direction is now Supabase-selective:

- Supabase PostgreSQL should be the managed primary database.
- Supabase Auth should replace the current custom JWT login/refresh flow.
- Supabase Storage should hold uploaded financial documents, appeal documents, consent evidence, and generated reports.
- FastAPI should remain the main backend for all credit-risk business logic and Python ML work.
- Supabase Edge Functions, pgvector, Realtime, and MLflow should wait until the core workflow works.

See `docs/SUPABASE_INTEGRATION_ARCHITECTURE_AND_PHASE_1_PLAN.md` for the detailed Supabase integration plan.

## What Remains

### Critical Backend Foundation

- Fix the SQLAlchemy session architecture by choosing one approach:
  - selected direction: convert backend services/routes to real SQLAlchemy 2.0 async patterns.
- Stop swallowing database startup failures in `backend/app/main.py`; failed table creation should be visible during development.
- Add Alembic migrations instead of relying on `Base.metadata.create_all`.
- Import all model metadata before table creation or migrations.
- Add a real seed script for demo users, borrowers, applications, data sources, and model records.
- Add backend tests for auth, borrower/application CRUD, upload, scoring, decisions, and reports.
- Configure SQLAlchemy against Supabase PostgreSQL using direct or session-pooled connectivity and conservative application-side pool settings.

### API Contract Alignment

- Align frontend API calls with implemented backend routes.
- Fix unsupported frontend calls such as:
  - `/auth/refresh`
  - `/monitoring/*`
  - `/ai/*`
  - `/scoring/explanations/{applicationId}`
  - `/scoring/counterfactuals/{applicationId}`
- Decide and document canonical route shapes, for example:
  - `POST /applications/{id}/score` versus `POST /scoring/score`
  - `GET /applications/{id}/data-sources` versus `GET /data-sources/{applicationId}`
- Normalize response field names. The backend returns snake_case ORM-style data, while frontend types expect camelCase demo objects.
- Add shared API DTO mapping at the frontend boundary instead of passing raw backend objects into mock-oriented components.

### Authentication and Authorization

- Replace custom FastAPI JWT authentication with Supabase Auth.
- Let Supabase handle registration, login, refresh tokens, password reset, email verification, and sessions.
- Add backend Supabase JWT verification and profile lookup from `public.users`.
- Replace frontend `/auth/refresh` usage with Supabase client session handling.
- Add role checks and object-level authorization. Current routes mostly authenticate, but do not yet enforce lender/admin/borrower separation deeply enough.
- Add organisation or tenant isolation if the lender-admin model remains in scope.
- Add RLS as defence in depth while keeping FastAPI authorization as the primary business-rule gate.

### Data Ingestion and Consent

- Implement consent enforcement before upload, feature generation, and scoring.
- Store file hashes and detect duplicates.
- Use Supabase Storage private buckets for uploaded files and generated reports.
- Store only file metadata in PostgreSQL.
- Expand upload handling beyond simple UTF-8 CSV/TSV if XLSX/PDF remains in the MVP definition.
- Add validation reports, source reliability details, and transaction correction workflows.
- Add data-source ownership checks so users cannot access arbitrary application data by ID.
- Generate signed URLs through FastAPI for temporary access to private files.

### AI and ML

- Build a real offline training pipeline under `backend/ml/` or an equivalent agreed location.
- Choose the labelled dataset and target definition.
- Train at least:
  - Logistic Regression baseline
  - XGBoost or LightGBM performance model
  - EBM or another interpretable challenger if feasible
- Add preprocessing, calibration, evaluation, and artifact export.
- Save model artifacts:
  - preprocessor
  - model
  - calibrator
  - feature schema
  - thresholds
  - metadata/model card
  - explainer where applicable
- Update `ScoringService` to load artifacts at startup or lazily, not create fake active model metrics.
- Add real SHAP or model-appropriate explanations.
- Keep fraud/integrity risk, data reliability, and credit risk separate.
- Add model agreement, OOD/abstention, counterfactuals, and stress testing after the core scoring path works.

### Frontend Completion

- Remove silent mock fallback from pages that claim to be live API-connected.
- Add explicit demo mode if mock data is still desired.
- Connect borrower application creation to the backend.
- Connect data upload, consent, scoring, explanations, decisions, appeals, reports, monitoring, and fairness to real APIs.
- Add loading, empty, error, and retry states consistently.
- Add validation with React Hook Form/Zod or another chosen pattern.
- Add route protection based on role.
- Align frontend dependencies with the documented stack. Current `package.json` does not include TanStack Query, Axios, React Hook Form, Zod, Playwright, or test tooling despite the docs/status suggesting some of them.

### Testing and Quality

- Add backend unit tests for services and feature formulas.
- Add API integration tests with a test database.
- Add frontend unit/component tests for critical components.
- Add Playwright E2E tests for:
  - borrower creates application
  - borrower grants consent/uploads data
  - analyst scores and reviews application
  - analyst records decision
  - borrower views explanation or appeal status
- Add lint/typecheck/test commands for backend and frontend in a consistent developer workflow.

### DevOps and Deployment

- Add Dockerfiles for backend and frontend.
- Add local workflow documentation for Next.js + FastAPI connected to Supabase PostgreSQL/Auth/Storage.
- Add Docker Compose only for local app services if useful; local PostgreSQL and MinIO are no longer required for the primary MVP path.
- Add CI for lint, typecheck, tests, and build.
- Add environment templates for frontend and backend.
- Add structured logging and request IDs.
- Add basic health checks that verify database connectivity, not only app process health.

## Ideal Plan for Flawless Execution

### Phase 1: Make the Supabase-Backed Vertical Slice Actually Run

Goal: login, create borrower/application, upload CSV, submit, score, view result, and record decision against a real database.

Actions:

1. Convert backend data access to SQLAlchemy 2.0 async patterns.
2. Configure Supabase PostgreSQL connection settings.
3. Add Alembic migrations and a seed/profile synchronization command.
4. Replace custom login with Supabase Auth in the frontend.
5. Add backend Supabase JWT verification and `public.users` profile lookup.
6. Add Supabase Storage upload orchestration through FastAPI.
7. Align application, borrower, consent, upload, scoring, and decision endpoint paths.
8. Add DTO mapping between backend snake_case and frontend camelCase.
9. Remove mock fallback from the target vertical-slice pages.
10. Add smoke tests for the full path.

This phase should come before Redis, MLflow, Docker hardening, or advanced UI features.

### Phase 2: Replace Prototype Scoring With a Defensible Model

Goal: a real calibrated tabular model produces persisted predictions with versioned metadata.

Actions:

1. Select and document the dataset.
2. Define the default target and leakage rules.
3. Build repeatable training scripts.
4. Train baseline and challenger models.
5. Calibrate probabilities.
6. Generate metrics and a model card.
7. Save artifacts and feature schema.
8. Update backend inference to load and validate artifacts.
9. Add ML tests for schema, deterministic inference, calibration, and metric thresholds.

### Phase 3: Explainability, Policy, and Human Decision Workflow

Goal: every score is explainable, policy-reviewed, and analyst-controlled.

Actions:

1. Generate real SHAP or model-appropriate explanations.
2. Convert feature contributions to controlled reason codes.
3. Implement independent policy rules.
4. Persist policy results.
5. Require decision reasons and override reasons.
6. Write audit records for scoring, policy evaluation, decisions, and overrides.
7. Expose borrower-safe explanations without internal fraud or policy-threshold details.

### Phase 4: Data Quality, Reliability, and Integrity

Goal: analysts can trust or challenge the data behind a score.

Actions:

1. Add source-level reliability scoring.
2. Add duplicate detection and file hashes.
3. Add missing-period and anomaly checks.
4. Add evidence traceability from feature to source transactions.
5. Add analyst correction/exclusion flow.
6. Recompute features after corrections.

### Phase 5: Advanced AI/Governance Features

Goal: complete the research-grade features without weakening the core path.

Actions:

1. Add model agreement and uncertainty/manual-review triggers.
2. Add OOD detection.
3. Add counterfactual simulation.
4. Add stress testing.
5. Add fairness reports with sample sizes and limitations.
6. Add monitoring dashboards backed by real prediction/model data.
7. Add reports and exports.

### Phase 6: Deployment and Demo Readiness

Goal: reproducible local and hosted demo.

Actions:

1. Add Docker Compose for local development.
2. Add CI.
3. Add staging/demo deployment.
4. Add demo seed data.
5. Add smoke-test script.
6. Add final documentation: setup, model training, deployment, limitations, and demo script.

## What I Need From You

1. Database decision:
   - Please provide the Supabase project URL and database connection string, or confirm I should prepare placeholders only.

2. Dataset decision:
   - Which labelled dataset should be the core training source: Home Credit, German Credit, Default of Credit Card Clients, or another dataset?

3. MVP deadline and grading priority:
   - Is the priority a flawless demo workflow, stronger ML experimentation, or broader feature coverage?

4. Auth/security expectation:
   - Should the frontend use Supabase SSR cookie-based session handling immediately, or start with the simpler browser client for the demo?

5. Demo roles:
   - Which seeded users should exist for borrower, analyst, admin, and compliance reviewer?

6. Deployment target:
   - Should the final MVP target Vercel + Render/Railway/Fly.io + Supabase, or a single VM running the frontend/backend while still using Supabase?

7. Scope control:
   - Should I prioritize completing one end-to-end borrower-to-analyst path before implementing monitoring/fairness/reporting pages?

## Recommended Immediate Next Step

Continue Phase 1 without waiting for external secrets:

1. Use a working local Python 3.12+ interpreter or Docker to run backend compile/import checks and tests.
2. Run Alembic and seed scripts against local PostgreSQL.
3. Prove the local JWT borrower/application/upload/scoring/decision vertical slice.
4. Install frontend dependencies and pass lint, typecheck, and production build.
5. Add DTO mappers and remove silent mock fallback from that vertical slice.
6. Add one browser E2E test covering the complete workflow.

Supabase credentials and the final dataset become necessary for managed integration and real ML validation, not for this local readiness pass.
