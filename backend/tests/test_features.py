from datetime import datetime, timedelta

from ml.service import load_ml_service


def test_backend_delegates_feature_calculation_to_central_ml_service():
    service = load_ml_service()
    as_of = datetime(2024, 2, 1)
    history = [
        {"product_id": "P1", "platform": "amazon", "timestamp": as_of - timedelta(days=day), "price": 100.0}
        for day in range(1, 31)
    ]
    result = service.analyze_product_observation(
        product_id="P1", platform="amazon", timestamp=as_of,
        current_price=100.0, original_price=120.0, historical_observations=history,
    )
    assert result["status"] == "OK"
    assert list(result["ml_anomaly"]["features"]) == [
        "msrp_to_30d_avg", "ratio_to_30d_avg", "price_volatility_30d", "recent_7d_surge"
    ]
    assert result["ml_anomaly"]["features"]["msrp_to_30d_avg"] == 1.2
    assert result["ml_anomaly"]["anomaly_score"] is not None
