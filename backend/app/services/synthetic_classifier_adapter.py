"""Adapter for synthetic scenario classification; never a fraud verdict."""

from pathlib import Path
from typing import Any

from ml.synthetic_classifier import classify_synthetic_scenario, load_classifier_bundle

ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_DIRECTORY = ROOT / "artifacts" / "ml" / "synthetic_discount_v1"


class SyntheticScenarioAdapter:
    def __init__(self, artifact_dir: Path = ARTIFACT_DIRECTORY):
        self.artifact_dir = Path(artifact_dir)
        self._bundle: dict[str, Any] | None = None
        self._load_error: str | None = None

    def classify(self, anomaly: dict[str, Any], *, current_price: float,
                 original_price: float, platform: str, category: str | None) -> dict[str, Any]:
        if anomaly.get("status") == "NEEDS_MORE_DATA":
            return {"status": "NEEDS_MORE_DATA", "predicted_scenario": None,
                    "message": "The synthetic scenario model requires the same verified historical feature vector as the Isolation Forest."}
        if not category:
            return {"status": "INSUFFICIENT_PRODUCT_METADATA", "predicted_scenario": None,
                    "message": "Dataset category is unavailable; no synthetic scenario result was produced."}
        if not self.artifact_dir.is_dir():
            return {"status": "UNAVAILABLE", "predicted_scenario": None,
                    "message": "The separately trained synthetic classifier bundle is unavailable."}
        if self._bundle is None and self._load_error is None:
            try:
                self._bundle = load_classifier_bundle(self.artifact_dir)
            except Exception:
                self._load_error = "The synthetic classifier artifact bundle failed checksum or load validation."
        if self._load_error:
            return {"status": "UNAVAILABLE", "predicted_scenario": None, "message": self._load_error}
        source_features = anomaly.get("features") or {}
        try:
            mapped = {name: float(source_features[name]) for name in (
                "msrp_to_30d_avg", "ratio_to_30d_avg", "price_volatility_30d", "recent_7d_surge")}
            mapped.update({
                "advertised_discount_pct": (float(original_price) - float(current_price)) / float(original_price) * 100.0,
                "platform": platform.strip().casefold(),
                "category": category,
            })
            return classify_synthetic_scenario(self._bundle, mapped)
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            return {"status": "INVALID_FEATURES", "predicted_scenario": None,
                    "message": "The synthetic experiment could not use the returned central feature values."}

    def comparison(self) -> dict[str, Any]:
        if self._bundle is None:
            try:
                self._bundle = load_classifier_bundle(self.artifact_dir)
            except Exception:
                return {"status": "UNAVAILABLE", "evaluation_scope": "SYNTHETIC_HELD_OUT_TEST_ONLY"}
        import json
        evaluation = json.loads((self.artifact_dir / "evaluation.json").read_text(encoding="utf-8"))
        return {"status": "AVAILABLE", "evaluation_scope": evaluation["evaluation_scope"],
                "selected_model": evaluation["selected_model"],
                "test_metrics": evaluation["test_metrics"],
                "disclaimer": "All scores are for held-out generated scenarios only; they are not real-world fraud metrics."}
