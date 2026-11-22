import csv
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.exceptions import MLServiceUnavailableError
from app.main import analysis_service, app
from app.services.history_service import HistoryService
from app.services.ml_adapter import CentralMLAdapter


@pytest.fixture
def client_with_history(tmp_path: Path, monkeypatch):
    dataset = tmp_path / "history.csv"
    as_of = datetime(2024, 10, 18)
    with dataset.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["product_id", "platform", "timestamp", "price", "original_price"])
        writer.writeheader()
        for day in range(1, 18):
            timestamp = datetime(2024, 10, day)
            writer.writerow({"product_id": "P1", "platform": "amazon", "timestamp": timestamp.isoformat(),
                             "price": 100 + day, "original_price": 150})
    monkeypatch.setattr(analysis_service, "history_service", HistoryService(dataset))
    return TestClient(app), dataset, as_of


def valid_payload(as_of="2024-10-18T00:00:00"):
    return {"product_id": "P1", "platform": "amazon", "as_of": as_of,
            "current_price": 110.0, "original_price": 150.0}


def test_five_field_request_and_real_model_success(client_with_history):
    client, _, _ = client_with_history
    response = client.post("/api/analyze", json=valid_payload())
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["success"] is True
    assert data["analysis_status"] == "OK"
    assert data["original_price"] == 150.0
    assert data["current_price"] == 110.0
    assert data["ml_anomaly"]["status"] == "OK"
    assert data["ml_anomaly"]["verdict"] in {"ANOMALY", "NO_ANOMALY"}
    assert isinstance(data["ml_anomaly"]["anomaly_score"], float)
    assert data["ml_anomaly"]["model_version"]
    assert list(data["ml_anomaly"]["features"]) == [
        "msrp_to_30d_avg", "ratio_to_30d_avg", "price_volatility_30d", "recent_7d_surge"
    ]


def test_fdi_insufficient_inputs_and_no_anomaly_to_fdi_mapping(client_with_history):
    client, _, _ = client_with_history
    data = client.post("/api/analyze", json=valid_payload()).json()
    assert data["fdi"]["status"] == "INSUFFICIENT_INPUTS"
    assert data["fdi"]["fdi_score"] is None
    assert data["fdi_score"] is None
    assert data["verdict"] is None
    assert data["confidence"] is None


def test_needs_more_data_has_no_prediction(client_with_history):
    client, _, _ = client_with_history
    data = client.post("/api/analyze", json=valid_payload("2024-10-05T00:00:00")).json()
    assert data["analysis_status"] == "NEEDS_MORE_DATA"
    assert data["ml_anomaly"]["status"] == "NEEDS_MORE_DATA"
    assert data["ml_anomaly"]["anomaly_score"] is None
    assert data["ml_anomaly"]["is_anomaly"] is None
    assert data["fdi"]["fdi_score"] is None
    assert data["fdi_score"] is None
    assert data["verdict"] is None


def test_current_price_above_original_returns_structured_422(client_with_history):
    client, _, _ = client_with_history
    payload = valid_payload()
    payload["current_price"] = 151
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_exactly_five_fields_are_required_and_extras_rejected(client_with_history):
    client, _, _ = client_with_history
    payload = valid_payload()
    payload.pop("platform")
    assert client.post("/api/analyze", json=payload).status_code == 422
    payload = valid_payload()
    payload["category"] = "Electronics"
    assert client.post("/api/analyze", json=payload).status_code == 422


def test_missing_artifacts_return_ml_service_unavailable(client_with_history, monkeypatch, tmp_path):
    client, _, _ = client_with_history
    monkeypatch.setattr(analysis_service, "ml_adapter", CentralMLAdapter(artifact_dir=tmp_path / "missing"))
    response = client.post("/api/analyze", json=valid_payload())
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ML_SERVICE_UNAVAILABLE"
    with pytest.raises(MLServiceUnavailableError):
        CentralMLAdapter(artifact_dir=tmp_path / "missing").analyze(
            product_id="P1", platform="amazon", timestamp="2024-10-18",
            current_price=110, original_price=150, historical_observations=[]
        )


def test_artifact_checksum_mismatch_is_rejected(tmp_path):
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    (artifact_dir / "checksums.sha256").write_text("0" * 64 + "  isolation_forest.joblib\n", encoding="utf-8")
    (artifact_dir / "isolation_forest.joblib").write_bytes(b"not the verified model")
    with pytest.raises(MLServiceUnavailableError):
        CentralMLAdapter(artifact_dir=artifact_dir).analyze(
            product_id="P1", platform="amazon", timestamp="2024-10-18",
            current_price=110, original_price=150, historical_observations=[]
        )


def test_conflicting_duplicate_history_returns_409(client_with_history):
    client, dataset, _ = client_with_history
    with dataset.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["P1", "amazon", "2024-10-01T12:00:00", "999", "150"])
    response = client.post("/api/analyze", json=valid_payload())
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "HISTORY_CONFLICT"


def test_identical_duplicates_deduplicated_and_cutoff_is_strict(client_with_history):
    client, dataset, as_of = client_with_history
    with dataset.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["P1", "amazon", "2024-10-01T12:00:00", "101", "150"])
        writer.writerow(["P1", "amazon", as_of.isoformat(), "999", "150"])
    history = analysis_service.history_service.lookup_history("P1", "amazon", as_of)
    assert len([item for item in history if item["timestamp"].date().isoformat() == "2024-10-01"]) == 1
    assert all(item["timestamp"] < as_of for item in history)
    response = client.post("/api/analyze", json=valid_payload())
    assert response.status_code == 200


def test_history_from_other_platform_is_not_used(client_with_history):
    client, dataset, _ = client_with_history
    with dataset.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        for day in range(1, 18):
            writer.writerow(["P1", "flipkart", f"2024-10-{day:02}T00:00:00", 1, 150])
    payload = valid_payload()
    payload["platform"] = "flipkart"
    data = client.post("/api/analyze", json=payload).json()
    assert data["ml_anomaly"]["features"]["ratio_to_30d_avg"] == pytest.approx(110.0)
