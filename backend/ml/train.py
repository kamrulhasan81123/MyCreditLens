from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from ml.adapters.uci_default_credit import load_uci_default_credit
from ml.contracts import RiskThresholds
from ml.training import TrainingConfig, train_credit_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train and export a MyCreditLens credit-risk model")
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--target")
    parser.add_argument("--adapter", choices=["generic", "uci_default_credit"], default="generic")
    parser.add_argument("--output-dir", type=Path, default=Path("ml/artifacts"))
    parser.add_argument("--model-version", default="1.0.0")
    parser.add_argument("--group-column")
    parser.add_argument("--time-column")
    parser.add_argument("--protected-column", action="append", default=[])
    parser.add_argument("--drop-column", action="append", default=[])
    parser.add_argument("--positive-label", default="1")
    parser.add_argument("--dataset-name", default="user_provided")
    parser.add_argument("--target-definition", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.adapter == "uci_default_credit":
        frame, target = load_uci_default_credit(args.dataset)
    else:
        frame = pd.read_csv(args.dataset)
        target = args.target
    if not target:
        raise SystemExit("--target is required for the generic adapter")
    positive_label: int | str = int(args.positive_label) if args.positive_label.isdigit() else args.positive_label
    metadata = train_credit_model(
        frame,
        TrainingConfig(
            target_column=target,
            output_dir=args.output_dir,
            model_version=args.model_version,
            positive_label=positive_label,
            group_column=args.group_column,
            time_column=args.time_column,
            protected_columns=tuple(args.protected_column),
            drop_columns=tuple(args.drop_column),
            thresholds=RiskThresholds(),
            dataset_name=args.dataset_name,
            target_definition=args.target_definition,
        ),
    )
    print(f"Exported {metadata['model_name']} {metadata['model_version']} to {args.output_dir}")


if __name__ == "__main__":
    main()
