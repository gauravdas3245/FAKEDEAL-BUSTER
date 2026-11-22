# PHASE 1: GITHUB AND GIT REPOSITORY AUDIT REPORT
**Project:** FakeDeal Buster — Sale-Day Artificial Discount & Price Scam Detector  
**Local Project Root:** `C:\end sem project\FAKEDEAL-BUSTER`  
**Central GitHub Repository:** `https://github.com/gauravdas3245/FAKEDEAL-BUSTER`  
**Default Branch:** `main`  
**Audit Date:** 22 November 2026  
**Auditor:** Senior Git Engineer, Repository Auditor & Software Project Architect  
**Mode:** READ-ONLY AUDIT (Phase 1) — Zero Destructive Actions Executed

---

## 1. Executive Summary: Git Synchronization State

A thorough, read-only audit of the local working tree and remote GitHub repository confirms a **critical synchronization divergence**:

1. **GitHub Central Repository State (`origin`):**
   * The public GitHub repository `gauravdas3245/FAKEDEAL-BUSTER` contains **exactly 1 branch (`main`)** and **28 commits** ending at commit `5b314a3` (dated 16 November 2026).
   * **Only 27 documentation and skeleton files** are currently tracked on GitHub.
   * **Zero lines of application implementation code** (Python FastAPI backend, React frontend, ML models, test suites, or execution scripts) exist on the central GitHub repository.
   * Total public Pull Requests on `gauravdas3245/FAKEDEAL-BUSTER`: **0 PRs** (open, closed, or merged).

2. **Local Working Tree State (`C:\end sem project\FAKEDEAL-BUSTER`):**
   * The local checkout is on branch `feature/project-config-and-baseline` pointing to commit `5b314a3`.
   * The working tree contains the **complete, working end-semester implementation** (FastAPI backend with 6 routers/services, React 19 UI with product inspection and forecast charts, ML Isolation Forest bundle, 40,000 synthetic discount scenarios, and 203 automated tests).
   * However, **none of this code has been staged or committed** to Git.
   * The working tree currently has **9 modified tracked files** and **48+ untracked directories/files**.
   * Local branch `feature/project-config-and-baseline` is `0 ahead, 0 behind` relative to `origin/main` because all changes remain purely uncommitted working tree modifications.

3. **External Fork Discovery (Lakhyajyoti Phukon):**
   * Contributor Lakhyajyoti Phukon maintained fork `https://github.com/phukon066-create/FAKEDEAL-BUSTER`.
   * On 18 November 2026, he merged **Pull Request #1** (`feat(qa): add data validation fixtures and quality documentation`, commit `a27b2d2`) containing 10 files (+5,557 lines).
   * **CRITICAL FINDING:** PR #1 was merged **internally into his own fork (`phukon066-create:main`)**. It was never submitted as an upstream PR to `gauravdas3245/FAKEDEAL-BUSTER:main`. None of his commits or QA fixtures currently exist in the local working tree or upstream GitHub repository.

---

## 2. Git Status and Configuration Details

### 2.1 Branch and Head Identification
* **Current Active Branch:** `feature/project-config-and-baseline`
* **Current Commit SHA:** `5b314a3510361c54aeb01e710a1492bc9d5ebc7d`
* **Commit Subject:** `Expand project README with overview and documentation`
* **Commit Date:** `2026-11-16 15:41:58 +0530`
* **Commit Author:** `GAURAV DAS <gauravdas3245@gmail.com>`

### 2.2 Remote Configuration
```
origin  https://github.com/gauravdas3245/FAKEDEAL-BUSTER.git (fetch)
origin  https://github.com/gauravdas3245/FAKEDEAL-BUSTER.git (push)
```
* **Remote Verification:** `origin` points exactly to the expected central repository `https://github.com/gauravdas3245/FAKEDEAL-BUSTER.git`.
* **Remote Branches (`git ls-remote`):**
  * `5b314a3510361c54aeb01e710a1492bc9d5ebc7d HEAD`
  * `5b314a3510361c54aeb01e710a1492bc9d5ebc7d refs/heads/main`
  * *Note:* No other branches, tags, or pull request references (`refs/pull/*`) exist on the remote.

### 2.3 Ahead / Behind Relationship
| Comparison | Left (Local) | Right (Remote) | Divergence Count | Status |
|---|---|---|---|---|
| `feature/project-config-and-baseline` vs `main` | `feature` (local) | `main` (local) | `0 0` | Synchronized at commit `5b314a3` |
| `main` vs `origin/main` | `main` (local) | `origin/main` | `0 0` | Synchronized at commit `5b314a3` |
| `feature/project-config-and-baseline` vs `origin/main` | `feature` (local) | `origin/main` | `0 0` | Synchronized at commit `5b314a3` |

> [!WARNING]
> While Git reports `0 ahead, 0 behind`, this is solely because no commits have been created locally. The actual working tree contains thousands of lines of uncommitted production code, models, and tests.

---

## 3. Working Tree Status Breakdown

