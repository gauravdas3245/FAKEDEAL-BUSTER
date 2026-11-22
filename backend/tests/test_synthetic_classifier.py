from app.services.synthetic_classifier_adapter import SyntheticScenarioAdapter


def test_unavailable_synthetic_bundle_does_not_make_a_prediction(tmp_path):
    adapter = SyntheticScenarioAdapter(tmp_path / "missing")
    result = adapter.classify({"status": "OK", "features": {}}, current_price=80,
                              original_price=100, platform="amazon", category="Electronics")
    assert result["status"] == "UNAVAILABLE"
    assert result["predicted_scenario"] is None


def test_synthetic_classifier_preserves_insufficient_central_history(tmp_path):
    adapter = SyntheticScenarioAdapter(tmp_path / "missing")
    result = adapter.classify({"status": "NEEDS_MORE_DATA"}, current_price=80,
                              original_price=100, platform="amazon", category="Electronics")
    assert result["status"] == "NEEDS_MORE_DATA"
    assert result["predicted_scenario"] is None
