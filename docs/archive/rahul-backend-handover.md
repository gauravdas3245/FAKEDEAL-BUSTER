# FakeDeal Buster — Backend Service

Backend API for **FakeDeal Buster**, an e-commerce discount analysis system designed to identify potentially misleading discounts using historical price patterns and machine learning.

> **Important Disclaimer:** The system outputs are risk indicators (FDI score and risk verdicts), **not** verified fraud classifications or accusations of seller crime.

---

## 1. Team Responsibilities

- **Gaurav Das** — Team Leader and ML Developer
- **Rahul Amin** — Backend Developer
- **Lakhyajyoti Phukan** — Data Preparation Analyst
- **Saniya Begum** — Frontend Developer
- **Myusha Chakma** — Testing and Integration Coordinator

---

## 2. Technology Stack & Environment

- **OS:** Windows 11
- **Python:** 3.14.7
- **Web Framework:** FastAPI 0.163.1 + Uvicorn 0.54.0
- **Validation:** Pydantic v2 (2.14.3)
- **Testing:** pytest 9.2.0 + httpx 0.28.1
- **Data Source:** Read-only CSV historical dataset extract (`data/p0000001_all_splits.csv`)

---

## 3. Directory Structure

```text
D:\FakeDeal-Buster\backend
│
├── .venv/                         # Python 3.14.7 virtual environment
├── .gitignore                     # Git ignore rules for Python, cache, and venv
├── API_CONTRACT.md                # Single source of truth API contract
├── requirements.txt               # Pinned dependencies
├── openapi.json                   # Live generated OpenAPI 3.1.0 specification
├── README.md                      # Backend documentation (this file)
│
├── data/
│   └── p0000001_all_splits.csv    # Read-only verified sample dataset (P0000001)
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application, routes, and exception handlers
│   ├── exceptions.py              # Domain exceptions (404, 409, 503, etc.)
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── request.py             # Pydantic AnalyzeRequest schema
│   │   └── response.py            # AnalyzeResponse, ErrorResponse, ForecastData schemas
│   │
│   └── services/
│       ├── __init__.py
│       ├── history_service.py     # CSV loader, filtering, and data-quality checks
│       ├── feature_service.py     # 4 Isolation Forest rolling features & sufficiency
│       ├── ml_service.py          # Isolation Forest model interface
│       └── analysis_service.py    # Orchestration service for POST /api/analyze
│
└── tests/
    ├── __init__.py
    ├── test_api.py                # Endpoint, validation, and error-handling tests
    ├── test_features.py           # Feature formula and threshold unit tests
    └── test_history.py            # Lookup, platform isolation, and duplicate tests
```

---

## 4. Setup and Installation

### 4.1. Prerequisites
Ensure you are in PowerShell or Command Prompt. The dedicated virtual environment is located at `D:\FakeDeal-Buster\backend\.venv`.

### 4.2. Activate the Virtual Environment

**In PowerShell:**
```powershell
D:\FakeDeal-Buster\backend\.venv\Scripts\Activate.ps1
```

**In Command Prompt (cmd):**
```cmd
D:\FakeDeal-Buster\backend\.venv\Scripts\activate.bat
```

> **Note on Windows Device Guard:** If standalone `pip.exe` is blocked by system policies, always invoke pip through python:
> ```powershell
> & "D:\FakeDeal-Buster\backend\.venv\Scripts\python.exe" -m pip install -r requirements.txt
> ```

---

## 5. Running the Backend Server

Start the development server with live reload:

```powershell
Push-Location "D:\FakeDeal-Buster\backend"
& "D:\FakeDeal-Buster\backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once running:
- **Root endpoint:** http://127.0.0.1:8000/
- **Health check:** http://127.0.0.1:8000/health
- **Interactive Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc documentation:** http://127.0.0.1:8000/redoc
- **OpenAPI Schema:** http://127.0.0.1:8000/openapi.json

---

## 6. API Endpoints

### 6.1. `GET /`
Returns API status and welcome message.

### 6.2. `GET /health`
Returns service health status (`{"status": "healthy", "service": "FakeDeal Buster Backend"}`).

### 6.3. `POST /api/analyze`
Analyzes a submitted product discount against historical pricing patterns.

#### Request Body (`AnalyzeRequest`):
```json
{
  "product_name": "Google Max Smartphones (Green)",
  "platform": "amazon",
  "category": "Electronics",
  "original_price": 221.26,
  "current_price": 180.00,
  "product_id": "P0000001",
  "as_of": "2024-10-18T00:00:00",
  "seller_name": "Retailer Hub",
  "seller_rating": 4.5,
  "product_url": "https://example.com/item"
}
```

#### Successful Response (`AnalyzeResponse`):
```json
{
  "success": true,
  "verdict": "LOW",
  "fdi_score": 28.5,
  "confidence": null,
  "explanation": "Price patterns are consistent with historical baseline.",
  "original_price": 221.26,
  "current_price": 180.0,
  "discount_percentage": 18.65,
  "forecast_status": "INSUFFICIENT_HISTORY",
  "forecast": null
}
```

#### Insufficient History Response (`NEEDS_MORE_DATA` state):
When fewer than 14 valid daily observations exist in the trailing 30 calendar days:
```json
{
  "success": true,
  "verdict": null,
  "fdi_score": null,
  "confidence": null,
  "explanation": "Insufficient valid price history to compute the required features. Insufficient historical observations in trailing 30 days: found 4, minimum required is 14.",
  "original_price": 221.26,
  "current_price": 203.92,
  "discount_percentage": 7.84,
  "forecast_status": "INSUFFICIENT_HISTORY",
  "forecast": null
}
```

#### Error Response Format:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Field 'product_name' must not be empty or whitespace."
  }
}
```

