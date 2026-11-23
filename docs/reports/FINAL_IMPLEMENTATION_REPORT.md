# FakeDeal Buster — Final Implementation Report (Prompt 1)

**Project:** FakeDeal Buster — Sale-Day Artificial Discount & Price Scam Detector  
**Institution:** Scholar Institute of Technology and Management (SITM), Guwahati (BCA Final Project, Group B)  
**Implementation Date:** 18 November 2026  
**Implementation Status:** **FULLY FUNCTIONAL ACADEMIC PROTOTYPE COMPLETED & VERIFIED**  

> [!NOTE]
> **Academic Integrity Statement:**  
> All source CSV files, existing database files, and the verified `isolation_forest_v1` production model bundle were strictly preserved. No raw data was modified. No Git commits, pushes, or branch operations were performed. All metrics for supervised classifiers are explicitly documented as **held-out synthetic scenario performance**, never fabricated as real-world e-commerce fraud accuracy.

---

## 1. What Was Already Working vs What Was Implemented

### What Was Already Working
1. **Historical Source Dataset & Runtime Database:** Lineage from `C:\end sem project\archive (5)` with 25,606,940 historical records (9,980 products, 5 platforms, 7 categories) from 2023-01-01 through 2024-12-30, indexed in `artifacts/derived/fakedeal_runtime.duckdb`.
2. **Production Isolation Forest Anomaly Detector:** Active bundle `artifacts/ml/isolation_forest_v1/` with canonical 4-feature vector (`msrp_to_30d_avg`, `ratio_to_30d_avg`, `price_volatility_30d`, `recent_7d_surge`), RobusterScaler/StandardScaler preprocessing, and SHA-256 checksum verification.
3. **Core FastAPI Backend:** Internal 5-field endpoint `POST /api/analyze`, `GET /api/catalog`, `GET /api/catalog/metadata`, `GET /api/catalog/search`, `POST /api/inspect`, `POST /api/forecast`, and `GET /api/models/synthetic-comparison`.
4. **Conditional 14-Day Baseline Forecasting:** Requiring 180 consecutive daily observations before `as_of`, 5-window rolling-origin backtest, and selection by minimum RMSE then MAE.
5. **Basic FDI Heuristic Structure:** 4-component formulation that correctly yields `INSUFFICIENT_INPUTS` when live anomaly inputs are missing.

### What Was Implemented / Enhanced in This Turn
1. **Three Distinguished Assessment Verdict States:**
   - Formalized and strictly integrated the three assessment states into both backend schemas and frontend presentation:
     1. `Potential Suspicious Discount Pattern` (Isolation Forest anomaly detected relative to 30-day baseline)
     2. `No Suspicious Pattern Detected` (price and discount conform to normal historical patterns)
     3. `Insufficient Evidence` (<14 observed days available before check date)
   - Added `assessment_verdict` and `assessment_explanation` fields to `AnalyzeResponse` (`backend/app/schemas/response.py`), `AnalysisService` (`backend/app/services/analysis_service.py`), and `/api/inspect` (`backend/app/main.py`).
2. **Frontend Assessment Verdict Display:**
   - Created prominent, specialized **Overall Discount Assessment Card** at the top of results in `frontend/src/App.jsx`.
   - Integrated status badges (`.ml-status-badge.anomaly`, `.normal`, `.inconclusive`) with descriptive text explaining that these are statistical assessments, not legal fraud judgments.
3. **Frontend Supervised Model Comparison Display:**
   - Implemented `ModelComparisonView` in `frontend/src/App.jsx` and added `loadSyntheticModelComparison` in `frontend/src/services/api.js`.
   - Wired navigation links in Navbar, Landing Page, and directly inside the Inspector's Synthetic Scenario Classifier card.
   - Built benchmark performance table (Threshold, Precision, Recall, F1, ROC-AUC, PR-AUC, Gini, False-Positive Rate) and confusion matrices side-by-side for Logistic Regression vs Random Forest.
   - Added clear explanations of the validation-constrained selection rule and academic disclaimers.
