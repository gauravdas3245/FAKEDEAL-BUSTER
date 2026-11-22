from datetime import date, timedelta
import hashlib
from pathlib import Path

import pytest

import ml.service as service_module
from ml.feature_extractor import FEATURE_NAMES
from ml.inference import InferenceValidationError, load_inference_engine
from ml.service import MLService, load_ml_service


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts/ml/isolation_forest_v1"


@pytest.fixture(scope="module")
def service():
    return load_ml_service(ARTIFACT_DIR)


def history(product="P1", platform="amazon", baseline=100.0, count=20):
    as_of = date(2024, 8, 1)
    return [{
        "product_id": product,
        "platform": platform,
        "timestamp": (as_of - timedelta(days=n)).isoformat(),
        "price": baseline + (10 if n % 2 else -10),
    } for n in range(count, 0, -1)]


def request(product="P1", platform="amazon", baseline=100.0, count=20):
    return {
        "product_id": product,
        "platform": platform,
        "timestamp": "2024-08-01",
        "current_price": 80.0,
        "original_price": 150.0,
        "historical_observations": history(product, platform, baseline, count),
    }


def test_success_returns_distinct_model_and_fdi_sections(service):
    result = service.analyze_product_observation(**request())
    assert result["status"] == "OK"
    assert result["model_version"] == "isolation_forest_v1"
    assert result["ml_anomaly"]["status"] == "OK"
    assert list(result["ml_anomaly"]["features"]) == list(FEATURE_NAMES)
    assert isinstance(result["ml_anomaly"]["anomaly_score"], float)
    assert result["fdi"]["status"] == "INSUFFICIENT_INPUTS"
    assert result["fdi"]["fdi_score"] is None
    assert result["fdi"]["missing_inputs"] == ["price_spike_flag", "pre_discount_hike_ratio"]
    assert result["fdi"]["validation_status"] == "PROVISIONAL_NOT_VALIDATED"


def test_insufficient_history_has_no_fabricated_scores_or_verdict(service):
    result = service.analyze_product_observation(**request(count=8))
    assert result["status"] == "NEEDS_MORE_DATA"
    assert result["ml_anomaly"]["status"] == "NEEDS_MORE_DATA"
    assert result["ml_anomaly"]["anomaly_score"] is None
    assert result["ml_anomaly"]["is_anomaly"] is None
    assert result["ml_anomaly"]["features"] is None
    assert result["fdi"]["status"] == "INSUFFICIENT_INPUTS"
    assert result["fdi"]["fdi_score"] is None
    assert "confidence" not in result


def test_invalid_input_returns_validation_error_without_results(service):
    params = request()
    params["current_price"] = 0
    result = service.analyze_product_observation(**params)
    assert result["status"] == "INVALID_INPUT"
    assert result["error"]["code"] == "VALIDATION_ERROR"
    assert result["ml_anomaly"] is result["fdi"] is None


def test_model_loading_failure_is_propagated_without_fabricated_service(monkeypatch):
    def fail(_path):
        raise ValueError("artifact checksum verification failed")
    monkeypatch.setattr(service_module, "load_inference_engine", fail)
    with pytest.raises(ValueError, match="checksum"):
        service_module.load_ml_service(ARTIFACT_DIR)


def test_unexpected_inference_failure_returns_processing_error(service):
    original = service.inference_engine.predict_product_observation
    service.inference_engine.predict_product_observation = lambda **_: (_ for _ in ()).throw(RuntimeError("boom"))
    try:
        result = service.analyze_product_observation(**request())
    finally:
        service.inference_engine.predict_product_observation = original
    assert result["status"] == "PROCESSING_ERROR"
    assert result["ml_anomaly"] is result["fdi"] is None
    assert result["error"]["message"] == "ML analysis could not be completed."


def test_product_platform_histories_are_independent(service):
    first = service.analyze_product_observation(**request("P1", "amazon", 100))
    second = service.analyze_product_observation(**request("P2", "ebay", 300))
    assert first["ml_anomaly"]["explanation"]["reference_values"]["prior_30d_mean_price"] == pytest.approx(100)
    assert second["ml_anomaly"]["explanation"]["reference_values"]["prior_30d_mean_price"] == pytest.approx(300)
    mismatched = request("P1", "amazon")
    mismatched["historical_observations"] = history("P1", "ebay")
    assert service.analyze_product_observation(**mismatched)["status"] == "INVALID_INPUT"


def test_version_feature_order_and_repeated_results_are_stable(service):
    first = service.analyze_product_observation(**request())
    second = service.analyze_product_observation(**request())
    assert first == second
    assert first["model_version"] == first["ml_anomaly"]["model_version"]
    assert list(first["ml_anomaly"]["features"]) == list(FEATURE_NAMES)
    assert first["methodology_version"] == first["fdi"]["methodology_version"]
    assert "confidence" not in first


def test_service_initializes_model_once_and_reuses_loaded_engine(monkeypatch):
    real_loader = service_module.load_inference_engine
    calls = []
    def counted(path):
        calls.append(path)
        return real_loader(path)
    monkeypatch.setattr(service_module, "load_inference_engine", counted)
    instance = service_module.load_ml_service(ARTIFACT_DIR)
    instance.analyze_product_observation(**request())
    instance.analyze_product_observation(**request())
    assert len(calls) == 1


def test_v1_artifacts_still_match_saved_checksum_manifest():
    for line in (ARTIFACT_DIR / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        expected, filename = line.split("  ", 1)
        actual = hashlib.sha256((ARTIFACT_DIR / filename).read_bytes()).hexdigest()
        assert actual == expected
