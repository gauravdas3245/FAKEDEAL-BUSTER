"""Evaluate the frozen v1 Isolation Forest on the untouched chronological test split.

Only train and validation observations are included as historical context. The test
split is scored once for descriptive anomaly metrics; no fitting or threshold tuning
is performed, and no label columns are used.
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import time

import duckdb
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.feature_extractor import FEATURE_NAMES
from ml.inference import load_inference_engine
from ml.train_pipeline import _ScoreAccumulator, _source_census, iter_feature_batches


def manifest_hashes(artifact_dir: Path) -> dict:
    hashes = {}
    for line in (artifact_dir / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        expected, filename = line.split("  ", 1)
        digest = hashlib.sha256()
        with (artifact_dir / filename).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        actual = digest.hexdigest()
        if actual != expected:
            raise RuntimeError(f"Artifact checksum mismatch before/after evaluation: {filename}")
        hashes[filename] = actual
    return hashes


def split_bounds(path: Path, memory_limit: str) -> tuple[int, str, str]:
    escaped = path.resolve().as_posix().replace("'", "''")
    con = duckdb.connect()
    try:
        con.execute("SET memory_limit = ?", [memory_limit])
        con.execute("SET threads = 1")
        count, minimum, maximum = con.execute(
            f"SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM read_csv_auto('{escaped}')"
        ).fetchone()
        if not count:
            raise ValueError(f"Split is empty: {path}")
        return int(count), str(minimum), str(maximum)
    finally:
        con.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True,
                        help="Dataset root containing data/splits/ecommerce_{train,val,test}.csv")
    parser.add_argument("--artifact-dir", type=Path,
                        default=ROOT / "artifacts/ml/isolation_forest_v1")
    parser.add_argument("--output-json", type=Path,
                        default=ROOT / "artifacts/ml/evaluations/v1_test_evaluation.json")
    parser.add_argument("--output-report", type=Path,
                        default=ROOT / "docs/ml-test-evaluation-report.md")
    parser.add_argument("--batch-size", type=int, default=25_000)
    parser.add_argument("--duckdb-memory-limit", default="1GB")
    parser.add_argument("--quantile-sample-size", type=int, default=100_000)
    args = parser.parse_args()
    if args.batch_size <= 0 or args.quantile_sample_size <= 0:
        parser.error("batch-size and quantile-sample-size must be positive")

    split_dir = args.data_root.resolve() / "data" / "splits"
    train_path = split_dir / "ecommerce_train.csv"
    val_path = split_dir / "ecommerce_val.csv"
    test_path = split_dir / "ecommerce_test.csv"
    missing = [str(p) for p in (train_path, val_path, test_path) if not p.is_file()]
    if missing:
        parser.error(f"Required chronological split files are missing: {missing}")

    checksums_before = manifest_hashes(args.artifact_dir)
    engine = load_inference_engine(args.artifact_dir)
    if engine.metadata["feature_names"] != list(FEATURE_NAMES):
        raise RuntimeError("Loaded v1 feature order differs from the canonical contract")

    splits = {
        "train": split_bounds(train_path, args.duckdb_memory_limit),
        "validation": split_bounds(val_path, args.duckdb_memory_limit),
        "test": split_bounds(test_path, args.duckdb_memory_limit),
    }
    if not (splits["train"][2] < splits["validation"][1] < splits["validation"][2] < splits["test"][1]):
        raise ValueError(f"Split boundaries are not strictly chronological: {splits}")
    source_census = _source_census(test_path, args.duckdb_memory_limit)
    test_start = splits["test"][1]
    started = time.perf_counter()
    overall = _ScoreAccumulator(args.quantile_sample_size, random_state=20261128)
    by_platform: dict[str, _ScoreAccumulator] = {}
    by_category: dict[str, _ScoreAccumulator] = {}
    invalid_features = 0
    prediction_score_mismatches = 0
    prediction_label_mismatches = 0
    raw_prediction_mismatches = 0
    score_sign_flag_mismatches = 0
    emitted = 0

    # Historical context is read from all chronological splits, but only rows
    # at/after test_start are yielded and scored. RANGE windows exclude future rows.
    for frame in iter_feature_batches(
        test_path,
        batch_size=args.batch_size,
        history_csv_paths=[train_path, val_path, test_path],
        output_start=test_start,
        include_category=True,
        preserve_result_order=False,
        duckdb_memory_limit=args.duckdb_memory_limit,
    ):
        emitted += len(frame)
        values = frame.loc[:, list(FEATURE_NAMES)].to_numpy(dtype=np.float64)
        valid = np.isfinite(values).all(axis=1)
        invalid_features += int((~valid).sum())
        if not valid.any():
            continue
        valid_frame = frame.loc[valid].reset_index(drop=True)
        scaled = engine.preprocessor.transform(values[valid])
        prediction = engine.detector.predict_anomaly(scaled)
        scores = np.asarray(prediction["anomaly_score"], dtype=np.float64)
        flags = np.asarray(prediction["is_anomaly"], dtype=bool)
        raw = np.asarray(prediction["raw_prediction"], dtype=np.int8)
        # Independently compare wrapper output against the saved estimator APIs.
        direct_scores = -engine.detector.model.decision_function(scaled)
        direct_raw = engine.detector.model.predict(scaled)
        prediction_score_mismatches += int(np.count_nonzero(~np.isclose(
            scores, direct_scores, rtol=0.0, atol=1e-14)))
        prediction_label_mismatches += int(np.count_nonzero(flags != (direct_raw == -1)))
        raw_prediction_mismatches += int(np.count_nonzero(raw != direct_raw))
        score_sign_flag_mismatches += int(np.count_nonzero(flags != (scores > 0.0)))

        overall.update(scores, flags)
        platforms = valid_frame["platform"].astype(str).to_numpy()
        categories = valid_frame["category"].astype(str).to_numpy()
        for key in np.unique(platforms):
            selected = platforms == key
            by_platform.setdefault(key, _ScoreAccumulator(args.quantile_sample_size, 20261128)).update(
                scores[selected], flags[selected]
            )
        for key in np.unique(categories):
            selected = categories == key
            by_category.setdefault(key, _ScoreAccumulator(args.quantile_sample_size, 20261128)).update(
                scores[selected], flags[selected]
            )

    elapsed = time.perf_counter() - started
    if emitted != splits["test"][0]:
        raise RuntimeError(f"Test rows yielded ({emitted}) do not match source rows ({splits['test'][0]})")
    if overall.count != emitted - invalid_features:
        raise RuntimeError("Feature eligibility and scoring counts do not reconcile")

    checksums_after = manifest_hashes(args.artifact_dir)
    if checksums_before != checksums_after:
        raise RuntimeError("One or more saved v1 artifacts changed during test evaluation")

    validation_reference = engine.metadata["validation"]
    validation_score = validation_reference["score_summary"]

    def segment_comparison(validation_segments: dict, scored_segments: dict) -> dict:
        comparison = {}
        for name in sorted(set(validation_segments) | set(scored_segments)):
            validation_rate = validation_segments.get(name, {}).get("anomaly_rate")
            test_rate = scored_segments.get(name, {}).get("anomaly_rate")
            comparison[name] = {
                "validation_anomaly_rate": validation_rate,
                "test_anomaly_rate": test_rate,
                "delta_percentage_points": (
                    (test_rate - validation_rate) * 100
                    if validation_rate is not None and test_rate is not None else None
                ),
            }
        return comparison

    summary = {
        "evaluation_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_type": "frozen_model_anomaly_detection_only",
        "dataset_type": engine.metadata.get("dataset_type"),
        "artifact_version": engine.model_version,
        "test_split_used_for_scoring_only": True,
        "test_labels_used": False,
        "test_source_rows_scanned": source_census["source_rows"],
        "test_source_invalid_raw_input_rows": source_census["invalid_input_rows"],
        "test_rows_emitted_for_scoring": emitted,
        "eligible_scored_rows": overall.count,
        "invalid_engineered_feature_rows": invalid_features,
        "test_boundaries": {
            "train": {"rows": splits["train"][0], "min": splits["train"][1], "max": splits["train"][2]},
            "validation": {"rows": splits["validation"][0], "min": splits["validation"][1], "max": splits["validation"][2]},
            "test": {"rows": splits["test"][0], "min": splits["test"][1], "max": splits["test"][2]},
        },
        "feature_names": list(FEATURE_NAMES),
        "scoring": {
            "anomaly_count": overall.anomaly_count,
            "anomaly_rate": overall.anomaly_count / overall.count if overall.count else None,
            "score_summary": overall.summary(),
            "by_platform": {key: acc.summary() for key, acc in sorted(by_platform.items())},
            "by_category": {key: acc.summary() for key, acc in sorted(by_category.items())},
        },
        "comparison_to_validation": {
            "validation_anomaly_rate": validation_reference["anomaly_rate"],
            "test_anomaly_rate": overall.anomaly_count / overall.count if overall.count else None,
            "anomaly_rate_delta_percentage_points": (
                (overall.anomaly_count / overall.count - validation_reference["anomaly_rate"]) * 100
                if overall.count else None
            ),
            "validation_score_mean": validation_score["score_mean"],
            "test_score_mean": overall.summary()["score_mean"] if overall.count else None,
            "score_mean_delta": (
                overall.summary()["score_mean"] - validation_score["score_mean"] if overall.count else None
            ),
            "by_platform": segment_comparison(validation_reference["by_platform"],
                                              {key: acc.summary() for key, acc in by_platform.items()}),
            "by_category": segment_comparison(validation_reference["by_category"],
                                              {key: acc.summary() for key, acc in by_category.items()}),
            "interpretation": "Descriptive drift comparison only; validation values do not tune or alter the frozen model or threshold.",
        },
        "prediction_consistency": {
            "wrapper_vs_direct_score_mismatches": prediction_score_mismatches,
            "wrapper_vs_estimator_flag_mismatches": prediction_label_mismatches,
            "wrapper_raw_prediction_mismatches": raw_prediction_mismatches,
            "flag_vs_positive_wrapper_score_mismatches": score_sign_flag_mismatches,
            "score_orientation": "higher anomaly_score is more anomalous; wrapper score is -decision_function",
        },
        "classification_metrics": {
            "available": False,
            "accuracy": None,
            "precision": None,
            "recall": None,
            "f1": None,
            "reason": "No verified fake-discount ground truth is available. The candidate fake_discount_flag has zero positives and undocumented generation logic; price_spike_flag is not fake-discount ground truth and was not used.",
        },
        "runtime_seconds": elapsed,
        "duckdb_memory_limit": args.duckdb_memory_limit,
        "batch_size": args.batch_size,
        "quantile_sample_size": min(overall.count, args.quantile_sample_size),
        "artifact_checksums_before": checksums_before,
        "artifact_checksums_after": checksums_after,
        "artifact_checksums_unchanged": True,
        "test_split_used_for_training_or_threshold_tuning": False,
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_report.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    score = summary["scoring"]["score_summary"]
    lines = [
        "# Frozen Isolation Forest v1: untouched test-split evaluation", "",
        f"**Evaluation time (UTC):** {summary['evaluation_timestamp_utc']}  ",
        "**Evaluation:** anomaly detection only; model, scaler, and threshold unchanged.  ",
        f"**Artifact:** `{engine.model_version}`; source dataset is {summary['dataset_type']}.  ",
        "**Test labels:** not used. The test split was not used for fitting or threshold tuning.", "",
        "## Data and score totals", "",
        f"- Test rows scanned/emitted: {emitted:,}.",
        f"- Eligible/scored: {overall.count:,}; invalid engineered features: {invalid_features:,}.",
        f"- Anomalies: {overall.anomaly_count:,} ({overall.anomaly_count / overall.count:.4%}).",
        f"- Test timestamp range: {splits['test'][1]} to {splits['test'][2]}.",
        f"- Runtime: {elapsed:.2f} seconds; DuckDB cap {args.duckdb_memory_limit}; batch size {args.batch_size:,}.",
        "- Historical context: train + validation + test rows are window input; only test-period rows are emitted. Strict prior calendar windows exclude the current/future timestamps.", "",
        "### Anomaly-score distribution", "",
        "| Statistic | Value |", "|---|---:|",
        f"| Minimum (exact) | {score['score_min']:.9f} |",
        f"| Maximum (exact) | {score['score_max']:.9f} |",
        f"| Mean (exact) | {score['score_mean']:.9f} |",
        f"| 5th percentile (bounded deterministic reservoir) | {score['score_q05_sample']:.9f} |",
        f"| 25th percentile (sample) | {score['score_q25_sample']:.9f} |",
        f"| Median (sample) | {score['score_median_sample']:.9f} |",
        f"| 75th percentile (sample) | {score['score_q75_sample']:.9f} |",
        f"| 95th percentile (sample) | {score['score_q95_sample']:.9f} |", "",
        "Quantiles use deterministic Algorithm R reservoirs per grouping; exact min, max, and mean are streaming aggregates.", "",
        "## Anomaly rate by platform", "",
        "| Platform | Scored | Anomalies | Rate | Mean score | Median score (sample) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, values in summary["scoring"]["by_platform"].items():
        lines.append(f"| {name} | {values['rows']:,} | {values['anomaly_count']:,} | {values['anomaly_rate']:.4%} | {values['score_mean']:.9f} | {values['score_median_sample']:.9f} |")
    lines += ["", "## Anomaly rate by category", "",
              "| Category | Scored | Anomalies | Rate | Mean score | Median score (sample) |",
              "|---|---:|---:|---:|---:|---:|"]
    for name, values in summary["scoring"]["by_category"].items():
        lines.append(f"| {name} | {values['rows']:,} | {values['anomaly_count']:,} | {values['anomaly_rate']:.4%} | {values['score_mean']:.9f} | {values['score_median_sample']:.9f} |")
    comparison = summary["comparison_to_validation"]
    lines += ["", "## Comparison with chronological validation", "",
              f"Validation anomaly rate: {comparison['validation_anomaly_rate']:.4%}; test anomaly rate: {comparison['test_anomaly_rate']:.4%}; change: {comparison['anomaly_rate_delta_percentage_points']:+.4f} percentage points.",
              f"Mean anomaly score changed from {comparison['validation_score_mean']:.9f} on validation to {comparison['test_score_mean']:.9f} on test (delta {comparison['score_mean_delta']:+.9f}).",
              "These comparisons describe distribution shift; they do not tune the threshold or measure classification accuracy.", "",
              "| Platform | Validation rate | Test rate | Change (percentage points) |",
              "|---|---:|---:|---:|"]
    for name, values in comparison["by_platform"].items():
        lines.append(f"| {name} | {values['validation_anomaly_rate']:.4%} | {values['test_anomaly_rate']:.4%} | {values['delta_percentage_points']:+.4f} |")
    lines += ["", "| Category | Validation rate | Test rate | Change (percentage points) |",
              "|---|---:|---:|---:|"]
    for name, values in comparison["by_category"].items():
        lines.append(f"| {name} | {values['validation_anomaly_rate']:.4%} | {values['test_anomaly_rate']:.4%} | {values['delta_percentage_points']:+.4f} |")
    consistency = summary["prediction_consistency"]
    lines += ["", "## Prediction consistency", "",
              f"- Wrapper/direct score mismatches: {consistency['wrapper_vs_direct_score_mismatches']:,}.",
              f"- Wrapper/estimator flag mismatches: {consistency['wrapper_vs_estimator_flag_mismatches']:,}.",
              f"- Wrapper/raw prediction mismatches: {consistency['wrapper_raw_prediction_mismatches']:,}.",
              f"- Flag/positive-wrapper-score mismatches: {consistency['flag_vs_positive_wrapper_score_mismatches']:,}.",
              "- The wrapper score is the negative decision function, so higher scores mean more anomalous.", "",
              "## Classification metrics and limitations", "",
              "**Classification accuracy, precision, recall, and F1 are not measurable from verified ground truth.** The candidate fake-discount label has zero positive examples and undocumented generation logic. The price-spike label is a different dataset anomaly signal, not fake-discount ground truth; it was excluded from scoring and metric calculation.", "",
              "Anomaly detection rate is the fraction of test observations the frozen Isolation Forest flags as anomalous. It is not classification accuracy, fraud prevalence, or a probability that an item is fraudulent. The source dataset is synthetic, so these results do not establish real-world fraud-detection performance.", "",
              f"Artifact checksums matched before and after evaluation: **{summary['artifact_checksums_unchanged']}**. Full machine-readable results: `{args.output_json.resolve()}`.", ""]
    args.output_report.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "report": str(args.output_report.resolve()),
        "summary": str(args.output_json.resolve()),
        "test_rows": emitted,
        "eligible_scored_rows": overall.count,
        "anomaly_count": overall.anomaly_count,
        "anomaly_rate": overall.anomaly_count / overall.count,
        "score_summary": score,
        "prediction_consistency": consistency,
        "runtime_seconds": elapsed,
        "artifact_checksums_unchanged": checksums_before == checksums_after,
        "classification_metrics_available": False,
    }, indent=2))


if __name__ == "__main__":
    main()
