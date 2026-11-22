"""Compare LR/RF on held-out generated discount scenarios only."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.synthetic_classifier import train_classifier_suite
from ml.synthetic_discount import sha256_file


def _report(result: dict) -> str:
    metadata = result["metadata"]
    evaluation = result["evaluation"]
    lines = [
        "# Synthetic Discount Scenario Classifier Evaluation",
        "",
        "**Evaluation scope: held-out synthetic test data only. These metrics are not real-world fraud accuracy.**",
        "",
        f"Selected using validation only: `{metadata['selected_model']}` at threshold `{metadata['selected_threshold']:.4f}`.",
        f"Threshold rule: {metadata['threshold_objective']}",
        "",
        "| Model | Threshold | Precision | Recall | F1 | ROC-AUC | PR-AUC (AP) | Gini (2*AUC-1) | FP rate on synthetic genuine | Test n |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, metrics in evaluation["test_metrics"].items():
        cm = metrics["confusion_matrix_labels_0_then_1"]
        lines.append(
            f"| {name} | {metrics['threshold']:.4f} | {metrics['precision']:.4f} | {metrics['recall']:.4f} | "
            f"{metrics['f1']:.4f} | {metrics['roc_auc']:.4f} | {metrics['pr_auc_average_precision']:.4f} | "
            f"{metrics['gini_coefficient_2auc_minus_1']:.4f} | {metrics['false_positive_rate_on_synthetic_genuine']:.4f} | "
            f"{sum(cm.values())} |"
        )
    lines += [
        "",
        "Confusion matrices are encoded in `evaluation.json` as TN/FP/FN/TP for synthetic labels 0/1.",
        "Label 1 is the generator-assigned artificially inflated reference-price scenario; label 0 is the generator-assigned genuine-discount scenario.",
        "",
        "Preprocessing (median imputation, categorical one-hot encoding, and LR scaling) is fitted inside each model pipeline on the training split only. The validation split selects each decision threshold and the model; the test split is held out until final metrics.",
        "",
        "These generated examples and labels do not establish real listing fraud or seller intent. Production Isolation Forest output remains separate. Synthetic classifier output is labelled as scenario resemblance only.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "artifacts/synthetic/discount_scenarios_v1")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/ml/synthetic_discount_v1")
    parser.add_argument("--seed", type=int, default=20261118)
    parser.add_argument("--rf-estimators", type=int, default=300)
    parser.add_argument("--overwrite", action="store_true", help="Overwrite only this synthetic classifier output directory")
    args = parser.parse_args()
    manifest_path = args.data_dir / "manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"Synthetic dataset manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("dataset_version") != "synthetic_discount_scenarios_v1" or not manifest.get("synthetic_only"):
        raise SystemExit("Refusing to train: dataset is not a recognized synthetic scenario bundle")
    filenames = ("train.csv", "validation.csv", "test.csv")
    for filename in filenames:
        path = args.data_dir / filename
        expected = manifest.get("splits", {}).get(filename, {}).get("sha256")
        if not expected or sha256_file(path) != expected:
            raise SystemExit(f"Synthetic data checksum mismatch: {filename}")
    splits = [pd.read_csv(args.data_dir / filename) for filename in filenames]
    result = train_classifier_suite(*splits, artifact_dir=args.output, seed=args.seed,
                                    rf_estimators=args.rf_estimators,
                                    dataset_manifest_sha256=sha256_file(manifest_path),
                                    overwrite=args.overwrite)
    report = _report(result)
    (args.output / "comparison_report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
