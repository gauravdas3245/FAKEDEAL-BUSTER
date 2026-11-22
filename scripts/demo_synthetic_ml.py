"""Reproducible, explicitly synthetic FakeDeal Buster ML demonstration.

Run from the repository root with the configured Conda environment:
    python scripts/demo_synthetic_ml.py

This script does not read or modify the project dataset. Both the price history
and Isolation Forest training observations are generated deterministically.
"""

from datetime import date, timedelta
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from ml.feature_extractor import FEATURE_NAMES, extract_single_product_features
from ml.isolation_forest import IsolationForestDetector
from ml.preprocessor import FeaturePreprocessor


def _history_for_training(rng: np.random.Generator, base_date: date, index: int):
    """Generate one synthetic 30-day price history for a baseline observation."""
    base = float(rng.uniform(60.0, 180.0))
    daily_noise = rng.normal(0.0, rng.uniform(0.005, 0.045), 30)
    mild_trend = np.linspace(rng.uniform(-0.03, 0.01), rng.uniform(-0.01, 0.03), 30)
    prices = base * (1.0 + daily_noise + mild_trend)
    return [
        {"date": str(base_date - timedelta(days=30 - day)), "price": float(price)}
        for day, price in enumerate(prices)
    ]


def main() -> None:
    rng = np.random.default_rng(20261117)
    evaluation_date = date(2024, 8, 1)

    # Construct a suspicious-looking example against a generated price history.
    demo_history = []
    for day in range(30, 0, -1):
        date_value = evaluation_date - timedelta(days=day)
        price = 100.0 + (5.0 if day <= 7 else 0.0) + ((day % 5) - 2) * 0.8
        demo_history.append({"date": str(date_value), "price": price})
    current_price = 78.0
    original_price = 150.0
    extracted = extract_single_product_features(
        current_price=current_price,
        original_price=original_price,
        historical_records=demo_history,
        current_date=evaluation_date,
    )
    if not extracted.is_success:
        raise RuntimeError(f"Synthetic demo feature extraction failed: {extracted.reason}")

    training_rows = []
    for index in range(300):
        history = _history_for_training(rng, evaluation_date, index)
        trailing_mean = float(np.mean([item["price"] for item in history]))
        current = trailing_mean * float(rng.uniform(0.93, 1.07))
        reference = current * float(rng.uniform(1.02, 1.22))
        result = extract_single_product_features(
            current_price=current,
            original_price=reference,
            historical_records=history,
            current_date=evaluation_date,
        )
        if result.is_success:
            training_rows.append(result.to_feature_vector())

    training_features = pd.DataFrame(training_rows, columns=FEATURE_NAMES)
    preprocessor = FeaturePreprocessor(scaler_type="robust")
    scaled_training = preprocessor.fit_transform(training_features)
    detector = IsolationForestDetector(
        n_estimators=100, contamination=0.03, random_state=20261117,
    ).fit(scaled_training)

    feature_dict = extracted.features
    scaled_example = preprocessor.transform_single(feature_dict)
    prediction = detector.predict_anomaly(scaled_example)
    history_prices = np.array([item["price"] for item in demo_history], dtype=float)
    seven_day_prices = np.array([item["price"] for item in demo_history[-7:]], dtype=float)
    history_mean = float(history_prices.mean())
    history_std = float(history_prices.std(ddof=1))
    claimed_discount = (original_price - current_price) / original_price * 100.0
    real_discount = (history_mean - current_price) / history_mean * 100.0

    output = {
        "data_status": "SYNTHETIC DEMONSTRATION — NOT PROJECT DATA",
        "evaluation_date": str(evaluation_date),
        "historical_observations": len(demo_history),
        "current_price": current_price,
        "original_price": original_price,
        "calculation_inputs": {
            "trailing_30d_mean": history_mean,
            "trailing_30d_sample_std": history_std,
            "trailing_7d_max": float(seven_day_prices.max()),
            "claimed_discount_pct": claimed_discount,
            "historical_discount_pct": real_discount,
        },
        "features_in_model_order": feature_dict,
        "scaled_features_in_model_order": scaled_example.tolist(),
        "synthetic_training_rows": len(training_features),
        "isolation_forest_result": prediction,
        "interpretation": "Anomaly score is a statistical outlier indicator, not a fraud probability or proof of fraud.",
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
