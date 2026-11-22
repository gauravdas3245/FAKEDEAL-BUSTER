# PHASE 1: LOCAL PROJECT FILE INVENTORY & AUDIT
**Project Root:** `C:\end sem project\FAKEDEAL-BUSTER`  
**Date of Audit:** 22 November 2026  
**Mode:** Read-Only Inventory & Categorization  

---

## 1. Inventory Summary & File Classification

- **Total Non-Vendor Application Files Audited:** 294 files
- **Git-Tracked Files:** 27 files
- **Untracked Core Files:** 267 files
- **Vendor / Virtual Environment Footprint (Excluded from Git):**
  - `.venv/` (Python virtual environment): ~13,600 files (~150 MB)
  - `frontend/node_modules/` (Node.js dependencies): ~600 files (~80 MB)
  - `Hand-over/saniya hand-over/project/node_modules/`: Redundant duplicate node_modules (~80 MB)
  - `Hand-over/saniya hand-over/project/.git/`: Redundant nested Git repository (~5 MB)

---

## 2. Large Files Audit (> 10 MB)

| File Relative Path | Size | Git Policy & Push Readiness |
|---|---|---|
| `artifacts/derived/fakedeal_runtime.duckdb` | **1989.76 MB** | CRITICAL BLOCKER: Exceeds GitHub 100MB limit. MUST BE IGNORED via `.gitignore`. |
| `Hand-over/saniya hand-over zip.zip` | **22.21 MB** | WARNING: Large binary archive (>10MB). Exclude from Git. |

---

## 3. Duplicate Filename Analysis & Content Collision

The following filenames occur multiple times across project directories:

| Filename | Occurrences | Locations & Content Assessment |
|---|:---:|---|
| `.env.example` | 4 | `.env.example`<br>`frontend/.env.example`<br>`Hand-over/rahul hand-over/.env.example`<br>`Hand-over/saniya hand-over/project/.env.example` |
| `.gitignore` | 6 | `.gitignore`<br>`.pytest_cache/.gitignore`<br>`frontend/.gitignore`<br>`Hand-over/rahul hand-over/.gitignore`<br>`Hand-over/saniya hand-over/project/.gitignore`<br>`tests/.pytest_cache/.gitignore` |
| `.oxlintrc.json` | 2 | `frontend/.oxlintrc.json`<br>`Hand-over/saniya hand-over/project/.oxlintrc.json` |
| `API_CONTRACT.md` | 2 | `backend/API_CONTRACT.md` (14.5 KB production integrated)<br>`Hand-over/rahul hand-over/API_CONTRACT.md` (11.4 KB early draft) |
| `App.css` | 2 | `frontend/src/App.css` (78.6 KB enhanced UI styling)<br>`Hand-over/saniya hand-over/project/src/App.css` (36.3 KB base handover) |
| `App.jsx` | 2 | `frontend/src/App.jsx` (71.9 KB full integrated interface)<br>`Hand-over/saniya hand-over/project/src/App.jsx` (44.8 KB base handover) |
| `CACHEDIR.TAG` | 2 | `.pytest_cache/CACHEDIR.TAG`<br>`tests/.pytest_cache/CACHEDIR.TAG` |
| `README.md` | 12 | `README.md`<br>`.pytest_cache/README.md`<br>`artifacts/rahul_dataset_handoff/README.md`<br>`assets/README.md`<br>`backend/README.md`<br>`dataset/README.md`<br>`frontend/README.md`<br>`Hand-over/rahul hand-over/README.md`<br>`Hand-over/saniya hand-over/project/README.md`<br>`ml/README.md`<br>`tests/README.md`<br>`tests/.pytest_cache/README.md` |
| `analysis_service.py` | 2 | `backend/app/services/analysis_service.py` (4.53 KB)<br>`Hand-over/rahul hand-over/app/services/analysis_service.py` (4.59 KB) |
| `api.js` | 2 | `frontend/src/services/api.js` (5.46 KB production client)<br>`Hand-over/saniya hand-over/project/src/services/api.js` (6.67 KB base client) |
| `api.test.js` | 2 | `frontend/tests/api.test.js`<br>`Hand-over/saniya hand-over/project/tests/api.test.js` |
| `checksums.sha256` | 2 | `artifacts/ml/isolation_forest_v1/checksums.sha256`<br>`artifacts/ml/synthetic_discount_v1/checksums.sha256` |
| `exceptions.py` | 2 | `backend/app/exceptions.py` (1.77 KB)<br>`Hand-over/rahul hand-over/app/exceptions.py` (1.44 KB) |
| `favicon.svg` | 4 | `frontend/dist/favicon.svg`<br>`frontend/public/favicon.svg`<br>`Hand-over/saniya hand-over/project/dist/favicon.svg`<br>`Hand-over/saniya hand-over/project/public/favicon.svg` |
| `hero.png` | 2 | `frontend/src/assets/hero.png`<br>`Hand-over/saniya hand-over/project/src/assets/hero.png` |
| `history_service.py` | 2 | `backend/app/services/history_service.py` (6.04 KB)<br>`Hand-over/rahul hand-over/app/services/history_service.py` (6.08 KB) |
| `icons.svg` | 2 | `Hand-over/saniya hand-over/project/dist/icons.svg`<br>`Hand-over/saniya hand-over/project/public/icons.svg` |
| `index.css` | 2 | `frontend/src/index.css`<br>`Hand-over/saniya hand-over/project/src/index.css` |
| `index.html` | 4 | `frontend/index.html`<br>`frontend/dist/index.html`<br>`Hand-over/saniya hand-over/project/index.html`<br>`Hand-over/saniya hand-over/project/dist/index.html` |
| `lastfailed` | 2 | `.pytest_cache/v/cache/lastfailed`<br>`tests/.pytest_cache/v/cache/lastfailed` |
| `main.jsx` | 2 | `frontend/src/main.jsx`<br>`Hand-over/saniya hand-over/project/src/main.jsx` |
| `main.py` | 2 | `backend/app/main.py` (12.35 KB integrated app)<br>`Hand-over/rahul hand-over/app/main.py` (4.32 KB prototype) |
| `manifest.json` | 2 | `artifacts/rahul_dataset_handoff/manifest.json`<br>`artifacts/synthetic/discount_scenarios_v1/manifest.json` |
| `metadata.json` | 2 | `artifacts/ml/isolation_forest_v1/metadata.json`<br>`artifacts/ml/synthetic_discount_v1/metadata.json` |
| `nodeids` | 2 | `.pytest_cache/v/cache/nodeids`<br>`tests/.pytest_cache/v/cache/nodeids` |
| `p0000001_all_splits.csv` | 2 | `artifacts/rahul_dataset_handoff/p0000001_all_splits.csv`<br>`Hand-over/rahul hand-over/data/p0000001_all_splits.csv` |
| `package-lock.json` | 2 | `frontend/package-lock.json`<br>`Hand-over/saniya hand-over/project/package-lock.json` |
| `package.json` | 3 | `frontend/package.json`<br>`frontend/.vite-cache/deps/package.json`<br>`Hand-over/saniya hand-over/project/package.json` |
| `request.py` | 2 | `backend/app/schemas/request.py`<br>`Hand-over/rahul hand-over/app/schemas/request.py` |
| `requirements.txt` | 2 | `requirements.txt` (Root unified)<br>`Hand-over/rahul hand-over/requirements.txt` |
| `response.py` | 2 | `backend/app/schemas/response.py`<br>`Hand-over/rahul hand-over/app/schemas/response.py` |
| `test_api.py` | 2 | `backend/tests/test_api.py`<br>`Hand-over/rahul hand-over/tests/test_api.py` |
| `test_features.py` | 2 | `backend/tests/test_features.py`<br>`Hand-over/rahul hand-over/tests/test_features.py` |
| `test_history.py` | 2 | `backend/tests/test_history.py`<br>`Hand-over/rahul hand-over/tests/test_history.py` |
| `test_synthetic_classifier.py` | 2 | `backend/tests/test_synthetic_classifier.py`<br>`tests/test_synthetic_classifier.py` |
| `validation.test.js` | 2 | `frontend/tests/validation.test.js`<br>`Hand-over/saniya hand-over/project/tests/validation.test.js` |
| `vite.config.js` | 2 | `frontend/vite.config.js`<br>`Hand-over/saniya hand-over/project/vite.config.js` |

