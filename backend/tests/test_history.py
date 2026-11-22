import csv
from datetime import datetime

import pytest

from app.exceptions import DatasetUnavailableError, HistoryConflictError
from app.services.history_service import HistoryService


def write_history(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["product_id", "platform", "timestamp", "price", "original_price"])
        writer.writerows(rows)


def test_history_excludes_as_of_and_future_and_deduplicates(tmp_path):
    dataset = tmp_path / "prices.csv"
    write_history(dataset, [
        ["P1", "amazon", "2024-01-01T00:00:00", 100, 120],
        ["P1", "amazon", "2024-01-01T12:00:00", 100, 120],
        ["P1", "amazon", "2024-01-02T00:00:00", 101, 120],
        ["P1", "amazon", "2024-01-03T00:00:00", 102, 120],
        ["P1", "flipkart", "2024-01-01T00:00:00", 1, 120],
    ])
    history = HistoryService(dataset).lookup_history("P1", "amazon", datetime(2024, 1, 2))
    assert len(history) == 1
    assert history[0]["price"] == 100
    assert all(item["timestamp"] < datetime(2024, 1, 2) for item in history)


def test_conflicting_same_date_prices_raise_history_conflict(tmp_path):
    dataset = tmp_path / "prices.csv"
    write_history(dataset, [
        ["P1", "amazon", "2024-01-01T00:00:00", 100, 120],
        ["P1", "amazon", "2024-01-01T12:00:00", 101, 120],
    ])
    with pytest.raises(HistoryConflictError) as exc:
        HistoryService(dataset).lookup_history("P1", "amazon", datetime(2024, 1, 2))
    assert exc.value.code == "HISTORY_CONFLICT"


def test_missing_runtime_dataset_is_reported_without_a_path_leak(tmp_path):
    missing = tmp_path / "missing.duckdb"
    with pytest.raises(DatasetUnavailableError) as exc:
        HistoryService(missing).lookup_history("P1", "amazon", datetime(2024, 1, 2))
    assert exc.value.code == "DATASET_UNAVAILABLE"
    assert str(missing) not in exc.value.message
