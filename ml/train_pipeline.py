"""Bounded-memory training and validation for the pricing anomaly pipeline.

Isolation Forest is not an incremental estimator, so this module uses a seeded
reservoir sample of training features. Feature rows are produced by DuckDB and
read in batches; validation is scored batch-by-batch and never used for fitting.
"""

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterator, Optional, Sequence, Union

import duckdb
import numpy as np
import pandas as pd
import time

from ml.feature_extractor import FEATURE_NAMES, build_duckdb_feature_query
from ml.isolation_forest import IsolationForestDetector
from ml.preprocessor import FeaturePreprocessor


@dataclass
class TrainingResult:
    preprocessor: FeaturePreprocessor
    detector: IsolationForestDetector
    training_rows_seen: int
    training_rows_used: int
    source_rows_scanned: int
    eligible_feature_rows: int
    excluded_feature_rows: int
    excluded_feature_rows_by_reason: dict
    training_min_timestamp: Optional[str]
    training_max_timestamp: Optional[str]
    validation_rows_scored: int
    validation_min_timestamp: Optional[str]
    validation_max_timestamp: Optional[str]
    validation_source_rows: int
    validation_eligible_feature_rows: int
    validation_excluded_feature_rows: Optional[int]
    validation_excluded_feature_rows_by_reason: Optional[dict]
    validation_anomaly_count: int
    validation_anomaly_rate: Optional[float]
    validation_score_summary: Optional[dict]
    validation_by_platform: dict
    validation_by_category: dict
    invalid_validation_feature_rows: int
    training_elapsed_seconds: float
    validation_elapsed_seconds: float
    verification_features: dict


def iter_feature_batches(
    csv_path: Union[str, Path], batch_size: int = 50_000,
    min_history: int = 14, limit: Optional[int] = None,
    duckdb_memory_limit: str = "1GB",
    history_csv_paths: Optional[Sequence[Union[str, Path]]] = None,
    output_start: Optional[Union[str, date, datetime, pd.Timestamp]] = None,
    source_row_limit: Optional[int] = None,
    product_ids: Optional[Sequence[str]] = None,
    include_category: Optional[bool] = None,
    preserve_result_order: bool = True,
) -> Iterator[pd.DataFrame]:
    """Yield engineered features in bounded batches from a chronological CSV.

    DuckDB's working memory is capped as well; larger window/sort intermediates
    may spill to DuckDB's temporary storage instead of growing without a limit.
    """
    if not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        raise ValueError("limit must be a positive integer or None")
    if source_row_limit is not None and (
        not isinstance(source_row_limit, int) or source_row_limit <= 0
    ):
        raise ValueError("source_row_limit must be a positive integer or None")
    if product_ids is not None and (
        not product_ids or any(not isinstance(product_id, str) for product_id in product_ids)
    ):
        raise ValueError("product_ids must be a non-empty sequence of strings")
    source_paths = list(history_csv_paths) if history_csv_paths is not None else [csv_path]
    if not source_paths:
        raise ValueError("At least one source path is required")
    def csv_source(csv_path: Union[str, Path]) -> str:
        quoted_path = "'" + Path(csv_path).resolve().as_posix().replace("'", "''") + "'"
        one_source = f"read_csv_auto({quoted_path})"
        if product_ids is not None:
            product_list = ", ".join(
                "'" + product_id.replace("'", "''") + "'" for product_id in product_ids
            )
            one_source = f"(SELECT * FROM {one_source} WHERE product_id IN ({product_list}))"
        return one_source

    sources = [csv_source(path) for path in source_paths]
    if len(sources) == 1:
        source = sources[0]
    else:
        source = "(" + " UNION ALL ".join(f"SELECT * FROM {item}" for item in sources) + ")"
    if source_row_limit is not None:
        source = f"(SELECT * FROM {source} LIMIT {source_row_limit})"
    con = duckdb.connect()
    try:
        con.execute("SET memory_limit = ?", [duckdb_memory_limit])
        con.execute("SET threads = 1")
        available_columns = {
            row[0] for row in con.execute(f"DESCRIBE SELECT * FROM {source} LIMIT 0").fetchall()
        }
        use_category = "category" in available_columns if include_category is None else include_category
        if use_category and "category" not in available_columns:
            raise ValueError("include_category=True requires a category column")
        query = build_duckdb_feature_query(
            source, min_history=min_history, limit=limit, output_start=output_start,
            include_category=use_category, order_results=preserve_result_order,
        )
        result = con.execute(query)
        columns = [description[0] for description in result.description]
        while True:
            rows = result.fetchmany(batch_size)
            if not rows:
                break
            frame = pd.DataFrame.from_records(rows, columns=columns)
            yield frame
    finally:
        con.close()


