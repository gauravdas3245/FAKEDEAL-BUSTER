# Day 1: Team & Repository Status Report

**Project:** FakeDeal Buster — Sale-Day Artificial Discount & Price Scam Detector  
**Institution:** Scholar Institute of Technology and Management (SITM), Guwahati  
**Department:** Department of Computer Science  
**Course & Semester:** Bachelor of Computer Applications (BCA), Semester I  
**Group:** Group B  
**Faculty Mentor:** Mr. Nitish Kr. Sarma  
**Date:** 16 November 2026 (Completed 17 November 2026 early hours)  
**Author / Coordinator:** Gaurav Das (Team Leader & ML Developer)

---

## 1. Team Register & Designated Responsibilities

The team register, contact information, and module ownership are verified against the Project Requirements Document ([FakeDeal_Buster_Group_B_Final_PRD.docx](file:///C:/end%20sem%20project/FakeDeal_Buster_Group_B_Final_PRD.docx)) and [docs/team-roles.md](file:///C:/end%20sem%20project/FAKEDEAL-BUSTER/docs/team-roles.md):

| No. | Member Name | Student ID | Contact Number | Primary Role | Designated Responsibilities |
|---|---|---|---|---|---|
| 1 | **Gaurav Das** | 2681000390 | 8471977772 | Team Leader, ML Developer, GitHub Maintainer | Overall project coordination; central GitHub repository maintenance; ML data loader, pipeline, and model development; target validation; PR review and merging. |
| 2 | **Rahul Amin** | 2681012412 | 7636009716 | Backend Developer | FastAPI REST API development (`GET /health`, `POST /api/analyze` or `/analyze`); request validation using Pydantic; backend model loading and orchestration; frontend coordination. |
| 3 | **Lakhyajyoti Phukan** | 2681000002 | 9395694382 | Data Preparation Analyst | Dataset inspection; data cleaning and preprocessing documentation; data dictionary maintenance; category/platform-specific encoding requirements; data quality reporting. |
| 4 | **Saniya Begum** | 2681000003 | 9954576326 | Frontend Developer | React.js user interface; product input forms (manual inputs with optional URL); verdict badge and indicator displays; price forecast visualization components; frontend validation. |
| 5 | **Myusha Chakma** | 2681000383 | 96123 64699 | Testing & Integration Coordinator | Integration testing between frontend, backend, and ML pipeline; test case checklist creation; end-to-end verification; defect tracking and presentation demonstration support. |

---

## 2. Repository Architecture & Directory Ownership

The central working repository is hosted at:
- **Repository Remote URL:** `https://github.com/gauravdas3245/FAKEDEAL-BUSTER.git`
- **Local Project Root:** `C:\end sem project\FAKEDEAL-BUSTER`
- **Current Active Branch:** `feature/project-config-and-baseline`
- **Central Default Branch:** `main`

### Working Directory Allocation:
To maintain clean separation of concerns and avoid merge conflicts, working directories are allocated as follows:

| Directory | Primary Owner | Scope & Deliverables | Current Status |
|---|---|---|---|
| `ml/` | Gaurav Das | Data loader (`data_loader.py`), dataset inspection (`inspect_dataset.py`), feature engineering, and scoring engine. | **Stage 1 Complete** (memory-safe DuckDB loader and full-split inspection scripts operational). |
| `tests/` | Myusha Chakma / Gaurav Das | Automated unit and integration tests (`test_data_loader.py`, API tests, pipeline tests). | **Active** (19/19 unit tests passing for data loader). |
| `backend/` | Rahul Amin | FastAPI application, Pydantic schemas, route definitions, Uvicorn runner. | **Initial Planned** (`backend/README.md` exists; implementation pending Rahul's environment setup). |
| `frontend/` | Saniya Begum | React application, UI components, form validators, API client. | **Initial Planned** (`frontend/README.md` exists; implementation pending Saniya's environment setup). |
| `dataset/` | Lakhyajyoti Phukan / Gaurav Das | Data dictionary, preprocessing notes, validation reports. | **Active** (`validation-report.md` updated with exhaustive census findings; `data-dictionary.md` pending update). |
| `docs/` | Gaurav Das (Lead) / All | System architecture, roadmap, API documentation, leakage assessments, feasibility notes. | **Active** (Updated with Day 1 deliverables). |
| `assets/` | Team-wide | Architecture diagrams, UI mockups, screenshots, presentation slides. | Available for integration assets. |

---

## 3. Collaboration Workflow & Communication Arrangements

1. **Git & GitHub Collaboration Model:**
   - The central repository is maintained by Gaurav Das.
   - Team members are to work via individual forks of `https://github.com/gauravdas3245/FAKEDEAL-BUSTER`.
   - Work is developed on feature-specific branches (e.g., `feature/backend-setup`, `feature/frontend-ui`).
   - Pull Requests (PRs) must be submitted to the central repository's `main` branch.
   - Direct pushes to the central `main` branch are restricted to maintain repository stability.
   - Code reviews and PR merges will be executed by Gaurav Das after passing automated tests.

2. **Communication Arrangements:**
   - Direct telephone / WhatsApp coordination using registered phone numbers.
   - Daily stand-up / status check during SITM college hours (10:00 AM – 5:00 PM).
   - Technical blockers are escalated immediately to Gaurav Das (Team Leader) or Mr. Nitish Kr. Sarma (Faculty Mentor).

---

## 4. Verified State vs. Pending Coordination Actions

### Currently Verified Facts:
- Central GitHub repository structure is initialized and configured with comprehensive `.gitignore` rules (excluding virtual environments, raw data, caches, and databases).
- Dedicated local ML runtime environment (`fakedeal` Conda environment on Python 3.12.16 with MKL-accelerated scientific libraries and DuckDB 2.0.0) is fully operational.
- Stage 1 data loader is complete, verified by 19 automated unit tests.
- Full 25.6M row dataset census has been successfully executed via DuckDB.

### Pending Actions & Confirmations:

> [!IMPORTANT]
> The following actions are strictly pending and must not be assumed as completed until explicitly confirmed by the respective team members:

1. **GitHub Collaborator & Fork Status (Pending All Members):**
   - GitHub invitations and fork confirmations have **not** yet been recorded in Git history.
   - *Action required:* Gaurav Das to confirm collaborator invitations on GitHub; Rahul, Lakhyajyoti, Saniya, and Myusha to fork the central repository and report their GitHub handles.
2. **Backend Setup & API Endpoint Route Confirmation (Pending Rahul Amin):**
   - Rahul Amin must configure his local FastAPI development environment and confirm whether the analysis endpoint should be `POST /api/analyze` (per API documentation) or `POST /analyze` (per PRD brief).
3. **Dataset Documentation Handover Alignment (Pending Lakhyajyoti Phukan):**
   - Lakhyajyoti Phukan must review the empirical Stage 1 census findings in [dataset/validation-report.md](file:///C:/end%20sem%20project/FAKEDEAL-BUSTER/dataset/validation-report.md) and update [dataset/data-dictionary.md](file:///C:/end%20sem%20project/FAKEDEAL-BUSTER/dataset/data-dictionary.md) to reflect the exact 46 columns and data types.
4. **Frontend Input Schema Alignment (Pending Saniya Begum):**
   - Saniya Begum must review the provisional input contract ([docs/ml-backend-contract-draft.md](file:///C:/end%20sem%20project/FAKEDEAL-BUSTER/docs/ml-backend-contract-draft.md)) to ensure the React product inspector form captures required fields (`current_price`, `original_price`, `product_name`) and handles optional historical inputs.
5. **Integration Test Matrix (Pending Myusha Chakma):**
   - Myusha Chakma must prepare the Day 2 / Day 3 testing matrix based on the provisional API contract and standardized verdict states.
