# PHASE 1: LAKHYAJYOTI PHUKON CONTRIBUTION & PULL REQUEST AUDIT
**Project:** FakeDeal Buster — Sale-Day Artificial Discount & Price Scam Detector  
**Team Member:** Lakhyajyoti Phukon (Student ID: 2681000002)  
**Role:** Data Preprocessing Analyst / Data Engineering Lead  
**Audit Date:** 22 November 2026  
**Auditor:** Senior Git Engineer & Project Architect  
**Mode:** READ-ONLY AUDIT (Phase 1)

---

## 1. Executive Summary & Resolution of Contribution Mystery

The student (Gaurav Das, Team Leader and GitHub maintainer) recalled approving a major contribution from Lakhyajyoti Phukon on GitHub, but could not locate the commits in the local working tree or central Git log.

This audit has **fully solved the mystery with conclusive cryptographic and GitHub API evidence**:

1. **Lakhyajyoti's GitHub Identity:**
   * **GitHub Username:** `phukon066-create`
   * **Associated Email:** `phukon066@gmail.com`
   * **User ID:** `295819262`
   * **Public Profile:** `https://github.com/phukon066-create`

2. **The Approved Pull Request:**
   * **Repository:** `phukon066-create/FAKEDEAL-BUSTER` (Fork of `gauravdas3245/FAKEDEAL-BUSTER`)
   * **Pull Request Number:** **PR #1**
   * **Title:** `feat(qa): add data validation fixtures and quality documentation`
   * **Created At:** 17 November 2026
   * **Reviewer:** `gauravdas3245` (Gaurav Das)
   * **Review Status:** **APPROVED** (`state: APPROVED`, review comment: `"ok. done"`, Review ID: `5955212293`, submitted on 18 November 2026 at 10:56:34 UTC)
   * **Merge Status:** **MERGED** on 18 November 2026 at 11:17:45 UTC by `phukon066-create` into `phukon066-create:main`.

3. **Why the Work is Missing Locally and Upstream:**
   * **The Architectural Disconnect:** Lakhyajyoti opened PR #1 **internally within his own fork** (merging his branch `feature/data-preparation-qa` into his fork's default branch `main`).
   * He did **not** open an upstream Pull Request targeting `gauravdas3245/FAKEDEAL-BUSTER:main`.
   * Consequently, when Gaurav Das approved PR #1 and Lakhyajyoti clicked "Merge", the commits were merged into `phukon066-create/FAKEDEAL-BUSTER:main`, but **never fetched, pulled, or merged into the central repository `gauravdas3245/FAKEDEAL-BUSTER:main` or the local working directory `C:\end sem project\FAKEDEAL-BUSTER`**.
   * His work is **100% real, approved, and preserved on GitHub**, but currently stranded on his fork.

---

## 2. Inventory of Lakhyajyoti's Commits

Inspection of `https://api.github.com/repos/phukon066-create/FAKEDEAL-BUSTER/commits` reveals exactly 4 commits associated with his contribution:

| # | Commit SHA | Date (UTC) | Author / Committer | Commit Subject |
|:---:|:---:|:---:|:---|:---|
| 1 | `d6f402f` | 2026-11-17 18:56:39 | Lakhyajyoti Phukon `<phukon066@gmail.com>` | `feat(qa): add data validation fixtures and quality documentation` |
| 2 | `ac3be46` | 2026-11-17 19:21:43 | Lakhyajyoti Phukon `<phukon066@gmail.com>` | `docs(dataset,qa): address review feedback on links, licence, schema, and provisional FDI scoring` |
| 3 | `4213882` | 2026-11-17 20:38:30 | Lakhyajyoti Phukon `<phukon066@gmail.com>` | `docs(qa): reconcile dataset evidence and clarify feature contracts` |
| 4 | `a27b2d2` | 2026-11-18 11:17:44 | Lakhyajyoti Phukon `<phukon066@gmail.com>` | `Merge pull request #1 from phukon066-create/feature/data-preparation-qa` |

* **Exists on `gauravdas3245/FAKEDEAL-BUSTER:main`?** **NO.**
* **Exists in local working tree `C:\end sem project\FAKEDEAL-BUSTER`?** **NO.**
* **Current Location:** Exclusively on remote `https://github.com/phukon066-create/FAKEDEAL-BUSTER` (on both `main` and `feature/data-preparation-qa` branches).

---

## 3. Files Contributed by Lakhyajyoti Phukon

A comprehensive diff comparison (`https://api.github.com/repos/gauravdas3245/FAKEDEAL-BUSTER/compare/main...phukon066-create:main`) reveals that Lakhyajyoti contributed **10 files** totaling **+5,557 lines added** and **-243 lines removed**:

### 3.1 New Files Added (5 Files)
1. `scripts/generate_qa_fixtures.py` (+1,177 lines)  
   * **Purpose:** Standalone Python CLI fixture generator that deterministically constructs, validates, and serializes synthetic test datasets with CLI options (`--output`, `--validate-only`, `--overwrite`).
   * **Status in local repo:** **MISSING** (File does not exist locally).
