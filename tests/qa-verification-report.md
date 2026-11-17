# FakeDeal Buster — QA Fixture Generation & Verification Report

**Author:** Data Preparation Analyst & QA Support (Lakhyajyoti Phukan)  
**Project:** FakeDeal Buster — Sale-Day Artificial Discount & Price Scam Detector  
**Institution:** Scholar Institute of Technology and Management (SITM), Guwahati  
**Component:** QA Fixture Suite Verification & Reproducibility Audit  
**Date:** 2024-01-31 (Execution Reference: November 17, 2026)  
**Status:** COMPLETE & VERIFIED  

---

## 1. Executive Summary and Scope Compliance

In accordance with the approved Day 3 Approved Fixture Specification specification, the deterministic Synthetic QA Fixture system has been fully implemented, executed, validated, and documented. 

This deliverable establishes an independent software testing baseline for the FakeDeal Buster pipeline. The fixture suite operates with zero runtime dependency on the 24.74 GB raw dataset, loads zero multi-gigabyte files into memory, executes purely with Python standard library modules, and guarantees 100% byte-identical reproducibility across independent runs.

### Scope and Safety Audit Confirmation
- **Original Dataset Integrity:** Raw files in `C:\End Sem Project\archive (1)` remain 100% untouched (verified by filesystem LastWriteTime audit).
- **Deliverable Isolation:** Zero ML model files (`ml/models/`), prototype pipeline code (`ml/prototype_pipeline.py`), frontend source files (`frontend/`), or backend source files (`backend/`) were created, edited, or modified.
- **Git State Preservation:** No Git commits, branches, staging operations (`git add`), or PRs were performed. The Git repository remains on clean branch `main`.
- **Approved Day 1 & Day 2 Deliverables:** All existing reports in `reports/day2_final/` remain strictly unmodified.

---

## 2. Inventory of Created Files

