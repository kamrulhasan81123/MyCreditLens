# Home Credit Default Risk (research / benchmark)

- **Dataset name:** Home Credit Default Risk
- **Original path:** `dataset for training/archive (5)/` (unmodified). Main table
  `train.csv`; secondary tables `previous_loan.csv`, `bureau*.csv`,
  `installments_payments.csv`, `credit_card_balance.csv`, `cash_pos_balance.csv`.
- **Original URL / publisher:** Home Credit Group, via the Kaggle competition
  "Home Credit Default Risk" (https://www.kaggle.com/c/home-credit-default-risk).
- **Download date:** present in repo before Phase 2 (bundled).
- **Licence:** Kaggle competition rules (research/educational use; competition
  data licensing applies — do not redistribute).
- **Geography:** Eastern Europe. NOT Malaysian.
- **Date range:** relative day-offsets only (`days_birth`, `days_employed`, …); no
  absolute application date.
- **Rows / cols (application_train):** 261,384 / 122. Column names are **renamed**
  in this copy (e.g. `reco_id_curr`, `income`, `loan_body`, `days_birth`,
  `housing_type_name`); target is lowercase `target`.
- **Target:** `target` = 1 if the client had payment difficulties (late payment
  beyond the defined threshold on early installments), else 0. ~8.2% positive.

## Role and gate result

Home Credit is the strongest **documented, real-default** dataset present, but it
**failed the inference-compatibility gate for deployment** (see
`docs/RETRAINING_DECISION.md`):

- Only a 6-feature subset maps to the MyCreditLens application (no `loan_intent`,
  no reliable `term_years`).
- Its strongest features (`external_source_1/2/3`) are proprietary bureau credit
  scores MyCreditLens cannot reproduce, and secondary tables require joins that
  are not reproducible at inference.
- **0% of Home Credit loans overlap MyCreditLens's loan range** (median loan
  ~513k vs MyCreditLens 5–20k) — a deployed Home Credit model would extrapolate
  on every real applicant.

It is retained as a **research/benchmark challenger** (`2.1.0-challenger`, not
promoted) under `backend/ml/artifacts/_challenger/home_credit_2_1_0/`.

**Point-in-time / leakage warning:** if secondary tables are ever used, every
feature must be aggregated at application level with strict point-in-time control
(no post-application information). This has not been done; secondary tables are
untouched.

Raw files are unmodified. See `dataset_manifest.json` for hash and counts.