4. **Comprehensive Automated Verification & Testing:**
   - Created `scripts/test_end_to_end.py` verifying all 5 required demonstration workflows against the live FastAPI app and DuckDB database.
   - Created `scripts/test_live_server.py` verifying real Uvicorn server startup, HTTP health probing, catalog metadata retrieval, and clean termination.
   - Added backend tests for the 3 distinguished verdict states (`backend/tests/test_product_inspection.py`).
   - Added frontend unit tests for verdict mapping and model comparison API client (`frontend/tests/api.test.js`).
   - Ran all ML (117), backend (57), frontend (29), end-to-end (5/5), live server, production build, and lint checks.

---

## 2. Modified Files

| File | Type | Changes Made |
|---|---|---|
| `backend/app/schemas/response.py` | Modified | Added `assessment_verdict` and `assessment_explanation` fields to `AnalyzeResponse`. |
| `backend/app/services/analysis_service.py` | Modified | Evaluated and populated `assessment_verdict` and `assessment_explanation` across all 3 assessment states while preserving `verdict=None` when FDI is incomplete. |
| `backend/app/main.py` | Modified | Exposed `assessment_verdict` and `assessment_explanation` in `/api/inspect` wrapper dictionary. |
| `backend/tests/test_product_inspection.py` | Modified | Added tests verifying all 3 distinguished assessment verdict states on `/api/inspect`. |
| `frontend/src/services/api.js` | Modified | Added `loadSyntheticModelComparison()` API client function. |
| `frontend/src/services/presentation.js` | Modified | Added `getAssessmentVerdict(analysis)` presentation helper. |
| `frontend/src/App.jsx` | Modified | Added `ModelComparisonView`, overall assessment card, benchmark details button, navbar/footer navigation, and updated feature descriptions. |
| `frontend/src/App.css` | Modified | Added styling classes for `.assessment-verdict-card`, `.comparison-table`, and `.confusion-matrix-grid`. |
| `frontend/tests/api.test.js` | Modified | Added unit tests for `getAssessmentVerdict` and `loadSyntheticModelComparison`. |
| `scripts/test_end_to_end.py` | Added | End-to-end integration test verifying the 5 mandatory evaluation workflows. |
| `scripts/test_live_server.py` | Added | Live Uvicorn server startup and HTTP probe test. |
| `README.md` | Modified | Comprehensive documentation of working system, commands, architecture, and academic disclaimer. |
| `backend/API_CONTRACT.md` | Modified | Documented `assessment_verdict` and `assessment_explanation` response schema. |
| `docs/api-documentation.md` | Modified | Updated route documentation with the three assessment states. |
| `docs/model-comparison-report.md` | Modified | Added full confusion matrices, Gini formulas, metrics table, and selection rationale. |
| `docs/testing-report.md` | Modified | Updated with latest test counts (203 unit/integration tests, E2E suite, live server probe). |
| `FINAL_IMPLEMENTATION_REPORT.md` | Modified | Complete end-of-turn report for Prompt 1. |

---

## 3. Dataset Engineering & Synthetic Scenarios

- **Original Kaggle Dataset:** 25,606,940 historical records across three splits from 2023-01-01 through 2024-12-30. 9,980 product IDs, 5 platforms (Amazon, Best Buy, eBay, Flipkart, Walmart), 7 categories (Appliances, Books, Electronics, Fashion, Gaming, Household, Sports).
- **Label Audit Finding:** `fake_discount_flag` has 0 positives (constant 0). `price_spike_flag` has 48,554 positives but measures sudden price spikes, not fake discounts. Neither can be treated as fake-discount ground truth.
- **Teacher Approval:** Teacher explicitly approved generating synthetic data for the academic demonstration.
- **Generated Synthetic Dataset:**
  - Artifact path: `artifacts/synthetic/discount_scenarios_v1/`
  - Generator script: `scripts/generate_synthetic_discount_dataset.py` (seed: `20261118`)
  - Sampled reference profiles: 60,000 valid rows sampled via DuckDB reservoir sampling from original training split (selecting only observed price/feature ranges, no IDs or target flags).
  - Total rows: **40,000 balanced rows** (50% genuine discount, 50% artificially inflated reference price).
  - Class 0 (`SYNTHETIC_GENUINE_DISCOUNT`): Current price sampled from below-average ratios (0.2–1.0x); discount magnitude sampled from observed discounts (3–75%).
  - Class 1 (`SYNTHETIC_ARTIFICIALLY_INFLATED_DISCOUNT`): Current price stays near observed historical baseline (0.85–1.20x); original reference price is artificially inflated by 1.10–1.55x.
  - Split sizes:
    - **Train (70%):** 28,000 rows (14,000 Class 0 / 14,000 Class 1)
    - **Validation (15%):** 6,000 rows (3,000 Class 0 / 3,000 Class 1)
    - **Held-Out Test (15%):** 6,000 rows (3,000 Class 0 / 3,000 Class 1)
  - Data integrity: Independent stratified splitting, no profile reuse across rows, all split checksums verified via SHA-256 in `manifest.json`.

