"""Quick analysis of all datasets to determine the best training strategy."""
import pandas as pd
from pathlib import Path

DATASET_DIR = Path(__file__).resolve().parent.parent.parent / "dataset for training"

datasets = {
    "loan_risk_prediction_dataset.csv": None,
    "loan_data.csv": None,
    "microloan_rural_india_data.csv": None,
    "gig_workers.csv": None,
    "gig_trips.csv": None,
    "transactions.csv": None,
    "LoanDataset - LoansDatasest.csv": None,
}

for name in datasets:
    path = DATASET_DIR / name
    if path.exists():
        try:
            df = pd.read_csv(path)
            datasets[name] = df
            print(f"\n{'='*60}")
            print(f"FILE: {name}")
            print(f"Shape: {df.shape}")
            print(f"Columns: {df.columns.tolist()}")
            print(f"Dtypes:\n{df.dtypes.to_string()}")
            print(f"Null counts:\n{df.isnull().sum().to_string()}")
            print(f"First 2 rows:\n{df.head(2).to_string()}")
        except Exception as e:
            print(f"ERROR reading {name}: {e}")
    else:
        print(f"NOT FOUND: {name}")