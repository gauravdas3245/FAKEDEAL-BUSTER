"""
Data Ingestion and Loading Module for FakeDeal Buster.

Provides memory-safe inspection, schema extraction, sequential previewing,
and batched streaming from raw dataset CSV files using DuckDB.
"""

import os
import re
import time
from pathlib import Path
from typing import Generator, Optional, Union

import duckdb
import pandas as pd

# Mapping of primary temporal splits to their expected relative paths
SPLIT_FILENAMES = {
    "train": "data/splits/ecommerce_train.csv",
    "val": "data/splits/ecommerce_val.csv",
    "test": "data/splits/ecommerce_test.csv",
}

# Derived subsets (for reference, excluded from primary temporal splits)
SUBSET_FILENAMES = {
    "anomalies": "data/subsets/ecommerce_anomalies.csv",
    "forecast": "data/subsets/ecommerce_forecast.csv",
}

# Identifier pattern for safe SQL column names
SAFE_IDENTIFIER_REGEX = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def escape_duckdb_path(file_path: Union[str, Path]) -> str:
    """
    Normalize file path to POSIX style and escape single quotes for DuckDB SQL string literals.

    Args:
        file_path: Path to target file.

    Returns:
        Escaped POSIX path string safe for insertion into SQL literals.
    """
    posix_path = Path(file_path).resolve().as_posix()
    return posix_path.replace("'", "''")