---

## 4. Machine Learning Pipeline Verification

### A. Production Isolation Forest (`isolation_forest_v1`)
- **Status:** Checksums verified, fresh process load verified, canonical feature order verified.
- **Features (Strict Order):** `msrp_to_30d_avg`, `ratio_to_30d_avg`, `price_volatility_30d`, `recent_7d_surge`.
- **Pretrained Artifacts:** `isolation_forest.joblib`, `preprocessor.json`, `metadata.json`, `verification_fixture.json`, `checksums.sha256`.
- **Validation Check:** Executed `scripts/validate_final_model.py`:
  - `checksums_verified: true`
  - `fresh_process_load_verified: true`
  - Output fixture prediction matches stored validation baseline: `is_anomaly: false`, `anomaly_score: -0.2097`.
  - Chronological held-out flag rate: 1.5357% (unsupervised anomaly rate, not fraud accuracy).

### B. Supervised Experiment: Logistic Regression vs Random Forest
- **Artifacts:** `artifacts/ml/synthetic_discount_v1/`
- **Features Used (Both Models):** Identical 7-feature vector (`msrp_to_30d_avg`, `ratio_to_30d_avg`, `price_volatility_30d`, `recent_7d_surge`, `advertised_discount_pct`, `platform`, `category`).
- **Data Leakage Prevention:** Preprocessor (median imputer, one-hot encoder, standard scaler for LR) fit strictly on the 28,000-row training set.
- **Validation Selection Rule:** Maximize recall on artificially inflated discounts while strictly constraining false-positive rate on genuine discounts to $\le 10\%$.
- **Held-Out Test Set Performance (N = 6,000):**

| Metric | Logistic Regression (Baseline) | Random Forest (Selected) | Delta |
|---|---:|---:|---:|
| **Optimal Threshold** | 0.6800 | **0.4100** | Tuned on validation |
| **Precision** | 0.8799 | **0.8954** | +0.0155 (+1.76%) |
| **Recall (Sensitivity)** | 0.6670 | **0.7360** | +0.0690 (+10.34%) |
| **F1-Score** | 0.7588 | **0.8079** | +0.0491 (+6.47%) |
| **ROC-AUC** | 0.8891 | **0.9160** | +0.0269 (+3.03%) |
| **PR-AUC (Average Precision)** | 0.9019 | **0.9308** | +0.0289 (+3.20%) |
| **Gini ($2 \times \text{ROC-AUC} - 1$)** | 0.7782 | **0.8320** | +0.0538 (+6.91%) |
| **FPR on Synthetic Genuine** | 0.0910 | **0.0860** | -0.0050 (Lower is better) |

### Confusion Matrices (Test N = 6,000; 3,000 Genuine / 3,000 Inflated):
- **Logistic Regression:**
  - True Negatives (TN): `2,727`
  - False Positives (FP): `273` (FPR = 9.10%)
  - False Negatives (FN): `999`
  - True Positives (TP): `2,001` (Recall = 66.70%)
- **Random Forest (Selected):**
  - True Negatives (TN): `2,742`
  - False Positives (FP): `258` (FPR = 8.60%)
  - False Negatives (FN): `792` (207 fewer missed inflated discounts)
  - True Positives (TP): `2,208` (Recall = 73.60%)

