# application_pd_hist_gradient_boosting — Model Card

## Version
- Model name: `application_pd_hist_gradient_boosting`
- Model version: `2.0.0`
- Feature schema version: `app_pd_2.0.0`
- Algorithm: `hist_gradient_boosting`
- Calibration: `sigmoid`
- Trained at: 2026-08-12T13:03:16.076630+00:00

## Intended Use
Decision-support probability of default for MyCreditLens loan applications.
MyCreditLens is an **MVP decision-support system, not a certified autonomous
lending system**. A human analyst remains accountable for every decision.

## Prohibited Use
- Fully automated approve/reject without human review.
- Use on populations unlike the training data without revalidation.
- Treating the score as a legally certified or fairness-certified outcome.

## Target Definition
Binary personal-loan default outcome derived from Current_loan_status: 1 = DEFAULT, 0 = NO DEFAULT. Provenance of the underlying public CSV is undocumented in the repository; treat metrics as development-grade, not evidence of real-world or Malaysian-market performance.

## Dataset
- Name: `loan_dataset_uk_32k`
- SHA-256: `41e45a6462069c9e05484c3fa221cc7d257f5b71f14a60010bb684132d026381`
- Status: public dataset, provenance undocumented in repository; development-grade metrics only
- Rows (train/val/test): 22274/4773/4774

## Features (inference-safe only)
  - `customer_age`
  - `customer_income`
  - `employment_duration`
  - `home_ownership`
  - `loan_intent`
  - `loan_amnt`
  - `term_years`
  - `loan_percent_income`

### Excluded columns and why
  - `loan_grade` — Bureau/lender-assigned risk grade; not collected by MyCreditLens.
  - `loan_int_rate` — Lender-set rate derived from loan_grade; circular and not available at decision time.
  - `cred_hist_length` — Requires a credit bureau MyCreditLens does not integrate.
  - `historical_default` — Prior-default bureau flag; ~63% missing and not collected.
  - `customer_id` — Row identifier; not predictive.
  - `Current_loan_status` — Raw target column (mapped into `target`).

## Split Strategy
stratified_random (70/15/15). unavailable: dataset has no reliable application timestamp.

## Leakage Controls
Bureau/lender-assigned and outcome-adjacent columns are excluded (see above).
Preprocessing is fit on the training split only; calibration uses validation
only; the test split is scored once.

## Held-Out Test Metrics
- ROC-AUC: 0.8672
- PR-AUC: 0.7325
- Brier score: 0.0971
- Log loss: 0.3273
- Recall (default): 0.4677
- Precision (default): 0.8804
- Expected calibration error: 0.0134
- KS statistic: 0.5737

## Calibration
Selected `sigmoid`. The calibrator is fit on one half of the
validation slice and the method is selected out-of-sample on the other half
(then refit on the full validation slice for serving), so the selection is not
rigged by an in-sample isotonic fit. Served probabilities are clamped to
[0.0001, 0.9999] so no PD is
ever exactly 0 or 1. Calibration was not fit on the test split.

## Thresholds
Risk bands (from `thresholds.json`, selected from the test-set threshold sweep in
`evaluation_report.json`, §32): low < 0.05, medium <
0.3, else high; decision threshold
0.3. The decision threshold is the
F1-maximising cut; `low_max` is the largest cut below it keeping the low band's
observed default rate ≤5%. These are persisted separately from model weights and
are not hard-coded in route code.

## Model Selection
Weighted framework (discrimination/calibration/stability/explainability;
fairness evaluated separately): {'discrimination': 0.35, 'calibration': 0.25, 'stability': 0.15, 'explainability': 0.15, 'fairness': 0.1}.
Scores: {'logistic_regression': 0.3333333333333333, 'xgboost': 0.6816080387785695, 'lightgbm': 0.7138380795961143, 'hist_gradient_boosting': 0.7718730172949432, 'random_forest': 0.48050118323847457}.
EBM was trained as a glass-box challenger but is not active-eligible because the
serving runtime's explainer supports only linear and tree-SHAP strategies.

## Fairness
No protected attribute is part of the inference feature set, so in-model
fairness is not applicable; fairness must be audited separately on held-out
protected attributes. **No legal fairness certification is claimed.**

## OOD / Uncertainty
A distance-based OOD trigger (99th-percentile training distance) flags
out-of-distribution inputs for manual review. OOD is a confidence signal, not a
credit score.

## Limitations
- Trained on a public dataset with undocumented provenance; not validated on Malaysian or gig-worker populations.
- No formal default horizon is documented by the source; the target is a static DEFAULT/NO DEFAULT label.
- Out-of-time validation is unavailable (no application timestamp).
- Decision-support only; not a certified autonomous lending system.

## Deployment Architecture
Application fields → ApplicationToModelAdapter → preprocessor → model →
calibrator → probability of default → risk band → OOD/uncertainty → SHAP →
prediction persistence. Transaction/alternative-data signals are computed
separately and are NOT inputs to this model.

## Human Review Requirement
Medium-risk, low-confidence, and OOD-flagged applications are routed to manual
analyst review.
