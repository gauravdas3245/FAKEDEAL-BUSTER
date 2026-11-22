# Implemented API contract

## `POST /api/analyze`

The request must contain exactly five fields. Extra fields are rejected.

```json
{
  "product_id": "P0000001",
  "platform": "amazon",
  "as_of": "2024-10-18T00:00:00",
  "current_price": 203.62,
  "original_price": 239.02
}
```

All fields are required. Product and platform must be non-empty strings, `as_of` must be a valid non-future ISO-8601 datetime, and prices must be positive finite numbers. `current_price` greater than `original_price` returns HTTP 422. The backend reads history only for the exact `(product_id, platform)` key and only before `as_of`. It rejects conflicting prices on the same date with HTTP 409 and `HISTORY_CONFLICT`; identical same-date prices are de-duplicated. No missing dates are filled. The central ML service requires at least 14 distinct dates in the trailing 30-day window and at least one observation in the trailing 7-day window.

## Successful response

The response preserves the central ML result in `ml_anomaly` and the complete central FDI result in `fdi`. It also includes the separate `synthetic_classifier` scenario-resemblance result. `ml_anomaly.verdict` is strictly the model's `ANOMALY` or `NO_ANOMALY` output; it is not a fraud judgment. The FDI is a separate provisional methodology. The classifier is trained on generated scenario labels only and is not a fraud judgment.

Additionally, `assessment_verdict` and `assessment_explanation` provide a standardized, explainable three-state assessment:
1. `Potential Suspicious Discount Pattern` — Anomaly detected by Isolation Forest relative to historical baseline.
2. `No Suspicious Pattern Detected` — Listed price and discount conform to normal historical patterns.
3. `Insufficient Evidence` — Inadequate historical price data (<14 days) to evaluate.

Example from the trained model using the full derived dataset store:

```json
{
  "success": true,
  "analysis_status": "OK",
  "verdict": null,
  "fdi_score": null,
  "confidence": null,
  "explanation": "Feature descriptions are descriptive, not causal model attributions. An anomaly is not proof of fraud. FDI score and risk level are unavailable because required FDI inputs are missing.",
  "original_price": 239.02,
  "current_price": 203.62,
  "discount_percentage": 14.81,
  "forecast_status": "UNAVAILABLE",
  "forecast": null,
  "ml_anomaly": {
    "status": "OK",
    "product_id": "P0000001",
    "platform": "amazon",
    "timestamp": "2024-10-18 00:00:00",
    "verdict": "NO_ANOMALY",
    "anomaly_score": -0.15759093500478655,
    "is_anomaly": false,
    "features": {
      "msrp_to_30d_avg": 1.3546942746757602,
      "ratio_to_30d_avg": 1.154057602750725,
      "price_volatility_30d": 0.1116823092336447,
      "recent_7d_surge": 0.18812049535720693
    },
    "explanation": {
      "model_result": "Isolation Forest did not flag an unusual feature combination.",
      "feature_descriptions": {
        "msrp_to_30d_avg": "Original price is 1.355x the prior 30-day average.",
        "ratio_to_30d_avg": "Current price is 1.154x the prior 30-day average.",
        "price_volatility_30d": "Prior 30-day sample volatility is 0.112 of the average.",
        "recent_7d_surge": "Recent 7-day maximum is 0.188 above the prior 30-day average (floored at zero)."
      },
      "reference_values": {
        "prior_30d_mean_price": 176.43833333333333,
        "prior_30d_observation_count": 30,
        "prior_7d_observation_count": 7
      },
      "interpretation": "Feature descriptions are descriptive, not causal model attributions. An anomaly is not proof of fraud."
    },
    "model_version": "isolation_forest_v1"
  },
  "fdi": {
    "status": "INSUFFICIENT_INPUTS",
    "fdi_score": null,
    "provisional_level": null,
    "component_scores": {
      "S_gap": 60.43247277171642,
      "S_mean_ratio": 100.0,
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
      "components": {
        "S_gap": "Difference between claimed discount percentage and the current discount versus prior 30-day mean.",
        "S_mean_ratio": "Current price relative to prior 30-day mean.",
        "S_msrp_inflation": "Advertised original price relative to prior 30-day mean.",
        "S_anomaly": "Proposed combination of a price-spike flag and pre-discount hike ratio; unavailable unless both signals are independently supplied."
      },
      "status_note": "PROVISIONAL_NOT_VALIDATED"
    },
    "methodology_version": "fdi_provisional_v1",
    "validation_status": "PROVISIONAL_NOT_VALIDATED"
  }
}
```

The top-level `verdict`, `fdi_score`, and `confidence` are null while FDI reports `INSUFFICIENT_INPUTS`. The partial component diagnostics remain available only inside the central `fdi` object. The backend does not map an anomaly score into FDI and does not infer confidence.

