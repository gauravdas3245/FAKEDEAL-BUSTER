"""Run a clearly labelled synthetic single and batch inference demonstration."""
import argparse
import json
from datetime import date, timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.inference import load_inference_engine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=ROOT / "artifacts/ml/isolation_forest_v1")
    args = parser.parse_args()
    engine = load_inference_engine(args.artifact_dir)
    print("DEMO DATA: synthetic illustrative product history; not dataset observations or model evaluation")
    today = date(2024, 8, 1)
    history = [{"product_id": "DEMO-1", "platform": "amazon",
                "timestamp": (today - timedelta(days=day)).isoformat(),
                "price": 90.0 if day % 2 == 0 else 110.0}
               for day in range(20, 0, -1)]
    valid = engine.predict_product_observation(
        product_id="DEMO-1", platform="amazon", timestamp=today.isoformat(),
        current_price=80, original_price=150, historical_observations=history,
    )
    insufficient = engine.predict_product_observation(
        product_id="DEMO-2", platform="amazon", timestamp=today.isoformat(),
        current_price=80, original_price=150,
        historical_observations=[{**row, "product_id": "DEMO-2"} for row in history[:8]],
    )
    print("SUCCESSFUL PREDICTION:")
    print(json.dumps(valid, indent=2))
    print("NEEDS_MORE_DATA EXAMPLE:")
    print(json.dumps(insufficient, indent=2))
    print("Batch statuses:", [item["status"] for item in engine.predict_batch([
        {"product_id": "DEMO-1", "platform": "amazon", "timestamp": today.isoformat(),
         "current_price": 80, "original_price": 150, "historical_observations": history},
        {"product_id": "DEMO-2", "platform": "amazon", "timestamp": today.isoformat(),
         "current_price": 80, "original_price": 150,
         "historical_observations": [{**row, "product_id": "DEMO-2"} for row in history[:8]]},
    ])])


if __name__ == "__main__":
    main()
