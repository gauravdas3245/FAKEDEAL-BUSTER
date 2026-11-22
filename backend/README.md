# FakeDeal Buster backend

FastAPI provides the five-field internal `POST /api/analyze` endpoint and shopper-facing `GET /api/catalog`, `GET /api/catalog/metadata`, bounded `GET /api/catalog/search`, `POST /api/inspect`, `POST /api/forecast`, and `GET /api/models/synthetic-comparison` routes. Analysis responses include a separate synthetic scenario classifier result. Search matches partial normalized title or brand and applies category/platform filters in DuckDB. Filter metadata is served separately so the frontend does not download the full catalogue. The inspector resolves actual title/category/platform records and returns ambiguity rather than guessing.

The production data source is the read-only derived store `artifacts/derived/fakedeal_runtime.duckdb`. Build it from the original dataset's extracted chronological splits as documented in `docs/dataset-processing.md`; set `FAKEDEAL_RAW_DATA_DIR` or pass `--data-root`. The compact handoff extract is not used by production catalog or history services. If the derived store is missing or unreadable, the API returns `DATASET_UNAVAILABLE`.

The dataset has product-level ASIN values. An Amazon `/dp/<ASIN>` or `/gp/product/<ASIN>` URL can resolve only when the exact ASIN, title, category, and Amazon platform all match. Other marketplace URLs are syntax-checked metadata and do not verify identity. Seller name and seller rating are optional validated metadata only; the source has no seller identity or seller rating fields, and neither value is an ML feature.

Ordinary inspection omits `as_of`; the backend uses its current local timestamp. Historical mode accepts a valid past ISO-8601 timestamp. History is strictly earlier than the analysis time. Since the source ends on 2024-12-30, current-date analysis correctly returns `NEEDS_MORE_DATA`. Historical price chart points and summaries are actual recorded observations only; no dates are synthesized or interpolated.

All feature extraction, preprocessing, Isolation Forest inference, anomaly score semantics, and FDI state are from the central `ml.service`. The active model is `isolation_forest_v1`; its six-file bundle remains under `artifacts/ml/isolation_forest_v1/`. FDI remains unavailable when its required live inputs are absent. Forecasting uses flat last-observation and trailing-seven-day-mean baselines, compares them on five chronological 14-day rolling-origin windows, and emits a selected 14-day curve only with 180 consecutive actual daily observations. It provides no confidence interval and is not a guarantee. See `../docs/forecasting-methodology.md`.

`GET /health` distinguishes process state, database presence, and model-bundle file presence. The bundle is reported as `present_unverified` until the central loader verifies its checksums during inference.

The separately trained LR/RF bundle lives under `artifacts/ml/synthetic_discount_v1/`. It has its own checksummed models, preprocessing pipelines, metadata, and synthetic held-out evaluation. Responses describe resemblance to generated scenarios only; they do not provide fraud probability, seller intent, or verified deal status. If this optional bundle is missing or invalid, central anomaly analysis remains available and the synthetic result reports unavailable.

## Start from repository root

```powershell
& 'C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe' -m uvicorn app.main:app --app-dir backend --reload
```

API: `http://127.0.0.1:8000`; health: `GET /health`; OpenAPI: `/docs`.

## Tests

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend')
& 'C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe' -m pytest backend/tests -v
& 'C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe' -m pytest tests -v
```

See [API_CONTRACT.md](API_CONTRACT.md) for request and response schemas, validation, status behavior, and error codes.