The `synthetic_classifier` object is either `SYNTHETIC_SCENARIO_EXPERIMENT`, `NEEDS_MORE_DATA`, `INSUFFICIENT_PRODUCT_METADATA`, or `UNAVAILABLE`. In its available state it contains `model`, `artifact_version`, `predicted_scenario`, `synthetic_scenario_score`, `decision_threshold`, `interpretation`, `disclaimer`, and `evaluation_scope`. The score is a model output over generated labels only; it is not calibrated for real listings and is not fraud probability or confidence. A real response example is:

```json
{
  "status": "SYNTHETIC_SCENARIO_EXPERIMENT",
  "model": "random_forest",
  "artifact_version": "synthetic_discount_classifier_v1",
  "predicted_scenario": "SYNTHETIC_ARTIFICIALLY_INFLATED_DISCOUNT",
  "synthetic_scenario_score": 0.9348723688275566,
  "decision_threshold": 0.41000000000000003,
  "interpretation": "This listing resembles the synthetic artificially inflated discount in generated training scenarios only.",
  "disclaimer": "Synthetic-scenario classifier output only. It is not a real-world fraud prediction, verified label, confidence score, or proof of seller intent.",
  "evaluation_scope": "SYNTHETIC_HELD_OUT_TEST_ONLY"
}
```

## Insufficient history

Insufficient history is a successful HTTP 200 analysis with `analysis_status: "NEEDS_MORE_DATA"`. The nested `ml_anomaly.status` is also `NEEDS_MORE_DATA`; its `anomaly_score`, `is_anomaly`, and `features` are null. FDI total, top-level verdict, and confidence are null. No low-risk result is substituted. The central FDI object reports its own `INSUFFICIENT_INPUTS` state.

## Error response

All errors use this shape:

```json
{
  "success": false,
  "error": {
    "code": "HISTORY_CONFLICT",
    "message": "Conflicting duplicate historical prices on 2024-10-01 for 'P0000001' on 'amazon'."
  }
}
```

| HTTP | Code | Meaning |
|---|---|---|
| 404 | `PRODUCT_NOT_FOUND` | No rows match the product/platform pair in the dataset. |
| 409 | `HISTORY_CONFLICT` | Different valid prices exist for the same product, platform, and date. |
| 422 | `VALIDATION_ERROR` | Invalid required fields, extra fields, invalid prices, or current price above original. |
| 422 | `INVALID_PRODUCT_URL` | Product URL is not a valid HTTP(S) URL. |
| 422 | `INVALID_PLATFORM` | Marketplace is unsupported or conflicts with a recognized URL domain. |
| 422 | `INVALID_CATEGORY` | Category is not present in the dataset. |
| 500 | `ANALYSIS_FAILED` | Central inference reports a processing failure. |
| 500 | `INTERNAL_SERVER_ERROR` | Unexpected backend error. |
| 503 | `DATASET_UNAVAILABLE` | The derived dataset store is absent or unreadable. |
| 503 | `ML_SERVICE_UNAVAILABLE` | The complete artifact bundle is missing, invalid, or fails checksum/model loading. |

## ML anomaly fields

`ml_anomaly` is passed through from `ml_service.analyze_product_observation` without recalculating its score. In the `OK` state it includes `status`, `product_id`, `platform`, `timestamp`, `verdict`, `anomaly_score`, `is_anomaly`, `features` in canonical model order, `explanation`, and `model_version`. The score direction and threshold semantics remain those of the central detector. It is not a probability or proof of fraud.

## Forecast

`POST /api/analyze` remains backward compatible and keeps `forecast: null` / `forecast_status: "UNAVAILABLE"`. The user-facing `POST /api/inspect` additionally returns a top-level `forecast` object, and `POST /api/forecast` accepts `{ "product_id": "P0000001", "platform": "amazon", "as_of": "2024-10-18T00:00:00" }` for internal integrations.

The 14-day forecast compares a flat last-observation baseline with a flat trailing-seven-observation mean using five chronological, non-overlapping 14-day backtest windows. It is emitted only when the 180 immediately preceding calendar days each have an actual valid observation. Dates are never filled or interpolated. The selected method minimizes backtest RMSE (then MAE); results include both methods' MAE/RMSE, actual history count, reference date, and limitations. No confidence interval is claimed. The output is a baseline research estimate, not a guarantee. Insufficient or gapped history returns `status: "INSUFFICIENT_HISTORY"`, `forecast: null`, and a reason.

## User-facing product inspection adapter

The React form uses `POST /api/inspect`. This adapter resolves visible listing metadata against the full derived dataset store, then constructs the existing five-field `AnalyzeRequest` and invokes the same `AnalysisService`. The public `POST /api/analyze` contract above and the central ML service remain unchanged.

