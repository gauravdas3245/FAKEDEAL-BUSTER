# FakeDeal Buster — GitHub Release Report (v1.0.0)

> **Release Tag:** `v1.0.0`  
> **Release Name:** FakeDeal Buster v1.0.0 — Academic Capstone Release  
> **Target Branch:** `main` (via `feature/complete-project-consolidation`)  
> **Commit Hash:** `de51f85`  
> **Date:** November 23, 2026  
> **Repository:** `https://github.com/gauravdas3245/FAKEDEAL-BUSTER`

---

## 1. Release Overview

**FakeDeal Buster v1.0.0** represents the complete, verified, academic capstone release of the Sale-Day Artificial Discount & Price Scam Detector. 

This release consolidates all individual contributor subsystems into a unified, tested, and deployment-ready architecture. It incorporates 25.6M historical price records, production unsupervised anomaly detection, a rigorous supervised benchmark (Logistic Regression vs. Random Forest on 40,000 synthetic discount scenarios), conditional 14-day price forecasting with rolling-origin backtesting, and an interactive React 19 single-page application.

---

## 2. Release Highlights & Feature Changelog

### 🧠 Machine Learning & Data Science (Gaurav Das)
- **Production Isolation Forest (`isolation_forest_v1`):** Trained on multi-marketplace e-commerce price dynamics with 4 canonical rolling features:
  - `msrp_to_30d_avg` (Reference price markup)
  - `ratio_to_30d_avg` (Transaction price deviation)
  - `price_volatility_30d` (Price stability metric)
  - `recent_7d_surge` (Pre-sale spike indicator)
- **Supervised Benchmark Experiment (`synthetic_discount_v1`):**
  - Generated 40,000 balanced, reproducible synthetic discount scenarios (28,000 train / 6,000 validation / 6,000 held-out test).
  - Selected **Random Forest Classifier** (Precision: 89.54%, Recall: 73.60%, F1: 0.8079, ROC-AUC: 0.9160, PR-AUC: 0.9308, Gini: 0.8320) over Logistic Regression baseline (Precision: 87.99%, Recall: 66.70%, F1: 0.7588) under validation FPR $\le$ 10% constraint.
- **Conditional 14-Day Price Forecasting:**
  - Evaluates flat last-observation vs. trailing-7-day-mean baselines across 5 chronological rolling origins (70 backtest points).
  - Strictly requires 180 consecutive daily observations before projecting future prices; returns `INSUFFICIENT_HISTORY` otherwise.
- **Provisional Fake Discount Indicator (FDI):**
  - Honest audit implementation that returns `INSUFFICIENT_INPUTS` when live signals are absent rather than fabricating risk scores.

### ⚙️ Backend & API Engineering (Rahul Amin)
- **FastAPI REST Application:** Modular routes for catalog search, metadata, product inspection, forecasting, model comparison, and health.
- **Analytical Columnar Querying:** Sub-millisecond queries backed by DuckDB.
- **Multi-Store Dynamic Path Resolution:** Seamless fallback across Full Store (2.08GB) -> Demo Store (20.8MB) -> CSV Fixture.
- **Robust Exception Handling:** RFC-compliant HTTP error responses for `PRODUCT_NOT_FOUND` (404), `HISTORY_CONFLICT` (409), `VALIDATION_ERROR` (422), and `ML_SERVICE_UNAVAILABLE` (503).
- **CORS Middleware:** Multi-environment support for local dev and Vercel cloud domains.

### 📊 Data Preprocessing & Quality Assurance (Lakhyajyoti Phukon)
- **25.6M Record Census Audit:** Complete statistical profile across 9,980 products, 5 platforms, and 7 categories.
- **Harmonized Schema Specifications:** 46 verified raw dataset columns + 13 prototype pipeline features (59 total).
- **10 Master Synthetic QA Scenarios:** 309 records covering cold starts, calendar gaps, duplicate keys, null values, and rolling baselines.
- **Deterministic QA Script:** `scripts/generate_qa_fixtures.py` with 10 automated mathematical validation checks.

