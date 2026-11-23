# FakeDeal Buster — Comprehensive Testing & Quality Assurance Suite

This directory documents the multi-layered testing infrastructure, automated test suites, synthetic test fixtures, and quality assurance protocols for **FakeDeal Buster**.

---

## 1. Quality Assurance Architecture Overview

The FakeDeal Buster quality assurance framework spans four distinct, mutually verifying validation layers:

| Layer | Component | Test Count / Scope | Framework | Target Location |
|---|---|---|---|---|
| **Layer 1** | Machine Learning & Feature Pipeline | 117 tests | pytest | `tests/` |
| **Layer 2** | Backend REST API & Services | 57 tests | pytest + FastAPI TestClient | `backend/tests/` |
| **Layer 3** | Frontend State, Form & API Mapping | 29 tests | Node.js Test Runner (`node --test`) | `frontend/tests/` |
| **Layer 4** | Synthetic QA Edge Case Scenarios | 10 scenarios (309 records) | Deterministic Python validator | `tests/fixtures/`, `scripts/` |
| **Integration** | End-to-End System Demonstration | 5 full workflows | Integration harness | `scripts/test_end_to_end.py` |

**Total Verification Points:** **203 automated unit/integration tests** + **10 synthetic QA scenarios (309 records)** + **5 E2E workflows** = **100% PASS RATE**.

---

## 2. Automated Test Execution Commands

### A. Central ML & Feature Pipeline Suite (117 Tests)
Validates rolling feature computation, Isolation Forest anomaly scoring, supervised synthetic classifier inference, data loaders, and provisional FDI edge cases:
```powershell
& "C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe" -m pytest tests/ -v
```

### B. Backend REST API & Service Suite (57 Tests)
Validates FastAPI endpoints, Pydantic v2 schemas, catalog filtering, historical DuckDB queries, multi-database fallback, and structured error handling (404, 409, 422, 500, 503):
```powershell
$env:PYTHONPATH = "backend"
& "C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe" -m pytest backend/tests/ -v
```

### C. Frontend Interface & Validation Suite (29 Tests)
Validates React component state, input normalization, date boundary enforcement, seller rating rules, and API error mappings:
```powershell
Set-Location frontend
npm.cmd test
```

### D. Lakhyajyoti Phukon's QA Fixture Suite Validation (10 Checks)
Executes deterministic validation checks (Checks 1 to 10) against `tests/fixtures/qa_scenarios.json`:
```powershell
& "C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe" scripts/generate_qa_fixtures.py --validate-only
```
*Expected Output:* `[INFO] Suite generated successfully: 10 scenarios, 309 records. Deterministic SHA-256: b739c46446329867f9cf79b7fe89669ad39dbb3a79f62417bc5dd198bbc2f1f4`.

### E. End-to-End Complete Integration Demonstration (5 Workflows)
Runs all 5 mandatory production demonstration workflows through the live FastAPI application:
```powershell
& "C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe" scripts/test_end_to_end.py
```

---

## 3. Directory Layout

```
tests/
├── fixtures/
│   ├── qa_scenarios.json            # Master synthetic QA fixture dataset (10 scenarios, 309 records)
│   └── README.md                    # Fixture specification, JSON schema, and rolling baseline guide
├── manual-qa-checklist.md           # 12-point manual testing checklist and verification protocol
├── qa-verification-report.md        # Reproducibility evidence and 13-point automated integrity audit
├── test_data_loader.py              # ML data loader validation tests (19 tests)
├── test_fdi.py                      # Fake Discount Indicator math & edge-case tests (46 tests)
├── test_feature_pipeline.py         # 4-feature rolling window math & alignment tests (13 tests)
├── test_inference.py                # Isolation Forest inference & threshold tests (15 tests)
├── test_service.py                  # High-level ML service lifecycle tests (9 tests)
├── test_synthetic_classifier.py     # Supervised LR & RF synthetic benchmark tests (4 tests)
└── test_train_pipeline.py           # Training artifact bundle & checksum tests (11 tests)
```

---

## 4. Testing Guidelines & Boundaries

1. **Deterministic Execution:** All synthetic fixtures and unit tests must execute deterministically without random seed variation.
2. **Strict Boundary Rule:** Synthetic QA fixtures test **software correctness, data validation logic, and feature mathematics**. They do NOT evaluate real-world e-commerce fraud rates.
3. **Provisional Scoring Notice:** FDI scores and risk bands in fixture scenarios represent illustrative prototype calculations using synthetic offline inputs. In live production, records lacking mandatory historical depth ($N < 14$) return `INSUFFICIENT_INPUTS` rather than fabricating a score.
4. **Honest Reporting Policy:** No test result or benchmark metric may be reported without actual terminal execution and verification.
