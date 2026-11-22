# PHASE 1: REPOSITORY RESTRUCTURING & CONSOLIDATION PLAN
**Project:** FakeDeal Buster — Sale-Day Artificial Discount & Price Scam Detector  
**Audit Date:** 22 November 2026  
**Auditor:** Senior Software Project Architect & Repository Auditor  
**Mode:** READ-ONLY AUDIT & PROPOSED PLAN (Phase 1) — Zero Modifications Performed

---

## 1. Executive Summary & Restructuring Goals

The FakeDeal Buster codebase contains high-quality, functioning software across all tiers, but currently suffers from **structural fragmentation** resulting from parallel student handovers and uncommitted local development:

1. **Integrated vs Handover Redundancy:** The primary directories `frontend/` and `backend/` already contain advanced, integrated implementations. However, `Hand-over/` contains duplicate codebases, duplicate node_modules (~80 MB), a nested `.git` directory, development logs, and multi-megabyte ZIP archives.
2. **Stranded Contributor Assets:** Lakhyajyoti Phukon's approved QA fixtures and data dictionary enhancements remain stranded on his GitHub fork.
3. **Large File Boundary Control:** A 1.99 GB DuckDB database (`artifacts/derived/fakedeal_runtime.duckdb`) and ZIP archives risk catastrophic Git push failure if `.gitignore` rules are not rigorously applied.
4. **Documentation Sprawl:** 35+ markdown documents exist across multiple directories, requiring clear classification into current, archived, and updated assets.

This plan details the exact, ordered steps for **Phase 2 Execution** to transform the repository into a clean, professional, fully attributed, and Git-synchronized project.

---

## 2. Handover Folder Audit & Migration Strategy

### 2.1 Rahul Amin's Backend Handover (`Hand-over/rahul hand-over/`)

