# FakeDeal Buster — Final Project Audit

**Audit date:** 2026-11-18 · **Mode:** read-only; no tests or expensive scans run in this audit.

## 1. Overall readiness

**PARTIALLY READY — core historical anomaly analysis is integrated; major PRD features remain missing or cannot be truthfully implemented from the current label.** No percentage is assigned because the PRD has conditional and scientifically incompatible requirements.

## 2. Repository inventory

- `frontend/src/App.jsx`, `App.css`, `services/{api,productValidation,presentation}.js`: React/Vite landing page, product inspector, client validation, API mapping, results and actual-price chart. `frontend/tests/`: three Node test files. `frontend/vite.config.js`: `/api` development proxy.
- `backend/app/main.py`: FastAPI routes. `schemas/{request,inspection,response}.py`: internal five-field and user inspection contracts. `services/{product_catalog_service,history_service,analysis_service,ml_adapter}.py`: catalogue resolution, DuckDB history, analysis orchestration and central-ML adapter. `backend/tests/`: four test files.
- `ml/{data_loader,feature_extractor,preprocessor,isolation_forest,inference,service,fdi,train_pipeline}.py`: data utilities, four numerical features, scaler, Isolation Forest, verified inference/service and provisional FDI. No classifier or forecast implementation found.
- `scripts/`: model train/evaluate/validate/demo scripts and `build_runtime_store.py`. `tests/`: six central ML test modules. `artifacts/ml/isolation_forest_v1/`: six-file verified bundle (`isolation_forest.joblib`, `preprocessor.json`, metadata, validation summary, fixture, SHA-256 manifest). `artifacts/derived/fakedeal_runtime.duckdb`: local production history/catalogue store with `observations`, `products`, `product_platforms`, and `store_metadata`.
- Database: local DuckDB, not a separate database server. No migrations/ORM. No forecast endpoint. The frontend’s forecast component is an explicit unavailable placeholder, not a prediction.
- Relevant evidence: `docs/day-1-dataset-and-label-audit.md`, `docs/day-1-ml-feasibility-decision.md`, `docs/day-1-target-leakage-assessment.md`, `docs/ml-training-report.md`, `docs/ml-test-evaluation-report.md`, `backend/API_CONTRACT.md`.

**Absent implementation modules:** supervised classifier training/evaluation; 14-day forecast service/route/schema; seller identity verification; browser-driven frontend/backend E2E tests. The forecast UI is an explicit unavailable placeholder. No live marketplace integration exists.

## 3. Dataset audit

The requested `C:\end sem project\dataset` path is absent. The handoff manifest and derived-store metadata identify `C:\end sem project\archive (5)` as the source; the app uses its three chronological split files through the derived DuckDB store. The compact P0000001 CSV is an integration extract, not the production catalogue.

Source metadata/schema report: **25,606,940 rows, 46 columns**, 9,980 observed IDs, 35,078 product/platform pairs, five platforms, seven categories, daily timestamps from **2023-01-01 to 2024-12-30**. Split row counts: train 20,450,474; validation 2,560,694; test 2,595,772. The existing quality audit reports no duplicate keys and no missing/nonpositive core prices. Expected early-window rolling-feature nulls are excluded by feature eligibility; no imputer is present.

Schema types from `schema_report.md`: strings: `product_id`, `title`, `brand`, `category`, `subcategory`, `platform`, `stock_status`, `asin`; timestamp: `timestamp`; numeric (`DOUBLE`): `year`, `month`, `day`, `dayofweek`, `price`, `original_price`, `discount_pct`, `avg_rating`, `review_count`, `is_flagship`, `launch_year`, `price_change_abs`, `price_change_pct`, `price_7d_avg`, `price_30d_avg`, `price_7d_std`, `price_30d_std`, `price_7d_min`, `price_30d_min`, `price_7d_max`, `price_30d_max`, `price_52w_min`, `price_52w_max`, `price_volatility_30d`, `discount_vs_30d_avg`, `is_all_time_low`, `is_all_time_high`, `popularity_score`, `fake_discount_flag`, `price_spike_flag`, `is_black_friday_week`, `is_holiday_season`, `is_weekend`, `value_score`, `target_price_7d`, `target_price_30d`, `target_price_direction_7d`.