### 🎨 Frontend UI/UX Engineering (Saniya Begum)
- **React 19 + Vite SPA:** Fast, responsive client interface with zero external CSS UI framework dependencies.
- **Interactive Product Inspector:** Real-time catalog autocomplete, platform switching, date selection, and custom entry.
- **Interactive Visualizers:** Pure SVG time-series charts with 30-day moving averages, reference price anchors, and 14-day forecast bands.
- **Model Comparison View:** Tabular benchmarks, threshold selection analysis, and confusion matrices.
- **Icons & Branding:** Unified SVG symbol sprite (`public/icons.svg`) and application screenshots.

### 🧪 System Testing & Integration (Myusha Chakma)
- **Multi-Tier Quality Assurance:** 218 total automated verification checkpoints spanning ML, Backend, Frontend, and QA fixtures.
- **End-to-End Test Suite:** `scripts/test_end_to_end.py` verifying all 5 primary demonstration workflows.

---

## 3. Verified Checksums of Major Artifacts

| Artifact Name | Path | SHA-256 Checksum | File Size |
|---|---|---|---|
| Demo DuckDB Store | `artifacts/derived/fakedeal_demo.duckdb` | `5e89d17d057a79e782e4e4271aa2cf98485c27633e9d80d2fc2ad76a4dfc0be1` | 21,770,240 bytes |
| Full DuckDB Store | `artifacts/derived/fakedeal_runtime.duckdb` | `3ea3da0c40c60b4a6fe729744417d8869baecdaa71447ac4efc6ef0fa0440890` | 2,086,416,384 bytes |
| Isolation Forest Model | `artifacts/ml/isolation_forest_v1/isolation_forest.joblib` | `3127a8bdabc83ed44f67de264c997721b5ced0ae0d02c5f047e3cff6f2c2c777` | 2,493,802 bytes |
| Random Forest Model | `artifacts/ml/synthetic_discount_v1/random_forest.joblib` | `9d4858fa0ea648c27a1aa3fe4df6d2af9673806bacd57387cf994c2424197695` | 6,179,682 bytes |
| Logistic Regression Model | `artifacts/ml/synthetic_discount_v1/logistic_regression.joblib` | `b73135583d70bf10c394efe2fa5928e38de0fe47988891e20e7d8bd022f701eb` | 2,205 bytes |
| Held-Out Synthetic Test CSV | `artifacts/synthetic/discount_scenarios_v1/test.csv` | `9c731a727854c7c53a06ac929398b57a93568453837bf6c60b2104c4cfd33e90` | 680,798 bytes |
| CSV Unit Fixture | `artifacts/rahul_dataset_handoff/p0000001_all_splits.csv` | `d658e25c15128c587acd57ee336e8b21e5806fc531f9e9c7a1268702138ab4f3` | 964,720 bytes |
| QA Scenarios JSON | `tests/fixtures/qa_scenarios.json` | `b739c46446329867f9cf79b7fe89669ad39dbb3a79f62417bc5dd198bbc2f1f4` | 109,059 bytes |

---

## 4. Academic Team & Contributor Attribution

- **Institution:** Scholar Institute of Technology and Management (SITM), Guwahati
- **Programme:** Bachelor of Computer Applications (BCA) — Group B
- **Faculty Mentor:** Prof. Nitish Kumar Sarma

| Contributor | Student ID | Role | Commit Contribution |
|---|---|---|---|
| **Gaurav Das** | 2681000390 | Team Leader & ML Lead | `5388306`, `de51f85`, `5b314a3` |
| **Rahul Amin** | 2681012412 | Backend & API Engineer | `728d3b5` |
| **Lakhyajyoti Phukon** | 2681000002 | Data Preprocessing Analyst | `d6f402f`, `ac3be46`, `4213882`, `a27b2d2` |
| **Saniya Begum** | 2681000003 | Frontend UI/UX Developer | `04f7798` |
| **Myusha Chakma** | 2681000383 | Testing & QA Coordinator | `b71ca6d` |
