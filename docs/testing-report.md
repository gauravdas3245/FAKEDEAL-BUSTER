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

The following table will be updated as tests are executed.

| Test ID | Actual Result | Status | Remarks |
|---|---|---|---|
| TC-01 to TC-10 | Pending execution | Not Tested | To be updated during testing |

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

This section will be completed after integration and final testing.

- Total test cases: 10
- Passed: Pending
- Failed: Pending
- Not tested: 10
- Final testing outcome: Pending
