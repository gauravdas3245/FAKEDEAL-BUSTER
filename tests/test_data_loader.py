"""
Unit and integration tests for ml.data_loader and split inspection logic.
Uses synthetic CSV fixtures in temporary directories; does not depend on raw large datasets.
"""

import os
import sys
from pathlib import Path
import pytest
import pandas as pd

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ml.data_loader import (
    escape_duckdb_path,
    get_dataset_root,
    get_split_full_stats,
    get_split_path,
    get_split_schema,
    load_preview,
    stream_batches,
    validate_columns,
)


@pytest.fixture
def synthetic_csv(tmp_path: Path) -> Path:
    """Create a small, deterministic 25-row synthetic pricing CSV file."""
    csv_path = tmp_path / "synthetic_pricing.csv"
    data = []
    for i in range(25):
        data.append({
            "product_id": f"PROD_{i:03d}",
            "title": f"Sample Product {i}",
            "platform": "amazon" if i % 2 == 0 else "flipkart",
            "timestamp": f"2023-01-{i+1:02d} 00:00:00",
            "price": 100.0 + (i * 5.0),
            "original_price": 150.0 + (i * 5.0),
            "discount_pct": round(((50.0) / (150.0 + (i * 5.0))) * 100, 2),
            "fake_discount_flag": 0,
            "price_spike_flag": 1 if i in [5, 12, 19] else 0,
        })
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def multi_split_dirs(tmp_path: Path) -> Path:
    """Create a temporary dataset root with separate train, val, and test splits."""
    splits_dir = tmp_path / "data" / "splits"
    splits_dir.mkdir(parents=True)

    # Train: 10 rows, Jan 2023
    train_data = [
        {
            "product_id": f"TR_{i:02d}",
            "timestamp": f"2023-01-{i+1:02d} 00:00:00",
            "price": 50.0 + i,
            "original_price": 80.0,
            "fake_discount_flag": 0,
            "price_spike_flag": 1 if i == 2 else 0,
        }
        for i in range(10)
    ]
    pd.DataFrame(train_data).to_csv(splits_dir / "ecommerce_train.csv", index=False)

    # Val: 5 rows, Feb 2023
    val_data = [
        {
            "product_id": f"VAL_{i:02d}",
            "timestamp": f"2023-02-{i+1:02d} 00:00:00",
            "price": 60.0 + i,
            "original_price": 85.0,
            "fake_discount_flag": 0,
            "price_spike_flag": 1 if i == 1 else 0,
        }
        for i in range(5)
    ]
    pd.DataFrame(val_data).to_csv(splits_dir / "ecommerce_val.csv", index=False)

    # Test: 5 rows, Mar 2023
    test_data = [
        {
            "product_id": f"TST_{i:02d}",
            "timestamp": f"2023-03-{i+1:02d} 00:00:00",
            "price": 70.0 + i,
            "original_price": 90.0,
            "fake_discount_flag": 0,
            "price_spike_flag": 0,
        }
        for i in range(5)
    ]
    pd.DataFrame(test_data).to_csv(splits_dir / "ecommerce_test.csv", index=False)

    return tmp_path


# --- Path Resolution & Configuration Tests ---

def test_get_dataset_root_unconfigured(monkeypatch):
    """Confirm FileNotFoundError is raised when neither arg nor env var is provided."""
    monkeypatch.delenv("FAKEDEAL_RAW_DATA_DIR", raising=False)
    with pytest.raises(FileNotFoundError, match="Dataset root directory is not configured"):
        get_dataset_root(None)


def test_get_dataset_root_explicit_path(tmp_path: Path):
    """Confirm explicit directory argument resolves correctly."""
    root = get_dataset_root(tmp_path)
    assert root == tmp_path.resolve()


def test_get_dataset_root_env_var(tmp_path: Path, monkeypatch):
    """Confirm FAKEDEAL_RAW_DATA_DIR environment variable resolves correctly."""
    monkeypatch.setenv("FAKEDEAL_RAW_DATA_DIR", str(tmp_path))
    root = get_dataset_root(None)
    assert root == tmp_path.resolve()


def test_get_dataset_root_nonexistent():
    """Confirm non-existent path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="does not exist"):
        get_dataset_root("C:/nonexistent_fakedeal_dir_xyz_123")


def test_get_split_path_unknown_split(tmp_path: Path):
    """Confirm invalid split name raises ValueError."""
    with pytest.raises(ValueError, match="Invalid split name 'unknown_split'"):
        get_split_path("unknown_split", root_dir=tmp_path)


def test_get_split_path_missing_file(tmp_path: Path):
    """Confirm missing split file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Split file 'train' not found"):
        get_split_path("train", root_dir=tmp_path)


def test_get_split_path_valid(multi_split_dirs: Path):
    """Confirm valid split file resolves to expected Path."""
    train_path = get_split_path("train", root_dir=multi_split_dirs)
    assert train_path.is_file()
    assert train_path.name == "ecommerce_train.csv"


# --- Path Escaping Tests ---