### 3.1 Modified Tracked Files (9 Files)
These 9 files were originally committed during repository scaffolding on 16 November 2026 and have since been updated in the working tree to reflect the real system:

1. `.gitignore` — Added rules for `.pytest-run/`, `*.duckdb`, `*.duckdb.wal`, `*.db`, `*.sqlite`, `*.zip`, `*.tar.gz`, and whitelist for `artifacts/rahul_dataset_handoff/p0000001_all_splits.csv`.
2. `README.md` — Replaced generic scaffold with detailed 10-section technical documentation, architecture pillars, quick-start guide, and API definitions.
3. `backend/README.md` — Updated with live FastAPI route specifications (`/api/catalog`, `/api/inspect`, `/api/forecast`, `/api/models/synthetic-comparison`).
4. `dataset/validation-report.md` — Expanded from blank 53-line template to exhaustive 156-line Stage 1 empirical census report across all 25,606,940 rows.
5. `docs/api-documentation.md` — Updated to reference live `backend/API_CONTRACT.md` and live Pydantic schemas.
6. `docs/limitations.md` — Updated with precise operational limitations (14-day conditional flat baseline forecaster, historical data bounded to Dec 2024).
7. `docs/testing-report.md` — Updated with final 203 automated test execution status and test subsystem matrix.
8. `frontend/README.md` — Updated with React 19 / Vite UI architecture and Product Inspector capabilities.
9. `ml/README.md` — Updated with finalized 17-feature dual-track ML pipeline and Isolation Forest / Synthetic benchmark architecture.

### 3.2 Untracked Core Project Files & Folders
The following core application files exist in the local workspace but are not tracked by Git:

* **Backend Implementation:**
  * `backend/API_CONTRACT.md` (14.8 KB live contract specification)
  * `backend/app/` (`main.py`, `exceptions.py`, `schemas/`, `services/`)
  * `backend/tests/` (`test_api.py`, `test_features.py`, `test_history.py`, `test_forecast.py`, `test_product_inspection.py`, `test_synthetic_classifier.py`)
* **Frontend Implementation:**
  * `frontend/package.json`, `frontend/package-lock.json`, `frontend/vite.config.js`, `frontend/index.html`
  * `frontend/.env.example`, `frontend/.gitignore`, `frontend/.oxlintrc.json`
  * `frontend/src/` (`App.jsx`, `App.css`, `main.jsx`, `services/`)
  * `frontend/public/`
  * `frontend/tests/`
* **Machine Learning & Pipeline:**
  * `ml/data_loader.py`, `ml/fdi.py`, `ml/feature_extractor.py`, `ml/inference.py`, `ml/inspect_dataset.py`, `ml/isolation_forest.py`, `ml/preprocessor.py`, `ml/service.py`, `ml/synthetic_classifier.py`, `ml/synthetic_discount.py`, `ml/train_pipeline.py`
  * `requirements.txt` (Root Python dependencies)
  * `tests/` (`test_data_loader.py`, `test_fdi.py`, `test_feature_pipeline.py`, `test_inference.py`, `test_service.py`, `test_synthetic_classifier.py`, `test_train_pipeline.py`)
* **Scripts & Utilities:**
  * `scripts/` (15 Python automation scripts including `build_runtime_store.py`, `evaluate_test_split.py`, `test_end_to_end.py`, `train_final_model.py`)
* **Serialized Model & Synthetic Artifacts:**
  * `artifacts/ml/isolation_forest_v1/` (`isolation_forest.joblib`, metadata, checksums)
  * `artifacts/ml/synthetic_discount_v1/` (`random_forest.joblib`, `logistic_regression.joblib`, `evaluation.json`)
  * `artifacts/synthetic/discount_scenarios_v1/` (`train.csv`, `validation.csv`, `test.csv`)
  * `artifacts/rahul_dataset_handoff/` (`p0000001_all_splits.csv`, manifest, documentation)
* **Technical Documentation:**
  * 15 comprehensive technical reports in `docs/`
  * `FINAL_AUDIT_REPORT.md` (13.9 KB)
  * `FINAL_IMPLEMENTATION_REPORT.md` (19.1 KB)

### 3.3 Large / Non-Committable Files in Working Tree
* `artifacts/derived/fakedeal_runtime.duckdb` — **1,989.76 MB (1.99 GB)**. Compiled DuckDB database. **MUST NOT BE COMMITTED TO GITHUB.** (Properly ignored by updated `.gitignore`).
* `Hand-over/saniya hand-over zip.zip` — **22.21 MB**. Archive of Saniya's handover.
* `Hand-over/` directory — Contains nested `node_modules/`, `.git/` inside Saniya's folder, and redundant zips.

---

## 4. Complete Git Commit History Audit (All 28 Commits)

All 28 commits in the repository were authored by Gaurav Das on 16 November 2026:

| # | Commit SHA | Commit Date | Author | Commit Subject | Files Changed |
|:---:|:---:|:---:|:---|:---|:---:|
| 1 | `03cc94e` | 2026-11-16 15:10:39 | GAURAV DAS | Initial commit | `.gitignore`, `CONTRIBUTING.md` |
| 2 | `6d7cab9` | 2026-11-16 15:13:58 | GAURAV DAS | Add contribution guidelines | `CONTRIBUTING.md` |
| 3 | `f0a82d7` | 2026-11-16 15:15:39 | GAURAV DAS | Add Python and React gitignore rules | `.gitignore` |
| 4 | `470f8f5` | 2026-11-16 15:17:14 | GAURAV DAS | Add example environment configuration | `.env.example` |
| 5 | `be8f442` | 2026-11-16 15:18:41 | GAURAV DAS | Add project overview documentation | `docs/project-overview.md` |
| 6 | `ccba915` | 2026-11-16 15:20:00 | GAURAV DAS | Add project problem statement | `docs/problem-statement.md` |
| 7 | `53d7709` | 2026-11-16 15:21:28 | GAURAV DAS | Add project objectives and scope | `docs/objectives-and-scope.md` |
| 8 | `fa1964c` | 2026-11-16 15:22:42 | GAURAV DAS | Add system architecture documentation | `docs/system-architecture.md` |
| 9 | `05f6b44` | 2026-11-16 15:23:44 | GAURAV DAS | Add system workflow documentation | `docs/workflow.md` |
| 10 | `db0d649` | 2026-11-16 15:24:43 | GAURAV DAS | Add technology stack documentation | `docs/technology-stack.md` |
| 11 | `42d4bc6` | 2026-11-16 15:25:28 | GAURAV DAS | Add team roles and responsibilities | `docs/team-roles.md` |
| 12 | `846f9bd` | 2026-11-16 15:26:07 | GAURAV DAS | Add project development roadmap | `docs/development-roadmap.md` |
| 13 | `7a87c49` | 2026-11-16 15:26:39 | GAURAV DAS | Add dataset source and attribution documentation | `docs/dataset-source.md` |
| 14 | `b5ea8d5` | 2026-11-16 15:27:14 | GAURAV DAS | Add API documentation | `docs/api-documentation.md` |
| 15 | `56f4c4d` | 2026-11-16 15:27:49 | GAURAV DAS | Add machine learning approach documentation | `docs/ml-approach.md` |
| 16 | `1ac159c` | 2026-11-16 15:28:14 | GAURAV DAS | Add testing report and test cases | `docs/testing-report.md` |
| 17 | `88ed89b` | 2026-11-16 15:29:13 | GAURAV DAS | Add project limitations documentation | `docs/limitations.md` |
| 18 | `73485ca` | 2026-11-16 15:26:39 | GAURAV DAS | Add dataset documentation and usage details | `dataset/README.md` |
| 19 | `4f9c393` | 2026-11-16 15:28:14 | GAURAV DAS | Add dataset data dictionary | `dataset/data-dictionary.md` |
| 20 | `5650e4a` | 2026-11-16 15:30:26 | GAURAV DAS | Add dataset preprocessing documentation | `dataset/preprocessing-notes.md` |
| 21 | `6c2b966` | 2026-11-16 15:31:53 | GAURAV DAS | Add dataset validation report template | `dataset/validation-report.md` |
| 22 | `5bd6f92` | 2026-11-16 15:33:14 | GAURAV DAS | Add project assets directory structure | `assets/README.md` |
| 23 | `fcfb8fe` | 2026-11-16 15:34:37 | GAURAV DAS | Add initialize frontend directory | `frontend/README.md` |
| 24 | `a121c12` | 2026-11-16 15:35:43 | GAURAV DAS | Add initialize backend directory | `backend/README.md` |
| 25 | `15c2c02` | 2026-11-16 15:36:37 | GAURAV DAS | Add initialize machine learning directory | `ml/README.md` |
| 26 | `7a2a7bc` | 2026-11-16 15:37:40 | GAURAV DAS | Add initialize testing directory | `tests/README.md` |
| 27 | `3ae8cd5` | 2026-11-16 15:38:39 | GAURAV DAS | Document repository structure and team workflow | `docs/repository-structure.md` |
| 28 | `5b314a3` | 2026-11-16 15:41:58 | GAURAV DAS | Expand project README with overview and documentation | `README.md` |

---

## 5. Summary of Git Audit Findings

1. **Working Tree Divergence:** The local working tree is fundamentally healthy and contains the complete, verified, end-to-end working system, but is completely unstaged.
2. **Missing Upstream Synchronization:** The GitHub remote `origin` is stalled at the initial project scaffold from 16 November 2026.
3. **No Dangling Commits Locally:** Git reflog confirms the local repository has only performed `clone` and `checkout` (`HEAD@{0}: checkout: moving from main to feature/project-config-and-baseline`, `HEAD@{1}: clone`).
4. **Safety Confirmation:** In accordance with Phase 1 instructions, zero commits, resets, merges, or pushes were performed.