---

## 5. Discount Fraud Indicator (FDI) Status & Limitations

- **Audit Finding:** FDI is a 4-component provisional heuristic ($0.35 S_{\text{gap}} + 0.30 S_{\text{mean\_ratio}} + 0.20 S_{\text{msrp\_inflation}} + 0.15 S_{\text{anomaly}}$).
- **Signal Availability:**
  - $S_{\text{gap}}$, $S_{\text{mean\_ratio}}$, $S_{\text{msrp\_inflation}}$ can be calculated when historical observations exist.
  - $S_{\text{anomaly}}$ requires `price_spike_flag` and `pre_discount_hike_ratio`. Neither is computable at live inference time from the approved dataset.
- **Honest Handling (Rule 9):**
  - The implementation **never fabricates** missing inputs, zeroes, or risk levels.
  - Returns `status: "INSUFFICIENT_INPUTS"` with `fdi_score: null` and `provisional_level: null`.
  - Explains exactly which inputs are missing (`missing_inputs: ["price_spike_flag", "pre_discount_hike_ratio"]`).
  - Partial diagnostic component scores remain visible inside the `fdi` object for transparency.

---

## 6. 14-Day Price Forecast Validation

- **Implementation:** `backend/app/services/forecast_service.py`
- **Methodology:** Requires 180 consecutive daily observations before `as_of`. Missing dates are never filled, forward-filled, or interpolated.
- **Backtesting:** Evaluates flat last-observation and trailing-7-day-mean baselines across 5 chronological rolling-origin windows (70 test points). Selects the best baseline by RMSE then MAE.
- **Output:** Returns 14 projected daily points with baseline values, reference date, training observation count, and backtest MAE/RMSE.
- **Stale/Insufficient Handling:**
  - For current 2026 dates (dataset ends 2024-12-30), returns `status: "INSUFFICIENT_HISTORY"` and `forecast: null`.
  - Never promises or guarantees future prices; includes explicit research disclaimer.

---

## 7. Product Input & 3-State Verdict Logic

- **Supported Fields:** Product name, platform (Amazon, Best Buy, eBay, Flipkart, Walmart), category (7 categories), original price, current price.
- **Optional Fields:** Seller name (unverified), seller rating (unverified; 1.0–5.0), product URL (optional HTTP/HTTPS).
- **Exact Identifier Resolution:** Amazon `/dp/<ASIN>` URLs resolve only when the ASIN, title, category, and platform match exact dataset records. Other URLs are validated as listing metadata without verifying identity.
- **No Silent Substitution:** If a product name or category is not found, returns HTTP 404 `PRODUCT_NOT_FOUND` rather than guessing or silently substituting another product.
- **Three Distinguished Verdict States:**
  1. `Potential Suspicious Discount Pattern`: Isolation Forest flags an anomaly relative to historical baseline.
  2. `No Suspicious Pattern Detected`: Current price and discount conform to normal historical patterns.
  3. `Insufficient Evidence`: Fewer than 14 observations in 30 days or future date beyond dataset range.

---

## 8. Summary of Automated Testing

| Test Suite | Total Executed | Passed | Failed | Status |
|---|---:|---:|---:|---|
| Central ML Pytest (`tests/`) | 117 | 117 | 0 | **PASSED** |
| Backend Pytest (`backend/tests/`) | 57 | 57 | 0 | **PASSED** |
| Frontend Node Test (`frontend/tests/`) | 29 | 29 | 0 | **PASSED** |
| End-to-End Suite (`scripts/test_end_to_end.py`) | 5 | 5 | 0 | **PASSED** |
| Live Server Startup & Probe (`scripts/test_live_server.py`) | 1 | 1 | 0 | **PASSED** |
| Frontend Production Build (`npm.cmd run build`) | 1 | 1 | 0 | **PASSED** |
| Frontend Oxlint (`npm.cmd run lint`) | 9 files | 0 errors | 0 warnings | **PASSED** |
| **Total Automated Tests** | **203** | **203** | **0** | **100% PASS** |

---

## 9. Startup Commands

