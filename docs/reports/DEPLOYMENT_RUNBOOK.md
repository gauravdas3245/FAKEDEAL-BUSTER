# FakeDeal Buster — Operations & Deployment Runbook

> **Document Status:** OFFICIAL PRODUCTION OPERATIONS RUNBOOK  
> **Target Version:** v1.0.0  
> **Applicable Environments:** Local Development, Render (Backend API), Vercel (Frontend SPA)

---

## 1. Local Development Setup Runbook

### 1.1 Prerequisites
- **Python:** 3.12+ (Anaconda or Miniconda recommended)
- **Node.js:** v20.x or v22.x LTS with npm
- **Git:** 2.40+
- **Terminal:** PowerShell on Windows or Bash on Linux/macOS

### 1.2 Repository Clone & Environment Activation
```powershell
# Clone the repository
git clone https://github.com/gauravdas3245/FAKEDEAL-BUSTER.git
cd FAKEDEAL-BUSTER

# Checkout the consolidated release branch (or main after merge)
git checkout feature/complete-project-consolidation

# Create or activate conda Python environment
conda activate fakedeal
# OR using python venv:
# python -m venv .venv
# .\.venv\Scripts\Activate.ps1
```

### 1.3 Install Dependencies
```powershell
# Install backend Python dependencies
pip install -r requirements.txt

# Install frontend Node dependencies
cd frontend
npm install
cd ..
```

### 1.4 Running the Local Application
Open two separate terminal windows:

**Terminal 1 — Backend API:**
```powershell
$env:PYTHONPATH = "backend"
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
*Health check URL:* `http://127.0.0.1:8000/health`  
*Interactive OpenAPI docs:* `http://127.0.0.1:8000/docs`

**Terminal 2 — Frontend UI:**
```powershell
cd frontend
npm run dev
```
*Application UI:* `http://localhost:5173`

---

## 2. Cloud Deployment Runbook: Render (Backend)

Render hosts the FastAPI application and analytical DuckDB store on its free tier.

### 2.1 Step-by-Step Deployment
1. Log into your [Render Dashboard](https://dashboard.render.com).
2. Click **New +** and select **Web Service**.
3. Select **Build and deploy from a Git repository** and connect `gauravdas3245/FAKEDEAL-BUSTER`.
4. Configure the Web Service settings:
   - **Name:** `fakedeal-buster-api`
   - **Region:** `Oregon (US West)` (or closest region)
   - **Branch:** `main` (or `feature/complete-project-consolidation`)
   - **Root Directory:** *(leave blank — repository root)*
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend`
   - **Instance Type:** `Free` (512 MB RAM, 0.1 CPU)
5. Expand **Advanced** and configure Environment Variables:
   | Key | Value | Purpose |
   |---|---|---|
   | `PYTHON_VERSION` | `3.12.0` | Ensures pinned Python runtime |
   | `PYTHONPATH` | `backend` | Resolves `app.*` import statements |
   | `FAKEDEAL_DATABASE_PATH` | `artifacts/derived/fakedeal_demo.duckdb` | Uses the 20.8 MB demo DuckDB store |
   | `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,https://*.vercel.app` | Authorizes local and Vercel clients |
   | `CORS_ORIGIN_REGEX` | `^https://.*\.vercel\.app$` | Dynamically authorizes all Vercel domains |
6. Set **Health Check Path** to `/health`.
7. Click **Create Web Service**.

### 2.2 Verification
Once deployment completes (indicated by a green checkmark), test the service:
```bash
curl -i https://<your-render-service-name>.onrender.com/health
```
**Expected Response:**
```json
HTTP/2 200
content-type: application/json

{
  "status": "healthy",
  "process": "healthy",
  "database": "available",
  "model_bundle": "present_unverified",
  "synthetic_classifier_bundle": "present_unverified"
}
```

---

## 3. Cloud Deployment Runbook: Vercel (Frontend)

Vercel hosts the React 19 single-page application on its global CDN edge network.

### 3.1 Step-by-Step Deployment
1. Log into your [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** -> **Project**.
3. Import your GitHub repository (`gauravdas3245/FAKEDEAL-BUSTER`).
4. Configure the Project:
   - **Framework Preset:** `Vite`
   - **Root Directory:** Click **Edit** and select `frontend`.
   - **Build Command:** `npm run build` (detected automatically)
   - **Output Directory:** `dist` (detected automatically)
5. Expand **Environment Variables** and add:
   | Variable Name | Value | Purpose |
   |---|---|---|
   | `VITE_API_BASE_URL` | `https://<your-render-service-name>.onrender.com` | Target Render backend URL (no trailing slash) |
6. Click **Deploy**.

### 3.2 Verification
1. Open your assigned Vercel URL (e.g., `https://fakedeal-buster.vercel.app`).
2. Navigate to `#inspector`.
3. Search for `Google Max Smartphones` and verify that suggestions populate from the Render API.
4. Run an analysis and confirm the 3-state verdict card, price history chart, and 14-day forecast render.

---

## 4. Operational Troubleshooting Guide

### 4.1 Cold Starts on Render Free Tier
- **Symptom:** First request after 15 minutes of inactivity takes 30-50 seconds.
- **Cause:** Render free tier puts inactive services into spin-down mode.
- **Mitigation:**
  - Setup a free uptime ping (e.g., using [cron-job.org](https://cron-job.org) or [UptimeRobot](https://uptimerobot.com)) to ping `https://<your-render-url>/health` every 10 minutes.
  - The frontend UI includes loading state feedback on the submit button so users know the request is in flight.

### 4.2 Cross-Origin Resource Sharing (CORS) Errors
- **Symptom:** Browser console reports `Access to XMLHttpRequest at ... from origin ... has been blocked by CORS policy`.
- **Resolution:**
  - Verify `CORS_ORIGIN_REGEX` is set to `^https://.*\.vercel\.app$` in the Render service settings.
  - If using a custom domain (e.g., `fakedeal.sitm.ac.in`), append it to `CORS_ALLOWED_ORIGINS` in Render:
    `CORS_ALLOWED_ORIGINS=http://localhost:5173,https://fakedeal.sitm.ac.in`

### 4.3 Out-Of-Memory (OOM) Errors on Render
- **Symptom:** Render logs display `Out of memory (OOM)` and the service restarts.
- **Cause:** Attempting to load the 2.08 GB database or reading large files into memory.
- **Resolution:**
  - Confirm `FAKEDEAL_DATABASE_PATH` points strictly to `artifacts/derived/fakedeal_demo.duckdb` (20.76 MB).
  - Verify `artifacts/derived/fakedeal_runtime.duckdb` is NOT in the deployed repository (confirmed via `.gitignore`).
  - DuckDB memory footprint will remain below 120 MB.

### 4.4 Rebuilding the Lightweight Demonstration Store
If catalog products need updating or re-stratification:
```powershell
python scripts/build_demo_runtime_store.py --limit 105
```
This re-extracts 15 products per category across all 7 categories from the local 2.08 GB store, updates metadata, indexes observations, and outputs the refreshed ~21 MB database.
