# MyCreditLens Dataset Integration Plan

## Current Dataset Status

No final labelled credit dataset has been provided yet. The complete supervised training and artifact-backed inference code is implemented.

Development can continue with:

- deterministic feature engineering
- local synthetic transaction fixtures for tests
- explicitly labelled demo scoring
- offline training pipeline execution tests

Do not publish final model metrics until a real labelled dataset, target definition, and licence are confirmed.

## Recommended Initial Dataset

Use UCI Default of Credit Card Clients as the first real tabular credit-risk dataset.

Why:

- labelled default target
- manageable size for an MVP
- suitable for Logistic Regression, XGBoost/LightGBM, calibration, and SHAP
- easier integration than Home Credit for the first real model

Expected adapter:

```text
backend/ml/adapters/uci_default_credit.py
```

Expected user-provided inputs:

- dataset file path or download source
- licence confirmation
- target definition confirmation
- approved feature list

## Recommended Advanced Dataset

Use Home Credit Default Risk after the initial pipeline works.

Why:

- richer feature space
- stronger final-year project experimentation
- better fit for model comparison and leakage discussion

Risks:

- larger data
- more complex joins
- higher leakage risk
- slower iteration

## Malaysian Localisation

Use OpenDOSM household income and expenditure data for context, synthetic ranges, and discussion only unless labelled lending outcomes are available.

Do not claim Malaysian predictive validity without Malaysian labelled repayment data.

## Synthetic Fixtures

Synthetic fixtures may be used for:

- parser tests
- feature formula tests
- API smoke tests
- frontend demonstrations

Synthetic fixtures must be labelled as synthetic and must not be used to report final model performance.

## Artifact Contract

The final training pipeline must export:

```text
preprocessor.joblib
model.joblib
calibrator.joblib
feature_schema.json
thresholds.json
model_metadata.json
explainer.joblib
model_card.md
```

FastAPI inference must load artifacts only. It must not retrain on startup.

## Implemented Training Command

```powershell
cd backend
python -m ml.train --dataset C:\path\to\dataset.csv --target default_90d --target-definition "1 = default within 90 days; 0 = no default within observation window" --dataset-name approved_dataset --output-dir ml\artifacts
```

For the UCI adapter:

```powershell
python -m ml.train --adapter uci_default_credit --dataset C:\path\to\default_of_credit_card_clients.xlsx --target-definition "UCI default payment next month label" --dataset-name uci_default_credit --output-dir ml\artifacts
```

The generic dataset used for deployed application scoring must contain the same transaction-derived features produced by `FeatureEngineer`. A conventional UCI model with incompatible columns is valid for experimentation but will be rejected by live application inference.
