# FakeDeal Buster — Team Roles and Responsibilities

## 1. Academic & Institutional Information

- **Project Title:** FakeDeal Buster — Sale-Day Artificial Discount & Price Scam Detector
- **Institution:** Scholar Institute of Technology and Management (SITM), Guwahati
- **Department:** Department of Computer Science & Engineering
- **Programme:** Bachelor of Computer Applications (BCA)
- **Group:** Group B
- **Faculty Mentor:** Prof. Nitish Kumar Sarma
- **Project Type:** Machine Learning-Based Web Application & E-Commerce Pricing Anomaly Detection Prototype

---

## 2. Team Members, Student IDs & Core Responsibilities

> [!IMPORTANT]
> The identification numbers listed below are **Student IDs**, NOT University Roll Numbers. University Roll Number fields in official examination records remain in their blank, unassigned state per institutional instructions.

### 1. Gaurav Das
- **Student ID:** 2681000390
- **Role:** Team Leader, Machine Learning Lead & GitHub Maintainer
- **Key Responsibilities:**
  - Coordinate overall project architecture, milestones, and cross-functional integration.
  - Formulate and train the central Isolation Forest anomaly detection model (`isolation_forest_v1`).
  - Implement feature engineering pipelines (`msrp_to_30d_avg`, `ratio_to_30d_avg`, `price_volatility_30d`, `recent_7d_surge`).
  - Design and evaluate the supervised synthetic scenario experiment (Logistic Regression vs. Random Forest on 40,000 scenarios).
  - Implement conditional 14-day chronological price forecasting with rolling-origin backtesting.
  - Maintain the central GitHub repository (`gauravdas3245/FAKEDEAL-BUSTER`), review pull requests, and manage branches and releases.

### 2. Rahul Amin
- **Student ID:** 2681012412
- **Role:** Backend & API Engineer
- **Key Responsibilities:**
  - Architect and develop the RESTful backend using Python and FastAPI.
  - Create and document all API endpoints (`/api/catalog`, `/api/inspect`, `/api/forecast`, `/api/models/synthetic-comparison`, `/health`).
  - Implement robust input validation (Pydantic v2 schemas) and structured HTTP error responses (404, 409, 422, 500, 503).
  - Develop DuckDB query services for sub-millisecond historical price retrieval across 25.6M records.
  - Implement CORS middleware and multi-database fallback resolution (Runtime DB -> Demo DB -> CSV Fixture).
  - Author and maintain the 57-test automated backend test suite (`backend/tests/`).

### 3. Lakhyajyoti Phukon
- **Student ID:** 2681000002
- **Role:** Data Preprocessing Analyst & QA Data Engineer
- **Key Responsibilities:**
  - Perform empirical census and statistical auditing of the 25,606,940-row Kaggle e-commerce price dataset.
  - Author the comprehensive 46-column dataset data dictionary and 59-column pipeline feature specification.
  - Formulate the 10 master synthetic QA scenarios (309 records) in `tests/fixtures/qa_scenarios.json`.
  - Author `scripts/generate_qa_fixtures.py` with deterministic validation checks (Checks 1 to 10).
  - Document manual QA checklists, stream isolation protocols, and provisional FDI (Fake Discount Indicator) scoring.

### 4. Saniya Begum
- **Student ID:** 2681000003
- **Role:** Frontend UI/UX Developer
- **Key Responsibilities:**
  - Design and build the single-page web user interface using React 19 and Vite.
  - Develop the interactive Product Inspector component with real-time search, category filtering, and date selection.
  - Implement responsive data visualizations: SVG historical price charts, 14-day forecast bands, and cross-platform comparisons.
  - Create the Model Comparison View displaying side-by-side benchmark tables, ROC curves, and confusion matrices.
  - Author the 29-test frontend test suite (`frontend/tests/`) covering API mapping, form validation, and state handling.

### 5. Myusha Chakma
- **Student ID:** 2681000383
- **Role:** Testing & Integration Coordinator
- **Key Responsibilities:**
  - Coordinate system-level quality assurance and full-stack integration verification.
  - Design and execute end-to-end integration workflows (`scripts/test_end_to_end.py`).
  - Verify error boundary handling across UI, API, and analytical engines.
  - Validate browser compatibility, responsive layouts, and accessibility standards.
  - Maintain the consolidated QA verification log and audit testing deliverables.

---

## 3. Team Collaboration & Git Workflow

1. **Central Repository:** Maintained by Team Leader at `https://github.com/gauravdas3245/FAKEDEAL-BUSTER`.
2. **Feature Branching:** All individual contributions are developed on designated feature branches (e.g., `feature/data-preparation-qa`, `feature/complete-project-consolidation`).
3. **Pull Request Workflow:** Team members fork or branch, implement changes, run test suites locally, and submit Pull Requests for review.
4. **Code Quality Gates:** No pull request is merged without 100% test pass rate across ML (117 tests), Backend (57 tests), Frontend (29 tests), and QA fixtures (10 checks).
5. **Direct Commit Policy:** Direct unreviewed commits to the central `main` branch are restricted. All merges are performed by the Team Leader with preserved author attribution.
