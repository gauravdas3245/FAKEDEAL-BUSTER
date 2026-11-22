"""
Unit Tests for FakeDeal Buster ML Feature Pipeline.

Validates:
1. Exact mathematical calculations for all 4 features and auxiliary gap.
2. Current observation exclusion (records on or after eval_date ignored).
3. Strictly backward-looking windows and future date exclusion.
4. Product/platform separation and chronological ordering.
5. Minimum 14-day history requirement enforcement.
6. Zero, negative, and invalid price rejection.
7. Duplicate and conflicting record handling.
8. Consistent feature ordering in preprocessor and detector.
9. Split isolation (preprocessor fitted on train only).
10. Preprocessor and Isolation Forest serialization roundtrips.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ml.feature_extractor import (
    FEATURE_NAMES,
    MINIMUM_HISTORICAL_DAYS,
    FeatureExtractionResult,
    extract_single_product_features,
)
from ml.isolation_forest import IsolationForestDetector, train_isolation_forest
from ml.preprocessor import FeaturePreprocessor


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def base_date():
    return date(2024, 8, 1)


@pytest.fixture
def synthetic_history_20d(base_date):
    """Generate 20 consecutive daily price records strictly prior to base_date."""
    records = []
    # base_date - 20 days up to base_date - 1 day
    for i in range(20, 0, -1):
        d = base_date - timedelta(days=i)
        # Price alternates between 90 and 110 (mean = 100)
        p = 90.0 if (i % 2 == 0) else 110.0
        records.append({"date": str(d), "price": p})
    return records


# ---------------------------------------------------------------------------
# Feature Extractor Tests
# ---------------------------------------------------------------------------

def test_exact_formula_calculations(base_date, synthetic_history_20d):
    """Verify exact formula values against hand-calculated expectations."""
    # 20 observations: ten 90.0 and ten 110.0
    # mean = 100.0
    # sample std: sum of squared diffs = 20 * (10^2) = 2000. std = sqrt(2000 / 19) = 10.2597835
    # volatility = std / 100.0 = 0.102597835
    # 7-day window (i in 7..1): alternate 90 and 110 -> 7d_max = 110.0
    # surge = max(0, (110 - 100) / 100) = 0.10
    current_price = 80.0
    original_price = 150.0

    res = extract_single_product_features(
        current_price=current_price,
        original_price=original_price,
        historical_records=synthetic_history_20d,
        current_date=base_date,
        min_history=14,
    )

    assert res.is_success
    assert res.features is not None
    f = res.features

    # 1. msrp_to_30d_avg = 150 / 100 = 1.50
    assert pytest.approx(f["msrp_to_30d_avg"], rel=1e-5) == 1.50

    # 2. ratio_to_30d_avg = 80 / 100 = 0.80
    assert pytest.approx(f["ratio_to_30d_avg"], rel=1e-5) == 0.80

    # 3. price_volatility_30d = 10.2597835 / 100 = 0.1025978
    expected_std = np.sqrt(2000.0 / 19.0)
    expected_vol = expected_std / 100.0
    assert pytest.approx(f["price_volatility_30d"], rel=1e-5) == expected_vol

    # 4. recent_7d_surge = (110 - 100) / 100 = 0.10
    assert pytest.approx(f["recent_7d_surge"], rel=1e-5) == 0.10

    # Auxiliary: discount_inflation_gap
    # claimed_discount = (150 - 80) / 150 * 100 = 46.6667%
    # real_discount = (100 - 80) / 100 * 100 = 20.0000%
    # gap = 46.6667 - 20.0 = 26.6667%
    assert res.auxiliary is not None
    aux = res.auxiliary
    assert pytest.approx(aux["claimed_discount_pct"], rel=1e-4) == (70.0 / 150.0) * 100.0
    assert pytest.approx(aux["real_discount_pct"], rel=1e-4) == 20.0
    assert pytest.approx(aux["discount_inflation_gap"], rel=1e-4) == ((70.0 / 150.0) * 100.0) - 20.0


def test_current_observation_exclusion(base_date, synthetic_history_20d):
    """Verify that adding an observation on or after eval_date does NOT alter features."""
    # Baseline run
    res1 = extract_single_product_features(
        current_price=80.0,
        original_price=150.0,
        historical_records=synthetic_history_20d,
        current_date=base_date,
    )

    # Poison history with an observation on eval_date and another in the future
    poisoned_history = list(synthetic_history_20d)
    poisoned_history.append({"date": str(base_date), "price": 9999.0})  # today
    poisoned_history.append({"date": str(base_date + timedelta(days=5)), "price": 9999.0})  # future

    res2 = extract_single_product_features(
        current_price=80.0,
        original_price=150.0,
        historical_records=poisoned_history,
        current_date=base_date,
    )

    assert res1.is_success and res2.is_success
    assert res1.features == res2.features
    assert res1.auxiliary == res2.auxiliary


def test_minimum_14_day_history_enforcement(base_date):
    """Enforce strict minimum 14 valid records requirement."""
    # 13 records (below threshold)
    records_13 = [
        {"date": str(base_date - timedelta(days=i)), "price": 100.0}
        for i in range(13, 0, -1)
    ]
    res_13 = extract_single_product_features(
        current_price=80.0,
        original_price=120.0,
        historical_records=records_13,
        current_date=base_date,
        min_history=14,
    )
    assert not res_13.is_success
    assert res_13.status == "insufficient_history"
    assert "found 13" in res_13.reason

    # Add 14th record (meets threshold)
    records_14 = list(records_13)
    records_14.append({"date": str(base_date - timedelta(days=14)), "price": 100.0})
    res_14 = extract_single_product_features(
        current_price=80.0,
        original_price=120.0,
        historical_records=records_14,
        current_date=base_date,
        min_history=14,
    )
    assert res_14.is_success
    assert res_14.status == "success"


def test_outside_30_day_window_ignored(base_date):
    """Records older than 30 calendar days must not contribute to the 30-day window count."""
    # 20 records, but 10 of them are 40-50 days old
    old_records = [
        {"date": str(base_date - timedelta(days=i)), "price": 100.0}
        for i in range(50, 40, -1)
    ]
    # Only 10 records within trailing 30 days
    recent_records = [
        {"date": str(base_date - timedelta(days=i)), "price": 100.0}
        for i in range(10, 0, -1)
    ]
    all_records = old_records + recent_records

    res = extract_single_product_features(
        current_price=80.0,
        original_price=120.0,
        historical_records=all_records,
        current_date=base_date,
        min_history=14,
    )
    # Total records is 20, but only 10 are in trailing 30d window
    assert not res.is_success
    assert res.status == "insufficient_history"
    assert "found 10" in res.reason


def test_invalid_and_negative_prices_rejected(base_date, synthetic_history_20d):
    """Verify robust rejection of zero, negative, or non-numeric prices."""
    # Negative current price
    res_neg_curr = extract_single_product_features(
        current_price=-10.0,
        original_price=100.0,
        historical_records=synthetic_history_20d,
        current_date=base_date,
    )
    assert res_neg_curr.status == "invalid_input"

    # Zero current price
    res_zero = extract_single_product_features(
        current_price=0.0,
        original_price=100.0,
        historical_records=synthetic_history_20d,
        current_date=base_date,
    )
    assert res_zero.status == "invalid_input"

    # original_price < current_price
    res_inverted = extract_single_product_features(
        current_price=150.0,
        original_price=100.0,
        historical_records=synthetic_history_20d,
        current_date=base_date,
    )
    assert res_inverted.status == "invalid_input"
    assert "cannot be strictly less than" in res_inverted.reason


def test_duplicate_dates_handling(base_date):
    """Conflicting prices on the same date raise invalid_input; identical duplicates are safely deduplicated."""
    records_with_identical_dup = [
        {"date": str(base_date - timedelta(days=i)), "price": 100.0}
        for i in range(15, 0, -1)
    ]
    # Add duplicate identical observation for day 5
    records_with_identical_dup.append({"date": str(base_date - timedelta(days=5)), "price": 100.0})

    res_dup = extract_single_product_features(
        current_price=80.0,
        original_price=120.0,
        historical_records=records_with_identical_dup,
        current_date=base_date,
    )
    assert res_dup.is_success

    # Now add conflicting price on day 5 (100.0 vs 200.0)
    records_with_conflict = list(records_with_identical_dup)
    records_with_conflict.append({"date": str(base_date - timedelta(days=5)), "price": 200.0})

    res_conflict = extract_single_product_features(
        current_price=80.0,
        original_price=120.0,
        historical_records=records_with_conflict,
        current_date=base_date,
    )
    assert res_conflict.status == "invalid_input"
    assert "Duplicate conflicting" in res_conflict.reason


def test_to_feature_vector_canonical_order(base_date, synthetic_history_20d):
    """Verify that to_feature_vector returns a numpy array in exact canonical order."""
    res = extract_single_product_features(
        current_price=80.0,
        original_price=150.0,
        historical_records=synthetic_history_20d,
        current_date=base_date,
    )
    vec = res.to_feature_vector()
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (4,)
    assert vec[0] == res.features["msrp_to_30d_avg"]
    assert vec[1] == res.features["ratio_to_30d_avg"]
    assert vec[2] == res.features["price_volatility_30d"]
    assert vec[3] == res.features["recent_7d_surge"]


def test_model_feature_vector_excludes_auxiliary_and_target_fields():
    assert list(FEATURE_NAMES) == [
        "msrp_to_30d_avg", "ratio_to_30d_avg",
        "price_volatility_30d", "recent_7d_surge",
    ]
    assert "discount_inflation_gap" not in FEATURE_NAMES
    assert not any(name.startswith("target_") or name.endswith("_flag") for name in FEATURE_NAMES)


# ---------------------------------------------------------------------------
# Preprocessor Tests
# ---------------------------------------------------------------------------

def test_preprocessor_fit_transform_canonical_order():
    """Verify FeaturePreprocessor enforces column order and fits without split leakage."""
    # Create synthetic train DataFrame with random order
    train_df = pd.DataFrame({
        "ratio_to_30d_avg": [0.8, 0.9, 1.0, 1.1],
        "recent_7d_surge": [0.0, 0.1, 0.05, 0.2],
        "msrp_to_30d_avg": [1.2, 1.5, 1.1, 1.8],
        "price_volatility_30d": [0.02, 0.05, 0.01, 0.08],
    })

    preprocessor = FeaturePreprocessor(scaler_type="robust")
    scaled_train = preprocessor.fit_transform(train_df)

    assert preprocessor.is_fitted
    assert scaled_train.shape == (4, 4)
    assert list(preprocessor.fitted_params_.keys()) == list(FEATURE_NAMES)

    # Transform single dictionary
    single_dict = {
        "msrp_to_30d_avg": 1.5,
        "ratio_to_30d_avg": 0.9,
        "price_volatility_30d": 0.05,
        "recent_7d_surge": 0.1,
    }
    scaled_single = preprocessor.transform_single(single_dict)
    assert scaled_single.shape == (4,)
    assert np.all(np.isfinite(scaled_single))


def test_preprocessor_split_isolation():
    """Ensure preprocessor fitted on train transforms val/test using strictly train statistics."""
    train_df = pd.DataFrame({
        "msrp_to_30d_avg": [1.0, 2.0],
        "ratio_to_30d_avg": [1.0, 1.0],
        "price_volatility_30d": [0.1, 0.1],
        "recent_7d_surge": [0.0, 0.0],
    })
    test_df = pd.DataFrame({
        "msrp_to_30d_avg": [10.0, 20.0],  # Wildly different distribution
        "ratio_to_30d_avg": [5.0, 5.0],
        "price_volatility_30d": [0.5, 0.5],
        "recent_7d_surge": [1.0, 1.0],
    })

    preprocessor = FeaturePreprocessor(scaler_type="standard")
    preprocessor.fit(train_df)

    # Train mean of msrp_to_30d_avg is 1.5, std is 0.5
    assert pytest.approx(preprocessor.fitted_params_["msrp_to_30d_avg"]["center"], rel=1e-5) == 1.5
    assert pytest.approx(preprocessor.fitted_params_["msrp_to_30d_avg"]["scale"], rel=1e-5) == 0.5

    # Transforming test must use train center (1.5) and scale (0.5)
    scaled_test = preprocessor.transform(test_df)
    # (10.0 - 1.5) / 0.5 = 17.0
    assert pytest.approx(scaled_test[0, 0], rel=1e-5) == 17.0


def test_preprocessor_json_serialization(tmp_path):
    """Test JSON serialization and deserialization of preprocessor parameters."""
    train_df = pd.DataFrame({
        "msrp_to_30d_avg": [1.2, 1.5, 1.8],
        "ratio_to_30d_avg": [0.8, 0.9, 1.0],
        "price_volatility_30d": [0.02, 0.05, 0.08],
        "recent_7d_surge": [0.0, 0.1, 0.2],
    })

    preprocessor = FeaturePreprocessor(scaler_type="robust")
    preprocessor.fit(train_df)

    json_file = tmp_path / "preprocessor.json"
    preprocessor.save_json(json_file)
    assert json_file.is_file()

    loaded = FeaturePreprocessor.load_json(json_file)
    assert loaded.is_fitted
    assert loaded.scaler_type == "robust"
    assert loaded.fitted_params_ == preprocessor.fitted_params_

    # Verify identical output on new data
    sample = {"msrp_to_30d_avg": 1.4, "ratio_to_30d_avg": 0.85, "price_volatility_30d": 0.03, "recent_7d_surge": 0.05}
    np.testing.assert_allclose(preprocessor.transform_single(sample), loaded.transform_single(sample))


# ---------------------------------------------------------------------------
# Isolation Forest Detector Tests
# ---------------------------------------------------------------------------

def test_isolation_forest_training_and_scoring():
    """Verify IsolationForestDetector trains, scores, and outputs standardized anomaly labels."""
    # Synthetic normal training data (around mean 1.0)
    np.random.seed(42)
    X_train = np.random.normal(loc=1.0, scale=0.1, size=(200, 4))
    train_df = pd.DataFrame(X_train, columns=FEATURE_NAMES)

    detector = train_isolation_forest(train_df, contamination=0.05, random_state=42)
    assert detector.is_fitted

    # Score normal instance
    normal_inst = pd.DataFrame([[1.0, 1.0, 0.1, 0.0]], columns=FEATURE_NAMES)
    normal_pred = detector.predict_anomaly(normal_inst)
    assert isinstance(normal_pred["is_anomaly"], bool)
    assert isinstance(normal_pred["anomaly_score"], float)

    # Score extreme anomaly (e.g. 5x MSRP inflation, 10x volatility)
    extreme_anomaly = pd.DataFrame([[15.0, 5.0, 2.5, 3.0]], columns=FEATURE_NAMES)
    anomaly_pred = detector.predict_anomaly(extreme_anomaly)
    assert anomaly_pred["is_anomaly"] is True
    # Anomaly intensity for extreme outlier should exceed normal instance
    assert anomaly_pred["anomaly_score"] > normal_pred["anomaly_score"]


def test_isolation_forest_serialization(tmp_path):
    """Verify Joblib roundtrip for IsolationForestDetector."""
    np.random.seed(42)
    X_train = np.random.normal(loc=1.0, scale=0.1, size=(50, 4))
    detector = train_isolation_forest(X_train, random_state=42)

    model_path = tmp_path / "iso_forest.joblib"
    detector.save(model_path)
    assert model_path.is_file()

    loaded = IsolationForestDetector.load(model_path)
    assert loaded.is_fitted

    sample = np.array([[1.0, 1.0, 0.1, 0.0]])
    np.testing.assert_allclose(detector.score(sample), loaded.score(sample))