The existing **2,086,416,384-byte** DuckDB metadata reports the same source root/version/row count and date span, five platforms/seven categories, and `url_mapping_available`, `seller_name_available`, `seller_rating_available` all false. Tables: `observations`, `products`, `product_platforms`, `store_metadata`.

Identity/pricing fields include product ID, title, brand, category/subcategory, platform, ASIN, timestamp, current/original prices, discount percentage, product average rating, review count, and historical statistics. There are **no product URLs, seller names, or seller ratings**; product `avg_rating` is not seller rating. Amazon ASIN is the only implemented URL identity mapping (exact supported Amazon path/ASIN plus metadata match).

The source README describes simulated retail behavior; the dataset is not verified real marketplace evidence. Existing full-census audit reports `fake_discount_flag`: **0 positive / 25,606,940 negative**, with undocumented label-generation logic. `price_spike_flag` has 48,554 positives, but is a different anomaly signal and not fake-discount ground truth. No independently verified fraud labels exist. A second dataset is **not required for the defensible anomaly/price-history app**, but a meaningful supervised fake-discount comparison and its PRD metrics require valid independent labels; this dataset cannot supply them.

Two years of actual histories and source future targets `target_price_7d`/`target_price_30d` make forecasting research possible in principle. There is no 14-day target or forecast model/backtest in the project. Forecasting therefore remains unverified and unavailable; do not treat future target fields as live inputs.

## 4. Requirement status

| PRD requirement | Status | Evidence / gap |
|---|---|---|
| Product inspector: details, prices, platform/category, seller info, URL | **PARTIAL** | Form has name/platform/category/prices and optional seller name/rating/URL. Seller fields are metadata only; no seller data or verification exists. URL identity works only for exact Amazon ASIN mapping. |
| Cleaning, missing values, categorical encoding, feature engineering, outlier detection | **PARTIAL** | Pipeline filters invalid/ineligible history and engineers four numerical features; Isolation Forest is outlier detection. No general categorical encoding or imputation pipeline; categories are not model inputs. |
| Logistic Regression vs Random Forest if labels suitable | **MISSING / NOT SUITABLE** | Neither classifier is implemented. `fake_discount_flag` is constant zero per existing full-census report; `price_spike_flag` is not a valid substitute. |
| Precision, Recall, F1, confusion matrix, ROC-AUC, Gini where valid | **NOT VALID** | No valid binary ground truth. Reports correctly omit classifier metrics. |
| FastAPI and Joblib serialization | **COMPLETE** | FastAPI routes and a Joblib Isolation Forest artifact exist in a checksum-verified bundle. The fitted scaler is a separate JSON artifact, not one serialized sklearn Pipeline. |
| Verdict “Verified Real Deal” / “Potential Fake Discount” | **MISSING (intentionally safe)** | UI displays “Price anomaly detected” / “No price anomaly detected.” Neither proves genuine/fake; PRD wording conflicts with its no-fraud-proof requirement. |
| Conditional 14-day price-drop forecast | **MISSING** | No forecast route/model; response is `forecast: null`, `UNAVAILABLE`; UI states unavailable. Dataset has histories and 7d/30d targets, not a validated 14d forecast. |
| Insufficient-data and uncertainty messages | **COMPLETE for current analysis** | Central inference returns `NEEDS_MORE_DATA` with null prediction fields; frontend maps this and FDI `INSUFFICIENT_INPUTS`. |
| No claim anomaly/synthetic labels prove fraud | **COMPLETE** | ML explanations and UI disclaimers explicitly state anomaly is not proof; reports reject accuracy claims. |

## 5. ML and backend findings