def _reservoir_sample(
    batches: Iterator[pd.DataFrame], max_rows: int, random_state: int,
) -> tuple[pd.DataFrame, int]:
    """Return a uniform, deterministic reservoir and the total rows observed."""
    if max_rows < 2:
        raise ValueError("max_rows must be at least 2")
    rng = np.random.default_rng(random_state)
    reservoir = np.empty((max_rows, len(FEATURE_NAMES)), dtype=np.float64)
    seen = 0
    for batch in batches:
        values = batch.loc[:, list(FEATURE_NAMES)].to_numpy(dtype=np.float64)
        values = values[np.isfinite(values).all(axis=1)]
        start = seen
        count = len(values)
        fill = min(max(0, max_rows - start), count)
        if fill:
            reservoir[start:start + fill] = values[:fill]
        remaining = count - fill
        if remaining:
            # Vectorized Algorithm R draws one uniform slot per arriving row.
            # Keep the last write for repeated slots to preserve sequential semantics.
            first_seen_index = start + fill
            upper = np.arange(first_seen_index + 1, first_seen_index + remaining + 1, dtype=np.int64)
            slots = rng.integers(0, upper)
            accepted = np.flatnonzero(slots < max_rows)
            if accepted.size:
                accepted_slots = slots[accepted]
                reverse_unique = np.unique(accepted_slots[::-1], return_index=True)[1]
                last_positions = accepted.size - 1 - reverse_unique
                chosen = accepted[last_positions]
                reservoir[slots[chosen]] = values[fill + chosen]
        seen += count
    return pd.DataFrame(reservoir[:min(seen, max_rows)], columns=FEATURE_NAMES), seen


def _source_census(
    csv_path: Union[str, Path], memory_limit: str = "1GB",
    source_row_limit: Optional[int] = None,
) -> dict:
    """Count source rows and mutually exclusive unusable-input reasons in DuckDB."""
    escaped = Path(csv_path).resolve().as_posix().replace("'", "''")
    source = f"read_csv_auto('{escaped}')"
    if source_row_limit is not None:
        source = f"(SELECT * FROM {source} LIMIT {source_row_limit})"
    con = duckdb.connect()
    try:
        con.execute("SET memory_limit = ?", [memory_limit])
        con.execute("SET threads = 1")
        row = con.execute(f"""
            SELECT COUNT(*) AS source_rows,
                COUNT(*) FILTER (WHERE product_id IS NULL OR platform IS NULL OR timestamp IS NULL) AS missing_key_or_timestamp,
                COUNT(*) FILTER (
                    WHERE product_id IS NOT NULL AND platform IS NOT NULL AND timestamp IS NOT NULL
                      AND (price IS NULL OR original_price IS NULL)
                ) AS missing_price_input,
                COUNT(*) FILTER (
                    WHERE product_id IS NOT NULL AND platform IS NOT NULL AND timestamp IS NOT NULL
                      AND price IS NOT NULL AND original_price IS NOT NULL
                      AND (NOT ISFINITE(TRY_CAST(price AS DOUBLE)) OR NOT ISFINITE(TRY_CAST(original_price AS DOUBLE)))
                ) AS non_finite_price_input,
                COUNT(*) FILTER (
                    WHERE product_id IS NOT NULL AND platform IS NOT NULL AND timestamp IS NOT NULL
                      AND price IS NOT NULL AND original_price IS NOT NULL
                      AND ISFINITE(TRY_CAST(price AS DOUBLE)) AND ISFINITE(TRY_CAST(original_price AS DOUBLE))
                      AND (TRY_CAST(price AS DOUBLE) <= 0 OR TRY_CAST(original_price AS DOUBLE) <= 0)
                ) AS non_positive_price_input
            FROM {source}
        """).fetchone()
        reasons = {
            "missing_product_platform_or_timestamp": row[1],
            "missing_price_or_original_price": row[2],
            "non_finite_price_or_original_price": row[3],
            "non_positive_price_or_original_price": row[4],
        }
        return {"source_rows": row[0], "invalid_input_rows": sum(reasons.values()), "invalid_input_reasons": reasons}
    finally:
        con.close()


