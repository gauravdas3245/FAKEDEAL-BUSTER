# PHASE 1: DEPLOYMENT READINESS PRE-CHECK AUDIT
**Project:** FakeDeal Buster — Sale-Day Artificial Discount & Price Scam Detector  
**Target Free Deployment Architecture:**
* **Frontend:** Vercel Hobby Tier (Static Single-Page Application)
* **Backend:** Render Free Web Service (Python FastAPI + Uvicorn)
**Audit Date:** 22 November 2026  
**Auditor:** Senior Software Project Architect & DevOps Auditor  
**Mode:** READ-ONLY PRE-CHECK (Phase 1) — Zero Deployment Actions Performed

---

## 1. Executive Summary: Free Tier Feasibility

Deploying FakeDeal Buster on free cloud tiers (Vercel + Render) is **technically feasible**, but requires addressing **two critical architectural blockers** on the backend:

```
┌───────────────────────────────────────┐        HTTPS / Cross-Origin Fetch       ┌──────────────────────────────────────┐
│         Vercel (Hobby Tier)           │────────────────────────────────────────►│          Render (Free Tier)          │
│  React 19 / Vite SPA                  │                                         │  FastAPI + Uvicorn (512 MB RAM)      │
│  • Output: dist/                      │◄────────────────────────────────────────│  • In-Memory / Pruned DuckDB         │
│  • Status: 100% READY                 │        Requires CORSMiddleware          │  • Status: REQUIRES 2 ADJUSTMENTS    │
└───────────────────────────────────────┘                                         └──────────────────────────────────────┘
```

1. **Frontend (Vercel):** **100% Deployment-Ready.** Static build via `npm run build` generates optimized assets in `dist/`. No server-side rendering (SSR) is needed.
2. **Backend (Render Free):** **Conditionally Feasible.** Render free tier imposes a strict **512 MB RAM limit**, ephemeral disk storage, and 15-minute inactivity spin-down. 
   * **Blocker 1 (Data Size):** The production DuckDB datastore (`fakedeal_runtime.duckdb`) is **1.99 GB**. It cannot be pushed to GitHub (100 MB hard limit) and would crash Render's 512 MB RAM with Out-Of-Memory (OOM) errors.
   * **Blocker 2 (Missing CORS):** `backend/app/main.py` currently lacks `CORSMiddleware`. Cross-origin browser requests from Vercel (`*.vercel.app`) to Render (`*.onrender.com`) will be blocked by default browser security policies.

---

## 2. Frontend Deployment Audit (Vercel Hobby Tier)

### 2.1 Configuration Assessment
* **Framework:** React 19.3.1 + Vite 8.3.6
* **Root Directory:** `frontend/`
* **Build Command:** `npm run build`
* **Output Directory:** `dist/`
* **Node Version Compatibility:** Node.js 18+ / 20+ (Default on Vercel)
* **Status:** Clean build test confirmed.

### 2.2 Environment Variables & API Binding
* **Current Implementation:** `frontend/src/services/api.js` resolves the API endpoint via:
  ```javascript
  const API_BASE_URL = (import.meta.env?.VITE_API_BASE_URL || '').replace(/\/+$/, '')
  ```
* **Local Development:** Defaults to empty string `''`, which leverages Vite's local dev server proxy configured in `frontend/vite.config.js` (`/api` -> `http://127.0.0.1:8000`).
* **Vercel Production Configuration:**
  * Configure environment variable in Vercel project settings:
    `VITE_API_BASE_URL=https://fakedeal-buster-api.onrender.com`
  * Alternatively, add a `vercel.json` rewrites rule to route `/api/:path*` directly to the Render service URL, avoiding client-side CORS configuration entirely.

### 2.3 Verdict on Frontend
* **Feasibility:** **PASS (READY)**
* **Action Required in Phase 2:** Commit `frontend/` files (excluding `node_modules` and `.vite-cache`).

---

## 3. Backend Deployment Audit (Render Free Web Service)

### 3.1 Server Environment & Startup Specifications
* **Runtime:** Python 3.12+ (Render native Python environment)
* **Entry Point:** `backend/app/main.py:app`
* **Startup Command:**
  ```bash
  uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
  ```
* **Dependencies:** Defined in root `requirements.txt` (FastAPI, Uvicorn, Pydantic v2, Scikit-learn, Joblib, DuckDB, NumPy, Pandas).
* **Disk & RAM Budget on Render Free:**
  * RAM: **512 MB**
  * CPU: 0.1 CPU core (shared)
  * Disk: Ephemeral filesystem (resets on restart)

### 3.2 The 1.99 GB DuckDB Blocker & Resolution Strategy

