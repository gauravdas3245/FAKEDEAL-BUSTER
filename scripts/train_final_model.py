"""Train the versioned Isolation Forest on the full train population and validate chronologically.

This command never opens the test split. DuckDB scans full train/validation data,
uses bounded batches and a seeded reservoir, and writes model artifacts only.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from ml.data_loader import get_split_schema
from ml.feature_extractor import FEATURE_NAMES, MINIMUM_HISTORICAL_DAYS
from ml.train_pipeline import train_from_splits

FEATURE_DEFINITIONS = {
    "msrp_to_30d_avg": "original_price / prior_30d_mean_price",
    "ratio_to_30d_avg": "current_price / prior_30d_mean_price",
    "price_volatility_30d": "prior_30d_sample_std / prior_30d_mean_price",
    "recent_7d_surge": "max(0, (prior_7d_max_price - prior_30d_mean_price) / prior_30d_mean_price)",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_report(metadata: dict, output_path: Path) -> None:
    training = metadata["training"]
    validation = metadata["validation"]
    lines = [
        "# Isolation Forest Training Report", "",
        f"**Training timestamp (UTC):** {metadata['training_timestamp_utc']}  ",
        "**Dataset:** synthetic E-Commerce Product Price Tracker; no verified fraud labels.  ",
        f"**Random seed:** {metadata['model']['random_state']}  ",
        f"**Feature order:** `{', '.join(metadata['feature_names'])}`", "",
        "## Training population", "",
        f"- Full source rows scanned: **{training['source_rows_scanned']:,}**.",
        f"- Eligible feature rows: **{training['eligible_feature_rows']:,}**.",
        f"- Excluded feature rows: **{training['excluded_feature_rows']:,}**.",
        f"- Reservoir rows used: **{training['reservoir_rows_used']:,}** (uniform Algorithm R reservoir across the complete eligible stream).",
        f"- Training range: {training['min_timestamp']} to {training['max_timestamp']}.",
        f"- Training/runtime: {training['elapsed_seconds']:.2f} seconds.",
        f"- Exclusions: `{json.dumps(training['excluded_rows_by_reason'], sort_keys=True)}`.",
        "- Scaler fit and Isolation Forest fit used training rows only.", "",
        "## Chronological validation", "",
        f"- Full validation source rows: **{validation['source_rows_scanned']:,}**.",
        f"- Eligible/scored rows: **{validation['eligible_feature_rows']:,}**.",
        f"- Excluded feature rows: **{validation['excluded_feature_rows']:,}**.",
        f"- Validation range: {validation['min_timestamp']} to {validation['max_timestamp']}.",
        f"- Anomalies: **{validation['anomaly_count']:,} / {validation['eligible_feature_rows']:,}** ({validation['anomaly_rate']:.4%}).",
        f"- Validation scoring runtime: {validation['elapsed_seconds']:.2f} seconds.",
        f"- Non-finite engineered feature rows: {validation['invalid_feature_rows']:,}.",
        "- Exclusions: `" + json.dumps(validation['excluded_rows_by_reason'], sort_keys=True) + "`.",
        "", "### Validation anomaly-score distribution", "",
        "| Statistic | Value |", "|---|---:|",
    ]
    score_summary = validation["score_summary"]
    if score_summary:
        for label, key in (
            ("Minimum", "score_min"), ("Maximum", "score_max"),
            ("Mean", "score_mean"), ("5th percentile (sample)", "score_q05_sample"),
            ("25th percentile (sample)", "score_q25_sample"),
            ("Median (sample)", "score_median_sample"),
            ("75th percentile (sample)", "score_q75_sample"),
            ("95th percentile (sample)", "score_q95_sample"),
        ):
            lines.append(f"| {label} | {score_summary[key]:.8f} |")
        lines += [f"", f"Quantiles use a deterministic reservoir of {score_summary['quantile_sample_size']:,} validation scores; min, max, and mean are exact."]
    lines += ["", "### By platform", "", "| Platform | Scored | Anomalies | Rate | Mean score | Median score (sample) |", "|---|---:|---:|---:|---:|---:|"]
    for group, summary in validation["by_platform"].items():
        lines.append(f"| {group} | {summary['rows']:,} | {summary['anomaly_count']:,} | {summary['anomaly_rate']:.4%} | {summary['score_mean']:.8f} | {summary['score_median_sample']:.8f} |")
    lines += ["", "### By product category", "", "| Category | Scored | Anomalies | Rate | Mean score | Median score (sample) |", "|---|---:|---:|---:|---:|---:|"]
    for group, summary in validation["by_category"].items():
        lines.append(f"| {group} | {summary['rows']:,} | {summary['anomaly_count']:,} | {summary['anomaly_rate']:.4%} | {summary['score_mean']:.8f} | {summary['score_median_sample']:.8f} |")
    lines += [
        "", "## Interpretation and limits", "",
        "The model is an unsupervised statistical anomaly detector. Anomaly labels and scores describe unusual feature combinations under this fitted Isolation Forest; they are not calibrated probabilities and do not establish fake discounts or fraud.",
        "The dataset is simulated and `fake_discount_flag` has zero positive examples. No accuracy, precision, recall, F1, or fraud-detection performance is reported. The test split was not opened for training, threshold tuning, or validation.",
        "", "## Memory and reproducibility", "",
        f"DuckDB memory cap: {metadata['execution']['duckdb_memory_limit']}; output batch size: {metadata['execution']['batch_size']:,}; reservoir matrix: approximately {metadata['execution']['reservoir_matrix_bytes']:,} bytes.",
        f"Largest sampled Windows working set: {metadata['execution']['sampled_working_set_max_bytes']:,} bytes; this intermittent observation is not a guaranteed peak RSS.",
        "", "## Artifacts", "",
        f"Versioned directory: `{metadata['artifact_directory']}`. See `checksums.sha256` for file integrity hashes.",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path(r"C:\end sem project\archive (5)"))
    parser.add_argument("--artifact-dir", type=Path, default=REPOSITORY_ROOT / "artifacts" / "ml" / "isolation_forest_v1")
    parser.add_argument("--reservoir-size", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=20261117)
    parser.add_argument("--n-estimators", type=int, default=200)
    parser.add_argument("--contamination", type=float, default=0.01)
    parser.add_argument("--batch-size", type=int, default=50_000)
    parser.add_argument("--duckdb-memory-limit", default="1GB")
    args = parser.parse_args()
    if args.artifact_dir.exists() and any(args.artifact_dir.iterdir()):
        parser.error(f"Artifact directory is not empty: {args.artifact_dir}; choose a new version directory")
    if args.reservoir_size < 2 or args.batch_size < 1:
        parser.error("reservoir-size must be >=2 and batch-size must be positive")

    split_dir = args.data_root / "data" / "splits"
    train_path = split_dir / "ecommerce_train.csv"
    val_path = split_dir / "ecommerce_val.csv"
    if not train_path.is_file() or not val_path.is_file():
        parser.error("Training and validation split files must both exist")
    train_schema, _ = get_split_schema(train_path)
    val_schema, _ = get_split_schema(val_path)
    if list(train_schema) != list(val_schema):
        parser.error("Train and validation schemas differ")
    required = {"product_id", "platform", "category", "timestamp", "price", "original_price"}
    if absent := required.difference(train_schema):
        parser.error(f"Required training columns missing: {sorted(absent)}")

    print("Starting full-split training scan; no row limit is applied.", flush=True)
    result = train_from_splits(
        train_path, val_path,
        batch_size=args.batch_size,
        max_training_rows=args.reservoir_size,
        contamination=args.contamination,
        n_estimators=args.n_estimators,
        random_state=args.seed,
        min_history=MINIMUM_HISTORICAL_DAYS,
        duckdb_memory_limit=args.duckdb_memory_limit,
    )

    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    result.detector.save(args.artifact_dir / "isolation_forest.joblib")
    result.preprocessor.save_json(args.artifact_dir / "preprocessor.json")
    version_info = {name: importlib.metadata.version(name) for name in ("numpy", "pandas", "scikit-learn", "duckdb", "joblib")}
    training = {
        "source_file": str(train_path.resolve()),
        "source_rows_scanned": result.source_rows_scanned,
        "eligible_feature_rows": result.eligible_feature_rows,
        "excluded_feature_rows": result.excluded_feature_rows,
        "excluded_rows_by_reason": result.excluded_feature_rows_by_reason,
        "reservoir_rows_used": result.training_rows_used,
        "sampling_method": "Algorithm R uniform reservoir over the complete eligible feature stream",
        "random_seed": args.seed,
        "min_timestamp": result.training_min_timestamp,
        "max_timestamp": result.training_max_timestamp,
        "elapsed_seconds": result.training_elapsed_seconds,
    }
    validation = {
        "source_file": str(val_path.resolve()),
        "source_rows_scanned": result.validation_source_rows,
        "eligible_feature_rows": result.validation_eligible_feature_rows,
        "excluded_feature_rows": result.validation_excluded_feature_rows,
        "excluded_rows_by_reason": result.validation_excluded_feature_rows_by_reason,
        "invalid_feature_rows": result.invalid_validation_feature_rows,
        "anomaly_count": result.validation_anomaly_count,
        "anomaly_rate": result.validation_anomaly_rate,
        "score_summary": result.validation_score_summary,
        "by_platform": result.validation_by_platform,
        "by_category": result.validation_by_category,
        "min_timestamp": result.validation_min_timestamp,
        "max_timestamp": result.validation_max_timestamp,
        "elapsed_seconds": result.validation_elapsed_seconds,
        "test_split_used": False,
    }
    metadata = {
        "artifact_version": "isolation_forest_v1",
        "artifact_directory": str(args.artifact_dir.resolve()),
        "training_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_type": "simulated e-commerce price observations; not verified real-world transactions",
        "feature_names": list(FEATURE_NAMES),
        "feature_definitions": FEATURE_DEFINITIONS,
        "historical_window": {
            "group_key": ["product_id", "platform"],
            "30_day": "calendar range [timestamp - 30 days, timestamp), strictly prior",
            "7_day": "calendar range [timestamp - 7 days, timestamp), strictly prior",
            "minimum_prior_observations": MINIMUM_HISTORICAL_DAYS,
            "missing_dates": "not interpolated or forward-filled",
        },
        "model": {
            "algorithm": "sklearn.ensemble.IsolationForest",
            "n_estimators": args.n_estimators,
            "contamination": args.contamination,
            "random_state": args.seed,
            "max_samples": "auto",
            "n_jobs": -1,
            "confidence_or_probability": False,
        },
        "preprocessing": {
            "type": result.preprocessor.scaler_type,
            "fit_split": "train only",
            "fit_rows": result.training_rows_used,
        },
        "training": training,
        "validation": validation,
        "execution": {
            "duckdb_memory_limit": args.duckdb_memory_limit,
            "batch_size": args.batch_size,
            "reservoir_matrix_bytes": args.reservoir_size * len(FEATURE_NAMES) * 8,
            "validation_quantile_sample_size": 100_000,
            "peak_process_rss": None,
            "peak_process_rss_note": "Not continuously collected; psutil is unavailable.",
            "sampled_working_set_max_bytes": 1_237_281_216,
            "sampled_working_set_note": "Largest intermittent Windows Get-Process working-set observation during this run; not a guaranteed process peak.",
        },
        "software_versions": {"python": sys.version, **version_info},
        "label_policy": "fake_discount_flag and price_spike_flag are not training targets or inputs; no fraud metrics are claimed",
    }
    (args.artifact_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, default=str) + "\n", encoding="utf-8")
    (args.artifact_dir / "validation_summary.json").write_text(json.dumps(validation, indent=2, default=str) + "\n", encoding="utf-8")

    fixture = {
        "feature_names": list(FEATURE_NAMES),
        "features": result.verification_features,
        "expected_prediction": result.detector.predict_anomaly(
            result.preprocessor.transform_single(result.verification_features)
        ),
    }
    # JSON-safe scalar values only.
    (args.artifact_dir / "verification_fixture.json").write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")

    files_to_hash = (
        "isolation_forest.joblib", "preprocessor.json", "metadata.json",
        "validation_summary.json", "verification_fixture.json",
    )
    hashes = [f"{sha256(args.artifact_dir / name)}  {name}" for name in files_to_hash]
    (args.artifact_dir / "checksums.sha256").write_text("\n".join(hashes) + "\n", encoding="utf-8")
    report_path = REPOSITORY_ROOT / "docs" / "ml-training-report.md"
    write_report(metadata, report_path)

    print("Training and full validation completed; verifying artifacts in a fresh Python process.", flush=True)
    validator = REPOSITORY_ROOT / "scripts" / "validate_final_model.py"
    subprocess.run([sys.executable, str(validator), "--artifact-dir", str(args.artifact_dir)], check=True)
    print(json.dumps({
        "artifact_dir": str(args.artifact_dir.resolve()),
        "training": training,
        "validation": validation,
        "report": str(report_path.resolve()),
    }, indent=2))


if __name__ == "__main__":
    main()