def test_escape_duckdb_path(tmp_path: Path):
    """Verify single-quote escaping for DuckDB SQL literal."""
    p = tmp_path / "test'file.csv"
    escaped = escape_duckdb_path(p)
    assert "''" in escaped


# --- Schema & Column Validation Tests ---

def test_get_split_schema(synthetic_csv: Path):
    """Verify schema inspection returns all columns and elapsed time."""
    schema, elapsed = get_split_schema(synthetic_csv)
    assert isinstance(schema, dict)
    assert "product_id" in schema
    assert "price" in schema
    assert "fake_discount_flag" in schema
    assert elapsed > 0


def test_validate_columns_valid(synthetic_csv: Path):
    """Verify column validation with legitimate columns."""
    schema, _ = get_split_schema(synthetic_csv)
    cols = validate_columns(["product_id", "price"], list(schema.keys()))
    assert cols == ["product_id", "price"]


def test_validate_columns_invalid_name():
    """Verify illegal SQL characters in column names are rejected."""
    with pytest.raises(ValueError, match="illegal characters"):
        validate_columns(["price; DROP TABLE users;"], ["price"])


def test_validate_columns_unrecognized():
    """Verify columns not in schema are rejected."""
    with pytest.raises(ValueError, match="not present in dataset schema"):
        validate_columns(["non_existent_column"], ["price", "title"])


# --- Preview & Deterministic Ordering Tests ---

def test_load_preview_bounds_and_order(synthetic_csv: Path):
    """
    Verify deterministic sequential ordering and exact row IDs.
    LIMIT 5 OFFSET 3 must return exactly PROD_003 through PROD_007 in order.
    """
    preview = load_preview(synthetic_csv, columns=["product_id", "price"], limit=5, offset=3)
    assert len(preview) == 5
    expected_ids = [f"PROD_{i:03d}" for i in range(3, 8)]
    assert preview["product_id"].tolist() == expected_ids


def test_load_preview_invalid_args(synthetic_csv: Path):
    """Verify non-positive limit or negative offset raises ValueError."""
    with pytest.raises(ValueError, match="limit must be a positive integer"):
        load_preview(synthetic_csv, limit=0)
    with pytest.raises(ValueError, match="offset must be a non-negative integer"):
        load_preview(synthetic_csv, limit=5, offset=-1)


def test_load_preview_column_projection(synthetic_csv: Path):
    """Verify only requested columns are returned."""
    df = load_preview(synthetic_csv, columns=["price", "original_price"], limit=2)
    assert list(df.columns) == ["price", "original_price"]


# --- Streaming Batches Tests ---

def test_stream_batches_total_rows(synthetic_csv: Path):
    """
    Verify stream_batches yields correct chunk counts and exactly 25 total rows
    without data corruption.
    """
    chunks = list(stream_batches(synthetic_csv, batch_size=10))
    # 25 rows with batch_size 10 -> chunks of size 10, 10, 5
    assert len(chunks) == 3
    assert len(chunks[0]) == 10
    assert len(chunks[1]) == 10
    assert len(chunks[2]) == 5

    full_df = pd.concat(chunks, ignore_index=True)
    assert len(full_df) == 25
    expected_ids = [f"PROD_{i:03d}" for i in range(25)]
    assert full_df["product_id"].tolist() == expected_ids


def test_stream_batches_early_termination(synthetic_csv: Path):
    """Verify early exit from stream_batches cleanly exits without error."""
    count = 0
    for chunk in stream_batches(synthetic_csv, batch_size=5):
        count += 1
        if count == 2:
            break
    assert count == 2


def test_stream_batches_invalid_batch_size(synthetic_csv: Path):
    """Verify batch_size <= 0 raises ValueError."""
    with pytest.raises(ValueError, match="batch_size must be a positive integer"):
        next(stream_batches(synthetic_csv, batch_size=0))


# --- Multi-Split Isolation Tests ---

def test_split_isolation(multi_split_dirs: Path):
    """
    Verify train, val, and test splits are analyzed completely independently
    and are never combined or cross-pollinated.
    """
    train_path = get_split_path("train", root_dir=multi_split_dirs)
    val_path = get_split_path("val", root_dir=multi_split_dirs)
    test_path = get_split_path("test", root_dir=multi_split_dirs)

    train_stats = get_split_full_stats(train_path)
    val_stats = get_split_full_stats(val_path)
    test_stats = get_split_full_stats(test_path)

    # Check row counts remain exact per file
    assert train_stats["row_count"] == 10
    assert val_stats["row_count"] == 5
    assert test_stats["row_count"] == 5

    # Check timestamps remain strictly chronological and non-overlapping
    assert train_stats["max_timestamp"] < val_stats["min_timestamp"]
    assert val_stats["max_timestamp"] < test_stats["min_timestamp"]

    # Check price spike flags remain separate
    assert train_stats["price_spike_flag"]["positive_count"] == 1
    assert val_stats["price_spike_flag"]["positive_count"] == 1
    assert test_stats["price_spike_flag"]["positive_count"] == 0
