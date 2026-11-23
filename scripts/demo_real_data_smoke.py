"""Small, bounded real-data ML smoke test; never uses validation/test for fitting.

Example:
  python scripts/demo_real_data_smoke.py --data-dir "C:\\end sem project\\archive (5)"

The script reads at most --source-row-limit rows from the training CSV, builds
calendar-window features in DuckDB, reservoir-samples at most --max-training-rows,
and scores one observed training row as a wiring smoke test (not evaluation).
"""

import argparse
import json
import os
from pathlib import Path
import sys

import duckdb
import numpy as np

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from ml.data_loader import get_split_schema
from ml.feature_extractor import FEATURE_NAMES
from ml.isolation_forest import IsolationForestDetector
from ml.preprocessor import FeaturePreprocessor
from ml.train_pipeline import iter_feature_batches, train_from_splits


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir", default=os.getenv("FAKEDEAL_RAW_DATA_DIR"),
        help="Dataset root containing data/splits (or set FAKEDEAL_RAW_DATA_DIR)",
    )
    parser.add_argument("--source-row-limit", type=int, default=100_000)
    parser.add_argument("--max-training-rows", type=int, default=5_000)
    parser.add_argument("--batch-size", type=int, default=5_000)
    parser.add_argument("--n-estimators", type=int, default=50)
    parser.add_argument("--validation-product-count", type=int, default=10)
    args = parser.parse_args()
    if not args.data_dir:
        parser.error("Provide --data-dir or set FAKEDEAL_RAW_DATA_DIR")

    split_dir = Path(args.data_dir).resolve() / "data" / "splits"
    train_path = split_dir / "ecommerce_train.csv"
    val_path = split_dir / "ecommerce_val.csv"
    test_path = split_dir / "ecommerce_test.csv"
    missing = [str(path) for path in (train_path, val_path, test_path) if not path.is_file()]
    if missing:
        parser.error(f"Expected all three split files; missing: {missing}")

    schema, _ = get_split_schema(train_path)
    required = {"product_id", "platform", "timestamp", "price", "original_price"}
    if absent := required.difference(schema):
        parser.error(f"Training schema is missing required columns: {sorted(absent)}")

    connection = duckdb.connect()
    connection.execute("SET memory_limit = '1GB'")
    try:
        def bounds(path: Path):
            escaped = path.resolve().as_posix().replace("'", "''")
            return connection.execute(
                f"SELECT MIN(timestamp), MAX(timestamp) FROM read_csv_auto('{escaped}')"
            ).fetchone()

        _, train_end = bounds(train_path)
        validation_start, _ = bounds(val_path)
    finally:
        connection.close()
    if train_end >= validation_start:
        parser.error("Training data does not end before the validation period starts")

    first_training_batch = next(iter_feature_batches(
        train_path, batch_size=args.batch_size,
        source_row_limit=args.source_row_limit,
    ))
    validation_products = (
        first_training_batch["product_id"].drop_duplicates()
        .head(args.validation_product_count).astype(str).tolist()
    )

    result = train_from_splits(
        train_path,
        batch_size=args.batch_size,
        max_training_rows=args.max_training_rows,
        n_estimators=args.n_estimators,
        random_state=20261117,
        train_source_row_limit=args.source_row_limit,
    )
    first_batch = next(iter_feature_batches(
        train_path,
        batch_size=args.batch_size,
        source_row_limit=args.source_row_limit,
    ))
    observed = first_batch.iloc[0]
    features = {name: float(observed[name]) for name in FEATURE_NAMES}
    preprocessor = result.preprocessor
    detector = result.detector
    scaled = preprocessor.transform_single(features)
    score = detector.predict_anomaly(scaled)

    validation_scores = []
    validation_anomalies = 0
    validation_rows = 0
    for batch in iter_feature_batches(
        val_path,
        batch_size=args.batch_size,
        history_csv_paths=[train_path, val_path],
        output_start=validation_start,
        product_ids=validation_products,
        limit=20_000,
    ):
        values = batch.loc[:, list(FEATURE_NAMES)].to_numpy(dtype=float)
        valid = np.isfinite(values).all(axis=1)
        if not valid.any():
            continue
        predictions = detector.predict_anomaly(preprocessor.transform(values[valid]))
        batch_scores = predictions["anomaly_score"]
        validation_rows += len(batch_scores)
        validation_anomalies += int(np.count_nonzero(predictions["is_anomaly"]))
        validation_scores.extend(batch_scores.tolist())

    validation_summary = None
    if validation_scores:
        validation_summary = {
            "rows_scored": validation_rows,
            "anomaly_count": validation_anomalies,
            "anomaly_rate": validation_anomalies / validation_rows,
            "score_min": float(np.min(validation_scores)),
            "score_mean": float(np.mean(validation_scores)),
            "score_q25": float(np.quantile(validation_scores, 0.25)),
            "score_median": float(np.median(validation_scores)),
            "score_q75": float(np.quantile(validation_scores, 0.75)),
            "score_max": float(np.max(validation_scores)),
        }

    output = {
        "data_status": "REAL PROJECT FILES — BOUNDED TRAINING + VALIDATION SMOKE",
        "training_csv": str(train_path),
        "training_schema_columns": len(schema),
        "source_row_limit": args.source_row_limit,
        "feature_rows_seen": result.training_rows_seen,
        "reservoir_rows_used": result.training_rows_used,
        "train_boundary": str(train_end),
        "validation_boundary": str(validation_start),
        "validation_product_ids": validation_products,
        "validation_rows_capped_at": 20_000,
        "validation_smoke_summary": validation_summary,
        "scored_observation": {
            "timestamp": str(observed["timestamp"]),
            "product_id": str(observed["product_id"]),
            "platform": str(observed["platform"]),
            "current_price": float(observed["price"]),
            "original_price": float(observed["original_price"]),
            "historical_30d_mean": float(observed["original_price"]) / features["msrp_to_30d_avg"],
            "historical_30d_sample_std": (
                features["price_volatility_30d"]
                * float(observed["original_price"])
                / features["msrp_to_30d_avg"]
            ),
            "historical_7d_max": (
                (1.0 + features["recent_7d_surge"])
                * float(observed["original_price"])
                / features["msrp_to_30d_avg"]
            ),
            "features_in_model_order": features,
            "scaled_features_in_model_order": scaled.tolist(),
            "isolation_forest_result": score,
        },
        "validation_used_for_fit": False,
        "test_used_for_fit_or_scoring": False,
        "interpretation": "Smoke-test anomaly indicator only; not fraud probability or model performance.",
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
