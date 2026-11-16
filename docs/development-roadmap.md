# FakeDeal Buster – Development Roadmap

## 1. Project Timeline

**Development Period:** 16 November 2026 – 18 November 2026  
**Presentation Period:** 19 November 2026 – 20 November 2026

The project will be developed in three main phases, followed by final presentation and evaluation.

## 2. Day 1 – 16 November 2026

**Focus: Repository Setup, Dataset Inspection and Planning**

### Tasks
- Create and configure the central GitHub repository.
- Prepare the project documentation.
- Set up the development environment.
- Download and inspect the approved e-commerce dataset.
- Examine dataset columns, data types and missing values.
- Check the availability and validity of discount-related labels.
- Define the initial frontend and backend structure.
- Prepare the testing checklist.

### Responsibilities
- **Gaurav Das:** Repository setup, project coordination and initial dataset inspection.
- **Rahul Amin:** Backend environment and FastAPI project setup.
- **Lakhyajyoti Phukan:** Dataset inspection and data quality report.
- **Saniya Begum:** React frontend setup and initial interface planning.
- **Myusha Chakma:** Testing checklist and initial integration requirements.

## 3. Day 2 – 17 November 2026

**Focus: Data Preparation, ML Development and Feature Implementation**

### Tasks
- Clean and preprocess the selected dataset.
- Identify relevant pricing features.
- Prepare the ML training and evaluation pipeline, subject to label validity.
- Develop initial machine learning models if suitable labels are available.
- Implement backend API endpoints.
- Develop frontend input and result components.
- Define the frontend-backend API contract.
- Perform initial module-level testing.

### Responsibilities
- **Gaurav Das:** Feature engineering, model development and evaluation.
- **Rahul Amin:** Backend API implementation and model integration preparation.
- **Lakhyajyoti Phukan:** Data cleaning, preprocessing and feature preparation.
- **Saniya Begum:** Frontend forms, layout and result components.
- **Myusha Chakma:** Module testing and issue reporting.

## 4. Day 3 – 18 November 2026

**Focus: Integration, Testing and Final Preparation**

### Tasks
- Integrate the frontend and backend.
- Connect the ML model to the backend, if model validation is successful.
- Test the complete application workflow.
- Fix critical bugs and integration issues.
- Verify output consistency and error handling.
- Prepare screenshots and presentation materials.
- Freeze the final working version.

### Responsibilities
- **Gaurav Das:** Final ML integration, repository review and project coordination.
- **Rahul Amin:** Backend integration and API debugging.
- **Lakhyajyoti Phukan:** Final data verification and preprocessing support.
- **Saniya Begum:** Frontend integration and UI corrections.
- **Myusha Chakma:** End-to-end testing and bug verification.

## 5. Presentation – 19–20 November 2026

### Preparation
- Prepare the final project demonstration.
- Explain the problem statement and proposed solution.
- Present the system architecture and technology stack.
- Demonstrate the application's working features.
- Explain the dataset, ML approach and evaluation results.
- Discuss project limitations and future improvements.
- Prepare for questions from the faculty panel.

## 6. Team Handoffs

| From | To | Deliverable |
|---|---|---|
| Lakhyajyoti Phukan | Gaurav Das | Cleaned dataset, feature information and data quality report |
| Gaurav Das | Rahul Amin | Validated model and preprocessing pipeline, if available |
| Rahul Amin | Saniya Begum | Backend API endpoints and request/response format |
| All Developers | Myusha Chakma | Integrated application for testing |
| All Members | Gaurav Das | Final contributions and presentation inputs |

## 7. Risk Management

- **Invalid Dataset Labels:** Verify label quality before supervised model training. Use documented anomaly analysis if classification labels are unsuitable.
- **Large Dataset Size:** Use selected columns, sampling or efficient data processing instead of loading the entire dataset into memory.
- **Integration Issues:** Define API contracts early and test modules independently.
- **Time Constraints:** Prioritise a working MVP over optional features.
- **Unexpected Bugs:** Maintain a testing checklist and fix critical issues before the final presentation.

## 8. Definition of Done

The project will be considered ready for presentation when:

- The approved dataset has been inspected and documented.
- Data processing is reproducible.
- The ML approach is supported by valid data and evaluation, or its limitations are clearly documented.
- The frontend and backend communicate successfully.
- Core application workflows work as expected.
- Critical bugs have been resolved.
- Project documentation and presentation materials are prepared.

**Note:** The project will not claim verified real-world fraud detection accuracy from synthetic data. All model claims and results must be supported by actual testing.
