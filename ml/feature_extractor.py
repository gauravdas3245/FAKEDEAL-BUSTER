"""
Feature Extraction and Engineering Module for FakeDeal Buster.

Implements the agreed 4-feature numerical vector for Isolation Forest anomaly detection
and auxiliary heuristic metrics (e.g., discount_inflation_gap) under strict governance rules:
- Strictly backward-looking trailing windows (excludes current observation t).
- Grouped by (product_id, platform).
- Positive, finite denominator enforcement.
- Minimum 14 valid daily historical observations within trailing 30 calendar days.
- Structured fallback for insufficient history or invalid prices (never manufactures features).
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import duckdb
import numpy as np
import pandas as pd

from ml.data_loader import escape_duckdb_path

# Standardized Isolation Forest feature order (DO NOT REORDER)
FEATURE_NAMES: Sequence[str] = (
    "msrp_to_30d_avg",
    "ratio_to_30d_avg",
    "price_volatility_30d",
    "recent_7d_surge",
)

# Auxiliary features reserved for heuristic explanation engine (excluded from Isolation Forest)
AUXILIARY_FEATURE_NAMES: Sequence[str] = (
    "discount_inflation_gap",
    "real_discount_pct",
    "claimed_discount_pct",
    "historical_30d_count",
    "historical_7d_count",
)

MINIMUM_HISTORICAL_DAYS = 14


@dataclass(frozen=True)
class FeatureExtractionResult:
    """Structured container for single-product feature extraction results."""

    status: str  # "success", "insufficient_history", "invalid_input"
    features: Optional[Dict[str, float]] = None
    auxiliary: Optional[Dict[str, float]] = None
    reason: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.status == "success"

    def to_feature_vector(self) -> Optional[np.ndarray]:
        """Return features as a 1D numpy array in exact canonical order."""
        if not self.is_success or self.features is None:
            return None
        return np.array([self.features[col] for col in FEATURE_NAMES], dtype=np.float64)


def parse_date(date_val: Union[str, date, datetime, pd.Timestamp]) -> date:
    """Parse various date representations to standard datetime.date."""
    if isinstance(date_val, datetime):
        return date_val.date()
    if isinstance(date_val, date):
        return date_val
    if isinstance(date_val, pd.Timestamp):
        return date_val.date()
    if isinstance(date_val, str):
        # Support common ISO strings: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS
        cleaned = date_val.strip().split("T")[0].split(" ")[0]
        return datetime.strptime(cleaned, "%Y-%m-%d").date()
    raise TypeError(f"Unsupported date format: {type(date_val)} ({date_val})")


def extract_single_product_features(
    current_price: float,
    original_price: float,
    historical_records: Sequence[Dict[str, Any]],
    current_date: Optional[Union[str, date, datetime]] = None,
    min_history: int = MINIMUM_HISTORICAL_DAYS,
) -> FeatureExtractionResult:
    """
    Extract the 4 agreed ML features and auxiliary metrics for a single product listing.

    Strict Constraints Enforced:
    1. current_price and original_price must be finite and > 0.
    2. historical_records must contain 'price' (> 0) and 'date'/'timestamp'.
    3. Trailing historical windows strictly EXCLUDE the current observation (records on or after current_date).
    4. Duplicate dates in history are detected; conflicting duplicate prices raise an error.
    5. Minimum valid historical observations within trailing 30 calendar days must be >= min_history (14).
    6. Denominators must be positive and non-zero; invalid cases return structured errors.

    Args:
        current_price: Advertised current selling price.
        original_price: Advertised reference/MSRP price.
        historical_records: List of historical dicts, each with 'date'/'timestamp' and 'price'.
        current_date: Reference evaluation date. Defaults to today's date if not provided.
        min_history: Minimum required historical observations in trailing 30 days.

    Returns:
        FeatureExtractionResult dataclass.
    """
    # 1. Validate Core Inputs
    if not isinstance(current_price, (int, float)) or np.isnan(current_price) or np.isinf(current_price) or current_price <= 0:
        return FeatureExtractionResult(
            status="invalid_input",
            reason=f"current_price must be a positive finite number, got: {current_price}",
        )
    if not isinstance(original_price, (int, float)) or np.isnan(original_price) or np.isinf(original_price) or original_price <= 0:
        return FeatureExtractionResult(
            status="invalid_input",
            reason=f"original_price must be a positive finite number, got: {original_price}",
        )
    if original_price < current_price:
        return FeatureExtractionResult(
            status="invalid_input",
            reason=f"original_price ({original_price}) cannot be strictly less than current_price ({current_price}) for a discount analysis",
        )

    # 2. Determine Reference Date
    if current_date is None:
        eval_date = date.today()
    else:
        try:
            eval_date = parse_date(current_date)
        except Exception as e:
            return FeatureExtractionResult(
                status="invalid_input",
                reason=f"Invalid current_date provided: {e}",
            )

    # 3. Clean and Validate Historical Records
    if not historical_records:
        return FeatureExtractionResult(
            status="insufficient_history",
            reason="Historical price records array is empty (0 observations available).",
        )

    valid_history: Dict[date, float] = {}
    for idx, rec in enumerate(historical_records):
        if not isinstance(rec, dict):
            return FeatureExtractionResult(
                status="invalid_input",
                reason=f"Historical record at index {idx} is not a dictionary.",
            )
        date_raw = rec.get("date") or rec.get("timestamp")
        price_raw = rec.get("price")

        if date_raw is None or price_raw is None:
            continue  # Skip incomplete records without manufacturing data

        try:
            rec_date = parse_date(date_raw)
            rec_price = float(price_raw)
        except Exception:
            continue  # Skip unparseable records

        if np.isnan(rec_price) or np.isinf(rec_price) or rec_price <= 0:
            continue  # Skip invalid prices

        # Check for duplicates on the same date
        if rec_date in valid_history:
            if abs(valid_history[rec_date] - rec_price) > 1e-4:
                return FeatureExtractionResult(
                    status="invalid_input",
                    reason=f"Duplicate conflicting historical price records detected on date {rec_date}: {valid_history[rec_date]} vs {rec_price}",
                )
            # Identical duplicate: keep single entry
            continue

        valid_history[rec_date] = rec_price

    # 4. Strictly Backward-Looking Window Filtering (Exclude current_date and future)
    prior_records = [(d, p) for d, p in valid_history.items() if d < eval_date]
    if not prior_records:
        return FeatureExtractionResult(
            status="insufficient_history",
            reason=f"Zero valid historical observations exist strictly prior to evaluation date {eval_date}.",
        )

    # Trailing 30 calendar days window: [eval_date - 30 days, eval_date - 1 day]
    window_30d_start = eval_date - timedelta(days=30)
    records_30d = [p for d, p in prior_records if d >= window_30d_start]

    # Trailing 7 calendar days window: [eval_date - 7 days, eval_date - 1 day]
    window_7d_start = eval_date - timedelta(days=7)
    records_7d = [p for d, p in prior_records if d >= window_7d_start]

    # 5. Enforce Minimum History
    count_30d = len(records_30d)
    if count_30d < min_history:
        return FeatureExtractionResult(
            status="insufficient_history",
            reason=f"Insufficient history: found {count_30d} valid daily records in trailing 30-day window, minimum required is {min_history}.",
        )

    # 6. Compute Feature Mathematics
    hist_30d_avg = float(np.mean(records_30d))
    if hist_30d_avg <= 0 or not np.isfinite(hist_30d_avg):
        return FeatureExtractionResult(
            status="invalid_input",
            reason=f"historical_30d_avg is non-positive or non-finite: {hist_30d_avg}",
        )

    # Sample standard deviation (ddof=1)
    hist_30d_sample_std = float(np.std(records_30d, ddof=1)) if count_30d > 1 else 0.0

    # 7-day maximum (if no records in 7-day window, fall back to 30-day average to yield 0.0 surge)
    if records_7d:
        hist_7d_max = float(np.max(records_7d))
    else:
        hist_7d_max = hist_30d_avg

    # 1. msrp_to_30d_avg
    msrp_to_30d_avg = original_price / hist_30d_avg

    # 2. ratio_to_30d_avg
    ratio_to_30d_avg = current_price / hist_30d_avg

    # 3. price_volatility_30d
    price_volatility_30d = hist_30d_sample_std / hist_30d_avg

    # 4. recent_7d_surge
    recent_7d_surge = max(0.0, (hist_7d_max - hist_30d_avg) / hist_30d_avg)

    # Verify all 4 features are finite
    feature_dict = {
        "msrp_to_30d_avg": float(msrp_to_30d_avg),
        "ratio_to_30d_avg": float(ratio_to_30d_avg),
        "price_volatility_30d": float(price_volatility_30d),
        "recent_7d_surge": float(recent_7d_surge),
    }
    for k, v in feature_dict.items():
        if not np.isfinite(v):
            return FeatureExtractionResult(
                status="invalid_input",
                reason=f"Calculated feature '{k}' is non-finite: {v}",
            )

    # Auxiliary features (e.g. for heuristic explanation engine)
    real_discount_pct = ((hist_30d_avg - current_price) / hist_30d_avg) * 100.0
    claimed_discount_pct = ((original_price - current_price) / original_price) * 100.0
    discount_inflation_gap = claimed_discount_pct - real_discount_pct

    auxiliary_dict = {
        "discount_inflation_gap": float(discount_inflation_gap),
        "real_discount_pct": float(real_discount_pct),
        "claimed_discount_pct": float(claimed_discount_pct),
        "historical_30d_count": float(count_30d),
        "historical_7d_count": float(len(records_7d)),
    }

    return FeatureExtractionResult(
        status="success",
        features=feature_dict,
        auxiliary=auxiliary_dict,
    )


def build_duckdb_feature_query(
    source_table_or_file: str,
    min_history: int = MINIMUM_HISTORICAL_DAYS,
    limit: Optional[int] = None,
    output_start: Optional[Union[str, date, datetime, pd.Timestamp]] = None,
    include_category: bool = False,
    order_results: bool = True,
) -> str:
    """
    Construct memory-safe DuckDB SQL to extract the 4 features strictly excluding current observation.

    Uses calendar RANGE windows partitioned by (product_id, platform) and ordered by timestamp.
    Rows with fewer than min_history prior observations are explicitly filtered out.
    Target columns (fake_discount_flag, price_spike_flag, target_price_*) are strictly excluded from output.

    Args:
        source_table_or_file: Escaped table name or 'read_csv_auto(...)' literal.
        min_history: Minimum required prior observations in 30d window (default 14).
        limit: Optional maximum rows to return.

    Returns:
        DuckDB SQL query string.
    """
    limit_clause = f"LIMIT {limit}" if limit is not None else ""
    if output_start is None:
        start_clause = ""
    else:
        start_value = str(output_start).replace("'", "''")
        start_clause = f"AND timestamp >= TIMESTAMP '{start_value}'"
    order_clause = "ORDER BY timestamp, product_id, platform" if order_results else ""
    return f"""
    WITH windowed AS (
        SELECT
            product_id,
            platform,
            timestamp,
            {"category," if include_category else ""}
            price,
            original_price,
            discount_pct,
            -- Calendar windows strictly exclude the current timestamp. RANGE
            -- keeps the window at 30/7 days even when observations are missing.
            COUNT(price) OVER w30 AS hist_30d_count,
            AVG(price) OVER w30 AS hist_30d_avg,
            STDDEV_SAMP(price) OVER w30 AS hist_30d_std,
            -- Strictly prior 7 calendar days
            COUNT(price) OVER w7 AS hist_7d_count,
            MAX(price) OVER w7 AS hist_7d_max
        FROM {source_table_or_file}
        WINDOW
            w30 AS (
                PARTITION BY product_id, platform
                ORDER BY timestamp
                RANGE BETWEEN INTERVAL 30 DAYS PRECEDING AND INTERVAL 1 MICROSECOND PRECEDING
            ),
            w7 AS (
                PARTITION BY product_id, platform
                ORDER BY timestamp
                RANGE BETWEEN INTERVAL 7 DAYS PRECEDING AND INTERVAL 1 MICROSECOND PRECEDING
            )
    )
    SELECT
        product_id,
        platform,
        timestamp,
        {"category," if include_category else ""}
        price,
        original_price,
        -- The 4 agreed Isolation Forest numerical features
        (original_price / hist_30d_avg) AS msrp_to_30d_avg,
        (price / hist_30d_avg) AS ratio_to_30d_avg,
        (COALESCE(hist_30d_std, 0.0) / hist_30d_avg) AS price_volatility_30d,
        GREATEST(0.0, (COALESCE(hist_7d_max, hist_30d_avg) - hist_30d_avg) / hist_30d_avg) AS recent_7d_surge,
        -- Auxiliary feature for explanation engine
        (((original_price - price) / original_price) * 100.0)
          - (((hist_30d_avg - price) / hist_30d_avg) * 100.0) AS discount_inflation_gap,
        hist_30d_count,
        hist_7d_count
    FROM windowed
    WHERE hist_30d_count >= {min_history}
      AND hist_30d_avg > 0
      AND price > 0
      AND original_price > 0
      AND ISFINITE(hist_30d_avg)
      AND ISFINITE(price)
      AND ISFINITE(original_price)
      {start_clause}
    {order_clause}
    {limit_clause}
    """


def extract_features_from_csv(
    csv_path: Union[str, Path],
    min_history: int = MINIMUM_HISTORICAL_DAYS,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """
    Extract features from a CSV split using DuckDB streaming execution without loading full CSV into RAM.

    Args:
        csv_path: Path to dataset CSV file.
        min_history: Minimum required prior observations (default 14).
        limit: Optional maximum rows.

    Returns:
        Pandas DataFrame of extracted features.
    """
    escaped_path = escape_duckdb_path(csv_path)
    source_expr = f"read_csv_auto('{escaped_path}')"
    query = build_duckdb_feature_query(source_expr, min_history=min_history, limit=limit)

    con = duckdb.connect()
    try:
        return con.execute(query).df()
    finally:
        con.close()
