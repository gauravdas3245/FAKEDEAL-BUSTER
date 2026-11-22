# FakeDeal Buster – Testing Report

## 1. Overview

This document defines the testing strategy, test cases, and testing results for the FakeDeal Buster application.

Testing will be conducted throughout development to verify functionality, reliability, usability, and integration between the frontend, backend, and machine learning components.

**Testing Coordinator:** Myusha Chakma – Testing & Integration Coordinator

## 2. Testing Objectives

- Verify that the application accepts valid product information.
- Ensure invalid inputs are handled correctly.
- Check communication between React frontend and FastAPI backend.
- Verify that analysis results are displayed correctly.
- Test model integration when a validated model is available.
- Identify, record, and track software defects.

## 3. Testing Types

| Testing Type | Purpose |
|---|---|
| Functional Testing | Verify application features |
| Input Validation Testing | Check valid and invalid inputs |
| API Testing | Verify backend endpoints and responses |
| Integration Testing | Check frontend-backend communication |
| Model Testing | Evaluate model output after validation |
| Usability Testing | Check interface clarity and ease of use |

## 4. Planned Test Cases

| Test ID | Test Scenario | Expected Result |
|---|---|---|
| TC-01 | Open the application | Application loads successfully |
| TC-02 | Submit valid product details | Backend accepts the request |
| TC-03 | Enter an empty product name | Validation error is displayed |
| TC-04 | Enter a negative price | Invalid input is rejected |
| TC-05 | Enter zero as the current price | Invalid input is rejected |
| TC-06 | Enter current price greater than original price | Standard discount validation is triggered |
| TC-07 | Check backend health endpoint | Backend returns healthy status |
| TC-08 | Submit an analysis request | Backend returns a structured response |
| TC-09 | Display analysis results | Frontend displays the returned information |
| TC-10 | Test unavailable or invalid API response | Application handles the error gracefully |

## 5. Test Execution Status

Final implementation regression executed 18 November 2026 with the existing `fakedeal` Python environment and installed frontend dependencies. Pytest used a verified writable temporary directory outside the repository.

| Test ID | Actual Result | Status | Remarks |
|---|---|---|---|
| Central ML pytest suite | 117 passed | Passed | `tests/`; central ML regression, data loader, feature pipeline, inference engine, FDI, and synthetic classifier unit tests. |
| Backend pytest suite | 57 passed | Passed | `backend/tests/`; product inspection, catalogue filtering, forecast backtesting, history retrieval, 3-state verdict evaluation, and API contracts. One Starlette deprecation warning. |
| Frontend Node tests | 29 passed | Passed | `frontend/tests/`; API client, validation, loading/error states, 3-state assessment presentation, and synthetic model comparison loading. |
| End-to-End Suite | 5/5 workflows passed | Passed | `scripts/test_end_to_end.py`; executes all 5 required workflows against the live FastAPI app and DuckDB runtime store. |
| Live Server Probe | Passed | Passed | `scripts/test_live_server.py`; verifies real Uvicorn server startup on 127.0.0.1, HTTP health check, catalog metadata, and clean shutdown. |
| Frontend production build | Passed | Passed | `npm.cmd run build`; Vite production bundles compiled cleanly. |
| Frontend lint | Passed | Passed | `npm.cmd run lint`; oxlint reports 0 warnings, 0 errors across all files. |
| Model bundle validation | Passed | Passed | Six-file Isolation Forest bundle validated by `scripts/validate_final_model.py`; synthetic LR/RF hashes and feature order verified by `scripts/validate_synthetic_classifier.py`. |
| Actual backend inspection API | HTTP 200 | Passed | Real product `Google Max Smartphones  (Green)`, Amazon, 2024-10-18; Isolation Forest, synthetic scenario result, and 14 forecast points. FDI correctly `INSUFFICIENT_INPUTS`. |
| Browser UI automation | Edge available; manual/API verified | Documented | Browser headless Edge available on host; frontend interaction verified via Node test harness and API response contracts. |

**Note:** No test is marked as passed until it has actually been executed and verified.

## 6. Bug and Issue Tracking

Identified issues will be recorded using the following format:

| Issue ID | Description | Severity | Status |
|---|---|---|---|
| BUG-01 | To be recorded during testing | To be assigned | Open |

Issues will be discussed with the responsible developer and retested after fixes.

## 7. Integration Testing

The following components will be tested together:

1. React frontend and FastAPI backend.
2. Backend input validation and data processing.
3. Backend and machine learning component, if available.
4. API response and frontend result display.

## 8. Testing Limitations

- Testing results depend on the implemented features.
- Model testing requires a validated model.
- Synthetic dataset results may not represent real marketplace behaviour.
- Live marketplace integration is not guaranteed in the initial version.

## 9. Testing Responsibility

**Responsible Member:** Myusha Chakma – Testing & Integration Coordinator

**Supporting Members:** All team members will assist in testing their respective components and resolving identified issues.

## 10. Final Testing Summary

- Automated tests: **203 passed total** (117 ML + 57 backend + 29 frontend).
- End-to-end integration: **5/5 workflows passed** via `scripts/test_end_to_end.py`.
- Live server test: **passed** via `scripts/test_live_server.py`.
- Production build: **passed** (`npm.cmd run build`).
- Frontend lint: **0 warnings, 0 errors** (`npm.cmd run lint`).
- Artifact integrity: SHA-256 checksums verified for both `isolation_forest_v1` and `synthetic_discount_v1`.
- Verified real backend and frontend communication without dummy mocks.
- The original source dataset is simulated and has no positive fake-discount labels. Synthetic classifier metrics are held-out generated-scenario metrics only, not real-world fraud performance.