def get_dataset_root(override_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Resolve the root directory of the raw dataset.

    Priority:
    1. Explicit override_path argument.
    2. FAKEDEAL_RAW_DATA_DIR environment variable.

    Raises:
        FileNotFoundError: If neither is configured or directory does not exist.
    """
    if override_path is not None:
        root = Path(override_path).resolve()
    elif os.getenv("FAKEDEAL_RAW_DATA_DIR"):
        root = Path(os.environ["FAKEDEAL_RAW_DATA_DIR"]).resolve()
    else:
        raise FileNotFoundError(
            "Dataset root directory is not configured. Please supply an explicit "
            "'override_path' argument or set the 'FAKEDEAL_RAW_DATA_DIR' environment variable."
        )

    if not root.is_dir():
        raise FileNotFoundError(f"Configured dataset root directory does not exist: {root}")

    return root


def get_split_path(split_name: str, root_dir: Optional[Union[str, Path]] = None) -> Path:
    """
    Resolve and validate the filesystem path for a primary temporal split.

    Args:
        split_name: Name of the split ('train', 'val', or 'test').
        root_dir: Optional override for the dataset root directory.

    Returns:
        Path to the validated split CSV file.

    Raises:
        ValueError: If split_name is not recognized.
        FileNotFoundError: If the split file does not exist.
    """
    if split_name not in SPLIT_FILENAMES:
        valid_splits = ", ".join(sorted(SPLIT_FILENAMES.keys()))
        raise ValueError(
            f"Invalid split name '{split_name}'. Expected one of primary temporal splits: {valid_splits}"
        )

    root = get_dataset_root(root_dir)
    target_path = root / SPLIT_FILENAMES[split_name]

    if not target_path.is_file():
        raise FileNotFoundError(f"Split file '{split_name}' not found at: {target_path}")

    return target_path


def validate_columns(
    requested_columns: Optional[list[str]],
    available_columns: list[str],
) -> list[str]:
    """
    Validate that requested columns exist in the available schema and use safe identifiers.

    Args:
        requested_columns: Columns requested by caller, or None for all available.
        available_columns: Complete list of valid column names from the file schema.

    Returns:
        Validated list of column names.

    Raises:
        ValueError: If requested_columns is empty or contains invalid/unrecognized names.
    """
    if requested_columns is None:
        return list(available_columns)

    if not requested_columns:
        raise ValueError("requested_columns cannot be empty. Pass None to select all columns.")

    available_set = set(available_columns)
    invalid_cols = []
    unrecognized_cols = []

    for col in requested_columns:
        if not isinstance(col, str) or not SAFE_IDENTIFIER_REGEX.match(col):
            invalid_cols.append(str(col))
        elif col not in available_set:
            unrecognized_cols.append(col)

    if invalid_cols:
        raise ValueError(f"Requested column identifiers contain illegal characters: {invalid_cols}")
    if unrecognized_cols:
        raise ValueError(f"Requested columns not present in dataset schema: {unrecognized_cols}")

    return requested_columns


def get_split_schema(file_path: Union[str, Path]) -> tuple[dict[str, str], float]:
    """
    Inspect the CSV schema using DuckDB.

    Note: DuckDB scans initial chunks of the CSV to infer data types according to its
    type inference algorithm. Execution time is measured and returned.

    Args:
        file_path: Path to CSV file.

    Returns:
        tuple of (schema_dict {column_name: duckdb_type}, elapsed_seconds).
    """
    path_str = escape_duckdb_path(file_path)
    start_time = time.perf_counter()
    con = duckdb.connect()
    try:
        query = f"DESCRIBE SELECT * FROM read_csv_auto('{path_str}') LIMIT 0"
        rows = con.execute(query).fetchall()
        schema = {r[0]: r[1] for r in rows}
        elapsed = time.perf_counter() - start_time
        return schema, elapsed
    finally:
        con.close()


def load_preview(
    file_path: Union[str, Path],
    columns: Optional[list[str]] = None,
    limit: int = 100,
    offset: int = 0,
) -> pd.DataFrame:
    """
    Load a sequential slice (preview) of rows from a CSV file.

    IMPORTANT: This returns a deterministic sequential slice (LIMIT N OFFSET M)
    based on the physical row order in the CSV file. It is a preview and inspection
    utility, NOT a statistically representative or stratified sample.

    Args:
        file_path: Path to target CSV file.
        columns: Optional list of column names to project.
        limit: Number of rows to return (must be an integer > 0).
        offset: Number of initial rows to skip (must be an integer >= 0).

    Returns:
        Pandas DataFrame containing the requested row slice.

    Raises:
        ValueError: If limit <= 0, offset < 0, or column validation fails.
    """
    if not isinstance(limit, int) or limit <= 0:
        raise ValueError(f"limit must be a positive integer, got: {limit}")
    if not isinstance(offset, int) or offset < 0:
        raise ValueError(f"offset must be a non-negative integer, got: {offset}")

    schema, _ = get_split_schema(file_path)
    selected_cols = validate_columns(columns, list(schema.keys()))
    col_clause = ", ".join(f'"{c}"' for c in selected_cols)
    path_str = escape_duckdb_path(file_path)

    con = duckdb.connect()
    try:
        # parallel=false enforces single-threaded deterministic physical line ordering
        query = (
            f"SELECT {col_clause} "
            f"FROM read_csv_auto('{path_str}', parallel=false) "
            f"LIMIT {limit} OFFSET {offset}"
        )
        return con.execute(query).df()
    finally:
        con.close()


def stream_batches(
    file_path: Union[str, Path],
    columns: Optional[list[str]] = None,
    batch_size: int = 50000,
) -> Generator[pd.DataFrame, None, None]:
    """
    Stream a CSV file in bounded chunks as Pandas DataFrames without loading
    the full dataset into memory.

    Resources (DuckDB connection and cursor) are cleanly closed upon completion
    or if the consumer terminates iteration early (via try...finally).

    Args:
        file_path: Path to target CSV file.
        columns: Optional list of column names to project.
        batch_size: Number of rows per yielded batch (must be an integer > 0).

    Yields:
        pd.DataFrame of size up to batch_size.

    Raises:
        ValueError: If batch_size <= 0 or column validation fails.
    """
    if not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError(f"batch_size must be a positive integer, got: {batch_size}")

    schema, _ = get_split_schema(file_path)
    selected_cols = validate_columns(columns, list(schema.keys()))
    col_clause = ", ".join(f'"{c}"' for c in selected_cols)
    path_str = escape_duckdb_path(file_path)

    con = duckdb.connect()
    try:
        query = f"SELECT {col_clause} FROM read_csv_auto('{path_str}', parallel=false)"
        rel = con.execute(query)
        col_names = [desc[0] for desc in rel.description]

        while True:
            rows = rel.fetchmany(batch_size)
            if not rows:
                break
            chunk_df = pd.DataFrame(rows, columns=col_names)
            yield chunk_df
    finally:
        con.close()


def get_split_full_stats(file_path: Union[str, Path]) -> dict:
    """
    Execute exhaustive scan of a CSV file to compute row count, date ranges,
    flag distributions (positives, negatives, nulls), and column-by-column null counts.

    All computations are performed via bounded streaming DuckDB queries without
    loading the CSV into Pandas memory. Execution time is recorded.

    Args:
        file_path: Path to CSV file.

    Returns:
        dict containing census metrics, on-disk file size in bytes, and elapsed time.
    """
    path_str = escape_duckdb_path(file_path)
    file_size_bytes = os.path.getsize(file_path)

    start_time = time.perf_counter()
    con = duckdb.connect()
    try:
        # Schema probe
        schema_rows = con.execute(
            f"DESCRIBE SELECT * FROM read_csv_auto('{path_str}') LIMIT 0"
        ).fetchall()
        col_names = [r[0] for r in schema_rows]

        # Core census metrics
        stats_query = f"""
            SELECT
                COUNT(*) AS total_rows,
                MIN(timestamp) AS min_timestamp,
                MAX(timestamp) AS max_timestamp,
                SUM(CASE WHEN fake_discount_flag = 1 THEN 1 ELSE 0 END) AS fake_discount_pos,
                SUM(CASE WHEN fake_discount_flag = 0 THEN 1 ELSE 0 END) AS fake_discount_neg,
                SUM(CASE WHEN fake_discount_flag IS NULL THEN 1 ELSE 0 END) AS fake_discount_null,
                SUM(CASE WHEN price_spike_flag = 1 THEN 1 ELSE 0 END) AS price_spike_pos,
                SUM(CASE WHEN price_spike_flag = 0 THEN 1 ELSE 0 END) AS price_spike_neg,
                SUM(CASE WHEN price_spike_flag IS NULL THEN 1 ELSE 0 END) AS price_spike_null
            FROM read_csv_auto('{path_str}')
        """
        stats_row = con.execute(stats_query).fetchone()

        # Exhaustive column-by-column missing value counts
        null_exprs = [
            f'SUM(CASE WHEN "{c}" IS NULL THEN 1 ELSE 0 END) AS "{c}__nulls"'
            for c in col_names
        ]
        null_query = f"SELECT {', '.join(null_exprs)} FROM read_csv_auto('{path_str}')"
        null_row = con.execute(null_query).fetchone()
        column_null_counts = {col_names[i]: null_row[i] for i in range(len(col_names))}

        elapsed = time.perf_counter() - start_time

        return {
            "file_path": str(file_path),
            "file_size_bytes": file_size_bytes,
            "row_count": stats_row[0],
            "min_timestamp": stats_row[1],
            "max_timestamp": stats_row[2],
            "fake_discount_flag": {
                "positive_count": stats_row[3],
                "negative_count": stats_row[4],
                "null_count": stats_row[5],
            },
            "price_spike_flag": {
                "positive_count": stats_row[6],
                "negative_count": stats_row[7],
                "null_count": stats_row[8],
            },
            "column_null_counts": column_null_counts,
            "column_count": len(col_names),
            "elapsed_seconds": elapsed,
        }
    finally:
        con.close()