| Handover File | Purpose | Corresponding Location in Project | Status & Phase 2 Action |
|---|---|---|---|
| `app/main.py` (4.3 KB) | Initial FastAPI router scaffold | `backend/app/main.py` (12.4 KB) | **SUPERSEDED.** Active `backend/app/main.py` contains full DuckDB catalog, ML adapters, and forecasting. Retain active version. |
| `app/services/` | Early service prototypes | `backend/app/services/` | **SUPERSEDED.** Active services implement complete business logic. |
| `API_CONTRACT.md` (11.4 KB) | Early API contract draft | `backend/API_CONTRACT.md` (14.5 KB) | **SUPERSEDED.** Active version matches live Pydantic schemas. |
| `openapi.json` (12.0 KB) | Generated OpenAPI schema | *None in backend/* | **MIGRATE.** Copy to `docs/openapi.json` for formal API contract documentation. |
| `README.md` (9.3 KB) | Backend setup instructions | `backend/README.md` (3.8 KB) | **MERGE & ARCHIVE.** Merge useful troubleshooting notes into `backend/README.md`; archive original as `docs/archive/rahul-handover-notes.md`. |
| `data/p0000001_all_splits.csv` | Mock single-product historical CSV | `artifacts/rahul_dataset_handoff/` | **DUPLICATE.** Exactly identical to `artifacts/rahul_dataset_handoff/p0000001_all_splits.csv`. Delete handover copy. |
| `requirements.txt` (492 B) | Pinned local venv dependencies | `requirements.txt` (Root unified) | **DUPLICATE.** Unified root `requirements.txt` covers all backend requirements. |
| `Hand-over/rahuk handover-over zip.zip` | Raw ZIP archive (243 KB) | *Redundant* | **REMOVE** after verifying all unique files are migrated. |

### 2.2 Saniya Begum's Frontend Handover (`Hand-over/saniya hand-over/project/`)

| Handover File | Purpose | Corresponding Location in Project | Status & Phase 2 Action |
|---|---|---|---|
| `src/App.jsx` (44.8 KB) | Initial React UI prototype | `frontend/src/App.jsx` (71.9 KB) | **SUPERSEDED.** Active `frontend/src/App.jsx` includes full Product Inspector, SVG price charts, and Presentation Mode. |
| `src/App.css` (36.3 KB) | Initial CSS styling | `frontend/src/App.css` (78.6 KB) | **SUPERSEDED.** Active CSS includes responsive card styles, badges, and layout grid. |
| `screenshots/landing-page.png` (460 KB) | UI screenshot for reports/presentation | *None in assets/* | **MIGRATE.** Move to `assets/screenshots/landing-page.png` for project documentation. |
| `screenshots/product-inspector.png` (452 KB) | UI screenshot for reports/presentation | *None in assets/* | **MIGRATE.** Move to `assets/screenshots/product-inspector.png` for project documentation. |
| `public/icons.svg` (4.9 KB) | SVG icon sprite | *Missing in frontend/public/* | **MIGRATE.** Move to `frontend/public/icons.svg` to fix missing icon references. |
| `FINAL_HANDOVER.md` (10.1 KB) | Saniya's frontend report | *None in docs/* | **ARCHIVE.** Move to `docs/archive/saniya-frontend-handover.md`. |
| `node_modules/` (~80 MB) | Duplicate local dependencies | `frontend/node_modules/` | **REMOVE.** Redundant build directory inside handover. |
| `.git/` (~5 MB) | Nested local Git repo from Saniya | *Invalid nested repo* | **REMOVE.** Must not commit nested `.git` folder to avoid submodule corruption. |
| `dev-output.log`, `dev-error.log` | Local dev server execution logs | *Temporary* | **REMOVE.** Ephemeral log files. |
| `cssgen.ps1`, `tmp.ps1`, `cssparts/` | Temporary styling generators | *Temporary* | **REMOVE.** Obsolete build helpers. |
| `Hand-over/saniya hand-over zip.zip` | Raw ZIP archive (22.2 MB) | *Redundant* | **REMOVE** after asset migration to prevent Git bloat. |

---

## 3. Lakhyajyoti Phukon Integration Strategy

To bring Lakhyajyoti's approved work into the project with authentic Git authorship:

1. **Add Remote & Fetch:**
   ```bash
   git remote add lakhya https://github.com/phukon066-create/FAKEDEAL-BUSTER.git
   git fetch lakhya
   ```
2. **Cherry-Pick / Import Commits:**
   Import commits `d6f402f`, `ac3be46`, and `4213882`:
   * `scripts/generate_qa_fixtures.py` -> Placed into `scripts/`
   * `tests/fixtures/qa_scenarios.json` -> Placed into `tests/fixtures/`
   * `tests/fixtures/README.md` -> Placed into `tests/fixtures/`
   * `tests/manual-qa-checklist.md` -> Placed into `tests/`
   * `tests/qa-verification-report.md` -> Placed into `tests/`
3. **Documentation Harmonization:**
   * Merge Lakhyajyoti's 59-column feature specification into `dataset/data-dictionary.md`.
   * Retain Gaurav's verified 25.6M row DuckDB census in `dataset/validation-report.md`.

---

## 4. Documentation Classification Matrix

| Document Path | Classification | Recommended Phase 2 Action |
|---|:---:|---|
| `README.md` | **KEEP** | Core repository landing documentation. Keep up-to-date. |
| `CONTRIBUTING.md` | **KEEP** | Team contribution guidelines. |
| `.env.example` | **UPDATE** | Ensure all backend/frontend environment variables are documented. |
| `FINAL_IMPLEMENTATION_REPORT.md` | **ARCHIVE** | Move to `docs/reports/FINAL_IMPLEMENTATION_REPORT.md`. |
| `FINAL_AUDIT_REPORT.md` | **ARCHIVE** | Move to `docs/reports/FINAL_AUDIT_REPORT.md`. |
| `backend/README.md` | **KEEP** | Backend service documentation. |
| `backend/API_CONTRACT.md` | **KEEP** | Authoritative REST API schema specification. |
| `frontend/README.md` | **KEEP** | Frontend application documentation. |
| `ml/README.md` | **KEEP** | Feature engineering and model architecture documentation. |
| `tests/README.md` | **UPDATE** | Update to index both pytest regression tests and Lakhyajyoti's QA fixtures. |
| `dataset/README.md` | **KEEP** | Dataset directory index. |
| `dataset/data-dictionary.md` | **UPDATE** | Reconcile Lakhyajyoti's 59-col schema with 46-col empirical raw census. |
| `dataset/preprocessing-notes.md` | **KEEP** | Methodology and chronological partitioning guide. |
| `dataset/validation-report.md` | **KEEP** | Empirical DuckDB census evidence. |
| `docs/api-documentation.md` | **KEEP** | High-level API overview. |
| `docs/system-architecture.md` | **KEEP** | High-level system architecture specification. |
| `docs/technology-stack.md` | **KEEP** | Pinned technology stack. |
| `docs/team-roles.md` | **KEEP** | Team member roles and Student IDs. |
| `docs/development-roadmap.md` | **KEEP** | Project sprint timeline. |
| `docs/limitations.md` | **KEEP** | Technical and operational limitations. |
| `docs/testing-report.md` | **UPDATE** | Updated with 203 automated test results. |
| `docs/day-1-*.md` (4 files) | **ARCHIVE** | Move to `docs/archive/day-1/` as historical sprint records. |
| `docs/day-2-5pm-ml-demo.md` | **ARCHIVE** | Move to `docs/archive/day-2/`. |
| `docs/fdi-methodology.md` | **KEEP** | Scoring engine methodology. |
| `docs/forecasting-methodology.md` | **KEEP** | 14-day conditional baseline forecasting methodology. |
| `docs/model-comparison-report.md` | **KEEP** | Comparative ML benchmark analysis (LR vs RF). |
| `docs/ml-test-evaluation-report.md` | **KEEP** | Isolation Forest held-out test evaluation report. |
| `docs/ml-training-report.md` | **KEEP** | Isolation Forest training documentation. |
| `docs/synthetic-discount-experiment.md` | **KEEP** | Synthetic scenario generation methodology. |

---

## 5. Target Clean Repository Directory Structure

```
FAKEDEAL-BUSTER/
├── .env.example                      # Root configuration template
├── .gitignore                         # Pinned exclusion rules (ignoring .duckdb, .venv, node_modules)
├── CONTRIBUTING.md                   # Collaboration guidelines
├── README.md                         # Authoritative project landing documentation
├── requirements.txt                  # Unified Python dependencies
│
├── assets/                           # Presentation and report media
│   ├── README.md
│   └── screenshots/                  # Migrated UI captures (landing-page.png, product-inspector.png)
│
├── backend/                          # FastAPI REST Application
│   ├── README.md
│   ├── API_CONTRACT.md
│   ├── app/
│   │   ├── main.py                   # Entry point (enhanced with CORS middleware)
│   │   ├── exceptions.py             # Domain exception hierarchy
│   │   ├── schemas/                  # Pydantic v2 request/response contracts
│   │   └── services/                 # Catalog, history, ML adapter, and forecast services
│   └── tests/                        # Backend unit & integration tests (57 tests)
│
├── frontend/                         # React 19 / Vite User Interface
│   ├── README.md
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── public/
│   │   ├── favicon.svg
│   │   └── icons.svg                 # Migrated from Saniya's handover
│   ├── src/                          # App.jsx, App.css, service clients
│   └── tests/                        # Vitest UI & validation tests (29 tests)
│
├── ml/                               # Machine Learning Core
│   ├── README.md
│   ├── data_loader.py                # Memory-safe DuckDB streaming loader
│   ├── fdi.py                        # Fake Discount Index heuristic scoring engine
│   ├── feature_extractor.py          # 17-dimension feature vector pipeline
│   ├── inference.py                  # Production inference service
│   ├── inspect_dataset.py            # Dataset census auditor
│   ├── isolation_forest.py           # Anomaly detector wrapper
│   ├── preprocessor.py               # RobustScaler & StandardScaler transformers
│   ├── service.py                    # Unified ML application service
│   ├── synthetic_classifier.py       # Supervised LR & RF benchmark trainer
│   ├── synthetic_discount.py         # Scenario generator constants
│   └── train_pipeline.py             # End-to-end model training workflow
│
├── artifacts/                        # Serialized Assets & Portable Datasets
│   ├── derived/                      # Local store directory (fakedeal_runtime.duckdb GIT-IGNORED)
│   ├── ml/
│   │   ├── isolation_forest_v1/      # Frozen Isolation Forest bundle (2.4 MB)
│   │   └── synthetic_discount_v1/    # Frozen LR & RF benchmark bundles (5.9 MB)
│   ├── rahul_dataset_handoff/        # Portable single-product test fixture (p0000001 CSV)
│   └── synthetic/
│       └── discount_scenarios_v1/    # 40,000 synthetic discount scenarios CSVs
│
├── dataset/                          # Dataset Documentation & Methodology
│   ├── README.md
│   ├── data-dictionary.md            # Reconciled 59-column production schema
│   ├── preprocessing-notes.md        # Preprocessing & chronological partitioning methodology
│   └── validation-report.md          # Exhaustive 25.6M row DuckDB census findings
│
├── scripts/                          # Automation, Training & Benchmark CLIs
│   ├── build_runtime_store.py        # Compiles raw CSVs into DuckDB store
│   ├── evaluate_test_split.py        # Evaluates models on held-out test split
│   ├── generate_qa_fixtures.py       # Lakhyajyoti's 10-scenario synthetic QA generator
│   ├── generate_synthetic_discount_dataset.py
│   ├── test_end_to_end.py            # 5-workflow E2E verification
│   └── train_final_model.py          # Isolation Forest production training CLI
│
├── tests/                            # ML & Test Suite
│   ├── README.md
│   ├── fixtures/                     # Lakhyajyoti's master QA scenario dataset
│   │   ├── README.md
│   │   └── qa_scenarios.json
│   ├── manual-qa-checklist.md        # 12-point manual test protocol
│   ├── qa-verification-report.md     # QA verification evidence
│   ├── test_data_loader.py           # Pytest ML tests (117 tests)
│   ├── test_fdi.py
│   ├── test_feature_pipeline.py
│   ├── test_inference.py
│   ├── test_service.py
│   ├── test_synthetic_classifier.py
│   └── test_train_pipeline.py
│
├── docs/                             # Engineering Specifications & Reports
│   ├── archive/                      # Historical Day-1/Day-2 notes and raw handovers
│   └── reports/                      # Implementation and audit reports
│
└── audit/                            # Phase 1 Discovery & Audit Reports
    ├── PHASE1_GITHUB_AUDIT.md
    ├── PHASE1_FILE_INVENTORY.md
    ├── PHASE1_LAKHYAJYOTI_CONTRIBUTION.md
    ├── PHASE1_RESTRUCTURING_PLAN.md
    └── PHASE1_DEPLOYMENT_READINESS.md
```

---

## 6. Ordered Phase 2 Execution Roadmap

When authorized by the user, Phase 2 will execute strictly in this order:

1. **Step 1: Backup & Safety Branch Creation**
   * Create working branch `feature/complete-project-consolidation` so `feature/project-config-and-baseline` remains untouched as a local rollback point.
2. **Step 2: Lakhyajyoti Git Attribution Integration**
   * Fetch `phukon066-create/FAKEDEAL-BUSTER`.
   * Import his commits or copy his QA assets (`generate_qa_fixtures.py`, `tests/fixtures/`, `tests/manual-qa-checklist.md`).
3. **Step 3: Handover Asset Harvesting & Deconfliction**
   * Copy screenshots (`landing-page.png`, `product-inspector.png`) to `assets/screenshots/`.
   * Copy `public/icons.svg` to `frontend/public/icons.svg`.
   * Copy `openapi.json` to `docs/openapi.json`.
   * Move handover summaries to `docs/archive/`.
4. **Step 4: Safe Removal of Redundant Handover Folders**
   * Remove `Hand-over/` directory (deleting the 22MB zip, duplicate `node_modules`, and nested `.git`).
   * Clean local test caches (`.pytest-run/`, `.tmp/`).
5. **Step 5: FastAPI Production Enhancement**
   * Add `CORSMiddleware` to `backend/app/main.py` allowing localhost and Vercel domains.
6. **Step 6: Rigorous Post-Restructuring Verification**
   * Execute full test suite:
     * ML: `pytest tests/` (117 passing tests)
     * Backend: `pytest backend/tests/` (57 passing tests)
     * Frontend: `npm --prefix frontend test` (29 passing tests)
     * QA Generator: `python scripts/generate_qa_fixtures.py --validate-only`
     * E2E: `python scripts/test_end_to_end.py`
7. **Step 7: Atomic Staging & Commit Structuring**
   * Stage core modules in logical commits (e.g., `feat(ml): ...`, `feat(backend): ...`, `feat(frontend): ...`, `docs: ...`).
   * Confirm no files $> 10 \text{ MB}$ or private secrets are staged.
8. **Step 8: Final Student Review & Push Authorization**
   * Present staged commit tree to the student for final push authorization.
