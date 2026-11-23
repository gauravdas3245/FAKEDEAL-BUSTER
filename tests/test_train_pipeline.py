"""Synthetic integration tests for bounded feature extraction and train/val flow."""

from datetime import date, timedelta

import pandas as pd
import numpy as np
import pytest

from ml.train_pipeline import _reservoir_sample, iter_feature_batches, train_from_splits


@pytest.fixture
def split_files(tmp_path):
    def write(name, offset, rows):
        records = []
        start = date(2024, 1, 1) + timedelta(days=offset)
        for product in range(4):
            for day in range(rows):
                price = 100 + product * 20 + ((day % 9) - 4) * (1 + product)
                records.append({
                    "product_id": f"P{product}", "platform": "shop",
                    "category": f"category-{product % 2}",
                    "timestamp": str(start + timedelta(days=day)),
                    "price": price, "original_price": price * 1.4,
                    "discount_pct": 28.6,
                })
        path = tmp_path / name
        pd.DataFrame(records).to_csv(path, index=False)
        return path

    return write("train.csv", 0, 50), write("val.csv", 50, 25)


def test_feature_batches_are_bounded_and_exclude_early_history(split_files):
    train, _ = split_files
    batches = list(iter_feature_batches(train, batch_size=7, limit=31))
    assert batches
    assert max(map(len, batches)) <= 7
    assert sum(map(len, batches)) == 31
    assert all("fake_discount_flag" not in frame and "target_price_7d" not in frame
               for frame in batches)


def test_source_row_limit_bounds_duckdb_input(split_files):
    train, _ = split_files
    batches = list(iter_feature_batches(train, batch_size=5, source_row_limit=20))
    assert sum(map(len, batches)) == 6
    assert all(len(batch) <= 5 for batch in batches)


def test_reservoir_sampling_is_deterministic_across_batch_sizes():
    from ml.feature_extractor import FEATURE_NAMES

    values = np.arange(400, dtype=float).reshape(100, 4)
    frame = pd.DataFrame(values, columns=FEATURE_NAMES)
    sample_a, seen_a = _reservoir_sample(iter([frame.iloc[:31], frame.iloc[31:]]), 17, 321)
    sample_b, seen_b = _reservoir_sample(iter([frame.iloc[:7], frame.iloc[7:64], frame.iloc[64:]]), 17, 321)
    assert seen_a == seen_b == 100
    pd.testing.assert_frame_equal(sample_a, sample_b)
    assert len(sample_a) == 17


def test_product_filter_bounds_validation_history_to_requested_products(split_files):
    train, val = split_files
    batches = list(iter_feature_batches(
        val, batch_size=50, history_csv_paths=[train, val],
        output_start="2024-02-20", product_ids=["P1"],
    ))
    assert batches
    assert {value for batch in batches for value in batch["product_id"]} == {"P1"}


def test_training_uses_train_only_and_scores_validation(split_files):
    train, val = split_files
    result = train_from_splits(
        train, val, batch_size=11, max_training_rows=40,
        n_estimators=20, random_state=4,
    )
    assert result.training_rows_seen > result.training_rows_used == 40
    assert result.validation_rows_scored > 0
    assert 0 <= result.validation_anomaly_rate <= 1
    assert result.validation_source_rows == 100
    assert result.validation_eligible_feature_rows == 100
    assert set(result.validation_by_category) == {"category-0", "category-1"}
    assert result.detector.is_fitted and result.preprocessor.is_fitted

    repeated = train_from_splits(
        train, val, batch_size=11, max_training_rows=40,
        n_estimators=20, random_state=4,
    )
    assert repeated.preprocessor.fitted_params_ == result.preprocessor.fitted_params_
    sample = next(iter_feature_batches(val, batch_size=1)).loc[:, list(result.preprocessor.feature_names)]
    first_score = result.detector.score(result.preprocessor.transform(sample))
    repeated_score = repeated.detector.score(repeated.preprocessor.transform(sample))
    np.testing.assert_allclose(first_score, repeated_score)