#### The Problem:
* `backend/app/services/product_catalog_service.py` and `history_service.py` default to:
  `REPOSITORY_ROOT / "artifacts" / "derived" / "fakedeal_runtime.duckdb"`
* The actual local DuckDB file is **2,086,416,384 bytes (~1.99 GB)**.
* **Why it cannot be deployed directly:**
  1. GitHub rejects any file $> 100 \text{ MB}$. Git LFS free tier bandwidth is capped at 1 GB/month.
  2. Downloading a 2 GB file onto Render at cold-start takes several minutes, exceeding Render's build and startup timeouts.
  3. Querying a 2 GB database on a 512 MB RAM container risks instantaneous SIGKILL due to memory over-allocation.

#### The Recommended Free-Tier Resolution:
The application code already contains dual-mode support for both DuckDB and standalone CSV fixtures!
* **Option A (Lightweight Seed DuckDB - Recommended):**  
  Execute a 10-second script to build `artifacts/derived/fakedeal_demo.duckdb` containing the top 100 most popular e-commerce products (~8–15 MB). This file can be safely committed to GitHub (well below 100 MB), loaded in Render RAM (< 100 MB footprint), and provides live catalog search, identity confirmation, and 30-day historical trajectories for all demo presentations.
* **Option B (CSV Fallback Mode):**  
  Configure environment variable:
  `DEFAULT_DATASET_PATH=artifacts/rahul_dataset_handoff/p0000001_all_splits.csv`  
  `HistoryService` natively parses this 942 KB CSV fixture, allowing zero-database standalone demonstration on product `P0000001` (Google Max Smartphones, Amazon).

### 3.3 The CORS Middleware Blocker & Fix

#### The Problem:
`backend/app/main.py` currently has **no CORS middleware**:
```python
# Current backend/app/main.py (L21)
app = FastAPI(
    title="FakeDeal Buster API",
    description="Backend API for detecting potentially misleading e-commerce discounts.",
    version="1.0.0"
)
# Zero CORS middleware registered!
```
When hosted on separate domains (`*.vercel.app` calling `*.onrender.com`), browsers block all HTTP requests with `CORS policy: No 'Access-Control-Allow-Origin' header is present`.

#### The Phase 2 Fix:
Add standard `CORSMiddleware` in `backend/app/main.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://*.vercel.app",
        "*"  # Or specific Vercel production domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3.4 ML Model Artifacts on Render
* **Isolation Forest Bundle:** `artifacts/ml/isolation_forest_v1/isolation_forest.joblib` (2.38 MB)
* **Random Forest Champion Bundle:** `artifacts/ml/synthetic_discount_v1/random_forest.joblib` (5.89 MB)
* **Logistic Regression Baseline:** `artifacts/ml/synthetic_discount_v1/logistic_regression.joblib` (2.15 KB)
* **Total Model Memory Footprint:** $< 30 \text{ MB}$ combined.
* **Assessment:** Safe for Git commit and comfortably fits inside Render's 512 MB memory limit.

### 3.5 Render Spin-Down / Inactivity Behavior
* On Render Free, services shut down after 15 minutes of inactivity.
* Initial requests after sleep take 50–70 seconds to respond.
* **Mitigation:** In the React frontend, display an informative toast or spinner: *"Waking up free cloud backend (first request may take up to 60s)..."* to prevent users from assuming the service is down.

---

## 4. Pre-Deployment Configuration Matrix

| Tier | Component | Free Cloud Platform | Required Configuration | Phase 2 Action |
|---|---|---|---|---|
| **Frontend** | React 19 UI | Vercel (Hobby) | Set `VITE_API_BASE_URL` | Zero code changes; add env var in Vercel |
| **Backend** | FastAPI Service | Render (Free) | Add `CORSMiddleware` | Add 10 lines of CORS config in `main.py` |
| **Datastore** | Analytical DB | Render (Free) | Pruned Demo DuckDB ($\approx 10 \text{ MB}$) | Generate seed DB or set CSV fallback |
| **ML Engine** | Joblib Models | Render (Free) | Pinned in `artifacts/ml/` | Safe to commit directly to Git ($< 10 \text{ MB}$) |
| **Monitoring** | Health Route | Render (Free) | `GET /health` | Already implemented and verified |

---

## 5. Deployment Pre-Check Sign-Off

```
========================================================================================
                         DEPLOYMENT READINESS SUMMARY
========================================================================================
Frontend (Vercel):      READY — Static build, zero blockers.
Backend (Render):       CONDITIONALLY READY — 2 code/data adjustments required in Phase 2:
                        1. Add CORSMiddleware to backend/app/main.py.
                        2. Bundle a lightweight seed DuckDB (~10MB) or CSV fixture.
Estimated Monthly Cost: $0.00 (100% Free Tiers)
========================================================================================
```