- Active model: `isolation_forest_v1`, Isolation Forest (200 estimators, contamination 0.01, seed 20261117 per artifact metadata). Training used 100,000-row deterministic reservoir from train features; preprocessing fit on training rows; validation and test are chronological. No random time-series split identified.
- Canonical feature order is verified in metadata/inference: `msrp_to_30d_avg`, `ratio_to_30d_avg`, `price_volatility_30d`, `recent_7d_surge`. Inference verifies checksums, metadata and feature order and applies the saved scaler before the detector. Backend lazily loads `ml.service` and supplies actual prior observations. Central minimum: 14 distinct dates in 30 days and at least one in 7 days; strict prior cut-off; no interpolation.
- Test-split report gives **1.5357% anomaly rate** (39,864/2,595,772); validation rate **1.1857%**. These are detector rates, not accuracy or fraud prevalence. Precision/recall/F1/ROC-AUC/confusion matrix/Gini are absent and invalid without suitable labels.
- FDI is a separate provisional weighted heuristic (`S_gap` .35, `S_mean_ratio` .30, `S_msrp_inflation` .20, `S_anomaly` .15; proposed bands LOW/MODERATE/HIGH/CRITICAL). Live `price_spike_flag` and `pre_discount_hike_ratio` are unavailable/undefined, so current FDI status is `INSUFFICIENT_INPUTS`, total and level null. Weights/bands are not validated.
- Routes: `GET /`, `GET /health`, `GET /api/catalog`, `GET /api/catalog/search`, `POST /api/inspect`, `POST /api/analyze`. `/api/analyze` has the five-field request. `/api/inspect` resolves name/platform/category and adapts to it. No 14-day forecast route. `/health` is process-only and can say healthy even if database/artifacts are unavailable.
- Catalogue search API accepts query/category/platform filters; frontend instead loads the full product list into a datalist. The platform options narrow after exact title match, but category options remain global; an incompatible category is rejected by backend rather than filtered in the UI. The derived database is local/ignored and must be built from the source before first run.
- URL schemes are HTTP(S)-validated; recognized domains must match selected platform; Amazon ASIN resolution is exact. There is no scraping or seller verification. Errors are structured. Current-time analysis in 2026 has no matching recent history because source ends 2024 and should return `NEEDS_MORE_DATA`.

## 6. Frontend and tests

The UI renders backend product metadata, prices/discount, actual 365-day observation points and summaries, cross-platform observations, the real ML anomaly object, and separate FDI state. Forecast is an explicit placeholder. Loading, retry, input errors, API/network errors and duplicate-submit prevention are present. No supervised verdict or fraud probability is rendered. The landing-page statistic still says “4 Marketplaces” although the actual catalogue has five; its floating price cards are explicitly marked illustrative. Browser/mobile rendering was not verified in this audit.

Test files exist: six ML, four backend, three frontend. `docs/testing-report.md` still says pending. Prior project verification records 113 ML, 47 backend, and 25 frontend tests passing, plus frontend build/lint; this audit did not rerun them. `docs/ml-test-evaluation-report.md` is an anomaly test-split evaluation report, not a current pytest run log.

## 7. Top 10 gaps by priority

1. Resolve PRD verdict conflict: retain anomaly wording unless approved genuine fraud labels support “Verified Real Deal” / “Potential Fake Discount.”
2. Make setup/health readiness check the required local database and model artifacts; document missing `C:\end sem project\dataset` vs available `archive (5)` source.
3. Add product-specific category filtering and use bounded `/api/catalog/search` for suggestions; avoid invalid combinations.
4. Decide supervised-classifier requirement: with this label, document non-applicability; do not fit meaningless LR/RF models. A verified label source would be needed if comparison is mandatory.
5. Implement the conditional 14-day forecast only with a chronological backtest and baseline comparison; otherwise keep unavailable and explicitly mark PRD partial.
6. Replace “seller verification” expectations with metadata-only language or obtain actual supported seller data; current fields cannot verify seller identity/rating.
7. Add backend/API integration test coverage for full catalogue behavior and errors; add a real browser UI smoke test at desktop/mobile sizes.
8. Update `docs/testing-report.md` from pending to actual suite statuses and distinguish anomaly rates from classifier metrics.
9. Correct the landing-page marketplace count from four to the five supported values.
10. Reconcile duplicate/stale statements in `backend/API_CONTRACT.md` with actual route behavior; keep FDI provisional/unavailable and never substitute anomaly scores or dataset-only labels for its missing inputs.

## 8. Shortest implementation order and demo risks

1. Confirm safe verdict language and document classifier infeasibility. 2. Make database/model readiness and dataset setup deterministic. 3. Fix product/category search filtering. 4. Decide whether to defer or build/backtest 14-day forecasting. 5. Update test report and run focused backend/frontend integration/browser checks.

**Demo risks:** default current-date inspection necessarily lacks recent history; the local derived DB is not portable unless rebuilt; product/category mismatches can reach an API error; browser/mobile E2E is not recorded; literal PRD fraud verdicts and classifier metrics cannot be defended with these labels. Use a historical date within 2023–2024 for a model demonstration, and describe the output as anomaly analysis, not fraud detection.