2. `tests/fixtures/qa_scenarios.json` (+3,351 lines, master dataset)  
   * **Purpose:** Comprehensive test dataset containing 10 scenarios across 309 records:
     * `QA-SCN-01`: Stable Baseline Pricing
     * `QA-SCN-02`: Pre-Sale Price Hike (FDI 70.83, High Risk)
     * `QA-SCN-03`: Legitimate Deep Discount (FDI 8.75, Low Risk)
     * `QA-SCN-04`: Inflated MSRP Anchor (FDI 70.00, High Risk)
     * `QA-SCN-05`: Cold-Start Rejection ($N < 30$ observations)
     * `QA-SCN-06`: Calendar Gap Discontinuity ($> 1$ day gap)
     * `QA-SCN-07`: Primary Key Collision (`P_TEST_007`, `bestbuy`, `2024-01-30`)
     * `QA-SCN-08`: Schema Boundary Validation (VR-01 through VR-08)
     * `QA-SCN-09`: Missing Mandatory Field Rejection
     * `QA-SCN-10`: Multi-Stream Partition Isolation
   * **Integrity Proof:** Deterministic SHA-256: `63d38dc83f7223720f71f4699597f37bd84c7ec58892b8defa070d5bb0ea4ba7`.
   * **Status in local repo:** **MISSING** (Directory `tests/fixtures/` does not exist locally).
3. `tests/fixtures/README.md` (+132 lines)  
   * **Purpose:** Fixture documentation detailing schema, scenario catalog, baseline precomputed inputs, expected behaviors, and generator instructions.
   * **Status in local repo:** **MISSING**.
4. `tests/manual-qa-checklist.md` (+227 lines)  
   * **Purpose:** Formal 12-point manual QA testing protocol with actionable pass/fail criteria and execution log template for team testers.
   * **Status in local repo:** **MISSING**.
5. `tests/qa-verification-report.md` (+122 lines)  
   * **Purpose:** Technical verification evidence documenting 13 integrity checks, reproducibility proofs, and test-data isolation.
   * **Status in local repo:** **MISSING**.

### 3.2 Existing Files Enhanced (5 Files)
6. `dataset/data-dictionary.md` (+173 lines, -60 lines)  
   * Expanded data dictionary to full 59-column production specification (46 verified raw columns + 13 feature engineering columns).
7. `dataset/preprocessing-notes.md` (+184 lines, -110 lines)  
   * Added formal 80/10/10 chronological split architecture, boundary null mitigation, and sampling strategies.
8. `dataset/validation-report.md` (+195 lines, -50 lines)  
   * Updated with verified empirical data quality scorecard based on 100% streaming census.
9. `dataset/README.md` (+53 lines, -64 lines)  
   * Updated dataset navigation links and measurement basis reconciliation (explaining the 24.74 GB uncompressed volume vs 7.73 GB consolidated CSV).
10. `tests/README.md` (+25 lines, -19 lines)  
    * Updated test documentation linking to new fixtures, manual checklist, and verification evidence.

---

## 4. Status of Lakhyajyoti's Work & Integration Gaps

| Work Component | Status on Lakhyajyoti's Fork | Status in Local Working Tree | Integration Requirement |
|---|:---:|:---:|---|
| **Synthetic QA Generator (`generate_qa_fixtures.py`)** | Complete & Tested | **Missing** | Pull into `scripts/generate_qa_fixtures.py` |
| **Master QA Fixtures (`qa_scenarios.json`)** | Complete & Verified | **Missing** | Pull into `tests/fixtures/qa_scenarios.json` |
| **QA Documentation & Checklists** | Complete | **Missing** | Pull into `tests/` directory |
| **Data Dictionary Updates** | Complete (59 cols) | Partial (Scaffold) | Merge with local Stage 1 empirical census |
| **Validation Report Updates** | Complete | Superseded locally | Local `dataset/validation-report.md` has exhaustive DuckDB census; merge notes |
| **Git Commit History** | Merged on Fork | Unmerged Upstream | Add remote `lakhya` and cherry-pick/merge to maintain authentic Git attribution |

---

## 5. Recommended Actions for Phase 2 (Restructuring)

To preserve Lakhyajyoti's official academic Git attribution without creating merge conflicts with the local production implementation:

1. **Add Remote for Lakhyajyoti's Fork:**
   ```bash
   git remote add lakhya https://github.com/phukon066-create/FAKEDEAL-BUSTER.git
   git fetch lakhya
   ```
2. **Cherry-pick or Merge his Commits:**
   * Commits `d6f402f`, `ac3be46`, and `4213882` contain his clean authored contributions.
   * Extract `scripts/generate_qa_fixtures.py`, `tests/fixtures/`, `tests/manual-qa-checklist.md`, and `tests/qa-verification-report.md`.
3. **Reconcile Dataset Documentation:**
   * Merge his 59-column schema definitions into `dataset/data-dictionary.md`.
   * Retain Gaurav's verified 25.6M row DuckDB census in `dataset/validation-report.md`.
4. **Result:** Lakhyajyoti will appear in `git log` and GitHub contributors with full, authentic attribution for his Data Preparation & QA deliverables.
