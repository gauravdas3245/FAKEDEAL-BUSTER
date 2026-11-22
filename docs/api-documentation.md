# API documentation

The implemented FastAPI contract is documented in [`backend/API_CONTRACT.md`](../backend/API_CONTRACT.md). This page intentionally summarizes the live routes; it does not retain the earlier proposed product-name-only response schema.

## Local API

From the repository root, with the derived dataset store and model artifacts available:

```powershell
& 'C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe' -m uvicorn app.main:app --app-dir backend --reload
```

The API listens on `http://127.0.0.1:8000`. `GET /health` checks process health and `/docs` serves FastAPI's OpenAPI UI.

## Implemented routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/health` | Process, database file, and model-bundle presence status. |
| GET | `/api/catalog` | Dataset-derived catalog metadata and supported values. |
| GET | `/api/catalog/metadata` | Supported filters/date range without product records. |
| GET | `/api/catalog/search` | Bounded search over actual catalog identities. |
| POST | `/api/inspect` | User product metadata resolution and analysis adapter. |
| POST | `/api/analyze` | Strict five-field internal analysis contract. |
| POST | `/api/forecast` | Conditional 14-day baseline forecast for product/platform/date. |
| GET | `/api/models/synthetic-comparison` | LR/RF metrics on generated held-out scenarios only. |

`/api/inspect` adapts a title/platform/category and submitted prices to the unchanged five-field ML request. Product IDs are resolved only from exact normalized actual catalog metadata. A recognized Amazon URL is identity evidence only when its parsed ASIN matches the actual Amazon dataset record and submitted name/category. Seller fields remain optional validated metadata and are not ML inputs.

`/api/analyze` and `/api/inspect` return separate `ml_anomaly` and `fdi` objects from the central ML service plus `synthetic_classifier`, along with `assessment_verdict` and `assessment_explanation`. The assessment states are:
1. `Potential Suspicious Discount Pattern` — Anomaly detected by Isolation Forest relative to historical baseline.
2. `No Suspicious Pattern Detected` — Listed price and discount conform to normal historical patterns.
3. `Insufficient Evidence` — Inadequate historical price data (<14 days) to evaluate.

The `synthetic_classifier` reports resemblance to a generated scenario and is not real-world fraud probability or confidence. `/api/models/synthetic-comparison` metrics are for the synthetic test split only. The Isolation Forest output is an anomaly assessment, not a fraud probability. Missing historical inputs produce `NEEDS_MORE_DATA`; FDI reports `INSUFFICIENT_INPUTS` with a null total when its required live inputs are missing.

The production backend reads the local derived store `artifacts/derived/fakedeal_runtime.duckdb`, built from the original dataset splits as described in [`dataset-processing.md`](dataset-processing.md). Dataset and model errors use structured responses. Forecasting uses two baselines, five chronological windows, and requires 180 consecutive observed days; see [`forecasting-methodology.md`](forecasting-methodology.md). Live marketplace access is not implemented.
