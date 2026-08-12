# Retraining Decision (Phase 2D + 2E)

Last updated: 2026-08-12

## Decision

> **RETRAINING_NOT_JUSTIFIED** (for promotion).
>
> The active model **2.0.0** (`application_pd_hist_gradient_boosting`, LoanDataset)
> **remains the active production model.** No available dataset provides a
> material improvement for the *deployed* MyCreditLens model while preserving
> inference compatibility. Home Credit was built as a **research challenger**
> (`2.1.0-challenger`, not promoted) to produce executed evidence for this
> decision; it is retained under `backend/ml/artifacts/_challenger/` and is not
> wired into scoring.

This is a decision *not to retrain the deployed model*, not a decision to stop
research. Home Credit and UCI remain available as external benchmarks.

## Phase 2D — inference-compatibility gate

The active MyCreditLens application provides exactly these fields at scoring
time (via `ApplicationToModelAdapter`): borrower `date_of_birth`,
`monthly_income_declared`, `employment_duration_years`, `home_ownership`;
application `requested_amount`, `requested_term_months`, `loan_intent`. From
these the adapter produces the 8-feature contract:
`customer_age, customer_income, employment_duration, home_ownership,
loan_intent, loan_amnt, term_years, loan_percent_income`.

### Home Credit → MyCreditLens feature mapping

| Dataset feature | MyCreditLens source | Transformation | Inference available | Include | Reason |
|---|---|---|---|---|---|
| `days_birth` | Borrower.date_of_birth | `-days_birth/365.25` → age | yes | ✅ include | Direct |
| `income` (AMT_INCOME_TOTAL) | Borrower.monthly_income_declared×12 | identity (annual) | yes | ⚠️ include, but **scale mismatch** | HC income median ~148k vs MCL ~54–108k RM |
| `loan_body` (AMT_CREDIT) | Application.requested_amount | identity | yes | ⚠️ include, but **scale mismatch** | HC loan median ~513k vs MCL 5–20k RM; **0% overlap** |
| `days_employed` | Borrower.employment_duration_years | `-days_employed/365.25`; sentinel 365243 → missing | yes | ✅ include | ~18% pensioner sentinel handled as missing |
| `housing_type_name` | Borrower.home_ownership | map {House/Office/Co-op→OWN; Rented/Municipal→RENT; With parents→OTHER} | yes | ✅ include | No `MORTGAGE` level in HC |
| `loan_body/income` | derived | ratio | yes | ✅ include | Scale-invariant (the one robust feature) |
| — (loan purpose) | Application.loan_intent | none — HC has contract type (Cash/Revolving), not purpose | **no** | ❌ exclude | Cannot reproduce MyCreditLens `loan_intent` |
| loan term | Application.requested_term_months | only approximable via `loan_body/annuity_payment` | partial | ❌ exclude | Approximate only; excluded for a clean contract |
| `external_source_1/2/3` | — | none | **no** | ❌ exclude | Proprietary external credit scores; not collected by MyCreditLens; bureau-derived |
| bureau / previous / installments / POS / credit_card | — | requires joins + point-in-time control | **no** | ❌ exclude | Not reproducible at MyCreditLens inference; offline research only |

**Gate result for Home Credit:** FAILS for deployment. Only a 6-feature subset is
reproducible (losing `loan_intent` and `term_years`); the two strongest raw
magnitudes (`income`, `loan_body`) are on a completely different scale from
MyCreditLens inputs (0% loan-range overlap), and Home Credit's real predictive
power (`external_source_*`, bureau) is inference-inaccessible.

### UCI / South German / Microloan gate

- **UCI Default of Credit Card Clients:** features are credit-card account
  behaviour (`PAY_0..6`, `BILL_AMT*`, `PAY_AMT*`, `LIMIT_BAL`). Only `AGE` maps.
  Gate FAILS — benchmark only.
- **South German Credit:** German-specific credit attributes; ≈1,000 rows. Gate
  FAILS — benchmark only.
- **Microloan India:** `Village_Risk_Score` and `Past_Repayment_History` are not
  MyCreditLens fields; only income/loan-size map. Gate weak — not adopted.

## Phase 2E — why not retrain the deployed model

Retraining the deployed model is justified only if a dataset materially improves
provenance, target validity, generalisation, calibration, feature relevance,
inference compatibility, or stability **without regressing deployment validity**.

Executed evidence (`MODEL_2_1_EVALUATION.md`):

| | Active 2.0.0 (LoanDataset) | Home Credit challenger (app-only) |
|---|---|---|
| Held-out ROC-AUC | **0.867** | 0.626 |
| Held-out PR-AUC | **0.733** | 0.124 |
| Inference features | 8 (full contract) | 6 (no loan_intent/term) |
| Loan-scale overlap with MyCreditLens | near-identical (median 8k vs 5–20k) | **0%** (median 513k) |
| Provenance | undocumented | documented (better) |
| Deployable on real MCL inputs | **yes** | no (extrapolation, undetected OOD) |

Home Credit improves **provenance** but fails on **deployment validity**, which is
decisive for a model that must score real MyCreditLens applications.

**The disqualifier is the 0% input-scale overlap** (Home Credit median loan ~513k
vs MyCreditLens 5–20k): the model would extrapolate on every real applicant and
the OOD detector would not flag it. This is independent of discrimination. The
ROC-AUC gap (0.63 vs 0.87) is *corroborating* but **confounded** — the challenger
changes dataset, feature count (6 vs 8), and scale simultaneously, so part of the
gap is Home Credit's genuinely harder real-default population, not only the lost
features. Net: not a material improvement for the deployed model, on the axis
(deployability) that is not confounded.

## What would change this decision (ADDITIONAL_DATA_REQUIRED for a real upgrade)

A promotion-worthy dataset would need: a documented real default/repayment
target; application-level features that map to the MyCreditLens form; an input
scale compatible with Malaysian RM incomes and small-ticket loans; and ideally an
application timestamp for out-of-time validation. The strongest single
improvement would be a **documented Malaysian (or RM-scale) labelled
default/repayment dataset**. Until then, 2.0.0 remains active and its metrics stay
labelled development-grade.