Example request:

```json
{
  "product_name": "Google Max Smartphones (Green)",
  "platform": "amazon",
  "category": "Electronics",
  "as_of": "2024-10-18T00:00:00",
  "current_price": 203.62,
  "original_price": 239.02,
  "seller_name": "Example Seller",
  "seller_rating": 4.8,
  "product_url": "https://shop.example/item"
}
```

Product name, platform, category, and both prices are required; `as_of` is optional. If omitted, the backend uses its current timestamp. Seller name, rating, URL, and `selected_product_id` are optional. Names are trimmed and whitespace/case/punctuation normalized for deterministic exact identity lookup. Platform and category must match actual dataset rows. Rating, when supplied, must be numeric from 1.0 to 5.0; URL, when supplied, must be HTTP or HTTPS. Seller metadata is validated but never passed to the ML feature extractor. An exact ASIN is resolved only from recognized Amazon `/dp/` or `/gp/product/` URL paths and only when it agrees with the submitted name/category/platform and a real dataset row. Other URLs are not identity-verified.

`GET /api/catalog` exposes product names, categories, platforms, brand/subcategory/ASIN metadata, product count, and actual date range. `GET /api/catalog/metadata` returns supported filter metadata without the full product list. `GET /api/catalog/search` returns bounded real metadata suggestions and filters partial title/brand search against compatible category/platform values. The source contains 9,980 product IDs, five platforms, and seven categories; observations span 2023-01-01 through 2024-12-30. It has ASIN values but no product URL, seller name, or seller rating columns.

`POST /api/inspect` success returns `status: "ANALYZED"`, a `product` object (`title`, `category`, `platform`, `brand`, `subcategory`, and `asin` when available), `url_mapping_supported`, `price_history`, `historical_summary`, `cross_platform`, and `analysis`. The nested `analysis` value is the complete response object documented for `POST /api/analyze`, including its distinct `ml_anomaly` and `fdi` objects. Every price history/statistic is calculated from actual stored observations for that request. `url_mapping_supported` is true only for an exact supported ASIN match and otherwise false. A multiple-match response instead has `status: "AMBIGUOUS_PRODUCT"`, `selection_possible`, and actual candidate metadata. Unsupported platforms/categories return HTTP 422 (`INVALID_PLATFORM` / `INVALID_CATEGORY`).

On a unique match, `/api/inspect` returns `status: "ANALYZED"` and an `analysis` object with the same response schema as `POST /api/analyze`; product identity in the wrapper contains title, category, platform, and brand, but not the internal product ID. If multiple internal products share all supplied metadata, it returns `status: "AMBIGUOUS_PRODUCT"` and candidate metadata with `selection_possible`. Candidate IDs are internal selection values and must not be displayed as product names. A second submission can include `selected_product_id` (optional, internal adapter field) only when actual brand/catalog metadata distinguishes the candidates. If available metadata cannot distinguish candidates, selection is disabled and analysis stops instead of choosing arbitrarily. No match returns HTTP 404 `PRODUCT_NOT_FOUND`. Validation failures, including future timestamps and invalid ratings/URLs/prices, return HTTP 422 `VALIDATION_ERROR`.

`as_of`, when provided, must not be in the future. Historical lookup remains strictly earlier than the timestamp; no records are shifted, filled, or interpolated. Current dates after the dataset end return `NEEDS_MORE_DATA` and do not reuse the stale last price as a current observation. The response includes actual observed `price_history`, a preceding-window `historical_summary`, and `cross_platform` latest records when available; these are descriptive observed data, not model outputs.

## Synthetic model comparison

`GET /api/models/synthetic-comparison` returns `AVAILABLE` with Logistic Regression and Random Forest test metrics from the held-out generated-scenario test split, selected model, and an explicit synthetic-only disclaimer. It does not expose metrics from original dataset target flags and does not claim real-world fraud performance. The full generator, labels, split, threshold selection, and metrics are documented in `docs/synthetic-discount-experiment.md`.

## Run

From the repository root, activate the existing project environment and run:

```powershell
python -m uvicorn app.main:app --app-dir backend --reload
```

The backend requires `artifacts/derived/fakedeal_runtime.duckdb` plus the complete `artifacts/ml/isolation_forest_v1/` bundle, including `isolation_forest.joblib`, `preprocessor.json`, `metadata.json`, `validation_summary.json`, `verification_fixture.json`, and `checksums.sha256`. Generate the derived store from approved source splits using `scripts/build_runtime_store.py`; see [dataset-processing.md](../docs/dataset-processing.md). The central loader verifies artifact checksums before loading the model.
