# ML inference integration guide

## Model and score semantics

Inference loads the existing `artifacts/ml/isolation_forest_v1` model and checks every file named in its SHA-256 manifest before deserialization. Initialize one engine per application process and reuse it. It verifies metadata, saved scaler and detector feature order against the canonical four features. It does not train or tune the model.

The detector wrapper returns `anomaly_score = -IsolationForest.decision_function(X)`, so larger values indicate stronger anomaly intensity. `is_anomaly` follows the fitted estimator's `predict()` output (`-1` is anomaly). These values are not fraud probabilities, causal explanations, or proof of fake discounts.

## Input contract

Required observation fields: `product_id` (non-empty string), `platform` (non-empty string), `timestamp` (date/datetime or ISO-8601), positive finite `current_price`, positive finite `original_price`, and `historical_observations` (sequence).

Each historical record contains matching `product_id`, `platform`, `timestamp` (or `date`), and positive finite `price`. History must be for the exact `(product_id, platform)` key. No interpolation, forward fill, or cross-platform substitution is performed. Duplicate same-date/same-price records are collapsed by the shared extractor; conflicting prices on a duplicate date are rejected. Invalid historical prices are rejected.

The four model inputs, in exact order, are:

1. `msrp_to_30d_avg = original_price / prior_30d_mean_price`
2. `ratio_to_30d_avg = current_price / prior_30d_mean_price`
3. `price_volatility_30d = prior_30d_sample_std / prior_30d_mean_price`
4. `recent_7d_surge = max(0, (prior_7d_max_price - prior_30d_mean_price) / prior_30d_mean_price)`

Inference applies the training SQL's calendar `RANGE` convention exactly: `[timestamp - 30 days, timestamp)` and `[timestamp - 7 days, timestamp)`. The current timestamp is excluded. It requires at least 14 distinct observed dates in the 30-day window and at least one valid observation in the 7-day window to calculate its maximum. It does not fill missing dates. If history is insufficient, a `NEEDS_MORE_DATA` response is returned without model scoring. `discount_inflation_gap` is not part of the model vector.

## Initialize once and predict

```python
from pathlib import Path
from ml.inference import load_inference_engine

engine = load_inference_engine(Path("artifacts/ml/isolation_forest_v1"))
result = engine.predict_product_observation(
    product_id="P0000001",
    platform="amazon",
    timestamp="2024-08-01T00:00:00",
    current_price=80.0,
    original_price=150.0,
    historical_observations=[
        {"product_id": "P0000001", "platform": "amazon",
         "timestamp": "2024-07-31T00:00:00", "price": 100.0},
        # Include enough valid daily history for both feature windows.
    ],
)
```

The abbreviated history above is illustrative and will produce `NEEDS_MORE_DATA`; production callers must supply sufficient history from their keyed store. The module is independent of FastAPI; a backend can initialize `engine` at application startup and call it from a route. No route/request contract is presumed finalized.

Successful response fields: `status="OK"`, product/platform/timestamp, `verdict` (`ANOMALY` or `NO_ANOMALY`), `anomaly_score`, `is_anomaly`, ordered `features`, descriptive `explanation`, and `model_version`. The explanation separates estimator output from feature ratios and explicitly says descriptions are not causal attributions.

Insufficient history returns `status="NEEDS_MORE_DATA"`, null verdict/score/flag/features and `explanation.reason="INSUFFICIENT_HISTORY"`. Invalid single input raises `InferenceValidationError` (a `ValueError` subclass). In batch mode each invalid item becomes `status="INVALID_INPUT"` with a validation message; neighboring items are still processed. Batch input is consumed in bounded groups controlled by `batch_size`, and model artifacts are never reloaded per item.

```python
results = engine.predict_batch(observations, batch_size=256)
# For a large stream, consume bounded output without retaining all responses:
for result in engine.iter_predict_batch(observations, batch_size=256):
    handle_result(result)
```

## Reproduce and verify

From repository root in PowerShell:

```powershell
& "C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe" scripts\demo_inference.py
& "C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe" scripts\validate_final_model.py --artifact-dir artifacts\ml\isolation_forest_v1
& "C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe" -m pytest -q --basetemp="C:\end sem project\FAKEDEAL-BUSTER\.pytest-run" -p no:cacheprovider
```

The demo examples are synthetic. They demonstrate API wiring only and do not represent dataset rows, model performance, or tuned thresholds. Use no test split for threshold tuning.
