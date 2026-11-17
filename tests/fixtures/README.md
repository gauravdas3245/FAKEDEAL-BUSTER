# FakeDeal Buster — Synthetic QA Test Fixtures

**Component:** Synthetic QA Test Fixture Suite & Validation Specification  
**Role:** Data Preparation Analyst & QA Support  
**Target Suite:** [qa_scenarios.json](qa_scenarios.json)  
**Generator Script:** [../../scripts/generate_qa_fixtures.py](../../scripts/generate_qa_fixtures.py)  

---

## 1. Directory Purpose and Overview

The `tests/fixtures/` directory houses independent, deterministic synthetic datasets designed specifically for automated testing and manual QA verification of the **FakeDeal Buster** system. 

These fixtures decouple pipeline and software validation from the multi-gigabyte raw e-commerce dataset (24.74 GB extracted total footprint). They provide compact, mathematically exact, and reproducible test cases covering standard pipeline calculations, edge cases, cold starts, calendar discontinuities, composite primary key collisions, schema violations, and multi-stream partition isolation.

> [!IMPORTANT]
> **Safety & Scope Boundary:**  
> These synthetic QA fixtures test **software correctness**, **data validation logic**, and **mathematical formula fidelity**. They **do NOT** evaluate machine learning fraud detection accuracy, precision, recall, or operational fraud detection performance on real-world e-commerce transactions.

---

## 2. Fixture Suite File: `qa_scenarios.json`

The fixture file `qa_scenarios.json` contains a total of **10 scenarios** across **309 records**. Every record is deterministically constructed with zero reliance on pseudo-random generation or external dataset files.

### Schema Structure

The top-level structure of `qa_scenarios.json` consists of:

```json
{
  "metadata": {
    "suite_name": "FakeDeal Buster Synthetic QA Fixture Suite",
    "version": "1.0.0",
    "generated_at": "2024-01-31T00:00:00Z",
    "generator_script": "scripts/generate_qa_fixtures.py",
    "role": "Data Preparation Analyst & QA Support",
    "institution": "Scholar Institute of Technology and Management (SITM), Guwahati",
    "total_scenarios": 10,
    "total_records": 309,
    "deterministic_seed": 42
  },
  "scenarios": [ ... ]
}
```

### Scenario Object Fields

Each scenario within `scenarios` contains:
- `scenario_id` *(string)*: Unique identifier (`QA-SCN-01` through `QA-SCN-10`).
- `scenario_name` *(string)*: Descriptive scenario title.
- `description` *(string)*: Test case premise and analytical rationale.
- `classification_status` *(string)*: Either `VERIFIED_PROTOTYPE_MATH` (formula matches [prototype_pipeline.py](../../ml/prototype_pipeline.py)) or `PROPOSED_QA_CONTRACT` (proposed backend/API specification for incoming modules).
- `expected_software_behaviour` *(string)*: `SUCCESS_EVALUATED`, `NEEDS_MORE_DATA`, `INVALID_INPUT_DUPLICATE`, or `VALIDATION_ERROR`.
- `expected_error` *(string | null)*: Target error code or reason when rejection is expected (e.g. `INSUFFICIENT_INPUTS` / `NEEDS_MORE_DATA`).
- `product_id` *(string)*: Product identifier.
- `platform` *(string)*: Marketplace platform name (`amazon`, `walmart`, `flipkart`, `bestbuy`).
- `record_count` *(integer)*: Exact count of records in `records`.
- `documented_context` *(object | null)*: Supporting historical context (e.g., 52-week catalog price anchor, calendar gap details).
- `precomputed_feature_inputs` *(object | null)*: The 6 rolling window inputs (`price_30d_avg`, `price_30d_max`, `price_52w_max`, `price_7d_max`, `price_volatility_30d`, `price_spike_flag`).
- `evaluation_record` *(object | null)*: The target evaluation record (Day 31 / Day 5 / Day 29).
- `expected_calculations` *(object | null)*: Exact expected values for 12 engineered features and subscores, plus final `fdi_score` and `fdi_risk_tier`.
- `expected_risk_tier` *(string | null)*: Target tier (`"Low Risk"`, `"Moderate Risk"`, `"High Risk"`, `"Critical Risk"`).
- `records` *(array of objects)*: Chronological observation sequence.

---

## 3. Scenario Inventory & Illustrative Prototype Calculations

> [!NOTE]
> **Provisional Scoring Specification:**  
> All reported FDI scores (e.g., 26.67, 70.83, 8.75, 70.00) and risk tier classifications (Low Risk, High Risk) represent **illustrative prototype calculations using synthetic offline inputs**. The risk bands ($\ge 80$ Critical, $\ge 60$ High, $\ge 30$ Moderate, $< 30$ Low) are provisional heuristic thresholds. In live inference, inputs lacking mandatory fields or sufficient historical depth ($N < 30$) return **`INSUFFICIENT_INPUTS`** (or `NEEDS_MORE_DATA`) rather than computing a risk tier.