### Terminal 1 — FastAPI Backend (from repository root):
```powershell
$env:PYTHONPATH = "backend"
& "C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe" -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

### Terminal 2 — React/Vite Frontend:
```powershell
Set-Location "C:\end sem project\FAKEDEAL-BUSTER\frontend"
npm.cmd run dev
```
Open `http://localhost:5173` in a web browser.

---

## 10. Recommended Academic Demonstration Sequence

1. **Verify Services & Health:**
   - Open `http://127.0.0.1:8000/health`. Confirm `status: "healthy"`, database available, model bundle present.
2. **Demonstrate Product Search & Normal Price Conformity:**
   - In Product Inspector (`http://localhost:5173/#inspector`), search `Google Max Smartphones`. Select `Google Max Smartphones  (Green) · Electronics · amazon`.
   - Enter Original Price: `239.02`, Current Price: `203.62`.
   - Check `Historical analysis` checkbox. Select `2024-10-18T00:00`.
   - Submit form.
   - **Show Output:**
     - Overall Assessment: `No Suspicious Pattern Detected`.
     - Isolation Forest: `NO_ANOMALY` (score: -0.1576).
     - Actual price history chart with 30-day recorded points.
     - 14-day conditional price forecast curve with backtest validation.
     - FDI honest status: `INSUFFICIENT_INPUTS` (clean explanation of missing live signals).
3. **Demonstrate Artificial Reference-Price Inflation Detection:**
   - Retain product and date (`2024-10-18T00:00`). Change Original Price to `850.00` and Current Price to `50.00` (extreme artificial markup).
   - Submit form.
   - **Show Output:**
     - Overall Assessment: `Potential Suspicious Discount Pattern`.
     - Isolation Forest: `ANOMALY`.
     - Synthetic Classifier: `Resembles the generated artificial-inflation scenario`.
4. **Demonstrate Insufficient History / Out-of-Bounds Date Handling:**
   - Uncheck historical mode (uses current 2026 date) or enter `2026-11-18`.
   - Submit form.
   - **Show Output:**
     - Overall Assessment: `Insufficient Evidence`.
     - Analysis Status: `NEEDS_MORE_DATA`.
     - Forecast Status: `INSUFFICIENT_HISTORY`.
     - Demonstrates that the system never fabricates data or uses stale prices as current.
5. **Demonstrate Supervised Model Comparison Benchmark (LR vs RF):**
   - Click **Model Comparison** in the top navigation bar or **View Supervised Model Benchmark** inside the Synthetic Scenario card.
   - **Show Output:**
     - Side-by-side performance table for Logistic Regression vs Random Forest.
     - Validation-selected threshold (0.4100 for Random Forest) under the 10% FPR constraint.
     - Confusion matrices for both models on 6,000 held-out test examples.
     - Academic disclaimer confirming these reflect synthetic held-out performance, not real fraud ground truth.
6. **Demonstrate Input Validation & Error Handling:**
   - Enter Current Price > Original Price -> Form blocks submission with inline validation error.
   - Enter invalid seller rating (e.g. 6.0) or invalid URL -> Validation error displayed.
   - Submit an unknown product name -> API returns HTTP 404 `PRODUCT_NOT_FOUND` without silently substituting another product.

---

## 11. Remaining Issues & Known Limitations

1. **Simulated Source Data:** The original Kaggle dataset is synthetically generated by its creator; `fake_discount_flag` contains 0 positive examples. True marketplace fraud ground truth does not exist in this data.
2. **Dataset Time Boundary:** The dataset observations terminate on 2024-12-30. Real-time analysis for current 2026 dates correctly returns `NEEDS_MORE_DATA`.
3. **Web Scraping:** Live scraping of active marketplace listings is omitted in Prompt 1 as approved by the mentor; integration with live web feeds remains future scope.
4. **FDI Incompleteness:** Full composite FDI scoring remains unavailable for production listings because `price_spike_flag` and `pre_discount_hike_ratio` are not derivable at inference time.
5. **Visual Styling Redesign:** Preserved the current layout and focused on complete functional and ML correctness; the final visual theme redesign will be performed in Prompt 2.