class _ScoreAccumulator:
    """Exact moments/min/max plus a deterministic bounded sample for quantiles."""

    def __init__(self, max_sample: int = 100_000, random_state: int = 42):
        self.count = 0
        self.anomaly_count = 0
        self.total = 0.0
        self.minimum = float("inf")
        self.maximum = float("-inf")
        self.sample = np.empty(max_sample, dtype=np.float64)
        self.rng = np.random.default_rng(random_state)

    def update(self, scores: np.ndarray, anomalies: np.ndarray) -> None:
        scores = np.atleast_1d(np.asarray(scores, dtype=np.float64))
        anomalies = np.atleast_1d(np.asarray(anomalies, dtype=bool))
        if not len(scores):
            return
        self.anomaly_count += int(anomalies.sum())
        self.total += float(scores.sum())
        self.minimum = min(self.minimum, float(scores.min()))
        self.maximum = max(self.maximum, float(scores.max()))

        start = self.count
        fill = min(max(0, len(self.sample) - start), len(scores))
        if fill:
            self.sample[start:start + fill] = scores[:fill]
        remaining = len(scores) - fill
        if remaining:
            first_index = start + fill
            upper = np.arange(first_index + 1, first_index + remaining + 1, dtype=np.int64)
            slots = self.rng.integers(0, upper)
            accepted = np.flatnonzero(slots < len(self.sample))
            if accepted.size:
                accepted_slots = slots[accepted]
                reverse_unique = np.unique(accepted_slots[::-1], return_index=True)[1]
                last_positions = accepted.size - 1 - reverse_unique
                chosen = accepted[last_positions]
                self.sample[slots[chosen]] = scores[fill + chosen]
        self.count += len(scores)

    def summary(self) -> Optional[dict]:
        if not self.count:
            return None
        sample = self.sample[:min(self.count, len(self.sample))]
        quantiles = np.quantile(sample, [0.05, 0.25, 0.5, 0.75, 0.95])
        return {
            "rows": self.count,
            "anomaly_count": self.anomaly_count,
            "anomaly_rate": self.anomaly_count / self.count,
            "score_min": self.minimum,
            "score_max": self.maximum,
            "score_mean": self.total / self.count,
            "score_q05_sample": float(quantiles[0]),
            "score_q25_sample": float(quantiles[1]),
            "score_median_sample": float(quantiles[2]),
            "score_q75_sample": float(quantiles[3]),
            "score_q95_sample": float(quantiles[4]),
            "quantile_sample_size": len(sample),
        }


