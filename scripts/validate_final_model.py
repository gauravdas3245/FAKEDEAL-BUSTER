"""Verify model artifact checksums and prediction consistency in a fresh process."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from ml.feature_extractor import FEATURE_NAMES
from ml.isolation_forest import IsolationForestDetector
from ml.preprocessor import FeaturePreprocessor


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.artifact_dir.resolve()
    checksum_file = root / "checksums.sha256"
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        expected, filename = line.split("  ", 1)
        actual = sha256(root / filename)
        if actual != expected:
            raise SystemExit(f"Checksum mismatch: {filename}")

    metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
    fixture = json.loads((root / "verification_fixture.json").read_text(encoding="utf-8"))
    if fixture["feature_names"] != list(FEATURE_NAMES) or metadata["feature_names"] != list(FEATURE_NAMES):
        raise SystemExit("Feature order mismatch")

    preprocessor = FeaturePreprocessor.load_json(root / "preprocessor.json")
    detector = IsolationForestDetector.load(root / "isolation_forest.joblib")
    scaled = preprocessor.transform_single(fixture["features"])
    actual = detector.predict_anomaly(scaled)
    expected = fixture["expected_prediction"]
    if actual["raw_prediction"] != expected["raw_prediction"] or actual["is_anomaly"] != expected["is_anomaly"]:
        raise SystemExit("Prediction label mismatch after fresh-process artifact load")
    if not math.isclose(actual["anomaly_score"], expected["anomaly_score"], rel_tol=1e-12, abs_tol=1e-12):
        raise SystemExit("Prediction score mismatch after fresh-process artifact load")

    print(json.dumps({
        "artifact_dir": str(root),
        "checksums_verified": True,
        "fresh_process_load_verified": True,
        "feature_order": list(FEATURE_NAMES),
        "fixture_prediction": actual,
        "artifact_version": metadata["artifact_version"],
    }, indent=2))


if __name__ == "__main__":
    main()