---

## 4. Empty Directories

- `.tmp`

---

## 5. Directory-by-Directory Application File Inventory

### 5.1 Root Configuration & Top-Level Documents
- `.env.example` (299 B) — Tracked
- `.gitignore` (819 B) — Tracked (modified)
- `CONTRIBUTING.md` (1.65 KB) — Tracked
- `FINAL_AUDIT_REPORT.md` (13.61 KB) — Untracked
- `FINAL_IMPLEMENTATION_REPORT.md` (18.69 KB) — Untracked
- `README.md` (9.67 KB) — Tracked (modified)
- `requirements.txt` (318 B) — Untracked

### 5.2 Backend Subsystem (`backend/`)
- `backend/API_CONTRACT.md` (14.52 KB) — Untracked
- `backend/README.md` (3.77 KB) — Tracked (modified)
- `backend/app/__init__.py` (0 B) — Untracked
- `backend/app/exceptions.py` (1.77 KB) — Untracked
- `backend/app/main.py` (12.35 KB) — Untracked (Production integrated FastAPI entry point)
- `backend/app/schemas/__init__.py` (205 B) — Untracked
- `backend/app/schemas/forecast.py` (825 B) — Untracked
- `backend/app/schemas/inspection.py` (3.47 KB) — Untracked
- `backend/app/schemas/request.py` (1.51 KB) — Untracked
- `backend/app/schemas/response.py` (1.43 KB) — Untracked
- `backend/app/services/__init__.py` (236 B) — Untracked
- `backend/app/services/analysis_service.py` (4.53 KB) — Untracked
- `backend/app/services/forecast_service.py` (4.80 KB) — Untracked
- `backend/app/services/history_service.py` (6.04 KB) — Untracked
- `backend/app/services/ml_adapter.py` (1.70 KB) — Untracked
- `backend/app/services/product_catalog_service.py` (10.63 KB) — Untracked
- `backend/app/services/synthetic_classifier_adapter.py` (3.39 KB) — Untracked
- `backend/tests/test_api.py` (6.69 KB) — Untracked
- `backend/tests/test_features.py` (901 B) — Untracked
- `backend/tests/test_forecast.py` (1.68 KB) — Untracked
- `backend/tests/test_history.py` (1.89 KB) — Untracked
- `backend/tests/test_product_inspection.py` (15.57 KB) — Untracked
- `backend/tests/test_synthetic_classifier.py` (898 B) — Untracked

### 5.3 Frontend Subsystem (`frontend/`)
- `frontend/.env.example` (180 B) — Untracked
- `frontend/.gitignore` (265 B) — Untracked
- `frontend/.oxlintrc.json` (231 B) — Untracked
- `frontend/README.md` (2.61 KB) — Tracked (modified)
- `frontend/index.html` (367 B) — Untracked
- `frontend/package-lock.json` (43.61 KB) — Untracked
- `frontend/package.json` (503 B) — Untracked
- `frontend/public/favicon.svg` (9.30 KB) — Untracked
- `frontend/src/App.css` (78.57 KB) — Untracked
- `frontend/src/App.jsx` (71.89 KB) — Untracked
- `frontend/src/assets/hero.png` (12.75 KB) — Untracked
- `frontend/src/index.css` (805 B) — Untracked
- `frontend/src/main.jsx` (229 B) — Untracked
- `frontend/src/services/api.js` (5.46 KB) — Untracked
- `frontend/src/services/presentation.js` (4.30 KB) — Untracked
- `frontend/src/services/productValidation.js` (4.02 KB) — Untracked
- `frontend/tests/api.test.js` (11.01 KB) — Untracked
- `frontend/tests/productValidation.test.js` (3.68 KB) — Untracked
- `frontend/tests/validation.test.js` (2.64 KB) — Untracked
- `frontend/vite.config.js` (453 B) — Untracked
- `frontend/dist/` (Compiled production build: JS, CSS, index.html) — Untracked

