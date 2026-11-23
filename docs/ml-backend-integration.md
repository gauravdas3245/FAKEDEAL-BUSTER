# ML service integration contract for FastAPI

This documents the central ML interface used by the implemented FastAPI backend. User-facing product resolution and dataset access are handled by the backend adapter; it translates resolved identities to the existing five-field analysis request and supplies actual historical observations. See [`backend/API_CONTRACT.md`](../backend/API_CONTRACT.md) for the HTTP routes and schemas.

## Import and initialize once

```python
from pathlib import Path
from ml.service import load_ml_service

ml_service = load_ml_service(Path("artifacts/ml/isolation_forest_v1"))
```

Initialization verifies the artifact checksum manifest, metadata and feature order, then loads the model/preprocessor once. `artifact_dir` is optional; when omitted, the module-relative `artifacts/ml/isolation_forest_v1` directory is used. A missing or invalid artifact raises during startup; do not serve predictions with an unverified model. Keep and reuse the same `ml_service` object for the application process.

## Exact method signature

```python
MLService.analyze_product_observation(
    *,
    product_id: str,
    platform: str,
    timestamp: Any,
    current_price: Any,
    original_price: Any,
    historical_observations: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]
```

`timestamp` may be a `date`, `datetime`, or ISO-8601 string. Current and original prices must be positive finite numbers, and original price cannot be below current price. Each historical record must contain the same `product_id` and `platform`, a `timestamp` (or `date`), and positive finite `price`. Supply history from the backend's history store for exactly that key. The inference engine performs strict prior calendar windows, excludes the current/future observations, does not interpolate missing dates, and rejects conflicting duplicate timestamps.

Example input preparation:

```python
from datetime import date, timedelta

as_of = date(2024, 8, 1)
history = [
    {
        "product_id": "P0000001",
        "platform": "amazon",
        "timestamp": (as_of - timedelta(days=day)).isoformat(),
        "price": 90.0 if day % 2 == 0 else 110.0,
    }
    for day in range(20, 0, -1)
]
response = ml_service.analyze_product_observation(
    product_id="P0000001",
    platform="amazon",
    timestamp=as_of.isoformat(),
    current_price=80.0,
    original_price=150.0,
    historical_observations=history,
)
```

This input is an illustrative synthetic example. In production, the backend must retrieve the observations; it must not synthesize history.

## Successful response shape

```json
{
  "status": "OK",
  "ml_anomaly": {
    "status": "OK",
    "product_id": "P0000001",
    "platform": "amazon",
    "timestamp": "2024-08-01 00:00:00",
    "verdict": "NO_ANOMALY",
    "anomaly_score": -0.17476044606593694,
    "is_anomaly": false,
    "features": {
      "msrp_to_30d_avg": 1.5,
      "ratio_to_30d_avg": 0.8,
      "price_volatility_30d": 0.1025978352085154,
      "recent_7d_surge": 0.1
    },
    "explanation": {
      "model_result": "Isolation Forest did not flag an unusual feature combination.",
      "interpretation": "Feature descriptions are descriptive, not causal model attributions. An anomaly is not proof of fraud."
    },
    "model_version": "isolation_forest_v1"
  },
  "fdi": {
    "status": "INSUFFICIENT_INPUTS",
    "fdi_score": null,
    "provisional_level": null,
    "component_scores": {
      "S_gap": 53.333333333333336,
      "S_mean_ratio": 0.0,
      "S_msrp_inflation": 100.0,
      "S_anomaly": null
    },
    "component_weights": {
      "S_gap": 0.35,
      "S_mean_ratio": 0.3,
      "S_msrp_inflation": 0.2,
      "S_anomaly": 0.15
    },
    "missing_inputs": ["price_spike_flag", "pre_discount_hike_ratio"],
    "explanation": {
      "summary": "FDI total unavailable because required pricing signals are missing; visible component scores are partial diagnostics only.",
      "status_note": "PROVISIONAL_NOT_VALIDATED"
    },
    "methodology_version": "fdi_provisional_v1",
    "validation_status": "PROVISIONAL_NOT_VALIDATED"
  },
  "model_version": "isolation_forest_v1",
  "methodology_version": "fdi_provisional_v1"
}
```

The Isolation Forest score uses the saved wrapper convention: higher scores indicate greater anomaly intensity; the flag follows the saved estimator threshold. Neither is a fraud probability or confirmed fraud decision. FDI is a separate heuristic result. Its proposed weights/bands are unvalidated and its official total is null because two inputs have no verified live derivation.

## `NEEDS_MORE_DATA`

If there are fewer than 14 distinct observed dates in the prior 30-day range, or no valid observation in the prior 7-day range, inference does not score the model. The service response has top-level `status="NEEDS_MORE_DATA"`; the nested `ml_anomaly` preserves that status with null `verdict`, `anomaly_score`, `is_anomaly`, and `features`. FDI is separately returned as `INSUFFICIENT_INPUTS`, with any computable component scores and a null FDI total. The backend should communicate data insufficiency distinctly from a normal/anomalous result.

## FDI unavailability

`discount_pct` and `real_discount_30d` are recomputed from current prices and verified historical inference output. `S_mean_ratio` and `S_msrp_inflation` use the verified inference features. The dataset's `price_spike_flag` is a label whose generation rule is not verified for live use, and `pre_discount_hike_ratio` has no documented definition. The service does not copy the label, invent a ratio, or substitute the Isolation Forest score. Thus FDI currently returns `status="INSUFFICIENT_INPUTS"`, null `fdi_score`/`provisional_level`, and those missing inputs even when ML inference succeeds.

## Errors and response handling

- `status="INVALID_INPUT"`: request/history validation failed. Both `ml_anomaly` and `fdi` are null and `error.code="VALIDATION_ERROR"` explains the issue. Map this to the backend's chosen client-error response.
- `status="PROCESSING_ERROR"`: unexpected inference/orchestration failure. Both prediction sections are null and the generic message contains no fabricated result. Log operational context in the backend and map to its chosen server-error response.
- Artifact initialization errors raise rather than producing a prediction. Treat invalid/missing artifacts as a startup failure.

Do not combine the ML and FDI statuses into a new verdict or confidence value. Preserve model and methodology version fields for logging and response traceability.

## Do not recreate ML feature calculations

The backend must not calculate or reorder `msrp_to_30d_avg`, `ratio_to_30d_avg`, `price_volatility_30d`, or `recent_7d_surge`; it must not fit or apply its own scaler, Isolation Forest, anomaly threshold, or FDI formula. Fetch correctly keyed history and pass raw current/original prices plus records to this service. The ML module owns the verified feature definitions, order, preprocessing, model decision behavior, and provisional FDI calculation.
