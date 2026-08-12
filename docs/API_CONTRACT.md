# MyCreditLens API Contract

Last updated: 2026-07-11

Base URL: `/api/v1`

`IMPLEMENTED_STATIC` means the route, authorization rule, schema, service/client integration, and source-level checks are complete. Runtime verification still requires the excluded Python/Node dependency environment.

## Authentication

| Method | Path | Access | Status |
|---|---|---|---|
| POST | `/auth/register` | Public borrower registration only | IMPLEMENTED_STATIC |
| POST | `/auth/login` | Public | IMPLEMENTED_STATIC |
| POST | `/auth/refresh` | Refresh token | IMPLEMENTED_STATIC |
| GET | `/auth/me` | Authenticated | IMPLEMENTED_STATIC |
| POST | `/auth/change-password` | Authenticated | IMPLEMENTED_STATIC |

Privileged users cannot self-register. Demo staff accounts are created only through the seed script.

## Borrowers and Applications

| Method | Path | Access | Status |
|---|---|---|---|
| GET | `/borrowers/` | Staff | IMPLEMENTED_STATIC |
| GET | `/borrowers/{borrower_id}` | Staff | IMPLEMENTED_STATIC |
| GET | `/borrowers/me` | Borrower owner | IMPLEMENTED_STATIC |
| PUT | `/borrowers/me` | Borrower owner | IMPLEMENTED_STATIC |
| POST | `/applications/` | Borrower | IMPLEMENTED_STATIC |
| GET | `/applications/` | Borrower sees own; staff sees portfolio | IMPLEMENTED_STATIC |
| GET | `/applications/{application_id}` | Owner or staff | IMPLEMENTED_STATIC |
| PUT | `/applications/{application_id}` | Borrower owner; draft only | IMPLEMENTED_STATIC |
| POST | `/applications/{application_id}/submit` | Borrower owner; active consent required | IMPLEMENTED_STATIC |

## Consent, Data, and Transactions

| Method | Path | Access | Status |
|---|---|---|---|
| GET | `/applications/{application_id}/consents` | Owner or staff | IMPLEMENTED_STATIC |
| POST | `/applications/{application_id}/consents` | Borrower owner | IMPLEMENTED_STATIC |
| POST | `/applications/{application_id}/consents/{consent_id}/revoke` | Borrower owner | IMPLEMENTED_STATIC |
| POST | `/applications/{application_id}/data-sources` | Borrower owner; matching active consent required | IMPLEMENTED_STATIC |
| GET | `/applications/{application_id}/data-sources` | Owner or staff | IMPLEMENTED_STATIC |
| GET | `/applications/{application_id}/transactions` | Owner or staff | IMPLEMENTED_STATIC |

Uploads enforce source type, size, duplicate hash detection, UTF-8 CSV/TSV parsing, validation metadata, and consent. External object storage is outside the local completion scope.

## Decisions, Appeals, Reports, and Audit

| Method | Path | Access | Status |
|---|---|---|---|
| POST | `/applications/{application_id}/decisions` | Admin or credit analyst | IMPLEMENTED_STATIC |
| GET | `/applications/{application_id}/decisions` | Owner or staff | IMPLEMENTED_STATIC |
| POST | `/applications/{application_id}/appeals` | Borrower owner; eligible decision state | IMPLEMENTED_STATIC |
| GET | `/applications/{application_id}/appeals` | Owner or staff | IMPLEMENTED_STATIC |
| PATCH | `/applications/{application_id}/appeals/{appeal_id}` | Admin or compliance reviewer | IMPLEMENTED_STATIC |
| POST | `/applications/{application_id}/reports` | Staff | IMPLEMENTED_STATIC |
| GET | `/applications/{application_id}/reports` | Owner or staff | IMPLEMENTED_STATIC |
| GET | `/audit-logs` | Staff | IMPLEMENTED_STATIC |

## Scoring and AI Governance

| Method | Path | Access | Status |
|---|---|---|---|
| POST | `/applications/{application_id}/score` | Admin or credit analyst | ARTIFACT_BACKED_WITH_DEMO_FALLBACK |
| GET | `/applications/{application_id}/predictions` | Owner or staff | IMPLEMENTED_STATIC |
| GET | `/applications/{application_id}/explanations` | Owner or staff | IMPLEMENTED_STATIC |
| POST | `/applications/{application_id}/counterfactuals` | Admin or credit analyst | TRAINED_ARTIFACT_REQUIRED |
| POST | `/applications/{application_id}/stress-tests` | Admin or credit analyst | TRAINED_ARTIFACT_REQUIRED |
| POST | `/fairness/evaluate` | Admin or compliance reviewer | IMPLEMENTED_STATIC |
| POST | `/monitoring/drift/evaluate` | Admin or compliance reviewer | IMPLEMENTED_STATIC |
| POST | `/monitoring/performance/evaluate` | Admin or compliance reviewer | IMPLEMENTED_STATIC |

Scoring loads only a checksum-verified artifact bundle and never retrains at API startup. A schema-incompatible model is rejected. The deterministic fallback is clearly labelled and can be disabled with `ALLOW_DEMO_SCORING=false` or made mandatory-artifact with `REQUIRE_MODEL_ARTIFACTS=true`.

## Frontend Boundary

- `lib/api-client.ts` owns backend DTO definitions and snake_case-to-domain mapping.
- Live borrower, lender application, borrower list, decision, consent, document, profile, portfolio, and audit pages do not silently substitute mock API data.
- Counterfactual and stress panels call trained-artifact APIs and show explicit unavailable/error states.
- Local JWT tokens are the supported no-secret MVP authentication mode.
