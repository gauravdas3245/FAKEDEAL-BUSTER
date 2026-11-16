
# FakeDeal Buster — Technology Stack

## 1. Frontend Technologies

| Technology | Purpose |
|---|---|
| React.js | Building the user interface |
| HTML5 | Structuring web pages |
| CSS3 | Styling and layout |
| JavaScript | Frontend logic and API communication |

## 2. Backend Technologies

| Technology | Purpose |
|---|---|
| Python | Backend programming and ML integration |
| FastAPI | Building REST API endpoints |
| Uvicorn | Running the FastAPI application |

## 3. Machine Learning and Data Processing

| Technology | Purpose |
|---|---|
| Pandas | Dataset loading and manipulation |
| NumPy | Numerical operations |
| Scikit-learn | Machine learning model development and evaluation |
| Logistic Regression | Candidate classification algorithm |
| Random Forest Classifier | Candidate classification algorithm |
| Joblib | Saving and loading trained models |

The final classification algorithm will be selected after dataset label validation and model evaluation.

## 4. Data Storage

| Technology | Purpose |
|---|---|
| CSV | Storing manageable processed datasets |
| Parquet | Efficient storage of processed tabular data |
| Joblib | Storing trained ML models and preprocessing objects |

A separate database is not required for the initial MVP.

## 5. Development Tools

| Tool | Purpose |
|---|---|
| Visual Studio Code | Code editing and development |
| Git | Version control |
| GitHub | Source code hosting and team collaboration |
| Web Browser | Application testing |
| Postman or API Docs | Testing backend API endpoints |

## 6. Deployment Environment

The initial version will run locally.

- React frontend: Local development server.
- FastAPI backend: Local Uvicorn server.
- ML model: Loaded locally by the backend.
- Data files: Stored locally in supported formats.

## 7. Technology Selection Rationale

The selected technologies are suitable for an academic prototype because:

- React.js supports modular frontend development.
- Python provides libraries for data analysis and machine learning.
- FastAPI provides a lightweight backend API framework.
- Scikit-learn supports classification and model evaluation.
- GitHub enables collaborative development through forks and pull requests.

## 8. Future Enhancements

Additional technologies or services may be considered if required by future project development. They are not part of the confirmed initial implementation.
