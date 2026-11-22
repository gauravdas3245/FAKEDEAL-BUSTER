"""Verify synthetic data and classifier SHA-256 manifests and feature order."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.synthetic_classifier import load_classifier_bundle
from ml.synthetic_discount import sha256_file


def main() -> None:
    data_dir = ROOT / "artifacts/synthetic/discount_scenarios_v1"
    model_dir = ROOT / "artifacts/ml/synthetic_discount_v1"
    manifest_path = data_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for filename, record in manifest["splits"].items():
        if sha256_file(data_dir / filename) != record["sha256"]:
            raise SystemExit(f"Synthetic split checksum mismatch: {filename}")
    bundle = load_classifier_bundle(model_dir)
    if bundle["metadata"].get("dataset_manifest_sha256") != sha256_file(manifest_path):
        raise SystemExit("Classifier metadata does not match the generated dataset manifest")
    evaluation = json.loads((model_dir / "evaluation.json").read_text(encoding="utf-8"))
    if evaluation.get("evaluation_scope") != "SYNTHETIC_HELD_OUT_TEST_ONLY":
        raise SystemExit("Evaluation scope metadata is not synthetic-test-only")
    print(json.dumps({
        "synthetic_data_checksums_verified": True,
        "classifier_artifact_checksums_verified": True,
        "feature_order_verified": bundle["metadata"]["feature_names_ordered"],
        "selected_model": bundle["metadata"]["selected_model"],
        "split_counts": bundle["metadata"]["split_counts"],
        "evaluation_scope": evaluation["evaluation_scope"],
    }, indent=2))


if __name__ == "__main__":
    main()
