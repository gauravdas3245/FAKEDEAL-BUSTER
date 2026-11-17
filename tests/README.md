# FakeDeal Buster — Test Suite & QA Resources

This directory contains test suites, synthetic fixtures, validation guidelines, and testing protocols for the FakeDeal Buster application.

## Directory Layout

| Resource | Purpose | Target Components |
|---|---|---|
| [tests/fixtures/qa_scenarios.json](file:///C:/Users/phuko/Documents/FAKEDEAL-BUSTER/tests/fixtures/qa_scenarios.json) | Master synthetic QA fixture dataset containing 10 scenarios and 309 records | Preprocessing, API Validation, Feature Math |
| [tests/fixtures/README.md](file:///C:/Users/phuko/Documents/FAKEDEAL-BUSTER/tests/fixtures/README.md) | Fixture catalog, JSON schema, rolling baselines, and CLI execution guide | All Developers & QA Testers |
| [tests/manual-qa-checklist.md](file:///C:/Users/phuko/Documents/FAKEDEAL-BUSTER/tests/manual-qa-checklist.md) | 12-point manual testing checklist and verification protocol | Backend API, Pipeline Preprocessing |
| [tests/qa-verification-report.md](file:///C:/Users/phuko/Documents/FAKEDEAL-BUSTER/tests/qa-verification-report.md) | Reproducibility evidence and 13-point automated integrity audit | QA Verification & Technical Auditing |

## Testing Areas

- **Data Integrity & Schema Validation:** Boundary checks, negative/zero price rejection, MSRP inflation constraints, and mandatory field null enforcement.
- **Time-Series Logic & Stream Isolation:** Cold-start handling, calendar gap discontinuity detection, primary key duplicate rejection, and `(product_id, platform)` partition independence.
- **FDI Formula Fidelity:** Mathematical precision of engineered features, sub-score clipping, and Fake Discount Index (FDI) composite scoring.
- **Backend API Integration:** Schema contracts for incoming FastAPI endpoints (`POST /analyze`).
- **End-to-End Application Testing:** React frontend and FastAPI backend integration.

## Testing Guidelines

- Test valid, boundary, and malformed inputs using the synthetic fixture suite.
- Verify API response structures and error codes match the specifications documented in [tests/fixtures/README.md](file:///C:/Users/phuko/Documents/FAKEDEAL-BUSTER/tests/fixtures/README.md).
- Do not claim tests as passed without actual execution and verification.
- **Testing Boundary Rule:** Synthetic QA fixtures test **software correctness and data validation logic**; they do NOT evaluate machine learning fraud detection accuracy or real-world classification performance.

## Test Ownership

- **Lakhyajyoti Phukan:** Data Preparation Analyst & QA Support (Synthetic QA fixtures, data dictionary, preprocessing validation).
- **Myusha Chakma:** Testing & Integration Coordinator (End-to-end and application testing).
- **Rahul Amin:** Backend Developer (FastAPI input validation and API contract enforcement).
- **Gaurav Das:** ML Developer (Model validation and feature pipeline integration).
