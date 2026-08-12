# Current LoanDataset (active model 2.0.0 training source)

- **Dataset name:** LoanDataset (a.k.a. `LoanDataset - LoansDatasest.csv`)
- **Original path:** `dataset for training/LoanDataset - LoansDatasest.csv` (unmodified)
- **Original URL / publisher:** **Undocumented.** A public CSV bundled with the
  project; no LICENSE or provenance file accompanies it.
- **Download date:** unknown (present in repo before Phase 2)
- **Licence:** unknown
- **Geography:** UK-like (amounts are £-denominated)
- **Date range:** none (no application timestamp)
- **Rows / cols:** 32,586 / 13 (31,821 after cleaning; see model `dataset_manifest.json`)
- **Target:** `Current_loan_status` → 1 = DEFAULT, 0 = NO DEFAULT (~21% default)

## Role and honesty note

This is the training source for the **active production model 2.0.0**. It was
chosen and retained because its application-level features and **input scale**
(income median ~£55k, loan median ~£8k) match the MyCreditLens application form
and real RM-scale inputs closely — see `docs/DATASET_COMPARISON_REPORT.md`.

**Its metrics are development-grade only.** Because provenance is undocumented and
the data is not Malaysian, the model must not be presented as validated for
real-world or Malaysian lending. Replacing this with a documented, RM-scale,
labelled default dataset is the top data priority (see
`docs/RETRAINING_DECISION.md` and `docs/USER_INPUT_REQUIRED.md`).

Raw file is unmodified. See `dataset_manifest.json` for hash and counts.
