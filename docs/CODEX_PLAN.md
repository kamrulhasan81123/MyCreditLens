# MyCreditLens Codex Execution Plan

Last updated: 2026-07-11

## Objective

Complete MyCreditLens as a coherent application, including a defensible offline AI engineering pipeline and artifact-backed inference, while keeping secrets and deployment-environment setup outside the source scope.

## Explicitly Out of Scope

- Supplying or licensing the final labelled credit dataset.
- Claiming final model performance or Malaysian predictive validity before that dataset is supplied.
- Supabase project creation, credentials, Auth/Storage integration, or hosted deployment.
- User-owned API keys, secrets, DNS, cloud resources, and machine-level software installation.

The deterministic score remains permitted only as a visibly labelled fallback when verified trained artifacts are absent.

## Acceptance Criteria

- Backend modules import and compile with no syntax errors.
- Database writes use async SQLAlchemy consistently and migrations describe the complete schema.
- Authentication supports register, login, refresh, current user, and password change in local mode.
- Role checks and object-level ownership checks protect borrower, application, upload, scoring, decision, appeal, and report data.
- Borrower profile, application, consent, upload/transactions, submission, demo scoring, explanation, decision, appeal, and report workflows have canonical APIs.
- Frontend API types map backend snake_case DTOs into UI domain types.
- Live workflow pages do not silently replace API failures with mock data.
- Demo-only and unavailable AI surfaces are labelled honestly.
- Backend tests cover health, auth, authorization, and the primary workflow.
- Frontend lint, typecheck, and production build pass when dependencies are available.
- `docs/API_CONTRACT.md`, `docs/IMPLEMENTATION_PROGRESS.md`, and this plan match the implemented code.

## Execution Checklist

| Phase | Deliverable | Status |
|---|---|---|
| 1 | Audit non-AI backend and frontend against the current contract | COMPLETED |
| 2 | Repair backend schema, services, transactions, and authorization | COMPLETED |
| 3 | Complete consent, transaction, workflow, appeal, decision, and report APIs | COMPLETED |
| 4 | Align frontend DTOs, auth, route guards, and live workflow pages | COMPLETED |
| 5 | Add focused backend workflow tests and frontend static contract checks | COMPLETED |
| 6 | Run all verification available without installing the excluded environment | COMPLETED |
| 7 | Reconcile API contract, progress tracker, and final readiness status | COMPLETED |
| 8 | Implement supervised training, leakage controls, calibration, evaluation, and artifact export | COMPLETED |
| 9 | Implement artifact-only inference, OOD detection, and real contribution explanations | COMPLETED |
| 10 | Implement model counterfactuals, stress tests, fairness, and drift evaluation | COMPLETED |
| 11 | Connect trained AI APIs to scoring and analyst frontend panels | COMPLETED |
| 12 | Add end-to-end ML artifact tests and AI documentation | COMPLETED |

## Working Rules

- Consult this file, `docs/IMPLEMENTATION_PROGRESS.md`, and `docs/API_CONTRACT.md` before broad code reads.
- Read only files relevant to the active phase unless a cross-cutting contract requires more context.
- Update this checklist as phases complete; do not mark a phase complete without implementation evidence.
- Preserve the boundary between implemented demo behavior and unavailable production AI behavior.

## Current Next Action

Provide the final labelled dataset and target definition, then execute the implemented training command. Environment-owned verification still requires installing declared dependencies.

## Verification Log

- 2026-07-11: Python 3.12 byte-compilation passed for `backend/app` and `backend/tests`.
- 2026-07-11: Static resolution passed for every local backend `app.*` import.
- 2026-07-11: Static resolution passed for every frontend `@/` and relative import.
- 2026-07-11: Frontend package import declarations passed against `package.json`.
- 2026-07-11: Canonical backend route inventory was generated and checked against `lib/api-client.ts`.
- 2026-07-11: Python byte-compilation and local import resolution passed for `backend/app`, `backend/ml`, and tests after AI implementation.
- 2026-07-11: Added an end-to-end test that trains a labelled fixture, verifies artifact checksums, loads the production runtime, and produces a calibrated prediction and explanation.
- Runtime imports remain dependent on installing packages from `backend/requirements.txt`; the available interpreter currently reports `ModuleNotFoundError: fastapi`.

## Completion Status

**COMPLETE for application and AI source implementation; final model training remains data- and environment-dependent.**

Completed source work includes local authentication, role and ownership authorization, borrower/application lifecycle, consent enforcement, CSV transaction ingestion, decisions, appeals, reports, audit records, API DTO mapping, route guards, removal of silent live-data fallbacks, honest AI prototype disclosures, seed repair, tests, import configuration, and contract documentation.

The AI source now includes schema and leakage validation, group/time/stratified splits, three candidate models, calibration selection, held-out metrics, model cards, checksummed artifacts, runtime schema enforcement, OOD scoring, real linear/SHAP contributions, controlled explanations, counterfactuals, stress tests, fairness evaluation, drift/performance evaluation, and frontend integration.

The remaining external boundary is dependency installation, the final labelled dataset and licence, executing training to create real artifacts, database/container startup, runtime tests, frontend build checks, secrets, and deployment.
