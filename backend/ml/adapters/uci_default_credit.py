from __future__ import annotations

from pathlib import Path

import pandas as pd


TARGET_ALIASES = (
    "default payment next month",
    "default.payment.next.month",
    "default_payment_next_month",
    "target",
)


def load_uci_default_credit(path: str | Path) -> tuple[pd.DataFrame, str]:
    dataset_path = Path(path)
    if not dataset_path.is_file():
        raise FileNotFoundError(dataset_path)
    if dataset_path.suffix.lower() in {".xls", ".xlsx"}:
        frame = pd.read_excel(dataset_path, header=1)
    else:
        frame = pd.read_csv(dataset_path)
    normalized = {str(column).strip().lower(): column for column in frame.columns}
    target = next((normalized[name] for name in TARGET_ALIASES if name in normalized), None)
    if target is None:
        raise ValueError(f"UCI target column not found. Expected one of: {', '.join(TARGET_ALIASES)}")
    if "ID" in frame.columns:
        frame = frame.drop(columns=["ID"])
    return frame, str(target)