| Scenario ID | Scenario Name | Status / Contract Type | Total Records | Expected Outcome | Illustrative Target FDI / Code |
|---|---|---|:---:|---|---|
| **QA-SCN-01** | Stable Normal Pricing | Verified Prototype Math | 31 | `SUCCESS_EVALUATED` | FDI = 26.67 (Low Risk) |
| **QA-SCN-02** | Current Price Above Historical Avg | Verified Prototype Math | 31 | `SUCCESS_EVALUATED` | FDI = 70.83 (High Risk) |
| **QA-SCN-03** | Legitimate Deep Discount | Verified Prototype Math | 31 | `SUCCESS_EVALUATED` | FDI = 8.75 (Low Risk) |
| **QA-SCN-04** | Inflated MSRP Anchor Discount | Verified Prototype Math | 31 | `SUCCESS_EVALUATED` | FDI = 70.00 (High Risk) |
| **QA-SCN-05** | Insufficient Historical Depth | Proposed QA Contract | 5 | `NEEDS_MORE_DATA` | `INSUFFICIENT_INPUTS` / `INSUFFICIENT_HISTORY_N_LESS_THAN_30` |
| **QA-SCN-06** | Discontinuous Time Series | Proposed QA Contract | 15 | `NEEDS_MORE_DATA` | `TIME_SERIES_DISCONTINUITY_CALENDAR_GAP` |
| **QA-SCN-07** | Duplicate Composite-Key Collision | Proposed QA Contract | 31 | `INVALID_INPUT_DUPLICATE` | `PRIMARY_KEY_COLLISION_DUPLICATE_TIMESTAMP` |
| **QA-SCN-08** | Malformed Price & Discount Boundaries | Proposed QA Contract | 7 | `VALIDATION_ERROR` | `VALIDATION_RULE_VIOLATION` (VR-01..VR-08) |
| **QA-SCN-09** | Missing Mandatory Fields | Proposed QA Contract | 3 | `VALIDATION_ERROR` | `MISSING_MANDATORY_FIELD` (price, msrp, ts) |
| **QA-SCN-10** | Multiple Stream Isolation | Verified Prototype Math | 124 | `SUCCESS_EVALUATED` | Stream 1: 8.75, Stream 2: 65.17, Stream 3: 15.00, Stream 4: 15.00 |
| **TOTAL** | **10 Scenarios** | — | **309** | — | — |

---

## 4. Execution and Verification Instructions

The test fixtures are generated and validated using Python standard library modules (`argparse`, `json`, `hashlib`, `pathlib`, `datetime`):

### 1. Validate In-Memory Without Writing
```powershell
python scripts/generate_qa_fixtures.py --validate-only
```

### 2. Generate / Overwrite Fixture File
```powershell
python scripts/generate_qa_fixtures.py --overwrite
```

### 3. Safe Overwrite Protection
If `tests/fixtures/qa_scenarios.json` exists, running without `--overwrite` will safely halt without modifying the file:
```powershell
python scripts/generate_qa_fixtures.py
# Exits with status 2: [WARNING] Destination file already exists...
```

### 4. Check Deterministic SHA-256 Checksum
The generated `qa_scenarios.json` produces the verified SHA-256 checksum:
```
63d38dc83f7223720f71f4699597f37bd84c7ec58892b8defa070d5bb0ea4ba7
```

---

## 5. Architectural Boundaries: Prototype Math vs Proposed QA Contracts

1. **Verified Prototype Math (Scenarios 1, 2, 3, 4, 10):**
   - Implements the exact feature engineering and Fake Discount Index (FDI) logic verified in [prototype_pipeline.py](../../ml/prototype_pipeline.py).
   - Weights: $0.35 \cdot S_{\text{gap}} + 0.30 \cdot S_{\text{mean}} + 0.20 \cdot S_{\text{msrp}} + 0.15 \cdot S_{\text{anom}}$.
   - Offline test convention: `price_spike_flag = 0.0`.
   - Volatility convention: Constant historical price sequences yield `price_volatility_30d = 0.0000`.
   - Entity partitioning: Grouping strictly by `(product_id, platform)`.
   - **Canonical Isolation Forest Features:** Highlights the 4 primary continuous dimensions (`ratio_to_30d_avg`, `ratio_to_30d_max`, `msrp_inflation_ratio`, `discount_inflation_gap`).

2. **Proposed QA Contracts (Scenarios 5, 6, 7, 8, 9):**
   - Represent mandatory data engineering requirements for Rahul Amin's incoming backend API validation layer.
   - `ml/prototype_pipeline.py` currently assumes cleaned, tabular splits and does not include calendar discontinuity checks, composite key collision handling, or null exception handlers.
   - These scenarios define the expected contract specifications for backend request validation before routing records to the scoring engine, returning `INSUFFICIENT_INPUTS` or `VALIDATION_ERROR` when constraints fail.