def train_from_splits(
    train_csv: Union[str, Path], validation_csv: Optional[Union[str, Path]] = None,
    *, batch_size: int = 50_000, max_training_rows: int = 100_000,
    contamination: float = 0.01, n_estimators: int = 100,
    random_state: int = 42, min_history: int = 14,
    train_source_row_limit: Optional[int] = None,
    duckdb_memory_limit: str = "1GB",
    validation_quantile_sample_size: int = 100_000,
) -> TrainingResult:
    """Fit on a reservoir from train and score validation in bounded batches."""
    training_started = time.perf_counter()
    train_min = train_max = val_min = val_max = None
    if validation_csv is not None:
        con = duckdb.connect()
        try:
            con.execute("SET memory_limit = '1GB'")
            con.execute("SET threads = 1")
            def timestamp_bounds(path: Union[str, Path]):
                escaped = Path(path).resolve().as_posix().replace("'", "''")
                return con.execute(
                    f"SELECT MIN(timestamp), MAX(timestamp) FROM read_csv_auto('{escaped}')"
                ).fetchone()

            train_min, train_max = timestamp_bounds(train_csv)
            val_min, val_max = timestamp_bounds(validation_csv)
        finally:
            con.close()
        if None in (train_min, train_max, val_min, val_max):
            raise ValueError("Train and validation files must contain timestamp observations")
        if train_max >= val_min:
            raise ValueError(
                f"Validation must be strictly later than training (train max {train_max}, validation min {val_min})"
            )

    train_census = _source_census(train_csv, duckdb_memory_limit, train_source_row_limit)
    sample, rows_seen = _reservoir_sample(
        iter_feature_batches(
            train_csv, batch_size, min_history,
            duckdb_memory_limit=duckdb_memory_limit,
            source_row_limit=train_source_row_limit,
            preserve_result_order=False,
        ),
        max_training_rows, random_state,
    )
    if len(sample) < 2:
        raise ValueError(f"Need at least 2 valid training feature rows; found {len(sample)}")

    preprocessor = FeaturePreprocessor()
    verification_features = {
        name: float(sample.iloc[0][name]) for name in FEATURE_NAMES
    }
    scaled = preprocessor.fit_transform(sample)
    detector = IsolationForestDetector(
        contamination=contamination, n_estimators=n_estimators,
        random_state=random_state,
    ).fit(scaled)
    training_elapsed = time.perf_counter() - training_started

    excluded = train_census["source_rows"] - rows_seen
    insufficient_history = excluded - train_census["invalid_input_rows"]
    if insufficient_history < 0:
        raise RuntimeError(
            "Eligible feature count exceeds source rows after invalid-input exclusions; "
            "check feature eligibility accounting."
        )
    exclusion_reasons = {
        **train_census["invalid_input_reasons"],
        "insufficient_prior_history_or_invalid_derived_baseline": insufficient_history,
    }

    validation_elapsed = 0.0
    validation_census = None
    validation_acc = _ScoreAccumulator(validation_quantile_sample_size, random_state + 11)
    platform_acc = {}
    category_acc = {}
    invalid_validation_features = 0
    if validation_csv is not None:
        validation_started = time.perf_counter()
        validation_census = _source_census(validation_csv, duckdb_memory_limit)
        for batch in iter_feature_batches(
            validation_csv, batch_size, min_history,
            duckdb_memory_limit=duckdb_memory_limit,
            history_csv_paths=[train_csv, validation_csv], output_start=val_min,
            preserve_result_order=False,
        ):
            values = batch.loc[:, list(FEATURE_NAMES)].to_numpy(dtype=np.float64)
            valid = np.isfinite(values).all(axis=1)
            invalid_validation_features += int((~valid).sum())
            if not valid.any():
                continue
            predictions = detector.predict_anomaly(preprocessor.transform(values[valid]))
            scores = np.atleast_1d(np.asarray(predictions["anomaly_score"], dtype=np.float64))
            labels = np.atleast_1d(np.asarray(predictions["is_anomaly"], dtype=bool))
            validation_acc.update(scores, labels)

            valid_positions = np.flatnonzero(valid)
            for group_column, accumulators in (("platform", platform_acc), ("category", category_acc)):
                if group_column not in batch.columns:
                    continue
                group_values = batch.iloc[valid_positions][group_column].fillna("<NULL>").astype(str).to_numpy()
                for group in np.unique(group_values):
                    selected = group_values == group
                    if group not in accumulators:
                        seed_offset = sum((i + 1) * ord(char) for i, char in enumerate(group))
                        accumulators[group] = _ScoreAccumulator(
                            max_sample=min(validation_quantile_sample_size, 25_000),
                            random_state=random_state + seed_offset,
                        )
                    accumulators[group].update(scores[selected], labels[selected])
        validation_elapsed = time.perf_counter() - validation_started

    validation_rows_scored = validation_acc.count
    validation_anomaly_count = validation_acc.anomaly_count
    validation_rate = (
        validation_anomaly_count / validation_rows_scored if validation_rows_scored else None
    )
    validation_score_summary = validation_acc.summary()
    validation_excluded = None
    validation_exclusion_reasons = None
    if validation_census is not None:
        validation_excluded = validation_census["source_rows"] - validation_rows_scored
        validation_history_excluded = (
            validation_excluded
            - validation_census["invalid_input_rows"]
            - invalid_validation_features
        )
        validation_exclusion_reasons = {
            **validation_census["invalid_input_reasons"],
            "insufficient_prior_history_or_invalid_derived_baseline": max(0, validation_history_excluded),
            "non_finite_engineered_features": invalid_validation_features,
        }

    by_platform = {key: value.summary() for key, value in sorted(platform_acc.items())}
    by_category = {key: value.summary() for key, value in sorted(category_acc.items())}

    return TrainingResult(
        preprocessor=preprocessor, detector=detector,
        training_rows_seen=rows_seen, training_rows_used=len(sample),
        source_rows_scanned=train_census["source_rows"],
        eligible_feature_rows=rows_seen,
        excluded_feature_rows=excluded,
        excluded_feature_rows_by_reason=exclusion_reasons,
        training_min_timestamp=str(train_min) if train_min is not None else None,
        training_max_timestamp=str(train_max) if train_max is not None else None,
        validation_rows_scored=validation_rows_scored,
        validation_min_timestamp=str(val_min) if val_min is not None else None,
        validation_max_timestamp=str(val_max) if val_max is not None else None,
        validation_source_rows=validation_census["source_rows"] if validation_census else 0,
        validation_eligible_feature_rows=validation_rows_scored,
        validation_excluded_feature_rows=validation_excluded,
        validation_excluded_feature_rows_by_reason=validation_exclusion_reasons,
        validation_anomaly_count=validation_anomaly_count,
        validation_anomaly_rate=validation_rate,
        validation_score_summary=validation_score_summary,
        validation_by_platform=by_platform,
        validation_by_category=by_category,
        invalid_validation_feature_rows=invalid_validation_features,
        training_elapsed_seconds=training_elapsed,
        validation_elapsed_seconds=validation_elapsed,
        verification_features=verification_features,
    )


def save_artifacts(result: TrainingResult, output_dir: Union[str, Path]) -> None:
    """Save fitted model and human-readable preprocessor metadata."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    result.detector.save(output / "isolation_forest.joblib")
    result.preprocessor.save_json(output / "preprocessor.json")
