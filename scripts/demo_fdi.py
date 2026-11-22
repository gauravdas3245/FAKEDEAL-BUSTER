"""Illustrate provisional FDI formulas with synthetic values only."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.fdi import calculate_fdi, calculate_fdi_from_inference


def main():
    print("SYNTHETIC ILLUSTRATION ONLY - not real product evidence, validation, or performance")
    illustrative_inputs = {
        "discount_pct": 40.0,
        "real_discount_30d": 10.0,
        "ratio_to_30d_avg": 0.97,
        "msrp_inflation_ratio": 1.15,
        "price_spike_flag": 1,
        "pre_discount_hike_ratio": 0.10,
    }
    print("All six values below are illustrative inputs, including both anomaly signals:")
    print(json.dumps(illustrative_inputs, indent=2))
    print("Complete formula illustration (provisional only):")
    print(json.dumps(calculate_fdi(illustrative_inputs), indent=2))

    inference_result = {
        "status": "OK",
        "features": {"ratio_to_30d_avg": 0.97, "msrp_to_30d_avg": 1.15},
        "anomaly_score": 0.12,
        "is_anomaly": False,
    }
    print("Inference-adapter result (shows unavailable live signals; anomaly score is not substituted):")
    print(json.dumps(calculate_fdi_from_inference(
        inference_result, current_price=97.0, original_price=115.0,
    ), indent=2))


if __name__ == "__main__":
    main()