### 5.4 Machine Learning Core (`ml/`)
- `ml/README.md` (8.06 KB) — Tracked (modified)
- `ml/data_loader.py` (11.54 KB) — Untracked
- `ml/fdi.py` (7.49 KB) — Untracked
- `ml/feature_extractor.py` (14.57 KB) — Untracked
- `ml/inference.py` (13.51 KB) — Untracked
- `ml/inspect_dataset.py` (6.66 KB) — Untracked
- `ml/isolation_forest.py` (6.82 KB) — Untracked
- `ml/preprocessor.py` (8.01 KB) — Untracked
- `ml/service.py` (3.41 KB) — Untracked
- `ml/synthetic_classifier.py` (13.92 KB) — Untracked
- `ml/synthetic_discount.py` (11.55 KB) — Untracked
- `ml/train_pipeline.py` (19.80 KB) — Untracked

### 5.5 Regression Test Suite (`tests/`)
- `tests/README.md` (783 B) — Tracked
- `tests/test_data_loader.py` (9.61 KB) — Untracked
- `tests/test_fdi.py` (6.24 KB) — Untracked
- `tests/test_feature_pipeline.py` (15.29 KB) — Untracked
- `tests/test_inference.py` (6.42 KB) — Untracked
- `tests/test_service.py` (5.55 KB) — Untracked
- `tests/test_synthetic_classifier.py` (3.71 KB) — Untracked
- `tests/test_train_pipeline.py` (7.77 KB) — Untracked

### 5.6 Execution & Evaluation Scripts (`scripts/`)
- `scripts/build_rahul_dataset_handoff.py` (20.42 KB) — Untracked
- `scripts/build_runtime_store.py` (7.67 KB) — Untracked
- `scripts/demo_fdi.py` (1.36 KB) — Untracked
- `scripts/demo_inference.py` (2.11 KB) — Untracked
- `scripts/demo_real_data_smoke.py` (7.13 KB) — Untracked
- `scripts/demo_synthetic_ml.py` (4.65 KB) — Untracked
- `scripts/evaluate_test_split.py` (18.80 KB) — Untracked
- `scripts/generate_synthetic_discount_dataset.py` (1.72 KB) — Untracked
- `scripts/test_end_to_end.py` (12.48 KB) — Untracked
- `scripts/test_live_server.py` (2.37 KB) — Untracked
- `scripts/train_final_model.py` (14.05 KB) — Untracked
- `scripts/train_synthetic_discount_classifiers.py` (4.30 KB) — Untracked
- `scripts/validate_final_model.py` (2.54 KB) — Untracked
- `scripts/validate_synthetic_classifier.py` (1.69 KB) — Untracked