HTTP Status Codes:
- `200` — Successful analysis (including `NEEDS_MORE_DATA`)
- `404` — `PRODUCT_NOT_FOUND` (no records for product and platform)
- `409` — `HISTORY_CONFLICT` (conflicting prices on the same calendar date)
- `422` — `VALIDATION_ERROR` (invalid request schema or fields)
- `500` — `INTERNAL_SERVER_ERROR` (unhandled exception)
- `503` — `ML_SERVICE_UNAVAILABLE` (model artifact pending delivery)

---

## 7. Historical Data Rules & Feature Calculations

### Composite Key:
All historical lookups use `(product_id, platform)`. Observations from different platforms are **never** combined.

### As-Of Cutoff Rule:
Historical observations must have `timestamp < as_of`. The current submitted price is **never** included in its own historical baseline. Future observations are strictly excluded.

### Four Isolation Forest Features:
1. `msrp_to_30d_avg` = `original_price / price_30d_avg`
2. `ratio_to_30d_avg` = `current_price / price_30d_avg`
3. `price_volatility_30d` = `price_30d_std / price_30d_avg` (sample std, `ddof=1`)
4. `recent_7d_surge` = `max(0.0, (price_7d_max - price_30d_avg) / price_30d_avg)`

### Window & Sufficiency Rules:
- **30-Day Window:** `[as_of - 30 days, as_of)`. Requires $\ge 14$ valid daily observations.
- **7-Day Window:** `[as_of - 7 days, as_of)`. Requires $\ge 1$ valid daily observation.
- If thresholds are not met, returns `NEEDS_MORE_DATA`.
- Missing dates are not interpolated or forward-filled.
- Conflicting duplicate prices on the same date raise HTTP 409 `HISTORY_CONFLICT`. Identical duplicate prices are de-duplicated.

---

## 8. ML Service Integration Status

- **Architecture:** Clean service boundary in `app/services/ml_service.py`.
- **Feature Vector:** Exactly 4 features ordered as `[msrp_to_30d_avg, ratio_to_30d_avg, price_volatility_30d, recent_7d_surge]`.
- **Status:** **Awaiting model artifact** from ML Developer (Gaurav Das).
- **Behavior:** When the model artifact (`isolation_forest.joblib` or `.pkl`) is absent, requests with sufficient data cleanly return HTTP 503 `ML_SERVICE_UNAVAILABLE`. No fake predictions or fabricated fallback algorithms are executed. Requests with insufficient history cleanly return 200 `NEEDS_MORE_DATA` without invoking the model.

---

## 9. Running Tests

Run the complete test suite with pytest:

```powershell
Push-Location "D:\FakeDeal-Buster\backend"
& "D:\FakeDeal-Buster\backend\.venv\Scripts\python.exe" -m pytest -v
Pop-Location
```

All 20 test cases verify:
- Feature formula correctness against exact manual calculations.
- Sample standard deviation with `ddof=1`.
- Trailing 30-day and 7-day observation thresholds.
- Historical lookup by `(product_id, platform)`.
- Platform isolation and chronological timestamp sorting.
- Current observation exclusion and future data leakage prevention.
- Duplicate detection (identical de-duplication vs conflicting 409).
- Non-finite and invalid price filtering.
- Request schema validation (422) and custom exception formats.
- `NEEDS_MORE_DATA` handling.
- ML service integration and 503 failure handling.

---

## 10. Known Limitations and Pending Decisions

1. **ML Model Artifact:** Blocked on Gaurav Das to train and export `isolation_forest.joblib`.
2. **Price Forecasting:** Forecasting remains optional and pending feasibility confirmation. Currently returns `forecast_status="INSUFFICIENT_HISTORY"` and `forecast=null`.
3. **Seller Rating Scale:** Kept optional until frontend and ML agree on the rating scale (1–5 vs 0–100).
4. **Git Repository:** Maintainer (Gaurav Das) will manage GitHub commits and remote repository synchronization.
