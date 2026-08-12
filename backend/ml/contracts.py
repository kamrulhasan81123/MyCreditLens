from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ARTIFACT_VERSION = "1.0"
REQUIRED_ARTIFACTS = (
    "preprocessor.joblib",
    "model.joblib",
    "calibrator.joblib",
    "feature_schema.json",
    "thresholds.json",
    "model_metadata.json",
    "explainer.joblib",
    "model_card.md",
)


@dataclass(frozen=True)
class RiskThresholds:
    low_max: float = 0.15
    medium_max: float = 0.30
    decision_threshold: float = 0.50

    def validate(self) -> None:
        if not 0 < self.low_max < self.medium_max < 1:
            raise ValueError("Risk thresholds must satisfy 0 < low < medium < 1")
        if not 0 < self.decision_threshold < 1:
            raise ValueError("Decision threshold must be between 0 and 1")

    def band(self, probability: float) -> str:
        if probability < self.low_max:
            return "low"
        if probability < self.medium_max:
            return "medium"
        return "high"

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(artifact_dir: Path) -> Path:
    missing = [name for name in REQUIRED_ARTIFACTS if not (artifact_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Artifact bundle is incomplete: {', '.join(missing)}")
    payload = {
        "artifact_contract_version": ARTIFACT_VERSION,
        "files": {name: sha256_file(artifact_dir / name) for name in REQUIRED_ARTIFACTS},
    }
    manifest_path = artifact_dir / "manifest.json"
    write_json(manifest_path, payload)
    return manifest_path


def verify_manifest(artifact_dir: Path) -> None:
    manifest_path = artifact_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("manifest.json is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("artifact_contract_version") != ARTIFACT_VERSION:
        raise ValueError("Unsupported artifact contract version")
    expected = manifest.get("files", {})
    for name in REQUIRED_ARTIFACTS:
        path = artifact_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"Required artifact is missing: {name}")
        if expected.get(name) != sha256_file(path):
            raise ValueError(f"Artifact checksum mismatch: {name}")
