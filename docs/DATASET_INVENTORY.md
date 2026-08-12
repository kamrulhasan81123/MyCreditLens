# Dataset Inventory (Phase 2A)

Last updated: 2026-08-12

Complete inventory of every dataset present in the project, plus datasets
collected in Phase 2B. **No model was trained during inventory.** The active
production model (2.0.0) is unchanged.

Recursive scan roots checked: `backend/ml/data/`, `data/`, `dataset/`,
`datasets/`, `dataset for training/`, `archive/`, `downloads/`. All dataset
files found live under `dataset for training/` (plus Phase 2B downloads under
`backend/ml/data/raw/`).

## Summary table

| Dataset | Path | Size | Rows | Cols | Target | Target meaning | Provenance | Geo | Synthetic/Real | Level | PD-suitable | Alt-data | Leakage risk | Recommendation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **LoanDataset (ACTIVE 2.0.0 source)** | `dataset for training/LoanDataset - LoansDatasest.csv` | 2.3 MB | 32,586 | 13 | `Current_loan_status` | DEFAULT / NO DEFAULT | **Undocumented** (public CSV, £-denominated) | UK-like | Real-looking, provenance unknown | Application | **Yes** (used) | No | Low after cleaning (bureau cols excluded) | **Keep as active dev training source** |
| loan_data.csv | `dataset for training/loan_data.csv` | 3.6 MB | 45,000 | 14 | `loan_status` | 1 default / 0 non-default | Kaggle "credit risk" (synthetic-augmented) | Mixed | **Synthetic-augmented** | Application | Partial | No | Requires `credit_score`, gender, education (inference-incompatible) | Reject for deployment (archived 0.977 bundle) |
| loan_risk_prediction_dataset.csv | `dataset for training/loan_risk_prediction_dataset.csv` | 0.3 MB | 5,000 | 10 | `LoanApproved` | **Approval decision, not repayment** | Undocumented | Unknown | Unknown | Application | **No** (approval-only) | No | Target is lender decision, not default | **Reject** (approval-only, per rules) |
| microloan_rural_india_data.csv | `dataset for training/microloan_rural_india_data.csv` | 0.2 MB | 10,000 | 5 | `Default` | 0/1 default (39% pos) | Undocumented | India (rural) | Unknown | Application | Marginal | No | `Village_Risk_Score`, `Past_Repayment_History` not reproducible | Downgrade (tiny, few mappable features) |
| Home Credit — application_train | `dataset for training/archive (5)/train.csv` | 140.6 MB | 261,384 | 122 | `target` (renamed) | Payment difficulties (real default) | **Documented** (Home Credit Group / Kaggle competition) | Eastern Europe | Real | Application | **Yes (real target)** — but see gate | No | `external_source_*` are proprietary scores → exclude | Research/benchmark challenger (see gate) |
| Home Credit — previous_loan | `dataset for training/archive (5)/previous_loan.csv` | 418.6 MB | 1,670,214 | 38 | — (secondary) | Prior application history | Documented | Eastern Europe | Real | Account/history | Feature-eng only | Some | Post-application leakage risk if joined naively | Offline research only |
| Home Credit — bureau/bureau_balance/installments/credit_card/POS | `dataset for training/archive (5)/*.csv` | ~2.6 GB total | 10M+ | varies | — (secondary) | Bureau + behaviour history | Documented | Eastern Europe | Real | Account/history | Feature-eng only | High if joined without point-in-time control | Offline research only; **not reproducible at MyCreditLens inference** |
| gig_workers.csv | `dataset for training/gig_workers.csv` | 16.2 MB | 120,000 | 27 | `credit_risk` / `credit_score_raw` | Synthetic gig credit signal | Undocumented / synthetic | Unknown | **Synthetic** | Account (monthly panel) | No (synthetic label) | Context/simulation | Contains `credit_score_raw` (synthetic) | Alt-data simulation only |
| gig_trips.csv | `dataset for training/gig_trips.csv` | 26.0 MB | 400,945 | 8 | — | Trip-level earnings | Undocumented / synthetic | Unknown | Synthetic | Transaction | No | Cash-flow feature source | n/a | Alt-data layer (transaction features) |
| transactions.csv | `dataset for training/transactions.csv` | 11.6 MB | 199,610 | 6 | `is_fraud` | **Fraud flag, not default** | Undocumented / synthetic | Unknown | Synthetic | Transaction | **No** (fraud ≠ default) | Cash-flow feature source | Fraud label must not be used as default | Alt-data layer only; do NOT use as PD label |
| UCI Default of Credit Card Clients (Phase 2B) | `backend/ml/data/raw/uci_default_credit_card/` | ~2.3 MB | 30,000 | 24 | `default payment next month` | Real default (next month) | **Documented** (UCI, Taiwan) | **Taiwan** | Real | Account (credit card) | Real target, but see gate | No | Payment-history/bill features are credit-card account data | External benchmark only (inference-incompatible) |

## Notes on provenance and honesty

- The active **LoanDataset** source has **undocumented provenance** and is
  £-denominated (UK-like); its metrics are development-grade, not evidence of
  real-world or Malaysian performance. This is its single biggest weakness.
- **Home Credit** is the only large, well-documented, real-default dataset
  present. Its column names are renamed (e.g. `reco_id_curr`, `income`,
  `loan_body`, `days_birth`), and its `train.csv` target is lowercase `target`.
  The bundled `.xlsx` column dictionary is not a valid Office file (could not be
  opened); Home Credit's schema is documented publicly.
- **UCI** is Taiwanese credit-card data — **not Malaysian**. It is a clean
  benchmark for methodology/calibration/fairness only.
- **OpenDOSM** (Malaysian socioeconomic statistics) was researched for
  localisation context; it provides **no borrower-level repayment outcome** and
  is therefore never used as a PD label (see `RETRAINING_DECISION.md`).
- `transactions.csv` carries an `is_fraud` label — **fraud is not default** and
  is never used as a PD target.

## Phase 2B datasets deliberately NOT collected

- **South German Credit** — skipped. ≈1,000 rows (too small for a primary model)
  and German-specific credit attributes that do not map to the MyCreditLens
  application (inference-incompatible; benchmark-only). It is scored from
  documentation in `DATASET_COMPARISON_REPORT.md` and flagged there as
  non-executed. Fetching it changes no decision.
- **Home Credit Credit Risk Model Stability** — skipped. The brief marks it
  optional ("do not make this mandatory if integration cost is excessive"). It is
  a large, multi-file Kaggle competition dataset whose value is temporal-stability
  research; integration cost is high and it cannot change a decision already
  settled by the standard Home Credit dataset's inference-gate failure. Documented
  as a future research option only.

## What each dataset is good for

- **Deployed application-PD model:** LoanDataset (current 2.0.0) — best
  inference + input-scale match to MyCreditLens (see `DATASET_COMPARISON_REPORT.md`).
- **External benchmark / methodology:** UCI (Taiwan), Home Credit (Eastern Europe).
- **Alternative-data research layer:** gig_workers / gig_trips / transactions
  (synthetic, cash-flow features only — no verified future default label).
- **Localisation context:** OpenDOSM (income/expenditure distributions only).
