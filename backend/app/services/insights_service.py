"""Read-only insight services: safe model metadata, DB-backed monitoring, and
real age-band fairness + calibration-by-segment on the model's own held-out test
split.

Nothing here fabricates production performance. Where real repayment outcomes do
not exist, monitoring reports ``performance_status = outcome_data_unavailable``.
Fairness/calibration are computed on the labelled evaluation dataset (the model's
held-out test split), clearly a development-grade, not production, measurement.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.runtime import PROB_CEIL, PROB_FLOOR, CreditModelRuntime, load_credit_runtime
from app.config import BACKEND_DIR, settings
from app.models.data_source import DataSource
from app.models.model import MLModel
from app.models.prediction import Prediction

# Age bands for the fairness audit (customer_age is a model feature).
AGE_BANDS = [(18, 24), (25, 34), (35, 44), (45, 54), (55, 200)]
AGE_BAND_LABELS = ["18-24", "25-34", "35-44", "45-54", "55+"]
SMALL_GROUP_THRESHOLD = 50


def _runtime() -> CreditModelRuntime | None:
    artifact_dir = settings.resolved_model_artifact_path
    if not (artifact_dir / "manifest.json").is_file():
        return None
    try:
        return load_credit_runtime(artifact_dir)
    except Exception:
        return None


def _eval_dataset_path() -> Path | None:
    candidate = BACKEND_DIR.parent / "dataset for training" / "LoanDataset - LoansDatasest.csv"
    return candidate if candidate.is_file() else None


def safe_model_metadata(runtime: CreditModelRuntime) -> dict[str, Any]:
    """Model-card-safe metadata. Never exposes filesystem paths or secrets."""
    md = runtime.metadata
    t = md.get("test_metrics", {})
    return {
        "model_name": md.get("model_name"),
        "model_version": md.get("model_version"),
        "algorithm": md.get("algorithm", md.get("selected_model")),
        "target": md.get("target_definition"),
        "status": "active",
        "calibration_method": md.get("calibration_method"),
        "feature_schema_version": md.get("feature_schema_version"),
        "dataset_provenance_status": md.get(
            "data_status",
            "Development-grade model trained on a labelled dataset whose original provenance has not yet been independently verified.",
        ),
        "evaluation_summary": {
            "roc_auc": t.get("roc_auc"),
            "pr_auc": t.get("pr_auc"),
            "brier_score": t.get("brier_score"),
            "expected_calibration_error": t.get("expected_calibration_error"),
            "ks_statistic": t.get("ks_statistic"),
            "note": "Held-out test metrics on the training dataset; development-grade, not production performance.",
        },
        "thresholds": md.get("thresholds"),
        "limitations": md.get("limitations", []),
    }


class InsightsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Model metadata / registry
    # ------------------------------------------------------------------
    async def active_model(self) -> dict[str, Any]:
        runtime = _runtime()
        if runtime is None:
            return {"status": "artifact_missing", "detail": "No active model bundle is available."}
        meta = safe_model_metadata(runtime)
        row = (
            await self.db.execute(
                select(MLModel).where(MLModel.version == runtime.model_version, MLModel.model_name == runtime.model_name)
            )
        ).scalar_one_or_none()
        meta["registered"] = row is not None
        meta["model_id"] = row.id if row else None
        return meta

    async def sync_registry(self) -> MLModel:
        """Upsert the active bundle into the ml_models registry (idempotent).
        Stores metrics/provenance; keeps model_path server-side only."""
        runtime = _runtime()
        if runtime is None:
            raise ValueError("No active model bundle to register")
        md = runtime.metadata
        row = (
            await self.db.execute(
                select(MLModel).where(MLModel.version == runtime.model_version, MLModel.model_name == runtime.model_name)
            )
        ).scalar_one_or_none()
        params = {
            "calibration_method": md.get("calibration_method"),
            "feature_schema_version": md.get("feature_schema_version"),
            "target_definition": md.get("target_definition"),
            "dataset_name": md.get("dataset_name"),
            "dataset_provenance_status": md.get("data_status"),
            "thresholds": md.get("thresholds"),
            "limitations": md.get("limitations", []),
        }
        # Deactivate other models, activate this one.
        for other in (await self.db.execute(select(MLModel).where(MLModel.is_active.is_(True)))).scalars().all():
            if not (other.version == runtime.model_version and other.model_name == runtime.model_name):
                other.is_active = False
        if row is None:
            row = MLModel(
                model_name=runtime.model_name,
                version=runtime.model_version,
                model_type=md.get("algorithm", md.get("selected_model", "unknown")),
                is_active=True,
                model_path=str(settings.resolved_model_artifact_path),
                metrics=md.get("test_metrics", {}),
                parameters=params,
                feature_names=list(runtime.schema["raw_feature_order"]),
            )
            self.db.add(row)
        else:
            row.is_active = True
            row.model_type = md.get("algorithm", row.model_type)
            row.metrics = md.get("test_metrics", {})
            row.parameters = params
            row.feature_names = list(runtime.schema["raw_feature_order"])
        await self.db.commit()
        await self.db.refresh(row)
        return row

    # ------------------------------------------------------------------
    # Monitoring (DB-backed, no fabricated performance)
    # ------------------------------------------------------------------
    async def monitoring_summary(self) -> dict[str, Any]:
        runtime = _runtime()
        preds = (await self.db.execute(select(Prediction))).scalars().all()
        total = len(preds)

        pd_bins = [0.0, 0.05, 0.15, 0.30, 0.50, 1.01]
        pd_labels = ["0-5%", "5-15%", "15-30%", "30-50%", "50%+"]
        pd_hist = {label: 0 for label in pd_labels}
        band_dist: dict[str, int] = {}
        version_usage: dict[str, int] = {}
        volume_by_day: dict[str, int] = {}
        ood_count = 0
        uncertainties = []
        for p in preds:
            v = float(p.probability_of_default)
            for i in range(len(pd_bins) - 1):
                if pd_bins[i] <= v < pd_bins[i + 1]:
                    pd_hist[pd_labels[i]] += 1
                    break
            band_dist[p.risk_band] = band_dist.get(p.risk_band, 0) + 1
            ver = p.model_version or "unknown"
            version_usage[ver] = version_usage.get(ver, 0) + 1
            if p.is_ood:
                ood_count += 1
            if p.uncertainty is not None:
                uncertainties.append(float(p.uncertainty))
            if p.scored_at:
                day = p.scored_at.date().isoformat()
                volume_by_day[day] = volume_by_day.get(day, 0) + 1

        # Data-reliability distribution from uploaded data sources.
        reliab = [float(r) for r in (await self.db.execute(select(DataSource.reliability_score))).scalars().all() if r is not None]
        reliab_dist = {"high (>=0.8)": 0, "medium (0.5-0.8)": 0, "low (<0.5)": 0}
        for r in reliab:
            if r >= 0.8:
                reliab_dist["high (>=0.8)"] += 1
            elif r >= 0.5:
                reliab_dist["medium (0.5-0.8)"] += 1
            else:
                reliab_dist["low (<0.5)"] += 1

        manual_review = sum(1 for p in preds if p.risk_band == "medium") + ood_count

        return {
            "active_model_name": runtime.model_name if runtime else None,
            "active_model_version": runtime.model_version if runtime else None,
            "total_predictions": total,
            "pd_distribution": pd_hist,
            "risk_band_distribution": band_dist,
            "ood_rate": round(ood_count / total, 4) if total else None,
            "manual_review_rate": round(manual_review / total, 4) if total else None,
            "mean_uncertainty": round(float(np.mean(uncertainties)), 4) if uncertainties else None,
            "data_reliability_distribution": reliab_dist,
            "scoring_volume_over_time": dict(sorted(volume_by_day.items())),
            "model_usage": version_usage,
            "scoring_failure_count": "not_recorded",
            "inference_latency_ms": "not_recorded",
            "performance_status": "outcome_data_unavailable",
            "performance_note": (
                "Real repayment/default outcomes are not yet available, so production "
                "ROC-AUC, calibration, and realised default rate cannot be computed. "
                "Development-grade held-out metrics are available via the model metadata API."
            ),
        }

    # ------------------------------------------------------------------
    # Fairness (age-band) + calibration-by-segment on the eval test split
    # ------------------------------------------------------------------
    def _score_eval_test_split(self, runtime: CreditModelRuntime):
        """Reproduce the training test split (seed 42/43) and batch-score it with
        the active preprocessor+calibrator. Returns (raw_df, y_true, pd_pred)."""
        from sklearn.model_selection import train_test_split

        from ml.datasets.application_pd import RAW_FEATURE_ORDER, TARGET_COLUMN, load_application_pd_frame

        path = _eval_dataset_path()
        if path is None:
            return None
        frame, _ = load_application_pd_frame(path)
        y = frame[TARGET_COLUMN].to_numpy()
        X = frame[RAW_FEATURE_ORDER]
        tr, ho, ytr, yho = train_test_split(X, y, train_size=0.70, stratify=y, random_state=42)
        val, te, yval, yte = train_test_split(ho, yho, train_size=0.50, stratify=yho, random_state=43)
        Xt = np.asarray(runtime.preprocessor.transform(te), dtype=float)
        proba = np.clip(runtime.calibrator.predict_proba(Xt)[:, 1], PROB_FLOOR, PROB_CEIL)
        return te.reset_index(drop=True), yte, proba

    @staticmethod
    def _group_metrics(y: np.ndarray, p: np.ndarray, threshold: float) -> dict[str, Any]:
        from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

        n = int(len(y))
        pred = (p >= threshold).astype(int)
        tp = int(((pred == 1) & (y == 1)).sum())
        fp = int(((pred == 1) & (y == 0)).sum())
        fn = int(((pred == 0) & (y == 1)).sum())
        tn = int(((pred == 0) & (y == 0)).sum())
        pos = int((y == 1).sum())
        neg = int((y == 0).sum())
        both = len(np.unique(y)) == 2
        return {
            "sample_count": n,
            "observed_default_rate": round(float(y.mean()), 4) if n else None,
            "mean_predicted_pd": round(float(p.mean()), 4) if n else None,
            "selection_rate_flagged_high": round(float(pred.mean()), 4) if n else None,
            "false_positive_rate": round(fp / neg, 4) if neg else None,
            "false_negative_rate": round(fn / pos, 4) if pos else None,
            "true_positive_rate": round(tp / pos, 4) if pos else None,
            "brier_score": round(float(brier_score_loss(y, p)), 4) if both else None,
            "roc_auc": round(float(roc_auc_score(y, p)), 4) if both else None,
            "pr_auc": round(float(average_precision_score(y, p)), 4) if both else None,
            "small_group_warning": n < SMALL_GROUP_THRESHOLD,
        }

    def age_band_fairness(self, runtime: CreditModelRuntime) -> dict[str, Any]:
        scored = self._score_eval_test_split(runtime)
        if scored is None:
            return {"status": "dataset_unavailable", "detail": "Evaluation dataset not present."}
        te, y, p = scored
        threshold = float(runtime.thresholds.decision_threshold)
        ages = te["customer_age"].to_numpy()
        groups = {}
        selection_rates = {}
        tpr_by_group = {}
        for (lo, hi), label in zip(AGE_BANDS, AGE_BAND_LABELS):
            mask = (ages >= lo) & (ages <= hi)
            if mask.sum() == 0:
                groups[label] = {"sample_count": 0}
                continue
            gm = self._group_metrics(y[mask], p[mask], threshold)
            groups[label] = gm
            if gm["selection_rate_flagged_high"] is not None:
                selection_rates[label] = gm["selection_rate_flagged_high"]
            if gm["true_positive_rate"] is not None:
                tpr_by_group[label] = gm["true_positive_rate"]

        dp_diff = di_ratio = eo_diff = None
        if len(selection_rates) >= 2:
            vals = list(selection_rates.values())
            dp_diff = round(max(vals) - min(vals), 4)
            di_ratio = round((min(vals) / max(vals)) if max(vals) > 0 else 0.0, 4)
        if len(tpr_by_group) >= 2:
            tvals = list(tpr_by_group.values())
            eo_diff = round(max(tvals) - min(tvals), 4)

        return {
            "status": "evaluated",
            "sensitive_attribute": "customer_age (age band)",
            "note": (
                "Development-grade fairness audit on the model's held-out test split. "
                "NOT a legal or regulatory fairness certification. `customer_age` is a "
                "model feature; disparities are expected and shown for governance review."
            ),
            "decision_threshold": threshold,
            "groups": groups,
            "demographic_parity_difference": dp_diff,
            "disparate_impact_ratio": di_ratio,
            "equal_opportunity_difference": eo_diff,
        }

    def calibration_by_segment(self, runtime: CreditModelRuntime) -> dict[str, Any]:
        from ml.evaluation import expected_calibration_error

        scored = self._score_eval_test_split(runtime)
        if scored is None:
            return {"status": "dataset_unavailable", "detail": "Evaluation dataset not present."}
        te, y, p = scored
        from sklearn.metrics import brier_score_loss

        ages = te["customer_age"].to_numpy()
        segments = {}
        for (lo, hi), label in zip(AGE_BANDS, AGE_BAND_LABELS):
            mask = (ages >= lo) & (ages <= hi)
            n = int(mask.sum())
            if n < SMALL_GROUP_THRESHOLD or len(np.unique(y[mask])) < 2:
                segments[label] = {"sample_count": n, "status": "insufficient_sample"}
                continue
            yg, pg = y[mask], p[mask]
            edges = np.linspace(0, 1, 6)
            curve = []
            for i in range(len(edges) - 1):
                b = (pg >= edges[i]) & (pg < edges[i + 1] if edges[i + 1] < 1 else pg <= 1)
                if b.sum() > 0:
                    curve.append({"mean_predicted": round(float(pg[b].mean()), 4), "observed_rate": round(float(yg[b].mean()), 4), "n": int(b.sum())})
            segments[label] = {
                "sample_count": n,
                "observed_default_rate": round(float(yg.mean()), 4),
                "mean_predicted_pd": round(float(pg.mean()), 4),
                "brier_score": round(float(brier_score_loss(yg, pg)), 4),
                "expected_calibration_error": round(float(expected_calibration_error(yg, pg)), 4),
                "calibration_curve": curve,
            }
        return {"status": "evaluated", "segment_by": "age_band", "note": "Development-grade; held-out test split.", "segments": segments}
