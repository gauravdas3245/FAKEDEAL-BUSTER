
# FAKEDEAL BUSTER

### An ML-Powered E-Commerce Discount Analysis System

FakeDeal Buster is a student project that aims to analyse e-commerce product prices and discounts to identify potentially misleading artificial discounts.

The system will use historical price information, discount-related features, and machine learning techniques to help users understand whether a displayed discount appears genuine or potentially misleading.

> **Project status:** Under Development

---

## Project Overview

Online shopping platforms frequently display large discount percentages. However, a high discount percentage does not always mean that a product is available at a genuinely reduced price.

FakeDeal Buster aims to address this problem by analysing product pricing information and presenting an understandable assessment of the displayed discount.

The project is being developed as part of the BCA Semester I academic project at Scholar Institute of Technology and Management (SITM), Guwahati.

## Objectives

- Analyse product prices and discount percentages.
- Examine historical pricing patterns where data is available.
- Identify unusual price changes and potentially misleading discount patterns.
- Apply machine learning techniques to price-related data.
- Present analysis results through a simple user interface.
- Help users make more informed shopping decisions.

## Planned Features

- Product price and discount analysis.
- Historical price trend analysis, subject to data availability.
- Detection of unusual pricing patterns.
- Machine learning-based discount assessment.
- Clear and understandable analysis results.
- Visual representation of price trends.

Features will be finalised based on dataset validation and implementation feasibility.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React.js, HTML5, CSS3, JavaScript |
| Backend | Python, FastAPI, Uvicorn |
| Data Processing | Pandas, NumPy |
| Machine Learning | Scikit-learn |
| Model Storage | Joblib |
| Version Control | Git and GitHub |

## System Architecture

The planned application follows a frontend-backend-machine-learning architecture.

1. **Frontend:** Collects product information and displays analysis results.
2. **Backend:** Handles requests, validates inputs, and connects the frontend with the analysis components.
3. **Machine Learning:** Processes pricing features and generates an assessment.
4. **Data Layer:** Uses the selected e-commerce price dataset for analysis and experimentation.

Refer to [System Architecture](docs/system-architecture.md) for more details.

## Dataset

The project uses the **E-Commerce Product Price Tracker Dataset** by Amith Nair, sourced from Kaggle.

- **Dataset:** E-Commerce Product Price Tracker Dataset
- **Author:** Amith Nair
- **Source:** Kaggle
- **Licence:** Kaggle Open License / CC BY-SA 4.0 (as confirmed by the project faculty mentor)

[View the Dataset](https://www.kaggle.com/datasets/amith1707/e-commerce-product-price-tracker-dataset)

The dataset is synthetic and is intended for project analysis and experimentation. Its labels and fields will be validated before being used for supervised machine learning.

The complete dataset will not be uploaded to this repository. Refer to the `dataset/` directory for dataset information, attribution, data dictionary, and preprocessing documentation.

## Machine Learning Approach

The planned machine learning workflow includes:

- Dataset inspection and validation.
- Data cleaning and preprocessing.
- Feature selection and engineering.
- Exploratory data analysis.
- Model training and evaluation.
- Model saving and integration with the backend.

Candidate algorithms include Logistic Regression and Random Forest. The final approach will depend on the quality and suitability of the validated data.

No model accuracy or real-world fraud detection performance is claimed at this stage.

See [ML Approach](docs/ml-approach.md).

## Repository Structure

```text
FAKEDEAL-BUSTER/
│
├── assets/       # Project images and visual resources
├── backend/      # Backend application and API
├── dataset/      # Dataset documentation and data information
├── docs/         # Project documentation
├── frontend/     # User interface
├── ml/           # Machine learning components
├── tests/        # Testing resources
│
├── .env.example
├── .gitignore
├── CONTRIBUTING.md
└── README.md
```

## Team Members

**Institution:** Scholar Institute of Technology and Management (SITM), Guwahati  
**Course:** Bachelor of Computer Applications (BCA), Semester I  
**Group:** B  
**Faculty Mentor:** Mr. Nitish Kr. Sarma

| Member | Responsibility |
|---|---|
| Gaurav Das | Team Leader, ML Developer & GitHub Maintainer |
| Rahul Amin | Backend Developer |
| Lakhyajyoti Phukan | Data Preparation Analyst |
| Saniya Begum | Frontend Developer |
| Myusha Chakma | Testing & Integration Coordinator |

## Development Timeline

| Date | Activity |
|---|---|
| 16 November 2026 | Project setup and dataset inspection |
| 17 November 2026 | Data preparation, ML, backend and frontend development |
| 18 November 2026 | Integration, testing and finalisation |
| 19–20 November 2026 | Project presentation |

## Documentation

- [Project Overview](docs/project-overview.md)
- [Problem Statement](docs/problem-statement.md)
- [Objectives and Scope](docs/objectives-and-scope.md)
- [System Architecture](docs/system-architecture.md)
- [Technology Stack](docs/technology-stack.md)
- [Development Roadmap](docs/development-roadmap.md)
- [Team Roles](docs/team-roles.md)
- [Workflow](docs/workflow.md)
- [API Documentation](docs/api-documentation.md)
- [Machine Learning Approach](docs/ml-approach.md)
- [Testing Report](docs/testing-report.md)
- [Project Limitations](docs/limitations.md)
- [Dataset Documentation](dataset/README.md)
- [Contribution Guidelines](CONTRIBUTING.md)

## Contribution Workflow

This project uses a central repository and fork-based contribution workflow.

1. Team members fork the central repository.
2. Each member works on their assigned tasks in their own fork.
3. Changes are submitted through Pull Requests.
4. The repository maintainer reviews and merges approved changes into the central repository.

Direct pushes to the central `main` branch are not part of the team workflow.

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Limitations

- The selected dataset contains synthetic data, not verified real-world marketplace transactions.
- Historical analysis depends on the availability and quality of product records.
- Machine learning results depend on validated labels and features.
- The system should be treated as an analytical aid, not a guarantee that a discount is genuine or fraudulent.
- Final features and predictions will depend on development and testing results.

## Disclaimer

FakeDeal Buster is an academic project developed for educational and experimental purposes. It is not affiliated with or endorsed by any e-commerce platform.

## Acknowledgements

We acknowledge the dataset author, Amith Nair, for making the E-Commerce Product Price Tracker Dataset available through Kaggle.

---

**Developed by Group B | BCA Semester I | SITM Guwahati**
