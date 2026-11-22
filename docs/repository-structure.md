# FakeDeal Buster — Repository Structure

This document outlines the directory structure and organization of the **FakeDeal Buster** repository following consolidation and contributor integration.

---

## 1. Directory Tree

```
FAKEDEAL-BUSTER/
├── .gitignore                               # Git exclusions (1.99GB DB, node_modules, .venv, caches)
├── .env.example                             # Environment variable template
├── CONTRIBUTING.md                          # Team contribution, pull request and code standards
├── LICENSE                                  # MIT / Academic Open Source License
├── README.md                                # Master project documentation & architecture overview
├── render.yaml                              # Render Web Service deployment blueprint
├── requirements.txt                         # Pinned Python production dependencies
├── assets/
│   ├── diagrams/                            # System architecture, pipeline & workflow diagrams
│   └── screenshots/                         # Verified application screenshots (landing & inspector)
│       ├── landing-page.png
│       └── product-inspector.png
├── artifacts/
│   ├── derived/
│   │   ├── fakedeal_demo.duckdb             # Lightweight 20.8MB demo store (98 products, 246k rows)
│   │   └── fakedeal_runtime.duckdb          # Full 2.08GB DuckDB store (git-ignored, 9,980 products)
│   ├── ml/
│   │   ├── evaluations/                     # Held-out test evaluation reports
│   │   ├── isolation_forest_v1/             # Production Isolation Forest bundle (model, metadata, checksums)
│   │   └── synthetic_discount_v1/           # Supervised benchmark artifacts (LR & RF models, metrics)
│   ├── rahul_dataset_handoff/               # Verified CSV fixture sample (p0000001_all_splits.csv)
│   └── synthetic/
│       └── discount_scenarios_v1/           # 40k synthetic discount scenario splits (train, val, test)
├── backend/
│   ├── API_CONTRACT.md                      # Comprehensive REST API contract specification
│   ├── README.md                            # Backend service documentation
│   ├── app/
│   │   ├── main.py                          # FastAPI application, CORS middleware & routes
│   │   ├── exceptions.py                    # Domain-specific HTTP exceptions (404, 409, 422, 503)
│   │   ├── schemas/                         # Pydantic v2 request and response schemas
│   │   └── services/                        # Business logic: catalog, history, forecast, ML adapters
│   └── tests/                               # 57 automated backend tests (pytest + TestClient)
├── dataset/
│   ├── README.md                            # Dataset overview, provenance, and license notice
│   ├── data-dictionary.md                   # 46 original raw columns + 13 pipeline features (59 total)
│   ├── preprocessing-notes.md               # Empirical data cleaning, gap analysis, and stream isolation
│   └── validation-report.md                 # 25.6M row DuckDB census and statistical audit report
├── docs/
│   ├── archive/                             # Preserved team handover reports (Rahul, Saniya)
│   │   ├── rahul-backend-handover.md
│   │   └── saniya-frontend-handover.md
│   ├── openapi.json                         # Exported OpenAPI 3.1.0 specification
│   ├── repository-structure.md              # Consolidated repository layout (this document)
│   ├── system-architecture.md               # Deep system architecture & data flow specification
│   └── team-roles.md                        # Academic team details, Student IDs, and role allocations
├── frontend/
│   ├── package.json                         # Frontend dependencies (React 19, Vite, oxlint)
│   ├── vite.config.js                       # Vite build & development proxy configuration
│   ├── vercel.json                          # Vercel SPA routing rewrite rules
│   ├── public/
│   │   └── icons.svg                        # SVG symbol sprite for UI iconography
│   ├── src/
│   │   ├── App.jsx                          # Main application layout and routing
│   │   ├── components/                      # UI components (Inspector, ModelComparison, Charts)
│   │   ├── services/                        # API client and backend adapter
│   │   └── styles/                          # CSS stylesheets and design system tokens
│   └── tests/                               # 29 automated frontend unit tests (node:test)
├── ml/
│   ├── data_loader.py                       # Time-series stream ingestion and split loading
│   ├── fdi.py                               # Provisional Fake Discount Indicator heuristics
│   ├── feature_pipeline.py                  # 4-feature canonical rolling window engineering
│   ├── inference.py                         # Isolation Forest inference and anomaly classification
│   ├── isolation_forest.py                  # Model architecture and training pipeline
│   ├── preprocessor.py                      # Training data scaling and normalization
│   ├── service.py                           # Central ML high-level analysis service
│   ├── synthetic_classifier.py              # Supervised benchmark (LR vs. RF) pipeline
│   └── train_pipeline.py                    # Pipeline orchestrator and artifact serializer
├── scripts/
│   ├── build_demo_runtime_store.py          # Builds lightweight 20.8MB demo DuckDB from runtime store
│   ├── generate_qa_fixtures.py              # Generates and validates Lakhyajyoti's 10 QA scenarios
│   └── test_end_to_end.py                   # Master 5-workflow end-to-end integration test
└── tests/
    ├── fixtures/
    │   ├── qa_scenarios.json                # Master synthetic QA fixture dataset (10 scenarios, 309 records)
    │   └── README.md                        # Fixture documentation, JSON schema & test matrix
    ├── manual-qa-checklist.md               # 12-point manual QA testing checklist
    ├── qa-verification-report.md            # Automated 13-check QA audit report
    └── test_*.py                            # 117 automated ML unit tests (pytest)
```

---

## 2. Component Ownership & Directory Mapping

| Directory / Domain | Primary Owner | Student ID | Core Scope |
|---|---|---|---|
| `ml/`, `artifacts/ml/`, `scripts/` | Gaurav Das | 2681000390 | Model formulation, feature pipelines, supervised benchmarks |
| `backend/`, `artifacts/derived/` | Rahul Amin | 2681012412 | REST APIs, DuckDB services, CORS, database fallback |
| `dataset/`, `tests/fixtures/` | Lakhyajyoti Phukon | 2681000002 | Data dictionary, QA fixtures, preprocessing audits |
| `frontend/`, `assets/screenshots/` | Saniya Begum | 2681000003 | React 19 UI, Product Inspector, model comparison views |
| `tests/`, `scripts/test_end_to_end.py` | Myusha Chakma | 2681000383 | End-to-end test orchestration, regression verification |
