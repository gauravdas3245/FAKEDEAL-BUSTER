from datetime import date, timedelta
import json
from pathlib import Path

import pytest

from ml.feature_extractor import FEATURE_NAMES
from ml.inference import InferenceValidationError, load_inference_engine


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "ml" / "isolation_forest_v1"


def make_history(product="P1", platform="amazon", count=20):
    today = date(2024, 8, 1)
    return [{"product_id": product, "platform": platform,
             "timestamp": (today - timedelta(days=day)).isoformat(),
             "price": 90.0 if day % 2 == 0 else 110.0}
            for day in range(count, 0, -1)]


@pytest.fixture(scope="module")
def engine():
    return load_inference_engine(ARTIFACTS)


def observation(history=None, **updates):
    value = {"product_id": "P1", "platform": "amazon", "timestamp": "2024-08-01",
             "current_price": 80.0, "original_price": 150.0,
             "historical_observations": make_history() if history is None else history}
    value.update(updates)
    return value


def test_v1_artifacts_and_fixture_are_verified(engine):
    fixture = json.loads((ARTIFACTS / "verification_fixture.json").read_text())
    scaled = engine.preprocessor.transform_single(fixture["features"])
    actual = engine.detector.predict_anomaly(scaled)
    assert engine.metadata["feature_names"] == list(FEATURE_NAMES)
    assert actual["is_anomaly"] == fixture["expected_prediction"]["is_anomaly"]
    assert actual["anomaly_score"] == pytest.approx(fixture["expected_prediction"]["anomaly_score"], abs=1e-12)


def test_valid_observation_has_explainable_structured_result(engine):
    result = engine.predict_product_observation(**observation())
    assert result["status"] == "OK"
    assert result["model_version"] == "isolation_forest_v1"
    assert list(result["features"]) == list(FEATURE_NAMES)
    direct = engine.detector.predict_anomaly(engine.preprocessor.transform_single(result["features"]))
    assert result["is_anomaly"] == direct["is_anomaly"]
    assert result["anomaly_score"] == pytest.approx(direct["anomaly_score"])
    assert "probability" not in str(result).lower()
    assert result["explanation"]["interpretation"].startswith("Feature descriptions are descriptive")


def test_calendar_history_excludes_current_future_and_missing_dates(engine):
    history = make_history(count=20)
    history += [{"product_id": "P1", "platform": "amazon", "timestamp": "2024-08-01", "price": 9999},
                {"product_id": "P1", "platform": "amazon", "timestamp": "2024-08-05", "price": 9999}]
    result = engine.predict_product_observation(**observation(history=history))
    assert result["features"]["ratio_to_30d_avg"] == pytest.approx(0.8)


def test_timestamp_windows_use_exclusive_current_instant_and_inclusive_30d_boundary(engine):
    history = make_history()
    history.extend([
        {"product_id": "P1", "platform": "amazon", "timestamp": "2024-07-02T12:00:00", "price": 200},
        {"product_id": "P1", "platform": "amazon", "timestamp": "2024-08-01T11:59:00", "price": 9999},
        {"product_id": "P1", "platform": "amazon", "timestamp": "2024-08-01T12:00:00", "price": 9999},
    ])
    result = engine.predict_product_observation(**observation(
        history=history, timestamp="2024-08-01T12:00:00"))
    # The exact 30-day lower bound is included; earlier on the current day is prior.
    assert result["explanation"]["reference_values"]["prior_30d_observation_count"] == 22
    assert result["features"]["ratio_to_30d_avg"] < 0.8


def test_key_isolation_and_conflicting_duplicates_are_errors(engine):
    with pytest.raises(InferenceValidationError, match="key does not match"):
        engine.predict_product_observation(**observation(history=make_history(platform="ebay")))
    conflicting = make_history() + [{"product_id": "P1", "platform": "amazon",
                                      "timestamp": "2024-07-31", "price": 111}]
    with pytest.raises(InferenceValidationError, match="Duplicate conflicting"):
        engine.predict_product_observation(**observation(history=conflicting))


@pytest.mark.parametrize("price", [0, -1, float("nan"), float("inf"), None])
def test_invalid_prices_are_validation_errors(engine, price):
    with pytest.raises(InferenceValidationError):
        engine.predict_product_observation(**observation(current_price=price))


def test_needs_more_data_has_null_prediction_fields(engine):
    result = engine.predict_product_observation(**observation(history=make_history(count=8)))
    assert result["status"] == "NEEDS_MORE_DATA"
    assert result["verdict"] is result["anomaly_score"] is result["is_anomaly"] is result["features"] is None
    assert result["explanation"]["reason"] == "INSUFFICIENT_HISTORY"


def test_requires_recent_week_observation_for_7d_maximum(engine):
    history = [{"product_id": "P1", "platform": "amazon", "timestamp":
                (date(2024, 8, 1) - timedelta(days=day)).isoformat(), "price": 100}
               for day in range(8, 28)]
    result = engine.predict_product_observation(**observation(history=history))
    assert result["status"] == "NEEDS_MORE_DATA"


def test_minimum_history_requires_fourteen_distinct_observation_dates(engine):
    same_day = [{"product_id": "P1", "platform": "amazon",
                 "timestamp": f"2024-07-31T00:{minute:02d}:00", "price": 100}
                for minute in range(20)]
    result = engine.predict_product_observation(**observation(history=same_day))
    assert result["status"] == "NEEDS_MORE_DATA"


def test_batch_matches_single_and_handles_items_independently(engine):
    good = observation()
    short = observation(history=make_history(count=5), product_id="P2",
                        historical_observations=make_history(product="P2", count=5))
    invalid = observation(current_price=0)
    results = engine.predict_batch([good, short, invalid], batch_size=2)
    assert results[0] == engine.predict_product_observation(**good)
    assert results[1]["status"] == "NEEDS_MORE_DATA"
    assert results[2]["status"] == "INVALID_INPUT"
    assert engine.predict_product_observation(**good) == results[0]
    assert list(engine.iter_predict_batch(iter([good, short]), batch_size=1)) == results[:2]


def test_artifact_tampering_is_rejected(tmp_path):
    import shutil
    copy = tmp_path / "artifact"
    shutil.copytree(ARTIFACTS, copy)
    with (copy / "metadata.json").open("a", encoding="utf-8") as stream:
        stream.write(" ")
    with pytest.raises(ValueError, match="checksum"):
        load_inference_engine(copy)