| File Path | Component | Purpose |
|---|---|---|
| [scripts/generate_qa_fixtures.py](file:///C:/Users/phuko/Documents/FAKEDEAL-BUSTER/scripts/generate_qa_fixtures.py) | Generator & Validator | Standalone Python CLI script using standard library modules to deterministically build, validate, and serialize the fixture suite. |
| [tests/fixtures/qa_scenarios.json](file:///C:/Users/phuko/Documents/FAKEDEAL-BUSTER/tests/fixtures/qa_scenarios.json) | Test Fixture Dataset | Serialized JSON file containing all 10 approved QA scenarios (309 total records) with explicit inputs, expectations, and context. |
| [tests/fixtures/README.md](file:///C:/Users/phuko/Documents/FAKEDEAL-BUSTER/tests/fixtures/README.md) | Fixture Documentation | Comprehensive schema specification, scenario catalog, usage guidelines, and contract boundary documentation. |
| [tests/qa-verification-report.md](file:///C:/Users/phuko/Documents/FAKEDEAL-BUSTER/tests/qa-verification-report.md) | QA Verification Report | Detailed report documenting execution results, record counts, 13 verification checks, and reproducibility proof. |
| [tests/manual-qa-checklist.md](file:///C:/Users/phuko/Documents/FAKEDEAL-BUSTER/tests/manual-qa-checklist.md) | QA Manual Checklist | Step-by-step manual testing protocol distinguishing software correctness checks from ML fraud detection evaluations. |

---

## 3. Scenario Inventory and Record Count Audit

| Scenario ID | Scenario Name | Primary Entity Key | Date Range / Timestamps | Record Count | Architectural Status | Expected Output / Code |
|---|---|---|---|:---:|---|---|
| **QA-SCN-01** | Stable Normal Pricing | `("P_TEST_001", "amazon")` | `2024-01-01` to `2024-01-31` | **31** | Verified Prototype Math | `SUCCESS_EVALUATED` (FDI = 26.67, Low Risk) |
| **QA-SCN-02** | Current Price Above Historical Avg | `("P_TEST_002", "amazon")` | `2024-01-01` to `2024-01-31` | **31** | Verified Prototype Math | `SUCCESS_EVALUATED` (FDI = 70.83, High Risk) |
| **QA-SCN-03** | Legitimate Deep Discount | `("P_TEST_003", "amazon")` | `2024-01-01` to `2024-01-31` | **31** | Verified Prototype Math | `SUCCESS_EVALUATED` (FDI = 8.75, Low Risk) |
| **QA-SCN-04** | Inflated MSRP Anchor Discount | `("P_TEST_004", "walmart")` | `2024-01-01` to `2024-01-31` | **31** | Verified Prototype Math | `SUCCESS_EVALUATED` (FDI = 70.00, High Risk) |
| **QA-SCN-05** | Insufficient Historical Depth | `("P_TEST_005", "walmart")` | `2024-01-01` to `2024-01-05` | **5** | Proposed QA Contract | `NEEDS_MORE_DATA` (`INSUFFICIENT_HISTORY_N_LESS_THAN_30`) |
| **QA-SCN-06** | Discontinuous Time Series | `("P_TEST_006", "flipkart")` | `2024-01-01`..`10` & `25`..`29` | **15** | Proposed QA Contract | `NEEDS_MORE_DATA` (`TIME_SERIES_DISCONTINUITY_CALENDAR_GAP`) |
| **QA-SCN-07** | Duplicate Key Collision | `("P_TEST_007", "bestbuy")` | `2024-01-01` to `2024-01-30` (x2) | **31** | Proposed QA Contract | `INVALID_INPUT_DUPLICATE` (`PRIMARY_KEY_COLLISION_DUPLICATE_TIMESTAMP`) |
| **QA-SCN-08** | Malformed Price & Discount Boundaries | `("P_TEST_008", "amazon")` | `2024-01-31` to `2024-02-06` | **7** | Proposed QA Contract | `VALIDATION_ERROR` (`VALIDATION_RULE_VIOLATION` VR-01..VR-08) |
| **QA-SCN-09** | Missing Mandatory Fields | `("P_TEST_009", "amazon")` | `2024-01-31`, `02-01`, `null` | **3** | Proposed QA Contract | `VALIDATION_ERROR` (`MISSING_MANDATORY_FIELD`) |
| **QA-SCN-10** | Multiple Stream Isolation | 4 Distinct Entities | `2024-01-01` to `2024-01-31` | **124** | Verified Prototype Math | `SUCCESS_EVALUATED` (Stream 1: 8.75, Stream 2: 65.17, Stream 3: 15.00, Stream 4: 15.00) |
| **TOTAL** | **10 Scenarios** | — | — | **309** | — | — |

---

## 4. Comprehensive Validation Results (13/13 Checks Passed)

All 13 validation and integrity checks stipulated in Section 6 of the Day 3 QA Fixture Suite specification were executed and confirmed passed:

```
[PASS] Check 1: All 10 scenario IDs present (QA-SCN-01 through QA-SCN-10).
[PASS] Check 2: Record counts exactly match Approved Fixture Specification specification (Total: 309 records).
[PASS] Check 3: Required fields and data types consistent across standard scenarios.
[PASS] Check 4: Timestamp formatting valid ISO-8601 for all populated timestamps.
[PASS] Check 5: Scenario 7 contains exact intended duplicate composite key on Day 30.
[PASS] Check 6: Scenario 9 contains exactly intended missing fields across distinct/null timestamps.
[PASS] Check 7: Scenario 8 contains exact corrected 7-record VR-01..VR-08 mapping.
[PASS] Check 8: Scenario 10 contains exactly 4 independent product-platform streams.
[PASS] Check 9: Scenario 10 rolling baselines isolated per stream (100, 200, 10, 500).
[PASS] Check 10: Expected FDI calculations match approved Approved Fixture Specification values exactly.
[PASS] Check 11: Two independent generator runs produce byte-identical output.
[PASS] Check 12: Original dataset files remain unchanged.
[PASS] Check 13: No ML, frontend, or backend source files were modified.
```

### Detailed Analysis of Specific Checks

#### Check 5: Scenario 7 Duplicate Key Collision Verification
- Composite primary key: `("P_TEST_007", "bestbuy", "2024-01-30T00:00:00")`.
- Record 30: `price = 45.00`, `original_price = 60.00`, `discount_pct = 25.00`.
- Record 31: `price = 55.00`, `original_price = 60.00`, `discount_pct = 8.33`.
- Result: Exactly two colliding rows sharing the Day 30 composite key within a 31-record stream. Passes duplicate isolation without contaminating preceding 29 daily rows.

#### Check 6: Scenario 9 Missing Field Isolation
- Record 1 (`SCN09_REC_01`): `timestamp = "2024-01-31T00:00:00"`, `price = null`.
- Record 2 (`SCN09_REC_02`): `timestamp = "2024-02-01T00:00:00"`, `original_price = null`.
- Record 3 (`SCN09_REC_03`): `timestamp = null`, `price = 80.00`, `original_price = 100.00`.
- Result: Timestamps are completely distinct or null, preventing unintended composite key collisions while testing isolated missing mandatory fields.

#### Check 7: Scenario 8 Validation Rule Mapping
- `SCN08_REC_01`: `P = 0.00, P_orig = 50.00, disc = 100.0%` $\to$ **VR-01, VR-06** (MULTIPLE)
- `SCN08_REC_02`: `P = -15.00, P_orig = 50.00, disc = 0.0%` $\to$ **VR-02, VR-08** (MULTIPLE)
- `SCN08_REC_03`: `P = 50.00, P_orig = 0.00, disc = 0.0%` $\to$ **VR-03, VR-04** (MULTIPLE)
- `SCN08_REC_04`: `P = 120.00, P_orig = 100.00, disc = -20.0%` $\to$ **VR-04, VR-05** (MULTIPLE INTRINSIC)
- `SCN08_REC_05`: `P = 5.00, P_orig = 100.00, disc = 95.0%` $\to$ **VR-06** (ISOLATED - Dataset 90% cap test)
- `SCN08_REC_06`: `P = 10.00, P_orig = 100.00, disc = 110.0%` $\to$ **VR-07, VR-08** (MULTIPLE - >100% ceiling test)
- `SCN08_REC_07`: `P = 80.00, P_orig = 100.00, disc = 50.0%` $\to$ **VR-08** (ISOLATED - Math mismatch test)

#### Check 8 & 9: Scenario 10 Partition Isolation
- Verified that 4 independent entities are tracked simultaneously:
  - Stream 1: `(P_TEST_010A, amazon)` $\to \mu_{30} = 100.00$, $\text{FDI} = 8.75$ (Low Risk)
  - Stream 2: `(P_TEST_010A, walmart)` $\to \mu_{30} = 200.00$, $\text{FDI} = 65.17$ (High Risk)
  - Stream 3: `(P_TEST_010B, amazon)` $\to \mu_{30} = 10.00$, $\text{FDI} = 15.00$ (Low Risk)
  - Stream 4: `(P_TEST_010B, walmart)` $\to \mu_{30} = 500.00$, $\text{FDI} = 15.00$ (Low Risk)
- Result: Cross-entity and cross-platform isolation strictly verified.

---

## 5. Reproducibility Test Results

Two independent generation runs were executed using `scripts/generate_qa_fixtures.py` across separate invocations, generating to independent targets. 

Both outputs were compared byte-for-byte and hashed using SHA-256:

| Execution Run | Output Destination | SHA-256 Checksum | Match Status |
|---|---|---|:---:|
| **Run 1 (Primary)** | `tests/fixtures/qa_scenarios.json` | `63d38dc83f7223720f71f4699597f37bd84c7ec58892b8defa070d5bb0ea4ba7` | **EXACT MATCH** |
| **Run 2 (Verification)** | `tests/fixtures/qa_scenarios_repro_test.json` | `63d38dc83f7223720f71f4699597f37bd84c7ec58892b8defa070d5bb0ea4ba7` | **EXACT MATCH** |

**Reproducibility Verdict:** 100% deterministic, byte-identical output across repeated executions.

---

## 6. Architectural Separation: Verified Prototype Math vs Proposed QA Contracts

| Capability / Behavior | Implementation in `ml/prototype_pipeline.py` | Implementation in `tests/fixtures/qa_scenarios.json` | Status / Architectural Classification |
|---|:---:|:---:|---|
| **Engineered Ratios & Differences** | Implemented (Lines 82–91) | Expected in Scenarios 1–4, 10 | **VERIFIED PROTOTYPE MATH** |
| **FDI Subscore & Composite Math** | Implemented (Lines 94–101) | Expected in Scenarios 1–4, 10 | **VERIFIED PROTOTYPE MATH** |
| **FDI Risk Tier Classification** | Implemented (Lines 104–111) | Expected in Scenarios 1–4, 10 | **VERIFIED PROTOTYPE MATH** |
| **Offline `price_spike_flag` Anchor** | Implemented (Line 75, 97) | Hardcoded to 0.0 in synthetic test inputs | **VERIFIED PROTOTYPE MATH (OFFLINE)** |
| **Product-Platform Entity Grouping** | Implemented in prototype parser | Verified in Scenario 10 | **VERIFIED PROTOTYPE MATH** |
| **Cold-Start Rejection ($N < 30$)** | Not Implemented (returns empty or div-zero) | Enforced in Scenario 5 (`NEEDS_MORE_DATA`) | **PROPOSED QA CONTRACT** |
| **Calendar Discontinuity Detection** | Not Implemented (treats rows as adjacent) | Enforced in Scenario 6 (`NEEDS_MORE_DATA`) | **PROPOSED QA CONTRACT** |
| **Primary Key Collision Handling** | Not Implemented in time-series logic | Enforced in Scenario 7 (`INVALID_INPUT_DUPLICATE`) | **PROPOSED QA CONTRACT** |
| **Boundary & Range Schema Validation** | Not Implemented (crashes on malformed values) | Enforced in Scenario 8 (`VALIDATION_ERROR`) | **PROPOSED QA CONTRACT** |
| **Mandatory Field Null Handling** | Not Implemented (TypeError on `float(None)`) | Enforced in Scenario 9 (`VALIDATION_ERROR`) | **PROPOSED QA CONTRACT** |

---

## 7. Known Limitations and Governance Boundaries

1. **Synthetic Nature of QA Fixtures:**  
   These fixtures are designed specifically for software correctness verification. They verify that formulas, bounds, aggregations, and error gates function strictly according to specification. **They do not evaluate or prove ML fraud detection accuracy, true-positive rates, or real-world classification effectiveness.**
2. **Offline Testing Boundary for `price_spike_flag`:**  
   In live streaming operations, detecting price spikes requires a certified, approved anomaly detection policy. Because no live spike policy has been approved by the ML team, the QA fixtures use `price_spike_flag = 0.0` as an explicit offline test anchor for non-spike test cases.
3. **Incoming Backend Contract Dependencies:**  
   The rejection behaviors in Scenarios 5 through 9 represent explicit functional requirements for Rahul Amin's incoming FastAPI validation middleware. When the backend package arrives, these fixtures will immediately serve as regression tests.

---

## 8. Conclusion and Sign-Off

The Day 3 QA Fixture Suite implementation of the FakeDeal Buster QA fixture suite is **100% complete**, fully validated against all 13 integrity checks, and ready for immediate use by QA and backend engineering teams.
