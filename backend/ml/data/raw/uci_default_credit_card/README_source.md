# UCI — Default of Credit Card Clients

- **Dataset name:** Default of Credit Card Clients
- **Original URL:** https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients
- **Publisher:** UCI Machine Learning Repository (data by I-Cheng Yeh)
- **Download date:** 2026-08-12
- **Licence:** Creative Commons Attribution 4.0 (CC BY 4.0), per UCI listing
- **Geography:** **Taiwan** (credit-card clients, 2005). NOT Malaysian.
- **Date range:** April–September 2005 (billing/payment history), default observed October 2005
- **Rows / cols:** 30,000 / 25 (incl. `ID`)
- **Target:** `default payment next month` (1 = default next month, 0 = no default). Class balance ≈ 22.1% positive.
- **Features:** `LIMIT_BAL`, `SEX`, `EDUCATION`, `MARRIAGE`, `AGE`, `PAY_0..PAY_6` (repayment status history), `BILL_AMT1..6` (bill statements), `PAY_AMT1..6` (prior payments).

## Known limitations & role in MyCreditLens

- The target is a **real, documented** next-month default — a clean benchmark for
  methodology, calibration, and fairness experiments.
- **Inference-incompatible** with the MyCreditLens application: the predictive
  features are credit-card account behaviour (payment/bill history) that
  MyCreditLens does not collect. Only `AGE` maps. Therefore this dataset is used
  **only as an external benchmark**, never as a MyCreditLens training source.
- Geography is Taiwanese; do not present as Malaysian.

Raw file is unmodified. See `dataset_manifest.json` for hash and counts.
