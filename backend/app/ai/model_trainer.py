from __future__ import annotations

import pandas as pd

from ml.training import TrainingConfig, train_credit_model


class ModelTrainer:
    """Compatibility facade for the offline supervised training pipeline."""

    @staticmethod
    def train_dataset(frame: pd.DataFrame, config: TrainingConfig) -> dict:
        return train_credit_model(frame, config)

    @staticmethod
    def train(*args, **kwargs):
        raise RuntimeError(
            "The prototype in-memory trainer was removed because it fabricated metrics. "
            "Use ModelTrainer.train_dataset(frame, TrainingConfig(...)) with labelled data."
        )