def test_validation_features_include_only_prior_training_history(split_files):
    train, val = split_files
    first_validation_day = pd.Timestamp("2024-02-20")
    batches = iter_feature_batches(
        val, batch_size=9, history_csv_paths=[train, val],
        output_start=first_validation_day,
    )
    first_day_rows = []
    for batch in batches:
        matches = batch[batch["timestamp"].astype(str).str.startswith(str(first_validation_day.date()))]
        first_day_rows.extend(matches.to_dict("records"))
    assert len(first_day_rows) == 4
    assert all(row["hist_30d_count"] == 30 for row in first_day_rows)


def test_calendar_window_ignores_old_rows_across_missing_dates(tmp_path):
    rows = []
    start = date(2024, 1, 1)
    for day in range(20):
        rows.append({
            "product_id": "P", "platform": "shop",
            "timestamp": str(start + timedelta(days=day * 2)),
            "price": 100.0 + day, "original_price": 150.0,
            "discount_pct": 33.3,
        })
    rows.append({
        "product_id": "P", "platform": "shop",
        "timestamp": str(start + timedelta(days=40)),
        "price": 90.0, "original_price": 150.0,
        "discount_pct": 40.0,
    })
    path = tmp_path / "missing_dates.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    frames = list(iter_feature_batches(path, batch_size=50, min_history=14))
    evaluation = pd.concat(frames)
    last = evaluation[evaluation["timestamp"].astype(str).str.startswith("2024-02-10")].iloc[0]
    # Prior days 10..38 (every other day): 15 observations in the 30-day window.
    assert last["hist_30d_count"] == 15


def test_windows_are_isolated_by_product_and_platform(tmp_path):
    rows = []
    start = date(2024, 1, 1)
    for platform, base_price in (("shop_a", 100.0), ("shop_b", 200.0)):
        for day in range(18):
            rows.append({
                "product_id": "same-product", "platform": platform,
                "timestamp": str(start + timedelta(days=day)),
                "price": base_price, "original_price": base_price * 1.5,
                "discount_pct": 33.3,
            })
    path = tmp_path / "platforms.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    frames = list(iter_feature_batches(path, batch_size=50, min_history=14))
    features = pd.concat(frames)
    last_day = features[features["timestamp"].astype(str).str.startswith("2024-01-18")]
    assert set(last_day["platform"]) == {"shop_a", "shop_b"}
    assert list(last_day["hist_30d_count"]) == [17, 17]


def test_duckdb_feature_formulas_match_historical_convention(tmp_path):
    start = date(2024, 1, 1)
    rows = []
    for day in range(21):
        price = (90.0 if day % 2 == 0 else 110.0) if day < 20 else 80.0
        rows.append({
            "product_id": "P", "platform": "shop",
            "timestamp": str(start + timedelta(days=day)),
            "price": price, "original_price": 150.0,
            "discount_pct": (150.0 - price) / 150.0 * 100.0,
        })
    path = tmp_path / "formula.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    frames = list(iter_feature_batches(path, batch_size=50))
    last = pd.concat(frames).iloc[-1]
    expected_std = (2000.0 / 19.0) ** 0.5
    assert last["hist_30d_count"] == 20
    assert last["msrp_to_30d_avg"] == pytest.approx(1.5)
    assert last["ratio_to_30d_avg"] == pytest.approx(0.8)
    assert last["price_volatility_30d"] == pytest.approx(expected_std / 100.0)
    assert last["recent_7d_surge"] == pytest.approx(0.1)


def test_invalid_batch_size_rejected(split_files):
    train, _ = split_files
    with pytest.raises(ValueError, match="batch_size"):
        next(iter_feature_batches(train, batch_size=0))


def test_overlapping_validation_period_is_rejected(split_files):
    train, _ = split_files
    overlap = train.parent / "overlap.csv"
    pd.read_csv(train).to_csv(overlap, index=False)
    with pytest.raises(ValueError, match="strictly later"):
        train_from_splits(train, overlap, max_training_rows=40, n_estimators=10)
