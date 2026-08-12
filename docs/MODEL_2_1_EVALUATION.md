# Model 2.1.0-challenger Evaluation (Home Credit, application-only)

Last updated: 2026-08-12

A challenger was trained **only as executed evidence** for the retraining
decision. It is **not promoted** and is **not wired into scoring**. Model 2.0.0
remains the active production model. Artifacts:
`backend/ml/artifacts/_challenger/home_credit_2_1_0/` (results JSON).
Reproduce: `.venv\Scripts\python -m ml.experiments.home_credit_challenger`.

## Challenger design

- **Source:** Home Credit `application_train` (261,384 rows), application-only.
- **Features (inference-safe subset, 6):** `customer_age, customer_income,
  employment_duration, loan_amnt, loan_percent_income, home_ownership`.
- **Excluded:** `external_source_1/2/3` (proprietary bureau scores), all secondary
  tables, `loan_intent` (unavailable), `term_years` (only approximable).
- **Method:** stratified 70/15/15; preprocessing fit on train only; candidates
  LR / HistGB / XGBoost / LightGBM; calibration selected out-of-sample; probability
  clamped to [1e-4, 1-1e-4]. Selected: HistGradientBoosting.

## Head-to-head vs active 2.0.0

| Metric | **Active 2.0.0 (LoanDataset)** | 2.1.0-challenger (Home Credit app-only) |
|---|---|---|
| Held-out ROC-AUC | **0.8672** | 0.6257 |
| Held-out PR-AUC | **0.7325** | 0.1242 |
| Held-out Brier | 0.0971 | 0.0731 † |
| Held-out ECE | 0.0134 | 0.0003 |
| Inference features | **8** | 6 (no loan_intent / term_years) |
| Provenance | undocumented | **documented (better)** |
| Sample size | 31,821 | **261,384 (larger)** |
| Loan-scale overlap w/ MyCreditLens | median 8k ≈ MCL 5–20k | **0%** (median 513k) |
| Deployable on real MCL inputs | **yes** | no |

† The challenger's lower Brier **and** its tiny ECE (0.0003) are artefacts, not a
calibration win. Home Credit's ~8% base rate makes Brier small for any model, and
the challenger's isotonic step-function collapses the low-probability bins so
bin-wise predicted≈observed trivially — an uninformative ECE, not evidence of
better calibration. **Discrimination (ROC-AUC / PR-AUC) is the honest comparison,
and the challenger is far worse.** Do not read ECE 0.0003 vs 0.0134 as the
challenger winning.

**Why the numbers differ is confounded:** the challenger changes three things at
once vs 2.0.0 — dataset, feature count (6 vs 8), and input scale. Part of the
0.867→0.626 ROC-AUC gap is Home Credit's genuinely harder population (real 8%
defaults), not only the missing features. The AUC gap is therefore *corroborating*
evidence, not the disqualifier. **The disqualifier is the 0% input-scale overlap
below**, which is independent of discrimination.

## Deployment-validity evidence (scale / OOD)

- **0.0%** of Home Credit training loans fall in MyCreditLens's loan range
  (RM 5k–25k); Home Credit median loan ≈ 513,000.
- Two representative MyCreditLens applicants scored through the challenger's
  preprocessor had OOD distances 2.05 and 0.85 vs a p99 threshold of 2.11 — i.e.
  **not flagged OOD**, despite being far below any loan the model was trained on.
  The model would **silently extrapolate** on real applicants — worse than an
  honest OOD flag.

## Promotion gate — NOT PASSED

A challenger may become active only if it is **demonstrably better overall** and
passes the gate. This challenger:

- ❌ discrimination worse (0.63 vs 0.87 ROC-AUC)
- ❌ inference-safe feature contract narrower (loses loan_intent, term_years)
- ❌ input scale incompatible (0% loan overlap; undetected extrapolation)
- ✅ provenance better; ✅ larger sample; ✅ no leakage in the app-only subset

The **primary, independent disqualifier is the input-scale non-overlap** (❌
above); the discrimination gap corroborates but is partly confounded (see the
three-variables note). Net: **not demonstrably better overall for deployment.**
The challenger is retained for research/benchmark value only. **Active model remains 2.0.0.** No
`MODEL_ARTIFACT_PATH`, `MLModel` row, or artifact bundle was changed.