### 5.7 Serialized Artifacts (`artifacts/`)
- `artifacts/derived/fakedeal_runtime.duckdb` (1989.76 MB) — Untracked (Excluded by `.gitignore`)
- `artifacts/ml/evaluations/v1_test_evaluation.json` (13.10 KB) — Untracked
- `artifacts/ml/isolation_forest_v1/checksums.sha256` (441 B) — Untracked
- `artifacts/ml/isolation_forest_v1/isolation_forest.joblib` (2.38 MB) — Untracked
- `artifacts/ml/isolation_forest_v1/metadata.json` (11.15 KB) — Untracked
- `artifacts/ml/isolation_forest_v1/preprocessor.json` (618 B) — Untracked
- `artifacts/ml/isolation_forest_v1/validation_summary.json` (7.56 KB) — Untracked
- `artifacts/ml/isolation_forest_v1/verification_fixture.json` (469 B) — Untracked
- `artifacts/ml/synthetic_discount_v1/checksums.sha256` (346 B) — Untracked
- `artifacts/ml/synthetic_discount_v1/comparison_report.md` (1.46 KB) — Untracked
- `artifacts/ml/synthetic_discount_v1/evaluation.json` (44.13 KB) — Untracked
- `artifacts/ml/synthetic_discount_v1/logistic_regression.joblib` (2.15 KB) — Untracked
- `artifacts/ml/synthetic_discount_v1/metadata.json` (5.55 KB) — Untracked
- `artifacts/ml/synthetic_discount_v1/random_forest.joblib` (5.89 MB) — Untracked
- `artifacts/rahul_dataset_handoff/README.md` (4.16 KB) — Untracked
- `artifacts/rahul_dataset_handoff/manifest.json` (4.95 KB) — Untracked
- `artifacts/rahul_dataset_handoff/p0000001_all_splits.csv` (942.11 KB) — Untracked
- `artifacts/rahul_dataset_handoff/quality_audit.md` (6.09 KB) — Untracked
- `artifacts/rahul_dataset_handoff/schema_report.md` (3.17 KB) — Untracked
- `artifacts/synthetic/discount_scenarios_v1/manifest.json` (3.57 KB) — Untracked
- `artifacts/synthetic/discount_scenarios_v1/test.csv` (664.84 KB) — Untracked
- `artifacts/synthetic/discount_scenarios_v1/train.csv` (3.03 MB) — Untracked
- `artifacts/synthetic/discount_scenarios_v1/validation.csv` (665.29 KB) — Untracked

### 5.8 Dataset Documentation (`dataset/`)
- `dataset/README.md` (2.45 KB) — Tracked
- `dataset/data-dictionary.md` (3.08 KB) — Tracked
- `dataset/preprocessing-notes.md` (3.62 KB) — Tracked
- `dataset/validation-report.md` (9.71 KB) — Tracked (modified)

### 5.9 Project Technical Documentation (`docs/`)
- `docs/api-documentation.md` (3.12 KB) — Tracked (modified)
- `docs/dataset-processing.md` (4.53 KB) — Untracked
- `docs/dataset-source.md` (3.66 KB) — Tracked
- `docs/day-1-dataset-and-label-audit.md` (11.56 KB) — Untracked
- `docs/day-1-ml-feasibility-decision.md` (6.07 KB) — Untracked
- `docs/day-1-target-leakage-assessment.md` (10.83 KB) — Untracked
- `docs/day-1-team-and-repository-status.md` (7.51 KB) — Untracked
- `docs/day-2-5pm-ml-demo.md` (6.06 KB) — Untracked
- `docs/development-roadmap.md` (5.03 KB) — Tracked
- `docs/fdi-methodology.md` (6.17 KB) — Untracked
- `docs/forecasting-methodology.md` (2.10 KB) — Untracked
- `docs/limitations.md` (2.75 KB) — Tracked (modified)
- `docs/ml-approach.md` (4.98 KB) — Tracked
- `docs/ml-backend-contract-draft.md` (8.68 KB) — Untracked
- `docs/ml-backend-integration.md` (6.89 KB) — Untracked
- `docs/ml-inference-guide.md` (4.77 KB) — Untracked
- `docs/ml-test-evaluation-report.md` (4.74 KB) — Untracked
- `docs/ml-training-report.md` (4.15 KB) — Untracked
- `docs/model-comparison-report.md` (7.23 KB) — Untracked
- `docs/objectives-and-scope.md` (2.58 KB) — Tracked
- `docs/problem-statement.md` (2.49 KB) — Tracked
- `docs/project-overview.md` (2.51 KB) — Tracked
- `docs/repository-structure.md` (1.84 KB) — Tracked
- `docs/synthetic-discount-experiment.md` (5.42 KB) — Untracked
- `docs/system-architecture.md` (4.42 KB) — Tracked
- `docs/team-roles.md` (2.94 KB) — Tracked
- `docs/technology-stack.md` (2.42 KB) — Tracked
- `docs/testing-report.md` (6.11 KB) — Tracked (modified)
- `docs/workflow.md` (3.39 KB) — Tracked
