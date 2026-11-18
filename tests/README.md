# FakeDeal Buster — Test Suite & QA Resources

This directory contains test suites, synthetic fixtures, validation guidelines, and testing protocols for the FakeDeal Buster application.

## Directory Layout

| Resource | Purpose | Target Components |
|---|---|---|
| [fixtures/qa_scenarios.json](fixtures/qa_scenarios.json) | Master synthetic QA fixture dataset containing 10 scenarios and 309 records | Preprocessing, API Validation, Feature Math |
| [fixtures/README.md](fixtures/README.md) | Fixture catalog, JSON schema, rolling baselines, and CLI execution guide | All Developers & QA Testers |
| [manual-qa-checklist.md](manual-qa-checklist.md) | 12-point manual testing checklist and verification protocol | Backend API, Pipeline Preprocessing |
| [qa-verification-report.md](qa-verification-report.md) | Reproducibility evidence and 13-point automated integrity audit | QA Verification & Technical Auditing |

## Testing Areas

- **Data Integrity & Schema Validation:** Boundary checks, negative/zero price rejection, MSRP inflation constraints, and mandatory field null enforcement.
- **Time-Series Logic & Stream Isolation:** Cold-start handling, calendar gap discontinuity detection, primary key duplicate rejection, and `(product_id, platform)` partition independence.
- **FDI Formula Fidelity:** Mathematical precision of engineered features, sub-score clipping, and Fake Discount Index (FDI) composite scoring.
  - *Provisional Scoring Note:* All FDI scores (e.g., 26.67, 70.83) and risk bands (Low/High Risk) represent illustrative prototype calculations using synthetic offline inputs and provisional heuristic thresholds. In live inference, inputs lacking mandatory fields or sufficient historical depth ($N < 30$) return `INSUFFICIENT_INPUTS` rather than computing a risk tier.
- **Backend API Integration:** Schema contracts for incoming FastAPI endpoints (`POST /analyze`).
- **End-to-End Application Testing:** React frontend and FastAPI backend integration.

## Testing Guidelines

- Test valid, boundary, and malformed inputs using the synthetic fixture suite.
- Verify API response structures and error codes match the specifications documented in [fixtures/README.md](fixtures/README.md).
- Do not claim tests as passed without actual execution and verification.
- **Testing Boundary Rule:** Synthetic QA fixtures test **software correctness and data validation logic**; they do NOT evaluate machine learning fraud detection accuracy or real-world classification performance.

## Test Ownership

- **Lakhyajyoti Phukan:** Data Preparation Analyst & QA Support (Synthetic QA fixtures, data dictionary, preprocessing validation).
- **Myusha Chakma:** Testing & Integration Coordinator (End-to-end and application testing).
- **Rahul Amin:** Backend Developer (FastAPI input validation and API contract enforcement).
- **Gaurav Das:** ML Developer (Model validation and feature pipeline integration).
