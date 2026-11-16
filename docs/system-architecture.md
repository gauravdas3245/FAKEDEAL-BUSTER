
# System Architecture

## 1. Architecture Overview

FakeDeal Buster follows a modular client-server architecture. The React frontend communicates with the Python FastAPI backend through HTTP API requests.

The backend handles product information, data processing, and communication with the machine learning component.

## 2. Main Components

### 2.1 Frontend Layer

**Technology:** React.js, HTML, CSS, JavaScript

Responsibilities:
- Provide the user interface.
- Accept product pricing information.
- Send analysis requests to the backend.
- Display discount analysis results.
- Present historical price information where available.

### 2.2 Backend Layer

**Technology:** Python, FastAPI, Uvicorn

Responsibilities:
- Receive requests from the frontend.
- Validate submitted product information.
- Apply required data preprocessing.
- Communicate with the machine learning component.
- Return analysis results through API responses.

### 2.3 Machine Learning Layer

**Technology:** Python, Pandas, NumPy, Scikit-learn

Planned responsibilities:
- Prepare and transform relevant pricing features.
- Train and evaluate classification models, subject to label validity.
- Analyse potentially misleading discount patterns.
- Generate predictions when a valid trained model is available.

Candidate algorithms include Logistic Regression and Random Forest Classifier. The final model will be selected after evaluation.

### 2.4 Dataset Layer

**Dataset:** E-Commerce Product Price Tracker Dataset (Kaggle)

Responsibilities:
- Provide product pricing records for analysis.
- Support data cleaning and feature engineering.
- Support historical price analysis where sufficient records are available.
- Provide documented data fields for model development.

The dataset is synthetic and should not be treated as verified real-world marketplace transaction data.

### 2.5 Model Storage

**Technology:** Joblib

Responsibilities:
- Store trained model files when available.
- Store preprocessing objects where required.
- Load the saved model for backend predictions.

## 3. System Workflow

1. The user opens the FakeDeal Buster web application.
2. The frontend accepts product pricing information.
3. The frontend sends the information to the FastAPI backend.
4. The backend validates the submitted data.
5. Required preprocessing and feature transformation are performed.
6. The machine learning component analyses the available features.
7. The backend prepares the analysis response.
8. The frontend displays the result to the user.

## 4. High-Level Architecture Diagram

```text
+---------------------------+
|        USER               |
+-------------+-------------+
              |
              v
+---------------------------+
|     REACT FRONTEND        |
|  Product Input / Results  |
+-------------+-------------+
              |
         HTTP API
              |
              v
+---------------------------+
|     FASTAPI BACKEND       |
| Validation and Processing|
+-------------+-------------+
              |
              v
+---------------------------+
|   DATA PREPROCESSING      |
| Feature Transformation   |
+-------------+-------------+
              |
              v
+---------------------------+
|   MACHINE LEARNING        |
| Model Prediction /        |
| Discount Analysis         |
+-------------+-------------+
              |
              v
+---------------------------+
|    ANALYSIS RESPONSE      |
+-------------+-------------+
              |
              v
+---------------------------+
|    REACT RESULTS UI       |
+---------------------------+
```

## 5. Communication

- The frontend and backend communicate through HTTP requests.
- JSON is used for API request and response data.
- FastAPI provides the backend API endpoints.
- The machine learning component is integrated into the backend.

## 6. Deployment

The initial application will run locally during development and demonstration.

The frontend and backend will run as separate local services and communicate through the configured API URL.

## 7. Architecture Limitations

- The initial version does not guarantee live marketplace integration.
- Model predictions depend on dataset quality and valid training labels.
- Historical analysis requires sufficient product price records.
- The architecture is designed for an academic prototype rather than commercial-scale deployment.
